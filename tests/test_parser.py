#!/usr/bin/env python
#
# Tests the parser
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.units

from shared import DIR_DATA

# Strings in Python2 and Python3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str


class TokenizerTest(unittest.TestCase):
    def test_tokenizer(self):
        import myokit._parser as p
        from myokit._parser import Tokenizer
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


class PhasedParseTest(unittest.TestCase):
    def test_parse_expression(self):
        """
        Test parse_expression()
        """
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

    def test_parse_state(self):
        """
        Test parse_state(), uses parse_expression()
        """
        pass    # TODO

    def test_parse_variable(self):
        """
        Tests parse_variable(), uses parse_expression()
        """
        from myokit._parser import parse_variable
        from myokit._parser import Tokenizer
        m = myokit.Model('test_model')
        c = m.add_component('test_component')

        def p(s, name=None):
            parse_variable(Tokenizer(s), None, c, convert_proto_rhs=True)
            if name:
                return c.var(name)

        s = """
            x1 = 5
            """
        v = p(s, 'x1')
        self.assertIsInstance(v, myokit.Variable)
        self.assertTrue(v.is_constant())
        self.assertTrue(v.is_literal())
        self.assertFalse(v.is_state())
        self.assertFalse(v.is_intermediary())
        self.assertEqual(v.unit(), None)
        self.assertEqual(v.rhs().unit(), None)
        s = """
            x2 = 5 [mV]
            """
        v = p(s, 'x2')
        self.assertIsInstance(v, myokit.Variable)
        self.assertTrue(v.is_constant())
        self.assertTrue(v.is_literal())
        self.assertFalse(v.is_state())
        self.assertFalse(v.is_intermediary())
        self.assertEqual(v.unit(), None)
        self.assertEqual(v.rhs().unit(), myokit.parse_unit('mV'))
        s = """
            x3 = 5
                in [mV]
            """
        v = p(s, 'x3')
        self.assertIsInstance(v, myokit.Variable)
        self.assertTrue(v.is_constant())
        self.assertTrue(v.is_literal())
        self.assertFalse(v.is_state())
        self.assertFalse(v.is_intermediary())
        self.assertEqual(v.unit(), myokit.parse_unit('mV'))
        self.assertEqual(v.rhs().unit(), None)
        s = """
            x4 = 5 [V] : This is x4
            """
        v = p(s, 'x4')
        self.assertIsInstance(v, myokit.Variable)
        self.assertTrue(v.is_constant())
        self.assertTrue(v.is_literal())
        self.assertFalse(v.is_state())
        self.assertFalse(v.is_intermediary())
        self.assertEqual(v.unit(), None)
        self.assertEqual(v.rhs().unit(), myokit.units.V)
        self.assertEqual(v.meta['desc'], 'This is x4')

    def test_parse_component(self):
        """
        Test parse_component(), uses parse_variable
        """
        from myokit._parser import parse_component as pc
        from myokit._parser import ParseInfo
        from myokit._parser import Tokenizer
        info = ParseInfo()
        info.model = m = myokit.Model('test_model')

        def p(s, name=None):
            pc(Tokenizer(s), info)
            if name:
                return m[name]

        s = """
            [test_component]
            x = 5 + b
                b = 13
                in [mV]
            desc: \"""
            This is a test component.
            \"""
            """
        c = p(s, 'test_component')
        self.assertEqual(len(c), 1)
        self.assertIn('desc', c.meta)
        self.assertEqual(c.meta['desc'], 'This is a test component.')
        pass

    def test_parse(self):
        """
        Test parse()
        """
        pass    # TODO

    def test_split(self):
        """
        Test split(), uses parse()
        """
        pass    # TODO


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
        """
        Tests unresolved reference errors.
        """
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
        """
        Tests cyclical reference errors.
        """
        code = """
            [[model]]

            [engine]
            time = 0 bind time

            [c]
            x = y
            y = x
            """
        self.assertRaises(myokit.ParseError, myokit.parse, code)
        try:
            myokit.parse(code)
        except myokit.ParseError as e:
            self.assertIsInstance(e.cause, myokit.IntegrityError)
            self.assertIsInstance(e.cause, myokit.CyclicalDependencyError)
            self.assertEqual(e.line, 9)
            self.assertEqual(e.char, 12)
            from myokit._parser import NAME
            self.assertEqual(e.cause.token(), (NAME, 'y', 9, 12))

    def test_piecewise(self):
        """
        Tests a model with a piecewise statement
        """
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
        """
        Tests if expressions for initial values are handled correctly.
        """
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
        """
        Tests the cloning, code and parse() by exporting models and
        reading them in again.
        """
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
        """
        Tests the new unit syntax where literals have units.
        """
        model = 'br-1977-units.mmt'
        m = myokit.load_model(os.path.join(DIR_DATA, model))
        m.validate()

    def test_unresolved_references(self):
        """
        Tests parsing models with unresolved references.
        """
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
        """
        Tests parsing a model with an invalid dot() in a variable's RHS.
        """
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
            myokit.ParseError, 'named variables', myokit.parse, code)


#TODO: Add tests for protocol parsing. Found a bug when parsing this:
#
#  [[protocol]]
#   -80     next    300     0
#   -120    3196.0  50.0    0       0
#


if __name__ == '__main__':
    unittest.main()
