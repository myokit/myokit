#!/usr/bin/env python
#
# Tests the UserFunction class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import myokit

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


# Further testing in test_model.py


class UserFunctionTest(unittest.TestCase):
    """ Tests :class:`UserFunction`. """

    def test_user_function(self):
        # Test :class:`UserFunction` creation and methods.

        # Create without arguments
        f = myokit.UserFunction('bert', [], myokit.Number(12))
        args = list(f.arguments())
        self.assertEqual(len(args), 0)
        self.assertEqual(f.convert([]), myokit.Number(12))

        # Create with one argument
        f = myokit.UserFunction(
            'x', [myokit.Name('a')], myokit.parse_expression('1 + a'))
        self.assertEqual(len(list(f.arguments())), 1)
        args = {myokit.Name('a'): myokit.Number(3)}
        self.assertEqual(f.convert(args).eval(), 4)

        # Create with two argument
        f = myokit.UserFunction(
            'x', [myokit.Name('a'), myokit.Name('b')],
            myokit.parse_expression('a + b'))
        self.assertEqual(len(list(f.arguments())), 2)
        args = {
            myokit.Name('a'): myokit.Number(3),
            myokit.Name('b'): myokit.Number(4)
        }
        self.assertEqual(f.convert(args), myokit.parse_expression('3 + 4'))

        # Call with wrong arguments
        del args[myokit.Name('a')]
        self.assertRaisesRegex(
            ValueError, 'Wrong number', f.convert, args)
        args[myokit.Name('c')] = myokit.Number(100)
        self.assertRaisesRegex(
            ValueError, 'Missing input argument', f.convert, args)


if __name__ == '__main__':
    unittest.main()
