#!/usr/bin/env python
#
# Copyright 2008 Google Inc.
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

"""Print classes which have a virtual method and non-virtual destructor."""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


import sys

from cpp import ast
from cpp import metrics
from cpp import utils


def _FindWarnings(filename, source, ast_list):
  for node in ast_list:
    if isinstance(node, ast.Class) and node.body:
      class_node = node
      has_virtuals = False
      for node in node.body:
        if isinstance(node, ast.Class) and node.body:
          _FindWarnings(filename, source, [node])
        elif (isinstance(node, ast.Function) and
            node.modifiers & ast.FUNCTION_VIRTUAL):
            has_virtuals = True
            if node.modifiers & ast.FUNCTION_DTOR:
              break
      else:
        if has_virtuals and not class_node.bases:
          lines = metrics.Metrics(source)
          print '%s:%d' % (filename, lines.GetLineNumber(class_node.start)),
          print class_node.name, 'has virtual methods without a virtual dtor'


def main(argv):
  for filename in argv[1:]:
    source = utils.ReadFile(filename)
    if source is None:
      continue

    print 'Processing', filename
    builder = ast.BuilderFromSource(source, filename)
    try:
      entire_ast = filter(None, builder.Generate())
    except KeyboardInterrupt:
      return
    except:
      # An error message was already printed since we couldn't parse.
      pass
    else:
      _FindWarnings(filename, source, entire_ast)


if __name__ == '__main__':
  main(sys.argv)
