#!/usr/bin/env python3
#
# Tests Myokit's SBML api.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.formats
import myokit.formats.sbml as sbml
from myokit.formats.sbml import SBMLParser

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:  # pragma: no python 3 cover
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str


class TestCompartment(unittest.TestCase):
    """
    Unit tests for :class:`Compartment`.
    """

    @classmethod
    def setUpClass(cls):
        cls.model = sbml.Model(name='model')
        cls.sid = 'compartment'
        cls.c = cls.model.add_compartment(sid=cls.sid)

    def test_bad_model(self):

        model = 'model'
        sid = 'compartment'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', sbml.Compartment, model, sid)

    def test_initial_value(self):

        # Check default initial value
        self.assertIsNone(self.c.initial_value())

        # Check bad value
        expr = 2
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.c.set_initial_value, expr)

        # Check good value
        expr = myokit.Number(2)
        self.c.set_initial_value(expr)

        self.assertEqual(self.c.initial_value(), expr)

    def test_is_rate(self):

        # Check default
        self.assertFalse(self.c.is_rate())

        # Check setting rate to true
        expr = myokit.Number(2)
        self.c.set_value(value=expr, is_rate=True)

        self.assertTrue(self.c.is_rate())

    def test_sid(self):
        self.assertEqual(self.c.sid(), self.sid)

    def test_size_units(self):

        # Check default units
        unit = myokit.units.dimensionless
        self.assertEqual(self.c.size_units(), unit)

        # Check spatial dimensions = 1
        self.c.set_spatial_dimensions(dimensions=1)
        unit = myokit.units.meter
        self.model.set_length_units(unit)

        self.assertEqual(self.c.size_units(), unit)

        # Check spatial dimensions = 2
        self.c.set_spatial_dimensions(dimensions=2)
        unit = myokit.units.meter**2
        self.model.set_area_units(unit)

        self.assertEqual(self.c.size_units(), unit)

        # Check spatial dimensions = 3
        self.c.set_spatial_dimensions(dimensions=3)
        unit = myokit.units.L
        self.model.set_volume_units(unit)

        self.assertEqual(self.c.size_units(), unit)

        # Check bad size units
        unit = 'mL'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.c.set_size_units, unit)

        # Check valid size units
        unit = myokit.units.L * 1E-3
        self.c.set_size_units(unit)

        self.assertEqual(self.c.size_units(), unit)

    def test_spatial_dimensions(self):

        # Test valid dimensions
        dim = 2.31
        self.c.set_spatial_dimensions(dim)

        self.assertEqual(self.c.spatial_dimensions(), dim)

    def test_string_representation(self):

        self.assertEqual(str(self.c), '<Compartment ' + self.sid + '>')

    def test_value(self):

        # Check bad value
        expr = 2
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.c.set_value, expr)

        # Check good value
        expr = myokit.Number(2)
        self.c.set_value(expr)

        self.assertEqual(self.c.value(), expr)


