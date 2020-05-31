#
# Converts SBML to Myokit expressions, using an ElementTree implementation.
#
# Only partial SBML support (Based on SBML level 3 version 2) is provided.
# The SBML file format specifications can be found here
# http://sbml.org/Documents/Specifications.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import re
import xml.etree.ElementTree as ET

import myokit
import myokit.units
import myokit.formats
from myokit.mxml import html2ascii, split
from myokit.formats.mathml import parse_mathml_etree

MATHML_NS = 'http://www.w3.org/1998/Math/MathML'


class SBMLError(myokit.ImportError):
    """
    Thrown if an error occurs when importing SBML.
    """
    pass


class SBMLParser(object):
    """
    Parses SBML models into :class:`myokit.Model` objects.

    General notes:

    - Component and variable names are created from ``id`` attributes, and
      ``name`` attributes are ignored. (Names are not typically required,
      while ids are; ids are almost myokit identifiers already (except that
      they can start with an underscore); and ids are guaranteed to be
      unique).

    Support notes:

    - SBML older than Level 2 version 1 is unlikely to work.
    - Units "celsius" are not supported.
    - Events are not supported.
    - Function definitions are not supported.

    """
    def __init__(self):
        # Regexes for id checking
        self.re_id = re.compile(r'^[a-zA-Z_]+[a-zA-Z0-9_]*$')

    def parse_file(self, path, logger=None):
        """
        Parses the SBML file at ``path`` and returns a :class:`myokit.Model`.

        An optional :class:`myokit.formats.TextLogger` may be passed in to log
        warnings to.
        """
        # Read file
        try:
            tree = ET.parse(path)
        except Exception as e:
            raise SBMLError('Unable to parse XML: ' + str(e))

        # Parse content
        return self.parse(tree.getroot(), logger)

    def parse_string(self, text, logger=None):
        """
        Parses the SBML XML in the string ``text`` and returns a
        :class:`myokit.Model`.

        An optional :class:`myokit.formats.TextLogger` may be passed in to log
        warnings to.
        """
        # Read string
        try:
            root = ET.fromstring(text)
        except Exception as e:
            raise SBMLError('Unable to parse XML: ' + str(e))

        # Parse content
        return self.parse(root, logger)

    def parse(self, root, logger=None):
        """
        Parses an SBML document rooted in the given ``ElementTree`` element and
        returns a :class:`myokit.Model`.

        An optional :class:`myokit.formats.TextLogger` may be passed in to log
        warnings to.
        """
        try:
            return self._parse_document(root, logger)
        except SBMLError as e:
            raise SBMLError(str(e))
        except myokit.formats.mathml.MathMLError as e:
            raise SBMLError(str(e))
        finally:
            # Remove all references to temporary state
            del(self._log)
            del(self._ns)

    def _parse_document(self, element, logger=None):
        """
        Parses an SBML document.
        """
        self._log = myokit.formats.TextLogger() if logger is None else logger

        # Supported namespaces
        # Other namespaces are allowed, but might not work.
        supported = (
            'http://www.sbml.org/sbml/level3/version2/core',
        )

        # Check whether document declares a supported namespace
        self._ns = split(element.tag)[0]
        if self._ns not in supported:
            self._log.warn(
                'Unknown SBML namespace ' + str(self._ns) + '. This version of'
                ' SBML may not be supported.')

        # Get model and parse
        model = element.find(self._path('model'))
        if model is None:
            raise SBMLError('Model element not found.')
        return self._parse_model(model, logger)

    def _parse_model(self, element, logger):
        """
        Parses a <model> element in an SBML document.
        """
        # Retrieve or create a model name.
        # SBML Models can have an optional name attribute (user friendly name)
        # or an optional id attribute (not necessarily user friendly) or can
        # have no name at all.
        name = element.get('name')
        if name is None:
            name = element.get('id')
        if name is None:
            name = 'Imported SBML model'

        # Create myokit model
        myokit_model = myokit.Model(name)
        self._log.log('Reading model "' + name + '"')

        # Create SBML model for storing parsing info
        model = SBMLModel()

        # Function definitions are not supported.
        x = element.find(self._path(
            'listOfFunctionDefinitions', 'functionDefinition'))
        if x is not None:
            raise SBMLError('Function definitions are not supported.')

        # Algebraic assignments are not supported
        x = element.find(self._path('listOfRules', 'algebraicRule'))
        if x is not None:
            raise SBMLError('Algebraic assignments are not supported.')

        # Constraints are not supported, but can be ignored
        x = element.find(self._path('listOfConstraints', 'constraint'))
        if x is not None:
            self._log.warn('Ignoring SBML constraints.')

        # Events are not supported, but can be ignored
        x = element.find(self._path('listOfEvents', 'event'))
        if x is not None:
            self._log.warn('Ignoring SBML events.')

        # Notes elements directly inside a model are turned into a description.
        notes = element.find(self._path('notes'))
        if notes:
            self._parse_notes(myokit_model, notes)

        # Parse unit definitions
        for unit in element.findall(self._path(
                'listOfUnitDefinitions', 'unitDefinition')):
            self._parse_unit_definition(unit, model)

        # Get model units
        for key in model.model_units:
            unit = element.get(key)
            if unit is not None:
                model.model_units[key] = model.get_unit(unit)

        # Add compartments to model
        model.components['myokit'] = myokit_model.add_component('myokit')
        compartments = element.findall(
            self._path('listOfCompartments', 'compartment'))
        for compartment in compartments:
            self._parse_compartment(myokit_model, model, compartment)

        # Parse parameters
        parameters = element.findall(
            self._path('listOfParameters', 'parameter'))
        for parameter in parameters:
            self._parse_parameter(myokit_model, model, parameter)

        # Add reference to global conversion factor
        conv_factor_id = element.get('conversionFactor')
        if conv_factor_id:
            if 'globalConversionFactor' in model.param_and_species:
                raise SBMLError(
                    'The ID <globalConversionFactor> is protected in a myokit'
                    ' SBML import. Please rename IDs.')
            try:
                conv_factor = model.param_and_species[conv_factor_id]
                model.param_and_species['globalConversionFactor'] = \
                    conv_factor
            except KeyError:
                raise SBMLError(
                    'The model conversionFactor points to non-existent ID.')

        # Parse species
        for species in element.findall(self._path('listOfSpecies', 'species')):
            self._parse_species(myokit_model, model, species)

        # Add time variable to model
        time = model.components['myokit'].add_variable('time')
        time.set_binding('time')
        time.set_unit(model.model_units['timeUnits'])
        time.set_rhs(0)
        model.param_and_species['http://www.sbml.org/sbml/symbols/time'] = time

        # Add reactions to model
        reactions = element.findall(self._path('listOfReactions', 'reaction'))
        for reaction in reactions:
            self._parse_reaction(myokit_model, model, reaction)
        self.add_rate_expressions_for_reactions(model)

        # Parse initial assignments
        assignments = element.findall(self._path(
            'listOfInitialAssignments', 'initialAssignment'))
        for assignment in assignments:
            self._parse_initial_assignment(model, assignment)

        # Parse assignment rules
        rules = element.findall(self._path('listOfRules', 'assignmentRule'))
        for rule in rules:
            self._parse_assignment_rule(model, rule)

        # Parse rate rules
        for rule in element.findall(self._path('listOfRules', 'rateRule')):
            self._parse_rate_rule(model, rule)

        return myokit_model

    def _parse_notes(self, model, element):
        """Parses the notes that can be embedded in a model."""

        self._log.log('Converting <model> notes to ascii.')
        notes = ET.tostring(element).decode()
        model.meta['desc'] = html2ascii(notes, width=75)

    def _parse_compartment(self, myokit_model, model, element):
        """
        Adds compartments to model and creates references in ``components``.

        A ``size`` variable is initialised in each compartment and references
        in param_and_species.
        """
        #TODO: Given the description above, it sounds like we need a
        # Compartment object.

        # Get id (required attribute)
        idx = element.get('id')
        if not idx:
            raise SBMLError('Required attribute "id" missing in compartment')
        name = self._convert_id(idx, element)
        if name == 'myokit':
            raise SBMLError(
                'The id "myokit" cannot be used for compartment names.')

        # Create component for compartment
        component = myokit_model.add_component(name)
        model.components[idx] = component

        # Get compartment size
        size = element.get('size')

        # Get units
        unit = element.get('units')
        if unit is not None:
            unit = model.get_unit(unit)
        else:
            dim = element.get('spatialDimensions')
            if dim is not None:
                dim = float(dim)  # can be non-integer
            if dim == 3:
                unit = model.model_units['volumeUnits']
            elif dim == 2:
                unit = model.model_units['areaUnits']
            elif dim == 1:
                unit = model.model_units['lengthUnits']
            else:
                unit = None

        # Add size parameter to compartment
        var = component.add_variable('size')
        var.set_unit(unit)
        var.set_rhs(size)

        # Save size in container for later assignments/reactions
        model.param_and_species[idx] = var

    def _parse_parameter(self, myokit_model, model, element):
        """
        Adds parameters to `myokit` compartment in model and creates references
        in `param_and_species`.
        """
        # Check id
        idp = element.get('id')
        if idp is None:
            raise SBMLError(
                'Required attribute "id" missing in parameter.')
        if idp in model.param_and_species:
            raise SBMLError('Duplicate parameter id: "' + str(idp) + '".')
        name = self._convert_id(idp, element)

        # Create variable (in global 'myokit' component)
        component = myokit_model['myokit']
        var = component.add_variable_allow_renaming(name)

        # Get value
        var.set_rhs(element.get('value'))

        # Get unit
        unit = element.get('units')
        if unit is not None:
            var.set_unit(model.get_unit(unit))

        # Store reference to variable for later assignments/reactions
        model.param_and_species[idp] = var

    def _parse_species(self, myokit_model, model, element):
        """
        Adds species to references compartment in model and creates references
        in `param_and_species`.
        """
        # Get species id
        ids = element.get('id')
        if ids is None:
            raise SBMLError('No species ID provided.')
        name = self._convert_id(ids, element)

        # Get compartment id
        idc = element.get('compartment')
        if not idc:
            raise SBMLError('No <compartment> attribute provided.')

        # Get value
        value = element.get('initialAmount')
        if value is None:
            value = element.get('initialConcentration')
            if value is not None:
                volume = param_and_species[compId]
                value = myokit.Multiply(
                    myokit.Number(amount), myokit.Name(volume))

        # Get unit
        #TODO: Refactor this: get rid of method call
        unit = element.get('substanceUnits')
        if unit is not None:
            unit = model.get_unit(unit)

        # Add variable in amount (needed for reactions, even if measured in
        # conc.).
        var = model.components[idc].add_variable_allow_renaming(name)
        var.set_unit(unit)
        var.set_rhs(value)

        # This property used to be optional (default False)
        #TODO: Should the value-getting code above be based on this?
        is_amount = element.get('hasOnlySubstanceUnits', 'false') == 'true'
        if not is_amount:
            # Save amount variable for later reference
            model.species_also_in_amount[ids] = var

            # Add variable in units of concentration
            volume = model.param_and_species[idc]
            value = myokit.Divide(myokit.Name(var), myokit.Name(volume))
            unit = unit / volume.unit()
            var = model.components[idc].add_variable_allow_renaming(
                name + '_Concentration')
            var.set_unit(unit)
            var.set_rhs(value)

        # Save species in container for later assignments/reactions
        if ids in model.param_and_species:
            raise SBMLError('Duplicate species id: "' + ids + '".')
        model.param_and_species[ids] = var

        # Constant and boundaryCondition attributes are optional in older
        # sbml versions
        is_constant = element.get('constant', 'false') == 'true'
        has_boundary = element.get('boundaryCondition', 'false') == 'true'

        # Get optional conversion factor
        conv_factor = element.get('conversionFactor')
        if conv_factor is not None:
            try:
                conv_factor = model.param_and_species[conv_factor]
            except KeyError:
                raise SBMLError(
                    'conversionFactor refers to non-existent ID.')
        else:
            conv_factor = model.param_and_species.get(
                'globalConversionFactor', None)

        # Save species properties to container for later assignments/
        # reactions
        #TODO This screams for an object
        model.species_prop[ids] = {
            'compartment': idc,
            'isAmount': is_amount,
            'isConstant': is_constant,
            'hasBoundaryCondition': has_boundary,
            'conversionFactor': conv_factor,
        }

    def _parse_reaction(self, myokit_model, model, element):
        """
        Adds rate expressions for species involved in reactions.

        It promotes the existing species variable measured in amount to a
        state variable and assigns a rate expression.

        Returns a dictionary mapping species to expressions.
        """
        components = model.components
        param_and_species = model.param_and_species
        species_prop = model.species_prop
        species_reference = model.species_reference

        # Create reaction specific species references
        reactants_stoich = {}
        products_stoich = {}

        # Get reactans, products and modifiers
        idc = element.get('compartment')

        # Reactants
        reactants = element.findall(self._path(
            'listOfReactants', 'speciesReference'))
        for reactant in reactants:
            ids = reactant.get('species')
            if ids not in param_and_species:
                raise SBMLError('Species ID not existent.')
            stoich = reactant.get('stoichiometry')
            if stoich is None:
                self._log.warn(
                    'Stoichiometry has not been set in reaction. Continued'
                    ' initialisation using value 1.')
                stoich = 1
            else:
                stoich = float(stoich)

            # If ID exits, create global parameter
            stoich_id = reactant.get('id')
            if stoich_id:
                name = self._convert_id(stoich_id, reactant)
                comp = components.get(idc, components['myokit'])
                var = comp.add_variable_allow_renaming(name)
                var.set_unit = myokit.units.dimensionless
                var.set_rhs(stoich)
                if stoich_id in param_and_species:
                    raise SBMLError('Stoichiometry ID is not unique.')
                param_and_species[stoich_id] = var

            # Save species behaviour in this reaction
            is_constant = species_prop[ids]['isConstant']
            has_boundary = species_prop[ids]['hasBoundaryCondition']
            if not (is_constant or has_boundary):
                # Only if constant and boundaryCondition is False,
                # species can change through a reaction
                reactants_stoich[ids] = \
                    stoich_id if stoich_id else stoich

            # Create reference that species is part of a reaction
            species_reference.add(ids)

        # Products
        products = element.findall(self._path(
            'listOfProducts', 'speciesReference'))
        for product in products:

            ids = product.get('species')
            if ids not in param_and_species:
                raise SBMLError('Species ID not existent.')
            stoich = product.get('stoichiometry')
            if stoich is None:
                self._log.warn(
                    'Stoichiometry has not been set in reaction. Continued'
                    ' initialisation using value 1.')
                stoich = 1
            else:
                stoich = float(stoich)

            # If ID exits, create global parameter
            stoich_id = product.get('id')
            if stoich_id:
                name = self._convert_id(stoich_id, product)
                comp = components.get(idc, components['myokit'])
                var = comp.add_variable_allow_renaming(name)
                var.set_unit = myokit.units.dimensionless
                var.set_rhs(stoich)
                if stoich_id in param_and_species:
                    raise SBMLError('Stoichiometry ID is not unique.')
                param_and_species[stoich_id] = var

            # Save species behaviour in this reaction
            is_constant = species_prop[ids]['isConstant']
            has_boundary = species_prop[ids]['hasBoundaryCondition']
            if not (is_constant or has_boundary):
                # Only if constant and boundaryCondition is False,
                # species can change through a reaction
                products_stoich[ids] = \
                    stoich_id if stoich_id else stoich

            # Create reference that species is part of a reaction
            species_reference.add(ids)

        # Raise error if neither reactants not products is populated
        if not species_reference:
            raise SBMLError(
                'Reaction must have at least one reactant or product.')

        # Modifiers
        modifiers = element.findall(self._path(
            'listOfModifiers', 'modifierSpeciesReference'))
        for modifier in modifiers:
            ids = modifier.get('species')
            if ids not in param_and_species:
                raise SBMLError('Species ID not existent.')

            # Create reference that species is part of a reaction
            species_reference.add(ids)

        # Raise error if different velocities of reactions are assumed
        if element.get('fast') == 'true':
            raise SBMLError(
                'Myokit does not support the conversion of <fast>'
                ' reactions to steady states. Please substitute the steady'
                ' states as AssigmentRule')

        # Parse kinetic law
        kinetic_law = element.find(self._path('kineticLaw'))
        if kinetic_law is None:
            return

        # Local parameters within reactions are not supported
        local_parameter = kinetic_law.find(self._path(
            'listOfLocalParameters', 'localParameter'))
        if local_parameter is not None:
            raise SBMLError(
                'Myokit does not support the definition of local'
                ' parameters in reactions. Please move their'
                ' definition to the <listOfParameters> instead.')

        # get rate expression for reaction
        expr = kinetic_law.find('{' + MATHML_NS + '}math')
        if expr is None:
            return
        try:
            expr = parse_mathml_etree(
                expr,
                lambda x, y: myokit.Name(param_and_species[x]),
                lambda x, y: myokit.Number(x))
        except myokit.formats.mathml._parser.MathMLError as e:
            raise SBMLError(
                'An error occured when importing a kineticLaw: ' + str(e))

        # Collect expressions for products
        for species in products_stoich:

            # Weight with stoichiometry
            stoich = products_stoich[species]
            if stoich in param_and_species:
                stoich = myokit.Name(param_and_species[stoich])
                weighted_expr = myokit.Multiply(stoich, expr)
            elif stoich == 1:
                weighted_expr = expr
            else:
                stoich = myokit.Number(stoich)
                weighted_expr = myokit.Multiply(stoich, expr)

            # Weight with conversion factor
            conv_factor = species_prop[species]['conversionFactor']
            if conv_factor:
                weighted_expr = myokit.Multiply(conv_factor, weighted_expr)

            # Add expression to rate expression of species
            partial_expr = model.reaction_species.get(species, None)
            if partial_expr is not None:
                weighted_expr = myokit.Plus(partial_expr, weighted_expr)
            model.reaction_species[species] = weighted_expr

        # Collect expressions for reactants
        for species in reactants_stoich:

            # Weight with stoichiometry
            stoich = reactants_stoich[species]
            if stoich in param_and_species:
                stoich = myokit.Name(param_and_species[stoich])
                weighted_expr = myokit.Multiply(stoich, expr)
            elif stoich == 1:
                weighted_expr = expr
            else:
                stoich = myokit.Number(stoich)
                weighted_expr = myokit.Multiply(stoich, expr)

            # weight with conversion factor
            conv_factor = species_prop[species]['conversionFactor']
            if conv_factor:
                weighted_expr = myokit.Multiply(conv_factor, weighted_expr)

            # Add (with minus sign) expression to rate expression of species
            partial_expr = model.reaction_species.get(species, None)
            if partial_expr is not None:
                weighted_expr = myokit.Minus(partial_expr, weighted_expr)
            else:
                weighted_expr = myokit.PrefixMinus(weighted_expr)
            model.reaction_species[species] = weighted_expr

    def add_rate_expressions_for_reactions(self, model):
        """Adds rate expressions for species to model."""

        for species in model.reaction_species:
            var = model.species_also_in_amount.get(
                species, model.param_and_species[species])
            expr = model.reaction_species[species]

            # weight expression with conversion factor
            conv_factor = model.species_prop[species]['conversionFactor']
            if conv_factor:
                expr = myokit.Multiply(conv_factor, expr)

            # The units of a reaction rate are according to SBML guidelines
            # extentUnits / timeUnits, which are both globally defined.
            # Rates in myokit don't get assigned with a unit explicitly,
            # but only the state variable has a unit and the time variable
            # has a unit, which then define the rate unit implicitly.
            #
            # A problem occurs when the extentUnit and the species unit do
            # not agree. Since initial values can be assigned to the
            # species with substanceUnits, we will choose the species
            # unit (in amount) over the globally defined extentUnits. This
            # is NOT according to SBML guidelines.
            unit = var.unit()
            extent_unit = model.model_units['extentUnits']
            if unit is None:
                unit = extent_unit
            if unit != extent_unit:
                self._log.warn(
                    'Myokit does not support extentUnits for reactions.'
                    ' Reactions will have the unit substanceUnit / timeUnit.')
            initial_value = var.rhs()
            initial_value = initial_value.eval() if initial_value else 0
            var.promote(initial_value)
            var.set_unit(unit)
            var.set_rhs(expr)

    def _parse_initial_assignment(self, model, element):
        """Parse an initial assignment of a model variable."""
        var_id = element.get('symbol')
        try:
            var = model.param_and_species[var_id]
        except KeyError:
            raise SBMLError(
                'Initial assignment refers to non-existent ID.')
        expr = element.find('{' + MATHML_NS + '}math')
        if expr is None:
            return
        expr = parse_mathml_etree(
            expr,
            lambda x, y: myokit.Name(model.param_and_species[x]),
            lambda x, y: myokit.Number(x))

        # If species, and it exists in conc. and amount, we update
        # amount, as conc = amount / size.
        try:
            var = model.species_also_in_amount[var_id]
        except KeyError:
            pass
        else:
            idc = model.species_prop[var_id]['compartment']
            volume = model.param_and_species[idc]
            expr = myokit.Multiply(expr, myokit.Name(volume))

        # Update inital value
        if var.is_state():
            var.set_state_value(value.eval())
        else:
            var.set_rhs(expr)

    def _parse_assignment_rule(self, model, element):
        """
        Parses an assignment rule, which sets an equation for a (non-state)
        variable.
        """
        var = element.get('variable')
        if var in model.species_reference:
            if not model.species_prop[var]['hasBoundaryCondition']:
                raise SBMLError(
                    'Species is assigned with rule, while being created /'
                    ' destroyed in reaction. Either set boundaryCondition'
                    ' to True or remove one of the assignments.')
        try:
            var = model.param_and_species[var]
        except KeyError:
            raise SBMLError('AssignmentRule refers to non-existent ID.')
        expr = element.find('{' + MATHML_NS + '}math')
        if expr:
            var.set_rhs(parse_mathml_etree(
                expr,
                lambda x, y: myokit.Name(model.param_and_species[x]),
                lambda x, y: myokit.Number(x)
            ))

    def _parse_rate_rule(self, model, element):
        """
        Parses a rate rule, which sets an equation for a state variable.
        """
        var_id = element.get('variable')
        if var_id in model.species_reference:
            if not model.species_prop[var_id]['hasBoundaryCondition']:
                raise SBMLError(
                    'Species is assigned with rule, while being created /'
                    ' destroyed in reaction. Either set boundaryCondition'
                    ' to True or remove one of the assignments.')
        try:
            var = model.param_and_species[var_id]
        except KeyError:
            raise SBMLError('RateRule refers to non-existent ID.')
        expr = element.find('{' + MATHML_NS + '}math')
        if expr is None:
            return
        expr = parse_mathml_etree(
            expr,
            lambda x, y: myokit.Name(model.param_and_species[x]),
            lambda x, y: myokit.Number(x)
        )

        # If species, and it exists in conc. and amount, we update
        # amount.
        try:
            var = model.species_also_in_amount[var_id]
        except KeyError:
            pass
        else:
            idc = model.species_prop[var_id]['compartment']
            volume = model.param_and_species[idc]
            expr = myokit.Divide(expr, myokit.Name(volume))

        # promote variable to state and set initial value
        value = var.eval()
        var.promote(value)
        var.set_rhs(expr)

    def _parse_unit_definition(self, element, model):
        """
        Converts a unit definition into a :class:`myokit.Unit`.
        """
        # Check id
        name = element.get('id')
        if name is None:
            raise SBMLError(
                'Required attribute "id" missing in unitDefinition')
        name = self._convert_id(name, element)

        # Construct Myokit unit
        myokit_unit = myokit.units.dimensionless
        for unit in element.findall(self._path('listOfUnits', 'unit')):

            # Get base unit (must be a predefined type)
            kind = unit.get('kind')
            if kind is None:
                raise SBMLError('Required attribute "kind" missing in unit.')
            part = model.get_base_unit(kind)

            # Note: mulitplier, scale, and exponent are required in level 3 but
            # optional in level 2.
            part *= float(unit.get('multiplier', default=1))
            part *= 10 ** float(unit.get('scale', default=0))
            part **= float(unit.get('exponent', default=1))

            # "add" composite unit to unit definition
            myokit_unit *= part

        # Store the unit
        model.add_unit(name, myokit_unit)

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

    def _convert_id(self, text, element=None):
        """
        Checks if the given ``text`` is a valid SBML identifier, and returns a
        string that can be used as a myokit component or variable name.
        """
        #TODO: Use element to raise nicer error messages

        if not self.re_id.match(text):
            raise SBMLError('Invalid id "' + str(text) + '".')

        # Unlike the SBML SId type, Myokit names cannot start with an
        # underscore
        if text[:1] == '_':
            text = 'underscore_' + text

        return text


