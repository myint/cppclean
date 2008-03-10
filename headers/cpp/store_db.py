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

"""Store the parse tree (AST) from C++ source in MySQL."""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


import os
import sys

import MySQLdb

from cpp import ast
from cpp import keywords
from cpp import metrics
from cpp import tokenize
from cpp import utils

_DB_HOST = 'localhost'
_DB_USER = 'neal'
_DB_PASSWD = ''
_DB_NAME = 'cppclean'

_NO_NAMESPACE = '<no-namespace>'
_UNKNOWN = '<unknown>'


class _Reference(object):
    """Data container for all columns in each DB table.

    i.e., any Declaration, Definition, or Use table.
    """

    def __init__(self, filename, line):
        self.filename = filename
        self.line = line

    def AsTuple(self):
        """Returns a tuple that can be used to store the values in a DB."""
        raise NotImplementedError


class _Declaration(_Reference):
    """Data container for all columns in each _decl DB table."""

    def __init__(self, name, namespace, filename, line):
        _Reference.__init__(self, filename, line)
        self.name = name
        self.namespace = namespace
        self.deleted = False

    def AsTuple(self):
        return self.name, self.namespace, self.filename, self.line, self.deleted


class TypedefDeclaration(_Declaration):
    pass


class EnumDeclaration(_Declaration):
    pass


class GlobalVariableDeclaration(_Declaration):
    pass


class FunctionDeclaration(_Declaration):
    def __init__(self, name, namespace, modifiers, num_parameters,
                 filename, line):
        _Declaration.__init__(self, name, namespace, filename, line)
        self.modifiers = modifiers
        self.num_parameters = num_parameters

    def AsTuple(self):
        return (self.name, self.namespace, self.modifiers, self.num_parameters,
                self.filename, self.line, self.deleted)


class ClassDeclaration(_Declaration):
    pass


class _MemberDeclaration(_Reference):
    """Data container for columns in _decl DB tables defined within a class."""

    def __init__(self, name, class_, filename, line):
        _Reference.__init__(self, filename, line)
        self.name = name
        self.class_ = class_
        self.deleted = False


class FieldDeclaration(_MemberDeclaration):
    def __init__(self, name, class_, modifiers, filename, line):
        _MemberDeclaration.__init__(self, name, class_, filename, line)
        self.modifiers = modifiers

    def AsTuple(self):
        return (self.name, self.class_, self.modifiers,
                self.filename, self.line, self.deleted)


class MethodDeclaration(_MemberDeclaration):
    def __init__(self, name, class_, modifiers, num_parameters, filename, line):
        _MemberDeclaration.__init__(self, name, class_, filename, line)
        self.modifiers = modifiers
        self.num_parameters = num_parameters

    def AsTuple(self):
        return (self.name, self.class_, self.modifiers, self.num_parameters,
                self.filename, self.line, self.deleted)


class _Definition(_Reference):
    """Data container for all columns in each *_definition DB table."""

    def __init__(self, declaration, num_lines, complexity, filename, line):
        _Reference.__init__(self, filename, line)
        self.declaration = declaration
        self.num_lines = num_lines
        self.complexity = complexity

    def AsTuple(self):
        return (self.declaration, self.num_lines, self.complexity,
                self.filename, self.line)


class FunctionDefinition(_Definition):
    pass


class MethodDefinition(_Definition):
    pass


def AsTuples(seq):
    """Convert a sequence of References to a sequence of tuples.

    The sequence of tuples can be used to insert many into the DB.

    Args:
      seq - sequence of _References

    Yields:
      each item in the sequence as a tuple
    """
    for item in seq:
        yield item.AsTuple()


