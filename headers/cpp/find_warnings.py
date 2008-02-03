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


import os
import sys

from cpp import ast
from cpp import headers
from cpp import metrics
from cpp import tokenize
from cpp import utils


class Module(object):
    """Data container represting a single source file."""

    def __init__(self, filename, ast_list):
        self.filename = filename
        self.ast_list = ast_list
        self.public_symbols = self._GetExportedSymbols()

    def _GetExportedSymbols(self):
        if not self.ast_list:
            return {}
        return dict((n.name, n) for n in self.ast_list if n.IsExportable())

    def IsAnyPublicSymbolUsed(self, ast_list):
        """Returns a bool whether any token in ast_list uses this module."""
        def _IsSymbolUsed(symbol):
            # TODO(nnorwitz): this doesn't handle namespaces properly.
            for node in ast_list:
                if node.Requires(symbol):
                    return True
            return False

        # Special case when we don't know the answer.  Assume it's ok.
        if self.ast_list is None:
            return True

        for symbol in self.public_symbols.itervalues():
            if _IsSymbolUsed(symbol):
                return True
        return False


def _IsHeaderFile(filename):
    base, ext = os.path.splitext(filename)
    return ext.lower() in ('.h', '.hpp', '.h++')


def _IsCppFile(filename):
    base, ext = os.path.splitext(filename)
    return ext.lower() in ('.c', '.cc', '.cpp', '.c++')


