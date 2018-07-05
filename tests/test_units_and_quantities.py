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
from myokit import (
    parse_unit as pu,
    parse_expression as pe,
    IncompatibleUnitError as E,
    UNIT_STRICT as S,
    UNIT_TOLERANT as T,
    Name, Derivative,
)


class MyokitUnitTest(unittest.TestCase):

    def test_create(self):
        """
        Test basic unit creation.
        """
        myokit.Unit.parse_simple('mV')
        myokit.Unit.parse_simple('g')
        myokit.Unit.parse_simple('kg')

    def test_convert(self):
        """
        Test unit conversion.
        """
        mV = myokit.Unit.parse_simple('mV')
        V = myokit.Unit.parse_simple('V')
        self.assertEqual(myokit.Unit.convert(2, mV, V), 0.002)
        self.assertEqual(myokit.Unit.convert(2, V, mV), 2000)

    def test_output(self):
        """
        Test unit representation.
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
    def test_basic(self):
        """
        Tests the basic functionality of the Quantity class.
        """
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

        # Conversion from myokit number
        from myokit import Number as N
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

        # Use in set_rhs
        m = myokit.Model()
        c = m.add_component('a')
        v = c.add_variable('v')
        v.set_rhs(a)
        self.assertEqual(v.rhs().unit(), myokit.units.mV)
        self.assertEqual(v.eval(), 10)

        # Equality and inequality
        a = Q('10 [mV]')
        self.assertEqual(a, Q('10 [mV]'))
        self.assertNotEqual(a, Q('11 [mV]'))
        self.assertNotEqual(a, Q('10 [mA]'))
        self.assertNotEqual(a, Q('10 [V]'))
        self.assertNotEqual(a, Q('0.01 [V]'))
        self.assertEqual(a, Q('0.01 [V]').convert('mV'))

        # Conversion
        a = Q('10 [mV]')
        self.assertEqual(a.convert('V'), Q('0.01 [V]'))

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

        # Cast
        a = Q('10 [uA]')
        b = a.cast('mV')
        self.assertEqual(a, Q('10 [uA]'))
        self.assertEqual(b, Q('10 [mV]'))


if __name__ == '__main__':
    unittest.main()
