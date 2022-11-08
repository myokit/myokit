#!/usr/bin/env python3
#
# Tests the expression classes.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import pickle
import unittest

import numpy as np

import myokit

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


# Unit --> See test_units.py
# Quantity --> See test_units.py


# Tiny model for partial derivative testing.
pd_model = myokit.parse_model("""
    [[model]]
    name: pd_model
    ina.m = 0.1
    membrane.V = -80
    bound.dot_pace_direct = 0
    bound.dot_pace_indirect = 0

    [engine]
    time = 0 [ms]
        in [ms]
        bind time

    [membrane]
    dot(V) = (ina.I1 + ina.I2) / C
        in [mV]
    C = 10 [pF]
        in [pF]

    [ina]
    use membrane.V
    a = 1 [1/ms] in [1/ms]
    b = 10 [1/mV] in [1/mV]
    c = 2 [1/ms] in [1/ms]
    d = 8 [1/mV] in [1/mV]
    k1 = a * exp(b * V)
        in [1/ms]
    k2 = c * exp(-d * V)
        in [1/ms]
    inf = k1 * tau
        in [1]
    tau = 1 / (k1 + k2)
        in [ms]
    dot(m) = (inf - m) / tau
        in [1]
    E = 2 * E2 in [mV]
    E2 = E3 / 3 in [mV]
    E3 = 100 [mV] in [mV]
    g = 16 [nS] in [nS]
    I1 = 0.6 * g * m^3 * (V - E)
        in [pA]
    I2 = 0.4 * g * m^3 * (V - E)
        in [pA]

    [bound]
    pace = 0 bind pace
    pace_direct = pace
    pace_indirect = pace_direct
    time_direct = engine.time
        in [ms]
    time_indirect = time_direct
        in [ms]
    dot(dot_pace_direct) = pace_direct
        in [ms]
    dot(dot_pace_indirect) = pace_indirect
        in [ms]

""")


class ExpressionTest(unittest.TestCase):
    """ Tests various methods of the :class:`myokit.Expression` class. """

    def test_contains_type(self):
        # Test :meth:`Expression.contains_type`.

        self.assertTrue(myokit.Name('x').contains_type(myokit.Name))
        self.assertFalse(myokit.Name('x').contains_type(myokit.Number))
        self.assertTrue(myokit.Number(4).contains_type(myokit.Number))
        self.assertFalse(myokit.Number(4).contains_type(myokit.Name))

        e = myokit.parse_expression('x + 3')
        self.assertTrue(e.contains_type(myokit.Name))
        self.assertTrue(e.contains_type(myokit.Number))
        self.assertTrue(e.contains_type(myokit.Plus))
        self.assertFalse(e.contains_type(myokit.Minus))

        e = myokit.parse_expression('x * (x * (x * (x * (x * (1 + 1)))))')
        self.assertTrue(e.contains_type(myokit.Multiply))
        self.assertTrue(e.contains_type(myokit.Plus))
        self.assertTrue(e.contains_type(myokit.Number))
        self.assertFalse(e.contains_type(myokit.Minus))

    def test_depends_on(self):
        # Tests Expression.depends_on()

        # Shallow checking
        m = pd_model.clone()
        c = m.get('membrane.C').lhs()
        v = m.get('membrane.V').lhs()
        self.assertTrue(c.depends_on(c))
        self.assertFalse(c.depends_on(v))
        self.assertTrue(v.depends_on(v))
        self.assertFalse(v.depends_on(c))

        # Deep checking
        self.assertFalse(c.depends_on(v, deep=True))
        self.assertTrue(v.depends_on(c, deep=True))

        # Deep checking can handle improper names
        # Note: The order of execution is not guaranteed, so that sometimes
        # the test will find 'c' before dealing with the improper ref. As a
        # result, the False scenario is required for consistent coverage.
        # https://github.com/myokit/myokit/issues/913
        p = myokit.Plus(c, myokit.Name('x'))
        self.assertTrue(p.depends_on(c, True))
        self.assertTrue(p.depends_on(myokit.Name('x'), True))
        self.assertFalse(p.depends_on(v, True))

        # Deep checking can handle partial derivs and inits
        q = myokit.PartialDerivative(myokit.Name(v.var()), c)
        self.assertFalse(q.depends_on(c, True))
        self.assertFalse(q.depends_on(c, False))
        self.assertFalse(q.depends_on(myokit.Name(v.var()), True))
        self.assertFalse(q.depends_on(myokit.Name(v.var()), False))
        q = myokit.InitialValue(myokit.Name(v.var()))
        self.assertFalse(q.depends_on(c, True))
        self.assertFalse(q.depends_on(c, False))
        self.assertFalse(q.depends_on(myokit.Name(v.var()), True))
        self.assertFalse(q.depends_on(myokit.Name(v.var()), False))

        # Deep checking can handle partial derivs and inits & improper names
        # See note above about issue 913
        q = myokit.Plus(p, myokit.PartialDerivative(v, myokit.Name('x')))
        self.assertTrue(q.depends_on(c, True))
        self.assertTrue(q.depends_on(myokit.Name('x'), True))
        q = myokit.Plus(p, myokit.InitialValue(myokit.Name('x')))
        self.assertTrue(q.depends_on(c, True))
        self.assertTrue(q.depends_on(myokit.Name('x'), True))
        self.assertFalse(q.depends_on(v, True))

        # Test with complex web of dependencies
        m.get('ina.E').set_rhs('a + b + c + k1 + k2 + inf')
        m.get('ina.E2').set_rhs('b + k1 + k2 + inf + tau + E3 + E')
        e = m.get('ina.E')
        a = m.get('ina.a').lhs()
        self.assertFalse(e.lhs().depends_on(a, False))
        self.assertTrue(e.lhs().depends_on(a, True))
        self.assertTrue(e.rhs().depends_on(a, False))
        self.assertTrue(e.rhs().depends_on(a, True))

        e = m.get('ina.E2')
        self.assertFalse(e.lhs().depends_on(a, False))
        self.assertTrue(e.lhs().depends_on(a, True))
        self.assertFalse(e.rhs().depends_on(a, False))
        self.assertTrue(e.rhs().depends_on(a, True))

    def test_depends_on_state(self):
        # Tests Expression.depends_on_state()

        # Shallow checking
        m = pd_model.clone()
        c = m.get('membrane.C').lhs()
        k = m.get('ina.k1').lhs()
        t = m.get('ina.tau').lhs()
        self.assertFalse(c.depends_on_state())
        self.assertFalse(k.depends_on_state())
        self.assertFalse(t.depends_on_state())
        self.assertTrue(k.depends_on_state(deep=True))
        self.assertTrue(t.depends_on_state(deep=True))

        v = m.get('membrane.V')
        self.assertTrue(myokit.Name(v).depends_on_state())
        self.assertTrue(myokit.Name(v).depends_on_state(deep=True))
        self.assertFalse(v.lhs().depends_on_state())
        self.assertTrue(v.rhs())
        self.assertTrue(v.lhs().depends_on_state(deep=True))

        # Can handle improper names
        p = myokit.Plus(c, myokit.Name('x'))
        self.assertFalse(p.depends_on_state(deep=False))
        self.assertFalse(p.depends_on_state(deep=True))

        # Can handle partial derivs and inits (always false)
        v = v.lhs()
        q = myokit.PartialDerivative(v, c)
        self.assertFalse(q.depends_on_state(False))
        self.assertFalse(q.depends_on_state(True))
        q = myokit.Plus(c, myokit.PartialDerivative(v, c))
        self.assertFalse(q.depends_on_state(False))
        self.assertFalse(q.depends_on_state(True))
        q = myokit.InitialValue(myokit.Name(v.var()))
        self.assertFalse(q.depends_on_state(False))
        self.assertFalse(q.depends_on_state(True))
        q = myokit.Plus(c, myokit.InitialValue(myokit.Name(v.var())))
        self.assertFalse(q.depends_on_state(False))
        self.assertFalse(q.depends_on_state(True))

    def test_diff(self):
        # Tests :meth:`Expression.diff()`

        # Test basic functionality
        m = pd_model.clone()
        m.check_units(myokit.UNIT_STRICT)

        # Direct dependence on a constant
        i = m.get('ina.I1')
        E = m.get('ina.E')
        d = i.rhs().diff(E.lhs())
        self.assertEqual(d.code(), '0.6 * ina.g * ina.m^3 * -1')

        # Dependence on a constant via another constant
        E3 = m.get('ina.E3')
        d = i.rhs().diff(E3.lhs())
        self.assertEqual(
            d.code(), '0.6 * ina.g * ina.m^3 * -diff(ina.E, ina.E3)')

        # Correct unit gets set for None
        p = E3.rhs().diff(E.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.units.dimensionless)
        E3.set_unit(None)
        E3.set_rhs('4')
        p = E3.rhs().diff(E.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.mV)
        E.set_unit(None)
        E.set_rhs('1 + E3')
        p = E3.rhs().diff(E.lhs())
        self.assertTrue(p.is_number(0))
        self.assertIsNone(p.unit())
        E3.set_unit('mV')
        E3.set_rhs('4 [mV]')
        p = E3.rhs().diff(E.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.units.mV)

        # Except if there are unit errors
        E3.set_unit('mV')
        E3.set_rhs('4 [mV] + 2 [pA]')
        E.set_unit('mV')
        E.set_rhs('1 [mV] + E3')
        p = E3.rhs().diff(E.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.mV)

        # Only Names or intial values are allowed
        self.assertRaisesRegex(
            ValueError, 'only be taken with respect to a myokit.Name or',
            i.rhs().diff, myokit.Number(3))
        V = m.get('membrane.V')
        self.assertRaisesRegex(
            ValueError, 'only be taken with respect to a myokit.Name or',
            i.rhs().diff, V.lhs())

        # Derivative w.r.t. initial condition is zero when states are
        # independent, otherwise equates to dependence on any state
        V0 = myokit.InitialValue(myokit.Name(V))
        dV = V.lhs()
        self.assertEqual(
            dV.diff(V0, independent_states=True),
            myokit.Number(0, 1 / myokit.units.ms))
        self.assertEqual(
            dV.diff(V0, independent_states=False),
            myokit.PartialDerivative(dV, V0))
        self.assertEqual(
            i.lhs().diff(V0, independent_states=True),
            myokit.Number(0, myokit.units.pA / myokit.units.mV))
        self.assertEqual(
            i.lhs().diff(V0, independent_states=False),
            myokit.PartialDerivative(i.lhs(), V0))

    def test_equal(self):
        # Test equality checking on general equations

        m1 = myokit.load_model('example')
        m2 = m1.clone()
        for v in m1.variables(deep=True):
            e1 = v.rhs()
            e2 = m2.get(v.qname()).rhs()
            if e1.is_literal():
                self.assertEqual(e1, e1)
            else:
                self.assertNotEqual(e1, e2)

    def test_eval(self):
        # Test :meth:`Expression.eval()`.

        # Test basic use
        e = myokit.parse_expression('1 + 1 + 1')
        self.assertEqual(e.eval(), 3)

        # Test errors
        e = myokit.parse_expression('1 / 0')
        self.assertRaises(myokit.NumericalError, e.eval)

        # Test errors-in-errors
        e = myokit.parse_expression('16^1000 / 0')
        self.assertRaisesRegex(myokit.NumericalError, 'another error', e.eval)

        # Test errors with variables
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(0)
        y.set_rhs('5 / 2')
        z.set_rhs('(x + y) / 0')
        self.assertRaisesRegex(
            myokit.NumericalError, 'c.x = 0', z.rhs().eval)
        self.assertRaisesRegex(
            myokit.NumericalError, 'c.y = 5 / 2', z.rhs().eval)

        # Test error in error with variables
        y.set_rhs('16^1000')
        self.assertRaisesRegex(
            myokit.NumericalError, 'another error', z.eval)

        # Test substitution
        y.set_rhs('5')
        z.set_rhs('x / y')
        z.rhs().eval(subst={x.lhs(): 0})
        z.rhs().eval(subst={x.lhs(): myokit.Number(1)})
        self.assertEqual(
            z.rhs().eval(
                subst={x.lhs(): myokit.parse_expression('5 * 5 * 5')}),
            25)

        # Test errors in substitution dict format
        self.assertRaisesRegex(ValueError, 'dict or None', z.rhs().eval, 2)
        self.assertRaisesRegex(ValueError, 'All keys', z.rhs().eval, {5: 1})
        self.assertRaisesRegex(
            ValueError, 'All values', z.rhs().eval, {x.lhs(): 'hello'})

        # Test if substituted Name is treated as number in error formatting
        y.set_rhs('x')
        z.set_rhs('(x + y) / 0')
        self.assertRaisesRegex(
            myokit.NumericalError, 'c.y = 3', z.rhs().eval, {y.lhs(): 3})

        # Error handling --> Correct bit should be highlighted
        z.set_rhs('(1 + 2 * (3 + sin(1 / (2 * x + (0 / 0)))))')
        with self.assertRaises(myokit.NumericalError) as e:
            z.eval()
        m = str(e.exception).splitlines()
        self.assertEqual(len(m), 7)
        self.assertEqual(m[2], '  1 + 2 * (3 + sin(1 / (2 * c.x + 0 / 0)))')
        self.assertEqual(m[3], '                                  ~~~~~')

        # Error handling --> Error when descending down a tree should be found
        y.set_rhs('3 * z')
        with self.assertRaises(myokit.NumericalError) as e:
            y.eval()
        m = str(e.exception).splitlines()
        self.assertEqual(len(m), 10)
        self.assertEqual(m[1], 'Encountered when evaluating')
        self.assertEqual(m[2], '  3 * c.z')
        self.assertEqual(m[3], 'Error located at:')
        self.assertEqual(m[4], '  c.z')
        self.assertEqual(
            m[5], 'c.z = 1 + 2 * (3 + sin(1 / (2 * c.x + 0 / 0)))')
        self.assertEqual(m[6], '                                      ~~~~~')
        self.assertEqual(m[7], 'With the following operands:')
        self.assertEqual(m[8], '  (1) 0.0')
        self.assertEqual(m[9], '  (2) 0.0')

        # Debugging name: unlinked!
        x = myokit.Name('x')
        self.assertEqual(
            x._eval_unit(myokit.UNIT_TOLERANT), None)
        self.assertEqual(
            x._eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_eval_unit_error(self):
        # Test error handling for eval_unit.

        # Incompatible units
        x = myokit.parse_expression('1 + 2 * (3 + 4 * (5 [mV] + 6 [A]))')
        with self.assertRaises(myokit.IncompatibleUnitError) as e:
            x.eval_unit()
        m = str(e.exception).splitlines()
        self.assertEqual(len(m), 4)
        self.assertEqual(m[2], '  1 + 2 * (3 + 4 * (5 [mV] + 6 [A]))')
        self.assertEqual(m[3], '                    ~~~~~~~~~~~~~~')

    def test_int_conversion(self):
        # Test conversion of expressions to int.

        x = myokit.parse_expression('1 + 2 + 3')
        self.assertEqual(int(x), 6)
        x = myokit.parse_expression('1 + 3.9')
        self.assertEqual(int(x), 4)

    def test_float_conversion(self):
        # Test conversion of expressions to float.

        x = myokit.parse_expression('1 + 2 + 3')
        self.assertEqual(int(x), 6)
        x = myokit.parse_expression('1 + 3.9')
        self.assertEqual(float(x), 4.9)

    def test_is_conditional(self):
        # Test :meth:`Expression.is_conditional().`.

        pe = myokit.parse_expression
        self.assertFalse(pe('1 + 2 + 3').is_conditional())
        self.assertTrue(pe('if(1, 0, 2)').is_conditional())
        self.assertTrue(pe('1 + if(1, 0, 2)').is_conditional())

    def test_pickling_error(self):
        # Tests pickling of expressions raises an exception

        # Test that the right exception is raised
        m = myokit.load_model('example')
        e = m.get('ina.INa').rhs()
        self.assertRaises(NotImplementedError, pickle.dumps, e)

        # Test that the trick in the exception actually works
        s = e.code()
        f = myokit.parse_expression(s, context=m)
        self.assertEqual(e, f)

    def test_pyfunc(self):
        # Test the pyfunc() method.

        # Note: Extensive testing happens in pywriter / numpywriter tests!
        x = myokit.parse_expression('3 * sqrt(v)')
        f = x.pyfunc(use_numpy=False)
        self.assertTrue(callable(f))
        self.assertEqual(f(4), 6)
        self.assertRaises(TypeError, f, np.array([1, 2, 3]))

        f = x.pyfunc(use_numpy=True)
        self.assertTrue(callable(f))
        self.assertEqual(f(4), 6)
        self.assertEqual(list(f(np.array([1, 4, 9]))), [3, 6, 9])

    def test_pystr(self):
        # Test the pystr() method.
        # Note: Extensive testing happens in pywriter / numpywriter tests!

        x = myokit.parse_expression('3 * sqrt(v)')
        self.assertEqual(x.pystr(use_numpy=False), '3.0 * math.sqrt(v)')
        self.assertEqual(x.pystr(use_numpy=True), '3.0 * numpy.sqrt(v)')

    def test_sequence_interface(self):
        # Tests the Expression class's sequence interface

        x = myokit.parse_expression('1 + 2')
        self.assertEqual(len(x), 2)                 # __len__
        self.assertIn(myokit.Number(1), x)          # __contains__
        self.assertIn(myokit.Number(2), x)
        self.assertEqual(x[0], myokit.Number(1))    # __getitem__
        self.assertEqual(x[1], myokit.Number(2))

        y = [op for op in x]                        # __iter__
        self.assertEqual(len(y), 2)
        self.assertIn(myokit.Number(1), y)
        self.assertIn(myokit.Number(2), y)
        self.assertEqual(y[0], myokit.Number(1))
        self.assertEqual(y[1], myokit.Number(2))

    def test_string_conversion(self):
        # Tests __str__ and __repr__

        x = myokit.Plus(myokit.Number(1), myokit.Number(2))
        self.assertEqual(str(x), '1 + 2')
        self.assertEqual(repr(x), 'myokit.Expression[1 + 2]')

    def test_tree_str(self):
        # Test :meth:`Expression.tree_str()`.
        # More extensive testing of this method should happen in the individual
        # expression tests.

        x = myokit.parse_expression('1 + 2 * 3 / 4')
        self.assertEqual(x.tree_str(), '\n'.join([
            '+',
            '  1',
            '  /',
            '    *',
            '      2',
            '      3',
            '    4',
            '',
        ]))

    def test_validation(self):
        # Test :meth:`Expression.validate()`.

        e = myokit.parse_expression('5 + 2 * exp(3 / (1 + 2))')
        e.validate()
        self.assertIsNone(e.validate())

        # Test cycles in expression tree are found (not via variables!)
        p = myokit.Plus(myokit.Number(1), myokit.Number(1))
        # Have to hack this in, since, properly used, expressions are immutable
        p._operands = (myokit.Number(2), p)
        self.assertRaisesRegex(myokit.IntegrityError, 'yclical', p.validate)

        # Wrong type operands
        # Again, need to hack this in so creation doesn't fault!
        p._operands = (myokit.Number(1), 2)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'must be other Expression', p.validate)

    def test_walk(self):
        # Test :meth:`Expression.walk().

        e = myokit.parse_expression('1 / (2 + exp(3 + sqrt(4)))')
        w = list(e.walk())
        self.assertEqual(len(w), 9)
        self.assertEqual(type(w[0]), myokit.Divide)
        self.assertEqual(type(w[1]), myokit.Number)
        self.assertEqual(type(w[2]), myokit.Plus)
        self.assertEqual(type(w[3]), myokit.Number)
        self.assertEqual(type(w[4]), myokit.Exp)
        self.assertEqual(type(w[5]), myokit.Plus)
        self.assertEqual(type(w[6]), myokit.Number)
        self.assertEqual(type(w[7]), myokit.Sqrt)
        self.assertEqual(type(w[8]), myokit.Number)
        self.assertEqual(w[1].eval(), 1)
        self.assertEqual(w[3].eval(), 2)
        self.assertEqual(w[6].eval(), 3)
        self.assertEqual(w[8].eval(), 4)

        w = list(e.walk(allowed_types=[myokit.Sqrt, myokit.Exp]))
        self.assertEqual(len(w), 2)
        self.assertEqual(type(w[0]), myokit.Exp)
        self.assertEqual(type(w[1]), myokit.Sqrt)

        w = list(e.walk(allowed_types=myokit.Exp))
        self.assertEqual(len(w), 1)
        self.assertEqual(type(w[0]), myokit.Exp)


