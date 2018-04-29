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

"""Tokenize C++ source code."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals


__author__ = 'nnorwitz@google.com (Neal Norwitz)'


# Add $ as a valid identifier char since so much code uses it.
_letters = 'abcdefghijklmnopqrstuvwxyz'
_valid_identifier_first_char = _letters + _letters.upper() + '_$'
_valid_identifier_char = _valid_identifier_first_char + '0123456789'
VALID_IDENTIFIER_FIRST_CHARS = frozenset(_valid_identifier_first_char)
VALID_IDENTIFIER_CHARS = frozenset(_valid_identifier_char)
HEX_DIGITS = frozenset('0123456789abcdefABCDEF')
INT_OR_FLOAT_DIGITS = frozenset('01234567890eE-+')


# C++0x string prefixes.
_STR_PREFIXES = frozenset(('R', 'u8', 'u8R', 'u', 'uR', 'U', 'UR', 'L', 'LR'))


# Token types.
UNKNOWN = 'UNKNOWN'
SYNTAX = 'SYNTAX'
CONSTANT = 'CONSTANT'
NAME = 'NAME'
PREPROCESSOR = 'PREPROCESSOR'


class TokenError(Exception):

    """Raised when tokenization fails."""


class Token(object):

    """Data container to represent a C++ token.

    Tokens can be identifiers, syntax char(s), constants, or
    pre-processor directives.

    start contains the index of the first char of the token in the source
    end contains the index of the last char of the token in the source
    """

    def __init__(self, token_type, name, start, end):
        self.token_type = token_type
        self.name = name
        self.start = start
        self.end = end

    def __str__(self):
        return 'Token(%r, %s, %s)' % (self.name, self.start, self.end)

    __repr__ = __str__


def _get_string(source, i):
    i = source.find('"', i + 1)
    while source[i - 1] == '\\':
        # Count the trailing backslashes.
        backslash_count = 1
        j = i - 2
        while source[j] == '\\':
            backslash_count += 1
            j -= 1
        # When trailing backslashes are even, they escape each other.
        if (backslash_count % 2) == 0:
            break
        i = source.find('"', i + 1)
    return i + 1


def _get_char(source, start, i):
    # NOTE(nnorwitz): may not be quite correct, should be good enough.
    i = source.find("'", i + 1)
    while i != -1 and source[i - 1] == '\\':
        # Need to special case '\\'.
        if source[i - 2] == '\\':
            break
        i = source.find("'", i + 1)
    # Try to handle unterminated single quotes.
    return i + 1 if i != -1 else start + 1


def get_tokens(source):
    """Returns a sequence of Tokens.

    Args:
      source: string of C++ source code.

    Yields:
      Token that represents the next token in the source.
    """
    if not source.endswith('\n'):
        source += '\n'

    # Cache various valid character sets for speed.
    valid_identifier_first_chars = VALID_IDENTIFIER_FIRST_CHARS
    valid_identifier_chars = VALID_IDENTIFIER_CHARS
    hex_digits = HEX_DIGITS
    int_or_float_digits = INT_OR_FLOAT_DIGITS
    int_or_float_digits2 = int_or_float_digits | set('.')

    # Ignore tokens while in a #if 0 block.
    count_ifs = 0

    i = 0
    end = len(source)
    while i < end:
        # Skip whitespace.
        while i < end and source[i].isspace():
            i += 1
        if i >= end:
            return

        token_type = UNKNOWN
        start = i
        c = source[i]
        # Find a string token.
        if c in valid_identifier_first_chars or c == '_':
            token_type = NAME
            while source[i] in valid_identifier_chars:
                i += 1
            # String and character constants can look like a name if
            # they are something like L"".
            if source[i] == "'" and source[start:i] in _STR_PREFIXES:
                token_type = CONSTANT
                i = _get_char(source, start, i)
            elif source[i] == '"' and source[start:i] in _STR_PREFIXES:
                token_type = CONSTANT
                i = _get_string(source, i)
        elif c == '/' and source[i + 1] == '/':  # Find // comments.
            i = _find(source, '\n', i)
            continue
        elif c == '/' and source[i + 1] == '*':  # Find /* comments. */
            i = _find(source, '*/', i) + 2
            continue
        elif c in '<>':                          # Handle '<' and '>' tokens.
            token_type = SYNTAX
            i += 1
            new_ch = source[i]
            # Do not merge '>>' or '>>=' into a single token
            if new_ch == c and c != '>':
                i += 1
                new_ch = source[i]
            if new_ch == '=':
                i += 1
        elif c in ':+-&|=':                      # Handle 'XX' and 'X=' tokens.
            token_type = SYNTAX
            i += 1
            new_ch = source[i]
            if new_ch == c:
                i += 1
            elif c == '-' and new_ch == '>':
                i += 1
            elif new_ch == '=':
                i += 1
        elif c in '!*^%/':                       # Handle 'X=' tokens.
            token_type = SYNTAX
            i += 1
            new_ch = source[i]
            if new_ch == '=':
                i += 1
        elif c in '()[]{}~?;.,':                 # Handle single char tokens.
            token_type = SYNTAX
            i += 1
            if c == '.' and source[i].isdigit():
                token_type = CONSTANT
                i += 1
                while source[i] in int_or_float_digits:
                    i += 1
                # Handle float suffixes.
                for suffix in ('l', 'f'):
                    if suffix == source[i:i + 1].lower():
                        i += 1
                        break
        elif c.isdigit():                        # Find integer.
            token_type = CONSTANT
            if c == '0' and source[i + 1] in 'xX':
                # Handle hex digits.
                i += 2
                while source[i] in hex_digits:
                    i += 1
            else:
                while source[i] in int_or_float_digits2:
                    i += 1
            # Handle integer (and float) suffixes.
            if source[i].isalpha():
                for suffix in ('ull', 'll', 'ul', 'l', 'f', 'u'):
                    size = len(suffix)
                    if suffix == source[i:i + size].lower():
                        i += size
                        break
        elif c == '"':                           # Find string.
            token_type = CONSTANT
            i = _get_string(source, i)
        elif c == "'":                           # Find char.
            token_type = CONSTANT
            i = _get_char(source, start, i)
        elif c == '#':                           # Find pre-processor command.
            token_type = PREPROCESSOR
            got_if = source[i:i + 3] == '#if'
            if count_ifs and source[i:i + 6] == '#endif':
                count_ifs -= 1
                if count_ifs == 0:
                    source = source[:i].ljust(i + 6) + source[i + 6:]
                    continue

            # Handle preprocessor statements (\ continuations).
            while True:
                i1 = source.find('\n', i)
                i2 = source.find('//', i)
                i3 = source.find('/*', i)
                i4 = source.find('"', i)
                # Get the first important symbol (newline, comment, EOF/end).
                i = min([x for x in (i1, i2, i3, i4, end) if x != -1])

                # Handle comments in #define macros.
                if i == i3:
                    i = _find(source, '*/', i) + 2
                    source = source[:i3].ljust(i) + source[i:]
                    continue

                # Handle #include "dir//foo.h" properly.
                if source[i] == '"':
                    i = _find(source, '"', i + 1) + 1
                    continue

                # Keep going if end of the line and the line ends with \.
                if i == i1 and source[i - 1] == '\\':
                    i += 1
                    continue

                if got_if:
                    begin = source.find('(', start, i)
                    if begin == -1:
                        begin = source.find(' ', start)
                    begin = begin + 1
                    s1 = source.find(' ', begin)
                    s2 = source.find(')', begin)
                    s3 = source.find('\n', begin)
                    s = min([x for x in (s1, s2, s3, end) if x != -1])

                    condition = source[begin:s]
                    if (
                        count_ifs or
                        condition == '0' or
                        condition == '__OBJC__'
                    ):
                        count_ifs += 1
                break
        elif c == '\\':                          # Handle \ in code.
            # This is different from the pre-processor \ handling.
            i += 1
            continue
        elif count_ifs:
            # Ignore bogus code when we are inside an #if block.
            i += 1
            continue
        else:
            raise TokenError("unexpected token '{0}'".format(c))

        if count_ifs:
            continue

        assert i > 0
        yield Token(token_type, source[start:i], start, i)


def _find(string, sub_string, start_index):
    """Return index of sub_string in string.

    Raise TokenError if sub_string is not found.
    """
    result = string.find(sub_string, start_index)
    if result == -1:
        raise TokenError("expected '{0}'".format(sub_string))
    return result
