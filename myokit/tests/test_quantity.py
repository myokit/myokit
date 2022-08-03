#!/usr/bin/env python3
#
# Tests the Quantity class
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


class QuantityTest(unittest.TestCase):
    """
    Tests the Quantity class for unit arithmetic.
    """

    def test_as_rhs(self):
        # Test Quantity use in set_rhs.
        from myokit import Quantity as Q

        m = myokit.Model()
        c = m.add_component('a')
        v = c.add_variable('v')
        a = Q('10 [mV]')
        v.set_rhs(a)
        self.assertEqual(v.rhs().unit(), myokit.units.mV)
        self.assertEqual(v.eval(), 10)

    def test_cast(self):
        # Test :meth:`Quanity.cast()`.

        from myokit import Quantity as Q

        a = Q('10 [uA]')
        b = a.cast('mV')
        self.assertEqual(a, Q('10 [uA]'))
        self.assertEqual(b, Q('10 [mV]'))

    def test_convert(self):
        # Test :meth:`Quantity.convert()`.

        from myokit import Quantity as Q

        a = Q('10 [mV]')
        self.assertEqual(a.convert('V'), Q('0.01 [V]'))

    def test_creation_and_str(self):
        # Test Quanity creation and :meth:`Quantity.__str__()`.

        from myokit import Quantity as Q

        # Creation and string representation
        a = Q('10 [mV]')
        self.assertEqual(float(a), 10)
        self.assertEqual(str(a), '10.0 [mV]')
        a = Q('2', myokit.units.uA)
        self.assertEqual(float(a), 2)
        self.assertEqual(str(a), '2.0 [uA]')
        a = Q(-2, 'uA/cm^2')
        self.assertEqual(float(a), -2)
        self.assertEqual(str(a), '-2.0 [uA/cm^2]')
        a = Q(3.0e1, 'km/N/g')
        self.assertEqual(float(a), 30)
        self.assertEqual(str(a), '30.0 [s^2/g^2]')
        a = Q(4)
        self.assertEqual(float(a), 4)
        self.assertEqual(str(a), '4.0 [1]')

        # Repr
        self.assertEqual(repr(a), '4.0 [1]')

        # Creation from a myokit Number
        x = myokit.Number(2)
        a = Q(x)
        self.assertRaisesRegex(
            ValueError, 'Cannot specify', Q, x, myokit.Unit())

        # Creation with string value
        x = myokit.Quantity('2')
        x = myokit.Quantity('2 [mV]')
        self.assertRaisesRegex(
            ValueError, 'could not be converted', myokit.Quantity, int)
        self.assertRaisesRegex(
            ValueError, 'Failed to parse', myokit.Quantity, 'wolf')
        self.assertRaisesRegex(
            ValueError, 'Failed to parse', myokit.Quantity, 'a [mV]')
        x = myokit.Quantity('2', 'mV')
        self.assertRaisesRegex(
            ValueError, 'Two units', myokit.Quantity, '2 [mV]', 'mV')

    def test_eq(self):
        # Test :meth:`Quantity.__eq__()`.
        from myokit import Quantity as Q

        a = Q('10 [mV]')
        self.assertEqual(a, Q('10 [mV]'))
        self.assertNotEqual(a, Q('11 [mV]'))
        self.assertNotEqual(a, Q('10 [mA]'))
        self.assertNotEqual(a, Q('10 [V]'))
        self.assertNotEqual(a, Q('0.01 [V]'))
        self.assertEqual(a, Q('0.01 [V]').convert('mV'))
        self.assertFalse(Q(4) == 4)
        self.assertFalse(4 == Q(4))

    def test_hash(self):
        # Test has does not change in quantity's lifetime

        try:
            u = myokit.units.m**8
            q1 = myokit.Quantity(1, u)
            h1 = hash(q1)
            myokit.Unit.register_preferred_representation('abc', u)
            q2 = myokit.Quantity(1, u)
            h2 = hash(q2)
            self.assertEqual(h1, h2)
        finally:
            # Bypassing the public API, this is bad test design!
            if u in myokit.Unit._preferred_representations:
                del myokit.Unit._preferred_representations[u]

    def test_number_conversion(self):
        # Test Quantity conversion from and to number.

        from myokit import Quantity as Q
        from myokit import Number as N

        # Conversion from number
        d = N(4)
        self.assertIsNone(d.unit())
        e = Q(d)
        self.assertEqual(float(e), 4)
        self.assertIsNotNone(e.unit())
        self.assertEqual(e.unit(), myokit.units.dimensionless)
        self.assertEqual(str(e), '4.0 [1]')

        # Conversion to number
        a = Q('10 [mV]')
        b = myokit.Number(a)
        self.assertEqual(b.eval(), 10)
        self.assertEqual(b.unit(), myokit.units.mV)

    def test_operators(self):
        # Test overloaded operators for Quantity.

        from myokit import Quantity as Q

        # Addition
        a = Q('10 [mV]')
        b = Q('3 [mV]')
        self.assertEqual(a + b, Q('13 [mV]'))
        self.assertEqual(a + Q('-4.2 [mV]'), Q('5.8 [mV]'))

        def add(a, b):
            return a + b
        self.assertEqual(add(a, b), Q('13 [mV]'))
        b = Q('3 [V]')
        self.assertRaises(myokit.IncompatibleUnitError, add, a, b)
        self.assertRaises(myokit.IncompatibleUnitError, add, a, 3)
        a = Q(4)
        self.assertEqual(a + 2, Q(6))
        self.assertEqual(a + 3, Q(7, myokit.units.dimensionless))
        self.assertEqual(a + 4, Q('8'))
        self.assertEqual(a + 5, Q('9 [1]'))
        self.assertEqual(a + 2, 2 + a)
        self.assertRaises(myokit.IncompatibleUnitError, add, a, b)

        # Subtraction
        a = Q('10 [mV]')
        b = Q('3 [mV]')
        self.assertEqual(a - b, Q('7 [mV]'))
        self.assertEqual(a - Q('-4.2 [mV]'), Q('14.2 [mV]'))

        def sub(a, b):
            return a - b
        self.assertEqual(sub(a, b), Q('7 [mV]'))
        b = Q('3 [V]')
        self.assertRaises(myokit.IncompatibleUnitError, sub, a, b)
        a = Q(10)
        self.assertEqual(a - 2, Q(8))
        self.assertEqual(a - 3, Q(7, myokit.units.dimensionless))
        self.assertEqual(a - 4, Q('6'))
        self.assertEqual(a - 5, Q('5 [1]'))
        self.assertEqual(Q(10) - 2, 10 - Q(2))
        self.assertRaises(myokit.IncompatibleUnitError, sub, a, b)

        # Multiplication
        a = Q(2)
        b = Q(3)
        self.assertEqual(a * b, Q(6))
        self.assertEqual(3 * b, Q(9))
        self.assertEqual(a * 4, Q(8))
        a = Q('10 [mV]')
        b = Q('2 [uA]')
        self.assertEqual(a * b, Q('20 [nW]'))
        self.assertEqual(a * 5, 5 * a)
        self.assertEqual(a * 5, Q('50 [mV]'))
        self.assertEqual(a * 1000, Q('10000 [mV]'))
        self.assertEqual((a * 1000).convert('V'), Q('10 [V]'))

        # Division
        a = Q('10 [uA]')
        b = Q('2 [mV]')
        c = a / b
        self.assertEqual(c, Q('5 [mS]'))
        self.assertEqual(float(c), 5.0)
        self.assertEqual(str(c), '5.0 [mS]')
        self.assertEqual(b.convert('V'), Q('0.002 [V]'))
        self.assertRaises(myokit.IncompatibleUnitError, a.convert, 'V')
        a = Q(3)
        self.assertEqual(a / 2, Q(3 / 2))

        a = Q('10 [uA]')
        self.assertEqual(a / 2, Q('5 [uA]'))
        self.assertEqual(2 / a, Q('0.2 [1/uA]'))

        # Powers
        a = Q('10 [uA]')
        self.assertEqual(a ** 2, Q('100 [uA^2]'))
        self.assertEqual(a ** 3, Q('1000 [uA^3]'))
        self.assertEqual(a ** Q(3), Q('1000 [uA^3]'))
        a = Q('10 [uA]') ** 3
        b = a ** (1 / 3)
        self.assertEqual(b.unit(), myokit.units.uA)
        self.assertAlmostEqual(b.value(), 10)
        with self.assertRaises(myokit.IncompatibleUnitError):
            a ** a


if __name__ == '__main__':
    unittest.main()
