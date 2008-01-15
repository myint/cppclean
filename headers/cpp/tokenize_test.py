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

"""Tokenize test."""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


from test import test_support
import unittest

from cpp import tokenize

# For convenience, add to test module.
UNKNOWN = tokenize.UNKNOWN
SYNTAX = tokenize.SYNTAX
CONSTANT = tokenize.CONSTANT
NAME = tokenize.NAME
PREPROCESSOR = tokenize.PREPROCESSOR


def __eq__(self, other):
    assert isinstance(other, self.__class__)
    return (self.token_type == other.token_type and
            self.name == other.name and
            self.start == other.start and
            self.end == other.end and
            self.whence == other.whence)

Token = tokenize.Token
Token.__eq__ = __eq__


class TokenizeTest(unittest.TestCase):

    def GetTokens(self, string, append_newline=True):
        if append_newline:
            string += '\n'
        return list(tokenize.GetTokens(string))

    def testGetTokens_EmptyString(self):
        self.assertEqual([], self.GetTokens('', False))

    def testGetTokens_Whitespace(self):
        self.assertEqual([], self.GetTokens('   ', False))
        self.assertEqual([], self.GetTokens('   \n\n\n', True))

    def testGetTokens_CppComment(self):
        self.assertEqual([], self.GetTokens('// comment'))

    def testGetTokens_MultilineComment(self):
        self.assertEqual([], self.GetTokens('/* comment\n\n\nfoo */', False))

    def testGetTokens_BinaryOperators(self):
        for operator in '+-*/%&|^<>':
            #                        012 345
            tokens = self.GetTokens('5 %s 3' % operator)
            self.assertEqual(3, len(tokens), tokens)
            self.assertEqual(Token(CONSTANT, '5', 0, 1), tokens[0])
            self.assertEqual(Token(SYNTAX, operator, 2, 3), tokens[1])
            self.assertEqual(Token(CONSTANT, '3', 4, 5), tokens[2])

    def testGetTokens_MultiCharBinaryOperators(self):
        for operator in ('<<', '>>', '**'):
            #                        0123456
            tokens = self.GetTokens('5 %s 3' % operator)
            self.assertEqual(3, len(tokens), tokens)
            self.assertEqual(Token(CONSTANT, '5', 0, 1), tokens[0])
            self.assertEqual(Token(SYNTAX, operator, 2, 4), tokens[1])
            self.assertEqual(Token(CONSTANT, '3', 5, 6), tokens[2])

    def testGetTokens_AdditionWithComment(self):
        #                        0123456789012 3 4 56789012345
        tokens = self.GetTokens('5 /* comment\n\n\nfoo */ + 3')
        self.assertEqual(3, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '5', 0, 1), tokens[0])
        self.assertEqual(Token(SYNTAX, '+', 22, 23), tokens[1])
        self.assertEqual(Token(CONSTANT, '3', 24, 25), tokens[2])

    def testGetTokens_LogicalOperators(self):
        for operator in ('&&', '||'):
            #                        012345
            tokens = self.GetTokens('a %s b' % operator)
            self.assertEqual(3, len(tokens), tokens)
            self.assertEqual(Token(NAME, 'a', 0, 1), tokens[0])
            self.assertEqual(Token(SYNTAX, operator, 2, 4), tokens[1])
            self.assertEqual(Token(NAME, 'b', 5, 6), tokens[2])

        #                        01234
        tokens = self.GetTokens('!not')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(SYNTAX, '!', 0, 1), tokens[0])
        self.assertEqual(Token(NAME, 'not', 1, 4), tokens[1])

    def testGetTokens_OnesComplement(self):
        #                        01234
        tokens = self.GetTokens('~not')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(SYNTAX, '~', 0, 1), tokens[0])
        self.assertEqual(Token(NAME, 'not', 1, 4), tokens[1])

    def testGetTokens_PreIncrementOperators(self):
        for operator in ('++', '--'):
            #                        012345
            tokens = self.GetTokens('%sFOO' % operator)
            self.assertEqual(2, len(tokens), tokens)
            self.assertEqual(Token(SYNTAX, operator, 0, 2), tokens[0])
            self.assertEqual(Token(NAME, 'FOO', 2, 5), tokens[1])

            #                        012345
            tokens = self.GetTokens('%s FOO' % operator)
            self.assertEqual(2, len(tokens), tokens)
            self.assertEqual(Token(SYNTAX, operator, 0, 2), tokens[0])
            self.assertEqual(Token(NAME, 'FOO', 3, 6), tokens[1])

    def testGetTokens_PostIncrementOperators(self):
        for operator in ('++', '--'):
            #                        012345
            tokens = self.GetTokens('FOO%s' % operator)
            self.assertEqual(2, len(tokens), tokens)
            self.assertEqual(Token(NAME, 'FOO', 0, 3), tokens[0])
            self.assertEqual(Token(SYNTAX, operator, 3, 5), tokens[1])

            #                        012345
            tokens = self.GetTokens('FOO %s' % operator)
            self.assertEqual(2, len(tokens), tokens)
            self.assertEqual(Token(NAME, 'FOO', 0, 3), tokens[0])
            self.assertEqual(Token(SYNTAX, operator, 4, 6), tokens[1])

    def testGetTokens_Semicolons(self):
        #                        0123456 789012
        tokens = self.GetTokens('  foo;\n  bar;')
        self.assertEqual(4, len(tokens), tokens)
        self.assertEqual(Token(NAME, 'foo', 2, 5), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 5, 6), tokens[1])
        self.assertEqual(Token(NAME, 'bar', 9, 12), tokens[2])
        self.assertEqual(Token(SYNTAX, ';', 12, 13), tokens[3])

    def testGetTokens_Pointers1(self):
        #                        0123456789
        tokens = self.GetTokens('foo->bar;')
        self.assertEqual(4, len(tokens), tokens)
        self.assertEqual(Token(NAME, 'foo', 0, 3), tokens[0])
        self.assertEqual(Token(SYNTAX, '->', 3, 5), tokens[1])
        self.assertEqual(Token(NAME, 'bar', 5, 8), tokens[2])
        self.assertEqual(Token(SYNTAX, ';', 8, 9), tokens[3])

    def testGetTokens_Pointers2(self):
        #                        01234567890
        tokens = self.GetTokens('(*foo).bar;')
        self.assertEqual(7, len(tokens), tokens)
        self.assertEqual(Token(SYNTAX, '(', 0, 1), tokens[0])
        self.assertEqual(Token(SYNTAX, '*', 1, 2), tokens[1])
        self.assertEqual(Token(NAME, 'foo', 2, 5), tokens[2])
        self.assertEqual(Token(SYNTAX, ')', 5, 6), tokens[3])
        self.assertEqual(Token(SYNTAX, '.', 6, 7), tokens[4])
        self.assertEqual(Token(NAME, 'bar', 7, 10), tokens[5])
        self.assertEqual(Token(SYNTAX, ';', 10, 11), tokens[6])

    def testGetTokens_Block(self):
        #                        0123456
        tokens = self.GetTokens('{ 0; }')
        self.assertEqual(4, len(tokens), tokens)
        self.assertEqual(Token(SYNTAX, '{', 0, 1), tokens[0])
        self.assertEqual(Token(CONSTANT, '0', 2, 3), tokens[1])
        self.assertEqual(Token(SYNTAX, ';', 3, 4), tokens[2])
        self.assertEqual(Token(SYNTAX, '}', 5, 6), tokens[3])

    def testGetTokens_BitFields(self):
        #                        012345678901234567
        tokens = self.GetTokens('unsigned foo : 1;')
        self.assertEqual(5, len(tokens), tokens)
        self.assertEqual(Token(NAME, 'unsigned', 0, 8), tokens[0])
        self.assertEqual(Token(NAME, 'foo', 9, 12), tokens[1])
        self.assertEqual(Token(SYNTAX, ':', 13, 14), tokens[2])
        self.assertEqual(Token(CONSTANT, '1', 15, 16), tokens[3])
        self.assertEqual(Token(SYNTAX, ';', 16, 17), tokens[4])

    def testGetTokens_IntConstants(self):
        #                        01234
        tokens = self.GetTokens('123;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '123', 0, 3), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 3, 4), tokens[1])

        for suffix in ('l', 'u', 'ul', 'll', 'ull'):
            #                        0123456
            tokens = self.GetTokens('123%s;' % suffix)
            self.assertEqual(2, len(tokens), tokens)
            value = '123%s' % suffix
            size = len(value)
            self.assertEqual(Token(CONSTANT, value, 0, size), tokens[0])
            self.assertEqual(Token(SYNTAX, ';', size, size+1), tokens[1])

            suffix = suffix.upper()

            #                        0123456
            tokens = self.GetTokens('123%s;' % suffix)
            self.assertEqual(2, len(tokens), tokens)
            value = '123%s' % suffix
            size = len(value)
            self.assertEqual(Token(CONSTANT, value, 0, size), tokens[0])
            self.assertEqual(Token(SYNTAX, ';', size, size+1), tokens[1])

    def testGetTokens_OctalConstants(self):
        #                        0123456789
        tokens = self.GetTokens('01234567;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '01234567', 0, 8), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 8, 9), tokens[1])

        for suffix in ('l', 'u', 'ul', 'll', 'ull'):
            #                        012345678901
            tokens = self.GetTokens('01234567%s;' % suffix)
            self.assertEqual(2, len(tokens), tokens)
            value = '01234567%s' % suffix
            size = len(value)
            self.assertEqual(Token(CONSTANT, value, 0, size), tokens[0])
            self.assertEqual(Token(SYNTAX, ';', size, size+1), tokens[1])

            suffix = suffix.upper()

            #                        012345678901
            tokens = self.GetTokens('01234567%s;' % suffix)
            self.assertEqual(2, len(tokens), tokens)
            value = '01234567%s' % suffix
            size = len(value)
            self.assertEqual(Token(CONSTANT, value, 0, size), tokens[0])
            self.assertEqual(Token(SYNTAX, ';', size, size+1), tokens[1])

    def testGetTokens_HexConstants(self):
        #                        012345678901
        tokens = self.GetTokens('0xDeadBEEF;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '0xDeadBEEF', 0, 10), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 10, 11), tokens[1])

        for suffix in ('l', 'u', 'ul', 'll', 'ull'):
            #                        0123456789
            tokens = self.GetTokens('0xBEEF%s;' % suffix)
            self.assertEqual(2, len(tokens), tokens)
            value = '0xBEEF%s' % suffix
            size = len(value)
            self.assertEqual(Token(CONSTANT, value, 0, size), tokens[0])
            self.assertEqual(Token(SYNTAX, ';', size, size+1), tokens[1])

            suffix = suffix.upper()

            #                        0123456789
            tokens = self.GetTokens('0xBEEF%s;' % suffix)
            self.assertEqual(2, len(tokens), tokens)
            value = '0xBEEF%s' % suffix
            size = len(value)
            self.assertEqual(Token(CONSTANT, value, 0, size), tokens[0])
            self.assertEqual(Token(SYNTAX, ';', size, size+1), tokens[1])

    def testGetTokens_FloatConstants(self):
        #                        012345678901
        tokens = self.GetTokens('3.14;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '3.14', 0, 4), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 4, 5), tokens[1])

        #                        012345678901
        tokens = self.GetTokens('3.14E;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '3.14E', 0, 5), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 5, 6), tokens[1])

        #                        012345678901
        tokens = self.GetTokens('3.14e;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '3.14e', 0, 5), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 5, 6), tokens[1])

        #                        012345678901
        tokens = self.GetTokens('.14;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '.14', 0, 3), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 3, 4), tokens[1])

        #                        012345678901
        tokens = self.GetTokens('3.14e+10;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '3.14e+10', 0, 8), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 8, 9), tokens[1])

        #                        012345678901
        tokens = self.GetTokens('3.14e-10;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '3.14e-10', 0, 8), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 8, 9), tokens[1])

        #                        012345678901
        tokens = self.GetTokens('3.14f;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '3.14f', 0, 5), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 5, 6), tokens[1])

        #                        012345678901
        tokens = self.GetTokens('3.14l;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '3.14l', 0, 5), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 5, 6), tokens[1])

        #                        012345678901
        tokens = self.GetTokens('3.14F;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '3.14F', 0, 5), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 5, 6), tokens[1])

        #                        012345678901
        tokens = self.GetTokens('3.14L;')
        self.assertEqual(2, len(tokens), tokens)
        self.assertEqual(Token(CONSTANT, '3.14L', 0, 5), tokens[0])
        self.assertEqual(Token(SYNTAX, ';', 5, 6), tokens[1])

    # TODO(nnorwitz): test all the following
    # ? :
    # Strings
    # Characters
    # Preprocessor: #define
    # Preprocessor: #if 0
    # Assignment
    # Augmented assignments (lots)
    # []
    # () and function calls
    # comma operator
    # identifiers (e.g., _).  what to do about dollar signs?


def test_main():
    test_support.run_unittest(TokenizeTest)


if __name__ == '__main__':
    test_main()
