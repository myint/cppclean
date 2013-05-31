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

"""Find and print the types in a source file.

The types are:  structs, unions, enums, typedefs
"""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


import sys

from cpp import ast


def main(argv):
    interesting_types = (ast.Struct, ast.Enum, ast.Typedef, ast.Union)
    condition = lambda node: isinstance(node, interesting_types)
    ast.PrintAllIndentifiers(argv[1:], condition)


if __name__ == '__main__':
    main(sys.argv)
