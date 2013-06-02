#!/usr/bin/env python

"""Setup for cppclean."""

from distutils import core


with open('README.rst') as readme:
    core.setup(name='cppclean',
               description='Find problems in C++ source that slow development '
                           'of large code bases.',
               long_description=readme.read(),
               packages=['cpp'],
               scripts=['cppclean'])