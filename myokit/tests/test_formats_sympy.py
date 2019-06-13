#!/usr/bin/env python
#
# Tests the importers for various formats
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
import myokit.formats.sympy

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class SymPyReadWriteTest(unittest.TestCase):
    """
    Tests the SymPy ewriter and ereader classes.
    """

    def test_all(self):
        """
        Test exporting and importing of all Myokit expression types.
        """
        import sympy

        model = myokit.Model()
        component = model.add_component('c')
        bvar = component.add_variable('b')
        bvar.set_rhs(1.23)
        avar = component.add_variable('a')
        avar.set_rhs('b')

        w = myokit.formats.sympy.SymPyExpressionWriter()
        r = myokit.formats.sympy.SymPyExpressionReader(model)

        # Name
        a = myokit.Name(avar)
        ca = sympy.Symbol('c.a')
        self.assertEqual(w.ex(a), ca)
        self.assertEqual(r.ex(ca), a)

        # Number with unit
        b = myokit.Number('12', 'pF')
        cb = sympy.Float(12)
        self.assertEqual(w.ex(b), cb)
        # Note: Units are lost in sympy im/ex-port!
        #self.assertEqual(r.ex(cb), b)

        # Number without unit
        b = myokit.Number('12')
        cb = sympy.Float(12)
        self.assertEqual(w.ex(b), cb)
        self.assertEqual(r.ex(cb), b)

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), cb)
        # Note: Sympy doesn't seem to have a prefix plus
        self.assertEqual(r.ex(cb), b)

        # Prefix minus
        # Note: SymPy treats -x as Mul(NegativeOne, x)
        # But for numbers just returns a number with a negative value
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), -cb)
        self.assertEqual(float(r.ex(-cb)), float(x))

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), ca + cb)
        # Note: SymPy likes to re-order the operands...
        self.assertEqual(float(r.ex(ca + cb)), float(x))

        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), ca - cb)
        self.assertEqual(float(r.ex(ca - cb)), float(x))

        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), ca * cb)
        self.assertEqual(float(r.ex(ca * cb)), float(x))

        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), ca / cb)
        self.assertEqual(float(r.ex(ca / cb)), float(x))

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(w.ex(x), ca // cb)
        self.assertEqual(float(r.ex(ca // cb)), float(x))

        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(w.ex(x), ca % cb)
        self.assertEqual(float(r.ex(ca % cb)), float(x))

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), ca ** cb)
        self.assertEqual(float(r.ex(ca ** cb)), float(x))

        # Sqrt
        x = myokit.Sqrt(a)
        cx = sympy.sqrt(ca)
        self.assertEqual(w.ex(x), cx)
        # Note: SymPy converts sqrt to power
        self.assertEqual(float(r.ex(cx)), float(x))

        # Exp
        x = myokit.Exp(a)
        cx = sympy.exp(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Log(a)
        x = myokit.Log(a)
        cx = sympy.log(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Log(a, b)
        x = myokit.Log(a, b)
        cx = sympy.log(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(float(r.ex(cx)), float(x))

        # Log10
        x = myokit.Log10(b)
        cx = sympy.log(cb, 10)
        self.assertEqual(w.ex(x), cx)
        self.assertAlmostEqual(float(r.ex(cx)), float(x))

        # Sin
        x = myokit.Sin(a)
        cx = sympy.sin(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Cos
        x = myokit.Cos(a)
        cx = sympy.cos(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Tan
        x = myokit.Tan(a)
        cx = sympy.tan(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # ASin
        x = myokit.ASin(a)
        cx = sympy.asin(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # ACos
        x = myokit.ACos(a)
        cx = sympy.acos(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # ATan
        x = myokit.ATan(a)
        cx = sympy.atan(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Floor
        x = myokit.Floor(a)
        cx = sympy.floor(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Ceil
        x = myokit.Ceil(a)
        cx = sympy.ceiling(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Abs
        x = myokit.Abs(a)
        cx = sympy.Abs(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Equal
        x = myokit.Equal(a, b)
        cx = sympy.Eq(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # NotEqual
        x = myokit.NotEqual(a, b)
        cx = sympy.Ne(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # More
        x = myokit.More(a, b)
        cx = sympy.Gt(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Less
        x = myokit.Less(a, b)
        cx = sympy.Lt(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # MoreEqual
        x = myokit.MoreEqual(a, b)
        cx = sympy.Ge(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # LessEqual
        x = myokit.LessEqual(a, b)
        cx = sympy.Le(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Not
        x = myokit.Not(a)
        cx = sympy.Not(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # And
        cond1 = myokit.More(a, b)
        cond2 = myokit.Less(a, b)
        c1 = sympy.Gt(ca, cb)
        c2 = sympy.Lt(ca, cb)

        x = myokit.And(cond1, cond2)
        cx = sympy.And(c1, c2)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Or
        x = myokit.Or(cond1, cond2)
        cx = sympy.Or(c1, c2)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # If
        # Note: sympy only does piecewise, not if
        x = myokit.If(cond1, a, b)
        cx = sympy.Piecewise((ca, c1), (cb, True))
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x.piecewise())

        # Piecewise
        c = myokit.Number(1)
        cc = sympy.Float(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        cx = sympy.Piecewise((ca, c1), (cb, c2), (cc, True))
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Myokit piecewise's (like CellML's) always have a final True
        # condition (i.e. an 'else'). SymPy doesn't require this, so test if
        # we can import this --> It will add an "else 0"
        x = myokit.Piecewise(cond1, a, myokit.Number(0))
        cx = sympy.Piecewise((ca, c1))
        self.assertEqual(r.ex(cx), x)

        # Myokit.Unsupported function placeholder --> Should raise exception
        u = myokit.UnsupportedFunction('frog', x)
        self.assertRaisesRegex(ValueError, 'Unsupported type', w.ex, u)

        # SymPy function without Myokit equivalent --> Should raise exception
        cu = sympy.principal_branch(cx, cc)
        self.assertRaisesRegex(ValueError, 'Unsupported type', r.ex, cu)

        # Derivative
        avar.promote(4)
        x = myokit.Derivative(myokit.Name(avar))
        cx = sympy.symbols('dot(c.a)')
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Equation
        e = myokit.Equation(a, b)
        ce = sympy.Eq(ca, cb)
        self.assertEqual(w.eq(e), ce)
        # There's no backwards equivalent for this!
        # The ereader can handle it, but it becomes and Equals expression.

    def test_access_via_myokit_formats(self):
        """
        Test fetching using formats.ewriter.
        """

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('sympy')
        self.assertIsInstance(w, myokit.formats.sympy.SymPyExpressionWriter)


if __name__ == '__main__':
    unittest.main()
