#!/usr/bin/env python3
#
# Tests the expression writer for OpenCL.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.formats
import myokit.formats.opencl


# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:  # pragma: no python 3 cover
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class OpenCLExpressionWriterTest(unittest.TestCase):
    """ Test the OpenCL ewriter class. """

    def test_basic(self):

        # Single and double precision and native maths
        ws = myokit.formats.opencl.OpenCLExpressionWriter()
        wd = myokit.formats.opencl.OpenCLExpressionWriter(
            myokit.DOUBLE_PRECISION)
        wn = myokit.formats.opencl.OpenCLExpressionWriter(native_math=False)

        a = myokit.Name(myokit.Model().add_component('c').add_variable('a'))
        b = myokit.Number('12', 'pF')

        # Name
        self.assertEqual(ws.ex(a), 'c.a')
        self.assertEqual(wd.ex(a), 'c.a')
        self.assertEqual(wn.ex(a), 'c.a')

        # Number with unit
        self.assertEqual(ws.ex(b), '12.0f')
        self.assertEqual(wd.ex(b), '12.0')
        self.assertEqual(wn.ex(b), '12.0f')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(ws.ex(x), '12.0f')
        self.assertEqual(wd.ex(x), '12.0')
        self.assertEqual(wn.ex(x), '12.0f')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(ws.ex(x), '(-12.0f)')
        self.assertEqual(wd.ex(x), '(-12.0)')
        self.assertEqual(wn.ex(x), '(-12.0f)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(ws.ex(x), 'c.a + 12.0f')
        self.assertEqual(wd.ex(x), 'c.a + 12.0')
        self.assertEqual(wn.ex(x), 'c.a + 12.0f')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(ws.ex(x), 'c.a - 12.0f')
        self.assertEqual(wd.ex(x), 'c.a - 12.0')
        self.assertEqual(wn.ex(x), 'c.a - 12.0f')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(ws.ex(x), 'c.a * 12.0f')
        self.assertEqual(wd.ex(x), 'c.a * 12.0')
        self.assertEqual(wn.ex(x), 'c.a * 12.0f')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(ws.ex(x), 'c.a / 12.0f')
        self.assertEqual(wd.ex(x), 'c.a / 12.0')
        self.assertEqual(wn.ex(x), 'c.a / 12.0f')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(ws.ex(x), 'floor(c.a / 12.0f)')
        self.assertEqual(wd.ex(x), 'floor(c.a / 12.0)')
        self.assertEqual(wn.ex(x), 'floor(c.a / 12.0f)')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(ws.ex(x), 'c.a - 12.0f * (floor(c.a / 12.0f))')
        self.assertEqual(wd.ex(x), 'c.a - 12.0 * (floor(c.a / 12.0))')
        self.assertEqual(wn.ex(x), 'c.a - 12.0f * (floor(c.a / 12.0f))')

    def test_functions(self):

        # Single and double precision and native maths
        ws = myokit.formats.opencl.OpenCLExpressionWriter()
        wd = myokit.formats.opencl.OpenCLExpressionWriter(
            myokit.DOUBLE_PRECISION)
        wn = myokit.formats.opencl.OpenCLExpressionWriter(native_math=False)

        a = myokit.Name(myokit.Model().add_component('c').add_variable('a'))
        b = myokit.Number('12', 'pF')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(ws.ex(x), 'pow(c.a, 12.0f)')
        self.assertEqual(wd.ex(x), 'pow(c.a, 12.0)')
        self.assertEqual(wn.ex(x), 'pow(c.a, 12.0f)')
        # Square
        x = myokit.Power(a, myokit.Number(2))
        self.assertEqual(ws.ex(x), '(c.a * c.a)')
        self.assertEqual(wd.ex(x), '(c.a * c.a)')
        self.assertEqual(wn.ex(x), '(c.a * c.a)')
        # Square with brackets
        x = myokit.Power(myokit.Plus(a, b), myokit.Number(2))
        self.assertEqual(ws.ex(x), '((c.a + 12.0f) * (c.a + 12.0f))')
        self.assertEqual(wd.ex(x), '((c.a + 12.0) * (c.a + 12.0))')
        self.assertEqual(wn.ex(x), '((c.a + 12.0f) * (c.a + 12.0f))')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(ws.ex(x), 'native_sqrt(12.0f)')
        self.assertEqual(wd.ex(x), 'native_sqrt(12.0)')
        self.assertEqual(wn.ex(x), 'sqrt(12.0f)')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(ws.ex(x), 'native_exp(c.a)')
        self.assertEqual(wd.ex(x), 'native_exp(c.a)')
        self.assertEqual(wn.ex(x), 'exp(c.a)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(ws.ex(x), 'native_log(12.0f)')
        self.assertEqual(wd.ex(x), 'native_log(12.0)')
        self.assertEqual(wn.ex(x), 'log(12.0f)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(ws.ex(x), '(native_log(c.a) / native_log(12.0f))')
        self.assertEqual(wd.ex(x), '(native_log(c.a) / native_log(12.0))')
        self.assertEqual(wn.ex(x), '(log(c.a) / log(12.0f))')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(ws.ex(x), 'native_log10(12.0f)')
        self.assertEqual(wd.ex(x), 'native_log10(12.0)')
        self.assertEqual(wn.ex(x), 'log10(12.0f)')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(ws.ex(x), 'native_sin(12.0f)')
        self.assertEqual(wd.ex(x), 'native_sin(12.0)')
        self.assertEqual(wn.ex(x), 'sin(12.0f)')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(ws.ex(x), 'native_cos(12.0f)')
        self.assertEqual(wd.ex(x), 'native_cos(12.0)')
        self.assertEqual(wn.ex(x), 'cos(12.0f)')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(ws.ex(x), 'native_tan(12.0f)')
        self.assertEqual(wd.ex(x), 'native_tan(12.0)')
        self.assertEqual(wn.ex(x), 'tan(12.0f)')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(ws.ex(x), 'asin(12.0f)')
        self.assertEqual(wd.ex(x), 'asin(12.0)')
        self.assertEqual(wn.ex(x), 'asin(12.0f)')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(ws.ex(x), 'acos(12.0f)')
        self.assertEqual(wd.ex(x), 'acos(12.0)')
        self.assertEqual(wn.ex(x), 'acos(12.0f)')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(ws.ex(x), 'atan(12.0f)')
        self.assertEqual(wd.ex(x), 'atan(12.0)')
        self.assertEqual(wn.ex(x), 'atan(12.0f)')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(ws.ex(x), 'floor(12.0f)')
        self.assertEqual(wd.ex(x), 'floor(12.0)')
        self.assertEqual(wn.ex(x), 'floor(12.0f)')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(ws.ex(x), 'ceil(12.0f)')
        self.assertEqual(wd.ex(x), 'ceil(12.0)')
        self.assertEqual(wn.ex(x), 'ceil(12.0f)')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(ws.ex(x), 'fabs(12.0f)')
        self.assertEqual(wd.ex(x), 'fabs(12.0)')
        self.assertEqual(wn.ex(x), 'fabs(12.0f)')

    def test_conditional(self):

        # Single and double precision and native maths
        ws = myokit.formats.opencl.OpenCLExpressionWriter()
        wd = myokit.formats.opencl.OpenCLExpressionWriter(
            myokit.DOUBLE_PRECISION)
        wn = myokit.formats.opencl.OpenCLExpressionWriter(native_math=False)

        a = myokit.Name(myokit.Model().add_component('c').add_variable('a'))
        b = myokit.Number('12', 'pF')
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(ws.ex(x), '(c.a == 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a == 12.0)')
        self.assertEqual(wn.ex(x), '(c.a == 12.0f)')
        x = myokit.Equal(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) == (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) == (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) == (2.0f < 1.0f))')
        x = myokit.Equal(cond1, b)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) == (12.0f != 0.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) == (12.0 != 0.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) == (12.0f != 0.0f))')
        x = myokit.Equal(a, cond2)
        self.assertEqual(ws.ex(x), '((c.a != 0.0f) == (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((c.a != 0.0) == (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((c.a != 0.0f) == (2.0f < 1.0f))')

        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(ws.ex(x), '(c.a != 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a != 12.0)')
        self.assertEqual(wn.ex(x), '(c.a != 12.0f)')
        x = myokit.NotEqual(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) != (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) != (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) != (2.0f < 1.0f))')
        x = myokit.NotEqual(cond1, b)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) != (12.0f != 0.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) != (12.0 != 0.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) != (12.0f != 0.0f))')
        x = myokit.NotEqual(a, cond2)
        self.assertEqual(ws.ex(x), '((c.a != 0.0f) != (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((c.a != 0.0) != (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((c.a != 0.0f) != (2.0f < 1.0f))')

        # More
        x = myokit.More(a, b)
        self.assertEqual(ws.ex(x), '(c.a > 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a > 12.0)')
        self.assertEqual(wn.ex(x), '(c.a > 12.0f)')
        x = myokit.More(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) > (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) > (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) > (2.0f < 1.0f))')
        x = myokit.More(cond1, b)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) > (12.0f != 0.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) > (12.0 != 0.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) > (12.0f != 0.0f))')
        x = myokit.More(a, cond2)
        self.assertEqual(ws.ex(x), '((c.a != 0.0f) > (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((c.a != 0.0) > (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((c.a != 0.0f) > (2.0f < 1.0f))')

        # Less
        x = myokit.Less(a, b)
        self.assertEqual(ws.ex(x), '(c.a < 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a < 12.0)')
        self.assertEqual(wn.ex(x), '(c.a < 12.0f)')
        x = myokit.Less(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) < (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) < (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) < (2.0f < 1.0f))')
        x = myokit.Less(cond1, b)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) < (12.0f != 0.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) < (12.0 != 0.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) < (12.0f != 0.0f))')
        x = myokit.Less(a, cond2)
        self.assertEqual(ws.ex(x), '((c.a != 0.0f) < (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((c.a != 0.0) < (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((c.a != 0.0f) < (2.0f < 1.0f))')

        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(ws.ex(x), '(c.a >= 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a >= 12.0)')
        self.assertEqual(wn.ex(x), '(c.a >= 12.0f)')
        x = myokit.MoreEqual(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) >= (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) >= (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) >= (2.0f < 1.0f))')
        x = myokit.MoreEqual(cond1, b)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) >= (12.0f != 0.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) >= (12.0 != 0.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) >= (12.0f != 0.0f))')
        x = myokit.MoreEqual(a, cond2)
        self.assertEqual(ws.ex(x), '((c.a != 0.0f) >= (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((c.a != 0.0) >= (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((c.a != 0.0f) >= (2.0f < 1.0f))')

        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(ws.ex(x), '(c.a <= 12.0f)')
        self.assertEqual(wd.ex(x), '(c.a <= 12.0)')
        self.assertEqual(wn.ex(x), '(c.a <= 12.0f)')
        x = myokit.LessEqual(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) <= (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) <= (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) <= (2.0f < 1.0f))')
        x = myokit.LessEqual(cond1, b)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) <= (12.0f != 0.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) <= (12.0 != 0.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) <= (12.0f != 0.0f))')
        x = myokit.LessEqual(a, cond2)
        self.assertEqual(ws.ex(x), '((c.a != 0.0f) <= (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((c.a != 0.0) <= (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((c.a != 0.0f) <= (2.0f < 1.0f))')

    def test_logical(self):

        # Single and double precision and native maths
        ws = myokit.formats.opencl.OpenCLExpressionWriter()
        wd = myokit.formats.opencl.OpenCLExpressionWriter(
            myokit.DOUBLE_PRECISION)
        wn = myokit.formats.opencl.OpenCLExpressionWriter(native_math=False)

        a = myokit.Name(myokit.Model().add_component('c').add_variable('a'))
        b = myokit.Number('12', 'pF')
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        condx = myokit.Number(1.2)

        # Not
        x = myokit.Not(cond1)
        self.assertEqual(ws.ex(x), '!((5.0f > 3.0f))')
        self.assertEqual(wd.ex(x), '!((5.0 > 3.0))')
        self.assertEqual(wn.ex(x), '!((5.0f > 3.0f))')
        x = myokit.Not(condx)
        self.assertEqual(ws.ex(x), '!((1.2f != 0.0f))')
        self.assertEqual(wd.ex(x), '!((1.2 != 0.0))')
        self.assertEqual(wn.ex(x), '!((1.2f != 0.0f))')

        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) && (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) && (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) && (2.0f < 1.0f))')
        x = myokit.And(condx, cond2)
        self.assertEqual(ws.ex(x), '((1.2f != 0.0f) && (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((1.2 != 0.0) && (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((1.2f != 0.0f) && (2.0f < 1.0f))')
        x = myokit.And(cond1, condx)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) && (1.2f != 0.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) && (1.2 != 0.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) && (1.2f != 0.0f))')

        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) || (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) || (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) || (2.0f < 1.0f))')
        x = myokit.Or(condx, cond2)
        self.assertEqual(ws.ex(x), '((1.2f != 0.0f) || (2.0f < 1.0f))')
        self.assertEqual(wd.ex(x), '((1.2 != 0.0) || (2.0 < 1.0))')
        self.assertEqual(wn.ex(x), '((1.2f != 0.0f) || (2.0f < 1.0f))')
        x = myokit.Or(cond1, condx)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) || (1.2f != 0.0f))')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) || (1.2 != 0.0))')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) || (1.2f != 0.0f))')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(ws.ex(x), '((5.0f > 3.0f) ? c.a : 12.0f)')
        self.assertEqual(wd.ex(x), '((5.0 > 3.0) ? c.a : 12.0)')
        self.assertEqual(wn.ex(x), '((5.0f > 3.0f) ? c.a : 12.0f)')
        x = myokit.If(condx, a, b)
        self.assertEqual(ws.ex(x), '((1.2f != 0.0f) ? c.a : 12.0f)')
        self.assertEqual(wd.ex(x), '((1.2 != 0.0) ? c.a : 12.0)')
        self.assertEqual(wn.ex(x), '((1.2f != 0.0f) ? c.a : 12.0f)')

        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            ws.ex(x),
            '((5.0f > 3.0f) ? c.a : ((2.0f < 1.0f) ? 12.0f : 1.0f))')
        self.assertEqual(
            wd.ex(x),
            '((5.0 > 3.0) ? c.a : ((2.0 < 1.0) ? 12.0 : 1.0))')
        self.assertEqual(
            wn.ex(x),
            '((5.0f > 3.0f) ? c.a : ((2.0f < 1.0f) ? 12.0f : 1.0f))')
        x = myokit.Piecewise(condx, a, condx, b, c)
        self.assertEqual(
            ws.ex(x),
            '((1.2f != 0.0f) ? c.a : ((1.2f != 0.0f) ? 12.0f : 1.0f))')
        self.assertEqual(
            wd.ex(x),
            '((1.2 != 0.0) ? c.a : ((1.2 != 0.0) ? 12.0 : 1.0))')
        self.assertEqual(
            wn.ex(x),
            '((1.2f != 0.0f) ? c.a : ((1.2f != 0.0f) ? 12.0f : 1.0f))')

    def test_fetching(self):
        # Test fetching using ewriter method
        w = myokit.formats.ewriter('opencl')
        self.assertIsInstance(w, myokit.formats.opencl.OpenCLExpressionWriter)

    def test_bad_operand(self):
        # Test without a Myokit expression
        w = myokit.formats.opencl.OpenCLExpressionWriter()
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


if __name__ == '__main__':
    unittest.main()
