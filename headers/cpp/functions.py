#!/usr/bin/env python

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
    builder = ast.BuilderFromSource(source)
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
