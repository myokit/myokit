#
# Parses a CellML 2.0 document.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import warnings

from lxml import etree

import myokit
import myokit.formats.mathml
import myokit.formats.cellml as cellml
import myokit.formats.cellml.v2

from myokit.formats.xml import split


def parse_file(path):
    """
    Parses a CellML 2.0 model at the given path and returns a
    :class:`myokit.formats.cellml.v2.Model`.

    Raises a :class:`CellMLParsingError` if anything goes wrong.

    For notes about CellML 2.0 support, see
    :class:`myokit.formats.cellml.v2.Model`.
    """
    return CellMLParser().parse_file(path)


def parse_string(text):
    """
    Parses a CellML 2.0 model from the given string and returns a
    :class:`myokit.formats.cellml.v2.Model`.

    Raises a :class:`CellMLParsingError` if anything goes wrong.

    For notes about CellML 2.0 support, see
    :class:`myokit.formats.cellml.v2.Model`.
    """
    return CellMLParser().parse_string(text)


class CellMLParsingError(myokit.ImportError):
    """
    Raised if an error occurs during CellML parsing.

    The argument ``element`` can be used to pass in an element that caused the
    error.
    """
    def __init__(self, message, element=None):
        if element is not None:
            try:    # pragma: no cover
                line = str(element.sourceline)
                message = 'Error on line ' + line + '. ' + message
            except AttributeError:
                pass
        super(CellMLParsingError, self).__init__(message)