class ParsedSource(object):
    def __init__(self, filename, source, tokens, entire_ast):
        self.filename = filename
        self.source = source
        self.tokens = tokens
        self.entire_ast = entire_ast

        # TODO(nnorwitz): handle function/method overloading (ie, no dups).
        self.typedef_declarations = []
        self.enum_declarations = []
        self.global_variable_declarations = []
        self.function_declarations = []
        self.class_declarations = []
        self.field_declarations = []
        self.method_declarations = []

        self.function_definitions = []
        self.method_definitions = []

    def _UpdateReferences(self, file_index, identifiers):
        """Iterates through the AST storing all reference info.

        i.e., Store the declarations, definitions, and uses.
        """
        for node in self.entire_ast.Generate():
            if isinstance(node, ast.Typedef):
                name = identifiers[node.name]
                namespace = identifiers[node.namespace or _NO_NAMESPACE]
                line = metrics.GetLineNumber(node.start)
                decl = TypedefDeclaration(name, namespace, file_index, line)
                self.typedef_declarations.append(decl)

            elif isinstance(node, ast.Enum):
                name = identifiers[node.name]
                namespace = identifiers[node.namespace or _NO_NAMESPACE]
                line = metrics.GetLineNumber(node.start)
                decl = EnumDeclaration(name, namespace, file_index, line)
                self.enum_declarations.append(decl)

            elif isinstance(node, ast.VariableDeclaration):
                name = identifiers[node.name]
                line = metrics.GetLineNumber(node.start)
                if not node.type_name:
                    # Handle global variables.
                    namespace = identifiers[node.namespace or _NO_NAMESPACE]
                    decl = GlobalVariableDeclaration(name, namespace,
                                                     file_index, line)
                    self.global_variable_declarations.append(decl)
                else:
                    # Handle fields (data members).
                    class_ = 1  # TODO(nnorwitz): get class decl reference.
                    modifiers = node.type_modifiers
                    decl = FieldDeclaration(name, class_, modifiers,
                                            file_index, line)
                    self.field_declarations.append(decl)

            elif isinstance(node, ast.Function):
                # TODO(nnorwitz): need to update AST for functions to contain
                # class information.  Then store methods here too.
                line = metrics.GetLineNumber(node.start)
                if node.body:
                    name = identifiers[node.name]
                    namespace = identifiers[node.namespace or _NO_NAMESPACE]
                    decl = FunctionDeclaration(name, namespace, node.modifiers,
                               len(node.parameters), file_index, line)
                    self.function_declarations.append(decl)
                else:
                    decl = 1  # TODO(nnorwitz): get decl
                    definition = FunctionDefinition(decl, None, None,
                                                    file_index, line)
                    self.function_definitions.append(definition)

            elif isinstance(node, ast.Class) and node.body:
                name = identifiers[node.name]
                namespace = identifiers[node.namespace or _NO_NAMESPACE]
                line = metrics.GetLineNumber(node.start)
                decl = ClassDeclaration(name, namespace, file_index, line)
                self.class_declarations.append(decl)

    def Write(self, db, paths, identifiers):
        file_index = paths[self.filename]
        self._UpdateReferences(file_index, identifiers)

        dbc = db.cursor()
        """This should be executed as a single big transaction.  This will
        keep the DB in a mostly consistent state.  I don't think there is
        a race condition, but I need to think about this more.

        The same file should not be processed simultaneously.

        // All the *_uses tables are currently unused.
        DELETE FROM typedef_uses WHERE filename = %s
        DELETE FROM enum_uses WHERE filename = %s
        DELETE FROM global_variable_uses WHERE filename = %s
        DELETE FROM function_uses WHERE filename = %s
        DELETE FROM class_uses WHERE filename = %s
        DELETE FROM field_uses WHERE filename = %s
        DELETE FROM method_uses WHERE filename = %s
        """

        self.UpdateTypedefs(dbc)
        self.UpdateEnums(dbc)
        self.UpdateGlobalVariables(dbc)
        self.UpdateFunctions(dbc)
        self.UpdateClasses(dbc)
        self.UpdateFields(dbc)
        self.UpdateMethods(dbc)
        self.UpdateFunctionDefinitions(dbc)
        self.UpdateMethodDefinitions(dbc)

        dbc.close()
        # TODO(nnorwitz): should we do a GC phase after updating?
        # Probably since it will keep the actual garbage small.

    def UpdateTypedefs(self, dbc):
        # UPDATE typedef_decl SET deleted = TRUE WHERE filename = %s
        sql = ('INSERT INTO typedef_decl(name, namespace, filename, line)'
               ' VALUES %s')
        dbc.executemany(sql, AsTuples(self.typedef_declarations))

    def UpdateEnums(self, dbc):
        # UPDATE enum_decl SET deleted = TRUE WHERE filename = %s
        sql = ('INSERT INTO enum_decl(name, namespace, filename, line)'
               ' VALUES %s')
        dbc.executemany(sql, AsTuples(self.enum_declarations))

    def UpdateGlobalVariables(self, dbc):
        # UPDATE global_variable_decl SET deleted = TRUE WHERE filename = %s
        sql = ('INSERT INTO'
               ' global_variable_decl(name, namespace, filename, line)'
               ' VALUES %s')
        dbc.executemany(sql, AsTuples(self.global_variable_declarations))

    def UpdateFunctions(self, dbc):
        # UPDATE function_decl SET deleted = TRUE WHERE filename = %s
        sql = ('INSERT INTO'
               ' function_decl(name, namespace, modifiers, num_parameters,'
               '               filename, line) VALUES %s')
        dbc.executemany(sql, AsTuples(self.function_declarations))

    def UpdateClasses(self, dbc):
        # UPDATE class_decl SET deleted = TRUE WHERE filename = %s
        sql = ('INSERT INTO class_decl(name, namespace, filename, line)'
               ' VALUES %s')
        dbc.executemany(sql, AsTuples(self.class_declarations))

    def UpdateFields(self, dbc):
        # UPDATE field_decl SET deleted = TRUE WHERE filename = %s
        sql = ('INSERT INTO'
               ' field_decl(name, namespace, modifiers, filename, line)'
               ' VALUES %s')
        dbc.executemany(sql, AsTuples(self.field_declarations))

    def UpdateMethods(self, dbc):
        # UPDATE method_decl SET deleted = TRUE WHERE filename = %s
        sql = ('INSERT INTO'
               ' method_decl(name, class, modifiers, num_parameters,'
               '             filename, line) VALUES %s')
        dbc.executemany(sql, AsTuples(self.method_declarations))

    def UpdateFunctionDefinitions(self, dbc):
        # DELETE FROM function_definition WHERE filename = %s
        sql = ('INSERT INTO'
               ' function_definition(declaration, num_lines, complexity,'
               '                     filename, line) VALUES %s')
        dbc.executemany(sql, AsTuples(self.function_definitions))

    def UpdateMethodDefinitions(self, dbc):
        # DELETE FROM method_definition WHERE filename = %s
        sql = ('INSERT INTO'
               ' method_definition(declaration, num_lines, complexity,'
               '                   filename, line) VALUES %s')
        dbc.executemany(sql, AsTuples(self.method_definitions))


