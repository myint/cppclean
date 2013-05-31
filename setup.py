#!/usr/bin/env python

"""Setup for cppclean."""

from __future__ import unicode_literals

from distutils import core


with open('README') as readme:
    core.setup(name='cppclean',
               description='Find problems in C++ source that slow development '
                           'of large code bases.',
               long_description=readme.read(),
               packages=['cpp'],
               scripts=['cppclean'])
