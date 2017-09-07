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

"""Find warnings for C++ code."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import fnmatch
import os
import sys

from cpp import __version__
from cpp import ast
from cpp import find_warnings
from cpp import nonvirtual_dtors
from cpp import static_data
from cpp import tokenize
from cpp import utils


def match_file(filename, exclude_patterns):
    """Return True if file is a C++ file or a directory."""
    base_name = os.path.basename(filename)

    if base_name.startswith('.'):
        return False

    for pattern in exclude_patterns:
        if fnmatch.fnmatch(base_name, pattern):
            return False

    if find_warnings.is_header_file(filename):
        return True

    if find_warnings.is_cpp_file(filename):
        return True

    if os.path.isdir(filename):
        return True

    return False


def find_files(filenames, exclude_patterns):
    """Yield filenames."""
    while filenames:
        name = filenames.pop(0)
        if os.path.isdir(name):
            for root, directories, children in os.walk(name):
                filenames += [os.path.join(root, f) for f in sorted(children)
                              if match_file(os.path.join(root, f),
                                            exclude_patterns)]
                directories[:] = [d for d in directories
                                  if match_file(os.path.join(root, d),
                                                exclude_patterns)]
        else:
            yield name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--exclude', action='append',
                        dest='exclude_patterns', default=[], metavar='pattern',
                        help='exclude files matching this pattern; '
                             'specify this multiple times for multiple '
                             'patterns')
    parser.add_argument('--include-path', '-i', '-I', action='append',
                        dest='include_paths', default=[],
                        metavar='path',
                        help='add a header include path; '
                             'specify this multiple times for multiple '
                             'include paths')
    parser.add_argument('--include-path-system', '-s', action='append',
                        dest='include_system_paths', default=[],
                        metavar='sys_path',
                        help='same as --include-path but explicitly '
                             'designates all header files found in these '
                             'directories as "system" includes')
    parser.add_argument('--include-path-non-system', '-n',
                        action='append', dest='include_nonsystem_paths',
                        metavar='nonsys_path',
                        default=[],
                        help='same as --include-path but explicitly '
                             'designates all header files found in these '
                             'directories as "non-system" includes')
    parser.add_argument('--verbose', action='store_true',
                        help='print verbose messages')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='ignore parse errors')
    args = parser.parse_args()

    # For Python 2 where argparse does not return Unicode.
    args.files = [filename.decode(sys.getfilesystemencoding())
                  if hasattr(filename, 'decode') else filename
                  for filename in args.files]

    all_includes = list(set(
        args.include_paths + args.include_system_paths +
        args.include_nonsystem_paths))

    status = 0
    for filename in (
        sorted(find_files(args.files,
                          exclude_patterns=args.exclude_patterns))
    ):
        if args.verbose:
            print('Processing', filename, file=sys.stderr)

        try:
            source = utils.read_file(filename)
            if source is None:
                continue

            builder = ast.builder_from_source(source,
                                              filename,
                                              args.include_system_paths,
                                              args.include_nonsystem_paths,
                                              quiet=args.quiet)
            entire_ast = list([_f for _f in builder.generate() if _f])
        except tokenize.TokenError as exception:
            if args.verbose:
                print('{}: token error: {}'.format(filename, exception),
                      file=sys.stderr)
            continue
        except (ast.ParseError,
                UnicodeDecodeError) as exception:
            if not args.quiet:
                print('{}: parsing error: {}'.format(filename, exception),
                      file=sys.stderr)
            continue

        for module in [find_warnings,
                       nonvirtual_dtors,
                       static_data]:
            if module.run(filename, source, entire_ast,
                          include_paths=all_includes,
                          system_include_paths=args.include_system_paths,
                          nonsystem_include_paths=args.include_nonsystem_paths,
                          quiet=args.quiet):
                status = 1

    return status


try:
    sys.exit(main())
except KeyboardInterrupt:
    sys.exit(1)
