#!/usr/bin/env python

"""Tests for find_warnings module."""

from __future__ import absolute_import

import unittest

from cpp import find_warnings


class Tests(unittest.TestCase):

    def test_get_correct_include_filename(self):
        self.assertEqual(
            'FOO.h',
            find_warnings.get_correct_include_filename(
                'foo.h',
                ['FOO.h', 'apple.h']))

    def test_get_correct_include_filename_without_match(self):
        self.assertEqual(
            None,
            find_warnings.get_correct_include_filename(
                'foo.h',
                ['f.h', 'apple.h']))

        self.assertEqual(
            None,
            find_warnings.get_correct_include_filename(
                'foo.h',
                []))


if __name__ == '__main__':
    unittest.main()
