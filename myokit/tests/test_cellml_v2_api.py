#!/usr/bin/env python3
#
# Tests the CellML 2.0 API.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.formats.cellml.v2 as cellml

from myokit.tests import WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python2 and Python3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str


class TestCellML2AnnotatableElement(unittest.TestCase):
    """ Tests for ``cellml.v2.AnnotatableElement``. """

    def test_annotatable(self):
        # Test making an annotation

        m = cellml.Model('m')
        m.meta['x'] = 'y'
        self.assertEqual(m.meta['x'], 'y')


class TestCellML2Component(unittest.TestCase):
    """ Tests for ``cellml.v2.Component``. """

    def test_creation(self):
        # Test component creation

        m = cellml.Model('m')
        c = m.add_component('c')

        self.assertRaisesRegex(
            cellml.CellMLError, 'valid CellML identifier',
            m.add_component, '123')

    def test_add_get_variable(self):
        # Tests adding and getting variables

        # Test adding
        m = cellml.Model('m')
        c = m.add_component('c')
        self.assertEqual(len(c), 0)
        v = c.add_variable('v', 'volt')
        self.assertEqual(len(c), 1)

        # Test getting
        self.assertIs(c.variable('v'), v)

        # Test adding duplicate
        self.assertRaisesRegex(
            cellml.CellMLError, 'unique', c.add_variable, 'v', 'metre')

        # Test iteration over all
        w = c.add_variable('w', 'volt')
        vs = [x for x in c.variables()]
        self.assertEqual(len(vs), 2)
        self.assertIn(v, vs)
        self.assertIn(w, vs)

        # Rest of creation is tested in variable test

    def test_model(self):
        # Tests Component.model()

        m = cellml.Model('m')
        c = m.add_component('pixie')
        self.assertIs(c.model(), m)

    def test_name(self):
        # Tests Component.name()

        m = cellml.Model('m')
        c = m.add_component('trixie')
        self.assertIs(c.name(), 'trixie')

    def test_sequence_interface(self):
        # Tests the sequence interface on a component

        m = cellml.Model('m')
        a = m.add_component('Stacey')
        b = m.add_component('Jane')
        c = m.add_component('Mary_jo_lisa')
        self.assertIs(a, m['Stacey'])
        self.assertIs(b, m['Jane'])
        self.assertIs(c, m['Mary_jo_lisa'])
        self.assertIn('Stacey', m)
        self.assertIn('Jane', m)
        self.assertIn('Mary_jo_lisa', m)
        self.assertEqual(len(m), 3)

    def test_set_get_parent(self):
        # Tests setting and getting of parents

        # Test getting
        m = cellml.Model('m')
        a = m.add_component('Stacey')
        b = m.add_component('Jane')
        c = m.add_component('Mary')
        d = m.add_component('Jo')
        e = m.add_component('Lisa')
        self.assertIsNone(a.parent())
        self.assertIsNone(b.parent())
        self.assertIsNone(c.parent())
        self.assertIsNone(d.parent())
        self.assertIsNone(e.parent())
        self.assertFalse(a.has_children())
        self.assertFalse(b.has_children())
        self.assertFalse(c.has_children())
        self.assertFalse(d.has_children())
        self.assertFalse(e.has_children())
        self.assertEqual(len(list(a.children())), 0)
        self.assertEqual(len(list(b.children())), 0)
        self.assertEqual(len(list(c.children())), 0)
        self.assertEqual(len(list(e.children())), 0)
        self.assertEqual(len(list(e.children())), 0)

        # Test setting
        b.set_parent(a)
        c.set_parent(b)
        d.set_parent(c)
        e.set_parent(c)
        self.assertIsNone(a.parent())
        self.assertIs(b.parent(), a)
        self.assertIs(c.parent(), b)
        self.assertIs(d.parent(), c)
        self.assertIs(e.parent(), c)
        self.assertTrue(a.has_children())
        self.assertTrue(b.has_children())
        self.assertTrue(c.has_children())
        self.assertFalse(d.has_children())
        self.assertFalse(e.has_children())
        self.assertEqual(len(list(a.children())), 1)
        self.assertEqual(len(list(b.children())), 1)
        self.assertEqual(len(list(c.children())), 2)
        self.assertEqual(len(list(d.children())), 0)
        self.assertEqual(len(list(e.children())), 0)
        self.assertIn(b, list(a.children()))
        self.assertIn(c, list(b.children()))
        self.assertIn(d, list(c.children()))
        self.assertIn(e, list(c.children()))

        # Test bad parent
        self.assertRaisesRegex(ValueError, 'cellml.Component', b.set_parent, m)
        m2 = cellml.Model('m2')
        c2 = m2.add_component('c2')
        self.assertRaisesRegex(ValueError, 'same model', b.set_parent, c2)

    def test_string_conversion(self):
        # Tests Component.__str__

        m = cellml.Model('mm')
        c = m.add_component('xx')
        self.assertEqual(str(c), 'Component[@name="xx"]')

    def test_validation(self):
        # Tests component validation

        # Test cyclical encapsulation detection
        m = cellml.Model('m')
        a = m.add_component('Stacey')
        b = m.add_component('Jane')
        c = m.add_component('Mary_jo_lisa')
        a.set_parent(b)
        b.set_parent(c)
        c.set_parent(a)
        self.assertRaisesRegex(cellml.CellMLError, 'circular', m.validate)
        c.set_parent(None)
        m.validate()


