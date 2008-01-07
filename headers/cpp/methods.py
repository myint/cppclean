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

"""Find and print the methods in a source file."""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


import sys

from cpp import ast


def main(argv):
    def IsMethod(node):
        # TODO(nnorwitz): also need to ignore friend methods.
        special_function = ast.FUNCTION_CTOR | ast.FUNCTION_DTOR
        if isinstance(node, ast.Class) and node.body:
            for node in node.body:
                if (isinstance(node, ast.Function) and
                    not (node.modifiers & special_function)):
                    # TODO(nnorwitz): print operators properly.
                    print node.name

    ast.PrintAllIndentifiers(argv[1:], IsMethod)


if __name__ == '__main__':
    main(sys.argv)
