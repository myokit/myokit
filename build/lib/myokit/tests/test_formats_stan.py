#!/usr/bin/env python3
#
# Tests writing of Stan equations.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit
import myokit.formats.stan

from myokit import (
    Number, PrefixPlus, PrefixMinus, Plus, Minus,
    Multiply, Divide, Quotient, Remainder, Power, Sqrt,
    Exp, Log, Log10, Sin, Cos, Tan, ASin, ACos, ATan, Floor, Ceil, Abs,
    Not, And, Or, Equal, NotEqual, More, Less, MoreEqual, LessEqual,
    If, Piecewise,
)

import myokit.tests


class StanExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """ Test conversion of expressions to Stan. """
    _name = 'stan'
    _target = myokit.formats.stan.StanExpressionWriter

    def test_number(self):
        self.eq(Number(1), '1.0')
        self.eq(Number(-1.3274924373284374), '-1.32749243732843736e+00')
        self.eq(Number(+1.3274924373284374), '1.32749243732843736e+00')
        self.eq(Number(-2), '-2.0')
        self.eq(Number(13, 'mV'), '13.0')

    def test_name(self):
        self.eq(self.a, 'a')
        w = self._target()
        w.set_lhs_function(lambda v: v.var().qname().upper())
        self.assertEqual(w.ex(self.a), 'COMP.A')

    def test_derivative(self):
        self.eq(myokit.Derivative(self.a), 'dot(a)')

    def test_partial_derivative(self):
        e = myokit.PartialDerivative(self.a, self.b)
        self.assertRaisesRegex(NotImplementedError, 'Partial', self.w.ex, e)

    def test_initial_value(self):
        e = myokit.InitialValue(self.a)
        self.assertRaisesRegex(NotImplementedError, 'Initial', self.w.ex, e)

    def test_prefix_plus_minus(self):
        # Test with numbers
        p = Number(11, 'kV')
        self.eq(PrefixPlus(p), '+11.0')
        self.eq(PrefixPlus(PrefixPlus(p)), '++11.0')
        self.eq(PrefixMinus(p), '-11.0')
        self.eq(PrefixMinus(PrefixMinus(p)), '--11.0')
        self.eq(PrefixMinus(Number(-1)), '--1.0')

        a, b, c = self.abc
        self.eq(PrefixMinus(Plus(a, b)), '-(a + b)')
        self.eq(Divide(PrefixPlus(Plus(a, b)), c), '+(a + b) / c')
        self.eq(Power(PrefixMinus(a), b), '(-a)^b')
        self.eq(Power(PrefixPlus(Power(b, a)), c), '(+b^a)^c')
        self.eq(Power(a, PrefixMinus(Power(b, c))), 'a^(-b^c)')

    def test_plus_minus(self):
        a, b, c = self.abc
        self.eq(Plus(a, b), 'a + b')
        self.eq(Plus(Plus(a, b), c), 'a + b + c')
        self.eq(Plus(a, Plus(b, c)), 'a + (b + c)')
        self.eq(Minus(a, b), 'a - b')
        self.eq(Minus(Minus(a, b), c), 'a - b - c')
        self.eq(Minus(a, Minus(b, c)), 'a - (b - c)')
        self.eq(Minus(a, b), 'a - b')
        self.eq(Plus(Minus(a, b), c), 'a - b + c')
        self.eq(Minus(a, Plus(b, c)), 'a - (b + c)')
        self.eq(Minus(Plus(a, b), c), 'a + b - c')
        self.eq(Minus(a, Plus(b, c)), 'a - (b + c)')

    def test_multiply_divide(self):
        a, b, c = self.abc
        self.eq(Multiply(a, b), 'a * b')
        self.eq(Multiply(Multiply(a, b), c), 'a * b * c')
        self.eq(Multiply(a, Multiply(b, c)), 'a * (b * c)')
        self.eq(Divide(a, b), 'a / b')
        self.eq(Divide(Divide(a, b), c), 'a / b / c')
        self.eq(Divide(a, Divide(b, c)), 'a / (b / c)')

        self.eq(Divide(Multiply(a, b), c), 'a * b / c')
        self.eq(Multiply(Divide(a, b), c), 'a / b * c')
        self.eq(Divide(a, Multiply(b, c)), 'a / (b * c)')
        self.eq(Multiply(a, Divide(b, c)), 'a * (b / c)')

        self.eq(Multiply(Minus(a, b), c), '(a - b) * c')
        self.eq(Divide(a, Plus(b, c)), 'a / (b + c)')
        self.eq(Minus(Multiply(a, b), c), 'a * b - c')
        self.eq(Plus(a, Divide(b, c)), 'a + b / c')

    def test_quotient_remainder(self):
        a, b, c = self.abc

        self.eq(Quotient(c, a), 'floor(c / a)')
        self.eq(Remainder(c, a), '(c - a * floor(c / a))')

    def test_power(self):
        a, b, c = self.abc
        self.eq(Power(a, b), 'a^b')
        self.eq(Power(Plus(a, b), c), '(a + b)^c')
        self.eq(Power(a, Minus(b, c)), 'a^(b - c)')
        self.eq(Power(Multiply(a, b), c), '(a * b)^c')
        self.eq(Power(a, Divide(b, c)), 'a^(b / c)')

        # Stan has a right-associative power operator, so must add brackets
        # to get Myokit behavuour
        self.eq(Power(Power(a, b), c), '(a^b)^c')
        self.eq(Power(a, Power(b, c)), 'a^b^c')

    def test_functions(self):
        a, b = self.ab

        self.eq(Sqrt(a), 'sqrt(a)')
        self.eq(Exp(a), 'exp(a)')
        self.eq(Log(a), 'log(a)')
        self.eq(Log(a, b), '(log(a) / log(b))')
        self.eq(Log10(a), 'log10(a)')
        self.eq(Sin(a), 'sin(a)')
        self.eq(Cos(a), 'cos(a)')
        self.eq(Tan(a), 'tan(a)')
        self.eq(ASin(a), 'asin(a)')
        self.eq(ACos(a), 'acos(a)')
        self.eq(ATan(a), 'atan(a)')
        self.eq(Floor(a), 'floor(a)')
        self.eq(Ceil(a), 'ceil(a)')
        self.eq(Abs(a), 'abs(a)')

    def test_conditions(self):
        a, b, c, d = self.abcd

        self.eq(Equal(a, b), '(a == b)')
        self.eq(NotEqual(a, b), '(a != b)')
        self.eq(More(b, a), '(b > a)')
        self.eq(Less(d, c), '(d < c)')
        self.eq(MoreEqual(c, a), '(c >= a)')
        self.eq(LessEqual(b, d), '(b <= d)')

        self.eq(And(Equal(a, b), NotEqual(c, d)), '((a == b) && (c != d))')
        self.eq(Or(More(d, c), Less(b, a)), '((d > c) || (b < a))')
        self.eq(Not(Equal(d, d)), '(!(d == d))')

    def test_conditionals(self):
        a, b, c, d = self.abcd
        self.eq(If(Equal(a, b), d, c), '((a == b) ? d : c)')
        self.eq(Piecewise(NotEqual(d, c), b, a), '((d != c) ? b : a)')
        self.eq(Piecewise(Equal(a, b), c, Equal(a, d), Number(3), Number(4)),
                '((a == b) ? c : ((a == d) ? 3.0 : 4.0))')


if __name__ == '__main__':
    unittest.main()
