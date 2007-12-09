#!/usr/bin/env python

"""Find warnings for C++ code."""

import os
import sys

from cpp import ast
from cpp import headers
from cpp import utils


class Module(object):
    def __init__(self, ast_list):
        self.ast_list = ast_list
        self.public_symbols = self._GetExportedSymbols()

    def _GetExportedSymbols(self):
        if not self.ast_list:
            return []
        return [node for node in self.ast_list if node.IsDefinition()]

    def IsAnyPublicSymbolUsed(self, ast_list):
        def _IsSymbolUsed(symbol):
            # TODO(nnorwitz): this doesn't handle namespaces properly.
            for node in ast_list:
                if node.Requires(symbol):
                    return True
            return False

        for symbol in self.public_symbols:
            if _IsSymbolUsed(symbol):
                return True
        return False


class WarningsHunter(object):

    # Cache filename: ast_list
    _module_cache = {}

    def __init__(self, filename, source, ast_list):
        self.filename = filename
        self.source = source
        self.ast_list = ast_list
        self.warnings = []
        if filename not in self._module_cache:
            self._module_cache[filename] = Module(ast_list)
        else:
            print 'Warning', filename, 'already in cache'

    def _GetLineNumber(self, start):
        return 1 + self.source.count('\n', 0, start)

    def _AddWarning(self, msg, ast):
        line_num = self._GetLineNumber(ast.start)
        self.warnings.append((line_num, msg))

    def ShowWarnings(self):
        self.warnings.sort()
        for line_num, msg in self.warnings:
            print '%s:%d: %s' % (self.filename, line_num, msg)

    def FindWarnings(self):
        # print 'Searching for warnings in:', self.filename
        base, ext = os.path.splitext(self.filename)
        if ext.lower() in ('.h', '.hpp'):
            self._FindHeaderWarnings()
        elif ext.lower() in ('.c', '.cc', '.cpp', '.c++'):
            self._FindSourceWarnings()
        else:
            print 'Unknown filetype (%s) for: %s' % (ext, self.filename)

    def _GetHeaderFile(self, filename):
        if filename in self._module_cache:
            return self._module_cache[filename]

        module = Module(None)
        source, actual_filename = headers.ReadSource(filename)
        if source is None:
            print 'Unable to find', filename
        else:
            builder = ast.BuilderFromSource(source)
            try:
                module = Module(filter(None, builder.Generate()))
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
            if node.IsDeclaration():
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

        # TODO(nnorwitz): this needs to be recursive.
        classes_used = {}
        for node in self.ast_list:
            if isinstance(node, ast.VariableDeclaration):
                classes_used[node.type_name] = True
            elif isinstance(node, ast.Function):
                _ProcessFunction(node)
            elif isinstance(node, ast.Class) and node.body:
                for node in node.body:
                    if (isinstance(node, ast.Function) and
                        not (node.modifiers & ast.FUNCTION_DTOR)):
                        _ProcessFunction(node)
                    if isinstance(node, ast.VariableDeclaration):
                        classes_used[node.type_name] = True
        return classes_used

    def _FindHeaderWarnings(self):
        forward_declarations, included_files = self._GetForwardDeclarations()
        classes_used = self._GetClassesUsed()

        # Find all the forward declarations that are not used.
        for cls in forward_declarations:
            if cls not in classes_used:
                node = forward_declarations[cls]
                self._AddWarning('%r not used' % cls, node)

        # TODO(nnorwitz): when a symbol is used, check if it is used
        # as a pointer and can be forward declared rather than
        # #include'ing the header file.

        # Find all the header files that are not used.
        # NOTE(nnorwitz): this could be sped up by iterating over the
        # file's AST and finding which symbols are used.  Then iterate
        # over each header file and see if any of the symbols are used.
        for node, module in included_files.values():
            if not module.IsAnyPublicSymbolUsed(self.ast_list):
                msg = '%s does not need to be #included' % node.filename
                self._AddWarning(msg, node)

    def _FindSourceWarnings(self):
        # Read all the #includes and store them in parsed form.
        # Keep a dict of all public identifiers from each #include
        # Iterate through the source AST/tokens.
        # For each initial token (ignore ->tokens), find the header
        # that referenced it and mark in that header.  If no header, bitch.

        # Finally, iterate over all the headers.  For each one that
        # has no markings of being used, bitch.
        pass


def main(argv):
    for filename in argv[1:]:
        source = utils.ReadFile(filename)
        if source is None:
            continue

        print 'Processing', filename
        builder = ast.BuilderFromSource(source)
        entire_ast = filter(None, builder.Generate())
        hunter = WarningsHunter(filename, source, entire_ast)
        hunter.FindWarnings()
        hunter.ShowWarnings()


if __name__ == '__main__':
    main(sys.argv)
