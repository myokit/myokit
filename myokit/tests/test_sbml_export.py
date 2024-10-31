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


class TestSBMLExport(unittest.TestCase):
    """
    Unit tests for the SBML export functionality.
    """

    def test_empty_model(self):
        # Test exporting an empty model
        model = Model()
        sbml_str = model.to_xml_str().decode("utf8")
        self.assertIn("<sbml", sbml_str)
        self.assertIn("</sbml>", sbml_str)
        self.assertIn('<model id="unnamed_model"/>', sbml_str)

    def test_time_unit(self):
        # Test setting the time unit
        model = Model()
        model.set_time_units(myokit.units.second)
        sbml_str = model.to_xml_str().decode("utf8")
        self.assertIn('timeUnits="second"', sbml_str)

    def test_area_unit(self):
        # Test setting the area unit
        model = Model()
        model.set_area_units(myokit.units.metre)
        sbml_str = model.to_xml_str().decode("utf8")
        self.assertIn('areaUnits="metre"', sbml_str)

    def test_volume_unit(self):
        # Test setting the volume unit
        model = Model()
        model.set_volume_units(myokit.units.litre)
        sbml_str = model.to_xml_str().decode("utf8")
        self.assertIn('volumeUnits="litre"', sbml_str)

    def test_substance_unit(self):
        # Test setting the substance unit
        model = Model()
        model.set_substance_units(myokit.units.mole)
        sbml_str = model.to_xml_str().decode("utf8")
        self.assertIn('substanceUnits="mole"', sbml_str)

    def test_extent_unit(self):
        # Test setting the extent unit
        model = Model()
        model.set_extent_units(myokit.units.mole)
        sbml_str = model.to_xml_str().decode("utf8")
        self.assertIn('extentUnits="mole"', sbml_str)

    def test_list_of_unit_definitions(self):
        # Test setting a list of unit definitions
        model = Model()
        model.add_unit("my_unit", myokit.units.ampere)
        sbml_str = model.to_xml_str().decode("utf8")
        self.assertIn("<listOfUnitDefinitions>", sbml_str)
        self.assertIn('<unitDefinition id="my_unit">', sbml_str)
        self.assertIn(
            '<unit kind="ampere" exponent="1.0" multiplier="1.0"/>',
            sbml_str
        )

    def test_list_of_compartments(self):
        # Test setting a list of compartments
        model = Model()
        model.add_compartment("my_compartment")
        sbml_str = model.to_xml_str().decode("utf8")
        print(sbml_str)
        self.assertIn("<listOfCompartments>", sbml_str)
        self.assertIn('<compartment id="my_compartment"/>', sbml_str)

    def test_list_of_parameters(self):
        # Test setting a list of parameters
        model = Model()
        model.add_parameter("my_parameter")
        sbml_str = model.to_xml_str().decode("utf8")
        self.assertIn("<listOfParameters>", sbml_str)
        self.assertIn('<parameter id="my_parameter"/>', sbml_str)

    def test_list_of_species(self):
        # Test setting a list of species
        model = Model()
        c = model.add_compartment("my_compartment")
        s = model.add_species(c, "my_species")
        s.set_substance_units(myokit.units.mole)
        s.set_value(myokit.Number(1), True)
        sbml_str = model.to_xml_str().decode("utf8")
        self.assertIn("<listOfSpecies>", sbml_str)
        self.assertIn(
            '<species id="my_species" compartment="my_compartment" constant="False" units="mole" boundaryCondition="False"/>',  # noqa: E501
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
        sbml_str = model.to_xml_str().decode("utf8")
        print(sbml_str)
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
        sbml_str = model.to_xml_str().decode("utf8")
        print(sbml_str)
        self.assertIn(
            '<speciesReference species="my_species" stoichiometry="1.0"/>',
            sbml_str
        )
