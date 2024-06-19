#!/usr/bin/env python3
#
# Tests writing of AnsiC expressions, as used by the Simulation.
# C++ tests are lumped in as well.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import math
import unittest

import myokit
import myokit.formats.ansic
import myokit.formats.cpp

from myokit import (
    Number, PrefixPlus, PrefixMinus, Plus, Minus,
    Multiply, Divide, Quotient, Remainder, Power, Sqrt,
    Exp, Log, Log10, Sin, Cos, Tan, ASin, ACos, ATan, Floor, Ceil, Abs,
    Not, And, Or, Equal, NotEqual, More, Less, MoreEqual, LessEqual,
    If, Piecewise,
)

import myokit.tests


class AnsiCExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """
    Test conversion to Ansi C, as used by the Simulation.
    Numerical tests are provided by composing and evaluating a single RHS.
    """
    _name = 'ansic'
    _target = myokit.formats.ansic.AnsiCExpressionWriter

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
        self.eq(myokit.PartialDerivative(self.a, self.b), 'partial(a, b)')

    def test_initial_value(self):
        self.eq(myokit.InitialValue(self.a), 'initial(a)')

    def test_prefix_plus(self):
        # Test with numbers
        p = Number(11, 'kV')
        self.eq(PrefixPlus(p), '+11.0')
        self.eq(PrefixPlus(PrefixPlus(p)), '+(+11.0)')
        self.eq(PrefixPlus(PrefixPlus(PrefixPlus(p))), '+(+(+11.0))')
        self.eq(PrefixPlus(Number('+1')), '+1.0')

        # Test with operators of precedence SUM, PRODUCT
        a, b, c = self.abc
        self.eq(PrefixPlus(Plus(a, b)), '+(a + b)')
        self.eq(Divide(PrefixPlus(Plus(a, b)), c), '+(a + b) / c')
        self.eq(PrefixPlus(Divide(b, a)), '+(b / a)')

    def test_prefix_minus(self):
        # Test with numbers
        p = Number(11, 'kV')
        self.eq(PrefixMinus(p), '-11.0')
        self.eq(PrefixMinus(PrefixMinus(p)), '-(-11.0)')
        self.eq(PrefixMinus(Number(-1)), '-(-1.0)')
        self.eq(PrefixMinus(PrefixMinus(Number(-2))), '-(-(-2.0))')

        # Test with operators of precedence SUM, PRODUCT
        a, b, c = self.abc
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
        self.eq(Remainder(a, b), '(a - b * floor(a / b))')
        self.eq(Remainder(Plus(a, c), b), '(a + c - b * floor((a + c) / b))')
        self.eq(Multiply(Remainder(a, b), c), '(a - b * floor(a / b)) * c')
        # Bracket() method expects a PRODUCT level operation, so will add
        # unnecessary brackets here
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
        self.eq(Abs(a), 'fabs(a)')

    def test_conditions(self):
        a, b, c, d = self.abcd
        p = myokit.Equal(a, b)
        q = myokit.NotEqual(c, d)

        self.eq(And(p, q), '((a == b) && (c != d))')
        self.eq(Or(q, p), '((c != d) || (a == b))')
        self.eq(Not(And(p, q)), '(!((a == b) && (c != d)))')
        self.eq(Not(p), '(!(a == b))')

        self.eq(Equal(a, b), '(a == b)')
        self.eq(NotEqual(a, b), '(a != b)')
        self.eq(More(b, a), '(b > a)')
        self.eq(Less(d, c), '(d < c)')
        self.eq(MoreEqual(c, a), '(c >= a)')
        self.eq(LessEqual(b, d), '(b <= d)')

        self.eq(And(Equal(a, b), NotEqual(c, d)), '((a == b) && (c != d))')
        self.eq(Or(More(d, c), Less(b, a)), '((d > c) || (b < a))')

    def test_conditionals(self):

        a, b, c, d = self.abcd
        self.eq(If(Equal(a, b), d, c), '((a == b) ? d : c)')
        self.eq(Piecewise(NotEqual(d, c), b, a), '((d != c) ? b : a)')
        self.eq(Piecewise(Equal(a, b), c, Equal(a, d), Number(3), Number(4)),
                '((a == b) ? c : ((a == d) ? 3.0 : 4.0))')

        # Using if-then-else function
        w = self._target()
        w.set_lhs_function(lambda v: v.var().name())
        w.set_condition_function('ite')

        self.assertEqual(w.ex(If(More(b, a), c, d)), 'ite((b > a), c, d)')
        self.assertEqual(w.ex(Piecewise(Less(d, c), b, a)),
                         'ite((d < c), b, a)')
        self.assertEqual(w.ex(
            Piecewise(Equal(a, b), c, Equal(a, d), Number(3), Number(4))),
            'ite((a == b), c, ite((a == d), 3.0, 4.0))')

    def test_in_c(self):
        """ Compile and test the values evaluated in C. """

        class CTester():
            def __init__(self, parent):
                self._parent = parent
                self._m = myokit.Model()
                self._c = self._m.add_component('c')
                t = self._c.add_variable('time', rhs=0, binding='time')
                self._expected = []

            def add(self, expression, expected):
                v = self._c.add_variable(
                    f'v{len(self._expected)}', rhs=expression, initial_value=0)
                self._expected.append(float(expected))

            def run(self):
                s = myokit.Simulation(self._m)
                x = s.evaluate_derivatives()
                self._parent.assertEqual(len(x), len(self._expected))
                for a, b in zip(x, self._expected):
                    self._parent.assertEqual(a, b)

        c = CTester(self,)

        c.add(Number(12, 'pF'), 12)

        c.add(PrefixPlus(Number(3)), 3)
        c.add(PrefixPlus(PrefixPlus(PrefixPlus(Number(4)))), 4)
        c.add(PrefixMinus(Number(6)), -6)
        c.add(PrefixMinus(PrefixMinus(Number(2))), 2)
        c.add(PrefixMinus(PrefixMinus(PrefixMinus(Number(5)))), -5)
        c.add(PrefixMinus(PrefixMinus(PrefixMinus(Number(-5)))), 5)

        c.add(Plus(Number(4), Number(2)), 6)
        c.add(Minus(Number(5), Number(1.5)), 3.5)

        c.add(Multiply(Number(7), Number(9)), 63)
        c.add(Divide(Number(5), Number(2)), 2.5)
        c.add(Divide(Divide(Number(12), Number(2)), Number(2)), 3)
        c.add(Divide(Number(1), Divide(Number(2), Number(3))), 1.5)

        c.add(Remainder(Number(10), Number(4)), 2)
        c.add(Remainder(Number(10), Number(6)), 4)
        c.add(Remainder(Number(5), Number(3)), 2)
        c.add(Remainder(Number(-5), Number(3)), 1)
        c.add(Remainder(Number(5), Number(-3)), -1)
        c.add(Remainder(Number(-5), Number(-3)), -2)

        c.add(Quotient(Number(10), Number(4)), 2)
        c.add(Quotient(Number(10), Number(6)), 1)
        c.add(Quotient(Number(5), Number(3)), 1)
        c.add(Quotient(Number(-5), Number(3)), -2)
        c.add(Quotient(Number(5), Number(-3)), -2)
        c.add(Quotient(Number(-5), Number(-3)), 1)

        c.add(Power(Number(4), Power(Number(2), Number(3))), 65536)
        c.add(Power(Power(Number(2), Number(3)), Number(4)), 4096)

        c.add(Log(Number(3)), math.log(3))
        c.add(Log10(Number(1000)), 3)
        c.add(Log10(Number(0.01)), -2)
        c.add(Log(Number(27), Number(3)), 3)
        c.add(Divide(Number(12), Log(Number(256), Number(4))), 3)
        c.add(Divide(Log(Number(256), Number(4)), Number(4)), 1)

        c.add(Sqrt(Number(9)), 3)
        c.add(Exp(Number(3)), math.exp(3))
        c.add(Sin(Number(1)), math.sin(1))
        c.add(Cos(Number(1)), math.cos(1))
        c.add(Tan(Number(4)), math.tan(4))
        c.add(ASin(Number(0.4)), math.asin(0.4))
        c.add(ACos(Number(0.4)), math.acos(0.4))
        c.add(ATan(Number(0.4)), math.atan(0.4))

        c.add(Floor(Number(3.9)), 3)
        c.add(Floor(Number(-3.9)), -4)
        c.add(Ceil(Number(4.01)), 5)
        c.add(Ceil(Number(-4.01)), -4)
        c.add(Abs(PrefixMinus(Number(12))), 12)
        c.add(Abs(Number(-13)), 13)

        true = Equal(Number(2), Number(2))
        false = Equal(Number(3), Number(-1))
        a, b = Number(10), Number(20)
        c.add(If(true, a, b), 10)
        c.add(If(false, a, b), 20)

        c.add(If(More(Number(5), Number(3)), a, b), 10)
        c.add(If(More(Number(3), Number(3)), a, b), 20)
        c.add(If(MoreEqual(Number(3), Number(3)), a, b), 10)
        c.add(If(Less(Number(3), Number(5)), a, b), 10)
        c.add(If(More(Number(3), Number(3)), a, b), 20)
        c.add(If(LessEqual(Number(3), Number(3)), a, b), 10)

        c.add(If(And(false, false), a, b), 20)
        c.add(If(And(false, true), a, b), 20)
        c.add(If(And(true, false), a, b), 20)
        c.add(If(And(true, true), a, b), 10)
        c.add(If(Or(false, false), a, b), 20)
        c.add(If(Or(false, true), a, b), 10)
        c.add(If(Or(true, false), a, b), 10)
        c.add(If(Or(true, true), a, b), 10)
        c.add(If(Not(true), a, b), 20)
        c.add(If(Not(false), a, b), 10)

        c.add(Piecewise(true, Number(10), false, Number(20), Number(30)), 10)
        c.add(Piecewise(true, Number(10), true, Number(20), Number(30)), 10)
        c.add(Piecewise(false, Number(10), true, Number(20), Number(30)), 20)
        c.add(Piecewise(false, Number(10), false, Number(20), Number(30)), 30)

        c.run()


if __name__ == '__main__':
    unittest.main()
