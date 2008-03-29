#!/usr/bin/env python
#
# Copyright 2008 Neal Norwitz
# Portions Copyright 2008 Google Inc.
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

"""AST test."""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


from test import test_support
import unittest

from cpp import ast
from cpp import tokenize


def _InstallGenericEqual(cls, attrs):
    """Add an __eq__ method to |cls| so objects can be compared for tests.

    Args:
      cls: Python class to add __eq__ method to
      attrs: string - space separated of attribute names to compare
    """
    attrs = attrs.split()
    def __eq__(self, other):
        if not isinstance(other, cls):
            return False
        for a in attrs:
            if getattr(self, a) != getattr(other, a):
                return False
        return True
    cls.__eq__ = __eq__


def _InstallEqualMethods():
    """Install __eq__ methods on the appropriate objects used for testing."""
    _InstallGenericEqual(ast.Class, 'name bases templated_types')
_InstallEqualMethods()


def MakeBuilder(code_string):
    """Convenience function to make an AstBuilder from a code snippet.."""
    tokens = list(tokenize.GetTokens(code_string + '\n'))
    return ast.AstBuilder(tokens, '<test>')


def Class(name, start=0, end=0, bases=None, body=None, templated_types=None,
          namespace=()):
    return ast.Class(start, end, name, bases, templated_types, body, namespace)


class AstBuilder_ConvertBaseTokensToAstTest(unittest.TestCase):

    def testSimple(self):
        builder = MakeBuilder('Bar')
        result = builder._ConvertBaseTokensToAST(builder.tokens)
        self.assertEqual(1, len(result))
        self.assertEqual(Class('Bar'), result[0])

    def testTemplate(self):
        builder = MakeBuilder('Bar<Foo>')
        result = builder._ConvertBaseTokensToAST(builder.tokens)
        self.assertEqual(1, len(result))
        self.assertEqual(Class('Bar', templated_types=[Class('Foo')]),
                         result[0])

    def testTemplateWithMultipleArgs(self):
        builder = MakeBuilder('Bar<Foo, Blah, Bling>')
        result = builder._ConvertBaseTokensToAST(builder.tokens)
        self.assertEqual(1, len(result))
        types = [Class('Foo'), Class('Blah'), Class('Bling')]
        self.assertEqual(Class('Bar', templated_types=types), result[0])

    def testTemplateWithMultipleTemplateArgsStart(self):
        builder = MakeBuilder('Bar<Foo<x>, Blah, Bling>')
        result = builder._ConvertBaseTokensToAST(builder.tokens)
        self.assertEqual(1, len(result))
        types = [Class('Foo', templated_types=[Class('x')]),
                 Class('Blah'),
                 Class('Bling')]
        self.assertEqual(types[0], result[0].templated_types[0])
        self.assertEqual(types[1], result[0].templated_types[1])
        self.assertEqual(types[2], result[0].templated_types[2])
        self.assertEqual(Class('Bar', templated_types=types), result[0])

    def testTemplateWithMultipleTemplateArgsMid(self):
        builder = MakeBuilder('Bar<Foo, Blah<x>, Bling>')
        result = builder._ConvertBaseTokensToAST(builder.tokens)
        self.assertEqual(1, len(result))
        types = [Class('Foo'),
                 Class('Blah', templated_types=[Class('x')]),
                 Class('Bling')]
        self.assertEqual(Class('Bar', templated_types=types), result[0])

    def testTemplateWithMultipleTemplateArgsEnd(self):
        builder = MakeBuilder('Bar<Foo, Blah, Bling<x> >')
        result = builder._ConvertBaseTokensToAST(builder.tokens)
        self.assertEqual(1, len(result))
        types = [Class('Foo'),
                 Class('Blah'),
                 Class('Bling', templated_types=[Class('x')])]
        self.assertEqual(Class('Bar', templated_types=types), result[0])



def test_main():
    test_support.run_unittest(AstBuilder_ConvertBaseTokensToAstTest)


if __name__ == '__main__':
    test_main()
