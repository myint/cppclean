#!/usr/bin/env python

# Run all the unittests.

import popen2
import os
import sys


def GetAndPrintOutput(fp):
    output = fp.read()
    if output:
        print output
    return output


def main(argv):
    dirname = os.path.abspath(os.path.dirname(argv[0]))
    test_dir = os.path.join(dirname, 'cpp')
    os.environ['PYTHONPATH'] = dirname
    exit_status = 0
    for f in os.listdir(test_dir):
        if f.endswith('_test.py'):
            # TODO(nnorwitz): need to properly quote args?
            args = [sys.executable, os.path.join(test_dir, f)]
            p = popen2.Popen3(args, True)
            status = p.wait()
            GetAndPrintOutput(p.fromchild)
            stderr = GetAndPrintOutput(p.childerr)
            if status or stderr:
                exit_status += 1
    return exit_status


if __name__ == '__main__':
    sys.exit(main(sys.argv))
