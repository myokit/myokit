#
# Imports a model from an SBML file.
# Only partial SBML support (Based on SBML level 3) is provided.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import re

import myokit
import myokit.units
import myokit.formats
from myokit.mxml import html2ascii
from myokit.mxml import dom_child, dom_next
from myokit.formats.mathml import parse_mathml_dom, parse_mathml_etree


info = """
Loads a Model definition from an SBML file. Warning: This importer hasn't been
extensively tested.
"""


class SBMLImporter(myokit.formats.Importer):
    """
    This:class:`Importer <myokit.formats.Importer>` load model definitions
    from files in SBML format.
    """
    def __init__(self):
        super(SBMLImporter, self).__init__()
        self.re_name = re.compile(r'^[a-zA-Z]+[a-zA-Z0-9_]*$')
        self.re_alpha = re.compile(r'[\W]+')
        self.re_white = re.compile(r'[ \t\f\n\r]+')
        self.units = {}
        self.ns = self._define_namespaces()

    def _convert_name(self, name):
        """
        Converts a name to something acceptable to myokit.
        """
        if not self.re_name.match(name):
            org_name = name
            name = self.re_white.sub('_', name)
            name = self.re_alpha.sub('_', name)
            if not self.re_name.match(name):
                name = 'x_' + name
            self.logger().warn(
                'Converting name <' + org_name + '> to <' + name + '>.')
        return name

    def _convert_unit(self, unit):
        """
        Converts an SBML unit to a myokit one using the lookup tables generated
        when parsing the XML file.
        """
        if unit in self.units:
            return self.units[unit]
        elif unit in unit_map:
            return unit_map[unit]
        else:      # pragma: no cover
            raise SBMLError('Unit not recognized: ' + str(unit))

    def info(self):
        return info

    def model(self, path):

        # Get logger
        log = self.logger()

        # Parse xml file
        path = os.path.abspath(os.path.expanduser(path))
        tree = ET.parse(path)
        root = tree.getroot()
        xmodel = root[0]

        # get SBML namespace
        sbml_ns = self._namespace(root)
        if sbml_ns not in self.ns['sbml']:   # pragma: no cover
            log.warn('The SBML version %s has not been tested.'
                     % sbml_ns)

        # Get model node
        if xmodel.get('name'):
            name = str(xmodel.get('name'))
        elif xmodel.get('id'):
            name = str(xmodel.get('id'))
        else:
            name = 'Imported SBML model'

        # Create myokit model
        model = myokit.Model(self._convert_name(name))
        log.log('Reading model "' + model.meta['name'] + '"')

        # Create one giant component to hold all variables
        comp = model.add_component('sbml')

        # Create table of variable names
        refs = {}

        # Handle notes, if given
        x = xmodel.find(sbml_ns + 'notes')
        if x:
            log.log('Converting <model> notes to ascii')
            model.meta['desc'] = html2ascii(ET.tostring(x, encoding='unicode'),
                                            width=75
                                            )
            # width = 79 - 4 for tab!

        # Warn about missing functionality
        x = xmodel.find(sbml_ns + 'listOfCompartments')
        if x:   # pragma: no cover
            log.warn('Compartments are not supported.')
        x = xmodel.find(sbml_ns + 'listOfSpecies')
        if x:   # pragma: no cover
            log.warn('Species are not supported.')
        x = xmodel.find(sbml_ns + 'listOfConstraints')
        if x:   # pragma: no cover
            log.warn('Constraints are not supported.')
        x = xmodel.find(sbml_ns + 'listOfReactions')
        if x:   # pragma: no cover
            log.warn('Reactions are not supported.')
        x = xmodel.find(sbml_ns + 'listOfEvents')
        if x:   # pragma: no cover
            log.warn('Events are not supported.')

        # Ignore custom functions
        x = xmodel.find(sbml_ns + 'listOfFunctionDefinitions')
        if x:   # pragma: no cover
            log.warn('Custom math functions are not (yet) implemented.')

        # Parse custom units
        x = xmodel.find(sbml_ns + 'listOfUnitDefinitions')
        if x:
            self._parse_units(model, comp, x, sbml_ns)

        # Parse parameters (constants + parameters)
        x = xmodel.find(sbml_ns + 'listOfParameters')
        if x:
            self._parse_parameters(model, comp, refs, x, sbml_ns)

        # Parse rules (equations)
        x = xmodel.find(sbml_ns + 'listOfRules')
        if x:
            self._parse_rules(model, comp, refs, x, sbml_ns)

        # Parse extra initial assignments
        x = xmodel.find(sbml_ns + 'listOfInitialAssignments')
        if x:
            self._parse_initial_assignments(model, comp, refs, x, sbml_ns)

        # Write warnings to log
        log.log_warnings()

        # Run model validation, order variables etc
        try:
            model.validate()
        except myokit.IntegrityError as e:
            log.log_line()
            log.log('WARNING: Integrity error found in model:')
            log.log(str(e))
            log.log_line()

        # Return finished model
        return model

    def _define_namespaces(self):
        """
        Defines supported namespaces.
        """
        ns = dict()
        # supported SBML versions
        ns['sbml'] = ["{http://www.sbml.org/sbml/level2/version3}"]

        # xhtml
        ns['xhtml'] = ["{http://www.w3.org/1999/xhtml}"]

        # MathML
        ns['mathml'] = "{http://www.w3.org/1998/Math/MathML}"

        return ns

    def _namespace(self, element):
        m = re.match(r'\{.*\}', element.tag)
        return m.group(0) if m else ''

    def _parse_initial_assignments(self, model, comp, refs, node, ns):
        """
        Parses any initial values specified outside of the rules section.
        """
        nodes = node.findall(ns + 'initialAssignment')
        print(nodes)
        # get mathml ns
        mathml_ns = self.ns['mathml']
        # iterate through initial assignments
        for node in nodes:
            var = str(node.get('symbol')).strip()
            var = self._convert_name(var)
            print(var)
            if var in comp:
                self.logger().log(
                    'Parsing initial assignment for "' + var + '".')
                var = comp[var]
                # get child
                child = node.find(mathml_ns + 'math')
                print('test: ', child)
                if child:
                    expr = parse_mathml_etree(
                        child,
                        lambda x, y: myokit.Name(refs[x]),
                        lambda x, y: myokit.Number(x)
                    )

                    if var.is_state():
                        # Initial value
                        var.set_state_value(expr)
                    else:
                        # Change of value
                        var.set_rhs(expr)
            else:   # pragma: no cover
                raise SBMLError(   # pragma: no cover
                    'Initial assignment found for unknown parameter <' + var
                    + '>.')

    def _parse_parameters(self, model, comp, refs, node, ns):
        """
        Parses parameters
        """
        nodes = node.findall(ns + 'parameter')
        for node in nodes:
            # Create variable
            org_name = str(node.get('id'))
            name = self._convert_name(org_name)
            self.logger().log('Found parameter "' + name + '"')
            if name in comp:    # pragma: no cover
                self.logger().warn(
                    'Skipping duplicate parameter name: ' + str(name))
            else:
                # Create variable
                unit = None
                if node.get('units'):
                    foreign_unit = node.get('units')
                    if foreign_unit:
                        unit = self._convert_unit(foreign_unit)
                value = None
                if node.get('value'):
                    value = node.get('value')
                var = comp.add_variable(name)
                var.set_unit(unit)
                var.set_rhs(value)

                # Store reference to variable
                refs[org_name] = refs[name] = var

    def _parse_rules(self, model, comp, refs, node, ns):
        """
        Parses the rules (equations) in this model
        """
        parent = node
        # Create variables with assignment rules (all except derivatives)
        nodes = parent.findall(ns + 'assignmentRule')
        # get MathML ns
        mathml_ns = self.ns['mathml']
        # iterate through assignment rules
        for node in nodes:
            var = self._convert_name(
                str(node.get('variable')).strip())
            if var in comp:
                self.logger().log(
                    'Parsing assignment rule for <' + str(var) + '>.')
                var = comp[var]
                # get child
                child = node.find(mathml_ns + 'math')
                # add expression to model
                if child:
                    var.set_rhs(parse_mathml_etree(
                        child,
                        lambda x, y: myokit.Name(refs[x]),
                        lambda x, y: myokit.Number(x)
                    )
                    )
            else:
                raise SBMLError(   # pragma: no cover
                    'Assignment found for unknown parameter: "' + var + '".')

        # Create variables with rate rules (states)
        nodes = parent.findall(ns + 'rateRule')
        for node in nodes:
            var = self._convert_name(
                str(node.get('variable')).strip())
            if var in comp:
                self.logger().log('Parsing rate rule for <' + var + '>.')
                var = comp[var]
                ini = var.rhs()
                ini = ini.eval() if ini else 0
                var.promote(ini)
                # get child
                child = node.find(mathml_ns + 'math')
                # add expression to model
                if child:
                    var.set_rhs(parse_mathml_etree(
                        child,
                        lambda x, y: myokit.Name(refs[x]),
                        lambda x, y: myokit.Number(x)
                    )
                    )
            else:
                raise SBMLError(   # pragma: no cover
                    'Derivative found for unknown parameter: <' + var + '>.')

    def _parse_units(self, model, comp, node, ns):
        """
        Parses custom unit definitions, creating a look-up table that can be
        used to convert these units to myokit ones.
        """
        nodes = node.findall(ns + 'unitDefinition')
        for node in nodes:
            name = node.get('id')
            self.logger().log('Parsing unit definition for "' + name + '".')
            unit = myokit.units.dimensionless
            units = node.find(ns + 'listOfUnits')
            units = units.findall(ns + 'unit')
            for node2 in units:
                kind = str(node2.get('kind')).strip()
                u2 = self._convert_unit(kind)
                if node2.get('multiplier'):
                    m = float(node2.get('multiplier'))
                else:
                    m = 1.0
                if node2.get('scale'):
                    m *= 10 ** float(node2.get('scale'))
                u2 *= m
                if node2.get('exponent'):
                    u2 **= float(node2.get('exponent'))
                unit *= u2
            self.units[name] = unit

    def supports_model(self):
        return True