class TestCellML2Model(unittest.TestCase):
    """ Tests for ``cellml.Model``. """

    def test_add_find_units(self):
        # Tests adding and finding units

        m = cellml.Model('m')

        # Test getting non-existent
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown', m.find_units, 'wooster')

        # Test adding
        u = m.add_units('wooster', myokit.units.lumen)
        self.assertEqual(m.find_units('wooster'), u)

        # Test doubles are not allowed
        self.assertRaisesRegex(
            cellml.CellMLError, 'same name',
            m.add_units, 'wooster', myokit.units.meter)

        # Test iteration
        w = m.add_units('jarvis', myokit.units.meter)
        us = [unit for unit in m.units()]
        self.assertEqual(len(us), 2)
        self.assertIn(u, us)
        self.assertIn(w, us)

        # Test finding names (finds the last added with that unit)
        self.assertEqual(m.find_units_name(myokit.units.meter), 'jarvis')
        self.assertEqual(m.find_units_name(myokit.units.volt), 'volt')
        self.assertRaisesRegex(
            cellml.CellMLError, 'No name found for myokit unit',
            m.find_units_name, 1 / myokit.units.volt)

    def test_add_get_component(self):
        # Tests adding and getting components

        # Test adding
        m = cellml.Model('m')
        self.assertEqual(len(m), 0)
        c = m.add_component('c')
        self.assertEqual(len(m), 1)

        # Test getting
        self.assertIs(m.component('c'), c)

        # Test adding duplicate
        self.assertRaisesRegex(
            cellml.CellMLError, 'unique', m.add_component, 'c')

        # Test iteration over all
        d = m.add_component('d')
        cs = [x for x in m.components()]
        self.assertEqual(len(cs), 2)
        self.assertIn(c, cs)
        self.assertIn(d, cs)

        # Rest of creation is tested in component test

    def test_add_connection(self):
        # Tests adding connections

        # Test setting connections
        #   a--b     c
        #      |     |
        #      d--e  f,g
        m = cellml.Model('m')
        ca = m.add_component('a')
        cb = m.add_component('b')
        cc = m.add_component('c')
        cd = m.add_component('d')
        ce = m.add_component('e')
        cf = m.add_component('f')
        cd.set_parent(cb)
        ce.set_parent(cb)
        cf.set_parent(cc)

        # Sibling connection
        a = ca.add_variable('a', 'volt', 'public')
        b = cb.add_variable('b', 'volt', 'public_and_private')
        m.add_connection(a, b)
        d = cd.add_variable('d', 'volt', 'public')
        e = ce.add_variable('e', 'volt', 'public')
        m.add_connection(d, e)

        # Parent-child connections
        m.add_connection(b, d)
        c = cc.add_variable('c', 'volt', 'private')
        f = cf.add_variable('f', 'volt', 'public')
        m.add_connection(c, f)

        # Check original connections can be retrieved
        citer = m.connections()
        self.assertEqual(next(citer), (a, b))
        self.assertEqual(next(citer), (d, e))
        self.assertEqual(next(citer), (b, d))
        self.assertEqual(next(citer), (c, f))
        self.assertRaises(StopIteration, next, citer)

        # Invalid sibling connections
        self.assertRaisesRegex(
            cellml.CellMLError, 'variable_2 requires the public interface',
            m.add_connection, b, c)
        self.assertRaisesRegex(
            cellml.CellMLError, 'variable_1 requires the public interface',
            m.add_connection, c, b)

        # Invalid parent-child connections
        g = cf.add_variable('g', 'volt', 'none')
        self.assertRaisesRegex(
            cellml.CellMLError, 'variable_2 requires the public interface',
            m.add_connection, c, g)
        self.assertRaisesRegex(
            cellml.CellMLError, 'variable_1 requires the public interface',
            m.add_connection, g, c)

        # Hidden set
        self.assertRaisesRegex(
            cellml.CellMLError, 'siblings or have a parent-child relationship',
            m.add_connection, a, d)
        self.assertRaisesRegex(
            cellml.CellMLError, 'siblings or have a parent-child relationship',
            m.add_connection, g, b)

        # Connected to self
        self.assertRaisesRegex(
            cellml.CellMLError, 'cannot be connected to themselves',
            m.add_connection, a, a)

        # Connected in the same component
        self.assertRaisesRegex(
            cellml.CellMLError, 'in the same component',
            m.add_connection, f, g)

        # Connected twice
        self.assertRaisesRegex(
            cellml.CellMLError, 'connected twice',
            m.add_connection, a, b)
        self.assertRaisesRegex(
            cellml.CellMLError, 'connected twice',
            m.add_connection, b, a)

        # Connected twice, triangle b,d,e
        self.assertRaisesRegex(
            cellml.CellMLError, 'connected twice',
            m.add_connection, b, e)
        self.assertRaisesRegex(
            cellml.CellMLError, 'connected twice',
            m.add_connection, e, b)

        # Units must be compatible
        m.add_units('millivolt', myokit.units.mV)
        q = cb.add_variable('q', 'ampere', 'public')
        r = cb.add_variable('r', 'millivolt', 'public')
        self.assertRaisesRegex(
            cellml.CellMLError, 'must have compatible units',
            m.add_connection, a, q)
        m.add_connection(a, r)

        # Not a variable or wrong model
        m = cellml.Model('m')
        a = m.add_component('a')
        b = m.add_component('b')
        c = m.add_component('c')
        c.set_parent(b)
        x = a.add_variable('x', 'volt', 'public')
        y = b.add_variable('y', 'volt', 'public_and_private')
        z = c.add_variable('z', 'volt', 'public')
        self.assertRaisesRegex(
            ValueError, 'variable_1 must be a cellml.v2.Variable.',
            m.add_connection, 'x', y)
        self.assertRaisesRegex(
            ValueError, 'variable_2 must be a cellml.v2.Variable.',
            m.add_connection, y, 'x')
        self.assertRaisesRegex(
            ValueError, 'variable_1 must be a variable from',
            m.add_connection, g, y)
        self.assertRaisesRegex(
            ValueError, 'variable_2 must be a variable from',
            m.add_connection, y, g)

    def test_add_connection_overdetermined(self):
        # Tests overdeterminedness checks when connecting variables

        m = cellml.Model('m')
        c1 = m.add_component('c1')
        c2 = m.add_component('c2')

        # Two equations
        a = c1.add_variable('a', 'volt', 'public')
        b = c2.add_variable('b', 'volt', 'public')
        a.set_equation(myokit.Equation(myokit.Name(a), myokit.Number(1)))
        b.set_equation(myokit.Equation(myokit.Name(b), myokit.Number(1)))
        self.assertRaisesRegex(
            cellml.CellMLError, 'ultiple equations defined in connected',
            m.add_connection, a, b)
        a.set_equation(None)
        b.set_equation(None)

        # Two initial values
        a.set_initial_value(3)
        b.set_initial_value(3)
        self.assertRaisesRegex(
            cellml.CellMLError, 'ultiple initial values defined in connected',
            m.add_connection, a, b)

    def test_clone(self):
        # Tests Model cloning

        # Create full-featured test model
        m1 = cellml.Model('hello')
        m1.add_units('bort', myokit.parse_unit('V/s^2'))
        m1.add_units('suzuki', myokit.parse_unit('1/mole'))
        a = m1.add_component('a')
        b = m1.add_component('b')
        c = m1.add_component('c')
        c.set_parent(b)
        p = a.add_variable('p', 'volt')
        q = a.add_variable('q', 'suzuki', 'public_and_private')
        r = b.add_variable('r', 'suzuki', 'public')
        s = b.add_variable('s', 'bort', 'public_and_private')
        t = c.add_variable('t', 'bort', 'public')
        u = c.add_variable('u', 'bort')
        p.set_initial_value(3)
        q.set_equation(myokit.Equation(
            myokit.Derivative(myokit.Name(q)),
            myokit.Plus(myokit.Name(p), myokit.Name(q))))
        m1.add_connection(q, r)
        r.set_initial_value(2)
        m1.add_connection(s, t)
        t.set_equation(myokit.Equation(myokit.Name(t), myokit.Name(u)))
        u.set_initial_value(1.2)
        z1 = a.add_variable('time', 'second', 'public')
        z2 = b.add_variable('time', 'second', 'public_and_private')
        z3 = c.add_variable('time', 'second', 'public')
        m1.set_variable_of_integration(z3)
        m1.add_connection(z1, z2)
        m1.add_connection(z2, z3)
        m1.meta['x'] = 'y'
        a.meta['a'] = 'yes'
        b.meta['x'] = 'no'
        z1.meta['desc'] = 'A variable'
        z1.meta['test'] = 'bork'
        z3.meta['howdy'] = 'yup'
        m1.validate()

        # Clone
        m2 = m1.clone()

        # Check
        def check_meta(x, y):
            for k, v in x.meta.items():
                self.assertIn(k, y.meta)
                self.assertEqual(v, y.meta[k])

        # Check basic model properties
        self.assertEqual(m1.name(), m2.name())
        check_meta(m1, m2)

        # Check components
        for c1 in m1:
            self.assertIn(c1.name(), m2)
            c2 = m2[c1.name()]
            check_meta(c1, c2)

            # Check encapsulation
            if c1.parent() is None:
                self.assertIsNone(c2.parent())
            else:
                self.assertEqual(c1.parent().name(), c2.parent().name())

            # Check variables
            for v1 in c1:
                self.assertIn(v1.name(), c2)
                v2 = c2[v1.name()]
                check_meta(v1, v2)
                self.assertEqual(v1.interface(), v2.interface())
                self.assertEqual(v1.units().name(), v2.units().name())
                self.assertEqual(
                    v1.units().myokit_unit(),
                    v2.units().myokit_unit())

        # Check connections
        seen = set()
        for c1 in m1:
            c2 = m2[c1.name()]
            for v1 in c1:
                if v1 in seen:
                    continue
                seen.add(v1)

                v2 = c2[v1.name()]
                v2_pals = [x.name() for x in v2.connected_variables()]
                for w1 in v1.connected_variables():
                    seen.add(w1)
                    w2 = m2[w1.component().name()][w1.name()]
                    self.assertIn(w2.name(), v2_pals)

        # Check equations and initial values
        for c1 in m1:
            c2 = m2[c1.name()]
            for v1 in c1:
                v2 = c2[v1.name()]
                #self.assertEqual(v1.is_local(), v2.is_local())

                self.assertEqual(v1.has_equation(), v2.has_equation())
                if v1.has_equation():
                    self.assertEqual(
                        v1.equation_variable().name(),
                        v2.equation_variable().name())
                    if v1 is v1.equation_variable():
                        self.assertEqual(
                            str(v1.equation()), str(v2.equation()))

                self.assertEqual(
                    v1.has_initial_value(), v2.has_initial_value())
                if v1.has_initial_value():
                    self.assertEqual(
                        v1.initial_value_variable().name(),
                        v2.initial_value_variable().name())
                    if v1 is v1.initial_value_variable():
                        self.assertEqual(
                            str(v1.initial_value()), str(v2.initial_value()))

        # Check variable of integration
        voi_1 = m1.variable_of_integration()
        voi_2 = m2.variable_of_integration()
        if voi_1 is None:
            self.assertIsNone(voi_2)
        else:
            self.assertEqual(str(voi_1), str(voi_2))

    def test_creation(self):
        # Tests Model creation

        m = cellml.Model('hiya')

        # Test bad name
        self.assertRaisesRegex(
            cellml.CellMLError, 'valid CellML identifier', cellml.Model, '1e2')

        # Test bad version
        self.assertRaisesRegex(
            ValueError, 'supported', cellml.Model, 'm', '1.0')
        self.assertRaisesRegex(
            ValueError, 'supported', cellml.Model, 'm', '1.1')
        self.assertRaisesRegex(
            ValueError, 'supported', cellml.Model, 'm', '1.2')
        self.assertRaisesRegex(
            ValueError, 'supported', cellml.Model, 'm', '2.1')

    def test_name(self):
        # Tests Model.name().

        m = cellml.Model('Stacey')
        self.assertEqual(m.name(), 'Stacey')

    def test_sequence_interface(self):
        # Tests the sequence interface on a model

        m = cellml.Model('m')
        a = m.add_component('Stacey')
        x = a.add_variable('x', 'volt')
        y = a.add_variable('y', 'volt')
        z = a.add_variable('z', 'volt')
        self.assertIs(a['x'], x)
        self.assertIs(a['y'], y)
        self.assertIs(a['z'], z)
        self.assertIn('x', a)
        self.assertIn('y', a)
        self.assertIn('z', a)
        self.assertEqual(len(a), 3)

    def test_string_conversion(self):
        # Tests Model.__str__

        m = cellml.Model('mm')
        self.assertEqual(str(m), 'Model[@name="mm"]')

    def test_validation(self):
        # Tests Model.validate(), doesn't check _validate methods

        # More than one variable without a definition
        m = cellml.Model('m')
        c1 = m.add_component('c1')
        x = c1.add_variable('x', 'mole', 'public')
        y = c1.add_variable('y', 'mole')
        c2 = m.add_component('c2')
        z = c2.add_variable('z', 'mole', 'public')
        with WarningCollector() as w:
            m.validate()
        warn = w.text()
        self.assertIn('No value set for Variable[@name="x"]', warn)
        self.assertIn('No value set for Variable[@name="y"]', warn)
        self.assertIn('No value set for Variable[@name="z"]', warn)
        self.assertIn('More than one variable does not have a value', warn)

        # Two without a definition
        z.set_initial_value(3)
        with WarningCollector() as w:
            m.validate()
        warn = w.text()
        self.assertIn('No value set for Variable[@name="x"]', warn)
        self.assertIn('No value set for Variable[@name="y"]', warn)
        self.assertIn('More than one variable does not have a value', warn)
        self.assertNotIn('No value set for Variable[@name="z"]', warn)

        # Only one without a definition, via connection
        m.add_connection(x, z)
        with WarningCollector() as w:
            m.validate()
        warn = w.text()
        self.assertIn('No value set for Variable[@name="y"]', warn)
        self.assertNotIn('More than one variable does not have a value', warn)

        # Variable of integration must be free
        m = cellml.Model('m')
        c = m.add_component('c')
        x = c.add_variable('x', 'volt')
        t = c.add_variable('t', 'second', 'public')
        x.set_equation(myokit.Equation(
            myokit.Derivative(myokit.Name(x)),
            myokit.Divide(
                myokit.Number(1, myokit.units.volt),
                myokit.Number(2, myokit.units.second)
            )))
        x.set_initial_value(3)
        m.set_variable_of_integration(t)
        m.validate()

        # Non-free via equation
        t.set_equation(myokit.Equation(
            myokit.Name(t), myokit.Number(1, myokit.units.second)))
        self.assertRaisesRegex(
            cellml.CellMLError, 'must be a free variable, but has equation.',
            m.validate)
        t.set_equation(None)
        m.validate()

        # Non-free via initial value
        t.set_initial_value(3)
        self.assertRaisesRegex(
            cellml.CellMLError, 'be a free variable, but has initial value.',
            m.validate)
        t.set_initial_value(None)
        m.validate()

        # Same, but now variable_of_integration() returns a variable that
        # doesn't define the equation/initial variable _itself_
        c2 = m.add_component('c2')
        t2 = c2.add_variable('t', 'second', 'public')
        m.add_connection(t, t2)
        m.validate()

        t.set_equation(myokit.Equation(
            myokit.Name(t), myokit.Number(1, myokit.units.second)))
        self.assertRaisesRegex(
            cellml.CellMLError, r'free variable, but has equation \(set by.',
            m.validate)
        t.set_equation(None)
        m.validate()

        # Non-free via initial value
        t.set_initial_value(3)
        self.assertRaisesRegex(
            cellml.CellMLError, r'variable, but has initial value \(set by',
            m.validate)
        t.set_initial_value(None)
        m.validate()

    def test_variable_of_integration(self):
        # Tests setting variable of integration.

        m = cellml.Model('m')
        c1 = m.add_component('c1')
        c2 = m.add_component('c2')
        c3 = m.add_component('c3')
        y1 = c1.add_variable('y1', 'volt')
        y2 = c2.add_variable('y2', 'volt')
        y3 = c3.add_variable('y3', 'volt')
        y1.set_initial_value(1)
        y2.set_initial_value(1)
        y3.set_initial_value(1)
        t1 = c1.add_variable('t', 'dimensionless', 'public')
        t2 = c2.add_variable('t', 'dimensionless', 'public')
        t3 = c3.add_variable('t', 'dimensionless', 'public')

        # No variable set yet
        m.set_variable_of_integration(t1)
        self.assertIs(m.variable_of_integration(), t1)

        # Two variables set
        self.assertRaisesRegex(
            cellml.CellMLError, 'as variable of integration',
            m.set_variable_of_integration, t2)

        # Connected variables set
        m.add_connection(t1, t2)
        m.set_variable_of_integration(t2)
        m.set_variable_of_integration(t2)
        m.set_variable_of_integration(t1)
        self.assertRaisesRegex(
            cellml.CellMLError, 'as variable of integration',
            m.set_variable_of_integration, t3)
        m.add_connection(t2, t3)
        m.set_variable_of_integration(t3)

        # Test variable of integration selection prefers components without
        # state variables
        x1 = c1.add_variable('x', 'dimensionless')
        x2 = c2.add_variable('x', 'dimensionless')
        x3 = c3.add_variable('x', 'dimensionless')
        x1.set_initial_value(3)
        x2.set_initial_value(1)
        x3.set_initial_value(2)
        x1.set_equation(myokit.Equation(
            myokit.Derivative(myokit.Name(x1)),
            myokit.Number(3)))
        x2.set_equation(myokit.Equation(
            myokit.Derivative(myokit.Name(x2)),
            myokit.Number(3.2)))
        self.assertIs(m.variable_of_integration(), t3)

        x2.set_equation(None)
        x3.set_equation(myokit.Equation(
            myokit.Derivative(myokit.Name(x3)),
            myokit.Number(4)))
        self.assertIs(m.variable_of_integration(), t2)

    def test_version(self):
        # TestsModel.version()

        m = cellml.Model('mm', '2.0')
        self.assertEqual(m.version(), '2.0')


