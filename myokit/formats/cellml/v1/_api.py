#
# CellML 1.0/1.1 API
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import collections
import re
import warnings

import myokit


# Identifier validation
_cellml_identifier = re.compile('^([_][0-9_]*)?[a-zA-Z][a-zA-Z0-9_]*$')


def is_valid_identifier(name):
    """
    Tests if the given ``name`` is a valid CellML 1.1 identifier.

    This method returns True if (and only if) the identifier

    1. contains only alphanumeric characters (from the basic latin set) or
       underscores
    2. contains at least one letter
    3. does not begin with a numerical character.

    The rules for 1.0 are slightly more lenient, and allow silly things like
    ``1e2``, ``123`` or ``_123`` as identifiers. Because this creates issues
    distinguishing identifiers from numbers, Myokit always follows the 1.1
    rule, even for 1.0 documents.
    """
    return _cellml_identifier.match(name) is not None


def clean_identifier(name):
    """
    Checks if ``name`` is a valid CellML identifier and if not attempts to make
    it into one.

    Raises a ``ValueError`` if it can't create a valid identifier.
    """
    if is_valid_identifier(name):
        return name

    # Replace spaces and hyphens with underscores
    clean = re.sub(r'[\s-]', '_', name)

    # Check if valid and return
    if is_valid_identifier(clean):
        return clean
    raise ValueError(
        'Unable to create a valid CellML identifier from "' + str(name) + '".')


def create_unit_name(unit):
    """
    Creates an almost readable name for a Myokit ``unit``.
    """
    # Get preferred name from Myokit's representation (e.g. [kg]) but trim off
    # the brackets
    name = str(unit)[1:-1]

    # If this is a valid name, return
    if is_valid_identifier(name):
        return name

    # Not allowed: could be because of a multiplier, e.g. [m (0.0254)]
    if ' ' in name:
        name, multiplier = name.split(' ')
    else:
        name, multiplier = name, ''

    # Could also be because it's g*m/mol^2
    name = name.replace('^', '')
    name = name.replace('/', '_per_')
    name = name.replace('*', '_')
    name = name.replace('.', '_dot_')

    # Remove "1_" from "1_per_mV"
    if name[:2] == '1_':
        name = name[2:]

    # Turn "1 (123)" into "dimensionless (123)"
    elif name == '1':
        # E.g. [1 (1000)]
        name = 'dimensionless'

    # Add multiplier (can be float)
    if multiplier:
        multiplier = unit.multiplier()

        # Use e-notation if multiple of 10
        multiplier10 = unit.multiplier_log_10()
        if myokit.float.eq(multiplier10, int(multiplier10)):
            multiplier = '1e' + str(int(multiplier10))

        # Format as integer
        elif myokit.float.eq(multiplier, int(multiplier)):
            multiplier = str(int(multiplier))

        # Format as float
        else:
            multiplier = str(multiplier)

        # Remove characters not allowed in CellML identifiers
        multiplier = multiplier.replace('+', '')
        multiplier = multiplier.replace('-', '_minus_')
        multiplier = multiplier.replace('.', '_dot_')
        name += '_times_' + multiplier

    return name


class AnnotatableElement(object):
    """
    Represents a CellML 1.0 or 1.1 element that can have a cmeta:id.

    Each ``AnnotatableElement`` also has a public dict ``meta`` that can be
    used to story key:value (string:string) pairs, for storing meta data.
    """

    def __init__(self, model):

        # The model this element is in (or is)
        self._model = model

        # A unique identifier (or None)
        self._cmeta_id = None

        # Public meta data
        self.meta = {}

    def cmeta_id(self):
        """
        Returns this element's cmeta:id if set, or ``None`` otherwise.
        """
        return self._cmeta_id

    def set_cmeta_id(self, cmeta_id):
        """
        Sets this element's cmeta id (must be a non-empty string or ``None``).
        """
        # Check if already set, ignore setting twice
        if self._cmeta_id is not None:
            # Ignore setting the same id again
            if cmeta_id == self._cmeta_id:
                return

        # Set new cmeta id, unregister old one
        if cmeta_id is None:
            if self._cmeta_id is not None:
                self._model._unregister_cmeta_id(self._cmeta_id)
            self._cmeta_id = None
        else:
            # Register and check uniqueness etc.
            self._model._register_cmeta_id(cmeta_id, self)

            # Unregister old (do _after_ register has checked new cmeta id)
            if self._cmeta_id is not None:
                self._model._unregister_cmeta_id(self._cmeta_id)

            # Store new
            self._cmeta_id = cmeta_id


class CellMLError(myokit.MyokitError):
    """
    Raised when an invalid CellML model is created or detected, or when a model
    uses CellML features that Myokit does not support.
    """


class UnitsError(CellMLError):
    """
    Raised when unsupported unit features are used.
    """


class UnsupportedBaseUnitsError(UnitsError):
    """
    Raised when unsupported base units are used.
    """
    def __init__(self, units):
        self.units = units
        super(UnsupportedBaseUnitsError, self).__init__(
            'Unsupported base units "' + units + '".')


class UnsupportedUnitOffsetError(UnitsError):
    """
    Raised when units with non-zero offsets are used.
    """
    def __init__(self):
        super(UnsupportedUnitOffsetError, self).__init__(
            'Units with non-zero offsets are not supported.')


