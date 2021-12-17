#!/usr/bin/env python3
#
# Tests the expression writer classes.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.formats
import myokit.formats.ansic
import myokit.formats.cpp
import myokit.formats.latex
import myokit.formats.matlab
import myokit.formats.python
import myokit.formats.stan


# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:  # pragma: no python 3 cover
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str


class ExpressionWriterTest(unittest.TestCase):
    """ Test shared expression writer functionality. """

    def test_ewriter_interface(self):
        # Test listing and creating expression writers.

        # Test listing
        es = myokit.formats.ewriters()
        self.assertTrue(len(es) > 0)

        # Create one of each
        for e in es:
            self.assertIsInstance(e, basestring)
            e = myokit.formats.ewriter(e)
            self.assertTrue(isinstance(e, myokit.formats.ExpressionWriter))

    def test_unknown(self):
        # Test requesting an unknown expression writer.
        # Test fetching using ewriter method
        self.assertRaisesRegex(
            KeyError, 'Expression writer not found', myokit.formats.ewriter,
            'dada')


class AnsicExpressionWriterTest(unittest.TestCase):
    """ Test the Ansi C ewriter class. """

    def test_all(self):
        w = myokit.formats.ansic.AnsiCExpressionWriter()

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), 'c.a')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(w.ex(b), '12.0')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '12.0')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '(-12.0)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), 'c.a + 12.0')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), 'c.a - 12.0')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), 'c.a * 12.0')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), 'c.a / 12.0')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(w.ex(x), 'floor(c.a / 12.0)')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(w.ex(x), 'c.a - 12.0 * (floor(c.a / 12.0))')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), 'pow(c.a, 12.0)')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), 'sqrt(12.0)')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), 'exp(c.a)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), 'log(12.0)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(w.ex(x), '(log(c.a) / log(12.0))')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), 'log10(12.0)')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), 'sin(12.0)')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), 'cos(12.0)')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), 'tan(12.0)')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), 'asin(12.0)')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), 'acos(12.0)')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), 'atan(12.0)')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), 'floor(12.0)')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), 'ceil(12.0)')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), 'fabs(12.0)')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '(c.a == 12.0)')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a != 12.0)')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '(c.a > 12.0)')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '(c.a < 12.0)')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a >= 12.0)')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a <= 12.0)')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), '!((5.0 > 3.0))')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) && (2.0 < 1.0))')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) || (2.0 < 1.0))')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) ? c.a : 12.0)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            '((5.0 > 3.0) ? c.a : ((2.0 < 1.0) ? 12.0 : 1.0))')

        # If/Piecewise with special function
        w.set_condition_function('ifthenelse')
        x = myokit.If(cond1, a, b)
        self.assertEqual(w.ex(x), 'ifthenelse((5.0 > 3.0), c.a, 12.0)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            'ifthenelse((5.0 > 3.0), c.a, ifthenelse((2.0 < 1.0), 12.0, 1.0))')

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('ansic')
        self.assertIsInstance(w, myokit.formats.ansic.AnsiCExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


class CppExpressionWriterTest(unittest.TestCase):
    """ Test the C++ ewriter class. """

    def test_all(self):
        w = myokit.formats.cpp.CppExpressionWriter()

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), 'c.a')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(w.ex(b), '12.0')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '12.0')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '(-12.0)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), 'c.a + 12.0')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), 'c.a - 12.0')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), 'c.a * 12.0')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), 'c.a / 12.0')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(w.ex(x), 'floor(c.a / 12.0)')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(w.ex(x), 'c.a - 12.0 * (floor(c.a / 12.0))')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), 'pow(c.a, 12.0)')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), 'sqrt(12.0)')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), 'exp(c.a)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), 'log(12.0)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(w.ex(x), '(log(c.a) / log(12.0))')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), 'log10(12.0)')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), 'sin(12.0)')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), 'cos(12.0)')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), 'tan(12.0)')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), 'asin(12.0)')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), 'acos(12.0)')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), 'atan(12.0)')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), 'floor(12.0)')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), 'ceil(12.0)')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), 'fabs(12.0)')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '(c.a == 12.0)')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a != 12.0)')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '(c.a > 12.0)')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '(c.a < 12.0)')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a >= 12.0)')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a <= 12.0)')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), '!((5.0 > 3.0))')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) && (2.0 < 1.0))')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) || (2.0 < 1.0))')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) ? c.a : 12.0)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            '((5.0 > 3.0) ? c.a : ((2.0 < 1.0) ? 12.0 : 1.0))')

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('cpp')
        self.assertIsInstance(w, myokit.formats.cpp.CppExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


class CudaExpressionWriterTest(unittest.TestCase):
    """ Test the CUDA ewriter class. """

    def test_all(self):
        # Single and double precision
        ws = myokit.formats.cuda.CudaExpressionWriter()
        wd = myokit.formats.cuda.CudaExpressionWriter(myokit.DOUBLE_PRECISION)

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(ws.ex(a), 'c.a')
        self.assertEqual(wd.ex(a), 'c.a')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(ws.ex(b), '12.0f')
        self.assertEqual(wd.ex(b), '12.0')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(ws.ex(x), '12.0f')
        self.assertEqual(wd.ex(x), '12.0')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(ws.ex(x), '(-12.0f)')
        self.assertEqual(wd.ex(x), '(-12.0)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(ws.ex(x), 'c.a + 12.0f')
        self.assertEqual(wd.ex(x), 'c.a + 12.0')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(ws.ex(x), 'c.a - 12.0f')
        self.assertEqual(wd.ex(x), 'c.a - 12.0')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(ws.ex(x), 'c.a * 12.0f')
        self.assertEqual(wd.ex(x), 'c.a * 12.0')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(ws.ex(x), 'c.a / 12.0f')
        self.assertEqual(wd.ex(x), 'c.a / 12.0')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(ws.ex(x), 'floorf(c.a / 12.0f)')
        self.assertEqual(wd.ex(x), 'floor(c.a / 12.0)')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(ws.ex(x), 'c.a - 12.0f * (floorf(c.a / 12.0f))')
        self.assertEqual(wd.ex(x), 'c.a - 12.0 * (floor(c.a / 12.0))')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(ws.ex(x), 'powf(c.a, 12.0f)')
        self.assertEqual(wd.ex(x), 'pow(c.a, 12.0)')
        # Square
        x = myokit.Power(a, myokit.Number(2))
        self.assertEqual(ws.ex(x), '(c.a * c.a)')
        self.assertEqual(wd.ex(x), '(c.a * c.a)')
        # Square with brackets
        x = myokit.Power(myokit.Plus(a, b), myokit.Number(2))
        self.assertEqual(ws.ex(x), '((c.a + 12.0f) * (c.a + 12.0f))')
        self.assertEqual(wd.ex(x), '((c.a + 12.0) * (c.a + 12.0))')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(ws.ex(x), 'sqrtf(12.0f)')
        self.assertEqual(wd.ex(x), 'sqrt(12.0)')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(ws.ex(x), 'expf(c.a)')
        self.assertEqual(wd.ex(x), 'exp(c.a)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(ws.ex(x), 'logf(12.0f)')
        self.assertEqual(wd.ex(x), 'log(12.0)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(ws.ex(x), '(logf(c.a) / logf(12.0f))')
        self.assertEqual(wd.ex(x), '(log(c.a) / log(12.0))')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(ws.ex(x), 'log10f(12.0f)')
        self.assertEqual(wd.ex(x), 'log10(12.0)')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(ws.ex(x), 'sinf(12.0f)')
        self.assertEqual(wd.ex(x), 'sin(12.0)')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(ws.ex(x), 'cosf(12.0f)')
        self.assertEqual(wd.ex(x), 'cos(12.0)')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(ws.ex(x), 'tanf(12.0f)')
        self.assertEqual(wd.ex(x), 'tan(12.0)')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(ws.ex(x), 'asinf(12.0f)')
        self.assertEqual(wd.ex(x), 'asin(12.0)')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(ws.ex(x), 'acosf(12.0f)')
        self.assertEqual(wd.ex(x), 'acos(12.0)')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(ws.ex(x), 'atanf(12.0f)')
        self.assertEqual(wd.ex(x), 'atan(12.0)')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(ws.ex(x), 'floorf(12.0f)')
        self.assertEqual(wd.ex(x), 'floor(12.0)')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(ws.ex(x), 'ceilf(12.0f)')
        self.assertEqual(wd.ex(x), 'ceil(12.0)')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(ws.ex(x), 'fabsf(12.0f)')
        self.assertEqual(wd.ex(x), 'fabs(12.0)')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(ws.ex(x), '(c.a == 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a == 12.0)')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(ws.ex(x), '(c.a != 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a != 12.0)')
        # More
        x = myokit.More(a, b)
        self.assertEqual(ws.ex(x), '(c.a > 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a > 12.0)')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(ws.ex(x), '(c.a < 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a < 12.0)')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(ws.ex(x), '(c.a >= 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a >= 12.0)')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(ws.ex(x), '(c.a <= 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a <= 12.0)')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        x = myokit.Not(cond1)
        self.assertEqual(ws.ex(x), '!((5.0f > 3.0f))')
        self.assertEqual(wd.ex(x), '!((5.0 > 3.0))')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) && (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) && (2.0 < 1.0))')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) || (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) || (2.0 < 1.0))')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) ? c.a : 12.0f)')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) ? c.a : 12.0)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            ws.ex(x),
            '((5.0f > 3.0f) ? c.a : ((2.0f < 1.0f) ? 12.0f : 1.0f))')
        self.assertEqual(
            wd.ex(x),
            '((5.0 > 3.0) ? c.a : ((2.0 < 1.0) ? 12.0 : 1.0))')

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('cuda')
        self.assertIsInstance(w, myokit.formats.cuda.CudaExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


class LatexExpressionWriterTest(unittest.TestCase):
    """ Test the Latex ewriter class. """

    def test_all(self):
        w = myokit.formats.latex.LatexExpressionWriter()

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Model needs to be validated --> sets unames
        avar.set_rhs(12)
        avar.set_binding('time')
        model.validate()

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), '\\text{a}')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(w.ex(b), '12.0')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '12.0')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '\\left(-12.0\\right)')
        # Prefix minus with bracket
        x = myokit.PrefixMinus(myokit.Plus(a, b))
        self.assertEqual(
            w.ex(x), '\\left(-\\left(\\text{a}+12.0\\right)\\right)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), '\\text{a}+12.0')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), '\\text{a}-12.0')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), '\\text{a}*12.0')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), '\\frac{\\text{a}}{12.0}')

        # Quotient
        # Not supported in latex!
        x = myokit.Quotient(a, b)
        self.assertEqual(
            w.ex(x), '\\left\\lfloor\\frac{\\text{a}}{12.0}\\right\\rfloor')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(w.ex(x), '\\bmod\\left(\\text{a},12.0\\right)')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), '\\text{a}^{12.0}')
        # Power with brackets
        x = myokit.Power(myokit.Plus(a, b), b)
        self.assertEqual(w.ex(x), '\\left(\\text{a}+12.0\\right)^{12.0}')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), '\\sqrt{12.0}')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), '\\exp\\left(\\text{a}\\right)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), '\\log\\left(12.0\\right)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(w.ex(x), '\\log_{12.0}\\left(\\text{a}\\right)')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), '\\log_{10.0}\\left(12.0\\right)')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), '\\sin\\left(12.0\\right)')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), '\\cos\\left(12.0\\right)')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), '\\tan\\left(12.0\\right)')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), '\\arcsin\\left(12.0\\right)')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), '\\arccos\\left(12.0\\right)')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), '\\arctan\\left(12.0\\right)')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), '\\left\\lfloor{12.0}\\right\\rfloor')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), '\\left\\lceil{12.0}\\right\\rceil')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), '\\lvert{12.0}\\rvert')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '\\left(\\text{a}=12.0\\right)')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '\\left(\\text{a}\\neq12.0\\right)')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '\\left(\\text{a}>12.0\\right)')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '\\left(\\text{a}<12.0\\right)')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '\\left(\\text{a}\\geq12.0\\right)')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '\\left(\\text{a}\\leq12.0\\right)')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        x = myokit.Not(cond1)
        self.assertEqual(
            w.ex(x), '\\not\\left(\\left(5.0>3.0\\right)\\right)')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(
            w.ex(x),
            '\\left(\\left(5.0>3.0\\right)\\and'
            '\\left(2.0<1.0\\right)\\right)')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(
            w.ex(x),
            '\\left(\\left(5.0>3.0\\right)\\or'
            '\\left(2.0<1.0\\right)\\right)')
        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(
            w.ex(x), 'if\\left(\\left(5.0>3.0\\right),\\text{a},12.0\\right)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            'piecewise\\left(\\left(5.0>3.0\\right),\\text{a},'
            '\\left(2.0<1.0\\right),12.0,1.0\\right)')

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('latex')
        self.assertIsInstance(w, myokit.formats.latex.LatexExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


class MatlabExpressionWriterTest(unittest.TestCase):
    """ Test the Matlab ewriter class. """

    def test_all(self):
        w = myokit.formats.matlab.MatlabExpressionWriter()

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), 'c.a')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(w.ex(b), '12.0')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '12.0')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '(-12.0)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), 'c.a + 12.0')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), 'c.a - 12.0')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), 'c.a * 12.0')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), 'c.a / 12.0')

        # Quotient

        x = myokit.Quotient(a, b)
        self.assertEqual(w.ex(x), 'floor(c.a / 12.0)')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(w.ex(x), 'mod(c.a, 12.0)')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), 'c.a ^ 12.0')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), 'sqrt(12.0)')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), 'exp(c.a)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), 'log(12.0)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(w.ex(x), '(log(c.a) / log(12.0))')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), 'log10(12.0)')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), 'sin(12.0)')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), 'cos(12.0)')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), 'tan(12.0)')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), 'asin(12.0)')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), 'acos(12.0)')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), 'atan(12.0)')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), 'floor(12.0)')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), 'ceil(12.0)')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), 'abs(12.0)')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '(c.a == 12.0)')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a != 12.0)')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '(c.a > 12.0)')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '(c.a < 12.0)')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a >= 12.0)')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a <= 12.0)')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), '!((5.0 > 3.0))')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) && (2.0 < 1.0))')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) || (2.0 < 1.0))')

        # If (custom function)
        x = myokit.If(cond1, a, b)
        self.assertEqual(w.ex(x), 'ifthenelse((5.0 > 3.0), c.a, 12.0)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            'ifthenelse((5.0 > 3.0), c.a, ifthenelse((2.0 < 1.0), 12.0, 1.0))')

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('matlab')
        self.assertIsInstance(w, myokit.formats.matlab.MatlabExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


class NumPyExpressionWriterTest(unittest.TestCase):
    """ Test the NumPy ewriter class. """

    def test_all(self):
        w = myokit.formats.python.NumPyExpressionWriter()

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), 'c.a')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(w.ex(b), '12.0')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '12.0')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '(-12.0)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), 'c.a + 12.0')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), 'c.a - 12.0')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), 'c.a * 12.0')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), 'c.a / 12.0')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(w.ex(x), 'c.a // 12.0')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(w.ex(x), 'c.a % 12.0')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), 'c.a ** 12.0')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), 'numpy.sqrt(12.0)')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), 'numpy.exp(c.a)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), 'numpy.log(12.0)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(w.ex(x), 'numpy.log(c.a, 12.0)')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), 'numpy.log10(12.0)')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), 'numpy.sin(12.0)')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), 'numpy.cos(12.0)')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), 'numpy.tan(12.0)')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), 'numpy.arcsin(12.0)')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), 'numpy.arccos(12.0)')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), 'numpy.arctan(12.0)')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), 'numpy.floor(12.0)')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), 'numpy.ceil(12.0)')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), 'abs(12.0)')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '(c.a == 12.0)')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a != 12.0)')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '(c.a > 12.0)')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '(c.a < 12.0)')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a >= 12.0)')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a <= 12.0)')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), 'not ((5.0 > 3.0))')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) and (2.0 < 1.0))')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) or (2.0 < 1.0))')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(
            w.ex(x), 'numpy.select([(5.0 > 3.0)], [c.a], 12.0)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            'numpy.select([(5.0 > 3.0), (2.0 < 1.0)], [c.a, 12.0], 1.0)')

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('numpy')
        self.assertIsInstance(w, myokit.formats.python.NumPyExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


class PythonExpressionWriterTest(unittest.TestCase):
    """ Test the Python ewriter class. """

    def test_all(self):
        w = myokit.formats.python.PythonExpressionWriter()

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), 'c.a')
        # Derivative
        x = myokit.Derivative(a)
        self.assertEqual(w.ex(x), 'dot(c.a)')
        # Partial derivative
        x = myokit.PartialDerivative(a, a)
        self.assertEqual(w.ex(x), 'diff(c.a, c.a)')
        # Initial value
        x = myokit.InitialValue(a)
        self.assertEqual(w.ex(x), 'init(c.a)')

        # Number
        b = myokit.Number(3)
        self.assertEqual(w.ex(b), '3.0')
        # Number with unit
        b = myokit.Number(12, 'pF')
        self.assertEqual(w.ex(b), '12.0')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '12.0')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '(-12.0)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), 'c.a + 12.0')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), 'c.a - 12.0')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), 'c.a * 12.0')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), 'c.a / 12.0')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(w.ex(x), 'c.a // 12.0')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(w.ex(x), 'c.a % 12.0')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), 'c.a ** 12.0')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), 'math.sqrt(12.0)')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), 'math.exp(c.a)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), 'math.log(12.0)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(w.ex(x), 'math.log(c.a, 12.0)')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), 'math.log10(12.0)')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), 'math.sin(12.0)')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), 'math.cos(12.0)')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), 'math.tan(12.0)')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), 'math.asin(12.0)')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), 'math.acos(12.0)')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), 'math.atan(12.0)')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), 'math.floor(12.0)')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), 'math.ceil(12.0)')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), 'abs(12.0)')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '(c.a == 12.0)')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a != 12.0)')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '(c.a > 12.0)')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '(c.a < 12.0)')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a >= 12.0)')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a <= 12.0)')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), 'not ((5.0 > 3.0))')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) and (2.0 < 1.0))')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) or (2.0 < 1.0))')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(w.ex(x), '(c.a if (5.0 > 3.0) else 12.0)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            '(c.a if (5.0 > 3.0) else (12.0 if (2.0 < 1.0) else 1.0))')

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('python')
        self.assertIsInstance(w, myokit.formats.python.PythonExpressionWriter)

        # Test lhs method
        w.set_lhs_function(lambda x: 'sheep')
        self.assertEqual(w.ex(a), 'sheep')

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


