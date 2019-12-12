#!/usr/bin/env python
#
# Tests the CellML 1.0 API.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.formats.cellml.cellml_1 as cellml

from shared import LogCapturer

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


class TestCellMLAnnotatedElement(unittest.TestCase):
    """ Tests for cellml.AnnotatableElement. """

    def test_cmeta_id(self):
        # Tests the cmeta_id methods.

        m = cellml.Model('m')
        c = m.add_component('c')

        # Test getting and setting
        self.assertIsNone(m.cmeta_id())
        self.assertIsNone(c.cmeta_id())
        m_id = 'this-is-m'
        c_id = 'this-is-c'
        m.set_cmeta_id(m_id)
        c.set_cmeta_id(c_id)
        self.assertEqual(m.cmeta_id(), m_id)
        self.assertEqual(c.cmeta_id(), c_id)

        # Test getting by cmeta id
        self.assertEqual(m.element_with_cmeta_id(m_id), m)
        self.assertEqual(m.element_with_cmeta_id(c_id), c)

        # Test unsetting
        m.set_cmeta_id(None)
        c.set_cmeta_id(None)
        self.assertIsNone(m.cmeta_id())
        self.assertIsNone(c.cmeta_id())
        self.assertRaises(KeyError, m.element_with_cmeta_id, m_id)
        self.assertRaises(KeyError, m.element_with_cmeta_id, c_id)

        # Test multiple setting
        c.set_cmeta_id(c_id)
        c.set_cmeta_id(c_id)
        c.set_cmeta_id(c_id)
        self.assertEqual(c.cmeta_id(), c_id)
        self.assertEqual(m.element_with_cmeta_id(c_id), c)
        c.set_cmeta_id(None)
        self.assertIsNone(c.cmeta_id())
        self.assertRaises(KeyError, m.element_with_cmeta_id, c_id)

        # Test id is checked for well-formedness
        c.set_cmeta_id('123')
        self.assertRaisesRegex(
            cellml.CellMLError, 'empty string', c.set_cmeta_id, '   ')

        # Test bad set call doesn't mess up state
        self.assertEqual(c.cmeta_id(), '123')
        self.assertEqual(m.element_with_cmeta_id('123'), c)
        c.set_cmeta_id(c_id)
        self.assertRaises(KeyError, m.element_with_cmeta_id, '123')

        # Test duplicates
        m.set_cmeta_id(m_id)
        self.assertRaisesRegex(
            cellml.CellMLError, 'unique', c.set_cmeta_id, m_id)


class TestCellMLComponent(unittest.TestCase):
    """ Tests for ``cellml.Component``. """

    def test_creation(self):
        # Test component creation

        m = cellml.Model('m')
        c = m.add_component('c')

        self.assertRaisesRegex(
            cellml.CellMLError, 'valid CellML identifier',
            m.add_component, '123')

    def test_add_find_units(self):
        # Tests adding and finding units

        m = cellml.Model('m')
        c = m.add_component('c')

        # Test getting non-existent
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown', c.find_units, 'wooster')

        # Test adding
        u = c.add_units('wooster', myokit.units.lumen)
        self.assertEqual(c.find_units('wooster'), u)

        # Test doubles are not allowed
        self.assertRaisesRegex(
            cellml.CellMLError, 'same name', c.add_units,
            'wooster', myokit.units.meter)

        # But shadowing is
        v = m.add_units('wooster', myokit.units.meter)
        self.assertEqual(c.find_units('wooster'), u)
        self.assertEqual(m.find_units('wooster'), v)

        # Test iteration
        w = c.add_units('jarvis', myokit.units.meter)
        us = [x for x in c.units()]
        self.assertEqual(len(us), 2)
        self.assertIn(u, us)
        self.assertIn(w, us)

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
            cellml.CellMLError, 'unique', c.add_variable, 'v', 'meter')

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
        c = m.add_component('Mary_jo_lisa')
        self.assertIsNone(a.parent())
        self.assertIsNone(b.parent())
        self.assertIsNone(c.parent())

        # Test setting
        a.set_parent(b)
        b.set_parent(c)
        c.set_parent(b)
        self.assertIs(a.parent(), b)
        self.assertIs(b.parent(), c)
        self.assertIs(c.parent(), b)

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


