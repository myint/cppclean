# Copyright 2007 Neal Norwitz
# Portions Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Find warnings for C++ code.

TODO(nnorwitz): provide a mechanism to configure which warnings should
be generated and which should be suppressed. Currently, all possible
warnings will always be displayed. There is no way to suppress any.
There also needs to be a way to use annotations in the source code to
suppress warnings.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from . import ast
from . import headers
from . import keywords
from . import metrics
from . import symbols
from . import tokenize
from . import utils


try:
    basestring
except NameError:
    basestring = str


__author__ = 'nnorwitz@google.com (Neal Norwitz)'


HEADER_EXTENSIONS = frozenset(['.h', '.hh', '.hpp', '.h++', '.hxx', '.cuh'])
CPP_EXTENSIONS = frozenset(['.cc', '.cpp', '.c++', '.cxx', '.cu'])

# These enumerations are used to determine how a symbol/#include file is used.
UNUSED = 0
USES_REFERENCE = 1
USES_DECLARATION = 2

DECLARATION_TYPES = (ast.Class, ast.Struct, ast.Enum, ast.Union)


class Module(object):

    """Data container representing a single source file."""

    def __init__(self, filename, ast_list):
        self.filename = filename
        self.ast_list = ast_list
        self.public_symbols = self._get_exported_symbols()

    def _get_exported_symbols(self):
        if not self.ast_list:
            return {}
        return dict([(n.name, n) for n in self.ast_list if n.is_exportable()])


def is_header_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in HEADER_EXTENSIONS


def is_cpp_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in CPP_EXTENSIONS


