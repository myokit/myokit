#!/usr/bin/env python3
#
# Tests the expression writer for OpenCL.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit
import myokit.formats.opencl

from myokit import (
    Number, PrefixPlus, PrefixMinus, Plus, Minus,
    Multiply, Divide, Quotient, Remainder, Power, Sqrt,
    Exp, Log, Log10, Sin, Cos, Tan, ASin, ACos, ATan, Floor, Ceil, Abs,
    Not, And, Or, Equal, NotEqual, More, Less, MoreEqual, LessEqual,
    If, Piecewise,
)

import myokit.tests


class OpenCLExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """
    Test conversion to Ansi C, as used by the Simulation.
    Numerical tests are provided by composing and evaluating a single RHS.
    """
    _name = 'opencl'
    _target = myokit.formats.opencl.OpenCLExpressionWriter

    def test_number(self):
        self.eq(Number(1), '1.0f')
        self.eq(Number(-2), '-2.0f')
        self.eq(Number(13, 'mV'), '13.0f')

    def test_number_double(self):
        w = self._target(precision=myokit.DOUBLE_PRECISION)
        self.assertEqual(w.ex(Number(1)), '1.0')
        self.assertEqual(w.ex(Number(-2)), '-2.0')
        self.assertEqual(w.ex(Number(13, 'mV')), '13.0')

    def test_name(self):
        self.eq(self.a, 'a')
        w = self._target()
        w.set_lhs_function(lambda v: v.var().qname().upper())
        self.assertEqual(w.ex(self.a), 'COMP.A')

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

    def test_prefix_plus_minus(self):
        # Inherited from c-based

        p = Number(11, 'kV')
        self.eq(PrefixPlus(p), '+11.0f')
        self.eq(PrefixPlus(PrefixPlus(p)), '+(+11.0f)')
        self.eq(PrefixPlus(PrefixPlus(PrefixPlus(p))), '+(+(+11.0f))')
        self.eq(PrefixPlus(Number('+1')), '+1.0f')
        self.eq(PrefixMinus(p), '-11.0f')
        self.eq(PrefixMinus(PrefixMinus(p)), '-(-11.0f)')
        self.eq(PrefixMinus(Number(-1)), '-(-1.0f)')
        self.eq(PrefixMinus(PrefixMinus(Number(-2))), '-(-(-2.0f))')

        # Test with operators of precedence SUM, PRODUCT
        a, b, c = self.abc
        self.eq(PrefixPlus(Plus(a, b)), '+(a + b)')
        self.eq(Divide(PrefixPlus(Plus(a, b)), c), '+(a + b) / c')
        self.eq(PrefixPlus(Divide(b, a)), '+(b / a)')
        self.eq(PrefixMinus(Minus(a, b)), '-(a - b)')
        self.eq(Multiply(PrefixMinus(Plus(b, a)), c), '-(b + a) * c')
        self.eq(PrefixMinus(Divide(b, a)), '-(b / a)')

    def test_prefix_plus_minus_double(self):

        w = self._target(precision=myokit.DOUBLE_PRECISION)
        p = Number(3, 'mA')
        self.assertEqual(w.ex(PrefixPlus(p)), '+3.0')
        self.assertEqual(w.ex(PrefixPlus(PrefixPlus(p))), '+(+3.0)')
        self.assertEqual(
            w.ex(PrefixPlus(PrefixPlus(PrefixPlus(p)))), '+(+(+3.0))')
        self.assertEqual(w.ex(PrefixPlus(Number('+1'))), '+1.0')
        self.assertEqual(w.ex(PrefixMinus(p)), '-3.0')
        self.assertEqual(w.ex(PrefixMinus(PrefixMinus(p))), '-(-3.0)')
        self.assertEqual(w.ex(PrefixMinus(Number(-1))), '-(-1.0)')
        self.assertEqual(
            w.ex(PrefixMinus(PrefixMinus(Number(-2)))), '-(-(-2.0))')

    def test_arithmetic(self):
        # Inherited from c-based

        a, b, c = self.abc
        self.eq(Minus(Plus(a, b), c), 'a + b - c')
        self.eq(Minus(a, Plus(b, c)), 'a - (b + c)')
        self.eq(Multiply(Minus(a, b), c), '(a - b) * c')
        self.eq(Multiply(a, Plus(b, c)), 'a * (b + c)')
        self.eq(Minus(Multiply(a, b), c), 'a * b - c')
        self.eq(Divide(a, Minus(b, c)), 'a / (b - c)')
        self.eq(Plus(Divide(a, b), c), 'a / b + c')
        self.eq(Divide(Divide(a, b), c), 'a / b / c')

    def test_quotient_remainder(self):
        # Inherited from c-based

        a, b, c = self.abc
        self.eq(Quotient(a, Divide(b, c)), 'floor(a / (b / c))')
        self.eq(Remainder(Plus(a, c), b), '(a + c - b * floor((a + c) / b))')
        self.eq(Divide(c, Remainder(b, a)), 'c / ((b - a * floor(b / a)))')

    def test_power(self):
        a, b, c = self.abc
        self.eq(Power(a, b), 'pow(a, b)')
        self.eq(Power(Power(a, b), c), 'pow(pow(a, b), c)')
        self.eq(Power(a, Power(b, c)), 'pow(a, pow(b, c))')

        self.eq(Power(Plus(a, b), c), 'pow(a + b, c)')
        self.eq(Power(a, Minus(b, c)), 'pow(a, b - c)')
        self.eq(Power(Multiply(a, b), c), 'pow(a * b, c)')
        self.eq(Power(a, Divide(b, c)), 'pow(a, b / c)')

    def test_log(self):
        a, b = self.ab
        self.eq(Log(a), 'native_log(a)')
        self.eq(Log10(a), 'native_log10(a)')
        self.eq(Log(a, b), '(native_log(a) / native_log(b))')

    def test_log_no_native(self):
        w = self._target(native_math=False)
        a, b = self.ab
        self.assertEqual(w.ex(Log(a)), 'log(comp.a)')
        self.assertEqual(w.ex(Log10(b)), 'log10(comp.b)')
        self.assertEqual(w.ex(Log(b, a)), '(log(comp.b) / log(comp.a))')

    def test_functions(self):
        a = self.a
        self.eq(Sqrt(self.a), 'native_sqrt(a)')
        self.eq(Exp(self.a), 'native_exp(a)')
        self.eq(Sin(self.a), 'native_sin(a)')
        self.eq(Cos(self.a), 'native_cos(a)')
        self.eq(Tan(self.a), 'native_tan(a)')
        self.eq(ASin(self.a), 'asin(a)')
        self.eq(ACos(self.a), 'acos(a)')
        self.eq(ATan(self.a), 'atan(a)')
        self.eq(Floor(self.a), 'floor(a)')
        self.eq(Ceil(self.a), 'ceil(a)')
        self.eq(Abs(self.a), 'fabs(a)')

    def test_functions_no_native(self):
        w = self._target(native_math=False)
        self.assertEqual(w.ex(Sqrt(self.a)), 'sqrt(comp.a)')
        self.assertEqual(w.ex(Exp(self.a)), 'exp(comp.a)')
        self.assertEqual(w.ex(Sin(self.a)), 'sin(comp.a)')
        self.assertEqual(w.ex(Cos(self.a)), 'cos(comp.a)')
        self.assertEqual(w.ex(Tan(self.a)), 'tan(comp.a)')
        self.assertEqual(w.ex(ASin(self.a)), 'asin(comp.a)')
        self.assertEqual(w.ex(ACos(self.a)), 'acos(comp.a)')
        self.assertEqual(w.ex(ATan(self.a)), 'atan(comp.a)')
        self.assertEqual(w.ex(Floor(self.a)), 'floor(comp.a)')
        self.assertEqual(w.ex(Ceil(self.a)), 'ceil(comp.a)')
        self.assertEqual(w.ex(Abs(self.a)), 'fabs(comp.a)')

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
        self.eq(Not(Less(Number(1), Number(2))), '(!(1.0f < 2.0f))')

    def test_conditionals(self):
        # Inherited from c-based

        a, b, c, d = self.abcd
        self.eq(If(Equal(a, b), d, c), '((a == b) ? d : c)')
        self.eq(Piecewise(NotEqual(d, c), b, a), '((d != c) ? b : a)')
        self.eq(Piecewise(Equal(a, b), c, Equal(a, d), Number(3), Number(4)),
                '((a == b) ? c : ((a == d) ? 3.0f : 4.0f))')


if __name__ == '__main__':
    unittest.main()
