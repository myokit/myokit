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


class SBMLParser(object):
    """
    Parses SBML models into :class:`myokit.Model` objects.
    """
    def __init__(self):
        self.re_name = re.compile(r'^[a-zA-Z]+[a-zA-Z0-9_]*$')
        self.re_alpha = re.compile(r'[\W]+')
        self.re_white = re.compile(r'[ \t\f\n\r]+')

    def parse_file(self, path):
        """
        Parses the SBML file at ``path`` and returns a myokit
        model.
        """
        # Read file
        try:
            tree = ET.parse(path)
        except Exception as e:
            raise SBMLError('Unable to parse XML: ' + str(e))

        # Parse content
        return self.parse(tree.getroot())

    def parse_string(self, text):
        """
        Parses the SBML XML in the string ``text`` and returns
        a myokit model.
        """
        # Read string
        try:
            root = ET.fromstring(text)
        except Exception as e:
            raise SBMLError('Unable to parse XML: ' + str(e))

        # Parse content
        return self.parse(root)

    def parse(self, root):
        """
        Parses and a SBML document rooted in the given elementtree
        element.
        """
        try:
            return self._parse_model(root)
        except SBMLError as e:
            raise SBMLError(str(e))
        except myokit.formats.mathml.MathMLError as e:
            raise SBMLError(str(e))

    def _parse_model(self, root):
        """
        Returns a :class:myokit.Model based on the SBML file provided.
        """
        # Get logger
        self._log = myokit.formats.TextLogger()

        # Check whether file has SBML 3.2 namespace
        ns = self._get_namespace(root)
        if ns != 'http://www.sbml.org/sbml/level3/version2/core':
            raise SBMLError(
                'The file does not adhere to SBML 3.2 standards. The global'
                ' namespace is not'
                ' <http://www.sbml.org/sbml/level3/version2/core>.')

        # Get model
        sbml_model = self._get_model(root)
        if not sbml_model:
            raise SBMLError(
                'The file does not adhere to SBML 3.2 standards.'
                ' No model provided.')

        # Get model name
        name = self._get_name(sbml_model)
        if not name:
            name = 'Imported SBML model'

        # Create myokit model
        self._model = myokit.Model(self._convert_name(name))
        self._log.log('Reading model "' + self._model.meta['name'] + '"')

        # Add notes, if provided, to model description
        notes = self._get_notes(sbml_model)
        if notes:
            self._log.log('Converting <model> notes to ascii')
            self._model.meta['desc'] = html2ascii(notes, width=75)
            # width = 79 - 4 for tab!

        # Raise error if function definitions are provided (could be added in
        # another PR)
        func_defs = self._get_list_of_function_definitions(sbml_model)
        if func_defs:
            raise SBMLError(
                'Myokit does not support functionDefinitions. Please insert '
                'your function wherever it occurs in yout SBML file and delete'
                ' the functionDefiniton in the file.')

        # Create user defined unit reference that maps ids to
        # myokit.Units object
        self._user_unit_dict = dict()

        # Get unit definitions
        unit_defs = self._get_list_of_unit_definitions(sbml_model)
        if unit_defs:
            for unit_def in unit_defs:
                unit_id = unit_def.get('id')
                if not unit_id:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' No unit ID provided.')
                self._user_unit_dict[
                    unit_id] = self._convert_unit_def(unit_def)

        # Get model units
        units = {
            'substanceUnit': sbml_model.get('substanceUnits'),
            'timeUnit': sbml_model.get('timeUnits'),
            'volumeUnit': sbml_model.get('volumeUnits'),
            'areaUnit': sbml_model.get('areaUnits'),
            'lengthUnit': sbml_model.get('lengthUnits'),
            'extentUnit': sbml_model.get('extentUnits'),
        }
        for unit_id, unit in units.items():
            if unit in self._user_unit_dict:
                self._user_unit_dict[unit_id] = self._user_unit_dict[unit]
            elif unit in sbml_to_myokit_unit_dict:
                self._user_unit_dict[unit_id] = sbml_to_myokit_unit_dict[unit]
            else:
                self._user_unit_dict[unit_id] = None

        # Initialise parameter and species dictionary; maps ids to
        # myokit.Variable objects.
        self._param_and_species_dict = dict()

        # Initialise compartment dictionary that maps ids to
        # myokit.Component objects.
        self._comp_dict = dict()

        # Add compartments to model
        self._parse_compartments(sbml_model)

        # Add parameters to model
        self._parse_parameters(sbml_model)

        # Add reference to global conversion factor
        conv_factor_id = sbml_model.get('conversionFactor')
        if conv_factor_id:
            if 'globalConversionFactor' in self._param_and_species_dict:
                raise SBMLError(
                    'The ID <globalConversionFactor> is protected in a myokit'
                    ' SBML import. Please rename IDs.')
            try:
                conv_factor = self._param_and_species_dict[conv_factor_id]
                self._param_and_species_dict[
                    'globalConversionFactor'] = conv_factor
            except KeyError:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' The model conversionFactor points to non-existent ID.')

        # Create species property dictionary for later reference that maps ids
        # to a dictionary of properties.
        self._species_prop_dict = dict()

        # Create dictionary for species that occur in amount and in
        # concentration that maps ids to myokit.Variable measured in
        # amount.
        self._species_also_in_amount_dict = dict()

        # Add species to compartments
        self._parse_species(sbml_model)

        # Add time bound variable to model
        time = self._comp_dict['Myokit'].add_variable('time')
        time.set_binding('time')
        time.set_unit(self._user_unit_dict['timeUnit'])
        time.set_rhs(0.0)  # According to SBML guidelines
        time_id = 'http://www.sbml.org/sbml/symbols/time'  # This ID is not
        # protected
        if time_id in self._param_and_species_dict:
            raise SBMLError(
                'Using the ID <%s> for parameters or species ' % time_id
                + 'leads import errors.')
        else:
            self._param_and_species_dict[
                'http://www.sbml.org/sbml/symbols/time'] = time

        # Create species reference for all species in reactions for later
        # assignment and rate rules
        self._species_reference = set()

        # Add Reactions to model
        self._parse_reactions(sbml_model)

        # Add initial assignments to model
        self._parse_initial_assignments(sbml_model)

        # Raise error if algebraicRules are in file
        rules = self._get_list_of_algebraic_rules(sbml_model)
        if rules:
            raise SBMLError(
                'Myokit does not support algebraic assignments.')

        # Add assignmentRules to model
        self._parse_assignment_rules(sbml_model)

        # Add rateRules to model
        self._parse_rate_rules(sbml_model)

        # Log warning if constraints are provided
        constraints = self._get_list_of_constraints(sbml_model)
        if constraints:
            self._log.warn(
                "Myokit does not support SBML's constraints feature. "
                "The constraints will be ignored for the simulation.")

        # Log warning if events are provided (could be supported in a later PR)
        events = self._get_list_of_events(sbml_model)
        if events:
            self._log.warn(
                "Myokit does not support SBML's events feature. The events"
                " will be ignored for the simulation. Have a look at myokits"
                " protocol feature for instantaneous state value changes.")

        return self._model

    def _parse_compartments(self, sbml_model):
        """
        Adds compartments to model and creates references in
        self._comp_dict. A ``size`` variable is initialised in each compartment
        and references in self._param_and_species_dict.
        """
        for comp in self._get_list_of_compartments(sbml_model):
            idx = comp.get('id')
            if not idx:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' No compartment ID provided.')
            name = comp.get('name')
            if not name:
                name = idx
            size = comp.get('size')
            unit = comp.get('units')
            if unit:
                if unit in self._user_unit_dict:
                    unit = self._user_unit_dict[unit]
                elif unit in sbml_to_myokit_unit_dict:
                    unit = sbml_to_myokit_unit_dict[unit]
            else:
                dim = comp.get('spatialDimensions')
                if dim:
                    dim = float(dim)  # can be non-integer
                if dim == 3.0:
                    unit = self._user_unit_dict['volumeUnit']
                elif dim == 2.0:
                    unit = self._user_unit_dict['areaUnit']
                elif dim == 1.0:
                    unit = self._user_unit_dict['lengthUnit']
                else:
                    unit = None

            # Create compartment
            self._comp_dict[idx] = self._model.add_component(
                self._convert_name(name))

            # Add size parameter to compartment
            var = self._comp_dict[idx].add_variable('size')
            var.set_unit(unit)
            var.set_rhs(size)

            # save size in container for later assignments/reactions
            self._param_and_species_dict[idx] = var

        name = self._convert_name('myokit')
        if 'Myokit' in self._comp_dict:
            raise SBMLError(
                'The compartment ID <Myokit> is reserved in a myokit'
                ' import.')
        self._comp_dict['Myokit'] = self._model.add_component(name)

    def _parse_parameters(self, sbml_model):
        """
        Adds parameters to `Myokit` compartment in model and creates
        references in `self._param_and_species_dict`.
        """
        for param in self._get_list_of_parameters(sbml_model):
            idp = param.get('id')
            if not idp:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' No parameter ID provided.')
            name = param.get('name')
            if not name:
                name = idp
            value = param.get('value')
            unit = self._get_units(param)

            # add parameter to sbml compartment
            comp = self._comp_dict['Myokit']
            var = comp.add_variable_allow_renaming(
                self._convert_name(name))
            var.set_unit(unit)
            var.set_rhs(value)

            # save param in container for later assignments/reactions
            self._param_and_species_dict[idp] = var

    def _parse_species(self, sbml_model):
        """
        Adds species to references compartment in model and creates references
        in `self._param_and_species_dict`.
        """
        for s in self._get_list_of_species(sbml_model):
            ids = s.get('id')
            if not ids:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' No species ID provided.')
            name = s.get('name')
            if not name:
                name = ids
            idc = s.get('compartment')
            if not idc:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' No <compartment> attribute provided.')
            is_amount = s.get('hasOnlySubstanceUnits')
            if is_amount is None:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' No <hasOnlySubstanceUnits> flag provided.')
            is_amount = True if is_amount == 'true' else False
            value = self._get_species_initial_value_in_amount(s, idc)
            unit = self._get_substance_units(s)

            # Add variable in amount (needed for reactions, even if
            # measured in conc.)
            var = self._comp_dict[idc].add_variable_allow_renaming(name)
            var.set_unit(unit)
            var.set_rhs(value)

            if not is_amount:
                # Safe amount variable for later reference
                self._species_also_in_amount_dict[ids] = var

                # Add variable in units of concentration
                volume = self._param_and_species_dict[idc]
                value = myokit.Divide(
                    myokit.Name(var), myokit.Name(volume))
                unit = unit / volume.unit()
                var = self._comp_dict[idc].add_variable_allow_renaming(
                    name + '_Concentration')
                var.set_unit(unit)
                var.set_rhs(value)

            # Save species in container for later assignments/reactions
            self._param_and_species_dict[ids] = var

            # save species properties to container for later assignments/
            # reactions
            is_constant = s.get('constant')
            if is_constant is None:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' No <constant> flag provided.')
            is_constant = False if is_constant == 'false' else True
            has_boundary = s.get('boundaryCondition')
            if has_boundary is None:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' No <boundaryCondition> flag provided.')
            has_boundary = False if has_boundary == 'false' else True
            conv_factor = s.get('conversionFactor')
            if conv_factor:
                try:
                    conv_factor = self._param_and_species_dict[conv_factor]
                except KeyError:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' conversionFactor refers to non-existent ID.')
            elif 'globalConversionFactor' in self._param_and_species_dict:
                conv_factor = self._param_and_species_dict[
                    'globalConversionFactor']
            else:
                conv_factor = None
            self._species_prop_dict[ids] = {
                'compartment': idc,
                'isAmount': is_amount,
                'isConstant': is_constant,
                'hasBoundaryCondition': has_boundary,
                'conversionFactor': conv_factor,
            }

    def _parse_reactions(self, sbml_model):
        """
        Adds rate expressions for species involved in reactions.

        It promotes the existing species variable measured in amount to a
        state variable and assigns a rate expression.
        """
        # Create reactant and product reference to build rate equations
        reaction_species_dict = dict()
        for reaction in self._get_list_of_reactions(sbml_model):
            # Create reaction specific species references
            reactants_stoich_dict = dict()
            products_stoich_dict = dict()

            # Get reactans, products and modifiers
            idc = reaction.get('compartment')

            # Reactants
            for reactant in self._get_list_of_reactants(reaction):
                ids = reactant.get('species')
                if ids not in self._param_and_species_dict:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 '
                        'standards. Species ID not existent.')
                stoich = reactant.get('stoichiometry')
                if stoich is None:
                    self._log.warn(
                        'Stoichiometry has not been set in reaction. '
                        'It may be set elsewhere in the SBML file, '
                        'myokit has, however, initialised the stoich-'
                        ' iometry with value 1.')
                    stoich = 1.0
                else:
                    stoich = float(stoich)
                stoich_id = reactant.get('id')
                name = reactant.get('name')
                if not name:
                    name = stoich_id

                # If ID exits, create global parameter
                if stoich_id:
                    try:
                        var = self._comp_dict[
                            idc].add_variable_allow_renaming(name)
                    except KeyError:
                        var = self._comp_dict[
                            'Myokit'].add_variable_allow_renaming(name)
                    var.set_unit = myokit.units.dimensionless
                    var.set_rhs(stoich)
                    self._param_and_species_dict[stoich_id] = var

                # Save species behaviour in this reaction
                is_constant = self._species_prop_dict[ids]['isConstant']
                has_boundary = self._species_prop_dict[ids][
                    'hasBoundaryCondition']
                if not (is_constant or has_boundary):
                    # Only if constant and boundaryCondition is False,
                    # species can change through a reaction
                    reactants_stoich_dict[
                        ids] = stoich_id if stoich_id else stoich

                # Create reference that species is part of a reaction
                self._species_reference.add(ids)

            # Products
            for product in self._get_list_of_products(reaction):
                ids = product.get('species')
                if ids not in self._param_and_species_dict:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 '
                        'standards. Species ID not existent.')
                stoich = product.get('stoichiometry')
                if stoich is None:
                    self._log.warn(
                        'Stoichiometry has not been set in reaction. '
                        'It may be set elsewhere in the SBML file, '
                        'myokit has, however, initialised the stoich'
                        'iometry with value 1.')
                    stoich = 1.0
                else:
                    stoich = float(stoich)
                stoich_id = product.get('id')
                name = product.get('name')
                if not name:
                    name = stoich_id

                # If ID exits, create global parameter
                if stoich_id:
                    try:
                        var = self._comp_dict[
                            idc].add_variable_allow_renaming(name)
                    except KeyError:
                        var = self._comp_dict[
                            'Myokit'].add_variable_allow_renaming(name)
                    var.set_unit = myokit.units.dimensionless
                    var.set_rhs(stoich)
                    self._param_and_species_dict[stoich_id] = var

                # Save species behaviour in this reaction
                is_constant = self._species_prop_dict[ids]['isConstant']
                has_boundary = self._species_prop_dict[ids][
                    'hasBoundaryCondition']
                if not (is_constant or has_boundary):
                    # Only if constant and boundaryCondition is False,
                    # species can change through a reaction
                    products_stoich_dict[
                        ids] = stoich_id if stoich_id else stoich

                # Create reference that species is part of a reaction
                self._species_reference.add(ids)

            # Raise error if neither reactants not products is populated
            if self._species_reference == set():
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards. '
                    'Reaction must have at least one reactant or product.')

            # Modifiers
            for modifier in self._get_list_of_modiefiers(reaction):
                ids = modifier.get('species')
                if ids not in self._param_and_species_dict:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 '
                        'standards. Species ID not existent.')

                # Create reference that species is part of a reaction
                self._species_reference.add(ids)

            # Raise error if different velocities of reactions are assumed
            is_fast = reaction.get('fast')
            is_fast = True if is_fast == 'true' else False
            if is_fast:
                raise SBMLError(
                    'Myokit does not support the conversion of <fast>'
                    ' reactions to steady states. Please do the maths'
                    ' and substitute the steady states as AssigmentRule')

            # Get kinetic law
            kinetic_law = self._get_kinetic_law(reaction)
            if kinetic_law:
                local_params = self._get_list_of_local_parameters(
                    kinetic_law)
                if local_params:
                    raise SBMLError(
                        'Myokit does currently not support the definition '
                        'of local parameters in reactions. Please move '
                        'their definition to the <listOfParameters> '
                        'instead.')

                # get rate expression for reaction
                expr = self._get_math(kinetic_law)
                if expr:
                    try:
                        expr = parse_mathml_etree(
                            expr,
                            lambda x, y: myokit.Name(
                                self._param_and_species_dict[
                                    x]),
                            lambda x, y: myokit.Number(x))
                    except KeyError:
                        SBMLError(
                            'The file does not adhere to SBML 3.2 '
                            'standards. The reaction refers to species '
                            'that are not listed as reactants, products'
                            ' or modifiers.')

                    # Collect expressions for products
                    for species in products_stoich_dict:
                        # weight with stoichiometry
                        stoich = products_stoich_dict[species]
                        if stoich in self._param_and_species_dict:
                            stoich = myokit.Name(
                                self._param_and_species_dict[stoich])
                            weighted_expr = myokit.Multiply(stoich, expr)
                        elif stoich == 1.0:
                            weighted_expr = expr
                        else:
                            stoich = myokit.Number(stoich)
                            weighted_expr = myokit.Multiply(stoich, expr)

                        # weight with conversion factor
                        conv_factor = self._species_prop_dict[species][
                            'conversionFactor']
                        if conv_factor:
                            weighted_expr = myokit.Multiply(
                                conv_factor, weighted_expr)

                        # add expression to rate expression of species
                        if species in reaction_species_dict:
                            partialExpr = reaction_species_dict[species]
                            reaction_species_dict[species] = myokit.Plus(
                                partialExpr, weighted_expr)
                        else:
                            reaction_species_dict[species] = weighted_expr

                    # Collect expressions for reactants
                    for species in reactants_stoich_dict:
                        # weight with stoichiometry
                        stoich = reactants_stoich_dict[species]
                        if stoich in self._param_and_species_dict:
                            stoich = myokit.Name(
                                self._param_and_species_dict[stoich])
                            weighted_expr = myokit.Multiply(stoich, expr)
                        elif stoich == 1.0:
                            weighted_expr = expr
                        else:
                            stoich = myokit.Number(stoich)
                            weighted_expr = myokit.Multiply(stoich, expr)

                        # weight with conversion factor
                        conv_factor = self._species_prop_dict[species][
                            'conversionFactor']
                        if conv_factor:
                            weighted_expr = myokit.Multiply(
                                conv_factor, weighted_expr)

                        # add (with minus sign) expression to rate
                        # expression of species
                        if species in reaction_species_dict:
                            partialExpr = reaction_species_dict[species]
                            reaction_species_dict[species] = myokit.Minus(
                                partialExpr, weighted_expr)
                        else:
                            weighted_expr = myokit.Multiply(
                                myokit.Number(-1.0), weighted_expr)
                            reaction_species_dict[species] = weighted_expr

        # Add rate expression for species to model
        for species in reaction_species_dict:
            try:
                var = self._species_also_in_amount_dict[species]
            except KeyError:
                var = self._param_and_species_dict[species]
            expr = reaction_species_dict[species]

            # weight expression with conversion factor
            conv_factor = self._species_prop_dict[species][
                'conversionFactor']
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
            extent_unit = self._user_unit_dict['extentUnit']
            if not unit:
                unit = extent_unit
            if unit != extent_unit:
                self._log.warn(
                    'Myokit does not support extentUnits for reactions. '
                    'Reactions will have the unit substanceUnit / '
                    'timeUnit')
            initial_value = var.rhs()
            initial_value = initial_value.eval() if initial_value else 0
            var.promote(initial_value)
            var.set_unit(unit)
            var.set_rhs(reaction_species_dict[species])

    def _parse_initial_assignments(self, sbml_model):
        """Adds initial assignments to variables in model."""
        for assign in self._get_list_of_initial_assignments(sbml_model):
            var_id = assign.get('symbol')
            try:
                var = self._param_and_species_dict[var_id]
            except KeyError:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' Initial assignment refers to non-existent ID.')
            expr = self._get_math(assign)
            if expr:
                expr = parse_mathml_etree(
                    expr,
                    lambda x, y: myokit.Name(
                        self._param_and_species_dict[x]),
                    lambda x, y: myokit.Number(x))

                # If species, and it exists in conc. and amount, we update
                # amount, as conc = amount / size.
                try:
                    var = self._species_also_in_amount_dict[var_id]
                except KeyError:
                    pass
                else:
                    idc = self._species_prop_dict[var_id]['compartment']
                    volume = self._param_and_species_dict[idc]
                    expr = myokit.Multiply(expr, myokit.Name(volume))

                # Update inital value
                if var.is_state():
                    value = expr.eval()
                    var.set_state_value(value)
                else:
                    var.set_rhs(expr)

    def _parse_assignment_rules(self, sbml_model):
        """Adds assignment rules to variables in model."""
        for rule in self._get_list_of_assignment_rules(sbml_model):
            var = rule.get('variable')
            if var in self._species_reference:
                if not self._species_prop_dict[
                        var]['hasBoundaryCondition']:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' Species is assigned with rule, while being '
                        'created / desctroyed in reaction. Either set '
                        'boundaryCondition to True or remove one of the'
                        ' assignments.')
            try:
                var = self._param_and_species_dict[var]
            except KeyError:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' AssignmentRule refers to non-existent ID.')
            expr = self._get_math(rule)
            if expr:
                var.set_rhs(parse_mathml_etree(
                    expr,
                    lambda x, y: myokit.Name(
                        self._param_and_species_dict[x]),
                    lambda x, y: myokit.Number(x)
                ))

    def _parse_rate_rules(self, sbml_model):
        """Adds rate rules for variables to model."""
        for rule in self._get_list_of_rate_rules(sbml_model):
            var_id = rule.get('variable')
            if var_id in self._species_reference:
                if not self._species_prop_dict[
                        var_id]['hasBoundaryCondition']:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' Species is assigned with rule, while being '
                        'created / desctroyed in reaction. Either set '
                        'boundaryCondition to True or remove one of the'
                        ' assignments.')
            try:
                var = self._param_and_species_dict[var_id]
            except KeyError:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' RateRule refers to non-existent ID.')
            expr = self._get_math(rule)
            if expr:
                expr = parse_mathml_etree(
                    expr,
                    lambda x, y: myokit.Name(
                        self._param_and_species_dict[x]),
                    lambda x, y: myokit.Number(x)
                )

                # If species, and it exists in conc. and amount, we update
                # amount.
                try:
                    var = self._species_also_in_amount_dict[var_id]
                except KeyError:
                    pass
                else:
                    idc = self._species_prop_dict[var_id]['compartment']
                    volume = self._param_and_species_dict[idc]
                    expr = myokit.Divide(expr, myokit.Name(volume))

                # promote variable to state and set initial value
                value = var.eval()
                var.promote(value)
                var.set_rhs(expr)

    def _get_namespace(self, element):
        return split(element.tag)[0]

    def _get_model(self, element):
        model = element.find(
            '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'model')
        if model:
            return model
        return None

    def _get_name(self, element):
        name = element.get('name')
        if name:
            return name
        name = element.get('id')
        if name:
            return name
        return None

    def _get_notes(self, element):
        notes = element.find(
            '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'notes')
        if notes:
            return ET.tostring(notes).decode()
        return None

    def _get_list_of_function_definitions(self, element):
        funcs = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfFunctionDefinitions/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'functionDefinition')
        if funcs:
            return funcs
        return None

    def _get_list_of_unit_definitions(self, element):
        units = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfUnitDefinitions/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'unitDefinition')
        if units:
            return units
        return None

    def _get_list_of_compartments(self, element):
        comps = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfCompartments/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'compartment')
        if comps:
            return comps
        return []

    def _get_list_of_parameters(self, element):
        params = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfParameters/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'parameter')
        if params:
            return params
        return []

    def _get_list_of_species(self, element):
        species = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfSpecies/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'species')
        if species:
            return species
        return []

    def _get_list_of_reactions(self, element):
        reactions = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfReactions/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'reaction')
        if reactions:
            return reactions
        return []

    def _get_list_of_reactants(self, element):
        reactants = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfReactants/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'speciesReference')
        if reactants:
            return reactants
        return []

    def _get_list_of_products(self, element):
        products = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfProducts/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'speciesReference')
        if products:
            return products
        return []

    def _get_list_of_modiefiers(self, element):
        modifiers = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfModifiers/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'modifierSpeciesReference')
        if modifiers:
            return modifiers
        return []

    def _get_kinetic_law(self, element):
        kinetic_law = element.find(
            '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'kineticLaw')
        if kinetic_law:
            return kinetic_law
        return None

    def _get_list_of_initial_assignments(self, element):
        assignments = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfInitialAssignments/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'initialAssignment')
        if assignments:
            return assignments
        return []

    def _get_list_of_algebraic_rules(self, element):
        rules = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfRules/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'algebraicRule')
        if rules:
            return rules
        return None

    def _get_list_of_assignment_rules(self, element):
        rules = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfRules/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'assignmentRule')
        if rules:
            return rules
        return []

    def _get_list_of_rate_rules(self, element):
        rules = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfRules/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'rateRule')
        if rules:
            return rules
        return []

    def _get_list_of_constraints(self, element):
        constraints = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfConstraints/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'constraint')
        if constraints:
            return constraints
        return None

    def _get_list_of_events(self, element):
        events = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfEvents/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'event')
        if events:
            return events
        return None

    def _get_math(self, element):
        math = element.find(
            '{http://www.w3.org/1998/Math/MathML}'
            + 'math')
        if math:
            return math
        return None

    def _get_list_of_local_parameters(self, element):
        params = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfLocalParameters/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'localParameter')
        if params:
            return params
        return None

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
            self._log.warn(
                'Converting name <' + org_name + '> to <' + name + '>.')
        return name

    def _convert_unit_def(self, unit_def):
        """
        Converts unit definition into a myokit unit.
        """
        # Get composing base units
        units = unit_def.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            'listOfUnits/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'unit')
        if not units:
            return None

        # instantiate unit definition
        unit_def = myokit.units.dimensionless

        # construct unit definition from base units
        for baseUnit in units:
            kind = baseUnit.get('kind')
            if not kind:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' No unit kind provided.')
            myokitUnit = sbml_to_myokit_unit_dict[kind]
            myokitUnit *= float(baseUnit.get('multiplier', default=1.0))
            myokitUnit *= 10 ** float(baseUnit.get('scale', default=0.0))
            myokitUnit **= float(baseUnit.get('exponent', default=1.0))

            # "add" composite unit to unit definition
            unit_def *= myokitUnit

        return unit_def

    def _get_units(self, parameter):
        """
        Returns :class:myokit.Unit expression of the unit of a parameter.
        """
        unit = parameter.get('units')
        if unit in self._user_unit_dict:
            return self._user_unit_dict[unit]
        elif unit in sbml_to_myokit_unit_dict:
            return sbml_to_myokit_unit_dict[unit]
        else:
            return None

    def _get_substance_units(self, species):
        """
        Returns :class:myokit.Unit expression of the unit of a species.
        """
        # Convert substance unit into myokiy.Unit
        unit = species.get('substanceUnits')
        if unit in self._user_unit_dict:
            return self._user_unit_dict[unit]
        elif unit in sbml_to_myokit_unit_dict:
            return sbml_to_myokit_unit_dict[unit]
        else:
            return None

    def _get_species_initial_value_in_amount(self, species, compId):
        """
        Returns the initial value of a species either in amount or
        concentration depend on the flag is Amount.
        """
        amount = species.get('initialAmount')
        if amount:
            return amount
        conc = species.get('initialConcentration')
        if conc:
            volume = self._param_and_species_dict[compId]
            return myokit.Multiply(
                myokit.Number(amount), myokit.Name(volume))
        return None


class SBMLError(myokit.ImportError):
    """
    Thrown if an error occurs when importing SBML
    """


# SBML base units according to libSBML
sbml_to_myokit_unit_dict = {
    'ampere': myokit.units.A,
    'avogadro': None,  # TODO: myokit equivalent not yet looked up
    'becquerel': myokit.units.Bq,
    'candela': myokit.units.cd,
    'celsius': myokit.units.C,
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
    'ohm': myokit.units.R,
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