class StanExpressionWriterTest(unittest.TestCase):
    """ Test the Stan ewriter class. """

    def test_all(self):
        w = myokit.formats.stan.StanExpressionWriter()

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), 'c.a')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(w.ex(b), '12.0')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '12.0')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '(-12.0)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), 'c.a + 12.0')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), 'c.a - 12.0')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), 'c.a * 12.0')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), 'c.a / 12.0')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(w.ex(x), 'floor(c.a / 12.0)')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(w.ex(x), 'fmod(c.a, 12.0)')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), 'c.a ^ 12.0')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), 'sqrt(12.0)')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), 'exp(c.a)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), 'log(12.0)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(w.ex(x), '(log(c.a) / log(12.0))')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), 'log10(12.0)')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), 'sin(12.0)')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), 'cos(12.0)')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), 'tan(12.0)')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), 'asin(12.0)')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), 'acos(12.0)')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), 'atan(12.0)')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), 'floor(12.0)')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), 'ceil(12.0)')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), 'abs(12.0)')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '(c.a == 12.0)')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a != 12.0)')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '(c.a > 12.0)')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '(c.a < 12.0)')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a >= 12.0)')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a <= 12.0)')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), '!((5.0 > 3.0))')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) && (2.0 < 1.0))')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) || (2.0 < 1.0))')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) ? c.a : 12.0)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            '((5.0 > 3.0) ? c.a : ((2.0 < 1.0) ? 12.0 : 1.0))')

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('stan')
        self.assertIsInstance(w, myokit.formats.stan.StanExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


if __name__ == '__main__':
    unittest.main()
