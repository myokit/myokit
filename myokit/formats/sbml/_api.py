import collections
import re

import myokit
import myokit.formats.sbml as sbml
import myokit.units


# Regex for id checking
_re_id = re.compile(r'^[a-zA-Z_]+[a-zA-Z0-9_]*$')


class Quantity(object):
    """
    Base class for anything that has a numerical value in an SBML model, and
    can be set by rules, reactions, or initial assignments.
    """
    def __init__(self):

        # Expression for initial value (myokit.Expression)
        self._initial_value = None

        # Expression for value (myokit.Expression)
        self._value = None

        # Whether or not this is a rate
        self._is_rate = False

    def initial_value(self):
        """
        Returns an expression for this quantity's initial value, or ``None`` if
        not set.
        """
        return self._initial_value

    def is_rate(self):
        """
        Returns ``True`` only if this quantity's value is defined through a
        rate.
        """
        return self._is_rate

    def set_initial_value(self, value):
        """
        Sets a :class:`myokit.Expression` for this quantity's initial value.
        """
        self._initial_value = value

    def set_value(self, value, is_rate=False):
        """
        Sets a :class:`myokit.Expression` for this quantity's value.

        Arguments:

        ``value``
            An expression
        ``rate``
            Set to ``True`` if the expression gives the rate of change of this
            variable.

        """
        self._value = value
        self._is_rate = bool(is_rate)

    def value(self):
        """
        Returns an expression for this quantity's value, or ``None`` if not
        set.
        """
        return self._value


class Compartment(Quantity):
    """
    Represents a compartment in SBML; to create a compartment use
    :meth:`model.add_compartment()`.

    A compartment acts as a :class:`Quantity`, where the value represents the
    compartment's size.

    Arguments:

    ``model``
        The model this compartment is in.
    ``sid``
        This compartment's SId.

    """
    def __init__(self, model, sid):
        super(Compartment, self).__init__()
        self._model = model
        self._sid = sid

        self._spatial_dimensions = None
        self._size_units = None

    def set_spatial_dimensions(self, dimensions):
        """
        Sets the dimensionality of this compartment's size (usually 1, 2, or
        3); this is used to determine the units for the compartment size in the
        case that they are not explicitly set.
        """
        self._spatial_dimensions = float(dimensions)

    def set_size_units(self, units):
        """Sets the units for this compartment's size."""
        self._size_units = units

    def sid(self):
        """Returns this compartment's sid."""
        return self._sid

    def size_units(self):
        """
        Returns the units this compartment's size is in.

        If not set explicitly, the units will be retrieved from the model. If
        not set there either, units of dimensionless are returned.
        """
        if self._size_units is not None:
            return self._size_units

        if self._spatial_dimensions == 1:
            return self._model.length_units()
        elif self._spatial_dimensions == 2:
            return self._model.area_units()
        elif self._spatial_dimensions == 3:
            return self._model.volume_units()
        else:
            # Other values are allowed, but have no model attribute
            return myokit.units.dimensionless

    def spatial_dimensions(self):
        """
        Returns this compartment's spatial dimensions, or ``None`` if not set.
        """
        return self._spatial_dimensions

    def __str__(self):
        return '<Compartment ' + str(self._sid) + '>'


