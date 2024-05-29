#!/usr/bin/env python3
#
# Tests the DiffSL module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import unittest

import myokit
import myokit.formats
import myokit.formats.diffsl
import myokit.tests
from myokit import (Abs, ACos, And, ASin, ATan, Ceil, Cos, Divide, Equal, Exp,
                    Floor, If, Less, LessEqual, Log, Log10, Minus, More,
                    MoreEqual, Multiply, Not, NotEqual, Number, Or, Piecewise,
                    Plus, Power, PrefixMinus, PrefixPlus, Quotient, Remainder,
                    Sin, Sqrt, Tan)
from myokit.tests import DIR_DATA, TemporaryDirectory, WarningCollector


class DiffSLExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """Test conversion to DiffSL syntax."""

    _name = 'diffsl'
    _target = myokit.formats.diffsl.DiffSLExpressionWriter

    def test_number(self):
        self.eq(Number(1), '1.0')
        self.eq(Number(-2), '-2.0')
        self.eq(Number(13, 'mV'), '13.0')

    def test_name(self):
        # Inherited from CBasedExpressionWriter
        self.eq(self.a, 'a')
        w = self._target()
        w.set_lhs_function(lambda v: v.var().qname().upper())
        self.assertEqual(w.ex(self.a), 'COMP.A')

    def test_derivative(self):
        # Inherited from CBasedExpressionWriter
        self.eq(myokit.Derivative(self.a), 'dadt')

    def test_partial_derivative(self):
        e = myokit.PartialDerivative(self.a, self.b)
        self.assertRaisesRegex(NotImplementedError, 'Partial', self.w.ex, e)

    def test_initial_value(self):
        e = myokit.InitialValue(self.a)
        self.assertRaisesRegex(NotImplementedError, 'Initial', self.w.ex, e)

    def test_prefix_plus_minus(self):
        # Inherited from CBasedExpressionWriter
        p = Number(11, 'kV')
        a, b, c = self.abc
        self.eq(PrefixPlus(p), '+11.0')
        self.eq(PrefixPlus(PrefixPlus(PrefixPlus(p))), '+(+(+11.0))')
        self.eq(Divide(PrefixPlus(Plus(a, b)), c), '+(a + b) / c')
        self.eq(PrefixMinus(p), '-11.0')
        self.eq(PrefixMinus(PrefixMinus(p)), '-(-11.0)')
        self.eq(PrefixMinus(Number(-1)), '-(-1.0)')
        self.eq(PrefixMinus(Minus(a, b)), '-(a - b)')
        self.eq(Multiply(PrefixMinus(Plus(b, a)), c), '-(b + a) * c')
        self.eq(PrefixMinus(Divide(b, a)), '-(b / a)')

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

        # No expm in DiffSL
        self.eq(Minus(Exp(Number(2)), Number(1)), 'exp(2.0) - 1.0')
        self.eq(Minus(Number(1), Exp(Number(3))), '1.0 - exp(3.0)')

    def test_multiply_divide(self):
        # Inherited from CBasedExpressionWriter
        a, b, c = self.abc
        self.eq(Multiply(a, b), 'a * b')
        self.eq(Multiply(Multiply(a, b), c), 'a * b * c')
        self.eq(Multiply(a, Multiply(b, c)), 'a * (b * c)')
        self.eq(Divide(a, b), 'a / b')
        self.eq(Divide(Divide(a, b), c), 'a / b / c')
        self.eq(Divide(a, Divide(b, c)), 'a / (b / c)')

    def test_quotient(self):
        # Inherited from CBasedExpressionWriter
        a, b, c = self.abc
        with WarningCollector():
            self.eq(Quotient(a, b), 'floor(a / b)')
            self.eq(Quotient(Plus(a, c), b), 'floor((a + c) / b)')
            self.eq(Quotient(Divide(a, c), b), 'floor(a / c / b)')
            self.eq(Quotient(a, Divide(b, c)), 'floor(a / (b / c))')
            self.eq(Multiply(Quotient(a, b), c), 'floor(a / b) * c')
            self.eq(Multiply(c, Quotient(a, b)), 'c * (floor(a / b))')

    def test_remainder(self):
        # Inherited from CBasedExpressionWriter
        a, b, c = self.abc
        with WarningCollector():
            self.eq(Remainder(a, b), '(a - b * floor(a / b))')
            self.eq(Remainder(Plus(a, c), b),
                    '(a + c - b * floor((a + c) / b))')
            self.eq(Multiply(Remainder(a, b), c), '(a - b * floor(a / b)) * c')
            self.eq(Divide(c, Remainder(b, a)), 'c / ((b - a * floor(b / a)))')

    def test_power(self):
        # Inherited from CBasedExpressionWriter
        a, b, c = self.abc
        self.eq(Power(a, b), 'pow(a, b)')
        self.eq(Power(Power(a, b), c), 'pow(pow(a, b), c)')
        self.eq(Power(a, Power(b, c)), 'pow(a, pow(b, c))')

    def test_log(self):
        # Inherited from CBasedExpressionWriter
        a, b = self.ab
        self.eq(Log(a), 'log(a)')
        self.eq(Log10(a), '(log(a) / log(10.0))')
        self.eq(Log(a, b), '(log(a) / log(b))')

    def test_supported_functions(self):
        a = self.a

        self.eq(Abs(a), 'abs(a)')
        self.eq(Cos(a), 'cos(a)')
        self.eq(Exp(a), 'exp(a)')
        self.eq(Log(a), 'log(a)')
        self.eq(Sin(a), 'sin(a)')
        self.eq(Sqrt(a), 'sqrt(a)')
        self.eq(Tan(a), 'tan(a)')

    def test_unsupported_functions(self):
        a = self.a

        with WarningCollector() as wc:
            self.eq(ACos(a), 'acos(a)')
        self.assertIn('Unsupported', wc.text())

        with WarningCollector() as wc:
            self.eq(ASin(a), 'asin(a)')
        self.assertIn('Unsupported', wc.text())

        with WarningCollector() as wc:
            self.eq(ATan(a), 'atan(a)')
        self.assertIn('Unsupported', wc.text())

        with WarningCollector() as wc:
            self.eq(Ceil(a), 'ceil(a)')
        self.assertIn('Unsupported', wc.text())

        with WarningCollector() as wc:
            self.eq(Floor(a), 'floor(a)')
        self.assertIn('Unsupported', wc.text())

    def test_boolean_operators(self):
        a, b = self.ab

        self.eq(And(a, b),
                '((1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))')

        self.eq(Equal(a, b),
                '(heaviside(a - b) * heaviside(b - a))')

        self.eq(Less(a, b),
                '(1 - heaviside(a - b))')

        self.eq(LessEqual(a, b),
                '(1 - (heaviside(a - b) * (1 - (heaviside(a - b) * heaviside(b - a)))))')

        self.eq(More(a, b),
                '(heaviside(a - b) * (1 - (heaviside(a - b) * heaviside(b - a))))')

        self.eq(MoreEqual(a, b),
                'heaviside(a - b)')

        self.eq(Not(a),
                '(heaviside(a) * heaviside(-a))')

        self.eq(NotEqual(a, b),
                '(1 - (heaviside(a - b) * heaviside(b - a)))')

        self.eq(Or(a, b),
                '((1 - heaviside(a) * heaviside(-a)) + (1 - heaviside(b) * heaviside(-b)) - (1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))')

    def test_if_expressions(self):
        a, b, c, d = self.abcd

        self.eq(If(a, c, d),
                '(c + heaviside(a) * heaviside(-a) * (d - c))')

        self.eq(If(Or(a, b), c, d),
                '(c + heaviside(((1 - heaviside(a) * heaviside(-a)) + (1 - heaviside(b) * heaviside(-b)) - (1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))) * heaviside(-((1 - heaviside(a) * heaviside(-a)) + (1 - heaviside(b) * heaviside(-b)) - (1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))) * (d - c))')

        self.eq(If(And(a, b), c, d),
                '(c + heaviside(((1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))) * heaviside(-((1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))) * (d - c))')

        self.eq(If(Not(a), c, d),
                '(d + heaviside(a) * heaviside(-a) * (c - d))')

        self.eq(If(Equal(a, b), c, d),
                '(d + heaviside(a - b) * heaviside(b - a) * (c - d))')

        self.eq(If(NotEqual(a, b), c, d),
                '(c + heaviside(a - b) * heaviside(b - a) * (d - c))')

        self.eq(If(More(a, b), c, d),
                '(c + heaviside(b - a) * (d - c))')

        self.eq(If(MoreEqual(a, b), c, d),
                '(d + heaviside(a - b) * (c - d))')

        self.eq(If(Less(a, b), c, d),
                '(c + heaviside(a - b) * (d - c))')

        self.eq(If(LessEqual(a, b), c, d),
                '(d + heaviside(b - a) * (c - d))')

    def test_piecewise_expressions(self):
        a, b, c, d = self.abcd

        self.eq(Piecewise(a, c, d),
                '(c + heaviside(a) * heaviside(-a) * (d - c))')

        self.eq(Piecewise(Or(a, b), c, d),
                '(c + heaviside(((1 - heaviside(a) * heaviside(-a)) + (1 - heaviside(b) * heaviside(-b)) - (1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))) * heaviside(-((1 - heaviside(a) * heaviside(-a)) + (1 - heaviside(b) * heaviside(-b)) - (1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))) * (d - c))')

        self.eq(Piecewise(And(a, b), c, d),
                '(c + heaviside(((1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))) * heaviside(-((1 - heaviside(a) * heaviside(-a)) * (1 - heaviside(b) * heaviside(-b)))) * (d - c))')

        self.eq(Piecewise(Not(a), c, d),
                '(d + heaviside(a) * heaviside(-a) * (c - d))')

        self.eq(Piecewise(Equal(a, b), c, d),
                '(d + heaviside(a - b) * heaviside(b - a) * (c - d))')

        self.eq(Piecewise(NotEqual(a, b), c, d),
                '(c + heaviside(a - b) * heaviside(b - a) * (d - c))')

        self.eq(Piecewise(More(a, b), c, d),
                '(c + heaviside(b - a) * (d - c))')

        self.eq(Piecewise(MoreEqual(a, b), c, d),
                '(d + heaviside(a - b) * (c - d))')

        self.eq(Piecewise(Less(a, b), c, d),
                '(c + heaviside(a - b) * (d - c))')

        self.eq(Piecewise(LessEqual(a, b), c, d),
                '(d + heaviside(b - a) * (c - d))')

        self.eq(Piecewise(Equal(a, b), c, Equal(a, d), Number(3), Number(4)),
                '((4.0 + heaviside(a - d) * heaviside(d - a) * (3.0 - 4.0)) + heaviside(a - b) * heaviside(b - a) * (c - (4.0 + heaviside(a - d) * heaviside(d - a) * (3.0 - 4.0))))')

        self.eq(Piecewise(a, b, c, d, Number(4)),
                '(b + heaviside(a) * heaviside(-a) * ((d + heaviside(c) * heaviside(-c) * (4.0 - d)) - b))')


if __name__ == '__main__':
    unittest.main()
