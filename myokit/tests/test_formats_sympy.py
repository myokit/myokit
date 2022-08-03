#!/usr/bin/env python3
#
# Tests the importers for various formats
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.formats.sympy as mypy

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class SymPyReadWriteTest(unittest.TestCase):
    """
    Tests the SymPy ewriter and ereader classes.
    """

    @classmethod
    def setUpClass(cls):
        # Create a model with a variable
        cls._model = myokit.Model()
        component = cls._model.add_component('c')
        bvar = component.add_variable('b')
        bvar.set_rhs(1.23)
        avar = component.add_variable('a')
        avar.set_rhs('b')
        cls._a = myokit.Name(avar)
        cls._b = myokit.Name(bvar)

    def test_reader_writer(self):
        # Test using the proper reader/writer
        try:
            import sympy as sp
        except ImportError:
            print('Sympy not found, skipping test.')
            return

        # Create writer and reader
        w = mypy.SymPyExpressionWriter()
        r = mypy.SymPyExpressionReader(self._model)

        # Name
        a = self._a
        ca = sp.Symbol('c.a')
        self.assertEqual(w.ex(a), ca)
        self.assertEqual(r.ex(ca), a)

        # Number with unit
        b = myokit.Number('12', 'pF')
        cb = sp.Float(12)
        self.assertEqual(w.ex(b), cb)
        # Note: Units are lost in sympy im/ex-port!
        #self.assertEqual(r.ex(cb), b)

        # Number without unit
        b = myokit.Number('12')
        cb = sp.Float(12)
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
        cx = sp.sqrt(ca)
        self.assertEqual(w.ex(x), cx)
        # Note: SymPy converts sqrt to power
        self.assertEqual(float(r.ex(cx)), float(x))

        # Exp
        x = myokit.Exp(a)
        cx = sp.exp(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Log(a)
        x = myokit.Log(a)
        cx = sp.log(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Log(a, b)
        x = myokit.Log(a, b)
        cx = sp.log(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(float(r.ex(cx)), float(x))

        # Log10
        x = myokit.Log10(b)
        cx = sp.log(cb, 10)
        self.assertEqual(w.ex(x), cx)
        self.assertAlmostEqual(float(r.ex(cx)), float(x))

        # Sin
        x = myokit.Sin(a)
        cx = sp.sin(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Cos
        x = myokit.Cos(a)
        cx = sp.cos(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Tan
        x = myokit.Tan(a)
        cx = sp.tan(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # ASin
        x = myokit.ASin(a)
        cx = sp.asin(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # ACos
        x = myokit.ACos(a)
        cx = sp.acos(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # ATan
        x = myokit.ATan(a)
        cx = sp.atan(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Floor
        x = myokit.Floor(a)
        cx = sp.floor(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Ceil
        x = myokit.Ceil(a)
        cx = sp.ceiling(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Abs
        x = myokit.Abs(a)
        cx = sp.Abs(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Equal
        x = myokit.Equal(a, b)
        cx = sp.Eq(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # NotEqual
        x = myokit.NotEqual(a, b)
        cx = sp.Ne(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # More
        x = myokit.More(a, b)
        cx = sp.Gt(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Less
        x = myokit.Less(a, b)
        cx = sp.Lt(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # MoreEqual
        x = myokit.MoreEqual(a, b)
        cx = sp.Ge(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # LessEqual
        x = myokit.LessEqual(a, b)
        cx = sp.Le(ca, cb)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Not
        x = myokit.Not(a)
        cx = sp.Not(ca)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # And
        cond1 = myokit.More(a, b)
        cond2 = myokit.Less(a, b)
        c1 = sp.Gt(ca, cb)
        c2 = sp.Lt(ca, cb)

        x = myokit.And(cond1, cond2)
        cx = sp.And(c1, c2)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Or
        x = myokit.Or(cond1, cond2)
        cx = sp.Or(c1, c2)
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # If
        # Note: sympy only does piecewise, not if
        x = myokit.If(cond1, a, b)
        cx = sp.Piecewise((ca, c1), (cb, True))
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x.piecewise())

        # Piecewise
        c = myokit.Number(1)
        cc = sp.Float(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        cx = sp.Piecewise((ca, c1), (cb, c2), (cc, True))
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Myokit piecewise's (like CellML's) always have a final True
        # condition (i.e. an 'else'). SymPy doesn't require this, so test if
        # we can import this --> It will add an "else 0"
        x = myokit.Piecewise(cond1, a, myokit.Number(0))
        cx = sp.Piecewise((ca, c1))
        self.assertEqual(r.ex(cx), x)

        # SymPy function without Myokit equivalent --> Should raise exception
        cu = sp.principal_branch(cx, cc)
        self.assertRaisesRegex(ValueError, 'Unsupported type', r.ex, cu)

        # Derivative
        m = self._model.clone()
        avar = m.get('c.a')
        r = mypy.SymPyExpressionReader(self._model)
        avar.promote(4)
        x = myokit.Derivative(self._a)
        cx = sp.symbols('dot(c.a)')
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r.ex(cx), x)

        # Equation
        e = myokit.Equation(a, b)
        ce = sp.Eq(ca, cb)
        self.assertEqual(w.eq(e), ce)
        # There's no backwards equivalent for this!
        # The ereader can handle it, but it becomes and Equals expression.

        # Test sympy division
        del m, avar, x, cx, e, ce
        a = self._model.get('c.a')
        b = self._model.get('c').add_variable('bbb')
        b.set_rhs('1 / a')
        e = b.rhs()
        ce = w.ex(b.rhs())
        e = r.ex(ce)
        self.assertEqual(
            e,
            myokit.Multiply(
                myokit.Number(1),
                myokit.Power(myokit.Name(a), myokit.Number(-1))
            )
        )

        # Test sympy negative numbers
        a = self._model.get('c.a')
        e1 = myokit.PrefixMinus(myokit.Name(a))
        ce = w.ex(e1)
        e2 = r.ex(ce)
        self.assertEqual(e1, e2)

    def test_read_write(self):
        # Test using the read() and write() methods
        try:
            import sympy as sp
        except ImportError:
            print('Sympy not found, skipping test.')
            return

        # Test writing and reading with a model
        a = self._a
        ca = sp.Symbol('c.a')
        self.assertEqual(mypy.write(a), ca)
        self.assertEqual(mypy.read(ca, self._model), a)

        # Test doing it again, with a different model
        m = myokit.Model()
        a = m.add_component('cc').add_variable('aa')
        a = myokit.Name(a)
        ca = sp.Symbol('cc.aa')
        self.assertEqual(mypy.write(a), ca)
        self.assertEqual(mypy.read(ca, m), a)

        # Test reading without a model
        b = myokit.Number('12')
        cb = sp.Float(12)
        self.assertEqual(mypy.write(b), cb)
        self.assertEqual(mypy.read(cb), b)

    def test_access_via_myokit_formats(self):
        # Test access via formats.ewriter.
        try:
            import sympy as sp
        except ImportError:
            print('Sympy not found, skipping test.')
            return
        del sp

        w = myokit.formats.ewriter('sympy')
        self.assertIsInstance(w, mypy.SymPyExpressionWriter)


if __name__ == '__main__':
    unittest.main()