class TestModel(unittest.TestCase):
    """
    Unit tests for :class:`Model`.
    """

    def test_area_units(self):

        model = sbml.Model(name='model')

        area_units = myokit.units.meter ** 2
        model.set_area_units(area_units)

        self.assertEqual(model.area_units(), area_units)

    def test_assignable(self):

        model = sbml.Model(name='model')

        # Add assignables to model
        c_sid = 'compartment'
        model.add_compartment(c_sid)

        p_sid = 'parameters'
        model.add_parameter(p_sid)

        s_sid = 'species'
        comp = sbml.Compartment(model=model, sid=c_sid)
        model.add_species(compartment=comp, sid=s_sid)

        # Check that all assignables are accessible
        self.assertIsNotNone(model.assignable(c_sid))
        self.assertIsNotNone(model.assignable(p_sid))
        self.assertIsNotNone(model.assignable(s_sid))

    def test_base_unit(self):

        model = sbml.Model(name='model')

        # Check all base units
        self.assertEqual(
            model.base_unit('ampere'), myokit.units.A)
        self.assertEqual(
            model.base_unit('avogadro'),
            myokit.parse_unit('1 (6.02214179e23)'))
        self.assertEqual(model.base_unit('becquerel'), myokit.units.Bq)
        self.assertEqual(model.base_unit('candela'), myokit.units.cd)
        self.assertEqual(model.base_unit('coulomb'), myokit.units.C)
        self.assertEqual(
            model.base_unit('dimensionless'), myokit.units.dimensionless)
        self.assertEqual(model.base_unit('farad'), myokit.units.F)
        self.assertEqual(model.base_unit('gram'), myokit.units.g)
        self.assertEqual(model.base_unit('gray'), myokit.units.Gy)
        self.assertEqual(model.base_unit('henry'), myokit.units.H)
        self.assertEqual(model.base_unit('hertz'), myokit.units.Hz)
        self.assertEqual(model.base_unit('item'), myokit.units.dimensionless)
        self.assertEqual(model.base_unit('joule'), myokit.units.J)
        self.assertEqual(model.base_unit('katal'), myokit.units.kat)
        self.assertEqual(model.base_unit('kelvin'), myokit.units.K)
        self.assertEqual(model.base_unit('kilogram'), myokit.units.kg)
        self.assertEqual(model.base_unit('liter'), myokit.units.L)
        self.assertEqual(model.base_unit('litre'), myokit.units.L)
        self.assertEqual(model.base_unit('lumen'), myokit.units.lm)
        self.assertEqual(model.base_unit('lux'), myokit.units.lux)
        self.assertEqual(model.base_unit('meter'), myokit.units.m)
        self.assertEqual(model.base_unit('metre'), myokit.units.m)
        self.assertEqual(model.base_unit('mole'), myokit.units.mol)
        self.assertEqual(model.base_unit('newton'), myokit.units.N)
        self.assertEqual(model.base_unit('ohm'), myokit.units.ohm)
        self.assertEqual(model.base_unit('pascal'), myokit.units.Pa)
        self.assertEqual(model.base_unit('radian'), myokit.units.rad)
        self.assertEqual(model.base_unit('second'), myokit.units.s)
        self.assertEqual(model.base_unit('siemens'), myokit.units.S)
        self.assertEqual(model.base_unit('sievert'), myokit.units.Sv)
        self.assertEqual(model.base_unit('steradian'), myokit.units.sr)
        self.assertEqual(model.base_unit('tesla'), myokit.units.T)
        self.assertEqual(model.base_unit('volt'), myokit.units.V)
        self.assertEqual(model.base_unit('watt'), myokit.units.W)
        self.assertEqual(model.base_unit('weber'), myokit.units.Wb)

        # Check celsius (not supported)
        self.assertRaisesRegex(
            sbml.SBMLError,
            'The units "celsius" are not supported.',
            model.base_unit,
            'celsius')

        # Check bad base unit
        self.assertRaisesRegex(
            sbml.SBMLError, '<', model.base_unit, 'some unit')

    def test_compartment(self):

        model = sbml.Model(name='model')

        # Test bad sid
        sid = ';'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Invalid SId "', model.add_compartment, sid)

        # Test good sid
        sid = 'compartment'
        model.add_compartment(sid)

        self.assertIsInstance(model.compartment(sid), sbml.Compartment)

        # Test duplicate sid
        sid = 'compartment'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Duplicate SId "', model.add_compartment, sid)

    def test_conversion_factor(self):

        model = sbml.Model(name='model')

        # Test default value
        self.assertIsNone(model.conversion_factor())

        # Bad conversion factor
        self.assertRaisesRegex(
            sbml.SBMLError, '<', model.set_conversion_factor, 10)

        # Good conversion factor
        factor = sbml.Parameter(model, 'parameter')
        model.set_conversion_factor(factor)

        self.assertIsInstance(
            model.conversion_factor(), sbml.Parameter)

    def test_extent_units(self):

        model = sbml.Model(name='model')

        # Test default
        self.assertEqual(model.extent_units(), myokit.units.dimensionless)

        # Test bad extent units
        self.assertRaisesRegex(
            sbml.SBMLError, '<', model.set_extent_units, 'mg')

        # Test good extent units
        model.set_extent_units(myokit.units.g)

        self.assertEqual(model.extent_units(), myokit.units.g)

    def test_length_units(self):

        model = sbml.Model(name='model')

        # Test default
        self.assertEqual(model.length_units(), myokit.units.dimensionless)

        # Test bad length units
        self.assertRaisesRegex(
            sbml.SBMLError, '<', model.set_length_units, 'm')

        # Test good length units
        model.set_length_units(myokit.units.meter)

        self.assertEqual(model.length_units(), myokit.units.meter)

    def test_name(self):

        name = 'model'
        model = sbml.Model(name=name)

        self.assertEqual(model.name(), name)

    def test_notes(self):

        model = sbml.Model(name='model')

        notes = 'Here are some notes.'
        model.set_notes(notes)

        self.assertEqual(model.notes(), notes)

    def test_parameter(self):

        model = sbml.Model(name='model')

        # Test bad sid
        sid = ';'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Invalid SId "', model.add_parameter, sid)

        # Test good sid
        sid = 'parameter'
        model.add_parameter(sid)

        self.assertIsInstance(model.parameter(sid), sbml.Parameter)

        # Test duplicate sid
        sid = 'parameter'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Duplicate SId "', model.add_parameter, sid)

    def test_reaction(self):

        model = sbml.Model(name='model')

        # Test bad sid
        sid = ';'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Invalid SId "', model.add_reaction, sid)

        # Test good sid
        sid = 'reaction'
        model.add_reaction(sid)

        self.assertIsInstance(model.reaction(sid), sbml.Reaction)

        # Test duplicate sid
        sid = 'reaction'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Duplicate SId "', model.add_reaction, sid)

    def test_species(self):

        model = sbml.Model(name='model')

        # Test bad compartment
        comp = 'some compartment'
        sid = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', model.add_species, comp, sid)

        # Test bad sid
        c_sid = 'compartment'
        comp = sbml.Compartment(model=model, sid=c_sid)
        sid = ';'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Invalid SId "', model.add_species, comp, sid)

        # Test good sid
        c_sid = 'compartment'
        comp = sbml.Compartment(model=model, sid=c_sid)
        sid = 'species'

        model.add_species(compartment=comp, sid=sid)

        self.assertIsInstance(model.species(sid), sbml.Species)

        # Test duplicate sid
        sid = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Duplicate SId "', model.add_species, comp, sid)

    def test_string_representation(self):

        # Check no name provided
        model = sbml.Model(name=None)

        self.assertEqual(str(model), '<SBMLModel>')

        # Check name provided
        name = 'model'
        model = sbml.Model(name='model')

        self.assertEqual(str(model), '<SBMLModel ' + name + '>')

    def test_substance_units(self):

        model = sbml.Model(name='model')

        # Test default
        self.assertEqual(model.substance_units(), myokit.units.dimensionless)

        # Test bad substance units
        self.assertRaisesRegex(
            sbml.SBMLError, '<', model.set_substance_units, 'mg')

        # Test good substance units
        model.set_substance_units(myokit.units.g)

        self.assertEqual(model.substance_units(), myokit.units.g)

    def test_time_units(self):

        model = sbml.Model(name='model')

        # Test default
        self.assertEqual(model.time_units(), myokit.units.dimensionless)

        # Test bad time units
        self.assertRaisesRegex(
            sbml.SBMLError, '<', model.set_time_units, 's')

        # Test good time units
        model.set_time_units(myokit.units.s)

        self.assertEqual(model.time_units(), myokit.units.s)

    def test_unit(self):

        model = sbml.Model(name='model')

        # Check bad units
        unitsid = 'some_unit'
        self.assertRaisesRegex(
            sbml.SBMLError, 'The unit SID <', model.unit, unitsid)

        # Check base unit
        unitsid = 'ampere'
        self.assertEqual(model.unit(unitsid), myokit.units.A)

        # Check invalid unitsid for user-defined unit
        unitsid = ';'
        unit = myokit.units.dimensionless
        self.assertRaisesRegex(
            sbml.SBMLError, 'Invalid UnitSId "', model.add_unit, unitsid, unit)

        # Check unitsid for user-defined unit that coincides with base unit
        unitsid = 'ampere'
        unit = myokit.units.dimensionless
        self.assertRaisesRegex(
            sbml.SBMLError,
            'User unit overrides built-in unit: "',
            model.add_unit,
            unitsid,
            unit)

        # Check invalid user-defined unit
        unitsid = 'some_unit'
        unit = 'ampere'
        self.assertRaisesRegex(
            sbml.SBMLError,
            'Unit "',
            model.add_unit,
            unitsid,
            unit)

        # Check good user-defined unit
        unitsid = 'some_unit'
        unit = myokit.units.A
        model.add_unit(unitsid, unit)

        self.assertEqual(model.unit(unitsid), unit)

        # Check duplicate unitsid
        unitsid = 'some_unit'
        unit = myokit.units.A
        self.assertRaisesRegex(
            sbml.SBMLError, 'Duplicate UnitSId: "',
            model.add_unit, unitsid, unit)

    def test_volume_units(self):

        model = sbml.Model(name='model')

        # Test default
        self.assertEqual(model.volume_units(), myokit.units.dimensionless)

        # Test bad volume units
        self.assertRaisesRegex(
            sbml.SBMLError, '<', model.set_volume_units, 'L')

        # Test good volume units
        model.set_volume_units(myokit.units.L)

        self.assertEqual(model.volume_units(), myokit.units.L)


