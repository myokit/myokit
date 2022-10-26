#!/usr/bin/env python3
#
# Tests the Model class.
#
# Notes:
#  - Tests for dependency checking in models are in `test_dependency_checking`.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import pickle
import re
import unittest

import myokit

from myokit.tests import TemporaryDirectory, WarningCollector


# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class ModelTest(unittest.TestCase):
    """
    Tests parts of :class:`myokit.Model`.
    """

    def test_add_component_allow_renamining(self):
        # Test the ``Model.add_component_allow_renaming`` method.

        m = myokit.Model('test')
        c = m.add_component('c')
        self.assertTrue(m.has_component('c'))
        self.assertRaises(myokit.DuplicateName, m.add_component, 'c')
        d = m.add_component_allow_renaming('c')
        self.assertEqual(c.name(), 'c')
        self.assertEqual(d.name(), 'c_1')
        e = m.add_component_allow_renaming('c')
        self.assertEqual(e.name(), 'c_2')

        # Test repeated calls
        r = m.add_component('r')
        for i in range(10):
            r = m.add_component_allow_renaming('r')
            self.assertEqual(r.name(), 'r_' + str(1 + i))

    def test_add_function(self):
        # Test the ``Model.add_function`` method.

        m = myokit.Model('m')
        c = m.add_component('c')
        x = c.add_variable('x')

        # Test basics
        m.add_function('f', ('a', 'b', 'c'), 'a + b + c')
        x.set_rhs('f(1, 2, 3)')
        self.assertEqual(x.eval(), 6)

        # Test duplicate name
        # Different number of arguments is allowed:
        m.add_function('f', ('a', 'b'), 'a + b')
        self.assertRaisesRegex(
            myokit.DuplicateFunctionName, 'already defined', m.add_function,
            'f', ('a', 'b'), 'a - b')

        # Test duplicate argument name
        self.assertRaisesRegex(
            myokit.DuplicateFunctionArgument, 'already in use',
            m.add_function, 'g', ('a', 'a'), 'a + a')

        # Dot operator is not allowed, nor are init or partial
        self.assertRaisesRegex(
            myokit.InvalidFunction, r'dot\(\) operator',
            m.add_function, 'fdot', ('a', ), 'dot(a)')
        a = myokit.Name('a')
        self.assertRaisesRegex(
            myokit.InvalidFunction, r'partial\(\) operator',
            m.add_function, 'fpart', ('a', ), myokit.PartialDerivative(a, a))
        self.assertRaisesRegex(
            myokit.InvalidFunction, r'init\(\) operator',
            m.add_function, 'finit', ('a', ), myokit.InitialValue(a))

        # Unused argument
        self.assertRaisesRegex(
            myokit.InvalidFunction, 'never used', m.add_function, 'fun',
            ('a', 'b'), 'a')

        # Unspecified variable
        self.assertRaisesRegex(
            myokit.InvalidFunction, 'never declared',
            m.add_function, 'fun', ('a', ), 'a + b')

    def test_binding(self):
        # Tests setting and getting of bindings

        # Note that set_binding() is part of Variable, so not tested here
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_binding('hello')
        y = c.add_variable('y')
        y.set_binding('goodbye')
        z = c.add_variable('z')
        z.set_binding('x')

        # Test binding()
        self.assertEqual(m.binding('goodbye'), y)
        self.assertEqual(m.binding('hello'), x)
        self.assertEqual(m.binding('x'), z)
        self.assertEqual(m.binding('y'), None)

        # Test bindings()
        bindings = dict(m.bindings())
        self.assertEqual(bindings['goodbye'], y)
        self.assertEqual(bindings['hello'], x)
        self.assertEqual(bindings['x'], z)
        self.assertFalse('y' in bindings)

        # Test bindingx()
        self.assertEqual(m.bindingx('goodbye'), y)
        self.assertEqual(m.bindingx('hello'), x)
        self.assertEqual(m.bindingx('x'), z)
        self.assertRaisesRegex(
            myokit.IncompatibleModelError,
            'No variable found with binding "y"',
            m.bindingx, 'y')

    def test_bindings(self):
        # Test setting bindings and :meth:`Model.bindings()`.

        # Test set_binding() and bindings()
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        w = c.add_variable('w')
        w.set_rhs(0)
        bindings = list(m.bindings())
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0][0], 'time')
        self.assertEqual(bindings[0][1], t)

        # Can't have two labels
        self.assertRaisesRegex(
            myokit.InvalidBindingError, 'already bound to', t.set_binding,
            'bert')

        # No two variables can have the same label
        self.assertRaisesRegex(
            myokit.InvalidBindingError, 'Duplicate binding', v.set_binding,
            'time')

        # Binding can't overlap with label
        v.set_label('membrane_potential')
        self.assertRaisesRegex(
            myokit.InvalidBindingError, 'in use as a label', w.set_binding,
            'membrane_potential')

        # State variables can't be bound
        v.promote(0)
        self.assertRaisesRegex(
            myokit.InvalidBindingError, 'State variables', v.set_binding, 'x')

    def test_check_units(self):
        # Test the ``model.check_units`` method.

        model = myokit.Model('m')
        component = model.add_component('c')
        t = component.add_variable('time')
        t.set_binding('time')

        # Check units before any rhs or units set
        s = myokit.UNIT_STRICT
        self.assertRaisesRegex(
            myokit.IntegrityError, 'No RHS set', model.check_units)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'No RHS set', model.check_units, s)

        # Check units before any rhs set
        t.set_unit('s')
        self.assertRaisesRegex(
            myokit.IntegrityError, 'No RHS set', model.check_units)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'No RHS set', model.check_units, s)

        # Check mini model with rhs and units, no states
        t.set_rhs('0 [s]')
        a = component.add_variable('a')
        a.set_rhs(1)
        model.check_units()
        model.check_units(s)

        # Check mini model with a state
        # Strict check should fail: a's RHS should be in 1/s
        a.promote(0)
        model.check_units()
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)
        a.set_rhs('1 [1/s]')
        model.check_units(s)

        b = component.add_variable('b')
        b.set_rhs(2)
        c = component.add_variable('c')
        c.set_rhs('2 * b')
        model.check_units()
        model.check_units(s)

        a.set_rhs('1 [N/s]')
        b.set_rhs('2 [m]')
        c.set_rhs('a * b')

        # No variable units set
        model.check_units()
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)

        # Variable unit set for state
        a.set_unit('N')     # So rhs should be N/s
        b.set_unit('m')
        model.check_units()
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)

        # Bad derived unit
        c.set_unit('A')
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units)
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)

        c.set_unit(myokit.parse_unit('N*m'))
        model.check_units()
        model.check_units(s)

        # References use variable unit, not RHS unit!
        model = myokit.Model('m')
        component = model.add_component('c')
        x = component.add_variable('x')
        y = component.add_variable('y')
        x.set_unit(None)
        y.set_unit(None)
        x.set_rhs('5 [mV]')
        y.set_rhs('3 [A] + x')  # x unit is unspecified, not mV!
        model.check_units()
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)

        # Tokens are used in IncompatibleUnitError messages
        m = myokit.parse_model('\n'.join([
            '[[model]]',
            '[a]',
            't = 0 [ms] bind time',
        ]))
        try:
            m.check_units(s)
        except myokit.IncompatibleUnitError as e:
            self.assertIn('on line 3', str(e))
            token = e.token()
            self.assertIsNotNone(token)
            self.assertEqual(token[2], 3)
            self.assertEqual(token[3], 0)

        # Test comparison with floating point issues
        m = myokit.parse_model('\n'.join([
            '[[model]]',
            '[a]',
            'x = 1 [cm^3] bind time',
            '    in [cm^3]',
            'y = 2 [day]',
            '    in [day]',
            'z = 3 [day^3]',
            '    in [day^3]',
            'a = (x / y / y / y) * z',
            '    in [cm^3]',
        ]))
        m.check_units(s)

    def test_clone(self):
        # Test :meth:`Model.clone() and :meth:`Model.has_parse_info()`.

        # Test model, component, variables
        m1 = myokit.load_model('example')
        m2 = m1.clone()
        self.assertFalse(m1 is m2)
        self.assertNotEqual(m1, m2)
        self.assertTrue(m1.is_similar(m2, True))

        # Test unames and uname prefixes
        m1.reserve_unique_names('barnard', 'lincoln', 'glasgow')
        m1.reserve_unique_name_prefix('monkey', 'giraffe')
        m1.reserve_unique_name_prefix('ostrich', 'turkey')
        m2 = m1.clone()
        self.assertTrue(m1.is_similar(m2, True))

        # Test tokens are not cloned
        self.assertTrue(m1.has_parse_info())
        self.assertFalse(m2.has_parse_info())

    def test_code(self):
        # Test :meth:`Model.code()`.

        model = myokit.Model('m')
        component = model.add_component('comp1')
        a = component.add_variable('a')
        b = component.add_variable('b')
        c = component.add_variable('c')
        a.set_rhs('1 [N]')
        a.set_label('aaa')
        b.set_rhs('2 [m]')
        b.set_binding('bbb')
        c.set_rhs('a * b')
        c.set_unit('N*m')
        component2 = model.add_component('comp2')
        d = component2.add_variable('d')
        d.set_rhs(myokit.Name(a))

        self.assertEqual(
            model.code(),
            '[[model]]\n'
            'name: m\n'
            '\n'
            '[comp1]\n'
            'a = 1 [N] label aaa\n'
            'b = 2 [m] bind bbb\n'
            'c = a * b\n'
            '    in [J]\n'
            '\n'
            '[comp2]\n'
            'd = comp1.a\n'
            '\n'
        )

        a.set_rhs('1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11')
        b.set_rhs('2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12')

        self.assertEqual(
            model.code(line_numbers=True),
            ' 1 [[model]]\n'
            ' 2 name: m\n'
            ' 3 \n'
            ' 4 [comp1]\n'
            ' 5 a = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11\n'
            ' 6     label aaa\n'
            ' 7 b = 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12\n'
            ' 8     bind bbb\n'
            ' 9 c = a * b\n'
            '10     in [J]\n'
            '11 \n'
            '12 [comp2]\n'
            '13 d = comp1.a\n'
        )

    def test_is_similar(self):
        # Check that equality takes both code() and unames into account

        # Test without custom reserved names
        m1 = myokit.load_model('example')
        m2 = m1.clone()
        self.assertIsInstance(m2, myokit.Model)
        self.assertFalse(m1 is m2)
        self.assertNotEqual(m1, m2)
        self.assertNotEqual(m2, m1)
        self.assertTrue(m1.is_similar(m2, False))
        self.assertTrue(m1.is_similar(m2, True))
        self.assertTrue(m2.is_similar(m1, False))
        self.assertTrue(m2.is_similar(m1, True))
        self.assertTrue(m1.is_similar(m1, True))
        self.assertTrue(m2.is_similar(m2, False))

        # Test with none-model
        self.assertFalse(m1.is_similar(None))
        self.assertFalse(m1.is_similar(m1.code()))

        # Add reserved names
        m1.reserve_unique_names('bertie')
        self.assertFalse(m1.is_similar(m2))
        m1.reserve_unique_names('clair')
        self.assertFalse(m1.is_similar(m2))
        m2.reserve_unique_names('clair', 'bertie')
        self.assertTrue(m1.is_similar(m2))

        # Add reserved name prefixes
        m1.reserve_unique_name_prefix('aa', 'bb')
        m1.reserve_unique_name_prefix('cc', 'dd')
        self.assertFalse(m1.is_similar(m2))
        m2.reserve_unique_name_prefix('aa', 'bb')
        m2.reserve_unique_name_prefix('cc', 'ee')
        self.assertFalse(m1.is_similar(m2))
        m2.reserve_unique_name_prefix('cc', 'dd')
        self.assertTrue(m1.is_similar(m2))

    def test_evaluate_derivatives(self):
        # Test Model.evaluate_derivatives().
        model = myokit.Model('m')
        component = model.add_component('comp1')
        t = component.add_variable('time')
        t.set_binding('time')
        t.set_rhs(1)
        a = component.add_variable('a')
        b = component.add_variable('b')
        c = component.add_variable('c')
        d = component.add_variable('d')
        a.promote(1)
        a.set_rhs('1')
        b.promote(2)
        b.set_rhs('2 * b')
        c.promote(3)
        c.set_rhs('b + d')
        d.set_rhs('1 * c')
        model.validate()

        # Test without input
        self.assertEqual(model.evaluate_derivatives(), [1, 4, 5])
        self.assertEqual(model.evaluate_derivatives(ignore_errors=True),
                         [1, 4, 5])

        # Test with alternative state
        self.assertEqual(
            model.evaluate_derivatives(state=[2, 3, 4]), [1, 6, 7])
        self.assertEqual(
            model.evaluate_derivatives(state=[2, 3, 4], ignore_errors=True),
            [1, 6, 7])

        # Test with input
        c.set_rhs('b + c + time')
        self.assertEqual(model.evaluate_derivatives(), [1, 4, 6])
        self.assertEqual(
            model.evaluate_derivatives(ignore_errors=True), [1, 4, 6])
        self.assertEqual(
            model.evaluate_derivatives(state=[2, 3, 4]), [1, 6, 8])
        self.assertEqual(
            model.evaluate_derivatives(state=[2, 3, 4], ignore_errors=True),
            [1, 6, 8])
        self.assertEqual(
            model.evaluate_derivatives(state=[2, 3, 4], inputs={'time': 10}),
            [1, 6, 17])
        self.assertEqual(
            model.evaluate_derivatives(
                state=[2, 3, 4], inputs={'time': 10}, ignore_errors=True),
            [1, 6, 17])

        # Deprecated name
        with WarningCollector() as w:
            self.assertEqual(
                model.eval_state_derivatives(
                    state=[1, 1, 2], inputs={'time': 0}),
                [1, 2, 3])
        self.assertIn('deprecated', w.text())

        # Ignoring errors should lead to Nans
        c.set_rhs('(b + c) / 0')
        self.assertRaises(myokit.NumericalError, model.evaluate_derivatives)
        nan = model.evaluate_derivatives(ignore_errors=True)[2]
        self.assertNotEqual(nan, nan)   # x != x is a nan test...

    def test_format_state(self):
        # Test Model.format_state()

        self.maxDiff = None
        m = myokit.load_model('example')

        # Test without state argument
        self.assertEqual(
            m.format_state(),
            'membrane.V = -84.5286\n'
            'ina.m      = 0.0017\n'
            'ina.h      = 0.9832\n'
            'ina.j      = 0.995484\n'
            'ica.d      = 3e-06\n'
            'ica.f      = 1.0\n'
            'ik.x       = 0.0057\n'
            'ica.Ca_i   = 0.0002'
        )

        # Test with state argument
        state1 = [1, 2, 3, 4, 5, 6, 7, 8]
        state1[3] = 124.35624574537437
        self.assertEqual(
            m.format_state(state1),
            'membrane.V = 1\n'
            'ina.m      = 2\n'
            'ina.h      = 3\n'
            'ina.j      =  1.24356245745374366e+02\n'
            'ica.d      = 5\n'
            'ica.f      = 6\n'
            'ik.x       = 7\n'
            'ica.Ca_i   = 8'
        )

        # Test with invalid state argument
        self.assertRaisesRegex(
            ValueError, r'list of \(8\)', m.format_state, [1, 2, 3])

        # Test with precision argument
        state1 = [1, 2, 3, 4, 5, 6, 7, 8]
        state1[3] = 124.35624574537437
        self.assertEqual(
            m.format_state(state1, precision=myokit.SINGLE_PRECISION),
            'membrane.V = 1\n'
            'ina.m      = 2\n'
            'ina.h      = 3\n'
            'ina.j      =  1.243562457e+02\n'
            'ica.d      = 5\n'
            'ica.f      = 6\n'
            'ik.x       = 7\n'
            'ica.Ca_i   = 8'
        )

        # Test with second state argument
        self.assertEqual(
            m.format_state([1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1]),
            'membrane.V = 1    8\n'
            'ina.m      = 2    7\n'
            'ina.h      = 3    6\n'
            'ina.j      = 4    5\n'
            'ica.d      = 5    4\n'
            'ica.f      = 6    3\n'
            'ik.x       = 7    2\n'
            'ica.Ca_i   = 8    1'
        )

        # Test with invalid second state argument
        self.assertRaisesRegex(
            ValueError, r'list of \(8\)', m.format_state,
            [1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3])

    def test_format_state_derivatives(self):
        # Test Model.format_state_derivatives().

        self.maxDiff = None
        m = myokit.load_model('example')

        # For whatever reason, CI gives slightly different final digits some
        # times.
        r1 = re.compile(
            r'^[a-zA-Z]\w*\.[a-zA-Z]\w*\s+=\s+([^\s]+)\s+dot\s+=\s+([^\s]+)$')

        def almost_equal(x, y):
            if x == y:
                return True
            g1, g2 = r1.match(x), r1.match(y)
            if g1 is None or g2 is None:
                return False
            x, y = float(g1.group(2)), float(g2.group(2))
            return myokit.float.close(x, y)

        # Test without arguments
        x = m.format_state_derivatives().splitlines()
        y = [
'membrane.V = -84.5286                   dot = -5.68008003798848027e-02', # noqa
'ina.m      = 0.0017                     dot = -4.94961486033834719e-03', # noqa
'ina.h      = 0.9832                     dot =  9.02025299127830887e-06', # noqa
'ina.j      = 0.995484                   dot = -3.70409866928434243e-04', # noqa
'ica.d      = 3e-06                      dot =  3.68067721821794798e-04', # noqa
'ica.f      = 1.0                        dot = -3.55010150519739432e-07', # noqa
'ik.x       = 0.0057                     dot = -2.04613933160084307e-07', # noqa
'ica.Ca_i   = 0.0002                     dot = -6.99430692442154227e-06'  # noqa
        ]
        for a, b in zip(x, y):
            self.assertTrue(almost_equal(a, b))
        self.assertEqual(len(x), len(y))

        # Test with state argument
        state1 = [1, 2, 3, 4, 5, 6, 7, 8]
        state1[2] = 536.46745856785678567845745637
        x = m.format_state_derivatives(state1).splitlines()
        y = [
'membrane.V = 1                          dot =  1.90853168050245158e+07', # noqa
'ina.m      = 2                          dot = -1.56738349674489310e+01', # noqa
'ina.h      =  5.36467458567856738e+02   dot = -3.05729251015767022e+03', # noqa
'ina.j      = 4                          dot = -1.15731427949362953e+00', # noqa
'ica.d      = 5                          dot = -1.85001944916516836e-01', # noqa
'ica.f      = 6                          dot = -2.15435819790876573e-02', # noqa
'ik.x       = 7                          dot = -1.25154369264425316e-02', # noqa
'ica.Ca_i   = 8                          dot = -5.63431267451130036e-01', # noqa                                       ^ ^^    ^ ---------   ^
        ]
        for a, b in zip(x, y):
            self.assertTrue(almost_equal(a, b))
        self.assertEqual(len(x), len(y))

        # Test with invalid state argument
        self.assertRaisesRegex(
            ValueError, r'list of \(8\)',
            m.format_state_derivatives, [1, 2, 3])

        # Test with state and precision argument
        # Ignoring some of the middle digits, as they differ on some (but not
        # all!) CI builds.
        out = m.format_state_derivatives(
            state1, precision=myokit.SINGLE_PRECISION).splitlines()
        self.assertEqual(len(out), 8)
        self.assertEqual(out[0][:15], 'membrane.V = 1 ')
        self.assertEqual(out[1][:15], 'ina.m      = 2 ')
        self.assertEqual(out[2][:29], 'ina.h      =  5.364674586e+02')
        self.assertEqual(out[3][:15], 'ina.j      = 4 ')
        self.assertEqual(out[4][:15], 'ica.d      = 5 ')
        self.assertEqual(out[5][:15], 'ica.f      = 6 ')
        self.assertEqual(out[6][:15], 'ik.x       = 7 ')
        self.assertEqual(out[7][:15], 'ica.Ca_i   = 8 ')
        out = [x[x.index('dot') + 6:] for x in out]
        self.assertEqual(out[0][:8], ' 1.90853')
        self.assertEqual(out[1][:8], '-1.56738')
        self.assertEqual(out[2][:8], '-3.05729')
        self.assertEqual(out[3][:8], '-1.15731')
        self.assertEqual(out[4][:8], '-1.85001')
        self.assertEqual(out[5][:8], '-2.15435')
        self.assertEqual(out[6][:8], '-1.25154')
        self.assertEqual(out[7][:8], '-5.63431')
        self.assertEqual(out[0][12:], 'e+07')
        self.assertEqual(out[1][12:], 'e+01')
        self.assertEqual(out[2][12:], 'e+03')
        self.assertEqual(out[3][12:], 'e+00')
        self.assertEqual(out[4][12:], 'e-01')
        self.assertEqual(out[5][12:], 'e-02')
        self.assertEqual(out[6][12:], 'e-02')
        self.assertEqual(out[7][12:], 'e-01')

        # Test with derivs argument
        self.assertEqual(
            m.format_state_derivatives(
                [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1]),
            'membrane.V = 1                          dot = 8\n'
            'ina.m      = 2                          dot = 7\n'
            'ina.h      = 3                          dot = 6\n'
            'ina.j      = 4                          dot = 5\n'
            'ica.d      = 5                          dot = 4\n'
            'ica.f      = 6                          dot = 3\n'
            'ik.x       = 7                          dot = 2\n'
            'ica.Ca_i   = 8                          dot = 1'
        )

        # Test with invalid derivs argument
        self.assertRaisesRegex(
            ValueError, r'list of \(8\)', m.format_state_derivatives,
            [1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3])

    def test_get(self):
        # Test Model.get().

        m = myokit.load_model('example')

        # Get by name
        v = m.get('membrane.V')
        self.assertEqual(v.qname(), 'membrane.V')
        self.assertIsInstance(v, myokit.Variable)

        # Get by variable ref (useful for handling unknown input type)
        w = m.get(v)
        self.assertIs(w, v)

        # Get by variable from another model
        m2 = m.clone()
        self.assertRaisesRegex(ValueError, 'different model', m2.get, v)

        # Get nested
        a = m.get('ina.m.alpha')
        self.assertEqual(a.qname(), 'ina.m.alpha')
        self.assertIsInstance(a, myokit.Variable)

        # Get component
        c = m.get('membrane')
        self.assertEqual(c.qname(), 'membrane')
        self.assertIsInstance(c, myokit.Component)

        # Get with filter
        a = m.get('ina.m.alpha', myokit.Variable)
        self.assertEqual(a.qname(), 'ina.m.alpha')
        self.assertIsInstance(a, myokit.Variable)
        self.assertRaises(KeyError, m.get, 'ina.m.alpha', myokit.Component)
        self.assertRaises(KeyError, m.get, 'ina', myokit.Variable)
        m.get('ina', myokit.Component)

        # Get non-existent
        self.assertRaises(KeyError, m.get, 'membrane.bert')
        self.assertRaises(KeyError, m.get, 'bert.bert')

    def test_has_variables(self):
        # Test VarProvider.has_variables (and VarProvider.variables)

        m = myokit.Model()
        z = m.add_component('z')
        self.assertFalse(m.has_variables())

        # Constant
        a = z.add_variable('a')
        a.set_rhs(0)
        self.assertTrue(m.has_variables())
        self.assertTrue(m.has_variables(const=True))
        self.assertFalse(m.has_variables(const=False))

        # State
        self.assertFalse(m.has_variables(state=True))
        b = z.add_variable('b')
        b.set_rhs(1)
        b.promote(0.2)
        self.assertTrue(m.has_variables(state=True))
        self.assertFalse(m.has_variables(const=False, state=False))

        # Inter and deep
        self.assertFalse(m.has_variables(inter=True))
        self.assertFalse(m.has_variables(inter=True, deep=True))
        c = b.add_variable('c')
        c.set_rhs('b * 2')
        b.set_rhs('1 + c')
        self.assertFalse(m.has_variables(inter=True))
        self.assertTrue(m.has_variables(inter=True, deep=True))

        # Bound
        self.assertFalse(m.has_variables(bound=True))
        t = z.add_variable('t')
        t.set_rhs(0)
        t.set_binding('time')
        self.assertTrue(m.has_variables(bound=True))
        self.assertFalse(
            m.has_variables(const=False, state=False, bound=False))

    def test_import_component(self):
        # Test :meth: 'import_component()'.

        # Source model, to import stuff from
        ms = myokit.parse_model('''
            [[model]]
            p.b = 0.2
            q.e = 0.2
            x.a = 0.2
            y.e = 0.2

            [e]
            t = 0 [s] bind time
                in [s]
            g = 0
                label this_is_g
            h = 4

            # Independent (except for time)
            [p]
            a = 1 [1/s]
                in [1/s]
            # Comments should be stripped out during parsing, so this is OK.
            dot(b) = a * c
                in [m]
                c = b * 2
                    in [m]

            # Requires mapping, has aliases and an unused alias
            [q]
            use p.a, p.b
            use e.h
            dot(e) = d * b
                in [m*A]
            f = 3 * dot(b)
                in [m/s]
            d = 0.2 [A] * a
                in [A/s]

            # Two components to import at the same time
            # (independent of the rest of the model)
            [x]
            use y.e
            dot(a) = c * e
                in [m*A]
            b = 3 * dot(e)
                in [m/s]
            c = 0.2 [A] * d
                in [A/s]
            d = 1 [1/s]
                in [1/s]

            [y]
            use x.d
            dot(e) = d * sub_e
                in [m]
                sub_e = 2 * e
                    in [m]

            # another group component but this isn't independant
            [z]
            use x.d
            use y.e
            use e.h

            f = d * e * h
                in [m/s]
        ''')
        ms.validate()
        ms.check_units(myokit.UNIT_STRICT)

        # Make copy of ms, to ensure nothing is altered in original model
        ms_unaltered = ms.clone()

        # Import independent component into empty model
        m1 = myokit.Model()
        m1.import_component(ms['p'])
        self.assertTrue(m1.has_component('p'))
        self.assertFalse(m1['p'] is ms['p'])
        self.assertEqual(m1['p'].code(), ms['p'].code())
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Import a second time, without renaming
        m1.import_component, ms['p']  # Check errors happen before changes
        m1_unaltered = m1.clone()
        self.assertRaises(myokit.DuplicateName, m1.import_component, ms['p'])
        self.assertTrue(m1.is_similar(m1_unaltered, True))

        # Import a second time, and rename
        m1.import_component(ms['p'], new_name='p2')
        self.assertTrue(m1.has_component('p2'))
        self.assertFalse(m1['p2'] is ms['p'])
        self.assertFalse(m1['p2'] is m1['p'])
        cs = '\n'.join((ms['p'].code().splitlines())[1:])
        c1 = '\n'.join((m1['p2'].code().splitlines())[1:])
        self.assertEqual(cs, c1)
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Import independent component with labels and bindings
        m1.import_component(ms['e'])
        self.assertTrue(m1.has_component('e'))
        self.assertFalse(m1['e'] is ms['e'])
        self.assertEqual(m1['e'].code(), ms['e'].code())
        self.assertEqual(m1.label('this_is_g'), m1.get('e.g'))
        self.assertEqual(m1.binding('time'), m1.get('e.t'))
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Now that it has a time variable, m1 should be valid
        m1.validate()
        self.assertTrue(m1.is_valid())

        # Re-importing e is not allowed, as it leads to double bindings and/or
        # labels
        m1_unaltered = m1.clone()
        ms.time().set_binding(None)
        self.assertRaisesRegex(
            myokit.InvalidLabelError, 'label "this_is_g"',
            m1.import_component, ms['e'], new_name='dinosaur')
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        ms.get('e.t').set_binding('time')
        ms.label('this_is_g').set_label(None)
        self.assertRaisesRegex(
            myokit.InvalidBindingError, 'binding "time"',
            m1.import_component, ms['e'], new_name='hello')
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        ms = ms_unaltered.clone()

        # Import r, using a custom variable mapping
        var_map = {'p.a': 'p.a', 'p.b': 'p2.b', 'e.h': 'e.h'}
        m1.import_component(ms['q'], var_map=var_map)
        self.assertTrue(m1.has_component('q'))
        self.assertFalse(m1['q'] is ms['q'])
        self.assertEqual(m1['q'].alias('a'), m1.get('p.a'))
        self.assertEqual(m1['q'].alias('b'), m1.get('p2.b'))
        self.assertEqual(m1['q'].alias('h'), m1.get('e.h'))
        cs = '\n'.join((ms['p'].code().splitlines())[4:])
        c1 = '\n'.join((m1['p2'].code().splitlines())[4:])
        self.assertEqual(cs, c1)
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Import r, using a label for p.b
        ms.get('p.b').set_label('this_is_b')
        m1.get('p2.b').set_label('this_is_b')
        var_map = {'p.a': 'p.a', 'e.h': 'e.h'}
        m1.import_component(ms['q'], var_map=var_map, new_name='q2')
        self.assertTrue(m1.has_component('q2'))
        self.assertFalse(m1['q2'] is ms['q'])
        self.assertFalse(m1['q2'] is m1['q'])
        self.assertEqual(m1['q2'].alias('a'), m1.get('p.a'))
        self.assertEqual(m1['q2'].alias('b'), m1.get('p2.b'))
        cs = '\n'.join((ms['p'].code().splitlines())[3:])
        c1 = '\n'.join((m1['p2'].code().splitlines())[3:])
        self.assertEqual(cs, c1)
        ms.get('p.b').set_label(None)
        m1.get('p2.b').set_label(None)
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Import r, using a binding for e.h
        ms.get('e.h').set_binding('this_is_h')
        m1.get('e.h').set_binding('this_is_h')
        var_map = {'p.a': 'p.a', 'p.b': 'p2.b'}
        m1.import_component(ms['q'], var_map=var_map, new_name='q3')
        self.assertTrue(m1.has_component('q3'))
        self.assertFalse(m1['q3'] is ms['q'])
        self.assertFalse(m1['q3'] is m1['q'])
        self.assertEqual(m1['q3'].alias('a'), m1.get('p.a'))
        self.assertEqual(m1['q3'].alias('b'), m1.get('p2.b'))
        cs = '\n'.join((ms['p'].code().splitlines())[3:])
        c1 = '\n'.join((m1['p2'].code().splitlines())[3:])
        self.assertEqual(cs, c1)
        ms.get('e.h').set_binding(None)
        m1.get('e.h').set_binding(None)
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Import r, using (partial) name mapping
        var_map = {'p.a': 'p2.a'}
        m1.import_component(
            ms['q'], var_map=var_map, new_name='q4', allow_name_mapping=True)
        self.assertTrue(m1.has_component('q3'))
        self.assertFalse(m1['q3'] is ms['q'])
        self.assertFalse(m1['q4'] is m1['q'])
        self.assertEqual(m1['q4'].alias('a'), m1.get('p2.a'))
        cs = '\n'.join((ms['p'].code().splitlines())[2:])
        c1 = '\n'.join((m1['p2'].code().splitlines())[2:])
        self.assertEqual(cs, c1)
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Import multiple components
        component_list = [ms['x'], ms['y']]
        m1.import_component(component_list)
        self.assertTrue(m1.has_component('x'))
        self.assertTrue(m1.has_component('y'))
        self.assertFalse(m1['x'] is ms['x'])
        self.assertFalse(m1['y'] is ms['y'])
        self.assertEqual(m1['x'].code(), ms['x'].code())
        self.assertEqual(m1['y'].code(), ms['y'].code())
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Import 1 component in list
        m1.import_component([ms['p']], new_name='p3')
        self.assertTrue(m1.has_component('p3'))
        self.assertFalse(m1['p3'] is ms['p'])
        self.assertFalse(m1['p3'] is m1['p'])
        cs = '\n'.join((ms['p'].code().splitlines())[1:])
        c1 = '\n'.join((m1['p3'].code().splitlines())[1:])
        self.assertEqual(cs, c1)
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Try and fail to import r without a mapping
        m1_unaltered = m1.clone()
        self.assertRaises(
            myokit.VariableMappingError,
            m1.import_component, ms['q'], new_name='q9')
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # With an invalid mapping
        self.assertRaisesRegex(
            TypeError, 'dict or None',
            m1.import_component, ms['q'], new_name='q9', var_map=[3])
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertRaisesRegex(
            TypeError, 'objects or fully qualified',
            m1.import_component, ms['q'], new_name='q9',
            var_map={'p.a': 123, 'p.b': 'p.b', 'e.h': 'e.h'})
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertRaisesRegex(
            TypeError, 'objects or fully qualified',
            m1.import_component, ms['q'], new_name='q9',
            var_map={345: 'p.a', 'p.b': 'p.b', 'e.h': 'e.h'})
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertRaisesRegex(
            myokit.VariableMappingError, 'Multiple variables map',
            m1.import_component, ms['q'], new_name='q9',
            var_map={'p.a': 'p.a', 'p.b': 'p.a', 'e.h': 'e.h'})
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # With variables from another model or that don't exist
        self.assertRaisesRegex(
            myokit.VariableMappingError, 'was not found in this model',
            m1.import_component, ms['q'], new_name='q9',
            var_map={'p.a': 'one.two', 'p.b': 'p.b', 'e.h': 'e.h'})
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        self.assertRaisesRegex(
            myokit.VariableMappingError, 'was not found in the source model',
            m1.import_component, ms['q'], new_name='q9',
            var_map={'ppp.aaa': 'p.a', 'p.b': 'p.b', 'e.h': 'e.h'})
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        v = myokit.Model('a').add_component('p').add_variable('b')
        self.assertRaisesRegex(
            myokit.VariableMappingError, 'is not part of this model',
            m1.import_component, ms['q'], new_name='q9',
            var_map={'p.a': v, 'p.b': 'p.b'})
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        self.assertRaisesRegex(
            myokit.VariableMappingError, 'is not part of the source model',
            m1.import_component, ms['q'], new_name='q9',
            var_map={v: 'p.a', 'p.b': 'p.b', 'e.h': 'e.h'})
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Incomplete mapping
        self.assertRaisesRegex(
            myokit.VariableMappingError, 'cannot be mapped',
            m1.import_component, ms['q'], new_name='q9', var_map={})
        self.assertTrue(m1.is_similar(m1_unaltered, True))
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Import something that's not a component
        self.assertRaisesRegex(
            TypeError, 'myokit.Component',
            m1.import_component, 'q')

        self.assertRaisesRegex(
            TypeError, 'myokit.Component',
            m1.import_component, [ms['q'], 'q'])

        # Import your own components
        self.assertRaisesRegex(
            ValueError, 'part of this model',
            m1.import_component, m1['p'], new_name='abc')

        # new_name is not string or list of correct length
        self.assertRaisesRegex(
            TypeError, 'new_name must be',
            m1.import_component, m1['p'], new_name=1)

        self.assertRaisesRegex(
            TypeError, 'new_name must be',
            m1.import_component, [m1['p'], m1['q']], new_name='abs')

        self.assertRaisesRegex(
            TypeError, 'new_name must be',
            m1.import_component, [m1['p'], m1['q']], new_name=['abs', 1])

        self.assertRaisesRegex(
            TypeError, 'new_name must be',
            m1.import_component, [m1['p'], m1['q']], new_name=['abs'])

        # Multiple imported components must be all from the same model
        m2 = myokit.parse_model('''
            [[model]]
            p.b = 0.2

            # Independent (except for time)
            [p]
            t = 0 [s] bind time
                in [s]
            a = 1 [m]
                in [m]
            # Comments should be stripped out during parsing, so this is OK.
            dot(b) = 2 * a
                in [m*s]

        ''')
        m2.validate()
        m2.check_units(myokit.UNIT_STRICT)

        self.assertRaisesRegex(
            ValueError, 'must be from the same model',
            m1.import_component, [m1['p'], m2['p']])

    def test_import_component_units(self):
        # Test :meth: 'import_component()' with unit conversion.

        # Source model, to import stuff from
        ms = myokit.parse_model('''
            [[model]]
            p.c = 0.1
            r.f = 0.2
            x.a = 0.2
            y.e = 0.2

            [e]
            t = 0 [s] bind time
                in [s]

            # Independent (except for time)
            [p]
            a = 1 [m] in [m]
            b = 10 [s] in [s]
            dot(c) = 0.2 [m/s]
                in [m]

            # Requires mapping, doesn't have states but has dot() reference
            [q]
            d = 3.2 [m/s] + dot(p.c)
                in [m/s]
            e = p.a + p.c + 0.1 [m]
                in [m]

            # Requires mapping, has a new state
            [r]
            use p.a, p.b
            dot(f) = a / b
                in [m]

            # Two components to import at the same time
            # (independent of the rest of the model)
            [x]
            use y.e
            dot(a) = c * e
                in [m*A]
            b = 3 * dot(e)
                in [m/s]
            c = 0.2 [A] * d
                in [A/s]
            d = 1 [1/s]
                in [1/s]

            [y]
            use x.d
            dot(e) = d * sub_e
                in [m]
                sub_e = 2 * e
                    in [m]

            # No time units used
            [s]
            x = 3 [kg] in [kg]
        ''')
        ms.validate()
        ms.check_units(myokit.UNIT_STRICT)

        # Make copy of ms, to ensure nothing is altered in original model
        ms_unaltered = ms.clone()

        # Conversion helpers
        vm = {'p.a': 'p.a', 'p.b': 'p.b', 'p.c': 'p.c'}
        s2ms = myokit.Number(1000, myokit.units.ms / myokit.units.s)
        mm2m = myokit.Number(0.001, myokit.units.m / myokit.units.mm)

        # Target model to import stuff into, with different time units
        m1 = myokit.parse_model('''
            [[model]]

            [e]
            t = 0 [ms] bind time
                in [ms]
        ''')
        m1.validate()
        m1.check_units(myokit.UNIT_STRICT)

        # Import p, should be same
        m1.import_component(ms['p'], convert_units=True)

        # Import q, should be same except for dot() expression
        m1.import_component(ms['q'], var_map=vm, convert_units=True)
        self.assertTrue(ms.is_similar(ms_unaltered, True))
        self.assertIn('q', m1)
        self.assertEqual(len(m1['q']), 2)
        self.assertEqual(m1.get('q.e').code(), ms.get('q.e').code())
        self.assertEqual(m1.get('q.d').unit(), ms.get('q.d').unit())
        self.assertEqual(
            m1.get('q.d').rhs().code(),
            myokit.Plus(myokit.Number(3.2, 'm/s'), myokit.Multiply(
                myokit.Derivative(myokit.Name(m1.get('p.c'))), s2ms)
            ).code())

        # Import r, should be same except for the state's RHS
        m1.import_component(ms['r'], var_map=vm, convert_units=True)
        self.assertTrue(ms.is_similar(ms_unaltered, True))
        self.assertIn('r', m1)
        self.assertEqual(len(m1['r']), 1)
        self.assertIn('f', m1['r'])
        self.assertTrue(m1.get('r.f').is_state())
        self.assertEqual(m1.get('r.f').unit(), ms.get('r.f').unit())
        self.assertEqual(
            m1.get('r.f').state_value(), ms.get('r.f').state_value())
        self.assertEqual(
            m1.get('r.f').rhs().code(),
            myokit.Multiply(ms.get('r.f').rhs(), s2ms).code())

        # Import multiple components
        m1.import_component([ms['x'], ms['y']], convert_units=True)
        self.assertTrue(m1.has_component('x'))
        self.assertTrue(m1.has_component('y'))
        self.assertFalse(m1['x'] is ms['x'])
        self.assertFalse(m1['y'] is ms['y'])
        self.assertEqual(m1.get('x.a').unit(), ms.get('x.a').unit())
        self.assertEqual(
            m1.get('x.a').state_value(), ms.get('x.a').state_value())
        self.assertEqual(
            m1.get('x.a').rhs().code(),
            myokit.Multiply(ms.get('x.a').rhs(), s2ms).code())
        self.assertEqual(
            m1.get('y.e').state_value(), ms.get('y.e').state_value())
        self.assertEqual(
            m1.get('y.e').rhs().code(),
            myokit.Multiply(ms.get('y.e').rhs(), s2ms).code())

        # Target model with different space units
        m1 = myokit.parse_model('''
            [[model]]
            p.c = 0.1

            [e]
            time = 0 [s] bind time
                in [s]

            [p]
            a = 1 [mm] in [mm]
            b = 10 [s] in [s]
            dot(c) = 0.2 [mm/s]
                in [mm]
        ''')
        m1.validate()
        m1.check_units(myokit.UNIT_STRICT)

        # Import q, converting p.a and dot(p.c)
        m1.import_component(ms['q'], var_map=vm, convert_units=True)
        self.assertTrue(ms.is_similar(ms_unaltered, True))
        self.assertIn('q', m1)
        self.assertEqual(len(m1['q']), 2)
        self.assertEqual(m1.get('q.d').unit(), ms.get('q.d').unit())
        self.assertEqual(
            m1.get('q.d').rhs().code(),
            myokit.Plus(
                myokit.Number(3.2, 'm/s'),
                myokit.Multiply(
                    myokit.Derivative(myokit.Name(m1.get('p.c'))), mm2m)
            ).code())
        self.assertEqual(m1.get('q.e').unit(), ms.get('q.e').unit())
        self.assertEqual(
            m1.get('q.e').rhs().code(),
            myokit.Plus(myokit.Plus(
                myokit.Multiply(myokit.Name(m1.get('p.a')), mm2m),
                myokit.Multiply(myokit.Name(m1.get('p.c')), mm2m)),
                myokit.Number(0.1, 'm')).code())

        # Target model with different time and space units
        m1 = myokit.parse_model('''
            [[model]]
            p.c = 0.1

            [e]
            time = 0 [ms] bind time
                in [ms]

            [p]
            a = 1 [mm] in [mm]
            b = 10 [ms] in [ms]
            dot(c) = 0.2 [mm/ms]
                in [mm]
        ''')
        m1.validate()
        m1.check_units(myokit.UNIT_STRICT)

        # Import q and p, converting p.a and dot(p.c)
        m1.import_component(ms['q'], var_map=vm, convert_units=True)
        self.assertTrue(ms.is_similar(ms_unaltered, True))
        self.assertIn('q', m1)
        self.assertEqual(len(m1['q']), 2)
        self.assertEqual(m1.get('q.d').unit(), ms.get('q.d').unit())
        self.assertEqual(
            m1.get('q.d').rhs().code(),
            myokit.Plus(
                myokit.Number(3.2, 'm/s'),
                myokit.Derivative(myokit.Name(m1.get('p.c')))
            ).code())
        self.assertEqual(m1.get('q.e').unit(), ms.get('q.e').unit())
        self.assertEqual(
            m1.get('q.e').rhs().code(),
            myokit.Plus(myokit.Plus(
                myokit.Multiply(myokit.Name(m1.get('p.a')), mm2m),
                myokit.Multiply(myokit.Name(m1.get('p.c')), mm2m)),
                myokit.Number(0.1, 'm')).code())

        # Attempt import with incompatible time units 1:
        # Component that defines a derivative in m/s
        m1 = myokit.parse_model('''
            [[model]]

            [e]
            time = 0 [A] bind time
                in [A]
        ''')
        m1.validate()
        m1.check_units(myokit.UNIT_STRICT)
        self.assertRaisesRegex(
            myokit.VariableMappingError, 'time variables',
            m1.import_component, ms['p'], convert_units=True)
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Attempt import with incompatible time units 1:
        # Component that uses a dot expression
        m1 = myokit.parse_model('''
            [[model]]
            p.c = 0

            [e]
            time = 0 [A] bind time
                in [A]

            [p]
            a = 1 [m] in [m]
            dot(c) = 0.2 [m/A]
                in [m]
        ''')
        m1.validate()
        m1.check_units(myokit.UNIT_STRICT)
        vm = {'p.a': 'p.a', 'p.c': 'p.c'}
        self.assertRaisesRegex(
            myokit.VariableMappingError, 'time variables',
            m1.import_component, ms['q'], var_map=vm, convert_units=True)
        self.assertTrue(ms.is_similar(ms_unaltered, True))

        # Attempt import with incompatible mapped (space) units
        m1 = myokit.parse_model('''
            [[model]]
            p.c = 0

            [e]
            time = 0 [s] bind time
                in [s]

            [p]
            a = 1 [V] in [V]
            b = 10 [s] in [s]
            dot(c) = 0.2 [V/s]
                in [V]
        ''')
        m1.validate()
        m1.check_units(myokit.UNIT_STRICT)
        vm = {'p.a': 'p.a', 'p.b': 'p.b', 'p.c': 'p.c'}
        self.assertRaisesRegex(
            myokit.VariableMappingError, 'Unable to convert',
            m1.import_component, ms['q'], var_map=vm, convert_units=True)
        self.assertTrue(ms.is_similar(ms_unaltered, True))

    def test_item_at_text_position(self):
        # Test :meth:`Model.item_at_text_position()`.

        text = [
            '[[model]]',        # 1
            'c.x = 0',          # 2
            '',                 # 3
            '[e]',              # 4
            't = 0 bind time',
            '',
            '[c]',
            'desc: This is a test component',
            'dot(x) = (10 - x) / y',
            'y = 5 + y1',
            '    y1 = 3',
            ''
        ]
        model = myokit.parse_model(text)
        e = model.get('e')
        t = model.get('e.t')
        c = model.get('c')
        x = model.get('c.x')
        y = model.get('c.y')
        y1 = model.get('c.y.y1')

        def check(line, char, var):
            tv = model.item_at_text_position(line, char)
            if var is None:
                self.assertIsNone(tv)
            else:
                token, var2 = tv
                self.assertIsNotNone(var2)
                self.assertEqual(var.qname(), var2.qname())

        # It doesn't work on initial conditions
        check(1, 0, None)
        check(1, 1, None)
        check(1, 2, None)

        # Find the component e and its variable
        check(4, 0, None)
        check(4, 1, e)
        check(4, 2, None)
        check(5, 0, t)
        check(5, 1, None)

        # Find the component c and its variables
        check(7, 1, c)
        check(9, 4, x)
        check(10, 0, y)
        check(11, 4, y1)

    def test_label(self):
        # Tests setting and getting of labels

        # Note that set_label() is part of Variable, so not tested here
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_label('hello')
        y = c.add_variable('y')
        y.set_label('goodbye')
        z = c.add_variable('z')
        z.set_label('x')

        # Test label()
        self.assertEqual(m.label('goodbye'), y)
        self.assertEqual(m.label('hello'), x)
        self.assertEqual(m.label('x'), z)
        self.assertEqual(m.label('y'), None)

        # Test labels()
        labels = dict(m.labels())
        self.assertEqual(labels['goodbye'], y)
        self.assertEqual(labels['hello'], x)
        self.assertEqual(labels['x'], z)
        self.assertFalse('y' in labels)

        # Test labelx()
        self.assertEqual(m.labelx('goodbye'), y)
        self.assertEqual(m.labelx('hello'), x)
        self.assertEqual(m.labelx('x'), z)
        self.assertRaisesRegex(
            myokit.IncompatibleModelError,
            'No variable found with label "y"',
            m.labelx, 'y')

        # Test incompatible model error includes name if possible
        self.assertRaisesRegex(
            myokit.IncompatibleModelError,
            'Incompatible model: No variable found',
            m.labelx, 'y')
        m.set_name('Bert')
        self.assertRaisesRegex(
            myokit.IncompatibleModelError,
            'Incompatible model <Bert>: No variable found',
            m.labelx, 'y')

    def test_labels(self):
        # Test setting labels and :meth:`Model.labels()`.

        # Test set_label() and labels()
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        v.set_label('membrane_potential')
        w = c.add_variable('w')
        w.set_rhs(1)
        x = c.add_variable('x')
        x.set_rhs(1)
        labels = list(m.labels())
        self.assertEqual(len(labels), 1)
        self.assertEqual(labels[0][0], 'membrane_potential')
        self.assertEqual(labels[0][1], v)

        # Can't have two labels
        self.assertRaisesRegex(
            myokit.InvalidLabelError, 'already has a label', v.set_label,
            'bert')

        # No two variables can have the same label
        self.assertRaisesRegex(
            myokit.InvalidLabelError, 'already in use', w.set_label,
            'membrane_potential')

        # Labels can't overlap with bindings
        self.assertRaisesRegex(
            myokit.InvalidLabelError, 'in use as a binding', w.set_label,
            'time')

    def test_load_save_state(self):
        # Test :meth:`Model.save_state()` and :meth:`Model.load_state()`.

        m = myokit.load_model('example')
        s1 = m.state()
        with TemporaryDirectory() as d:
            path = d.path('state.csv')
            m.save_state(path)
            self.assertEqual(m.state(), s1)
            sx = list(s1)
            sx[0] = 10
            m.set_state(sx)
            self.assertNotEqual(m.state(), s1)
            m.load_state(path)
            self.assertEqual(m.state(), s1)

    def test_map_to_state(self):
        # Test :meth:`Model.map_to_state()`.

        # Create test model
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        v.promote(0)
        w = c.add_variable('w')
        w.set_rhs('1 - w')
        w.promote(0)

        # List of numbers
        x = m.map_to_state([1, 2])
        self.assertEqual(x, [1.0, 2.0])

        # Wrong size list
        self.assertRaisesRegex(
            ValueError, 'Wrong number', m.map_to_state, [1, 2, 3])

        # String not tested, handled by parse_state.

        # Dict of names
        x = m.map_to_state({'c.v': 2, 'c.w': 3})
        self.assertEqual(x, [2.0, 3.0])

        # Dict of Variables
        x = m.map_to_state({v: 2, 'c.w': 3})
        self.assertEqual(x, [2.0, 3.0])

        # Missing state
        self.assertRaisesRegex(
            ValueError, 'Missing state', m.map_to_state, {v: 2})

    def test_no_rhs_error(self):
        # Test an exception is raised when a variable is missing an rhs.

        m = myokit.Model('LotkaVolterra')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_binding('time')
        self.assertRaises(myokit.MissingRhsError, m.validate)
        t.set_rhs(myokit.Number(0))
        m.validate()
        a = c0.add_variable('test')
        self.assertRaises(myokit.MissingRhsError, m.validate)
        a.set_rhs(myokit.Number(1))
        m.validate()
        b = c0.add_variable('derv')
        b.promote(10)
        self.assertRaises(myokit.MissingRhsError, m.validate)
        b.set_rhs(2)
        m.validate()

    def test_no_time_variable(self):
        # Test an exception is raised if nothing is bound to time.

        m = myokit.Model('LotkaVolterra')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_rhs(myokit.Number(0))
        self.assertRaises(myokit.MissingTimeVariableError, m.validate)

    def test_name(self):
        # Test :meth:`Model.set_name(name)`.

        m = myokit.Model()
        self.assertIsNone(m.name())
        m.set_name('ernie')
        self.assertEqual(m.name(), 'ernie')
        m.set_name(None)
        self.assertIsNone(m.name())
        m.set_name(None)
        self.assertIsNone(m.name())

        m = myokit.Model(name='ernie')
        self.assertEqual(m.name(), 'ernie')
        m.set_name(None)
        self.assertIsNone(m.name())
        m.set_name('bert')
        self.assertEqual(m.name(), 'bert')

    def test_pickling(self):
        # Test pickling and unpickling a model

        # Test model structure
        m1 = myokit.load_model('example')
        m_bytes = pickle.dumps(m1)
        m2 = pickle.loads(m_bytes)
        self.assertFalse(m1 is m2)
        self.assertFalse(m1 == m2)
        self.assertIsInstance(m2, myokit.Model)
        self.assertTrue(m1.is_similar(m2))

        # Test unique names and prefixes (see also test_clone)
        m1.reserve_unique_names('barnard', 'lincoln', 'glasgow')
        m1.reserve_unique_name_prefix('monkey', 'giraffe')
        m1.reserve_unique_name_prefix('ostrich', 'turkey')
        m_bytes = pickle.dumps(m1)
        m2 = pickle.loads(m_bytes)
        self.assertTrue(m1.is_similar(m2, True))

    def test_remove_component(self):
        # Test the removal of a component.

        # Create model
        m = myokit.Model('LotkaVolterra')
        # Simplest case
        X = m.add_component('X')
        self.assertEqual(m.count_components(), 1)
        m.remove_component(X)
        self.assertEqual(m.count_components(), 0)
        self.assertRaises(KeyError, m.remove_component, X)

        # Test if orphaned
        self.assertIsNone(X.parent())

        # Re-adding
        self.assertEqual(m.count_components(), 0)
        X = m.add_component('X')
        self.assertEqual(m.count_components(), 1)

        # With internal variables and string name
        a = X.add_variable('a')
        a.set_rhs(myokit.Number(4))
        b = X.add_variable('b')
        b.set_rhs(myokit.Name(a))
        m.remove_component('X')
        self.assertEqual(m.count_components(), 0)

        # With dependencies from another component
        X = m.add_component('X')
        a = X.add_variable('a')
        a.set_rhs(myokit.Number(45))
        b = X.add_variable('b')
        b.set_rhs(myokit.Name(b))
        Y = m.add_component('Y')
        c = Y.add_variable('c')
        c.set_rhs(myokit.Name(a))
        d = Y.add_variable('d')
        d.set_rhs(myokit.Name(c))
        self.assertEqual(m.count_components(), 2)
        self.assertRaises(myokit.IntegrityError, m.remove_component, X)
        self.assertEqual(m.count_components(), 2)

        # In the right order...
        m.remove_component(Y)
        self.assertEqual(m.count_components(), 1)
        m.remove_component(X)
        self.assertEqual(m.count_components(), 0)

    def test_remove_derivative_references(self):
        # Test the remove_derivative_references() method.

        m0 = myokit.parse_model("""
            [[model]]
            c.x = 0
            c.y = 1

            [e]
            t = 0 bind time

            [c]
            dot(x) = (1 - x) * alpha
                alpha = 3 * beta + dot_x
                beta = exp(-y) + cc
                    cc = 1.23
                dot_x = 3
            dot(y) = (12 - y) / 7
            z = 3 * dot(y)

            [d]
            z = 3 * dot(c.x) / dot(c.y)
            """)
        m2 = myokit.parse_model("""
            [[model]]
            c.x = 0
            c.y = 1

            [e]
            t = 0 bind time

            [c]
            dot(x) = dot_x_1
            dot_x_1 = (1 - x) * alpha
                alpha = 3 * beta + dot_x
                beta = exp(-y) + cc
                    cc = 1.23
                dot_x = 3
            dot(y) = dot_y
            dot_y = (12 - y) / 7
            z = 3 * dot_y

            [d]
            z = 3 * c.dot_x_1 / c.dot_y
            """)

        # Remove derivatives from m1
        m1 = m0.clone()
        m1.remove_derivative_references()

        # Assert model matches expected code
        self.assertEqual(m1.code(), m2.code())

        # Assert models both produce the same derivatives
        dy1 = m1.evaluate_derivatives()
        dy2 = m2.evaluate_derivatives()
        self.assertEqual(dy1, dy2)

        # Test time unit is None
        self.assertIsNone(m1.get('c.dot_y').unit())

        # Only one unit set? Then unit is still None
        m1 = m0.clone()
        m1.get('c.y').set_unit('mV')
        m1.remove_derivative_references()
        self.assertIsNone(m1.get('c.dot_y').unit())

        m1 = m0.clone()
        m1.get('e.t').set_unit('ms')
        m1.remove_derivative_references()
        self.assertIsNone(m1.get('c.dot_y').unit())

        # Both units set? Then unit is division of two
        m1 = m0.clone()
        m1.get('e.t').set_unit('ms')
        m1.get('c.y').set_unit('mV')
        m1.remove_derivative_references()
        self.assertEqual(m1.get('c.dot_y').unit(), myokit.parse_unit('mV/ms'))

    def test_remove_variable_with_alias(self):
        # Test cloning of a variable with an alias after an add / remove event.

        m = myokit.Model('AddRemoveClone')
        c = m.add_component('c')
        p = c.add_variable('p')
        p.set_binding('time')
        p.set_rhs(0)
        q = c.add_variable('q')
        q.set_rhs(12)
        m.validate()    # Raises error if not ok
        m.clone()       # Raises error if not ok
        d = m.add_component('d')
        d.add_alias('bert', p)
        e = d.add_variable('e')
        e.set_rhs('10 * bert')
        m.validate()
        m.clone()
        d.add_alias('ernie', q)
        m.validate()
        m.clone()
        c.remove_variable(q)
        m.validate()
        m.clone()   # Will raise error if alias isn't deleted

    def test_reorder_state(self):
        # Test :meth:`Model.reorder_state()`.

        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        v.promote(0)
        w = c.add_variable('w')
        w.set_rhs(1)
        w.promote(0)
        self.assertEqual(list(m.states()), [v, w])
        m.reorder_state([w, v])
        self.assertEqual(list(m.states()), [w, v])
        m.reorder_state([w, v])
        self.assertEqual(list(m.states()), [w, v])
        m.reorder_state([v, w])
        self.assertEqual(list(m.states()), [v, w])

        # Wrong number of states
        self.assertRaisesRegex(
            ValueError, 'number of entries', m.reorder_state, [v])
        self.assertRaisesRegex(
            ValueError, 'number of entries', m.reorder_state, [v, w, v])

        # Duplicate entries
        self.assertRaisesRegex(
            ValueError, 'Duplicate', m.reorder_state, [v, v])

        # Not a state
        self.assertRaisesRegex(
            ValueError, 'must all be', m.reorder_state, [v, t])

    def test_resolve_interdependent_components(self):
        # Test :meth:`Model.resolve_interdependent_components()`.

        # Create test model
        m = myokit.Model()
        c1 = m.add_component('c1')
        t = c1.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        c2 = m.add_component('c2')
        v = c2.add_variable('v')
        c3 = m.add_component('c3')
        w = c3.add_variable('w')
        x = c3.add_variable('x')
        v.set_rhs(3)
        w.set_rhs(2)
        x.set_rhs(1)

        # Test merge not required
        self.assertEqual(m.has_interdependent_components(), False)

        # Test merge doesn't change model
        self.assertEqual(m.count_components(), 3)
        m.resolve_interdependent_components()
        self.assertEqual(m.count_components(), 3)

        # Create interdependent components
        v.set_rhs('3 - c3.x')
        w.set_rhs('1 - c2.v')

        # Test merge is required
        self.assertTrue(m.has_interdependent_components())

        # Merge
        self.assertEqual(m.count_components(), 3)
        m.resolve_interdependent_components()
        self.assertEqual(m.count_components(), 4)
        m.get('remaining')

        # Test name clash detection
        m = myokit.Model()
        c1 = m.add_component('remaining')
        t = c1.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        c2 = m.add_component('remaining_1')
        v = c2.add_variable('v')
        c3 = m.add_component('c3')
        w = c3.add_variable('w')
        x = c3.add_variable('x')
        v.set_rhs('3 - c3.x')
        w.set_rhs('1 - remaining_1.v')
        x.set_rhs('12')

        self.assertEqual(m.count_components(), 3)
        m.resolve_interdependent_components()
        self.assertEqual(m.count_components(), 4)
        m.get('remaining_2')

    def test_sequence_interface(self):
        # Test the sequence interface implementation
        model = myokit.load_model('example')

        cs = [c for c in model]
        self.assertEqual(cs, list(model.components()))
        self.assertEqual(len(cs), len(model))
        c = model['membrane']
        self.assertEqual(c.name(), 'membrane')

    def test_show_evaluation_of(self):
        # Test :meth:`Model.show_evaluation_of(variable)`.
        # Depends mostly on `references()`, and `code()` methods.

        m = myokit.load_model('example')

        # Test for literal
        e = m.show_evaluation_of('cell.Na_o')
        self.assertIn('cell.Na_o = ', e)
        self.assertIn('Literal constant', e)
        self.assertEqual(len(e.splitlines()), 6)

        # Test for calculated constant
        e = m.show_evaluation_of('ina.ENa')
        self.assertIn('ina.ENa = ', e)
        self.assertIn('Calculated constant', e)
        self.assertEqual(len(e.splitlines()), 12)

        # Test for intermediary variable
        e = m.show_evaluation_of('ina.INa')
        self.assertIn('ina.INa = ', e)
        self.assertIn('Intermediary variable', e)
        self.assertEqual(len(e.splitlines()), 15)

        # Test for state variable (with nested variables)
        e = m.show_evaluation_of('ina.m')
        self.assertIn('ina.m = ', e)
        self.assertIn('State variable', e)
        self.assertEqual(len(e.splitlines()), 15)

        # Test with guessing of similar
        e = m.show_evaluation_of('ina.Na_o')
        self.assertIn('not found', e)
        self.assertIn('cell.Na_o = ', e)
        self.assertIn('Literal constant', e)
        self.assertEqual(len(e.splitlines()), 7)

        # Test with nothing similar
        m = myokit.Model()
        self.assertRaises(Exception, m.show_evaluation_of, 'Hello')

    def test_show_expressions_for(self):
        # Test :meth:`Model.show_expressions_for(variable)`.

        m = myokit.load_model('example')
        e = m.show_expressions_for(m.get('ina.INa'))
        self.assertIn('ina.INa is a function of', e)
        self.assertEqual(len(e.splitlines()), 22)

    def test_show_line_of(self):
        # Test :meth:`Model.show_line_of(variable)`.

        # Check string with info
        m = myokit.load_model('example')
        v = m.get('ina.INa')
        e = m.show_line_of(v)
        self.assertIn('Defined on line 91', e)
        self.assertIn('Intermediary variable', e)
        self.assertEqual(len(e.splitlines()), 4)

        # Check with freshly made model
        m2 = m.clone()
        v2 = m2.get('ina.INa')
        e = m2.show_line_of(v2)
        self.assertNotIn('Defined on line', e)
        self.assertIn('Intermediary variable', e)
        self.assertEqual(len(e.splitlines()), 3)

        # 'raw' version
        self.assertEqual(m.show_line_of(v, raw=True), 91)
        self.assertIsNone(m2.show_line_of(v2, raw=True))

    def test_str(self):
        # Test conversion to string

        m = myokit.Model()
        self.assertEqual(str(m), '<Unnamed Model>')
        self.assertEqual(repr(m), '<Unnamed Model>')

        m.set_name('bert')
        self.assertEqual(str(m), '<Model(bert)>')
        self.assertEqual(repr(m), '<Model(bert)>')

    def test_suggest(self):
        # Test :meth:`Model.suggest(variable_name)`.

        m = myokit.Model()
        c1 = m.add_component('c1')
        t = c1.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        c2 = m.add_component('c2')
        v = c2.add_variable('v')
        v.set_rhs('3')

        # Test with correct name
        found, suggested, msg = m.suggest_variable('c1.time')
        self.assertEqual(found, t)
        self.assertIsNone(suggested)
        self.assertIsNone(msg)

        # Test with wrong name
        found, suggested, msg = m.suggest_variable('c1.tim')
        self.assertIsNone(found)
        self.assertEqual(suggested, t)
        self.assertIn('Unknown', msg)

        # Test with case mismatch
        found, suggested, msg = m.suggest_variable('c1.timE')
        self.assertIsNone(found)
        self.assertEqual(suggested, t)
        self.assertIn('Case mismatch', msg)

        # Test without component
        found, suggested, msg = m.suggest_variable('time')
        self.assertIsNone(found)
        self.assertEqual(suggested, t)
        self.assertIn('No component', msg)

    def test_unique_names_1(self):
        # Test Model.create_unique_names().

        # Heavily disputed variable names
        m = myokit.Model()
        a = m.add_component('a')
        ax = a.add_variable('x')
        b = m.add_component('b')
        bx = b.add_variable('x')
        x = m.add_component('x')
        xx = x.add_variable('x')
        m.create_unique_names()
        self.assertEqual(a.uname(), 'a')
        self.assertEqual(ax.uname(), 'a_x')
        self.assertEqual(b.uname(), 'b')
        self.assertEqual(bx.uname(), 'b_x')
        self.assertEqual(x.uname(), 'x_1')
        self.assertEqual(xx.uname(), 'x_x')

        # Disputed variable name --> Generated name already exists
        m = myokit.Model()
        a = m.add_component('a')
        ax = a.add_variable('x')
        abx = a.add_variable('b_x')
        aax = a.add_variable('a_x')
        ax11 = a.add_variable('x_1_1')
        b = m.add_component('b')
        bx = b.add_variable('x')
        bx11 = b.add_variable('x_1_1')
        m.create_unique_names()
        self.assertEqual(a.uname(), 'a')
        self.assertEqual(ax.uname(), 'a_x_1')
        self.assertEqual(abx.uname(), 'b_x')
        self.assertEqual(aax.uname(), 'a_x')
        self.assertEqual(ax11.uname(), 'a_x_1_1')
        self.assertEqual(b.uname(), 'b')
        self.assertEqual(bx.uname(), 'b_x_1')
        self.assertEqual(bx11.uname(), 'b_x_1_1')

        # Disputed component name
        m = myokit.Model()
        a = m.add_component('a')
        a.add_variable('x')
        m.add_component('x')
        m.create_unique_names()
        self.assertEqual(m.get('a').uname(), 'a')
        self.assertEqual(m.get('a.x').uname(), 'a_x')
        self.assertEqual(m.get('x').uname(), 'x_1')

        # Disputed component name --> Generated name already exists
        m = myokit.Model()
        a = m.add_component('a')
        a.add_variable('x')
        m.add_component('x')
        m.add_component('x_1')
        m.create_unique_names()
        self.assertEqual(m.get('a').uname(), 'a')
        self.assertEqual(m.get('a.x').uname(), 'a_x')
        self.assertEqual(m.get('x').uname(), 'x_2')
        self.assertEqual(m.get('x_1').uname(), 'x_1')

    def test_unique_names_2(self):
        # Test reserving of unique name prefixes

        m = myokit.Model()
        a = m.add_component('paddington')
        x = a.add_variable('v_x')
        y = a.add_variable('bear')
        b = m.add_component('yogi')
        z = b.add_variable('bear')

        m.create_unique_names()
        self.assertEqual(x.uname(), 'v_x')
        self.assertEqual(y.uname(), 'paddington_bear')
        self.assertEqual(z.uname(), 'yogi_bear')

        # Don't allow v_ prefix
        m.reserve_unique_name_prefix('v_', 'var_')
        m.create_unique_names()
        self.assertEqual(x.uname(), 'var_v_x')
        self.assertEqual(y.uname(), 'paddington_bear')
        self.assertEqual(z.uname(), 'yogi_bear')

        # Don't allow pad prefix
        m.reserve_unique_name_prefix('pad', 'marmelade_')
        m.create_unique_names()
        self.assertEqual(x.uname(), 'var_v_x')
        self.assertEqual(y.uname(), 'marmelade_paddington_bear')
        self.assertEqual(z.uname(), 'yogi_bear')
        self.assertEqual(a.uname(), 'marmelade_paddington')

        # Test bad calls
        self.assertRaisesRegex(
            ValueError, 'prefix cannot be empty',
            m.reserve_unique_name_prefix, '', 'x')
        self.assertRaisesRegex(
            ValueError, 'prepend cannot be empty',
            m.reserve_unique_name_prefix, 'x', '')
        self.assertRaisesRegex(
            ValueError, 'prepend cannot start with prefix',
            m.reserve_unique_name_prefix, 'x', 'x')

    def test_validate_and_remove_unused_variables(self):
        # Test :class:`Model.validate` with ``remove_unused_variables=True``.

        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        z1 = z.add_variable('z1')
        x.set_rhs('(10 - x) / y')
        x.promote(0)
        y.set_rhs(1)
        z.set_rhs('2 + z1')
        z1.set_rhs(3)

        # Two unused variables: z and z1
        m.validate()
        self.assertEqual(len(m.warnings()), 2)

        # Remove unused variables
        m.validate(remove_unused_variables=True)
        self.assertEqual(len(m.warnings()), 2)  # 2 removal warnings
        m.validate()
        self.assertEqual(len(m.warnings()), 0)  # issue fixed!

    def test_value(self):
        # Test :meth:`Model.value()`.

        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('t')
        t.set_binding('time')
        t.set_rhs(1000)
        self.assertEqual(m.value('c.t'), 1000)

    def test_warnings(self):
        # Test Model.has_warnings(), model.warnings() and
        # Model.format_warnings().

        # Test model without warnings
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        v.promote(0.1)
        m.validate()

        self.assertFalse(m.has_warnings())
        self.assertIn('0 validation warning', m.format_warnings())
        self.assertEqual(m.warnings(), [])

        # Test model with warnings
        v.validate()
        v.demote()
        v.validate()
        v.set_rhs(3)
        m.validate()

        self.assertTrue(m.has_warnings())
        self.assertIn('1 validation warning', m.format_warnings())
        self.assertIn('Unused variable', str(m.warnings()[0]))


if __name__ == '__main__':
    unittest.main()

