#!/usr/bin/env python3
#
# Tests the parser and expression writer for content MathML.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import re
import unittest

import lxml.etree as etree

import myokit
import myokit.formats.mathml as mathml

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class ContentMathMLParserTest(unittest.TestCase):
    """ Tests content MathML parsing. """

    def p(self, xml):
        """ Parses a MathML string and returns a myokit.Expression. """

        return mathml.parse_mathml_etree(
            etree.fromstring(xml),
            lambda x, y: myokit.Name(x),
            lambda x, y: myokit.Number(x),
        )

    def test_apply(self):
        # Test <apply> element parsing

        self.assertRaisesRegex(
            mathml.MathMLError, 'Apply must contain at least one child',
            self.p, '<apply/>')

    def test_arithmetic_binary(self):
        # Tests parsing prefix operators

        # Plus
        a = myokit.Name('a')
        b = myokit.Number(1.0)
        e = myokit.Plus(a, b)
        x = '<apply><plus/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Minus
        e = myokit.Minus(a, b)
        x = '<apply><minus/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Multiply
        e = myokit.Multiply(a, b)
        x = '<apply><times/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Divide
        e = myokit.Divide(a, b)
        x = '<apply><divide/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # No operands
        self.assertRaisesRegex(
            mathml.MathMLError, 'at least one operand', self.p,
            '<apply><times/></apply>')

        # Only one operand
        self.assertRaisesRegex(
            mathml.MathMLError, 'at least two operands', self.p,
            '<apply><times/><cn>1.0</cn></apply>')

        # Several operands
        e = myokit.Multiply(
            myokit.Multiply(myokit.Multiply(a, b), myokit.Number(2)),
            myokit.Number(3))
        x = '<apply><times/><ci>a</ci><cn>1</cn><cn>2</cn><cn>3</cn></apply>'
        self.assertEqual(self.p(x), e)

    def test_arithmetic_unary(self):
        # Tests parsing basic arithmetic operators

        # Prefix plus
        e = myokit.PrefixPlus(myokit.Number(1))
        x = '<apply><plus/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Prefix minus
        e = myokit.PrefixMinus(myokit.Number(1))
        x = '<apply><minus/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

    def test_conditionals(self):
        # Tests if and piecewise parsing

        # If
        a = myokit.Name('c.a')
        b = myokit.Number(1.0)
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<apply><gt/><cn>5.0</cn><cn>3.0</cn></apply>'
        c2 = '<apply><lt/><cn>2.0</cn><cn>1.0</cn></apply>'
        e = myokit.If(cond1, a, b)
        x = (
            '<piecewise>'
            '<piece><ci>c.a</ci>' + c1 + '</piece>'
            '<otherwise><cn>1.0</cn></otherwise>'
            '</piecewise>'
        )
        self.assertEqual(self.p(x), e.piecewise())

        # Piecewise
        e = myokit.Piecewise(cond1, a, cond2, b, myokit.Number(100))
        x = (
            '<piecewise>'
            '<piece><ci>c.a</ci>' + c1 + '</piece>'
            '<piece><cn>1.0</cn>' + c2 + '</piece>'
            '<otherwise><cn>100.0</cn></otherwise>'
            '</piecewise>'
        )
        self.assertEqual(self.p(x), e)

        # Piecewise with extra otherwise
        x = (
            '<piecewise>'
            '  <piece>'
            '    <cn>1.0</cn><apply><eq/><cn>1.0</cn><cn>1.0</cn></apply>'
            '  </piece>'
            '  <otherwise>'
            '    <cn>2</cn>'
            '  </otherwise>'
            '  <otherwise>'
            '    <cn>3</cn>'
            '  </otherwise>'
            '</piecewise>'
        )
        self.assertRaisesRegex(
            mathml.MathMLError, 'Found more than one <otherwise>', self.p, x)

        # Check otherwise is automatically added if not given
        x = (
            '<piecewise>'
            '  <piece>'
            '    <cn>2</cn><apply><eq/><cn>1.0</cn><cn>1.0</cn></apply>'
            '  </piece>'
            '  <piece>'
            '    <cn>1.0</cn><apply><eq/><cn>1.0</cn><cn>1.0</cn></apply>'
            '  </piece>'
            '</piecewise>'
        )
        e = self.p(x)
        pieces = list(e.pieces())
        self.assertEqual(len(pieces), 3)
        self.assertEqual(pieces[0], myokit.Number(2))
        self.assertEqual(pieces[1], myokit.Number(1))
        self.assertEqual(pieces[2], myokit.Number(0))

        # Too much stuff in a piece
        x = (
            '<piecewise>'
            '  <piece>'
            '    <cn>1</cn><apply><eq/><cn>1</cn><cn>1</cn></apply>'
            '    <cn>2</cn>'
            '  </piece>'
            '  <otherwise>'
            '    <cn>3</cn>'
            '  </otherwise>'
            '</piecewise>'
        )
        self.assertRaisesRegex(
            mathml.MathMLError, '<piece> element must have exactly 2 children',
            self.p, x)

        # Too much stuff in an otherwise
        x = (
            '<piecewise>'
            '  <piece>'
            '    <cn>1</cn><apply><eq/><cn>1</cn><cn>1</cn></apply>'
            '  </piece>'
            '  <otherwise>'
            '    <cn>3</cn><ci>x</ci>'
            '  </otherwise>'
            '</piecewise>'
        )
        self.assertRaisesRegex(
            mathml.MathMLError, '<otherwise> element must have exactly 1',
            self.p, x)

        # Unexpected tag in piecwise
        x = (
            '<piecewise>'
            '  <piece>'
            '    <cn>1.0</cn><apply><eq/><cn>1.0</cn><cn>1.0</cn></apply>'
            '  </piece>'
            '  <otherwise>'
            '    <cn>3</cn>'
            '  </otherwise>'
            '  <apply><eq/><cn>1.0</cn><cn>1.0</cn></apply>'
            '</piecewise>'
        )
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unexpected content in <piecewise>', self.p, x)

    def test_constants(self):
        # Tests parsing of MathML special constants.

        # Pi
        import math
        x = self.p('<pi/>')
        self.assertAlmostEqual(math.pi, float(x))

        # Test e
        import math
        x = self.p('<exponentiale/>')
        self.assertAlmostEqual(math.e, float(x))

        # Test booleans
        import math
        x = self.p('<true/>')
        self.assertEqual(float(x), 1)
        x = self.p('<false/>')
        self.assertEqual(float(x), 0)

        # Nan and inf
        x = self.p('<notanumber/>')
        self.assertTrue(math.isnan(float(x)))
        x = self.p('<infinity/>')
        self.assertEqual(float(x), float('inf'))

        # Test constants are handled via the number factory
        xml = '<pi/>'
        x = mathml.parse_mathml_etree(
            etree.fromstring(xml),
            lambda x, y: myokit.Name(x),
            lambda x, y: myokit.Number(x, myokit.units.volt),
        )
        self.assertEqual(x.unit(), myokit.units.volt)

    def test_csymbol(self):
        # Test csymbol parsing
        # A csymbol MathML's way to define extensions, e.g. functions or
        # operators or symbols not defined in MathML. In Myokit we only
        # support their use as a type of <ci>.

        self.assertEqual(
            self.p('<csymbol definitionURL="hello" />'),
            myokit.Name('hello')
        )

        # Missing definition url
        self.assertRaisesRegex(
            mathml.MathMLError, 'must contain a definitionURL attribute',
            self.p, '<csymbol>Hiya</csymbol>')

        # Unknown variable
        d = {'a': myokit.Name('a')}
        p = mathml.MathMLParser(
            lambda x, y: d[x],
            lambda x, y: myokit.Number(x),
        )
        x = etree.fromstring('<csymbol definitionURL="a" />')
        self.assertEqual(p.parse(x), myokit.Name('a'))
        x = etree.fromstring('<csymbol definitionURL="b" />')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unable to create Name from csymbol',
            p.parse, x)

    def test_derivatives(self):
        # Test parsing of derivatives

        # Basic derivative
        x = (
            '<apply>'
            '  <diff/>'
            '  <bvar>'
            '    <ci>time</ci>'
            '  </bvar>'
            '  <ci>V</ci>'
            '</apply>'
        )
        e = myokit.Derivative(myokit.Name('V'))
        self.assertEqual(self.p(x), e)

        # Derivative with degree element
        x = (
            '<apply>'
            '  <diff/>'
            '  <bvar>'
            '    <ci>time</ci>'
            '    <degree><cn>1.0</cn></degree>'
            '  </bvar>'
            '  <ci>V</ci>'
            '</apply>'
        )
        e = myokit.Derivative(myokit.Name('V'))
        self.assertEqual(self.p(x), e)

        # Derivative with degree element other than 1
        self.assertRaisesRegex(
            mathml.MathMLError, 'degree one',
            self.p,
            '<apply>'
            '  <diff/>'
            '  <bvar>'
            '    <ci>time</ci>'
            '    <degree><cn>2</cn></degree>'
            '  </bvar>'
            '  <ci>V</ci>'
            '</apply>'
        )

        # Derivative with degree element but no cn
        self.assertRaisesRegex(
            mathml.MathMLError, '<degree> element must contain a <cn>',
            self.p,
            '<apply>'
            '  <diff/>'
            '  <bvar>'
            '    <ci>time</ci>'
            '    <degree/>'
            '  </bvar>'
            '  <ci>V</ci>'
            '</apply>'
        )

        # Derivative of an expression
        self.assertRaisesRegex(
            mathml.MathMLError, '<diff> element must contain a <ci>', self.p,
            '<apply>'
            '  <diff/>'
            '  <bvar>'
            '    <ci>time</ci>'
            '  </bvar>'
            '  <apply><plus/><cn>1.0</cn><ci>V</ci></apply>'
            '</apply>'
        )

        # Derivative without a bvar
        self.assertRaisesRegex(
            mathml.MathMLError, '<diff> element must contain a <bvar>', self.p,
            '<apply>'
            '  <diff/>'
            '  <ci>x</ci>'
            '</apply>'
        )

        # Derivative without ci in its bvar
        self.assertRaisesRegex(
            mathml.MathMLError, '<bvar> element must contain a <ci>', self.p,
            '<apply>'
            '  <diff/>'
            '  <bvar/>'
            '  <ci>x</ci>'
            '</apply>'
        )

    def test_functions(self):
        # Tests parsing basic functions

        # Power
        a = myokit.Name('a')
        b = myokit.Number(1)
        e = myokit.Power(a, b)
        x = '<apply><power/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        #TODO: Degree etc.

        # Exp
        e = myokit.Exp(a)
        x = '<apply><exp/><ci>a</ci></apply>'
        self.assertEqual(self.p(x), e)

        # No operands
        x = '<apply><exp/></apply>'
        self.assertRaisesRegex(
            mathml.MathMLError, r'Expecting 1 operand\(s\)', self.p, x)

        # Too many operands
        x = '<apply><exp/><cn>1</cn><cn>2</cn></apply>'
        self.assertRaisesRegex(
            mathml.MathMLError, r'Expecting 1 operand\(s\)', self.p, x)

        # Floor
        e = myokit.Floor(b)
        x = '<apply><floor/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Ceil
        e = myokit.Ceil(b)
        x = '<apply><ceiling/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Abs
        e = myokit.Abs(b)
        x = '<apply><abs/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Quotient
        e = myokit.Quotient(a, b)
        x = '<apply><quotient/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Remainder
        e = myokit.Remainder(a, b)
        x = '<apply><rem/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

    def test_functions_log(self):
        # Tests parsing logs

        # Log(a)
        a = myokit.Name('a')
        b = myokit.Number(1)
        e = myokit.Log(b)
        x = '<apply><ln/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Log(a, b)
        e = myokit.Log(a, b)
        x = '<apply><log/><logbase><cn>1.0</cn></logbase><ci>a</ci></apply>'
        self.assertEqual(self.p(x), e)

        # Log10
        e = myokit.Log10(b)
        x = '<apply><log/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Empty log
        x = '<apply><log/></apply>'
        self.assertRaisesRegex(
            mathml.MathMLError, 'Expecting operand after <log>', self.p, x)

        # Empty logbase
        x = '<apply><log/><logbase/><ci>a</ci></apply>'
        self.assertRaisesRegex(
            mathml.MathMLError, 'Expecting a single', self.p, x)

        # Crowded logbase
        x = ('<apply>'
             '<log/><logbase><cn>1</cn><cn>2</cn></logbase><ci>a</ci>'
             '</apply>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Expecting a single', self.p, x)

        # Too many operands
        x = '<apply><log/><cn>3</cn><ci>a</ci></apply>'
        self.assertRaisesRegex(
            mathml.MathMLError, 'Expecting a single', self.p, x)

        # Too many operands after logbase
        x = ('<apply>'
             '<log/><logbase><cn>1</cn></logbase><cn>3</cn><ci>a</ci>'
             '</apply>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Expecting a single', self.p, x)

    def test_functions_root(self):
        # Tests parsing roots

        # Square root
        e = myokit.Sqrt(myokit.Number(1))
        x = '<apply><root/><cn>1</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Root without operands
        x = '<apply><root/></apply>'
        self.assertRaisesRegex(
            mathml.MathMLError, 'Expecting operand after <root>', self.p, x)

        # Root with too many operands
        x = '<apply><root/><cn>1</cn><cn>2</cn></apply>'
        self.assertRaisesRegex(
            mathml.MathMLError, 'Expecting a single operand', self.p, x)

        # Root with degree 2
        e = myokit.Sqrt(myokit.Number(3))
        x = '<apply><root/><degree><cn>2</cn></degree><cn>3</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Root with degree 2 and extra operands
        x = ('<apply>'
             '<root/><degree><cn>2</cn></degree><cn>3</cn><cn>3</cn>'
             '</apply>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'single operand after the <degree>', self.p, x)

        # Root with degree 3
        e = myokit.Power(
            myokit.Number(3),
            myokit.Divide(myokit.Number(1), myokit.Number(3)))
        x = '<apply><root/><degree><cn>3</cn></degree><cn>3</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Root with degree in the wrong place
        x = '<apply><root/><cn>1</cn><degree><cn>2</cn></degree></apply>'
        self.assertRaisesRegex(
            mathml.MathMLError, 'Expecting a single operand', self.p, x)

        # Root with too many elements in degree
        e = myokit.Sqrt(myokit.Number(3))
        x = ('<apply>'
             '<root/><degree><cn>2</cn><cn>3</cn></degree><cn>3</cn>'
             '</apply>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Expecting a single operand inside <degree>',
            self.p, x)

    def test_inequalities(self):
        # Test parsing (in)equalities

        # Equal
        a = myokit.Name('a')
        b = myokit.Number(1.0)
        e = myokit.Equal(a, b)
        x = '<apply><eq/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # NotEqual
        e = myokit.NotEqual(a, b)
        x = '<apply><neq/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # More
        e = myokit.More(a, b)
        x = '<apply><gt/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Less
        e = myokit.Less(a, b)
        x = '<apply><lt/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # MoreEqual
        e = myokit.MoreEqual(a, b)
        x = '<apply><geq/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # LessEqual
        e = myokit.LessEqual(a, b)
        x = '<apply><leq/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

    def test_logic_operators(self):
        # Tests parsing logic operators

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<apply><gt/><cn>5.0</cn><cn>3.0</cn></apply>'
        c2 = '<apply><lt/><cn>2.0</cn><cn>1.0</cn></apply>'
        e = myokit.Not(cond1)
        x = '<apply><not/>' + c1 + '</apply>'
        self.assertEqual(self.p(x), e)

        # And
        e = myokit.And(cond1, cond2)
        x = '<apply><and/>' + c1 + c2 + '</apply>'
        self.assertEqual(self.p(x), e)

        # Or
        e = myokit.Or(cond1, cond2)
        x = '<apply><or/>' + c1 + c2 + '</apply>'
        self.assertEqual(self.p(x), e)

        # Xor
        e = myokit.And(
            myokit.Or(cond1, cond2),
            myokit.Not(myokit.And(cond1, cond2))
        )
        x = '<apply><xor/>' + c1 + c2 + '</apply>'
        self.assertEqual(self.p(x), e)

    def test_parse_mathml_string(self):
        # Test :meth:`mathml.parse_mathml_string()`.

        self.assertEqual(
            mathml.parse_mathml_string('<apply><cn>1.0</cn></apply>'),
            myokit.Number(1)
        )

    def test_name(self):
        # Test name parsing

        self.assertEqual(self.p('<ci>var</ci>'), myokit.Name('var'))

        # Empty ci
        self.assertRaisesRegex(
            mathml.MathMLError, 'must contain a variable name',
            self.p, '<ci/>')

        # Non-existent variable
        d = {'a': myokit.Name('a')}
        p = mathml.MathMLParser(
            lambda x, y: d[x],
            lambda x, y: myokit.Number(x),
        )
        x = etree.fromstring('<ci>a</ci>')
        self.assertEqual(p.parse(x), myokit.Name('a'))
        x = etree.fromstring('<ci>b</ci>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unable to create Name', p.parse, x)

    def test_number(self):
        # Test number parsing

        # Real
        x = self.p('<cn>4</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn>   4  \n </cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn type="real">4</cn>')
        self.assertEqual(x, myokit.Number(4))
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unable to convert contents of <cn>',
            self.p, '<cn>barry</cn>')

        # Real with base
        x = self.p('<cn type="real" base="10">4</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn type="real" base="  10  ">4</cn>')
        self.assertEqual(x, myokit.Number(4))
        self.assertRaisesRegex(
            mathml.MathMLError, 'bases other than 10',
            self.p, '<cn type="real" base="9">4</cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Invalid base',
            self.p, '<cn type="real" base="x">4</cn>')

        # Integer
        x = self.p('<cn type="integer">4</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn type="integer">\n4  </cn>')
        self.assertEqual(x, myokit.Number(4))
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unable to convert contents of <cn>',
            self.p, '<cn type="integer">barry</cn>')

        # Integer with base
        x = self.p('<cn type="integer" base="2">100</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn type="integer" base="  2  ">100</cn>')
        self.assertEqual(x, myokit.Number(4))
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unable to parse base',
            self.p, '<cn type="integer" base="barry">7</cn>')

        # Double
        x = self.p('<cn type="double">4</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn type="double">\t4\n</cn>')
        self.assertEqual(x, myokit.Number(4))
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unable to convert contents of <cn>',
            self.p, '<cn type="double">larry</cn>')

        # E-notation
        x = self.p('<cn type="e-notation">40<sep/>-1</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn type="e-notation">\n40<sep/>-1</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn type="e-notation">40<sep/>\t-1</cn>')
        self.assertEqual(x, myokit.Number(4))
        self.assertRaisesRegex(
            mathml.MathMLError, 'e-notation should have the format',
            self.p, '<cn type="e-notation">12</cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'missing part before the separator',
            self.p, '<cn type="e-notation"> <sep/>2</cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'missing part before the separator',
            self.p, '<cn type="e-notation"><sep/>2</cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'missing part after the separator',
            self.p, '<cn type="e-notation">2<sep/> </cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'missing part after the separator',
            self.p, '<cn type="e-notation">2<sep/></cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unable to parse number in e-notation',
            self.p, '<cn type="e-notation">larry<sep/>2</cn>')

        # Rational
        x = self.p('<cn type="rational">16<sep/>4</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn type="rational"> 16\t<sep/>4</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = self.p('<cn type="rational">16<sep/>\n4 </cn>')
        self.assertEqual(x, myokit.Number(4))
        self.assertRaisesRegex(
            mathml.MathMLError, 'Rational number should have the format',
            self.p, '<cn type="rational">12</cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'missing part before the separator',
            self.p, '<cn type="rational"> <sep/>2</cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'missing part before the separator',
            self.p, '<cn type="rational"><sep/>2</cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'missing part after the separator',
            self.p, '<cn type="rational">1<sep/></cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'missing part after the separator',
            self.p, '<cn type="rational">1<sep/> </cn>')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unable to parse rational number',
            self.p, '<cn type="rational">larry<sep/>2</cn>')

        # Unknown type
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unsupported <cn> type',
            self.p, '<cn type="special">1</cn>')

        # Missing value
        self.assertRaisesRegex(
            mathml.MathMLError, 'Empty <cn>', self.p, '<cn />')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Empty <cn>',
            self.p, '<cn type="real" />')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Empty <cn>',
            self.p, '<cn type="integer" />')
        self.assertRaisesRegex(
            mathml.MathMLError, 'Empty <cn>',
            self.p, '<cn type="double" />')

    def test_trig_basic(self):
        # Test parsing basic trig functions

        # Sin
        e = myokit.Sin(myokit.Number(1))
        x = '<apply><sin/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Cos
        e = myokit.Cos(myokit.Number(1))
        x = '<apply><cos/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # Tan
        e = myokit.Tan(myokit.Number(1))
        x = '<apply><tan/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # ASin
        e = myokit.ASin(myokit.Number(1))
        x = '<apply><arcsin/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # ACos
        e = myokit.ACos(myokit.Number(1))
        x = '<apply><arccos/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

        # ATan
        e = myokit.ATan(myokit.Number(1))
        x = '<apply><arctan/><cn>1.0</cn></apply>'
        self.assertEqual(self.p(x), e)

    def test_trig_extra(self):
        # Tests parsing of the annoying trig functions.

        # Cosecant
        x = self.p('<apply><csc/><cn>3</cn></apply>')
        y = myokit.parse_expression('1/ sin(3)')
        self.assertEqual(x, y)

        # Secant
        x = self.p('<apply><sec/><cn>3</cn></apply>')
        y = myokit.parse_expression('1/ cos(3)')
        self.assertEqual(x, y)

        # Cotangent
        x = self.p('<apply><cot/><cn>3</cn></apply>')
        y = myokit.parse_expression('1/ tan(3)')
        self.assertEqual(x, y)

        # arc-cosecant
        x = self.p('<apply><arccsc/><cn>3</cn></apply>')
        y = myokit.parse_expression('asin(1/ 3)')
        self.assertEqual(x, y)

        # arc-secant
        x = self.p('<apply><arcsec/><cn>3</cn></apply>')
        y = myokit.parse_expression('acos(1/ 3)')
        self.assertEqual(x, y)

        # arc-cotangent
        x = self.p('<apply><arccot/><cn>3</cn></apply>')
        y = myokit.parse_expression('atan(1/ 3)')
        self.assertEqual(x, y)

        # Hyperbolic sine
        x = self.p('<apply><sinh/><cn>3</cn></apply>')
        y = myokit.parse_expression('0.5 * (exp(3) - exp(-3))')
        self.assertEqual(x, y)

        # Hyperbolic cosine
        x = self.p('<apply><cosh/><cn>3</cn></apply>')
        y = myokit.parse_expression('0.5 * (exp(3) + exp(-3))')
        self.assertEqual(x, y)

        # Hyperbolic tangent
        x = self.p('<apply><tanh/><cn>3</cn></apply>')
        y = myokit.parse_expression('(exp(2*3) - 1)/ (exp(2*3) + 1)')
        self.assertEqual(x, y)

        # Hyperbolic arc sine
        x = self.p('<apply><arcsinh/><cn>3</cn></apply>')
        y = myokit.parse_expression('log(3 + sqrt(3*3 + 1))')
        self.assertEqual(x, y)

        # Hyperbolic arc cosine
        x = self.p('<apply><arccosh/><cn>3</cn></apply>')
        y = myokit.parse_expression('log(3 + sqrt(3*3 - 1))')
        self.assertEqual(x, y)

        # Hyperbolic arc tangent
        x = self.p('<apply><arctanh/><cn>3</cn></apply>')
        y = myokit.parse_expression('0.5 * log((1 + 3) / (1 - 3))')
        self.assertEqual(x, y)

        # Hyperbolic cosecant
        x = self.p('<apply><csch/><cn>3</cn></apply>')
        y = myokit.parse_expression('2/ (exp(3) - exp(-3))')
        self.assertEqual(x, y)

        # Hyperbolic secant
        x = self.p('<apply><sech/><cn>3</cn></apply>')
        y = myokit.parse_expression('2/ (exp(3) + exp(-3))')
        self.assertEqual(x, y)

        # Hyperbolic cotangent
        x = self.p('<apply><coth/><cn>3</cn></apply>')
        y = myokit.parse_expression('(exp(2*3) + 1)/ (exp(2*3) - 1)')
        self.assertEqual(x, y)

        # Hyperbolic arc cosecant
        x = self.p('<apply><arccsch/><cn>3</cn></apply>')
        y = myokit.parse_expression('log(1/3 + sqrt(1/(3*3) + 1))')
        self.assertEqual(x, y)

        # Hyperbolic arc secant
        x = self.p('<apply><arcsech/><cn>3</cn></apply>')
        y = myokit.parse_expression('log(1/3 + sqrt(1/(3*3) - 1))')
        self.assertEqual(x, y)

        # Hyperbolic arc cotangent
        x = self.p('<apply><arccoth/><cn>3</cn></apply>')
        y = myokit.parse_expression('0.5 * log((3 + 1) / (3 - 1))')
        self.assertEqual(x, y)

    def test_unsupported(self):
        # Test parsing unsupported elements

        # Unsupported atomic
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unsupported element', self.p, '<apple/>')

        # Unsupported in apply
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unsupported element', self.p,
            '<apply><yum/><ci>3</ci></apply>')