class Component(AnnotatableElement):
    """
    Represents a model component, should not be created directly but only via
    :meth:`Model.add_component()`.
    """
    def __init__(self, model, name):
        super(Component, self).__init__(model)

        # Store model
        self._model = model

        # Check and store name
        if not is_valid_identifier(name):
            raise CellMLError(
                'Component name must be a valid CellML identifier (3.4.2.2).')
        self._name = name

        # This component's encapsulation relationships
        self._parent = None
        self._children = set()

        # This component's variables
        self._variables = collections.OrderedDict()

        # This component's component-level units
        self._units = {}

        # Lookup myokit unit to name (note this lookup may not be unique)
        self._myokit_unit_to_name = {}

    def add_units(self, name, myokit_unit):
        """
        Add a component-level units definition to this component.

        Arguments:

        ``name``
            A valid CellML identifier to use as the name
        ``myokit_unit``
            A :class:`myokit.Unit` object.
        """
        # Check uniqueness
        if name in self._units:
            raise CellMLError(
                'Units defined in the same component cannot have the same'
                ' name (5.4.1.2)')

        # Create, store, and return
        # Note: there can be units with different names but the same myokit
        # unit, in this case we simply overwrite whatever name was already
        # there. This shouldn't cause any issues because the name still refers
        # to a valid unit.
        units = Units(name, myokit_unit)
        self._units[name] = units
        self._myokit_unit_to_name[myokit_unit] = name
        return units

    def add_variable(self, name, units, public_interface='none',
                     private_interface='none'):
        """
        Adds a variable with the given ``name`` and ``units``.

        Arguments

        ``name``
            A valid CellML identifier (string).
        ``units``
            The name of a units definition known to this component or its
            parent model.
        ``public_interface``
            The variable's public interface.
        ``private_interface``
            The variable's private interface.

        """
        # Check name uniqueness
        if name in self._variables:
            raise CellMLError(
                'Variable name must be unique within Component (3.4.3.2).')

        # Create, store, and return
        self._variables[name] = v = Variable(
            self, name, units, public_interface, private_interface)
        return v

    def children(self):
        """
        Returns an iterator over any encapsulated child components.
        """
        return iter(self._children)

    def __contains__(self, key):
        return key in self._variables

    def find_units(self, name):
        """
        Looks up and returns a :class:`Units` object with the given ``name``.

        Searches first in this component, then in its model, then in the list
        of predefined units.

        Raises a :class:`CellMLError` is no unit is found.
        """
        try:
            return self._units[name]
        except KeyError:
            return self._model.find_units(name)

    def find_units_name(self, myokit_unit):
        """
        Attempts to find a string name for the given :class:`myokit.Unit`.

        Searches first in this component, then in its model, then in the list
        of predefined units. If multiple units definitions have the same
        :class:`myokit.Unit`, the last added name is returned.

        Raises a :class:`CellMLError` is no appropriate unit is found.
        """
        try:
            return self._myokit_unit_to_name[myokit_unit]
        except KeyError:
            return self._model.find_units_name(myokit_unit)

    def __getitem__(self, key):
        return self._variables[key]

    def has_children(self):
        """
        Checks if this component has any encapsulated child components.
        """
        return len(self._children) > 0

    def __iter__(self):
        return iter(self._variables.values())

    def __len__(self):
        return len(self._variables)

    def model(self):
        """
        Return this component's model.
        """
        return self._model

    def name(self):
        """
        Returns this component's name.
        """
        return self._name

    def parent(self):
        """
        Returns this component's parent component (or None).
        """
        return self._parent

    def set_parent(self, parent):
        """
        Sets this component as the encapsulated child of the component
        ``parent``.
        """
        # Check parent is a component from the same model (or None)
        if parent is not None:
            if not isinstance(parent, Component):
                raise ValueError('Parent must be a cellml.v1.Component.')
            if self._model != parent._model:
                raise ValueError('Parent must be from the same model.')

        # Store relationship
        if self._parent is not None:
            self._parent._children.remove(self)
        self._parent = parent
        if parent is not None:
            parent._children.add(self)

    def __str__(self):
        return 'Component[@name="' + self._name + '"]'

    def units(self):
        """
        Returns an iterator over the :class:`Units` objects in this component.
        """
        return iter(self._units.values())

    def _validate(self):
        """
        Validates this component, raising a :class:`CellMLError` if any errors
        are found.
        """
        # Check for cycles in the encapsulation hierarchy
        parent = self._parent
        while parent is not None:
            if parent is self:
                raise CellMLError(
                    'Encapsulation hierarchy cannot be circular (6.4.3.2).')
            parent = parent._parent

        # Validate variables
        for v in self._variables.values():
            v._validate()

        # If this component has states, check that it also has a free variable
        # in the local component.
        has_states = False
        has_free = False
        for v in self._variables.values():
            if v.is_state():
                has_states = True
            elif v.value_source().is_free():
                has_free = True
            if has_states and has_free:
                break

        # If derivatives are used, check that a time variable is defined and
        # is available in this component.
        if has_states:
            if self._model.free_variable() is None:
                raise CellMLError(
                    'If state variables are used, a free variable must be set'
                    ' with Model.set_free_variable().')
            if not has_free:
                raise CellMLError(
                    str(self) + ' has state variables, but no local variable'
                    ' connected to the free variable.')

    def variable(self, name):
        """
        Returns the variable with the given ``name``.
        """
        return self._variables[name]

    def variables(self):
        """
        Returns an iterator over this component's variables.
        """
        return iter(self._variables.values())


