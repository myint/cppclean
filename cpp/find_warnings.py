#!/usr/bin/env python
#
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
be generated and which should be suppressed.  Currently, all possible
warnings will always be displayed.  There is no way to suppress any.
There also needs to be a way to use annotations in the source code to
suppress warnings.
"""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


try:
    # Python 3.x
    import builtins
except ImportError:
    # Python 2.x
    import __builtin__ as builtins

import os
import sys

from cpp import ast
from cpp import headers
from cpp import keywords
from cpp import metrics
from cpp import symbols
from cpp import tokenize
from cpp import utils

if not hasattr(builtins, 'set'):
    # Nominal support for Python 2.3.
    from sets import Set as set

if not hasattr(builtins, 'next'):
    # Support Python 2.5 and earlier.
    def next(obj):
        return obj.next()


# The filename extension used for the primary header file associated w/.cc file.
PRIMARY_HEADER_EXTENSION = '.h'

# These enumerations are used to determine how an symbol/#include file is used.
UNUSED = 0
USES_REFERENCE = 1
USES_DECLARATION = 2


class Module(object):
    """Data container represting a single source file."""

    def __init__(self, filename, ast_list):
        self.filename = filename
        self.normalized_filename = os.path.abspath(filename)
        self.ast_list = ast_list
        self.public_symbols = self._GetExportedSymbols()

    def _GetExportedSymbols(self):
        if not self.ast_list:
            return {}
        return dict([(n.name, n) for n in self.ast_list if n.IsExportable()])


def _IsHeaderFile(filename):
    base, ext = os.path.splitext(filename)
    return ext.lower() in ('.h', '.hpp', '.h++', '.hxx')


def _IsCppFile(filename):
    base, ext = os.path.splitext(filename)
    return ext.lower() in ('.c', '.cc', '.cpp', '.c++', '.cxx')


class WarningHunter(object):

    # Cache filename: ast_list
    _module_cache = {}

    def __init__(self, filename, source, ast_list):
        self.filename = filename
        self.normalized_filename = os.path.abspath(filename)
        self.source = source
        self.ast_list = ast_list
        self.symbol_table = symbols.SymbolTable()

        self.metrics = metrics.Metrics(source)
        self.warnings = []
        if filename not in self._module_cache:
            self._module_cache[filename] = Module(filename, ast_list)

    def _GetLineNum(self, metrics, node):
        return metrics.GetLineNumber(node.start)

    def _AddWarning(self, msg, node, filename=None):
        if filename is not None:
            src_metrics = metrics.Metrics(open(filename).read())
        else:
            filename = self.filename
            src_metrics = self.metrics
        line_number = self._GetLineNum(src_metrics, node)
        self.warnings.append((filename, line_number, msg))

    def ShowWarnings(self):
        self.warnings.sort()
        for filename, line_num, msg in self.warnings:
            print('%s:%d: %s' % (filename, line_num, msg))

    def FindWarnings(self):
        # print('Searching for warnings in: %s' % self.filename)
        if _IsHeaderFile(self.filename):
            self._FindHeaderWarnings()
        elif _IsCppFile(self.filename):
            self._FindSourceWarnings()
        else:
            print('Unknown filetype for: %s' % self.filename)

    def _UpdateSymbolTable(self, module):
        for name, node in module.public_symbols.items():
            self.symbol_table.AddSymbol(name, node.namespace, node, module)

    def _GetModule(self, filename):
        if filename in self._module_cache:
            # The cache survives across all instances, but the symbol table
            # is per instance, so we need to make sure the symbol table
            # is updated even if the module was in the cache.
            module = self._module_cache[filename]
            self._UpdateSymbolTable(module)
            return module

        source, actual_filename = headers.ReadSource(filename)
        if source is None:
            module = Module(filename, None)
            print('Unable to find %s' % filename)
        else:
            builder = ast.BuilderFromSource(source, filename)
            try:
                module = Module(filename, filter(None, builder.Generate()))
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                print('Exception while processing %s' % filename)
                module = Module(filename, None)
            else:
                self._UpdateSymbolTable(module)
        self._module_cache[filename] = module
        return module

    def _ReadAndParseIncludes(self):
        DECLARATION_TYPES = (ast.Class, ast.Struct, ast.Enum, ast.Union)

        # Map header-filename: (#include AST node, module).
        included_files = {}
        # Map declaration-name: AST node.
        forward_declarations = {}
        for node in self.ast_list:
            # Ignore #include <> files.  Only handle #include "".
            # Assume that <> are used for only basic C/C++ headers.
            if isinstance(node, ast.Include) and not node.system:
                module = self._GetModule(node.filename)
                included_files[module.normalized_filename] = node, module
            if isinstance(node, DECLARATION_TYPES) and node.IsDeclaration():
                forward_declarations[node.FullName()] = node

        return included_files, forward_declarations

    def _VerifyIncludes(self, included_files):
        # Read and parse all the #include'd files and warn about really
        # stupid things that can be determined from the #include'd file name.
        files_seen = {}
        for filename, (node, module) in included_files.items():
            normalized_filename = module.normalized_filename
            if _IsCppFile(filename):
                msg = 'should not #include C++ source file: %s' % filename
                self._AddWarning(msg, node)
            if normalized_filename == self.normalized_filename:
                self._AddWarning('%s #includes itself' % filename, node)
            if normalized_filename in files_seen:
                include_node = files_seen[normalized_filename]
                line_num = self._GetLineNum(self.metrics, include_node)
                msg = '%s already #included on line %d' % (filename, line_num)
                self._AddWarning(msg, node)
            else:
                files_seen[normalized_filename] = node

    def _VerifyIncludeFilesUsed(self, file_uses, included_files):
        # Find all #include files that are unnecessary.
        for include_file, use in file_uses.items():
            if use != USES_DECLARATION:
                node, module = included_files[include_file]
                if module.ast_list is not None:
                    msg = module.filename + ' does not need to be #included'
                    if use == USES_REFERENCE:
                        msg += '.  Use references instead'
                    self._AddWarning(msg, node)

    def _VerifyForwardDeclarationsUsed(self, forward_declarations, decl_uses,
                                       file_uses):
        # Find all the forward declarations that are not used.
        for cls in forward_declarations:
            if decl_uses[cls] == UNUSED:
                node = forward_declarations[cls]
                if cls in file_uses:
                    msg = '%r forward declared, but needs to be #included' % cls
                else:
                    msg = '%r not used' % cls
                self._AddWarning(msg, node)

    def _DetermineUses(self, included_files, forward_declarations):
        # Setup the use type of each symbol.
        file_uses = dict.fromkeys(included_files, UNUSED)
        decl_uses = dict.fromkeys(forward_declarations, UNUSED)
        symbol_table = self.symbol_table

        def _AddReference(name, namespace):
            if name in decl_uses:
                decl_uses[name] |= USES_REFERENCE
            elif not None in namespace:
                # TODO(nnorwitz): make less hacky, do real name lookup.
                name = '::'.join(namespace) + '::' + name
                if name in decl_uses:
                    decl_uses[name] |= USES_REFERENCE

        def _AddUse(name, namespace):
            if isinstance(name, list):
                # name contains a list of tokens.
                name = '::'.join([n.name for n in name])
            elif not isinstance(name, str):
                # Happens when variables are defined with inlined types, e.g.:
                #   enum {...} variable;
                return
            try:
                file_use_node = symbol_table.LookupSymbol(name, namespace)
            except symbols.Error:
                # TODO(nnorwitz): symbols from the current module
                # should be added to the symbol table and then this
                # exception should not happen...unless the code relies
                # on another header for proper compilation.
                # Store the use since we might really need to #include it.
                file_uses[name] = file_uses.get(name, 0) | USES_DECLARATION
                return
            if not file_use_node:
                print('Could not find #include file for %s in %s' %
                      (name, namespace))
                return
            # TODO(nnorwitz): do proper check for ref/pointer/symbol.
            name = file_use_node[1].normalized_filename
            if name in file_uses:
                file_uses[name] |= USES_DECLARATION

        def _AddVariable(node, name, namespace):
            if not name:
                # Assume that all the types without names are builtin.
                return
            if node.reference or node.pointer:
                _AddReference(name, namespace)
            else:
                _AddUse(name, namespace)
            # This needs to recurse when the node is a templated type.
            for n in node.templated_types or ():
                _AddVariable(n, n.name, namespace)

        def _ProcessFunction(function):
            if function.return_type:
                return_type = function.return_type
                _AddVariable(return_type, return_type.name, function.namespace)
            templated_types = function.templated_types or ()
            for p in function.parameters:
                if p.type.name not in templated_types:
                    if function.body and p.name and p.type.name:
                        # Assume that if the the function has a body and a name
                        # the parameter type is really used.
                        # NOTE(nnorwitz): this is over-aggressive. It would be
                        # better to iterate through the body and determine
                        # actual uses based on local vars and data members used.
                        _AddUse(p.type.name, function.namespace)
                    else:
                        _AddVariable(p.type, p.type.name, function.namespace)

        def _ProcessFunctionBody(function, namespace):
            iterator = iter(function.body)
            for t in iterator:
                if t.token_type == tokenize.NAME:
                    if not keywords.IsKeyword(t.name):
                        # TODO(nnorwitz): handle :: names.
                        # TODO(nnorwitz): handle static function calls.
                        # TODO(nnorwitz): handle using statements in file.
                        # TODO(nnorwitz): handle using statements in function.
                        # TODO(nnorwitz): handle namespace assignment in file.
                        _AddUse(t.name, namespace)
                elif t.name in ('.', '->'):
                    # Skip tokens after a dereference.
                    next(iterator)

        def _AddTemplateUse(name, types, namespace):
            if types:
                for cls in types:
                    if name.endswith('_ptr'):
                        # Special case templated classes that end w/_ptr.
                        # These are things like auto_ptr which do
                        # not require the class definition, only decl.
                        _AddReference(cls.name, namespace)
                    else:
                        _AddUse(cls.name, namespace)
                    _AddTemplateUse(cls.name, cls.templated_types, namespace)

        # Iterate through the source AST/tokens, marking each symbols use.
        ast_seq = [self.ast_list]
        while ast_seq:
            for node in ast_seq.pop():
                if isinstance(node, ast.VariableDeclaration):
                    _AddVariable(node.type, node.type.name, node.namespace)
                    _AddTemplateUse(node.type.name,
                                    node.type.templated_types, node.namespace)
                elif isinstance(node, ast.Function):
                    _ProcessFunction(node)
                    if node.body:
                        _ProcessFunctionBody(node, node.namespace)
                elif isinstance(node, ast.Typedef):
                    alias = node.alias
                    if isinstance(alias, ast.Type):
                        _AddUse(alias.name, node.namespace)
                        _AddTemplateUse('<typedef>', alias.templated_types,
                                        node.namespace)
                elif isinstance(node, ast.Friend):
                    if node.expr and node.expr[0].name == 'class':
                        name = ''.join([n.name for n in node.expr[1:]])
                        _AddReference(name, node.namespace)
                elif isinstance(node, ast.Class) and node.body is not None:
                    if node.body:
                        ast_seq.append(node.body)
                    _AddTemplateUse('', node.bases, node.namespace)
                elif isinstance(node, ast.Struct) and node.body is not None:
                    pass  # TODO(nnorwitz): impl
                elif isinstance(node, ast.Union) and node.fields:
                    pass  # TODO(nnorwitz): impl

        return file_uses, decl_uses

    def _FindUnusedWarnings(self):
        included_files, forward_declarations = self._ReadAndParseIncludes()
        file_uses, decl_uses = \
            self._DetermineUses(included_files, forward_declarations)
        self._VerifyIncludes(included_files)
        self._VerifyIncludeFilesUsed(file_uses, included_files)
        self._VerifyForwardDeclarationsUsed(forward_declarations, decl_uses,
                                            file_uses)

    def _FindHeaderWarnings(self):
        self._FindUnusedWarnings()
        # TODO(nnorwitz): other warnings to add:
        #   * too much non-template impl in header file
        #   * too many methods/data members
        #   * missing include for classes used for inheritenace

    def _FindPublicFunctionWarnings(self, node, name, primary_header,
                                    public_symbols, all_headers):
        # Not found in the primary header, search all other headers.
        for header_node, header in all_headers.values():
            if name in header.public_symbols:
                # If the primary.filename == header.filename, it probably
                # indicates an error elsewhere.  It sucks to mask it,
                # but false positives are worse.
                if (primary_header and
                    primary_header.filename != header.filename):
                    msg = ('expected to find %s in %s, but found in %s' %
                           (name, primary_header.filename, header.filename))
                    self._AddWarning(msg, node)
                break
        else:
            where = 'in any directly #included header'
            if primary_header:
                where = ('in expected header ' + primary_header.filename +
                         ' or any other directly #included header')
            self._AddWarning('%s not found %s' % (name, where), node)

    def _CheckPublicFunctions(self, primary_header, all_headers):
        # Verify all the public functions are also declared in a header file.
        public_symbols = ()
        declared_only_symbols = {}
        if primary_header:
            public_symbols = {}
            for name, symbol in primary_header.public_symbols.items():
                if isinstance(symbol, ast.Function):
                    public_symbols[name] = symbol
            declared_only_symbols = dict.fromkeys(public_symbols, True)

        using_values = []
        for node in self.ast_list:
            if isinstance(node, ast.Using):
                using_values.append(node)

            # Make sure we have a function that should be exported.
            if not isinstance(node, ast.Function):
                continue
            if isinstance(node, ast.Method):
                # Ensure that for Foo::Bar, Foo is *not* a namespace.
                # If Foo is a namespace, we have a function and not a method.
                names = [n.name for n in node.in_class]
                if names != self.symbol_table.GetNamespace(names):
                    continue
            if not (node.IsDefinition() and node.IsExportable()):
                continue

            # TODO(nnorwitz): need to handle using statements.

            # This function should be declared in a header file.
            name = node.name
            if name in public_symbols:
                declared_only_symbols[name] = False
            else:
                self._FindPublicFunctionWarnings(node, name, primary_header,
                                                 public_symbols, all_headers)

        for name, declared_only in declared_only_symbols.items():
            if declared_only:
                # TODO(nnorwitz): shouldn't warn if function is templatized.
                node = public_symbols[name]
                msg = '%s declared but not defined' % name
                self._AddWarning(msg, node, primary_header.filename)

    def _GetPrimaryHeader(self, included_files):
        basename = os.path.splitext(self.normalized_filename)[0]
        primary_header = included_files.get(basename + PRIMARY_HEADER_EXTENSION)
        if not primary_header:
            primary_header = included_files.get(basename)
        if primary_header:
            return primary_header[1]
        return None

    def _FindSourceWarnings(self):
        included_files, forward_declarations = self._ReadAndParseIncludes()
        if forward_declarations:
            # TODO(nnorwitz): This really isn't a problem, but might
            # be something to warn against.  I expect this will either
            # be configurable or removed in the future.  But it's easy
            # to check for now.
            msg = 'forward declarations not expected in source file'
            self._AddWarning(msg, next(forward_declarations.values()))

        # A primary header is optional.  However, when looking up
        # defined methods in the source, always look in the
        # primary_header first.  Expect that is the most likely location.
        # Use of primary_header is primarily an optimization.
        primary_header = self._GetPrimaryHeader(included_files)
        if not primary_header:
            # TODO(nnorwitz): This shouldn't always be a warning.
            # For example, *main.cc shouldn't need a header.  But
            # almost all other source files should have a
            # corresponding header.
            msg = 'unable to find header file with matching name'
            self._AddWarning(msg, self.ast_list[0])

        self._CheckPublicFunctions(primary_header, included_files)

        # TODO(nnorwitz): other warnings to add:
        #   * unused forward decls for variables (globals)/classes
        #   * Functions that are too large/complex
        #   * Variables declared far from first use
        #   * primitive member variables not initialized in ctor


def main(argv):
    for filename in argv[1:]:
        source = utils.ReadFile(filename)
        if source is None:
            continue

        print('Processing %s' % filename)
        builder = ast.BuilderFromSource(source, filename)
        entire_ast = list(filter(None, builder.Generate()))
        hunter = WarningHunter(filename, source, entire_ast)
        hunter.FindWarnings()
        hunter.ShowWarnings()


if __name__ == '__main__':
    main(sys.argv)