class NumberTest(unittest.TestCase):
    """ Tests myokit.Number. """

    def test_basic(self):
        # Test construction, other basics.

        # Test myokit.Number creation and representation
        x = myokit.Number(-4.0)
        self.assertEqual(str(x), '-4')
        self.assertEqual(x.value(), -4)
        self.assertIsNone(x.unit())
        x = myokit.Number(4.0)
        self.assertEqual(str(x), '4')
        y = myokit.Number(4)
        self.assertEqual(str(y), '4')
        self.assertEqual(x, y)
        self.assertFalse(x is y)
        x = myokit.Number(4.01)
        self.assertEqual(str(x), '4.01')
        x = myokit.Number(-4.01)
        self.assertEqual(str(x), '-4.01')
        x = myokit.Number('-4e9')
        self.assertEqual(str(x), '-4.00000000000000000e9')
        x = myokit.Number('4e+09')
        self.assertEqual(str(x), ' 4.00000000000000000e9')
        x = myokit.Number('-4e+00')
        self.assertEqual(str(x), '-4')
        x = myokit.Number('4e-05')
        self.assertEqual(str(x), '4e-5')
        x = myokit.Number('4e+15')
        self.assertEqual(float(x), 4e15)
        x = myokit.Number(4, myokit.Unit.parse_simple('pF'))
        self.assertEqual(str(x), '4 [pF]')
        x = myokit.Number(-3, myokit.Unit.parse_simple('pF'))
        self.assertEqual(str(x), '-3 [pF]')

        # Test unit conversion
        x = myokit.Number('2000', myokit.units.pF)
        y = x.convert('nF')
        self.assertEqual(y.eval(), 2)
        self.assertEqual(str(y), '2 [nF]')
        self.assertEqual(y.unit(), myokit.Unit.parse_simple('nF'))
        a = y.convert('uF')
        b = x.convert('uF')
        self.assertEqual(a, b)
        self.assertRaises(myokit.IncompatibleUnitError, x.convert, 'A')

        # Test properties
        x = myokit.Number(2)
        self.assertFalse(x.is_conditional())
        self.assertTrue(x.is_constant())
        self.assertTrue(x.is_literal())
        self.assertFalse(x.is_state_value())

        # Test construction
        # Second argument must be a unit, if given
        myokit.Number(3, 'kg')
        self.assertRaisesRegex(ValueError, 'Unit', myokit.Number, 3, 1)
        # Construction from quantity
        q = myokit.Quantity(3, 'kg')
        myokit.Number(q)
        self.assertEqual(q.unit(), myokit.parse_unit('kg'))
        self.assertRaisesRegex(ValueError, 'unit', myokit.Number, q, 'kg')

    def test_bracket(self):
        # Test Number.bracket().
        # Never needs a bracket
        x = myokit.Number(2)
        self.assertFalse(x.bracket())

        # Doesn't have an operand
        self.assertRaises(ValueError, x.bracket, myokit.Number(2))

    def test_clone(self):
        # Test Number.clone().

        x = myokit.Number(2)
        y = x.clone()
        self.assertIsNot(x, y)
        self.assertEqual(x, y)

        # With substitution
        z = myokit.Number(10)
        y = x.clone(subst={x: z})
        self.assertEqual(y, z)

        # Test that substitution changes references
        # Note: This should follow automatically from set_rhs() implementation
        # and fact that expressions are immutable.
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(2)
        y = c.add_variable('y')
        y.set_rhs('3 * x')
        self.assertIn(x.lhs(), y.rhs().references())
        self.assertIn(x, y.refs_to())
        self.assertIn(y, x.refs_by())
        y.set_rhs(y.rhs().clone(subst={x.lhs(): myokit.Number(4)}))
        self.assertNotIn(x.lhs(), y.rhs().references())
        self.assertNotIn(x, y.refs_to())
        self.assertNotIn(y, x.refs_by())

    def test_diff(self):

        # Derivative of a number w.r.t. anything is zero (but with the right
        # unit)
        m = pd_model
        C = m.get('membrane.C')
        E = m.get('ina.E')
        self.assertEqual(C.unit(), myokit.units.pF)
        self.assertEqual(E.unit(), myokit.units.mV)
        self.assertIsInstance(C.rhs(), myokit.Number)
        d = C.rhs().diff(E.lhs())
        self.assertTrue(d.is_number(0))
        self.assertEqual(d.unit(), myokit.units.pF / myokit.units.mV)

    def test_equal(self):
        # Test equality checking on numbers
        a = myokit.Number(1)
        b = myokit.Number(1)
        c = myokit.Number(2)
        self.assertEqual(a, b)
        self.assertEqual(b, a)
        self.assertNotEqual(a, c)
        self.assertNotEqual(c, a)
        self.assertNotEqual(b, c)
        self.assertNotEqual(c, b)

    def test_eval(self):
        # Test evaluation (with single precision).

        x = myokit.Number(2)
        self.assertEqual(type(x.eval()), float)
        self.assertEqual(
            type(x.eval(precision=myokit.SINGLE_PRECISION)), np.float32)

    def test_eval_unit(self):
        # Test Number eval_unit.

        # Test in tolerant mode
        x = myokit.Number(3)
        self.assertEqual(x.eval_unit(), None)
        y = myokit.Number(3, myokit.units.ampere)
        self.assertEqual(y.eval_unit(), myokit.units.ampere)

        # Test in strict mode
        self.assertEqual(
            x.eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(y.eval_unit(myokit.UNIT_STRICT), myokit.units.ampere)

    def test_is_name_number_derivative(self):
        # Test is_name(), is_number(), and is_derivative()

        x = myokit.Number(3, myokit.units.volt)
        self.assertFalse(x.is_name())
        self.assertFalse(x.is_derivative())
        v = myokit.Model().add_component('c').add_variable('x')
        self.assertFalse(x.is_name(v))
        self.assertFalse(x.is_derivative(v))

        self.assertTrue(x.is_number())
        self.assertFalse(x.is_number(12))
        self.assertFalse(x.is_number(0))
        self.assertTrue(x.is_number(3))

        x = myokit.Number(0)
        self.assertTrue(x.is_number())
        self.assertTrue(x.is_number(0))

    def test_tree_str(self):
        # Test Number.tree_str()

        # Test simple
        x = myokit.Number(1)
        self.assertEqual(x.tree_str(), '1\n')

        # Test with spaces
        e = myokit.Plus(x, myokit.Number(-2))
        self.assertEqual(e.tree_str(), '+\n  1\n  -2\n')


class NameTest(unittest.TestCase):
    """ Tests myokit.Name. """

    def test_basics(self):
        # Test Name basics

        model = myokit.Model()
        component = model.add_component('c')
        xvar = component.add_variable('x')
        xvar.set_rhs('15')
        yvar = component.add_variable('y')
        yvar.set_rhs('3 * x ')
        zvar = component.add_variable('z')
        zvar.set_rhs('2 + y + x')

        x = myokit.Name(xvar)
        y = myokit.Name(yvar)
        z = myokit.Name(zvar)

        self.assertEqual(x.code(), 'c.x')

        # Test rhs
        # Name of non-state: rhs() should be the associated variable's rhs
        self.assertEqual(x.rhs(), myokit.Number(15))
        # Name of state: rhs() should be the initial value (since this is the
        # value of the variable).
        xvar.promote(12)
        self.assertEqual(x.rhs(), myokit.Number(12))
        # Invalid variable:
        a = myokit.Name('test')
        self.assertIsNone(a.rhs())

        # Test validation
        x.validate()
        y.validate()
        z.validate()
        a = myokit.Name('test')
        self.assertRaises(myokit.IntegrityError, a.validate)

        # Test var()
        self.assertEqual(x.var(), xvar)
        self.assertEqual(y.var(), yvar)
        self.assertEqual(z.var(), zvar)

        # Test properties
        # State x
        self.assertFalse(x.is_conditional())
        self.assertFalse(x.is_constant())
        self.assertFalse(x.is_literal())
        self.assertTrue(x.is_state_value())

        # State-dependent variable y
        self.assertFalse(y.is_conditional())
        self.assertFalse(y.is_constant())
        self.assertFalse(y.is_literal())
        self.assertFalse(y.is_state_value())

        # Non-state x
        xvar.demote()
        self.assertFalse(x.is_conditional())
        self.assertTrue(x.is_constant())
        self.assertFalse(x.is_literal())    # A name is never a literal!
        self.assertFalse(x.is_state_value())

        # (Non-state)-dependent variable y
        self.assertFalse(y.is_conditional())
        self.assertTrue(y.is_constant())
        self.assertFalse(y.is_literal())
        self.assertFalse(y.is_state_value())

    def test_bracket(self):
        # Test Name.bracket().
        # Never needs a bracket
        x = myokit.Name('hi')
        self.assertFalse(x.bracket())

        # Doesn't have an operand
        self.assertRaises(ValueError, x.bracket, myokit.Number(2))

    def test_clone(self):
        # Test Name.clone().
        m = myokit.Model()
        c = m.add_component('c')
        vx = c.add_variable('x')
        vy = c.add_variable('y')
        vz = c.add_variable('z')
        vx.set_rhs(1)
        vy.set_rhs('2 * x')
        vz.set_rhs('2 * x + y')
        x = myokit.Name(vx)
        y = myokit.Name(vy)
        z = myokit.Name(vz)

        # Test clone
        a = x.clone()
        self.assertEqual(x, a)
        a = z.clone()
        self.assertEqual(z, a)

        # With substitution (handled in Name)
        a = x.clone(subst={x: y})
        self.assertEqual(y, a)
        a = x.clone()
        self.assertEqual(x, a)

        # With expansion (handled in Name)
        a = z.clone()
        self.assertEqual(z, a)
        a = z.clone(expand=True)
        self.assertTrue(a.is_literal())
        self.assertFalse(z.is_literal())
        self.assertEqual(z.eval(), a.eval())

        # With expansion but retention of selected variables (handled in Name)
        a = z.clone(expand=True, retain=[x])
        self.assertNotEqual(a, z)
        self.assertFalse(a.is_literal())
        self.assertEqual(z.eval(), a.eval())

        # Few options for how to specify x:
        b = z.clone(expand=True, retain=['c.x'])
        self.assertEqual(a, b)
        b = z.clone(expand=True, retain=[vx])
        self.assertEqual(a, b)

    def test_diff(self):
        # Tests Name.diff

        # Derivative of a state variable is one, zero, or an object
        m = pd_model.clone()
        V = myokit.Name(m.get('membrane.V'))
        self.assertEqual(V.diff(V, independent_states=True), myokit.Number(1))
        self.assertEqual(V.diff(V, independent_states=False), myokit.Number(1))
        C = myokit.Name(m.get('membrane.C'))
        self.assertEqual(
            V.diff(C, independent_states=True),
            myokit.Number(0, myokit.units.mV / myokit.units.pF))
        self.assertEqual(
            V.diff(C, independent_states=False),
            myokit.PartialDerivative(V, C))

        # Derivative of an non-state variable is one, zero, or an object
        tau = myokit.Name(m.get('ina.tau'))
        self.assertEqual(
            tau.diff(tau, independent_states=True), myokit.Number(1))
        self.assertEqual(
            tau.diff(tau, independent_states=False), myokit.Number(1))
        self.assertEqual(
            tau.diff(C, independent_states=True),    # No dep
            myokit.Number(0, myokit.units.ms / myokit.units.pF))
        self.assertEqual(
            tau.diff(C, independent_states=False),    # No dep
            myokit.PartialDerivative(tau, C))
        a = myokit.Name(m.get('ina.a'))
        self.assertEqual(
            tau.diff(a, independent_states=True),     # Dep
            myokit.PartialDerivative(tau, a))
        self.assertEqual(
            tau.diff(a, independent_states=False),    # Dep
            myokit.PartialDerivative(tau, a))

        # Derivative of a bound variable is one or zero
        t = myokit.Name(m.get('engine.time'))
        self.assertEqual(t.diff(t, independent_states=True), myokit.Number(1))
        self.assertEqual(t.diff(t, independent_states=False), myokit.Number(1))
        self.assertEqual(
            t.diff(C, independent_states=True),
            myokit.Number(0, myokit.units.ms / myokit.units.pF))
        self.assertEqual(
            t.diff(C, independent_states=False),
            myokit.Number(0, myokit.units.ms / myokit.units.pF))
        # Even if it has an interesting RHS
        t.var().set_rhs('4 * membrane.C')
        self.assertEqual(t.diff(t, independent_states=True), myokit.Number(1))
        self.assertEqual(t.diff(t, independent_states=False), myokit.Number(1))
        self.assertEqual(
            t.diff(C, independent_states=True),
            myokit.Number(0, myokit.units.ms / myokit.units.pF))
        self.assertEqual(
            t.diff(C, independent_states=False),
            myokit.Number(0, myokit.units.ms / myokit.units.pF))

        # Derivative of something depending only on a bound variable is one or
        # zero
        p = myokit.Name(m.get('bound.pace'))
        self.assertEqual(p.diff(p, independent_states=True), myokit.Number(1))
        self.assertEqual(p.diff(p, independent_states=False), myokit.Number(1))
        self.assertEqual(
            p.diff(C, independent_states=True),
            myokit.Number(0, 1 / myokit.units.pF))
        self.assertEqual(
            p.diff(C, independent_states=False),
            myokit.Number(0, 1 / myokit.units.pF))

        pd = myokit.Name(m.get('bound.pace_direct'))
        self.assertEqual(
            pd.diff(C, independent_states=True),
            myokit.Number(0, 1 / myokit.units.pF))
        self.assertEqual(
            pd.diff(C, independent_states=False),
            myokit.Number(0, 1 / myokit.units.pF))

        pi = myokit.Name(m.get('bound.pace_indirect'))
        self.assertEqual(
            pi.diff(C, independent_states=True),
            myokit.Number(0, 1 / myokit.units.pF))
        self.assertEqual(
            pi.diff(C, independent_states=False),
            myokit.Number(0, 1 / myokit.units.pF))

        td = myokit.Name(m.get('bound.time_direct'))
        self.assertEqual(
            td.diff(C, independent_states=True),
            myokit.Number(0, myokit.units.ms / myokit.units.pF))
        self.assertEqual(
            td.diff(C, independent_states=False),
            myokit.Number(0, myokit.units.ms / myokit.units.pF))

        ti = myokit.Name(m.get('bound.time_indirect'))
        self.assertEqual(
            ti.diff(C, independent_states=True),
            myokit.Number(0, myokit.units.ms / myokit.units.pF))
        self.assertEqual(
            ti.diff(C, independent_states=False),
            myokit.Number(0, myokit.units.ms / myokit.units.pF))

        # Test diff of "improper" name
        x = myokit.Name('x')
        y = myokit.Name('y')
        z = x.diff(y)
        self.assertIsInstance(z, myokit.PartialDerivative)
        self.assertEqual(z.code(), 'diff(str:x, str:y)')

    def test_equal(self):
        # Test equality checking on names

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(3)
        y = c.add_variable('y')
        y.set_rhs(2)
        y.set_unit(myokit.units.Newton)

        self.assertEqual(myokit.Name(x), myokit.Name(x))
        self.assertEqual(myokit.Name(y), myokit.Name(y))
        self.assertNotEqual(myokit.Name(x), myokit.Name(y))
        self.assertNotEqual(myokit.Name(y), myokit.Name(x))
        self.assertNotEqual(myokit.Name(x), myokit.Name(m.clone().get('c.x')))
        self.assertNotEqual(myokit.Name(x), myokit.Name('x'))
        self.assertNotEqual(myokit.Name(x), myokit.Name('c.x'))

        # Debug/unofficial options
        self.assertEqual(myokit.Name('a'), myokit.Name('a'))
        self.assertNotEqual(myokit.Name('a'), myokit.Name('A'))
        # The next ones _should_ be equal: since the components and models are
        # not what's supposed to go inside a name, it will convert to string
        # and compare the resulting representations. This is the same as what
        # would happen if __eq__ was called on an expression wrapping a Name.
        self.assertEqual(myokit.Name(c), myokit.Name(c))
        self.assertEqual(myokit.Name(m), myokit.Name(m.clone()))

    def test_eval_unit(self):
        # Test Name eval_unit.

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(3)
        y = c.add_variable('y')
        y.set_rhs(2)
        y.set_unit(myokit.units.Newton)

        # At this point, x and y both have a unitless rhs (despite y having a
        # variable unit)

        # Test in tolerant mode
        self.assertEqual(x.rhs().eval_unit(), None)
        self.assertEqual(y.rhs().eval_unit(), None)

        # Test in strict mode
        self.assertEqual(
            x.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(
            y.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

        # Now have x mention y in its rhs
        x.set_rhs('y')

        # Test in tolerant mode
        self.assertEqual(x.rhs().eval_unit(), myokit.units.Newton)
        self.assertEqual(y.rhs().eval_unit(), None)

        # Test in strict mode
        self.assertEqual(
            x.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.Newton)
        self.assertEqual(
            y.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_is_name_number_derivative(self):
        # Tests is_name(), is_number(), and is_derivative()

        v = myokit.Model().add_component('c').add_variable('v')
        x = myokit.Name(v)
        self.assertTrue(x.is_name())
        self.assertTrue(x.is_name(v))
        self.assertFalse(x.is_derivative())
        w = v.parent().add_variable('w')
        self.assertFalse(x.is_name(w))
        self.assertFalse(x.is_derivative(v))
        self.assertFalse(x.is_derivative(w))

        self.assertFalse(x.is_number())
        self.assertFalse(x.is_number(0))

    def test_rhs(self):
        # Test Name.rhs().

        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('3 + 2')

        x = myokit.Name(x)
        self.assertEqual(x.rhs().eval(), 5)

    def test_tree_str(self):
        # Test Name.tree_str()

        # Test simple
        x = myokit.Name('y')
        self.assertEqual(x.tree_str(), 'y\n')

        # Test with spaces
        e = myokit.Plus(x, x)
        self.assertEqual(e.tree_str(), '+\n  y\n  y\n')

    def test_values(self):
        # Test with values other than Variables

        # Special case: string
        x = myokit.Name('this is ok')
        self.assertEqual(x.code(), 'str:this is ok')

        # All other values (this allows e.g. CellML expressions to be created)
        x = myokit.Name(12.3)
        self.assertEqual(x.code(), '12.3')


class DerivativeTest(unittest.TestCase):
    """ Tests myokit.Derivative. """

    def test_basic(self):
        # Test creation.

        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(3)
        x.promote(0)
        y = c.add_variable('y')
        y.set_rhs(2)

        # Derivative of state
        d = myokit.Derivative(myokit.Name(x))
        d.validate()

        # Derivative of non-state: allowed during model building, but doesn't
        # validate
        d = myokit.Derivative(myokit.Name(y))
        self.assertRaisesRegex(
            myokit.IntegrityError, 'only be defined for state', d.validate)

        # Derivative of something other than a name: never allowed
        self.assertRaisesRegex(
            myokit.IntegrityError, 'on variables', myokit.Derivative,
            myokit.Number(1))

    def test_bracket(self):
        # Test Derivative.bracket()
        x = myokit.Derivative(myokit.Name('x'))
        self.assertFalse(x.bracket(myokit.Name('x')))
        self.assertRaises(ValueError, x.bracket, myokit.Number(1))

    def test_clone(self):
        # Test Derivative.clone().
        x = myokit.Derivative(myokit.Name('x'))
        y = x.clone()
        self.assertIsNot(y, x)
        self.assertEqual(y, x)

        z = myokit.Derivative(myokit.Name('z'))
        y = x.clone(subst={x: z})
        self.assertIsNot(y, x)
        self.assertIs(y, z)
        self.assertNotEqual(y, x)
        self.assertEqual(y, z)

        i = myokit.Name('i')
        j = myokit.Name('j')
        x = myokit.Derivative(i)
        y = x.clone(subst={i: j})
        self.assertIsNot(y, x)
        self.assertNotEqual(y, x)
        self.assertEqual(y, myokit.Derivative(j))

    def test_diff(self):
        # Tests Derivative.diff()

        # Derivative of a dot is zero or an object
        m = pd_model
        C = m.get('membrane.C').lhs()
        dm = m.get('ina.m').lhs()       # No dep on C
        dV = m.get('membrane.V').lhs()  # Dep on C
        self.assertEqual(
            dm.diff(C, independent_states=True),
            myokit.Number(0, 1 / myokit.units.pF / myokit.units.ms))
        self.assertEqual(
            dm.diff(C, independent_states=False),
            myokit.PartialDerivative(dm, C))
        self.assertEqual(
            dV.diff(C, independent_states=True),
            myokit.PartialDerivative(dV, C))
        self.assertEqual(
            dV.diff(C, independent_states=False),
            myokit.PartialDerivative(dV, C))

        # Diff of "improper" partial derivative
        x = myokit.Derivative(myokit.Name('x'))
        y = myokit.Name('y')
        z = x.diff(y)
        self.assertIsInstance(z, myokit.PartialDerivative)
        self.assertEqual(z.code(), 'diff(dot(str:x), str:y)')

        # Derivative of something depending only on a bound variable is one or
        # zero
        dpd = m.get('bound.dot_pace_direct').lhs()
        self.assertEqual(
            dpd.diff(C, independent_states=True),
            myokit.Number(0, 1 / myokit.units.pF))
        self.assertEqual(
            dpd.diff(C, independent_states=False),
            myokit.Number(0, 1 / myokit.units.pF))

        dpi = m.get('bound.dot_pace_indirect').lhs()
        self.assertEqual(
            dpi.diff(C, independent_states=True),
            myokit.Number(0, 1 / myokit.units.pF))
        self.assertEqual(
            dpi.diff(C, independent_states=False),
            myokit.Number(0, 1 / myokit.units.pF))

    def test_equal(self):
        # Test equality checking on derivatives

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(3)
        y = c.add_variable('y')
        y.set_rhs(2)
        y.set_unit(myokit.units.Newton)

        D, N = myokit.Derivative, myokit.Name
        self.assertEqual(D(N(x)), D(N(x)))
        self.assertEqual(D(N(y)), D(N(y)))
        self.assertNotEqual(D(N(x)), D(N(y)))
        self.assertNotEqual(D(N(y)), D(N(x)))
        self.assertNotEqual(D(N(x)), D(N(m.clone().get('c.x'))))
        self.assertNotEqual(D(N(x)), D(N('x')))
        self.assertNotEqual(D(N(x)), D(N('c.x')))

    def test_eval_unit(self):
        # Test Derivative.eval_unit()
        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('t')
        t.set_rhs('0')
        t.set_binding('time')
        x = c.add_variable('x')
        x.set_rhs('(10 - x) / 100')
        x.promote(0)

        # Get derivative object
        d = x.lhs()

        s = myokit.UNIT_STRICT

        # No units set anywhere: dimensionless
        self.assertEqual(d.eval_unit(), None)
        self.assertEqual(d.eval_unit(s), myokit.units.dimensionless)

        # Time has a unit
        t.set_unit(myokit.units.second)
        self.assertEqual(d.eval_unit(), 1 / myokit.units.second)
        self.assertEqual(d.eval_unit(s), 1 / myokit.units.second)

        # Both have a unit
        x.set_unit(myokit.units.volt)
        self.assertEqual(
            d.eval_unit(), myokit.units.volt / myokit.units.second)
        self.assertEqual(
            d.eval_unit(s), myokit.units.volt / myokit.units.second)

        # Time has no unit
        t.set_unit(None)
        self.assertEqual(d.eval_unit(), myokit.units.volt)
        self.assertEqual(d.eval_unit(s), myokit.units.volt)

    def test_is_name_number_derivative(self):
        # Tests is_name(), is_number(), and is_derivative()

        v = myokit.Model().add_component('c').add_variable('v')
        x = myokit.Derivative(myokit.Name(v))
        self.assertFalse(x.is_name())
        self.assertFalse(x.is_name(v))
        self.assertTrue(x.is_derivative())
        self.assertTrue(x.is_derivative(v))
        w = v.parent().add_variable('w')
        self.assertFalse(x.is_name(w))
        self.assertFalse(x.is_derivative(w))

        self.assertFalse(x.is_number())
        self.assertFalse(x.is_number(0))
        self.assertFalse(x.is_number(1))

    def test_rhs(self):
        # Test Derivative.rhs()
        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('(10 - x) / 100')
        x.promote(0)

        # Get derivative object
        d = x.lhs()
        self.assertEqual(d.rhs(), x.rhs())

        # Test with "improper" derivative
        x = myokit.Derivative(myokit.Name('x'))
        self.assertIsNone(x.rhs())

    def test_tree_str(self):
        # Test Derivative.tree_str()

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('(10 - x) / 100')
        x.promote(0)

        # Get derivative object
        d = x.lhs()

        # Test simple
        self.assertEqual(d.tree_str(), 'dot(c.x)\n')

        # Test with spaces
        e = myokit.Plus(d, d)
        self.assertEqual(e.tree_str(), '+\n  dot(c.x)\n  dot(c.x)\n')


class PartialDerivativeTest(unittest.TestCase):
    """ Tests myokit.PartialDerivative. """

    def test_creation(self):
        # Tests creating a partial derivative

        n = myokit.Name('v')
        d = myokit.Derivative(n)
        i = myokit.InitialValue(n)

        # First = name or derivative, Second = name or initial value
        p = myokit.PartialDerivative(n, n)
        self.assertIs(p.dependent_expression(), n)
        self.assertIs(p.independent_expression(), n)

        p = myokit.PartialDerivative(d, n)
        self.assertIs(p.dependent_expression(), d)
        self.assertIs(p.independent_expression(), n)

        p = myokit.PartialDerivative(n, i)
        self.assertIs(p.dependent_expression(), n)
        self.assertIs(p.independent_expression(), i)

        p = myokit.PartialDerivative(d, i)
        self.assertIs(p.dependent_expression(), d)
        self.assertIs(p.independent_expression(), i)

        # Others are not allowed
        self.assertRaisesRegex(
            myokit.IntegrityError, 'first argument to a partial',
            myokit.PartialDerivative, i, n)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'first argument to a partial',
            myokit.PartialDerivative, myokit.Number(3), n)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'first argument to a partial',
            myokit.PartialDerivative, myokit.PrefixPlus(n), n)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'second argument to a partial',
            myokit.PartialDerivative, n, d)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'second argument to a partial',
            myokit.PartialDerivative, n, myokit.Number(3))
        self.assertRaisesRegex(
            myokit.IntegrityError, 'second argument to a partial',
            myokit.PartialDerivative, n, myokit.PrefixPlus(n))

    def test_bracket(self):
        # Tests PartialDerivative.bracket()
        n = myokit.Name('v')
        p = myokit.PartialDerivative(n, n)
        self.assertFalse(p.bracket(n))
        m = myokit.Name('w')
        self.assertRaises(ValueError, p.bracket, m)

    def test_clone(self):
        # Tests PartialDerivative.clone()
        n = myokit.Name('v')
        m = myokit.Name('w')
        p = myokit.PartialDerivative(n, n)
        self.assertEqual(p, p.clone())
        self.assertFalse(p is p.clone())
        self.assertEqual(p.clone(subst={n: m}), myokit.PartialDerivative(m, m))
        self.assertEqual(p.clone(subst={p: m}), m)

    def test_code(self):
        # Tests PartialDerivative.code()
        n = myokit.Name('v')
        p = myokit.PartialDerivative(n, n)
        self.assertEqual(p.code(), 'diff(str:v, str:v)')

    def test_diff(self):
        # Tests PartialDerivative.diff()
        m = pd_model
        C = m.get('membrane.C').lhs()
        p = myokit.PartialDerivative(C, C)
        self.assertRaises(NotImplementedError, p.diff, C)

    def test_equal(self):
        # Tests PartialDerivative.__equal__()
        n = myokit.Name('v')
        m = myokit.Name('w')
        p = myokit.PartialDerivative(n, n)
        q = myokit.PartialDerivative(n, n)
        r = myokit.PartialDerivative(n, m)
        self.assertEqual(p, q)
        self.assertFalse(p is q)
        self.assertNotEqual(p, r)
        self.assertNotEqual(p, n)

    def test_eval_unit(self):
        # Tests PartialDerivative.eval_unit()
        m = pd_model.clone()
        V = myokit.Name(m.get('membrane.V'))
        C = myokit.Name(m.get('membrane.C'))
        p = myokit.PartialDerivative(V, C)
        self.assertEqual(p.eval_unit(), myokit.units.mV / myokit.units.pF)
        m.get('membrane.V').set_unit(None)
        self.assertEqual(p.eval_unit(), 1 / myokit.units.pF)
        m.get('membrane.V').set_unit('mV')
        m.get('membrane.C').set_unit(None)
        self.assertEqual(p.eval_unit(), myokit.units.mV)
        m.get('membrane.V').set_unit(None)
        self.assertEqual(p.eval_unit(), None)

    def test_repr(self):
        # Tests PartialDerivative.__repr__()
        n = myokit.Name('v')
        p = myokit.PartialDerivative(n, n)
        self.assertEqual(
            repr(p), '<PartialDerivative(' + repr(n) + ', ' + repr(n) + ')>')

    def test_rhs(self):
        # Tests PartialDerivative.rhs()
        n = myokit.Name('v')
        p = myokit.PartialDerivative(n, n)
        self.assertIsNone(p.rhs())

    def test_tree_str(self):
        # Tests PartialDerivative.tree_str()
        n = myokit.Name('v')
        p = myokit.PartialDerivative(n, n)
        self.assertEqual(p.tree_str(), 'partial\n  v\n  v\n')
        q = myokit.PrefixPlus(p)
        self.assertEqual(q.tree_str(), '+\n  partial\n    v\n    v\n')

    def test_var(self):
        # Tests PartialDerivative.var()
        m = pd_model
        V = myokit.Name(m.get('membrane.V'))
        C = myokit.Name(m.get('membrane.C'))
        p = myokit.PartialDerivative(V, C)
        self.assertEqual(p.var(), V.var())