class SBMLTestMyokitModel(unittest.TestCase):
    """
    Unit tests for Model.myokit_model method.
    """

    @classmethod
    def setUpClass(cls):
        cls.p = SBMLParser()

        #

    def parse(self, xml, lvl=3, v=2):
        """
        Inserts the given ``xml`` into an <sbml> element, parses it, and
        returns the result.
        """
        return self.p.parse_string(self.wrap(xml, lvl, v))

    def wrap(self, xml_content, level=3, version=2):
        """
        Wraps ``xml_content`` into an SBML document of the specified ``level``
        and ``version``.
        """
        lv = 'level' + str(level) + '/version' + str(version)
        return (
            '<sbml xmlns="http://www.sbml.org/sbml/' + lv + '/core"'
            ' level="' + str(level) + '"'
            ' version="' + str(version) + '">'
            + xml_content +
            '</sbml>'
        )

    def test_add_compartments(self):
        # Tests whether compartments are added properly to the myokit model.

        # Create inputs
        myokit_model = myokit.Model()
        component_references = {}
        variable_references = {}
        expression_references = {}

        # Create sbml.Model with one compartment
        m = sbml.Model(name='model')
        sid = 'compartment'
        c = m.add_compartment(sid)
        unit = myokit.units.L
        c.set_size_units(unit)

        # Add compartment to myokit model
        m._add_compartments(
            myokit_model, component_references, variable_references,
            expression_references)

        # Check that compartment was added properly
        self.assertTrue(myokit_model.has_component(sid))
        self.assertIsInstance(component_references[sid], myokit.Component)

        # Check size variable is set properly
        self.assertIn(sid, variable_references.keys())
        var = variable_references[sid]
        self.assertIsInstance(var, myokit.Variable)
        self.assertEqual(var.unit(), unit)
        self.assertEqual(
            expression_references[myokit.Name(c)], myokit.Name(var))

    def test_add_myokit_component(self):
        # Tests whether myokit component is added properly to the myokit model.

        # Create inputs
        myokit_model = myokit.Model()
        component_references = {}

        # Create sbml.Model
        m = sbml.Model(name='model')

        # Add component to myokit model
        m._add_myokit_component(myokit_model, component_references)

        # Check that myokit component exists
        sid = 'myokit'
        self.assertTrue(myokit_model.has_component(sid))
        self.assertIsInstance(component_references[sid], myokit.Component)

    def test_add_parameters(self):
        # Tests whether parameters are added properly to myokit component.

        # Create myokit component
        myokit_model = myokit.Model()
        component_references = {}
        m = sbml.Model(name='model')
        m._add_myokit_component(myokit_model, component_references)
        c = component_references['myokit']

        # Create remaining inputs
        variable_references = {}
        expression_references = {}

        # Add parameter to sbml.Model
        sid = 'parameter'
        p = m.add_parameter(sid)
        unit = myokit.units.A
        p.set_units(unit)

        # Add parameter to myokit model
        m._add_parameters(c, variable_references, expression_references)

        # Check that parameter is added properly to myokit component
        self.assertTrue(c.has_variable(sid))
        self.assertIn(sid, variable_references.keys())
        var = variable_references[sid]
        self.assertIsInstance(var, myokit.Variable)
        self.assertEqual(var.unit(), unit)

    def test_add_species(self):
        # Tests whether species are added properly to the associated
        # components.

        # Add compartment to myokit model
        myokit_model = myokit.Model()
        component_references = {}
        variable_references = {}
        expression_references = {}

        m = sbml.Model(name='model')
        c_sid = 'compartment'
        c = m.add_compartment(c_sid)
        c_unit = myokit.units.L
        c.set_size_units(c_unit)

        m._add_compartments(
            myokit_model, component_references, variable_references,
            expression_references)

        # Create remaining inputs
        species_amount_references = {}

        # Case I: Species in concentration
        # Add species to sbml.Model
        sid = 'species'
        s = m.add_species(c, sid)
        s_unit = myokit.units.g
        s.set_substance_units(s_unit)

        # Add species to myokit model
        m._add_species(
            component_references, species_amount_references,
            variable_references, expression_references)

        # Check species has been added in amount and concentration
        comp = component_references[c_sid]
        self.assertTrue(comp.has_variable(sid + '_amount'))
        self.assertTrue(comp.has_variable(sid + '_concentration'))

        # Check that variable reference points to concentration and
        # units are set properly
        self.assertIn(sid, variable_references.keys())
        var = variable_references[sid]
        self.assertEqual(var.unit(), s_unit / c_unit)

        # Check that amount variable is referenced in species_amount_references
        # and that units are set properly
        self.assertIn(sid, species_amount_references.keys())
        var = species_amount_references[sid]
        self.assertEqual(var.unit(), s_unit)

        # Case II: Species in amount
        # Add species to sbml.Model
        sid = 'species_2'
        s = m.add_species(c, sid, is_amount=True)
        s_unit = myokit.units.g
        s.set_substance_units(s_unit)

        # Add species to myokit model
        m._add_species(
            component_references, species_amount_references,
            variable_references, expression_references)

        # Check species has been added in amount and concentration
        comp = component_references[c_sid]
        self.assertTrue(comp.has_variable(sid + '_amount'))
        self.assertFalse(comp.has_variable(sid + '_concentration'))

        # Check that variable reference points to amount and
        # units are set properly
        self.assertIn(sid, variable_references.keys())
        var = variable_references[sid]
        self.assertEqual(var.unit(), s_unit)

        # Check that amount variable is referenced in species_amount_references
        # and that units are set properly
        self.assertIn(sid, species_amount_references.keys())
        var = species_amount_references[sid]
        self.assertEqual(var.unit(), s_unit)

    def test_add_stoichiometries(self):
        # Tests whether stoichiometries are added properly to the associated
        # component.

        # Add compartment and species to myokit model
        myokit_model = myokit.Model()
        component_references = {}
        variable_references = {}
        expression_references = {}
        species_amount_references = {}

        m = sbml.Model(name='model')
        c_sid = 'compartment'
        c = m.add_compartment(c_sid)

        m._add_compartments(
            myokit_model, component_references, variable_references,
            expression_references)

        sid = 'species'
        s = m.add_species(c, sid)

        m._add_species(
            component_references, species_amount_references,
            variable_references, expression_references)

        # Case I: No stoichiometry reference
        # Add reaction to sbml.Model
        sid = 'reaction'
        r = m.add_reaction(sid)
        r_sid = None
        r.add_reactant(species=s, sid=r_sid)
        p_sid = None
        r.add_product(species=s, sid=p_sid)

        # Add stoichiometries to myokit model
        m._add_stoichiometries(
            component_references, variable_references, expression_references)

        # Check that stoichiometries do not exist in myokit model and are not
        # referenced in variable_references
        comp = component_references[c_sid]
        self.assertFalse(comp.has_variable(str(r_sid)))
        self.assertFalse(comp.has_variable(str(p_sid)))
        self.assertNotIn(r_sid, variable_references.keys())
        self.assertNotIn(p_sid, variable_references.keys())

        # Case II: Existing stoichiometry reference
        # Add reaction to sbml.Model
        sid = 'reaction_2'
        r = m.add_reaction(sid)
        r_sid = 'reactant'
        rs = r.add_reactant(species=s, sid=r_sid)
        p_sid = 'product'
        ps = r.add_product(species=s, sid=p_sid)

        # Add stoichiometries to myokit model
        m._add_stoichiometries(
            component_references, variable_references, expression_references)

        # Check that stoichiometries exist in myokit model and are
        # referenced in variable_references
        comp = component_references[c_sid]
        self.assertTrue(comp.has_variable(str(r_sid)))
        self.assertTrue(comp.has_variable(str(p_sid)))
        self.assertIn(r_sid, variable_references.keys())
        self.assertIn(p_sid, variable_references.keys())

        # Check that their units are set to dimensionless
        # and that their expressions are referenced
        unit = myokit.units.dimensionless
        var = variable_references[r_sid]
        self.assertEqual(var.unit(), unit)
        self.assertEqual(
            expression_references[myokit.Name(rs)], myokit.Name(var))
        var = variable_references[p_sid]
        self.assertEqual(var.unit(), unit)
        self.assertEqual(
            expression_references[myokit.Name(ps)], myokit.Name(var))

        # Check that stoichiometries are referenced in

    def test_add_time(self):
        # Tests whether time bound variable is added properly to myokit
        # component.

        # Create myokit component
        myokit_model = myokit.Model()
        component_references = {}
        m = sbml.Model(name='model')
        m._add_myokit_component(myokit_model, component_references)
        c = component_references['myokit']

        # Create remaining inputs
        variable_references = {}

        # Add time bound variable to myokit model
        unit = myokit.units.s
        m.set_time_units(unit)
        m._add_time(c, variable_references)

        # Check that time bound variable exists in myokit component
        self.assertTrue(c.has_variable('time'))

        # Check that variable is referenced under csymbol
        sid = 'http://www.sbml.org/sbml/symbols/time'
        self.assertIn(sid, variable_references.keys())

        # Check that variable has correct units and initial value
        var = variable_references[sid]
        self.assertEqual(var.rhs(), myokit.Number(0))
        self.assertEqual(var.unit(), unit)

    def test_name(self):

        # Test regular name
        name = 'model'
        m = sbml.Model(name=name)
        m = m.myokit_model()

        self.assertEqual(m.name(), name)

        # Test name with leading underscore
        name = '_model'
        m = sbml.Model(name=name)
        m = m.myokit_model()

        self.assertEqual(m.name(), 'underscore' + name)

    def test_notes(self):

        # Test that notes are set as meta data
        n = 'These are some notes'
        m = sbml.Model()
        m.set_notes(n)
        m = m.myokit_model()

        self.assertEqual(m.meta['desc'], n)

    def test_species_exist(self):
        # Tests whether species initialisation in amount and concentration
        # works.
        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>')
        b = (' </listOfSpecies>'
             '</model>')

        # Species in amount
        x = '<species compartment="c" id="spec" hasOnlySubstanceUnits="true"/>'
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check whether species exists in amount
        self.assertTrue(m.has_variable('c.spec_amount'))

        # Check that component has 2 variables
        # [size, spec_amount]
        component = m.get('c')
        self.assertEqual(component.count_variables(), 2)

        # Species in concentration
        x = '<species compartment="c" id="spec" />'
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check whether species exists in amount and concentration
        self.assertTrue(m.has_variable('c.spec_amount'))
        self.assertTrue(m.has_variable('c.spec_concentration'))

        # Check that component has 3 variables
        # [size, spec_amount, spec_concentration]
        component = m.get('c')
        self.assertEqual(component.count_variables(), 3)

    def test_species_units(self):
        # Tests whether species units are set properly.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>')
        b = (' </listOfSpecies>'
             '</model>')

        # Test I: No substance nor size units provided
        x = '<species compartment="c" id="spec" />'
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check that units are set properly
        amount = m.get('c.spec_amount')
        conc = m.get('c.spec_concentration')

        self.assertEqual(amount.unit(), myokit.units.dimensionless)
        self.assertEqual(conc.unit(), myokit.units.dimensionless)

        # Test II: Substance and size units provided
        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" units="meter"/>'
             ' </listOfCompartments>'
             ' <listOfSpecies>')
        b = (' </listOfSpecies>'
             '</model>')

        x = '<species compartment="c" id="spec" substanceUnits="kilogram"/>'
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check that units are set properly
        amount = m.get('c.spec_amount')
        conc = m.get('c.spec_concentration')

        self.assertEqual(amount.unit(), myokit.units.kg)
        self.assertEqual(conc.unit(), myokit.units.kg / myokit.units.meter)

    def test_species_initial_values(self):
        # Tests whether initial values of species is set properly.
        a = ('<model>'
             '  <listOfCompartments>'
             '    <compartment id="c" size="10"/>'
             '  </listOfCompartments>'
             '  <listOfSpecies>'
             '    <species compartment="c" id="spec"'
             '      initialConcentration="2.1"/>'
             '  </listOfSpecies>')
        b = ('</model>')

        # Test I: Set by species
        m = self.parse(a + b)
        m = m.myokit_model()

        # Check that intial values are set
        amount = m.get('c.spec_amount')
        conc = m.get('c.spec_concentration')

        self.assertEqual(amount.eval(), 21)
        self.assertEqual(conc.eval(), 2.1)

        # Test II: Set by initialAssignment
        x = ('<listOfInitialAssignments>'
             '  <initialAssignment symbol="spec">'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '      <cn>5</cn>'
             '    </math>'
             '  </initialAssignment>'
             '</listOfInitialAssignments>')

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check that intial values are set
        amount = m.get('c.spec_amount')
        conc = m.get('c.spec_concentration')

        self.assertEqual(amount.eval(), 50)
        self.assertEqual(conc.eval(), 5)

    def test_species_values(self):
        # Tests whether values of species is set properly. This does not
        # include rate expressions from reactions.

        a = ('<model>'
             '  <listOfCompartments>'
             '    <compartment id="c" size="10"/>'
             '  </listOfCompartments>'
             '  <listOfSpecies>'
             '    <species compartment="c" id="spec"'
             '      initialConcentration="2.1" boundaryCondition="true"/>'
             '  </listOfSpecies>')
        b = ('</model>')

        # Test I: Set by assignmentRule
        x = ('<listOfRules>'
             '  <assignmentRule variable="spec"> '
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '      <apply>'
             '        <plus/>'
             '        <ci> c </ci>'
             '        <cn> 5 </cn>'
             '      </apply>'
             '    </math>'
             '  </assignmentRule>'
             '</listOfRules>')

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check that values are set
        amount = m.get('c.spec_amount')
        conc = m.get('c.spec_concentration')

        self.assertEqual(amount.eval(), 150)
        self.assertEqual(conc.eval(), 15)

        # Test II: Set by rateRule
        x = ('<listOfRules>'
             '  <rateRule variable="spec"> '
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '      <apply>'
             '        <plus/>'
             '        <ci> c </ci>'
             '        <cn> 5 </cn>'
             '      </apply>'
             '    </math>'
             '  </rateRule>'
             '</listOfRules>')

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check that intial values are set
        damount = m.get('c.spec_amount')
        conc = m.get('c.spec_concentration')

        self.assertEqual(damount.eval(), 150)
        self.assertEqual(conc.eval(), 2.1)

    def test_parameter_exist(self):
        # Tests whether initialisation of parameters works properly.

        a = '<model><listOfParameters>'
        b = '</listOfParameters></model>'

        x = '<parameter id="a" /><parameter id="b" />'
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check that model created parameters in 'myokit' component
        self.assertTrue(m.has_variable('myokit.a'))
        self.assertTrue(m.has_variable('myokit.b'))

        # Check that total number of parameters is 3
        # [a, b, time]
        self.assertEqual(m.count_variables(), 3)

    def test_parameter_units(self):
        # Tests whether parameter units are set properly.

        a = '<model><listOfParameters>'
        b = '</listOfParameters></model>'

        x = ('<parameter id="c" value="2" />'
             '<parameter id="d" units="volt" />'
             '<parameter id="e" units="ampere" value="-1.2e-3" />')
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Get parameters
        c = m.get('myokit.c')
        d = m.get('myokit.d')
        e = m.get('myokit.e')

        # Check that units are set properly
        self.assertIsNone(c.unit())
        self.assertEqual(d.unit(), myokit.units.volt)
        self.assertEqual(e.unit(), myokit.units.ampere)

    def test_parameter_initial_values(self):
        # Tests whether initial values of parameters are set correctly.

        a = '<model>'
        b = '</model>'

        # Test I: Initial value set by parameter
        x = '<listOfParameters>' + \
            '  <parameter id="V" value="1.2">' + \
            '  </parameter>' + \
            '</listOfParameters>'

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check initial value of parameter
        var = m.get('myokit.V')
        self.assertEqual(var.eval(), 1.2)

        # Test II: Initial value set by initialAssignment
        x = '<listOfParameters>' + \
            '  <parameter id="V" value="1.2">' + \
            '  </parameter>' + \
            '</listOfParameters>' + \
            '<listOfInitialAssignments>' + \
            '  <initialAssignment symbol="V">' + \
            '    <math xmlns="http://www.w3.org/1998/Math/MathML">' + \
            '      <cn>5</cn>' + \
            '    </math>' + \
            '  </initialAssignment>' + \
            '</listOfInitialAssignments>'

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check initial value of parameter
        var = m.get('myokit.V')
        self.assertEqual(var.eval(), 5)

    def test_parameter_values(self):
        # Tests whether values of parameters are set correctly.

        a = '<model>' + \
            '  <listOfParameters>' + \
            '    <parameter id="V" value="1.2">' + \
            '    </parameter>' + \
            '    <parameter id="K" value="3">' + \
            '    </parameter>' + \
            '  </listOfParameters>'
        b = '</model>'

        # Test I: Set by assignmentRule
        x = '<listOfRules>' + \
            '  <assignmentRule variable="V"> ' + \
            '    <math xmlns="http://www.w3.org/1998/Math/MathML">' + \
            '      <apply>' + \
            '        <plus/>' + \
            '        <ci> K </ci>' + \
            '        <cn> 5 </cn>' + \
            '      </apply>' + \
            '    </math>' + \
            '  </assignmentRule>' + \
            '</listOfRules>'

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check value of parameter
        var = m.get('myokit.V')
        self.assertEqual(var.eval(), 8)

        # Test II: Set by rateRule
        x = '<listOfRules>' + \
            '  <rateRule variable="V"> ' + \
            '    <math xmlns="http://www.w3.org/1998/Math/MathML">' + \
            '      <apply>' + \
            '        <plus/>' + \
            '        <ci> V </ci>' + \
            '        <cn> 5 </cn>' + \
            '      </apply>' + \
            '    </math>' + \
            '  </rateRule>' + \
            '</listOfRules>'

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check that parameter is state variable
        var = m.get('myokit.V')
        self.assertTrue(var.is_state())

        # Check value of parameter
        self.assertEqual(var.eval(), 6.2)

    def test_stoichiometries_exist(self):
        # Tests whether stoichiometries are created properly.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" />'
             '  <species id="s2" compartment="c" />'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="s1" id="sr" />'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="s2" id="sp" />'
             '   </listOfProducts>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <plus/>'
             '      <ci>s1</ci>'
             '      <ci>s2</ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>'
             ' </listOfReactions>')
        b = ('</model>')

        m = self.parse(a + b)
        m = m.myokit_model()

        # Check that stoichiometry variables exists
        self.assertTrue(m.has_variable('c.sr'))
        self.assertTrue(m.has_variable('c.sp'))

    def test_stoichiometries_initial_value(self):
        # Tests whether initial values of stoichiometries are set properly.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" />'
             '  <species id="s2" compartment="c" />'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="s1" id="sr" stoichiometry="2.1"/>'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="s2" id="sp" stoichiometry="3.5"/>'
             '   </listOfProducts>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <plus/>'
             '      <ci>s1</ci>'
             '      <ci>s2</ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>'
             ' </listOfReactions>')
        b = ('</model>')

        # Test I: Set by speciesReference
        m = self.parse(a + b)
        m = m.myokit_model()

        # Check that initial values are set properly
        stoich_reactant = m.get('c.sr')
        stoich_product = m.get('c.sp')

        self.assertEqual(stoich_reactant.eval(), 2.1)
        self.assertEqual(stoich_product.eval(), 3.5)

        # Test I: Set by initialAssignment
        x = (' <listOfInitialAssignments>'
             '  <initialAssignment symbol="sr">'
             '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <cn>4.51</cn>'
             '   </math>'
             '  </initialAssignment>'
             '  <initialAssignment symbol="sp">'
             '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <cn>6</cn>'
             '   </math>'
             '  </initialAssignment>'
             ' </listOfInitialAssignments>')

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check that initial values are set properly
        stoich_reactant = m.get('c.sr')
        stoich_product = m.get('c.sp')

        self.assertEqual(stoich_reactant.eval(), 4.51)
        self.assertEqual(stoich_product.eval(), 6)

    def test_stoichiometry_values(self):
        # Tests whether values of parameters are set correctly.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfParameters>'
             '  <parameter id="V" value="10.23">'
             '  </parameter>'
             ' </listOfParameters>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" />'
             '  <species id="s2" compartment="c" />'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="s1" id="sr" stoichiometry="2.1"/>'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="s2" id="sp" stoichiometry="3.5"/>'
             '   </listOfProducts>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <plus/>'
             '      <ci>s1</ci>'
             '      <ci>s2</ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>'
             ' </listOfReactions>')
        b = ('</model>')

        # Test I: Set by assignmentRule
        x = ('<listOfRules>'
             '  <assignmentRule variable="sr"> '
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '      <apply>'
             '        <plus/>'
             '        <ci> V </ci>'
             '        <cn> 5 </cn>'
             '      </apply>'
             '    </math>'
             '  </assignmentRule>'
             '  <assignmentRule variable="sp"> '
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '      <apply>'
             '        <plus/>'
             '        <ci> V </ci>'
             '        <cn> 3.81 </cn>'
             '      </apply>'
             '    </math>'
             '  </assignmentRule>'
             '</listOfRules>')

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check value of stoichiometries
        var = m.get('c.sr')
        self.assertEqual(var.eval(), 15.23)

        var = m.get('c.sp')
        self.assertAlmostEqual(var.eval(), 14.04)

        # Test II: Set by rateRule
        x = ('<listOfRules>'
             '  <rateRule variable="sr"> '
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '      <apply>'
             '        <plus/>'
             '        <ci> V </ci>'
             '        <cn> 3 </cn>'
             '      </apply>'
             '    </math>'
             '  </rateRule>'
             '  <rateRule variable="sp"> '
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '      <apply>'
             '        <minus/>'
             '        <ci> V </ci>'
             '        <cn> 1 </cn>'
             '      </apply>'
             '    </math>'
             '  </rateRule>'
             '</listOfRules>')

        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check that stoichiometries are state variables
        var = m.get('c.sr')
        self.assertTrue(var.is_state())

        var = m.get('c.sp')
        self.assertTrue(var.is_state())

        # Check value of stoichiometries
        var = m.get('c.sr')
        self.assertEqual(var.eval(), 13.23)

        var = m.get('c.sp')
        self.assertEqual(var.eval(), 9.23)

    def test_reaction_expression(self):
        # Tests whether species reaction rate expressions are set correctly.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" initialAmount="2" />'
             '  <species id="s2" compartment="c" initialConcentration="1.5" />'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="s1"/>'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="s2"/>'
             '   </listOfProducts>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <plus/>'
             '      <ci>s1</ci>'
             '      <ci>s2</ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>'
             ' </listOfReactions>')
        b = ('</model>')

        m = self.parse(a + b)
        m = m.myokit_model()

        # Check that species are state variables
        var = m.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = m.get('c.s2_amount')
        self.assertTrue(var.is_state())

        # Check rates
        var = m.get('c.s1_amount')
        self.assertEqual(var.eval(), -(2 / 1.2 + 1.5))

        var = m.get('c.s2_amount')
        self.assertEqual(var.eval(), 2 / 1.2 + 1.5)

    def test_reaction_no_kinteic_law(self):
        # Tests whether missing kinetic law is handled correctly.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" initialAmount="2" />'
             '  <species id="s2" compartment="c" initialConcentration="1.5" />'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="s1"/>'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="s2"/>'
             '   </listOfProducts>'
             '  </reaction>'
             ' </listOfReactions>')
        b = ('</model>')

        m = self.parse(a + b)
        m = m.myokit_model()

        # Check that species are state variables
        var = m.get('c.s1_amount')
        self.assertFalse(var.is_state())

        var = m.get('c.s2_amount')
        self.assertFalse(var.is_state())

        # Check rates
        var = m.get('c.s1_amount')
        self.assertEqual(var.eval(), 2)

        var = m.get('c.s2_amount')
        self.assertEqual(var.eval(), 1.2 * 1.5)

    def test_reaction_boundary_species(self):
        # Tests whether rate of boundary species remains unaltered.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" initialAmount="2" />'
             '  <species id="s2" compartment="c" initialAmount="2"'
             '    boundaryCondition="true"/>'
             '  <species id="s3" compartment="c" initialConcentration="1.5"'
             '    boundaryCondition="true"/>'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="s1"/>'
             '    <speciesReference species="s2"/>'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="s3"/>'
             '   </listOfProducts>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <plus/>'
             '      <ci>s1</ci>'
             '      <ci>s3</ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>'
             ' </listOfReactions>')
        b = ('</model>')

        m = self.parse(a + b)
        m = m.myokit_model()

        # Check that species are state variables
        var = m.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = m.get('c.s2_amount')
        self.assertFalse(var.is_state())

        var = m.get('c.s3_amount')
        self.assertFalse(var.is_state())

        # Check rates
        var = m.get('c.s1_amount')
        self.assertEqual(var.eval(), -(2 / 1.2 + 1.5))

        var = m.get('c.s2_amount')
        self.assertEqual(var.eval(), 2)

        var = m.get('c.s3_amount')
        self.assertEqual(var.eval(), 1.2 * 1.5)

    def test_reaction_stoichiometry(self):
        # Tests whether stoichiometry is used in reactions correctly.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" initialAmount="2" />'
             '  <species id="s2" compartment="c" initialConcentration="1.5" />'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="s1" stoichiometry="3"/>'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="s2" stoichiometry="2"/>'
             '   </listOfProducts>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <plus/>'
             '      <ci>s1</ci>'
             '      <ci>s2</ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>'
             ' </listOfReactions>')
        b = ('</model>')

        m = self.parse(a + b)
        m = m.myokit_model()

        # Check that species are state variables
        var = m.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = m.get('c.s2_amount')
        self.assertTrue(var.is_state())

        # Check rates
        var = m.get('c.s1_amount')
        self.assertEqual(var.eval(), -3 * (2 / 1.2 + 1.5))

        var = m.get('c.s2_amount')
        self.assertEqual(var.eval(), 2 * (2 / 1.2 + 1.5))

    def test_reaction_stoichiometry_parameter(self):
        # Tests whether stoichiometry is used in reactions correctly,
        # when it's set by a parameter.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" initialAmount="2" />'
             '  <species id="s2" compartment="c" initialConcentration="1.5" />'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference id="s1ref" species="s1"'
             '      stoichiometry="3"/>'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference id="s2ref" species="s2"'
             '      stoichiometry="2"/>'
             '   </listOfProducts>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <plus/>'
             '      <ci>s1</ci>'
             '      <ci>s2</ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>'
             ' </listOfReactions>')
        b = ('</model>')

        x = ('<listOfRules>'
             '  <assignmentRule variable="s1ref"> '
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '      <cn> 5 </cn>'
             '    </math>'
             '  </assignmentRule>'
             '  <rateRule variable="s2ref"> '
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '      <cn> 3.81 </cn>'
             '    </math>'
             '  </rateRule>'
             '</listOfRules>')

        m = self.parse(a + x + b)

        m = m.myokit_model()

        # Check that species are state variables
        var = m.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = m.get('c.s2_amount')
        self.assertTrue(var.is_state())

        # Check rates
        var = m.get('c.s1_amount')
        self.assertEqual(var.eval(), -5 * (2 / 1.2 + 1.5))

        var = m.get('c.s2_amount')
        self.assertEqual(var.eval(), 2 * (2 / 1.2 + 1.5))

    def test_reaction_conversion_factor(self):
        # Tests whether rate contributions are converted correctly.

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfParameters>'
             '  <parameter id="x" value="1.2">'
             '  </parameter>'
             '  <parameter id="y" value="3">'
             '  </parameter>'
             ' </listOfParameters>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" initialAmount="2"'
             '    conversionFactor="x"/>'
             '  <species id="s2" compartment="c" initialConcentration="1.5"'
             '    conversionFactor="y"/>'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="s1"/>'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="s2"/>'
             '   </listOfProducts>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <plus/>'
             '      <ci>s1</ci>'
             '      <ci>s2</ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>'
             ' </listOfReactions>')
        b = ('</model>')

        m = self.parse(a + b)
        m = m.myokit_model()

        # Check that species are state variables
        var = m.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = m.get('c.s2_amount')
        self.assertTrue(var.is_state())

        # Check rates
        var = m.get('c.s1_amount')
        self.assertEqual(var.eval(), -1.2 * (2 / 1.2 + 1.5))

        var = m.get('c.s2_amount')
        self.assertEqual(var.eval(), 3 * (2 / 1.2 + 1.5))

    def test_time(self):
        # Tests whether time variable is created properly.

        a = '<model timeUnits="second"><listOfParameters>'
        b = '</listOfParameters></model>'

        m = self.parse(a + b)
        m = m.myokit_model()

        # Check that time variable exists
        self.assertTrue(m.has_variable('myokit.time'))

        # Check that unit is set
        var = m.get('myokit.time')
        self.assertEqual(var.unit(), myokit.units.second)

        # Check that initial value is set
        self.assertEqual(var.eval(), 0)

        # Chet that variable is time bound
        self.assertTrue(var.binding(), 'time')


