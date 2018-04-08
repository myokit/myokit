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


#TODO Add tests for all operators

# Expression, LhsExpression, Derivative,
# PrefixExpression, PrefixPlus, PrefixMinus,
# InfixExpression,
# Function,
# Condition, PrefixCondition, InfixCondition

# [ ] Name
# [ ] Number

# [ ] Plus
# [ ] Minus
# [ ] Multiply
# [ ] Divide

# [ ] Quotient
# [ ] Remainder

# [ ] Power
# [ ] Sqrt
# [ ] Exp
# [ ] Log
# [ ] Log10

# [ ] Sin
# [ ] Cos
# [ ] Tan
# [ ] ASin
# [ ] ACos
# [ ] ATan

# [ ] Floor
# [ ] Ceil
# [ ] Abs

# [ ] Equal
# [ ] NotEqual
# [ ] More
# [ ] Less
# [ ] MoreEqual
# [ ] LessEqual

# [ ] Not
# [ ] And
# [ ] Or

# [ ] If
# [ ] Piecewise,

# [ ] UnsupportedFunction

# [x] Unit --> See test_units.py
# [x] Quantity --> See test_units.py


class ExpressionsTest(unittest.TestCase):

    def test_number(self):
        """ Tests ``Number``. """
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

        # Test python function
        f = x.pyfunc()
        self.assertTrue(callable(f))
        self.assertEqual(f(), x.eval())

    def test_name(self):
        """ Tests ``Name``. """
        model = myokit.Model()
        component = model.add_component('c')
        xvar = component.add_variable('x')
        xvar.set_rhs('15')
        yvar = component.add_variable('y')
        yvar.set_rhs('3 * x ')
        zvar = component.add_variable('z')
        zvar.set_rhs('2 + y + x')

        x = myokit.Name(xvar)
        self.assertEqual(x.code(), 'c.x')

        # Test clone
        a = x.clone()
        self.assertEqual(x, a)
        z = myokit.Name(zvar)
        a = z.clone()
        self.assertEqual(z, a)
        # With substitution (handled in Name)
        y = myokit.Name(yvar)
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
        b = z.clone(expand=True, retain=[xvar])
        self.assertEqual(a, b)

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

        # Test python function
        # Function for Name is always `lambda x: x` (ignores rhs!)
        f = x.pyfunc()
        self.assertTrue(callable(f))
        self.assertEqual(f(100), 100)
        f = z.pyfunc()
        self.assertTrue(callable(f))
        self.assertEqual(f(5), 5)


class ExpressionTest(unittest.TestCase):
    def test_equal(self):
        """
        Tests __eq__ operators
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
        Tests If
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


if __name__ == '__main__':
    unittest.main()
