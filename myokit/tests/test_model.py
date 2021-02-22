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
import unittest

import myokit

from shared import TemporaryDirectory, WarningCollector


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

        # Dot operator is not allowed
        self.assertRaisesRegex(
            myokit.InvalidFunction, r'dot\(\) operator',
            m.add_function, 'fdot', ('a', ), 'dot(a)')

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
        self.assertEqual(m1, m2)

        # Test unames and uname prefixes
        m1.reserve_unique_names('barnard', 'lincoln', 'glasgow')
        m1.reserve_unique_name_prefix('monkey', 'giraffe')
        m1.reserve_unique_name_prefix('ostrich', 'turkey')
        m2 = m1.clone()
        self.assertEqual(m1, m2)

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

    def test_equals(self):
        # Check that equality takes both code() and unames into account

        # Test without custom reserved names
        m1 = myokit.load_model('example')
        m2 = m1.clone()
        self.assertIsInstance(m2, myokit.Model)
        self.assertFalse(m1 is m2)
        self.assertEqual(m1, m2)
        self.assertEqual(m1, m1)

        # Test with none-model
        self.assertNotEqual(m1, None)
        self.assertNotEqual(m1, m1.code())

        # Add reserved names
        m1.reserve_unique_names('bertie')
        self.assertNotEqual(m1, m2)
        m1.reserve_unique_names('clair')
        self.assertNotEqual(m1, m2)
        m2.reserve_unique_names('clair', 'bertie')
        self.assertEqual(m1, m2)

        # Add reserved name prefixes
        m1.reserve_unique_name_prefix('aa', 'bb')
        m1.reserve_unique_name_prefix('cc', 'dd')
        self.assertNotEqual(m1, m2)
        m2.reserve_unique_name_prefix('aa', 'bb')
        m2.reserve_unique_name_prefix('cc', 'ee')
        self.assertNotEqual(m1, m2)
        m2.reserve_unique_name_prefix('cc', 'dd')
        self.assertEqual(m1, m2)

    def test_eval_state_derivatives(self):
        # Test Model.eval_state_derivatives().
        model = myokit.Model('m')
        component = model.add_component('comp1')
        t = component.add_variable('time')
        t.set_binding('time')
        t.set_rhs(1)
        a = component.add_variable('a')
        b = component.add_variable('b')
        c = component.add_variable('c')
        a.promote(1)
        a.set_rhs('1')
        b.promote(2)
        b.set_rhs('2 * b')
        c.promote(3)
        c.set_rhs('b + c')
        model.validate()
        self.assertEqual(model.eval_state_derivatives(), [1, 4, 5])
        self.assertEqual(
            model.eval_state_derivatives(state=[1, 1, 2]), [1, 2, 3])
        c.set_rhs('b + c + time')
        self.assertEqual(model.eval_state_derivatives(), [1, 4, 6])
        self.assertEqual(
            model.eval_state_derivatives(state=[1, 1, 2], inputs={'time': 0}),
            [1, 2, 3])

        # Errors
        c.set_rhs('(b + c) / 0')
        self.assertRaises(myokit.NumericalError, model.eval_state_derivatives)
        nan = model.eval_state_derivatives(ignore_errors=True)[2]
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

        # Test without arguments
        self.assertEqual(
            m.format_state_derivatives(),
'membrane.V = -84.5286                   dot = -5.68008003798848027e-02\n' # noqa
'ina.m      = 0.0017                     dot = -4.94961486033834719e-03\n' # noqa
'ina.h      = 0.9832                     dot =  9.02025299127830887e-06\n' # noqa
'ina.j      = 0.995484                   dot = -3.70409866928434243e-04\n' # noqa
'ica.d      = 3e-06                      dot =  3.68067721821794798e-04\n' # noqa
'ica.f      = 1.0                        dot = -3.55010150519739432e-07\n' # noqa
'ik.x       = 0.0057                     dot = -2.04613933160084307e-07\n' # noqa
'ica.Ca_i   = 0.0002                     dot = -6.99430692442154227e-06'    # noqa
        )

        # Test with state argument
        state1 = [1, 2, 3, 4, 5, 6, 7, 8]
        state1[2] = 536.46745856785678567845745637
        self.assertEqual(
            m.format_state_derivatives(state1),
'membrane.V = 1                          dot =  1.90853168050245158e+07\n' # noqa
'ina.m      = 2                          dot = -1.56738349674489310e+01\n' # noqa
'ina.h      =  5.36467458567856738e+02   dot = -3.05729251015767022e+03\n' # noqa
'ina.j      = 4                          dot = -1.15731427949362953e+00\n' # noqa
'ica.d      = 5                          dot = -1.85001944916516836e-01\n' # noqa
'ica.f      = 6                          dot = -2.15435819790876573e-02\n' # noqa
'ik.x       = 7                          dot = -1.25154369264425316e-02\n' # noqa
'ica.Ca_i   = 8                          dot = -5.63431267451130036e-01' # noqa                                       ^ ^^    ^ ---------   ^
        )

        # Test with invalid state argument
        self.assertRaisesRegex(
            ValueError, r'list of \(8\)',
            m.format_state_derivatives, [1, 2, 3])

        # Test with state and precision argument
        # Ignoring some of the middle digits, as they differ on some (but not
        # all!) travis builds.
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
        self.assertIsInstance(m2, myokit.Model)
        self.assertEqual(m1, m2)

        # Test unique names and prefixes (see also test_clone)
        m1.reserve_unique_names('barnard', 'lincoln', 'glasgow')
        m1.reserve_unique_name_prefix('monkey', 'giraffe')
        m1.reserve_unique_name_prefix('ostrich', 'turkey')
        m_bytes = pickle.dumps(m1)
        m2 = pickle.loads(m_bytes)
        self.assertEqual(m1, m2)

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
        dy1 = m1.eval_state_derivatives()
        dy2 = m2.eval_state_derivatives()
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

        # Test deprecated name
        with WarningCollector() as wc:
            m.merge_interdependent_components()
        self.assertIn('deprecated', wc.text())
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

        # Test deprecated alias
        with WarningCollector() as wc:
            m.show_line(m.get('ina.INa'))
        self.assertIn('deprecated', wc.text())

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
