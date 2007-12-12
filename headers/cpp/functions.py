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

"""Find and print the functions in a source file."""

import sys

from cpp import ast
from cpp import utils


def PrintFunctions(filename):
    source = utils.ReadFile(filename, False)
    if source is None:
        print 'Unable to find', filename
        return

    #print 'Processing', actual_filename
    builder = ast.BuilderFromSource(source, filename)
    try:
        for node in builder.Generate():
            # TODO(nnorwitz): need to ignore friend method declarations.
            if isinstance(node, ast.Function):
                print node.name
    except:
        pass

    
def main(argv):
    for filename in argv[1:]:
        PrintFunctions(filename)


if __name__ == '__main__':
    main(sys.argv)
