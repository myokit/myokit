#!/usr/bin/env python3
#
# Tests the CellML 1.0/1.1 writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import re
import unittest

import myokit
import myokit.formats.cellml.v1 as cellml

from myokit.tests import TemporaryDirectory, WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class TestCellMLWriter(unittest.TestCase):
    """ Tests for cellml.Writer. """

    def test_cmeta_ids(self):
        # Tests cmeta ids are written for models, components, and variables

        m1 = cellml.Model('m')
        m1.set_cmeta_id('modell')
        c1 = m1.add_component('c')
        c1.set_cmeta_id('commponnent')
        v1 = c1.add_variable('v', 'volt')
        v1.set_cmeta_id('variiable')
        v1.set_initial_value(3)

        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)

        self.assertEqual(m2.cmeta_id(), 'modell')
        self.assertEqual(m2['c'].cmeta_id(), 'commponnent')
        self.assertEqual(m2['c']['v'].cmeta_id(), 'variiable')

    def test_component(self):
        # Tests if components are written

        m1 = cellml.Model('m')
        c = m1.add_component('c')
        d = m1.add_component('d')

        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)

        self.assertIn('c', m2)
        self.assertIn('d', m2)

    def test_connections(self):
        # Tests if connections are written

        m1 = cellml.Model('m')
        c = m1.add_component('c')
        d = m1.add_component('d')
        p = c.add_variable('p', 'mole', public_interface='out')
        q = d.add_variable('q', 'mole', public_interface='in')
        r = c.add_variable('r', 'ampere', public_interface='in')
        s = d.add_variable('r', 'ampere', public_interface='out')
        p.set_initial_value(1)
        s.set_initial_value(2)
        m1.add_connection(p, q)
        m1.add_connection(r, s)

        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)

        p = m2['c']['p']
        q = m2['d']['q']
        r = m2['c']['r']
        s = m2['d']['r']
        self.assertIsNone(p.source())
        self.assertIs(q.source(), p)
        self.assertIs(r.source(), s)
        self.assertIsNone(s.source())

    def test_evaluating_derivatives(self):
        # Writes and then parses a model and compares the derivatives

        m1 = myokit.load_model('example')
        c1 = cellml.Model.from_myokit_model(m1)
        xml = cellml.write_string(c1)
        c2 = cellml.parse_string(xml)
        m2 = c2.myokit_model()

        self.assertEqual(
            m1.get('membrane.V').eval(), m2.get('membrane.V').eval())
        self.assertEqual(m1.get('ina.m').eval(), m2.get('ina.m').eval())
        self.assertEqual(m1.get('ina.h').eval(), m2.get('ina.h').eval())
        self.assertEqual(m1.get('ina.j').eval(), m2.get('ina.j').eval())
        self.assertEqual(m1.get('ica.d').eval(), m2.get('ica.d').eval())
        self.assertEqual(m1.get('ica.f').eval(), m2.get('ica.f').eval())
        self.assertEqual(m1.get('ik.x').eval(), m2.get('ik.x').eval())
        self.assertEqual(m1.get('ica.Ca_i').eval(), m2.get('ica.Ca_i').eval())

    def test_groups(self):
        # Tests if encapsulation relationships are written out.

        # Create a model with
        #      d
        #   a     e
        #       f   c
        #             b
        #
        m1 = cellml.Model('m')
        a = m1.add_component('a')
        b = m1.add_component('b')
        c = m1.add_component('c')
        d = m1.add_component('d')
        e = m1.add_component('e')
        f = m1.add_component('f')
        a.set_parent(d)
        e.set_parent(d)
        f.set_parent(e)
        c.set_parent(e)
        b.set_parent(c)

        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)
        a, b, c, d, e, f = [m2.component(x) for x in 'abcdef']
        self.assertIs(a.parent(), d)
        self.assertIs(e.parent(), d)
        self.assertIs(f.parent(), e)
        self.assertIs(c.parent(), e)
        self.assertIs(b.parent(), c)

    def test_initial_value_representation(self):
        # Test the way initial values are represented in generated CellML code

        def find(xml):
            i = xml.index(b'initial_value')
            i += 15
            j = xml.index(b'"', i)
            return xml[i:j].decode()

        m = cellml.Model('m', '1.0')
        c = m.add_component('c')
        p = c.add_variable('p', 'mole')

        p.set_initial_value(1.234)
        x = find(cellml.write_string(m))
        self.assertEqual(x, '1.234')

        p.set_initial_value(1e-6)
        x = find(cellml.write_string(m))
        self.assertEqual(x, '1e-06')

        p.set_initial_value(1e9)
        x = find(cellml.write_string(m))
        self.assertEqual(x, '1.00000000000000000e+09')

        # String e+00
        p.set_initial_value(1.23424352342423)
        x = find(cellml.write_string(m))
        self.assertEqual(x, '1.23424352342422994')

    def test_maths(self):
        # Test maths is written

        self._test_maths('1.0')
        self._test_maths('1.1')

    def _test_maths(self, version):
        # Test maths is written in either 1.0 or 1.1

        # Create model
        m1 = cellml.Model('m', version)
        c1 = m1.add_component('c')
        p1 = c1.add_variable('p', 'mole')
        p1.set_initial_value(2)
        q1 = c1.add_variable('q', 'dimensionless')
        r1 = c1.add_variable('r', 'second')
        r1.set_is_state(True)
        r1.set_initial_value(0.1)
        t1 = c1.add_variable('t', 'second')
        m1.set_free_variable(t1)

        # Add component without maths
        d1 = m1.add_component('d')
        s1 = d1.add_variable('s', 'volt')
        s1.set_initial_value(1.23)

        # Add two rhs equations
        eq1 = myokit.Plus(myokit.Number(3, myokit.units.mole), myokit.Name(p1))
        # Note: Numbers without units become dimensionless in CellML
        er1 = myokit.Power(myokit.Name(q1), myokit.Number(2))
        q1.set_rhs(eq1)
        r1.set_rhs(er1)

        # Write and read
        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)

        # Check results
        p2, q2, r2, s2 = m2['c']['p'], m2['c']['q'], m2['c']['r'], m2['d']['s']
        subst = {
            myokit.Name(p1): myokit.Name(p2),
            myokit.Name(q1): myokit.Name(q2),
        }
        eq2 = eq1.clone(subst)
        er2 = er1.clone(subst)
        self.assertEqual(q2.rhs(), eq2)
        self.assertEqual(r2.rhs(), er2)
        self.assertEqual(s2.initial_value(), 1.23)
        self.assertFalse(p2.is_state())
        self.assertFalse(q2.is_state())
        self.assertTrue(r2.is_state())
        self.assertFalse(s2.is_state())
        self.assertIs(m2.free_variable(), m2['c']['t'])

    def test_model(self):
        # Tests model writing

        m1 = cellml.Model('model_name')
        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)

        self.assertEqual(m2.name(), 'model_name')
        self.assertEqual(len(m2), 0)

    def test_ordering(self):
        # Tests ordering of components and variables

        # Check component ordering
        m = cellml.Model('m')
        c = m.add_component('C')
        a = m.add_component('A')
        d = m.add_component('D')
        b = m.add_component('B')

        xml = cellml.write_string(m)
        reg = re.compile(br'<component [^>]*name="[\w]+"')
        items = reg.findall(xml)
        items_sorted = list(sorted(items))
        self.assertEqual(items, items_sorted)

        # Check variable ordering
        m = cellml.Model('m')
        c = m.add_component('C')
        r = c.add_variable('r', 'volt')
        p = c.add_variable('p', 'ampere')
        s = c.add_variable('s', 'kilogram')
        q = c.add_variable('q', 'mole')
        r.set_initial_value(1)
        p.set_initial_value(1)
        s.set_initial_value(1)
        q.set_initial_value(1)

        xml = cellml.write_string(m)
        reg = re.compile(br'<variable [^>]*name="[\w]+"')
        items = reg.findall(xml)
        items_sorted = list(sorted(items))
        self.assertEqual(items, items_sorted)

    def test_oxmeta_annotations(self):
        # Tests if oxmeta annotations are written

        # Create mini model
        m = cellml.Model('m')
        c = m.add_component('c')
        v = c.add_variable('v', 'volt')
        v.set_rhs(myokit.Number(0, myokit.units.volt))

        # Test no RDF is written without oxmeta or cmeta
        xml = cellml.write_string(m)
        self.assertNotIn(b'rdf:RDF', xml)

        v.meta['oxmeta'] = 'membrane_voltage'
        xml = cellml.write_string(m)
        self.assertNotIn(b'rdf:RDF', xml)

        del v.meta['oxmeta']
        v.set_cmeta_id('vvv')
        xml = cellml.write_string(m)
        self.assertNotIn(b'rdf:RDF', xml)

        # Test it is written if both are set
        v.meta['oxmeta'] = 'membrane_voltage'
        xml = cellml.write_string(m)
        self.assertIn(b'rdf:RDF', xml)

        # Test reading it again with the parser
        m2 = cellml.parse_string(xml)
        v2 = m2['c']['v']
        self.assertEqual(v2.cmeta_id(), 'vvv')
        self.assertIn('oxmeta', v2.meta)
        self.assertEqual(v2.meta['oxmeta'], 'membrane_voltage')

    def test_units(self):
        # Test writing of units

        u1 = myokit.parse_unit('kg*m^2/mole^3 (0.123)')
        u2 = myokit.parse_unit('1 (4.56)')

        m1 = cellml.Model('mmm')
        m1.add_units('flibbit', u1)
        m1.add_units('special_volt', myokit.units.Volt)
        c = m1.add_component('ccc')
        c.add_units('flibbit', u2)
        p = c.add_variable('p', 'flibbit')
        p.set_rhs(myokit.Number(1, u2))
        d = m1.add_component('ddd')
        q = d.add_variable('q', 'flibbit')
        q.set_rhs(myokit.Number(2, u1))

        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)

        p, q = m2['ccc']['p'], m2['ddd']['q']
        self.assertEqual(p.units().name(), 'flibbit')
        self.assertEqual(q.units().name(), 'flibbit')
        self.assertEqual(p.units().myokit_unit(), u2)
        self.assertEqual(q.units().myokit_unit(), u1)
        self.assertEqual(
            m2.find_units('special_volt').myokit_unit(), myokit.units.volt)

    def test_variable(self):
        # Tests writing of variables

        m1 = cellml.Model('m')
        c = m1.add_component('c')
        p = c.add_variable('p', 'mole')
        q = c.add_variable('q', 'kelvin', public_interface='in')
        r = c.add_variable('r', 'ampere', private_interface='out')
        p.set_initial_value(1)

        with WarningCollector():
            xml = cellml.write_string(m1)
            m2 = cellml.parse_string(xml)

        p, q, r = m2['c']['p'], m2['c']['q'], m2['c']['r']
        self.assertEqual(p.units().name(), 'mole')
        self.assertEqual(q.units().name(), 'kelvin')
        self.assertEqual(r.units().name(), 'ampere')
        self.assertEqual(p.public_interface(), 'none')
        self.assertEqual(q.public_interface(), 'in')
        self.assertEqual(r.public_interface(), 'none')
        self.assertEqual(p.private_interface(), 'none')
        self.assertEqual(q.private_interface(), 'none')
        self.assertEqual(r.private_interface(), 'out')
        self.assertEqual(p.initial_value(), 1)
        self.assertEqual(q.initial_value(), None)
        self.assertEqual(r.initial_value(), None)

    def test_version(self):
        # Tests if both versions can be written

        # Version 1.0
        m1 = cellml.Model('m', version='1.0')
        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)
        self.assertEqual(m2.version(), '1.0')

        # Version 1.1
        m1 = cellml.Model('m', version='1.1')
        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)
        self.assertEqual(m2.version(), '1.1')

    def test_write_file(self):
        # Tests write_file

        m1 = cellml.Model('ernie')
        with TemporaryDirectory() as d:
            path = d.path('test.cellml')
            cellml.write_file(path, m1)
            m2 = cellml.parse_file(path)

        self.assertEqual(m2.name(), 'ernie')
        self.assertEqual(len(m2), 0)

    def test_write_string(self):
        # Tests write_string

        m1 = cellml.Model('ernie')
        xml = cellml.write_string(m1)
        m2 = cellml.parse_string(xml)

        self.assertEqual(m2.name(), 'ernie')
        self.assertEqual(len(m2), 0)


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
