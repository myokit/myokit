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
        self.assertFalse(x.bracket())

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

        # No units set anywhere: dimensionless
        self.assertEqual(d.eval_unit(), myokit.units.dimensionless)

        # Time has a unit
        t.set_unit(myokit.units.second)
        self.assertEqual(d.eval_unit(), myokit.parse_unit('1/s'))

        # Both have a unit
        x.set_unit(myokit.units.volt)
        self.assertEqual(d.eval_unit(), myokit.parse_unit('V/s'))

        # Time has no unit
        t.set_unit(None)
        self.assertEqual(d.eval_unit(), myokit.units.volt)

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


# Plus
# Minus
# Multiply
# Divide

# Quotient
# Remainder

# Power
# Sqrt
# Exp
# Log
# Log10

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
