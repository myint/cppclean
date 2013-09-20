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

from __future__ import print_function

__author__ = 'nnorwitz@google.com (Neal Norwitz)'


import os

from . import utils

# Allow a site to override the defaults if they choose.
# Just put a siteheaders.py somewhere in the PYTHONPATH.
try:
    import siteheaders
except ImportError:
    siteheaders = None
GetIncludeDirs = getattr(siteheaders, 'GetIncludeDirs', lambda fn: ['.'])


def read_source(relative_filename):
    source = None
    for path in GetIncludeDirs(relative_filename):
        filename = os.path.join(path, relative_filename)
        source = utils.read_file(filename, False)
        if source is not None:
            return source, filename
    return None, relative_filename