class InitialValueTest(unittest.TestCase):
    """ Tests myokit.InitialValue. """

    def test_creation(self):
        # Tests creating an initial value

        n = myokit.Name('v')
        d = myokit.Derivative(n)
        i = myokit.InitialValue(n)

        # Value must be a name
        self.assertRaisesRegex(
            myokit.IntegrityError, 'first argument to an initial',
            myokit.InitialValue, d)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'first argument to an initial',
            myokit.InitialValue, myokit.Number(3),)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'first argument to an initial',
            myokit.InitialValue, myokit.PrefixPlus(n))

    def test_bracket(self):
        # Tests InitialValue.bracket()
        n = myokit.Name('v')
        i = myokit.InitialValue(n)
        self.assertFalse(i.bracket(n))
        m = myokit.Name('w')
        self.assertRaises(ValueError, i.bracket, m)

    def test_clone(self):
        # Tests InitialValue.clone()
        n = myokit.Name('v')
        m = myokit.Name('w')
        i = myokit.InitialValue(n)
        self.assertEqual(i, i.clone())
        self.assertFalse(i is i.clone())
        self.assertEqual(i.clone(subst={n: m}), myokit.InitialValue(m))
        self.assertEqual(i.clone(subst={i: m}), m)

    def test_code(self):
        # Tests InitialValue.code()
        n = myokit.Name('v')
        i = myokit.InitialValue(n)
        self.assertEqual(i.code(), 'init(str:v)')

    def test_diff(self):
        # Tests InitialValue.diff()
        m = pd_model
        V = myokit.Name(m.get('membrane.V'))
        C = myokit.Name(m.get('membrane.C'))
        i = myokit.InitialValue(V)
        self.assertRaises(NotImplementedError, i.diff, C)

    def test_equal(self):
        # Tests InitialValue.__equal__()
        n = myokit.Name('v')
        m = myokit.Name('w')
        i = myokit.InitialValue(n)
        j = myokit.InitialValue(n)
        k = myokit.InitialValue(m)
        self.assertEqual(i, j)
        self.assertFalse(i is j)
        self.assertNotEqual(i, k)
        self.assertNotEqual(i, m)

    def test_eval_unit(self):
        # Tests InitialValue.eval_unit()

        m = pd_model.clone()
        V = myokit.Name(m.get('membrane.V'))
        i = myokit.InitialValue(V)
        self.assertEqual(i.eval_unit(), myokit.units.mV)

    def test_repr(self):
        # Tests InitialValue.__repr__()
        n = myokit.Name('v')
        i = myokit.InitialValue(n)
        self.assertEqual(repr(i), '<InitialValue(' + repr(n) + ')>')

    def test_rhs(self):
        # Tests InitialValue.rhs()
        n = myokit.Name('v')
        i = myokit.InitialValue(n)
        self.assertIsNone(i.rhs())

    def test_tree_str(self):
        # Tests InitialValue.tree_str()
        n = myokit.Name('v')
        i = myokit.InitialValue(n)
        self.assertEqual(i.tree_str(), 'init(v)\n')
        q = myokit.PrefixPlus(i)
        self.assertEqual(q.tree_str(), '+\n  init(v)\n')

    def test_var(self):
        # Tests InitialValue.var()
        m = pd_model
        V = myokit.Name(m.get('membrane.V'))
        i = myokit.InitialValue(V)
        self.assertEqual(i.var(), V.var())

    def test_validate(self):
        # Tests InitialValue validation

        # Must be a state
        m = pd_model
        V = myokit.Name(m.get('membrane.V'))
        C = myokit.Name(m.get('membrane.C'))
        i = myokit.InitialValue(V)
        i.validate()
        i = myokit.InitialValue(C)
        self.assertRaises(myokit.IntegrityError, i.validate)


