#!/usr/bin/env python3
#
# Tests writing of Stan equations.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit
import myokit.formats.latex

from myokit import (
    Number, PrefixPlus, PrefixMinus, Plus, Minus,
    Multiply, Divide, Quotient, Remainder, Power, Sqrt,
    Exp, Log, Log10, Sin, Cos, Tan, ASin, ACos, ATan, Floor, Ceil, Abs,
    Not, And, Or, Equal, NotEqual, More, Less, MoreEqual, LessEqual,
)

import myokit.tests


class LatexExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """
    Test conversion of expressions to Python.
    This is used by pyfunc(), although that's usually done with the
    NumPyExpressionWriter instead.
    Numerical tests are provided.
    """
    _name = 'latex'
    _target = myokit.formats.latex.LatexExpressionWriter
    _update_lhs_function = False

    def test_number(self):
        self.eq(Number(1), '1.0')
        self.eq(Number(-1.3274924373284374), '-1.32749243732843736e+00')
        self.eq(Number(+1.3274924373284374), '1.32749243732843736e+00')
        self.eq(Number(-2), '-2.0')
        self.eq(Number(13, 'mV'), r'13.0 \text{mV}')
        self.eq(Number(2, 'A/F'), r'2.0 \text{A/F}')
        self.eq(Number(7, myokit.units.dimensionless), '7.0')

    def test_name(self):
        self.eq(self.a, r'\text{a}')
        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('under_score', rhs=3)
        t = c.add_variable('time', rhs=0, binding='time')
        m.validate()
        self.eq(myokit.Name(v), r'\text{under\_score}')

        w = self._target()
        w.set_lhs_function(lambda v: v.var().qname().upper())
        self.assertEqual(w.ex(self.a), 'COMP.A')

    def test_derivative(self):
        self.eq(myokit.Derivative(self.a), r'\frac{d\text{a}}{d\text{t}}')

        w = self._target()
        w.set_time_variable_name('timmy')
        self.assertEqual(w.ex(myokit.Derivative(self.a)),
                         r'\frac{d\text{a}}{d\text{timmy}}')
        w.set_time_variable_name('Bob')
        self.assertEqual(w.ex(myokit.Derivative(self.a)),
                         r'\frac{d\text{a}}{d\text{Bob}}')

    def test_partial_derivative(self):
        self.eq(myokit.PartialDerivative(self.a, self.b),
                r'\frac{\partial\text{a}}{\partial\text{b}}')

    def test_initial_value(self):
        self.eq(myokit.InitialValue(self.a), r'\text{a}(\text{t} = 0)')

    def test_prefix_plus(self):
        # Test with numbers
        p = Number(11, 'mV')
        self.eq(PrefixPlus(p), r'+11.0 \text{mV}')
        p = Number(3)
        self.eq(PrefixPlus(PrefixPlus(p)), '++3.0')
        self.eq(PrefixPlus(Number('+1')), '+1.0')

        # Test with operators of precedence SUM, PRODUCT, POWER
        a, b, c = self.abc
        self.eq(PrefixPlus(Plus(a, b)), r'+\left(\text{a}+\text{b}\right)')
        self.eq(Divide(PrefixPlus(Plus(a, b)), c),
                r'\frac{+\left(\text{a}+\text{b}\right)}{\text{c}}')
        self.eq(Power(PrefixPlus(b), a),
                r'\left(+\text{b}\right)^\text{a}')

    def test_prefix_minus(self):
        # Test with numbers
        p = Number(3, 'uA')
        self.eq(PrefixMinus(p), r'-3.0 \text{uA}')
        p = Number(2)
        self.eq(PrefixMinus(PrefixMinus(p)), '--2.0')
        self.eq(PrefixMinus(Number('-1')), '--1.0')

        # Test with operators of precedence SUM, PRODUCT, POWER
        a, b, c = self.abc
        self.eq(PrefixMinus(Plus(a, b)), r'-\left(\text{a}+\text{b}\right)')
        self.eq(Divide(PrefixMinus(Plus(a, b)), c),
                r'\frac{-\left(\text{a}+\text{b}\right)}{\text{c}}')
        self.eq(Power(PrefixMinus(b), a),
                r'\left(-\text{b}\right)^\text{a}')

    def test_plus_minus(self):
        a, b, c = self.abc
        ta, tb, tc = r'\text{a}', r'\text{b}', r'\text{c}'
        self.eq(Plus(a, b), f'{ta}+{tb}')
        self.eq(Plus(Plus(a, b), c), f'{ta}+{tb}+{tc}')
        self.eq(Plus(a, Plus(b, c)), rf'{ta}+\left({tb}+{tc}\right)')

        self.eq(Minus(a, b), f'{ta}-{tb}')
        self.eq(Minus(Minus(a, b), c), f'{ta}-{tb}-{tc}')
        self.eq(Minus(a, Minus(b, c)), rf'{ta}-\left({tb}-{tc}\right)')

        self.eq(Minus(a, b), f'{ta}-{tb}')
        self.eq(Plus(Minus(a, b), c), f'{ta}-{tb}+{tc}')
        self.eq(Minus(a, Plus(b, c)), rf'{ta}-\left({tb}+{tc}\right)')
        self.eq(Minus(Plus(a, b), c), f'{ta}+{tb}-{tc}')
        self.eq(Minus(a, Plus(b, c)), rf'{ta}-\left({tb}+{tc}\right)')

    def test_multiply_divide(self):
        a, b, c = self.abc
        ta, tb, tc = r'\text{a}', r'\text{b}', r'\text{c}'
        l, r = r'\left(', r'\right)'
        self.eq(Multiply(a, b), rf'{ta}\cdot{tb}')
        self.eq(Multiply(Multiply(a, b), c), rf'{ta}\cdot{tb}\cdot{tc}')
        self.eq(Multiply(a, Multiply(b, c)), rf'{ta}\cdot{l}{tb}\cdot{tc}{r}')
        self.eq(Divide(a, b), r'\frac{\text{a}}{\text{b}}')
        self.eq(Divide(Divide(a, b), c),
                r'\frac{\frac{\text{a}}{\text{b}}}{\text{c}}')
        self.eq(Divide(a, Divide(b, c)),
                r'\frac{\text{a}}{\frac{\text{b}}{\text{c}}}')
        self.eq(Divide(Divide(a, b), c),
                r'\frac{\frac{\text{a}}{\text{b}}}{\text{c}}')
        self.eq(Divide(Multiply(a, b), c),
                r'\frac{\text{a}\cdot\text{b}}{\text{c}}')

        self.eq(Multiply(Minus(a, b), c), rf'{l}{ta}-{tb}{r}\cdot{tc}')
        self.eq(Multiply(a, Plus(b, c)), rf'{ta}\cdot{l}{tb}+{tc}{r}')
        self.eq(Plus(a, Multiply(b, c)), rf'{ta}+{tb}\cdot{tc}')

    def test_remainder_quotient(self):
        a, b = self.ab
        self.eq(Remainder(a, b), r'\text{a}\bmod\text{b}')
        self.eq(Quotient(a, b),
                r'\left\lfloor\frac{\text{a}}{\text{b}}\right\rfloor')

    def test_power(self):
        a, b, c = self.abc
        ta, tb, tc = r'\text{a}', r'\text{b}', r'\text{c}'
        l, r = r'\left(', r'\right)'
        p, q = '{', '}'
        self.eq(Power(a, b), f'{ta}^{tb}')
        self.eq(Power(Power(a, b), c), f'{l}{ta}^{tb}{r}^{tc}')
        self.eq(Power(a, Power(b, c)), f'{ta}^{p}{tb}^{tc}{q}')
        self.eq(Power(Plus(a, b), c), f'{l}{ta}+{tb}{r}^{tc}')
        self.eq(Power(a, Minus(b, c)), f'{ta}^{p}{tb}-{tc}{q}')

    def test_functions(self):
        a, b = self.ab

        self.eq(Sqrt(a), r'\sqrt{\text{a}}')
        self.eq(Exp(a), r'\exp\left(\text{a}\right)')
        self.eq(Log(a), r'\log\left(\text{a}\right)')
        self.eq(Log(a, b), r'\log_{\text{b}}\left(\text{a}\right)')
        self.eq(Log10(a), r'\log_{10}\left(\text{a}\right)')
        self.eq(Sin(a), r'\sin\left(\text{a}\right)')
        self.eq(Cos(a), r'\cos\left(\text{a}\right)')
        self.eq(Tan(a), r'\tan\left(\text{a}\right)')
        self.eq(ASin(a), r'\arcsin\left(\text{a}\right)')
        self.eq(ACos(a), r'\arccos\left(\text{a}\right)')
        self.eq(ATan(a), r'\arctan\left(\text{a}\right)')
        self.eq(Floor(a), r'\left\lfloor{\text{a}}\right\rfloor')
        self.eq(Ceil(a), r'\left\lceil{\text{a}}\right\rceil')
        self.eq(Abs(a), r'\lvert{\text{a}}\rvert')

    def test_conditions(self):
        a, b, c, d = self.abcd

        self.eq(Equal(a, b), r'\left(\text{a}=\text{b}\right)')
        self.eq(NotEqual(a, b), r'\left(\text{a}\neq\text{b}\right)')
        self.eq(More(b, a), r'\left(\text{b}>\text{a}\right)')
        self.eq(Less(d, c), r'\left(\text{d}<\text{c}\right)')
        self.eq(MoreEqual(c, a), r'\left(\text{c}\geq\text{a}\right)')
        self.eq(LessEqual(b, d), r'\left(\text{b}\leq\text{d}\right)')

        self.eq(And(Equal(a, b), NotEqual(c, d)),
                r'\left(\left(\text{a}=\text{b}\right)\and'
                r'\left(\text{c}\neq\text{d}\right)\right)')
        self.eq(Or(Equal(a, b), NotEqual(c, d)),
                r'\left(\left(\text{a}=\text{b}\right)\or'
                r'\left(\text{c}\neq\text{d}\right)\right)')
        self.eq(Not(Equal(d, d)),
                r'\left(\not\left(\text{d}=\text{d}\right)\right)')

    def test_conditionals(self):
        a, b, c, d = self.abcd
        p = myokit.Equal(a, b)
        q = myokit.NotEqual(c, d)
        self.eq(myokit.If(p, c, d), r'\text{if}\left(\left(\text{a}=\text{b}'
                r'\right),\text{c},\text{d}\right)')
        self.eq(myokit.Piecewise(p, b, q, d, Number(1)), r'\text{piecewise}'
                r'\left(\left(\text{a}=\text{b}\right),\text{b},\left(\text{c}'
                r'\neq\text{d}\right),\text{d},1.0\right)')


if __name__ == '__main__':
    unittest.main()
