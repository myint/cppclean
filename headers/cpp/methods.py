#!/usr/bin/env python

"""Find and print the methods in a source file."""

import sys

from cpp import ast
from cpp import utils


def PrintMethods(filename):
    source = utils.ReadFile(filename, False)
    if source is None:
        print 'Unable to find', filename
        return

    #print 'Processing', actual_filename
    builder = ast.BuilderFromSource(source)
    try:
        # TODO(nnorwitz): also need to ignore friend methods.
        special_function = ast.FUNCTION_CTOR | ast.FUNCTION_DTOR
        for node in builder.Generate():
            if isinstance(node, ast.Class) and node.body:
                for node in node.body:
                    if (isinstance(node, ast.Function) and
                        not (node.modifiers & special_function)):
                        print node.name
    except:
        pass

    
def main(argv):
    for filename in argv[1:]:
        PrintMethods(filename)


if __name__ == '__main__':
    main(sys.argv)