class TestParameter(unittest.TestCase):
    """
    Unit tests for :class:`Parameter`.
    """

    @classmethod
    def setUpClass(cls):
        cls.model = sbml.Model(name='model')
        cls.sid = 'parameter'
        cls.p = cls.model.add_parameter(sid=cls.sid)

    def test_bad_model(self):

        model = 'model'
        sid = 'parameter'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', sbml.Parameter, model, sid)

    def test_initial_value(self):

        # Check default initial value
        self.assertIsNone(self.p.initial_value())

        # Check bad value
        expr = 2
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.p.set_initial_value, expr)

        # Check good value
        expr = myokit.Number(2)
        self.p.set_initial_value(expr)

        self.assertEqual(self.p.initial_value(), expr)

    def test_is_rate(self):

        # Check default
        self.assertFalse(self.p.is_rate())

        # Check setting rate to true
        expr = myokit.Number(2)
        self.p.set_value(value=expr, is_rate=True)

        self.assertTrue(self.p.is_rate())

    def test_sid(self):
        self.assertEqual(self.p.sid(), self.sid)

    def test_string_representation(self):
        self.assertEqual(str(self.p), '<Parameter ' + self.sid + '>')

    def test_units(self):

        # Check default units
        self.assertIsNone(self.p.units())

        # Check bad size units
        unit = 'mL'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.p.set_units, unit)

        # Check valid size units
        unit = myokit.units.L * 1E-3
        self.p.set_units(unit)

        self.assertEqual(self.p.units(), unit)

    def test_value(self):

        # Check bad value
        expr = 2
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.p.set_value, expr)

        # Check good value
        expr = myokit.Number(2)
        self.p.set_value(expr)

        self.assertEqual(self.p.value(), expr)