class Model(AnnotatableElement):
    """
    Represents a CellML 1.0 or 1.1 model.

    Support notes for 1.0 and 1.1:

    - Units with offsets are not supported, including the base units "celsius".
    - Defining new base units is not supported.
    - Reactions are not supported.
    - Models that take derivatives with respect to more than one variable are
      not supported.
    - Models written as a DAE (e.g. ``1 + x = 2 + y``) are not supported.
    - cmeta:id support is limited to models, components, and variables.

    Support notes for 1.1:

    - The new feature of using variables in ``initial_value`` attributes is not
      supported.
    - Imports (CellML 1.1) are not supported.

    Support notes for 1.0:

    - The stricter 1.1 rule for identifiers is used for both CellML 1.0 and
      1.1: a valid identifier not start with a number, and must contain at
      least one letter.

    Arguments:

    ``name``
        A valid CellML identifier string.
    ``version``
        A string representing the CellML version this model is in (must be
        '1.0' or '1.1').

    """
    def __init__(self, name, version='1.0'):
        super(Model, self).__init__(self)

        # Check and store name
        if not is_valid_identifier(name):
            raise CellMLError(
                'Model name must be a valid CellML identifier (3.4.1.2).')
        self._name = name

        # Check and store version
        if version not in ('1.0', '1.1'):
            raise ValueError(
                'Only 1.0 and 1.1 models are supported by this API.')
        self._version = version

        # This model's components
        self._components = collections.OrderedDict()

        # This model's model-level units
        self._units = {}

        # Lookup myokit unit to name (note this lookup may not be unique)
        self._myokit_unit_to_name = {}

        # A mapping from cmeta:ids to CellML element objects.
        self._cmeta_ids = {}

        # This model's free variable
        self._free_variable = None

        # Note: encapsulation relationships are stored inside the components,
        # other relationship types are not stored at all

        # Note: connections are stored in the variable with the "in" interface.

    def add_component(self, name):
        """
        Adds an empty component with the given ``name``.
        """
        # Check uniqueness
        if name in self._components:
            raise CellMLError(
                'Component name must be unique within model (3.4.2.2).')

        # Create, store, and return
        self._components[name] = c = Component(self, name)
        return c

    def add_connection(self, variable_1, variable_2):
        """
        Adds a connection between ``variable_1`` and ``variable_2``.
        """
        # Check both are variables, and from this model
        if not isinstance(variable_1, Variable):
            raise ValueError('Argument variable_1 must be a'
                             ' cellml.v1.Variable.')
        if not isinstance(variable_2, Variable):
            raise ValueError('Argument variable_2 must be a'
                             ' cellml.v1.Variable.')
        if variable_1._model is not self:
            raise ValueError('Argument variable_1 must be a variable from this'
                             ' model.')
        if variable_2._model is not self:
            raise ValueError('Argument variable_2 must be a variable from this'
                             ' model.')

        # Check variables are distinct
        if variable_1 is variable_2:
            raise CellMLError(
                'Variables cannot be connected to themselves.')

        # Check components are distinct
        component_1 = variable_1.component()
        component_2 = variable_2.component()
        if component_1 is component_2:
            raise CellMLError('Variables cannot be connected to variables in'
                              ' the same component (3.4.5.4)')

        # Determine which interfaces connect these variables
        interface_1 = variable_1.public_interface()
        interface_2 = variable_2.public_interface()
        string_1 = string_2 = 'public'
        if component_1 == component_2.parent():
            # Component 1 is the parent and uses the private interface
            interface_1 = variable_1.private_interface()
            string_1 = 'private'
        elif component_2 == component_1.parent():
            # Component 2 is the parent and uses the private interface
            interface_2 = variable_2.private_interface()
            string_2 = 'private'
        elif component_1.parent() != component_2.parent():
            raise CellMLError(
                'Connections can only be made between components that are'
                ' siblings or have a parent-child (encapsulation)'
                ' relationship (3.4.6.4).')

        # Check interfaces and connect variables
        # Note: We're allowing the same connection to be specified twice here
        if interface_1 == 'out' and interface_2 == 'in':
            if variable_2._source is None:
                variable_2._source = variable_1
            elif variable_2._source is variable_1:
                raise CellMLError(
                    'Invalid connection: ' + str(variable_2) + ' is already'
                    ' connected to ' + str(variable_1) + '.')
            else:
                raise CellMLError(
                    'Invalid connection: ' + str(variable_2) + ' has a '
                    + string_1 + '_interface of "in" and is already connected'
                    ' to a variable with an interface of "out".')
        elif interface_1 == 'in' and interface_2 == 'out':
            if variable_1._source is None:
                variable_1._source = variable_2
            elif variable_1._source is variable_2:
                raise CellMLError(
                    'Invalid connection: ' + str(variable_1) + ' is already'
                    ' connected to ' + str(variable_2) + '.')
            else:
                raise CellMLError(
                    'Invalid connection: ' + str(variable_1) + ' has a '
                    + string_2 + '_interface of "in" and is already connected'
                    ' to a variable with an interface of "out".')
        else:
            raise CellMLError(
                'Invalid connection: ' + str(variable_1) + ' has a ' + string_1
                + '_interface of "' + interface_1 + '", while '
                + str(variable_2) + ' has a ' + string_2 + '_interface of "'
                + interface_2 + '" (3.4.6.4).')

    def add_units(self, name, myokit_unit):
        """
        Add a model-level units definition to this model.

        Arguments:

        ``name``
            A valid CellML identifier to use as the name
        ``myokit_unit``
            A :class:`myokit.Unit` object.
        """
        # Check uniqueness
        if name in self._units:
            raise CellMLError(
                'Units defined in the same model cannot have the same name'
                ' (5.4.1.2)')

        # Create, store, and return
        units = Units(name, myokit_unit)
        self._units[name] = units
        self._myokit_unit_to_name[myokit_unit] = name
        return units

    def component(self, name):
        """
        Returns the :class:`Component` with the given ``name``.
        """
        return self._components[name]

    def components(self):
        """
        Returns an iterator over this model's components.
        """
        return iter(self._components.values())

    def __contains__(self, key):
        return key in self._components

    def element_with_cmeta_id(self, cmeta_id):
        """
        Returns the model, component, or variable with the given ``cmeta_id``
        or raises a KeyError if no such element is found.
        """
        return self._cmeta_ids[cmeta_id]

    def find_units(self, name):
        """
        Looks up and returns a :class:`Units` object with the given ``name``.

        Searches first in this model, then in the list of predefined units.

        Raises a :class:`CellMLError` is no unit is found.
        """
        try:
            return self._units[name]
        except KeyError:
            return Units.find_units(name)

    def find_units_name(self, myokit_unit):
        """
        Attempts to find a string name for the given :class:`myokit.Unit`.

        Searches first in this model, then in the list of predefined units. If
        multiple units definitions have the same :class:`myokit.Unit`, the last
        added name is returned.

        Raises a :class:`CellMLError` is no appropriate unit is found.
        """
        try:
            return self._myokit_unit_to_name[myokit_unit]
        except KeyError:
            return Units.find_units_name(myokit_unit)

    def free_variable(self):
        """
        Returns the free variable set with :meth:`set_free_variable`.
        """
        return self._free_variable

    @staticmethod
    def from_myokit_model(model, version='1.0'):
        """
        Creates a CellML :class:`Model` from a :class:`myokit.Model`.

        The CellML version to use can be set with ``version``, which must be
        either "1.0" or "1.1".
        """
        # Model must be valid
        # Otherwise could have cycles, invalid references, etc.
        model.validate()

        # Get name for CellML model
        name = model.name()
        if name is None:
            name = 'unnamed_myokit_model'
        else:
            try:
                name = clean_identifier(name)
            except ValueError:
                name = 'unnamed_myokit_model'

        # Create CellML model
        m = Model(name, version)

        # Valid model always has a time variable
        time = model.time()

        # Method to obtain or infer variable unit
        def variable_unit(variable, time_unit):
            """Returns variable.unit(), or attempts to infer it if not set."""
            unit = variable.unit()
            if unit is not None:
                return unit

            rhs = variable.rhs()
            if rhs is not None:
                try:
                    # Tolerant evaluation, see above. Result may be None.
                    unit = rhs.eval_unit(myokit.UNIT_TOLERANT)
                except myokit.IncompatibleUnitError:
                    return None
                if variable.is_state():
                    if unit is not None and time_unit is not None:
                        # RHS is divided by time unit, so multiply
                        unit *= time_unit
            return unit

        # Time unit, used to infer units of state variables
        # (May itself be inferred)
        time_unit = variable_unit(time, None)

        # Gather unit objects used in Myokit model, and gather numbers without
        # units that will need to be replaced.
        used = set()
        numbers_without_units = {}
        for variable in model.variables(deep=True):

            # Add variable unit, or unit inferred from variable's RHS
            used.add(variable_unit(variable, time_unit))

            # Check number units
            rhs = variable.rhs()
            if rhs is not None:
                for e in rhs.walk(myokit.Number):
                    u = e.unit()
                    if u is None:
                        numbers_without_units[e] = myokit.Number(
                            e.eval(), myokit.units.dimensionless)
                    used.add(u)

        # Remove 'None' from the set of used units
        if None in used:
            used.remove(None)

        # Add units to models, and store mapping from objects to names
        unit_map = dict(Units._si_units_r)
        for unit in used:
            if unit not in unit_map:
                name = create_unit_name(unit)
                unit_map[unit] = name
                m.add_units(name, unit)

        # Map None to dimensionless
        unit_map[None] = 'dimensionless'

        # Variable naming strategy:
        # 1. Component level variables always use their unqualified names
        # 2. Nested variables use their unames
        # 3. Variable-in variables use their unames

        # Create unames in model
        model.create_unique_names()

        # Dict of interface-in variables that need to be added to each
        # component
        in_variables = {component: set() for component in model}

        # Dict mapping Myokit variables to CellML variables, per component
        var_map = {component: dict() for component in model}

        # Add components
        for component in model:
            c = m.add_component(component.name())

            # Local var_map entry
            local_var_map = var_map[component]

            # Add variables
            for variable in component:

                # Check if this variable is needed in other components
                interface = 'none'

                # Get all refs to variable's LHS
                refs = set(variable.refs_by())
                if variable.is_state():
                    # If it's a state, refs to dot(x) also require the time
                    # variable
                    if refs:
                        refs.add(time)

                    # And refs should include references to the state itself
                    refs = refs.union(variable.refs_by(True))

                elif variable is time:
                    # If this is the time variable, then ensure that all states
                    # have a local reference to it.
                    for ref in model.states():
                        refs.add(ref)

                # Update lists of required interface-in variables, and set
                # interface to 'out' if needed
                for user in refs:
                    parent = user.parent(myokit.Component)
                    if parent != component:
                        in_variables[parent].add(variable)
                        interface = 'out'

                # Get declared or inferred variable unit
                unit = variable_unit(variable, time_unit)

                # Add variable
                local_var_map[variable] = v = c.add_variable(
                    variable.name(),
                    unit_map[unit],
                    public_interface=interface
                )

                # Copy meta data
                for key, value in variable.meta.items():
                    v.meta[key] = value

                # Create cmeta id for variables with an oxmeta annotation
                if 'oxmeta' in variable.meta:
                    v.set_cmeta_id(variable.uname())

                # Add nested variables
                for nested in variable.variables(deep=True):
                    local_var_map[nested] = v = c.add_variable(
                        nested.uname(),
                        unit_map[variable_unit(nested, time_unit)])

                    # Copy meta-data
                    for key, value in nested.meta.items():
                        v.meta[key] = value

                    # Create cmeta id for variables with an oxmeta annotation
                    if 'oxmeta' in nested.meta:
                        v.set_cmeta_id(nested.uname())

        # Add interface-in variables
        for component, variables in in_variables.items():
            c = m[component.name()]

            # Local var_map entry
            local_var_map = var_map[component]

            # Add variables
            for variable in variables:
                local_var_map[variable] = v = c.add_variable(
                    variable.uname(),
                    unit_map[variable_unit(variable, time_unit)],
                    public_interface='in',
                )

                # Add connection
                source = m[variable.parent().name()][variable.name()]
                m.add_connection(v, source)

        # Set RHS equations
        for component in model:

            # Create dict of Name substitutions
            local_var_map = var_map[component]
            subst = {
                myokit.Name(x): myokit.Name(y)
                for x, y in local_var_map.items()}

            # Add number substitutions
            for x, y in numbers_without_units.items():
                subst[x] = y

            # Set RHS equations
            for variable in component.variables(deep=True):
                v = local_var_map[variable]

                # Create RHS with updated numbers and references
                rhs = variable.rhs().clone(subst=subst)

                # Free variable shouldn't have a value
                if variable is time:
                    m.set_free_variable(v)

                # Promote states and set rhs and initial value
                elif variable.is_state():
                    v.set_is_state(True)
                    v.set_initial_value(variable.state_value())
                    v.set_rhs(rhs)

                # Store literals (single number) in initial value
                elif isinstance(rhs, myokit.Number):
                    v.set_initial_value(rhs.eval())

                # For all other use rhs
                else:
                    v.set_rhs(rhs)

        # Return model
        return m

    def __getitem__(self, key):
        return self._components[key]

    def __iter__(self):
        return iter(self._components.values())

    def __len__(self):
        return len(self._components)

    def myokit_model(self):
        """
        Returns this model's :class:`myokit.Model` equivalent.
        """
        # Make sure model is valid before starting
        self.validate()

        # Create model
        m = myokit.Model(self.name())
        m.meta['author'] = 'Myokit CellML 1 API'

        # Copy meta data
        for key, value in self.meta.items():
            m.meta[key] = value

        # Gather set of variables that are used in (local) equations
        used = set()
        for component in self:
            for variable in component:
                rhs = variable.rhs()
                if rhs is not None:
                    for ref in rhs.references():
                        used.add(ref.var())

        # Gather dict of variables that need unit conversion, mapping their
        # CellML variables to a tuple of units (from, to).
        # This is the set of variables that are non-local, have a different
        # unit than their source, and are referenced by other variables.
        needs_conversion = set()
        for component in self:
            for variable in component:
                if variable.is_local() or variable not in used:
                    continue

                # Compare units
                ufrom = variable.value_source().units().myokit_unit()
                uto = variable.units().myokit_unit()
                if ufrom != uto:
                    needs_conversion.add(variable)

        # Add components
        for component in self:
            c = m.add_component(component.name())

            # Copy meta data
            for key, value in component.meta.items():
                c.meta[key] = value

            # Create local variables or variables that need unit conversion
            for variable in component:
                if variable.is_local() or variable in needs_conversion:
                    v = c.add_variable(variable.name())
                    v.set_unit(variable.units().myokit_unit())

                    # Copy meta data
                    for key, value in variable.meta.items():
                        v.meta[key] = value

        # Add equations
        undefined_variables = []
        for component in self:
            c = m[component.name()]

            # Create dict of variable reference substitutions
            var_map = {}
            for variable in component:
                cname = myokit.Name(variable)
                if variable.is_local() or variable in needs_conversion:
                    mname = myokit.Name(c[variable.name()])
                else:
                    source = variable.value_source()
                    source = m[source.component().name()][source.name()]
                    mname = myokit.Name(source)
                var_map[cname] = mname

            # Add equations
            for variable in component:

                # Add local variable equations
                if variable.is_local():
                    v = c[variable.name()]

                    # At this point, the model has been validated so there can
                    # only be one variable without an rhs or initial value, and
                    # this is either known to be the free variable or assumed
                    # to be (if not explicitly set by the user).

                    # Add equation
                    rhs = variable.rhs_or_initial_value()
                    if variable.is_free() or rhs is None:
                        # Use zero for free or undefined variables
                        v.set_rhs(
                            myokit.Number(0, variable.units().myokit_unit()))
                        if variable.is_free():
                            v.set_binding('time')
                        else:
                            undefined_variables.append(v)
                    else:
                        # Add RHS with Myokit references
                        rhs = rhs.clone(subst=var_map)

                        v.set_rhs(rhs)
                        if variable.is_state():
                            init = variable.initial_value()
                            v.promote(0 if init is None else init)

                # Add local copies of variables requiring unit conversion
                elif variable in needs_conversion:

                    # Get Myokit variable
                    v = c[variable.name()]

                    # Get Myokit variable for source
                    r = variable.value_source()
                    r = m[r.component().name()][r.name()]

                    # Get conversion factor
                    try:
                        f = myokit.Unit.conversion_factor(r.unit(), v.unit())
                        f = myokit.Number(f)
                    except myokit.IncompatibleUnitError:
                        warnings.warn(
                            'Unable to determine unit conversion factor for '
                            + str(v) + ', from ' + str(v.unit()) + ' to '
                            + str(r.unit()) + '.')
                        f = myokit.Number(1)

                    # Add equation
                    v.set_rhs(myokit.Multiply(myokit.Name(r), f))

        # Check that a binding to time has been made
        if m.binding('time') is None:
            if undefined_variables:
                undefined_variables[0].set_binding('time')

        return m

    def name(self):
        """
        Returns this model's name.
        """
        return self._name

    def _register_cmeta_id(self, cmeta_id, element):
        """
        Should be called whenever a cmeta:id is set for a CellML element in
        this model (or for the model itself).

        Arguments

        ``cmeta_id``
            A cmeta:id string, unique within this model.
        ``element``
            An :class:`AnnotatableElement` object.

        """
        # Check
        cmeta_id = str(cmeta_id).strip()
        if not cmeta_id:
            raise CellMLError('A cmeta:id must be a non-empty string.')
        if cmeta_id in self._cmeta_ids:
            raise CellMLError(
                'A cmeta:id must be unique within a model (8.5.1).')

        # And store
        self._cmeta_ids[cmeta_id] = element

    def set_free_variable(self, variable):
        """
        Tells this model which variable to regard as the free variable (with
        respect to which derivatives are taken).
        """
        if variable is not None and variable._model is not self:
            raise ValueError('Given variable must be from this model.')

        # Check interface
        if variable is not None and (variable._public_interface == 'in' or
                                     variable._private_interface == 'in'):
            raise CellMLError(
                'The free variable cannot have an "in" interface.')

        # Unset previous
        if self._free_variable is not None:
            self._free_variable._is_free = False

        # Set new
        self._free_variable = variable
        if variable is not None:
            variable._is_free = True

    def __str__(self):
        return 'Model[@name="' + self._name + '"]'

    def units(self):
        """
        Returns an iterator over the :class:`Units` objects in this model.
        """
        # Note: Must use _by_name here, other one doesn't necessarily contain
        # all units objects (only names are unique).
        return iter(self._units.values())

    def _unregister_cmeta_id(self, cmeta_id):
        """
        Should be called whenever a cmeta:id for a CellML element in this model
        (or for this model itself) is unset.
        """
        del self._cmeta_ids[cmeta_id]

    def validate(self):
        """
        Validates this model, raising a :class:`CellMLError` if an errors are
        found.
        """
        # Validate components and variables
        for c in self._components.values():
            c._validate()

        # Check at most one variable doesn't have a source (one free variable
        # is allowed)
        free = set()
        for c in self:
            for v in c:
                if v.value_source() is v:
                    if v.rhs() is None and v.initial_value() is None:
                        free.add(v)

        if len(free) > 1:
            warnings.warn('More than one variable does not have a value.')

        elif self._free_variable is not None and len(free) == 1:
            free = free.pop()
            if self._free_variable is not free:
                warnings.warn(
                    'No value is defined for the variable "'
                    + free.name() + '", but "' + self._free_variable.name()
                    + '" is listed as the free variable.')

    def version(self):
        """
        Returns the CellML version this model is in.
        """
        return self._version


