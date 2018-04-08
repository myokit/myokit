#!/usr/bin/env python
#
# Tests the expression writer classes.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import myokit
import myokit.formats
import myokit.formats.ansic
import myokit.formats.cellml
import myokit.formats.cpp
import myokit.formats.latex
import myokit.formats.mathml
import myokit.formats.matlab
import myokit.formats.python


# Name
# Number

# Plus
# Minus
# Multiply
# Divide

# Quotient
# Remainder

# Power
# Sqrt
# Exp
# Log
# Log10

# Sin
# Cos
# Tan
# ASin
# ACos
# ATan

# Floor
# Ceil
# Abs

# Equal
# NotEqual
# More
# Less
# MoreEqual
# LessEqual

# Not
# And
# Or

# If
# Piecewise


class AnsicExpressionWriterTest(unittest.TestCase):
    """ Tests the Ansi C ewriter class. """

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
        w = myokit.formats.ewriter('ansic')
        self.assertIsInstance(w, myokit.formats.ansic.AnsiCExpressionWriter)


class CellMLExpressionWriterTest(unittest.TestCase):
    """ Tests the CellML ewriter class. """

    def test_all(self):
        # CellML requires unit mapping
        units = {
            myokit.parse_unit('pF'): 'picofarad',
        }
        w = myokit.formats.cellml.CellMLExpressionWriter(units)

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Requires valid model with unames set
        avar.set_rhs(0)
        avar.set_binding('time')
        model.validate()

        # Name
        a = myokit.Name(avar)
        ca = '<ci>a</ci>'
        self.assertEqual(w.ex(a), ca)
        # Number with unit
        b = myokit.Number('12', 'pF')
        cb = '<cn cellml:units="picofarad">12.0</cn>'
        self.assertEqual(w.ex(b), cb)
        # Number without unit
        c = myokit.Number(1)
        cc = '<cn cellml:units="dimensionless">1.0</cn>'
        self.assertEqual(w.ex(c), cc)

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), '<apply><plus />' + ca + cb + '</apply>')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), '<apply><minus />' + ca + cb + '</apply>')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), '<apply><times />' + ca + cb + '</apply>')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), '<apply><divide />' + ca + cb + '</apply>')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), '<apply><power />' + ca + cb + '</apply>')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), '<apply><root />' + cb + '</apply>')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), '<apply><exp />' + ca + '</apply>')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), '<apply><ln />' + cb + '</apply>')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(
            w.ex(x),
            '<apply><log /><logbase>' + cb + '</logbase>' + ca + '</apply>'
        )
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), '<apply><log />' + cb + '</apply>')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), '<apply><sin />' + cb + '</apply>')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), '<apply><cos />' + cb + '</apply>')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), '<apply><tan />' + cb + '</apply>')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), '<apply><arcsin />' + cb + '</apply>')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), '<apply><arccos />' + cb + '</apply>')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), '<apply><arctan />' + cb + '</apply>')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), '<apply><floor />' + cb + '</apply>')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), '<apply><ceiling />' + cb + '</apply>')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), '<apply><abs />' + cb + '</apply>')

        # Quotient
        # Uses custom implementation: CellML doesn't have these operators.
        x = myokit.Quotient(a, b)
        self.assertEqual(
            w.ex(x),
            '<apply><floor /><apply><divide />' + ca + cb + '</apply></apply>')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(
            w.ex(x),
            '<apply><minus />' + ca +
            '<apply><times />' + cb +
            '<apply><floor /><apply><divide />' + ca + cb + '</apply></apply>'
            '</apply>'
            '</apply>'
        )

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '<apply><eq />' + ca + cb + '</apply>')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '<apply><neq />' + ca + cb + '</apply>')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '<apply><gt />' + ca + cb + '</apply>')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '<apply><lt />' + ca + cb + '</apply>')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '<apply><geq />' + ca + cb + '</apply>')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '<apply><leq />' + ca + cb + '</apply>')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = ('<apply><gt />'
              '<cn cellml:units="dimensionless">5.0</cn>'
              '<cn cellml:units="dimensionless">3.0</cn>'
              '</apply>')
        c2 = ('<apply><lt />'
              '<cn cellml:units="dimensionless">2.0</cn>'
              '<cn cellml:units="dimensionless">1.0</cn>'
              '</apply>')
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), '<apply><not />' + c1 + '</apply>')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '<apply><and />' + c1 + c2 + '</apply>')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '<apply><or />' + c1 + c2 + '</apply>')
        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(
            w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<otherwise>' + cb + '</otherwise>'
            '</piecewise>'
        )
        # Piecewise
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<piece>' + cb + c2 + '</piece>'
            '<otherwise>' + cc + '</otherwise>'
            '</piecewise>'
        )

        # Test fetching using ewriter method --> Won't work!
        self.assertRaises(TypeError, myokit.formats.ewriter, 'cellml')


