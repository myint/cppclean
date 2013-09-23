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

from __future__ import print_function

from . import ast
from . import metrics


__author__ = 'nnorwitz@google.com (Neal Norwitz)'


def _find_warnings(filename, source, ast_list, static_is_optional):
    def print_warning(node, name):
        lines = metrics.Metrics(source)
        print('%s:%d' % (filename, lines.get_line_number(node.start)), end=' ')
        print('static data:', name)

    def find_static(function_node):
        for node in function_node.body:
            if node.name == 'static':
                # TODO(nnorwitz): should ignore const. Is static const common
                # here?
                print_warning(node, function_node.name)

    for node in ast_list:
        if isinstance(node, ast.VariableDeclaration):
            # Ignore 'static' at module scope so we can find globals too.
            is_static = 'static' in node.type.modifiers
            is_not_const = 'const' not in node.type.modifiers
            if is_not_const and (static_is_optional or is_static):
                print_warning(node, node.name)
        elif isinstance(node, ast.Function):
            if node.body:
                find_static(node)
        elif isinstance(node, ast.Class) and node.body:
            _find_warnings(filename, source, node.body, False)


def run(filename, source, entire_ast, include_paths):
    _find_warnings(filename, source, entire_ast, True)
