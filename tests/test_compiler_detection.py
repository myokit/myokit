#!/usr/bin/env python3
#
# Tests the Compiler detection class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit


class CompilerDetectionTest(unittest.TestCase):
    """
    Tests the compiler detection.
    """
    def test_compiler(self):
        # Test the compiler detection.
        self.assertIsInstance(myokit.Compiler.info(), str)


if __name__ == '__main__':
    unittest.main()
