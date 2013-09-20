#!/usr/bin/env python

"""Setup for cppclean."""

from __future__ import absolute_import

import ast
from distutils import core
import os


def version(filename):
    """Return version string."""
    with open(filename) as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s


with open('README.rst') as readme:
    core.setup(name='cppclean',
               version=version(os.path.join('cpp', '__init__.py')),
               description='Find problems in C++ source that slow development '
                           'of large code bases.',
               long_description=readme.read(),
               packages=['cpp'],
               scripts=['cppclean'])