class PrefixPlusTest(unittest.TestCase):
    """Tests myokit.PrefixPlus."""

    def test_clone(self):
        # Test PrefixPlus.clone().
        x = myokit.PrefixPlus(myokit.Number(3))
        y = x.clone()
        self.assertIsNot(y, x)
        self.assertEqual(y, x)

        z = myokit.PrefixPlus(myokit.Number(4))
        y = x.clone(subst={x: z})
        self.assertIsNot(y, x)
        self.assertIs(y, z)
        self.assertNotEqual(y, x)
        self.assertEqual(y, z)

        i = myokit.Number(1)
        j = myokit.Number(2)
        x = myokit.PrefixPlus(i)
        y = x.clone(subst={i: j})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, myokit.PrefixPlus(j))

    def test_bracket(self):
        # Test PrefixPlus.bracket().
        i = myokit.Number(1)
        x = myokit.PrefixPlus(i)
        self.assertFalse(x.bracket(i))
        i = myokit.Plus(myokit.Number(1), myokit.Number(2))
        x = myokit.PrefixPlus(i)
        self.assertTrue(x.bracket(i))
        self.assertRaises(ValueError, x.bracket, myokit.Number(1))

    def test_diff(self):
        # Tests PrefixPlus.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('+ina.I1')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g)')
        V.set_rhs('+4')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test PrefixPlus evaluation.
        x = myokit.PrefixPlus(myokit.Number(2))
        self.assertEqual(x.eval(), 2)

    def test_eval_unit(self):
        # Test PrefixPlus.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('+(3)')
        y = c.add_variable('y')
        y.set_rhs('+(2 [N])')

        # Test in tolerant mode
        self.assertEqual(x.rhs().eval_unit(), None)
        self.assertEqual(y.rhs().eval_unit(), myokit.units.Newton)

        # Test in strict mode
        self.assertEqual(
            x.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(
            y.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.Newton)

    def test_is_name_number_derivative(self):
        # Tests is_name(), is_number(), and is_derivative()

        x = myokit.PrefixPlus(myokit.Number(1))
        self.assertFalse(x.is_name())
        v = myokit.Model().add_component('c').add_variable('v')
        self.assertFalse(x.is_name(v))
        self.assertFalse(x.is_derivative())
        self.assertFalse(x.is_derivative(v))

        self.assertFalse(x.is_number())
        self.assertFalse(x.is_number(0))
        self.assertFalse(x.is_number(1))

    def test_tree_str(self):
        # Test PrefixPlus.tree_str()

        # Test simple
        x = myokit.PrefixPlus(myokit.Number(1))
        self.assertEqual(x.tree_str(), '+\n  1\n')

        # Test with spaces
        y = myokit.Plus(
            myokit.PrefixPlus(myokit.Number(-1)),
            myokit.PrefixPlus(myokit.Number(2)))
        self.assertEqual(y.tree_str(), '+\n  +\n    -1\n  +\n    2\n')


class PrefixMinusTest(unittest.TestCase):
    """Tests myokit.PrefixMinus."""

    def test_clone(self):
        # Test PrefixMinus.clone().
        x = myokit.PrefixMinus(myokit.Number(3))
        y = x.clone()
        self.assertIsNot(y, x)
        self.assertEqual(y, x)

        z = myokit.PrefixMinus(myokit.Number(4))
        y = x.clone(subst={x: z})
        self.assertIsNot(y, x)
        self.assertIs(y, z)
        self.assertNotEqual(y, x)
        self.assertEqual(y, z)

        i = myokit.Number(1)
        j = myokit.Number(2)
        x = myokit.PrefixMinus(i)
        y = x.clone(subst={i: j})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, myokit.PrefixMinus(j))

    def test_bracket(self):
        # Test PrefixMinus.bracket().

        i = myokit.Number(1)
        x = myokit.PrefixMinus(i)
        self.assertFalse(x.bracket(i))
        i = myokit.Plus(myokit.Number(1), myokit.Number(2))
        x = myokit.PrefixMinus(i)
        self.assertTrue(x.bracket(i))
        self.assertRaises(ValueError, x.bracket, myokit.Number(1))

    def test_diff(self):
        # Tests PrefixMinus.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('-ina.I1')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), '-diff(ina.I1, ina.g)')
        V.set_rhs('-4')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test PrefixMinus evaluation.

        x = myokit.PrefixMinus(myokit.Number(2))
        self.assertEqual(x.eval(), -2)

    def test_eval_unit(self):
        # Test PrefixMinus.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('-(3)')
        y = c.add_variable('y')
        y.set_rhs('-(2 [N])')

        # Test in tolerant mode
        self.assertEqual(x.rhs().eval_unit(), None)
        self.assertEqual(y.rhs().eval_unit(), myokit.units.Newton)

        # Test in strict mode
        self.assertEqual(
            x.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(
            y.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.Newton)

    def test_is_name_number_derivative(self):
        # Tests is_name(), is_number(), and is_derivative()

        x = myokit.PrefixMinus(myokit.Number(1))
        self.assertFalse(x.is_name())
        v = myokit.Model().add_component('c').add_variable('v')
        self.assertFalse(x.is_name(v))
        self.assertFalse(x.is_derivative())
        self.assertFalse(x.is_derivative(v))

        self.assertFalse(x.is_number())
        self.assertFalse(x.is_number(0))
        self.assertFalse(x.is_number(1))

    def test_tree_str(self):
        # Test PrefixMinus.tree_str()
        # Test simple
        x = myokit.PrefixMinus(myokit.Number(1))
        self.assertEqual(x.tree_str(), '-\n  1\n')

        # Test with spaces
        y = myokit.Plus(
            myokit.PrefixMinus(myokit.Number(1)),
            myokit.PrefixMinus(myokit.Number(-2)))
        self.assertEqual(y.tree_str(), '+\n  -\n    1\n  -\n    -2\n')


class PlusTest(unittest.TestCase):
    """Tests myokit.Plus."""

    def test_clone(self):
        # Test Plus.clone().
        i = myokit.Number(3)
        j = myokit.Number(4)
        x = myokit.Plus(i, j)
        y = x.clone()
        self.assertIsNot(y, x)
        self.assertEqual(y, x)

        z = myokit.Plus(j, i)
        y = x.clone(subst={x: z})
        self.assertIsNot(y, x)
        self.assertIs(y, z)
        self.assertNotEqual(y, x)
        self.assertEqual(y, z)

        y = x.clone(subst={i: j})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, myokit.Plus(j, j))
        y = x.clone(subst={j: i})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, myokit.Plus(i, i))

    def test_bracket(self):
        # Test Plus.bracket().
        i = myokit.Number(1)
        j = myokit.parse_expression('1 + 2')
        x = myokit.Plus(i, j)
        self.assertFalse(x.bracket(i))
        self.assertTrue(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

    def test_diff(self):
        # Tests Plus.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('2 + ina.I1')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g)')
        V.set_rhs('ina.I1 + 2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g)')
        V.set_rhs('ina.I1 + ina.I2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'diff(ina.I1, ina.g) + diff(ina.I2, ina.g)')
        V.set_rhs('1 [mV/ms] + 4 [mV/ms]')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.parse_unit('mV/ms/nS'))

    def test_eval(self):
        # Test Plus evaluation.

        x = myokit.Plus(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.eval(), 3)
        x = myokit.Plus(myokit.Number(1), myokit.PrefixMinus(myokit.Number(2)))
        self.assertEqual(x.eval(), -1)

    def test_eval_unit(self):
        # Test Plus.eval_unit().
        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(1)
        y.set_rhs(1)
        z.set_rhs(myokit.Plus(x.lhs(), y.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.rhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(myokit.units.volt)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        x.set_unit(None)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.rhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

        # Tokens are used in IncompatibleUnitError messages
        m = myokit.parse_model('\n'.join([
            '[[model]]',
            '[a]',
            't = 1 [ms] + 1 [mV]',
            '    in [ms]',
            '    bind time',
        ]))
        try:
            m.check_units(myokit.UNIT_STRICT)
        except myokit.IncompatibleUnitError as e:
            self.assertIn('on line 3', str(e))
            token = e.token()
            self.assertIsNotNone(token)
            self.assertEqual(token[2], 3)
            self.assertEqual(token[3], 11)

    def test_is_name_number_derivative(self):
        # Tests is_name(), is_number(), and is_derivative()

        x = myokit.Plus(myokit.Number(1), myokit.Number(0))
        self.assertFalse(x.is_name())
        v = myokit.Model().add_component('c').add_variable('v')
        self.assertFalse(x.is_name(v))
        self.assertFalse(x.is_derivative())
        self.assertFalse(x.is_derivative(v))

        self.assertFalse(x.is_number())
        self.assertFalse(x.is_number(0))
        self.assertFalse(x.is_number(1))

    def test_tree_str(self):
        # Test Plus.tree_str().
        # Test simple
        x = myokit.Plus(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '+\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  +\n    1\n    2\n')
        x = myokit.parse_expression('1 + (2 + 3)')
        self.assertEqual(x.tree_str(), '+\n  1\n  +\n    2\n    3\n')


class MinusTest(unittest.TestCase):
    """Tests myokit.Minus."""

    def test_diff(self):
        # Tests Minus.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('2 - ina.I1')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), '-diff(ina.I1, ina.g)')
        V.set_rhs('ina.I1 - 2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g)')
        V.set_rhs('ina.I1 - ina.I2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'diff(ina.I1, ina.g) - diff(ina.I2, ina.g)')
        V.set_rhs('1 [mV/ms] - 4 [mV/ms]')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.parse_unit('mV/ms/nS'))

    def test_eval(self):
        # Test Minus evaluation.

        x = myokit.Minus(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.eval(), -1)

    def test_eval_unit(self):
        # Test Minus.eval_unit().

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(1)
        y.set_rhs(1)
        z.set_rhs(myokit.Minus(x.lhs(), y.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.rhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(myokit.units.volt)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        x.set_unit(None)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.rhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_is_name_number_derivative(self):
        # Tests is_name(), is_number(), and is_derivative()

        x = myokit.Minus(myokit.Number(2), myokit.Number(3))
        self.assertFalse(x.is_name())
        v = myokit.Model().add_component('c').add_variable('v')
        self.assertFalse(x.is_name(v))
        self.assertFalse(x.is_derivative())
        self.assertFalse(x.is_derivative(v))

        self.assertFalse(x.is_number())
        self.assertFalse(x.is_number(0))
        self.assertFalse(x.is_number(1))

    def test_tree_str(self):
        # Test Minus.tree_str().
        # Test simple
        x = myokit.Minus(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '-\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  -\n    1\n    2\n')
        x = myokit.parse_expression('1 - (2 - 3)')
        self.assertEqual(x.tree_str(), '-\n  1\n  -\n    2\n    3\n')


class MultiplyTest(unittest.TestCase):
    """Tests myokit.Multiply."""

    def test_diff(self):
        # Tests Multiply.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('2 * ina.I1')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), '2 * diff(ina.I1, ina.g)')
        V.set_rhs('ina.I1 * 2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g) * 2')
        V.set_rhs('ina.I1 * ina.I2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'diff(ina.I1, ina.g) * ina.I2 + '
            'ina.I1 * diff(ina.I2, ina.g)')
        V.set_rhs('1 [mV] * 4 [1/ms]')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.parse_unit('mV/ms/nS'))

    def test_eval(self):
        # Test Multiply evaluation.

        x = myokit.Multiply(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.eval(), 2)

    def test_eval_unit(self):
        # Test Multiply.eval_unit().

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(1)
        y.set_rhs(1)
        z.set_rhs(myokit.Multiply(x.lhs(), y.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.rhs().eval_unit(), myokit.units.volt * myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode (where None becomes dimensionless)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.volt * myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        # Test Multiply.tree_str().

        # Test simple
        x = myokit.Multiply(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '*\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  *\n    1\n    2\n')
        x = myokit.parse_expression('1 * (2 * 3)')
        self.assertEqual(x.tree_str(), '*\n  1\n  *\n    2\n    3\n')


class DivideTest(unittest.TestCase):
    """Tests myokit.Divide."""

    def test_diff(self):
        # Tests Divide.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('2 / ina.I1')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), '-2 * diff(ina.I1, ina.g) / ina.I1^2')
        V.set_rhs('ina.I1 / 2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g) / 2')
        V.set_rhs('ina.I1 / ina.I2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            '(diff(ina.I1, ina.g) * ina.I2'
            ' - ina.I1 * diff(ina.I2, ina.g))'
            ' / ina.I2^2')
        V.set_rhs('1 [mV] / 4 [ms]')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.parse_unit('mV/ms/nS'))

    def test_eval(self):
        # Test Divide evaluation.

        x = myokit.Divide(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.eval(), 0.5)

    def test_eval_unit(self):
        # Test Divide.eval_unit().

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(1)
        y.set_rhs(1)
        z.set_rhs(myokit.Divide(x.lhs(), y.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.rhs().eval_unit(), myokit.units.volt / myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), 1 / myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode (where None becomes dimensionless)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.volt / myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT),
            1 / myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        # Test Divide.tree_str().
        # Test simple
        x = myokit.Divide(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '/\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  /\n    1\n    2\n')
        x = myokit.parse_expression('1 / (2 / 3)')
        self.assertEqual(x.tree_str(), '/\n  1\n  /\n    2\n    3\n')


class QuotientTest(unittest.TestCase):
    """Tests myokit.Quotient."""

    def test_diff(self):
        # Tests Quotient.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('ina.I1 // ina.I2')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.parse_unit('1/nS'))

    def test_eval(self):
        # Test Quotient evaluation.

        x = myokit.Quotient(myokit.Number(7), myokit.Number(2))
        self.assertEqual(x.eval(), 3.0)

    def test_eval_unit(self):
        # Test Quotient.eval_unit().

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(1)
        y.set_rhs(1)
        z.set_rhs(myokit.Quotient(x.lhs(), y.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.rhs().eval_unit(), myokit.units.volt / myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), 1 / myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode (where None becomes dimensionless)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.volt / myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT),
            1 / myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        # Test Quotient.tree_str().
        # Test simple
        x = myokit.Quotient(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '//\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  //\n    1\n    2\n')
        x = myokit.parse_expression('1 // (2 // 3)')
        self.assertEqual(x.tree_str(), '//\n  1\n  //\n    2\n    3\n')


class RemainderTest(unittest.TestCase):
    """Tests myokit.Remainder."""

    def test_diff(self):
        # Tests Remainder.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('2 % ina.I1')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), '-diff(ina.I1, ina.g) * floor(2 / ina.I1)')
        V.set_rhs('ina.I1 % 2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g)')
        V.set_rhs('ina.I1 % ina.I2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'diff(ina.I1, ina.g) - '
            'diff(ina.I2, ina.g) * floor(ina.I1 / ina.I2)')
        V.set_rhs('1 [mV/ms] % 4 [1]')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.parse_unit('mV/ms/nS'))

    def test_eval(self):
        # Test Divide evaluation.

        x = myokit.Remainder(myokit.Number(7), myokit.Number(4))
        self.assertEqual(x.eval(), 3.0)

    def test_eval_unit(self):
        # Test Remainder.eval_unit().

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(1)
        y.set_rhs(1)
        z.set_rhs(myokit.Remainder(x.lhs(), y.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.rhs().eval_unit(), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode (where None becomes dimensionless)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.dimensionless)
        y.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        # Test Remainder.tree_str().

        # Test simple
        x = myokit.Remainder(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '%\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  %\n    1\n    2\n')
        x = myokit.parse_expression('1 % (2 % 3)')
        self.assertEqual(x.tree_str(), '%\n  1\n  %\n    2\n    3\n')


class PowerTest(unittest.TestCase):
    """Tests myokit.Power."""

    def test_bracket(self):
        # Test Power.bracket().
        i = myokit.Number(1)
        j = myokit.parse_expression('1 + 2')
        x = myokit.Power(i, j)
        self.assertFalse(x.bracket(i))
        self.assertTrue(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

    def test_clone(self):
        # Test Power.clone().
        i = myokit.Number(3)
        j = myokit.Number(4)
        x = myokit.Power(i, j)
        y = x.clone()
        self.assertIsNot(y, x)
        self.assertEqual(y, x)

        z = myokit.Power(j, i)
        y = x.clone(subst={x: z})
        self.assertIsNot(y, x)
        self.assertIs(y, z)
        self.assertNotEqual(y, x)
        self.assertEqual(y, z)

        y = x.clone(subst={i: j})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, myokit.Power(j, j))
        y = x.clone(subst={j: i})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, myokit.Power(i, i))

    def test_diff(self):
        # Tests Power.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('ina.I1^(2 * 3)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), '2 * 3 * ina.I1^(2 * 3 - 1) * diff(ina.I1, ina.g)')
        V.set_rhs('ina.I1^3')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), '3 * ina.I1^2 * diff(ina.I1, ina.g)')
        V.set_rhs('ina.I1^2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), '2 * ina.I1 * diff(ina.I1, ina.g)')
        V.set_rhs('ina.I1^1')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g)')
        V.set_rhs('2^ina.I1')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), '2^ina.I1 * diff(ina.I1, ina.g) / log(2)')
        V.set_rhs('ina.I1^ina.I2')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'ina.I1^ina.I2 * ('
            'log(ina.I1) * diff(ina.I2, ina.g) + '
            'ina.I2 / ina.I1 * diff(ina.I1, ina.g))')
        V.set_rhs('1 [mV]^1')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.units.mV / myokit.units.nS)

    def test_eval(self):
        # Test Power evaluation.

        x = myokit.Power(myokit.Number(2), myokit.Number(3))
        self.assertEqual(x.eval(), 8)
        x = myokit.Power(
            myokit.Number(2), myokit.PrefixMinus(myokit.Number(1)))
        self.assertEqual(x.eval(), 0.5)

    def test_eval_unit(self):
        # Test Power.eval_unit().

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(1)
        y.set_rhs(2)
        z.set_rhs(myokit.Power(x.lhs(), y.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt ** 2)
        y.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt ** 2)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.volt ** 2)
        y.set_unit(myokit.units.volt)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.rhs().eval_unit, myokit.UNIT_STRICT)
        x.set_unit(None)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.rhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(None)
        self.assertEqual(
            z.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_is_name_number_derivative(self):
        # Tests is_name(), is_number(), and is_derivative()

        x = myokit.Power(myokit.Number(2), myokit.Number(3))
        self.assertFalse(x.is_name())
        v = myokit.Model().add_component('c').add_variable('v')
        self.assertFalse(x.is_name(v))
        self.assertFalse(x.is_derivative())
        self.assertFalse(x.is_derivative(v))

        self.assertFalse(x.is_number())
        self.assertFalse(x.is_number(0))
        self.assertFalse(x.is_number(1))

    def test_tree_str(self):
        # Test Power.tree_str().

        # Test simple
        x = myokit.Power(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '^\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  ^\n    1\n    2\n')
        x = myokit.parse_expression('1^(2^3)')
        self.assertEqual(x.tree_str(), '^\n  1\n  ^\n    2\n    3\n')


class SqrtTest(unittest.TestCase):
    """Tests myokit.Sqrt."""

    def test_bracket(self):
        # Test Sqrt.bracket().
        i = myokit.Number(1)
        j = myokit.parse_expression('1 + 2')
        x = myokit.Sqrt(i)
        self.assertFalse(x.bracket(i))
        x = myokit.Sqrt(j)
        self.assertFalse(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

    def test_creation(self):
        # Test Sqrt creation.
        myokit.Sqrt(myokit.Number(1))
        self.assertRaisesRegex(
            myokit.IntegrityError, 'wrong number', myokit.Sqrt,
            myokit.Number(1), myokit.Number(2))

    def test_clone(self):
        # Test Sqrt.clone().
        i = myokit.Number(3)
        j = myokit.Number(10)
        x = myokit.Sqrt(i)
        y = x.clone()
        self.assertIsNot(y, x)
        self.assertEqual(y, x)

        z = myokit.Sqrt(j)
        y = x.clone(subst={x: z})
        self.assertIsNot(y, x)
        self.assertIs(y, z)
        self.assertNotEqual(y, x)
        self.assertEqual(y, z)

        y = x.clone(subst={i: j})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, z)

    def test_diff(self):
        # Tests Sqrt.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('sqrt(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'diff(ina.I1, ina.g) / (2 * sqrt(ina.I1))')
        V.set_rhs('sqrt(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test Sqrt evaluation.

        x = myokit.Sqrt(myokit.Number(9))
        self.assertEqual(x.eval(), 3)

    def test_eval_unit(self):
        # Test Sqrt.eval_unit().

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        z = c.add_variable('z')
        x.set_rhs(1)
        z.set_rhs(myokit.Sqrt(x.lhs()))

        # Test in tolerant mode
        #self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt**0.5)
        x.set_unit(myokit.units.volt ** 2)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.volt**0.5)
        x.set_unit(myokit.units.volt ** 2)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)

    def test_tree_str(self):
        # Test Sqrt.tree_str().
        # Test simple
        x = myokit.Sqrt(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'sqrt\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  sqrt\n    2\n')
        x = myokit.parse_expression('sqrt(1 + sqrt(2))')
        self.assertEqual(x.tree_str(), 'sqrt\n  +\n    1\n    sqrt\n      2\n')


