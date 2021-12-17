#
# CellML 2.0 API
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

# Strings in Python2 and Python3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str


# Data types
_cellml_identifier = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
_cellml_integer = re.compile(r'^[+-]?[0-9]+$')
_real = r'[+-]?(([0-9]*\.[0-9]+)|([0-9]+\.?[0-9]*))'
_cellml_basic_real = re.compile(r'^' + _real + r'$')
_cellml_real = re.compile(r'^' + _real + r'([eE][+-]?[0-9]+)?$')


def is_identifier(name):
    """
    Tests if the given ``name`` is a valid CellML 2.0 identifier.

    This method returns True if (and only if) the identifier

    1. begins with a letter (from the basic latin set)
    2. only contains letters, numbers, and underscores.

    """
    return _cellml_identifier.match(name) is not None


def is_integer_string(text):
    """
    Tests if the given ``text`` is a valid CellML 2.0 integer string.
    """
    return _cellml_integer.match(text) is not None


def is_basic_real_number_string(text):
    """
    Tests if the given ``text`` is a valid CellML 2.0 basic real number string.
    """
    return _cellml_basic_real.match(text) is not None


def is_real_number_string(text):
    """
    Tests if the given ``text`` is a valid CellML 2.0 basic real number string.
    """
    return _cellml_real.match(text) is not None


def clean_identifier(name):
    """
    Checks if ``name`` is a valid CellML 2.0 identifier and if not attempts to
    make it into one.

    Raises a ``ValueError`` if it can't create a valid identifier.
    """
    if is_identifier(name):
        return name

    # Replace spaces and hyphens with underscores
    clean = re.sub(r'[\s-]', '_', name)

    # Check if valid and return
    if is_identifier(clean):
        return clean
    raise ValueError(
        'Unable to create a valid CellML 2.0 identifier from "' + str(name)
        + '".')


