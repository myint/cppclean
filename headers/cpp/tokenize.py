#!/usr/bin/env python

"""Tokenize C++ source code"""

import sys

from cpp import utils


# Token types.
UNKNOWN = 'UNKNOWN'
SYNTAX = 'SYNTAX'
CONSTANT = 'CONSTANT'
NAME = 'NAME'
PREPROCESSOR = 'PREPROCESSOR'


def GetTokens(source):
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
        if c.isalpha() or c == '_':               # Find a string token.
            token_type = NAME
            while source[i].isalpha() or source[i].isdigit() or source[i] == '_':
                i += 1
        elif c == '"':                            # Find string.
            token_type = CONSTANT
            i = source.find('"', i+1)
            while source[i-1] == '\\':
                i = source.find('"', i+1)
            i += 1
        elif c == "'":                            # Find char.
            token_type = CONSTANT
            # NOTE(nnorwitz): may not be quite correct, should be good enough.
            i = source.find("'", i+1)
            while source[i-1] == '\\':
                # Need to special case '\\'.
                if (i - 2) > start and source[i-2] == '\\':
                    break
                i = source.find("'", i+1)
            i += 1
        elif c.isdigit():                         # Find integer.
            token_type = CONSTANT
            if c == '0' and source[i+1] in 'xX':
                # Handle hex digits.
                i += 2
                while source[i].isdigit() or source[i].lower() in 'abcdef':
                    i += 1
            else:
                while source[i].isdigit() or source[i] in 'eE+-.':
                    i += 1
        elif c == '/' and source[i+1] == '/':     # Find // comments.
            i = source.find('\n', i)
            if i == -1:  # Handle EOF.
                i = end
            continue
        elif c == '/' and source[i+1] == '*':     # Find /* comments. */
            i = source.find('*/', i) + 2
            continue
        elif c == '#':                            # Find pre-processor command.
            token_type = PREPROCESSOR
            # TODO(nnorwitz): handle preprocessor statements (\ continuations).
            while 1:
                i1 = source.find('\n', i)
                i2 = source.find('//', i)
                i3 = source.find('/*', i)
                # NOTE(nnorwitz): doesn't handle comments in #define macros.
                # Get the first important symbol (newline, comment, EOF/end).
                i = min([x for x in (i1, i2, i3, end) if x != -1])
                # Keep going if end of the line and the line ends with \.
                if not (i == i1 and source[i-1] == '\\'):
                    break
                i += 1
        elif c in ':+-<>&|*=':                    # : or :: (plus other chars).
            token_type = SYNTAX
            i += 1
            new_ch = source[i]
            if new_ch == c:
                i += 1
            elif c == '-' and new_ch == '>':
                i += 1
            elif new_ch == '=':
                i += 1
        elif c in '()[]{}~!?^%;/.,':              # Handle single char tokens.
            token_type = SYNTAX
            i += 1
            if c == '.' and source[i].isdigit():
                token_type = CONSTANT
                i += 1
                while source[i].isdigit() or source[i] in 'eE+-':
                    i += 1
        elif c == '\\':                           # Handle \ in code.
            # This is different from the pre-processor \ handling.
            i += 1
            continue
        else:
            print 'Unknown: %d:%s: %r' % (i, c, source[i-10:i+10])
            raise RuntimeError, 'unexpected token'

        yield token_type, source[start:i], start, i
        if i <= 0:
            print 'Invalid index, exiting now.'
            return
            

def main(argv):
    for filename in argv[1:]:
        source = utils.ReadFile(filename)
        if source is None:
            continue

        tokens = GetTokens(source)
        for token_type, token, start, end in tokens:
            print '%-12s: %s' % (token_type, token)
            # print '\r%6.2f%%' % (100.0 * index / end),
        print


if __name__ == '__main__':
    main(sys.argv)
