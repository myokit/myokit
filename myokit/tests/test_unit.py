#!/usr/bin/env python3
#
# Tests the Unit class
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


class MyokitUnitTest(unittest.TestCase):

    def test_create(self):
        # Test basic unit creation.

        myokit.Unit.parse_simple('mV')
        myokit.Unit.parse_simple('g')
        myokit.Unit.parse_simple('kg')

        myokit.Unit([0, 0, 0, 0, 0, 0, 0])
        self.assertRaises(ValueError, myokit.Unit, [0, 0, 0, 0, 0, 0])
        self.assertRaises(ValueError, myokit.Unit, [0, 0, 0, 0, 0, 0, 0, 0])

    def test_can_convert(self):
        # Test :meth:`Unit.can_convert()`.

        self.assertTrue(myokit.Unit.can_convert(
            myokit.units.volt, myokit.units.mV))
        self.assertFalse(myokit.Unit.can_convert(
            myokit.units.volt, myokit.units.ampere))

    def test_close(self):
        # Test the "close" method, to see if units are highly similar

        # Test for base unit without a prefix
        m = myokit.units.m
        m_close = m * (1 - 1e-15)
        m_far = m * 2
        not_m = m_close / m

        self.assertTrue(myokit.Unit.close(m, m))
        self.assertTrue(myokit.Unit.close(m, m_close))
        self.assertTrue(myokit.Unit.close(m_close, m))
        self.assertTrue(myokit.Unit.close(m_close, m_close))
        self.assertFalse(myokit.Unit.close(m, m_far))
        self.assertFalse(myokit.Unit.close(m, not_m))

        # Test for base unit with a prefix.
        # (Note that e.g. mV actually doesn't have an "m" when represented in
        # the base units Myokit uses!)
        mm = myokit.Unit.parse_simple('mm')
        mm_close = mm * (1 - 1e-15)
        mm_far = mm * 2
        not_mm = mm_close / mm

        self.assertTrue(myokit.Unit.close(m, m))
        self.assertTrue(myokit.Unit.close(m, m_close))
        self.assertTrue(myokit.Unit.close(m_close, m))
        self.assertTrue(myokit.Unit.close(m_close, m_close))
        self.assertFalse(myokit.Unit.close(m, m_far))
        self.assertFalse(myokit.Unit.close(m, not_m))

        # Test tiny, but feasible, units
        pF2 = myokit.units.pF**2
        not_pF2 = pF2 * 1.0001
        self.assertTrue(myokit.Unit.close(pF2, pF2))
        self.assertTrue(myokit.Unit.close(not_pF2, not_pF2))
        self.assertFalse(myokit.Unit.close(not_pF2, pF2))
        self.assertFalse(myokit.Unit.close(pF2, not_pF2))

        # The next test is not a requirement, but tests the current behaviour:
        u = myokit.units.m * 1.000000001
        self.assertTrue(myokit.Unit.close(u, myokit.units.m))

    def test_conversion_factor(self):
        # Test :meth:`Unit.conversion_factor()`.

        cf = myokit.Unit.conversion_factor
        q = myokit.Quantity
        u = myokit.parse_unit

        # Same units
        self.assertEqual(cf('V', 'V'), q(1))

        # Prefixed units
        self.assertEqual(cf('m', 'km'), q(0.001, '1 (1000)'))
        self.assertEqual(cf('km', 'm'), q(1000, '1 (0.001)'))
        self.assertEqual(cf('hm', 'm'), q(100, '1 (0.01)'))

        # Units with a multiplier
        cm_per_inch = cf('inches', 'cm')
        self.assertEqual(type(cm_per_inch), myokit.Quantity)
        self.assertEqual(cm_per_inch.value(), 2.54)
        self.assertEqual(cm_per_inch.unit(), u('cm/inches'))

        # Old unit: uA/cm^2
        # New unit: A/cm^2
        # To get from old to new, multiply by 1e-6 [1 (1e6)]
        # Because uA*(A/uA) = A,
        #   the unit for that factor is A/uA = 1/1e-6 = 1e6
        self.assertEqual(cf('uA/cm^2', 'A/cm^2'), q(1e-6, '1 (1e6)'))
        self.assertEqual(cf('uA/cm^2', 'A/cm^2'), q(1e-6, 'A/uA'))
        self.assertEqual(cf('uA/cm^2', 'A/cm^2'), q('1e-6 [A/uA]'))

        # Incompatible units
        self.assertRaises(
            myokit.IncompatibleUnitError, cf, u('g'), u('s'))
        self.assertRaises(
            myokit.IncompatibleUnitError, cf, u('N'), u('C'))

        # Convertible via helpers

        # Old unit: uA/cm^2
        # New unit: uA/uF
        # Helper: 2 [uF/cm^2]
        # To get from old to new, multiply by 0.5 [cm^2/uF]
        self.assertEqual(
            cf('uA/cm^2', 'uA/uF', ['0.5 [cm^2/uF]']), q(0.5, u('cm^2/uF')))
        self.assertEqual(
            cf('uA/cm^2', 'uA/uF', ['2 [uF/cm^2]']), q(0.5, u('cm^2/uF')))

        # Old unit: uA/uF = A/F = pA/pF
        # New unit: pA
        # Helper: 123 pF
        # To get from old to new, multiply by 123 [pF]
        self.assertEqual(
            cf('uA/uF', 'pA', ['123 [pF]']), q('123 [pF]'))
        self.assertEqual(
            cf('uA/uF', 'nA', ['123 [pF]']), q('0.123 [nF]'))
        self.assertEqual(
            cf('uA/cm^2', 'uA', ['0.123 [cm^2]']), q('0.123 [cm^2]'))

        # And:
        #   uA/cm^2 * cm^2 = uA
        #   uA/cm^2 * cm^2 * nA/uA = nA
        # So expecting 1 [cm^2] * 1000 [nA/uA] = 1000 [1 (1e-3)]
        # Factor in the 0.123 cm^2 to get 123 [cm^2 (1e-3)]
        self.assertEqual(
            cf('uA/cm^2', 'nA', ['0.123 [cm^2]']), q('123 [cm^2 (1e-3)]'))

        # Multiple factors to try
        h1 = ['123 [pF]', '0.123 [cm^2]']
        h2 = h1[::-1]
        self.assertEqual(cf('uA/uF', 'nA', h1), q('0.123 [nF]'))
        self.assertEqual(cf('uA/uF', 'nA', h2), q('0.123 [nF]'))
        self.assertEqual(cf('uA/cm^2', 'nA', h1), q('123 [cm^2 (1e-3)]'))
        self.assertEqual(cf('uA/cm^2', 'nA', h2), q('123 [cm^2 (1e-3)]'))

        # No good factors to try
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'even with', cf, 'mV', 'nA', h2)

    def test_convert(self):
        # Test :meth:`Unit.convert()`.

        # Test with float and int
        mV = myokit.units.mV
        V = myokit.units.V
        cv = myokit.Unit.convert
        self.assertEqual(cv(2, mV, V), 0.002)
        self.assertEqual(cv(2.0, V, mV), 2000)

        # Test with quantity
        q = myokit.Quantity
        self.assertEqual(cv(q(2, mV), mV, V), q(0.002, V))

        # None and dimensionless are ok
        d = myokit.units.dimensionless
        self.assertEqual(cv(1, None, None), 1)
        self.assertEqual(cv(1, d, None), 1)
        self.assertEqual(cv(1, None, d), 1)
        self.assertEqual(cv(1, d, d), 1)
        self.assertRaises(
            myokit.IncompatibleUnitError, myokit.Unit.convert, 1, d, V)
        self.assertRaises(
            myokit.IncompatibleUnitError, myokit.Unit.convert, 1, V, d)
        self.assertRaises(
            myokit.IncompatibleUnitError, myokit.Unit.convert, 1, None, V)
        self.assertRaises(
            myokit.IncompatibleUnitError, myokit.Unit.convert, 1, V, None)

        # Strings can be parsed
        self.assertEqual(cv(1, None, '1'), 1)
        self.assertEqual(cv(1, '1', None), 1)
        self.assertEqual(cv(1, 'V', V), 1)
        self.assertEqual(cv(1, V, 'V'), 1)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'from',
            myokit.Unit.convert, 1, V, 'A')
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'from',
            myokit.Unit.convert, 1, 'A', V)

    def test_exponents(self):
        # Test Unit.exponents

        x = myokit.Unit()
        self.assertEqual(x.exponents(), [0] * 7)

        x = myokit.units.m ** -2
        self.assertEqual(x.exponents(), [0, -2, 0, 0, 0, 0, 0])

    def test_float(self):
        # Test :meth:`Unit.__float__()`.
        x = myokit.Unit()
        x *= 123
        self.assertAlmostEqual(float(x), 123)

        # Can't convert unless dimensionless (but with any multiplier)
        x *= myokit.units.V
        self.assertRaises(TypeError, float, x)

    def test_operators(self):
        # Test overloaded unit operators.

        # Test div
        d = myokit.Unit()
        self.assertEqual(d.exponents(), [0] * 7)
        d = d / myokit.units.m
        self.assertEqual(d.exponents(), [0, -1, 0, 0, 0, 0, 0])
        d = d / myokit.units.m
        self.assertEqual(d.exponents(), [0, -2, 0, 0, 0, 0, 0])
        d = d / d
        self.assertEqual(d.exponents(), [0, 0, 0, 0, 0, 0, 0])

        # Test mul
        d = myokit.Unit()
        self.assertEqual(d.exponents(), [0] * 7)
        d = d * myokit.units.s
        self.assertEqual(d.exponents(), [0, 0, 1, 0, 0, 0, 0])
        d = d * myokit.units.m
        self.assertEqual(d.exponents(), [0, 1, 1, 0, 0, 0, 0])
        d = d * d
        self.assertEqual(d.exponents(), [0, 2, 2, 0, 0, 0, 0])

        # Test pow
        d = myokit.Unit()
        self.assertEqual(d.exponents(), [0] * 7)
        d *= myokit.units.s
        d *= myokit.units.m
        self.assertEqual(d.exponents(), [0, 1, 1, 0, 0, 0, 0])
        d = d**3
        self.assertEqual(d.exponents(), [0, 3, 3, 0, 0, 0, 0])

        # Test rdiv and rmul (i.e. with non-units)
        d = myokit.Unit()
        d *= myokit.units.meter
        self.assertEqual(d._m, 0)
        self.assertEqual(d.exponents(), [0, 1, 0, 0, 0, 0, 0])
        d = 1000 * d
        self.assertEqual(d._m, 3)
        d = 1 / d
        self.assertEqual(d._m, -3)
        self.assertEqual(d.exponents(), [0, -1, 0, 0, 0, 0, 0])
        d = 100 * d
        self.assertEqual(d._m, -1)
        d = 10 * d
        self.assertEqual(d._m, 0)

    def test_multiplier(self):
        # Test :meth:`Unit.multiplier()` and :meth:`Unit.multiplier_log_10`.
        d = myokit.Unit()
        d *= myokit.units.meter
        d *= 1000
        self.assertEqual(d.multiplier(), 1000)
        self.assertEqual(d.multiplier_log_10(), 3)

    def test_parse_simple(self):
        # Test edge cases for :meth:`Unit.parse_simple()`.

        # Easy case
        self.assertEqual(myokit.Unit.parse_simple('mV'), myokit.units.mV)

        # Bad quantifier
        self.assertRaisesRegex(
            KeyError, 'Unknown quantifier', myokit.Unit.parse_simple, 'jV')

        # Not a quantifiable unit
        self.assertRaisesRegex(
            KeyError, 'cannot have quantifier', myokit.Unit.parse_simple,
            'mNewton')

        # Unknown unit
        self.assertRaisesRegex(
            KeyError, 'Unknown unit', myokit.Unit.parse_simple, 'Frog')

    def test_powers(self):
        # Fractional powers are allowed now

        m2 = myokit.units.m**2
        s15 = myokit.units.s**1.5
        mol123 = myokit.units.mol**1.23
        x = m2 * s15 / mol123
        self.assertEqual(x.exponents(), [0, 2, 1.5, 0, 0, 0, -1.23])

    def test_register_errors(self):
        # Test errors for Unit.register (rest is already used a lot).
        self.assertRaises(TypeError, myokit.Unit.register, 4, myokit.Unit())
        self.assertRaises(TypeError, myokit.Unit.register, 'hi', 4)

    def test_register_preferred_representation(self):
        # Test new representations can be registered

        u = myokit.units.m**8
        self.assertEqual(str(u), '[m^8]')
        try:
            myokit.Unit.register_preferred_representation(
                'abc', myokit.units.m**8)
            self.assertEqual(str(u), '[abc]')

            self.assertRaisesRegex(
                ValueError, 'must be a myokit.Unit',
                myokit.Unit.register_preferred_representation, 'x', 123)

        finally:
            # Bypassing the public API, this is bad test design!
            if u in myokit.Unit._preferred_representations:
                del myokit.Unit._preferred_representations[u]

    def test_str(self):
        # Test :meth:`Unit.str()`

        # Unit with representation in alternative base
        km_per_s = myokit.Unit([0, 1, -1, 0, 0, 0, 0], 3)

        # Myokit doesn't know km/s, it does know m/s so this should become:
        self.assertEqual(str(km_per_s), '[m/s (1000)]')

        # Myokit doesn't know MA/m^2
        mam2 = myokit.parse_unit('MA/m^2')
        self.assertEqual(str(mam2), '[A/m^2 (1e+06)]')

        # Simple units
        m = myokit.parse_unit('m')
        self.assertEqual(str(m), '[m]')
        im = 1 / m
        self.assertEqual(str(im), '[1/m]')

        # Predefined complex unit
        self.assertEqual(str(myokit.units.N), '[N]')

        # Low mulipliers
        um = m * 1e-6
        self.assertEqual(str(um), '[um]')
        um3 = myokit.parse_unit('um^3')
        self.assertEqual(str(um3), '[um^3]')
        attomol = myokit.parse_unit('amol')
        self.assertEqual(str(attomol), '[mol (1e-18)]')

        # High multipliers
        nn = myokit.units.N * 1e-2
        self.assertEqual(str(nn), '[N (0.01)]')
        nn = myokit.units.N * 1e2
        self.assertEqual(str(nn), '[N (100)]')
        nn = myokit.units.N * 1e7
        self.assertEqual(str(nn), '[N (1e+07)]')

        # Unit very similar to a known unit
        c = myokit.units.V
        d = c * 1.000000001
        self.assertFalse(c == d)
        self.assertTrue(myokit.Unit.close(c, d))
        self.assertEqual(str(c), '[V]')
        self.assertEqual(str(d), '[V]')

    def test_repr(self):
        # Test :meth:`Unit.repr()`.

        # Simple units
        m = myokit.parse_unit('m')
        self.assertEqual(repr(m), '[m]')
        im = 1 / m
        self.assertEqual(repr(im), '[1/m]')
        um = m * 1e-6

        # Predefined complex unit
        self.assertEqual(repr(myokit.units.N), '[g*m/s^2 (1000)]')

        # Low multipliers
        self.assertEqual(repr(um), '[m (1e-06)]')
        um3 = myokit.parse_unit('um^3')
        self.assertEqual(repr(um3), '[m^3 (1e-18)]')

        # High multipliers
        nn = myokit.units.N * 1e-2
        self.assertEqual(repr(nn), '[g*m/s^2 (10)]')
        nn = myokit.units.N * 1e7
        self.assertEqual(repr(nn), '[g*m/s^2 (1e+10)]')


if __name__ == '__main__':
    unittest.main()
