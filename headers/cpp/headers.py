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

"""Find and print the headers #include'd in a source file."""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


import os
import sys

from cpp import ast
from cpp import utils

# Allow a site to override the defaults if they choose.
# Just put a siteheaders.py somewhere in the PYTHONPATH.
try:
    import siteheaders
except ImportError:
    siteheaders = None
_TRANSITIVE = getattr(siteheaders, 'TRANSITIVE', False)
GetIncludeDirs = getattr(siteheaders, 'GetIncludeDirs', lambda fn: ['.'])


def ReadSource(relative_filename):
    source = None
    for path in GetIncludeDirs(relative_filename):
        filename = os.path.join(path, relative_filename)
        source = utils.ReadFile(filename, False)
        if source is not None:
            return source, filename
    return None, relative_filename


def GetHeaders(filename):
    source, actual_filename = ReadSource(filename)
    if source is None:
        print('Unable to find %s' % filename)
        return []

    included_files = []

    print('Processing %s' % actual_filename)
    builder = ast.BuilderFromSource(source, filename)
    for node in builder.Generate():
        if isinstance(node, ast.Include):
            if not node.system:
                print(node.filename)
                included_files.append(node.filename)

    # Transitively process all the files that were included.
    if _TRANSITIVE:
        for filename in included_files:
            included_files.extend(GetHeaders(filename))
    return included_files


def main(argv):
    for filename in argv[1:]:
        GetHeaders(filename)


if __name__ == '__main__':
    main(sys.argv)