class TestCellMLModel(unittest.TestCase):
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
        us = [x for x in m.units()]
        self.assertEqual(len(us), 2)
        self.assertIn(u, us)
        self.assertIn(w, us)

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

        # Rest of creation is tested in component test

    def test_add_connection(self):
        # Tests adding connections

        # Test setting connections and using Variable.source()
        m = cellml.Model('m')
        a = m.add_component('a')
        b = m.add_component('b')
        c = m.add_component('c')
        c.set_parent(b)

        x = a.add_variable('x', 'volt', 'out', 'none')
        y = b.add_variable('y', 'volt', 'in', 'out')
        z = c.add_variable('z', 'volt', 'in', 'none')

        m.add_connection(x, y)
        m.add_connection(z, y)
        self.assertIs(x.source(), x)
        self.assertIs(y.source(), x)
        self.assertIs(z.source(), x)

        # Test bad connections
        x2 = x
        m = cellml.Model('m')
        a = m.add_component('a')
        b = m.add_component('b')
        c = m.add_component('c')
        c.set_parent(b)
        x = a.add_variable('x', 'volt', 'out', 'none')
        y = b.add_variable('y', 'volt', 'in', 'out')
        z = c.add_variable('z', 'volt', 'in', 'none')

        # Not a variable or wrong model
        self.assertRaisesRegex(
            ValueError, 'variable_1 must be a cellml.Variable.',
            m.add_connection, 'x', y)
        self.assertRaisesRegex(
            ValueError, 'variable_2 must be a cellml.Variable.',
            m.add_connection, y, 'x')
        self.assertRaisesRegex(
            ValueError, 'variable_1 must be a cellml.Variable from',
            m.add_connection, x2, y)
        self.assertRaisesRegex(
            ValueError, 'variable_2 must be a cellml.Variable from',
            m.add_connection, y, x2)

        # Connected to self
        self.assertRaisesRegex(
            cellml.CellMLError, 'cannot be connected to themselves',
            m.add_connection, x, x)
        xsib = a.add_variable('x_sibling', 'liter')
        self.assertRaisesRegex(
            cellml.CellMLError, 'in the same component',
            m.add_connection, x, xsib)

        # Must be sibling or parent/child
        self.assertRaisesRegex(
            cellml.CellMLError, 'siblings or have a parent-child',
            m.add_connection, x, z)

        # Invalid interface
        self.assertRaisesRegex(
            cellml.CellMLError, 'Invalid connection',
            m.add_connection, xsib, y)

    def test_creation(self):
        # Tests Model creation

        m = cellml.Model('hiya')

        # Test bad name
        self.assertRaisesRegex(
            cellml.CellMLError, 'valid CellML identifier', cellml.Model, '1e2')

        # Test bad version
        self.assertRaisesRegex(
            ValueError, 'supported', cellml.Model, 'm', '2.0')

    def test_myokit_model(self):
        # Tests conversion to a Myokit model

        # Create model
        m = cellml.Model('m')
        documentation = 'This is the documentation.'
        m.meta['documentation'] = documentation
        a = m.add_component('a')
        b = m.add_component('b')
        c = m.add_component('c')
        c.set_parent(b)
        x = a.add_variable('x', 'volt', 'out', 'none')
        xb = b.add_variable('x', 'volt', 'in', 'out')
        xc = c.add_variable('x', 'volt', 'in', 'none')
        y = b.add_variable('y', 'volt')
        z = c.add_variable('z', 'volt')
        m.add_connection(x, xb)
        m.add_connection(xc, xb)
        z2 = c.add_variable('z2', 'meter')
        z2.set_initial_value(4)
        t = a.add_variable('t', 'second')
        m.set_free_variable(t)

        x.set_rhs(myokit.Number(1, myokit.units.V))
        x.set_is_state(True)
        x.set_initial_value(0.123)
        y.set_rhs(
            myokit.Plus(myokit.Number(2, myokit.units.V), myokit.Name(xb)))
        z.set_rhs(
            myokit.Plus(myokit.Number(3, myokit.units.V), myokit.Name(xc)))

        # Convert
        mm = m.myokit_model()
        self.assertIsInstance(mm, myokit.Model)
        self.assertEqual(mm.name(), 'm')
        self.assertIn('author', mm.meta)
        self.assertIn('desc', mm.meta)
        self.assertEqual(mm.meta['desc'], documentation)

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

        # Check RHS equations
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

        # Create model with variables used only to pass value through
        # components
        m = cellml.Model('m')
        a = m.add_component('a')
        b = m.add_component('b')
        c = m.add_component('c')
        d = m.add_component('d')
        c.set_parent(b)
        d.set_parent(c)
        ax = a.add_variable('x', 'volt', 'out', 'none')
        bx = b.add_variable('x', 'volt', 'in', 'out')
        cx = c.add_variable('x', 'volt', 'in', 'out')
        dx = d.add_variable('x', 'volt', 'in', 'none')
        dy = d.add_variable('y', 'volt')
        m.add_connection(ax, bx)
        m.add_connection(cx, bx)
        m.add_connection(dx, cx)
        ax.set_rhs(myokit.Number(1, myokit.units.V))
        dy.set_rhs(myokit.Name(dx))

        # Convert and check
        mm = m.myokit_model()
        self.assertEqual(len(mm), 4)
        self.assertEqual(len(mm['a']), 1)
        self.assertEqual(len(mm['b']), 0)
        self.assertEqual(len(mm['c']), 0)
        self.assertEqual(len(mm['d']), 1)
        self.assertIn('x', mm['a'])
        self.assertIn('y', mm['d'])

        # Create model with pass-through values that requires unit conversion
        m = cellml.Model('m')
        m.add_units('millivolt', myokit.units.volt * 1e-3)
        m.add_units('kilovolt', myokit.units.volt * 1e3)
        a = m.add_component('a')
        b = m.add_component('b')
        c = m.add_component('c')
        c.set_parent(b)
        ax = a.add_variable('x', 'volt', 'out', 'none')
        bx = b.add_variable('x', 'millivolt', 'in', 'out')
        cx = c.add_variable('x', 'kilovolt', 'in', 'none')
        m.add_connection(ax, bx)
        m.add_connection(bx, cx)
        ax.set_rhs(myokit.Number(1, myokit.units.V))

        # Convert and check
        with LogCapturer() as c:
            mm = m.myokit_model()
            self.assertIn('Unit conversion required', c.text())

    def test_name(self):
        # Tests Model.name().

        m = cellml.Model('Stacey')
        self.assertEqual(m.name(), 'Stacey')

    def test_free_variable(self):
        # Tests setting the free variable.

        m = cellml.Model('m')
        c = m.add_component('c')
        x = c.add_variable('x', 'meter')
        y = c.add_variable('y', 'second')
        self.assertFalse(x.is_free())
        self.assertFalse(y.is_free())

        # Test setting
        m.set_free_variable(x)
        self.assertTrue(x.is_free())
        self.assertFalse(y.is_free())

        # Test changing
        m.set_free_variable(y)
        self.assertFalse(x.is_free())
        self.assertTrue(y.is_free())

        # Test unsetting
        m.set_free_variable(None)
        self.assertFalse(x.is_free())
        self.assertFalse(y.is_free())

        # Test wrong model
        z = cellml.Model('mm').add_component('c').add_variable('z', 'liter')
        self.assertRaisesRegex(
            ValueError, 'from this model', m.set_free_variable, z)

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
        c = m.add_component('c')
        x = c.add_variable('x', 'mole')
        y = c.add_variable('y', 'liter')
        with LogCapturer() as c:
            m.validate()
            self.assertIn(
                'More than one variable does not have a value',
                c.text())

        # Free variable has a value, but other value does not
        x.set_initial_value(0.1)
        m.validate()
        m.set_free_variable(x)
        with LogCapturer() as c:
            m.validate()
            self.assertIn(
                'No value is defined for the variable "y"',
                c.text())

        # Free variable must be known if state is used
        y.set_rhs(myokit.Name(x))
        y.set_initial_value(0.1)
        y.set_is_state(True)
        m.set_free_variable(None)
        self.assertRaisesRegex(
            cellml.CellMLError, 'a free variable must be set', m.validate)

    def test_version(self):
        # TestsModel.version()

        m = cellml.Model('mm', '1.1')
        self.assertEqual(m.version(), '1.1')


