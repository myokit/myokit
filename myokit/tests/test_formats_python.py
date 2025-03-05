#!/usr/bin/env python3
#
# Tests writing of Python and NumPy equations.
# These are used in pyfunc() and related, so numerical tests are possible and
# desirable.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import math
import unittest

import numpy

import myokit
import myokit.formats.python

from myokit import (
    Number, PrefixPlus, PrefixMinus, Plus, Minus,
    Multiply, Divide, Quotient, Remainder, Power, Sqrt,
    Exp, Log, Log10, Sin, Cos, Tan, ASin, ACos, ATan, Floor, Ceil, Abs,
    Not, And, Or, Equal, NotEqual, More, Less, MoreEqual, LessEqual,
    If, Piecewise,
)

import myokit.tests


class PythonExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """
    Test conversion of expressions to Python.
    This is used by pyfunc(), although that's usually done with the
    NumPyExpressionWriter instead.
    Numerical tests are provided.
    """
    _name = 'python'
    _target = myokit.formats.python.PythonExpressionWriter

    def py(self, expression, expected):
        """ Test by converting to Python and executing. """
        function = expression.pyfunc(use_numpy=False)
        value = function()
        self.assertEqual(value, expected)

    def test_number(self):
        self.eq(Number(1), '1.0')
        self.eq(Number(-1.3274924373284374), '-1.32749243732843736e+00')
        self.eq(Number(+1.3274924373284374), '1.32749243732843736e+00')
        self.eq(Number(-2), '-2.0')
        self.eq(Number(13, 'mV'), '13.0')
        self.py(Number(14, 'mV'), 14)

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
        # Test with numbers
        p = Number(11, 'kV')
        self.eq(PrefixPlus(p), '+11.0')
        self.eq(PrefixPlus(PrefixPlus(p)), '++11.0')
        self.eq(PrefixPlus(Number('+1')), '+1.0')
        self.py(PrefixPlus(Number(3)), 3)

        # Test with operators of precedence SUM, PRODUCT, POWER
        a, b, c = self.abc
        self.eq(PrefixPlus(Plus(a, b)), '+(a + b)')
        self.eq(Divide(PrefixPlus(Plus(a, b)), c), '+(a + b) / c')
        self.eq(PrefixPlus(Remainder(b, a)), '+(b % a)')
        self.eq(Power(PrefixPlus(a), b), '(+a)**b')
        self.eq(Power(PrefixPlus(Power(b, a)), c), '(+b**a)**c')
        self.eq(Power(a, PrefixPlus(Power(b, c))), 'a**(+b**c)')

    def test_prefix_minus(self):
        # Test with numbers
        p = Number(11, 'kV')
        self.eq(PrefixMinus(p), '-11.0')
        self.eq(PrefixMinus(PrefixMinus(p)), '--11.0')
        self.eq(PrefixMinus(Number(-1)), '--1.0')
        self.py(PrefixMinus(Number(3)), -3)

        # Test with operators of precedence SUM, PRODUCT, POWER
        a, b, c = self.abc
        self.eq(PrefixMinus(Minus(a, b)), '-(a - b)')
        self.eq(Multiply(PrefixMinus(Plus(b, a)), c), '-(b + a) * c')
        self.eq(PrefixMinus(Quotient(b, a)), '-(b // a)')
        self.eq(Power(PrefixMinus(a), b), '(-a)**b')
        self.eq(Power(PrefixMinus(Power(c, b)), a), '(-c**b)**a')
        self.eq(Power(a, PrefixMinus(Power(b, c))), 'a**(-b**c)')

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

        self.py(Plus(Number(4), Number(2)), 6)
        self.py(Minus(Number(5), Number(1.5)), 3.5)

    def test_multiply_divide(self):
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

        self.py(Multiply(Number(7), Number(9)), 63)
        self.py(Divide(Number(5), Number(2)), 2.5)
        self.py(Multiply(Number(7), Plus(Number(1), Number(9))), 70)
        self.py(Divide(Minus(Number(19), Number(5)), Number(2)), 7)

    def test_quotient_remainder(self):
        a, b, c = self.abc

        self.eq(Remainder(Multiply(a, b), c), 'a * b % c')
        self.eq(Multiply(Quotient(a, b), c), 'a // b * c')
        self.eq(Quotient(a, Multiply(b, c)), 'a // (b * c)')
        self.eq(Multiply(a, Remainder(b, c)), 'a * (b % c)')

        self.eq(Divide(a, Quotient(b, c)), 'a / (b // c)')
        self.eq(Divide(Quotient(b, c), a), 'b // c / a')
        self.eq(Divide(a, Remainder(b, c)), 'a / (b % c)')
        self.eq(Divide(Remainder(b, c), a), 'b % c / a')

        self.py(Quotient(Number(10), Number(4)), 2)     # 2*4 + 2
        self.py(Remainder(Number(10), Number(4)), 2)
        self.py(Quotient(Number(10), Number(6)), 1)     # 6 + 4
        self.py(Remainder(Number(10), Number(6)), 4)
        self.py(Quotient(Number(5), Number(3)), 1)      # 1*3 + 2
        self.py(Remainder(Number(5), Number(3)), 2)
        self.py(Quotient(Number(-5), Number(3)), -2)    # -2*3 + 1
        self.py(Remainder(Number(-5), Number(3)), 1)
        self.py(Quotient(Number(5), Number(-3)), -2)    # -2*-3 - 1
        self.py(Remainder(Number(5), Number(-3)), -1)
        self.py(Quotient(Number(-5), Number(-3)), 1)    # 1*-3 - 2
        self.py(Remainder(Number(-5), Number(-3)), -2)
        # The quotient has sign sign(a)*sign(b)

    def test_power(self):
        a, b, c = self.abc
        self.eq(Power(a, b), 'a**b')

        # In Python, a**b**c = a**(b**c), whereas Myokit uses a^b^c = (a^b)^c
        self.eq(Power(Power(a, b), c), '(a**b)**c')
        self.eq(Power(a, Power(b, c)), 'a**b**c')

        self.eq(Power(Plus(a, b), c), '(a + b)**c')
        self.eq(Power(a, Minus(b, c)), 'a**(b - c)')
        self.eq(Power(Multiply(a, b), c), '(a * b)**c')
        self.eq(Power(a, Divide(b, c)), 'a**(b / c)')

        self.py(Power(Number(4), Power(Number(2), Number(3))), 65536)
        self.py(Power(Power(Number(2), Number(3)), Number(4)), 4096)

    def test_functions(self):
        a, b = self.ab

        self.eq(Sqrt(a), 'math.sqrt(a)')
        self.eq(Exp(a), 'math.exp(a)')
        self.eq(Log(a), 'math.log(a)')
        self.eq(Log(a, b), 'math.log(a, b)')
        self.eq(Log10(a), 'math.log10(a)')
        self.eq(Sin(a), 'math.sin(a)')
        self.eq(Cos(a), 'math.cos(a)')
        self.eq(Tan(a), 'math.tan(a)')
        self.eq(ASin(a), 'math.asin(a)')
        self.eq(ACos(a), 'math.acos(a)')
        self.eq(ATan(a), 'math.atan(a)')
        self.eq(Floor(a), 'math.floor(a)')
        self.eq(Ceil(a), 'math.ceil(a)')
        self.eq(Abs(a), 'abs(a)')

        self.py(Sqrt(Number(9)), 3)
        self.py(Exp(Number(3)), math.exp(3))
        self.py(Log(Number(3)), math.log(3))
        self.py(Log(Number(8), Number(2)), 3)
        self.py(Log10(Number(100)), 2)
        self.py(Sin(Number(1)), math.sin(1))
        self.py(Cos(Number(1)), math.cos(1))
        self.py(Tan(Number(4)), math.tan(4))
        self.py(ASin(Number(0.4)), math.asin(0.4))
        self.py(ACos(Number(0.4)), math.acos(0.4))
        self.py(ATan(Number(0.4)), math.atan(0.4))
        self.py(Floor(Number(3.9)), 3)
        self.py(Ceil(Number(4.01)), 5)
        self.py(Abs(PrefixMinus(Number(12))), 12)
        self.py(Abs(Number(-13)), 13)

    def test_conditions(self):
        a, b, c, d = self.abcd

        self.eq(Equal(a, b), '(a == b)')
        self.eq(NotEqual(a, b), '(a != b)')
        self.eq(More(b, a), '(b > a)')
        self.eq(Less(d, c), '(d < c)')
        self.eq(MoreEqual(c, a), '(c >= a)')
        self.eq(LessEqual(b, d), '(b <= d)')

        self.eq(And(Equal(a, b), NotEqual(c, d)), '((a == b) and (c != d))')
        self.eq(Or(More(d, c), Less(b, a)), '((d > c) or (b < a))')
        self.eq(Not(Equal(d, d)), '(not (d == d))')

        true = Equal(Number(3), Number(3))
        self.py(true, True)
        false = NotEqual(Number(3), Number(3))
        self.py(false, False)
        self.py(More(Number(5), Number(3)), True)
        self.py(More(Number(3), Number(3)), False)
        self.py(MoreEqual(Number(3), Number(3)), True)
        self.py(Less(Number(3), Number(5)), True)
        self.py(More(Number(3), Number(3)), False)
        self.py(LessEqual(Number(3), Number(3)), True)

        self.py(And(true, false), False)
        self.py(And(true, true), True)
        self.py(Or(true, false), True)
        self.py(Or(true, true), True)
        self.py(Or(false, false), False)
        self.py(Not(true), False)
        self.py(Not(false), True)

    def test_conditionals(self):

        a, b, c, d = self.abcd
        self.eq(If(Equal(a, b), d, c), '(d if (a == b) else c)')
        self.py(If(Equal(Number(1), Number(1)), Number(2), Number(3)), 2)
        self.py(If(Equal(Number(10), Number(1)), Number(2), Number(3)), 3)

        self.eq(Piecewise(NotEqual(d, c), b, a), '(b if (d != c) else a)')
        self.eq(Piecewise(Equal(a, b), c, Equal(a, d), Number(3), Number(4)),
                '(c if (a == b) else (3.0 if (a == d) else 4.0))')

        self.py(Piecewise(Equal(Number(7), Number(7)), Number(2),
                          Equal(Number(7), Number(8)), Number(3),
                          Number(4)), 2)
        self.py(Piecewise(Equal(Number(7), Number(7)), Number(2),
                          Equal(Number(7), Number(7)), Number(3),
                          Number(4)), 2)
        self.py(Piecewise(NotEqual(Number(7), Number(7)), Number(2),
                          Equal(Number(7), Number(7)), Number(3),
                          Number(4)), 3)
        self.py(Piecewise(NotEqual(Number(7), Number(7)), Number(2),
                          NotEqual(Number(8), Number(8)), Number(3),
                          Number(4)), 4)


class NumPyExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """
    Test conversion of expressions to NumPy-compatible Python.
    This is used e.g. to graph expressions.
    Numerical tests are provided.
    """
    _name = 'numpy'
    _target = myokit.formats.python.NumPyExpressionWriter

    def py(self, expression, expected, *arguments):
        """ Test by executing in NumPy, possibly with vector arguments. """
        function = expression.pyfunc(use_numpy=True)
        if arguments:
            arguments = [numpy.array(arg) for arg in arguments]
            values = function(*arguments)
            self.assertEqual(list(values), list(expected))
        else:
            value = function()
            self.assertEqual(value, expected)

    def test_number(self):
        self.eq(Number(2), '2.0')
        self.eq(Number(-1), '-1.0')
        self.eq(Number(14, 'kV'), '14.0')
        self.py(Number(-7, 'mA'), -7)

    def test_name(self):
        self.eq(self.b, 'b')
        w = self._target()
        w.set_lhs_function(lambda v: v.var().qname().upper())
        self.assertEqual(w.ex(self.d), 'COMP.D')

    def test_derivative(self):
        self.eq(myokit.Derivative(self.d), 'dot(d)')

    def test_partial_derivative(self):
        e = myokit.InitialValue(self.a)
        self.assertRaisesRegex(NotImplementedError, 'Initial', self.w.ex, e)

    def test_initial_value(self):
        e = myokit.PartialDerivative(self.a, self.b)
        self.assertRaisesRegex(NotImplementedError, 'Partial', self.w.ex, e)

    def test_prefix_plus(self):
        # Test with numbers
        p = Number(11, 'kV')
        self.eq(PrefixPlus(p), '+11.0')
        self.eq(PrefixPlus(PrefixPlus(p)), '++11.0')
        self.eq(PrefixPlus(Number('+1')), '+1.0')
        self.py(PrefixPlus(Number(3)), 3)
        self.py(PrefixPlus(self.a), [3, 4], [3, 4])

        # Test with operators of precedence SUM, PRODUCT, POWER
        a, b, c = self.abc
        self.eq(PrefixPlus(Plus(a, b)), '+(a + b)')
        self.eq(Divide(PrefixPlus(Plus(a, b)), c), '+(a + b) / c')
        self.eq(PrefixPlus(Remainder(b, a)), '+(b % a)')
        self.eq(Power(PrefixPlus(Power(b, b)), c), '(+b**b)**c')
        self.eq(Power(a, PrefixPlus(Power(b, c))), 'a**(+b**c)')

    def test_prefix_minus(self):
        # Test with numbers
        p = Number(11, 'kV')
        self.eq(PrefixMinus(p), '-11.0')
        self.eq(PrefixMinus(PrefixMinus(p)), '--11.0')
        self.eq(PrefixMinus(Number(-1)), '--1.0')
        self.py(PrefixMinus(Number(3)), -3)
        self.py(PrefixMinus(self.a), [3, -4], [-3, 4])

        # Test with operators of precedence SUM, PRODUCT, POWER
        a, b, c = self.abc
        self.eq(PrefixMinus(Minus(a, b)), '-(a - b)')
        self.eq(Multiply(PrefixMinus(Plus(b, a)), c), '-(b + a) * c')
        self.eq(PrefixMinus(Quotient(b, a)), '-(b // a)')
        self.eq(Power(PrefixMinus(Power(c, b)), a), '(-c**b)**a')
        self.eq(Power(a, PrefixMinus(Power(b, c))), 'a**(-b**c)')

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

        self.py(Plus(Number(4), Number(2)), 6)
        self.py(Minus(Number(5), Number(1.5)), 3.5)
        self.py(Plus(a, Number(2)), [5, 1], [3, -1])
        self.py(Minus(Number(5), b), [2, -5], [3, 10])
        self.py(Plus(a, b), [6, 5, 4], [1, 2, 3], [5, 3, 1])
        self.py(Minus(a, b), [1, 2, 3], [8, 2, 5], [7, 0, 2])

    def test_multiply_divide(self):
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

        self.eq(Remainder(Multiply(a, b), c), 'a * b % c')
        self.eq(Multiply(Quotient(a, b), c), 'a // b * c')
        self.eq(Quotient(a, Multiply(b, c)), 'a // (b * c)')
        self.eq(Multiply(a, Remainder(b, c)), 'a * (b % c)')

        self.eq(Divide(a, Quotient(b, c)), 'a / (b // c)')
        self.eq(Divide(Quotient(b, c), a), 'b // c / a')
        self.eq(Divide(a, Remainder(b, c)), 'a / (b % c)')
        self.eq(Divide(Remainder(b, c), a), 'b % c / a')

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

        self.py(Multiply(Number(7), Number(9)), 63)
        self.py(Divide(Number(5), Number(2)), 2.5)
        self.py(Multiply(a, Number(2)), [6, -2], [3, -1])
        self.py(Divide(a, b), [5, -3, 10], 60, [12, -20, 6])

    def test_power(self):
        a, b, c = self.abc
        self.eq(Power(a, b), 'a**b')

        # In Python, a**b**c = a**(b**c), whereas Myokit uses a^b^c = (a^b)^c
        self.eq(Power(Power(a, b), c), '(a**b)**c')
        self.eq(Power(a, Power(b, c)), 'a**b**c')

        self.eq(Power(Plus(a, b), c), '(a + b)**c')
        self.eq(Power(a, Minus(b, c)), 'a**(b - c)')
        self.eq(Power(Multiply(a, b), c), '(a * b)**c')
        self.eq(Power(a, Divide(b, c)), 'a**(b / c)')

        self.py(Power(Number(4), Power(Number(2), Number(3))), 65536)
        self.py(Power(Power(Number(2), Number(3)), Number(4)), 4096)
        self.py(Power(a, Power(b, c)),
                [65536, 1, 4], [4, 1, 2], [2, 1, 4], [3, 1, 0.5])
        self.py(Power(Power(a, b), c),
                [4096, 0.01], [2, 10.0], [3, 2], [4, -1])

    def test_functions(self):
        a, b, c = self.abc

        self.eq(Sqrt(a), 'numpy.sqrt(a)')
        self.eq(Exp(a), 'numpy.exp(a)')
        self.eq(Log(a), 'numpy.log(a)')
        # Log replaced by divide always adds brackets, because parent element
        # won't have added any (never needed around a log(a, b) function).
        self.eq(Log(a, b), '(numpy.log(a) / numpy.log(b))')
        self.eq(Divide(a, Log(b, c)), 'a / (numpy.log(b) / numpy.log(c))')
        self.eq(Log10(a), 'numpy.log10(a)')
        self.eq(Sin(a), 'numpy.sin(a)')
        self.eq(Cos(a), 'numpy.cos(a)')
        self.eq(Tan(a), 'numpy.tan(a)')
        self.eq(ASin(a), 'numpy.arcsin(a)')
        self.eq(ACos(a), 'numpy.arccos(a)')
        self.eq(ATan(a), 'numpy.arctan(a)')
        self.eq(Floor(a), 'numpy.floor(a)')
        self.eq(Ceil(a), 'numpy.ceil(a)')
        self.eq(Abs(a), 'numpy.abs(a)')

        self.py(Sqrt(a), [3, 4], [9, 16])
        self.py(Exp(a), numpy.exp([2, 3]), [2, 3])
        self.py(Log(a), numpy.log([3, 5]), [3, 5])
        self.py(Log(a, b), [3, 4], [27, 16], [3, 2])
        self.py(Log10(a), [2, 3], [100, 1000])
        self.py(Sin(a), numpy.sin([1, 2]), [1, 2])
        self.py(Cos(a), numpy.cos([3, 4]), [3, 4])
        self.py(Tan(a), numpy.tan([5, 6]), [5, 6])
        self.py(ASin(a), numpy.arcsin([0.1, 0.2]), [0.1, 0.2])
        self.py(ACos(a), numpy.arccos([0.3, 0.4, 0.5]), [0.3, 0.4, 0.5])
        self.py(ATan(a), numpy.arctan([0.1]), [0.1])
        self.py(Floor(a), [3, 3], [3.1, 3.9])
        self.py(Ceil(a), [2, 3], [1.1, 3])
        self.py(Abs(a), [13, 13], [13, -13])
        self.py(Abs(PrefixMinus(a)), [1, 2], [1, -2])

    def test_conditions(self):
        a, b, c, d = self.abcd

        self.eq(Equal(a, b), '(a == b)')
        self.eq(NotEqual(a, b), '(a != b)')
        self.eq(More(b, a), '(b > a)')
        self.eq(Less(d, c), '(d < c)')
        self.eq(MoreEqual(c, a), '(c >= a)')
        self.eq(LessEqual(b, d), '(b <= d)')

        self.eq(And(Equal(a, b), NotEqual(c, d)),
                'numpy.logical_and((a == b), (c != d))')
        self.eq(Or(More(d, c), Less(b, a)),
                'numpy.logical_or((d > c), (b < a))')
        self.eq(Not(Equal(d, d)), 'numpy.logical_not((d == d))')

        true = Equal(Number(3), Number(3))
        self.py(true, True)
        false = NotEqual(Number(3), Number(3))
        self.py(false, False)
        self.py(More(Number(5), Number(3)), True)
        self.py(More(Number(3), Number(3)), False)
        self.py(MoreEqual(Number(3), Number(3)), True)
        self.py(Less(Number(3), Number(5)), True)
        self.py(More(Number(3), Number(3)), False)
        self.py(LessEqual(Number(3), Number(3)), True)
        self.py(And(true, false), False)
        self.py(And(true, true), True)
        self.py(Or(true, false), True)
        self.py(Not(true), False)

    def test_conditionals(self):
        a, b, c, d = self.abcd
        e, f, g = self.efg

        self.eq(If(Equal(a, b), d, c), 'numpy.select([(a == b)], [d], c)')
        self.eq(Piecewise(NotEqual(d, c), b, a),
                'numpy.select([(d != c)], [b], a)')
        self.eq(Piecewise(Equal(a, b), c, Equal(a, d), Number(3), Number(4)),
                'numpy.select([(a == b), (a == d)], [c, 3.0], 4.0)')

        self.py(If(Equal(Number(10), Number(1)), Number(2), Number(3)), 3)
        self.py(If(Equal(a, b), c, d), [3, 2], [2, 2], [2, 3], [3, 4], [1, 2])
        self.py(Piecewise(Equal(a, b), c, Equal(d, e), f, g),
                [1, 2, 30], [1, 1, 1], [1, 2, 3], [1, 1, 1], [1, 4, 5],
                [1, 4, 6], [2, 2, 2], [3, 3, 30])


if __name__ == '__main__':
    unittest.main()
