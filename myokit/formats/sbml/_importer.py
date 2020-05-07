#
# Imports a model from an SBML file.
# Only partial SBML support (Based on SBML level 3 version 2) is provided.
# The file format specifications can be found here
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

    def info(self):
        return info

    def supports_model(self):
        """See :meth: myokit.formats.Importer.supports_model()."""
        return True

    def supports_component(self):
        """See :meth: myokit.formats.Importer.supports_component()."""
        return False

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
        except myokit.formats.sbml._importer.SBMLError as e:
            raise SBMLError(str(e))
        except myokit.formats.mathml.MathMLError as e:
            raise SBMLError(str(e))

    def _parse_model(self, root):
        """
        Returns a :class:myokit.Model based on the SBML file provided.
        """
        # Get logger
        log = self.logger()

        # Check whether file has SBML 3.2 namespace
        ns = self._get_namespace(root)
        if ns != 'http://www.sbml.org/sbml/level3/version2/core':
            raise SBMLError(
                'The file does not adhere to SBML 3.2 standards. The global'
                ' namespace is not'
                ' <http://www.sbml.org/sbml/level3/version2/core>.')

        # Get model
        SBMLmodel = self._get_model(root)
        if not SBMLmodel:
            raise SBMLError(
                'The file does not adhere to SBML 3.2 standards.'
                ' No model provided.')

        # Get model name
        name = self._get_name(SBMLmodel)
        if not name:
            name = 'Imported SBML model'

        # Create myokit model
        model = myokit.Model(self._convert_name(name))
        log.log('Reading model "' + model.meta['name'] + '"')

        # Add notes, if provided, to model description
        notes = self._get_notes(SBMLmodel)
        if notes:
            log.log('Converting <model> notes to ascii')
            model.meta['desc'] = html2ascii(notes, width=75)
            # width = 79 - 4 for tab!

        # Raise error if function definitions are provided (could be added in
        # another PR)
        funcDefs = self._get_list_of_function_definitions(SBMLmodel)
        if funcDefs:
            raise SBMLError(
                'Myokit does not support functionDefinitions. Please insert '
                'your function wherever it occurs in yout SBML file and delete'
                ' the functionDefiniton in the file.')

        # Create user defined unit reference
        self.userUnitDict = dict()

        # Get unit definitions
        unitDefs = self._get_list_of_unit_definitions(SBMLmodel)
        if unitDefs:
            for unitDef in unitDefs:
                unitId = unitDef.get('id')
                if not unitId:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' No unit ID provided.')
                self.userUnitDict[
                    unitId] = self._convert_unit_def(unitDef)

        # Get model units
        units = {
            'substanceUnit': SBMLmodel.get('substanceUnits'),
            'timeUnit': SBMLmodel.get('timeUnits'),
            'volumeUnit': SBMLmodel.get('volumeUnits'),
            'areaUnit': SBMLmodel.get('areaUnits'),
            'lengthUnit': SBMLmodel.get('lengthUnits'),
            'extentUnit': SBMLmodel.get('extentUnits'),
        }
        for unitId in units:
            unit = units[unitId]
            if unit in self.userUnitDict:
                self.userUnitDict[unitId] = self.userUnitDict[unit]
            elif unit in SBML2MyoKitUnitDict:
                self.userUnitDict[unitId] = SBML2MyoKitUnitDict[unit]
            else:
                self.userUnitDict[unitId] = None

        # Initialise parameter and species dictionary
        self.paramAndSpeciesDict = dict()

        # Add compartments to model
        compDict = dict()
        comps = self._get_list_of_compartments(SBMLmodel)
        if comps:
            for comp in comps:
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
                    if unit in self.userUnitDict:
                        unit = self.userUnitDict[unit]
                    elif unit in SBML2MyoKitUnitDict:
                        unit = SBML2MyoKitUnitDict[unit]
                else:
                    dim = comp.get('spatialDimensions')
                    if dim:
                        dim = float(dim)  # can be non-integer
                    if dim == 3.0:
                        unit = self.userUnitDict['volumeUnit']
                    elif dim == 2.0:
                        unit = self.userUnitDict['areaUnit']
                    elif dim == 1.0:
                        unit = self.userUnitDict['lengthUnit']
                    else:
                        unit = None

                # Create compartment
                compDict[idx] = model.add_component(
                    self._convert_name(name))

                # Add size parameter to compartment
                var = compDict[idx].add_variable('size')
                var.set_unit(unit)
                var.set_rhs(size)

                # save size in container for later assignments/reactions
                self.paramAndSpeciesDict[idx] = var

        name = self._convert_name('myokit')
        if 'Myokit' in compDict:
            raise SBMLError(
                'The compartment ID <Myokit> is reserved in a myokit'
                ' import.')
        compDict['Myokit'] = model.add_component(name)

        # Add parameters to model
        params = self._get_list_of_parameters(SBMLmodel)
        if params:
            for param in params:
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
                comp = compDict['Myokit']
                var = comp.add_variable_allow_renaming(
                    self._convert_name(name))
                var.set_unit(unit)
                var.set_rhs(value)

                # save param in container for later assignments/reactions
                self.paramAndSpeciesDict[idp] = var

        # Add reference to global conversion factor
        convFactorId = SBMLmodel.get('conversionFactor')
        if convFactorId:
            if 'globalConversionFactor' in self.paramAndSpeciesDict:
                raise SBMLError(
                    'The ID <globalConversionFactor> is protected in a myokit'
                    ' SBML import. Please rename IDs.')
            try:
                convFactor = self.paramAndSpeciesDict[convFactorId]
                self.paramAndSpeciesDict['globalConversionFactor'] = convFactor
            except KeyError:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' The model conversionFactor points to non-existent ID.')

        # Create properties dictionary for later reference
        speciesPropDict = dict()

        # Create dictionary for species that occur in amount and in
        # concentration
        speciesAlsoInAmountDict = dict()

        # Add species to compartments
        species = self._get_list_of_species(SBMLmodel)
        if species:
            for s in species:
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
                isAmount = s.get('hasOnlySubstanceUnits')
                if isAmount is None:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' No <hasOnlySubstanceUnits> flag provided.')
                isAmount = True if isAmount == 'true' else False
                value = self._get_species_initial_value_in_amount(s, idc, isAmount)
                unit = self._get_substance_units(s)

                # Add variable in amount (needed for reactions, even if
                # measured in conc.)
                var = compDict[idc].add_variable_allow_renaming(name)
                var.set_unit(unit)
                var.set_rhs(value)

                if not isAmount:
                    # Safe amount variable for later reference
                    speciesAlsoInAmountDict[ids] = var

                    # Add variable in units of concentration
                    volume = self.paramAndSpeciesDict[idc]
                    value = myokit.Divide(
                        myokit.Name(var), myokit.Name(volume))
                    unit = unit / volume.unit()
                    var = compDict[idc].add_variable_allow_renaming(
                        name + '_Concentration')
                    var.set_unit(unit)
                    var.set_rhs(value)

                # Save species in container for later assignments/reactions
                self.paramAndSpeciesDict[ids] = var

                # save species properties to container for later assignments/
                # reactions
                isConstant = s.get('constant')
                if isConstant is None:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' No <constant> flag provided.')
                isConstant = False if isConstant == 'false' else True
                hasBoundaryCond = s.get('boundaryCondition')
                if hasBoundaryCond is None:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' No <boundaryCondition> flag provided.')
                hasBoundaryCond = False if hasBoundaryCond == 'false' else True
                convFactor = s.get('conversionFactor')
                if convFactor:
                    try:
                        convFactor = self.paramAndSpeciesDict[convFactor]
                    except KeyError:
                        raise SBMLError(
                            'The file does not adhere to SBML 3.2 standards.'
                            ' conversionFactor refers to non-existent ID.')
                elif 'globalConversionFactor' in self.paramAndSpeciesDict:
                    convFactor = self.paramAndSpeciesDict[
                        'globalConversionFactor']
                else:
                    convFactor = None
                speciesPropDict[ids] = {
                    'compartment': idc,
                    'isAmount': isAmount,
                    'isConstant': isConstant,
                    'hasBoundaryCondition': hasBoundaryCond,
                    'conversionFactor': convFactor,
                }

        # Add time bound variable to model
        time = compDict['Myokit'].add_variable('time')
        time.set_binding('time')
        time.set_unit(self.userUnitDict['timeUnit'])
        time.set_rhs(0.0)  # According to SBML guidelines
        time_id = 'http://www.sbml.org/sbml/symbols/time'  # This ID is not
        # protected
        if time_id in self.paramAndSpeciesDict:
            raise SBMLError(
                'Using the ID <%s> for parameters or species ' % time_id
                + 'leads import errors.')
        else:
            self.paramAndSpeciesDict[
                'http://www.sbml.org/sbml/symbols/time'] = time

        # Create speciesReference for all species in reactions for later
        # assignment and rate rules
        speciesReference = set()

        # Add Reactions to model
        reactions = self._get_list_of_reactions(SBMLmodel)
        if reactions:
            # Create reactant and product reference to build rate equations
            reactionSpeciesDict = dict()
            for reaction in reactions:
                # Create reaction specific species references
                reactantsStoichDict = dict()
                productsStoichDict = dict()

                # Get reactans, products and modifiers
                idc = reaction.get('compartment')

                # Reactants
                reactants = self._get_list_of_reactants(reaction)
                if reactants:
                    for reactant in reactants:
                        ids = reactant.get('species')
                        if ids not in self.paramAndSpeciesDict:
                            raise SBMLError(
                                'The file does not adhere to SBML 3.2 '
                                'standards. Species ID not existent.')
                        stoich = reactant.get('stoichiometry')
                        if stoich is None:
                            log.warn(
                                'Stoichiometry has not been set in reaction. '
                                'It may be set elsewhere in the SBML file, '
                                'myokit has, however, initialised the stoich-'
                                ' iometry with value 1.')
                            stoich = 1.0
                        else:
                            stoich = float(stoich)
                        idStoich = reactant.get('id')
                        name = reactant.get('name')
                        if not name:
                            name = idStoich

                        # If ID exits, create global parameter
                        if idStoich:
                            try:
                                var = compDict[
                                    idc].add_variable_allow_renaming(name)
                            except KeyError:
                                var = compDict[
                                    'Myokit'].add_variable_allow_renaming(name)
                            var.set_unit = myokit.units.dimensionless
                            var.set_rhs(stoich)
                            self.paramAndSpeciesDict[idStoich] = var

                        # Save species behaviour in this reaction
                        isConstant = speciesPropDict[ids]['isConstant']
                        hasBoundaryCond = speciesPropDict[ids][
                            'hasBoundaryCondition']
                        if not (isConstant or hasBoundaryCond):
                            # Only if constant and boundaryCondition is False,
                            # species can change through a reaction
                            reactantsStoichDict[
                                ids] = idStoich if idStoich else stoich

                        # Create reference that species is part of a reaction
                        speciesReference.add(ids)

                # Products
                products = self._get_list_of_products(reaction)
                if products:
                    for product in products:
                        ids = product.get('species')
                        if ids not in self.paramAndSpeciesDict:
                            raise SBMLError(
                                'The file does not adhere to SBML 3.2 '
                                'standards. Species ID not existent.')
                        stoich = product.get('stoichiometry')
                        if stoich is None:
                            log.warn(
                                'Stoichiometry has not been set in reaction. '
                                'It may be set elsewhere in the SBML file, '
                                'myokit has, however, initialised the stoich'
                                'iometry with value 1.')
                            stoich = 1.0
                        else:
                            stoich = float(stoich)
                        idStoich = product.get('id')
                        name = product.get('name')
                        if not name:
                            name = idStoich

                        # If ID exits, create global parameter
                        if idStoich:
                            try:
                                var = compDict[
                                    idc].add_variable_allow_renaming(name)
                            except KeyError:
                                var = compDict[
                                    'Myokit'].add_variable_allow_renaming(name)
                            var.set_unit = myokit.units.dimensionless
                            var.set_rhs(stoich)
                            self.paramAndSpeciesDict[idStoich] = var

                        # Save species behaviour in this reaction
                        isConstant = speciesPropDict[ids]['isConstant']
                        hasBoundaryCond = speciesPropDict[ids][
                            'hasBoundaryCondition']
                        if not (isConstant or hasBoundaryCond):
                            # Only if constant and boundaryCondition is False,
                            # species can change through a reaction
                            productsStoichDict[
                                ids] = idStoich if idStoich else stoich

                        # Create reference that species is part of a reaction
                        speciesReference.add(ids)
                if reactants is None and products is None:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards. '
                        'Reaction must have at least one reactant or product.')

                # Modifiers
                modifiers = self._get_list_of_modiefiers(reaction)
                if modifiers:
                    for modifier in modifiers:
                        ids = modifier.get('species')
                        if ids not in self.paramAndSpeciesDict:
                            raise SBMLError(
                                'The file does not adhere to SBML 3.2 '
                                'standards. Species ID not existent.')

                        # Create reference that species is part of a reaction
                        speciesReference.add(ids)

                # Raise error if different velocities of reactions are assumed
                isFast = reaction.get('fast')
                isFast = True if isFast == 'true' else False
                if isFast:
                    raise SBMLError(
                        'Myokit does not support the conversion of <fast>'
                        ' reactions to steady states. Please do the maths'
                        ' and substitute the steady states as AssigmentRule')

                # Get kinetic law
                kineticLaw = self._get_kinetic_law(reaction)
                if kineticLaw:
                    localParams = self._get_list_of_local_parameters(
                        kineticLaw)
                    if localParams:
                        raise SBMLError(
                            'Myokit does currently not support the definition '
                            'of local parameters in reactions. Please move '
                            'their definition to the <listOfParameters> '
                            'instead.')

                    # get rate expression for reaction
                    expr = self._get_math(kineticLaw)
                    if expr:
                        try:
                            expr = parse_mathml_etree(
                                expr,
                                lambda x, y: myokit.Name(
                                    self.paramAndSpeciesDict[
                                        x]),
                                lambda x, y: myokit.Number(x))
                        except KeyError:
                            SBMLError(
                                'The file does not adhere to SBML 3.2 '
                                'standards. The reaction refers to species '
                                'that are not listed as reactants, products'
                                ' or modifiers.')

                        # Collect expressions for products
                        for species in productsStoichDict:
                            # weight with stoichiometry
                            stoich = productsStoichDict[species]
                            if stoich in self.paramAndSpeciesDict:
                                stoich = myokit.Name(self.paramAndSpeciesDict[
                                    stoich])
                                weightedExpr = myokit.Multiply(stoich, expr)
                            elif stoich == 1.0:
                                weightedExpr = expr
                            else:
                                stoich = myokit.Number(stoich)
                                weightedExpr = myokit.Multiply(stoich, expr)

                            # weight with conversion factor
                            convFactor = speciesPropDict[species][
                                'conversionFactor']
                            if convFactor:
                                weightedExpr = myokit.Multiply(
                                    convFactor, weightedExpr)

                            # add expression to rate expression of species
                            if species in reactionSpeciesDict:
                                partialExpr = reactionSpeciesDict[species]
                                reactionSpeciesDict[species] = myokit.Plus(
                                    partialExpr, weightedExpr)
                            else:
                                reactionSpeciesDict[species] = weightedExpr

                        # Collect expressions for reactants
                        for species in reactantsStoichDict:
                            # weight with stoichiometry
                            stoich = reactantsStoichDict[species]
                            if stoich in self.paramAndSpeciesDict:
                                stoich = myokit.Name(self.paramAndSpeciesDict[
                                    stoich])
                                weightedExpr = myokit.Multiply(stoich, expr)
                            elif stoich == 1.0:
                                weightedExpr = expr
                            else:
                                stoich = myokit.Number(stoich)
                                weightedExpr = myokit.Multiply(stoich, expr)

                            # weight with conversion factor
                            convFactor = speciesPropDict[species][
                                'conversionFactor']
                            if convFactor:
                                weightedExpr = myokit.Multiply(
                                    convFactor, weightedExpr)

                            # add (with minus sign) expression to rate
                            # expression of species
                            if species in reactionSpeciesDict:
                                partialExpr = reactionSpeciesDict[species]
                                reactionSpeciesDict[species] = myokit.Minus(
                                    partialExpr, weightedExpr)
                            else:
                                weightedExpr = myokit.Multiply(
                                    myokit.Number(-1.0), weightedExpr)
                                reactionSpeciesDict[species] = weightedExpr

            # Add rate expression for species to model
            for species in reactionSpeciesDict:
                try:
                    var = speciesAlsoInAmountDict[species]
                except KeyError:
                    var = self.paramAndSpeciesDict[species]
                expr = reactionSpeciesDict[species]

                # weight expression with conversion factor
                convFactor = speciesPropDict[species][
                    'conversionFactor']
                if convFactor:
                    expr = myokit.Multiply(convFactor, expr)

                # The units of a reaction rate are according to SBML guidelines
                # extentUnits / timeUnits, which are both globally defined.
                # Rates in myokit don't get assigned with a unit explicitly,
                # but only the state variable has a unit and the time variable
                # has a unit, which then define the rate unit implicitly.
                #
                # A problem occurs when the extentUnit and the species unit do
                # not agree. Since initial values can be assigned to the secies
                # in the respective substance units, we will choose the species
                # unit (in amount) over the globally defined extentUnits. This
                # is NOT according to SBML guidelines.
                unit = var.unit()
                extentUnit = self.userUnitDict['extentUnit']
                if not unit:
                    unit = extentUnit
                if unit != extentUnit:
                    log.warn(
                        'Myokit does not support extentUnits for reactions. '
                        'Reactions will have the unit substanceUnit / '
                        'timeUnit')
                initialValue = var.rhs()
                initialValue = initialValue.eval() if initialValue else 0
                var.promote(initialValue)
                var.set_unit(unit)
                var.set_rhs(reactionSpeciesDict[species])

        # Add initial assignments to model
        assignments = self._get_list_of_initial_assignments(SBMLmodel)
        if assignments:
            for assign in assignments:
                varId = assign.get('symbol')
                try:
                    var = self.paramAndSpeciesDict[varId]
                except KeyError:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' Initial assignment refers to non-existent ID.')
                expr = self._get_math(assign)
                if expr:
                    expr = parse_mathml_etree(
                        expr,
                        lambda x, y: myokit.Name(self.paramAndSpeciesDict[x]),
                        lambda x, y: myokit.Number(x))

                    # If species, and it exists in conc. and amount, we update
                    # amount.
                    try:
                        var = speciesAlsoInAmountDict[varId]
                    except KeyError:
                        pass
                    else:
                        idc = speciesPropDict[varId]['compartment']
                        volume = self.paramAndSpeciesDict[idc]
                        expr = myokit.Multiply(expr, myokit.Name(volume))

                    # Update inital value
                    if var.is_state():
                        value = expr.eval()
                        var.set_state_value(value)
                    else:
                        var.set_rhs(expr)

        # Raise error if algebraicRules are in file
        rules = self._get_list_of_algebraic_rules(SBMLmodel)
        if rules:
            raise SBMLError(
                'Myokit does not support algebraic assignments.')

        # Add assignmentRules to model
        rules = self._get_list_of_assignment_rules(SBMLmodel)
        if rules:
            for rule in rules:
                var = rule.get('variable')
                if var in speciesReference:
                    if not speciesPropDict[var]['hasBoundaryCondition']:
                        raise SBMLError(
                            'The file does not adhere to SBML 3.2 standards.'
                            ' Species is assigned with rule, while being '
                            'created / desctroyed in reaction. Either set '
                            'boundaryCondition to True or remove one of the'
                            ' assignments.')
                try:
                    var = self.paramAndSpeciesDict[var]
                except KeyError:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' AssignmentRule refers to non-existent ID.')
                expr = self._get_math(rule)
                if expr:
                    var.set_rhs(parse_mathml_etree(
                        expr,
                        lambda x, y: myokit.Name(self.paramAndSpeciesDict[x]),
                        lambda x, y: myokit.Number(x)
                    ))

        # Add rateRules to model
        rules = self._get_list_of_rate_rules(SBMLmodel)
        if rules:
            for rule in rules:
                varId = rule.get('variable')
                if varId in speciesReference:
                    if not speciesPropDict[varId]['hasBoundaryCondition']:
                        raise SBMLError(
                            'The file does not adhere to SBML 3.2 standards.'
                            ' Species is assigned with rule, while being '
                            'created / desctroyed in reaction. Either set '
                            'boundaryCondition to True or remove one of the'
                            ' assignments.')
                try:
                    var = self.paramAndSpeciesDict[varId]
                except KeyError:
                    raise SBMLError(
                        'The file does not adhere to SBML 3.2 standards.'
                        ' RateRule refers to non-existent ID.')
                expr = self._get_math(rule)
                if expr:
                    expr = parse_mathml_etree(
                        expr,
                        lambda x, y: myokit.Name(self.paramAndSpeciesDict[x]),
                        lambda x, y: myokit.Number(x)
                    )

                    # If species, and it exists in conc. and amount, we update
                    # amount.
                    try:
                        var = speciesAlsoInAmountDict[varId]
                    except KeyError:
                        pass
                    else:
                        idc = speciesPropDict[varId]['compartment']
                        volume = self.paramAndSpeciesDict[idc]
                        expr = myokit.Divide(expr, myokit.Name(volume))

                    # promote variable to state and set initial value
                    value = var.eval()
                    var.promote(value)
                    var.set_rhs(expr)

        # Log warning if constraints are provided
        constraints = self._get_list_of_constraints(SBMLmodel)
        if constraints:
            log.warn(
                "Myokit does not support SBML's constraints feature. "
                "The constraints will be ignored for the simulation.")

        # Log warning if events are provided (could be supported in a later PR)
        events = self._get_list_of_events(SBMLmodel)
        if events:
            log.warn(
                "Myokit does not support SBML's events feature. The events"
                " will be ignored for the simulation. Have a look at myokits"
                " protocol feature for instantaneous state value changes.")

        return model

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
        return None

    def _get_list_of_parameters(self, element):
        params = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfParameters/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'parameter')
        if params:
            return params
        return None

    def _get_list_of_species(self, element):
        species = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfSpecies/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'species')
        if species:
            return species
        return None

    def _get_list_of_reactions(self, element):
        reactions = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfReactions/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'reaction')
        if reactions:
            return reactions
        return None

    def _get_list_of_reactants(self, element):
        reactants = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfReactants/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'speciesReference')
        if reactants:
            return reactants
        return None

    def _get_list_of_products(self, element):
        products = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfProducts/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'speciesReference')
        if products:
            return products
        return None

    def _get_list_of_modiefiers(self, element):
        modifiers = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfModifiers/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'modifierSpeciesReference')
        if modifiers:
            return modifiers
        return None

    def _get_kinetic_law(self, element):
        kineticLaw = element.find(
            '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'kineticLaw')
        if kineticLaw:
            return kineticLaw
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
        return None

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
        return None

    def _get_list_of_rate_rules(self, element):
        rules = element.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'listOfRules/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'rateRule')
        if rules:
            return rules
        return None

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
            self.logger().warn(
                'Converting name <' + org_name + '> to <' + name + '>.')
        return name

    def _convert_unit_def(self, unitDef):
        """
        Converts unit definition into a myokit unit.
        """
        # Get composing base units
        units = unitDef.findall(
            './'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            'listOfUnits/'
            + '{http://www.sbml.org/sbml/level3/version2/core}'
            + 'unit')
        if not units:
            return None

        # instantiate unit definition
        unitDef = myokit.units.dimensionless

        # construct unit definition from base units
        for baseUnit in units:
            kind = baseUnit.get('kind')
            if not kind:
                raise SBMLError(
                    'The file does not adhere to SBML 3.2 standards.'
                    ' No unit kind provided.')
            myokitUnit = SBML2MyoKitUnitDict[kind]
            myokitUnit *= float(baseUnit.get('multiplier', default=1.0))
            myokitUnit *= 10 ** float(baseUnit.get('scale', default=0.0))
            myokitUnit **= float(baseUnit.get('exponent', default=1.0))

            # "add" composite unit to unit definition
            unitDef *= myokitUnit

        return unitDef

    def _get_units(self, parameter):
        """
        Returns :class:myokit.Unit expression of the unit of a parameter.
        """
        unit = parameter.get('units')
        if unit in self.userUnitDict:
            return self.userUnitDict[unit]
        elif unit in SBML2MyoKitUnitDict:
            return SBML2MyoKitUnitDict[unit]
        else:
            return None

    def _get_substance_units(self, species):
        """
        Returns :class:myokit.Unit expression of the unit of a species.
        """
        # Convert substance unit into myokiy.Unit
        unit = species.get('substanceUnits')
        if unit in self.userUnitDict:
            return self.userUnitDict[unit]
        elif unit in SBML2MyoKitUnitDict:
            return SBML2MyoKitUnitDict[unit]
        else:
            return None

    def _get_species_initial_value_in_amount(self, species, compId, isAmount):
        """
        Returns the initial value of a species either in amount or
        concentration depend on the flag is Amount.
        """
        amount = species.get('initialAmount')
        if amount:
            return amount
        conc = species.get('initialConcentration')
        if conc:
            volume = self.paramAndSpeciesDict[compId]
            return myokit.Multiply(
                myokit.Number(amount), myokit.Name(volume))
        return None


class SBMLError(myokit.ImportError):
    """
    Thrown if an error occurs when importing SBML
    """


# SBML base units according to libSBML
SBML2MyoKitUnitDict = {
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
    'item': None,  # TODO: myokit equivalent not yet looked up
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