class ExpTest(unittest.TestCase):
    """Tests myokit.Exp. """

    def test_bracket(self):
        # Test Exp.bracket().
        i = myokit.Number(1)
        j = myokit.parse_expression('1 + 2')
        x = myokit.Exp(i)
        self.assertFalse(x.bracket(i))
        x = myokit.Exp(j)
        self.assertFalse(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

    def test_clone(self):
        # Test Exp.clone().
        i = myokit.Number(3)
        j = myokit.Number(10)
        x = myokit.Exp(i)
        y = x.clone()
        self.assertIsNot(y, x)
        self.assertEqual(y, x)

        z = myokit.Exp(j)
        y = x.clone(subst={x: z})
        self.assertIsNot(y, x)
        self.assertIs(y, z)
        self.assertNotEqual(y, x)
        self.assertEqual(y, z)

        y = x.clone(subst={i: j})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, z)

    def test_creation(self):
        # Test Exp creation.
        myokit.Exp(myokit.Number(1))
        self.assertRaisesRegex(
            myokit.IntegrityError, 'wrong number', myokit.Exp,
            myokit.Number(1), myokit.Number(2))

    def test_diff(self):
        # Tests Exp.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('exp(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'exp(ina.I1) * diff(ina.I1, ina.g)')
        V.set_rhs('exp(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test Exp.eval().
        x = myokit.Exp(myokit.Number(9))
        self.assertEqual(x.eval(), np.exp(9))

    def test_eval_unit(self):
        # Test Exp.eval_unit().

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        z = c.add_variable('z')
        x.set_rhs(1)
        z.set_rhs(myokit.Exp(x.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless',
            z.rhs().eval_unit, s)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)

    def test_is_name_number_derivative(self):
        # Tests is_name(), is_number(), and is_derivative()

        x = myokit.Exp(myokit.Number(7))
        self.assertFalse(x.is_name())
        v = myokit.Model().add_component('c').add_variable('v')
        self.assertFalse(x.is_name(v))
        self.assertFalse(x.is_derivative())
        self.assertFalse(x.is_derivative(v))

        self.assertFalse(x.is_number())
        self.assertFalse(x.is_number(0))
        self.assertFalse(x.is_number(1))

    def test_tree_str(self):
        # Test Exp.tree_str().

        # Test simple
        x = myokit.Exp(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'exp\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  exp\n    2\n')
        x = myokit.parse_expression('exp(1 + exp(2))')
        self.assertEqual(x.tree_str(), 'exp\n  +\n    1\n    exp\n      2\n')


class LogTest(unittest.TestCase):
    """Tests myokit.Log."""

    def test_bracket(self):
        # Test Log.bracket().
        i = myokit.Number(1)
        j = myokit.parse_expression('1 + 2')

        # Test with one operand
        x = myokit.Log(i)
        self.assertFalse(x.bracket(i))
        x = myokit.Log(j)
        self.assertFalse(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

        # Test with two operands
        x = myokit.Log(i, j)
        self.assertFalse(x.bracket(i))
        self.assertFalse(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

    def test_clone(self):
        # Test Log.clone().

        # Test with one operand
        i = myokit.Number(3)
        j = myokit.Number(10)
        x = myokit.Log(i)
        y = x.clone()
        self.assertIsNot(y, x)
        self.assertEqual(y, x)

        z = myokit.Log(j)
        y = x.clone(subst={x: z})
        self.assertIsNot(y, x)
        self.assertIs(y, z)
        self.assertNotEqual(y, x)
        self.assertEqual(y, z)

        y = x.clone(subst={i: j})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, z)

        # Test with two operands
        x = myokit.Log(i, j)
        y = x.clone()
        self.assertIsNot(y, x)
        self.assertEqual(y, x)

        z = myokit.Log(j, i)
        y = x.clone(subst={x: z})
        self.assertIsNot(y, x)
        self.assertIs(y, z)
        self.assertNotEqual(y, x)
        self.assertEqual(y, z)

        y = x.clone(subst={i: j})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, myokit.Log(j, j))
        y = x.clone(subst={j: i})
        self.assertIsNot(x, y)
        self.assertNotEqual(x, y)
        self.assertEqual(y, myokit.Log(i, i))

    def test_creation(self):
        # Test Log creation.
        myokit.Log(myokit.Number(1))
        myokit.Log(myokit.Number(1), myokit.Number(2))
        self.assertRaisesRegex(
            myokit.IntegrityError, 'wrong number', myokit.Log,
            myokit.Number(1), myokit.Number(2), myokit.Number(3))

    def test_diff(self):
        # Tests Log.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')

        # One operand
        V.set_rhs('log(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g) / ina.I1')
        V.set_rhs('log(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

        # Two operands
        V.set_rhs('log(ina.I1, 3)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'diff(ina.I1, ina.g) / (ina.I1 * log(3))')
        V.set_rhs('log(2, ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            '-diff(ina.I1, ina.g) * log(2) / (ina.I1 * log(ina.I1)^2)')
        V.set_rhs('log(ina.I2, ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'diff(ina.I2, ina.g) / (ina.I2 * log(ina.I1)) - '
            'diff(ina.I1, ina.g) * log(ina.I2) / ('
            'ina.I1 * log(ina.I1)^2)')
        V.set_rhs('log(3, 2)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test Exp.eval().
        # One argument
        x = myokit.Log(myokit.Number(9))
        self.assertEqual(x.eval(), np.log(9))

        # Two arguments
        x = myokit.Log(myokit.Number(9), myokit.Number(5))
        self.assertEqual(x.eval(), np.log(9) / np.log(5))

    def test_eval_unit(self):
        # Test Log.eval_unit().

        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(1)
        y.set_rhs(2)

        # Single operand
        z.set_rhs(myokit.Log(x.lhs()))

        # Test in tolerant mode (single operand)
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode (single operand)
        s = myokit.UNIT_STRICT
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless',
            z.rhs().eval_unit, s)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)

        # Double operand
        z.set_rhs(myokit.Log(x.lhs(), y.lhs()))

        # Test in tolerant mode (double operand)
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        y.set_unit(myokit.units.volt)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode (double operand)
        s = myokit.UNIT_STRICT
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless',
            z.rhs().eval_unit, s)
        y.set_unit(myokit.units.volt)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless',
            z.rhs().eval_unit, s)
        x.set_unit(None)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless',
            z.rhs().eval_unit, s)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)

    def test_tree_str(self):
        # Test Log.tree_str().

        # Test simple
        x = myokit.Log(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'log\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  log\n    2\n')
        x = myokit.parse_expression('log(log(1, 2))')
        self.assertEqual(x.tree_str(), 'log\n  log\n    1\n    2\n')


