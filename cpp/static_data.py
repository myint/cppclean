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


def _FindWarnings(filename, source, ast_list, static_is_optional):
  def PrintWarning(node, name):
    lines = metrics.Metrics(source)
    print '%s:%d' % (filename, lines.GetLineNumber(node.start)),
    print 'static data:', name

  def FindStatic(function_node):
    for node in function_node.body:
      if node.name == 'static':
        # TODO(nnorwitz): should ignore const.  Is static const common here?
        PrintWarning(node, function_node.name)

  for node in ast_list:
    if isinstance(node, ast.VariableDeclaration):
      # Ignore 'static' at module scope so we can find globals too.
      is_static = 'static' in node.type.modifiers
      is_not_const = 'const' not in node.type.modifiers
      if is_not_const and (static_is_optional or is_static):
        PrintWarning(node, node.name)
    elif isinstance(node, ast.Function):
      if node.body:
        FindStatic(node)
    elif isinstance(node, ast.Class) and node.body:
      _FindWarnings(filename, source, node.body, False)


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
      _FindWarnings(filename, source, entire_ast, True)


if __name__ == '__main__':
  main(sys.argv)
