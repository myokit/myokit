#!/usr/bin/env python3
#
# Tests the parsing module.
# See also test_io.py
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.units

from myokit.tests import DIR_DATA, TemporaryDirectory

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str


class TokenizerTest(unittest.TestCase):
    """
    Tests the tokenizer class.
    """

    def test_tokenizer(self):
        # Test basic Tokenizer functionality.

        import myokit._parsing as p
        from myokit._parsing import Tokenizer
        s = Tokenizer('5')
        self.assertEqual(next(s), (p.INTEGER, '5', 1, 0))
        s = Tokenizer('3.0')
        self.assertEqual(next(s), (p.FLOAT, '3.0', 1, 0))
        s = Tokenizer('3.')
        self.assertEqual(next(s), (p.FLOAT, '3.', 1, 0))
        s = Tokenizer('3.E0')
        self.assertEqual(next(s), (p.FLOAT, '3.E0', 1, 0))
        s = Tokenizer('.30')
        self.assertEqual(next(s), (p.FLOAT, '.30', 1, 0))

        # Finished? Then should get a StopIteration
        self.assertEqual(s.peek()[0], p.EOL)
        self.assertEqual(next(s)[0], p.EOL)
        self.assertEqual(s.peek()[0], p.EOF)
        self.assertEqual(next(s)[0], p.EOF)
        self.assertRaises(IndexError, s.peek)
        self.assertRaises(StopIteration, next, s)

        # Unknown token
        self.assertRaisesRegex(
            myokit.ParseError, 'invalid token', Tokenizer, '@')
        s = Tokenizer('x  @')
        self.assertRaisesRegex(
            myokit.ParseError, 'invalid token', s.next)

        # Block-comment
        s = Tokenizer('"""Hello"""')
        self.assertEqual(next(s)[0], p.EOF)

        # Multi-line string
        s = Tokenizer('x: """Hello\nWo\trld"""')
        self.assertEqual(next(s)[0], p.META_NAME)
        self.assertEqual(next(s)[0], p.COLON)
        self.assertEqual(s.peek()[0], p.TEXT)
        self.assertEqual(next(s)[1], 'Hello\nWo\trld')
        self.assertEqual(next(s)[0], p.EOL)
        s = Tokenizer('x: """Hello"""World')
        self.assertEqual(next(s)[0], p.META_NAME)
        self.assertRaisesRegex(
            myokit.ParseError, 'after closing of multi-line string', next, s)
        s = Tokenizer('x: """He\nll\no"""World')
        self.assertEqual(next(s)[0], p.META_NAME)
        self.assertRaisesRegex(
            myokit.ParseError, 'after closing of multi-line string', next, s)
        s = Tokenizer('x: """Hello\n')
        self.assertEqual(next(s)[0], p.META_NAME)
        self.assertRaisesRegex(
            myokit.ParseError, 'Unclosed multi-line', s.next)

        # Indented is removed from multi-line string
        s = Tokenizer('    x: """Hello \n    world"""')
        self.assertEqual(next(s)[0], p.META_NAME)
        self.assertEqual(next(s)[0], p.COLON)
        self.assertEqual(s.peek()[0], p.TEXT)
        self.assertEqual(s.peek()[1], 'Hello\nworld')
        s = Tokenizer('\tx: """Hello \n\tworld"""')
        self.assertEqual(next(s)[0], p.META_NAME)
        self.assertEqual(next(s)[0], p.COLON)
        self.assertEqual(s.peek()[0], p.TEXT)
        self.assertEqual(s.peek()[1], 'Hello\nworld')

        # Empty lines
        s = Tokenizer('\n\n\nx: """Hello\nWorld"""\n\n\n')
        next(s)
        next(s)
        self.assertEqual(next(s)[1], 'Hello\nWorld')
        s = Tokenizer('\n\n\nx: """Hello\n\n\nWorld"""\n\n\n')
        next(s)
        next(s)
        self.assertEqual(next(s)[1], 'Hello\n\n\nWorld')

        # Line continuation
        s = Tokenizer('x: this is \\\nthe value of x')
        next(s)
        next(s)
        self.assertEqual(next(s)[1], 'this is the value of x')
        self.assertEqual(next(s)[0], p.EOL)

        s = Tokenizer('x: this is \\\nthe\\\n\n\n value of x')
        next(s)
        next(s)
        self.assertEqual(next(s)[1], 'this is the')
        self.assertEqual(next(s)[0], p.EOL)

        s = Tokenizer('x: this is \\\nthe\\\n\n\n value of x')
        next(s)
        next(s)
        self.assertEqual(next(s)[1], 'this is the')
        self.assertEqual(next(s)[0], p.EOL)

        # Comment doesn't end line continuation
        s = Tokenizer('x: this is \\\n#Hi mike\nthe value of x')
        next(s)
        next(s)
        self.assertEqual(next(s)[1], 'this is the value of x')

        # Line continuation must be last character on line
        s = Tokenizer('1 + \\3')
        next(s)
        self.assertRaisesRegex(
            myokit.ParseError, ' Backslash must be last', s.next)

        # But backslash is allowed in text (only seen as line cont. if last)
        s = Tokenizer('x: Hello\\michael\nHow are you')
        self.assertEqual(next(s)[0], p.META_NAME)
        self.assertEqual(next(s)[0], p.COLON)
        self.assertEqual(next(s)[1], 'Hello\\michael')

        # Brackets
        s = Tokenizer('x = (\n1 + \n\n2 + (\n3\n\n)\n\n) + 4')
        next(s)
        next(s)
        from myokit._parsing import parse_expression_stream
        e = parse_expression_stream(s)
        self.assertEqual(e.code(), '1 + 2 + 3 + 4')

        # Mismatched brackets
        s = Tokenizer('x = (1 + 2')
        self.assertEqual(next(s)[0], p.NAME)
        self.assertEqual(next(s)[0], p.EQUAL)
        self.assertEqual(next(s)[0], p.PAREN_OPEN)
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.PLUS)
        self.assertRaisesRegex(
            myokit.ParseError, 'Parentheses mismatch', s.next)

        s = Tokenizer('x = 1 + 2)')
        self.assertEqual(next(s)[0], p.NAME)
        self.assertEqual(next(s)[0], p.EQUAL)
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.PLUS)
        self.assertRaisesRegex(
            myokit.ParseError, 'Parentheses mismatch', s.next)

        # Test indenting (Tabs count as 8 spaces)
        s = '\n'.join([
            '1',
            '        2',
            '\t3',
            '        4',
            '5',
        ])
        s = Tokenizer(s)
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.EOL)
        self.assertEqual(next(s)[0], p.INDENT)
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.EOL)
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.EOL)
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.EOL)
        self.assertEqual(next(s)[0], p.DEDENT)
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.EOL)

        # Test indenting error
        s = Tokenizer('\n'.join([
            '1',
            '    2',
            '  3',
        ]))
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.EOL)
        self.assertEqual(next(s)[0], p.INDENT)
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.EOL)
        self.assertRaisesRegex(
            myokit.ParseError, 'Unexpected indenting level', s.next)

        # Line feed counts as a newline
        s = Tokenizer('123\f456')
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.EOL)
        self.assertEqual(next(s)[0], p.INTEGER)
        self.assertEqual(next(s)[0], p.EOL)


