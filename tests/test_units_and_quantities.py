#!/usr/bin/env python
#
# Tests the unit and quantity classes
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit


class MyokitUnitTest(unittest.TestCase):

    def test_create(self):
        """
        Test basic unit creation.
        """
        myokit.Unit.parse_simple('mV')
        myokit.Unit.parse_simple('g')
        myokit.Unit.parse_simple('kg')

        myokit.Unit([0, 0, 0, 0, 0, 0, 0])
        self.assertRaises(ValueError, myokit.Unit, [0, 0, 0, 0, 0, 0])
        self.assertRaises(ValueError, myokit.Unit, [0, 0, 0, 0, 0, 0, 0, 0])

    def test_can_convert(self):
        """
        Tests :meth:`Unit.can_convert()`.
        """
        self.assertTrue(myokit.Unit.can_convert(
            myokit.units.volt, myokit.units.mV))
        self.assertFalse(myokit.Unit.can_convert(
            myokit.units.volt, myokit.units.ampere))

    def test_convert(self):
        """
        Test :meth:`Unit.convert()`.
        """
        mV = myokit.units.mV
        V = myokit.units.V
        self.assertEqual(myokit.Unit.convert(2, mV, V), 0.002)
        self.assertEqual(myokit.Unit.convert(2, V, mV), 2000)

        # None and dimensionless are ok
        d = myokit.units.dimensionless
        self.assertEqual(myokit.Unit.convert(1, None, None), 1)
        self.assertEqual(myokit.Unit.convert(1, d, None), 1)
        self.assertEqual(myokit.Unit.convert(1, None, d), 1)
        self.assertEqual(myokit.Unit.convert(1, d, d), 1)
        self.assertRaises(
            myokit.IncompatibleUnitError, myokit.Unit.convert, 1, d, V)
        self.assertRaises(
            myokit.IncompatibleUnitError, myokit.Unit.convert, 1, V, d)
        self.assertRaises(
            myokit.IncompatibleUnitError, myokit.Unit.convert, 1, None, V)
        self.assertRaises(
            myokit.IncompatibleUnitError, myokit.Unit.convert, 1, V, None)

        # Strings can be parsed
        self.assertEqual(myokit.Unit.convert(1, None, '1'), 1)
        self.assertEqual(myokit.Unit.convert(1, '1', None), 1)
        self.assertEqual(myokit.Unit.convert(1, 'V', V), 1)
        self.assertEqual(myokit.Unit.convert(1, V, 'V'), 1)
        self.assertRaisesRegexp(
            myokit.IncompatibleUnitError, 'from',
            myokit.Unit.convert, 1, V, 'A')
        self.assertRaisesRegexp(
            myokit.IncompatibleUnitError, 'from',
            myokit.Unit.convert, 1, 'A', V)
        self.assertRaisesRegexp(
            myokit.IncompatibleUnitError, 'given object',
            myokit.Unit.convert, 1, V, 'Alf')
        self.assertRaisesRegexp(
            myokit.IncompatibleUnitError, 'given object',
            myokit.Unit.convert, 1, 'Alf', V)

    def test_float(self):
        """ Tests :meth:`Unit.__float__()`. """
        x = myokit.Unit()
        x *= 123
        self.assertAlmostEqual(float(x), 123)

        # Can't convert unless dimensionless (but with any multiplier)
        x *= myokit.units.V
        self.assertRaises(TypeError, float, x)

    def test_operators(self):
        """ Tests overloaded unit operators. """
        # Test div
        d = myokit.Unit()
        self.assertEqual(d._x, [0] * 7)
        d = d / myokit.units.m
        self.assertEqual(d._x, [0, -1, 0, 0, 0, 0, 0])
        d = d / myokit.units.m
        self.assertEqual(d._x, [0, -2, 0, 0, 0, 0, 0])
        d = d / d
        self.assertEqual(d._x, [0, 0, 0, 0, 0, 0, 0])

        # Test mul
        d = myokit.Unit()
        self.assertEqual(d._x, [0] * 7)
        d = d * myokit.units.s
        self.assertEqual(d._x, [0, 0, 1, 0, 0, 0, 0])
        d = d * myokit.units.m
        self.assertEqual(d._x, [0, 1, 1, 0, 0, 0, 0])
        d = d * d
        self.assertEqual(d._x, [0, 2, 2, 0, 0, 0, 0])

        # Test pow
        d = myokit.Unit()
        self.assertEqual(d._x, [0] * 7)
        d *= myokit.units.s
        d *= myokit.units.m
        self.assertEqual(d._x, [0, 1, 1, 0, 0, 0, 0])
        d = d**3
        self.assertEqual(d._x, [0, 3, 3, 0, 0, 0, 0])

        # Test rdiv and rmul (i.e. with non-units)
        d = myokit.Unit()
        d *= myokit.units.meter
        self.assertEqual(d._m, 0)
        self.assertEqual(d._x, [0, 1, 0, 0, 0, 0, 0])
        d = 1000 * d
        self.assertEqual(d._m, 3)
        d = 1 / d
        self.assertEqual(d._m, -3)
        self.assertEqual(d._x, [0, -1, 0, 0, 0, 0, 0])
        d = 100 * d
        self.assertEqual(d._m, -1)
        d = 10 * d
        self.assertEqual(d._m, 0)

    def test_parse_simple(self):
        """
        Tests edge cases for :meth:`Unit.parse_simple()`.
        """
        # Easy case
        self.assertEqual(myokit.Unit.parse_simple('mV'), myokit.units.mV)

        # Bad quantifier
        self.assertRaisesRegexp(
            KeyError, 'Unknown quantifier', myokit.Unit.parse_simple, 'jV')

        # Not a quantifiable unit
        self.assertRaisesRegexp(
            KeyError, 'cannot have quantifier', myokit.Unit.parse_simple,
            'mNewton')

        # Unknown unit
        self.assertRaisesRegexp(
            KeyError, 'Unknown unit', myokit.Unit.parse_simple, 'Frog')

    def test_register_errors(self):
        """ Tests errors for Unit.register (rest is already used a lot). """
        self.assertRaises(TypeError, myokit.Unit.register, 4, myokit.Unit())
        self.assertRaises(TypeError, myokit.Unit.register, 'hi', 4)

    def test_str_and_repr(self):
        """
        Test :meth:`Unit.str()` and :meth:`Unit.repr()`.
        """
        self.assertEqual(repr(myokit.units.N), '[g*m/s^2 (1000)]')
        # Unit with representation in alternative base
        km_per_s = myokit.Unit([0, 1, -1, 0, 0, 0, 0], 3)
        # Myokit doesn't know km/s, it does know m/s so this should become:
        self.assertEqual(str(km_per_s), '[m/s (1000)]')
        # Myokit doesn't know MA/m^2
        mam2 = myokit.parse_unit('MA/m^2')
        self.assertEqual(str(mam2), '[A/m^2 (1000000)]')