class SBMLModel(object):
    """
    Represents a model in SBML.
    """
    def __init__(self):

        # User-defined units (maps ids to myokit.Unit objects)
        self._user_units = {}

        # TODO: The objects below should probably be classes instead of dicts,
        # and be hidden from the user (but accessible via methods).

        # Model units
        self.model_units = {
            'substanceUnits': None,
            'timeUnits': None,
            'volumeUnits': None,
            'areaUnits': None,
            'lengthUnits': None,
            'extentUnits': None,
        }

        # Mapping from ??? ids to properties
        self.species_prop = {}

        # All species in reactions for later assignment and rate rules
        self.species_reference = set()

        # Mapping for species that occur in amount and in concentration; maps
        # ??? ids to myokit.Variable measured in amount.
        self.species_also_in_amount = {}

        # Mapping from species to expressions
        self.reaction_species = {}

        # Mapping from parameter or species id to myokit.Variable objects.
        self.param_and_species = {}

        # Mapping from compartment ids to myokit.Component objects.
        self.components = {}

    def add_unit(self, name, unit):
        """Adds a user unit with the given ``name`` and myokit ``unit``."""
        self._user_units[name] = unit

    def get_base_unit(self, name):
        """Returns an SBML predefined unit."""
        if name == 'celsius':
            raise SBMLError('The units "celsius" are not supported.')
        try:
            return self.base_units[name]
        except KeyError:
            raise SBMLError('Unknown units "' + str(name) + '".')

    def get_unit(self, name):
        """Returns a user-defined or predefined unit."""
        try:
            return self._user_units[name]
        except KeyError:
            return self.get_base_unit(name)

    # SBML base units (except Celsius, because it's not defined in myokit)
    base_units = {
        'ampere': myokit.units.A,
        'avogadro': myokit.parse_unit('1 (6.02214179e23)'),
        'becquerel': myokit.units.Bq,
        'candela': myokit.units.cd,
        'coulomb': myokit.units.C,
        'dimensionless': myokit.units.dimensionless,
        'farad': myokit.units.F,
        'gram': myokit.units.g,
        'gray': myokit.units.Gy,
        'henry': myokit.units.H,
        'hertz': myokit.units.Hz,
        'item': myokit.units.dimensionless,  # Myokit does not have item unit
        'joule': myokit.units.J,
        'katal': myokit.units.kat,
        'kelvin': myokit.units.K,
        'kilogram': myokit.units.kg,
        'liter': myokit.units.L,
        'litre': myokit.units.L,
        'lumen': myokit.units.lm,
        'lux': myokit.units.lux,
        'meter': myokit.units.m,
        'metre': myokit.units.m,
        'mole': myokit.units.mol,
        'newton': myokit.units.N,
        'ohm': myokit.units.ohm,
        'pascal': myokit.units.Pa,
        'radian': myokit.units.rad,
        'second': myokit.units.s,
        'siemens': myokit.units.S,
        'sievert': myokit.units.Sv,
        'steradian': myokit.units.sr,
        'tesla': myokit.units.T,
        'volt': myokit.units.V,
        'watt': myokit.units.W,
        'weber': myokit.units.Wb,
    }
