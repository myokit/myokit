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
import os
import re

import myokit
import myokit.units
import myokit.formats
from myokit.mxml import html2ascii, split
from myokit.formats.mathml import parse_mathml_etree


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

    def model(self, path, bind_time=True):
        """
        Returns a :class:myokit.Model based on the SBML file provided.

        Arguments:

        ``path``
            The path to the SBML file.
        `` bind_time``
            If set to ``True`` (default), a variable called "time" will be
            created and bound to `time`.

        """
        # Get logger
        log = self.logger()

        # Parse xml file
        path = os.path.abspath(os.path.expanduser(path))
        tree = ET.parse(path)
        root = tree.getroot()

        # get SBML namespace
        sbml_version = self._get_sbml_version(root)
        self.ns = self._get_namespaces(sbml_version, log)

        # Get model node
        xmodel = root[0]
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
        x = xmodel.find(self.ns['sbml'] + 'notes')
        if x:
            log.log('Converting <model> notes to ascii')
            model.meta['desc'] = html2ascii(
                ET.tostring(x).decode(), width=75)
            # width = 79 - 4 for tab!

        # Warn about missing functionality
        x = xmodel.find(self.ns['sbml'] + 'listOfCompartments')
        if x:   # pragma: no cover
            log.warn('Compartments are not supported.')
        x = xmodel.find(self.ns['sbml'] + 'listOfSpecies')
        if x:   # pragma: no cover
            log.warn('Species are not supported.')
        x = xmodel.find(self.ns['sbml'] + 'listOfConstraints')
        if x:   # pragma: no cover
            log.warn('Constraints are not supported.')
        x = xmodel.find(self.ns['sbml'] + 'listOfReactions')
        if x:   # pragma: no cover
            log.warn('Reactions are not supported.')
        x = xmodel.find(self.ns['sbml'] + 'listOfEvents')
        if x:   # pragma: no cover
            log.warn('Events are not supported.')

        # Ignore custom functions
        x = xmodel.find(self.ns['sbml'] + 'listOfFunctionDefinitions')
        if x:   # pragma: no cover
            log.warn('Custom math functions are not (yet) implemented.')

        # Parse custom units
        x = xmodel.find(self.ns['sbml'] + 'listOfUnitDefinitions')
        if x:
            self._parse_units(model, comp, x)

        # Add time as independent variable (not explicit in SBML format)
        if bind_time:
            # Add and bind time variable to component
            time = comp.add_variable_allow_renaming('time')
            time.set_binding('time')

            # Set unit and value
            try:
                unit = self.units['time']
            except KeyError:    # pragma: no cover
                unit = myokit.units.s
                log.warn('Unit of time could not be found in file (falling'
                         ' back onto default of seconds.')
            time.set_unit(unit)
            time.set_rhs(0.0)

        # Parse parameters (constants + parameters)
        x = xmodel.find(self.ns['sbml'] + 'listOfParameters')
        if x:
            self._parse_parameters(model, comp, refs, x, self.ns['sbml'])

        # Parse rules (equations)
        x = xmodel.find(self.ns['sbml'] + 'listOfRules')
        if x:
            self._parse_rules(model, comp, refs, x, self.ns['sbml'])

        # Parse extra initial assignments
        x = xmodel.find(self.ns['sbml'] + 'listOfInitialAssignments')
        if x:
            self._parse_initial_assignments(
                model, comp, refs, x)

        # Write warnings to log
        log.log_warnings()

        # Check that valid model was created
        try:
            model.validate()
        except myokit.IntegrityError as e:  # pragma: no cover
            log.log_line()
            log.log('WARNING: Integrity error found in model:')
            log.log(str(e))
            log.log_line()

        # Return finished model
        return model

    def _get_namespaces(self, sbml_version, log):
        """
        Creates a dict of namespaces, based on the given ``sbml_version``
        string.
        """
        supported_sbml_versions = [
            # "{http://www.sbml.org/sbml/level2/version3}",
            # "{http://www.sbml.org/sbml/level2/version4}",
            # "{http://www.sbml.org/sbml/level2/version5}",
            # "{http://www.sbml.org/sbml/level3/version1}",
            "{http://www.sbml.org/sbml/level3/version2}"
        ]
        if sbml_version not in supported_sbml_versions:
            log.warn(
                'The SBML version ' + str(sbml_version) + ' has not been'
                ' tested. The model may not be imported correctly.')

        # Create namespace dict
        ns = dict()
        ns['sbml'] = sbml_version
        ns['mathml'] = "{http://www.w3.org/1998/Math/MathML}"
        return ns

    def _get_sbml_version(self, root):
        """
        Returns the SBML version of the file.
        """
        namespace = split(root.tag)[0]
        # Add brackets, so we can find nodes by namespace + name
        return '{' + namespace + '}'

    def _parse_initial_assignments(self, model, comp, refs, node):
        """
        Parses any initial values specified outside of the rules section.
        """
        ns = self.ns['sbml']
        mathml_ns = self.ns['mathml']

        # Iterate over initial assignments
        for node in node.findall(ns + 'initialAssignment'):
            var = str(node.get('symbol')).strip()
            var = self._convert_name(var)
            if var in comp:
                self.logger().log(
                    'Parsing initial assignment for "' + var + '".')
                var = comp[var]
                # get child
                child = node.find(mathml_ns + 'math')
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
        for node in node.findall(ns + 'parameter'):
            # Create variable
            org_name = str(node.get('id'))
            name = self._convert_name(org_name)
            self.logger().log('Found parameter "' + name + '"')
            if name in comp:    # pragma: no cover
                self.logger().warn(
                    'Skipping duplicate parameter name: ' + str(name))
            else:
                # Create variable
                unit = node.get('units')
                if unit:
                    unit = self._convert_unit(unit)
                value = node.get('value')
                var = comp.add_variable(name)
                var.set_unit(unit)
                var.set_rhs(value)

                # Store reference to variable
                refs[org_name] = refs[name] = var

    def _parse_rules(self, model, comp, refs, parent, ns):
        """
        Parses the rules (equations) in this model
        """
        # get MathML ns
        mathml_ns = self.ns['mathml']
        # Define rules for variables (intermediate expressions)
        for node in parent.findall(ns + 'assignmentRule'):
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

        # Define rates for variables (states)
        for node in parent.findall(ns + 'rateRule'):
            var = node.get('variable')
            if var is not None:
                var = self._convert_name(str(var).strip())
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
                        'Derivative found for unknown parameter: <' + var
                        + '>.')
            else:
                raise SBMLError(   # pragma: no cover
                    'RateRule has no attribute "variable".')

    def _parse_units(self, model, comp, node):
        """
        Parses custom unit definitions, creating a look-up table that can be
        used to convert these units to myokit ones.
        """
        ns = self.ns['sbml']
        for node in node.findall(ns + 'unitDefinition'):
            name = node.get('id')
            self.logger().log('Parsing unit definition for "' + name + '".')
            unit = myokit.units.dimensionless
            units = node.find(ns + 'listOfUnits')
            units = units.findall(ns + 'unit')
            for node2 in units:
                kind = str(node2.get('kind')).strip()
                u2 = self._convert_unit(kind)
                u2 *= float(node2.get('multiplier', default=1.0))
                u2 *= 10 ** float(node2.get('scale', default=0.0))
                u2 **= float(node2.get('exponent', default=1.0))
                unit *= u2
            self.units[name] = unit

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
