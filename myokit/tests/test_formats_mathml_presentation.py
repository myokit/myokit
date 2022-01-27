#!/usr/bin/env python3
#
# Tests the MathML expression writer in presentation mode.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import re
import unittest

import myokit
import myokit.formats.mathml as mathml

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class PresentationMathMLTest(unittest.TestCase):
    """
    Tests export of presentation MathML.
    """

    @classmethod
    def setUpClass(cls):
        model = myokit.Model()
        component = model.add_component('c')
        cls.avar = component.add_variable('a')

        cls.w = mathml.MathMLExpressionWriter()
        cls.w.set_mode(presentation=True)

        # MathML opening and closing tags
        cls._math = re.compile(r'^<math [^>]+>(.*)</math>$', re.S)

    def assertWrite(self, expression, xml):
        """ Assert writing an ``expression`` results in the given ``xml``. """
        x = self.w.ex(expression)
        m = self._math.match(x)
        self.assertTrue(m)
        self.assertEqual(m.group(1), xml)

    def test_arithmetic_binary(self):
        # Tests writing basic arithmetic operators

        a = myokit.Name(self.avar)
        b = myokit.Number('12', 'pF')
        ca = '<mi>c.a</mi>'
        cb = '<mn>12.0</mn>'

        # Plus
        x = myokit.Plus(a, b)
        self.assertWrite(x, '<mrow>' + ca + '<mo>+</mo>' + cb + '</mrow>')

        # Minus
        x = myokit.Minus(a, b)
        self.assertWrite(x, '<mrow>' + ca + '<mo>-</mo>' + cb + '</mrow>')

        # Multiply
        x = myokit.Multiply(a, b)
        self.assertWrite(x, '<mrow>' + ca + '<mo>*</mo>' + cb + '</mrow>')

        # Divide
        x = myokit.Divide(a, b)
        self.assertWrite(x, '<mfrac>' + ca + cb + '</mfrac>')

    def test_arithmetic_unary(self):
        # Tests writing prefix operators

        b = myokit.Number('12', 'pF')
        cb = '<mn>12.0</mn>'

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertWrite(x, '<mrow><mo>+</mo>' + cb + '</mrow>')

        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertWrite(x, '<mrow><mo>-</mo>' + cb + '</mrow>')

    def test_conditionals(self):
        # Tests if and piecewise writing

        a = myokit.Name('a')
        b = myokit.Number(1)
        c = myokit.Number(1)
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')

        ca = '<mi>a</mi>'
        cb = '<mn>1.0</mn>'
        cc = '<mn>1.0</mn>'
        c1 = '<mrow><mn>5.0</mn><mo>&gt;</mo><mn>3.0</mn></mrow>'
        c2 = '<mrow><mn>2.0</mn><mo>&lt;</mo><mn>1.0</mn></mrow>'

        # If
        x = myokit.If(cond1, a, b)
        self.assertWrite(
            x,
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<otherwise>' + cb + '</otherwise>'
            '</piecewise>'
        )
        # Piecewise
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertWrite(
            x,
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<piece>' + cb + c2 + '</piece>'
            '<otherwise>' + cc + '</otherwise>'
            '</piecewise>'
        )

    def test_creation(self):
        # Test creation via formats.ewriter

        w = myokit.formats.ewriter('mathml')
        self.assertIsInstance(self.w, mathml.MathMLExpressionWriter)

    def test_functions(self):
        # Tests writing basic functions

        a = myokit.Name(self.avar)
        b = myokit.Number('12', 'pF')
        ca = '<mi>c.a</mi>'
        cb = '<mn>12.0</mn>'

        # Power
        x = myokit.Power(a, b)
        self.assertWrite(x, '<msup>' + ca + cb + '</msup>')

        # Sqrt
        x = myokit.Sqrt(b)
        self.assertWrite(
            x, '<mrow><mi>root</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Exp
        x = myokit.Exp(a)
        self.assertWrite(x, '<msup><mi>e</mi>' + ca + '</msup>')

        # Log(a)
        x = myokit.Log(b)
        self.assertWrite(
            x, '<mrow><mi>ln</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertWrite(
            x,
            '<mrow><msub><mi>log</mi>' + cb + '</msub>'
            '<mfenced>' + ca + '</mfenced></mrow>'
        )

        # Log10
        x = myokit.Log10(b)
        self.assertWrite(
            x, '<mrow><mi>log</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Floor
        x = myokit.Floor(b)
        self.assertWrite(
            x, '<mrow><mi>floor</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Ceil
        x = myokit.Ceil(b)
        self.assertWrite(
            x, '<mrow><mi>ceiling</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Abs
        x = myokit.Abs(b)
        self.assertWrite(
            x, '<mrow><mi>abs</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertWrite(x, '<mrow>' + ca + '<mo>//</mo>' + cb + '</mrow>')

        # Remainder
        x = myokit.Remainder(a, b)
        self.assertWrite(x, '<mrow>' + ca + '<mo>%</mo>' + cb + '</mrow>')

    def test_inequalities(self):
        # Test writing (in)equalities

        a = myokit.Name(self.avar)
        b = myokit.Number('12', 'pF')
        ca = '<mi>c.a</mi>'
        cb = '<mn>12.0</mn>'

        # Equal
        x = myokit.Equal(a, b)
        self.assertWrite(x, '<mrow>' + ca + '<mo>==</mo>' + cb + '</mrow>')

        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertWrite(x, '<mrow>' + ca + '<mo>!=</mo>' + cb + '</mrow>')

        # More
        x = myokit.More(a, b)
        self.assertWrite(x, '<mrow>' + ca + '<mo>&gt;</mo>' + cb + '</mrow>')

        # Less
        x = myokit.Less(a, b)
        self.assertWrite(x, '<mrow>' + ca + '<mo>&lt;</mo>' + cb + '</mrow>')

        # MoreEqual
        # Named version &ge; is not output, shows decimal code instead
        x = myokit.MoreEqual(a, b)
        self.assertWrite(
            x, '<mrow>' + ca + '<mo>&#8805;</mo>' + cb + '</mrow>')

        # LessEqual
        # Named version &le; is not output, shows decimal code instead
        x = myokit.LessEqual(a, b)
        self.assertWrite(
            x, '<mrow>' + ca + '<mo>&#8804;</mo>' + cb + '</mrow>')

    def test_logic_operators(self):
        # Tests writing logic operators

        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<mrow><mn>5.0</mn><mo>&gt;</mo><mn>3.0</mn></mrow>'
        c2 = '<mrow><mn>2.0</mn><mo>&lt;</mo><mn>1.0</mn></mrow>'

        # Not
        x = myokit.Not(cond1)
        self.assertWrite(
            x, '<mrow><mo>(</mo><mo>not</mo>' + c1 + '<mo>)</mo></mrow>')

        # And
        x = myokit.And(cond1, cond2)
        self.assertWrite(x, '<mrow>' + c1 + '<mo>and</mo>' + c2 + '</mrow>')

        # Or
        x = myokit.Or(cond1, cond2)
        self.assertWrite(x, '<mrow>' + c1 + '<mo>or</mo>' + c2 + '</mrow>')

    def test_name_and_numbers(self):
        # Test name and number writing

        # Name
        self.assertWrite(myokit.Name(self.avar), '<mi>c.a</mi>')

        # Number with unit
        self.assertWrite(myokit.Number(12, 'pF'), '<mn>12.0</mn>')

        # Number without unit
        self.assertWrite(myokit.Number(1), '<mn>1.0</mn>')

        # E-notation is allowed in presentation MathML
        self.assertWrite(myokit.Number(1e-6), '<mn>1e-06</mn>')
        self.assertWrite(myokit.Number(1e24), '<mn>1e+24</mn>')

    def test_trig_basic(self):
        # Test writing basic trig functions

        b = myokit.Number('12', 'pF')
        cb = '<mn>12.0</mn>'

        # Sin
        x = myokit.Sin(b)
        self.assertWrite(
            x, '<mrow><mi>sin</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Cos
        x = myokit.Cos(b)
        self.assertWrite(
            x, '<mrow><mi>cos</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Tan
        x = myokit.Tan(b)
        self.assertWrite(
            x, '<mrow><mi>tan</mi><mfenced>' + cb + '</mfenced></mrow>')

        # ASin
        x = myokit.ASin(b)
        self.assertWrite(
            x, '<mrow><mi>arcsin</mi><mfenced>' + cb + '</mfenced></mrow>')

        # ACos
        x = myokit.ACos(b)
        self.assertWrite(
            x, '<mrow><mi>arccos</mi><mfenced>' + cb + '</mfenced></mrow>')

        # ATan
        x = myokit.ATan(b)
        self.assertWrite(
            x, '<mrow><mi>arctan</mi><mfenced>' + cb + '</mfenced></mrow>')

    def test_unknown_expression(self):
        # Test without a Myokit expression

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', self.w.ex, 7)


if __name__ == '__main__':
    unittest.main()
