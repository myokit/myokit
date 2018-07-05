#!/usr/bin/env python
#
# Tests the expression classes.
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
import numpy as np

#TODO Add tests for all operators

# Unit --> See test_units.py
# Quantity --> See test_units.py


class ExpressionTest(unittest.TestCase):

    def test_equal(self):
        """
        Tests expression's ``__eq__`` operators
        """
        a1 = myokit.Number(4)
        a2 = myokit.Number(5)
        self.assertEqual(a1, a1)
        self.assertEqual(a1, myokit.Number(4))
        self.assertEqual(a1, myokit.Number(4.0))
        self.assertNotEqual(a1, a2)
        b1 = myokit.Name('test')
        b2 = myokit.Name('tost')
        self.assertEqual(b1, b1)
        self.assertNotEqual(b1, b2)
        c1 = myokit.PrefixPlus(a1)
        c2 = myokit.PrefixPlus(a1)
        self.assertEqual(c1, c1)
        self.assertEqual(c1, c2)
        c2 = myokit.PrefixPlus(a2)
        self.assertNotEqual(c1, c2)
        d1 = myokit.Plus(a1, a2)
        d2 = myokit.Plus(a1, a2)
        self.assertEqual(d1, d1)
        self.assertEqual(d1, d2)
        d2 = myokit.Plus(a2, a1)
        self.assertNotEqual(d2, d1)
        e1 = myokit.Sqrt(a1)
        e2 = myokit.Sqrt(a1)
        self.assertEqual(e1, e1)
        self.assertEqual(e1, e2)
        e2 = myokit.Sqrt(a2)
        self.assertNotEqual(e1, e2)

    def test_if(self):
        """
        Tests :class:`If`.
        """
        true = myokit.Number(1)
        false = myokit.Number(0)
        two = myokit.Number(2)
        three = myokit.Number(3)
        x = myokit.If(true, two, three)
        self.assertEqual(x.eval(), 2)
        self.assertEqual(x.condition(), true)
        x = myokit.If(true, three, two)
        self.assertEqual(x.eval(), 3)
        x = myokit.If(false, two, three)
        self.assertEqual(x.eval(), 3)
        self.assertEqual(x.condition(), false)
        x = myokit.If(false, three, two)
        self.assertEqual(x.eval(), 2)

        # Conversion to piecewise
        x = myokit.If(true, two, three).piecewise()
        self.assertIsInstance(x, myokit.Piecewise)
        self.assertEqual(x.eval(), 2)
        x = myokit.If(true, three, two).piecewise()
        self.assertIsInstance(x, myokit.Piecewise)
        self.assertEqual(x.eval(), 3)
        x = myokit.If(false, two, three).piecewise()
        self.assertIsInstance(x, myokit.Piecewise)
        self.assertEqual(x.eval(), 3)
        x = myokit.If(false, three, two).piecewise()
        self.assertIsInstance(x, myokit.Piecewise)
        self.assertEqual(x.eval(), 2)

    def test_contains_type(self):
        """
        Tests :meth:`Expression.contains_type`.
        """
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

    def test_eval(self):
        """
        Tests :meth:`Expression.eval()`.
        """
        # Test basic use
        e = myokit.parse_expression('1 + 1 + 1')
        self.assertEqual(e.eval(), 3)

        # Test errors
        e = myokit.parse_expression('1 / 0')
        self.assertRaises(myokit.NumericalError, e.eval)

        # Test errors-in-errors
        e = myokit.parse_expression('16^1000 / 0')
        self.assertRaisesRegexp(myokit.NumericalError, 'another error', e.eval)

        # Test errors with variables
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        x.set_rhs(0)
        y.set_rhs('5 / 2')
        z.set_rhs('(x + y) / 0')
        self.assertRaisesRegexp(
            myokit.NumericalError, 'c.x = 0', z.rhs().eval)
        self.assertRaisesRegexp(
            myokit.NumericalError, 'c.y = 5 / 2', z.rhs().eval)

        # Test error in error with variables
        y.set_rhs('16^1000')
        self.assertRaisesRegexp(
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
        self.assertRaisesRegexp(ValueError, 'dict or None', z.rhs().eval, 2)
        self.assertRaisesRegexp(ValueError, 'All keys', z.rhs().eval, {5: 1})
        self.assertRaisesRegexp(
            ValueError, 'All values', z.rhs().eval, {x.lhs(): 'hello'})

        # Test if substituted Name is treated as number in error formatting
        y.set_rhs('x')
        z.set_rhs('(x + y) / 0')
        self.assertRaisesRegexp(
            myokit.NumericalError, 'c.y = 3', z.rhs().eval, {y.lhs(): 3})

    def test_int_conversion(self):
        """
        Tests conversion of expressions to int.
        """
        x = myokit.parse_expression('1 + 2 + 3')
        self.assertEqual(int(x), 6)
        x = myokit.parse_expression('1 + 3.9')
        self.assertEqual(int(x), 4)

    def test_float_conversion(self):
        """
        Tests conversion of expressions to float.
        """
        x = myokit.parse_expression('1 + 2 + 3')
        self.assertEqual(int(x), 6)
        x = myokit.parse_expression('1 + 3.9')
        self.assertEqual(float(x), 4.9)

    def test_is_conditional(self):
        """
        Tests :meth:`Expression.is_conditional().`.
        """
        pe = myokit.parse_expression
        self.assertFalse(pe('1 + 2 + 3').is_conditional())
        self.assertTrue(pe('if(1, 0, 2)').is_conditional())
        self.assertTrue(pe('1 + if(1, 0, 2)').is_conditional())

    def test_pyfunc(self):
        """
        Tests the pyfunc() method.
        """
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
        """
        Tests the pystr() method.
        """
        # Note: Extensive testing happens in pywriter / numpywriter tests!
        x = myokit.parse_expression('3 * sqrt(v)')
        self.assertEqual(x.pystr(use_numpy=False), '3.0 * math.sqrt(v)')
        self.assertEqual(x.pystr(use_numpy=True), '3.0 * numpy.sqrt(v)')

    def test_tree_str(self):
        """
        Tests :meth:`Expression.tree_str()`.
        More extensive testing of this method should happen in the individual
        expression tests.
        """
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
        """
        Tests :meth:`Expression.validate()`.
        """
        e = myokit.parse_expression('5 + 2 * exp(3 / (1 + 2))')
        e.validate()
        self.assertIsNone(e.validate())

        # Test cycles in expression tree are found (not via variables!)
        p = myokit.Plus(myokit.Number(1), myokit.Number(1))
        # Have to hack this in, since, properly used, expressions are immutable
        p._operands = (myokit.Number(2), p)
        self.assertRaisesRegexp(myokit.IntegrityError, 'yclical', p.validate)

        # Wrong type operands
        # Again, need to hack this in so creation doesn't fault!
        p._operands = (myokit.Number(1), 2)
        self.assertRaisesRegexp(myokit.IntegrityError, 'type', p.validate)

    def test_walk(self):
        """
        Tests :meth:`Expression.walk().
        """
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
    """
    Tests myokit.Number.
    """

    def test_basic(self):
        """
        Tests construction, other basics.
        """
        # Test myokit.Number creation and representation
        x = myokit.Number(-4.0)
        self.assertEqual(str(x), '-4')
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
        self.assertRaisesRegexp(ValueError, 'Unit', myokit.Number, 3, 1)
        # Construction from quantity
        q = myokit.Quantity(3, 'kg')
        myokit.Number(q)
        self.assertEqual(q.unit(), myokit.parse_unit('kg'))
        self.assertRaisesRegexp(ValueError, 'unit', myokit.Number, q, 'kg')

    def test_bracket(self):
        """ Tests Number.bracket(). """
        # Never needs a bracket
        x = myokit.Number(2)
        self.assertFalse(x.bracket())

        # Doesn't have an operand
        self.assertRaises(ValueError, x.bracket, myokit.Number(2))

    def test_clone(self):
        """ Tests Number.clone(). """
        x = myokit.Number(2)
        y = x.clone()
        self.assertIsNot(x, y)
        self.assertEqual(x, y)

        # With substitution
        z = myokit.Number(10)
        y = x.clone(subst={x: z})
        self.assertEqual(y, z)

    def test_eval(self):
        """
        Tests evaluation (with single precision).
        """
        x = myokit.Number(2)
        self.assertEqual(type(x.eval()), float)
        self.assertEqual(
            type(x.eval(precision=myokit.SINGLE_PRECISION)), np.float32)

    def test_eval_unit(self):
        """
        Tests Number eval_unit.
        """
        # Test in tolerant mode
        x = myokit.Number(3)
        self.assertEqual(x.eval_unit(), None)
        y = myokit.Number(3, myokit.units.ampere)
        self.assertEqual(y.eval_unit(), myokit.units.ampere)

        # Test in strict mode
        self.assertEqual(
            x.eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(y.eval_unit(myokit.UNIT_STRICT), myokit.units.ampere)

    def test_tree_str(self):
        """ Tests Number.tree_str() """
        # Test simple
        x = myokit.Number(1)
        self.assertEqual(x.tree_str(), '1\n')

        # Test with spaces
        e = myokit.Plus(x, myokit.Number(-2))
        self.assertEqual(e.tree_str(), '+\n  1\n  -2\n')


class NameTest(unittest.TestCase):
    """
    Tests myokit.Name.
    """

    def test_basics(self):
        """
        Tests creation, representation,
        """
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

        # Test invalid creation
        myokit.Name('this is ok')
        self.assertRaises(ValueError, myokit.Name, 3)

        # Test rhs
        # Name of non-state: rhs() should be the associated variable's rhs
        self.assertEqual(x.rhs(), myokit.Number(15))
        # Name of state: rhs() should be the initial value (since this is the
        # value of the variable).
        xvar.promote(12)
        self.assertEqual(x.rhs(), myokit.Number(12))
        # Invalid variable:
        a = myokit.Name('test')
        self.assertRaises(Exception, a.rhs)

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
        """ Tests Name.bracket(). """
        # Never needs a bracket
        x = myokit.Name('hi')
        self.assertFalse(x.bracket())

        # Doesn't have an operand
        self.assertRaises(ValueError, x.bracket, myokit.Number(2))

    def test_clone(self):
        """ Tests Name.clone(). """
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

    def test_eval_unit(self):
        """
        Tests Name eval_unit.
        """
        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(3)
        y = c.add_variable('y')
        y.set_rhs(2)
        y.set_unit(myokit.units.Newton)

        # Test in tolerant mode
        self.assertEqual(x.lhs().eval_unit(), None)
        self.assertEqual(y.lhs().eval_unit(), myokit.units.Newton)

        # Test in strict mode
        self.assertEqual(
            x.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(
            y.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.Newton)

    def test_rhs(self):
        """
        Tests Name.rhs().
        """
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('3 + 2')

        x = myokit.Name(x)
        self.assertEqual(x.rhs().eval(), 5)

    def test_tree_str(self):
        """ Tests Name.tree_str() """
        # Test simple
        x = myokit.Name('y')
        self.assertEqual(x.tree_str(), 'y\n')

        # Test with spaces
        e = myokit.Plus(x, x)
        self.assertEqual(e.tree_str(), '+\n  y\n  y\n')


class DerivativeTest(unittest.TestCase):
    """
    Tests myokit.Derivative.
    """
    def test_basic(self):
        """
        Tests creation.
        """
        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        n = myokit.Name(v)

        myokit.Derivative(n)
        self.assertRaisesRegexp(
            ValueError, 'of Name', myokit.Derivative, myokit.Number(1))

    def test_bracket(self):
        """ Tests Derivative.bracket() """
        x = myokit.Derivative(myokit.Name('x'))
        self.assertFalse(x.bracket(myokit.Name('x')))
        self.assertRaises(ValueError, x.bracket, myokit.Number(1))

    def test_clone(self):
        """ Tests Derivative.clone(). """
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

    def test_eval_unit(self):
        """ Tests Derivative.eval_unit() """
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

    def test_rhs(self):
        """ Tests Derivative.rhs() """
        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('(10 - x) / 100')
        x.promote(0)

        # Get derivative object
        d = x.lhs()
        self.assertEqual(d.rhs(), x.rhs())

    def test_tree_str(self):
        """ Tests Derivative.tree_str() """
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


class PrefixPlusTest(unittest.TestCase):
    """
    Tests myokit.PrefixPlus.
    """
    def test_clone(self):
        """ Tests PrefixPlus.clone(). """
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
        """ Tests PrefixPlus.bracket(). """
        i = myokit.Number(1)
        x = myokit.PrefixPlus(i)
        self.assertFalse(x.bracket(i))
        i = myokit.Plus(myokit.Number(1), myokit.Number(2))
        x = myokit.PrefixPlus(i)
        self.assertTrue(x.bracket(i))
        self.assertRaises(ValueError, x.bracket, myokit.Number(1))

    def test_eval(self):
        """
        Tests PrefixPlus evaluation.
        """
        x = myokit.PrefixPlus(myokit.Number(2))
        self.assertEqual(x.eval(), 2)

    def test_eval_unit(self):
        """
        Tests PrefixPlus.eval_unit().
        """
        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('+(3)')
        y = c.add_variable('y')
        y.set_rhs('+(2 [N])')

        # Test in tolerant mode
        self.assertEqual(x.lhs().eval_unit(), None)
        self.assertEqual(y.lhs().eval_unit(), myokit.units.Newton)

        # Test in strict mode
        self.assertEqual(
            x.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(
            y.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.Newton)

    def test_tree_str(self):
        """ Tests PrefixPlus.tree_str() """
        # Test simple
        x = myokit.PrefixPlus(myokit.Number(1))
        self.assertEqual(x.tree_str(), '+\n  1\n')

        # Test with spaces
        y = myokit.Plus(
            myokit.PrefixPlus(myokit.Number(-1)),
            myokit.PrefixPlus(myokit.Number(2)))
        self.assertEqual(y.tree_str(), '+\n  +\n    -1\n  +\n    2\n')


class PrefixMinusTest(unittest.TestCase):
    """
    Tests myokit.PrefixMinus.
    """
    def test_clone(self):
        """ Tests PrefixMinus.clone(). """
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
        """ Tests PrefixMinus.bracket(). """
        i = myokit.Number(1)
        x = myokit.PrefixMinus(i)
        self.assertFalse(x.bracket(i))
        i = myokit.Plus(myokit.Number(1), myokit.Number(2))
        x = myokit.PrefixMinus(i)
        self.assertTrue(x.bracket(i))
        self.assertRaises(ValueError, x.bracket, myokit.Number(1))

    def test_eval(self):
        """
        Tests PrefixMinus evaluation.
        """
        x = myokit.PrefixMinus(myokit.Number(2))
        self.assertEqual(x.eval(), -2)

    def test_eval_unit(self):
        """
        Tests PrefixMinus.eval_unit().
        """
        # Mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('-(3)')
        y = c.add_variable('y')
        y.set_rhs('-(2 [N])')

        # Test in tolerant mode
        self.assertEqual(x.lhs().eval_unit(), None)
        self.assertEqual(y.lhs().eval_unit(), myokit.units.Newton)

        # Test in strict mode
        self.assertEqual(
            x.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        self.assertEqual(
            y.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.Newton)

    def test_tree_str(self):
        """ Tests PrefixMinus.tree_str() """
        # Test simple
        x = myokit.PrefixMinus(myokit.Number(1))
        self.assertEqual(x.tree_str(), '-\n  1\n')

        # Test with spaces
        y = myokit.Plus(
            myokit.PrefixMinus(myokit.Number(1)),
            myokit.PrefixMinus(myokit.Number(-2)))
        self.assertEqual(y.tree_str(), '+\n  -\n    1\n  -\n    -2\n')


class PlusTest(unittest.TestCase):
    """
    Tests myokit.Plus.
    """
    def test_clone(self):
        """ Tests Plus.clone(). """
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
        """ Tests Plus.bracket(). """
        i = myokit.Number(1)
        j = myokit.parse_expression('1 + 2')
        x = myokit.Plus(i, j)
        self.assertFalse(x.bracket(i))
        self.assertTrue(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

    def test_eval(self):
        """
        Tests Plus evaluation.
        """
        x = myokit.Plus(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.eval(), 3)
        x = myokit.Plus(myokit.Number(1), myokit.PrefixMinus(myokit.Number(2)))
        self.assertEqual(x.eval(), -1)

    def test_eval_unit(self):
        """ Tests Plus.eval_unit(). """
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
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        y.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.lhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(myokit.units.volt)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        x.set_unit(None)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.lhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        """ Tests Plus.tree_str(). """
        # Test simple
        x = myokit.Plus(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '+\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  +\n    1\n    2\n')
        x = myokit.parse_expression('1 + (2 + 3)')
        self.assertEqual(x.tree_str(), '+\n  1\n  +\n    2\n    3\n')


class MinusTest(unittest.TestCase):
    """
    Tests myokit.Minus.
    """
    def test_eval(self):
        """
        Tests Minus evaluation.
        """
        x = myokit.Minus(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.eval(), -1)

    def test_eval_unit(self):
        """ Tests Minus.eval_unit(). """
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
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        y.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.lhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(myokit.units.volt)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        x.set_unit(None)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.lhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        """ Tests Minus.tree_str(). """
        # Test simple
        x = myokit.Minus(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '-\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  -\n    1\n    2\n')
        x = myokit.parse_expression('1 - (2 - 3)')
        self.assertEqual(x.tree_str(), '-\n  1\n  -\n    2\n    3\n')


class MultiplyTest(unittest.TestCase):
    """
    Tests myokit.Multiply.
    """
    def test_eval(self):
        """
        Tests Multiply evaluation.
        """
        x = myokit.Multiply(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.eval(), 2)

    def test_eval_unit(self):
        """ Tests Multiply.eval_unit(). """
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
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.lhs().eval_unit(), myokit.units.volt * myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode (where None becomes dimensionless)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.volt * myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        """ Tests Multiply.tree_str(). """
        # Test simple
        x = myokit.Multiply(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '*\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  *\n    1\n    2\n')
        x = myokit.parse_expression('1 * (2 * 3)')
        self.assertEqual(x.tree_str(), '*\n  1\n  *\n    2\n    3\n')


class DivideTest(unittest.TestCase):
    """
    Tests myokit.Divide.
    """
    def test_tree_str(self):
        """ Tests Divide.tree_str(). """
        # Test simple
        x = myokit.Divide(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '/\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  /\n    1\n    2\n')
        x = myokit.parse_expression('1 / (2 / 3)')
        self.assertEqual(x.tree_str(), '/\n  1\n  /\n    2\n    3\n')

    def test_eval(self):
        """
        Tests Divide evaluation.
        """
        x = myokit.Divide(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.eval(), 0.5)

    def test_eval_unit(self):
        """ Tests Divide.eval_unit(). """
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
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.lhs().eval_unit(), myokit.units.volt / myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), 1 / myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode (where None becomes dimensionless)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.volt / myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT),
            1 / myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)


class QuotientTest(unittest.TestCase):
    """
    Tests myokit.Quotient.
    """
    def test_eval(self):
        """
        Tests Quotient evaluation.
        """
        x = myokit.Quotient(myokit.Number(7), myokit.Number(2))
        self.assertEqual(x.eval(), 3.0)

    def test_eval_unit(self):
        """ Tests Quotient.eval_unit(). """
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
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.lhs().eval_unit(), myokit.units.volt / myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), 1 / myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode (where None becomes dimensionless)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.volt / myokit.units.meter)
        x.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT),
            1 / myokit.units.meter)
        y.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        """ Tests Quotient.tree_str(). """
        # Test simple
        x = myokit.Quotient(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '//\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  //\n    1\n    2\n')
        x = myokit.parse_expression('1 // (2 // 3)')
        self.assertEqual(x.tree_str(), '//\n  1\n  //\n    2\n    3\n')