class TestReaction(unittest.TestCase):
    """
    Unit tests for :class:`Reaction`.
    """

    @classmethod
    def setUpClass(cls):
        cls.model = sbml.Model(name='model')
        cls.sid = 'reaction'
        cls.r = cls.model.add_reaction(sid=cls.sid)

    def test_bad_model(self):

        model = 'model'
        sid = 'reaction'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', sbml.Reaction, model, sid)

    def test_kinetic_law(self):

        # Check default
        self.assertIsNone(self.r.kinetic_law())

        # Check bad kinetic law
        expr = '2 * s'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.r.set_kinetic_law, expr)

        # Check good kinetic law
        expr = myokit.Multiply(myokit.Number(2), myokit.Name('s'))
        self.r.set_kinetic_law(expr)

        self.assertEqual(self.r.kinetic_law(), expr)

    def test_modifiers(self):

        # Check bad species
        sid = 'modifier'
        species = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.r.add_modifier, species, sid)

        # Check invalid sid
        sid = ';'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid='species',
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.assertRaisesRegex(
            sbml.SBMLError, 'Invalid SId "', self.r.add_modifier, species, sid)

        # Check good sid
        sid = 'modifier'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid='species',
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.r.add_modifier(species, sid)

        self.assertEqual(len(self.r.modifiers()), 1)
        self.assertIsInstance(
            self.r.modifiers()[0], sbml.ModifierSpeciesReference)

        # Check duplicate sid
        sid = 'modifier'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid='species',
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.assertRaisesRegex(
            sbml.SBMLError, 'Duplicate SId "', self.r.add_modifier, species,
            sid)

    def test_products(self):

        # Check bad species
        sid = 'product'
        species = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.r.add_product, species, sid)

        # Check invalid sid
        sid = ';'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid='species',
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.assertRaisesRegex(
            sbml.SBMLError, 'Invalid SId "', self.r.add_product, species, sid)

        # Check good sid
        sid = 'product'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid='species',
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.r.add_product(species, sid)

        self.assertEqual(len(self.r.products()), 1)
        self.assertIsInstance(
            self.r.products()[0], sbml.SpeciesReference)

        # Check duplicate sid
        sid = 'product'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid='species',
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.assertRaisesRegex(
            sbml.SBMLError, 'Duplicate SId "', self.r.add_product, species,
            sid)

    def test_reactants(self):

        # Check bad species
        sid = 'reactant'
        species = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.r.add_reactant, species, sid)

        # Check invalid sid
        sid = ';'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid='species',
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.assertRaisesRegex(
            sbml.SBMLError, 'Invalid SId "', self.r.add_reactant, species, sid)

        # Check good sid
        sid = 'reactant'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid='species',
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.r.add_reactant(species, sid)

        self.assertEqual(len(self.r.reactants()), 1)
        self.assertIsInstance(
            self.r.reactants()[0], sbml.SpeciesReference)

        # Check duplicate sid
        sid = 'reactant'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid='species',
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.assertRaisesRegex(
            sbml.SBMLError, 'Duplicate SId "', self.r.add_reactant, species,
            sid)

    def test_sid(self):
        self.assertEqual(self.r.sid(), self.sid)

    def test_species(self):

        # Add modifier species
        sid = 'modifier_species'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid=sid,
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.r.add_modifier(species, sid)

        # Check that species are accessible
        self.assertIsInstance(self.r.species(sid), sbml.Species)

        # Add product species
        sid = 'product_species'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid=sid,
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.r.add_product(species, sid)

        # Check that species are accessible
        self.assertIsInstance(self.r.species(sid), sbml.Species)

        # Add reactant species
        sid = 'reactant_species'
        compartment = sbml.Compartment(self.model, sid='compartment')
        species = sbml.Species(
            compartment=compartment,
            sid=sid,
            is_amount=False,
            is_constant=False,
            is_boundary=False)
        self.r.add_reactant(species, sid)

        # Check that species are accessible
        self.assertIsInstance(self.r.species(sid), sbml.Species)

    def test_string_representation(self):
        self.assertEqual(str(self.r), '<Reaction ' + self.sid + '>')


