#
# CellML 1.0/1.1 API
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import collections
import myokit
import re


# Namespaces
#NS_BQBIOL = 'http://biomodels.net/biology-qualifiers/'
NS_CELLML_1_0 = 'http://www.cellml.org/cellml/1.0#'
NS_CELLML_1_1 = 'http://www.cellml.org/cellml/1.1#'
NS_CMETA = 'http://www.cellml.org/metadata/1.0#'
NS_MATHML = 'http://www.w3.org/1998/Math/MathML'
#NS_OXMETA = 'https://chaste.comlab.ox.ac.uk/cellml/ns/oxford-metadata#'
#NS_RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
#NS_RDFS = 'http://www.w3.org/2000/01/rdf-schema#'
#NS_TMP_DOC = 'http://cellml.org/tmp-documentation'


# Identifier validation
_cellml_identifier = re.compile('^([_][0-9_]*)?[a-zA-Z][a-zA-Z0-9_]*$')


def is_valid_identifier(name):
    """
    Tests if the given ``name`` is a valid CellML 1 identifier.

    The official for 1.0 docs allow silly things, e.g. ``1e2``, ``123`` or
    ``_123``. This method is more strict, requiring (1) at least one letter,
    and (2) that the first character is not a number.
    """
    return _cellml_identifier.match(name) is not None


class AnnotatableElement(object):
    """
    Represents a CellML 1.0 or 1.1 element that can have a cmeta:id.
    """

    def __init__(self, model):

        # The model this element is in (or is)
        self._model = model

        # A unique identifier (or None)
        self._cmeta_id = None

    def cmeta_id(self):
        """
        Returns this element's cmeta:id if set, or ``None`` otherwise.
        """
        return self._cmeta_id

    def set_cmeta_id(self, cmeta_id):
        """
        Sets this element's cmeta id (must be a non-empty string or ``None``).
        """
        # Check if already set
        if self._cmeta_id is not None:
            # Ignore setting the same id again
            if cmeta_id == self._cmeta_id:
                return

            # Unregister if changing
            self._model._unregister_cmeta_id(self._cmeta_id)

        # Set new cmeta id
        if cmeta_id is None:
            self._cmeta_id = None
        else:
            # Check well-formedness
            cmeta_id = str(cmeta_id)
            if not cmeta_id:
                raise CellMLError(
                    'A cmeta:id must be a non-empty string (if set).')

            # Register and check uniqueness
            self._model._register_cmeta_id(cmeta_id, self)

            # Store
            self._cmeta_id = cmeta_id


class CellMLError(myokit.MyokitError):
    """
    Raised when an invalid CellML model is created or detected, or when a model
    uses CellML features that Myokit does not support.
    """
# TODO: Catch these when parsing, and then rethrow but with line and char
# number where possible.


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
        self._variables= collections.OrderedDict()

        # This component's component-level units
        self._units = {}

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
        self._units[name] = u = Units(name, myokit_unit)
        return u

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

    def find_units(self, name):
        """
        Looks up and returns a :class:`Units` object with the given ``name``.

        If no such unit exists in the component, the model units and predefined
        units are searched. If a unit still isn't found, a `KeyError` is
        raised.
        """
        try:
            return self._units[name]
        except KeyError:
            return self._model.find_units(name)

    def __getitem__(self, key):
        return self._variables[key]

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

    def units(self):
        """
        Returns an iterator over this component's :class:`Unit` objects.
        """
        return self._units.values()

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
                    'Encapsulation hierarchy can not be circular (6.4.3.2).')
            parent = parent._parent

        # Validate variables
        for v in self._variables.values():
            v._validate()

    def variable(self, name):
        """
        Returns the variable with the given ``name``.
        """
        return self._variables[name]


