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
"""Find and print the headers #include'd in a source file."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os

from . import utils

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


def read_source(filename, include_paths):
    for path in include_paths:
        actual_filename = os.path.join(path, filename)
        actual_filename = actual_filename if not actual_filename.startswith(
            "./") else actual_filename[2:]
        source = utils.read_file(actual_filename, False)
        if source is not None:
            return source, actual_filename
    return None, filename
