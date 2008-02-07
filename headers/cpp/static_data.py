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

"""Print classes, functions and modules which contain static data."""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


import sys

from cpp import ast
from cpp import metrics
from cpp import utils


def _FindWarnings(filename, source, ast_list):
  def FindStatic(function_node):
    for node in function_node:
      if node.name == 'static':
        lines = metrics.Metrics(source)
        print '%s:%d' % (filename, lines.GetLineNumber(node.start)),
        print function_node.name, 'has static data'

  for node in ast_list:
    if isinstance(node, ast.Function):
      if node.body:
        FindStatic(node)
    elif isinstance(node, ast.Class) and node.body:
      for node in node.body:
        if isinstance(node, ast.Function) and node.body:
            FindStatic(node)


def main(argv):
  for filename in argv[1:]:
    source = utils.ReadFile(filename)
    if source is None:
      continue

    print 'Processing', filename
    builder = ast.BuilderFromSource(source, filename)
    try:
      entire_ast = filter(None, builder.Generate())
      _FindWarnings(filename, source, entire_ast)
    except KeyboardInterrupt:
      return
    except:
      # An error message was already printed since we couldn't parse.
      pass


if __name__ == '__main__':
  main(sys.argv)
