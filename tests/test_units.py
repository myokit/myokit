#!/usr/bin/env python
#
# Tests the unit-checking tool.
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


class ExpressionUnitTest(unittest.TestCase):
    """
    Tests the unit checking / arithmetic methods in expressions.
    """
    @classmethod
    def setUpClass(self):
        # Using the @classmethod setUpClass, this set up is only run once
        self.m = myokit.load_model('example')
        self.v = self.m.get('membrane.V')
        self.v.rename('v')
        self.v.set_unit('mV')
        # Save for resetting
        self._v_unit = 'mV'
        self._v_rhs = self.v.rhs()

    @classmethod
    def tearDownClass(self):
        del(self.m)

    def reset(self):
        self.v.set_unit(self._v_unit)
        self.v.set_rhs(self._v_rhs)

    def test_number(self):
        x = myokit.Number(12, pu('kmol^2*s'))
        self.assertEqual(x.unit(), x.eval_unit())
        self.assertEqual(x.unit(), pu('kmol^2*s'))
        self.assertNotEqual(x.unit(), None)
        x = myokit.Number(9)
        self.assertEqual(x.unit(), x.eval_unit())
        self.assertEqual(x.unit(), None)

    def test_name(self):
        self.v.set_rhs('3 [m/s]')
        self.assertEqual(self.v.rhs().eval_unit(), pu('m/s'))
        self.assertEqual(self.v.unit(), pu('mV'))
        # Reset
        self.reset()

    def test_derivative(self):
        t = self.m.time()
        t.set_unit(None)
        d = Derivative(Name(self.v))
        self.assertEqual(d.eval_unit(), pu('mV'))
        t.set_unit('ms')
        self.assertEqual(d.eval_unit(), pu('mV/ms'))
        self.assertEqual(d.eval_unit(), pu('V/s'))

    def test_prefix_plus(self):
        self.v.set_rhs('+5 [mV]')
        self.assertEqual(self.v.rhs().eval_unit(), pu('mV'))
        self.v.set_rhs('+5')
        self.assertEqual(self.v.rhs().eval_unit(), None)
        self.v.set_rhs('+v')
        self.assertEqual(self.v.rhs().eval_unit(), pu('mV'))
        # Reset
        self.reset()

    def test_prefix_minus(self):
        self.v.set_rhs('-2 [kg]')
        self.assertEqual(self.v.rhs().eval_unit(), pu('kg'))
        self.v.set_rhs('-2')
        self.assertEqual(self.v.rhs().eval_unit(), None)
        # Reset
        self.reset()

    def test_plus(self):
        self.v.set_rhs('3 [kg] + 2 [m]')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertRaises(E, self.v.rhs().eval_unit, T)
        self.v.set_rhs('3 [kg] + 2')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('kg'))
        self.v.set_rhs('3 [1] + 2')
        self.v.rhs().eval_unit(S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('3 + 2')
        self.v.rhs().eval_unit(S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        self.v.set_rhs('3 + 2 [cd]')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('cd'))
        self.v.set_rhs('3 + 2 [1]')
        self.v.rhs().eval_unit(S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        # Reset
        self.reset()

    def test_minus(self):
        self.v.set_rhs('3 [kg] - 2 [m]')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertRaises(E, self.v.rhs().eval_unit, T)
        self.v.set_rhs('3 [kg] - 2')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('kg'))
        self.v.set_rhs('3 [1] - 2')
        self.v.rhs().eval_unit(S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('3 - 2')
        self.v.rhs().eval_unit(S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        self.v.set_rhs('3 - 2 [cd]')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('cd'))
        self.v.set_rhs('3 - 2 [1]')
        self.v.rhs().eval_unit(S)
        self.v.rhs().eval_unit(T)
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        # Reset
        self.reset()

    def test_multiply(self):
        self.v.set_rhs('3 [kg] * 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('kg*m'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('kg*m'))
        self.v.set_rhs('3 [1] * 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('m'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('m'))
        self.v.set_rhs('3 * 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('m'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('m'))
        self.v.set_rhs('3 [1/m] * 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('3 * 4')
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        # Reset
        self.reset()

    def test_divide(self, op='/'):
        self.v.set_rhs('3 [kg] ' + op + ' 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('kg/m'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('kg/m'))
        self.v.set_rhs('3 [1] ' + op + ' 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1/m'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1/m'))
        self.v.set_rhs('3 ' + op + ' 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1/m'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1/m'))
        self.v.set_rhs('3 [1/m] ' + op + ' 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1/m^2'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1/m^2'))
        self.v.set_rhs('3 ' + op + ' 4')
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        self.v.set_rhs('3 [mM] ' + op + ' 2 [mM]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('3 [1/m] ' + op + ' 2 [1/m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_unit('mM')
        self.v.set_rhs('v ' + op + ' 2 [mM]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        # Reset
        self.reset()

    def test_quotient(self):
        self.test_divide('//')

    def test_remainder(self):
        self.v.set_rhs('3 [kg] % 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('kg'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('kg'))
        self.v.set_rhs('3 [1] % 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('3 % 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        self.v.set_rhs('3 [1/m] % 2 [m]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1/m'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1/m'))
        self.v.set_rhs('3 % 4')
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        # Reset
        self.reset()

    def test_power(self):
        self.v.set_rhs('3 [kg] ^ 2')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('kg^2'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('kg^2'))
        self.v.set_rhs('3 [1] ^ 3')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('3 ^ 2')
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        # Second unit is ignored in tolerant mode:
        self.v.set_rhs('3 [m] ^ 2 [m]')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('m^2'))
        self.v.set_rhs('1 ^ 2 [m]')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        # Reset
        self.reset()

    def test_sqrt(self):
        self.v.set_rhs('sqrt(3 [kg^2])')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('kg'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('kg'))
        self.v.set_rhs('sqrt(3 [1])')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('sqrt(3)')
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        # Reset
        self.reset()

    def test_sin(self, op='sin'):
        self.v.set_rhs(op + '(3)')
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        self.v.set_rhs(op + '(3 [1])')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs(op + '(3 [kg])')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        # Reset
        self.reset()

    def test_cos(self):
        self.test_sin('cos')

    def test_tan(self):
        self.test_sin('tan')

    def test_asin(self):
        self.test_sin('asin')

    def test_acos(self):
        self.test_sin('acos')

    def test_atan(self):
        self.test_sin('atan')

    def test_exp(self):
        self.test_sin('exp')

    def test_log(self):
        # 1 operand version
        self.test_sin('log')
        # 2 operand version
        self.v.set_rhs('log(3, 2)')
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        self.v.set_rhs('log(3 [1], 3)')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('log(3 [kg], 5)')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('log(3, 2 [1])')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('log(3 [1], 3)')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('log(3 [kg], 5 [kg])')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('log(3 [m], 5 [kg])')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('log(3 [1], 5 [kg])')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('log(3, 5 [kg])')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        # Reset
        self.reset()

    def test_log10(self):
        self.test_sin('log10')

    def test_floor(self, op='floor'):
        e = pe(op + '(18 [1])')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe(op + '(7)')
        self.assertEqual(e.eval_unit(S), None)
        self.assertEqual(e.eval_unit(T), None)
        e = pe(op + '(7 [kg/m^2])')
        self.assertEqual(e.eval_unit(S), pu('kg*m^-2'))
        self.assertEqual(e.eval_unit(T), pu('kg*m^-2'))

    def test_ceil(self):
        self.test_floor('ceil')

    def test_abs(self):
        self.test_floor('abs')

    def test_not(self):
        self.v.set_rhs('not 3')
        self.assertEqual(self.v.rhs().eval_unit(S), None)
        self.assertEqual(self.v.rhs().eval_unit(T), None)
        self.v.set_rhs('not 3 [1]')
        self.assertEqual(self.v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(self.v.rhs().eval_unit(T), pu('1'))
        self.v.set_rhs('not 3 [kg]')
        self.assertRaises(E, self.v.rhs().eval_unit, S)
        self.assertRaises(E, self.v.rhs().eval_unit, T)
        # Reset
        self.reset()

    def test_equal(self, op='=='):
        e = pe('14 ' + op + ' 12')
        self.assertEqual(e.eval_unit(S), None)
        self.assertEqual(e.eval_unit(T), None)
        e = pe('14 [1]' + op + ' 12')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('14 ' + op + ' 12 [1]')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('14 [1]' + op + ' 12 [1]')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('14 [kg]' + op + ' 12')
        self.assertRaises(E, e.eval_unit, S)
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('14 [kg]' + op + ' 12 [1]')
        self.assertRaises(E, e.eval_unit, S)
        self.assertRaises(E, e.eval_unit, T)

    def test_not_equal(self):
        self.test_equal('!=')

    def test_more(self):
        self.test_equal('>')

    def test_less(self):
        self.test_equal('<')

    def test_more_equal(self):
        self.test_equal('>=')

    def test_less_equal(self):
        self.test_equal('<=')

    def test_and(self, op='and'):
        e = pe('2 ' + op + ' 3')
        self.assertEqual(e.eval_unit(S), None)
        self.assertEqual(e.eval_unit(T), None)
        e = pe('2 [1] ' + op + ' 3')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('2 [1] ' + op + ' 3 [1]')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('2 ' + op + ' 3 [1]')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('2 [kg] ' + op + ' 3')
        self.assertRaises(E, e.eval_unit, S)
        self.assertRaises(E, e.eval_unit, T)

    def test_or(self):
        self.test_and(op='or')

    def test_if(self, op='if'):
        e = pe(op + '(2 == 2, 4, 7)')
        self.assertEqual(e.eval_unit(S), None)
        self.assertEqual(e.eval_unit(T), None)
        e = pe(op + '(2 == 0, 4, 7)')
        self.assertEqual(e.eval_unit(S), None)
        self.assertEqual(e.eval_unit(T), None)
        e = pe(op + '(0 == 0 [1], 4, 7)')
        self.assertEqual(e.eval_unit(S), None)
        self.assertEqual(e.eval_unit(T), None)
        e = pe(op + '(2 == 2, 4 [1], 7)')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe(op + '(2 == 2, 4 [1], 7 [1])')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe(op + '(2 == 2, 4 [mol], 7 [mol])')
        self.assertEqual(e.eval_unit(S), pu('mol'))
        self.assertEqual(e.eval_unit(T), pu('mol'))
        e = pe(op + '(2 == 2, 4 [kg], 7)')
        self.assertRaises(E, e.eval_unit, S)
        self.assertEqual(e.eval_unit(T), pu('kg'))
        e = pe(op + '(2 == 2, 4, 7 [kg])')
        self.assertRaises(E, e.eval_unit, S)
        self.assertEqual(e.eval_unit(T), pu('kg'))
        e = pe(op + '(2 == 2, 4 [kg], 7 [1])')
        self.assertRaises(E, e.eval_unit, S)
        self.assertRaises(E, e.eval_unit, T)

    def test_piecewise(self):
        # Repeat if-tests
        self.test_if('piecewise')
        # Multi-branch tests
        e = pe('piecewise(2 == 2, 4, 3==3, 7, 12)')
        self.assertEqual(e.eval_unit(S), None)
        self.assertEqual(e.eval_unit(T), None)
        e = pe('piecewise(2 == 0, 4, 7==7, 1, 2)')
        self.assertEqual(e.eval_unit(S), None)
        self.assertEqual(e.eval_unit(T), None)
        e = pe('piecewise(2 == 0, 4, 7==0, 1, 2)')
        self.assertEqual(e.eval_unit(S), None)
        self.assertEqual(e.eval_unit(T), None)
        e = pe('piecewise(2 == 0, 4, 7==7, 1, 2 [1])')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('piecewise(2 == 0, 4, 7==7, 1 [1], 2)')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('piecewise(2 == 0, 4 [1], 7==7, 1, 2)')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('piecewise(2 == 0, 4 [1], 7==7, 1, 2 [1])')
        self.assertEqual(e.eval_unit(S), pu('1'))
        self.assertEqual(e.eval_unit(T), pu('1'))
        e = pe('piecewise(2 == 0, 4 [kg], 7==7, 1, 2)')
        self.assertRaises(E, e.eval_unit, S)
        self.assertEqual(e.eval_unit(T), pu('kg'))
        e = pe('piecewise(2 == 0, 4, 7==7, 1 [kg], 2)')
        self.assertRaises(E, e.eval_unit, S)
        self.assertEqual(e.eval_unit(T), pu('kg'))
        e = pe('piecewise(2 == 0, 4 [kg], 7==7, 1, 2 [m/s])')
        self.assertRaises(E, e.eval_unit, S)
        self.assertRaises(E, e.eval_unit, T)

    def test_opiecewise(self):
        v = self.v
        v.set_unit(None)
        # No units
        v.set_rhs('opiecewise(v, 4, 3, 7, 12, 2)')
        self.assertEqual(v.rhs().eval_unit(S), None)
        self.assertEqual(v.rhs().eval_unit(T), None)
        # Units in v and switching points
        v.set_unit('1')
        v.set_rhs('opiecewise(v, 4, 3 [1], 7, 12, 2)')
        self.assertEqual(v.rhs().eval_unit(S), None)
        self.assertEqual(v.rhs().eval_unit(T), None)
        v.set_unit('1')
        v.set_rhs('opiecewise(v, 4, 3 [1], 7, 12 [1], 2)')
        self.assertEqual(v.rhs().eval_unit(S), None)
        self.assertEqual(v.rhs().eval_unit(T), None)
        v.set_unit(None)
        v.set_rhs('opiecewise(v, 4, 3 [1], 7, 12 [1], 2)')
        self.assertEqual(v.rhs().eval_unit(S), None)
        self.assertEqual(v.rhs().eval_unit(T), None)
        v.set_unit(None)
        v.set_rhs('opiecewise(v, 4, 3 [s], 7, 12 [s], 2)')
        self.assertRaises(E, v.rhs().eval_unit, S)
        self.assertEqual(v.rhs().eval_unit(T), None)
        v.set_unit(None)
        v.set_rhs('opiecewise(v, 4, 3 [s], 7, 12, 2)')
        self.assertRaises(E, v.rhs().eval_unit, S)
        self.assertEqual(v.rhs().eval_unit(T), None)
        v.set_unit('ks')
        v.set_rhs('opiecewise(v, 4, 3, 7, 12, 2)')
        self.assertRaises(E, v.rhs().eval_unit, S)
        self.assertEqual(v.rhs().eval_unit(T), None)
        v.set_unit(None)
        v.set_rhs('opiecewise(v, 4, 3 [s], 7, 12 [ms], 2)')
        self.assertRaises(E, v.rhs().eval_unit, S)
        self.assertRaises(E, v.rhs().eval_unit, T)
        # Units in output
        v.set_unit(None)
        v.set_rhs('opiecewise(v, 4 [1], 3, 7, 12, 2)')
        self.assertEqual(v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(v.rhs().eval_unit(T), pu('1'))
        v.set_rhs('opiecewise(v, 4 [1], 3, 7 [1], 12, 2)')
        self.assertEqual(v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(v.rhs().eval_unit(T), pu('1'))
        v.set_rhs('opiecewise(v, 4 [kg], 3, 7, 12, 2)')
        self.assertRaises(E, v.rhs().eval_unit, S)
        self.assertEqual(v.rhs().eval_unit(T), pu('kg'))
        v.set_rhs('opiecewise(v, 4, 3, 7, 12, 2 [kg])')
        self.assertRaises(E, v.rhs().eval_unit, S)
        self.assertEqual(v.rhs().eval_unit(T), pu('kg'))
        v.set_rhs('opiecewise(v, 4 [kg], 3, 7 [kg], 12, 2 [kg])')
        self.assertEqual(v.rhs().eval_unit(S), pu('kg'))
        self.assertEqual(v.rhs().eval_unit(T), pu('kg'))
        v.set_unit('V')
        v.set_rhs('opiecewise(v, 4 [kg], 3, 7 [kg], 12, 2 [kg])')
        self.assertRaises(E, v.rhs().eval_unit, S)
        self.assertEqual(v.rhs().eval_unit(T), pu('kg'))
        v.set_rhs('opiecewise(v, 4 [V], 3, 7 [V], 12, 2 [V])')
        self.assertRaises(E, v.rhs().eval_unit, S)
        self.assertEqual(v.rhs().eval_unit(T), pu('V'))
        v.set_rhs('opiecewise(v, 4 [V], 3 [V], 7 [V], 12 [V], 2 [V])')
        self.assertEqual(v.rhs().eval_unit(S), pu('V'))
        self.assertEqual(v.rhs().eval_unit(T), pu('V'))
        v.set_unit('mg')
        v.set_rhs('opiecewise(v, 4 [V], 3 [mg], 7 [V], 12 [mg], 2 [V])')
        self.assertEqual(v.rhs().eval_unit(S), pu('V'))
        self.assertEqual(v.rhs().eval_unit(T), pu('V'))
        v.set_unit(None)
        v.set_rhs('opiecewise(v, 4 [1], 3, 7, 12, 2)')
        self.assertEqual(v.rhs().eval_unit(S), pu('1'))
        self.assertEqual(v.rhs().eval_unit(T), pu('1'))
        # Reset
        self.reset()

    def test_example(self):
        self.m.check_units(T)
        self.m.check_units(S)


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
