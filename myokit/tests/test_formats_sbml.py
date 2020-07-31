#!/usr/bin/env python3
#
# Tests Myokit's SBML support.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.formats
import myokit.formats.sbml
from myokit.formats.sbml import SBMLParser, SBMLParsingError

# from shared import DIR_FORMATS, WarningCollector
from shared import DIR_FORMATS, WarningCollector

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


'''
class SBMLImporterTest(unittest.TestCase):
    """
    Tests the SBMLImporter.
    """

    def test_capability_reporting(self):
        # Test if the right capabilities are reported.
        i = myokit.formats.importer('sbml')
        self.assertFalse(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_hh_model(self):
        # Tests importing the Hodgkin-Huxley model
        i = myokit.formats.importer('sbml')
        with WarningCollector() as w:
            model = i.model(
                os.path.join(DIR_FORMATS, 'sbml', 'HodgkinHuxley.xml'))
        self.assertIn('Unknown SBML namespace', w.text())

        v = model.get('myokit.V')
        self.assertAlmostEqual(v.rhs().eval(), -4.01765286235500341e-03)
'''


class SBMLParserTest(unittest.TestCase):
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
        # In this test, we cross-test:
        #  - TODO
        #  - TODO
        # Units do not have SIds, but their own UnitSIds.

        '''
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
        self.assertBad(xml, 'Duplicate parameter id')

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
        self.assertBad(xml, 'Duplicate species id')

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
        self.assertBad(xml, 'Duplicate species id')

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
            '<reaction >'
            '<listOfReactants>'
            '<speciesReference species="someSpecies" '
            'id="' + stoich_id + '"/>'
            '</listOfReactants>'
            '</reaction>'
            '</listOfReactions>'
            '</model>')
        with WarningCollector() as w:
            self.assertBad(xml=xml, message='Stoichiometry ID is not unique.')
        self.assertEqual(w.count(), 1)
        self.assertIn('Stoichiometry has not been set', w.text())

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
            '<reaction >'
            '<listOfProducts>'
            '<speciesReference species="someSpecies" '
            'id="' + stoich_id + '"/>'
            '</listOfProducts>'
            '</reaction>'
            '</listOfReactions>'
            '</model>')
        with WarningCollector() as w:
            self.assertBad(xml=xml, message='Stoichiometry ID is not unique.')
        self.assertEqual(w.count(), 1)
        self.assertIn('Stoichiometry has not been set', w.text())
        '''

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
        self.assertBad(a + x + c, 'Unable to parse MathML: Expect')

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
        self.assertEqual(s.initial_value(), myokit.Number(4.5))

        # Reset a species amount (or concentration)
        b = (' <listOfSpecies>'
             '  <species id="s" compartment="c" initialConcentration="3" />'
             ' </listOfSpecies>')
        m = self.parse(a + b + d)
        s = m.species('s')
        self.assertEqual(s.initial_value(), myokit.Number(3))
        m = self.parse(a + b + c + d)
        s = m.species('s')
        self.assertEqual(s.initial_value(), myokit.Number(4.5))

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

        self.assertBad('<model areaUnits="meter_squared" />', 'Unknown units')

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

    def test_parse_reaction(self):
        # Test parsing reactions, species references, kinetic laws

        a = ('<model>'
             ' <listOfCompartments>'
             '  <compartment id="c" size="1.2" />'
             ' </listOfCompartments>'
             ' <listOfSpecies>'
             '  <species id="S1" compartment="c" />'
             '  <species id="S2" compartment="c" />'
             '  <species id="S3" compartment="c" />'
             '  <species id="S4" compartment="c" />'
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

    def test_parse_rule(self):
        # Tests parsing assignment rules and rate rules

        #TODO: See parse_initial_assignment
        pass

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
        self.assertFalse(s0.amount())
        x = '<species compartment="c" id="s" hasOnlySubstanceUnits="false" />'
        s = self.parse(a + x + b).species('s')
        self.assertFalse(s.amount())
        x = '<species compartment="c" id="s" hasOnlySubstanceUnits="true" />'
        s = self.parse(a + x + b).species('s')
        self.assertTrue(s.amount())

        # Boundary
        self.assertFalse(s0.boundary())
        x = '<species compartment="c" id="s" boundary="false" />'
        s = self.parse(a + x + b).species('s')
        self.assertFalse(s.boundary())
        x = '<species compartment="c" id="s" boundary="true" />'
        s = self.parse(a + x + b).species('s')
        self.assertTrue(s.boundary())

        # Constant
        self.assertFalse(s0.constant())
        x = '<species compartment="c" id="s" constant="false" />'
        s = self.parse(a + x + b).species('s')
        self.assertFalse(s.constant())
        x = '<species compartment="c" id="s" constant="true" />'
        s = self.parse(a + x + b).species('s')
        self.assertTrue(s.constant())

        # Substance units
        self.assertEqual(s0.substance_units(), myokit.units.dimensionless)
        x = '<species compartment="c" id="s" substanceUnits="volt" />'
        s = self.parse(a + x + b).species('s')
        self.assertEqual(s.substance_units(), myokit.units.volt)
        x = ('<species compartment="c" id="s"'
             ' substanceUnits="volt" hasOnlySubstanceUnits="true" />')
        s = self.parse(a + x + b).species('s')
        self.assertEqual(s.substance_units(), myokit.units.volt)

        # Initial amount
        x = ('<species compartment="c" id="s"'
             ' hasOnlySubstanceUnits="true" initialAmount="3" />')
        s = self.parse(a + x + b).species('s')
        self.assertEqual(s.initial_value(), myokit.Number(3))

        # Initial concentration
        x = ('<species compartment="c" id="s"'
             ' hasOnlySubstanceUnits="false" initialConcentration="1.2" />')
        s = self.parse(a + x + b).species('s')
        self.assertEqual(s.initial_value(), myokit.Number(1.2))

        # Conversion factor parameter
        x = ('<species compartment="c" id="s" conversionFactor="p" />')
        m = self.parse(a + x + b)
        s = m.species('s')
        self.assertEqual(s.conversion_factor(), m.parameter('p'))

        # Conversion factor points to unknown parameter
        x = ('<species compartment="c" id="s" conversionFactor="q" />')
        self.assertBad(a + x + b, 'Unknown parameter')

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

    def test_myokit_model_compartments_exist(self):
        # Tests compartment conversion from SBML to myokit model.

        a = '<model><listOfCompartments>'
        b = '</listOfCompartments></model>'

        # Test simple compartment
        x = '<compartment id="a" />'
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check whether component 'a' exists
        self.assertTrue(m.has_component('a'))

        # Check whether component 'myokit' exists
        self.assertTrue(m.has_component('myokit'))

        # Check that number of components is as expected
        # (component 'a' and 'myokit')
        self.assertEqual(m.count_components(), 2)

    def test_myokit_model_compartment_size(self):
        # Tests whether compartment size variable is created and units are set
        # correctly.

        # Test I: No size unit provided
        a = '<model><listOfCompartments>'
        b = '</listOfCompartments></model>'

        # Test simple compartment
        x = '<compartment id="c" />'
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Test that size variable exists
        component = m.get('c')
        self.assertTrue(component.has_variable('size'))

        # Check that units are set correctly
        var = component.get('size')
        self.assertEqual(var.unit(), myokit.units.dimensionless)

        # Test II: Size unit provided
        a = '<model><listOfCompartments>'
        b = '</listOfCompartments></model>'

        # Test simple compartment
        x = '<compartment id="c" units="meter"/>'
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Test that size variable exists
        component = m.get('c')
        self.assertTrue(component.has_variable('size'))

        # Check that units are set correctly
        var = component.get('size')
        self.assertEqual(var.unit(), myokit.units.meter)

    def test_myokit_model_existing_myokit_compartment(self):
        # Tests that renaming of 'myokit' compartment works.

        a = '<model><listOfCompartments>'
        b = '</listOfCompartments></model>'

        # Test simple compartment
        x = '<compartment id="myokit" />'
        m = self.parse(a + x + b)
        m = m.myokit_model()

        # Check whether component 'a' exists
        self.assertTrue(m.has_component('myokit'))

        # Check whether component 'myokit' exists
        self.assertTrue(m.has_component('myokit_1'))

        # Check that number of components is as expected
        # (component 'a' and 'myokit')
        self.assertEqual(m.count_components(), 2)

    def test_myokit_model_species_exist(self):
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

    def test_myokit_model_species_units(self):
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

    '''
    def test_reserved_compartment_id(self):
        # ``Myokit`` is a reserved ID that is used while importing for the
        # myokit compartment.

        xml = (
            '<model id="test" name="test" timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="myokit"/>'
            '</listOfCompartments>'
            '</model>')
        self.assertBad(xml=xml, message='The id "myokit".')

    def test_reserved_parameter_id(self):
        # ``globalConversionFactor`` is a reserved ID that is used while
        # importing the global conversion factor.

        xml = (
            '<model id="test" conversionFactor="someFactor" '
            'timeUnits="second">'
            '<listOfParameters>'
            '<parameter id="globalConversionFactor"/>'
            '</listOfParameters>'
            '</model>')
        self.assertBad(
            xml=xml,
            message='The ID <globalConversionFactor> is protected in a myokit'
            ' SBML import. Please rename IDs.')

    def test_stoichiometry_reference(self):
        # Tests whether stoichiometry parameters are linked properly to global
        # variables.

        # Check that reactant stoichiometry is added as parameter to referenced
        # compartment
        comp_id = 'someComp'
        stoich_id = 'someStoich'
        xml = (
            '<model id="test" name="test" timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="' + comp_id + '"/>'
            '</listOfCompartments>'
            '<listOfSpecies>'
            '<species id="someSpecies" hasOnlySubstanceUnits="true" '
            'compartment="' + comp_id + '" '
            'constant="false" boundaryCondition="false"/>'
            '</listOfSpecies>'
            '<listOfReactions>'
            '<reaction compartment="' + comp_id + '">'
            '<listOfReactants>'
            '<speciesReference species="someSpecies" '
            'id="' + stoich_id + '"/>'
            '</listOfReactants>'
            '</reaction>'
            '</listOfReactions>'
            '</model>')
        with WarningCollector() as w:
            model = self.parse(xml)
        self.assertTrue(model.has_variable(comp_id + '.' + stoich_id))
        self.assertEqual(w.count(), 1)

        # Check that reactant stoichiometry is added as parameter to <myokit>
        # compartment, if no compartment is referenced
        comp_id = 'myokit'
        stoich_id = 'someStoich'
        xml = (
            '<model id="test" name="test" timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="someComp"/>'
            '</listOfCompartments>'
            '<listOfSpecies>'
            '<species id="someSpecies" hasOnlySubstanceUnits="true" '
            'compartment="someComp" constant="false" boundaryCondition="false"'
            '/>'
            '</listOfSpecies>'
            '<listOfReactions>'
            '<reaction >'
            '<listOfReactants>'
            '<speciesReference species="someSpecies" '
            'id="' + stoich_id + '"/>'
            '</listOfReactants>'
            '</reaction>'
            '</listOfReactions>'
            '</model>')
        with WarningCollector() as w:
            model = self.parse(xml)
        self.assertTrue(model.has_variable(comp_id + '.' + stoich_id))
        self.assertEqual(w.count(), 1)

        # Check that product stoichiometry is added as parameter to referenced
        # compartment
        comp_id = 'someComp'
        stoich_id = 'someStoich'
        xml = (
            '<model id="test" name="test" timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="' + comp_id + '"/>'
            '</listOfCompartments>'
            '<listOfSpecies>'
            '<species id="someSpecies" hasOnlySubstanceUnits="true" '
            'compartment="' + comp_id + '" '
            'constant="false" boundaryCondition="false"/>'
            '</listOfSpecies>'
            '<listOfReactions>'
            '<reaction compartment="' + comp_id + '">'
            '<listOfProducts>'
            '<speciesReference species="someSpecies" '
            'id="' + stoich_id + '"/>'
            '</listOfProducts>'
            '</reaction>'
            '</listOfReactions>'
            '</model>')
        with WarningCollector() as w:
            model = self.parse(xml)
        self.assertTrue(model.has_variable(comp_id + '.' + stoich_id))
        self.assertEqual(w.count(), 1)

        # Check that product stoichiometry is added as parameter to <myokit>
        # compartment, if no compartment is referenced
        comp_id = 'myokit'
        stoich_id = 'someStoich'
        xml = (
            '<model id="test" name="test" timeUnits="second">'
            '<listOfCompartments>'
            '<compartment id="someComp"/>'
            '</listOfCompartments>'
            '<listOfSpecies>'
            '<species id="someSpecies" hasOnlySubstanceUnits="true" '
            'compartment="someComp" constant="false" boundaryCondition="false"'
            '/>'
            '</listOfSpecies>'
            '<listOfReactions>'
            '<reaction >'
            '<listOfProducts>'
            '<speciesReference species="someSpecies" '
            'id="' + stoich_id + '"/>'
            '</listOfProducts>'
            '</reaction>'
            '</listOfReactions>'
            '</model>')
        with WarningCollector() as w:
            model = self.parse(xml)
        self.assertTrue(model.has_variable(comp_id + '.' + stoich_id))
        self.assertEqual(w.count(), 1)
'''


class SBMLTestSuiteExampleTest(unittest.TestCase):
    """
    Tests parsing an SBML file with species, compartments, and reactions, as
    well as assignment rules.

    This tests uses a modified model (case 00004) from the SBML test suite
    http://sbml.org/Facilities/Database/.
    """
    @classmethod
    def setUpClass(cls):
        p = SBMLParser()
        with WarningCollector():
            # Parse SBML model
            model = p.parse_file(os.path.join(
                DIR_FORMATS, 'sbml', '00004-sbml-l3v2-modified.xml'))

            # Convert model to myokit model
            cls.model = model.myokit_model()

    # def test_assignment_rules(self):
    #     # Tests whether intermediate variables have been assigned with correct
    #     # expressions.

    #     # parameter 1
    #     parameter = 'S1_Concentration'
    #     parameter = self.model.get('compartment.' + parameter)
    #     expression = 'compartment.S1 / compartment.size'
    #     self.assertEqual(str(parameter.rhs()), expression)

    #     # parameter 2
    #     parameter = 'S2_Concentration'
    #     parameter = self.model.get('compartment.' + parameter)
    #     expression = 'compartment.S2 / compartment.size'
    #     self.assertEqual(str(parameter.rhs()), expression)

    #     # parameter 3
    #     parameter = 'i_Na'
    #     parameter = self.model.get('myokit.' + parameter)
    #     expression = 'myokit.g_Na * myokit.m ^ 3'
    #     self.assertEqual(str(parameter.rhs()), expression)

    def test_compartments_exist(self):
        # Tests whether compartments have been imported properly. Compartments
        # should include the compartments in the SBML file, plus a myokit
        # compartment for the global parameters.

        # compartment 1
        comp = 'compartment'
        self.assertTrue(self.model.has_component(comp))

        # compartment 2
        comp = 'myokit'
        self.assertTrue(self.model.has_component(comp))

        # total number of compartments
        number = 2
        self.assertEqual(self.model.count_components(), number)

    # def test_compartment_initial_size(self):
    #     # Tests whether species have been initialised with the correct values.

    #     # Compartment 1
    #     expected_size = 1
    #     size = self.model.get('compartment.size')
    #     self.assertEqual(size.eval(), expected_size)

    def test_species_exist(self):
        # Tests whether species have been imported properly. Species should
        # exist in amount, and if hasOnlySubstanceUnits is False also in
        # concentration.

        print(self.model.code())

        # Species 1
        # In amount
        species = 'compartment.S1_amount'
        self.assertTrue(self.model.has_variable(species))

        # In concentration
        species = 'compartment.S1_concentration'
        self.assertTrue(self.model.has_variable(species))

        # Species 1
        # In amount
        species = 'compartment.S2_amount'
        self.assertTrue(self.model.has_variable(species))

        # In concentration
        species = 'compartment.S2_concentration'
        self.assertTrue(self.model.has_variable(species))

    def test_parameters_exist(self):
        # Tests whether parameters have been imported properly. Parameters
        # should be imported to the 'myokit' component, except the 'size'
        # parameters

        #
        # Parameter 1
        parameter = 'myokit.k1'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 2
        parameter = 'myokit.k2'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 3
        parameter = 'myokit.V'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 4
        parameter = 'myokit.i_Na'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 5
        parameter = 'myokit.g_Na'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 6
        parameter = 'myokit.m'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 7
        parameter = 'myokit.h'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 8
        parameter = 'myokit.Cm'
        self.assertTrue(self.model.has_variable(parameter))

    def test_number_variables_in_components(self):
        # Test that no untested variables are in the components.

        # Check 'compartment' component
        # Expected number of variables
        # [size, S1_amount, S1_concentration, S2_amount, S2_concentration]
        n = 5

        # Asssert that exactly n variables are in component
        component = self.model.get('compartment')
        self.assertEqual(component.count_variables(), n)

        # Check 'myokit' component
        # Expected number of variables
        # [k1, k2, V, i_Na, g_Na, m, h, Cm, time]
        n = 9

        # Asssert that exactly n variables are in component
        component = self.model.get('myokit')
        self.assertEqual(component.count_variables(), n)


    # def test_species_initial_value(self):
    #     # Tests whether species have been initialised with the correct values.

    #     # Species 1
    #     # Initial amount
    #     expected_amount = 0.15
    #     species = self.model.get('compartment.S1_amount')
    #     self.assertEqual(species.eval(), expected_amount)

    #     # Initial concentration
    #     expected_conc = 0.15 / 1
    #     species = self.model.get('compartment.S1_concentration')
    #     self.assertEqual(species.eval(), expected_conc)

    #     # Species 2
    #     # Initial amount
    #     expected_amount = 0
    #     species = self.model.get('compartment.S2_amount')
    #     self.assertEqual(species.eval(), expected_amount)

    #     # Initial concentration
    #     expected_conc = 0 / 1
    #     species = self.model.get('compartment.S2_concentration')
    #     self.assertEqual(species.eval(), expected_conc)


'''
    def test_constant_parameters(self):
        # Tests whether all constant parameters in the file were properly
        # imported.

        # parameter 1
        parameter = 'k1'
        self.assertTrue(self.model.has_variable('myokit.' + parameter))
        parameter = self.model.get('myokit.' + parameter)
        self.assertTrue(parameter.is_constant())

        # parameter 2
        parameter = 'k2'
        self.assertTrue(self.model.has_variable('myokit.' + parameter))
        parameter = self.model.get('myokit.' + parameter)
        self.assertTrue(parameter.is_constant())

        # parameter 3
        parameter = 'size'
        self.assertTrue(
            self.model.has_variable('compartment.' + parameter))
        parameter = self.model.get('compartment.' + parameter)
        self.assertTrue(parameter.is_constant())

        # parameter g_Na
        parameter = 'g_Na'
        self.assertTrue(self.model.has_variable('myokit.' + parameter))
        parameter = self.model.get('myokit.' + parameter)
        self.assertTrue(parameter.is_constant())

        # parameter Cm
        parameter = 'Cm'
        self.assertTrue(self.model.has_variable('myokit.' + parameter))
        parameter = self.model.get('myokit.' + parameter)
        self.assertTrue(parameter.is_constant())

        # total number of constants
        number = 6
        self.assertEqual(self.model.count_variables(const=True), number)

    def test_initial_values(self):
        # Tests whether initial values of constant parameters and state
        # variables have been set properly.

        # State S1
        state = self.model.get('compartment.S1')
        self.assertEqual(state.state_value(), 0.15)

        # State S2
        state = self.model.get('compartment.S2')
        self.assertEqual(state.state_value(), 0)

        # State V
        state = self.model.get('myokit.V')
        self.assertEqual(state.state_value(), -80)

        # State m
        state = self.model.get('myokit.m')
        self.assertAlmostEqual(state.state_value(), 0.3)

        # parameter 1
        parameter = self.model.get('myokit.k1')
        self.assertEqual(parameter.eval(), 0.35)

        # parameter 2
        parameter = self.model.get('myokit.k2')
        self.assertEqual(parameter.eval(), 180)

        # parameter compartment.size
        parameter = self.model.get('compartment.size')
        self.assertEqual(parameter.eval(), 1)

        # parameter g_Na
        parameter = self.model.get('myokit.g_Na')
        self.assertEqual(parameter.eval(), 2)

        # parameter Cm
        parameter = self.model.get('myokit.Cm')
        self.assertEqual(parameter.eval(), 1)

    def test_intermediary_variables(self):
        # Tests whether all intermediary variables in the file were properly
        # imported.

        var = self.model.get('compartment.S1_Concentration')
        self.assertTrue(var.is_intermediary())

        var = self.model.get('compartment.S2_Concentration')
        self.assertTrue(var.is_intermediary())

        var = self.model.get('myokit.i_Na')
        self.assertTrue(var.is_intermediary())

        # total number of intermediary variables
        self.assertEqual(self.model.count_variables(inter=True), 3)

    def test_older_version(self):
        # Test loading the same model in an older SBML format.

        # Parse model in older format
        p = SBMLParser()
        with WarningCollector():
            old_model = p.parse_file(os.path.join(
                DIR_FORMATS, 'sbml', '00004-sbml-l2v1-modified.xml'))

        # Set time units (Only introduced in level 3 version 1)
        old_model.time().set_unit(self.model.time().unit())

        # Update initial states set with initialAssignment (level 3 only)
        new_value = self.model.get('myokit.m').state_value()
        self.assertAlmostEqual(
            old_model.get('myokit.m').state_value(), new_value)
        old_model.get('myokit.m').set_state_value(new_value)

        # Update initial value set with initialAssignment (level 3 only)
        self.assertAlmostEqual(
            old_model.get('myokit.h').eval(),
            self.model.get('myokit.h').eval(),
        )
        old_model.get('myokit.h').set_rhs(
            self.model.get('myokit.h').rhs().code())

        # Now models should be equal
        #with open('new.xml', 'w') as f:
        #    f.write(self.model.code())
        #with open('old.xml', 'w') as f:
        #    f.write(old_model.code())
        self.assertEqual(self.model.code(), old_model.code())

    def test_rate_expressions(self):
        # Tests whether state variables have been assigned with the correct
        # rate expression. Those may come from a rateRule or reaction.

        # state 1
        state = 'S1'
        state = self.model.get('compartment.' + state)
        expression = (
            '-(compartment.size * myokit.k1 * compartment.S1_Concentration)'
            ' + compartment.size * myokit.k2'
            ' * compartment.S2_Concentration ^ 2')
        self.assertEqual(state.rhs().code(), expression)

        # state 2
        state = 'S2'
        state = self.model.get('compartment.' + state)
        expression = str(
            '2 * (compartment.size * myokit.k1 * '
            + 'compartment.S1_Concentration) - 2 * '
            + '(compartment.size * myokit.k2 '
            + '* compartment.S2_Concentration ^ 2)')
        self.assertEqual(str(state.rhs()), expression)

        # state 3
        state = 'V'
        state = self.model.get('myokit.' + state)
        expression = 'myokit.i_Na / myokit.Cm'
        self.assertEqual(str(state.rhs()), expression)

    def test_state_variables(self):
        # Tests whether all dynamic variables were imported properly.

        # state 1
        state = 'S1'
        self.assertTrue(self.model.has_variable('compartment.' + state))
        state = self.model.get('compartment.' + state)
        self.assertTrue(state.is_state())

        # state 2
        state = 'S2'
        self.assertTrue(self.model.has_variable('compartment.' + state))
        state = self.model.get('compartment.' + state)
        self.assertTrue(state.is_state())

        # state V
        self.assertTrue(self.model.has_variable('myokit.V'))
        state = self.model.get('myokit.V')
        self.assertTrue(state.is_state())

        # state m
        self.assertTrue(self.model.has_variable('myokit.m'))
        state = self.model.get('myokit.m')
        self.assertTrue(state.is_state())

        # total number of states
        self.assertEqual(self.model.count_variables(state=True), 4)

    def test_time(self):
        # Tests whether the time bound variable was set properly

        variable = 'time'
        self.assertTrue(self.model.has_variable('myokit.' + variable))
        variable = self.model.get('myokit.' + variable)
        self.assertTrue(variable.is_bound())

    def test_units(self):
        # Tests units parsing.

        # state 1
        state = 'S1'
        state = self.model.get('compartment.' + state)
        unit = myokit.units.mol
        self.assertEqual(state.unit(), unit)

        # state 2
        state = 'S2'
        state = self.model.get('compartment.' + state)
        unit = myokit.units.mol
        self.assertEqual(state.unit(), unit)

        # state 3
        state = 'V'
        state = self.model.get('myokit.' + state)
        unit = myokit.units.V * 10 ** (-3)
        self.assertEqual(state.unit(), unit)

        # parameter 1
        parameter = 'k1'
        parameter = self.model.get('myokit.' + parameter)
        unit = None
        self.assertEqual(parameter.unit(), unit)

        # parameter 2
        parameter = 'k2'
        parameter = self.model.get('myokit.' + parameter)
        unit = None
        self.assertEqual(parameter.unit(), unit)

        # parameter 3
        parameter = 'size'
        parameter = self.model.get('compartment.' + parameter)
        unit = myokit.units.L
        self.assertEqual(parameter.unit(), unit)

        # parameter 4
        parameter = 'S1_Concentration'
        parameter = self.model.get('compartment.' + parameter)
        unit = myokit.units.mol / myokit.units.L
        self.assertEqual(parameter.unit(), unit)

        # parameter 5
        parameter = 'S2_Concentration'
        parameter = self.model.get('compartment.' + parameter)
        unit = myokit.units.mol / myokit.units.L
        self.assertEqual(parameter.unit(), unit)

        # parameter 6
        parameter = 'i_Na'
        parameter = self.model.get('myokit.' + parameter)
        unit = None
        self.assertEqual(parameter.unit(), unit)

        # parameter 7
        parameter = 'g_Na'
        parameter = self.model.get('myokit.' + parameter)
        unit = None
        self.assertEqual(parameter.unit(), unit)

        # parameter 8
        parameter = 'm'
        parameter = self.model.get('myokit.' + parameter)
        unit = None
        self.assertEqual(parameter.unit(), unit)

        # parameter 9
        parameter = 'Cm'
        parameter = self.model.get('myokit.' + parameter)
        unit = None
        self.assertEqual(parameter.unit(), unit)
'''


class SBMLHodgkinHuxleyExampleTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        p = SBMLParser()
        with WarningCollector():
            # Parse SBML model
            model = p.parse_file(os.path.join(
                DIR_FORMATS, 'sbml', 'HodgkinHuxley.xml'))

            # Convert model to myokit model
            cls.model = model.myokit_model()

    def test_compartments_exist(self):
        # Tests whether compartments have been imported properly. Compartments
        # should include the compartments in the SBML file, plus a myokit
        # compartment for the global parameters.

        # compartment 1
        comp = 'unit_compartment'
        self.assertTrue(self.model.has_component(comp))

        # compartment 2
        comp = 'myokit'
        self.assertTrue(self.model.has_component(comp))

        # total number of compartments
        number = 2
        self.assertEqual(self.model.count_components(), number)

    def test_parameters_exist(self):
        # Tests whether parameters have been imported properly. Parameters
        # should be imported to the 'myokit' component.

        # Parameter 1
        parameter = 'myokit.V'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 2
        parameter = 'myokit.V_neg'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 3
        parameter = 'myokit.E'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 4
        parameter = 'myokit.I'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 5
        parameter = 'myokit.i_Na'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 6
        parameter = 'myokit.i_K'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 7
        parameter = 'myokit.m'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 8
        parameter = 'myokit.h'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 9
        parameter = 'myokit.n'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 10
        parameter = 'myokit.E_R'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 11
        parameter = 'myokit.Cm'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 12
        parameter = 'myokit.g_Na'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 13
        parameter = 'myokit.g_K'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 14
        parameter = 'myokit.g_L'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 15
        parameter = 'myokit.E_Na'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 16
        parameter = 'myokit.E_K'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 17
        parameter = 'myokit.E_L'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 18
        parameter = 'myokit.V_Na'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 19
        parameter = 'myokit.V_K'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 20
        parameter = 'myokit.V_L'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 21
        parameter = 'myokit.alpha_m'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 22
        parameter = 'myokit.beta_m'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 23
        parameter = 'myokit.alpha_h'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 24
        parameter = 'myokit.beta_h'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 25
        parameter = 'myokit.alpha_n'
        self.assertTrue(self.model.has_variable(parameter))

        # Parameter 26
        parameter = 'myokit.beta_n'
        self.assertTrue(self.model.has_variable(parameter))



if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