class ContentMathMLWriterTest(unittest.TestCase):
    """ Test writing content MathML expressions. """

    @classmethod
    def setUpClass(cls):
        cls.w = mathml.MathMLExpressionWriter()
        cls.w.set_mode(presentation=False)

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

        # Plus
        a = myokit.Name('a')
        b = myokit.Number(1)
        e = myokit.Plus(a, b)
        x = '<apply><plus/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Minus
        e = myokit.Minus(a, b)
        x = '<apply><minus/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Multiply
        e = myokit.Multiply(a, b)
        x = '<apply><times/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Divide
        e = myokit.Divide(a, b)
        x = '<apply><divide/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

    def test_arithmetic_unary(self):
        # Tests writing prefix operators

        # Prefix plus
        m = myokit.PrefixPlus(myokit.Number(1))
        x = '<apply><plus/><cn>1.0</cn></apply>'
        self.assertWrite(m, x)

        # Prefix minus
        m = myokit.PrefixMinus(myokit.Number(1))
        x = '<apply><minus/><cn>1.0</cn></apply>'
        self.assertWrite(m, x)

    def test_conditionals(self):
        # Tests if and piecewise writing

        a = myokit.Name('a')
        b = myokit.Number(1)
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<apply><gt/><cn>5.0</cn><cn>3.0</cn></apply>'
        c2 = '<apply><lt/><cn>2.0</cn><cn>1.0</cn></apply>'

        # If
        e = myokit.If(cond1, a, b)
        x = (
            '<piecewise>'
            '<piece><ci>a</ci>' + c1 + '</piece>'
            '<otherwise><cn>1.0</cn></otherwise>'
            '</piecewise>'
        )
        self.assertWrite(e, x)

        # Piecewise
        e = myokit.Piecewise(cond1, a, cond2, b, myokit.Number(100))
        x = (
            '<piecewise>'
            '<piece><ci>a</ci>' + c1 + '</piece>'
            '<piece><cn>1.0</cn>' + c2 + '</piece>'
            '<otherwise><cn>100.0</cn></otherwise>'
            '</piecewise>'
        )
        self.assertWrite(e, x)

    def test_creation(self):
        # Test creation via formats.ewriter

        w = myokit.formats.ewriter('mathml')
        self.assertIsInstance(self.w, mathml.MathMLExpressionWriter)

    def test_equation(self):
        # Test equation writing

        expression = myokit.Equation(myokit.Name('a'), myokit.Number(1))
        xml = '<apply><eq/><ci>a</ci><cn>1.0</cn></apply>'

        x = self.w.eq(expression)
        m = self._math.match(x)
        self.assertTrue(m)
        self.assertEqual(m.group(1), xml)

    def test_functions(self):
        # Tests writing basic functions

        # Power
        a = myokit.Name('a')
        b = myokit.Number(1)
        e = myokit.Power(a, b)
        x = '<apply><power/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Sqrt
        e = myokit.Sqrt(b)
        x = '<apply><root/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Exp
        e = myokit.Exp(a)
        x = '<apply><exp/><ci>a</ci></apply>'
        self.assertWrite(e, x)

        # Log(a)
        e = myokit.Log(b)
        x = '<apply><ln/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Log(a, b)
        e = myokit.Log(a, b)
        x = '<apply><log/><logbase><cn>1.0</cn></logbase><ci>a</ci></apply>'
        self.assertWrite(e, x)

        # Log10
        e = myokit.Log10(b)
        x = '<apply><log/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Floor
        e = myokit.Floor(b)
        x = '<apply><floor/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Ceil
        e = myokit.Ceil(b)
        x = '<apply><ceiling/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Abs
        e = myokit.Abs(b)
        x = '<apply><abs/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Quotient
        e = myokit.Quotient(a, b)
        x = '<apply><quotient/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Remainder
        e = myokit.Remainder(a, b)
        x = '<apply><rem/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

    def test_inequalities(self):
        # Test writing (in)equalities

        # Equal
        a = myokit.Name('a')
        b = myokit.Number(1)
        e = myokit.Equal(a, b)
        x = '<apply><eq/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # NotEqual
        e = myokit.NotEqual(a, b)
        x = '<apply><neq/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # More
        e = myokit.More(a, b)
        x = '<apply><gt/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Less
        e = myokit.Less(a, b)
        x = '<apply><lt/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # MoreEqual
        e = myokit.MoreEqual(a, b)
        x = '<apply><geq/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # LessEqual
        e = myokit.LessEqual(a, b)
        x = '<apply><leq/><ci>a</ci><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

    def test_lhs_function(self):
        # Test writing with a special lhs function

        w = mathml.MathMLExpressionWriter()
        w.set_mode(presentation=False)
        w.set_lhs_function(lambda v: 'bert')

        expression = myokit.Name('ernie')
        xml = '<ci>bert</ci>'

        x = w.ex(expression)
        m = self._math.match(x)
        self.assertTrue(m)
        self.assertEqual(m.group(1), xml)

    def test_logic_operators(self):
        # Tests writing logic operators

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<apply><gt/><cn>5.0</cn><cn>3.0</cn></apply>'
        c2 = '<apply><lt/><cn>2.0</cn><cn>1.0</cn></apply>'
        e = myokit.Not(cond1)
        x = '<apply><not/>' + c1 + '</apply>'
        self.assertWrite(e, x)

        # And
        e = myokit.And(cond1, cond2)
        x = '<apply><and/>' + c1 + c2 + '</apply>'
        self.assertWrite(e, x)

        # Or
        e = myokit.Or(cond1, cond2)
        x = '<apply><or/>' + c1 + c2 + '</apply>'
        self.assertWrite(e, x)

    def test_name_and_numbers(self):
        # Test name and number writing

        self.assertWrite(myokit.Name('a'), '<ci>a</ci>')

        # Number without unit
        self.assertWrite(myokit.Number(0), '<cn>0.0</cn>')
        self.assertWrite(myokit.Number(1), '<cn>1.0</cn>')

        # Number with unit
        # Unit isn't exported by default!
        self.assertWrite(myokit.Number('-12', 'pF'), '<cn>-12.0</cn>')

        # Number with e notation (note that Python will turn e.g. 1e3 into
        # 1000, so must pick tests carefully)
        self.assertWrite(myokit.Number(1e3), '<cn>1000.0</cn>')
        self.assertWrite(myokit.Number(1e-3), '<cn>0.001</cn>')
        self.assertWrite(
            myokit.Number(1e-6),
            '<cn type="e-notation">1<sep/>-6</cn>')
        self.assertWrite(
            myokit.Number(2.3e24),
            '<cn type="e-notation">2.3<sep/>24</cn>')
        # myokit.float.str(1.23456789) = 1.23456788999999989e+00
        self.assertWrite(
            myokit.Number(1.23456789), '<cn>1.23456788999999989</cn>')

    def test_trig_basic(self):
        # Test writing basic trig functions

        # Sin
        b = myokit.Number(1)
        e = myokit.Sin(b)
        x = '<apply><sin/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Cos
        e = myokit.Cos(b)
        x = '<apply><cos/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # Tan
        e = myokit.Tan(b)
        x = '<apply><tan/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # ASin
        e = myokit.ASin(b)
        x = '<apply><arcsin/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # ACos
        e = myokit.ACos(b)
        x = '<apply><arccos/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

        # ATan
        e = myokit.ATan(b)
        x = '<apply><arctan/><cn>1.0</cn></apply>'
        self.assertWrite(e, x)

    def test_unknown_expression(self):
        # Test without a Myokit expression

        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', self.w.ex, 7)


if __name__ == '__main__':
    unittest.main()
