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

from myokit.formats.sbml._api import _MyokitConverter as X

from myokit.tests import WarningCollector

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
        # Tests assignable() and assignable_or_csymbol()

        model = sbml.Model(name='model')

        # Add assignables to model
        c_sid = 'compartment'
        c = model.add_compartment(c_sid)

        p_sid = 'parameters'
        p = model.add_parameter(p_sid)

        s_sid = 'species'
        comp = sbml.Compartment(model=model, sid=c_sid)
        s = model.add_species(compartment=comp, sid=s_sid)

        # Check that all assignables are accessible
        t = 'http://www.sbml.org/sbml/symbols/time'
        self.assertEqual(model.assignable(c_sid), c)
        self.assertEqual(model.assignable(p_sid), p)
        self.assertEqual(model.assignable(s_sid), s)
        self.assertRaises(KeyError, model.assignable, t)

        # Check that assignables and csymbols can be obtained with
        # assignable_or_csymbol:
        self.assertEqual(model.assignable_or_csymbol(c_sid), c)
        self.assertEqual(model.assignable_or_csymbol(p_sid), p)
        self.assertEqual(model.assignable_or_csymbol(s_sid), s)
        self.assertEqual(model.assignable_or_csymbol(t), model.time())
        self.assertRaises(
            KeyError, model.assignable,
            'http://www.sbml.org/sbml/symbols/beer')
        self.assertRaises(
            KeyError, model.assignable, 'http://google.com')
        self.assertRaises(
            KeyError, model.assignable, 'https://google.com')

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

    def test_time_symbol(self):

        model = sbml.Model(name='model')
        time = model.time()
        turl = 'http://www.sbml.org/sbml/symbols/time'
        self.assertIsInstance(time, sbml.CSymbolVariable)
        self.assertEqual(str(time), '<CSymbolVariable ' + turl + '>')
        self.assertEqual(time.definition_url(), turl)

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

    def test_initial_value(self):

        sid = 'species'
        species = sbml.Species(
            compartment=self.c, sid=sid, is_amount=False, is_constant=False,
            is_boundary=False)

        # Check default initial value
        expr, is_amount = species.initial_value()
        self.assertIsNone(expr)
        self.assertIsNone(is_amount)

        # Check bad value
        expr = 2
        self.assertRaisesRegex(
            sbml.SBMLError, '<', species.set_initial_value, expr)

        # Check good value (default in_amount=False)
        expr = myokit.Number(2)
        species.set_initial_value(expr)
        value, is_amount = species.initial_value()

        self.assertEqual(value, expr)
        self.assertFalse(is_amount)

        # Check good value
        expr = myokit.Number(10.1)
        species.set_initial_value(expr, in_amount=True)
        value, is_amount = species.initial_value()

        self.assertEqual(value, expr)
        self.assertTrue(is_amount)

        # Check bad in_amount argument
        expr = myokit.Number(10.1)
        self.assertRaisesRegex(
            sbml.SBMLError,
            '<in_amount> needs to be an instance of bool or None.',
            species.set_initial_value, expr, 'Yes')

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