class RemainderTest(unittest.TestCase):
    """
    Tests myokit.Remainder.
    """
    def test_eval(self):
        """
        Tests Divide evaluation.
        """
        x = myokit.Remainder(myokit.Number(7), myokit.Number(4))
        self.assertEqual(x.eval(), 3.0)

    def test_eval_unit(self):
        """ Tests Remainder.eval_unit(). """
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
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.lhs().eval_unit(), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)
        y.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode (where None becomes dimensionless)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.volt)
        y.set_unit(myokit.units.meter)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT),
            myokit.units.dimensionless)
        y.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        """ Tests Remainder.tree_str(). """
        # Test simple
        x = myokit.Remainder(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '%\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  %\n    1\n    2\n')
        x = myokit.parse_expression('1 % (2 % 3)')
        self.assertEqual(x.tree_str(), '%\n  1\n  %\n    2\n    3\n')


class PowerTest(unittest.TestCase):
    """
    Tests myokit.Power.
    """
    def test_clone(self):
        """ Tests Power.clone(). """
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

    def test_bracket(self):
        """ Tests Power.bracket(). """
        i = myokit.Number(1)
        j = myokit.parse_expression('1 + 2')
        x = myokit.Power(i, j)
        self.assertFalse(x.bracket(i))
        self.assertTrue(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

    def test_eval(self):
        """
        Tests Power evaluation.
        """
        x = myokit.Power(myokit.Number(2), myokit.Number(3))
        self.assertEqual(x.eval(), 8)
        x = myokit.Power(
            myokit.Number(2), myokit.PrefixMinus(myokit.Number(1)))
        self.assertEqual(x.eval(), 0.5)

    def test_eval_unit(self):
        """ Tests Power.eval_unit(). """
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
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt ** 2)
        y.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt ** 2)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)
        y.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.lhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(s), myokit.units.volt ** 2)
        y.set_unit(myokit.units.volt)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.lhs().eval_unit, myokit.UNIT_STRICT)
        x.set_unit(None)
        self.assertRaises(
            myokit.IncompatibleUnitError,
            z.lhs().eval_unit, myokit.UNIT_STRICT)
        y.set_unit(None)
        self.assertEqual(
            z.lhs().eval_unit(myokit.UNIT_STRICT), myokit.units.dimensionless)

    def test_tree_str(self):
        """ Tests Power.tree_str(). """
        # Test simple
        x = myokit.Power(myokit.Number(1), myokit.Number(2))
        self.assertEqual(x.tree_str(), '^\n  1\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  ^\n    1\n    2\n')
        x = myokit.parse_expression('1 ^ (2 ^ 3)')
        self.assertEqual(x.tree_str(), '^\n  1\n  ^\n    2\n    3\n')