class WarningHunter(object):

    # Cache filename: ast_list
    _module_cache = {}

    def __init__(self, filename, source, ast_list):
        self.filename = filename
        self.source = source
        self.ast_list = ast_list

        self.metrics = metrics.Metrics(source)
        self.warnings = []
        if filename not in self._module_cache:
            self._module_cache[filename] = Module(filename, ast_list)
        else:
            print 'Warning', filename, 'already in cache'

    def _AddWarning(self, msg, node, filename=None):
        source = self.metrics
        if filename is not None:
            source = metrics.Metrics(open(filename).read())
        else:
            filename = self.filename
        line_num = source.GetLineNumber(node.start)
        self.warnings.append((filename, line_num, msg))

    def ShowWarnings(self):
        self.warnings.sort()
        for filename, line_num, msg in self.warnings:
            print '%s:%d: %s' % (filename, line_num, msg)

    def FindWarnings(self):
        # print 'Searching for warnings in:', self.filename
        if _IsHeaderFile(self.filename):
            self._FindHeaderWarnings()
        elif _IsCppFile(self.filename):
            self._FindSourceWarnings()
        else:
            print 'Unknown filetype for: %s' % self.filename

    def _GetHeaderFile(self, filename):
        if filename in self._module_cache:
            return self._module_cache[filename]

        module = Module(filename, None)
        source, actual_filename = headers.ReadSource(filename)
        if source is None:
            print 'Unable to find', filename
        else:
            builder = ast.BuilderFromSource(source, filename)
            try:
                module = Module(filename, filter(None, builder.Generate()))
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                print 'Exception while processing', filename
        self._module_cache[filename] = module
        return module

    def _GetForwardDeclarations(self):
        # Map header-filename: (#include AST node, ast_list_for_file)
        included_files = {}
        # Find all the forward declared types.
        # TODO(nnorwitz): Need to handle structs too.
        forward_declared_classes = {}
        for node in self.ast_list:
            if isinstance(node, ast.Class) and node.IsDeclaration():
                forward_declared_classes[node.FullName()] = node
            if isinstance(node, ast.Include) and not node.system:
                module = self._GetHeaderFile(node.filename)
                included_files[node.filename] = node, module

        return forward_declared_classes, included_files

    def _GetClassesUsed(self):
        def _ProcessFunction(function):
            if function.return_type:
                classes_used[function.return_type[0].name] = True
            # TODO(nnorwitz): ignoring the body for now.
            for p in ast._SequenceToParameters(function.parameters):
                classes_used[p.type_name] = True

        def _ProcessTypedef(typedef):
            for token in typedef.alias:
                if (isinstance(token, tokenize.Token) and
                    token.token_type == tokenize.NAME):
                    classes_used[token.name] = True
                elif isinstance(token, ast.Struct):
                    pass                # TODO(nnorwitz): impl
                elif isinstance(token, ast.Union):
                    pass                # TODO(nnorwitz): impl

        # TODO(nnorwitz): this needs to be recursive.
        classes_used = {}
        for node in self.ast_list:
            if isinstance(node, ast.VariableDeclaration):
                classes_used[node.type_name] = True
            elif isinstance(node, ast.Function):
                _ProcessFunction(node)
            elif isinstance(node, ast.Typedef):
                _ProcessTypedef(node)
            elif isinstance(node, ast.Class) and node.body:
                for node in node.body:
                    if (isinstance(node, ast.Function) and
                        not (node.modifiers & ast.FUNCTION_DTOR)):
                        _ProcessFunction(node)
                    if isinstance(node, ast.VariableDeclaration):
                        classes_used[node.type_name] = True
        return classes_used

    def _FindUnusedWarnings(self):
        # NOTE(nnorwitz): this could be sped up by iterating over the
        # file's AST and finding which symbols are used.  Then iterate
        # over each header file and see if any of the symbols are used.
        #
        # This is how this method should be implemented:
        # Read all the #includes and store them in parsed form.
        # Keep a dict of all public identifiers from each #include
        # Iterate through the source AST/tokens.
        # For each initial token (ignore ->tokens), find the header
        # that referenced it and mark in that header.  If no header, bitch.

        # Finally, iterate over all the headers.  For each one that
        # has no markings of being used, bitch.

        forward_declarations, included_files = self._GetForwardDeclarations()
        classes_used = self._GetClassesUsed()

        # Find all the forward declarations that are not used.
        for cls in forward_declarations:
            if cls not in classes_used:
                node = forward_declarations[cls]
                self._AddWarning('%r not used' % cls, node)

        # Find all the header files that are not used.
        for node, module in included_files.values():
            if _IsCppFile(module.filename):
                msg = ('should not include C++ source files: %s' %
                       module.filename)
                self._AddWarning(msg, node)
            if node.filename == self.filename:
                self._AddWarning('%s includes itself' % node.filename, node)
            if not module.IsAnyPublicSymbolUsed(self.ast_list):
                msg = '%s does not need to be #included' % node.filename
                self._AddWarning(msg, node)

    def _FindHeaderWarnings(self):
        self._FindUnusedWarnings()
        # TODO(nnorwitz): other warnings to add:
        #   * when a symbol is used, check if it is used as a pointer
        #     and can be forward declared rather than #include'ing the
        #     header file.  This only applies to header files until we
        #     track all variable accesses/derefs.
        #   * too much non-template impl in header file

    def _FindPublicFunctionWarnings(self, node, name, primary_header,
                                    public_symbols, all_headers):
        # Not found in the primary header, search all other headers.
        for header_node, header in all_headers.itervalues():
            if name in header.public_symbols:
                if primary_header:
                    msg = ('expected to find %s in %s, but found in %s' %
                           (name, primary_header.filename, header.filename))
                    self._AddWarning(msg, node)
                break
        else:
            where = 'in any directly included header'
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
            for name, symbol in primary_header.public_symbols.iteritems():
                if isinstance(symbol, ast.Function):
                    public_symbols[name] = symbol
            declared_only_symbols = dict.fromkeys(public_symbols, True)

        for node in self.ast_list:
            # Make sure we have a function that should be exported.
            if not isinstance(node, ast.Function):
                continue
            if isinstance(node, ast.Method):
                continue
            if not (node.IsDefinition() and node.IsExportable()):
                continue

            # This function should be declared in a header file.
            name = node.name
            if name in public_symbols:
                declared_only_symbols[name] = False
            else:
                self._FindPublicFunctionWarnings(node, name, primary_header,
                                                 public_symbols, all_headers)

        for name, declared_only in declared_only_symbols.iteritems():
            if declared_only:
                # TODO(nnorwitz): shouldn't warn if function is templatized.
                node = public_symbols[name]
                msg = '%s declared but not defined' % name
                self._AddWarning(msg, node, primary_header.filename)

    def _GetPrimaryHeader(self, included_files):
        basename = os.path.splitext(self.filename)[0]
        primary_header = included_files.get(basename + '.h')
        if not primary_header:
            primary_header = included_files.get(basename)
        if primary_header:
            return primary_header[1]
        return None

    def _FindSourceWarnings(self):
        forward_declarations, included_files = self._GetForwardDeclarations()
        if forward_declarations:
            # TODO(nnorwitz): This really isn't a problem, but might
            # be something to warn against.  I expect this will either
            # be configurable or removed in the future.  But it's easy
            # to check for now.
            msg = 'forward declarations not expected in source file'
            self._AddWarning(msg, self.ast_list[0])

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


def main(argv):
    for filename in argv[1:]:
        source = utils.ReadFile(filename)
        if source is None:
            continue

        print 'Processing', filename
        builder = ast.BuilderFromSource(source, filename)
        entire_ast = filter(None, builder.Generate())
        hunter = WarningHunter(filename, source, entire_ast)
        hunter.FindWarnings()
        hunter.ShowWarnings()


if __name__ == '__main__':
    main(sys.argv)