class SourceRevision(object):
    def __init__(self):
        self.parse_trees = {}
        self.paths = {}
        self.identifiers = {}

    def Add(self, path, source, tokens, ast_nodes):
        self.parse_trees[path] = ParsedSource(path, source, tokens, ast_nodes)

    def _GetAllNames(self, dbc, table):
        dbc.execute('SELECT id, name FROM ' + table)
        result = dbc.fetchall()
        names = {}
        for id, name in result:
            names[name] = id
        return names

    def _GetAstIdentifiers(self):
        identifiers = {}
        for parse_tree in self.parse_trees.itervalues():
            for token_type, name, start, end in parse_tree.tokens:
                if token_type == tokenize.NAME and not keywords.IsKeyword(name):
                    identifiers[name] = 1
        return identifiers

    def UpdatePathsAndIdentifiers(self, db):
        ast_identifiers = self._GetAstIdentifiers()

        dbc = db.cursor()
        self.paths = paths = self._GetDbPaths(dbc, 'path')
        new_files = [p for p in self.parse_trees if p not in paths]
        if new_files:
            sql = 'INSERT INTO path(name) VALUES (%s)'
            dbc.executemany(sql, new_files)
            self.paths = self._GetDbPaths(dbc)

        self.identifiers = identifiers = self._GetAllNames(dbc, 'identifier')
        new_names = list(set(ast_identifiers) - set(identifiers))
        if new_names:
            sql = 'INSERT INTO identifier(name) VALUES (%s)'
            dbc.executemany(sql, new_names)
            self.identifiers = self._GetAllNames(dbc, 'identifier')

        dbc.close()
        print self.paths
        print self.identifiers

    def GetParseTrees(self):
        # TODO(nnorwitz): return these in-order, depth-first.
        # Need to handle all headers, then inlines, then cc files (more/less).

        # For now it should be sufficient to return headers, then cc files.
        values = []
        for value in self.parse_trees.itervalues():
            name, ext = os.path.splitext(value.filename)
            values.append((ext, name, value))
        values.sort(reverse=True)
        return [value for ext, name, value in values]


def main(argv):
    db = MySQLdb.connect(host=_DB_HOST, user=_DB_USER, passwd=_DB_PASSWD,
                         db=_DB_NAME)
    changelist = SourceRevision()
    # Parse all the files and get all the tokens.
    for filename in argv[1:]:
        source = utils.ReadFile(filename)
        if source is None:
            continue

        print 'Processing', filename
        tokens = list(tokenize.GetTokens(source))
        builder = ast.AstBuilder(iter(tokens), source)
        entire_ast = filter(None, builder.Generate())
        changelist.Add(filename, source, tokens, entire_ast)

    # Before storing details about each file, store the new identifiers
    # and paths.  This makes it easy to reference these.  Since they
    # are write-once and not modified, this saves DB work and does not
    # introduce any race conditions.
    changelist.UpdatePathsAndIdentifiers(db)

    # For each file, write it the parse tree to the DB.
    for parsed_source in changelist.GetParseTrees():
        parsed_source.Write(db, changelist.paths, changelist.identifiers)


if __name__ == '__main__':
    main(sys.argv)
