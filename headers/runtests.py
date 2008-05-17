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

"""Run all the unittests."""

import difflib
import popen2
import os
import StringIO
import sys

from cpp import ast
from cpp import find_warnings


# [(module, 'directory', 'input-file', 'expected-output-file')]
_GOLDEN_FILE_TESTS = [
    (ast, 'test', 'foo.h', 'foo.h.expected'),
    (find_warnings, 'test', 'foo.h', 'foo.h.expected-warnings'),
    (find_warnings, 'test', 'need-class.h', 'need-class.h.expected-warnings'),
    (find_warnings, 'test/define', 'd1.cc', 'd1.expected'),
    (find_warnings, 'test/define', 'd2.cc', 'd2.expected'),
    (find_warnings, 'test/define', 'd3.cc', 'd3.expected'),
    (find_warnings, 'test/define', 'd4.h', 'd4.expected'),
    (find_warnings, 'test/define', 'd5.h', 'd5.expected'),
    (find_warnings, 'test/define', 'd6.h', 'd6.expected'),
    (find_warnings, 'test/define', 'd7.h', 'd7.expected'),
    (find_warnings, 'test/define', 'd8.h', 'd8.expected'),
    ]


def GetAndPrintOutput(fp):
    output = fp.read()
    if output:
        print output
    return output


def DiffGoldenFile(test_type, test_name, output_lines, expected_file):
    expected_lines = open(expected_file).readlines()
    diffs = list(difflib.unified_diff(output_lines, expected_lines))
    if diffs:
        print >>sys.__stdout__, test_type, test_name, 'failed.  Diffs:'
        for line in diffs:
            print >>sys.__stdout__, line,
        return 1
    print >>sys.__stdout__, test_type, test_name, 'passed'
    return 0


def RunGoldenTests(generate_output):
    start_cwd = os.path.abspath(os.getcwd())
    for module, directory, input_file, expected_file in _GOLDEN_FILE_TESTS:
        # Capture stdout.
        sys.stdout = StringIO.StringIO()
        try:
            # Setup directory and test name.
            os.chdir(os.path.join(start_cwd, directory))
            test_name = module.__name__

            # Run the test.
            module.main([test_name, input_file])

            # Verify output.
            output = sys.stdout.getvalue()
            if generate_output:
                fp = open(expected_file, 'w+')
                fp.write(output)
                fp.close()
            output_lines = output.splitlines(True)
            exit_status = DiffGoldenFile(test_name, input_file,
                                         output_lines, expected_file)
            if exit_status != 0:
                # Stop after first failure.
                break
        finally:
            sys.stdout = sys.__stdout__


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
    if exit_status == 0:
        generate_golden_files = len(argv) > 1 and argv[1] == '--expected'
        RunGoldenTests(generate_golden_files)
    return exit_status


if __name__ == '__main__':
    sys.exit(main(sys.argv))