class CppExpressionWriterTest(unittest.TestCase):
    """ Tests the C++ ewriter class. """

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


class CudaExpressionWriterTest(unittest.TestCase):
    """ Tests the CUDA ewriter class. """

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


class LatexExpressionWriterTest(unittest.TestCase):
    """ Tests the Latex ewriter class. """

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


class MathMLExpressionWriterTest(unittest.TestCase):
    """ Tests the MathML ewriter class. """

    def test_content(self):
        w = myokit.formats.mathml.MathMLExpressionWriter()
        w.set_mode(presentation=False)

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        ca = '<ci>c.a</ci>'
        self.assertEqual(w.ex(a), ca)
        # Number with unit
        b = myokit.Number('12', 'pF')
        cb = '<cn>12.0</cn>'
        self.assertEqual(w.ex(b), cb)
        # Number without unit
        c = myokit.Number(1)
        cc = '<cn>1.0</cn>'
        self.assertEqual(w.ex(c), cc)

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), '<apply><plus />' + ca + cb + '</apply>')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), '<apply><minus />' + ca + cb + '</apply>')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), '<apply><times />' + ca + cb + '</apply>')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), '<apply><divide />' + ca + cb + '</apply>')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), '<apply><power />' + ca + cb + '</apply>')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), '<apply><root />' + cb + '</apply>')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), '<apply><exp />' + ca + '</apply>')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), '<apply><ln />' + cb + '</apply>')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(
            w.ex(x),
            '<apply><log /><logbase>' + cb + '</logbase>' + ca + '</apply>'
        )
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), '<apply><log />' + cb + '</apply>')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), '<apply><sin />' + cb + '</apply>')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), '<apply><cos />' + cb + '</apply>')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), '<apply><tan />' + cb + '</apply>')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), '<apply><arcsin />' + cb + '</apply>')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), '<apply><arccos />' + cb + '</apply>')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), '<apply><arctan />' + cb + '</apply>')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), '<apply><floor />' + cb + '</apply>')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), '<apply><ceiling />' + cb + '</apply>')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), '<apply><abs />' + cb + '</apply>')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(w.ex(x), '<apply><quotient />' + ca + cb + '</apply>')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(w.ex(x), '<apply><rem />' + ca + cb + '</apply>')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '<apply><eq />' + ca + cb + '</apply>')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '<apply><neq />' + ca + cb + '</apply>')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '<apply><gt />' + ca + cb + '</apply>')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '<apply><lt />' + ca + cb + '</apply>')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '<apply><geq />' + ca + cb + '</apply>')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '<apply><leq />' + ca + cb + '</apply>')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<apply><gt /><cn>5.0</cn><cn>3.0</cn></apply>'
        c2 = '<apply><lt /><cn>2.0</cn><cn>1.0</cn></apply>'
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), '<apply><not />' + c1 + '</apply>')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '<apply><and />' + c1 + c2 + '</apply>')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '<apply><or />' + c1 + c2 + '</apply>')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(
            w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<otherwise>' + cb + '</otherwise>'
            '</piecewise>'
        )
        # Piecewise
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<piece>' + cb + c2 + '</piece>'
            '<otherwise>' + cc + '</otherwise>'
            '</piecewise>'
        )

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('mathml')
        self.assertIsInstance(w, myokit.formats.mathml.MathMLExpressionWriter)

    def test_presentation(self):
        w = myokit.formats.mathml.MathMLExpressionWriter()
        w.set_mode(presentation=True)

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        ca = '<mi>c.a</mi>'
        self.assertEqual(w.ex(a), ca)
        # Number with unit
        b = myokit.Number('12', 'pF')
        cb = '<mn>12.0</mn>'
        self.assertEqual(w.ex(b), cb)
        # Number without unit
        c = myokit.Number(1)
        cc = '<mn>1.0</mn>'
        self.assertEqual(w.ex(c), cc)

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>+</mo>' + cb + '</mrow>')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>-</mo>' + cb + '</mrow>')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>*</mo>' + cb + '</mrow>')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), '<mfrac>' + ca + cb + '</mfrac>')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), '<msup>' + ca + cb + '</msup>')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>root</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), '<msup><mi>e</mi>' + ca + '</msup>')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>ln</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(
            w.ex(x),
            '<mrow><msub><mi>log</mi>' + cb + '</msub>'
            '<mfenced>' + ca + '</mfenced></mrow>'
        )
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>log</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>sin</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>cos</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>tan</mi><mfenced>' + cb + '</mfenced></mrow>')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>arcsin</mi><mfenced>' + cb + '</mfenced></mrow>')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>arccos</mi><mfenced>' + cb + '</mfenced></mrow>')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>arctan</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>floor</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>ceiling</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>abs</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>//</mo>' + cb + '</mrow>')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>%</mo>' + cb + '</mrow>')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>==</mo>' + cb + '</mrow>')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>!=</mo>' + cb + '</mrow>')
        # More
        x = myokit.More(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>&gt;</mo>' + cb + '</mrow>')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>&lt;</mo>' + cb + '</mrow>')
        # MoreEqual
        # Named version &ge; is not output, shows decimal code instead
        x = myokit.MoreEqual(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>&#8805;</mo>' + cb + '</mrow>')
        # LessEqual
        # Named version &le; is not output, shows decimal code instead
        x = myokit.LessEqual(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>&#8804;</mo>' + cb + '</mrow>')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<mrow><mn>5.0</mn><mo>&gt;</mo><mn>3.0</mn></mrow>'
        c2 = '<mrow><mn>2.0</mn><mo>&lt;</mo><mn>1.0</mn></mrow>'
        x = myokit.Not(cond1)
        self.assertEqual(
            w.ex(x), '<mrow><mo>(</mo><mo>not</mo>' + c1 + '<mo>)</mo></mrow>')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(
            w.ex(x), '<mrow>' + c1 + '<mo>and</mo>' + c2 + '</mrow>')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(
            w.ex(x), '<mrow>' + c1 + '<mo>or</mo>' + c2 + '</mrow>')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(
            w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<otherwise>' + cb + '</otherwise>'
            '</piecewise>'
        )
        # Piecewise
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<piece>' + cb + c2 + '</piece>'
            '<otherwise>' + cc + '</otherwise>'
            '</piecewise>'
        )

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('mathml')
        self.assertIsInstance(w, myokit.formats.mathml.MathMLExpressionWriter)


class MatlabExpressionWriterTest(unittest.TestCase):
    """ Tests the Matlab ewriter class. """

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


class NumpyExpressionWriterTest(unittest.TestCase):
    """ Tests the Numpy ewriter class. """

    def test_all(self):
        w = myokit.formats.python.NumpyExpressionWriter()

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), 'c.a')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(w.ex(b), '12.0')

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
        self.assertIsInstance(w, myokit.formats.python.NumpyExpressionWriter)


class PythonExpressionWriterTest(unittest.TestCase):
    """ Tests the Python ewriter class. """

    def test_all(self):
        w = myokit.formats.python.PythonExpressionWriter()

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), 'c.a')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(w.ex(b), '12.0')

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


if __name__ == '__main__':
    unittest.main()