class TestCellML2ModelConversion(unittest.TestCase):
    """
    Tests for converting between Myokit and CellML models.
    """

    def model(self, name=None):
        """ Creates and returns a model with a time variable. """
        m = myokit.Model(name)
        t = m.add_component('env').add_variable('time')
        t.set_rhs(myokit.Number(0, myokit.units.ms))
        t.set_unit(myokit.units.ms)
        t.set_binding('time')
        return m

    def test_m2c_model_names(self):
        # Tests name issues when creating a CellML model

        # Test model name is transferred
        m = self.model('test')
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(cm.name(), 'test')
        m = self.model('test model')
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(cm.name(), 'test_model')

        # Test model is renamed if can't clean name
        m = self.model('123')
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(cm.name(), 'unnamed_myokit_model')

        # Test model is ramed if no name given
        m = self.model()
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(cm.name(), 'unnamed_myokit_model')

        # Test duplicate names are solved
        m = self.model()
        c1 = m.add_component('c1')
        c2 = m.add_component('c2')
        x1 = c1.add_variable('x')
        x2 = c2.add_variable('x')
        y = c2.add_variable('y')
        x1.set_rhs(1)
        x2.set_rhs('3 + c1.x')
        y.set_rhs('2 * x')
        cm = cellml.Model.from_myokit_model(m)
        mm = cm.myokit_model()
        self.assertEqual(mm.get('c2.y').eval(), 8)

    def test_m2c_units(self):
        # Test unit issues when creating a CellML model

        m = self.model()
        c1 = m.add_component('c1')
        c2 = m.add_component('c2')
        x1 = c1.add_variable('x')
        x2 = c2.add_variable('x')
        y = c2.add_variable('y')
        x1.set_rhs(1)
        x2.set_rhs('3 + c1.x')
        y.set_rhs('2 * x')
        cm = cellml.Model.from_myokit_model(m)
        mm = cm.myokit_model()

        # Test numbers and variables without units are dimensionless...
        self.assertEqual(cm['c1']['x'].units().name(), 'dimensionless')
        self.assertEqual(
            cm['c2']['y'].rhs(),
            myokit.Multiply(
                myokit.Number(2, myokit.units.dimensionless),
                myokit.Name(cm['c2']['x']))
        )

        # ...or have a unit inferred from their RHS
        z = c2.add_variable('z')
        z.set_rhs('3 [mole/ms]')
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(
            cm['c2']['z'].units().myokit_unit(),
            myokit.units.mole / myokit.units.ms)

        # ...which should take the time units into account, for state variables
        z.promote(0)
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(
            cm['c2']['z'].units().myokit_unit(), myokit.units.mole)

        # ...even if the time units themselves need to be inferred
        m.get('env.time').set_unit(None)
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(
            cm['c2']['z'].units().myokit_unit(), myokit.units.mole)

        # Units can have fractional exponents
        y.set_rhs('1 [mV] ^ 1.2')
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(
            cm['c2']['y'].units().myokit_unit(), myokit.units.mV ** 1.2)

        # If a variable doesn't have units, the RHS will be inspected. This can
        # lead to unit errors, which should be ignored
        y.set_rhs('1 [mV] + 3 [A]')
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(
            cm['c2']['y'].units().myokit_unit(), myokit.units.dimensionless)

    def test_m2c_nested_variables(self):
        # Test nested variables are handled, and name conflicts are handled
        # when creating a CellML model.

        m1 = self.model()
        c1 = m1.add_component('c1')
        c2 = m1.add_component('c2')
        a1 = c1.add_variable('a1')
        a2 = a1.add_variable('a2')
        a3 = a2.add_variable('a3')
        a4 = a3.add_variable('a4')
        a3b = c2.add_variable('a3')
        a3b.set_rhs(10)
        a4.set_rhs('1 + c2.a3')
        a3.set_rhs('1 + a4')
        a2.set_rhs('1 + a3')
        a1.set_rhs('1 + a2')
        cm = cellml.Model.from_myokit_model(m1)
        m2 = cm.myokit_model()
        self.assertEqual(m2.get('c1.a1').eval(), 14)

    def test_m2c_derivatives(self):
        # Test derivative support when creating a CellML model

        # Test references to derivatives
        m = self.model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('log10(1000) + x')
        x.promote(0.1)
        y = c.add_variable('y')
        y.set_rhs('2 * dot(x)')
        cm = cellml.Model.from_myokit_model(m)
        mm = cm.myokit_model()
        self.assertEqual(mm.get('c.y').eval(), 6.2)

    def test_m2c_oxmeta(self):
        # Test that oxmeta data is passed on when creating a CellML model.

        # Test oxmeta data is passed on
        m = self.model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = x.add_variable('y')
        y.set_rhs(1)
        x.set_rhs('1 + y')
        x.meta['oxmeta'] = 'membrane_voltage'
        y.meta['oxmeta'] = 'fish'
        d = m.add_component('d')
        x2 = d.add_variable('x')
        x2.set_rhs(3)
        cm = cellml.Model.from_myokit_model(m)
        self.assertEqual(len(cm['c']['x'].meta), 1)
        self.assertEqual(len(cm['c']['y'].meta), 1)
        self.assertEqual(len(cm['d']['x'].meta), 0)
        self.assertEqual(cm['c']['x'].meta['oxmeta'], 'membrane_voltage')
        self.assertEqual(cm['c']['y'].meta['oxmeta'], 'fish')

        # Test cmeta id is set if variable has oxmeta annotation
        # TODO
        # self.assertEqual(cm['c']['x'].id(), 'c_x')
        # self.assertEqual(cm['c']['y'].id(), 'y')
        # self.assertIsNone(cm['d']['x'].id())

    def test_evaluating_states(self):
        # Test converting to and from CellML doesn't change the state
        # variable evaluations.

        # Test evaluating states of model
        m = myokit.load_model('example')
        cm = cellml.Model.from_myokit_model(m)

        with WarningCollector() as w:
            cm.validate()
        self.assertFalse(w.has_warnings())

        # Recreate myokit model and test states
        mm = cm.myokit_model()
        mm.validate()
        state_1 = m.state()
        state_2 = mm.state()
        states_1 = [x.name() for x in m.states()]
        states_2 = [x.name() for x in mm.states()]
        state_2 = [state_2[states_2.index(x)] for x in states_1]
        self.assertEqual(state_1[0], state_2[0])
        self.assertEqual(state_1[1], state_2[1])
        self.assertEqual(state_1[2], state_2[2])
        self.assertEqual(state_1[3], state_2[3])
        self.assertEqual(state_1[4], state_2[4])
        self.assertEqual(state_1[5], state_2[5])
        self.assertEqual(state_1[6], state_2[6])
        self.assertEqual(state_1[7], state_2[7])

    def test_c2m_basic(self):
        # Tests basic features of conversion to a Myokit model

        # Create model
        m = cellml.Model('m')
        documentation = 'This is the documentation.'
        m.meta['documentation'] = documentation
        a = m.add_component('a')
        a.meta['harry'] = 'wilco'
        b = m.add_component('b')
        c = m.add_component('c')
        c.set_parent(b)
        x = a.add_variable('x', 'volt', 'public')
        xb = b.add_variable('x', 'volt', 'public_and_private')
        xc = c.add_variable('x', 'volt', 'public')
        xc.meta['blue'] = 'yellow'
        y = b.add_variable('y', 'volt')
        z = c.add_variable('z', 'volt')
        m.add_connection(x, xb)
        m.add_connection(xc, xb)
        z2 = c.add_variable('z2', 'metre')
        z2.set_initial_value(4)
        t = a.add_variable('t', 'second')
        t.meta['yes'] = 'no'
        m.set_variable_of_integration(t)

        x.set_equation(myokit.Equation(
            myokit.Derivative(myokit.Name(x)),
            myokit.Number(1, myokit.units.V)))
        x.set_initial_value(0.123)
        y.set_equation(myokit.Equation(
            myokit.Name(y),
            myokit.Plus(myokit.Number(2, myokit.units.V), myokit.Name(xb))))
        z.set_equation(myokit.Equation(
            myokit.Name(z),
            myokit.Plus(myokit.Number(3, myokit.units.V), myokit.Name(xc))))

        # Convert
        mm = m.myokit_model()

        self.assertIsInstance(mm, myokit.Model)
        self.assertEqual(mm.name(), 'm')

        # Check meta data is added
        self.assertIn('author', mm.meta)

        # Check meta data is passed on
        self.assertIn('documentation', mm.meta)
        self.assertEqual(mm.meta['documentation'], documentation)
        self.assertIn('harry', mm.get('a').meta)
        self.assertEqual(mm.get('a').meta['harry'], 'wilco')
        self.assertIn('yes', mm.get('a.t').meta)
        self.assertEqual(mm.get('a.t').meta['yes'], 'no')

        # Check components are present
        ma = mm['a']
        mb = mm['b']
        mc = mm['c']
        self.assertEqual(len(mm), 3)

        # Check variables are present
        mt = ma['t']
        mx = ma['x']
        self.assertEqual(len(ma), 2)
        my = mb['y']
        self.assertEqual(len(mb), 1)
        mz = mc['z']
        mz2 = mc['z2']
        self.assertEqual(len(mc), 2)

        # Check units are set
        self.assertEqual(mt.unit(), myokit.units.second)
        self.assertEqual(mx.unit(), myokit.units.volt)
        self.assertEqual(my.unit(), myokit.units.volt)
        self.assertEqual(mz.unit(), myokit.units.volt)
        self.assertEqual(mz2.unit(), myokit.units.meter)

        # Check equations
        self.assertEqual(mt.rhs(), myokit.Number(0, myokit.units.second))
        self.assertEqual(mx.rhs(), myokit.Number(1, myokit.units.volt))
        self.assertEqual(
            my.rhs(),
            myokit.Plus(myokit.Number(2, myokit.units.volt), myokit.Name(mx)))
        self.assertEqual(
            mz.rhs(),
            myokit.Plus(myokit.Number(3, myokit.units.volt), myokit.Name(mx)))
        self.assertEqual(mz2.rhs(), myokit.Number(4, myokit.units.meter))

        # Check state
        self.assertTrue(mx.is_state())
        self.assertEqual(mx.state_value(), 0.123)

        # Check binding
        self.assertEqual(mt.binding(), 'time')

    def test_c2m_no_voi(self):
        # Test creating a myokit model from a model where there's no variable
        # of integration

        m = cellml.Model('m')
        c = m.add_component('c')
        x = c.add_variable('x', 'second')
        with WarningCollector():
            model = m.myokit_model()
        self.assertIsNotNone(model.time())

        # Try again (test that original model wasn't affected)
        with WarningCollector():
            model = m.myokit_model()
        self.assertIsNotNone(model.time())

        # Setting initial value should stop this variable from becoming the voi
        x.set_initial_value(3)
        model = m.myokit_model()
        self.assertIsNone(model.time())

    def test_c2m_pass_through_variables(self):
        # Test support for variables used only to pass a value through a
        # hierarchical CellML structure.
        #
        #    ax--bx     ax sets value, only dy uses it
        #        |
        #        cx
        #        |
        #        dx,dy

        m = cellml.Model('m')
        a = m.add_component('a')
        b = m.add_component('b')
        c = m.add_component('c')
        d = m.add_component('d')
        c.set_parent(b)
        d.set_parent(c)
        ax = a.add_variable('x', 'volt', 'public')
        bx = b.add_variable('x', 'volt', 'public_and_private')
        cx = c.add_variable('x', 'volt', 'public_and_private')
        dx = d.add_variable('x', 'volt', 'public')
        dy = d.add_variable('y', 'volt')
        m.add_connection(ax, bx)
        m.add_connection(cx, bx)
        m.add_connection(dx, cx)
        ax.set_equation(myokit.Equation(
            myokit.Name(ax), myokit.Number(1, myokit.units.V)))
        dy.set_equation(myokit.Equation(myokit.Name(dy), myokit.Name(dx)))

        # Convert and check
        mm = m.myokit_model()
        self.assertEqual(len(mm), 4)
        self.assertEqual(len(mm['a']), 1)
        self.assertEqual(len(mm['b']), 0)
        self.assertEqual(len(mm['c']), 0)
        self.assertEqual(len(mm['d']), 1)
        self.assertIn('x', mm['a'])
        self.assertIn('y', mm['d'])

    def test_c2m_unit_conversion(self):
        # Test support for unit conversion (and pass-through variables)
        #
        #    a--b
        #       |
        #       c

        # Create model with encapsulation hierarchy
        cm = cellml.Model('m')
        a = cm.add_component('a')
        b = cm.add_component('b')
        c = cm.add_component('c')
        c.set_parent(b)

        # Add some units
        cm.add_units('millivolt', myokit.units.volt * 1e-3)
        cm.add_units('kilovolt', myokit.units.volt * 1e3)
        cm.add_units('millimole', myokit.units.mole * 1e-3)
        cm.add_units('megamole', myokit.units.mole * 1e6)
        cm.add_units('kilowatt', myokit.units.W * 1e3)

        # x requires conversion, and is used in c: it should get a new variable
        # in c with the correct nuits
        ax = a.add_variable('x', 'volt', 'public')
        bx = b.add_variable('x', 'millivolt', 'public_and_private')
        cx = c.add_variable('x', 'kilovolt', 'public')
        ax.set_equation(myokit.Equation(
            myokit.Name(ax), myokit.Number(1, myokit.units.volt)))

        # y does not require conversion, and is used in c: it should not get a
        # new variable in c
        ay = a.add_variable('y', 'ampere', 'public')
        by = b.add_variable('y', 'ampere', 'public_and_private')
        cy = c.add_variable('y', 'ampere', 'public')
        ay.set_equation(myokit.Equation(
            myokit.Name(ay), myokit.Number(2, myokit.units.ampere)))

        # z requires unit conversion, and is not used in c: it should not get a
        # new variable in c
        az = a.add_variable('z', 'mole', 'public')
        bz = b.add_variable('z', 'millimole', 'public_and_private')
        cz = c.add_variable('z', 'megamole', 'public')
        az.set_equation(myokit.Equation(
            myokit.Name(az), myokit.Number(3, myokit.units.mole)))

        # p uses variables
        cp = c.add_variable('p', 'kilowatt')
        cp.set_equation(myokit.Equation(
            myokit.Name(cp),
            myokit.Multiply(myokit.Name(cx), myokit.Name(cy))))

        # Connect variables
        cm.add_connection(ax, bx)
        cm.add_connection(bx, cx)
        cm.add_connection(ay, by)
        cm.add_connection(by, cy)
        cm.add_connection(az, bz)
        cm.add_connection(bz, cz)

        # Convert and check
        m = cm.myokit_model()
        a, b, c = m['a'], m['b'], m['c']

        # Check that pass-through variables have disappeared
        self.assertEqual(len(b), 0)

        # Check rest of variables
        self.assertEqual(len(a), 3)
        self.assertEqual(len(c), 2)
        ax, bx, cx = a['x'], a['y'], a['z']
        cx, cp = c['x'], c['p']

        # Check variable RHS's
        self.assertEqual(ax.rhs().code(), '1 [V]')
        self.assertEqual(ay.rhs().code(), '2 [A]')
        self.assertEqual(az.rhs().code(), '3 [mol]')
        self.assertEqual(
            cx.rhs(),
            myokit.Multiply(
                myokit.Name(ax),
                myokit.Number(1e-3, '1 (1000)')
            )
        )
        self.assertEqual(cp.rhs().code(), 'c.x * a.y')

        # Units should now be good
        m.check_units(mode=myokit.UNIT_STRICT)


