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

import sys

import MySQLdb

from cpp import ast
from cpp import keywords
from cpp import tokenize
from cpp import utils

_DB_HOST = 'localhost'
_DB_USER = 'neal'
_DB_PASSWD = ''
_DB_NAME = 'cppclean'


class FileInserter(object):
    def __init__(self, filename, source, tokens, entire_ast):
        self.filename = filename
        self.source = source
        self.tokens = tokens
        self.entire_ast = entire_ast

    def _GetAllNames(self, dbc, table):
        dbc.execute('SELECT id, name FROM ' + table)
        result = dbc.fetchall()
        names = {}
        for id, name in result:
            names[name] = id
        return names

    def _GetDbIdentifiers(self, dbc):
        return self._GetAllNames(dbc, 'identifier')

    def _GetDbPaths(self, dbc):
        return self._GetAllNames(dbc, 'path')

    def _GetAstIdentifiers(self):
        identifiers = {}
        for token_type, name, start, end in self.tokens:
            if (token_type == tokenize.NAME and not keywords.IsKeyword(name)):
                identifiers[name] = 1
        return identifiers

    def Write(self, db):
        ast_identifiers = self._GetAstIdentifiers()

        dbc = db.cursor()
        identifiers = self._GetDbIdentifiers(dbc)
        paths = self._GetDbPaths(dbc)
        if self.filename not in paths:
            dbc.execute('INSERT INTO path(name) VALUES (%s)', self.filename)
            paths[self.filename] = dbc.lastrowid

        new_names = list(set(ast_identifiers) - set(identifiers))
        print 'new', new_names
        result = dbc.executemany('INSERT INTO identifier(name) VALUES (%s)',
                                 new_names)
        print result
        
        dbc.close()
        print paths
        print identifiers


def main(argv):
    db = MySQLdb.connect(host=_DB_HOST, user=_DB_USER, passwd=_DB_PASSWD,
                         db=_DB_NAME)
    for filename in argv[1:]:
        source = utils.ReadFile(filename)
        if source is None:
            continue

        print 'Processing', filename
        tokens = list(tokenize.GetTokens(source))
        builder = ast.AstBuilder(iter(tokens), source)
        entire_ast = filter(None, builder.Generate())
        inserter = FileInserter(filename, source, tokens, entire_ast)
        inserter.Write(db)


if __name__ == '__main__':
    main(sys.argv)
