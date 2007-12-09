#!/usr/bin/env python

"""Find and print the headers #include'd in a source file."""

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
_INCLUDE_DIRS = getattr(siteheaders, 'INCLUDE_DIRS', ['.'])


def ReadSource(relative_filename):
    source = None
    for path in _INCLUDE_DIRS:
        filename = os.path.join(path, relative_filename)
        source = utils.ReadFile(filename, False)
        if source:
            return source, filename
    return None, relative_filename


def GetHeaders(filename):
    source, actual_filename = ReadSource(filename)
    if source is None:
        print 'Unable to find', filename
        return []

    included_files = []

    print 'Processing', actual_filename
    builder = ast.BuilderFromSource(source)
    for node in builder.Generate():
        if isinstance(node, ast.Include):
            if not node.system:
                print node.filename
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
