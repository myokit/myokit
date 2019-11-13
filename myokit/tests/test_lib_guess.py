#!/usr/bin/env python
#
# Tests the lib.guess variable meaning guessing module
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.lib.guess as guess

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class LibGuessTest(unittest.TestCase):

    def test_distance_to_bound(self):
        # Tests the (hidden) method to calculate the distance to a bound
        # variable

        # Test case 1
        # Get distance to env.time, but only for variables that depend on
        # time but are otherwise constant
        m = myokit.parse_model("""
            [[model]]
            c.a = 1

            [env]
            time = 0 bind time

            [c]
            dot(a) = (b + 7) / a + c
            b = exp(a)
            c = 10 * b + d
            d = 1 + e
            e = 2 + f
            f = 3 / env.time
            g = 4 + e
            """)
        d = guess._distance_to_bound(m.get('env.time'))
        self.assertEqual(len(d), 4)
        self.assertEqual(d[m.get('c.d')], 3)
        self.assertEqual(d[m.get('c.e')], 2)
        self.assertEqual(d[m.get('c.f')], 1)
        self.assertEqual(d[m.get('c.g')], 3)
        self.assertEqual(m.get('env.time').binding(), 'time')

        # Test case 2
        m = myokit.parse_model("""
            [[model]]
            c.a = 1

            [env]
            time = 0 bind time

            [c]
            dot(a) = (b + 7) / a + c
            b = exp(a) + j
            c = 1 + env.time
            d = 2 / env.time
            e = 3 * env.time
            f = c + d
            g = j ^ d
            h = 1 - e
            i = cos(e)
            j = 2 * f
            """)
        d = guess._distance_to_bound(m.get('env.time'))
        self.assertEqual(len(d), 8)
        self.assertEqual(d[m.get('c.c')], 1)
        self.assertEqual(d[m.get('c.d')], 1)
        self.assertEqual(d[m.get('c.e')], 1)
        self.assertEqual(d[m.get('c.f')], 2)
        self.assertEqual(d[m.get('c.g')], 2)
        self.assertEqual(d[m.get('c.h')], 2)
        self.assertEqual(d[m.get('c.i')], 2)
        self.assertEqual(d[m.get('c.j')], 3)
        self.assertEqual(m.get('env.time').binding(), 'time')

        # Can only be called on bound variable
        self.assertRaisesRegex(
            ValueError, 'must be a bound variable',
            guess._distance_to_bound, m.get('c.a'))
        self.assertRaisesRegex(
            ValueError, 'must be a bound variable',
            guess._distance_to_bound, m.get('c.c'))


if __name__ == '__main__':
    unittest.main()
