#
# Converts SBML to Myokit expressions, using an ElementTree implementation.
#
# Only partial SBML support (based on SBML level 3 version 2) is provided.
# The SBML file format specifications can be found here
# http://sbml.org/Documents/Specifications.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import re
import warnings

from lxml import etree

import myokit
import myokit.units
import myokit.formats
import myokit.formats.html
import myokit.formats.mathml
import myokit.formats.sbml
import myokit.formats.xml


# Namespaces
NS_MATHML = 'http://www.w3.org/1998/Math/MathML'
NS_SBML_3_2 = 'http://www.sbml.org/sbml/level3/version2/core'


# Regex for id checking
_re_id = re.compile(r'^[a-zA-Z_]+[a-zA-Z0-9_]*$')


def _parse_mathml(expr, name_generator):
    """
    Parses the MathML expression ``expr`` and wraps any errors in an SBMLError.
    """
    def name(x, y):
        try:
            return name_generator(x, y)
        except KeyError:
            raise myokit.formats.sbml.SBMLError(
                'Unknown or inaccessible symbol in MathML: "' + str(x) + '".')

    try:
        return myokit.formats.mathml.parse_mathml_etree(
            expr, name, lambda x, y: myokit.Number(x))
    except myokit.formats.mathml.MathMLError as e:
        raise myokit.formats.sbml.SBMLError(
            'Unable to parse MathML: ' + str(e))

    # Note: In any place we parse mathematics, we could also check that
    # there's nothing after the mathematics. E.g.
    #   <math xmlns="..">
    #    <cn>1</cn>
    #    <cn>2</cn>
    #   </math>
    # is currently allowed because only the first statement is read.
    # But for now we're being lenient.


class SBMLParsingError(myokit.ImportError):
    """
    Thrown if an error occurs when parsing SBML.

    The argument ``element`` can be used to pass in an element that caused the
    error.
    """
    def __init__(self, message, element=None):
        if element is not None:
            try:
                line = str(element.sourceline)
                message = 'Error on line ' + line + '. ' + message
            except AttributeError:  # pragma: no cover
                pass
        super(SBMLParsingError, self).__init__(message)


