#!/usr/bin/env python

"""Find and print the headers #include'd in a source file."""

import os
import sys

from cpp import ast
from cpp import utils


_TRANSITIVE = False
_INCLUDE_DIRS = ['.']


def ReadSource(relative_filename):
    source = None
    for path in _INCLUDE_DIRS:
        filename = os.path.join(path, relative_filename)
        source = utils.ReadFile(filename, False)
        if source:
            return source, filename
    return None, relative_filename


def ProcessFile(filename):
    source, actual_filename = ReadSource(filename)
    if source is None:
        print 'Unable to find', filename
        return

    included_files = []

    print 'Processing', actual_filename
    builder = ast.BuilderFromSource(source)
    for node in builder.Generate():
        if isinstance(node, ast.Include):
            if not node.system:
                print node.filename
                if _TRANSITIVE:
                    included_files.append(node.filename)

    # Transitively process all the files that were included.
    for filename in included_files:
        ProcessFile(filename)

    
def main(argv):
    for filename in argv[1:]:
        ProcessFile(filename)


if __name__ == '__main__':
    main(sys.argv)