class Units(object):
    """
    Represents a CellML units definition, should not be created directly but
    only via :meth:`Model.add_units()` or :meth:`Component.add_units()`.

    Arguments:

    ``name``
        A string name, used to refer to these units in the model.
    ``myokit_unit``
        A :class:`myokit.Unit` representing these units.
    ``predefined``
        Set to ``True`` when creating an object for a predefined name. This is
        only used internally.

    """
    def __init__(self, name, myokit_unit, predefined=False):

        # Check and store name
        if not is_valid_identifier(name):
            raise CellMLError(
                'Units name must be a valid CellML identifier (5.4.1.2).')
        if not predefined and name in self._si_units:
            raise CellMLError(
                'Units name "' + name + '" overlaps with a predefined name'
                ' (5.4.1.2).')
        self._name = name

        # Check and store Myokit unit
        if not isinstance(myokit_unit, myokit.Unit):
            raise ValueError(
                'The argument `myokit_unit` must be a myokit.Unit object.')
        self._myokit_unit = myokit_unit

    @classmethod
    def find_units(cls, name):
        """
        Searches for a predefined unit with the given ``name`` and returns a
        :class:`Units` object representing it.

        If no such unit is found a :class:`CellMLError` is raised.
        """
        # Check for unsupported units
        if name == 'celsius':
            raise UnsupportedBaseUnitsError('celsius')

        # Check if we have a cached object for this
        obj = cls._si_unit_objects.get(name, None)
        if obj is None:

            # Check if this is an si unit
            myokit_unit = cls._si_units.get(name, None)

            # If not raise error (and one that makes sense even if this was
            # called via a model or component units lookup).
            if myokit_unit is None:
                raise CellMLError('Unknown units name "' + str(name) + '".')

            # Create and store object
            obj = cls(name, myokit_unit, predefined=True)
            cls._si_unit_objects[name] = obj

        # Return
        return obj

    @classmethod
    def find_units_name(cls, myokit_unit):
        """
        Attempts to find a string name for the given :class:`myokit.Unit`.

        Raises a :class:`CellMLError` is no appropriate unit is found.
        """
        try:
            return cls._si_units_r[myokit_unit]
        except KeyError:
            raise CellMLError(
                'No name found for myokit unit ' + str(myokit_unit) + '.')

    def myokit_unit(self):
        """
        Returns the :class:`Myokit.Unit` equivalent for this units definition.
        """
        return self._myokit_unit

    def name(self):
        """
        Returns the string name for this units definition.
        """
        return self._name

    @classmethod
    def parse_unit_row(cls, units, prefix=None, exponent=None, multiplier=None,
                       context=None):
        """
        Creates a :class:`myokit.Unit` using the information found in a single
        CellML ``unit`` element.

        Arguments

        ``units``
            The name of the units to start from.
        ``prefix``
            An optional argument that can be either a string from one of the
            predefined units prefixes, or an integer. If an integer is given
            the unit is scaled by ``10**prefix``. Used to make e.g. ``cm``.
        ``exponent``
            An optional exponent (power) for this unit, used to make e.g.
            ``m**2`` or ``cm**2``.
        ``multiplier``
            An optional multiplier for this unit, used to make e.g. ``inches``.
            Note that exponentiation affects prefixes, but not multipliers.
        ``context``
            An optional :class:`Model` or :class:`Component` to use when
            looking up ``units`` names. If not given, only the SI units will be
            supported.

        """
        # Find units object to start from
        if context is None:
            unit = cls.find_units(units)
        else:
            unit = context.find_units(units)
        unit = unit.myokit_unit()

        # Handle prefix
        if prefix is not None:
            p = cls._si_prefixes.get(prefix, None)
            if p is None:
                try:
                    # Test if can convert to float
                    p = float(prefix)
                except ValueError:
                    pass
                else:
                    # Test if is integer
                    if int(p) != p:
                        p = None
            if p is None:
                raise CellMLError(
                    'Units prefix must be a string from the list of known'
                    ' prefixes or an integer (5.4.2.3).')

            # Apply prefix to unit

            # float(10**309) is the first int that doesn't fit in a float
            if p > 309:
                raise CellMLError('Unit prefix too large: 10^' + str(p))
            unit *= 10**int(p)

        # Handle exponent (note: prefix is exponentiated, multiplier is not).
        if exponent is not None:
            try:
                e = float(exponent)
            except ValueError:
                raise CellMLError(
                    'Unit exponent must be a real number (5.4.2.4).')

            # Apply exponent to unit
            unit **= e

        # Handle multiplier
        if multiplier is not None:
            try:
                m = float(multiplier)
            except ValueError:
                raise CellMLError(
                    'Unit multiplier must be a real number (5.4.2.5).')

            # Apply multiplier to unit
            unit *= m

        # Return
        return unit

    @classmethod
    def si_unit_names(cls):
        """
        Returns an iterator over the predefined unit names.
        """
        return cls._si_units.keys()

    def __str__(self):
        return 'Units[@name="' + self._name + '"]'

    # Predefined units in CellML, name to Unit
    _si_units = {
        'ampere': myokit.units.A,
        'becquerel': myokit.units.Bq,
        'candela': myokit.units.cd,
        'celsius': None,
        'coulomb': myokit.units.C,
        'dimensionless': myokit.units.dimensionless,
        'farad': myokit.units.F,
        'gram': myokit.units.g,
        'gray': myokit.units.Gy,
        'henry': myokit.units.H,
        'hertz': myokit.units.Hz,
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
        'radian': myokit.units.radian,
        'second': myokit.units.s,
        'siemens': myokit.units.S,
        'sievert': myokit.units.Sv,
        'steradian': myokit.units.steradian,
        'tesla': myokit.units.T,
        'volt': myokit.units.V,
        'watt': myokit.units.W,
        'weber': myokit.units.Wb,
    }

    # Predefined Units objects
    _si_unit_objects = {}

    # Predefined units in CellML, Unit object to name
    _si_units_r = {
        myokit.units.A: 'ampere',
        myokit.units.Bq: 'becquerel',
        myokit.units.cd: 'candela',
        myokit.units.C: 'coulomb',
        myokit.units.dimensionless: 'dimensionless',
        myokit.units.F: 'farad',
        myokit.units.g: 'gram',
        myokit.units.Gy: 'gray',
        myokit.units.H: 'henry',
        myokit.units.hertz: 'hertz',
        myokit.units.joule: 'joule',
        myokit.units.kat: 'katal',
        myokit.units.K: 'kelvin',
        myokit.units.kg: 'kilogram',
        myokit.units.L: 'litre',
        myokit.units.lumen: 'lumen',
        myokit.units.lux: 'lux',
        myokit.units.m: 'metre',
        myokit.units.mol: 'mole',
        myokit.units.N: 'newton',
        myokit.units.ohm: 'ohm',
        myokit.units.Pa: 'pascal',
        myokit.units.s: 'second',
        myokit.units.S: 'siemens',
        myokit.units.sievert: 'sievert',
        myokit.units.T: 'tesla',
        myokit.units.V: 'volt',
        myokit.units.W: 'watt',
        myokit.units.weber: 'weber',
    }

    # Recognised unit prefixes, name to multiplier
    _si_prefixes = {
        'yotta': 24,
        'zetta': 21,
        'exa': 18,
        'peta': 15,
        'tera': 12,
        'giga': 9,
        'mega': 6,
        'kilo': 3,
        'hecto': 2,
        'deka': 1,            # US Style, as defined in CellML 1.0
        'deca': 1,            # SI prefix
        'deci': -1,
        'centi': -2,
        'milli': -3,
        'micro': -6,
        'nano': -9,
        'pico': -12,
        'femto': -15,
        'atto': -18,
        'zepto': -21,
        'yocto': -24,
    }