class SBMLParser(object):
    """
    Parses SBML models, creating an SBML Model structure that can be converted
    to a :class:`myokit.Model` object.

    Support notes:

    - SBML older than Level 2 version 1 is unlikely to work.
    - Algebraic rules are not supported.
    - Constraints are not supported.
    - Events are not supported.
    - Function definitions are not supported.
    - Local parameters in reactions are not supported.
    - Units "celsius" are not supported.
    - Since SBML does not support units in equations, variable units will be
      set, but RHS units will not.

    """

    def _check_required_attributes(self, element, *attributes):
        """
        Checks that an ``elementtree`` element has all the required attributes.
        """
        for attribute in attributes:
            if element.get(attribute) is None:
                raise SBMLParsingError(
                    'Element ' + self._tag(element) + ' is missing required'
                    ' attribute "' + str(attribute) + '".', element)

    def parse_file(self, path):
        """
        Parses the SBML file at ``path`` and returns a :class:`myokit.Model`.
        """
        # Read file
        try:
            parser = etree.XMLParser(remove_comments=True)
            tree = etree.parse(path, parser=parser)
        except Exception as e:
            raise SBMLParsingError('Unable to parse XML: ' + str(e))

        # Parse content
        return self.parse(tree.getroot())

    def parse_string(self, text):
        """
        Parses the SBML XML in the string ``text`` and returns a
        :class:`myokit.Model`.
        """
        # Read string
        try:
            root = etree.fromstring(text)
        except Exception as e:
            raise SBMLParsingError('Unable to parse XML: ' + str(e))

        # Parse content
        return self.parse(root)

    def parse(self, element):
        """
        Parses an SBML document rooted in the given ``ElementTree`` element and
        returns a :class:`myokit.Model`.
        """
        # Supported namespaces
        # Other namespaces are allowed, but might not work.
        supported = (
            NS_SBML_3_2,
        )

        # Check whether document declares a supported namespace
        self._ns = myokit.formats.xml.split(element.tag)[0]
        try:
            if self._ns not in supported:
                warnings.warn(
                    'Unknown SBML namespace ' + str(self._ns) + '. This'
                    ' version of SBML may not be supported.')

            # Get model and parse
            model = element.find(self._path('model'))
            if model is None:
                raise SBMLParsingError('Model element not found.', element)
            return self._parse_model(model)

        finally:
            # Remove all references to temporary state
            del self._ns

    def _parse_compartment(self, element, model):
        """Parses a ``compartment`` element."""

        # Check required attributes
        self._check_required_attributes(element, 'id')
        # The attribute 'constant' is also required in level 3, but optional in
        # level 2 (default true). If constant is false then the compartment's
        # size can be changed.

        # Note: Any place we check required attributes, we could also check for
        # allowed attributes (e.g. errors for unrecognised ones). Bit tricky
        # for multiple SBML versions. For now we're being lenient.

        sid = element.get('id')
        try:
            # Create compartment
            compartment = model.add_compartment(sid)

            # Get units, if given
            units = element.get('units')
            if units is not None:
                try:
                    units = model.unit(units)
                except myokit.formats.sbml.SBMLError:
                    raise SBMLParsingError(
                        'Unknown units "' + units + '".', element)
                compartment.set_size_units(units)

            # Get spatial dimensions, if given
            dim = element.get('spatialDimensions')
            if dim is not None:
                try:
                    dim = float(dim)
                except ValueError:
                    raise SBMLParsingError(
                        'Unable to convert spatial dimensions value "'
                        + str(dim) + '" to float.', element)
                compartment.set_spatial_dimensions(dim)

            # Get compartment size, if set
            size = element.get('size')
            if size is not None:
                try:
                    size = float(size)
                except ValueError:
                    raise SBMLParsingError(
                        'Unable to convert size "' + str(size) + '" to float.',
                        element)

                # Ignore units in RHS
                compartment.set_initial_value(myokit.Number(size))

        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Unable to parse compartment "' + sid + '": ' + str(e),
                element)

    def _parse_initial_assignment(self, element, model):
        """Parses an initial assignment."""

        # Check required attributes
        self._check_required_attributes(element, 'symbol')

        # Check that symbol refers to an assignable
        var = element.get('symbol')
        try:
            var = model.assignable(var)
        except KeyError:
            raise SBMLParsingError(
                'Unable to parse rule: The given SId "' + str(var) + '" does'
                ' not refer to a Compartment, Species, SpeciesReference, or'
                ' Parameter in this model.')

        try:
            # Find mathematics
            expr = element.find('{' + NS_MATHML + '}math')
            if expr is None:
                # This is allowed, so that SBML extensions can do mysterious
                # things.
                warnings.warn(
                    'Initial assignment does not define any mathematics')
                return

            # Parse rule and apply
            var.set_initial_value(_parse_mathml(
                expr,
                lambda x, y: myokit.Name(model.assignable_or_csymbol(x)),
            ))

        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Unable to parse initial assignment: ' + str(e), element)

    def _parse_kinetic_law(self, element, model, reaction):
        """
        Parses the ``kinetic_law`` element used in reactions and returns the
        resulting :class:`myokit.Expression``.

        Returns ``None`` if no expression is found.
        """

        # Local parameters are not supported
        x = element.find(self._path('listOfLocalParameters', 'localParameter'))
        if x is not None:
            raise SBMLParsingError('Local parameters are not supported.', x)

        # Kinetic law is not allowed use species unless they're defined in the
        # reaction.
        def name(x, y):
            obj = model.assignable_or_csymbol(x)
            if isinstance(obj, myokit.formats.sbml.Species):
                obj = reaction.species(x)
            return myokit.Name(obj)

        # Find and parse expression
        expr = element.find('{' + NS_MATHML + '}math')
        if expr is None:
            return None
        try:
            return _parse_mathml(expr, name)
        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Unable to parse kinetic law: ' + str(e), element)

    def _parse_model(self, element):
        """Parses a ``model`` element in an SBML document."""

        # Retrieve or create a model name.
        # SBML Models can have an optional name attribute (user friendly name)
        # or an optional id attribute (not necessarily user friendly) or can
        # have no name at all.
        name = element.get('name')
        if name is None:
            name = element.get('id')
        if name is None:
            name = 'Imported SBML model'

        # Create SBML model
        model = myokit.formats.sbml.Model(name)

        # Algebraic rules are not supported
        x = element.find(self._path('listOfRules', 'algebraicRule'))
        if x is not None:
            raise SBMLParsingError(
                'Algebraic rules are not supported.', x)

        # Constraints are not supported, but will be ignored
        x = element.find(self._path('listOfConstraints', 'constraint'))
        if x is not None:
            warnings.warn('Ignoring SBML constraints.')

        # Events are not supported, but will be ignored
        x = element.find(self._path('listOfEvents', 'event'))
        if x is not None:
            warnings.warn('Ignoring SBML events.')

        # Function definitions are not supported.
        x = element.find(self._path(
            'listOfFunctionDefinitions', 'functionDefinition'))
        if x is not None:
            raise SBMLParsingError(
                'Function definitions are not supported.', x)

        # Parse notes element (converts HTML to plain text)
        notes = element.find(self._path('notes'))
        if notes is not None:
            self._parse_notes(notes, model)

        # Parse unit definitions
        for unit in element.findall(self._path(
                'listOfUnitDefinitions', 'unitDefinition')):
            self._parse_unit_definition(unit, model)

        # Parse model unit attributes
        try:
            # Default units for compartment sizes
            units = element.get('lengthUnits')
            if units is not None:
                model.set_length_units(model.unit(units))
            units = element.get('areaUnits')
            if units is not None:
                model.set_area_units(model.unit(units))
            units = element.get('volumeUnits')
            if units is not None:
                model.set_volume_units(model.unit(units))

            # Default units for species amounts (not concentrations)
            units = element.get('substanceUnits')
            if units is not None:
                model.set_substance_units(model.unit(units))

            # Default units for reactions and rates.
            # The KineticLaw equations are in units of extentUnits / timeUnits.
            units = element.get('extentUnits')
            if units is not None:
                model.set_extent_units(model.unit(units))
            units = element.get('timeUnits')
            if units is not None:
                model.set_time_units(model.unit(units))

        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Error parsing model element: ' + str(e), element)

        # Parse parameters
        for parameter in element.findall(self._path(
                'listOfParameters', 'parameter')):
            self._parse_parameter(parameter, model)

        # Set global conversion factor, if provided (must refer to a parameter)
        factor = element.get('conversionFactor')
        if factor is not None:
            try:
                factor = model.parameter(factor)
            except KeyError:
                raise SBMLParsingError(
                    'Model conversion factor "' + str(factor) + '" does not'
                    ' refer to a parameter SId.', element)
            model.set_conversion_factor(factor)

        # Parse compartments
        for compartment in element.findall(self._path(
                'listOfCompartments', 'compartment')):
            self._parse_compartment(compartment, model)

        # Parse species
        for species in element.findall(self._path('listOfSpecies', 'species')):
            self._parse_species(species, model)

        # Parse reactions
        for reaction in element.findall(self._path(
                'listOfReactions', 'reaction')):
            self._parse_reaction(reaction, model)

        # Parse initial assignments
        for assignment in element.findall(self._path(
                'listOfInitialAssignments', 'initialAssignment')):
            self._parse_initial_assignment(assignment, model)

        # Parse assignment rules
        for rule in element.findall(self._path(
                'listOfRules', 'assignmentRule')):
            self._parse_rule(rule, model, False)

        # Parse rate rules
        for rule in element.findall(self._path('listOfRules', 'rateRule')):
            self._parse_rule(rule, model, True)

        return model

    def _parse_notes(self, element, model):
        """Parses a model's ``notes`` element, converting it to plain text."""

        notes = etree.tostring(element).decode()
        notes = myokit.formats.html.html2ascii(notes, width=75)
        if notes:
            model.set_notes(notes)

    def _parse_parameter(self, element, model):
        """Parses a ``parameter`` element."""

        # Check required attributes
        self._check_required_attributes(element, 'id')
        # The attribute 'constant' is also required in level 3, but optional in
        # level 2 (default false)

        # Create
        try:
            parameter = model.add_parameter(element.get('id'))

            # Get optional units
            unit = element.get('units')
            if unit is not None:
                try:
                    unit = model.unit(unit)
                except myokit.formats.sbml.SBMLError:
                    raise SBMLParsingError(
                        'Unknown units "' + unit + '".', element)
                parameter.set_units(unit)

            # Get optional initial value
            value = element.get('value')
            if value is not None:
                try:
                    value = float(value)
                except ValueError:
                    raise SBMLParsingError(
                        'Unable to convert parameter value "' + str(value)
                        + '" to float.', element)

                # Ignore unit
                parameter.set_initial_value(myokit.Number(value))

        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Unable to parse ' + self._tag(element) + ': ' + str(e),
                element)

    def _parse_reaction(self, element, model):
        """Parses a ``reaction`` element."""

        # Check required attributes
        self._check_required_attributes(element, 'id')
        # The attribute 'reversible' is also required, but doesn't affect the
        # maths, so we ignore it here.
        # The attribute 'compartment' is not required, and doesn't affect the
        # maths, so we ignore it here.

        # The 'fast' attribute was removed in L3V2 and is not supported here
        if element.get('fast') == 'true':
            raise SBMLParsingError(
                'Reactions with fast="true" are not supported.', element)

        # Create
        try:
            reaction = model.add_reaction(element.get('id'))
        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Unable to parse ' + self._tag(element) + ': ' + str(e),
                element)

        # Add reactants, products, modifiers
        have_reactant_or_product = False
        for x in element.findall(self._path(
                'listOfReactants', 'speciesReference')):
            self._parse_species_reference(
                x, model, reaction,
                myokit.formats.sbml.SpeciesReference.REACTANT)
            have_reactant_or_product = True

        for x in element.findall(self._path(
                'listOfProducts', 'speciesReference')):
            self._parse_species_reference(
                x, model, reaction,
                myokit.formats.sbml.SpeciesReference.PRODUCT)
            have_reactant_or_product = True

        for x in element.findall(self._path(
                'listOfModifiers', 'modifierSpeciesReference')):
            self._parse_species_reference(
                x, model, reaction,
                myokit.formats.sbml.SpeciesReference.MODIFIER)

        # Raise error if neither reactants nor products is populated
        if not have_reactant_or_product:
            raise SBMLParsingError(
                'Reaction must have at least one reactant or product.',
                element)

        # Parse kinetic law
        kinetic_law = element.find(self._path('kineticLaw'))
        if kinetic_law is not None:
            kinetic_law = self._parse_kinetic_law(kinetic_law, model, reaction)
        if kinetic_law is None:
            warnings.warn(
                'No kinetic law set for reaction "' + reaction.sid() + '".')
        else:
            reaction.set_kinetic_law(kinetic_law)

    def _parse_rule(self, element, model, rate=False):
        """Parses an assignment or rate rule."""

        # Check required attributes
        self._check_required_attributes(element, 'variable')

        # Check that variable refers to an assignable
        var = element.get('variable')
        try:
            var = model.assignable(var)
        except KeyError:
            raise SBMLParsingError(
                'Unable to parse rule: The given SId "' + str(var) + '" does'
                ' not refer to a Compartment, Species, SpeciesReference, or'
                ' Parameter in this model.')

        try:
            # Check that this assignable can be changed with assignment rules
            if isinstance(var, myokit.formats.sbml.Species):
                if not var.is_boundary():
                    raise SBMLParsingError(
                        'Assignment or rate rule set for species that is'
                        ' created or destroyed in a reaction.', element)
            # TODO: Could also gather 'constant' attributes for all, and check
            # here. But maybe we're not all that interested in validation...

            # Find mathematics
            expr = element.find('{' + NS_MATHML + '}math')
            if expr is None:
                # This is allowed, so that SBML extensions can do mysterious
                # things.
                warnings.warn('Rule does not define any mathematics')
                return

            # Parse rule and apply
            var.set_value(_parse_mathml(
                expr,
                lambda x, y: myokit.Name(model.assignable_or_csymbol(x)),
            ), rate)

        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError('Unable to parse rule: ' + str(e), element)

    def _parse_species(self, element, model):
        """
        Adds species to references compartment in model.
        """
        # Check required attributes (note: constant is also required in L3)
        self._check_required_attributes(element, 'id', 'compartment')
        # The attributes 'hasOnlySubstaneUnits', 'boundaryCondition', and
        # 'constant' are required in level 3, but optional in level 2 (default
        # is false for all three).

        # Check if it's an amount or a concentration
        is_amount = element.get('hasOnlySubstanceUnits', 'false') == 'true'

        # Check if constant, and if at a reaction boundary
        is_constant = element.get('constant', 'false') == 'true'
        is_boundary = element.get('boundaryCondition', 'false') == 'true'

        # Note: In lines like the above we could raise an error if the value
        # isn't 'true' or false', but for now we're being lenient.

        # Get compartment
        compartment = element.get('compartment')
        try:
            compartment = model.compartment(compartment)
        except KeyError:
            raise SBMLParsingError(
                'Unknown compartment "' + compartment + '"', element)

        # Create
        try:
            species = model.add_species(
                compartment,
                element.get('id'),
                is_amount,
                is_constant,
                is_boundary)

            # Set units, if provided
            units = element.get('substanceUnits')
            if units is not None:
                try:
                    units = model.unit(units)
                except myokit.formats.sbml.SBMLError:
                    raise SBMLParsingError(
                        'Unknown units "' + units + '"', element)

                # Set substance units, not concentration units
                species.set_substance_units(units)

            # Check that not both initialAmount and initialConcentration are
            # provided
            if (element.get('initialAmount') is not None) and (
                    element.get('initialConcentration') is not None):
                raise SBMLParsingError(
                    'Species cannot set both an initialAmount and an'
                    ' initialConcentration.')

            # Get initial amount
            value = element.get('initialAmount')

            # Indicate whether units of initial value are in amount
            value_in_amount = True

            # If initial amount is not provided, get initial concentration
            if value is None:
                value = element.get('initialConcentration')

                # Indicate whether units of initial value are correct
                value_in_amount = False

            # Set initial value
            if value is not None:
                try:
                    value = float(value)
                except ValueError:
                    raise SBMLParsingError(
                        'Unable to convert initial species value to float "'
                        + str(value) + '".', element)

                # Ignore units in equations
                species.set_initial_value(
                    myokit.Number(value), value_in_amount)

            # Set conversion factor if provided (must refer to a parameter)
            factor = element.get('conversionFactor')
            if factor is not None:
                try:
                    factor = model.parameter(factor)
                except KeyError:
                    raise SBMLParsingError(
                        'Unknown parameter "' + str(factor) + '" set as'
                        ' conversion factor.', element)
                species.set_conversion_factor(factor)

        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Unable to parse ' + self._tag(element) + ': ' + str(e),
                element)

    def _parse_species_reference(self, element, model, reaction, ref_type):
        """Parses a ``speciesReference`` element inside a reaction."""

        # Check required attributes
        # Note: Level 3 also has a required attribute 'constant'
        self._check_required_attributes(element, 'species')

        # Find species
        species = element.get('species')
        try:
            species = model.species(species)
        except KeyError:
            raise SBMLParsingError(
                'Reference to unknown species "' + species + '"', element)

        # Get optional SId
        sid = element.get('id')

        try:
            # Create
            if ref_type == myokit.formats.sbml.SpeciesReference.REACTANT:
                reference = reaction.add_reactant(species, sid)
            elif ref_type == myokit.formats.sbml.SpeciesReference.PRODUCT:
                reference = reaction.add_product(species, sid)
            else:
                # Modifier references require no further parsing
                return reaction.add_modifier(species, sid)

            # Get optional stoichiometry
            stoichiometry = element.get('stoichiometry')
            if stoichiometry is not None:
                try:
                    stoichiometry = float(stoichiometry)
                except ValueError:
                    raise SBMLParsingError(
                        'Unable to convert stoichiometry value "'
                        + str(stoichiometry) + '" to float.', element)
                reference.set_initial_value(myokit.Number(stoichiometry))

        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Unable to parse species reference: ' + str(e), element)

        return reference

    def _parse_unit_definition(self, element, model):
        """Parses a ``unitDefinition`` element."""

        # Check required attributes
        self._check_required_attributes(element, 'id')

        # Parse units and combine
        myokit_unit = myokit.units.dimensionless
        for unit in element.findall(self._path('listOfUnits', 'unit')):
            myokit_unit *= self._parse_unit(unit, model)

        # Store the unit
        sid = element.get('id')
        try:
            model.add_unit(sid, myokit_unit)
        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Unable to parse unit definition for "' + sid + '": ' + str(e),
                element)

    def _parse_unit(self, element, model):
        """Parses a ``unit`` element and returns a :class:`myokit.Unit`."""

        # Check required attributes
        self._check_required_attributes(element, 'kind')
        # The attributes 'multiplier', 'scale', and 'exponent' are required in
        # level 3, but are optional in level 2.

        # Get base unit (must be a predefined type)
        try:
            unit = model.base_unit(element.get('kind'))
        except myokit.formats.sbml.SBMLError as e:
            raise SBMLParsingError(
                'Unable to parse unit kind: ' + str(e), element)

        # Parse remaining parts and return
        try:
            unit *= float(element.get('multiplier', default=1))
            unit *= 10 ** float(element.get('scale', default=0))
            unit **= float(element.get('exponent', default=1))
        except ValueError:
            raise SBMLParsingError('Unable to parse unit attributes', element)

        return unit

    def _path(self, *tags):
        """
        Returns a string created by prepending the namespace to each tag and
        adding forward slashes to separate.

        If a tag starts with a forward slash or period, no namespace will be
        prepended.
        """
        treated = []
        for tag in tags:
            if tag[:1] not in './':
                tag = '{' + self._ns + '}' + tag
            tag = tag.rstrip('/')
            treated.append(tag)
        return '/'.join(treated)

    def _tag(self, element):
        """
        Returns an element's name, but changes the syntax from ``{...}tag`` to
        ``sbml:tag`` for SBML elements.
        """
        _, el = myokit.formats.xml.split(element.tag)

        # Replace known namespaces
        tag = 'sbml:' + el

        # Add id if known
        sid = element.get('id', element.get('unitsid'))
        if sid is not None:
            tag += '[@id=' + str(sid) + ']'

        return tag