class CellMLParser(object):
    """
    Parses CellML 2.0 documents, and performs (partial) validation.

    For notes about CellML 2.0 support, see
    :class:`myokit.formats.cellml.v2.Model`.
    """

    # Note on assignment form, used in errors
    _dae_message = (
        'Each equation must have either a single variable or a derivative of a'
        ' single variable as its left-hand side, and each variable may only'
        ' appear on a left-hand side once.')

    def _check_allowed_content(
            self, element, children, attributes, name=None, math=False):
        """
        Scans ``element`` and raises an exception if any unlisted CellML
        children are found, if any unlisted null-namespace attributes are
        found, or if the element contains text.

        With ``math=False`` (default), the method also checks that no MathML
        elements are present. With ``math=True`` only a MathML ``<math>``
        element is allowed.
        """
        # Check for text inside this tag
        # For mixed-context xml this checks only up until the first child tag.
        if element.text is not None:
            if element.text.strip():
                raise CellMLParsingError(
                    'Text found in ' + self._tag(element, name) + '.',
                    element)

        # Check child elements
        allowed = set([self._join(x) for x in children])
        if math:
            allowed.add(self._join('math', cellml.NS_MATHML))

        # Check if only contains allowed child elements
        for child in element:
            # Check for trailing text
            if child.tail is not None and child.tail.strip():
                raise CellMLParsingError(
                    'Text found in ' + self._tag(element, name)
                    + ', after ' + self._tag(child) + ' element.',
                    child)

            # Check if allowed
            if str(child.tag) in allowed:
                continue

            raise CellMLParsingError(
                'Unexpected content type in ' + self._tag(element, name)
                + ', found element of type ' + self._tag(child) + '.', child)

        # Check attributes
        allowed = set(attributes)
        for key in element.attrib:
            # id is always allowed
            if key == 'id':
                continue

            # Must be in allowed list
            if key not in allowed:
                # Split off namespace, and add back in again (to get nicer
                # formatting).
                ns, at = split(key)
                key = self._item(ns, at)
                raise CellMLParsingError(
                    'Unexpected attribute ' + key + ' found in '
                    + self._tag(element, name) + '.', element)

    def _check_id(self, element, obj=None):
        """
        Checks for an ``id`` attribute in element, and stores a link from the
        id to the given object if found.
        """
        # Find attribute
        xid = element.attrib.get('id', None)
        if xid is None:
            return

        # Check well-formedness
        if not xid:
            raise CellMLParsingError(
                'If present, an id must be a non-empty string.', element)

        # Check uniqueness
        if xid in self._ids:
            raise CellMLParsingError('Duplicate id "' + xid + '".', element)

        # Store and return
        self._ids[xid] = obj

    def _item(self, ns, item):
        """
        Given a namespace ``ns`` and an element or attribute ``item``, this
        method will return a nicely formatted combination, e.g. ``item`` for
        the null namespace, ``cellml:item`` for a namespace with a known
        prefix, or ``{ns}item`` for a namespace without a known prefix.

        See also :meth:`_tag`.
        """
        if ns is None:
            return item
        elif ns == self._ns:
            return 'cellml:' + item
        elif ns == cellml.NS_MATHML:
            return 'mathml:' + item
        else:
            return '{' + ns + '}' + item

    def _join(self, element, namespace=None):
        """
        Joins a ``namespace`` and an ``element`` string into a single string.
        """
        if namespace is None:
            namespace = self._ns
        return '{' + namespace + '}' + element

    def parse(self, root):
        """
        Parses and validates a CellML document rooted in the given elementtree
        element.
        """
        # Parse model, using temporary state properties
        self._ns = None
        self._ids = {}
        self._vois = set()  # variables of integration
        try:
            return self._parse_model(root)
        except myokit.formats.cellml.v2.CellMLError as e:
            raise CellMLParsingError(str(e))
        except myokit.formats.mathml.MathMLError as e:
            raise CellMLParsingError(str(e))
        finally:
            del self._ns, self._ids, self._vois

    def parse_file(self, path):
        """
        Parses and validates the CellML file at ``path`` and returns a CellML
        Model.
        """
        # Read file
        try:
            parser = etree.XMLParser(remove_comments=True)
            tree = etree.parse(path, parser=parser)
        except Exception as e:
            raise CellMLParsingError('Unable to parse XML: ' + str(e))

        # Parse content
        return self.parse(tree.getroot())

    def parse_string(self, text):
        """
        Parses and validates the CellML XML in the string ``text`` and returns
        a CellML model.
        """
        # Read string
        import xml.etree.ElementTree as etree   # lxml makes this difficult
        try:
            root = etree.fromstring(text)
        except Exception as e:
            raise CellMLParsingError('Unable to parse XML: ' + str(e))

        # Parse content
        return self.parse(root)

    def _parse_component(self, element, model):
        """
        Parses a component ``element`` and adds it to the given ``model``.
        """
        # Check name is present
        try:
            name = element.attrib['name']
        except KeyError:
            raise CellMLParsingError(
                'Component element must have a name attribute.',
                element)

        # Create component (validates name and checks uniqueness)
        try:
            component = model.add_component(name)

            # Check and store id
            self._check_id(element, component)

        except myokit.formats.cellml.v2.CellMLError as e:
            raise CellMLParsingError(str(e), element)

        # Check for resets
        reset = element.find(self._join('reset'))
        if reset is not None:
            raise CellMLParsingError('Resets are not supported.', reset)

        # Check allowed content
        self._check_allowed_content(
            element, ['variable'], ['name'], name, math=True)

        # Create variables and set interfaces
        for child in element.findall(self._join('variable')):
            self._parse_variable(child, component)

    def _parse_connection(self, element, model, connected):
        """
        Parses a connection ``element``.

        A set of tuples representing connected components is passed in as
        ``connected``. Each pair of components should be represented twice in
        this set; once in each order.
        """
        # Get component_1 and component_2
        try:
            c1 = element.attrib['component_1']
        except KeyError:
            raise CellMLParsingError(
                'A connection element must define a component_1 attribute.',
                element)
        try:
            c2 = element.attrib['component_2']
        except KeyError:
            raise CellMLParsingError(
                'A connection element must define a component_2 attribute.',
                element)

        # Check components are different
        if c1 == c2:
            raise CellMLParsingError(
                'The component_1 and component_2 attributes in a connection'
                ' element must be different, got "' + str(c1)
                + '" twice.', element)

        # Get components
        try:
            c1 = model.component(c1)
        except KeyError:
            raise CellMLParsingError(
                'A map_components component_1 attribute must refer to a'
                ' component in the current model, got "' + str(c1) + '".',
                element)
        try:
            c2 = model.component(c2)
        except KeyError:
            raise CellMLParsingError(
                'A map_components component_2 attribute must refer to a'
                ' component in the current model, got "' + str(c2) + '".',
                element)

        # Check components are not yet connected
        if (c1, c2) in connected:
            raise CellMLParsingError(
                'Each connection in a model must connect a unique pair of'
                ' components, found multiple for "' + c1.name() + '" and "'
                + c2.name() + '".', element)
        connected.add((c1, c2))
        connected.add((c2, c1))

        # Check at least one map_variables is present
        map_variables = element.findall(self._join('map_variables'))
        if len(map_variables) < 1:
            raise CellMLParsingError(
                'A connection must contain at least one map_variables'
                ' element.', element)

        # Parse map_variables elements
        for child in map_variables:
            self._parse_connection_map_variables(child, c1, c2)

        # Check id
        self._check_id(element)

        # Check allowed content
        self._check_allowed_content(
            element, ['map_variables'], ['component_1', 'component_2'])

    def _parse_connection_map_variables(self, element, c1, c2):
        """
        Parses a map_variables ``element`` for a connection with components
        ``c1`` and ``c2``.
        """
        # Get variable_1 and variable_2
        try:
            v1 = element.attrib['variable_1']
        except KeyError:
            raise CellMLParsingError(
                'A map_variables element must define a variable_1 attribute.',
                element)
        try:
            v2 = element.attrib['variable_2']
        except KeyError:
            raise CellMLParsingError(
                'A map_variables element must define a variable_2 attribute.',
                element)

        # Get variables
        try:
            v1 = c1.variable(v1)
        except KeyError:
            raise CellMLParsingError(
                'A map_variables variable_1 attribute must refer to a'
                ' variable in component_1, got "' + str(v1) + '".',
                element)
        try:
            v2 = c2.variable(v2)
        except KeyError:
            raise CellMLParsingError(
                'A map_variables variable_2 attribute must refer to a'
                ' variable in component_2, got "' + str(v1) + '".',
                element)

        # Connect variables
        model = c1.model()
        try:
            model.add_connection(v1, v2)
        except myokit.formats.cellml.v2.CellMLError as e:
            raise CellMLParsingError(str(e), element)

        # Check id
        self._check_id(element)

        # Check allowed content
        self._check_allowed_content(element, [], ['variable_1', 'variable_2'])

    def _parse_encapsulation(self, element, model):
        """
        Parses an encapsulation ``element`` and updates components in the given
        ``model``.
        """

        # Check id
        self._check_id(element)

        # Check contains at least one component_ref
        if element.find(self._join('component_ref')) is None:
            raise CellMLParsingError(
                'Group must contain at least one component_ref element.',
                element)

        # Check allowed content
        self._check_allowed_content(element, ['component_ref'], [])

        # Parse component refs
        for child in element.findall(self._join('component_ref')):
            self._parse_encapsulation_component_ref(child, model)

    def _parse_encapsulation_component_ref(self, element, model, parent=None):
        """
        Parses a component_ref ``element``.

        If this component_ref is nested inside another component_ref, set the
        parent component as ``parent``.
        """
        # Check id
        self._check_id(element)

        # Get component attribute
        try:
            component = element.attrib['component']
        except KeyError:
            raise CellMLParsingError(
                'A component_ref must define a component attribute.',
                element)

        # Get component
        try:
            component = model.component(component)
        except KeyError:
            raise CellMLParsingError(
                'A component_ref\'s component attribute must reference a'
                ' component in the same model, got "' + component + '".',
                element)

        # Check allowed content
        self._check_allowed_content(element, ['component_ref'], ['component'])

        # Store encapsulation relationships
        if parent is not None:

            # Check for existing parent
            if component.parent() is not None:
                raise CellMLParsingError(
                    'A component can only have a single encapsulation parent:'
                    ' found ' + str(component) + ' with parents '
                    + str(component.parent()) + ' and ' + str(parent) + '.',
                    element)

            # Set parent (won't raise CellMLErrors)
            component.set_parent(parent)

        # Check child component refs
        kids = element.findall(self._join('component_ref'))
        for child in kids:
            self._parse_encapsulation_component_ref(child, model, component)

        # No parent? Then must have at least one child
        if len(kids) == 0 and parent is None:
            raise CellMLParsingError(
                'The first component_ref in an encapsulation must have at'
                ' least one child.')

    def _parse_math(self, element, component):
        """
        Parses a mathml:math ``element``, adding equations to the variables of
        the given ``component``.
        """
        model = component.model()

        # Get variables from component
        def variable_factory(name, element):
            try:
                var = component.variable(name)
            except KeyError:
                raise CellMLParsingError(
                    'Variable references in equations must name a variable'
                    ' from the local component.', element)

            return myokit.Name(var)

        # Create numbers with units
        attr = self._join('units')

        def number_factory(value, element):
            # Numbers not connected to a cn
            if element is None:
                return myokit.Number(value, myokit.units.dimensionless)

            # Get units attribute
            try:
                units = element.attrib[attr]
            except KeyError:
                raise CellMLParsingError(
                    'Numbers inside MathML must define a cellml:units'
                    ' attribute.', element)

            # Find units in component
            try:
                units = model.find_units(units)
            except myokit.formats.cellml.v2.CellMLError:
                raise CellMLParsingError(
                    'Unknown unit "' + str(units) + '" referenced inside a'
                    ' MathML equation.', element)

            # Create and return
            return myokit.Number(value, units.myokit_unit())

        # Create parser
        p = myokit.formats.mathml.MathMLParser(
            variable_factory, number_factory, self._vois)

        # Iterate over applies.
        for child in element:

            # Check each child is in MathML namespace
            ns, el = split(child.tag)
            if ns != cellml.NS_MATHML:
                raise CellMLParsingError(
                    'The contents of a mathml:math element must be in the'
                    ' mathml namespace, found "' + str(child.tag) + '" inside '
                    + str(component) + '.', child)

            # If it isn't these it must be an apply
            if el != 'apply':
                raise CellMLParsingError(
                    'Unexpected contents in mathml:math. Expecting'
                    ' mathml:apply but found mathml:' + el + ' inside maths'
                    ' for ' + str(component) + '.', child)

            # Parse
            eq = p.parse(child)
            if not isinstance(eq, myokit.Equal):
                raise CellMLParsingError(
                    'Unexpected element in MathML, expecting a list of'
                    ' equations, got ' + self._tag(child) + '.', child)
            lhs, rhs = eq

            # Check lhs
            if not isinstance(lhs, myokit.LhsExpression):
                raise CellMLParsingError(
                    'Invalid expression found on the left-hand side of an'
                    ' equation: ' + self._dae_message, child)

            # Check variable is undefined
            var = lhs.var()
            if var.has_equation():
                raise CellMLParsingError(
                    'Overdefined variable: ' + str(var) + ': Two defining'
                    ' equations.', child)

            # Set equations
            try:
                lhs.var().set_equation(myokit.Equation(lhs, rhs))
            except myokit.formats.cellml.v2.CellMLError \
                    as e:  # pragma: no cover (currently can't happen)
                raise CellMLParsingError(str(e), child)

    def _parse_model(self, element):
        """
        Parses a CellML model element.
        """

        # Handle document-level validation here.

        # Check namespace
        ns, el = split(element.tag)
        if ns == cellml.NS_CELLML_2_0:
            version = '2.0'
        else:
            raise CellMLParsingError(
                'Root node must be in CellML 2.0 namespace.', element)

        # Store namespace
        self._ns = ns

        # Check root element is a model
        if el != 'model':
            raise CellMLParsingError(
                'Root node must be a CellML model element.', element)

        # Check name is present
        try:
            name = element.attrib['name']
        except KeyError:
            raise CellMLParsingError(
                'Model element must have a name attribute.', element)

        # Create model (validates name)
        try:
            model = myokit.formats.cellml.v2.Model(name, version)
        except myokit.formats.cellml.v2.CellMLError as e:
            raise CellMLParsingError(str(e), element)

        # Check id
        self._check_id(element, model)

        # Check for imports
        im = element.find(self._join('import'))
        if im is not None:
            raise CellMLParsingError('Imports are not supported.', im)

        # Check allowed content
        self._check_allowed_content(
            element,
            ['component', 'connection', 'encapsulation', 'units'],
            ['name'],
            name,
        )

        # Create model units
        for child in self._sort_units(element):
            self._parse_units(child, model)

        # Create components
        components = element.findall(self._join('component'))
        for child in components:
            self._parse_component(child, model)

        # Create encapsulation hierarchy
        encapsulation = element.findall(self._join('encapsulation'))
        if len(encapsulation) > 1:
            raise CellMLParsingError(
                'A model cannot contain more than one encapsulation element.',
                encapsulation[1])
        for child in encapsulation:
            self._parse_encapsulation(child, model)

        # Add connections
        connected = set()
        for child in element.findall(self._join('connection')):
            self._parse_connection(child, model, connected)

        # Add equations
        for child in components:
            component = model.component(child.attrib['name'])
            for math in child.findall(self._join('math', cellml.NS_MATHML)):
                self._parse_math(math, component)

        # Check number of variables of integration
        try:
            for var in self._vois:
                model.set_variable_of_integration(var.var())
        except myokit.formats.cellml.v2.CellMLError as e:
            raise CellMLParsingError(
                'Models that take derivatives with respect to more than one'
                ' variable are not supported (' + str(e) + ').')

        # Read any rdf annotations
        # TODO: Allow RDF annotations from external files

        # Perform final validation and return
        model.validate()

        return model

    def _parse_unit(self, element, owner):
        """
        Parses a unit ``element`` and returns a :class:`myokit.Unit`, using the
        :class:`Model` or :class:`Component` ``owner`` is used to look up
        units definitions.
        """

        # Get units attribute (already checked)
        units = element.attrib['units']

        # Check id
        self._check_id(element)

        # Get prefix, exponent, and multiplier
        prefix = element.attrib.get('prefix', 0)
        exponent = element.attrib.get('exponent', 1)
        multiplier = element.attrib.get('multiplier', 1)

        # Check allowed content
        self._check_allowed_content(
            element, [], ['units', 'prefix', 'exponent', 'multiplier'])

        # Create and return
        return myokit.formats.cellml.v2.Units.parse_unit_row(
            units, prefix, exponent, multiplier, owner)

    def _parse_units(self, element, owner):
        """
        Parses a units ``element``, adding the resulting units definition to
        the :class:`Model` ``owner``.
        """

        # Name has already been checked at this point
        name = element.attrib['name']

        # Check id
        self._check_id(element)

        # Check allowed content
        self._check_allowed_content(element, ['unit'], ['name'], name)

        # Check the units definition has children
        children = element.findall(self._join('unit'))
        if not children:
            warnings.warn(
                'Unable to parse definition for units "' + str(name) + '",'
                ' using `dimensionless instead. (Defining new base units is'
                ' not supported.)')

        # Parse content
        myokit_unit = myokit.units.dimensionless
        for child in children:
            myokit_unit *= self._parse_unit(child, owner)

        # Add units to owner
        try:
            owner.add_units(name, myokit_unit)
        except myokit.formats.cellml.v2.CellMLError as e:
            raise CellMLParsingError(str(e), element)

    def _parse_variable(self, element, component):
        """
        Parses a variable ``element`` and adds a variable to the given
        ``component``.
        """
        # Check name is present
        try:
            name = element.attrib['name']
        except KeyError:
            raise CellMLParsingError(
                'Variable element must have a name attribute.',
                element)

        # Check units are present
        try:
            units = element.attrib['units']
        except KeyError:
            raise CellMLParsingError(
                'Variable element must have a units attribute.',
                element)

        # Get interface
        interface = element.attrib.get('interface', 'none')

        # Create variable (validates name, units, interface, and uniqueness)
        try:
            variable = component.add_variable(name, units, interface)

            # Check id
            self._check_id(element, variable)

            # Check allowed content
            attr = [
                'initial_value',
                'name',
                'interface',
                'units',
            ]
            self._check_allowed_content(element, [], attr, name)

            # Set initial value
            variable.set_initial_value(
                element.attrib.get('initial_value', None))

        except myokit.formats.cellml.v2.CellMLError as e:
            raise CellMLParsingError(str(e), element)

    def _sort_units(self, element):
        """
        Returns all units elements in ``element``, sorted in an order that
        makes them resolvable.

        Arguments

        ``element``
            A model element.
        """
        # Create a list of resolved and a dict mapping unresolved unit names to
        # their unknown dependencies
        resolved = set()
        unresolved = {}

        # Add SI units to the list of resolved units
        si_units = set(myokit.formats.cellml.v2.Units.si_unit_names())
        resolved.update(si_units)

        # Mapping of local units to their elementtree elements
        local_units = {}

        # Populate the set of unresolved units.
        for units in element.findall(self._join('units')):
            # Get name, complain if it doesn't exist
            try:
                name = units.attrib['name']
            except KeyError:
                raise CellMLParsingError(
                    'Units element must have a name attribute.',
                    element)

            # Check doesn't shadow an si unit
            if name in si_units:
                raise CellMLParsingError(
                    'Units name "' + name + '" overlaps with a predefined name'
                    ' in ' + self._tag(element) + '.', element)

            # Check for duplicates
            if name in local_units:
                raise CellMLParsingError(
                    'Duplicate units definition "' + name + '" in '
                    + self._tag(element) + '.', element)
            local_units[name] = units

            # Determine dependencies
            deps = set()
            for unit in units.findall(self._join('unit')):
                try:
                    dep = unit.attrib['units']
                except KeyError:
                    raise CellMLParsingError(
                        'Unit elements must have a units attribute.',
                        element)
                deps.add(dep)
            unresolved[name] = deps

        # Remove resolved variables from deps
        for name, deps in unresolved.items():
            deps.difference_update(resolved)

        # Sort
        ordered = []
        while unresolved:
            fresh = set()
            for name, deps in unresolved.items():
                if not deps:
                    fresh.add(name)
                    ordered.append(local_units[name])
            if fresh:
                for name in fresh:
                    resolved.add(name)
                    del unresolved[name]
                for name, deps in unresolved.items():
                    deps.difference_update(fresh)
            else:
                raise CellMLParsingError(
                    'Unable to resolve network of units in '
                    + self._tag(element) + '.', element)
        return ordered

    def _tag(self, element, name=None):
        """
        Returns an element's name, but changes the syntax from ``{...}tag`` to
        ``cellml:tag`` for CellML elements.

        If the element is in a CellML namespace and an optional ``name``
        attribute is given, this is added to the returned output using xpath
        syntax, e.g. ``cellml:model[@name="MyModel"]``.

        Can also be used for attributes.
        """
        ns, el = split(element.tag)
        tag = self._item(ns, el)
        if ns == self._ns and name is not None:
            tag += '[@name="' + name + '"]'
        return tag