class SqrtTest(unittest.TestCase):
    """
    Tests myokit.Sqrt.
    """
    def test_creation(self):
        """ Tests Sqrt creation. """
        myokit.Sqrt(myokit.Number(1))
        self.assertRaisesRegexp(
            myokit.IntegrityError, 'wrong number', myokit.Sqrt,
            myokit.Number(1), myokit.Number(2))

    def test_clone(self):
        """ Tests Sqrt.clone(). """
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

    def test_bracket(self):
        """ Tests Sqrt.bracket(). """
        i = myokit.Number(1)
        j = myokit.parse_expression('1 + 2')
        x = myokit.Sqrt(i)
        self.assertFalse(x.bracket(i))
        x = myokit.Sqrt(j)
        self.assertFalse(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

    def test_eval(self):
        """
        Tests Sqrt evaluation.
        """
        x = myokit.Sqrt(myokit.Number(9))
        self.assertEqual(x.eval(), 3)

    def test_eval_unit(self):
        """ Tests Sqrt.eval_unit(). """
        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        z = c.add_variable('z')
        x.set_rhs(1)
        z.set_rhs(myokit.Sqrt(x.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertRaisesRegexp(
            myokit.IncompatibleUnitError, 'non-integer exponents',
            z.lhs().eval_unit)
        x.set_unit(myokit.units.volt ** 2)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.lhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaisesRegexp(
            myokit.IncompatibleUnitError, 'non-integer exponents',
            z.lhs().eval_unit, s)
        x.set_unit(myokit.units.volt ** 2)
        self.assertEqual(z.lhs().eval_unit(s), myokit.units.volt)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(s), myokit.units.dimensionless)

    def test_tree_str(self):
        """ Tests Sqrt.tree_str(). """
        # Test simple
        x = myokit.Sqrt(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'sqrt\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  sqrt\n    2\n')
        x = myokit.parse_expression('sqrt(1 + sqrt(2))')
        self.assertEqual(x.tree_str(), 'sqrt\n  +\n    1\n    sqrt\n      2\n')


class ExpTest(unittest.TestCase):
    """
    Tests myokit.Exp.
    """
    def test_creation(self):
        """ Tests Exp creation. """
        myokit.Exp(myokit.Number(1))
        self.assertRaisesRegexp(
            myokit.IntegrityError, 'wrong number', myokit.Exp,
            myokit.Number(1), myokit.Number(2))

    def test_clone(self):
        """ Tests Exp.clone(). """
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

    def test_bracket(self):
        """ Tests Exp.bracket(). """
        i = myokit.Number(1)
        j = myokit.parse_expression('1 + 2')
        x = myokit.Exp(i)
        self.assertFalse(x.bracket(i))
        x = myokit.Exp(j)
        self.assertFalse(x.bracket(j))
        self.assertRaises(ValueError, x.bracket, myokit.Number(3))

    def test_eval(self):
        """ Tests Exp.eval(). """
        x = myokit.Exp(myokit.Number(9))
        self.assertEqual(x.eval(), np.exp(9))

    def test_eval_unit(self):
        """ Tests Exp.eval_unit(). """
        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        z = c.add_variable('z')
        x.set_rhs(1)
        z.set_rhs(myokit.Exp(x.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.lhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaisesRegexp(
            myokit.IncompatibleUnitError, 'dimensionless',
            z.lhs().eval_unit, s)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(s), myokit.units.dimensionless)

    def test_tree_str(self):
        """ Tests Exp.tree_str(). """
        # Test simple
        x = myokit.Exp(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'exp\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  exp\n    2\n')
        x = myokit.parse_expression('exp(1 + exp(2))')
        self.assertEqual(x.tree_str(), 'exp\n  +\n    1\n    exp\n      2\n')


class LogTest(unittest.TestCase):
    """
    Tests myokit.Log.
    """
    def test_creation(self):
        """ Tests Log creation. """
        myokit.Log(myokit.Number(1))
        myokit.Log(myokit.Number(1), myokit.Number(2))
        self.assertRaisesRegexp(
            myokit.IntegrityError, 'wrong number', myokit.Log,
            myokit.Number(1), myokit.Number(2), myokit.Number(3))

    def test_clone(self):
        """ Tests Log.clone(). """
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

    def test_bracket(self):
        """ Tests Log.bracket(). """
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

    def test_eval(self):
        """ Tests Exp.eval(). """
        x = myokit.Log(myokit.Number(9))
        self.assertEqual(x.eval(), np.log(9))

    def test_eval_unit(self):
        """ Tests Log.eval_unit(). """
        # Create mini model
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        z = c.add_variable('z')
        x.set_rhs(1)
        z.set_rhs(myokit.Log(x.lhs()))

        # Test in tolerant mode
        self.assertEqual(z.lhs().eval_unit(), None)
        x.set_unit(myokit.units.volt)
        self.assertEqual(z.lhs().eval_unit(), myokit.units.dimensionless)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(), None)

        # Test in strict mode
        s = myokit.UNIT_STRICT
        self.assertEqual(z.lhs().eval_unit(s), myokit.units.dimensionless)
        x.set_unit(myokit.units.volt)
        self.assertRaisesRegexp(
            myokit.IncompatibleUnitError, 'dimensionless',
            z.lhs().eval_unit, s)
        x.set_unit(None)
        self.assertEqual(z.lhs().eval_unit(s), myokit.units.dimensionless)

    def test_tree_str(self):
        """ Tests Log.tree_str(). """
        # Test simple
        x = myokit.Log(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'log\n  2\n')

        # Test with spaces
        x = myokit.PrefixMinus(x)
        self.assertEqual(x.tree_str(), '-\n  log\n    2\n')
        x = myokit.parse_expression('log(log(1, 2))')
        self.assertEqual(x.tree_str(), 'log\n  log\n    1\n    2\n')


class Log10Test(unittest.TestCase):
    """
    Tests myokit.Log10.
    """
    def test_eval(self):
        """ Tests Log10.eval(). """
        x = myokit.Log10(myokit.Number(9))
        self.assertEqual(x.eval(), np.log10(9))

    def test_tree_str(self):
        """ Tests Log10.tree_str(). """
        # Test simple
        x = myokit.Log10(myokit.Number(2))
        self.assertEqual(x.tree_str(), 'log10\n  2\n')


# Sin
# Cos
# Tan
# ASin
# ACos
# ATan

# Floor
# Ceil
# Abs

# Equal
# NotEqual
# More
# Less
# MoreEqual
# LessEqual

# Not
# And
# Or

# If
# Piecewise,

# UnsupportedFunction


if __name__ == '__main__':
    unittest.main()