class PhasedParseTest(unittest.TestCase):
    """
    Tests several phases of parsing.
    """
    def test_segment_parsing(self):
        # Test :meth:`parse_model()`.
        from myokit._parsing import parse

        # Empty code --> error
        code = ''
        self.assertRaisesRegex(
            myokit.ParseError,
            r'expecting Segment header "\[\[segment_name]]"',
            parse, code)

        # Unexpected before model
        code = (
            '[[bert]]\n',
        )
        self.assertRaisesRegex(
            myokit.ParseError,
            r'Expecting \[\[model]] or \[\[protocol]] or \[\[script]]',
            parse, code)

        # Unexpected before protocol
        code = (
            '[[model]]\n',
            '[c]\n',
            't = 0 bind time\n',
            '[[bert]]\n',
        )
        self.assertRaisesRegex(
            myokit.ParseError,
            r'Expecting \[\[protocol]] or \[\[script]]',
            parse, code)

        # Unexpected before script
        code = (
            '[[model]]\n',
            '[c]\n',
            't = 0 bind time\n',
            '[[protocol]]\n',
            '[[bert]]\n',
        )
        self.assertRaisesRegex(
            myokit.ParseError,
            r'Expecting \[\[script]]',
            parse, code)

        # Bad segment order (same as unexpected after protocol)
        code = (
            '[[protocol]]\n',
            '[[model]]\n',
            '[c]\n',
            't = 0 bind time\n',
        )
        self.assertRaisesRegex(
            myokit.ParseError, r'Expecting \[\[script]]', parse, code)

    def test_parse_model(self):
        # Test the parse_model method.
        from myokit._parsing import parse_model

        # Test simple
        code = (
            '[[model]]\n',
            '[c]\n',
            't = 0 bind time\n',
        )
        model = parse_model(code)
        self.assertIsInstance(model, myokit.Model)
        model = parse_model(''.join(code))
        self.assertIsInstance(model, myokit.Model)

        # Not a model
        code = (
            '[[muddle]]\n',
            '[c]\n',
            't = 0 bind time\n',
        )
        self.assertRaisesRegex(
            myokit.ParseError, r'Expecting \[\[model]]', parse_model, code)

    def test_parse_model_from_stream_error(self):
        # Quick error testing for :meth:`parse_model_from_stream`.
        from myokit._parsing import parse_model_from_stream
        from myokit._parsing import Tokenizer

        def p(code):
            return parse_model_from_stream(Tokenizer(iter(code)))

        code = (
            '[[model]]',
            '[c]',
            't = 0 bind time',
        )
        model = p(code)
        self.assertIsInstance(model, myokit.Model)

        # Not a model
        code = (
            '[[muddle]]',
            '[c]',
            't = 0 bind time',
        )
        self.assertRaisesRegex(
            myokit.ParseError, r'Expecting \[\[model]]', p, code)

        # Double meta-data value
        code = (
            '[[model]]',
            'ax: 1',
            'ax: 1',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'Duplicate meta-data key', p, code)

        # Double initial values
        code = (
            '[[model]]',
            'a.x = 1',
            'a.x = 1',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'Duplicate initial value', p, code)

        # Unused initial values
        code = (
            '[[model]]',
            'a.x = 1',
            '[c]',
            't = 0 bind time',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'Unused initial value', p, code)

    def test_parse_user_function(self):
        # Test :meth:`parse_user_function()`.
        from myokit._parsing import parse_model as p

        # Test basics
        code = (
            '[[model]]',
            'michael(x) = 1 + sin(x)',
            '[c]',
            't = 0 bind time',
            'x = michael(12)',
        )
        p(code)

        code = (
            '[[model]]',
            'michael(x, y, z) = x + y / z',
            '[c]',
            't = 0 bind time',
            'x = michael(1,2,3)',
        )
        p(code)

        # Duplicate name
        code = (
            '[[model]]',
            'michael(x, y, z) = x + y / z',
            'michael(x, y, z) = x - y - z',
            '[c]',
            't = 0 bind time',
            'x = michael(1,2,3)',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'already defined', p, code)

    def test_block_comments(self):
        # Test block comments in model.
        from myokit._parsing import parse_model_from_stream
        from myokit._parsing import Tokenizer

        def p(code):
            return parse_model_from_stream(Tokenizer(iter(code)))

        # Block comments
        c1 = (
            '[[model]]',
            '[c]',
            't = 0 bind time',
        )
        m1 = p(c1)
        c2 = (
            '[[model]]',
            '"""This is a comment"""',
            '[c]',
            't = 0 bind time',
        )
        m2 = p(c2)
        c3 = (
            '[[model]]',
            '"""'
            'This is a long',
            'long',
            'long',
            'comment',
            '"""',
            '[c]',
            't = 0 bind time',
        )
        m3 = p(c3)
        self.assertEqual(m1.code(), m2.code(), m3.code())

    def test_parse_component(self):
        # Test parse_component(), uses parse_variable
        from myokit._parsing import parse_model as p

        # Test basics
        code = (
            '[[model]]',
            '[test]',
            't = 0',
            '    bind time',
            'x = 5 + b',
            '    b = 13',
            '    in [mV]',
            'desc: \"""',
            'This is a test component.',
            '\"""',
        )
        m = p(code)
        self.assertIn('test', m)
        self.assertEqual(
            m.get('test').meta['desc'], 'This is a test component.')

        # Test duplicate name
        code = (
            '[[model]]',
            '[test]',
            't = 0',
            '    bind time',
            '[test]',
            'x = 2',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'Duplicate component name', p, code)

        # Test invalid name --> Handled by tokenizer

        # Test duplicate meta data key
        code = (
            '[[model]]',
            '[test]',
            'yes: no',
            't = 0',
            '    bind time',
            'yes: yes',
            '[test]',
            'x = 2',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'Duplicate meta-data key', p, code)

    def test_parse_alias(self):
        # Test :meth:`parse_alias()`.
        from myokit._parsing import parse_model as p

        # Test basics
        code = (
            '[[model]]',
            '[a]',
            't = 10',
            '    bind time',
            '[b]',
            'use a.t as time',
            'b = time',
            '\"""',
        )
        m = p(code)
        self.assertEqual(m.get('b.b').eval(), 10)

        # Test bad variable name
        code = (
            '[[model]]',
            '[a]',
            't = 10',
            '    bind time',
            '[b]',
            'use t as time',
            'b = time',
            '\"""',
        )
        self.assertRaisesRegex(myokit.ParseError, 'fully qualified', p, code)

        # Test bad alias name
        code = (
            '[[model]]',
            '[a]',
            't = 10',
            '    bind time',
            '[b]',
            'use a.t as _flbt12',
            'b = time',
            '\"""',
        )
        self.assertRaisesRegex(myokit.ParseError, 'invalid token', p, code)

        # Unknown variable
        code = (
            '[[model]]',
            '[a]',
            't = 10',
            '    bind time',
            '[b]',
            'use a.x as time',
            'b = time',
            '\"""',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'Variable not found', p, code)

    def test_parse_variable(self):
        # Test parse_variable(), uses parse_expression()
        from myokit._parsing import parse_model as p

        # Test basics
        s = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
        )
        t = p(s).get('x.t')
        self.assertEqual(t.name(), 't')
        self.assertEqual(t.qname(), 'x.t')
        self.assertEqual(t.unit(), None)
        self.assertEqual(t.binding(), 'time')

        s = (
            '[[model]]',
            '[x]',
            't = 0',
            '    bind time',
        )
        t = p(s).get('x.t')
        self.assertEqual(t.name(), 't')
        self.assertEqual(t.qname(), 'x.t')
        self.assertEqual(t.unit(), None)
        self.assertEqual(t.binding(), 'time')

        s = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'x1 = 5'
        )
        v = p(s).get('x.x1')
        self.assertIsInstance(v, myokit.Variable)
        self.assertTrue(v.is_constant())
        self.assertTrue(v.is_literal())
        self.assertFalse(v.is_state())
        self.assertFalse(v.is_intermediary())
        self.assertEqual(v.unit(), None)
        self.assertEqual(v.rhs().unit(), None)

        s = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'x2 = 5 [mV]'
        )
        v = p(s).get('x.x2')
        self.assertIsInstance(v, myokit.Variable)
        self.assertTrue(v.is_constant())
        self.assertTrue(v.is_literal())
        self.assertFalse(v.is_state())
        self.assertFalse(v.is_intermediary())
        self.assertEqual(v.unit(), None)
        self.assertEqual(v.rhs().unit(), myokit.parse_unit('mV'))

        s = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'x3 = 5',
            '    in [mV]',
        )
        v = p(s).get('x.x3')
        self.assertIsInstance(v, myokit.Variable)
        self.assertTrue(v.is_constant())
        self.assertTrue(v.is_literal())
        self.assertFalse(v.is_state())
        self.assertFalse(v.is_intermediary())
        self.assertEqual(v.unit(), myokit.parse_unit('mV'))
        self.assertEqual(v.rhs().unit(), None)

        s = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'x3 = 5 in [mV]',
        )
        v = p(s).get('x.x3')
        self.assertIsInstance(v, myokit.Variable)
        self.assertTrue(v.is_constant())
        self.assertTrue(v.is_literal())
        self.assertFalse(v.is_state())
        self.assertFalse(v.is_intermediary())
        self.assertEqual(v.unit(), myokit.parse_unit('mV'))
        self.assertEqual(v.rhs().unit(), None)

        s = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'x4 = 5 [V] : This is x4',
        )
        v = p(s).get('x.x4')
        self.assertIsInstance(v, myokit.Variable)
        self.assertTrue(v.is_constant())
        self.assertTrue(v.is_literal())
        self.assertFalse(v.is_state())
        self.assertFalse(v.is_intermediary())
        self.assertEqual(v.unit(), None)
        self.assertEqual(v.rhs().unit(), myokit.units.V)
        self.assertEqual(v.meta['desc'], 'This is x4')

        code = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'x = 5 label vvv',
        )
        x = p(code).get('x.x')
        self.assertIsInstance(x, myokit.Variable)
        self.assertEqual(x.label(), 'vvv')

        s = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'x = 5',
            '    label vvv',
        )
        x = p(code).get('x.x')
        self.assertIsInstance(x, myokit.Variable)
        self.assertEqual(x.label(), 'vvv')

        # Illegal lhs
        code = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'sin(x) = 5',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'variable names or the dot', p, code)

        # Duplicate name
        code = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'x = 5',
            'x = 5',
        )
        self.assertRaisesRegex(myokit.ParseError, 'Duplicate var', p, code)

        # Missing initial value
        code = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            'dot(x) = 5',
        )
        self.assertRaisesRegex(myokit.ParseError, 'Missing initial', p, code)

        # Duplicate meta
        code = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            '    yes: really',
            '    yes: no',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'Duplicate meta-data key', p, code)

        # Duplicate unit
        code = (
            '[[model]]',
            '[x]',
            't = 0 bind time',
            '    in [s]',
            '    in [s]',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'Duplicate variable unit', p, code)

    def test_parse_unit(self):
        # Test :meth:`parse_unit` and :meth:`parse_unit_string`.
        from myokit._parsing import parse_unit_string as p

        # Test dimensionless
        self.assertEqual(p('1'), myokit.units.dimensionless)

        # Test bare unit
        self.assertEqual(p('V'), myokit.units.Volt)

        # Test unit with quantifier
        self.assertEqual(p('mV'), myokit.units.Volt / 1000)

        # Test multiplied units
        self.assertEqual(p('V*A'), myokit.units.Volt * myokit.units.Ampere)
        self.assertEqual(p('J/s'), myokit.units.Watt)
        self.assertEqual(p('1/s'), 1 / myokit.units.second)

        # Test units with exponents (first unit)
        self.assertEqual(p('m^2'), myokit.units.meter ** 2)
        self.assertEqual(p('m^-1'), 1 / myokit.units.meter)
        # Exponents on remaining units
        self.assertEqual(
            p('s*m^2'), myokit.units.second * myokit.units.meter ** 2)
        self.assertEqual(
            p('s*m^-1'), myokit.units.second / myokit.units.meter)

        # Test units with multipliers
        self.assertEqual(p('m (123)'), myokit.units.meter * 123)

        # Test bad unit
        self.assertRaisesRegex(
            myokit.ParseError, 'Unit not recognized', p, 'michael')
        self.assertRaisesRegex(
            myokit.ParseError, 'Unit not recognized', p, 'kg/michael')
        self.assertRaisesRegex(
            myokit.ParseError, 'Unexpected token', p, '*2')
        self.assertRaisesRegex(
            myokit.ParseError, 'Invalid unit specification', p, '2')
        self.assertRaisesRegex(
            myokit.ParseError, 'Invalid unit multiplier', p, 'm (x)')

    def test_parse_protocol(self):
        # Test :meth:`parse_protocol()`.
        from myokit._parsing import parse_protocol

        # Test simple
        # Level   Start   Length  Period  Multiplier
        code = (
            '[[protocol]]\n',
        )
        protocol = parse_protocol(code)
        self.assertIsInstance(protocol, myokit.Protocol)
        protocol = parse_protocol(''.join(code))
        self.assertIsInstance(protocol, myokit.Protocol)

        code = (
            '[[protocol]]\n',
            '0 0 1 0 0\n',
        )
        protocol = parse_protocol(code)
        self.assertIsInstance(protocol, myokit.Protocol)

        # Funny numbers
        code = ('[[protocol]]\n', '-1 0 1 0 0\n')
        protocol = parse_protocol(code)
        self.assertIsInstance(protocol, myokit.Protocol)
        code = ('[[protocol]]\n', '-1 0 1e3 0 0\n')
        protocol = parse_protocol(code)
        self.assertIsInstance(protocol, myokit.Protocol)
        code = ('[[protocol]]\n', '-1 0 1e3 1000 +3\n')
        protocol = parse_protocol(code)
        self.assertIsInstance(protocol, myokit.Protocol)
        code = ('[[protocol]]\n', '0.1 0 1 0 0\n')
        protocol = parse_protocol(code)
        self.assertIsInstance(protocol, myokit.Protocol)
        code = ('[[protocol]]\n', '0.1e-2 0 1 0 0\n')
        protocol = parse_protocol(code)
        self.assertIsInstance(protocol, myokit.Protocol)
        code = ('[[protocol]]\n', '.1e-2 0 1 0 0\n')
        protocol = parse_protocol(code)
        self.assertIsInstance(protocol, myokit.Protocol)

        # Not a protocol
        code = (
            '[[protcle]]\n',
            '0 0 1 0 0\n',
        )
        self.assertRaisesRegex(
            myokit.ParseError, r'Expecting \[\[protocol]]',
            parse_protocol, code)

        # Not a protocol (in stream)
        from myokit._parsing import parse_protocol_from_stream, Tokenizer
        stream = Tokenizer(iter(code))
        self.assertRaisesRegex(
            myokit.ParseError, r'Expecting \[\[protocol]]',
            parse_protocol_from_stream, stream)

        # Test using 'next'
        code = (
            '[[protocol]]\n',
            '00 0 100 0 0\n',
            '10 next 100 0 0\n',
            '20 next 100 0 0\n',
        )
        p1 = parse_protocol(code)
        code = (
            '[[protocol]]\n',
            '00 0 100 0 0\n',
            '10 100 100 0 0\n',
            '20 200 100 0 0\n',
        )
        p2 = parse_protocol(code)
        self.assertEqual(p1.code(), p2.code())

        # Test invalid use of next (after periodic event)
        code = (
            '[[protocol]]\n',
            '00 0 100 1000 0\n',
            '10 next 100 0 0\n',
        )
        self.assertRaisesRegex(
            myokit.ProtocolParseError, 'Invalid next', parse_protocol, code)

        # Simultaneous events
        code = (
            '[[protocol]]\n',
            '00 0 100 0 0\n',
            '10 0 100 0 0\n',
        )
        self.assertRaisesRegex(
            myokit.ProtocolParseError, 'same time', parse_protocol, code)
        code = (
            '[[protocol]]\n',
            '00 0 100 1000 0\n',
            '10 0 1100 0 0\n',
        )
        self.assertRaisesRegex(
            myokit.ProtocolParseError, 'same time', parse_protocol, code)

        # Wrong order
        code = (
            '[[protocol]]\n',
            '0 10 1 0 0\n',
            '1 0  1 0 0\n',
        )
        self.assertRaisesRegex(
            myokit.ProtocolParseError, 'chronological', parse_protocol, code)

        # Duration <= 0
        code = ('[[protocol]]\n', '0 10 -1 0 0\n')
        self.assertRaisesRegex(
            myokit.ProtocolParseError, 'Invalid duration',
            parse_protocol, code)
        code = ('[[protocol]]\n', '0 10 0 0 0\n')
        self.assertRaisesRegex(
            myokit.ProtocolParseError, 'Invalid duration',
            parse_protocol, code)

        # Negative period
        code = ('[[protocol]]\n', '0 10 1 -1 0\n')
        self.assertRaisesRegex(
            myokit.ProtocolParseError, 'Negative period',
            parse_protocol, code)

        # Negative multiplier
        # Multiplier for non-periodic event
        code = ('[[protocol]]\n', '0 10 1 100 -1\n')
        self.assertRaisesRegex(
            myokit.ProtocolParseError, 'Negative multiplier',
            parse_protocol, code)

        # Multiplier for non-periodic event
        code = ('[[protocol]]\n', '0 10 1 0 1\n')
        self.assertRaisesRegex(
            myokit.ProtocolParseError, 'Invalid multiplier',
            parse_protocol, code)

        # Found a bug when parsing this
        code = (
            '[[protocol]]\n',
            '-80     next    300     0       0\n',
            '-120    3196.0  50.0    0       0\n',
        )
        parse_protocol(code)

    def test_parse_script(self):
        # Test :meth:`parse_script()`.
        from myokit._parsing import parse_script

        # Test simple
        code = (
            '[[script]]',
        )
        script = parse_script(code)
        self.assertIsInstance(script, basestring)
        script = parse_script(''.join(code))
        self.assertIsInstance(script, basestring)

        code = (
            '[[script]]\n',
        )
        script = parse_script(code)
        self.assertIsInstance(script, basestring)

        code = (
            '[[script]]\n',
            'print("hi")',
        )
        script = parse_script(code)
        self.assertIsInstance(script, basestring)

        code = (
            '[[script]]\n',
            'print("hi")\n',
        )
        script = parse_script(code)
        self.assertIsInstance(script, basestring)

        # Not a script
        code = (
            '[[hello]]\n',
            'print("hi")\n',
        )
        self.assertRaisesRegex(
            myokit.ParseError, r'Expecting \[\[script]]', parse_script, code)

        # Not a script, parsing from stream
        from myokit._parsing import Tokenizer, parse_script_from_stream
        raw = iter(code)
        stream = Tokenizer(raw)
        self.assertRaisesRegex(
            myokit.ParseError, r'Expecting \[\[script]]',
            parse_script_from_stream, stream, raw)

    def test_split(self):
        # Test split(), uses parse()
        from myokit._parsing import split

        # Test horrible scenario
        code = [
            '',
            '',
            '[[model]]',
            '',
            'Bad model',
            '',
            '',
            '',
            '[[protocol]]',
            '',
            '',
            '1 1 1 1 1',
            '',
            '',
            '4 4 4 4 4',
            'no'
            '',
            '',
            '[[script]]',
            '',
            '',
        ]
        m, p, x = split('\n'.join(code))
        self.assertEqual(m, '\n'.join(code[:8]))
        self.assertEqual(p, '\n'.join(code[8:17]))
        self.assertEqual(x, '\n'.join(code[17:-1]))

        # Scenario 2
        code[17] = '[[scrubbed]]'
        m, p, x = split('\n'.join(code))
        self.assertEqual(m, '\n'.join(code[:8]))
        self.assertEqual(p, '\n'.join(code[8:-1]))

    def test_unexpected_token(self):
        # Test :meth:`unexpected_token`.
        import myokit._parsing as p

        # code, text, line, char
        token = p.AND, 'and', 10, 5

        # Test with string expectation
        self.assertRaisesRegex(
            myokit.ParseError, 'expecting the spanish inquisition',
            p.unexpected_token, token, 'the spanish inquisition')

        # Test with one expected type
        self.assertRaisesRegex(
            myokit.ParseError, 'expecting End of line',
            p.unexpected_token, token, p.EOL)

        # Test with two expected type
        self.assertRaisesRegex(
            myokit.ParseError, 'expecting End of line or End of file',
            p.unexpected_token, token, [p.EOL, p.EOF])

        # Test with many expected type
        self.assertRaisesRegex(
            myokit.ParseError,
            r'expecting one of \[Plus "\+", Minus "-", Star "\*"]',
            p.unexpected_token, token, [p.PLUS, p.MINUS, p.STAR])

    def test_parse_expression(self):
        # Test parse_expression()
        from myokit import parse_expression as p
        from myokit import Number
        e = p('5')
        self.assertIsInstance(e, Number)
        self.assertEqual(e.eval(), 5.0)
        self.assertEqual(float(e), 5.0)
        e = p('5[m]')
        self.assertIsInstance(e, Number)
        self.assertEqual(e.eval(), 5.0)
        self.assertEqual(float(e), 5.0)
        self.assertEqual(e.unit(), myokit.units.m)
        e = p('5 [m/s]')
        self.assertIsInstance(e, Number)
        self.assertEqual(e.eval(), 5.0)
        self.assertEqual(float(e), 5.0)
        self.assertEqual(e.unit(), myokit.parse_unit('m/s'))
        self.assertEqual(e.unit(), myokit.units.m / myokit.units.s)
        e = p('+5')
        self.assertIsInstance(e, myokit.PrefixPlus)
        self.assertEqual(e.eval(), 5.0)
        e = p('++5')
        self.assertIsInstance(e, myokit.PrefixPlus)
        self.assertEqual(e.eval(), 5.0)
        e = p('-5')
        self.assertIsInstance(e, myokit.PrefixMinus)
        self.assertEqual(e.eval(), -5.0)
        e = p('--5')
        self.assertIsInstance(e, myokit.PrefixMinus)
        self.assertEqual(e.eval(), 5.0)
        e = p('5 + 2')
        self.assertIsInstance(e, myokit.Plus)
        self.assertEqual(e.eval(), 7)
        e = p('5 + 1 + 1')
        self.assertIsInstance(e, myokit.Plus)
        self.assertEqual(e.eval(), 7)
        e = p('5 - 2')
        self.assertIsInstance(e, myokit.Minus)
        self.assertEqual(e.eval(), 3)
        e = p('5 -- 2')
        self.assertIsInstance(e, myokit.Minus)
        self.assertEqual(e.eval(), 7)
        e = p('5 --+ 2')
        self.assertIsInstance(e, myokit.Minus)
        self.assertEqual(e.eval(), 7)
        e = p('5 --- 2')
        self.assertIsInstance(e, myokit.Minus)
        self.assertEqual(e.eval(), 3)
        # Etc etc etc

        # Test bad value
        self.assertRaises(myokit.ParseError, p, '5 beans')

    def test_parse_expression_string(self):
        # Test :meth:`parse_expression_string()`.
        from myokit._parsing import parse_expression_string
        e = parse_expression_string('5 --- 2')
        self.assertIsInstance(e, myokit.Minus)
        self.assertEqual(e.eval(), 3)

        # Only a single expression can be given
        self.assertRaisesRegex(
            myokit.ParseError, 'Unexpected token INTEGER',
            parse_expression_string, '5 + 2 3 * 7')

    def test_parse_state(self):
        # Test parse_state()
        # Further tests in test_loadsave

        # Test basic
        from myokit._parsing import parse_state
        self.assertEqual(parse_state(''), [])

        code = (
            '1.23\n',
        )
        self.assertEqual(parse_state(code), [1.23])

        code = (
            '1.23\n',
            '5.67',
        )
        self.assertEqual(parse_state(code), [1.23, 5.67])

        code = (
            'x.y = 1.23\n',
        )
        self.assertEqual(parse_state(code), {'x.y': 1.23})

        code = (
            'x.y = 1.23\n',
            'x.z = 2.34',
        )
        self.assertEqual(parse_state(code), {'x.y': 1.23, 'x.z': 2.34})

        # Must use fully qualified names
        code = (
            'x = 5',
        )
        self.assertRaisesRegex(
            myokit.ParseError, 'must be fully qualified', parse_state, code)

    def test_format_parse_error(self):
        # Test format_parse_error.

        # Test basic formatting, with and without source
        bad = '    5 + / 2'
        try:
            myokit.parse_expression(bad)
        except myokit.ParseError as e:

            # No source
            self.assertEqual(
                myokit.format_parse_error(e),
                '\n'.join([
                    'Syntax error',
                    '  Unexpected token SLASH "/" expecting expression',
                    'On line 1 character 8',
                ])
            )

            # List-of-strings source
            self.assertEqual(
                myokit.format_parse_error(e, source=[bad]),
                '\n'.join([
                    'Syntax error',
                    '  Unexpected token SLASH "/" expecting expression',
                    'On line 1 character 8',
                    '  5 + / 2',
                    '      ^'
                ])
            )

            # File source
            with TemporaryDirectory() as d:
                path = d.path('mmt')
                with open(path, 'w') as f:
                    f.write(bad + '\n')
                myokit.format_parse_error(e, source=path),
                '\n'.join([
                    'Syntax error',
                    '  Unexpected token SLASH "/" expecting expression',
                    'On line 1 character 8',
                    '  5 + / 2',
                    '      ^'
                ])

            # Line doesn't exist in source
            self.assertEqual(
                myokit.format_parse_error(e, source=[]),
                '\n'.join([
                    'Syntax error',
                    '  Unexpected token SLASH "/" expecting expression',
                    'On line 1 character 8',
                ])
            )

            # Char doesn't exist in source
            self.assertEqual(
                myokit.format_parse_error(e, source=['x']),
                '\n'.join([
                    'Syntax error',
                    '  Unexpected token SLASH "/" expecting expression',
                    'On line 1 character 8',
                ])
            )

        # Very long lines
        bad = '    1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 100 + 1000 + 11'
        bad += ' + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20 + 21 + 22'
        bad += ' + 23 + 24 + 25 + 26 + 27 + 28 + 29 + 30 + 31'

        # Error near start
        error = '\n'.join([
            'Syntax error',
            '  Unexpected token SLASH "/" expecting expression',
            'On line 1 character 12',
            '  1 + 2 + / 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 100 + 1000 + ..',
            '          ^',
        ])
        b = bad[:12] + '/ ' + bad[12:]
        try:
            myokit.parse_expression(b)
        except myokit.ParseError as e:
            self.assertEqual(myokit.format_parse_error(e, source=[b]), error)

        error = '\n'.join([
            'Syntax error',
            '  Unexpected token SLASH "/" expecting expression',
            'On line 1 character 83',
            '  ..+ 12 + 13 + 14 + 15 + / 16 + 17 + 18 + 19 + 20 + 21 + 22..',
            '                          ^',
        ])
        b = bad[:83] + '/ ' + bad[83:]
        try:
            myokit.parse_expression(b)
        except myokit.ParseError as e:
            self.assertEqual(myokit.format_parse_error(e, source=[b]), error)

        error = '\n'.join([
            'Syntax error',
            '  Unexpected token SLASH "/" expecting expression',
            'On line 1 character 133',
            '  ..+ 21 + 22 + 23 + 24 + 25 + / 26 + 27 + 28 + 29 + 30 + 31',
            '                               ^',
        ])
        b = bad[:133] + '/ ' + bad[133:]
        try:
            myokit.parse_expression(b)
        except myokit.ParseError as e:
            self.assertEqual(myokit.format_parse_error(e, source=[b]), error)