class SBMLImporterOld(myokit.formats.Importer):
    """
    This:class:`Importer <myokit.formats.Importer>` load model definitions
    from files in SBML format.
    """
    def __init__(self):
        super(SBMLImporterOld, self).__init__()
        self.re_name = re.compile(r'^[a-zA-Z]+[a-zA-Z0-9_]*$')
        self.re_alpha = re.compile(r'[\W]+')
        self.re_white = re.compile(r'[ \t\f\n\r]+')
        self.units = {}

    def _convert_name(self, name):
        """
        Converts a name to something acceptable to myokit.
        """
        if not self.re_name.match(name):
            org_name = name
            name = self.re_white.sub('_', name)
            name = self.re_alpha.sub('_', name)
            if not self.re_name.match(name):
                name = 'x_' + name
            self.logger().warn(
                'Converting name <' + org_name + '> to <' + name + '>.')
        return name

    def _convert_unit(self, unit):
        """
        Converts an SBML unit to a myokit one using the lookup tables generated
        when parsing the XML file.
        """
        if unit in self.units:
            return self.units[unit]
        elif unit in unit_map:
            return unit_map[unit]
        else:      # pragma: no cover
            raise SBMLError('Unit not recognized: ' + str(unit))

    def info(self):
        return info

    def model(self, path):

        # Get logger
        log = self.logger()

        # Parse xml file
        path = os.path.abspath(os.path.expanduser(path))
        dom = xml.dom.minidom.parse(path)
        xmodel = dom.getElementsByTagName('model')[0]

        # Get model node
        if xmodel.getAttribute('name'):
            name = str(xmodel.getAttribute('name'))
        elif xmodel.getAttribute('id'):
            name = str(xmodel.getAttribute('id'))
        else:
            name = 'Imported SBML model'

        # Create myokit model
        model = myokit.Model(self._convert_name(name))
        log.log('Reading model "' + model.meta['name'] + '"')

        # Create one giant component to hold all variables
        comp = model.add_component('sbml')

        # Create table of variable names
        refs = {}

        # Handle notes, if given
        x = dom_child(xmodel, 'notes')
        if x:
            log.log('Converting <model> notes to ascii')
            model.meta['desc'] = html2ascii(x.toxml(), width=75)
            # width = 79 - 4 for tab!

        # Warn about missing functionality
        x = dom_child(xmodel, 'listOfCompartments')
        if x:   # pragma: no cover
            log.warn('Compartments are not supported.')
        x = dom_child(xmodel, 'listOfSpecies')
        if x:   # pragma: no cover
            log.warn('Species are not supported.')
        x = dom_child(xmodel, 'listOfConstraints')
        if x:   # pragma: no cover
            log.warn('Constraints are not supported.')
        x = dom_child(xmodel, 'listOfReactions')
        if x:   # pragma: no cover
            log.warn('Reactions are not supported.')
        x = dom_child(xmodel, 'listOfEvents')
        if x:   # pragma: no cover
            log.warn('Events are not supported.')

        # Ignore custom functions
        x = dom_child(xmodel, 'listOfFunctionDefinitions')
        if x:   # pragma: no cover
            log.warn('Custom math functions are not (yet) implemented.')

        # Parse custom units
        x = dom_child(xmodel, 'listOfUnitDefinitions')
        if x:
            self._parse_units(model, comp, x)

        # Parse parameters (constants + parameters)
        x = dom_child(xmodel, 'listOfParameters')
        if x:
            self._parse_parameters(model, comp, refs, x)

        # Parse rules (equations)
        x = dom_child(xmodel, 'listOfRules')
        if x:
            self._parse_rules(model, comp, refs, x)

        # Parse extra initial assignments
        x = dom_child(xmodel, 'listOfInitialAssignments')
        if x:
            self._parse_initial_assignments(model, comp, refs, x)

        # Write warnings to log
        log.log_warnings()

        # Run model validation, order variables etc
        try:
            model.validate()
        except myokit.IntegrityError as e:
            log.log_line()
            log.log('WARNING: Integrity error found in model:')
            log.log(str(e))
            log.log_line()

        # Return finished model
        return model

    def _parse_initial_assignments(self, model, comp, refs, node):
        """
        Parses any initial values specified outside of the rules section.
        """
        node = dom_child(node, 'initialAssignment')
        while node:
            var = str(node.getAttribute('symbol')).strip()
            var = self._convert_name(var)
            if var in comp:
                self.logger().log(
                    'Parsing initial assignment for "' + var + '".')
                var = comp[var]
                expr = parse_mathml_dom(
                    dom_child(node, 'math'), refs, self.logger())

                if var.is_state():
                    # Initial value
                    var.set_state_value(expr)
                else:
                    # Change of value
                    var.set_rhs(expr)
            else:   # pragma: no cover
                raise SBMLError(   # pragma: no cover
                    'Initial assignment found for unknown parameter <' + var
                    + '>.')

            node = dom_next(node, 'initialAssignment')

    def _parse_parameters(self, model, comp, refs, node):
        """
        Parses parameters
        """
        node = dom_child(node, 'parameter')
        while node:
            # Create variable
            org_name = str(node.getAttribute('id'))
            name = self._convert_name(org_name)
            self.logger().log('Found parameter "' + name + '"')
            if name in comp:    # pragma: no cover
                self.logger().warn(
                    'Skipping duplicate parameter name: ' + str(name))
            else:
                # Create variable
                unit = None
                if node.hasAttribute('units'):
                    foreign_unit = node.getAttribute('units')
                    if foreign_unit:
                        unit = self._convert_unit(foreign_unit)
                value = None
                if node.hasAttribute('value'):
                    value = node.getAttribute('value')
                var = comp.add_variable(name)
                var.set_unit(unit)
                var.set_rhs(value)

                # Store reference to variable
                refs[org_name] = refs[name] = var

            node = dom_next(node, 'parameter')

    def _parse_rules(self, model, comp, refs, node):
        """
        Parses the rules (equations) in this model
        """
        parent = node
        # Create variables with assignment rules (all except derivatives)
        node = dom_child(parent, 'assignmentRule')
        while node:
            var = self._convert_name(
                str(node.getAttribute('variable')).strip())
            if var in comp:
                self.logger().log(
                    'Parsing assignment rule for <' + str(var) + '>.')
                var = comp[var]
                var.set_rhs(parse_mathml_dom(
                    dom_child(node, 'math'), refs, self.logger()))
            else:
                raise SBMLError(   # pragma: no cover
                    'Assignment found for unknown parameter: "' + var + '".')
            node = dom_next(node, 'assignmentRule')

        # Create variables with rate rules (states)
        node = dom_child(parent, 'rateRule')
        while node:
            var = self._convert_name(
                str(node.getAttribute('variable')).strip())
            if var in comp:
                self.logger().log('Parsing rate rule for <' + var + '>.')
                var = comp[var]
                ini = var.rhs()
                ini = ini.eval() if ini else 0
                var.promote(ini)
                var.set_rhs(parse_mathml_dom(
                    dom_child(node, 'math'), refs, self.logger()))
            else:
                raise SBMLError(   # pragma: no cover
                    'Derivative found for unknown parameter: <' + var + '>.')
            node = dom_next(node, 'rateRule')

    def _parse_units(self, model, comp, node):
        """
        Parses custom unit definitions, creating a look-up table that can be
        used to convert these units to myokit ones.
        """
        node = dom_child(node, 'unitDefinition')
        while node:
            name = node.getAttribute('id')
            self.logger().log('Parsing unit definition for "' + name + '".')
            unit = myokit.units.dimensionless
            node2 = dom_child(node, 'listOfUnits')
            node2 = dom_child(node2, 'unit')
            while node2:
                kind = str(node2.getAttribute('kind')).strip()
                u2 = self._convert_unit(kind)
                if node2.hasAttribute('multiplier'):
                    m = float(node2.getAttribute('multiplier'))
                else:
                    m = 1.0
                if node2.hasAttribute('scale'):
                    m *= 10 ** float(node2.getAttribute('scale'))
                u2 *= m
                if node2.hasAttribute('exponent'):
                    u2 **= float(node2.getAttribute('exponent'))
                unit *= u2
                node2 = dom_next(node2, 'unit')
            self.units[name] = unit
            node = dom_next(node, 'unitDefinition')

    def supports_model(self):
        return True


