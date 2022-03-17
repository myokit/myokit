#!/usr/bin/env python3
#
# Tests Myokit's SBML support.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.formats
import myokit.formats.sbml
from myokit.formats.sbml import SBMLParser, SBMLParsingError

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


class TestSBMLParser(unittest.TestCase):
    """
    Unit tests for the SBMLParser class.
    """

    @classmethod
    def setUpClass(cls):
        cls.p = SBMLParser()

    def assertBad(self, xml, message, lvl=3, v=2):
        """
        Inserts the given ``xml`` into a <model> element, parses it, and checks
        that this raises an exception matching ``message``.
        """
        self.assertRaisesRegex(
            SBMLParsingError, message, self.parse, xml, lvl, v)

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

    def test_duplicate_sids(self):
        # Checks that an error is thrown when an SId is used twice.
        # Nearly every object can have an SId, but Myokit only checks:
        #  compartments, species, species references, reactions, parameters
        # Units do not have SIds, but their own UnitSIds.

        # Coinciding compartment and parameter ids
        xml = (
            '<model id="test" '
            'timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="someId"/>'
            '</listOfCompartments>'
            '<listOfParameters>'
            '<parameter id="someId"/>'
            '</listOfParameters>'
            '</model>')
        self.assertBad(xml, 'Unable to parse compartment "')

        # Coinciding compartment and species ids
        xml = (
            '<model id="test" '
            'timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="someId"/>'
            '</listOfCompartments>'
            '<listOfSpecies>'
            '<species id="someId" hasOnlySubstanceUnits="true"'
            ' compartment="someId" constant="false"'
            ' boundaryCondition="true" />'
            '</listOfSpecies>'
            '</model>')
        self.assertBad(xml, 'Unable to parse ')

        # Coinciding parameter and species ids
        xml = (
            '<model id="test" '
            'timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="someComp"/>'
            '</listOfCompartments>'
            '<listOfParameters>'
            '<parameter id="someId"/>'
            '</listOfParameters>'
            '<listOfSpecies>'
            '<species id="someId" hasOnlySubstanceUnits="true"'
            ' compartment="someComp" constant="false"'
            ' boundaryCondition="true" />'
            '</listOfSpecies>'
            '</model>')
        self.assertBad(xml, 'Unable to parse ')

        # Coinciding parameter and reactant stoichiometry IDs
        stoich_id = 'someStoich'
        xml = (
            '<model id="test" name="test" timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="someComp"/>'
            '</listOfCompartments>'
            '<listOfParameters>'
            '<parameter id="' + stoich_id + '"/>'
            '</listOfParameters>'
            '<listOfSpecies>'
            '<species id="someSpecies" hasOnlySubstanceUnits="true" '
            'compartment="someComp" constant="false" boundaryCondition="false"'
            '/>'
            '</listOfSpecies>'
            '<listOfReactions>'
            '<reaction id="reaction">'
            '<listOfReactants>'
            '<speciesReference species="someSpecies" '
            'id="' + stoich_id + '"/>'
            '</listOfReactants>'
            '</reaction>'
            '</listOfReactions>'
            '</model>')
        self.assertBad(xml=xml, message='Unable to parse ')

        # Coinciding parameter and product stoichiometry IDs
        stoich_id = 'someStoich'
        xml = (
            '<model id="test" name="test" timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="someComp"/>'
            '</listOfCompartments>'
            '<listOfParameters>'
            '<parameter id="' + stoich_id + '"/>'
            '</listOfParameters>'
            '<listOfSpecies>'
            '<species id="someSpecies" hasOnlySubstanceUnits="true" '
            'compartment="someComp" constant="false" boundaryCondition="false"'
            '/>'
            '</listOfSpecies>'
            '<listOfReactions>'
            '<reaction id="reaction">'
            '<listOfProducts>'
            '<speciesReference species="someSpecies" '
            'id="' + stoich_id + '"/>'
            '</listOfProducts>'
            '</reaction>'
            '</listOfReactions>'
            '</model>')
        self.assertBad(xml=xml, message='Unable to parse ')

    def test_parse_algebraic_rule(self):
        # Tests parsing algebraic rules (not supported)
        xml = (
            '<model>'
            ' <listOfRules>'
            '  <algebraicRule>'
            '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
            '    <apply>'
            '    </apply>'
            '   </math>'
            '  </algebraicRule>'
            ' </listOfRules>'
            '</model>'
        )
        self.assertBad(xml, 'Algebraic rules are not supported')

    def test_parse_compartment(self):
        # Test parsing compartments

        a = '<model><listOfCompartments>'
        b = '</listOfCompartments></model>'

        # Test simple compartment
        x = '<compartment id="a" />'
        m = self.parse(a + x + b)
        c = m.compartment('a')
        self.assertEqual(m.compartment('a').sid(), 'a')

        # Missing id
        x = '<compartment/>'
        self.assertBad(a + x + b, 'required attribute "id"')

        # Invalid id
        x = '<compartment id="123" />'
        self.assertBad(a + x + b, 'Invalid SId')

        # Spatial dimensions and model default units
        x = (
            '<model lengthUnits="volt" areaUnits="gram" volumeUnits="lux">'
            ' <listOfCompartments>'
            '  <compartment id="c" />'
            '  <compartment id="s1" spatialDimensions="1" />'
            '  <compartment id="s2" spatialDimensions="2" />'
            '  <compartment id="s3" spatialDimensions="3" />'
            '  <compartment id="d" spatialDimensions="1.4" units="henry" />'
            ' </listOfCompartments>'
            '</model>')
        m = self.parse(x)
        c = m.compartment('c')
        self.assertEqual(c.spatial_dimensions(), None)
        self.assertEqual(c.size_units(), myokit.units.dimensionless)
        c = m.compartment('s1')
        self.assertEqual(c.spatial_dimensions(), 1)
        self.assertEqual(c.size_units(), myokit.units.volt)
        c = m.compartment('s2')
        self.assertEqual(c.spatial_dimensions(), 2)
        self.assertEqual(c.size_units(), myokit.units.g)
        c = m.compartment('s3')
        self.assertEqual(c.spatial_dimensions(), 3)
        self.assertEqual(c.size_units(), myokit.units.lux)
        c = m.compartment('d')
        self.assertEqual(c.spatial_dimensions(), 1.4)
        self.assertEqual(c.size_units(), myokit.units.henry)

        # Unknown units
        x = '<compartment id="x" units="made-up" />'
        self.assertBad(a + x + b, 'Unknown units')

        # Spatial dimensions that cannot be converted to float
        x = '<compartment id="x" spatialDimensions="made-up" />'
        self.assertBad(a + x + b, 'Unable to convert spatial dimensions value')

        # Size that cannot be converted to float
        x = '<compartment id="x" size="made-up" />'
        self.assertBad(a + x + b, 'Unable to convert size')

        # Initial value for size
        x = '<compartment id="x" size="1.32" />'
        m = self.parse(a + x + b)
        c = m.compartment('x')
        self.assertEqual(c.initial_value(), myokit.Number(1.32))

    def test_parse_constraint(self):
        # Test parsing constraints (these are ignored)

        xml = (
            '<model>'
            ' <listOfConstraints>'
            '  <constraint>'
            '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
            '    <apply> <lt/> <cn> 1 </cn> <ci> S1 </ci> </apply>'
            '   </math>'
            '   <message>'
            '     <p xmlns="http://www.w3.org/1999/xhtml">Out of range.</p>'
            '   </message>'
            '  </constraint>'
            ' </listOfConstraints>'
            '</model>')

        with WarningCollector() as w:
            self.p.parse_string(self.wrap(xml))
        self.assertIn('Ignoring SBML constraints', w.text())

    def test_parse_csymbol_time(self):
        # Test parsing of the csymbol "time"
        xml = (
            '<model timeUnits="second">'
            ' <listOfParameters>'
            '  <parameter id="bacterial_count" value="1" constant="false"/>'
            ' </listOfParameters>'
            ' <listOfRules>'
            '  <assignmentRule variable="bacterial_count">'
            '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
            '    <apply>'
            '     <times/>'
            '     <ci>bacterial_count</ci>'
            ' <csymbol definitionURL="http://www.sbml.org/sbml/symbols/time"/>'
            '    </apply>'
            '   </math>'
            '  </assignmentRule>'
            ' </listOfRules>'
            '</model>')

        self.p.parse_string(self.wrap(xml))

    def test_parse_events(self):
        # Test parsing events (these are ignored)

        xml = (
            '<model>'
            ' <listOfEvents>'
            '  <event useValuesFromTriggerTime="true">'
            '   <trigger initialValue="false" persistent="true">'
            '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
            '     <apply> <leq/> <ci> P_1 </ci> <ci> P_2 </ci> </apply>'
            '    </math>'
            '   </trigger>'
            '   <listOfEventAssignments>'
            '    <eventAssignment variable="k2">'
            '     <math xmlns="http://www.w3.org/1998/Math/MathML">'
            '      <ci> k2reset </ci>'
            '     </math>'
            '    </eventAssignment>'
            '   </listOfEventAssignments>'
            '  </event>'
            ' </listOfEvents>'
            '</model>')

        with WarningCollector() as w:
            self.p.parse_string(self.wrap(xml))
        self.assertIn('Ignoring SBML events', w.text())

    def test_parse_file(self):
        # Tests parse_file()

        # Supported level
        xml = self.wrap('<model id="a" name="a"/>', 3, 2)
        with WarningCollector() as w:
            self.p.parse_string(xml)
        self.assertNotIn('This version of SBML may not be supported', w.text())

        # Unsupported level
        xml = self.wrap('<model id="a" name="a"/>', 2, 2)
        with WarningCollector() as w:
            self.p.parse_string(xml)
        self.assertIn('This version of SBML may not be supported', w.text())

        # Unsupported version
        xml = self.wrap('<model id="a" name="a"/>', 3, 1)
        with WarningCollector() as w:
            self.p.parse_string(xml)
        self.assertIn('This version of SBML may not be supported', w.text())

        # Check whether error is thrown for invalid path
        path = 'some/path'
        message = 'Unable to parse XML: '
        self.assertRaisesRegex(
            SBMLParsingError,
            message,
            self.p.parse_file,
            path)

        # Check whether error is thrown for invalid xml
        self.assertBad('<model>', 'Unable to parse XML: ')

    def test_function_definitions(self):
        # Function definitions are not supported

        xml = (
            '<model id="test" name="test" timeUnits="second"> '
            ' <listOfFunctionDefinitions>'
            '  <functionDefinition id="multiply" name="multiply">'
            '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
            '    <lambda>'
            '     <bvar>'
            '      <ci> x </ci>'
            '     </bvar>'
            '     <bvar>'
            '      <ci> y </ci>'
            '     </bvar>'
            '     <apply>'
            '      <times/>'
            '       <ci> x </ci>'
            '       <ci> y </ci>'
            '     </apply>'
            '    </lambda>'
            '   </math>'
            '  </functionDefinition>'
            ' </listOfFunctionDefinitions>'
            '</model>')
        self.assertBad(xml, 'Function definitions are not supported.')

    def test_parse_initial_assignment(self):
        # Test parsing initial assignments.

        # Set a parameter value
        a = ('<model name="mathml">'
             ' <listOfParameters>'
             '  <parameter id="x" constant="true" />'
             ' </listOfParameters>'
             ' <listOfInitialAssignments>')
        b = ('  <initialAssignment symbol="x">'
             '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <cn>5</cn>'
             '   </math>'
             '  </initialAssignment>')
        c = (' </listOfInitialAssignments>'
             '</model>')
        p = self.parse(a + b + c).parameter('x')
        self.assertEqual(p.initial_value(), myokit.Number(5))

        # Reset a parameter value
        x = ('<model name="mathml">'
             ' <listOfParameters>'
             '  <parameter id="x" value="3" constant="true" />'
             ' </listOfParameters>'
             ' <listOfInitialAssignments>')
        p = self.parse(x + c).parameter('x')
        self.assertEqual(p.initial_value(), myokit.Number(3))
        p = self.parse(x + b + c).parameter('x')
        self.assertEqual(p.initial_value(), myokit.Number(5))

        # No maths: warning
        y = '<initialAssignment symbol="x"></initialAssignment>'
        with WarningCollector() as w:
            p = self.parse(x + y + c).parameter('x')
        self.assertIn('nitial assignment does not define any math', w.text())
        self.assertEqual(p.initial_value(), myokit.Number(3))

        # Invalid maths: error
        x = ('  <initialAssignment symbol="x">'
             '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply><power /><cn>1</cn></apply>'
             '   </math>'
             '  </initialAssignment>')
        self.assertBad(a + x + c, r'Expecting 2 operand\(s\), got 1 for power')

        # Missing symbol: error
        x = '<initialAssignment />'
        self.assertBad(a + x + c, 'required attribute "symbol"')

        # Invalid/unknown symbol
        x = ('  <initialAssignment symbol="blue">'
             '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <cn>5</cn>'
             '   </math>'
             '  </initialAssignment>')
        self.assertBad(a + x + c, 'SId "blue" does not refer to')

        # Set a compartment size
        a = ('<model name="mathml">')
        b = (' <listOfCompartments>'
             '  <compartment id="c" />'
             ' </listOfCompartments>')
        c = (' <listOfInitialAssignments>'
             '  <initialAssignment symbol="c">'
             '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <cn>1.23</cn>'
             '   </math>'
             '  </initialAssignment>'
             ' </listOfInitialAssignments>')
        d = ('</model>')
        m = self.parse(a + b + c + d)
        self.assertEqual(
            m.compartment('c').initial_value(), myokit.Number((1.23)))

        # Reset a compartment size
        b = ('<listOfCompartments>'
             '<compartment id="c" size="12" />'
             '</listOfCompartments>')
        m = self.parse(a + b + d)
        self.assertEqual(
            m.compartment('c').initial_value(), myokit.Number((12)))
        m = self.parse(a + b + c + d)
        self.assertEqual(
            m.compartment('c').initial_value(), myokit.Number((1.23)))

        # Set a species amount (or concentration)
        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>')
        b = (' <listOfSpecies>'
             '  <species id="s" compartment="c" />'
             ' </listOfSpecies>')
        c = (' <listOfInitialAssignments>'
             '  <initialAssignment symbol="s">'
             '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <cn>4.5</cn>'
             '   </math>'
             '  </initialAssignment>'
             ' </listOfInitialAssignments>')
        d = ('</model>')
        m = self.parse(a + b + c + d)
        s = m.species('s')
        expr, expr_in_amount = s.initial_value()
        self.assertEqual(expr, myokit.Number(4.5))
        self.assertIsNone(expr_in_amount)

        # Reset a species amount (or concentration)
        b = (' <listOfSpecies>'
             '  <species id="s" compartment="c" initialConcentration="3" />'
             ' </listOfSpecies>')
        m = self.parse(a + b + d)
        s = m.species('s')
        expr, expr_in_amount = s.initial_value()
        self.assertEqual(expr, myokit.Number(3))
        self.assertFalse(expr_in_amount)
        m = self.parse(a + b + c + d)
        s = m.species('s')
        expr, expr_in_amount = s.initial_value()
        self.assertEqual(expr, myokit.Number(4.5))
        self.assertIsNone(expr_in_amount)

        # Set a stoichiometry
        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="s" compartment="c" />'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>')
        b = ('    <speciesReference species="s" id="sr" />')
        c = ('   </listOfReactants>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply><ci>s</ci></apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>'
             ' </listOfReactions>')
        d = (' <listOfInitialAssignments>'
             '  <initialAssignment symbol="sr">'
             '   <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <cn>4.51</cn>'
             '   </math>'
             '  </initialAssignment>'
             ' </listOfInitialAssignments>')
        e = ('</model>')
        sr = self.parse(a + b + c + d + e).reaction('r').reactants()[0]
        self.assertEqual(sr.initial_value(), myokit.Number(4.51))

        # Reset a stoichiometry
        b = '<speciesReference species="s" id="sr" stoichiometry="2" />'
        sr = self.parse(a + b + c + e).reaction('r').reactants()[0]
        self.assertEqual(sr.initial_value(), myokit.Number(2))
        sr = self.parse(a + b + c + d + e).reaction('r').reactants()[0]
        self.assertEqual(sr.initial_value(), myokit.Number(4.51))

    def test_parse_model(self):
        # Tests parsing a model.

        # No model
        self.assertBad(xml='', message='Model element not found.')
        self.assertBad(xml='<hello/>', message='Model element not found.')

        # Name from name attribute
        m = self.parse('<model id="yes" name="no" />')
        self.assertEqual(m.name(), 'no')

        # Name from id attribute
        m = self.parse('<model id="yes" />')
        self.assertEqual(m.name(), 'yes')

        # Default name
        m = self.parse('<model />')
        self.assertEqual(m.name(), 'Imported SBML model')

        # Notes
        m = self.parse(
            '<model>'
            ' <notes>'
            '  <body xmlns="http://www.w3.org/1999/xhtml">'
            '   <h1>This is a bunch of notes</h1>'
            '   <div><p>With sentences like this one</p></div>'
            '   <p>And a<br />line break</p>'
            '  </body>'
            ' </notes>'
            '</model>'
        )
        self.assertIn('sentences like this one', m.notes())

        # Global units: length, area, volume, substance, extent, time
        m = self.parse('<model />')
        self.assertEqual(m.length_units(), myokit.units.dimensionless)
        self.assertEqual(m.area_units(), myokit.units.dimensionless)
        self.assertEqual(m.volume_units(), myokit.units.dimensionless)
        self.assertEqual(m.substance_units(), myokit.units.dimensionless)
        self.assertEqual(m.extent_units(), myokit.units.dimensionless)
        self.assertEqual(m.time_units(), myokit.units.dimensionless)

        m = self.parse(
            '<model'
            ' lengthUnits="meter"'
            ' areaUnits="meter_squared"'
            ' volumeUnits="candela"'
            ' substanceUnits="coulomb"'
            ' extentUnits="hertz"'
            ' timeUnits="second"'
            '>'
            ' <listOfUnitDefinitions>'
            '  <unitDefinition id="meter_squared">'
            '   <listOfUnits>'
            '    <unit kind="meter" exponent="2" />'
            '   </listOfUnits>'
            '  </unitDefinition>'
            ' </listOfUnitDefinitions>'
            '</model>'
        )
        self.assertEqual(m.length_units(), myokit.units.m)
        self.assertEqual(m.area_units(), myokit.units.m**2)
        self.assertEqual(m.volume_units(), myokit.units.candela)
        self.assertEqual(m.substance_units(), myokit.units.coulomb)
        self.assertEqual(m.extent_units(), myokit.units.hertz)
        self.assertEqual(m.time_units(), myokit.units.s)

        self.assertBad(
            '<model areaUnits="meter_squared" />',
            'Error parsing model element: ')
        self.assertBad(
            '<model areaUnits="celsius" />',
            'Error parsing model element: ')

        # Global conversion factor
        m = self.parse('<model />')
        self.assertIsNone(m.conversion_factor())
        m = self.parse(
            '<model conversionFactor="x">'
            ' <listOfParameters>'
            '  <parameter id="x" />'
            ' </listOfParameters>'
            '</model>'
        )
        self.assertEqual(m.conversion_factor(), m.parameter('x'))

        self.assertBad(
            '<model conversionFactor="x" />', 'Model conversion factor')

    def test_parse_parameter(self):
        # Tests parsing parameters

        a = '<model><listOfParameters>'
        b = '</listOfParameters></model>'

        # Named
        x = '<parameter id="a" /><parameter id="b" />'
        m = self.parse(a + x + b)
        self.assertEqual(m.parameter('a').sid(), 'a')
        self.assertEqual(m.parameter('b').sid(), 'b')

        # With value and units
        x = ('<parameter id="c" value="2" />'
             '<parameter id="d" units="volt" />'
             '<parameter id="e" units="ampere" value="-1.2e-3" />')
        m = self.parse(a + x + b)
        c = m.parameter('c')
        d = m.parameter('d')
        e = m.parameter('e')
        self.assertEqual(c.sid(), 'c')
        self.assertIsNone(c.units())
        self.assertIsInstance(c.initial_value(), myokit.Number)
        self.assertEqual(c.initial_value().eval(), 2)
        self.assertEqual(d.sid(), 'd')
        self.assertEqual(d.units(), myokit.units.volt)
        self.assertIsNone(d.initial_value())
        self.assertEqual(e.sid(), 'e')
        self.assertEqual(e.units(), myokit.units.ampere)
        self.assertEqual(e.initial_value().eval(), -1.2e-3)
        self.assertIsInstance(e.initial_value(), myokit.Number)

        # Missing id
        x = '<parameter/>'
        self.assertBad(a + x + b, 'required attribute "id"')

        # Invalid id
        x = '<parameter id="123" />'
        self.assertBad(a + x + b, 'Invalid SId')

        # Bad units
        x = '<parameter id="x" units="made-up" />'
        self.assertBad(a + x + b, 'Unknown units')

        # Bad value
        x = '<parameter id="x" value="made-up" />'
        self.assertBad(a + x + b, 'Unable to convert parameter value')

    def test_parse_reaction(self):
        # Test parsing reactions, species references, kinetic laws

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="S1" compartment="c" initialAmount="0"/>'
             '  <species id="S2" compartment="c" initialAmount="0"/>'
             '  <species id="S3" compartment="c" initialAmount="0"/>'
             '  <species id="S4" compartment="c" initialAmount="0"/>'
             ' </listOfSpecies>'
             ' <listOfParameters>'
             '  <parameter id="k1" value="3" />'
             ' </listOfParameters>'
             ' <listOfReactions>')
        b = ('  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="S1" stoichiometry="2" id="r1" />'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="S2" stoichiometry="5" id="r2" />'
             '   </listOfProducts>'
             '   <listOfModifiers>'
             '    <modifierSpeciesReference species="S3" id="r3" />'
             '   </listOfModifiers>')
        c = ('   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <times/>'
             '      <ci> c </ci>'
             '      <ci> k1 </ci>'
             '      <ci> S1 </ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>')
        d = ('  </reaction>')
        e = (' </listOfReactions>'
             '</model>')

        # Parse valid reaction
        m = self.parse(a + b + c + d + e)
        r = m.reaction('r')
        self.assertEqual(r.sid(), 'r')

        # Check reaction knows S1, S2, S3 but not S4
        self.assertEqual(r.species('S1'), m.species('S1'))
        self.assertEqual(r.species('S2'), m.species('S2'))
        self.assertEqual(r.species('S3'), m.species('S3'))
        self.assertRaises(KeyError, r.species, 'S4')
        m.species('S4')

        # Check reactants, products, modifiers
        s1r = r.reactants()
        self.assertEqual(len(s1r), 1)
        s1r = s1r[0]
        self.assertEqual(s1r.species(), m.species('S1'))
        self.assertEqual(s1r.initial_value(), myokit.Number(2))
        s2r = r.products()
        self.assertEqual(len(s2r), 1)
        s2r = s2r[0]
        self.assertEqual(s2r.species(), m.species('S2'))
        self.assertEqual(s2r.initial_value(), myokit.Number(5))
        s3r = r.modifiers()
        self.assertEqual(len(s3r), 1)
        s3r = s3r[0]
        self.assertEqual(s3r.species(), m.species('S3'))
        with self.assertRaises(AttributeError):
            s3r.initial_value()

        # Reactants and products are assignable, modifier is not
        self.assertEqual(m.assignable('r1'), s1r)
        self.assertEqual(m.assignable('r2'), s2r)
        self.assertRaises(KeyError, m.assignable, 'r3')

        # Check kinetic law
        self.assertEqual(
            r.kinetic_law().code(),
            '<Compartment c> * <Parameter k1> * <Species S1>')

        # Fast=true raises an error
        self.assertBad(
            a + '<reaction id="r" fast="true" />' + e, 'not supported')

        # Reactions must have a valid id
        self.assertBad(a + '<reaction />' + e, 'required attribute "id"')
        self.assertBad(a + '<reaction id="" />' + e, 'Invalid SId')

        # Reactions must have a product or reactant
        x = ('<reaction id="r" />')
        self.assertBad(a + x + e, 'at least one reactant or product')

        # Missing or empty kinetic law is ignored
        with WarningCollector() as w:
            self.parse(a + b + d + e)
        self.assertEqual(w.count(), 1)
        self.assertIn('No kinetic law set for reaction "r"', w.text())
        x = '<kineticLaw />'
        with WarningCollector() as w:
            m = self.parse(a + b + x + d + e)
        self.assertEqual(w.count(), 1)
        self.assertIn('No kinetic law set for reaction "r"', w.text())

        # Kinetic law: using species not used in reaction
        x = ('<kineticLaw>'
             ' <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '  <apply><ci>S4</ci></apply>'
             ' </math>'
             '</kineticLaw>')
        self.assertBad(a + b + x + d + e, 'Unknown or inaccessible')

        # Kinetic law: local parameters are not supported
        x = ('<kineticLaw>'
             ' <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '  <apply><ci>k</ci></apply>'
             ' </math>'
             ' <listOfLocalParameters>'
             '  <localParameter id="k" value="3.4" />'
             ' </listOfLocalParameters>'
             '</kineticLaw>')
        self.assertBad(a + b + x + d + e, 'Local parameters')

        # Kinetic law: invalid MathML
        x = ('<kineticLaw>'
             ' <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '  <apply><species>S3</species></apply>'
             ' </math>'
             '</kineticLaw>')
        self.assertBad(a + b + x + d + e, 'Unsupported element')

        # Unknown species in species reference
        x = ('<reaction id="r">'
             ' <listOfReactants>'
             '  <speciesReference species="S1" stoichiometry="2" id="r1" />'
             '  <speciesReference species="S5" stoichiometry="5" id="r2" />'
             ' </listOfReactants>')
        self.assertBad(a + x + c + d + e, 'unknown species "S5"')

        # Invalid stoichiometry
        x = ('<reaction id="r">'
             ' <listOfReactants>'
             '  <speciesReference species="S1" stoichiometry="2" id="r1" />'
             '  <speciesReference species="S2" stoichiometry="one" id="r2" />'
             ' </listOfReactants>')
        self.assertBad(a + x + c + d + e, 'Unable to convert stoichiometry')

        # Check that rate of change equations are correctly computed from
        # multiple reactions
        f = ('  <reaction id="reaction2">'
             '   <listOfReactants>'
             '    <speciesReference species="S1" />'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="S3" />'
             '   </listOfProducts>'
             '   <listOfModifiers>'
             '    <modifierSpeciesReference species="S4" />'
             '   </listOfModifiers>'
             '   <kineticLaw>'
             '    <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '     <apply>'
             '      <times/>'
             '      <ci> c </ci>'
             '      <ci> k1 </ci>'
             '      <ci> S1 </ci>'
             '     </apply>'
             '    </math>'
             '   </kineticLaw>'
             '  </reaction>')

        # Parse reaction
        m = self.parse(a + b + c + d + f + e)

        # Check first reaction
        r = m.reaction('r')
        self.assertEqual(r.sid(), 'r')

        # Check reaction knows S1, S2, S3 but not S4
        self.assertEqual(r.species('S1'), m.species('S1'))
        self.assertEqual(r.species('S2'), m.species('S2'))
        self.assertEqual(r.species('S3'), m.species('S3'))
        self.assertRaises(KeyError, r.species, 'S4')
        m.species('S4')

        # Check reactants, products, modifiers
        s1r = r.reactants()
        self.assertEqual(len(s1r), 1)
        s1r = s1r[0]
        self.assertEqual(s1r.species(), m.species('S1'))
        self.assertEqual(s1r.initial_value(), myokit.Number(2))
        s2r = r.products()
        self.assertEqual(len(s2r), 1)
        s2r = s2r[0]
        self.assertEqual(s2r.species(), m.species('S2'))
        self.assertEqual(s2r.initial_value(), myokit.Number(5))
        s3r = r.modifiers()
        self.assertEqual(len(s3r), 1)
        s3r = s3r[0]
        self.assertEqual(s3r.species(), m.species('S3'))
        with self.assertRaises(AttributeError):
            s3r.initial_value()

        # Reactants and products are assignable, modifier is not
        self.assertEqual(m.assignable('r1'), s1r)
        self.assertEqual(m.assignable('r2'), s2r)
        self.assertRaises(KeyError, m.assignable, 'r3')

        # Check kinetic law
        self.assertEqual(
            r.kinetic_law().code(),
            '<Compartment c> * <Parameter k1> * <Species S1>')

        # Check second reaction
        r = m.reaction('reaction2')
        self.assertEqual(r.sid(), 'reaction2')

        # Check reaction knows S1, S3, S4 but not S2
        self.assertEqual(r.species('S1'), m.species('S1'))
        self.assertEqual(r.species('S3'), m.species('S3'))
        self.assertEqual(r.species('S4'), m.species('S4'))
        self.assertRaises(KeyError, r.species, 'S2')
        m.species('S2')

        # Check kinetic law
        self.assertEqual(
            r.kinetic_law().code(),
            '<Compartment c> * <Parameter k1> * <Species S1>')

        # Check species reactions (no unecessary zeros and all terms present)
        model_mmt = m.myokit_model().code()
        S1_rhs = \
            'dot(S1_amount) = -(r1 * (size * myokit.k1 * S1_concentration)) ' \
            + '- size * myokit.k1 * S1_concentration'
        self.assertTrue(S1_rhs in model_mmt)
        S2_rhs = 'dot(S2_amount) = r2 * (size * myokit.k1 * S1_concentration)'
        self.assertTrue(S2_rhs in model_mmt)
        S3_rhs = 'dot(S3_amount) = size * myokit.k1 * S1_concentration'
        self.assertTrue(S3_rhs in model_mmt)

    def test_parse_rule(self):
        # Tests parsing assignment rules and rate rules

        # Set a parameter value
        a = ('<model name="mathml">'
             ' <listOfParameters>'
             '  <parameter id="x" constant="true" value="3"/>'
             '  <parameter id="y" constant="true" value="5"/>'
             ' </listOfParameters>')
        b = ('</model>')

        p = self.parse(a + b).parameter('x')
        self.assertEqual(p.initial_value(), myokit.Number(3))

        p = self.parse(a + b).parameter('y')
        self.assertEqual(p.initial_value(), myokit.Number(5))

        # Set RHS with assignmentRule or rateRule
        x = ('<listOfRules>'
             '  <assignmentRule variable="x">'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '    <apply>'
             '      <times/>'
             '      <ci> y </ci>'
             '      <cn> 3 </cn>'
             '    </apply>'
             '  </math>'
             '  </assignmentRule>'
             '  <rateRule variable="y">'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '    <apply>'
             '      <times/>'
             '      <ci> y </ci>'
             '      <apply>'
             '        <power/>'
             '        <ci> x </ci>'
             '        <cn> 2 </cn>'
             '      </apply>'
             '    </apply>'
             '  </math>'
             '  </rateRule>'
             '</listOfRules>')

        px = self.parse(a + x + b).parameter('x')
        py = self.parse(a + x + b).parameter('y')

        self.assertEqual(px.initial_value(), myokit.Number(3))
        self.assertEqual(py.initial_value(), myokit.Number(5))

        self.assertFalse(px.is_rate())
        self.assertTrue(py.is_rate())

        expr = myokit.Multiply(myokit.Name(py), myokit.Number(3))
        self.assertEqual(px.value().code(), expr.code())

        expr = myokit.Multiply(
            myokit.Name(py),
            myokit.Power(myokit.Name(px), myokit.Number(2)))
        self.assertEqual(py.value().code(), expr.code())

        # Set a compartment size
        a = ('<model name="mathml">'
             ' <listOfCompartments>'
             '  <compartment id="cx" size="10"/>'
             '  <compartment id="cy" size="5"/>'
             ' </listOfCompartments>')
        b = ('</model>')

        p = self.parse(a + b).compartment('cx')
        self.assertEqual(p.initial_value(), myokit.Number(10))

        p = self.parse(a + b).compartment('cy')
        self.assertEqual(p.initial_value(), myokit.Number(5))

        # Set RHS with assignmentRule or rateRule
        x = ('<listOfRules>'
             '  <assignmentRule variable="cx">'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '    <apply>'
             '      <times/>'
             '      <ci> cy </ci>'
             '      <cn> 3 </cn>'
             '    </apply>'
             '  </math>'
             '  </assignmentRule>'
             '  <rateRule variable="cy">'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '    <apply>'
             '      <times/>'
             '      <ci> cy </ci>'
             '      <apply>'
             '        <power/>'
             '        <ci> cx </ci>'
             '        <cn> 2 </cn>'
             '      </apply>'
             '    </apply>'
             '  </math>'
             '  </rateRule>'
             '</listOfRules>')

        px = self.parse(a + x + b).compartment('cx')
        py = self.parse(a + x + b).compartment('cy')

        self.assertEqual(px.initial_value(), myokit.Number(10))
        self.assertEqual(py.initial_value(), myokit.Number(5))

        self.assertFalse(px.is_rate())
        self.assertTrue(py.is_rate())

        expr = myokit.Multiply(myokit.Name(py), myokit.Number(3))
        self.assertEqual(px.value().code(), expr.code())

        expr = myokit.Multiply(
            myokit.Name(py),
            myokit.Power(myokit.Name(px), myokit.Number(2)))
        self.assertEqual(py.value().code(), expr.code())

        # Set a species amount (or concentration)
        a = ('<model name="mathml">'
             ' <listOfCompartments>'
             '  <compartment id="c" size="10"/>'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="sx" compartment="c" initialAmount="3.4"'
             '    boundaryCondition="true"/>'
             '  <species id="sy" compartment="c" initialConcentration="1.2"'
             '    boundaryCondition="true"/>'
             ' </listOfSpecies>')
        b = ('</model>')

        p = self.parse(a + b).species('sx')
        expr, expr_in_amount = p.initial_value()
        self.assertEqual(expr, myokit.Number(3.4))
        self.assertTrue(expr_in_amount)

        p = self.parse(a + b).species('sy')
        expr, expr_in_amount = p.initial_value()
        self.assertEqual(expr, myokit.Number(1.2))
        self.assertFalse(expr_in_amount)

        # Set RHS with assignmentRule or rateRule
        x = ('<listOfRules>'
             '  <assignmentRule variable="sx">'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '    <apply>'
             '      <times/>'
             '      <ci> sy </ci>'
             '      <cn> 3 </cn>'
             '    </apply>'
             '  </math>'
             '  </assignmentRule>'
             '  <rateRule variable="sy">'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '    <apply>'
             '      <times/>'
             '      <ci> sy </ci>'
             '      <apply>'
             '        <power/>'
             '        <ci> sx </ci>'
             '        <cn> 2 </cn>'
             '      </apply>'
             '    </apply>'
             '  </math>'
             '  </rateRule>'
             '</listOfRules>')

        px = self.parse(a + x + b).species('sx')
        py = self.parse(a + x + b).species('sy')

        expr, expr_in_amount = px.initial_value()
        self.assertEqual(expr, myokit.Number(3.4))
        self.assertTrue(expr_in_amount)

        expr, expr_in_amount = py.initial_value()
        self.assertEqual(expr, myokit.Number(1.2))
        self.assertFalse(expr_in_amount)

        self.assertFalse(px.is_rate())
        self.assertTrue(py.is_rate())

        expr = myokit.Multiply(myokit.Name(py), myokit.Number(3))
        self.assertEqual(px.value().code(), expr.code())

        expr = myokit.Multiply(
            myokit.Name(py),
            myokit.Power(myokit.Name(px), myokit.Number(2)))
        self.assertEqual(py.value().code(), expr.code())

        # Non-boundary species
        y = ('<model name="mathml">'
             ' <listOfCompartments>'
             '  <compartment id="c" size="10"/>'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="sx" compartment="c" initialAmount="3.4"/>'
             '  <species id="sy" compartment="c" initialConcentration="1.2"/>'
             ' </listOfSpecies>')

        self.assertBad(
            y + x + b, 'Assignment or rate rule set for species that is')

        # Set a stoichiometry
        a = ('<model name="mathml">'
             ' <listOfCompartments>'
             '  <compartment id="c" size="10"/>'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="s1" compartment="c" />'
             '  <species id="s2" compartment="c" />'
             ' </listOfSpecies>'
             ' <listOfReactions>'
             '  <reaction id="r">'
             '   <listOfReactants>'
             '    <speciesReference species="s1" id="sx" stoichiometry="2.1"/>'
             '   </listOfReactants>'
             '   <listOfProducts>'
             '    <speciesReference species="s2" id="sy" stoichiometry="3.5"/>'
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

        reaction = self.parse(a + x + b).reaction('r')
        px = reaction.reactants().pop()
        py = reaction.products().pop()

        self.assertEqual(px.initial_value(), myokit.Number(2.1))
        self.assertEqual(py.initial_value(), myokit.Number(3.5))

        # Set RHS with assignmentRule or rateRule
        x = ('<listOfRules>'
             '  <assignmentRule variable="sx">'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '    <apply>'
             '      <times/>'
             '      <ci> sy </ci>'
             '      <cn> 3 </cn>'
             '    </apply>'
             '  </math>'
             '  </assignmentRule>'
             '  <rateRule variable="sy">'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '    <apply>'
             '      <times/>'
             '      <ci> sy </ci>'
             '      <apply>'
             '        <power/>'
             '        <ci> sx </ci>'
             '        <cn> 2 </cn>'
             '      </apply>'
             '    </apply>'
             '  </math>'
             '  </rateRule>'
             '</listOfRules>')

        reaction = self.parse(a + x + b).reaction('r')
        px = reaction.reactants().pop()
        py = reaction.products().pop()

        self.assertEqual(px.initial_value(), myokit.Number(2.1))
        self.assertEqual(py.initial_value(), myokit.Number(3.5))

        self.assertFalse(px.is_rate())
        self.assertTrue(py.is_rate())

        expr = myokit.Multiply(myokit.Name(py), myokit.Number(3))
        self.assertEqual(px.value().code(), expr.code())

        expr = myokit.Multiply(
            myokit.Name(py),
            myokit.Power(myokit.Name(px), myokit.Number(2)))
        self.assertEqual(py.value().code(), expr.code())

        # No maths: warning
        a = ('<model name="mathml">'
             ' <listOfParameters>'
             '  <parameter id="x" constant="true" value="3"/>'
             '  <parameter id="y" constant="true" value="5"/>'
             ' </listOfParameters>')
        b = ('</model>')

        x = ('<listOfRules>'
             '  <assignmentRule variable="x">'
             '  </assignmentRule>'
             '</listOfRules>')
        with WarningCollector() as w:
            p = self.parse(a + x + b).parameter('x')
        self.assertIn('Rule does not define any mathematics', w.text())

        x = ('<listOfRules>'
             '  <rateRule variable="y">'
             '  </rateRule>'
             '</listOfRules>')
        with WarningCollector() as w:
            p = self.parse(a + x + b).parameter('y')
        self.assertIn('Rule does not define any mathematics', w.text())

        # Bad maths: error
        x = ('<listOfRules>'
             '  <assignmentRule variable="x">'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
             '    <apply>'
             '      <times/>'
             '      <weird_maths> 2 </weird_maths>'
             '      <cn> 3 </cn>'
             '    </apply>'
             '  </math>'
             '  </assignmentRule>'
             '</listOfRules>')
        self.assertBad(a + x + b, 'Unable to parse rule: ')

        # Missing symbol: error
        x = ('<listOfRules>'
             '  <rateRule>'
             '  </rateRule>'
             '</listOfRules>')
        self.assertBad(a + x + b, 'Element')

        # Invalid/unknown symbol
        x = ('<listOfRules>'
             '  <rateRule variable="blue">'
             '  </rateRule>'
             '</listOfRules>')
        self.assertBad(a + x + b, 'SId "blue" does not refer to')

    def test_parse_species(self):
        # Tests parsing species

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>')
        b = (' </listOfSpecies>'
             ' <listOfParameters>'
             '  <parameter id="p" />'
             ' </listOfParameters>'
             '</model>')

        # Simple species
        x = '<species compartment="c" id="spec" />'
        s0 = self.parse(a + x + b).species('spec')
        self.assertTrue(s0.sid() == 'spec')

        # Missing id
        x = '<species compartment="c" />'
        self.assertBad(a + x + b, 'required attribute "id"')

        # Invalid id
        x = '<species compartment="c" id="456" />'
        self.assertBad(a + x + b, 'Invalid SId')

        # Missing compartment
        x = '<species id="spec" />'
        self.assertBad(a + x + b, 'required attribute "compartment"')

        # Unknown compartment
        x = '<species id="spec" compartment="hello" />'
        self.assertBad(a + x + b, 'Unknown compartment')

        # Amount or concentration
        self.assertFalse(s0.is_amount())
        x = '<species compartment="c" id="s" hasOnlySubstanceUnits="false" />'
        s = self.parse(a + x + b).species('s')
        self.assertFalse(s.is_amount())
        x = '<species compartment="c" id="s" hasOnlySubstanceUnits="true" />'
        s = self.parse(a + x + b).species('s')
        self.assertTrue(s.is_amount())

        # Boundary
        self.assertFalse(s0.is_boundary())
        x = '<species compartment="c" id="s" boundaryCondition="false" />'
        s = self.parse(a + x + b).species('s')
        self.assertFalse(s.is_boundary())
        x = '<species compartment="c" id="s" boundaryCondition="true" />'
        s = self.parse(a + x + b).species('s')
        self.assertTrue(s.is_boundary())

        # Constant
        self.assertFalse(s0.is_constant())
        x = '<species compartment="c" id="s" constant="false" />'
        s = self.parse(a + x + b).species('s')
        self.assertFalse(s.is_constant())
        x = '<species compartment="c" id="s" constant="true" />'
        s = self.parse(a + x + b).species('s')
        self.assertTrue(s.is_constant())

        # Substance units
        self.assertEqual(s0.substance_units(), myokit.units.dimensionless)
        x = '<species compartment="c" id="s" substanceUnits="volt" />'
        s = self.parse(a + x + b).species('s')
        self.assertEqual(s.substance_units(), myokit.units.volt)
        x = ('<species compartment="c" id="s"'
             ' substanceUnits="volt" hasOnlySubstanceUnits="true" />')
        s = self.parse(a + x + b).species('s')
        self.assertEqual(s.substance_units(), myokit.units.volt)

        # Invalid units
        x = '<species compartment="c" id="s" substanceUnits="made-up" />'
        self.assertBad(a + x + b, 'Unknown units')

        # Initial amount
        x = ('<species compartment="c" id="s"'
             ' hasOnlySubstanceUnits="true" initialAmount="3" />')
        s = self.parse(a + x + b).species('s')
        expr, expr_in_amount = s.initial_value()
        self.assertEqual(expr, myokit.Number(3))
        self.assertTrue(expr_in_amount)

        # Initial concentration
        x = ('<species compartment="c" id="s"'
             ' hasOnlySubstanceUnits="false" initialConcentration="1.2" />')
        s = self.parse(a + x + b).species('s')
        expr, expr_in_amount = s.initial_value()
        self.assertEqual(expr, myokit.Number(1.2))
        self.assertFalse(expr_in_amount)

        # Set both initial amount and concentration
        x = ('<species compartment="c" id="s"'
             ' hasOnlySubstanceUnits="true" initialAmount="3"'
             ' initialConcentration="10"/>')
        self.assertBad(
            a + x + b, 'Species cannot set both an initialAmount and an')

        # Invalid initial value
        x = ('<species compartment="c" id="s"'
             ' hasOnlySubstanceUnits="true" initialAmount="made-up" />')
        self.assertBad(
            a + x + b, 'Unable to convert initial species value to float "')

        # Conversion factor parameter
        x = ('<species compartment="c" id="s" conversionFactor="p" />')
        m = self.parse(a + x + b)
        s = m.species('s')
        self.assertEqual(s.conversion_factor(), m.parameter('p'))

        # Conversion factor points to unknown parameter
        x = ('<species compartment="c" id="s" conversionFactor="q" />')
        self.assertBad(a + x + b, 'Unknown parameter')

    def test_parse_species_reference(self):
        # TODO:
        pass

    def test_parse_unit(self):
        # Tests parsing units and unit definitions

        a = '<model><listOfUnitDefinitions>'
        b = '</listOfUnitDefinitions></model>'

        # Dimensionless units
        xml = '<unitDefinition id="dimless" />'
        m = self.parse(a + xml + b)
        self.assertEqual(m.unit('dimless'), myokit.units.dimensionless)

        # Dimensionless units
        xml = (
            '<unitDefinition id="dimless">'
            ' <listOfUnits />'
            '</unitDefinition>')
        m = self.parse(a + xml + b)
        self.assertEqual(m.unit('dimless'), myokit.units.dimensionless)

        # Full featured units
        xml = (
            '<unitDefinition id="centimeter">'
            ' <listOfUnits>'
            '  <unit kind="meter" scale="-2" />'
            ' </listOfUnits>'
            '</unitDefinition>'
            '<unitDefinition id="supervolt">'
            ' <listOfUnits>'
            '  <unit kind="volt" multiplier="2.3" scale="3" exponent="2" />'
            '  <unit kind="meter" exponent="-1" />'
            ' </listOfUnits>'
            '</unitDefinition>')
        m = self.parse(a + xml + b)
        self.assertEqual(m.unit('centimeter'), myokit.units.cm)
        sv = (myokit.units.volt * 2.3e3)**2 / myokit.units.meter
        self.assertEqual(m.unit('supervolt'), sv)

        # Parameter with custom unit
        x = ('<model>'
             ' <listOfUnitDefinitions>'
             '  <unitDefinition id="centimeter">'
             '   <listOfUnits>'
             '    <unit kind="meter" scale="-2" />'
             '   </listOfUnits>'
             '  </unitDefinition>'
             ' </listOfUnitDefinitions>'
             ' <listOfParameters>'
             '  <parameter id="a" units="centimeter" />'
             ' </listOfParameters>'
             '</model>')
        m = self.parse(x)
        self.assertEqual(m.parameter('a').units(), myokit.units.cm)

        # Missing id
        xml = '<unitDefinition />'
        self.assertBad(a + xml + b, 'required attribute "id"')

        # Invalid id
        xml = '<unitDefinition id="123" />'
        self.assertBad(a + xml + b, 'Invalid UnitSId')

        # Invalid unit kind
        xml = (
            '<unitDefinition id="centimeter">'
            ' <listOfUnits>'
            '  <unit kind="celsius" scale="-2" />'
            ' </listOfUnits>'
            '</unitDefinition>')
        self.assertBad(a + xml + b, 'Unable to parse unit kind: ')

        # Invalid unit attributes
        xml = (
            '<unitDefinition id="centimeter">'
            ' <listOfUnits>'
            '  <unit kind="volt" scale="made-up" />'
            ' </listOfUnits>'
            '</unitDefinition>')
        self.assertBad(a + xml + b, 'Unable to parse unit attributes')

    def test_tag(self):
        # Tests handling of different namespaces.

        # Create content that raises a missing ID error and therefore
        # tags the component.
        xml_content = (
            '<model>'
            ' <listOfCompartments>'
            '  <compartment />'
            ' </listOfCompartments>'
            '</model>')

        # Test SBML 3.2 namespace
        level = 3
        version = 2
        lv = 'level' + str(level) + '/version' + str(version)
        sbml_file = (
            '<sbml xmlns="http://www.sbml.org/sbml/' + lv + '/core"'
            ' level="' + str(level) + '"'
            ' version="' + str(version) + '">'
            + xml_content +
            '</sbml>')

        tag = 'sbml:compartment'
        message = 'Element ' + tag + ' is missing required'

        self.assertRaisesRegex(
            SBMLParsingError, message, self.p.parse_string, sbml_file)


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