class Log10Test(unittest.TestCase):
    """Tests myokit.Log10."""

    def test_diff(self):
        # Tests Log10.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')

        V.set_rhs('log10(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'diff(ina.I1, ina.g) / (ina.I1 * log(10))')
        V.set_rhs('log10(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test Log10.eval().
        x = myokit.Log10(myokit.Number(9))
        self.assertEqual(x.eval(), np.log10(9))

    def test_tree_str(self):
        # Test Log10.tree_str().
        x = myokit.Log10(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'log10\n  2\n')


class SinTest(unittest.TestCase):
    """Tests myokit.Sin."""

    def test_diff(self):
        # Tests Sin.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')

        V.set_rhs('sin(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'cos(ina.I1) * diff(ina.I1, ina.g)')
        V.set_rhs('sin(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test Sin.eval().
        x = myokit.Sin(myokit.Number(9))
        self.assertEqual(x.eval(), np.sin(9))

    def test_tree_str(self):
        # Test Sin.tree_str().
        x = myokit.Sin(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'sin\n  2\n')


class CosTest(unittest.TestCase):
    """Tests myokit.Cos."""

    def test_diff(self):
        # Tests Cos.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('cos(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), '-sin(ina.I1) * diff(ina.I1, ina.g)')
        V.set_rhs('cos(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test Cos.eval().
        x = myokit.Cos(myokit.Number(9))
        self.assertEqual(x.eval(), np.cos(9))

    def test_tree_str(self):
        # Test Cos.tree_str().
        x = myokit.Cos(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'cos\n  2\n')


class TanTest(unittest.TestCase):
    """ Tests myokit.Tan. """

    def test_diff(self):
        # Tests Tan.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('tan(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(p.code(), 'diff(ina.I1, ina.g) / cos(ina.I1)^2')
        V.set_rhs('tan(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test Tan.eval().
        x = myokit.Tan(myokit.Number(9))
        self.assertEqual(x.eval(), np.tan(9))

    def test_tree_str(self):
        # Test Tan.tree_str().
        x = myokit.Tan(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'tan\n  2\n')


class ASinTest(unittest.TestCase):
    """ Tests myokit.ASin. """

    def test_diff(self):
        # Tests ASin.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')
        V.set_rhs('asin(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'diff(ina.I1, ina.g) / sqrt(1 - ina.I1^2)')
        V.set_rhs('asin(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test ASin.eval().
        x = myokit.ASin(myokit.Number(0.9))
        self.assertEqual(x.eval(), np.arcsin(0.9))

    def test_tree_str(self):
        # Test ASin.tree_str().
        x = myokit.ASin(myokit.Number(0.5))
        self.assertEqual(x.tree_str(), 'asin\n  0.5\n')


class ACosTest(unittest.TestCase):
    """ Tests myokit.ACos. """

    def test_diff(self):
        # Tests ACos.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')

        V.set_rhs('acos(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), '-diff(ina.I1, ina.g) / sqrt(1 - ina.I1^2)')
        V.set_rhs('acos(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test ACos.eval().
        x = myokit.ACos(myokit.Number(0.9))
        self.assertEqual(x.eval(), np.arccos(0.9))

    def test_tree_str(self):
        # Test ACos.tree_str().
        x = myokit.ACos(myokit.Number(0.5))
        self.assertEqual(x.tree_str(), 'acos\n  0.5\n')


class ATanTest(unittest.TestCase):
    """ Tests myokit.ATan. """

    def test_diff(self):
        # Tests ATan.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')

        V.set_rhs('atan(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'diff(ina.I1, ina.g) / (1 + ina.I1^2)')
        V.set_rhs('atan(3)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test ATan.eval().
        x = myokit.ATan(myokit.Number(0.9))
        self.assertEqual(x.eval(), np.arctan(0.9))

    def test_tree_str(self):
        # Test ATan.tree_str().
        x = myokit.ATan(myokit.Number(0.5))
        self.assertEqual(x.tree_str(), 'atan\n  0.5\n')


class FloorTest(unittest.TestCase):
    """ Tests myokit.Floor. """

    def test_diff(self):
        # Tests Floor.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        C = m.get('membrane.C')

        V.set_rhs('floor(membrane.V)')
        p = V.rhs().diff(C.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.units.mV / myokit.units.pF)
        V.set_rhs('floor(3.2)')
        p = V.rhs().diff(C.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.pF)

    def test_eval(self):
        # Test Floor.eval().
        x = myokit.Floor(myokit.Number(0.9))
        self.assertEqual(x.eval(), 0)

    def test_eval_unit(self):
        # Test Floor.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('floor(3)')
        y = c.add_variable('y')
        y.set_rhs('floor(2 [N])')

        # Test in tolerant mode
        self.assertEqual(x.rhs().eval_unit(), None)
        self.assertEqual(y.rhs().eval_unit(), myokit.units.Newton)

        # Test in strict mode
        self.assertEqual(
            x.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(
            y.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.Newton)

    def test_tree_str(self):
        # Test Floor.tree_str().
        x = myokit.Floor(myokit.Number(0.5))
        self.assertEqual(x.tree_str(), 'floor\n  0.5\n')


class CeilTest(unittest.TestCase):
    """ Tests myokit.Ceil. """

    def test_diff(self):
        # Tests Ceil.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        C = m.get('membrane.C')

        V.set_rhs('ceil(membrane.V)')
        p = V.rhs().diff(C.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.units.mV / myokit.units.pF)
        V.set_rhs('ceil(3.2)')
        p = V.rhs().diff(C.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.pF)

    def test_eval(self):
        # Test Ceil.eval().
        x = myokit.Ceil(myokit.Number(0.9))
        self.assertEqual(x.eval(), 1)

    def test_eval_unit(self):
        # Test Ceil.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('ceil(3)')
        y = c.add_variable('y')
        y.set_rhs('ceil(2 [N])')

        # Test in tolerant mode
        self.assertEqual(x.rhs().eval_unit(), None)
        self.assertEqual(y.rhs().eval_unit(), myokit.units.Newton)

        # Test in strict mode
        self.assertEqual(
            x.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(
            y.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.Newton)

    def test_tree_str(self):
        # Test Ceil.tree_str().
        x = myokit.Ceil(myokit.Number(0.5))
        self.assertEqual(x.tree_str(), 'ceil\n  0.5\n')


class AbsTest(unittest.TestCase):
    """ Tests myokit.Abs. """

    def test_diff(self):
        # Tests Abs.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')

        # Operand with derivative, and units
        V.set_rhs('abs(ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'if(ina.I1 >= 0 [pA], diff(ina.I1, ina.g),'
            ' -diff(ina.I1, ina.g))')
        # Operand with derivative, no units
        i = m.get('ina.I1')
        i.set_unit(None)
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'if(ina.I1 >= 0, diff(ina.I1, ina.g), -diff(ina.I1, ina.g))')
        # Operand with derivative, and invalid units
        V.set_rhs('abs(ina.I1 + 2 [pF])')
        i.set_unit('pA')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'if(ina.I1 + 2 [pF] >= 0, diff(ina.I1, ina.g), '
            '-diff(ina.I1, ina.g))')
        # Operand without derivative or units
        V.set_rhs('abs(-13.2)')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), 1 / myokit.units.nS)

    def test_eval(self):
        # Test Abs.eval().
        x = myokit.Abs(myokit.Number(0.9))
        self.assertEqual(x.eval(), 0.9)
        x = myokit.Abs(myokit.Number(-0.9))
        self.assertEqual(x.eval(), 0.9)

    def test_eval_unit(self):
        # Test Abs.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('abs(3)')
        y = c.add_variable('y')
        y.set_rhs('abs(2 [N])')

        # Test in tolerant mode
        self.assertEqual(x.rhs().eval_unit(), None)
        self.assertEqual(y.rhs().eval_unit(), myokit.units.Newton)

        # Test in strict mode
        self.assertEqual(
            x.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(
            y.rhs().eval_unit(myokit.UNIT_STRICT), myokit.units.Newton)

    def test_tree_str(self):
        # Test Abs.tree_str().
        x = myokit.Abs(myokit.Number(0.5))
        self.assertEqual(x.tree_str(), 'abs\n  0.5\n')


class EqualTest(unittest.TestCase):
    """ Tests myokit.Equal. """

    def test_diff(self):
        # Tests Equal.diff()
        x = myokit.Equal(myokit.Number(1), myokit.Number(1))
        y = myokit.Model().add_component('c').add_variable('y')
        y.set_rhs('3')
        y = myokit.Name(y)
        self.assertRaises(NotImplementedError, x.diff, y)

    def test_eval(self):
        # Test Equal.eval().
        x = myokit.Equal(myokit.Number(1), myokit.Number(1))
        self.assertTrue(x.eval())
        x = myokit.Equal(myokit.Number(1), myokit.Number(2))
        self.assertFalse(x.eval())

    def test_eval_unit(self):
        # Test Equal.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('3')
        y = c.add_variable('y')
        y.set_rhs('3')
        z = c.add_variable('z')
        z.set_rhs('x == y')

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.ampere)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        y.set_unit(myokit.units.ampere)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        y.set_unit(myokit.units.volt)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'equal units', z.rhs().eval_unit)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'equal units', z.rhs().eval_unit, s)
        y.set_unit(myokit.units.ampere)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        y.set_unit(myokit.units.volt)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'equal units', z.rhs().eval_unit)
        x.set_unit(None)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'equal units', z.rhs().eval_unit, s)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)

    def test_tree_str(self):
        # Test Equal.tree_str().
        x = myokit.Equal(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '==\n  1\n  2\n')
        x = myokit.Plus(myokit.Number(3), x)
        self.assertEqual(x.tree_str(), '+\n  3\n  ==\n    1\n    2\n')


class NotEqualTest(unittest.TestCase):
    """ Tests myokit.NotEqual. """

    def test_eval(self):
        # Test NotEqual.eval().
        x = myokit.NotEqual(myokit.Number(1), myokit.Number(1))
        self.assertFalse(x.eval())
        x = myokit.NotEqual(myokit.Number(1), myokit.Number(2))
        self.assertTrue(x.eval())

    def test_tree_str(self):
        # Test NotEqual.tree_str().
        x = myokit.NotEqual(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '!=\n  1\n  2\n')
        x = myokit.Plus(myokit.Number(3), x)
        self.assertEqual(x.tree_str(), '+\n  3\n  !=\n    1\n    2\n')


class MoreTest(unittest.TestCase):
    """ Tests myokit.More. """
    def test_eval(self):
        # Test More.eval().
        x = myokit.More(myokit.Number(1), myokit.Number(1))
        self.assertFalse(x.eval())
        x = myokit.More(myokit.Number(3), myokit.Number(2))
        self.assertTrue(x.eval())

    def test_tree_str(self):
        # Test More.tree_str().
        x = myokit.More(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '>\n  1\n  2\n')
        x = myokit.Plus(myokit.Number(3), x)
        self.assertEqual(x.tree_str(), '+\n  3\n  >\n    1\n    2\n')


class LessTest(unittest.TestCase):
    """ Tests myokit.Less. """
    def test_eval(self):
        # Test Less.eval().
        x = myokit.Less(myokit.Number(1), myokit.Number(1))
        self.assertFalse(x.eval())
        x = myokit.Less(myokit.Number(1), myokit.Number(2))
        self.assertTrue(x.eval())

    def test_tree_str(self):
        # Test Less.tree_str().
        x = myokit.Less(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '<\n  1\n  2\n')
        x = myokit.Plus(myokit.Number(3), x)
        self.assertEqual(x.tree_str(), '+\n  3\n  <\n    1\n    2\n')


class MoreEqualTest(unittest.TestCase):
    """ Tests myokit.MoreEqual. """

    def test_eval(self):
        # Test MoreEqual.eval().
        x = myokit.MoreEqual(myokit.Number(1), myokit.Number(1))
        self.assertTrue(x.eval())
        x = myokit.MoreEqual(myokit.Number(3), myokit.Number(2))
        self.assertTrue(x.eval())
        x = myokit.MoreEqual(myokit.Number(1), myokit.Number(2))
        self.assertFalse(x.eval())

    def test_tree_str(self):
        # Test MoreEqual.tree_str().
        x = myokit.MoreEqual(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '>=\n  1\n  2\n')
        x = myokit.Plus(myokit.Number(3), x)
        self.assertEqual(x.tree_str(), '+\n  3\n  >=\n    1\n    2\n')


class LessEqualTest(unittest.TestCase):
    """ Tests myokit.LessEqual. """

    def test_eval(self):
        # Test LessEqual.eval().
        x = myokit.LessEqual(myokit.Number(1), myokit.Number(1))
        self.assertTrue(x.eval())
        x = myokit.LessEqual(myokit.Number(1), myokit.Number(2))
        self.assertTrue(x.eval())
        x = myokit.LessEqual(myokit.Number(2), myokit.Number(1))
        self.assertFalse(x.eval())

    def test_tree_str(self):
        # Test LessEqual.tree_str().
        x = myokit.LessEqual(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '<=\n  1\n  2\n')
        x = myokit.Plus(myokit.Number(3), x)
        self.assertEqual(x.tree_str(), '+\n  3\n  <=\n    1\n    2\n')


class AndTest(unittest.TestCase):
    """ Tests myokit.And. """

    def test_diff(self):
        # Tests And.diff()
        x1 = myokit.Equal(myokit.Number(1), myokit.Number(1))
        x2 = myokit.Equal(myokit.Number(2), myokit.Number(3))
        x = myokit.And(x1, x2)

        y = myokit.Model().add_component('c').add_variable('y')
        y.set_rhs('3')
        y = myokit.Name(y)
        self.assertRaises(NotImplementedError, x.diff, y)

    def test_eval(self):
        # Test And.eval().
        x = myokit.And(myokit.Number(1), myokit.Number(1))
        self.assertTrue(x.eval())
        x = myokit.And(myokit.Number(0), myokit.Number(2))
        self.assertFalse(x.eval())

    def test_eval_unit(self):
        # Test And.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('1')
        y = c.add_variable('y')
        y.set_rhs('1')
        z = c.add_variable('z')
        z.set_rhs('x and y')

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless', z.rhs().eval_unit)
        y.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless', z.rhs().eval_unit)
        x.set_unit(myokit.units.dimensionless)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless', z.rhs().eval_unit)
        y.set_unit(myokit.units.dimensionless)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionles', z.rhs().eval_unit, s)
        y.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionles', z.rhs().eval_unit, s)
        x.set_unit(myokit.units.dimensionless)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionles', z.rhs().eval_unit, s)
        y.set_unit(myokit.units.dimensionless)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)

    def test_tree_str(self):
        # Test And.tree_str().
        x = myokit.And(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), 'and\n  1\n  2\n')
        x = myokit.Plus(myokit.Number(3), x)
        self.assertEqual(x.tree_str(), '+\n  3\n  and\n    1\n    2\n')


class OrTest(unittest.TestCase):
    """ Tests myokit.Or. """

    def test_eval(self):
        # Test Or.eval().
        x = myokit.Or(myokit.Number(1), myokit.Number(1))
        self.assertTrue(x.eval())
        x = myokit.Or(myokit.Number(0), myokit.Number(2))
        self.assertTrue(x.eval())
        x = myokit.Or(myokit.Number(0), myokit.Number(0))
        self.assertFalse(x.eval())

    def test_eval_unit(self):
        # Test Or.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('1')
        y = c.add_variable('y')
        y.set_rhs('1')
        z = c.add_variable('z')
        z.set_rhs('x or y')

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless', z.rhs().eval_unit)
        y.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless', z.rhs().eval_unit)
        x.set_unit(myokit.units.dimensionless)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless', z.rhs().eval_unit)
        y.set_unit(myokit.units.dimensionless)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionles', z.rhs().eval_unit, s)
        y.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionles', z.rhs().eval_unit, s)
        x.set_unit(myokit.units.dimensionless)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionles', z.rhs().eval_unit, s)
        y.set_unit(myokit.units.dimensionless)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        y.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)

    def test_tree_str(self):
        # Test Or.tree_str().
        x = myokit.Or(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), 'or\n  1\n  2\n')
        x = myokit.Plus(myokit.Number(3), x)
        self.assertEqual(x.tree_str(), '+\n  3\n  or\n    1\n    2\n')


class NotTest(unittest.TestCase):
    """ Tests myokit.Not. """

    def test_code(self):
        # Test Not.code().
        x = myokit.Not(myokit.Number(1))
        self.assertEqual(x.code(), 'not 1')
        x = myokit.Not(myokit.Equal(myokit.Number(1), myokit.Number(1)))
        self.assertEqual(x.code(), 'not (1 == 1)')

    def test_diff(self):
        # Tests Not.diff()
        x = myokit.Not(myokit.Equal(myokit.Number(1), myokit.Number(1)))
        y = myokit.Model().add_component('c').add_variable('y')
        y.set_rhs('3')
        y = myokit.Name(y)
        self.assertRaises(NotImplementedError, x.diff, y)

    def test_eval(self):
        # Test Not.eval().
        x = myokit.Not(myokit.Number(1))
        self.assertFalse(x.eval())
        x = myokit.Not(myokit.Number(0))
        self.assertTrue(x.eval())

    def test_eval_unit(self):
        # Test Not.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('1')
        z = c.add_variable('z')
        z.set_rhs('not x')

        # Test in tolerant mode
        self.assertEqual(z.rhs().eval_unit(), None)
        x.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionless', z.rhs().eval_unit)
        x.set_unit(myokit.units.dimensionless)
        self.assertEqual(z.rhs().eval_unit(), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.ampere)
        self.assertRaisesRegex(
            myokit.IncompatibleUnitError, 'dimensionles', z.rhs().eval_unit, s)
        x.set_unit(myokit.units.dimensionless)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.rhs().eval_unit(s), myokit.units.dimensionless)

    def test_polish(self):
        # Test Not._polish().
        x = myokit.Not(myokit.Number(1))
        self.assertEqual(x._polish(), 'not 1')
        x = myokit.Not(myokit.Equal(myokit.Number(1), myokit.Number(1)))
        self.assertEqual(x._polish(), 'not == 1 1')


class IfTest(unittest.TestCase):
    """ Tests myokit.If. """

    def test_creation(self):
        # Test creation plus some accessor methods.

        cond = myokit.Equal(myokit.Number(1), myokit.Number(1))
        then = myokit.Number(10)
        else_ = myokit.Number(20)
        if_ = myokit.If(cond, then, else_)

        # Test condition()
        self.assertEqual(if_.condition(), cond)

        # Test is_conditional()
        self.assertTrue(if_.is_conditional())

    def test_diff(self):
        # Tests If.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')

        V.set_rhs('if(1 == 1, ina.I1, 7 [pA])')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'if(1 == 1, diff(ina.I1, ina.g), 0 [mV])')
        V.set_rhs('if(1 == 1, 7 [pA], ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(), 'if(1 == 1, 0 [mV], diff(ina.I1, ina.g))')
        V.set_rhs('if(1 == 1, 2 * ina.I1, ina.I2)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'if(1 == 1, 2 * diff(ina.I1, ina.g), '
            'diff(ina.I2, ina.g))')
        V.set_rhs('if(1 == 1, 4 [mV/ms], 7 [mV/ms])')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.parse_unit('mV/ms/nS'))

    def test_eval(self):
        # Test If.eval().

        cond = myokit.Equal(myokit.Number(1), myokit.Number(1))
        then = myokit.Number(10)
        else_ = myokit.Number(20)
        if_ = myokit.If(cond, then, else_)
        self.assertEqual(if_.eval(), 10)

        cond = myokit.Equal(myokit.Number(1), myokit.Number(2))
        if_ = myokit.If(cond, then, else_)
        self.assertEqual(if_.eval(), 20)

    def test_eval_unit(self):
        # Test If.eval_unit().

        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        v1 = c.add_variable('v1')
        v2 = c.add_variable('v2')
        v3 = c.add_variable('v3')
        v4 = c.add_variable('v4')
        v1.set_rhs('1 == 1')
        v2.set_rhs(2)
        v3.set_rhs(3)
        v4.set_rhs('if(v1, v2, v3)')
        z = v4.rhs()

        # Test in tolerant mode
        self.assertEqual(z.eval_unit(), None)
        v2.set_unit(myokit.units.ampere)
        self.assertEqual(z.eval_unit(), myokit.units.ampere)
        v3.set_unit(myokit.units.ampere)
        self.assertEqual(z.eval_unit(), myokit.units.ampere)
        v2.set_unit(None)
        self.assertEqual(z.eval_unit(), myokit.units.ampere)
        v3.set_unit(None)
        self.assertEqual(z.eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.eval_unit(s), myokit.units.dimensionless)
        v2.set_unit(myokit.units.ampere)
        self.assertRaises(myokit.IncompatibleUnitError, z.eval_unit, s)
        v3.set_unit(myokit.units.ampere)
        self.assertEqual(z.eval_unit(s), myokit.units.ampere)
        v2.set_unit(None)
        self.assertRaises(myokit.IncompatibleUnitError, z.eval_unit, s)
        v3.set_unit(None)
        self.assertEqual(z.eval_unit(s), myokit.units.dimensionless)

    def test_piecewise_conversion(self):
        # Test If.piecewise().
        cond = myokit.Equal(myokit.Number(1), myokit.Number(1))
        then = myokit.Number(10)
        else_ = myokit.Number(20)
        if_ = myokit.If(cond, then, else_)
        pw = if_.piecewise()
        self.assertEqual(if_.eval(), pw.eval())

        cond = myokit.Equal(myokit.Number(1), myokit.Number(2))
        if_ = myokit.If(cond, then, else_)
        pw = if_.piecewise()
        self.assertEqual(if_.eval(), pw.eval())

    def test_value(self):
        # Test If.value().
        cond = myokit.Equal(myokit.Number(1), myokit.Number(1))
        then = myokit.Number(10)
        else_ = myokit.Number(20)
        if_ = myokit.If(cond, then, else_)
        self.assertEqual(if_.value(True), then)
        self.assertEqual(if_.value(False), else_)


class PiecewiseTest(unittest.TestCase):
    """Tests myokit.Piecewise."""

    def test_creation(self):
        # Test Piecewise creation plus some accessor methods.

        # Like an if
        cond1 = myokit.Equal(myokit.Number(1), myokit.Number(1))
        then1 = myokit.Number(10)
        final = myokit.Number(99)
        pw = myokit.Piecewise(cond1, then1, final)

        # Test is_conditional()
        self.assertTrue(pw.is_conditional())

        # Test conditions()
        c = list(pw.conditions())
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0], cond1)

        # Test pieces()
        p = list(pw.pieces())
        self.assertEqual(len(p), 2)
        self.assertEqual(p[0], then1)
        self.assertEqual(p[1], final)

        # Like a big if
        cond1 = myokit.Equal(myokit.Number(2), myokit.Number(1))
        then1 = myokit.Number(1)
        cond2 = myokit.Equal(myokit.Number(3), myokit.Number(1))
        then2 = myokit.Number(2)
        cond3 = myokit.Equal(myokit.Number(1), myokit.Number(1))
        then3 = myokit.Number(3)
        final = myokit.Number(99)
        pw = myokit.Piecewise(cond1, then1, cond2, then2, cond3, then3, final)

        # Test conditions()
        c = list(pw.conditions())
        self.assertEqual(len(c), 3)
        self.assertEqual(c[0], cond1)
        self.assertEqual(c[1], cond2)
        self.assertEqual(c[2], cond3)

        # Test pieces()
        p = list(pw.pieces())
        self.assertEqual(len(p), 4)
        self.assertEqual(p[0], then1)
        self.assertEqual(p[1], then2)
        self.assertEqual(p[2], then3)
        self.assertEqual(p[3], final)

        # Wrong number of operands
        self.assertRaisesRegex(
            myokit.IntegrityError, 'odd number', myokit.Piecewise,
            cond1, then1)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'odd number', myokit.Piecewise,
            cond1, then1, cond2, then2)

        # Wrong number of operands
        self.assertRaisesRegex(
            myokit.IntegrityError, '3 or more', myokit.Piecewise, cond1)

    def test_diff(self):
        # Tests Piecewise.diff()

        m = pd_model.clone()
        V = m.get('membrane.V')
        g = m.get('ina.g')

        V.set_rhs('piecewise(1 == 1, ina.I1, 2 == 2, 3 [pA], 7 [pA])')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'piecewise('
            '1 == 1, diff(ina.I1, ina.g), '
            '2 == 2, 0 [mV], '
            '0 [mV])')
        V.set_rhs('piecewise(1 == 1, 7 [pA], 2 == 2, 3 [pA], ina.I1)')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'piecewise('
            '1 == 1, 0 [mV], '
            '2 == 2, 0 [mV], '
            'diff(ina.I1, ina.g))')
        V.set_rhs('piecewise(1 == 1, 2 * ina.I1, 2 == 2, ina.I1, 3 [pA])')
        p = V.rhs().diff(g.lhs())
        self.assertEqual(
            p.code(),
            'piecewise('
            '1 == 1, 2 * diff(ina.I1, ina.g), '
            '2 == 2, diff(ina.I1, ina.g), '
            '0 [mV])')
        V.set_rhs('piecewise(1 == 1, 4 [mV/ms], 7 [mV/ms])')
        p = V.rhs().diff(g.lhs())
        self.assertTrue(p.is_number(0))
        self.assertEqual(p.unit(), myokit.parse_unit('mV/ms/nS'))

    def test_eval(self):
        # Test Piecewise.eval().
        ct = myokit.Equal(myokit.Number(1), myokit.Number(1))
        cf = myokit.Equal(myokit.Number(1), myokit.Number(2))
        then1 = myokit.Number(1)
        then2 = myokit.Number(2)
        then3 = myokit.Number(3)
        final = myokit.Number(99)

        pw = myokit.Piecewise(cf, then1, cf, then2, cf, then3, final)
        self.assertEqual(pw.eval(), 99)
        pw = myokit.Piecewise(cf, then1, cf, then2, ct, then3, final)
        self.assertEqual(pw.eval(), 3)
        pw = myokit.Piecewise(cf, then1, ct, then2, ct, then3, final)
        self.assertEqual(pw.eval(), 2)
        pw = myokit.Piecewise(ct, then1, ct, then2, ct, then3, final)
        self.assertEqual(pw.eval(), 1)
        pw = myokit.Piecewise(ct, then1, cf, then2, ct, then3, final)
        self.assertEqual(pw.eval(), 1)
        pw = myokit.Piecewise(ct, then1, ct, then2, cf, then3, final)
        self.assertEqual(pw.eval(), 1)
        pw = myokit.Piecewise(ct, then1, cf, then2, cf, then3, final)
        self.assertEqual(pw.eval(), 1)
        pw = myokit.Piecewise(cf, then1, cf, then2, cf, then3, final)
        self.assertEqual(pw.eval(), 99)

    def test_eval_unit(self):
        # Test Piecewise.eval_unit().
        # Mini model
        m = myokit.Model()
        comp = m.add_component('comp')

        # Create conditions
        c1 = comp.add_variable('c1')
        c2 = comp.add_variable('c2')
        c1.set_rhs('1 == 2')
        c2.set_rhs('1 == 2')

        # Create values
        t1 = comp.add_variable('t1')
        t2 = comp.add_variable('t2')
        t3 = comp.add_variable('t3')
        t1.set_rhs(1)
        t2.set_rhs(2)
        t3.set_rhs(3)

        # Create piecewise
        pw = comp.add_variable('pw')
        pw.set_rhs('piecewise(c1, t1, c2, t2, t3)')
        z = pw.rhs()

        # Test in tolerant mode
        self.assertEqual(z.eval_unit(), None)
        t1.set_unit(myokit.units.ampere)
        self.assertEqual(z.eval_unit(), myokit.units.ampere)
        t2.set_unit(myokit.units.ampere)
        self.assertEqual(z.eval_unit(), myokit.units.ampere)
        t3.set_unit(myokit.units.ampere)
        self.assertEqual(z.eval_unit(), myokit.units.ampere)
        t1.set_unit(None)
        self.assertEqual(z.eval_unit(), myokit.units.ampere)
        t2.set_unit(None)
        self.assertEqual(z.eval_unit(), myokit.units.ampere)
        t3.set_unit(None)
        self.assertEqual(z.eval_unit(), None)
        t2.set_unit(myokit.units.Newton)
        t3.set_unit(myokit.units.volt)
        self.assertRaises(myokit.IncompatibleUnitError, z.eval_unit)
        t1.set_unit(None)
        t2.set_unit(None)
        t3.set_unit(None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.eval_unit(s), myokit.units.dimensionless)
        t1.set_unit(myokit.units.ampere)
        self.assertRaises(myokit.IncompatibleUnitError, z.eval_unit, s)
        t2.set_unit(myokit.units.ampere)
        self.assertRaises(myokit.IncompatibleUnitError, z.eval_unit, s)
        t3.set_unit(myokit.units.ampere)
        self.assertEqual(z.eval_unit(s), myokit.units.ampere)
        t1.set_unit(None)
        self.assertRaises(myokit.IncompatibleUnitError, z.eval_unit, s)
        t2.set_unit(None)
        self.assertRaises(myokit.IncompatibleUnitError, z.eval_unit, s)
        t3.set_unit(None)
        self.assertEqual(z.eval_unit(s), myokit.units.dimensionless)
        t2.set_unit(myokit.units.Newton)
        t3.set_unit(myokit.units.volt)
        self.assertRaises(myokit.IncompatibleUnitError, z.eval_unit, s)


