#!/usr/bin/env python3
#
# Tests the expression writer for C++.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit
import myokit.formats.cpp

import myokit.tests


class CppExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """
    Test the C++ expression writer.
    This inherits from Ansi C, only dropping support for initial values and
    partial derivatives.
    """
    _name = 'cpp'
    _target = myokit.formats.cpp.CppExpressionWriter

    def test_basics(self):
        # Test a few arbitrary expressions, just to check the inheritcance has
        # worked.
        a, b, c, d = self.abcd
        self.eq(myokit.Number(1), '1.0')
        self.eq(myokit.Number(13, 'mV'), '13.0')
        self.eq(myokit.Divide(myokit.PrefixPlus(myokit.Plus(a, b)), c),
                '+(a + b) / c')
        self.eq(myokit.Multiply(myokit.PrefixMinus(myokit.Plus(b, a)), c),
                '-(b + a) * c')
        self.eq(myokit.Multiply(myokit.Divide(a, b), c), 'a / b * c')
        self.eq(myokit.Divide(a, myokit.Multiply(b, c)), 'a / (b * c)')
        self.eq(myokit.Quotient(myokit.Divide(a, c), b), 'floor(a / c / b)')
        self.eq(myokit.ASin(a), 'asin(a)')
        self.eq(myokit.Power(myokit.PrefixMinus(a), b), 'pow(-a, b)')
        self.eq(myokit.Power(a, myokit.Minus(b, c)), 'pow(a, b - c)')
        self.eq(myokit.Power(myokit.Multiply(a, b), c), 'pow(a * b, c)')
        self.eq(myokit.Log(a, b), '(log(a) / log(b))')
        self.eq(myokit.Sin(a), 'sin(a)')
        self.eq(myokit.And(myokit.Equal(a, b), myokit.NotEqual(c, d)),
                '((a == b) && (c != d))')
        self.eq(myokit.Not(myokit.Less(myokit.Number(1), myokit.Number(2))),
                '(!(1.0 < 2.0))')
        self.eq(myokit.If(myokit.Equal(a, b), d, c), '((a == b) ? d : c)')

    def test_derivative(self):
        self.eq(myokit.Derivative(self.a), 'dot(a)')

    def test_partial_derivative(self):
        self.assertRaisesRegex(
            NotImplementedError, 'Partial',
            self.w.ex, myokit.PartialDerivative(self.a, self.b))

    def test_initial_value(self):
        self.assertRaisesRegex(
            NotImplementedError, 'Initial',
            self.w.ex, myokit.InitialValue(self.a))

    def test_conditionals(self):
        # Inherited from AnsiCExpressionWriter

        a, b, c, d = self.abcd
        self.eq(myokit.If(myokit.Equal(a, b), d, c), '((a == b) ? d : c)')
        self.eq(myokit.Piecewise(myokit.NotEqual(d, c), b, a),
                '((d != c) ? b : a)')
        self.eq(myokit.Piecewise(myokit.Equal(a, b), c,
                                 myokit.Equal(a, d), myokit.Number(3),
                                 myokit.Number(4)),
                '((a == b) ? c : ((a == d) ? 3.0 : 4.0))')

        # Using if-then-else function
        w = self._target()
        w.set_lhs_function(lambda v: v.var().name())
        w.set_condition_function('ite')

        self.assertEqual(w.ex(myokit.If(myokit.More(b, a), c, d)),
                         'ite((b > a), c, d)')
        self.assertEqual(w.ex(myokit.Piecewise(myokit.Less(d, c), b, a)),
                         'ite((d < c), b, a)')
        self.assertEqual(
            w.ex(myokit.Piecewise(myokit.Equal(a, b), c,
                                  myokit.Equal(a, d), myokit.Number(3),
                                  myokit.Number(4))),
            'ite((a == b), c, ite((a == d), 3.0, 4.0))')


if __name__ == '__main__':
    unittest.main()