class SBMLError(myokit.ImportError):
    """
    Thrown if an error occurs when importing SBML
    """


unit_map = {
    'dimensionless': myokit.units.dimensionless,
    'ampere': myokit.units.A,
    'farad': myokit.units.F,
    'katal': myokit.units.kat,
    'lux': myokit.units.lux,
    'pascal': myokit.units.Pa,
    'tesla': myokit.units.T,
    'becquerel': myokit.units.Bq,
    'gram': myokit.units.g,
    'kelvin': myokit.units.K,
    'meter': myokit.units.m,
    'radian': myokit.units.rad,
    'volt': myokit.units.V,
    'candela': myokit.units.cd,
    'gray': myokit.units.Gy,
    'kilogram': myokit.units.kg,
    'metre': myokit.units.m,
    'second': myokit.units.s,
    'watt': myokit.units.W,
    'celsius': myokit.units.C,
    'henry': myokit.units.H,
    'liter': myokit.units.L,
    'mole': myokit.units.mol,
    'siemens': myokit.units.S,
    'weber': myokit.units.Wb,
    'coulomb': myokit.units.C,
    'hertz': myokit.units.Hz,
    'litre': myokit.units.L,
    'newton': myokit.units.N,
    'sievert': myokit.units.Sv,
    'joule': myokit.units.J,
    'lumen': myokit.units.lm,
    'ohm': myokit.units.R,
    'steradian': myokit.units.sr,
}
