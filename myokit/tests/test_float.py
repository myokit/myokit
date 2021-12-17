#!/usr/bin/env python3
#
# Tests the methods and classes in myokit.floats
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import sys
import unittest

import myokit


class FloatTest(unittest.TestCase):
    """Tests the methods in ``myokit.float``."""

    def test_close(self):
        # Test that close allows bigger errors than eq
        x = 49
        y = x * (1 + 1e-11)
        self.assertNotEqual(x, y)
        self.assertFalse(myokit.float.eq(x, y))
        self.assertTrue(myokit.float.close(x, y))

        # And that close thinks everything small is equal
        x = 1e-16
        y = 1e-12
        self.assertNotEqual(x, y)
        self.assertFalse(myokit.float.eq(x, y))
        self.assertTrue(myokit.float.close(x, y))

    def test_cround(self):
        # Test rounding based on closeness
        x = 49
        y = x * (1 + 1e-11)
        self.assertNotEqual(x, y)
        self.assertEqual(x, myokit.float.cround(y))
        self.assertIsInstance(myokit.float.cround(y), int)
        self.assertNotEqual(x, myokit.float.cround(49.001))

    def test_eq_and_geq(self):
        # Test the floating point comparison methods

        # Check that test is going to work
        x = 49
        y = 1 / (1 / x)
        self.assertNotEqual(x, y)

        # Test if eq allows 1 floating point error
        self.assertTrue(myokit.float.eq(x, y))
        self.assertTrue(myokit.float.geq(x, y))
        self.assertTrue(myokit.float.geq(y, x))
        x += x * sys.float_info.epsilon
        self.assertTrue(myokit.float.eq(x, y))
        self.assertTrue(myokit.float.geq(x, y))
        self.assertTrue(myokit.float.geq(y, x))
        x += x * sys.float_info.epsilon
        self.assertFalse(myokit.float.eq(x, y))
        self.assertTrue(myokit.float.geq(x, y))
        self.assertFalse(myokit.float.geq(y, x))

    def test_round(self):
        # Test rounding, ignoring single rounding errors

        # Check that test is going to work
        x = 49
        y = 1 / (1 / x)
        self.assertNotEqual(x, y)
        x += 2 * x * sys.float_info.epsilon
        self.assertFalse(myokit.float.eq(x, y))
        self.assertTrue(myokit.float.geq(x, y))
        self.assertFalse(myokit.float.geq(y, x))

        # Test rounding
        self.assertNotEqual(49, y)
        self.assertEqual(49, myokit.float.round(y))
        self.assertNotEqual(49, myokit.float.round(x))
        self.assertEqual(0.5, myokit.float.round(0.5))
        self.assertIsInstance(myokit.float.round(y), int)

        # Try with negative numbers
        self.assertNotEqual(-49, -y)
        self.assertEqual(-49, myokit.float.round(-y))
        self.assertNotEqual(-49, myokit.float.round(-x))
        self.assertEqual(-0.5, myokit.float.round(-0.5))

    def test_str(self):
        # Test float to string conversion.

        # String should be passed through
        # Note: convert to str() to test in python 2 and 3.
        self.assertEqual(myokit.float.str(str('123')), '123')

        # Simple numbers
        self.assertEqual(myokit.float.str(0), '0')
        self.assertEqual(myokit.float.str(0.0000), '0.0')
        self.assertEqual(myokit.float.str(1.234), '1.234')
        self.assertEqual(
            myokit.float.str(0.12432656245e12), ' 1.24326562450000000e+11')
        self.assertEqual(myokit.float.str(-0), '0')
        self.assertEqual(myokit.float.str(-0.0000), '-0.0')
        self.assertEqual(myokit.float.str(-1.234), '-1.234')
        self.assertEqual(
            myokit.float.str(-0.12432656245e12), '-1.24326562450000000e+11')

        # Strings are not converted
        x = '1.234'
        self.assertEqual(x, myokit.float.str(x))

        # Myokit Numbers are converted
        x = myokit.Number(1.23)
        self.assertEqual(myokit.float.str(x), '1.23')

        # Single and double precision
        self.assertEqual(
            myokit.float.str(-1.234, precision=myokit.SINGLE_PRECISION),
            '-1.234')
        self.assertEqual(
            myokit.float.str(
                -0.124326562458734682153498731245756e12,
                precision=myokit.SINGLE_PRECISION),
            '-1.243265625e+11')
        self.assertEqual(
            myokit.float.str(-1.234, precision=myokit.DOUBLE_PRECISION),
            '-1.234')
        self.assertEqual(
            myokit.float.str(
                -0.124326562458734682153498731245756e12,
                precision=myokit.DOUBLE_PRECISION),
            '-1.24326562458734680e+11')

        # Full precision override
        self.assertEqual(
            myokit.float.str(1.23, True), ' 1.22999999999999998e+00')
        self.assertEqual(
            myokit.float.str(1.23, True, myokit.DOUBLE_PRECISION),
            ' 1.22999999999999998e+00')
        self.assertEqual(
            myokit.float.str(1.23, True, myokit.SINGLE_PRECISION),
            ' 1.230000000e+00')


if __name__ == '__main__':
    unittest.main()