class Model(object):
    """
    Represents a model in SBML.

    Arguments:

    ``name``
        A user-friendly name for this model.

    """
    def __init__(self, name):

        self._name = name

        # Optional notes
        self._notes = None

        # Maps unit names to Unit objects
        # Units are the only things that can have a UnitSId
        self._units = {}

        # Used SIds
        self._sids = set()

        # Assignables: Compartments, species, species references, parameters
        self._assignables = {}

        # Compartments, parameters, species (all maps from sids to objects)
        self._compartments = collections.OrderedDict()
        self._parameters = collections.OrderedDict()
        self._species = collections.OrderedDict()

        # Reactions (map from sids to objects)
        self._reactions = collections.OrderedDict()

        # Default compartment size units
        self._length_units = myokit.units.dimensionless
        self._area_units = myokit.units.dimensionless
        self._volume_units = myokit.units.dimensionless

        # Default species amount units (not concentration)
        self._substance_units = myokit.units.dimensionless

        # Default time and extent units (kinetic law = extentUnits / timeUnits)
        self._time_units = myokit.units.dimensionless
        self._extent_units = myokit.units.dimensionless

        # Global conversion factor for species
        self._conversion_factor = None

    def add_compartment(self, sid):
        """Adds an SBML compartment to this model."""
        self._register_sid(sid)
        c = Compartment(self, sid)
        self._compartments[sid] = c
        self._assignables[sid] = c
        return c

    def add_parameter(self, sid):
        """Adds a parameter to this model."""
        self._register_sid(sid)
        p = Parameter(self, sid)
        self._parameters[sid] = p
        self._assignables[sid] = p
        return p

    def add_reaction(self, sid):
        """Adds a reaction to this model."""
        self._register_sid(sid)
        r = Reaction(self, sid)
        self._reactions[sid] = r
        return r

    def add_species(
            self, compartment, sid, is_amount=False, is_constant=False,
            is_boundary=False):
        """
        Adds a species to this model (located in the given ``compartment``).
        """
        self._register_sid(sid)
        s = Species(compartment, sid, is_amount, is_constant, is_boundary)
        self._species[sid] = s
        self._assignables[sid] = s

        return s

    def add_unit(self, unitsid, unit):
        """Adds a user unit with the given ``unitsid`` and myokit ``unit``."""
        if not _re_id.match(unitsid):
            raise sbml.SBMLError('Invalid UnitSId "' + str(unitsid) + '".')
        if unitsid in self._base_units or unitsid == 'celsius':
            raise sbml.SBMLError(
                'User unit overrides built-in unit: "' + str(unitsid) + '".')
        if unitsid in self._units:
            raise sbml.SBMLError(
                'Duplicate UnitSId: "' + str(unitsid) + '".')
        u = self._units[unitsid] = unit
        return u

    def area_units(self):
        """
        Returns the default compartment size units for 2-dimensional
        compartments, or dimensionless if not set.
        """
        return self._area_units

    def assignable(self, sid):
        """
        Returns the :class:`Compartment`, :class:`Species`,
        :class:`SpeciesReference`, or :class:`Parameter` referenced by the
        given SId.
        """
        return self._assignables[sid]

    def base_unit(self, unitsid):
        """
        Returns an SBML base unit, raises an :class:`SBMLError` if not
        supported.
        """
        # Check this base unit is supported
        if unitsid == 'celsius':
            raise sbml.SBMLError('The units "celsius" are not supported.')

        # Find and return
        return self._base_units[unitsid]

    def compartment(self, sid):
        """Returns the compartment with the given sid."""
        return self._compartments[sid]

    def conversion_factor(self):
        """
        Returns the :class:`Parameter` acting as global species conversion
        factor, or ``None`` if not set, see :meth:`Species.conversion_factor`.
        """
        return self._conversion_factor

    def extent_units(self):
        """
        Returns the default extent units in this model, or dimensionless if not
        set.
        """
        return self._extent_units

    def length_units(self):
        """
        Returns the default compartment size units for 1-dimensional
        compartments, or dimensionless if not set.
        """
        return self._length_units

    def myokit_model(self):
        """
        Converts this model to a :class:`myokit.Model`.

        SBML IDs are used for naming components and variables. If an ID starts
        with an underscore, the myokit name will be converter to
        `underscore<name>`.

        Compartments defined by the SBML file are mapped to myokit.Components.
        """

        # Create myokit model
        myokit_model = myokit.Model(self.name())

        # Add notes
        notes = self.notes()
        if notes:
            myokit_model.meta['desc'] = notes

        # Create reference container that links sid's to myokit objects
        component_references = {}
        variable_references = {}

        # Create additional container for species variables in amount
        # (Reactions define rates exclusively for amount of species)
        species_amount_references = {}

        # Create reference from Model expressions to myokit model expressions
        expression_references = {}

        # Instantiate component and variable objects first without assigning
        # RHS expressions. Myokit objects may have to be renamed, so
        # expressions are added in a second step.

        # Add SBML compartments to myokit model
        for sid, compartment in self._compartments.items():
            # Create component for compartment
            component = myokit_model.add_component_allow_renaming(
                convert_name(sid))

            # Add component to reference list
            component_references[sid] = component

            # Add compartment size to component
            var = component.add_variable_allow_renaming('size')

            # Set unit of size variable
            var.set_unit(compartment.size_units())

            # Add size variable to reference list
            variable_references[sid] = var
            expression_references[myokit.Name(compartment)] = myokit.Name(var)

        # Add myokit component to model to store time bound variable
        # and global parameters

        # Create default name of component
        myokit_component_name = 'myokit'

        # Add component
        component = myokit_model.add_component_allow_renaming(
            myokit_component_name)

        # Add myokit component to referece list
        component_references[myokit_component_name] = component

        # Add species to components
        for sid, species in self._species.items():
            # Get component from reference list
            compartment = species.compartment()
            compartment_sid = compartment.sid()
            component = component_references[compartment_sid]

            # Add species in amount to component
            # (needed for reactions, even if species is defined in
            # concentration)
            var = component.add_variable_allow_renaming(
                sid + '_amount')

            # Set unit of amount
            var.set_unit(species.substance_units())

            # Add reference to amount variable
            species_amount_references[sid] = var

            # Add species in concentration if measured in concentration
            if not species.is_amount():
                # Add species in concentration
                var = component.add_variable_allow_renaming(
                    sid + '_concentration')

                # Get myokit amount and size variable
                amount = species_amount_references[sid]
                size = variable_references[compartment_sid]

                # Set unit of concentration
                var.set_unit(amount.unit() / size.unit())

                # Define RHS of concentration as amount / size
                rhs = myokit.Divide(
                    myokit.Name(amount),
                    myokit.Name(size))
                var.set_rhs(rhs)

            # Add reference to species (either in amount or concentration)
            variable_references[sid] = var
            expression_references[myokit.Name(species)] = myokit.Name(var)

        # Add parameters to myokit component
        for sid, parameter in self._parameters.items():
            # Get myokit component
            component = component_references[myokit_component_name]

            # Add parameter to component
            var = component.add_variable_allow_renaming(sid)

            # Set unit of parameter
            var.set_unit(parameter.units())

            # Add reference to parameter
            variable_references[sid] = var
            expression_references[myokit.Name(parameter)] = myokit.Name(var)

        # Add stoichiometries from reactions
        for reaction in self._reactions.values():
            # Get all reactants and products (modifier do not have
            # stoichiometries)
            species_references = reaction.reactants() + reaction.products()

            for species_reference in species_references:
                sid = species_reference.sid()
                if sid is not None:
                    # Get component
                    species = species_reference.species()
                    compartment = species.compartment()
                    compartment_sid = compartment.sid()
                    component = component_references[compartment_sid]

                    # Add variable to component
                    var = component.add_variable_allow_renaming(sid)

                    # Set unit of variable
                    # (SBML defines stoichiometries as dimensionless)
                    var.set_unit(myokit.units.dimensionless)

                    # Add reference to variable
                    variable_references[sid] = var
                    expression_references[
                        myokit.Name(species_reference)] = myokit.Name(var)

        # Add time variable to myokit component
        component = component_references[myokit_component_name]
        var = component.add_variable_allow_renaming('time')

        # Bind time variable to time in myokit model
        var.set_binding('time')

        # Set time unit and initial value (SBML default: t=0)
        var.set_unit(self.time_units())
        var.set_rhs(0)

        # Add reference to time variable
        # (SBML referes to time by a csymbol:
        # 'http://www.sbml.org/sbml/symbols/time/')
        variable_references[
            'http://www.sbml.org/sbml/symbols/time'] = var

        # Set RHS of compartment sizes
        for sid, compartment in self._compartments.items():
            # Get myokit variable
            var = variable_references[sid]

            # Set initial value
            expr = compartment.initial_value()
            if expr is not None:
                var.set_rhs(expr.clone(
                    subst=expression_references))

            if compartment.is_rate():
                # Promote size to state variable
                var.promote(state_value=var.eval())

            # Set RHS
            # (assignmentRule overwrites initialAssignment)
            expr = compartment.value()
            if expr is not None:
                var.set_rhs(expr.clone(
                    subst=expression_references))

        # Set RHS of species (initalAssignemnt, assignmentRule, rateRule)
        # NOTE: Concentration is already set by (amount / size). So we
        # only set RHS of amount here.
        for sid, species in self._species.items():
            # Get myokit variable
            # We only adapt amount of species
            var = species_amount_references[sid]

            # Set initial value
            expr = species.initial_value()
            if expr is not None:
                # Need to convert initial value if
                # 1. the species is in amount but initial value units are not
                # 2. the species and the initial value is in concentration
                if species.is_amount() != species.units_initial_value():
                    # Get initial compartment size
                    compartment = species.compartment()
                    size = compartment.initial_value()

                    # Convert initial value from concentration to amount
                    expr = myokit.Multiply(expr, size)

                # Set initial value
                var.set_rhs(expr.clone(subst=expression_references))

            if species.is_rate():
                # Promote species to state variable
                var.promote(var.eval())

            # Set RHS (reactions are dealt with elsewhere)
            expr = species.value()
            if expr is not None:
                # Need to convert initial value if species is measured in
                # concentration (assignments match unit of measurement)
                if not species.is_amount():
                    # Get initial compartment size
                    compartment = species.compartment()
                    size = compartment.initial_value()

                    # Convert initial value from concentration to amount
                    expr = myokit.Multiply(expr, size)

                # Set initial value
                var.set_rhs(expr.clone(subst=expression_references))

        # Set RHS of parameters
        for sid, parameter in self._parameters.items():
            # Get myokit variable
            var = variable_references[sid]

            # Set initial value
            expr = parameter.initial_value()
            if expr is not None:
                var.set_rhs(expr.clone(
                    subst=expression_references))

            if parameter.is_rate():
                # Promote parameter to state variable
                var.promote(state_value=var.eval())

            # Set RHS
            # (assignmentRule overwrites initialAssignment)
            expr = parameter.value()
            if expr is not None:
                var.set_rhs(expr.clone(
                    subst=expression_references))

        # Set RHS of stoichiometries
        for reaction in self._reactions.values():
            # Get all reactants and products (modifier do not have
            # stoichiometries)
            species_references = reaction.reactants() + reaction.products()

            for species_reference in species_references:
                # Get sid
                sid = species_reference.sid()

                # Get stoichiometry variable
                try:
                    var = variable_references[sid]
                except KeyError:
                    continue

                # Set initial value
                expr = species_reference.initial_value()
                if expr is not None:
                    var.set_rhs(expr.clone(
                        subst=expression_references))

                if species_reference.is_rate():
                    # Promote stoichiometry to state variable
                    var.promote(state_value=var.eval())

                # Set RHS
                # (assignmentRule overwrites initialAssignment)
                expr = species_reference.value()
                if expr is not None:
                    var.set_rhs(expr.clone(
                        subst=expression_references))

        # Set RHS of species changed by reactions
        for reaction in self._reactions.values():
            # Get kinetic law
            kinetic_law = reaction.kinetic_law()

            if kinetic_law is None:
                # Skip to the next reaction
                continue

            for reactant in reaction.reactants():
                # Get species object
                species = reactant.species()

                if species.is_constant() or species.is_boundary():
                    # Species is not altered by the reaction
                    # Skip to the next reactant
                    continue

                # Instantiate rate expression
                expr = kinetic_law.clone()

                # Get stoichiometry of reactant
                try:
                    stoichiometry = myokit.Name(
                        variable_references[reactant.sid()])
                except KeyError:
                    stoichiometry = reactant.initial_value()

                if stoichiometry is not None:
                    # Weight rate expression by stoichiometry
                    expr = myokit.Multiply(stoichiometry, expr)

                factor = species.conversion_factor()
                if factor is not None:
                    # Get conversion factor variable
                    sid = factor.sid()
                    conversion_factor = variable_references[sid]

                    # Convert rate expression from units of reaction extent
                    # to amount units
                    conversion_factor = myokit.Name(conversion_factor)
                    expr = myokit.Multiply(conversion_factor, expr)

                # Get myokit amount variable
                var = species_amount_references[species.sid()]

                if not var.is_state():
                    # Promote amount to state variable
                    try:
                        var.promote(state_value=var.eval())
                        var.set_rhs(None)
                    except AttributeError:
                        var.promote()
                        var.set_rhs(None)

                if var.rhs().eval():
                    # Subtract rate contributions
                    # (Reaction removes species from compartment)
                    expr = myokit.Minus(var.rhs(), expr)
                else:
                    expr = myokit.PrefixMinus(expr)

                # Set RHS
                var.set_rhs(expr.clone(subst=expression_references))

            for product in reaction.products():
                # Get species object
                species = product.species()

                if species.is_constant() or species.is_boundary():
                    # Species is not altered by the reaction
                    # Skip to the next product
                    continue

                # Instantiate rate expression
                expr = kinetic_law.clone()

                # Get stoichiometry of product
                try:
                    stoichiometry = myokit.Name(
                        variable_references[product.sid()])
                except KeyError:
                    stoichiometry = product.initial_value()

                if stoichiometry is not None:
                    # Weight rate expression by stoichiometry
                    expr = myokit.Multiply(stoichiometry, expr)

                if species.conversion_factor():
                    # Get conversion factor variable
                    sid = species.conversion_factor().sid()
                    conversion_factor = variable_references[sid]

                    # Convert rate expression from units of reaction extent
                    # to amount units
                    conversion_factor = myokit.Name(conversion_factor)
                    expr = myokit.Multiply(conversion_factor, expr)

                # Get myokit amount variable
                var = species_amount_references[species.sid()]

                if not var.is_state():
                    # Promote amount to state variable
                    try:
                        var.promote(state_value=var.eval())
                        var.set_rhs(None)
                    except AttributeError:
                        var.promote()
                        var.set_rhs(None)

                if var.rhs().eval():
                    # Add rate contributions
                    expr = myokit.Plus(var.rhs(), expr)

                # Set RHS
                var.set_rhs(expr.clone(subst=expression_references))

        return myokit_model

    def name(self):
        """Returns this model's name."""
        return self._name

    def notes(self):
        """Returns a string of notes (if set), or ``None``."""
        return self._notes

    def parameter(self, sid):
        """Returns the :class:`Parameter` with the given id."""
        return self._parameters[sid]

    def reaction(self, sid):
        """Returns the :class:`Reaction` with the given id."""
        return self._reactions[sid]

    def _register_sid(self, sid):
        """
        Checks if the given SId is valid and available, registers it if it is,
        raises an error if it's not.
        """
        if not _re_id.match(sid):
            raise sbml.SBMLError('Invalid SId "' + str(sid) + '".')
        if sid in self._sids:
            raise sbml.SBMLError('Duplicate SId "' + str(sid) + '".')
        self._sids.add(sid)

    def set_area_units(self, units):
        """
        Sets the default compartment size units for 2-dimensional compartments.
        """
        self._area_units = units

    def set_conversion_factor(self, factor):
        """
        Sets a :class:`Parameter` as global conversion factor for species,
        see :meth:`Species.conversion_factor()`.
        """
        self._conversion_factor = factor

    def set_extent_units(self, units):
        """
        Sets the default units for "reaction extent", i.e. for the kinetic law
        equations in reactions.
        """
        self._extent_units = units

    def set_length_units(self, units):
        """
        Sets the default compartment size units for 1-dimensional compartments.
        """
        self._length_units = units

    def set_notes(self, notes=None):
        """Sets an optional notes string for this model."""
        self._notes = None if notes is None else str(notes)

    def set_substance_units(self, units):
        """Sets the default units for reaction amounts (not concentrations)."""
        self._substance_units = units

    def set_time_units(self, units):
        """Sets the time units used throughout the model."""
        self._time_units = units

    def set_volume_units(self, units):
        """
        Sets the default compartment size units for 3-dimensional compartments.
        """
        self._volume_units = units

    def __str__(self):
        if self._name is None:
            return '<SBMLModel>'
        return '<SBMLModel ' + str(self._name) + '>'

    def species(self, sid):
        """Returns the species with the given id."""
        return self._species[sid]

    def substance_units(self):
        """
        Returns the default units for reaction amounts (not concentrations), or
        dimensionless if not set.
        """
        return self._substance_units

    def time_units(self):
        """Returns the default units for time, or dimensionless if not set."""
        return self._time_units

    def unit(self, unitsid):
        """Returns a user-defined or predefined unit."""
        try:
            return self._units[unitsid]
        except KeyError:
            return self.base_unit(unitsid)

    def volume_units(self):
        """
        Returns the default compartment size units for 3-dimensional
        compartments, or dimensionless if not set.
        """
        return self._volume_units

    # SBML base units (except Celsius, because it's not defined in myokit)
    _base_units = {
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


class Parameter(Quantity):
    """
    Represents a parameter in SBML; to create a parameter use
    :meth:`model.add_parameter()`.

    Arguments:

    ``model``
        The model this parameter is in.
    ``sid``
        This parameter's SId.

    """
    def __init__(self, model, sid):
        super(Parameter, self).__init__()

        self._model = model
        self._sid = sid
        self._units = None

    def set_units(self, units):
        """Sets this parameters units to the given ``Units``."""
        self._units = units

    def sid(self):
        """Returns this parameter's sid."""
        return self._sid

    def __str__(self):
        return '<Parameter ' + str(self._sid) + '>'

    def units(self):
        """Returns the units this parameter is in, or ``None`` if not set."""
        return self._units


class Reaction(object):
    """
    Represents an SBML reaction; to create a reaction use
    :meth:`Model.add_reaction()`.

    Arguments:

    ``model``
        The model this reaction is in.
    ``sid``
        This reaction's SId.

    """
    def __init__(self, model, sid):
        self._model = model
        self._sid = sid

        # Reactants, reaction products, and modifiers: all as SpeciesReference
        self._reactants = []
        self._products = []
        self._modifiers = []

        # All species involved in this reaction (sid to object)
        self._species = collections.OrderedDict()

        # The kinetic law specifying this reaction's rate (if set)
        self._kinetic_law = None

    def add_modifier(self, species, sid=None):
        """Adds a modifier to this reaction and returns the created object."""
        if sid is not None:
            self._model._register_sid(sid)
        ref = ModifierSpeciesReference(species, sid)
        self._modifiers.append(ref)
        self._species[species.sid()] = species
        return ref

    def add_product(self, species, sid=None):
        """
        Adds a reaction product to this reaction and returns the created
        object.
        """
        if sid is not None:
            self._model._register_sid(sid)
        ref = SpeciesReference(species, sid)
        self._products.append(ref)
        self._species[species.sid()] = species
        if sid is not None:
            self._model._assignables[sid] = ref
        return ref

    def add_reactant(self, species, sid=None):
        """Adds a reactant to this reaction and returns the created object."""
        if sid is not None:
            self._model._register_sid(sid)
        ref = SpeciesReference(species, sid)
        self._reactants.append(ref)
        self._species[species.sid()] = species
        if sid is not None:
            self._model._assignables[sid] = ref
        return ref

    def kinetic_law(self):
        """
        Returns the kinetic law set for this reaction, or ``None`` if not set.
        """
        return self._kinetic_law

    def modifiers(self):
        """
        Returns the list of modifiers used by this reaction (as
        :class:`SpeciesReference` objects).
        """
        return list(self._modifiers)

    def products(self):
        """
        Returns the list of products created by this reaction (as
        :class:`SpeciesReference` objects).
        """
        return list(self._products)

    def reactants(self):
        """
        Returns the list of reactions used by this reaction (as
        :class:`SpeciesReference` objects).
        """
        return list(self._reactants)

    def set_kinetic_law(self, expression):
        """
        Sets this reaction's kinetic law (as a :class:`myokit.Expression`).
        """
        self._kinetic_law = expression

    def sid(self):
        """Returns this reaction's sid."""
        return self._sid

    def species(self, sid):
        """
        Finds and returns a :class:`Species` used in this reaction.
        """
        return self._species[sid]

    def __str__(self):
        return '<Reaction ' + str(self._sid) + '>'


class Species(Quantity):
    """
    Represents an SBML species; to create a species use
    :meth:`Compartment.add_species()`.

    Arguments:

    ``compartment``
        The :class:`Compartment` that this species is in.
    ``sid``
        This species's SId.
    ``is_amount``
        Whether this species value is represented as an amount (if false, it is
        represented as a concentration, which depends on the size of the
        compartment it is in).
    ``is_constant``
        Whether or not this species is constant.
    ``is_boundary``
        Whether or not this species is at the boundary of a reaction.

    """
    def __init__(self, compartment, sid, is_amount, is_constant, is_boundary):
        super(Species, self).__init__()

        self._compartment = compartment

        self._sid = sid
        self._is_amount = bool(is_amount)
        self._is_constant = bool(is_constant)
        self._is_boundary = bool(is_boundary)

        # Units for the amount, not the concentration
        self._units = None

        # Optional conversion factor from substance to extent units
        self._conversion_factor = None

        # Flag whether initial value is in correct units
        # (amount or concentration)
        self._units_initial_value = True

    def is_amount(self):
        """
        Returns ``True`` only if this species is defined as an amount (not a
        concentration).
        """
        return self._is_amount

    def is_boundary(self):
        """Returns ``True`` only if this species is at a reaction boundary."""
        return self._is_boundary

    def compartment(self):
        """Returns the :class:`Compartment` that this species is in."""
        return self._compartment

    def is_constant(self):
        """Returns ``True`` only if this species is constant."""
        return self._is_constant

    def conversion_factor(self):
        """
        Returns the :class:`Parameter` acting as conversion factor for this
        species, or the model default if not set (and ``None`` if that isn't
        set either).

        When calculating the rate of change of the species, multiplying by this
        factor converts from the species units to "number of reaction events".
        """
        if self._conversion_factor is not None:
            return self._conversion_factor
        return self._compartment._model.conversion_factor()

    def set_conversion_factor(self, factor):
        """
        Sets a :class:`Parameter` as conversion factor for this species,
        see :meth:`conversion_factor()`.
        """
        self._conversion_factor = factor

    def set_substance_units(self, units):
        """Sets the units this species amount (not concentration) is in."""
        self._units = units

    def set_units_initial_value(self, flag):
        """Sets a flag whether the units of the initial value are correct."""
        self._units_initial_value = flag

    def units_initial_value(self):
        """
        Returns a boolean flag whether the initial value has the correct units.
        """
        return self._units_initial_value

    def sid(self):
        """Returns this species's sid."""
        return self._sid

    def __str__(self):
        return '<Species ' + str(self._sid) + '>'

    def substance_units(self):
        """
        Returns the units an amount of this species (not a concentration) is
        in, or the model default if not set.
        """
        if self._units is not None:
            return self._units
        return self._compartment._model.substance_units()


class SpeciesReference(Quantity):
    """
    Represents a reference to a reactant or product species in an SBML
    reaction.

    A species reference acts as a :class:`Quantity`, where the value represents
    the species' stoichiometry.
    """
    REACTANT = 0
    PRODUCT = 1
    MODIFIER = 2

    def __init__(self, species, sid=None):
        super(SpeciesReference, self).__init__()

        self._species = species
        self._sid = sid

    def species(self):
        """Returns the species this object refers to."""
        return self._species

    def sid(self):
        """Returns this species reference's SId, or ``None`` if not set."""
        return self._sid


class ModifierSpeciesReference(object):
    """Represents a reference to a modifier species in an SBML reaction."""

    def __init__(self, species, sid=None):
        super(ModifierSpeciesReference, self).__init__()

        self._species = species
        self._sid = sid

    def species(self):
        """Returns the species this object refers to."""
        return self._species

    def sid(self):
        """Returns this species reference's SId, or ``None`` if not set."""
        return self._sid


def convert_name(name):
    """
    Converts SBML name to myokit compatible name.

    Unlike the SBML SId type, Myokit names cannot start with an
    underscore.
    """
    if name[:1] == '_':
        name = 'underscore_' + name
    return name