def create_unit_name(unit):
    """
    Creates an almost readable name for a Myokit ``unit``.
    """
    # Get preferred name from Myokit's representation (e.g. [kg]) but trim off
    # the brackets
    name = str(unit)[1:-1]

    # If this is a valid name, return
    if is_identifier(name):
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
    Represents a CellML 2.0 element that can be annotated (using a public dict
    ``meta`` that stores key:value pairs).
    """

    def __init__(self):

        # Public meta data
        self.meta = {}


class CellMLError(myokit.MyokitError):
    """
    Raised when an invalid CellML 2.0 model is created or detected, or when a
    model uses CellML features that Myokit does not support.
    """


class Component(AnnotatableElement):
    """
    Represents a model component; should not be created directly but only via
    :meth:`Model.add_component()`.
    """
    def __init__(self, model, name):
        super(Component, self).__init__()

        # Store model
        self._model = model

        # Check and store name
        if not is_identifier(name):
            raise CellMLError(
                'Component name must be a valid CellML identifier.')
        self._name = name

        # This component's encapsulation relationships
        self._parent = None
        self._children = set()

        # This component's variables
        self._variables = collections.OrderedDict()

    def add_variable(self, name, units, interface='none'):
        """
        Adds a variable with the given ``name`` and ``units``.

        Arguments

        ``name``
            A valid CellML identifier (string).
        ``units``
            The name of a units definition known to this component or its
            parent model.
        ``interface``
            The variable's interface.

        """
        # Check name uniqueness
        if name in self._variables:
            raise CellMLError(
                'Variable name must be unique within component.')

        # Create, store, and return
        self._variables[name] = v = Variable(self, name, units, interface)
        return v

    def children(self):
        """
        Returns an iterator over any encapsulated child components.
        """
        return iter(self._children)

    def __contains__(self, key):
        return key in self._variables

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
                raise ValueError('Parent must be a cellml.Component.')
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
                    'Encapsulation hierarchy cannot be circular.')
            parent = parent._parent

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
    Represents a CellML 2.0 model.

    Support notes:

    - Imports are not supported.
    - Reset rules are not supported.
    - Using variables in ``initial_value`` attributes is not supported.
    - Defining new base units is not supported.
    - All equations must be of the form ``x = ...`` or ``dx/dt = ...``.
    - Models that take derivatives with respect to more than one variable are
      not supported.

    Arguments:

    ``name``
        A valid CellML identifier string.
    ``version``
        A string representing the CellML version this model is in (must be
        '2.0').

    """
    def __init__(self, name, version='2.0'):
        super(Model, self).__init__()

        # Check and store name
        if not is_identifier(name):
            raise CellMLError(
                'Model name must be a valid CellML identifier.')
        self._name = name

        # Check and store version
        if version not in ('2.0'):
            raise ValueError(
                'Only CellML 2.0 models are supported by this API.')
        self._version = version

        # This model's components
        self._components = collections.OrderedDict()

        # This model's units
        self._units = {}

        # Lookup myokit unit to name (note this lookup may not be unique)
        self._myokit_unit_to_name = {}

        # Variable of integration
        self._voi = None

        # Note:
        #  Encapsulation relationships are stored inside the components.

        # Connections create connected variable sets, but are stored in a
        # second structure so that the original connection pairs don't go lost.
        self._connections = []

    def add_component(self, name):
        """
        Adds an empty component with the given ``name``.
        """
        # Check uniqueness
        if name in self._components:
            raise CellMLError('Component name must be unique within model.')

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
                             ' cellml.v2.Variable.')
        if not isinstance(variable_2, Variable):
            raise ValueError('Argument variable_2 must be a'
                             ' cellml.v2.Variable.')
        if variable_1._model is not self:
            raise ValueError('Argument variable_1 must be a variable from this'
                             ' model.')
        if variable_2._model is not self:
            raise ValueError('Argument variable_2 must be a variable from this'
                             ' model.')

        # Check variables are distinct.
        if variable_1 is variable_2:
            raise CellMLError(
                'Variables cannot be connected to themselves.')

        # Check components are distinct.
        component_1 = variable_1.component()
        component_2 = variable_2.component()
        if component_1 is component_2:
            raise CellMLError('Variables cannot be connected to variables in'
                              ' the same component.')

        # Determine the relevant interfaces.
        interface_1 = interface_2 = None
        if component_1.parent() == component_2.parent():
            interface_1 = interface_2 = 'public'
        elif component_1.parent() == component_2:
            interface_1 = 'public'
            interface_2 = 'private'
        elif component_2.parent() == component_1:
            interface_1 = 'private'
            interface_2 = 'public'
        else:
            raise CellMLError(
                'Unable to connect ' + str(variable_1) + ' to '
                + str(variable_2) + ': connections can only be made between'
                ' components that are siblings or have a parent-child'
                ' relationship.')

        # Check the variables' interfaces.
        if interface_1 not in variable_1.interface():
            raise CellMLError(
                'Unable to connect ' + str(variable_1) + ' to '
                + str(variable_2) + ': variable_1 requires the ' + interface_1
                + ' interface, but is set to ' + variable_1.interface() + '.')
        if interface_2 not in variable_2.interface():
            raise CellMLError(
                'Unable to connect ' + str(variable_1) + ' to '
                + str(variable_2) + ': variable_2 requires the ' + interface_2
                + ' interface, but is set to ' + variable_2.interface() + '.')

        # Check the variables' units.
        unit_1 = variable_1.units().myokit_unit()
        unit_2 = variable_2.units().myokit_unit()
        if not myokit.Unit.can_convert(unit_1, unit_2):
            raise CellMLError(
                'Unable to connect ' + str(variable_1) + ' to '
                + str(variable_2) + ': Connected variables must have'
                ' compatible units. Found ' + str(variable_1.units())
                + ' and ' + str(variable_2.units()) + '.')

        # Check the variables aren't already connected
        if variable_1 in variable_2._cset:
            raise CellMLError(
                'Variables cannot be connected twice: ' + str(variable_1)
                + ' is already in the connected variable set of '
                + str(variable_2) + '.')

        # Connect the variables, by merging their connected variable sets.
        ConnectedVariableSet._merge(variable_1._cset, variable_2._cset)

        # Store the connection
        self._connections.append((variable_1, variable_2))

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
                'Units defined in the same model cannot have the same name.')

        # Create, store, and return
        units = Units(name, myokit_unit)
        self._units[name] = units
        self._myokit_unit_to_name[myokit_unit] = name
        return units

    def clone(self):
        """
        Returns a copy of this model.
        """
        def copy_metadata(x, y):
            # Copy meta data: May need to be made smarter in the future
            for k, v in x.meta.items():
                y.meta[k] = v

        # Create model
        m = Model(self._name, self._version)
        copy_metadata(self, m)

        # Clone units
        for name, units in self._units.items():
            m.add_units(name, units.myokit_unit())

        # Clone bare components and variables
        cmap = {}
        vmap = {}
        for component_1 in self:
            component_2 = m.add_component(component_1.name())
            cmap[component_1] = component_2
            copy_metadata(component_1, component_2)

            for variable_1 in component_1:
                variable_2 = component_2.add_variable(
                    variable_1.name(),
                    variable_1.units().name(),
                    variable_1.interface())
                vmap[variable_1] = variable_2
                copy_metadata(variable_1, variable_2)

        # Clone encapsulation relationships
        for child_1, child_2 in cmap.items():
            parent_1 = child_1.parent()
            if parent_1 is not None:
                child_2.set_parent(cmap[parent_1])

        # Clone connections
        for v1, v2 in self._connections:
            m.add_connection(vmap[v1], vmap[v2])

        # Clone equations and initial values
        nmap = {myokit.Name(x): myokit.Name(y) for x, y in vmap.items()}
        for component_1 in self:
            for variable_1 in component_1:
                if variable_1 is variable_1.equation_variable():
                    lhs, rhs = variable_1.equation()
                    vmap[variable_1].set_equation(myokit.Equation(
                        lhs.clone(subst=nmap), rhs.clone(subst=nmap)))
                if variable_1 is variable_1.initial_value_variable():
                    vmap[variable_1].set_initial_value(
                        variable_1.initial_value().clone(subst=nmap))

        # Clone variable of integration
        if self._voi is not None:
            m._voi = vmap[self._voi]

        return m

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

    def connections(self):
        """
        Returns an iterator over all connections in this model (as variable
        tuples).
        """
        return iter(self._connections)

    def __contains__(self, key):
        return key in self._components

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

    @staticmethod
    def from_myokit_model(model, version='2.0'):
        """
        Creates a CellML :class:`Model` from a :class:`myokit.Model`.

        The CellML version to use can be set with ``version`` (which must be
        "2.0").
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

            # Add variable unit, or unit evaluated from variable's RHS
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

        # Dict of alias variables that need to be added to each component
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
                        interface = 'public'

                # Get variable unit, or infer from RHS if None
                unit = variable_unit(variable, time_unit)

                # Add variable
                local_var_map[variable] = v = c.add_variable(
                    variable.name(),
                    unit_map[unit],
                    interface=interface
                )

                # Copy meta data
                for key, value in variable.meta.items():
                    v.meta[key] = value

                # Create id for variables with an oxmeta annotation
                # TODO
                # if 'oxmeta' in variable.meta:
                #    v.set_id(variable.uname())

                # Add nested variables
                for nested in variable.variables(deep=True):
                    local_var_map[nested] = v = c.add_variable(
                        nested.uname(),
                        unit_map[variable_unit(nested, time_unit)])

                    # Copy meta-data
                    for key, value in nested.meta.items():
                        v.meta[key] = value

                    # Create id for variables with an oxmeta annotation
                    # TODO
                    # if 'oxmeta' in nested.meta:
                    #    v.set_id(nested.uname())

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
                    interface='public',
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
                lhs = variable.lhs().clone(subst=subst)
                rhs = variable.rhs().clone(subst=subst)

                # Free variable shouldn't have a value
                if variable is time:
                    m.set_variable_of_integration(v)

                # Promote states and set rhs and initial value
                elif variable.is_state():
                    v.set_initial_value(variable.state_value())
                    v.set_equation(myokit.Equation(lhs, rhs))

                # Store literals (single number) in initial value
                elif isinstance(rhs, myokit.Number):
                    v.set_initial_value(rhs.eval())

                # For all other use rhs
                else:
                    v.set_equation(myokit.Equation(lhs, rhs))

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

        # Get a clone, so that we can make modifications
        cmodel = self.clone()
        # Get variable of integration (if any)
        voi = cmodel.variable_of_integration()

        # All myokit variables need an RHS, so set one for each set of free
        # variables.
        if voi is not None:
            voi.set_initial_value(0)

        for component in cmodel:
            for variable in component:
                if variable.is_free():
                    variable.set_initial_value(0)
                    if voi is None:
                        voi = variable

        # Create model
        m = myokit.Model(cmodel.name())
        m.meta['author'] = 'Myokit CellML 2 API'

        # Copy meta data
        for key, value in cmodel.meta.items():
            m.meta[key] = value

        # Gather set of variables that are used in equations.
        used = set()
        for component in cmodel:
            for variable in component:
                if variable.is_local() and variable.has_rhs():
                    for ref in variable.rhs().references():
                        used.add(ref.var())

        # Gather dict of variables that need unit conversion, mapping their
        # CellML variables to a tuple of units (from, to).
        # This is the set of variables that are non-local, have a different
        # unit than their source, and are referenced by other variables.
        needs_conversion = set()
        for component in cmodel:
            for variable in component:
                if variable.is_local() or variable not in used:
                    continue

                # Compare units
                ufrom = variable.rhs_variable().units().myokit_unit()
                uto = variable.units().myokit_unit()
                if ufrom != uto:
                    needs_conversion.add(variable)

        # Add components
        for component in cmodel:
            c = m.add_component(component.name())

            # Copy meta data
            for key, value in component.meta.items():
                c.meta[key] = value

            # Create local variables or variables that need unit conversion
            for variable in component:
                if variable.is_local() or variable in needs_conversion:
                    v = c.add_variable(variable.name())
                    v.set_unit(variable.units().myokit_unit())

                    # Copy meta data from all connected variables
                    for pal in variable.connected_variables():
                        for key, value in pal.meta.items():
                            v.meta[key] = value

                    # Copy meta data from 'source' variable, potentially
                    # overriding values from connected variables.
                    for key, value in variable.meta.items():
                        v.meta[key] = value

        # Add equations
        for component in cmodel:
            c = m[component.name()]

            # Create dict of variable reference substitutions
            var_map = {}
            for variable in component:
                cname = myokit.Name(variable)
                if variable.is_local() or variable in needs_conversion:
                    mname = myokit.Name(c[variable.name()])
                else:
                    source = variable.rhs_variable()
                    source = m[source.component().name()][source.name()]
                    mname = myokit.Name(source)
                var_map[cname] = mname

            # Add equations
            for variable in component:

                # Add local variable equations
                if variable.is_local():
                    v = c[variable.name()]

                    # Add equation with myokit references
                    rhs = variable.rhs()
                    rhs = rhs.clone(subst=var_map)
                    v.set_rhs(rhs)

                    # Promote states
                    if variable.is_state():
                        init = variable.initial_value().eval()
                        v.promote(0 if init is None else init)

                    # Set time variable
                    if variable is voi:
                        v.set_binding('time')

                # Add local copies of variables requiring unit conversion
                elif variable in needs_conversion:

                    # Get Myokit variable
                    v = c[variable.name()]

                    # Get Myokit variable for source
                    r = variable.rhs_variable()
                    r = m[r.component().name()][r.name()]

                    # Get conversion factor
                    f = myokit.Unit.conversion_factor(r.unit(), v.unit())
                    f = myokit.Number(f)

                    # Add equation
                    v.set_rhs(myokit.Multiply(myokit.Name(r), f))

        return m

    def name(self):
        """
        Returns this model's name.
        """
        return self._name

    def set_variable_of_integration(self, variable):
        """
        Marks a variable as this model's variable of integration.
        """
        if self._voi is None:
            self._voi = variable
        elif variable not in self._voi._cset:
            voi = self.variable_of_integration()
            raise CellMLError(
                'Cannot set ' + str(variable) + ' as variable of integration,'
                ' the variable ' + str(voi) + ' has already been set.')

    def __str__(self):
        return 'Model[@name="' + self._name + '"]'

    def units(self):
        """
        Returns an iterator over the :class:`Units` objects in this model.
        """
        return iter(self._units.values())

    def validate(self):
        """
        Validates this model, raising a :class:`CellMLError` if an errors are
        found.
        """

        # Validate components and variables
        for c in self._components.values():
            c._validate()

        # Collect all connected variable sets for validation
        csets = set()
        for component in self:
            for variable in component:
                csets.add(variable._cset)

        # Test each variable set
        free = set()
        for cset in csets:
            # Validate cset
            cset._validate()

            # Check if free
            if cset.equation() is None and cset.initial_value() is None:
                free.add(cset)
                if self._voi not in cset:
                    for var in cset:
                        warnings.warn('No value set for ' + str(var) + '.')

        # Check that there's at most one free variable.
        if len(free) > 1:
            warnings.warn('More than one variable does not have a value.')

        # Check that the variable of integration is a free variable
        voi = self.variable_of_integration()
        if not (voi is None or voi.is_free()):
            msg = 'Variable of integration ' + str(voi) + ' must be a free'
            msg += ' variable, but has '
            if voi.has_equation():
                var = voi.equation_variable()
                if voi is var:
                    msg += 'equation.'
                else:
                    msg += 'equation (set by ' + str(var) + ').'
            else:
                var = voi.initial_value_variable()
                if voi is var:
                    msg += 'initial value.'
                else:
                    msg += 'initial value (set by ' + str(var) + ').'
            raise CellMLError(msg)

    def variable_of_integration(self):
        """
        Returns the model's variable of integration, if any.
        """
        # No variable of integration?
        if self._voi is None or len(self._voi._cset) == 0:
            return None

        # Attempt to return variable in component without derivatives
        for voi in self._voi._cset:
            no_derivs = True
            for var in voi.component():
                if var.is_state():
                    no_derivs = False
                    break
            if no_derivs:
                return voi

        # Return first version of voi found
        return self._voi

    def version(self):
        """
        Returns the CellML version this model is in.
        """
        return self._version


class Units(object):
    """
    Represents a CellML units definition; should not be created directly but
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
        if not is_identifier(name):
            raise CellMLError(
                'Units name must be a valid CellML identifier.')
        if not predefined and name in self._si_units:
            raise CellMLError(
                'Units name "' + name + '" overlaps with a predefined name.')
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
            # Parse prefix
            if is_integer_string(str(prefix).strip()):
                p = int(prefix)
            else:
                try:
                    p = cls._si_prefixes[prefix]
                except KeyError:
                    raise CellMLError(
                        'Units prefix must be a string from the list of known'
                        ' prefixes or an integer string, got "' + str(prefix)
                        + '".')

            # Apply prefix to unit

            # float(10**309) is the first int that doesn't fit in a float
            if p > 309:
                raise CellMLError('Unit prefix too large: 10^' + str(p))
            unit *= 10**int(p)

        # Handle exponent (note: prefix is exponentiated, multiplier is not).
        if exponent is not None:
            # Parse exponent

            if not is_real_number_string(str(exponent).strip()):
                raise CellMLError(
                    'Unit exponent must be a real number string, got "'
                    + str(multiplier) + '"')
            e = float(exponent)

            # Apply exponent to unit
            unit **= e

        # Handle multiplier
        if multiplier is not None:
            if not is_real_number_string(str(multiplier).strip()):
                raise CellMLError(
                    'Unit multiplier must be a real number string, got "'
                    + str(multiplier) + '"')
            m = float(multiplier)

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
        'litre': myokit.units.L,
        'lumen': myokit.units.lm,
        'lux': myokit.units.lux,
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
        'deca': 1,
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
        The string name of a units object known to this variable's model.
    ``interface``
        The variable's interface.

    """
    def __init__(self, component, name, units, interface='none'):
        super(Variable, self).__init__()

        # Store model and component
        self._model = component.model()
        self._component = component

        # Check and store name
        if not is_identifier(name):
            raise CellMLError(
                'Variable name must be a valid CellML identifier.')
        self._name = name

        # Check and store units
        try:
            self._units = self._model.find_units(units)
        except CellMLError:
            raise CellMLError(
                'Variable units attribute must reference a units element in'
                ' the model, or one of the predefined units, found "'
                + str(units) + '".')

        # Check and store interfaces
        interfaces = ('none', 'public', 'private', 'public_and_private')
        if interface not in interfaces:
            raise CellMLError(
                'Interface must be "public", "private", "public_and_private",'
                ' or "none".')
        self._interface = interface

        # Connected variable set: will also be manipulated by the Model class.
        self._cset = ConnectedVariableSet(self)

    def component(self):
        """
        Returns this variable's component.
        """
        return self._component

    def connected_variables(self):
        """
        Returns an list of all variables connected to this one.
        """
        return [v for v in self._cset if v is not self]

    def equation(self):
        """
        Returns the equation for this variable (or its connected variable set),
        in the correct units.
        """
        eq = self._cset.equation()
        if eq is None or eq.lhs.var() is self:
            return eq

        # Check units
        var = self._cset.equation_variable()
        u1 = var.units().myokit_unit()
        u2 = self.units().myokit_unit()
        if u1 != u2:
            f = myokit.Unit.conversion_factor(u1, u2)
            rhs = myokit.Multiply(eq.rhs, myokit.Number(f))
        else:
            rhs = eq.rhs

        # Return updated equation
        return myokit.Equation(myokit.Name(self), rhs)

    def equation_variable(self):
        """
        Returns the variable from the connected variable set that provides an
        equation for this set (if any).
        """
        return self._cset.equation_variable()

    def has_equation(self):
        """
        Returns True if an equation is defined in this variable's connected
        variable set.
        """
        return self._cset.equation() is not None

    def has_initial_value(self):
        """
        Returns True if an initial value is defined in this variable's
        connected variable set.
        """
        return self._cset.initial_value() is not None

    def has_rhs(self):
        """
        Returns True if an equation or initial value is defined in this
        variable's connected variable set.
        """
        return (self._cset.equation() is not None or
                self._cset.initial_value() is not None)

    def initial_value(self):
        """
        Returns the initial value for this variable (or its connected variable
        set), in the correct units.

        The returned value is a :class:`myokit.Expression`.
        """
        value = self._cset.initial_value()
        if value is None or self._cset.initial_value_variable() is self:
            return value

        # Check units
        var = self._cset.initial_value_variable()
        u1 = var.units().myokit_unit()
        u2 = self.units().myokit_unit()
        if u1 != u2:
            f = myokit.Unit.conversion_factor(u1, u2)
            return myokit.Multiply(value, myokit.Number(f))
        else:
            return value

    def initial_value_variable(self):
        """
        Returns the variable from the connected variable set that provides an
        initial value for this set (if any).
        """
        return self._cset.initial_value_variable()

    def interface(self):
        """
        Returns this variable's interface (as a string).
        """
        return self._interface

    def is_free(self):
        """
        Returns ``True`` if this variable doesn't define a value anywhere in
        its connected variable set.
        """
        return (self._cset.equation() is None and
                self._cset.initial_value() is None)

    def is_local(self):
        """
        Returns ``True`` if this variable provides its own value, i.e. if it is
        the variable defining an equation (or an initial value if no equation
        is set) within its connected variable set.
        """
        var = self._cset.equation_variable()
        if var is self:
            return True
        elif var is None:
            return self._cset.initial_value_variable() is self
        else:
            return False

    def is_state(self):
        """
        Returns ``True`` if this variable is a state variable (i.e. if its
        definition anywhere in the connected variable set is through a
        differential equation).
        """
        eq = self._cset.equation()
        return eq is not None and isinstance(eq.lhs, myokit.Derivative)

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

    def __repr__(self):
        return str(self)

    def rhs(self):
        """
        Returns an RHS for this variable, in the appropriate units.

        The RHS will be derived either from a defining equation or, if no
        equation is found in the connected variable set, from the initial
        value.

        If neither is found, ``None`` will be returned.
        """
        eq = self.equation()
        return eq.rhs if eq is not None else self.initial_value()

    def rhs_variable(self):
        """
        Returns the variable that defines the RHS for this variable's connected
        variable set (or ``None``).
        """
        var = self.equation_variable()
        return var if var is not None else self.initial_value_variable()

    def set_equation(self, equation):
        """
        Sets a defining equation for this variable.

        The given ``equation`` must be a :class:`myokit.Equation` where any
        :class:`myokit.Name` objects have a CellML :class:`Variable` from this
        variable's model as their value.
        """
        if equation is not None:

            # Unpack equation
            lhs, rhs = equation

            # Check LHS
            if not isinstance(lhs, myokit.LhsExpression):
                raise CellMLError(
                    'Model must be in assignment form, where each equation is'
                    ' of the form `x = ...` or `dx/dt = ...`.')
            if lhs.var() is not self:
                raise CellMLError(
                    'Equation for ' + str(lhs.var()) + ' passed to variable '
                    + str(self) + '.')

            # Check all references are local
            for ref in lhs.references() | rhs.references():
                var = ref.var()
                if var._component is not self._component:
                    raise CellMLError(
                        'An equation can only reference variables from the'
                        ' same component, found: ' + str(var) + '.')

            # Check all units in the RHS are known, and replace numbers
            # without units with numbers in units 'dimensionless'.
            numbers_without_units = {}
            for x in rhs.walk(myokit.Number):
                if x.unit() is None:
                    numbers_without_units[x] = myokit.Number(
                        x.eval(), myokit.units.dimensionless)
                else:
                    try:
                        self._model.find_units_name(x.unit())
                    except CellMLError:
                        raise CellMLError(
                            'All units appearing in a variable\'s RHS must'
                            ' be known, found: ' + str(x.unit()) + '.')
            if numbers_without_units:
                rhs = rhs.clone(subst=numbers_without_units)
                equation = myokit.Equation(lhs, rhs)

        # Store
        self._cset.set_equation(self, equation)

    def set_initial_value(self, value):
        """
        Sets this variable's intial value (must be a number or ``None``).
        """
        # Allow unsetting with ``None``
        if value is not None:

            # Check value is a real number string
            if isinstance(value, basestring):
                if is_real_number_string(value):
                    value = float(value)
                else:
                    raise CellMLError(
                        'If given, a variable initial_value must be a real'
                        ' number (using variables as initial values is not'
                        ' supported).')
            else:
                value = float(value)

            value = myokit.Number(value, self._units.myokit_unit())

        # Store
        self._cset.set_initial_value(self, value)

    def __str__(self):
        return (
            'Variable[@name="' + self._name + '"] in ' + str(self._component))

    def units(self):
        """
        Returns the units this variable is in (as a :class:`Units` object).
        """
        return self._units


class ConnectedVariableSet(object):
    """
    Represents a set of connected variables.

    Arguments:

    ``variable=None``
        An optional first variable in this set.
    """
    def __init__(self, variable=None):

        # All variables in this set
        self._variables = set()

        # Equation, and variable owning equation
        self._equation = None
        self._equation_variable = None

        # Initial value, and variable owning initial value
        self._initial_value = None
        self._initial_value_variable = None

        # Add first variable
        if variable is not None:
            self._variables.add(variable)

    def __contains__(self, item):
        return item in self._variables

    def equation(self):
        """
        Returns the equation (if any) for this variable set.
        """
        return self._equation

    def equation_variable(self):
        """
        Returns the variable (if any) that defines an equation.
        """
        return self._equation_variable

    def initial_value(self):
        """
        Returns the initial value (if any) for this variable set.
        """
        return self._initial_value

    def initial_value_variable(self):
        """
        Returns the variable (if any) that defines an initial value.
        """
        return self._initial_value_variable

    def __iter__(self):
        return iter(self._variables)

    def __len__(self):
        return len(self._variables)

    @staticmethod
    def _merge(set1, set2):
        """
        Merges two variable sets.
        """
        # Get equation
        equation = set1._equation
        equation_variable = set1._equation_variable
        if equation is None:
            equation = set2._equation
            equation_variable = set2._equation_variable
        elif set2._equation is not None:
            raise CellMLError(
                'Multiple equations defined in connected variable set: '
                + str(set1._equation_variable) + ' and '
                + str(set2._equation_variable) + '.')

        # Get initial value
        initial_value = set1._initial_value
        initial_value_variable = set1._initial_value_variable
        if initial_value is None:
            initial_value = set2._initial_value
            initial_value_variable = set2._initial_value_variable
        elif set2._initial_value is not None:
            raise CellMLError(
                'Multiple initial values defined in connected variable set: '
                + str(set1._initial_value_variable) + ' and '
                + str(set2._initial_value_variable) + '.')

        # Create new set
        cset = ConnectedVariableSet()
        cset._variables = set1._variables | set2._variables
        cset._equation = equation
        cset._equation_variable = equation_variable
        cset._initial_value = initial_value
        cset._initial_value_variable = initial_value_variable

        # Update all variables in the set
        for var in cset:
            var._cset = cset

    def set_equation(self, variable, equation=None):
        """
        Sets the ``equation`` for this variable set, as defined for
        ``variable``.
        """
        if self._equation_variable not in (variable, None):
            raise CellMLError(
                'Unable to change equation: the equation in this connected'
                ' variable set is already defined by '
                + str(self._equation_variable) + '.')

        # Update
        self._equation = equation
        self._equation_variable = None if equation is None else variable

    def set_initial_value(self, variable, value=None):
        """
        Sets the ``initial_value`` for this variable set, as defined for
        ``variable``.
        """
        if self._initial_value_variable not in (variable, None):
            raise CellMLError(
                'Unable to change initial value: the initial value in this'
                ' connected variable set is already defined by '
                + str(self._initial_value_variable) + '.')

        # Update
        self._initial_value = value
        self._initial_value_variable = None if value is None else variable

    def _validate(self):
        """
        Validates this variable set, raising a CellMLError if errors are found.
        """
        # Check if initial value is set for ODE, and only for ODE
        if self._equation is None:
            return

        if isinstance(self._equation.lhs, myokit.Derivative):
            if self._initial_value is None:
                raise CellMLError(
                    'No initial value set for state variable '
                    + str(self._equation_variable) + '.')
        elif self._initial_value is not None:
            msg = 'Overdefined variable: ' + str(self._equation_variable)
            msg += ' has both a (non-ODE) equation and an initial value'
            if self._initial_value_variable is not self._equation_variable:
                msg += ' (set by ' + str(self._initial_value_variable) + ')'
            msg += '.'
            raise CellMLError(msg)