class TestCellML2Variable(unittest.TestCase):
    """ Tests for ``cellml.Variable``. """

    def test_creation(self):
        # Tests variable creation

        m = cellml.Model('mmm')
        c = m.add_component('ccc')
        v = c.add_variable('vee', 'metre')

        # Test setting (and getting) interfaces
        self.assertEqual(v.interface(), 'none')
        w = c.add_variable('doubleyou', 'ampere', 'public')
        self.assertEqual(w.interface(), 'public')

        # Test bad name
        self.assertRaisesRegex(
            cellml.CellMLError, 'valid CellML identifier',
            c.add_variable, '', 'metre')

        # Test bad units
        self.assertRaisesRegex(
            cellml.CellMLError, 'units attribute',
            c.add_variable, 'soy_sauce', 'meters')

        # Test bad interface
        self.assertRaisesRegex(
            cellml.CellMLError, 'Interface',
            c.add_variable, 'soy', 'metre', 'republic')

    def test_component_and_model(self):
        # Tests Variable.component() and Variable.model()

        m = cellml.Model('mm')
        c = m.add_component('comp')
        v = c.add_variable('bert', 'metre')
        self.assertIs(v.component(), c)
        self.assertIs(v.model(), m)

    def test_equation_setting(self):
        # Tests Variable.set_equation()

        m = cellml.Model('mm')
        c = m.add_component('c1')
        d = m.add_component('c2')
        x = c.add_variable('bart', 'metre')
        y = c.add_variable('bort', 'volt')
        z = d.add_variable('bert', 'ampere')

        # Test setting of equation
        x.set_equation(None)
        x.set_equation(None)
        lhs = myokit.Name(x)
        rhs = myokit.Plus(myokit.Number(3), myokit.Name(y))
        x.set_equation(myokit.Equation(lhs, rhs))

        # Test numbers without units are replaced with dimensionless ones
        e = x.equation()
        self.assertIsInstance(e.rhs, myokit.Plus)
        self.assertIsInstance(e.rhs[0], myokit.Number)
        self.assertEqual(e.rhs[0].unit(), myokit.units.dimensionless)

        # Test unknown units in numbers are detected
        u = myokit.parse_unit('metre^4 (1.23)')
        rhs = myokit.Plus(myokit.Number(3, u), myokit.Name(y))
        self.assertRaisesRegex(
            cellml.CellMLError, 'All units appearing in a variable',
            x.set_equation, myokit.Equation(lhs, rhs))

        # Test non-local references are detected
        rhs = myokit.Plus(myokit.Number(4), myokit.Name(z))
        self.assertRaisesRegex(
            cellml.CellMLError, 'variables from the same component',
            x.set_equation, myokit.Equation(lhs, rhs))

        # Test equation is an assignment
        lhs = myokit.Multiply(myokit.Number(2), myokit.Name(x))
        self.assertRaisesRegex(
            cellml.CellMLError, 'assignment form',
            x.set_equation, myokit.Equation(lhs, rhs))

        # Test equation sets current variable
        lhs = myokit.Name(y)
        self.assertRaisesRegex(
            cellml.CellMLError, 'Equation for',
            x.set_equation, myokit.Equation(lhs, rhs))

    def test_equation_setting_connected(self):
        # Tests setting of equations on connected variables.

        m = cellml.Model('mm')
        m.add_units('millivolt', myokit.units.mV)
        c = m.add_component('c1')
        d = m.add_component('c2')
        e = m.add_component('c3')
        x = c.add_variable('bart', 'volt', 'public')
        y = d.add_variable('bort', 'millivolt', 'public')
        z = e.add_variable('bert', 'volt', 'public')
        m.add_connection(x, y)
        m.add_connection(y, z)

        # Check current state of variables
        self.assertFalse(x.has_equation())
        self.assertFalse(y.has_equation())
        self.assertFalse(z.has_equation())
        self.assertIsNone(x.equation_variable())
        self.assertIsNone(y.equation_variable())
        self.assertIsNone(z.equation_variable())
        self.assertIsNone(x.equation())
        self.assertIsNone(y.equation())
        self.assertIsNone(z.equation())

        # Set equation for x
        x.set_equation(myokit.Equation(
            myokit.Name(x), myokit.Number(3, myokit.units.volt)))
        self.assertTrue(x.has_equation())
        self.assertTrue(y.has_equation())
        self.assertTrue(z.has_equation())
        self.assertIs(x.equation_variable(), x)
        self.assertIs(y.equation_variable(), x)
        self.assertIs(z.equation_variable(), x)

        # Check unit conversion
        eq1 = x.equation()
        eq2 = y.equation()
        eq3 = z.equation()
        self.assertIsNotNone(eq1)
        self.assertIsNotNone(eq2)
        self.assertIsNotNone(eq3)
        self.assertEqual(eq1.lhs, myokit.Name(x))
        self.assertEqual(eq2.lhs, myokit.Name(y))
        self.assertEqual(eq3.lhs, myokit.Name(z))
        self.assertEqual(eq1.rhs.eval(), eq3.rhs.eval())
        self.assertEqual(eq1.rhs.eval() * 1000, eq2.rhs.eval())

        # Check equation can be unset and set elsewhere
        x.set_equation(None)
        self.assertFalse(x.has_equation())
        self.assertFalse(y.has_equation())
        self.assertFalse(z.has_equation())
        z.set_equation(eq3)
        self.assertTrue(x.has_equation())
        self.assertTrue(y.has_equation())
        self.assertTrue(z.has_equation())
        self.assertIs(x.equation_variable(), z)
        self.assertIs(y.equation_variable(), z)
        self.assertIs(z.equation_variable(), z)

        # Check double equations can't be set
        z.set_equation(eq3)
        z.set_equation(myokit.Equation(eq3.lhs, myokit.Number(123)))
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unable to change equation',
            x.set_equation, eq1)

    def test_initial_value_setting(self):
        # Tests setting of initial values.

        m = cellml.Model('mm')
        m.add_units('millivolt', myokit.units.mV)
        c = m.add_component('c1')
        x = c.add_variable('bart', 'volt', 'public')

        # Not set yet
        self.assertIsNone(x.initial_value())

        # Set with float
        x.set_initial_value(3)
        self.assertTrue(x.has_initial_value())
        self.assertEqual(x.initial_value(), myokit.Number(3, myokit.units.V))

        # Unit is ignored
        x.set_initial_value(myokit.Number(2, myokit.units.dimensionless))
        self.assertEqual(x.initial_value(), myokit.Number(2, myokit.units.V))

        # Unset
        x.set_initial_value(None)
        self.assertIsNone(x.initial_value())

        # Set with other than a number
        self.assertRaisesRegex(
            cellml.CellMLError, 'must be a real number',
            x.set_initial_value, 'twelve')

    def test_initial_value_setting_connection(self):
        # Tests setting of initial values on connected variables.

        m = cellml.Model('mm')
        m.add_units('millivolt', myokit.units.mV)
        c = m.add_component('c1')
        d = m.add_component('c2')
        e = m.add_component('c3')
        x = c.add_variable('bart', 'volt', 'public')
        y = d.add_variable('bort', 'millivolt', 'public')
        z = e.add_variable('bert', 'volt', 'public')
        m.add_connection(x, y)
        m.add_connection(y, z)

        # Check current state of variables
        self.assertFalse(x.has_initial_value())
        self.assertFalse(y.has_initial_value())
        self.assertFalse(z.has_initial_value())
        self.assertIsNone(x.initial_value_variable())
        self.assertIsNone(y.initial_value_variable())
        self.assertIsNone(z.initial_value_variable())
        self.assertIsNone(x.initial_value())
        self.assertIsNone(y.initial_value())
        self.assertIsNone(z.initial_value())

        # Set initial value for x
        x.set_initial_value(300)
        self.assertTrue(x.has_initial_value())
        self.assertTrue(y.has_initial_value())
        self.assertTrue(z.has_initial_value())
        self.assertIs(x.initial_value_variable(), x)
        self.assertIs(y.initial_value_variable(), x)
        self.assertIs(z.initial_value_variable(), x)

        # Check unit conversion
        v1 = x.initial_value()
        v2 = y.initial_value()
        v3 = z.initial_value()
        self.assertIsNotNone(v1)
        self.assertIsNotNone(v2)
        self.assertIsNotNone(v3)
        self.assertEqual(v1.eval(), v3.eval())
        self.assertEqual(v1.eval() * 1000, v2.eval())

        # Check initial value can be unset and set elsewhere
        x.set_initial_value(None)
        self.assertFalse(x.has_initial_value())
        self.assertFalse(y.has_initial_value())
        self.assertFalse(z.has_initial_value())
        z.set_initial_value(v1)
        self.assertTrue(x.has_initial_value())
        self.assertTrue(y.has_initial_value())
        self.assertTrue(z.has_initial_value())
        self.assertIs(x.initial_value_variable(), z)
        self.assertIs(y.initial_value_variable(), z)
        self.assertIs(z.initial_value_variable(), z)

        # Check double initial values can't be set
        z.set_initial_value(v2)
        z.set_initial_value(myokit.Number(200))
        z.set_initial_value(-123)
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unable to change initial value',
            x.set_initial_value, 123)

    def test_is_local_and_is_free(self):
        # Tests Variable.is_local() and Variable.is_free()

        m = cellml.Model('mm')
        m.add_units('millivolt', myokit.units.mV)
        c = m.add_component('c1')
        d = m.add_component('c2')
        x = c.add_variable('bart', 'volt', 'public')
        y = d.add_variable('bort', 'millivolt', 'public')
        m.add_connection(x, y)

        # No equation or variable
        self.assertFalse(x.is_local())
        self.assertFalse(y.is_local())
        self.assertTrue(x.is_free())
        self.assertTrue(y.is_free())

        # Equation set
        x.set_equation(myokit.Equation(myokit.Name(x), myokit.Number(1)))
        self.assertTrue(x.is_local())
        self.assertFalse(y.is_local())
        self.assertFalse(x.is_free())
        self.assertFalse(y.is_free())

        # Equation and initial value set
        y.set_initial_value(4)
        self.assertTrue(x.is_local())
        self.assertFalse(y.is_local())
        self.assertFalse(x.is_free())
        self.assertFalse(y.is_free())

        # Only initial value set
        x.set_equation(None)
        self.assertFalse(x.is_local())
        self.assertTrue(y.is_local())
        self.assertFalse(x.is_free())
        self.assertFalse(y.is_free())

        # Neither set
        y.set_initial_value(None)
        self.assertFalse(x.is_local())
        self.assertFalse(y.is_local())
        self.assertTrue(x.is_free())
        self.assertTrue(y.is_free())

    def test_rhs(self):
        # Tests Variable.rhs().

        m = cellml.Model('mm')
        m.add_units('millivolt', myokit.units.mV)
        c = m.add_component('c1')
        d = m.add_component('c2')
        x = c.add_variable('bart', 'volt', 'public')
        y = d.add_variable('bort', 'volt', 'public')
        m.add_connection(x, y)

        # No equation or variable
        self.assertIsNone(x.rhs())
        self.assertIsNone(y.rhs())

        # Equation set
        x.set_equation(myokit.Equation(myokit.Name(x), myokit.Number(1)))
        self.assertEqual(x.rhs(), y.rhs())
        self.assertEqual(x.rhs(), myokit.Number(1, myokit.units.dimensionless))

        # Equation and initial value set
        y.set_initial_value(4)
        self.assertEqual(x.rhs(), y.rhs())
        self.assertEqual(x.rhs(), myokit.Number(1, myokit.units.dimensionless))

        # Only initial value set
        x.set_equation(None)
        self.assertEqual(x.rhs(), y.rhs())
        self.assertEqual(y.rhs(), myokit.Number(4, myokit.units.V))

        # Neither set
        y.set_initial_value(None)
        self.assertIsNone(x.rhs())
        self.assertIsNone(y.rhs())

    def test_name(self):
        # Tests Variable.name()

        v = cellml.Model('m').add_component('a').add_variable('ernie', 'volt')
        self.assertEqual(v.name(), 'ernie')

    def test_validation(self):
        # Tests variable validation (via their connected sets)

        # State needs initial value
        m = cellml.Model('m')
        m.add_units('v_per_s', myokit.units.volt / myokit.units.second)
        c = m.add_component('c')
        v = c.add_variable('v', 'volt', 'public')
        v.set_equation(myokit.Equation(
            myokit.Derivative(myokit.Name(v)),
            myokit.Number(2, myokit.units.volt / myokit.units.second)))
        self.assertRaisesRegex(
            cellml.CellMLError, 'No initial value set for state', m.validate)
        v.set_initial_value(3)
        m.validate()

        # Non-state can't have equation and initial value
        v.set_equation(myokit.Equation(
            myokit.Name(v), myokit.Number(2, myokit.units.volt)))
        self.assertRaisesRegex(
            cellml.CellMLError, r'both a \(non-ODE\) equation and an initial',
            m.validate)

        # Even if initial value is remote
        v.set_initial_value(None)
        m.validate()
        c2 = m.add_component('c2')
        v2 = c2.add_variable('v', 'volt', 'public')
        v2.set_initial_value(2)
        m.validate()
        m.add_connection(v, v2)
        self.assertRaisesRegex(
            cellml.CellMLError, r'both a \(non-ODE\) equation and an initial',
            m.validate)

    def test_string_conversion(self):
        # Tests Variable.__str__

        v = cellml.Model('m').add_component('c').add_variable('bert', 'metre')
        self.assertEqual(
            str(v), 'Variable[@name="bert"] in Component[@name="c"]')