class Variable(AnnotatableElement):
    """
    Represents a model variable, should not be created directly but only via
    :meth:`Component.add_variable()`.

    Arguments

    ``component``
        This variable's parent :class:`Component`.
    ``name``
        This variable's name (a valid CellML identifier string).
    ``units``
        The string name of a units object known to this variable's component.
    ``public_interface``
        The variable's public interface.
    ``private_interface``
        The variable's private interface.

    """
    def __init__(self, component, name, units, public_interface='none',
                 private_interface='none'):
        super(Variable, self).__init__(component.model())

        # Store component
        self._component = component

        # Check and store name
        if not is_valid_identifier(name):
            raise CellMLError(
                'Variable name must be a valid CellML identifier (3.4.3.2).')
        self._name = name

        # Check and store units
        try:
            self._units = component.find_units(units)
        except UnsupportedBaseUnitsError as e:
            raise UnsupportedBaseUnitsError(
                'Variable units attribute references the unsupported base'
                ' units "' + e.units + '".')
        except CellMLError:
            raise CellMLError(
                'Variable units attribute must reference a units element in'
                ' the current component or model, or one of the predefined'
                ' units, found "' + str(units) + '" (3.4.3.3).')

        # Check and store interfaces
        if public_interface not in ['none', 'in', 'out']:
            raise CellMLError(
                'Public interface must be "in", "out", or "none" (3.4.3.4).')
        if private_interface not in ['none', 'in', 'out']:
            raise CellMLError(
                'Private interface must be "in", "out", or "none" (3.4.3.5).')
        # Can't have two "in" interfaces
        if public_interface == private_interface == 'in':
            raise CellMLError(
                'Public and private interface can not both be "in" (3.4.3.6).')
        self._public_interface = public_interface
        self._private_interface = private_interface

        # Initial value
        self._initial_value = None

        # RHS
        self._rhs = None

        # Is this a state variable?
        self._is_state = False

        # Is this the free variable?
        self._is_free = False

        # If this variable derives its value from another variable, that
        # variable is listed here.
        self._source = None

    def component(self):
        """
        Return this variable's component.
        """
        return self._component

    def initial_value(self):
        """
        Returns this variable's initial value, or ``None`` if it is not set.
        """
        return self._initial_value

    def is_local(self):
        """
        Checks if this variable defines its own value.
        """
        return self._source is None

    def is_free(self):
        """
        Checks if this variable has been marked as the free variable.

        See :meth:`Model.set_free_variable()`.
        """
        return self._is_free

    def is_state(self):
        """
        Checks if this variable has been marked as a state variable.
        """
        return self._is_state

    def model(self):
        """
        Return this variable's model.
        """
        return self._model

    def name(self):
        """
        Returns this variable's name.
        """
        return self._name

    def public_interface(self):
        """
        Returns this variable's public interface.
        """
        return self._public_interface

    def private_interface(self):
        """
        Returns this variable's private interface.
        """
        return self._private_interface

    def rhs(self):
        """
        Returns this variable's right-hand side.
        """
        return self._rhs

    def rhs_or_initial_value(self):
        """
        For non-states, returns this variable's RHS or a :class:`myokit.Number`
        representing the initial value if no RHS is set. For states always
        returns the RHS.
        """
        if self._is_state:
            return self._rhs
        if self._rhs is None and self._initial_value is not None:
            return myokit.Number(
                self._initial_value, self._units.myokit_unit())
        return self._rhs

    def set_initial_value(self, value):
        """
        Sets this variable's intial value (must be a number or ``None``).
        """
        # Allow unsetting with ``None``
        if value is None:
            self._initial_value = None
            return

        # Check interface
        if self._public_interface == 'in' or self._private_interface == 'in':
            i = 'public' if self._public_interface == 'in' else 'private'
            raise CellMLError(
                'An initial value cannot be set for ' + str(self) + ', which'
                ' has ' + i + '_interface="in" (3.4.3.8).')

        # Check and store
        try:
            self._initial_value = float(value)
        except ValueError:
            if self._model.version() == '1.0':
                raise CellMLError(
                    'If given, a variable initial_value must be a real number'
                    ' (3.4.3.7).')
            else:
                raise CellMLError(
                    'If given, a variable initial_value must be a real number'
                    ' (using variables as initial values is not supported).')

    def set_is_state(self, state):
        """
        Set whether this variable is a state variable or not.
        """
        # Check interface
        if self._public_interface == 'in' or self._private_interface == 'in':
            i = 'public' if self._public_interface == 'in' else 'private'
            raise CellMLError(
                'State variables can not have an "in" interface.')

        self._is_state = bool(state)

    def set_rhs(self, rhs):
        """
        Sets a right-hand side expression for this variable.

        The given ``rhs`` must be a :class:`myokit.Expression` tree where any
        :class:`myokit.Name` objects have a CellML :class:`Variable` as their
        value.
        """
        # Check interface
        if self._public_interface == 'in' or self._private_interface == 'in':
            i = 'public' if self._public_interface == 'in' else 'private'
            raise CellMLError(
                'An equation cannot be set for ' + str(self) + ', which has '
                + i + '_interface="in" (4.4.4).')

        # Check all references in equation are known and local
        if rhs is not None:
            for ref in rhs.references():
                var = ref.var()
                if var._component is not self._component:
                    raise CellMLError(
                        'A variable RHS can only reference variables from the'
                        ' same component, found: ' + str(var) + '.')

            # Check all units are known
            numbers_without_units = {}
            for x in rhs.walk(myokit.Number):
                # Replace None with dimensionless
                if x.unit() is None:
                    numbers_without_units[x] = myokit.Number(
                        x.eval(), myokit.units.dimensionless)
                else:
                    try:
                        self._component.find_units_name(x.unit())
                    except CellMLError:
                        raise CellMLError(
                            'All units appearing in a variable\'s RHS must be'
                            ' known to its component, found: ' + str(x.unit())
                            + '.')
            if numbers_without_units:
                rhs = rhs.clone(subst=numbers_without_units)

        # Store
        self._rhs = rhs

    def source(self):
        """
        If this :class:`Variable` has an "in" interface and is connected to
        another variable, this method returns that variable.

        If not, it returns ``None``.
        """
        return self._source

    def __str__(self):
        return (
            'Variable[@name="' + self._name + '"] in ' + str(self._component))

    def units(self):
        """
        Returns the units this variable is in (as a :class:`Units` object).
        """
        return self._units

    def _validate(self):
        """
        Validates this variable, raising a :class:`CellMLError` if any errors
        are found.
        """
        # Check that variables with an in interface are connected
        # Sort of allowed in the spec ?
        if self._public_interface == 'in' or self._private_interface == 'in':
            i = 'public' if self._public_interface == 'in' else 'private'
            if self._source is None:
                warnings.warn(
                    str(self) + ' has ' + i + '_interface="in", but is not'
                    ' connected to a variable with an appropriate "out"')

        # Check that state variables define two values
        elif self._is_state:

            if self._initial_value is None:
                warnings.warn(
                    'State ' + str(self) + ' has no initial value.')

            if self._rhs is None:
                raise CellMLError(
                    'State ' + str(self) + ' must have a defining equation.')

        # Check that other variables define a value
        elif self._rhs is None:
            if self._initial_value is None and not self._is_free:
                warnings.warn('No value set for ' + str(self) + '.')

        # And only one value
        elif self._initial_value is not None:
            raise CellMLError(
                'Overdefined: ' + str(self) + ' has both an initial value and'
                ' a defining equation (which is not an ODE).')

    def value_source(self):
        """
        Returns the :class:`Variable` that this variable derives its value
        from.

        If the variable has a defining equation or an initial value, this will
        return the variable itself. If it is connected to another variable, it
        will follow the chain of dependencies until a variable with an equation
        or value is found.
        """
        var = self
        while var._source is not None:
            var = var._source
            assert var is not self
        return var