class WarningHunter(object):

    # Cache filename: ast_list
    _module_cache = {}

    def __init__(self, filename, source, ast_list, include_paths,
                 system_include_paths, nonsystem_include_paths,
                 quiet=False):
        self.filename = filename
        self.source = source
        self.ast_list = ast_list
        self.include_paths = include_paths[:]
        self.system_include_paths = system_include_paths
        self.nonsystem_include_paths = nonsystem_include_paths
        self.quiet = quiet
        self.symbol_table = symbols.SymbolTable()

        self.metrics = metrics.Metrics(source)
        self.warnings = set()
        if filename not in self._module_cache:
            self._module_cache[filename] = Module(filename, ast_list)

    def _add_warning(self, msg, node, filename=None):
        if filename is not None:
            contents = utils.read_file(filename)
            src_metrics = metrics.Metrics(contents)
        else:
            filename = self.filename
            src_metrics = self.metrics
        line_number = get_line_number(src_metrics, node)
        self.warnings.add((filename, line_number, msg))

    def show_warnings(self):
        for filename, line_num, msg in sorted(self.warnings):
            if line_num == 0:
                print('{}: {}'.format(filename, msg))
            else:
                print('{}:{}: {}'.format(filename, line_num, msg))

    def find_warnings(self):
        if is_header_file(self.filename):
            self._find_header_warnings()
        elif is_cpp_file(self.filename):
            self._find_source_warnings()

    def _update_symbol_table(self, module):
        for name, node in module.public_symbols.items():
            self.symbol_table.add_symbol(name, node.namespace, node, module)

    def _get_module(self, node):
        include_paths = [os.path.dirname(self.filename)] + self.include_paths
        source, filename = headers.read_source(node.filename, include_paths)

        if source is None:
            module = Module(filename, None)
            msg = "unable to find '{}'".format(filename)
            self._add_warning(msg, node)
        elif filename in self._module_cache:
            # The cache survives across all instances, but the symbol table
            # is per instance, so we need to make sure the symbol table
            # is updated even if the module was in the cache.
            module = self._module_cache[filename]
            self._update_symbol_table(module)
        else:
            ast_list = None
            try:
                builder = ast.builder_from_source(source, filename,
                                                  self.system_include_paths,
                                                  self.nonsystem_include_paths,
                                                  quiet=self.quiet)
                ast_list = [_f for _f in builder.generate() if _f]
            except tokenize.TokenError:
                pass
            except ast.ParseError as error:
                if not self.quiet:
                    print(
                        "Exception while processing '{}': {}".format(
                            filename,
                            error),
                        file=sys.stderr)
            module = Module(filename, ast_list)
            self._module_cache[filename] = module
            self._update_symbol_table(module)
        return module

    def _read_and_parse_includes(self):
        # Map header-filename: (#include AST node, module).
        included_files = {}
        # Map declaration-name: AST node.
        forward_declarations = {}
        files_seen = {}
        for node in self.ast_list:
            if isinstance(node, ast.Include):
                if node.system:
                    filename = node.filename
                else:
                    module = self._get_module(node)
                    filename = module.filename
                    _, ext = os.path.splitext(filename)
                    if ext.lower() != '.hxx':
                        included_files[filename] = node, module
                if is_cpp_file(filename):
                    self._add_warning(
                        "should not #include C++ source file '{}'".format(
                            node.filename),
                        node)
                if filename == self.filename:
                    self._add_warning(
                        "'{}' #includes itself".format(node.filename),
                        node)
                if filename in files_seen:
                    include_node = files_seen[filename]
                    line_num = get_line_number(self.metrics, include_node)
                    self._add_warning(
                        "'{}' already #included on line {}".format(
                            node.filename,
                            line_num),
                        node)
                else:
                    files_seen[filename] = node
            if isinstance(node, DECLARATION_TYPES) and node.is_declaration():
                forward_declarations[node.full_name()] = node

        return included_files, forward_declarations

    def _verify_include_files_used(self, file_uses, included_files):
        """Find all #include files that are unnecessary."""
        for include_file, use in file_uses.items():
            if not use & USES_DECLARATION:
                node, module = included_files[include_file]
                if module.ast_list is not None:
                    msg = "'{}' does not need to be #included".format(
                        node.filename)
                    if use & USES_REFERENCE:
                        msg += '; use a forward declaration instead'
                    self._add_warning(msg, node)

    def _verify_forward_declarations_used(self, forward_declarations,
                                          decl_uses, file_uses):
        """Find all the forward declarations that are not used."""
        for cls in forward_declarations:
            if cls in file_uses:
                if not decl_uses[cls] & USES_DECLARATION:
                    node = forward_declarations[cls]
                    msg = ("'{}' forward declared, "
                           'but needs to be #included'.format(cls))
                    self._add_warning(msg, node)
            else:
                if decl_uses[cls] == UNUSED:
                    node = forward_declarations[cls]
                    msg = "'{}' not used".format(cls)
                    self._add_warning(msg, node)

    def _determine_uses(self, included_files, forward_declarations):
        """Set up the use type of each symbol."""
        file_uses = dict.fromkeys(included_files, UNUSED)
        decl_uses = dict.fromkeys(forward_declarations, UNUSED)
        symbol_table = self.symbol_table

        for name, node in forward_declarations.items():
            try:
                symbol_table.lookup_symbol(node.name, node.namespace)
                decl_uses[name] |= USES_REFERENCE
            except symbols.Error:
                module = Module(name, None)
                symbol_table.add_symbol(node.name, node.namespace, node,
                                        module)

        def _do_lookup(name, namespace):
            try:
                file_use_node = symbol_table.lookup_symbol(name, namespace)
            except symbols.Error:
                return
            name = file_use_node[1].filename
            file_uses[name] = file_uses.get(name, 0) | USES_DECLARATION

        def _add_declaration(name, namespace):
            if not name:
                # Ignore anonymous struct. It is not standard, but we might as
                # well avoid crashing if it is easy.
                return

            names = [n for n in namespace if n is not None]
            if names:
                name = '::'.join(names) + '::' + name
            if name in decl_uses:
                decl_uses[name] |= USES_DECLARATION

        def _add_reference(name, namespace):
            try:
                file_use_node = symbol_table.lookup_symbol(name, namespace)
            except symbols.Error:
                return

            name = file_use_node[1].filename
            if file_use_node[1].ast_list is None:
                decl_uses[name] |= USES_REFERENCE
            elif name in file_uses:
                # enum and typedef can't be forward declared
                if isinstance(file_use_node[0], (ast.Enum, ast.Typedef)):
                    file_uses[name] |= USES_DECLARATION
                else:
                    file_uses[name] |= USES_REFERENCE

        def _add_use(node, namespace, name=''):
            if isinstance(node, basestring):
                name = node
            elif isinstance(node, list):
                # name contains a list of tokens.
                name = '::'.join([n.name for n in name])

            # node is a Type so look for its symbol immediately.
            if name:
                _do_lookup(name, namespace)
                return

            # Try to search for the value of the variable declaration for any
            # symbols, such as `#define` values or other variable names which
            # may be included in other files.
            obj = getattr(node, 'initial_value', None)
            if obj:
                _do_lookup(obj, namespace)

            # If node is a VariableDeclaration, check if the variable type is
            # a symbol used in other includes.
            obj = getattr(node, 'type', None)
            if obj and isinstance(obj.name, basestring):
                _do_lookup(obj.name, namespace)

            if not isinstance(node, basestring):
                # Happens when variables are defined with inlined types, e.g.:
                #   enum {...} variable;
                return

        def _add_variable(node, namespace, reference=False):
            obj = node.type if isinstance(
                node, ast.VariableDeclaration) else node

            if obj.reference or obj.pointer or reference:
                _add_reference(obj.name, namespace)
            else:
                # Add a use for the variable declaration type as well as the
                # variable value.
                _add_use(obj.name, namespace)
                _add_use(node, namespace)
            # This needs to recurse when the node is a templated type.
            _add_template_use(obj.name,
                              obj.templated_types,
                              namespace,
                              reference)

        def _process_function(function, namespace):
            reference = function.body is None
            if function.return_type:
                return_type = function.return_type
                _add_variable(return_type, namespace, reference)

            for s in function.specializations:
                _add_variable(s, namespace, not function.body)

            templated_types = function.templated_types or ()
            for p in function.parameters:
                node = p.type
                if node.name not in templated_types:
                    if function.body and p.name:
                        # Assume that if the function has a body and a name
                        # the parameter type is really used.
                        # NOTE(nnorwitz): this is over-aggressive. It would be
                        # better to iterate through the body and determine
                        # actual uses based on local vars and data members
                        # used.
                        _add_use(node.name, namespace)
                    elif (
                        p.default and
                        p.default[0].name != '0' and
                        p.default[0].name != 'NULL' and
                        p.default[0].name != 'nullptr'
                    ):
                        _add_use(node.name, namespace)
                    elif node.reference or node.pointer or reference:
                        _add_reference(node.name, namespace)
                    else:
                        _add_use(node.name, namespace)
                    _add_template_use(node.name,
                                      node.templated_types,
                                      namespace,
                                      reference)

        def _process_function_body(function, namespace):
            previous = None
            save = namespace[:]
            for t in function.body:
                if t.token_type == tokenize.NAME:
                    previous = t
                    if not keywords.is_keyword(t.name):
                        # TODO(nnorwitz): handle static function calls.
                        # TODO(nnorwitz): handle using statements in file.
                        # TODO(nnorwitz): handle using statements in function.
                        # TODO(nnorwitz): handle namespace assignment in file.
                        _add_use(t.name, namespace)
                elif t.name == '::' and previous is not None:
                    namespace.append(previous.name)
                elif t.name in (':', ';'):
                    namespace = save[:]

        def _add_template_use(name, types, namespace, reference=False):
            for cls in types or ():
                if cls.pointer or cls.reference or reference:
                    _add_reference(cls.name, namespace)
                elif name.endswith('_ptr'):
                    # Special case templated classes that end w/_ptr.
                    # These are things like auto_ptr which do
                    # not require the class definition, only decl.
                    _add_reference(cls.name, namespace)
                elif name.startswith('Q') and name.endswith('Pointer'):
                    # Special case templated classes from the Qt framework.
                    _add_reference(cls.name, namespace)
                else:
                    _add_use(cls.name, namespace)
                _add_template_use(cls.name, cls.templated_types,
                                  namespace, reference)

        def _process_types(nodes, namespace):
            for node in nodes:
                if isinstance(node, ast.Type):
                    _add_variable(node, namespace)

        # Iterate through the source AST/tokens, marking each symbols use.
        ast_seq = [self.ast_list]
        namespace_stack = []
        while ast_seq:
            for node in ast_seq.pop():
                if isinstance(node, ast.VariableDeclaration):
                    namespace = namespace_stack + node.namespace
                    _add_variable(node, namespace)
                elif isinstance(node, ast.Function):
                    namespace = namespace_stack + node.namespace
                    _process_function(node, namespace)
                    if node.body:
                        _process_function_body(node, namespace)
                elif isinstance(node, ast.Typedef):
                    namespace = namespace_stack + node.namespace
                    _process_types(node.alias, namespace)
                elif isinstance(node, ast.Friend):
                    expr = node.expr
                    namespace = namespace_stack + node.namespace
                    if isinstance(expr, ast.Type):
                        _add_reference(expr.name, namespace)
                    elif isinstance(expr, ast.Function):
                        _process_function(expr, namespace)
                elif isinstance(node, ast.Union) and node.body is not None:
                    ast_seq.append(node.body)
                elif isinstance(node, ast.Class) and node.body is not None:
                    _add_declaration(node.name, node.namespace)
                    namespace = namespace_stack + node.namespace
                    _add_template_use('', node.bases, namespace)
                    ast_seq.append(node.body)
                elif isinstance(node, ast.Using):
                    if node.names[0].name == 'namespace':
                        namespace_stack.append(node.names[1].name)

        return file_uses, decl_uses

    def _find_unused_warnings(self, included_files, forward_declarations,
                              primary_header=None):
        file_uses, decl_uses = self._determine_uses(included_files,
                                                    forward_declarations)
        if primary_header and primary_header.filename in file_uses:
            file_uses[primary_header.filename] |= USES_DECLARATION
        self._verify_include_files_used(file_uses, included_files)
        self._verify_forward_declarations_used(forward_declarations, decl_uses,
                                               file_uses)
        for node in forward_declarations.values():
            try:
                file_use_node = self.symbol_table.lookup_symbol(node.name,
                                                                node.namespace)
            except symbols.Error:
                continue
            name = file_use_node[1].filename
            if (
                file_use_node[1].ast_list is not None and
                name in file_uses and
                file_uses[name] & USES_DECLARATION
            ):
                msg = ("'{}' forward declared, "
                       "but already #included in '{}'".format(node.name, name))
                self._add_warning(msg, node)

    def _find_incorrect_case(self, included_files):
        for (filename, node_and_module) in included_files.items():
            base_name = os.path.basename(filename)
            try:
                candidates = os.listdir(os.path.dirname(filename))
            except OSError:
                continue

            correct_filename = get_correct_include_filename(base_name,
                                                            candidates)
            if correct_filename:
                self._add_warning(
                    "'{}' should be '{}'".format(base_name, correct_filename),
                    node_and_module[0])

    def _find_header_warnings(self):
        included_files, forward_declarations = self._read_and_parse_includes()
        self._find_unused_warnings(included_files, forward_declarations)
        self._find_incorrect_case(included_files)

    def _find_public_function_warnings(self, node, name, primary_header,
                                       all_headers):
        # Not found in the primary header, search all other headers.
        for _, header in all_headers.values():
            if name in header.public_symbols:
                # If the primary.filename == header.filename, it probably
                # indicates an error elsewhere. It sucks to mask it,
                # but false positives are worse.
                if primary_header:
                    msg = ("expected to find '{}' in '{}', "
                           "but found in '{}'".format(name,
                                                      primary_header.filename,
                                                      header.filename))
                    self._add_warning(msg, node)
                break
        else:
            where = 'in any directly #included header'
            if primary_header:
                where = (
                    "in expected header '{}' "
                    'or any other directly #included header'.format(
                        primary_header.filename))

            if name != 'main' and name != name.upper():
                self._add_warning("'{}' not found {}".format(name, where),
                                  node)

    def _check_public_functions(self, primary_header, all_headers):
        """Verify all the public functions are also declared in a header
        file."""
        public_symbols = {}
        declared_only_symbols = {}
        if primary_header:
            for name, symbol in primary_header.public_symbols.items():
                if isinstance(symbol, ast.Function):
                    public_symbols[name] = symbol
            declared_only_symbols = dict.fromkeys(public_symbols, True)

        for node in self.ast_list:
            # Make sure we have a function that should be exported.
            if not isinstance(node, ast.Function):
                continue
            if isinstance(node, ast.Method):
                # Ensure that for Foo::Bar, Foo is *not* a namespace.
                # If Foo is a namespace, we have a function and not a method.
                names = [n.name for n in node.in_class]
                if names != self.symbol_table.get_namespace(names):
                    continue
            if not (node.is_definition() and node.is_exportable()):
                continue

            # This function should be declared in a header file.
            name = node.name
            if name in public_symbols:
                declared_only_symbols[name] = False
            else:
                self._find_public_function_warnings(node,
                                                    name,
                                                    primary_header,
                                                    all_headers)

        for name, declared_only in declared_only_symbols.items():
            if declared_only:
                node = public_symbols[name]
                if node.templated_types is None:
                    msg = "'{}' declared but not defined".format(name)
                    self._add_warning(msg, node, primary_header.filename)

    def _get_primary_header(self, included_files):
        basename = os.path.basename(os.path.splitext(self.filename)[0])
        include_paths = [os.path.dirname(self.filename)] + self.include_paths
        source, filename = headers.read_source(basename + '.h', include_paths)
        primary_header = included_files.get(filename)
        if primary_header:
            return primary_header[1]
        if source is not None:
            msg = "should #include header file '{}'".format(filename)
            self.warnings.add((self.filename, 0, msg))
        return None

    def _find_source_warnings(self):
        included_files, forward_declarations = self._read_and_parse_includes()
        self._find_incorrect_case(included_files)

        for node in forward_declarations.values():
            # TODO(nnorwitz): This really isn't a problem, but might
            # be something to warn against. I expect this will either
            # be configurable or removed in the future. But it's easy
            # to check for now.
            msg = (
                "'{}' forward declaration not expected in source file".format(
                    node.name))
            self._add_warning(msg, node)

        # A primary header is optional. However, when looking up
        # defined methods in the source, always look in the
        # primary_header first. Expect that is the most likely location.
        # Use of primary_header is primarily an optimization.
        primary_header = self._get_primary_header(included_files)

        self._check_public_functions(primary_header, included_files)
        if primary_header and primary_header.ast_list is not None:
            includes = [
                node.filename
                for node in primary_header.ast_list
                if isinstance(node, ast.Include)
            ]
            for (node, _) in included_files.values():
                if node.filename in includes:
                    msg = "'{}' already #included in '{}'".format(
                        node.filename, primary_header.filename)
                    self._add_warning(msg, node)

        # TODO(nnorwitz): other warnings to add:
        #   * unused forward decls for variables (globals)/classes
        #   * Functions that are too large/complex
        #   * Variables declared far from first use
        #   * primitive member variables not initialized in ctor


def get_line_number(metrics_instance, node):
    return metrics_instance.get_line_number(node.start)


def get_correct_include_filename(filename, candidate_filenames):
    if filename not in candidate_filenames:
        for candidate in candidate_filenames:
            if filename.lower() == candidate.lower():
                return candidate
    return None


def run(filename, source, entire_ast, include_paths,
        system_include_paths, nonsystem_include_paths, quiet):
    hunter = WarningHunter(filename, source, entire_ast,
                           include_paths=include_paths,
                           system_include_paths=system_include_paths,
                           nonsystem_include_paths=nonsystem_include_paths,
                           quiet=quiet)
    hunter.find_warnings()
    hunter.show_warnings()
    return len(hunter.warnings)
