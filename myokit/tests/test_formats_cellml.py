#!/usr/bin/env python3
#
# Tests the CellML importer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.formats as formats
import myokit.formats.cellml
from myokit.formats.cellml import CellMLImporterError

from shared import TemporaryDirectory, DIR_FORMATS

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


class CellMLImporterTest(unittest.TestCase):
    """
    Tests the CellML importer.
    """

    def test_capability_reporting(self):
        # Test if the right capabilities are reported.
        i = formats.importer('cellml')
        self.assertFalse(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model_simple(self):
        # Beeler-Reuter is a simple model
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR_FORMATS, 'br-1977.cellml'))
        m.validate()

    def test_model_dot(self):
        # This is beeler-reuter but with a dot() in an expression
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR_FORMATS, 'br-1977-dot.cellml'))
        m.validate()

    def test_model_nesting(self):
        # The corrias model has multiple levels of nesting (encapsulation)
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR_FORMATS, 'corrias.cellml'))
        m.validate()

    def test_info(self):
        i = formats.importer('cellml')
        self.assertIsInstance(i.info(), basestring)

    def test_import(self):
        # Imports should raise an error
        i = formats.importer('cellml')
        self.assertRaisesRegex(
            CellMLImporterError, 'Imports are not supported',
            i.model, os.path.join(DIR_FORMATS, 'cellml-1-import.cellml'))

    def test_reaction(self):
        # Reaction elements should raise an error
        i = formats.importer('cellml')
        self.assertRaisesRegex(
            CellMLImporterError, 'Reactions are not supported',
            i.model, os.path.join(DIR_FORMATS, 'cellml-2-reaction.cellml'))


    def test_factorial(self):
        # Test if factorial, partialdiff, and sum elements trigger a warning.

        i = formats.importer('cellml')
        self.assertRaisesRegex(
            CellMLImporterError,
            'Unsupported element in apply',
            i.model,
            os.path.join(
                DIR_FORMATS, 'cellml-3-factorial-partialdiff-sum.cellml'),
        )

    def test_unit_errors(self):
        # Test if warnings to do with units are raised.

        i = formats.importer('cellml')
        self.assertRaisesRegex(
            CellMLImporterError,
            'Unable to resolve network of units in cellml:component',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-4-unit-errors-1.cellml')
        )

        # Offset attribute is not supported
        self.assertRaisesRegex(
            CellMLImporterError,
            'non-zero offsets',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-4-unit-errors-2.cellml')
        )

        # Unknown prefix
        self.assertRaisesRegex(
            CellMLImporterError,
            'must be a string from the list of known prefixes',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-4-unit-errors-3.cellml')
        )

        # Non-integer prefix
        self.assertRaisesRegex(
            CellMLImporterError,
            'or an integer',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-4-unit-errors-4.cellml')
        )

        # Non-integer exponent
        self.assertRaisesRegex(
            CellMLImporterError,
            'Non-integer unit exponents',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-4-unit-errors-5.cellml')
        )

        # Non-number exponent
        self.assertRaisesRegex(
            CellMLImporterError,
            'Unit exponent must be a real number',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-4-unit-errors-6.cellml')
        )


    def test_group_errors(self):
        # Test if warnings related to groups are raised.

        i = formats.importer('cellml')
        self.assertRaisesRegex(
            CellMLImporterError,
            'component attribute must reference a component',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-5-group-errors-1.cellml'))

        self.assertRaisesRegex(
            CellMLImporterError,
            'component attribute must reference a component',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-5-group-errors-2.cellml'))

    def test_connection_errors(self):
        # Test if warnings related to connections are raised.

        # Connection fo component that doesn't exist
        i = formats.importer('cellml')
        self.assertRaisesRegex(
            CellMLImporterError,
            'component_1 attribute must refer to a component',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-6-connection-errors-1.cellml'))

        # Map variables for bad variable_1, bad variable_2, and resulting
        # unresolved references
        self.assertRaisesRegex(
            CellMLImporterError,
            'Variable units attribute must reference a units element',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-6-connection-errors-2.cellml')
        )

    def test_equation_errors(self):
        # Test warnings raised in equation handling.

        i = formats.importer('cellml')

        # Two variables of integration
        self.assertRaisesRegex(
            CellMLImporterError,
            'Found derivatives to two different variables',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-1.cellml'))

        # Only <apply> is allowed in <maths>
        self.assertRaisesRegex(
            CellMLImporterError,
            'expecting <apply>',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-2.cellml'))

        # Only <apply> is allowed in <maths>
        self.assertRaisesRegex(
            CellMLImporterError,
            'expecting <eq>',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-3.cellml'))

        # No DAEs
        self.assertRaisesRegex(
            CellMLImporterError,
            'Differential algebraic',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-4.cellml'))

        # Equation for non-existent variable
        self.assertRaisesRegex(
            CellMLImporterError,
            'Equation found for unknown variable',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-5.cellml'))

        i.model(
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-6.cellml'))
        w = '\n'.join(i.logger().warnings())
        self.assertIn('No initial value', w)

    def test_name_errors(self):
        # Test name handling raises exceptions

        # Not a valid CellML identifier
        i = formats.importer('cellml')
        self.assertRaisesRegex(
            CellMLImporterError,
            'identifier',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-8-invalid-names-1.cellml')
        )

        # Valid CellML identifier, but not valid in Myokit
        i = formats.importer('cellml')
        i.model(os.path.join(
            DIR_FORMATS, 'cellml-8-invalid-names-2-fixable.cellml'))
        w = '\n'.join(i.logger().warnings())
        self.assertIn('Invalid name', w)

        # Not a valid CellML identifier: unit name
        i = formats.importer('cellml')
        self.assertRaisesRegex(
            CellMLImporterError,
            'identifier',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-8-invalid-names-3-unit.cellml')
        )


class CellMLExpressionWriterTest(unittest.TestCase):
    """
    Tests :class:`myokit.formats.cellml.CellMLExpressionWriter`.
    """

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

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '<apply><plus />' + cb + '</apply>')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '<apply><minus />' + cb + '</apply>')

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

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('cellml')
        self.assertIsInstance(w, myokit.formats.cellml.CellMLExpressionWriter)

        # Content mode not allowed
        self.assertRaises(RuntimeError, w.set_mode, True)

        # Lhs function setting not allowed
        self.assertRaises(NotImplementedError, w.set_lhs_function, None)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


class CellMLExporterTest(unittest.TestCase):
    """
    Provides further tests of :class:`myokit.formats.cellml.CellMLExporter`.
    """

    def test_stimulus_generation(self):
        # Test generation of a default stimulus current.

        # Start creating model
        model = myokit.Model()
        engine = model.add_component('engine')
        time = engine.add_variable('time')
        time.set_rhs(0)
        time.set_binding('time')

        # Create exporter and importer
        e = myokit.formats.cellml.CellMLExporter()
        i = myokit.formats.cellml.CellMLImporter()

        # Export --> Should generate warning, missing pace variable
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)
        self.assertIn('No variable bound to "pace"', e.logger().text())

        # Add pace variable, start testing generation
        pace = engine.add_variable('pace')
        pace.set_rhs(0)
        pace.set_binding('pace')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)
            self.assertNotIn('No variable bound to "pace"', e.logger().text())

            # Import model and check added stimulus works
            m2 = i.model(path)
            m2.get('engine.time').set_binding('time')
            self.assertIn('stimulus', m2)
            self.assertEqual(m2.get('stimulus.ctime').eval(), 0)
            self.assertEqual(m2.get('stimulus.duration').eval(), 2)
            self.assertEqual(m2.get('stimulus.offset').eval(), 100)
            self.assertEqual(m2.get('stimulus.period').eval(), 1000)
            self.assertEqual(m2.get('stimulus.pace').eval(), 0)
            m2.get('engine.time').set_rhs(101)
            self.assertEqual(m2.get('stimulus.pace').eval(), 1)
            m2.validate()

        # Test with pace variable in seconds
        time.set_unit('s')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)
            self.assertNotIn('No variable bound to "pace"', e.logger().text())

            # Import model and check added stimulus works
            m2 = i.model(path)
            m2.get('engine.time').set_binding('time')
            self.assertIn('stimulus', m2)
            self.assertEqual(m2.get('stimulus.ctime').eval(), 0)
            self.assertEqual(m2.get('stimulus.duration').eval(), 0.002)
            self.assertEqual(m2.get('stimulus.offset').eval(), 0.1)
            self.assertEqual(m2.get('stimulus.period').eval(), 1)
            self.assertEqual(m2.get('stimulus.pace').eval(), 0)
            m2.get('engine.time').set_rhs(0.101)
            self.assertEqual(m2.get('stimulus.pace').eval(), 1)
            m2.validate()

        # Test pace variable's children are removed
        pace.add_variable('hello')
        self.assertEqual(len(pace), 1)
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)
            self.assertNotIn('No variable bound to "pace"', e.logger().text())

            # Import model and check added stimulus works
            m2 = i.model(path)
            m2.get('engine.time').set_binding('time')
            self.assertIn('stimulus', m2)
            self.assertEqual(m2.get('stimulus.ctime').eval(), 0)
            self.assertEqual(m2.get('stimulus.duration').eval(), 0.002)
            self.assertEqual(m2.get('stimulus.offset').eval(), 0.1)
            self.assertEqual(m2.get('stimulus.period').eval(), 1)
            self.assertEqual(m2.get('stimulus.pace').eval(), 0)
            m2.get('engine.time').set_rhs(0.101)
            self.assertEqual(m2.get('stimulus.pace').eval(), 1)
            m2.validate()

            # Check child variables are gone (and pace lives in stimulus now)
            self.assertEqual(len(m2.get('stimulus.pace')), 0)

        # Test name is adapted if stimulus is already a component
        model.add_component('stimulus')
        model.add_component('stimulus_2')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)

            # Import model and check added stimulus works
            m2 = i.model(path)
            m2.get('engine.time').set_binding('time')
            self.assertIn('stimulus_3', m2)
            self.assertEqual(m2.get('stimulus_3.ctime').eval(), 0)

    def test_unit_export(self):
        # Test exporting units.

        # Start creating model
        model = myokit.Model()
        engine = model.add_component('engine')
        time = engine.add_variable('time')
        time.set_rhs(0)
        time.set_binding('time')
        three = engine.add_variable('three')
        three.set_rhs(3)

        mad_unit = myokit.Unit()
        mad_unit *= 1.234
        mad_unit *= myokit.units.m
        mad_unit /= myokit.units.s
        mad_unit *= myokit.units.A
        time.set_unit(mad_unit)

        pure_multiplier = myokit.Unit()
        pure_multiplier *= 1000
        three.set_unit(pure_multiplier)

        # Create exporter and importer
        e = myokit.formats.cellml.CellMLExporter()
        i = myokit.formats.cellml.CellMLImporter()

        # Export
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)

            # Import model and check units
            m2 = i.model(path)
            self.assertEqual(m2.get('engine.three').eval(), 3)
            self.assertEqual(m2.get('engine.three').unit(), pure_multiplier)
            self.assertEqual(m2.get('engine.time').unit(), mad_unit)

    def test_component_name_clashes(self):
        # Test if name clashes in components (due to nested variables parents
        # becoming components) are resolved.

        # Start creating model
        model = myokit.Model()
        engine = model.add_component('x')
        time = engine.add_variable('time')
        time.set_rhs(0)
        time.set_binding('time')
        y = engine.add_variable('y')
        y.set_rhs(1)
        yc = y.add_variable('yc')
        yc.set_rhs(2)

        comp = model.add_component('x_y')
        z = comp.add_variable('z')
        z.set_rhs(2)

        # The model now has a component `x_y` and a variable `x.y` that will be
        # converted to a component `x_y`

        # Create exporter and importer
        e = myokit.formats.cellml.CellMLExporter()
        i = myokit.formats.cellml.CellMLImporter()

        # Export
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)

            # Import model and check presence of renamed component
            m2 = i.model(path)
            self.assertIn('x_y', m2)
            self.assertIn('x_y_2', m2)

    def test_nested_variables(self):
        # Test export of deep nesting structures.

        # Start creating model
        model = myokit.Model()
        engine = model.add_component('x')
        time = engine.add_variable('time')
        time.set_rhs(0)
        time.set_binding('time')

        def add(parent, name, rhs=0):
            var = parent.add_variable(name)
            var.set_rhs(rhs)
            return var

        p1 = add(engine, 'p1', 1)
        p2 = add(p1, 'p2', 2)
        p3 = add(p2, 'p3', 3)
        p4 = add(p3, 'p4', 4)
        p5 = add(p4, 'p5', 5)
        add(p5, 'p6', 6)

        # Create exporter and importer
        e = myokit.formats.cellml.CellMLExporter()
        i = myokit.formats.cellml.CellMLImporter()

        # Export
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)

            # Import model and check presence of renamed component
            m2 = i.model(path)
            self.assertIn('x', m2)
            self.assertIn('x_p1', m2)
            self.assertIn('x_p1_p2', m2)
            self.assertIn('x_p1_p2_p3', m2)
            self.assertIn('x_p1_p2_p3_p4', m2)
            self.assertIn('x_p1_p2_p3_p4_p5', m2)
            self.assertNotIn('x_p1_p2_p3_p4_p5_p6', m2)

    def test_component_ordering(self):

        # Create quick model without any nested variables
        m = myokit.Model()
        m.meta['name'] = 'Hello'

        c = m.add_component('C')
        x = c.add_variable('x')
        x.set_rhs('5 [ms]')
        x.set_unit('ms')
        x.set_binding('time')

        a = m.add_component('A')
        x = a.add_variable('x')
        x.set_rhs('2 [ms]')
        x.set_unit('ms')

        d = m.add_component('D')
        x = d.add_variable('x')
        x.set_rhs('1 [ms]')
        x.set_unit('ms')

        b = m.add_component('B')
        x = b.add_variable('x')
        x.set_rhs('3 [ms]')
        x.set_unit('ms')

        e = myokit.formats.cellml.CellMLExporter()
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, m)

            comps = []
            with open(path, 'r') as f:
                for line in f.readlines():
                    line = line.strip()
                    if line.startswith('<component name="'):
                        comps.append(line[17:-2])
            sorted_comps = list(comps)
            sorted_comps.sort()
            self.assertTrue(comps == sorted_comps)

    def test_oxmeta_annotation_export(self):
        # Text export of weblab oxmeta annotation

        # Create a test model
        m = myokit.Model()
        m.meta['name'] = 'Hello'

        cc = m.add_component('C')
        t = cc.add_variable('time')
        t.set_rhs('0 [ms]')
        t.set_unit('ms')
        t.set_binding('time')

        ca = m.add_component('A')
        x = ca.add_variable('INa')
        x.set_rhs('2 [ms]')
        x.set_unit('ms')

        cd = m.add_component('D')
        y = cd.add_variable('y')
        y.set_rhs('1 [ms]')
        y.set_unit('ms')

        cb = m.add_component('B')
        z = cb.add_variable('z')
        z.set_rhs('3 [ms]')
        z.set_unit('ms')

        # No oxmeta annotations: No cmeta namespace or RDF annotations
        exporter = myokit.formats.cellml.CellMLExporter()
        importer = myokit.formats.cellml.CellMLImporter()
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            exporter.model(path, m)
            with open(path, 'r') as f:
                xml = f.read()
            self.assertTrue('xmlns:cmeta' not in xml)
            self.assertTrue('cmeta:id' not in xml)
            self.assertTrue('<rdf' not in xml)

        # Add oxmeta annotations
        t.meta['oxmeta'] = 'time'
        x.meta['oxmeta'] = 'membrane_fast_sodium_current'
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            exporter.model(path, m)
            time_found = ina_found = False
            with open(path, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if 'rdf:about="#time"' in line:
                        time_found = True
                        self.assertIn('oxford-metadata#time', lines[i + 1])

                    if 'rdf:about="#INa"' in line:
                        ina_found = True
                        self.assertIn(
                            'oxford-metadata#membrane_fast_sodium_current',
                            lines[i + 1])

                self.assertTrue(time_found)
                self.assertTrue(ina_found)

            # Re-import, check if model can still be read
            m2 = importer.model(path)

    def test_weird_custom_units(self):
        # Test export of units with large/small multipliers

        # Create a test model
        m = myokit.Model()
        m.meta['name'] = 'Hello'

        cc = m.add_component('C')
        t = cc.add_variable('time')
        t.set_rhs('0 [ms]')
        t.set_unit('ms')
        t.set_binding('time')

        ca = m.add_component('A')
        x = ca.add_variable('INa')
        x.set_rhs('2 [N (1e+12)]')
        x.set_unit('N (1e+12)')

        cd = m.add_component('D')
        y = cd.add_variable('y')
        y.set_rhs('1 [s (1e-13)]')
        y.set_unit('s (1e-13)')

        cb = m.add_component('B')
        z = cb.add_variable('z')
        z.set_rhs('3 [1 (1e+06)]')
        z.set_unit('1 (1e+06)')

        # Export and read back in again
        exporter = myokit.formats.cellml.CellMLExporter()
        importer = myokit.formats.cellml.CellMLImporter()
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            exporter.model(path, m)
            with open(path, 'r') as f:
                xml = f.read()
            m2 = importer.model(path)


if __name__ == '__main__':
    unittest.main()