class TestSpecies(unittest.TestCase):
    """
    Unit tests for :class:`Species`.
    """

    @classmethod
    def setUpClass(cls):
        cls.model = sbml.Model(name='model')
        cls.c = cls.model.add_compartment(sid='compartment')

    def test_is_amount(self):

        # Test is amount
        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=True, is_constant=False,
            is_boundary=False)

        self.assertTrue(species.is_amount())

        # Test is concentration
        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        self.assertFalse(species.is_amount())

        # Test bad amount
        sid = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Is_amount <', sbml.Species, self.c,
            sid, 'No', False, False)

    def test_is_boundary(self):

        # Test is boundary
        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=True)

        self.assertTrue(species.is_boundary())

        # Test is not boundary
        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        self.assertFalse(species.is_boundary())

        # Test bad boundary
        sid = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Is_boundary <', sbml.Species, self.c,
            sid, False, False, 'No')

    def test_compartment(self):

        # Bad compartment
        sid = 'species'
        comp = 'compartment'

        self.assertRaisesRegex(
            sbml.SBMLError, '<', sbml.Species, comp,
            sid, False, 'No', False)

        # Test good compartment
        sid = 'species'
        comp = self.c
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=True,
            is_boundary=False)

        self.assertEqual(species.compartment(), self.c)

    def test_is_constant(self):

        # Test is constant
        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=True,
            is_boundary=False)

        self.assertTrue(species.is_constant())

        # Test is not constant
        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        self.assertFalse(species.is_boundary())

        # Test bad constant
        sid = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, 'Is_constant <', sbml.Species, self.c,
            sid, False, 'No', False)

    def test_conversion_factor(self):

        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        # Test default value
        self.assertIsNone(species.conversion_factor())

        # Bad conversion factor
        self.assertRaisesRegex(
            sbml.SBMLError, '<', species.set_conversion_factor, 10)

        # Good model conversion factor
        factor = sbml.Parameter(self.model, 'parameter')
        self.model.set_conversion_factor(factor)

        self.assertEqual(species.conversion_factor(), factor)

        # Good species conversion factor
        factor = sbml.Parameter(self.model, 'parameter 2')
        species.set_conversion_factor(factor)

        self.assertEqual(species.conversion_factor(), factor)

    def test_correct_initial_value(self):

        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        # Check default
        self.assertTrue(species.correct_initial_value())

        # Check bad input
        self.assertRaisesRegex(
            sbml.SBMLError, '<', species.set_correct_initial_value, 'Yes')

        # Check not correct units
        species.set_correct_initial_value(False)
        self.assertFalse(species.correct_initial_value())

        # Check correct units
        species.set_correct_initial_value(True)
        self.assertTrue(species.correct_initial_value())

    def test_initial_value(self):

        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        # Check default initial value
        self.assertIsNone(species.initial_value())

        # Check bad value
        expr = 2
        self.assertRaisesRegex(
            sbml.SBMLError, '<', species.set_initial_value, expr)

        # Check good value
        expr = myokit.Number(2)
        species.set_initial_value(expr)

        self.assertEqual(species.initial_value(), expr)

    def test_is_rate(self):

        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        # Check default
        self.assertFalse(species.is_rate())

        # Check setting rate to true
        expr = myokit.Number(2)
        species.set_value(value=expr, is_rate=True)

        self.assertTrue(species.is_rate())

    def test_sid(self):
        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        self.assertEqual(species.sid(), sid)

    def test_string_representation(self):
        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        self.assertEqual(str(species), '<Species ' + sid + '>')

    def test_substance_units(self):

        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        # Check default substance units
        unit = myokit.units.dimensionless
        self.assertEqual(species.substance_units(), unit)

        # Check bad units
        unit = 'mg'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', species.set_substance_units, unit)

        # Check model substance units
        unit = myokit.units.g
        self.model.set_substance_units(unit)

        self.assertEqual(species.substance_units(), unit)

        # Check species subtance units
        unit = myokit.units.g * 1E-3
        species.set_substance_units(unit)

        self.assertEqual(species.substance_units(), unit)

    def test_value(self):

        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        # Check bad value
        expr = 2
        self.assertRaisesRegex(
            sbml.SBMLError, '<', species.set_value, expr)

        # Check good value
        expr = myokit.Number(2)
        species.set_value(expr)

        self.assertEqual(species.value(), expr)