class ModelParseTest(unittest.TestCase):
    def test_model_creation(self):
        m = myokit.load_model(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Test components
        self.assertEqual(len(m), 9)
        self.assertIn('engine', m)
        self.assertIn('membrane', m)
        self.assertIn('cell', m)
        self.assertIn('ina', m)
        self.assertIn('ik1', m)
        self.assertIn('ica', m)
        self.assertIn('ib', m)
        self.assertIn('ik', m)
        self.assertIn('ikp', m)

        # Test state
        states = [
            'membrane.V',
            'ina.m',
            'ina.h',
            'ina.j',
            'ica.d',
            'ica.f',
            'ik.x',
            'ica.Ca_i']
        values = [
            -84.5286,
            0.0017,
            0.9832,
            0.995484,
            0.000003,
            1,
            0.0057,
            0.0002]
        out = ', '.join([str(x) for x in m.states()])
        ref = ', '.join(states)
        self.assertEqual(ref, out)
        for k, eq in enumerate(m.inits()):
            self.assertEqual(eq.rhs.eval(), values[k])

        # Test state parsing / setting
        m.set_state(values)
        for k, eq in enumerate(m.inits()):
            self.assertEqual(eq.rhs.eval(), values[k])
        s = dict(zip(states, values))
        m.set_state(s)
        for k, eq in enumerate(m.inits()):
            self.assertEqual(eq.rhs.eval(), values[k])
        s = '\n'.join([str(a) + '=' + str(b) for a, b in s.items()])
        m.set_state(s)
        for k, eq in enumerate(m.inits()):
            self.assertEqual(eq.rhs.eval(), values[k])

        # Test cloning
        try:
            m2 = m.clone()
        except Exception as e:
            s = m.code(line_numbers=True)
            print('\n')
            print(s)
            print('-' * 80)
            print(myokit.format_parse_error(e, s.splitlines()))
            raise e
        self.assertEqual(m.code(), m2.code())

    def test_unresolved_reference_error(self):
        # Test unresolved reference errors.
        code = """
            [[model]]

            [engine]
            time = 0 bind time

            [c]
            x = a
            """
        self.assertRaises(myokit.ParseError, myokit.parse, code)
        try:
            myokit.parse(code)
        except myokit.ParseError as e:
            self.assertIsInstance(e.cause, myokit.IntegrityError)
            self.assertIsInstance(e.cause, myokit.UnresolvedReferenceError)
            # Token is not set when resolving name (string)
            self.assertIsNone(e.cause.token())
            # But line and char should be set in parse error by parser
            self.assertEqual(e.line, 8)
            self.assertEqual(e.char, 16)
            # Check str() method (only implemented for parse errors)
            str(e)

    def test_cyclical_reference_error(self):
        # Test cyclical reference errors.

        code = """
            [[model]]

            [engine]
            time = 0 bind time

            [c]
            x = y
            y = x
            """
        self.assertRaises(myokit.ParseError, myokit.parse, code)
        with self.assertRaises(myokit.ParseError) as e:
            myokit.parse(code)
        e = e.exception
        self.assertIsInstance(e.cause, myokit.IntegrityError)
        self.assertIsInstance(e.cause, myokit.CyclicalDependencyError)
        self.assertIn(e.line, [8, 9])
        self.assertEqual(e.char, 12)
        from myokit._parsing import NAME
        if e.line == 8:
            self.assertEqual(e.cause.token(), (NAME, 'x', 8, 12))
        else:
            self.assertEqual(e.cause.token(), (NAME, 'y', 9, 12))

    def test_piecewise(self):
        # Test a model with a piecewise statement

        m = myokit.load_model(
            os.path.join(DIR_DATA, 'conditional.mmt'))
        # Test evaluation
        x = m.get('test.x')
        y = m.get('test.y')
        s = m.state()
        i = m.get('membrane.V').indice()
        # Test x, xo, y, yo
        s[i] = -80
        m.set_state(s)
        self.assertEqual(x.rhs().eval(), 3)
        self.assertEqual(y.rhs().eval(), 2)
        s[i] = -10
        m.set_state(s)
        self.assertEqual(x.rhs().eval(), 2)
        self.assertEqual(y.rhs().eval(), 2)
        s[i] = 30
        m.set_state(s)
        self.assertEqual(x.rhs().eval(), 1)
        self.assertEqual(y.rhs().eval(), 1)
        # Test code() output by cloning
        m.clone()

    def test_initial_values(self):
        # Test if expressions for initial values are handled correctly.

        code = """
            [[model]]
            c.p = 1.0
            c.q = 10 * 2

            [engine]
            time = 0 bind time

            [c]
            dot(p) = 1
            dot(q) = 2
            """
        myokit.parse(code)

        # Non-literal value
        code = """
            [[model]]
            c.p = 1.0
            c.q = 10 * 2 + b

            [engine]
            time = 0 bind time

            [c]
            dot(p) = 1
            dot(q) = 2
            """
        self.assertRaises(myokit.ParseError, myokit.parse, code)

    def test_aliases(self):
        code = """
            [[model]]

            [engine]
            time = 0 bind time

            [c]
            p = 1

            [d]
            use c.p
            q = 2 * p

            [e]
            use c.p as ploep
            r = 10 * ploep
            """
        myokit.parse(code)

        # Duplicate alias is allowed
        code = """
            [[model]]

            [engine]
            time = 0 bind time

            [c]
            p = 1

            [d]
            use c.p as one
            use c.p as two
            q = 2 * one
            """
        myokit.parse(code)

        # Duplicate name
        code = """
            [[model]]

            [engine]
            time = 0 bind time

            [c]
            p = 1

            [d]
            q = 10
            use c.p as q
            """
        self.assertRaises(myokit.ParseError, myokit.parse, code)

        # API Alias
        m = myokit.Model('InvalidNameAlias')
        c = m.add_component('c')
        p = c.add_variable('p')
        p.set_rhs('4 / 20')
        q = c.add_variable('q')
        q.set_rhs('-sqrt(3)')
        d = m.add_component('d')
        r = d.add_variable('r')
        r.set_rhs('1 / 1e2')
        d.add_alias('p', p)

        # Invalid name
        self.assertRaises(myokit.InvalidNameError, d.add_alias, '_plf', q)

        # Duplicate names
        self.assertRaises(myokit.DuplicateName, d.add_alias, 'p', q)
        self.assertRaises(myokit.DuplicateName, c.add_alias, 'p', r)

    def test_clone_code_parse(self):
        # Test the cloning, code and parse() by exporting models and
        # reading them in again.
        models = [
            'conditional.mmt',
        ]
        for model in models:
            m1 = myokit.load_model(os.path.join(DIR_DATA, model))
            c1 = m1.code()
            m2 = myokit.parse(c1)[0]
            c2 = m2.code()
            self.assertEqual(c1, c2)
            m3 = m2.clone()
            c3 = m3.code()
            self.assertEqual(c1, c3)

    def test_advanced_units(self):
        # Test the new unit syntax where literals have units.
        model = 'beeler-1977-units.mmt'
        m = myokit.load_model(os.path.join(DIR_DATA, model))
        m.validate()

    def test_unresolved_references(self):
        # Test parsing models with unresolved references.
        m = """
            [[model]]

            [c]
            t = 0 bind time
            x = 5
            """
        myokit.parse_model(m)

        # Bad variable in same component
        m = """
            [[model]]

            [c]
            t = 0 bind time
            x = 5
            y = z
            """
        self.assertRaises(myokit.ParseError, myokit.parse_model, m)

        # Bad component
        m = """
            [[model]]

            [c]
            t = 0 bind time
            x = 5
            y = d.z
            """
        self.assertRaises(myokit.ParseError, myokit.parse_model, m)

        # Bad variable in other component
        m = """
            [[model]]

            [c]
            t = 0 bind time
            x = 5
            y = d.b

            [d]
            a = 12
            """
        self.assertRaises(myokit.ParseError, myokit.parse_model, m)

    def test_invalid_dot_in_rhs(self):
        # Test parsing a model with an invalid dot() in a variable's RHS.

        # This model has dot(1 - x), which is not allowed!
        code = """
            [[model]]
            c.x = 0

            [engine]
            time = 0 bind time

            [c]
            dot(x) = 1 - x
            p = dot(1 - x)
            """
        self.assertRaisesRegex(
            myokit.ParseError, 'only be used on variables', myokit.parse, code)

    def test_strip_expression_units(self):
        # Test :meth:`strip_expression_units`.
        from myokit._parsing import parse_model, strip_expression_units

        m1 = myokit.load_model('example')
        m2 = parse_model(m1.code())
        self.assertEqual(m1.code(), m2.code())

        m2 = parse_model(strip_expression_units(m1.code()))
        c1 = m1.code()
        c2 = m2.code()
        self.assertNotEqual(c1, c2)
        self.assertTrue(len(c2) < len(c1))
        self.assertEqual(
            m1.evaluate_derivatives(), m2.evaluate_derivatives())

        m2 = parse_model(strip_expression_units(m1.code().splitlines()))
        c1 = m1.code()
        c2 = m2.code()
        self.assertNotEqual(c1, c2)
        self.assertTrue(len(c2) < len(c1))
        self.assertEqual(
            m1.evaluate_derivatives(), m2.evaluate_derivatives())

    def test_function_parsing(self):
        # Test parsing of functions.

        # Test simple function
        m = """
            [[model]]

            [c]
            t = 0 bind time
            x = asin(sin(1))
            """
        m = myokit.parse_model(m)
        self.assertAlmostEqual(m.get('c.x').eval(), 1)

        # Test function with multiple arguments
        m = """
            [[model]]

            [c]
            t = 0 bind time
            x = log(8, 2)
            """
        m = myokit.parse_model(m)
        self.assertAlmostEqual(m.get('c.x').eval(), 3)

        # Unknown function
        m = """
            [[model]]

            [c]
            t = 0 bind time
            x = blog(8, 2)
            """
        self.assertRaisesRegex(
            myokit.ParseError, 'Unknown function', myokit.parse_model, m)

        # Wrong number of arguments
        m = """
            [[model]]

            [c]
            t = 0 bind time
            x = sin(8, 2)
            """
        self.assertRaisesRegex(
            myokit.ParseError, 'Wrong number of arguments', myokit.parse_model,
            m)


if __name__ == '__main__':
    unittest.main()