class EquationTest(unittest.TestCase):
    """
    Tests :class:`myokit.Equation` (which is not strictly speaking a part of
    the equation system).
    """

    def test_clone(self):
        # Test equation cloning
        eq1 = myokit.Equation(myokit.Name('x'), myokit.Name('y'))
        eq2 = myokit.Equation(myokit.Name('y'), myokit.Name('x'))
        self.assertEqual(eq1.clone(), eq1)
        self.assertEqual(eq1, eq2.clone(subst={
            myokit.Name('x'): myokit.Name('y'),
            myokit.Name('y'): myokit.Name('x'),
        }))

    def test_code(self):
        # Test :meth:`Equation.code()`.
        eq = myokit.Equation(myokit.Name('x'), myokit.Number('3'))
        self.assertEqual(eq.code(), 'str:x = 3')
        self.assertEqual(eq.code(), str(eq))

    def test_creation(self):
        # Test creation of equations.
        lhs = myokit.Name('x')
        rhs = myokit.Number('3')
        myokit.Equation(lhs, rhs)

    def test_eq(self):
        # Test equality checking.
        eq1 = myokit.Equation(myokit.Name('x'), myokit.Number('3'))
        eq2 = myokit.Equation(myokit.Name('x'), myokit.Number('3'))
        self.assertEqual(eq1, eq2)
        self.assertEqual(eq2, eq1)
        self.assertFalse(eq1 != eq2)

        eq2 = myokit.Equation(myokit.Name('x'), myokit.Number('4'))
        self.assertNotEqual(eq1, eq2)
        self.assertNotEqual(eq2, eq1)
        self.assertTrue(eq1 != eq2)

        eq2 = myokit.Equation(myokit.Name('y'), myokit.Number('3'))
        self.assertNotEqual(eq1, eq2)
        self.assertNotEqual(eq2, eq1)

        eq2 = myokit.Equal(myokit.Name('x'), myokit.Number('3'))
        self.assertNotEqual(eq1, eq2)
        self.assertNotEqual(eq2, eq1)

        eq2 = 'hi'
        self.assertNotEqual(eq1, eq2)
        self.assertNotEqual(eq2, eq1)

    def test_hash(self):
        # Test that equations can be hashed.
        # No exception = pass
        hash(myokit.Equation(myokit.Name('x'), myokit.Number('3')))

        # Hash must be consistent during lifetime.
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('3 * sqrt(2)')
        a = hash(x.eq())
        x.rename('y')
        b = hash(x.eq())
        self.assertEqual(a, b)

    def test_iter(self):
        # Test iteration over an equation.
        lhs = myokit.Name('x')
        rhs = myokit.Number('3')
        eq = myokit.Equation(lhs, rhs)
        i = iter(eq)
        self.assertEqual(next(i), lhs)
        self.assertEqual(next(i), rhs)
        self.assertEqual(len(list(eq)), 2)

    def test_str_and_repr(self):
        # Test string conversion
        x = myokit.Model('m').add_component('c').add_variable('x')
        eq1 = myokit.Equation(myokit.Name(x), myokit.Number('3'))
        self.assertEqual(str(eq1), 'c.x = 3')
        self.assertEqual(repr(eq1), '<Equation c.x = 3>')


if __name__ == '__main__':
    unittest.main()