class TestSpeciesReference(unittest.TestCase):
    """
    Unit tests for :class:`SpeciesReference`.
    """

    @classmethod
    def setUpClass(cls):
        model = sbml.Model(name='model')
        comp = model.add_compartment(sid='compartment')
        cls.species = sbml.Species(comp, 'species', False, False, False)
        cls.sid = 'species_reference'
        cls.sr = sbml.SpeciesReference(cls.species, cls.sid)

    def test_initial_value(self):

        # Check default initial value
        self.assertIsNone(self.sr.initial_value())

        # Check bad value
        expr = 2
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.sr.set_initial_value, expr)

        # Check good value
        expr = myokit.Number(2)
        self.sr.set_initial_value(expr)

        self.assertEqual(self.sr.initial_value(), expr)

    def test_is_rate(self):

        # Check default
        self.assertFalse(self.sr.is_rate())

        # Check setting rate to true
        expr = myokit.Number(2)
        self.sr.set_value(value=expr, is_rate=True)

        self.assertTrue(self.sr.is_rate())

    def test_sid(self):
        self.assertEqual(self.sr.sid(), self.sid)

    def test_species(self):

        # Check bad species
        species = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', sbml.SpeciesReference, species)

        # Check good species
        self.assertEqual(self.sr.species(), self.species)

    def test_value(self):

        # Check bad value
        expr = 2
        self.assertRaisesRegex(
            sbml.SBMLError, '<', self.sr.set_value, expr)

        # Check good value
        expr = myokit.Number(2)
        self.sr.set_value(expr)

        self.assertEqual(self.sr.value(), expr)


class TestModifierSpeciesReference(unittest.TestCase):
    """
    Unit tests for :class:`ModifierSpeciesReference`.
    """

    @classmethod
    def setUpClass(cls):
        model = sbml.Model(name='model')
        comp = model.add_compartment(sid='compartment')
        cls.species = sbml.Species(comp, 'species', False, False, False)
        cls.sid = 'modifier_species_reference'
        cls.sr = sbml.ModifierSpeciesReference(cls.species, cls.sid)

    def test_sid(self):
        self.assertEqual(self.sr.sid(), self.sid)

    def test_species(self):

        # Check bad species
        species = 'species'
        self.assertRaisesRegex(
            sbml.SBMLError, '<', sbml.ModifierSpeciesReference, species)

        # Check good species
        self.assertEqual(self.sr.species(), self.species)


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
