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
