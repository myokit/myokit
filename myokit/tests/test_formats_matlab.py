#!/usr/bin/env python3
#
# Tests the expression writer for Matlab.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit
import myokit.formats.matlab

from myokit import (
    Number, PrefixPlus, PrefixMinus, Plus, Minus,
    Multiply, Divide, Quotient, Remainder, Power, Sqrt,
    Exp, Log, Log10, Sin, Cos, Tan, ASin, ACos, ATan, Floor, Ceil, Abs,
    Not, And, Or, Equal, NotEqual, More, Less, MoreEqual, LessEqual,
    If, Piecewise,
)

import myokit.tests


class MatlabExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    _name = 'matlab'
    _target = myokit.formats.matlab.MatlabExpressionWriter

    def test_number(self):
        self.eq(Number(1), '1.0')
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

    def test_prefix_plus(self):
        # Inherited from Python writer
        # Test with numbers
        p = Number(11, 'kV')
        self.eq(PrefixPlus(p), '+11.0')
        self.eq(PrefixPlus(PrefixPlus(p)), '++11.0')
        self.eq(PrefixPlus(Number('+1')), '+1.0')

        a, b, c = self.abc
        self.eq(PrefixPlus(Plus(a, b)), '+(a + b)')
        self.eq(Divide(PrefixPlus(Plus(a, b)), c), '+(a + b) / c')
        self.eq(Power(PrefixPlus(a), b), '(+a)^b')

    def test_prefix_minus(self):
        # Inherited from Python writer
        # Test with numbers
        p = Number(11, 'kV')
        self.eq(PrefixMinus(p), '-11.0')
        self.eq(PrefixMinus(PrefixMinus(p)), '--11.0')
        self.eq(PrefixMinus(Number(-1)), '--1.0')

        a, b, c = self.abc
        self.eq(PrefixMinus(Minus(a, b)), '-(a - b)')
        self.eq(Multiply(PrefixMinus(Plus(b, a)), c), '-(b + a) * c')
        self.eq(Power(PrefixMinus(a), b), '(-a)^b')

    def test_plus_minus(self):
        # Inherited from Python writer
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
        # Inherited from Python writer

        a, b, c = self.abc
        self.eq(Multiply(a, b), 'a * b')
        # Left-to-right, so (a * b) * c is the same as a * b * c...
        self.eq(Multiply(Multiply(a, b), c), 'a * b * c')
        # ...but order-of-operations-wise, a * (b * c) is different!
        self.eq(Multiply(a, Multiply(b, c)), 'a * (b * c)')
        # Note that a user typing a * b * c results in (a * b) * c

        self.eq(Divide(a, b), 'a / b')
        self.eq(Divide(Divide(a, b), c), 'a / b / c')
        self.eq(Divide(a, Divide(b, c)), 'a / (b / c)')

        self.eq(Divide(Multiply(a, b), c), 'a * b / c')
        self.eq(Multiply(Divide(a, b), c), 'a / b * c')
        self.eq(Divide(a, Multiply(b, c)), 'a / (b * c)')
        self.eq(Multiply(a, Divide(b, c)), 'a * (b / c)')

        self.eq(Multiply(Minus(a, b), c), '(a - b) * c')
        self.eq(Multiply(a, Plus(b, c)), 'a * (b + c)')
        self.eq(Minus(Multiply(a, b), c), 'a * b - c')
        self.eq(Plus(a, Multiply(b, c)), 'a + b * c')
        self.eq(Divide(Plus(a, b), c), '(a + b) / c')
        self.eq(Divide(a, Minus(b, c)), 'a / (b - c)')
        self.eq(Plus(Divide(a, b), c), 'a / b + c')
        self.eq(Minus(a, Divide(b, c)), 'a - b / c')
        self.eq(Divide(a, Divide(b, c)), 'a / (b / c)')
        self.eq(Divide(Divide(a, b), c), 'a / b / c')

    def test_quotient(self):
        a, b, c = self.abc
        self.eq(Quotient(a, b), 'floor(a / b)')
        self.eq(Quotient(Plus(a, c), b), 'floor((a + c) / b)')
        self.eq(Quotient(Divide(a, c), b), 'floor(a / c / b)')
        self.eq(Quotient(a, Divide(b, c)), 'floor(a / (b / c))')
        self.eq(Multiply(Quotient(a, b), c), 'floor(a / b) * c')
        # Bracket() method expects a PRODUCT level operation, so will add
        # unnecessary brackets here
        self.eq(Multiply(c, Quotient(a, b)), 'c * (floor(a / b))')

    def test_remainder(self):
        a, b, c = self.abc
        self.eq(Remainder(a, b), 'mod(a, b)')
        self.eq(Remainder(Plus(a, c), b), 'mod(a + c, b)')
        self.eq(Multiply(Remainder(a, b), c), 'mod(a, b) * c')
        # Bracket() method expects a PRODUCT level operation, so will add
        # unnecessary brackets here
        self.eq(Divide(c, Remainder(b, a)), 'c / (mod(b, a))')

    def test_power(self):
        a, b, c = self.abc
        self.eq(Power(a, b), 'a^b')

        # Like Myokit, Matlab sees a^b^c as (a^b)^c
        self.eq(Power(Power(a, b), c), 'a^b^c')
        self.eq(Power(a, Power(b, c)), 'a^(b^c)')

        self.eq(Power(Plus(a, b), c), '(a + b)^c')
        self.eq(Power(a, Minus(b, c)), 'a^(b - c)')
        self.eq(Power(Multiply(a, b), c), '(a * b)^c')
        self.eq(Power(a, Divide(b, c)), 'a^(b / c)')

    def test_log(self):
        a, b = self.ab
        self.eq(Log(a), 'log(a)')
        self.eq(Log10(a), 'log10(a)')
        self.eq(Log(a, b), '(log(a) / log(b))')

    def test_functions(self):
        a, b = self.ab
        self.eq(Sqrt(a), 'sqrt(a)')
        self.eq(Exp(a), 'exp(a)')
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
        self.eq(If(Equal(a, b), d, c), 'ifthenelse((a == b), d, c)')
        self.eq(Piecewise(NotEqual(d, c), b, a), 'ifthenelse((d != c), b, a)')
        self.eq(Piecewise(Equal(a, b), c, Equal(a, d), Number(3), Number(4)),
                'ifthenelse((a == b), c, ifthenelse((a == d), 3.0, 4.0))')

    def test_unset_condition_function(self):
        # No ternary operator, so matlab must always have an ifthenelse
        w = self._target()
        self.assertRaisesRegex(
            ValueError, 'needs a condition function',
            w.set_condition_function, None)
        self.assertRaisesRegex(
            ValueError, 'needs a condition function',
            w.set_condition_function, '')


if __name__ == '__main__':
    unittest.main()
