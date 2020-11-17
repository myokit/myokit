#!/usr/bin/env python3
#
# Tests the Compiler detection class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit


# Strings in Python2 and Python3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str


class CompilerDetectionTest(unittest.TestCase):
    """
    Tests the compiler detection.
    """
    def test_compiler(self):
        # Test the compiler detection.
        self.assertIsInstance(myokit.Compiler.info(), basestring)


if __name__ == '__main__':
    unittest.main()
