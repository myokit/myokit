#!/usr/bin/env python3
#
# Tests Myokit's SBML support.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit
import myokit.formats

import myokit.formats.sbml
from myokit.formats.sbml._api import Model
from myokit.formats.sbml._writer import write_string
import myokit.formats.sbml as sbml


class TestSBMLExport(unittest.TestCase):
    """
    Unit tests for the SBML export functionality.
    """

    def test_empty_model(self):
        # Test exporting an empty model
        model = Model()
        sbml_str = write_string(model).decode("utf8")
        self.assertIn("<sbml", sbml_str)
        self.assertIn("</sbml>", sbml_str)
        self.assertIn('<model id="unnamed_model"/>', sbml_str)

    def test_time_unit(self):
        # Test setting the time unit
        model = Model()
        model.set_time_units(myokit.units.second)
        sbml_str = write_string(model).decode("utf8")
        self.assertIn('timeUnits="second"', sbml_str)

    def test_area_unit(self):
        # Test setting the area unit
        model = Model()
        model.set_area_units(myokit.units.metre)
        sbml_str = write_string(model).decode("utf8")
        self.assertIn('areaUnits="metre"', sbml_str)

    def test_volume_unit(self):
        # Test setting the volume unit
        model = Model()
        model.set_volume_units(myokit.units.litre)
        sbml_str = write_string(model).decode("utf8")
        self.assertIn('volumeUnits="litre"', sbml_str)

    def test_substance_unit(self):
        # Test setting the substance unit
        model = Model()
        model.set_substance_units(myokit.units.mole)
        sbml_str = write_string(model).decode("utf8")
        self.assertIn('substanceUnits="mole"', sbml_str)

    def test_extent_unit(self):
        # Test setting the extent unit
        model = Model()
        model.set_extent_units(myokit.units.mole)
        sbml_str = write_string(model).decode("utf8")
        self.assertIn('extentUnits="mole"', sbml_str)

    def test_list_of_unit_definitions(self):
        # Test setting a list of unit definitions
        model = Model()
        model.add_unit("my_unit", myokit.units.ampere)
        model.add_unit("my_unit2", 2 * myokit.units.dimensionless)
        sbml_str = write_string(model).decode("utf8")
        self.assertIn("<listOfUnitDefinitions>", sbml_str)
        self.assertIn('<unitDefinition id="my_unit">', sbml_str)
        self.assertIn(
            '<unit kind="ampere" exponent="1.0" multiplier="1.0"/>',
            sbml_str
        )
        self.assertIn('<unitDefinition id="my_unit2">', sbml_str)
        self.assertIn(
            '<unit kind="dimensionless" multiplier="2.0"/>',
            sbml_str
        )

    def test_list_of_compartments(self):
        # Test setting a list of compartments
        model = Model()
        c = model.add_compartment("my_compartment")
        c.set_size_units(myokit.units.litre)
        c.set_spatial_dimensions(3)
        model.add_compartment("my_compartment2")
        sbml_str = write_string(model).decode("utf8")
        self.assertIn("<listOfCompartments>", sbml_str)
        self.assertIn(
            '<compartment id="my_compartment" units="litre" spatialDimensions="3.0"/>',  # noqa: E501
            sbml_str
        )
        self.assertIn('<compartment id="my_compartment2"/>', sbml_str)

    def test_list_of_parameters(self):
        # Test setting a list of parameters
        model = Model()
        p = model.add_parameter("my_parameter")
        p.set_value(myokit.Number(1))
        p = model.add_parameter("my_parameter2")
        p.set_units(1e3 * myokit.units.metre / myokit.units.second)
        p.set_value(myokit.Number(2))
        sbml_str = write_string(model).decode("utf8")
        self.assertIn("<listOfParameters>", sbml_str)
        self.assertIn(
            '<parameter id="my_parameter" constant="true" value="1.0"/>',
            sbml_str
        )
        self.assertIn(
            '<parameter id="my_parameter2" units="m_per_s_times_1e3" constant="true" value="2.0"/>',  # noqa: E501
            sbml_str
        )
        self.assertNotIn("<listOfRules>", sbml_str)
        self.assertNotIn("<listOfInitialAssignments>", sbml_str)

        model = Model()
        p = model.add_parameter("my_parameter", is_constant=False)
        p.set_initial_value(myokit.Number(1))
        p.set_value(myokit.Number(2))
        sbml_str = write_string(model).decode("utf8")
        self.assertIn("<listOfRules>", sbml_str)
        self.assertIn('<assignmentRule variable="my_parameter">', sbml_str)
        self.assertIn("<cn>2.0</cn>", sbml_str)
        self.assertIn("<listOfInitialAssignments>", sbml_str)
        self.assertIn('<initialAssignment symbol="my_parameter">', sbml_str)
        self.assertIn("<cn>1.0</cn>", sbml_str)

    def test_list_of_species(self):
        # Test setting a list of species
        model = Model()
        c = model.add_compartment("my_compartment")
        s = model.add_species(c, "my_species")
        s.set_substance_units(myokit.units.mole / myokit.units.litre)
        s.set_value(myokit.Number(1), True)
        s.set_initial_value(myokit.Number(2))
        s = model.add_species(c, "my_species2")
        s.set_substance_units(myokit.units.mole)
        s.set_value(myokit.Number(1), True)
        s.set_initial_value(myokit.Number(2), in_amount=True)
        sbml_str = write_string(model).decode("utf8")
        self.assertIn("<listOfSpecies>", sbml_str)
        self.assertIn(
            '<species id="my_species" compartment="my_compartment" initialConcentration="2.0" constant="False" units="M" boundaryCondition="False"/>',  # noqa: E501
            sbml_str,
        )
        self.assertIn(
            '<species id="my_species2" compartment="my_compartment" initialAmount="2.0" constant="False" units="mole" boundaryCondition="False"/>',  # noqa: E501
            sbml_str,
        )
        self.assertIn("<listOfRules>", sbml_str)
        self.assertIn('<rateRule variable="my_species">', sbml_str)
        self.assertIn("<cn>1.0</cn>", sbml_str)

    def test_list_of_reactions(self):
        # test kinetic law
        model = Model()
        c = model.add_compartment("my_compartment")
        s = model.add_species(c, "my_species")
        r = model.add_reaction("my_reaction")
        r.add_reactant(s)
        r.add_product(s)
        r.add_modifier(s)
        r.set_kinetic_law(myokit.Number(1))
        sbml_str = write_string(model).decode("utf8")
        self.assertIn("<listOfReactions>", sbml_str)
        self.assertIn('<reaction id="my_reaction">', sbml_str)
        self.assertIn("<listOfReactants>", sbml_str)
        self.assertIn("<listOfProducts>", sbml_str)
        self.assertIn('<speciesReference species="my_species"/>', sbml_str)
        self.assertIn("<listOfModifiers>", sbml_str)
        self.assertIn(
            '<modifierSpeciesReference species="my_species"/>',
            sbml_str
        )
        self.assertIn("<kineticLaw>", sbml_str)
        self.assertIn("<cn>1.0</cn>", sbml_str)

        # test stochoimetry
        model = Model()
        c = model.add_compartment("my_compartment")
        s = model.add_species(c, "my_species")
        r = model.add_reaction("my_reaction")
        react = r.add_reactant(s)
        react.set_value(myokit.Number(1))
        r.add_product(s)
        sbml_str = write_string(model).decode("utf8")
        self.assertIn(
            '<speciesReference species="my_species" stoichiometry="1.0"/>',
            sbml_str
        )

    def test_expressions_multiple_compartments(self):
        m = myokit.Model()
        c = m.add_component('comp')
        t = c.add_variable('time', rhs=myokit.Number(0))
        t.set_unit(myokit.units.second)
        t.set_binding('time')
        c2 = m.add_component('comp2')
        v = c.add_variable('var', initial_value=3)
        v.set_rhs(myokit.Name(t))
        v2 = c2.add_variable('var', initial_value=3)
        v2.set_rhs(myokit.Name(v))

        # check that the equation is exported correctly to sbml.Model
        s = sbml.Model.from_myokit_model(m)
        parameter_names = [v.sid() for v in s.parameters()]
        self.assertCountEqual(parameter_names, ['comp_var', 'comp2_var'])
        v2_sbml = s.parameter('comp2_var')
        self.assertEqual(
            v2_sbml.value(),
            myokit.Name(v)
        )

        # check that the equation is exported correctly to sbml string
        sbml_str = write_string(s).decode("utf8")
        self.assertIn('<rateRule variable="comp2_var">', sbml_str)
        self.assertIn('<ci>comp_var</ci>', sbml_str)
        self.assertIn('<rateRule variable="comp_var">', sbml_str)
        self.assertIn(
            '<ci>http://www.sbml.org/sbml/symbols/time</ci>',
            sbml_str
        )