class TestCellMLVariable(unittest.TestCase):
    """ Tests for ``cellml.Variable``. """

    def test_creation(self):
        # Tests variable creation

        m = cellml.Model('mmm')
        c = m.add_component('ccc')
        v = c.add_variable('vee', 'meter')

        # Test setting (and getting) interfaces
        self.assertEqual(v.public_interface(), 'none')
        self.assertEqual(v.private_interface(), 'none')
        w = c.add_variable('doubleyou', 'ampere', 'out', 'in')
        self.assertEqual(w.public_interface(), 'out')
        self.assertEqual(w.private_interface(), 'in')

        # Test bad name
        self.assertRaisesRegex(
            cellml.CellMLError, 'valid CellML identifier',
            c.add_variable, '', 'meter')

        # Test bad units
        self.assertRaisesRegex(
            cellml.CellMLError, 'units attribute',
            c.add_variable, 'soy_sauce', 'meters')

        # Test bad interfaces
        self.assertRaisesRegex(
            cellml.CellMLError, 'Public interface',
            c.add_variable, 'soy', 'meter', 'bin')
        self.assertRaisesRegex(
            cellml.CellMLError, 'Private interface',
            c.add_variable, 'soy', 'meter', 'in', 'bout')
        self.assertRaisesRegex(
            cellml.CellMLError, 'both',
            c.add_variable, 'soy', 'meter', 'in', 'in')

    def test_component_and_model(self):
        # Tests Variable.component() and Variable.model()

        m = cellml.Model('mm')
        c = m.add_component('comp')
        v = c.add_variable('bert', 'meter')
        self.assertIs(v.component(), c)
        self.assertIs(v.model(), m)

    def test_initial_value(self):
        # Tests getting and setting intial values

        v = cellml.Model('m').add_component('c').add_variable('v', 'volt')
        self.assertIsNone(v.initial_value())

        # Test setting and changing
        v.set_initial_value(4)
        self.assertEqual(v.initial_value(), 4)
        v.set_initial_value(-1.2e9)
        self.assertEqual(v.initial_value(), -1.2e9)

        # Test unsetting
        v.set_initial_value(None)
        self.assertIsNone(v.initial_value())

        # Bad value
        self.assertRaisesRegex(
            cellml.CellMLError, 'real number', v.set_initial_value, 'blue')

        # Bad interface
        w = v.component().add_variable('w', 'volt', private_interface='in')
        self.assertRaisesRegex(
            cellml.CellMLError, 'private_interface="in"',
            w.set_initial_value, 1)
        x = v.component().add_variable('x', 'volt', public_interface='in')
        self.assertRaisesRegex(
            cellml.CellMLError, 'public_interface="in"',
            x.set_initial_value, 1)

    def test_is_local_and_source(self):
        # Tests Variable.is_local() and Variable.source()

        m = cellml.Model('m')
        a = m.add_component('a')
        b = m.add_component('b')
        ax = a.add_variable('x', 'volt', 'out')
        bx = b.add_variable('x', 'volt', 'in')
        m.add_connection(ax, bx)

        self.assertTrue(ax.is_local())
        self.assertFalse(bx.is_local())
        self.assertIs(ax.source(), ax)
        self.assertIs(bx.source(), ax)

    def test_name(self):
        # Tests Variable.name()

        v = cellml.Model('m').add_component('a').add_variable('ernie', 'volt')
        self.assertEqual(v.name(), 'ernie')

    def test_rhs_or_initial_value(self):
        # Tests Variable.rhs_or_initial_value()

        v = cellml.Model('m').add_component('c').add_variable('bert', 'meter')
        self.assertIsNone(v.rhs_or_initial_value())

        # Test initial value is returned
        v.set_initial_value(3)
        i = myokit.Number(3, myokit.units.meter)
        self.assertEqual(v.rhs_or_initial_value(), i)

        # RHS takes precedence over initial value
        r = myokit.Number(18, myokit.units.meter)
        v.set_rhs(r)
        self.assertEqual(v.rhs_or_initial_value(), r)
        v.set_rhs(None)
        self.assertEqual(v.rhs_or_initial_value(), i)

        # State never returns initial value
        v.set_is_state(True)
        self.assertIsNone(v.rhs_or_initial_value())

    def test_set_and_get_rhs(self):
        # Tests Variable.set_rhs() and Variable.rhs()

        v = cellml.Model('m').add_component('c').add_variable('bert', 'meter')
        self.assertIsNone(v.rhs())
        r = myokit.Number(1, myokit.units.meter)
        v.set_rhs(r)
        self.assertEqual(v.rhs(), r)
        v.set_rhs(None)
        self.assertIsNone(v.rhs())

        # Bad interface
        w = v.component().add_variable('w', 'volt', 'in')
        self.assertRaisesRegex(
            cellml.CellMLError, 'public_interface="in"', w.set_rhs, r)
        x = v.component().add_variable('x', 'volt', 'out', 'in')
        self.assertRaisesRegex(
            cellml.CellMLError, 'private_interface="in"', x.set_rhs, r)

        # Invalid references
        z = v.model().add_component('d').add_variable('z', 'volt')
        self.assertRaisesRegex(
            cellml.CellMLError, 'can only reference variables from the same',
            v.set_rhs, myokit.Name(z))

    def test_set_and_is_state(self):
        # Tests Variable.set_is_state() and Variable.is_state()

        v = cellml.Model('m').add_component('a').add_variable('v', 'volt')
        self.assertFalse(v.is_state())
        v.set_initial_value(4)
        v.set_rhs(myokit.Number(3, myokit.units.volt / myokit.units.second))
        self.assertFalse(v.is_state())

        # Test setting and unsetting
        v.set_is_state(True)
        self.assertTrue(v.is_state())
        v.set_is_state(False)
        self.assertFalse(v.is_state())

        # Bad interface
        w = v.component().add_variable('w', 'volt', 'in')
        self.assertRaisesRegex(
            cellml.CellMLError, 'an "in" interface', w.set_is_state, True)
        x = v.component().add_variable('x', 'volt', 'out', 'in')
        self.assertRaisesRegex(
            cellml.CellMLError, 'an "in" interface', x.set_is_state, True)

    def test_string_conversion(self):
        # Tests Variable.__str__

        v = cellml.Model('m').add_component('c').add_variable('bert', 'meter')
        self.assertEqual(
            str(v), 'Variable[@name="bert"] in Component[@name="c"]')

    def test_validate(self):
        # Tests Variable validation

        # Unconnected variables
        m = cellml.Model('m')
        a = m.add_component('a')
        b = m.add_component('b')
        t = a.add_variable('t', 'dimensionless')
        m.set_free_variable(t)
        ax = a.add_variable('x', 'meter', 'in')
        bx = b.add_variable('x', 'meter', 'out')
        bx.set_initial_value(3)
        with LogCapturer() as c:
            m.validate()
            self.assertIn('not connected', c.text())

        # States must define two values
        m.add_connection(ax, bx)
        m.validate()
        bx.set_is_state(True)
        self.assertRaisesRegex(
            cellml.CellMLError, 'must have a defining equation', m.validate)
        bx.set_rhs(myokit.Number(1, 'meter'))
        m.validate()
        bx.set_initial_value(None)
        with LogCapturer() as c:
            m.validate()
            self.assertIn('has no initial value', c.text())