class Model(AnnotatableElement):
    """
    Represents a CellML 1.0 or 1.1 model.

    Support notes:

    - Imports (CellML 1.1) are not supported.
    - A slightly more strict rule for 'valid CellML identifiers' is used (must
      not start with a number, must contain at least one letter).
    - Units that require an offset (celsius and fahrenheit) are not supported.
    - Units with a non-integer exponent are not supported.
    - Defining new base units is not supported.
    - Reactions are not supported.

    Arguments

    ``name``
        A valid CellML identifier string.
    ``version``
        A string representing the CellML version this model is in (must be
        '1.0' or '1.1').

    """
    #TODO: Update list above about base units: Might support them but convert
    # to dimensionless for Myokit??
    def __init__(self, name, version):
        super(Model, self).__init__(self)

        # Check and store name
        if not is_valid_identifier(name):
            raise CellMLError(
                'Model name must be a valid CellML identifier (3.4.1.2).')
        self._name = name

        # Check and store version
        if version not in ('1.0', '1.1'):
            raise ValueError('Only 1.0 and 1.1 models are supported.')

        # This model's components
        self._components = collections.OrderedDict()

        # This model's model-level units
        self._units = {}

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
        Adds a connection between variables ``comp1.var1`` and ``comp2.var2``.

        Arguments:

        ``variable_1``
            One variable to connect.
        ``variable_2``
            The other variable to connect.

        """
        # Check both are variables, and from this model
        if not isinstance(variable_1, Variable):
            raise ValueError('Argument variable_1 must be a cellml.Variable')
        if not isinstance(variable_2, Variable):
            raise ValueError('Argument variable_2 must be a cellml.Variable')
        if variable_1._model is not self:
            raise ValueError('Argument variable_1 must be a cellml.Variable'
                             ' from this model.')
        if variable_2._model is not self:
            raise ValueError('Argument variable_1 must be a cellml.Variable'
                             ' from this model.')

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
        if interface_1 == 'out' and interface_2 == 'in':
            variable_2._source = variable_1
        elif interface_1 == 'in' and interface_2 == 'out':
            variable_1._source = variable_2
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
        self._units[name] = u = Units(name, myokit_unit)
        return u

    def component(self, name):
        """
        Returns the :class:`Component` with the given ``name``.
        """
        return self._components[name]

    def find_units(self, name):
        """
        Looks up and returns a :class:`Units` object with the given ``name``.

        If no such unit exists in the model, the predefined units are searched.
        If a unit still isn't found, a `KeyError` is raised.
        """
        try:
            return self._units[name]
        except KeyError:
            return Units.find_units(name)

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

        # Add components
        for component in self:
            c = m.add_component(component.name())

            # Add local variables
            for variable in component:
                if variable.is_local():
                    v = c.add_variable(variable.name())
                    v.set_unit(variable.units().myokit_unit())

        # Add equations
        for component in self:
            c = m[component.name()]

            # Create dict of variable reference substitutions
            varmap = {}
            for variable in component:
                source = variable.source()
                parent = m[source.component().name()]
                varmap[myokit.Name(variable)] = myokit.Name(
                    parent[source.name()])

            # Add equations
            for variable in component:
                if variable.is_local():
                    v = c[variable.name()]

                    # Add equation
                    if variable.is_free():
                        # Add zero for the free variable
                        v.set_rhs(
                            myokit.Number(0, variable.units().myokit_unit()))
                    else:
                        # Add RHS with Myokit references
                        rhs = variable.rhs_or_initial_value()
                        rhs = rhs.clone(subst=varmap)
                        v.set_rhs(rhs)
                        if variable.is_state():
                            v.promote(variable.initial_value())

        # TODO
        # - [ ] Bind free variable to time
        # - [ ] Sort state variables in order of occurence?
        # - [ ] Unit conversion
        # - [ ] Meta data (about etc.)
        # - [ ] Oxmeta / RDF is annotations
        # TODO
        # - [ ] Add importer that also creates a protocol, remove i_stim
        #
        #

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
        try:
            cmeta_id = str(cmeta_id)
        except ValueError:
            raise CellMLError('A cmeta:id must be a string.')
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
        if variable._model is not self:
            raise ValueError('Given variable must be from this model.')

        # Unset previous
        if self._free_variable is not None:
            self._free_variable._is_free = False

        # Set new
        self._free_variable = variable
        variable._is_free = True

    def __str__(self):
        return 'Model[@name="' + self._name + '"]'

    def units(self):
        """
        Returns an iterator over this model's :class:`Unit` objects.
        """
        return self._units.values()

    def _unregister_cmeta_id(self, cmeta_id):
        """
        Should be called whenever a cmeta:id for a CellML element in this model
        (or for this model itself) is unset.
        """
        del(self._cmeta_ids[cmeta_id])

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
        for c in self._components.values():
            for v in c._variables.values():
                if v.source() is None:
                    free.add(v)
        if len(free) > 1:
            raise CellMLError(
                'More than one free variable detected: ' +
                ', '.join([str(v) for v in free]) + '.')

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
        """
        obj = cls._si_unit_objects.get(name, None)
        if obj is None:
            myokit_unit = cls._si_units.get(name, None)
            if myokit_unit is None:
                raise KeyError('Unknown predefined unit "' + str(name) + '".')
            obj = cls(name, myokit_unit, predefined=True)
            cls._si_unit_objects[name] = obj
        return obj

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
            try:
                unit = cls.find_units(units)
            except KeyError:
                raise CellMLError(
                    'Unknown predefined units name "' + str(units)
                    + '" (5.4.2.2).')
        else:
            try:
                unit = context.find_units(units)
            except KeyError:
                raise CellMLError(
                    'Unknown units name "' + str(units) + '" within '
                    + str(context) + ' (5.4.2.2).')
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
            if not myokit._feq(e, int(e)):
                raise CellMLError(
                    'Non-integer unit exponents are not supported.')

            # Apply exponent to unit
            unit **= int(e)

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

    # Predefined Units objects
    _si_unit_objects = {}

    # Predefined units in CellML, Unit object to name
    '''
    _si_units_r = {
        myokit.units.dimensionless: 'dimensionless',
        myokit.units.A: 'ampere',
        myokit.units.F: 'farad',
        myokit.units.kat: 'katal',
        myokit.units.lux: 'lux',
        myokit.units.Pa: 'pascal',
        myokit.units.T: 'tesla',
        myokit.units.Bq: 'becquerel',
        myokit.units.g: 'gram',
        myokit.units.K: 'kelvin',
        myokit.units.m: 'meter',
        myokit.units.V: 'volt',
        myokit.units.cd: 'candela',
        myokit.units.Gy: 'gray',
        myokit.units.kg: 'kilogram',
        myokit.units.m: 'metre',
        myokit.units.s: 'second',
        myokit.units.W: 'watt',
        myokit.units.C: 'celsius',
        myokit.units.H: 'henry',
        myokit.units.L: 'liter',
        myokit.units.mol: 'mole',
    }
    '''

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

    # Recognised unit prefixes, multiplier to name
    '''
    _si_prefixes_r = {
        -24: 'yocto',
        -21: 'zepto',
        -18: 'atto',
        -15: 'femto',
        -12: 'pico',
        -9: 'nano',
        -6: 'micro',
        -3: 'milli',
        -2: 'centi',
        -1: 'deci',
        1: 'deka',
        2: 'hecto',
        3: 'kilo',
        6: 'mega',
        9: 'giga',
        12: 'tera',
        15: 'peta',
        18: 'exa',
        21: 'zetta',
        24: 'yotta',
    }
    '''


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
        except KeyError:
            raise CellMLError(
                'Variable units attribute must reference a units element in'
                ' the current component or model, or one of the predefined'
                ' units (3.4.3.3).')

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
        Checks if this is a state variable.
        """
        return self._is_state

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
        if self._rhs is None:
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
            i = 'public' if public_interface == 'in' else 'private'
            raise CellMLError(
                'An initial value cannot be set for ' + str(self) + ', which'
                ' has ' + i + '_interface="in" (3.4.3.8).')

        # Check and store
        try:
            self._initial_value = float(value)
        except ValueError:
            raise CellMLError(
                'If given, a variable initial_value must be a real number'
                ' (3.4.3.7).')

    def set_is_state(self, state):
        """
        Set whether this variable is a state variable or not.
        """
        # Check interface
        if self._public_interface == 'in' or self._private_interface == 'in':
            i = 'public' if public_interface == 'in' else 'private'
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
            i = 'public' if public_interface == 'in' else 'private'
            raise CellMLError(
                'An equation cannot be set for ' + str(self) + ', which has '
                + i + '_interface="in" (4.4.4).')

        # Check all references in equation are known and local
        #TODO

        # Store
        self._rhs = rhs

    def source(self):
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
        return var

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
        if self._public_interface == 'in' or self._private_interface == 'in':
            i = 'public' if self._public_interface == 'in' else 'private'
            if self.source() is None:
                raise CellMLError(
                    str(self) + ' has ' + i + '_interface="in", but is not'
                    ' connected to a variable with an appropriate "out"'
                    ' interface (3.4.6.4).')

        # Check that state variables define two values
        elif self._is_state:
            if self._initial_value is None:
                raise CellMLError(
                    'State ' + str(self) + ' must define an initial value.')
            if self._rhs is None:
                raise CellMLError(
                    'State ' + str(self) + ' must have a defining equation.')

        # Check that other variables define one value (except the free
        # variable)
        elif self._rhs is None and self._initial_value is None:
            if not self._is_free:
                raise CellMLError(str(self) + ' must have an initial value or'
                                  ' a defining equation.')

