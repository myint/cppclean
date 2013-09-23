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

"""Calculate metrics for C++ code."""

from . import keywords


__author__ = 'nnorwitz@google.com (Neal Norwitz)'


# A set of every keyword that increases the cyclomatic complexity.
_COMPLEXITY_KEYWORDS = \
    frozenset(keywords.CONTROL | keywords.LOOP | keywords.EXCEPTION)


class Metrics(object):

    """Calculate various metrics on C++ source code."""

    def __init__(self, source):
        self.source = source

    def get_line_number(self, index):
        """Return the line number in the source based on the index."""
        return 1 + self.source.count('\n', 0, index)

    def get_line_count(self, token_stream):
        """Return the number of lines for the method in the token_stream."""
        first_line = self.get_line_number(token_stream[0].start)
        last_line = self.get_line_number(token_stream[-1].end)
        return last_line - first_line

    def get_complexity(self, token_stream):
        """Return cyclomatic complexity for the method in the token_stream."""
        complexity = 1
        for token in token_stream:
            complexity += token.name in _COMPLEXITY_KEYWORDS
        return complexity