class TestCellMLUnits(unittest.TestCase):
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

        # Create model with model and component units
        m = cellml.Model('m')
        c = m.add_component('c')
        m.add_units('wooster', myokit.units.V)
        c.add_units('wooster', myokit.units.A)

        # Test lookup of predefined, model, and component units
        u = cellml.Units.parse_unit_row('meter')
        self.assertEqual(u, myokit.units.m)
        u = cellml.Units.parse_unit_row('wooster', context=m)
        self.assertEqual(u, myokit.units.V)
        u = cellml.Units.parse_unit_row('wooster', context=c)
        self.assertEqual(u, myokit.units.A)

        # Test bad lookup
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown units name',
            cellml.Units.parse_unit_row, 'wooster')
        self.assertRaisesRegex(
            cellml.CellMLError, 'Unknown units name',
            cellml.Units.parse_unit_row, 'muppet', context=m)

        # Test prefixes
        u = cellml.Units.parse_unit_row('meter', 'micro')
        self.assertEqual(u, myokit.parse_unit('um'))
        u = cellml.Units.parse_unit_row('meter', -4)
        self.assertEqual(u, myokit.parse_unit('m (1e-4)'))
        u = cellml.Units.parse_unit_row('meter', -4.0)
        self.assertEqual(u, myokit.parse_unit('m (1e-4)'))

        # Test bad prefixes
        self.assertRaisesRegex(
            cellml.CellMLError, 'known prefixes or an integer',
            cellml.Units.parse_unit_row, 'meter', 'forty')
        self.assertRaisesRegex(
            cellml.CellMLError, 'known prefixes or an integer',
            cellml.Units.parse_unit_row, 'meter', 14.8)
        self.assertRaisesRegex(
            cellml.CellMLError, 'too large',
            cellml.Units.parse_unit_row, 'meter', 999)

        # Test exponent
        u = cellml.Units.parse_unit_row('meter', exponent=2)
        self.assertEqual(u, myokit.parse_unit('m^2'))
        u = cellml.Units.parse_unit_row('meter', exponent=-1.0)
        self.assertEqual(u, myokit.parse_unit('m^-1'))

        # Test bad exponent
        self.assertRaisesRegex(
            cellml.CellMLError, 'must be a real number',
            cellml.Units.parse_unit_row, 'meter', exponent='bert')
        self.assertRaisesRegex(
            cellml.CellMLError, 'Non-integer unit exponents',
            cellml.Units.parse_unit_row, 'meter', exponent=1.23)

        # Test multiplier
        u = cellml.Units.parse_unit_row('meter', multiplier=1.234)
        self.assertEqual(u, myokit.parse_unit('m (1.234)'))

        # Bad multiplier
        self.assertRaisesRegex(
            cellml.CellMLError, 'must be a real number',
            cellml.Units.parse_unit_row, 'meter', multiplier='hiya')

        # All combined
        u = cellml.Units.parse_unit_row(
            'meter', prefix='milli', exponent=2, multiplier=1.234)
        self.assertEqual(u, myokit.parse_unit('mm^2 (1.234)'))

    def test_predefined(self):
        # Tests all predefined units exist

        self.assertEqual(cellml.Units.find_units(
            'dimensionless').myokit_unit(), myokit.units.dimensionless)
        self.assertEqual(cellml.Units.find_units(
            'ampere').myokit_unit(), myokit.units.A)
        self.assertEqual(cellml.Units.find_units(
            'farad').myokit_unit(), myokit.units.F)
        self.assertEqual(cellml.Units.find_units(
            'katal').myokit_unit(), myokit.units.kat)
        self.assertEqual(cellml.Units.find_units(
            'lux').myokit_unit(), myokit.units.lux)
        self.assertEqual(cellml.Units.find_units(
            'pascal').myokit_unit(), myokit.units.Pa)
        self.assertEqual(cellml.Units.find_units(
            'tesla').myokit_unit(), myokit.units.T)
        self.assertEqual(cellml.Units.find_units(
            'becquerel').myokit_unit(), myokit.units.Bq)
        self.assertEqual(cellml.Units.find_units(
            'gram').myokit_unit(), myokit.units.g)
        self.assertEqual(cellml.Units.find_units(
            'kelvin').myokit_unit(), myokit.units.K)
        self.assertEqual(cellml.Units.find_units(
            'meter').myokit_unit(), myokit.units.m)
        self.assertEqual(cellml.Units.find_units(
            'radian').myokit_unit(), myokit.units.rad)
        self.assertEqual(cellml.Units.find_units(
            'volt').myokit_unit(), myokit.units.V)
        self.assertEqual(cellml.Units.find_units(
            'candela').myokit_unit(), myokit.units.cd)
        self.assertEqual(cellml.Units.find_units(
            'gray').myokit_unit(), myokit.units.Gy)
        self.assertEqual(cellml.Units.find_units(
            'kilogram').myokit_unit(), myokit.units.kg)
        self.assertEqual(cellml.Units.find_units(
            'metre').myokit_unit(), myokit.units.m)
        self.assertEqual(cellml.Units.find_units(
            'second').myokit_unit(), myokit.units.s)
        self.assertEqual(cellml.Units.find_units(
            'watt').myokit_unit(), myokit.units.W)
        self.assertEqual(cellml.Units.find_units(
            'celsius').myokit_unit(), myokit.units.C)
        self.assertEqual(cellml.Units.find_units(
            'henry').myokit_unit(), myokit.units.H)
        self.assertEqual(cellml.Units.find_units(
            'liter').myokit_unit(), myokit.units.L)
        self.assertEqual(cellml.Units.find_units(
            'mole').myokit_unit(), myokit.units.mol)
        self.assertEqual(cellml.Units.find_units(
            'siemens').myokit_unit(), myokit.units.S)
        self.assertEqual(cellml.Units.find_units(
            'weber').myokit_unit(), myokit.units.Wb)
        self.assertEqual(cellml.Units.find_units(
            'coulomb').myokit_unit(), myokit.units.C)
        self.assertEqual(cellml.Units.find_units(
            'hertz').myokit_unit(), myokit.units.Hz)
        self.assertEqual(cellml.Units.find_units(
            'litre').myokit_unit(), myokit.units.L)
        self.assertEqual(cellml.Units.find_units(
            'newton').myokit_unit(), myokit.units.N)
        self.assertEqual(cellml.Units.find_units(
            'sievert').myokit_unit(), myokit.units.Sv)
        self.assertEqual(cellml.Units.find_units(
            'joule').myokit_unit(), myokit.units.J)
        self.assertEqual(cellml.Units.find_units(
            'lumen').myokit_unit(), myokit.units.lm)
        self.assertEqual(cellml.Units.find_units(
            'ohm').myokit_unit(), myokit.units.R)
        self.assertEqual(cellml.Units.find_units(
            'steradian').myokit_unit(), myokit.units.sr)

    def test_prefixes(self):
        # Tests if all units prefixes are parsed correctly.

        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'yotta'),
            myokit.parse_unit('m (1e24)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'zetta'),
            myokit.parse_unit('m (1e21)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'exa'),
            myokit.parse_unit('m (1e18)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'peta'),
            myokit.parse_unit('m (1e15)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'tera'),
            myokit.parse_unit('m (1e12)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'giga'),
            myokit.parse_unit('m (1e9)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'mega'),
            myokit.parse_unit('m (1e6)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'kilo'),
            myokit.parse_unit('m (1e3)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'hecto'),
            myokit.parse_unit('m (1e2)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'deka'),
            myokit.parse_unit('m (1e1)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'deca'),
            myokit.parse_unit('m (1e1)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'deci'),
            myokit.parse_unit('m (1e-1)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'centi'),
            myokit.parse_unit('m (1e-2)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'milli'),
            myokit.parse_unit('m (1e-3)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'micro'),
            myokit.parse_unit('m (1e-6)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'nano'),
            myokit.parse_unit('m (1e-9)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'pico'),
            myokit.parse_unit('m (1e-12)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'femto'),
            myokit.parse_unit('m (1e-15)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'atto'),
            myokit.parse_unit('m (1e-18)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'zepto'),
            myokit.parse_unit('m (1e-21)'))
        self.assertEqual(
            cellml.Units.parse_unit_row('meter', 'yocto'),
            myokit.parse_unit('m (1e-24)'))

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


class TestCellMLMethods(unittest.TestCase):
    """ Tests for public CellML API methods. """

    def test_valid_identifier(self):
        # Tests is_valid_identifier().

        self.assertTrue(cellml.is_valid_identifier('hello'))
        self.assertTrue(cellml.is_valid_identifier('h_e_l_l_o'))
        self.assertTrue(cellml.is_valid_identifier('X123'))
        self.assertTrue(cellml.is_valid_identifier('ZAa123_lo_2'))
        self.assertTrue(cellml.is_valid_identifier('a'))
        self.assertTrue(cellml.is_valid_identifier('_a'))

        self.assertFalse(cellml.is_valid_identifier('_'))
        self.assertFalse(cellml.is_valid_identifier('123'))
        self.assertFalse(cellml.is_valid_identifier('1e3'))


if __name__ == '__main__':
    unittest.main()