class QuantityTest(unittest.TestCase):
    """
    Tests the Quantity class for unit arithmetic.
    """
    def test_creation_and_str(self):
        """ Tests Quanity creation and :meth:`Quantity.__str__()`. """
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

        # Creation from a myokit Number
        x = myokit.Number(2)
        a = Q(x)
        self.assertRaisesRegexp(
            ValueError, 'Cannot specify', Q, x, myokit.Unit())

        # Creation with string value
        x = myokit.Quantity('2')
        x = myokit.Quantity('2 [mV]')
        self.assertRaisesRegexp(
            ValueError, 'could not be converted', myokit.Quantity, int)
        self.assertRaisesRegexp(
            ValueError, 'Failed to parse', myokit.Quantity, 'wolf')
        self.assertRaisesRegexp(
            ValueError, 'Failed to parse', myokit.Quantity, 'a [mV]')
        x = myokit.Quantity('2', 'mV')
        self.assertRaisesRegexp(
            ValueError, 'Two units', myokit.Quantity, '2 [mV]', 'mV')

    def test_number_conversion(self):
        """ Tests Quantity conversion from and to number. """
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

    def test_as_rhs(self):
        """ Test Quantity use in set_rhs. """
        from myokit import Quantity as Q

        m = myokit.Model()
        c = m.add_component('a')
        v = c.add_variable('v')
        a = Q('10 [mV]')
        v.set_rhs(a)
        self.assertEqual(v.rhs().unit(), myokit.units.mV)
        self.assertEqual(v.eval(), 10)

    def test_eq(self):
        """ Test :meth:`Quantity.__eq__()`. """
        from myokit import Quantity as Q

        a = Q('10 [mV]')
        self.assertEqual(a, Q('10 [mV]'))
        self.assertNotEqual(a, Q('11 [mV]'))
        self.assertNotEqual(a, Q('10 [mA]'))
        self.assertNotEqual(a, Q('10 [V]'))
        self.assertNotEqual(a, Q('0.01 [V]'))
        self.assertEqual(a, Q('0.01 [V]').convert('mV'))

    def test_convert(self):
        """ Test :meth:`Quantity.convert()`. """
        from myokit import Quantity as Q

        a = Q('10 [mV]')
        self.assertEqual(a.convert('V'), Q('0.01 [V]'))

    def test_operators(self):
        """ Test overloaded operators for Quantity. """
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

    def test_cast(self):
        """ Test :meth:`Quanity.cast()`. """
        from myokit import Quantity as Q

        a = Q('10 [uA]')
        b = a.cast('mV')
        self.assertEqual(a, Q('10 [uA]'))
        self.assertEqual(b, Q('10 [mV]'))


if __name__ == '__main__':
    unittest.main()