class SBMLTestMyokitModel(unittest.TestCase):
    """
    Unit tests for Model.myokit_model method.
    """

    def test_compartments(self):
        # Tests whether compartments are added properly to the myokit model.

        # Check setting initial value for size
        sm = sbml.Model()
        c = sm.add_compartment('comp')
        c.set_initial_value(myokit.Number(2))
        mm = sm.myokit_model()
        self.assertTrue(mm.has_component('comp'))
        self.assertEqual(mm.get('comp.size').rhs(), myokit.Number(2))
        self.assertFalse(mm.get('comp.size').is_state())

        # Check setting unreferenced initial value parameter for size
        sm = sbml.Model()
        p = sbml.Parameter(sm, 'parameter')
        c = sm.add_compartment('comp')
        c.set_initial_value(myokit.Name(p))
        self.assertRaisesRegex(
            sbml.SBMLError, 'Initial value for the size of <',
            sm.myokit_model)

        # Check setting referenced initial value parameter for size
        sm = sbml.Model()
        p = sm.add_parameter('parameter')
        c = sm.add_compartment('comp')
        c.set_initial_value(myokit.Name(p))
        mm = sm.myokit_model()
        self.assertTrue(mm.has_component('comp'))
        self.assertEqual(mm.get('comp.size').rhs().code(), 'myokit.parameter')
        self.assertFalse(mm.get('comp.size').is_state())

        # Check setting size as value
        sm = sbml.Model()
        c = sm.add_compartment('comp')
        c.set_value(myokit.Number(3))
        mm = sm.myokit_model()
        self.assertEqual(mm.get('comp.size').rhs(), myokit.Number(3))
        self.assertFalse(mm.get('comp.size').is_state())

        # Check setting unreferenced value parameter for size
        sm = sbml.Model()
        p = sbml.Parameter(sm, 'parameter')
        c = sm.add_compartment('comp')
        c.set_value(myokit.Name(p))
        self.assertRaisesRegex(
            sbml.SBMLError, 'Value for the size of <',
            sm.myokit_model)

        # Check setting referenced value parameter for size
        sm = sbml.Model()
        p = sm.add_parameter('parameter')
        c = sm.add_compartment('comp')
        c.set_value(myokit.Name(p))
        mm = sm.myokit_model()
        self.assertTrue(mm.has_component('comp'))
        self.assertEqual(mm.get('comp.size').rhs().code(), 'myokit.parameter')
        self.assertFalse(mm.get('comp.size').is_state())

        # Check setting size as rate
        sm = sbml.Model()
        c = sm.add_compartment('comp')
        c.set_value(myokit.Number(1.5), is_rate=True)
        with WarningCollector():
            mm = sm.myokit_model()
        self.assertEqual(mm.get('comp.size').rhs(), myokit.Number(1.5))
        self.assertTrue(mm.get('comp.size').is_state())

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

    def test_parameters(self):
        # Tests if parameters are converted

        m = sbml.Model()
        m.add_parameter('z')
        m.add_parameter('boat')
        m.add_parameter('c')
        m = m.myokit_model()

        # Check that model created parameters in 'global' component
        self.assertTrue(m.has_variable('myokit.z'))
        self.assertTrue(m.has_variable('myokit.boat'))
        self.assertTrue(m.has_variable('myokit.c'))

        # Check that total number of parameters is 4 (3 parameters and time)
        self.assertEqual(m.count_variables(), 4)

    def test_parameters_initial_value(self):
        # Tests adding parameters set with initial values

        m = sbml.Model()
        p = m.add_parameter('param')
        p.set_initial_value(myokit.Number(7))
        mm = m.myokit_model()
        pp = mm.get('myokit.param')
        self.assertFalse(pp.is_state())
        self.assertEqual(pp.rhs(), myokit.Number(7))

        # Test units
        self.assertIsNone(pp.unit())
        p.set_units(myokit.units.pF)
        mm = m.myokit_model()
        pp = mm.get('myokit.param')
        self.assertFalse(pp.is_state())
        self.assertEqual(pp.rhs(), myokit.Number(7))
        self.assertEqual(pp.unit(), myokit.units.pF)

        # Unreferenced parameter
        m = sbml.Model()
        p_bad = sbml.Parameter(m, 'p_bad')
        p = m.add_parameter('param')
        p.set_initial_value(myokit.Name(p_bad))
        self.assertRaisesRegex(
            sbml.SBMLError, 'Initial value of <', m.myokit_model)

    def test_parameters_values(self):
        # Tests adding parameters set with a value (non-state)

        m = sbml.Model()
        p = m.add_parameter('param')
        p.set_value(myokit.Plus(myokit.Number(7), myokit.Number(3)))
        mm = m.myokit_model()
        pp = mm.get('myokit.param')
        self.assertFalse(pp.is_state())
        self.assertEqual(
            pp.rhs(), myokit.Plus(myokit.Number(7), myokit.Number(3)))

        # Test units
        self.assertIsNone(pp.unit())
        p.set_units(myokit.units.pF)
        mm = m.myokit_model()
        pp = mm.get('myokit.param')
        self.assertFalse(pp.is_state())
        self.assertEqual(pp.rhs().code(), '7 + 3')
        self.assertEqual(pp.unit(), myokit.units.pF)

        # Unreferenced parameter
        m = sbml.Model()
        p_bad = sbml.Parameter(m, 'p_bad')
        p = m.add_parameter('param')
        p.set_value(myokit.Name(p_bad))
        self.assertRaisesRegex(
            sbml.SBMLError, 'Value of <', m.myokit_model)

    def test_parameter_values_rate(self):
        # Tests adding parameters set with a value (state)

        m = sbml.Model()
        p = m.add_parameter('param')
        p.set_value(myokit.Number(3.2), is_rate=True)
        with WarningCollector():
            mm = m.myokit_model()
        pp = mm.get('myokit.param')
        self.assertTrue(pp.is_state())
        self.assertEqual(pp.rhs(), myokit.Number(3.2))
        self.assertEqual(pp.state_value(), 0)

        # With initial value
        p.set_initial_value(myokit.Number(1))
        mm = m.myokit_model()
        pp = mm.get('myokit.param')
        self.assertTrue(pp.is_state())
        self.assertEqual(pp.rhs(), myokit.Number(3.2))
        self.assertEqual(pp.state_value(), 1)

        # Test units
        self.assertIsNone(pp.unit())
        p.set_units(myokit.units.pF)
        mm = m.myokit_model()
        pp = mm.get('myokit.param')
        self.assertTrue(pp.is_state())
        self.assertEqual(pp.rhs(), myokit.Number(3.2))
        self.assertEqual(pp.unit(), myokit.units.pF)

        # Unreferenced parameter
        m = sbml.Model()
        p_bad = sbml.Parameter(m, 'p_bad')
        p = m.add_parameter('param')
        p.set_value(myokit.Name(p_bad), is_rate=True)
        with WarningCollector():
            self.assertRaisesRegex(
                sbml.SBMLError, 'Value of <', m.myokit_model)

    def test_species(self):
        # Tests whether species initialisation in amount and concentration
        # works.

        # Species in amount
        m = sbml.Model()
        c = m.add_compartment('c')
        m.add_species(c, 's1', is_amount=True)
        mm = m.myokit_model()

        # Check whether species exists in amount
        self.assertTrue(mm.has_variable('c.s1_amount'))
        self.assertFalse(mm.has_variable('c.s1_concentration'))

        # Check that component has 2 variables (compartment size and s1 amount)
        self.assertEqual(mm.get('c').count_variables(), 2)

        # Species in concentration
        m.add_species(c, 's2', is_amount=False)
        mm = m.myokit_model()

        # Check whether species exists in amount and concentration
        self.assertTrue(mm.has_variable('c.s2_amount'))
        self.assertTrue(mm.has_variable('c.s2_concentration'))

        # Check that component now has 4 variables
        self.assertEqual(mm.get('c').count_variables(), 4)

    def test_species_bad_compartment(self):
        # Tests handling of unreferenced compartment.

        m = sbml.Model()
        c = sbml.Compartment(m, 'c')
        m.add_species(c, 's1', is_amount=True)
        self.assertRaisesRegex(
            sbml.SBMLError, 'The <', m.myokit_model)

    def test_species_initial_value(self):
        # Tests converting setting species defined through an initial value

        # I: Species in amount
        m = sbml.Model()
        c = m.add_compartment('comp')
        c.set_initial_value(myokit.Number(2))
        s1 = m.add_species(c, 'spec_1', is_amount=True)

        # Initial value in amount
        s1.set_initial_value(value=myokit.Number(3), in_amount=True)
        mm = m.myokit_model()
        ms = mm.get('comp.spec_1_amount')
        self.assertFalse(ms.is_state())
        self.assertEqual(ms.rhs(), myokit.Number(3))

        # Initial value in concentration
        s1.set_initial_value(value=myokit.Number(3), in_amount=False)
        mm = m.myokit_model()
        ms = mm.get('comp.spec_1_amount')
        self.assertFalse(ms.is_state())
        self.assertEqual(
            ms.rhs().code(), '3 * comp.size')
        self.assertEqual(ms.eval(), 3 * 2)

        # Species in concentration
        s2 = m.add_species(c, 'spec_2', is_amount=False)
        s2.set_initial_value(myokit.Number(4))
        mm = m.myokit_model()
        sc = mm.get('comp.spec_2_concentration')
        self.assertFalse(sc.is_state())
        self.assertEqual(
            sc.rhs().code(), 'comp.spec_2_amount / comp.size')
        sa = mm.get('comp.spec_2_amount')
        self.assertFalse(sa.is_state())
        self.assertEqual(sa.rhs().code(), '4 * comp.size')

        # Species in amount: unreferenced parameter
        p1 = sbml.Parameter(m, 'p1')
        s1.set_initial_value(value=myokit.Name(p1), in_amount=True)
        self.assertRaisesRegex(
            sbml.SBMLError, 'Initial value of <', m.myokit_model)

        # Species in amount: referenced parameter
        p1 = m.add_parameter('p1')
        s1.set_initial_value(value=myokit.Name(p1), in_amount=True)
        mm = m.myokit_model()
        ms = mm.get('comp.spec_1_amount')
        self.assertFalse(ms.is_state())
        self.assertEqual(ms.rhs().code(), 'myokit.p1')

        # Species in concentration: unreferenced parameter
        p2 = sbml.Parameter(m, 'p2')
        s2.set_initial_value(value=myokit.Name(p2), in_amount=False)
        self.assertRaisesRegex(
            sbml.SBMLError, 'Initial value of <', m.myokit_model)

    def test_species_value(self):
        # Tests converting setting species defined through a normal equation

        # Species in amount
        m = sbml.Model()
        c = m.add_compartment('comp')
        s1 = m.add_species(c, 'spec_1', is_amount=True)
        s1.set_value(myokit.Number(3))
        mm = m.myokit_model()
        ms = mm.get('comp.spec_1_amount')
        self.assertFalse(ms.is_state())
        self.assertEqual(ms.rhs(), myokit.Number(3))

        # Species in concentration
        s2 = m.add_species(c, 'spec_2', is_amount=False)
        s2.set_value(myokit.Number(4))
        mm = m.myokit_model()
        sc = mm.get('comp.spec_2_concentration')
        self.assertFalse(sc.is_state())
        self.assertEqual(
            sc.rhs().code(), 'comp.spec_2_amount / comp.size')
        sa = mm.get('comp.spec_2_amount')
        self.assertFalse(sa.is_state())
        self.assertEqual(sa.rhs().code(), '4 * comp.size')

        # Species in amount: bad parameter
        m = sbml.Model()
        p = sbml.Parameter(m, 'parameter')
        c = m.add_compartment('comp')
        s1 = m.add_species(c, 'spec_1', is_amount=True)
        s1.set_value(myokit.Name(p))
        self.assertRaisesRegex(sbml.SBMLError, 'Value of <', m.myokit_model)

        # Species in concentration: bad parameter
        m = sbml.Model()
        p = sbml.Parameter(m, 'parameter')
        c = m.add_compartment('comp')
        s1 = m.add_species(c, 'spec_1', is_amount=False)
        s1.set_value(myokit.Name(p))
        self.assertRaisesRegex(sbml.SBMLError, 'Value of <', m.myokit_model)

    def test_species_value_rate(self):
        # Tests converting setting species defined through an ODE equation

        # I: No initial compartment size
        m = sbml.Model()
        c = m.add_compartment('comp')

        # Species in amount
        s1 = m.add_species(c, 'spec_1', is_amount=True)
        s1.set_value(myokit.Number(3), is_rate=True)
        with WarningCollector():
            mm = m.myokit_model()
        ms = mm.get('comp.spec_1_amount')
        self.assertTrue(ms.is_state())
        self.assertEqual(ms.rhs(), myokit.Number(3))
        self.assertEqual(ms.state_value(), 0)
        s1.set_initial_value(myokit.Number(7))
        mm = m.myokit_model()
        ms = mm.get('comp.spec_1_amount')
        self.assertTrue(ms.is_state())
        self.assertEqual(ms.rhs(), myokit.Number(3))
        self.assertEqual(ms.state_value(), 7)

        # Species in concentration
        s2 = m.add_species(c, 'spec_2', is_amount=False)
        s2.set_value(myokit.Number(4), is_rate=True)
        with WarningCollector():
            mm = m.myokit_model()
        sc = mm.get('comp.spec_2_concentration')
        self.assertFalse(sc.is_state())
        self.assertEqual(
            sc.rhs().code(), 'comp.spec_2_amount / comp.size')
        sa = mm.get('comp.spec_2_amount')
        self.assertTrue(sa.is_state())
        self.assertEqual(sa.rhs().code(), '4 * comp.size')
        self.assertEqual(sa.state_value(), 0)

        # I: Set compartment size
        m = sbml.Model()
        c = m.add_compartment('comp')
        c.set_initial_value(myokit.Number(2))

        # Species in amount
        s1 = m.add_species(c, 'spec_1', is_amount=True)
        s1.set_value(myokit.Number(3), is_rate=True)
        with WarningCollector():
            mm = m.myokit_model()
        ms = mm.get('comp.spec_1_amount')
        self.assertTrue(ms.is_state())
        self.assertEqual(ms.rhs(), myokit.Number(3))
        self.assertEqual(ms.state_value(), 0)
        s1.set_initial_value(myokit.Number(7))
        mm = m.myokit_model()
        ms = mm.get('comp.spec_1_amount')
        self.assertTrue(ms.is_state())
        self.assertEqual(ms.rhs(), myokit.Number(3))
        self.assertEqual(ms.state_value(), 7)

        # Species in concentration
        s2 = m.add_species(c, 'spec_2', is_amount=False)
        s2.set_value(myokit.Number(4), is_rate=True)
        with WarningCollector():
            mm = m.myokit_model()
        sc = mm.get('comp.spec_2_concentration')
        self.assertFalse(sc.is_state())
        self.assertEqual(
            sc.rhs().code(), 'comp.spec_2_amount / comp.size')
        s2.set_initial_value(myokit.Number(6))
        mm = m.myokit_model()
        sa = mm.get('comp.spec_2_amount')
        self.assertTrue(sa.is_state())
        self.assertEqual(sa.rhs().code(), '4 * comp.size')
        self.assertEqual(sa.state_value(), 6 * 2)

    def test_species_units(self):
        # Tests whether species units are set properly.

        # Test I: No substance nor size units provided
        m = sbml.Model()
        c = m.add_compartment('c')
        s = m.add_species(c, 'spec')
        mm = m.myokit_model()
        amount = mm.get('c.spec_amount')
        conc = mm.get('c.spec_concentration')
        self.assertEqual(amount.unit(), myokit.units.dimensionless)
        self.assertEqual(conc.unit(), myokit.units.dimensionless)

        # Test II: Substance and size units provided
        c.set_size_units(myokit.units.m)
        s.set_substance_units(myokit.units.kg)
        mm = m.myokit_model()
        amount = mm.get('c.spec_amount')
        conc = mm.get('c.spec_concentration')
        self.assertEqual(amount.unit(), myokit.units.kg)
        self.assertEqual(conc.unit(), myokit.units.kg / myokit.units.meter)

    def test_reaction_expression(self):
        # Tests whether species reaction rate expressions are set correctly.

        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s1.set_initial_value(myokit.Number(2), in_amount=True)
        s2 = m.add_species(c, 's2')
        s2.set_initial_value(myokit.Number(1.5))
        r = m.add_reaction('r')
        r.add_reactant(s1)
        r.add_product(s2)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))
        mm = m.myokit_model()

        # Check that species are state variables
        var = mm.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = mm.get('c.s2_amount')
        self.assertTrue(var.is_state())

        # Check rates
        var = mm.get('c.s1_amount')
        self.assertEqual(var.eval(), -(2 / 1.2 + 1.5))

        var = mm.get('c.s2_amount')
        self.assertEqual(var.eval(), 2 / 1.2 + 1.5)

    def test_reaction_bad_compartment(self):
        # Tests handling of unreferenced compartment for reactants/products.

        # Bad compartment for reactant
        m = sbml.Model()
        c = sbml.Compartment(m, 'compartment')
        s1 = sbml.Species(c, 's1', False, False, False)
        r = m.add_reaction('r')
        r.add_reactant(s1, 'sr1')
        self.assertRaisesRegex(sbml.SBMLError, 'The <', m.myokit_model)

        # Bad compartment for product
        m = sbml.Model()
        c = sbml.Compartment(m, 'compartment')
        s1 = sbml.Species(c, 's1', False, False, False)
        r = m.add_reaction('r')
        r.add_product(s1, 'sr1')
        self.assertRaisesRegex(sbml.SBMLError, 'The <', m.myokit_model)

    def test_reaction_bad_species(self):
        # Tests handling of unreferenced species in kinetic law.

        # Bad reactant
        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = sbml.Species(c, 's1', False, False, False)
        r = m.add_reaction('r')
        r.add_reactant(s1)
        r.set_kinetic_law(myokit.Name(s1))
        self.assertRaisesRegex(
            sbml.SBMLError, 'Kinetic law of <', m.myokit_model)

        # Bad product
        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s2 = sbml.Species(c, 's2', False, False, False)
        r = m.add_reaction('r')
        r.add_product(s2)
        r.set_kinetic_law(myokit.Name(s2))
        self.assertRaisesRegex(
            sbml.SBMLError, 'Kinetic law of <', m.myokit_model)

        # Good reactant, bad modifier
        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s2 = sbml.Species(c, 's2', False, False, False)
        r = m.add_reaction('r')
        r.add_reactant(s1)
        r.add_modifier(s2)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))
        with WarningCollector():
            self.assertRaisesRegex(
                sbml.SBMLError, 'Reaction rate expression of <',
                m.myokit_model)

        # Good product, bad modifier
        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s2 = sbml.Species(c, 's2', False, False, False)
        r = m.add_reaction('r')
        r.add_product(s1)
        r.add_modifier(s2)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))
        with WarningCollector():
            self.assertRaisesRegex(
                sbml.SBMLError, 'Reaction rate expression of <',
                m.myokit_model)

    def test_reaction_bad_kinetic_law(self):
        # Tests handling of unreferenced variables in ketic law.
        m = sbml.Model()
        p = sbml.Parameter(m, 'parameter')
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        r = m.add_reaction('r')
        r.add_reactant(s1)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(p)))

        with WarningCollector():
            self.assertRaisesRegex(
                sbml.SBMLError, 'Reaction rate expression of <',
                m.myokit_model)

    def test_reaction_no_kinetic_law(self):
        # Tests whether missing kinetic law is handled correctly.

        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s1.set_initial_value(myokit.Number(2), in_amount=True)
        s2 = m.add_species(c, 's2')
        s2.set_initial_value(myokit.Number(1.5))
        r = m.add_reaction('r')
        r.add_reactant(s1)
        r.add_product(s2)
        mm = m.myokit_model()

        # Check that species are state variables
        var = mm.get('c.s1_amount')
        self.assertFalse(var.is_state())

        var = mm.get('c.s2_amount')
        self.assertFalse(var.is_state())

        # Check rates
        var = mm.get('c.s1_amount')
        self.assertEqual(var.eval(), 2)

        var = mm.get('c.s2_amount')
        self.assertEqual(var.eval(), 1.2 * 1.5)

    def test_reaction_bad_conversion_factor(self):
        # Tests whether error is thrown when conversion factor is
        # not referenced in model.

        # Bad conversion factor for reactant
        m = sbml.Model()
        px = sbml.Parameter(m, 'x')
        px.set_value(myokit.Number(1.2))
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s1.set_initial_value(myokit.Number(2), in_amount=True)
        s1.set_conversion_factor(px)
        s2 = m.add_species(c, 's2')
        s2.set_initial_value(myokit.Number(1.5))
        r = m.add_reaction('r')
        r.add_reactant(s1)
        r.add_product(s2)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))

        self.assertRaisesRegex(sbml.SBMLError, 'Species <', m.myokit_model)

        # Bad conversion factor for product
        m = sbml.Model()
        px = sbml.Parameter(m, 'x')
        px.set_value(myokit.Number(1.2))
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s1.set_initial_value(myokit.Number(2), in_amount=True)
        s2 = m.add_species(c, 's2')
        s2.set_initial_value(myokit.Number(1.5))
        s2.set_conversion_factor(px)
        r = m.add_reaction('r')
        r.add_reactant(s1)
        r.add_product(s2)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))

        self.assertRaisesRegex(sbml.SBMLError, 'Species <', m.myokit_model)

    def test_reaction_boundary_species(self):
        # Tests whether rate of boundary species remains unaltered.

        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s1.set_initial_value(myokit.Number(2), in_amount=True)
        s2 = m.add_species(compartment=c, sid='s2', is_boundary=True)
        s2.set_initial_value(myokit.Number(2), in_amount=True)
        s3 = m.add_species(compartment=c, sid='s3', is_boundary=True)
        s3.set_initial_value(myokit.Number(1.5), in_amount=False)
        r = m.add_reaction('r')
        r.add_reactant(s1)
        r.add_reactant(s2)
        r.add_product(s3)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s3)))
        mm = m.myokit_model()

        # Check that species are state variables
        var = mm.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = mm.get('c.s2_amount')
        self.assertFalse(var.is_state())

        var = mm.get('c.s3_amount')
        self.assertFalse(var.is_state())

        # Check rhs
        var = mm.get('c.s1_amount')
        self.assertEqual(
            var.rhs().code(), '-(c.s1_concentration + c.s3_concentration)')
        self.assertEqual(var.eval(), -(2 / 1.2 + 1.5))

        var = mm.get('c.s2_amount')
        self.assertEqual(var.eval(), 2)

        var = mm.get('c.s3_amount')
        self.assertEqual(var.eval(), 1.2 * 1.5)

    def test_reaction_conversion_factor(self):
        # Tests whether rate contributions are converted correctly.

        m = sbml.Model()
        px = m.add_parameter('x')
        px.set_value(myokit.Number(1.2))
        py = m.add_parameter('y')
        py.set_value(myokit.Number(3))
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s1.set_initial_value(myokit.Number(2), in_amount=True)
        s1.set_conversion_factor(px)
        s2 = m.add_species(c, 's2')
        s2.set_initial_value(myokit.Number(1.5))
        s2.set_conversion_factor(py)
        r = m.add_reaction('r')
        r.add_reactant(s1)
        r.add_product(s2)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))
        mm = m.myokit_model()

        # Check that species are state variables
        var = mm.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = mm.get('c.s2_amount')
        self.assertTrue(var.is_state())

        # Check rates
        var = mm.get('c.s1_amount')
        self.assertEqual(var.eval(), -1.2 * (2 / 1.2 + 1.5))

        var = mm.get('c.s2_amount')
        self.assertEqual(var.eval(), 3 * (2 / 1.2 + 1.5))

    def test_reaction_stoichiometry(self):
        # Tests whether stoichiometry is used in reactions correctly.

        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s1.set_initial_value(myokit.Number(2), in_amount=True)
        s2 = m.add_species(c, 's2')
        s2.set_initial_value(myokit.Number(1.5))
        r = m.add_reaction('r')
        sr1 = r.add_reactant(s1)
        sr1.set_initial_value(myokit.Number(3))
        sr2 = r.add_product(s2)
        sr2.set_initial_value(myokit.Number(2))
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))
        mm = m.myokit_model()

        # Check that species are state variables
        var = mm.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = mm.get('c.s2_amount')
        self.assertTrue(var.is_state())

        # Check rates
        var = mm.get('c.s1_amount')
        self.assertEqual(var.eval(), -3 * (2 / 1.2 + 1.5))

        var = mm.get('c.s2_amount')
        self.assertEqual(var.eval(), 2 * (2 / 1.2 + 1.5))

    def test_reaction_stoichiometry_parameter(self):
        # Tests whether stoichiometry is used in reactions correctly,
        # when it's set by a parameter.

        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s1.set_initial_value(myokit.Number(2), in_amount=True)
        s2 = m.add_species(c, 's2')
        s2.set_initial_value(myokit.Number(1.5))
        r = m.add_reaction('r')
        sr1 = r.add_reactant(s1, 'sr1')
        sr1.set_initial_value(myokit.Number(3))
        sr1.set_value(myokit.Number(5))
        sr2 = r.add_product(s2, 'sr2')
        sr2.set_value(value=myokit.Number(3.82), is_rate=True)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))
        with WarningCollector():
            mm = m.myokit_model()

        # Check that species are state variables
        var = mm.get('c.s1_amount')
        self.assertTrue(var.is_state())

        var = mm.get('c.s2_amount')
        self.assertTrue(var.is_state())

        # Check whether stoichiometries are state variables
        var = mm.get('c.sr1')
        self.assertFalse(var.is_state())

        var = mm.get('c.sr2')
        self.assertTrue(var.is_state())

        # Check rates of species
        var = mm.get('c.s1_amount')
        self.assertEqual(var.eval(), -5 * (2 / 1.2 + 1.5))

        var = mm.get('c.s2_amount')
        self.assertEqual(var.eval(), 0 * (2 / 1.2 + 1.5))

        # Check values for stoichiometries
        var = mm.get('c.sr1')
        self.assertEqual(var.eval(), 5)

        var = mm.get('c.sr2')
        self.assertEqual(var.state_value(), 0)
        self.assertEqual(var.eval(), 3.82)

    def test_reaction_stoichiometries_exist(self):
        # Tests whether stoichiometries are created properly.

        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s1.set_initial_value(myokit.Number(2), in_amount=True)
        s2 = m.add_species(c, 's2')
        s2.set_initial_value(myokit.Number(1.5))
        r = m.add_reaction('r')
        r.add_reactant(s1, 'sr1')
        r.add_product(s2, 'sr2')
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))
        mm = m.myokit_model()

        # Check that stoichiometry variables exists
        self.assertTrue(mm.has_variable('c.sr1'))
        self.assertTrue(mm.has_variable('c.sr2'))

    def test_reaction_stoichiometries_initial_value(self):
        # Tests whether initial values of stoichiometries are set properly.

        m = sbml.Model()
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s2 = m.add_species(c, 's2')
        r = m.add_reaction('r')
        sr1 = r.add_reactant(s1, 'sr1')
        sr1.set_initial_value(myokit.Number(2.1))
        sr2 = r.add_product(s2, 'sr2')
        sr2.set_initial_value(myokit.Number(3.5))
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))
        with WarningCollector():
            mm = m.myokit_model()

        # Check that initial values are set properly
        stoich_reactant = mm.get('c.sr1')
        stoich_product = mm.get('c.sr2')

        self.assertEqual(stoich_reactant.eval(), 2.1)
        self.assertEqual(stoich_product.eval(), 3.5)

        # Bad initial value
        m = sbml.Model()
        p = sbml.Parameter(m, 'parameter')
        c = m.add_compartment('c')
        s1 = m.add_species(c, 's1')
        r = m.add_reaction('r')
        sr1 = r.add_reactant(s1, 'sr1')
        sr1.set_initial_value(myokit.Name(p))
        r.set_kinetic_law(myokit.Name(s1))
        self.assertRaisesRegex(
            sbml.SBMLError, 'Initial value of <', m.myokit_model)

    def test_reaction_stoichiometry_values(self):
        # Tests whether values of parameters are set correctly.

        m = sbml.Model()
        p = m.add_parameter('V')
        p.set_value(myokit.Number(10.23))
        c = m.add_compartment('c')
        c.set_initial_value(myokit.Number(1.2))
        s1 = m.add_species(c, 's1')
        s2 = m.add_species(c, 's2')
        r = m.add_reaction('r')
        sr1 = r.add_reactant(s1, 'sr1')
        sr1.set_initial_value(myokit.Number(2.1))
        sr1.set_value(myokit.Plus(myokit.Name(p), myokit.Number(5)))
        sr2 = r.add_product(s2, 'sr2')
        sr2.set_initial_value(myokit.Number(3.5))
        sr2.set_value(
            myokit.Minus(myokit.Name(p), myokit.Number(1)), True)
        r.set_kinetic_law(myokit.Plus(myokit.Name(s1), myokit.Name(s2)))
        with WarningCollector():
            mm = m.myokit_model()

        # Check that stoichiometries are state/ not state variables
        var = mm.get('c.sr1')
        self.assertFalse(var.is_state())

        var = mm.get('c.sr2')
        self.assertTrue(var.is_state())

        # Check value of stoichiometries
        var = mm.get('c.sr1')
        self.assertEqual(var.eval(), 15.23)

        var = mm.get('c.sr2')
        self.assertEqual(var.state_value(), 3.5)
        self.assertEqual(var.eval(), 9.23)

        # Bad value
        m = sbml.Model()
        p = sbml.Parameter(m, 'parameter')
        c = m.add_compartment('c')
        s1 = m.add_species(c, 's1')
        r = m.add_reaction('r')
        sr1 = r.add_reactant(s1, 'sr1')
        sr1.set_value(myokit.Name(p))
        r.set_kinetic_law(myokit.Name(s1))
        self.assertRaisesRegex(
            sbml.SBMLError, 'Value of <', m.myokit_model)

    def test_reaction_stoichiometries(self):
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

        X.add_compartments(
            m, myokit_model, component_references, variable_references,
            expression_references)

        sid = 'species'
        s = m.add_species(c, sid)

        X.add_species(
            m, component_references, species_amount_references,
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
        X.add_stoichiometries(
            m, component_references, variable_references,
            expression_references)

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
        X.add_stoichiometries(
            m, component_references, variable_references,
            expression_references)

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

    def test_time_variable_is_created(self):
        # Tests whether time variable is created.

        m = sbml.Model()
        m.set_time_units(myokit.units.ampere)
        m = m.myokit_model()

        # Check that time variable exists
        self.assertTrue(m.has_variable('myokit.time'))

        # Check that unit is set
        var = m.get('myokit.time')
        self.assertEqual(var.unit(), myokit.units.ampere)

        # Check that initial value is set
        self.assertEqual(var.rhs(), myokit.Number(0, myokit.units.ampere))

        # Chet that variable is time bound
        self.assertTrue(var.binding(), 'time')

    def test_time_variable_is_usable(self):
        # Tests that time variable can be used in equations

        # Create SBML model
        s = sbml.Model()
        s.set_time_units(myokit.units.ms)
        p = s.add_parameter('param')
        p.set_value(myokit.Plus(myokit.Number(1), myokit.Name(s.time())))
        m = s.myokit_model()
        t = m.get('myokit.time')
        self.assertEqual(t.unit(), myokit.units.ms)
        self.assertEqual(
            m.get('myokit.param').rhs(),
            myokit.Plus(myokit.Number(1), myokit.Name(m.time())))


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
