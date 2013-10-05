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
from __future__ import unicode_literals

import collections

from . import ast
from . import metrics


__author__ = 'nnorwitz@google.com (Neal Norwitz)'


def _find_warnings(filename, source, ast_list, static_is_optional):
    lines = metrics.Metrics(source)

    def print_warning(node, name):
        print('%s:%d' % (filename, lines.get_line_number(node.start)), end=' ')
        print("static data: '{}'".format(name))

    def find_static(function_node):
        for node in function_node.body:
            if node.name == 'static':
                # TODO(nnorwitz): should ignore const. Is static const common
                # here?
                lines = metrics.Metrics(source)
                print_warning(node, lines.get_line(node.start).strip())

    static_declarations = {}
    for node in ast_list:
        if isinstance(node, ast.VariableDeclaration):
            # Ignore 'static' at module scope so we can find globals too.
            is_static = 'static' in node.type.modifiers
            is_not_const = 'const' not in node.type.modifiers
            if is_not_const and (static_is_optional or is_static):
                print_warning(node, node.name)
                static_declarations[node.name] = node
        elif isinstance(node, ast.Function):
            if node.body:
                find_static(node)
        elif isinstance(node, ast.Class) and node.body:
            _find_warnings(filename, source, node.body, False)

    _find_unused_static_warnings(ast_list, static_declarations,
                                 filename=filename,
                                 lines=lines)


def _find_unused_static_warnings(ast_list, static_declarations,
                                 filename, lines):
    """Warn about unused static variables."""
    static_counts = collections.Counter()
    for node in ast_list:
        if isinstance(node, ast.Function) and node.body:
            for child in node.body:
                if child.name in static_declarations:
                    static_counts[child.name] += 1

    for name, count in static_counts.items():
        if count == 1:
            print("{}:{}: Unused variable '{}'".format(
                filename,
                lines.get_line_number(static_declarations[name].start),
                name))


def run(filename, source, entire_ast, include_paths):
    _find_warnings(filename, source, entire_ast, True)