class TestCellML2Units(unittest.TestCase):
    """ Tests for ``cellml.Units``. """

    def test_creation(self):
        # Test creation

        mv = cellml.Units('millivolt', myokit.units.mV)
        self.assertRaisesRegex(
            cellml.CellMLError, 'valid CellML identifier',
            cellml.Units, '132', myokit.units.mV)
        self.assertRaisesRegex(
            cellml.CellMLError, 'predefined',
            cellml.Units, 'volt', myokit.units.V)
        self.assertRaisesRegex(
            ValueError, 'myokit.Unit',
            cellml.Units, 'wooster', 'mV')

    def test_find(self):
        # Tests predefined unit lookup

        # Test lookup
        v = cellml.Units.find_units('volt')
        self.assertEqual(v.name(), 'volt')
        self.assertEqual(v.myokit_unit(), myokit.units.volt)

        # Test lookup returns same object on repeated calls
        self.assertIs(v, cellml.Units.find_units('volt'))
        self.assertIs(v, cellml.Units.find_units('volt'))

        # Test bad lookup
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown units name',
            cellml.Units.find_units, 'wooster')

    def test_myokit_unit(self):
        # Tests myokit_unit()

        u = cellml.Units('woppa', myokit.units.pA)
        self.assertEqual(u.myokit_unit(), myokit.units.pA)

    def test_name(self):
        # Tests name()

        u = cellml.Units('woppa', myokit.units.m)
        self.assertEqual(u.name(), 'woppa')

    def test_parse_unit_row(self):
        # Tests Units.parse_unit_row().

        # Create model with units
        m = cellml.Model('m')
        c = m.add_component('c')
        m.add_units('wooster', myokit.units.V)

        # Test lookup of predefined and model units
        u = cellml.Units.parse_unit_row('metre')
        self.assertEqual(u, myokit.units.m)
        u = cellml.Units.parse_unit_row('wooster', context=m)
        self.assertEqual(u, myokit.units.V)

        # Test bad lookup
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown units name',
            cellml.Units.parse_unit_row, 'wooster')
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown units name',
            cellml.Units.parse_unit_row, 'muppet', context=m)

        # Test prefixes
        u = cellml.Units.parse_unit_row('metre', 'micro')
        self.assertEqual(u, myokit.parse_unit('um'))
        u = cellml.Units.parse_unit_row('metre', -4)
        self.assertEqual(u, myokit.parse_unit('m (1e-4)'))

        # Test bad prefixes
        self.assertRaisesRegex(
            cellml.CellMLError, 'known prefixes or an integer',
            cellml.Units.parse_unit_row, 'metre', '4.0')
        self.assertRaisesRegex(
            cellml.CellMLError, 'known prefixes or an integer',
            cellml.Units.parse_unit_row, 'metre', 'forty')
        self.assertRaisesRegex(
            cellml.CellMLError, 'known prefixes or an integer',
            cellml.Units.parse_unit_row, 'metre', 14.8)
        self.assertRaisesRegex(
            cellml.CellMLError, 'too large',
            cellml.Units.parse_unit_row, 'metre', 999)

        # Test exponent
        u = cellml.Units.parse_unit_row('metre', exponent=2)
        self.assertEqual(u, myokit.parse_unit('m^2'))
        u = cellml.Units.parse_unit_row('metre', exponent=-1.0)
        self.assertEqual(u, myokit.parse_unit('m^-1'))

        # Test bad exponent
        self.assertRaisesRegex(
            cellml.CellMLError, 'must be a real number',
            cellml.Units.parse_unit_row, 'metre', exponent='bert')

        # Test multiplier
        u = cellml.Units.parse_unit_row('metre', multiplier=1.234)
        self.assertEqual(u, myokit.parse_unit('m (1.234)'))

        # Bad multiplier
        self.assertRaisesRegex(
            cellml.CellMLError, 'must be a real number',
            cellml.Units.parse_unit_row, 'metre', multiplier='hiya')

        # All combined
        u = cellml.Units.parse_unit_row(
            'metre', prefix='milli', exponent=2, multiplier=1.234)
        self.assertEqual(u, myokit.parse_unit('mm^2 (1.234)'))

    def test_predefined(self):
        # Tests the predefined units exist and map to the correct myokit units

        self.assertEqual(cellml.Units.find_units(
            'ampere').myokit_unit(), myokit.units.A)
        self.assertEqual(cellml.Units.find_units(
            'becquerel').myokit_unit(), myokit.units.Bq)
        self.assertEqual(cellml.Units.find_units(
            'candela').myokit_unit(), myokit.units.cd)
        self.assertEqual(cellml.Units.find_units(
            'coulomb').myokit_unit(), myokit.units.C)
        self.assertEqual(cellml.Units.find_units(
            'dimensionless').myokit_unit(), myokit.units.dimensionless)
        self.assertEqual(cellml.Units.find_units(
            'farad').myokit_unit(), myokit.units.F)
        self.assertEqual(cellml.Units.find_units(
            'gram').myokit_unit(), myokit.units.g)
        self.assertEqual(cellml.Units.find_units(
            'gray').myokit_unit(), myokit.units.Gy)
        self.assertEqual(cellml.Units.find_units(
            'henry').myokit_unit(), myokit.units.H)
        self.assertEqual(cellml.Units.find_units(
            'hertz').myokit_unit(), myokit.units.Hz)
        self.assertEqual(cellml.Units.find_units(
            'joule').myokit_unit(), myokit.units.J)
        self.assertEqual(cellml.Units.find_units(
            'katal').myokit_unit(), myokit.units.kat)
        self.assertEqual(cellml.Units.find_units(
            'kelvin').myokit_unit(), myokit.units.K)
        self.assertEqual(cellml.Units.find_units(
            'kilogram').myokit_unit(), myokit.units.kg)
        self.assertEqual(cellml.Units.find_units(
            'litre').myokit_unit(), myokit.units.L)
        self.assertEqual(cellml.Units.find_units(
            'lumen').myokit_unit(), myokit.units.lm)
        self.assertEqual(cellml.Units.find_units(
            'lux').myokit_unit(), myokit.units.lux)
        self.assertEqual(cellml.Units.find_units(
            'metre').myokit_unit(), myokit.units.m)
        self.assertEqual(cellml.Units.find_units(
            'mole').myokit_unit(), myokit.units.mol)
        self.assertEqual(cellml.Units.find_units(
            'newton').myokit_unit(), myokit.units.N)
        self.assertEqual(cellml.Units.find_units(
            'ohm').myokit_unit(), myokit.units.R)
        self.assertEqual(cellml.Units.find_units(
            'pascal').myokit_unit(), myokit.units.Pa)
        self.assertEqual(cellml.Units.find_units(
            'radian').myokit_unit(), myokit.units.rad)
        self.assertEqual(cellml.Units.find_units(
            'second').myokit_unit(), myokit.units.s)
        self.assertEqual(cellml.Units.find_units(
            'siemens').myokit_unit(), myokit.units.S)
        self.assertEqual(cellml.Units.find_units(
            'sievert').myokit_unit(), myokit.units.Sv)
        self.assertEqual(cellml.Units.find_units(
            'steradian').myokit_unit(), myokit.units.sr)
        self.assertEqual(cellml.Units.find_units(
            'tesla').myokit_unit(), myokit.units.T)
        self.assertEqual(cellml.Units.find_units(
            'volt').myokit_unit(), myokit.units.V)
        self.assertEqual(cellml.Units.find_units(
            'watt').myokit_unit(), myokit.units.W)
        self.assertEqual(cellml.Units.find_units(
            'weber').myokit_unit(), myokit.units.Wb)

        # Some CellML 1.0 units have gone
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown units',
            cellml.Units.find_units, 'celsius')
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown units',
            cellml.Units.find_units, 'liter')
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown units',
            cellml.Units.find_units, 'meter')

    def test_prefixes(self):
        # Tests if all units prefixes are parsed correctly.

        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'yotta'),
            myokit.parse_unit('m (1e24)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'zetta'),
            myokit.parse_unit('m (1e21)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'exa'),
            myokit.parse_unit('m (1e18)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'peta'),
            myokit.parse_unit('m (1e15)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'tera'),
            myokit.parse_unit('m (1e12)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'giga'),
            myokit.parse_unit('m (1e9)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'mega'),
            myokit.parse_unit('m (1e6)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'kilo'),
            myokit.parse_unit('m (1e3)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'hecto'),
            myokit.parse_unit('m (1e2)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'deca'),
            myokit.parse_unit('m (1e1)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'deci'),
            myokit.parse_unit('m (1e-1)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'centi'),
            myokit.parse_unit('m (1e-2)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'milli'),
            myokit.parse_unit('m (1e-3)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'micro'),
            myokit.parse_unit('m (1e-6)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'nano'),
            myokit.parse_unit('m (1e-9)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'pico'),
            myokit.parse_unit('m (1e-12)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'femto'),
            myokit.parse_unit('m (1e-15)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'atto'),
            myokit.parse_unit('m (1e-18)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'zepto'),
            myokit.parse_unit('m (1e-21)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('metre', 'yocto'),
            myokit.parse_unit('m (1e-24)'))

        # Deka isn't allowed in CellML 2.0
        self.assertRaisesRegex(
            cellml.CellMLError, 'must be a string from the list of known',
            cellml.Units.parse_unit_row, 'metre', 'deka')

    def test_si_unit_names(self):
        # Tests Units.si_unit_names()

        names = [x for x in cellml.Units.si_unit_names()]
        self.assertTrue(len(names) > 10)
        for name in names:
            self.assertTrue(isinstance(name, basestring))
            self.assertTrue(
                isinstance(cellml.Units.find_units(name), cellml.Units))

    def test_string_conversion(self):
        # Test __str__

        u = cellml.Units('Numpty', myokit.units.ampere)
        self.assertEqual(str(u), 'Units[@name="Numpty"]')


class TestCellML2Methods(unittest.TestCase):
    """ Tests for public CellML API methods. """

    def test_clean_identifier(self):
        # Tests clean_identifier().

        # Valid identifiers get passed through
        name = 'hello'
        self.assertEqual(cellml.clean_identifier(name), name)
        name = 'h_ello'
        self.assertEqual(cellml.clean_identifier(name), name)
        name = 'x123'
        self.assertEqual(cellml.clean_identifier(name), name)
        name = 'x_123'
        self.assertEqual(cellml.clean_identifier(name), name)

        # Some identifiers can be fixed
        self.assertEqual(
            cellml.clean_identifier('this is a model'),
            'this_is_a_model')
        self.assertEqual(
            cellml.clean_identifier('This-is-a-model'),
            'This_is_a_model')

        # Some identifiers can't be fixed
        self.assertRaises(ValueError, cellml.clean_identifier, '18 + 25')

    def test_create_unit_name(self):
        # Tests create_unit_name().

        # Easy ones
        u = myokit.units.kg
        self.assertEqual(cellml.create_unit_name(u), 'kg')
        u = myokit.units.mV
        self.assertEqual(cellml.create_unit_name(u), 'mV')

        # Easy unit with funny multiplier
        u = myokit.units.m * 1.234
        self.assertEqual(cellml.create_unit_name(u), 'm_times_1_dot_234')

        # Dimensionless unit with multiplier
        u = myokit.units.dimensionless * 2
        self.assertEqual(cellml.create_unit_name(u), 'dimensionless_times_2')

        # Dimensionless unit with multiplier in e-notation
        u = myokit.units.dimensionless * 1000
        self.assertEqual(cellml.create_unit_name(u), 'dimensionless_times_1e3')
        u = myokit.units.dimensionless / 1000
        self.assertEqual(
            cellml.create_unit_name(u), 'dimensionless_times_1e_minus_3')

        # Per meter
        u = 1 / myokit.units.meter
        self.assertEqual(cellml.create_unit_name(u), 'per_m')

        # Unit known to myokit (per second
        u = 1 / myokit.units.second
        self.assertEqual(cellml.create_unit_name(u), 'S_per_F')

        # Square meters
        u = myokit.units.meter ** 2
        self.assertEqual(cellml.create_unit_name(u), 'm2')

    def test_is_identifier(self):
        # Tests is_identifier().

        self.assertTrue(cellml.is_identifier('hello'))
        self.assertTrue(cellml.is_identifier('h_e_l_l_o'))
        self.assertTrue(cellml.is_identifier('X123'))
        self.assertTrue(cellml.is_identifier('ZAa123_lo_2'))
        self.assertTrue(cellml.is_identifier('a'))

        self.assertFalse(cellml.is_identifier(''))
        self.assertFalse(cellml.is_identifier('_'))
        self.assertFalse(cellml.is_identifier('_a'))
        self.assertFalse(cellml.is_identifier('_1'))
        self.assertFalse(cellml.is_identifier('123'))
        self.assertFalse(cellml.is_identifier('1e3'))

    def test_is_integer_string(self):
        # Tests is_integer_string().

        self.assertTrue(cellml.is_integer_string('0'))
        self.assertTrue(cellml.is_integer_string('+0'))
        self.assertTrue(cellml.is_integer_string('-0'))
        self.assertTrue(cellml.is_integer_string('3'))
        self.assertTrue(cellml.is_integer_string('+3'))
        self.assertTrue(cellml.is_integer_string('-3'))
        self.assertTrue(cellml.is_integer_string('34269386698604537836794387'))

        self.assertFalse(cellml.is_integer_string(''))
        self.assertFalse(cellml.is_integer_string('.'))
        self.assertFalse(cellml.is_integer_string('1.2'))
        self.assertFalse(cellml.is_integer_string('-1.2'))
        self.assertFalse(cellml.is_integer_string('1.0'))
        self.assertFalse(cellml.is_integer_string('1.'))
        self.assertFalse(cellml.is_integer_string('.0'))
        self.assertFalse(cellml.is_integer_string('1e3'))
        self.assertFalse(cellml.is_integer_string('++1'))
        self.assertFalse(cellml.is_integer_string('+-3'))
        self.assertFalse(cellml.is_integer_string('--1'))
        self.assertFalse(cellml.is_integer_string('+'))
        self.assertFalse(cellml.is_integer_string('-'))
        self.assertFalse(cellml.is_integer_string('a'))
        self.assertFalse(cellml.is_integer_string('12C'))

    def test_is_basic_real_number_string(self):
        # Tests is_basic_real_number_string().

        self.assertTrue(cellml.is_basic_real_number_string('0'))
        self.assertTrue(cellml.is_basic_real_number_string('+0'))
        self.assertTrue(cellml.is_basic_real_number_string('-0'))
        self.assertTrue(cellml.is_basic_real_number_string('3'))
        self.assertTrue(cellml.is_basic_real_number_string('+3'))
        self.assertTrue(cellml.is_basic_real_number_string('-3'))
        self.assertTrue(cellml.is_basic_real_number_string(
            '3426938669860453783679436474536745674567887'))
        self.assertTrue(cellml.is_basic_real_number_string(
            '-.342693866982438645847568457875604537836794387'))
        self.assertTrue(cellml.is_basic_real_number_string('1.2'))
        self.assertTrue(cellml.is_basic_real_number_string('-1.2'))
        self.assertTrue(cellml.is_basic_real_number_string('1.0'))
        self.assertTrue(cellml.is_basic_real_number_string('1.'))
        self.assertTrue(cellml.is_basic_real_number_string('.1'))

        self.assertFalse(cellml.is_basic_real_number_string(''))
        self.assertFalse(cellml.is_basic_real_number_string('.'))
        self.assertFalse(cellml.is_basic_real_number_string('1e3'))
        self.assertFalse(cellml.is_basic_real_number_string('++1'))
        self.assertFalse(cellml.is_basic_real_number_string('+-3'))
        self.assertFalse(cellml.is_basic_real_number_string('--1'))
        self.assertFalse(cellml.is_basic_real_number_string('+'))
        self.assertFalse(cellml.is_basic_real_number_string('-'))
        self.assertFalse(cellml.is_basic_real_number_string('a'))
        self.assertFalse(cellml.is_basic_real_number_string('12C'))

    def test_is_real_number_string(self):
        # Tests is_real_number_string().

        self.assertTrue(cellml.is_real_number_string('0'))
        self.assertTrue(cellml.is_real_number_string('+0'))
        self.assertTrue(cellml.is_real_number_string('-0'))
        self.assertTrue(cellml.is_real_number_string('3'))
        self.assertTrue(cellml.is_real_number_string('+3'))
        self.assertTrue(cellml.is_real_number_string('-3'))
        self.assertTrue(cellml.is_real_number_string(
            '3426938669860453783679436474536745674567887'))
        self.assertTrue(cellml.is_real_number_string(
            '-.342693866982438645847568457875604537836794387'))
        self.assertTrue(cellml.is_real_number_string('1.2'))
        self.assertTrue(cellml.is_real_number_string('-1.2'))
        self.assertTrue(cellml.is_real_number_string('+1.0'))
        self.assertTrue(cellml.is_real_number_string('+1.'))
        self.assertTrue(cellml.is_real_number_string('.1'))
        self.assertTrue(cellml.is_real_number_string('1e3'))
        self.assertTrue(cellml.is_real_number_string('.1e-3'))
        self.assertTrue(cellml.is_real_number_string('-1.E0'))
        self.assertTrue(cellml.is_real_number_string('1E33464636'))
        self.assertTrue(cellml.is_real_number_string(
            '1.23000000000000028e+02'))

        self.assertFalse(cellml.is_real_number_string(''))
        self.assertFalse(cellml.is_real_number_string('.'))
        self.assertFalse(cellml.is_real_number_string('++1'))
        self.assertFalse(cellml.is_real_number_string('+-3'))
        self.assertFalse(cellml.is_real_number_string('--1'))
        self.assertFalse(cellml.is_real_number_string('+'))
        self.assertFalse(cellml.is_real_number_string('-'))
        self.assertFalse(cellml.is_real_number_string('a'))
        self.assertFalse(cellml.is_real_number_string('12C'))


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
