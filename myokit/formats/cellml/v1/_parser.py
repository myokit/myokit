#
# Parses a CellML 1.0 or 1.1 document.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import collections
import warnings

from lxml import etree

import myokit
import myokit.formats.mathml
import myokit.formats.cellml as cellml
import myokit.formats.cellml.v1

from myokit.formats.xml import split


def parse_file(path):
    """
    Parses a CellML 1.0 or 1.1 model at the given path and returns a
    :class:`myokit.formats.cellml.v1.Model`.

    Raises a :class:`CellMLParsingError` if anything goes wrong.

    For notes about CellML 1.0/1.1 support, see
    :class:`myokit.formats.cellml.v1.Model`.
    """
    return CellMLParser().parse_file(path)


def parse_string(text):
    """
    Parses a CellML 1.0 or 1.1 model from the given string and returns a
    :class:`myokit.formats.cellml.v1.Model`.

    Raises a :class:`CellMLParsingError` if anything goes wrong.

    For notes about CellML 1.0/1.1 support, see
    :class:`myokit.formats.cellml.v1.Model`.
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
    Parses CellML 1.0 and 1.1 documents, and performs (partial) validation of a
    CellML document.

    For notes about CellML 1.0/1.1 support, see
    :class:`myokit.formats.cellml.v1.Model`.
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
                    'Text found in ' + self._tag(element, name) + '.', element)

        # Not extension namespaces
        not_ext_ns = (
            self._ns, cellml.NS_CMETA, cellml.NS_RDF, cellml.NS_MATHML)

        # Check child elements
        allowed = set([self._join(x) for x in children])
        allowed.add(self._join('RDF', cellml.NS_RDF))
        if math:
            allowed.add(self._join('math', cellml.NS_MATHML))

        # Check if only contains allowed child elements
        for child in element:
            # Check for trailing text
            if child.tail is not None and child.tail.strip():
                raise CellMLParsingError(
                    'Text found in ' + self._tag(element, name)
                    + ' (after ' + self._tag(child) + ' element).',
                    child)

            # Check if allowed
            if str(child.tag) in allowed:
                continue

            # Check if in an extension element
            ns = split(child.tag)[0]
            if ns in not_ext_ns:
                raise CellMLParsingError(
                    'Unexpected content type in ' + self._tag(element, name)
                    + ', found element of type ' + self._tag(child) + '.',
                    child)
            else:
                # Check if CellML appearing in non-CellML elements
                # But leave checking inside MathML for later
                self._check_for_cellml_in_extensions(child)

        # Check attributes
        allowed = set(attributes)
        cmeta_id = self._join('id', cellml.NS_CMETA)
        for key in element.attrib:
            # Cmeta id is always allowed
            if key == cmeta_id:
                continue

            # Extension namespaces are always allowed
            ns, at = split(key)
            if ns is not None and ns not in not_ext_ns:
                continue

            # No namespace, then must be in allowed list
            if key not in allowed:
                key = self._item(ns, at)
                raise CellMLParsingError(
                    'Unexpected attribute ' + key + ' found in '
                    + self._tag(element, name) + '.', element)

    def _check_for_cellml_in_extensions(self, element):
        """
        Checks that a non-CellML element does not contain CellML elements or
        attributes.
        """
        # Check if this element contains CellML attributes
        for key in element.attrib:
            ns, at = split(key)
            if ns == self._ns:
                raise CellMLParsingError(
                    'CellML attribute ' + self._item(ns, at) + ' found'
                    ' in extension element ' + self._tag(element)
                    + ' (2.4.3).', element)

        # Check if this element has CellML children
        for child in element:
            if split(child.tag)[0] == self._ns:
                raise CellMLParsingError(
                    'CellML element ' + self._tag(child) + ' found inside'
                    ' extension element ' + self._tag(element) + ' (2.4.3).',
                    child)

            # Recurse into children
            self._check_for_cellml_in_extensions(child)

    def _check_cmeta_id(self, element):
        """
        Checks and returns the ``cmeta_id`` of a given ``element``.

        If present, the well-formedness and uniqueness of the cmeta id is
        tested.
        """
        # Find attribute
        cmeta_id = element.attrib.get(self._join('id', cellml.NS_CMETA), None)
        if cmeta_id is None:
            return None

        # Check well-formedness
        if not cmeta_id:
            raise CellMLParsingError(
                'If present, a cmeta:id must be a non-empty string.', element)

        # Check uniqueness
        if cmeta_id in self._cmeta_ids:
            raise CellMLParsingError(
                'Duplicate cmeta:id "' + cmeta_id + '" (8.5.1).', element)

        # Store and return
        self._cmeta_ids.add(cmeta_id)
        return cmeta_id

    def flatten(self, element):
        """
        Converts an element tree to a plain text string.
        """
        import re
        import textwrap

        # Gather all text
        def gather(element, text=[]):
            """ Flatten and gather text. """
            if element.text is not None:
                text.append(element.text)
            for child in element:
                gather(child, text)
            if element.tail is not None:
                text.append(element.tail)
            return text

        # Gather text, replace whitespace
        text = ' '.join(gather(element)).strip()

        # Replace all whitespace except newlines with a single space
        text = re.sub(r'[ \t\f\r]+', ' ', text)

        # Remove leading/trailing spaces
        text = re.sub(r'[ \t\f\r]*[\n]+[ \t\f\r]*', '\n', text)

        # Remove double line-breaks
        text = re.sub(r'[\n][\n]+', '\n\n', text)

        # Replace non-ascii characters
        text = text.encode('ascii', errors='ignore').decode()

        # Space text so that it's readable(ish)
        lines = []
        for line in text.splitlines():
            if line:
                lines.extend(textwrap.wrap(line, width=75))
            else:
                lines.append('')
        text = '\n'.join(lines)

        return text

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
        elif ns == cellml.NS_RDF:
            return 'rdf:' + item
        elif ns == cellml.NS_CMETA:
            return 'cmeta:' + item
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
        self._cmeta_ids = set()
        self._free_vars = set()
        try:
            return self._parse_model(root)
        except myokit.formats.cellml.v1.CellMLError as e:
            raise CellMLParsingError(str(e))
        except myokit.formats.mathml.MathMLError as e:
            raise CellMLParsingError(str(e))
        finally:
            del self._ns, self._cmeta_ids, self._free_vars

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
                'Component element must have a name attribute (3.4.2.1).',
                element)

        # Create component (validates name and checks uniqueness)
        try:
            component = model.add_component(name)

            # Check cmeta id
            cmeta_id = self._check_cmeta_id(element)
            if cmeta_id:
                component.set_cmeta_id(cmeta_id)

        except myokit.formats.cellml.v1.CellMLError as e:
            raise CellMLParsingError(str(e), element)

        # Check for reactions
        reaction = element.find(self._join('reaction'))
        if reaction is not None:
            raise CellMLParsingError('Reactions are not supported.', reaction)

        # Check allowed content
        self._check_allowed_content(
            element, ['units', 'variable'], ['name'], name, math=True)

        # Create component units
        for child in self._sort_units(element, model):
            self._parse_units(child, component)

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
        # Check exactly one map_components is present
        map_components = element.findall(self._join('map_components'))
        if len(map_components) != 1:
            raise CellMLParsingError(
                'A connection must contain exactly one map_components element,'
                ' found ' + str(len(map_components)) + ' (3.4.4.1).', element)

        # Check at least one map_variables is present
        map_variables = element.findall(self._join('map_variables'))
        if len(map_variables) < 1:
            raise CellMLParsingError(
                'A connection must contain at least one map_variables element'
                ' (3.4.4.1).', element)

        # Check cmeta id
        self._check_cmeta_id(element)

        # Check allowed content
        self._check_allowed_content(
            element, ['map_components', 'map_variables'], [])

        # Parse map_components element
        c1, c2 = self._parse_connection_map_components(
            map_components[0], model, connected)

        # Parse map_variables elements
        for child in map_variables:
            self._parse_connection_map_variables(child, c1, c2)

    def _parse_connection_map_components(self, element, model, connected):
        """
        Parses a map_components ``element``.
        """
        # Get component_1 and component_2
        try:
            c1 = element.attrib['component_1']
        except KeyError:
            raise CellMLParsingError(
                'A map_components element must define a component_1 attribute'
                ' (3.4.5.1).', element)
        try:
            c2 = element.attrib['component_2']
        except KeyError:
            raise CellMLParsingError(
                'A map_components element must define a component_2 attribute'
                ' (3.4.5.1).', element)

        # Check components are different
        if c1 == c2:
            raise CellMLParsingError(
                'The component_1 and component_2 attributes in a'
                ' map_components element must be different, got "' + str(c1)
                + '" twice (3.4.5.4).', element)

        # Get components
        try:
            c1 = model.component(c1)
        except KeyError:
            raise CellMLParsingError(
                'A map_components component_1 attribute must refer to a'
                ' component in the current model, got "' + str(c1)
                + '" (3.4.5.2).', element)
        try:
            c2 = model.component(c2)
        except KeyError:
            raise CellMLParsingError(
                'A map_components component_2 attribute must refer to a'
                ' component in the current model, got "' + str(c2)
                + '" (3.4.5.3).', element)

        # Check components are not yet connected
        if (c1, c2) in connected:
            raise CellMLParsingError(
                'Each connection in a model must connect a unique pair of'
                ' components, found multiple for "' + c1.name() + '" and "'
                + c2.name() + '" (3.4.5.4).', element)
        connected.add((c1, c2))
        connected.add((c2, c1))

        # Check cmeta id
        self._check_cmeta_id(element)

        # Check allowed content
        self._check_allowed_content(
            element, [], ['component_1', 'component_2'])

        # Return components
        return c1, c2

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
                'A map_variables element must define a variable_1 attribute'
                ' (3.4.6.1).', element)
        try:
            v2 = element.attrib['variable_2']
        except KeyError:
            raise CellMLParsingError(
                'A map_variables element must define a variable_2 attribute'
                ' (3.4.6.1).', element)

        # Get variables
        try:
            v1 = c1.variable(v1)
        except KeyError:
            raise CellMLParsingError(
                'A map_variables variable_1 attribute must refer to a'
                ' variable in component_1, got "' + str(v1) + '" (3.4.6.2).',
                element)
        try:
            v2 = c2.variable(v2)
        except KeyError:
            raise CellMLParsingError(
                'A map_variables variable_2 attribute must refer to a'
                ' variable in component_2, got "' + str(v1) + '" (3.4.6.3).',
                element)

        # Connect variables
        model = c1.model()
        try:
            model.add_connection(v1, v2)
        except myokit.formats.cellml.v1.CellMLError as e:
            raise CellMLParsingError(str(e), element)

        # Check cmeta id
        self._check_cmeta_id(element)

        # Check allowed content
        self._check_allowed_content(element, [], ['variable_1', 'variable_2'])

    def _parse_documentation(self, element, model):
        """
        Parses an old-fashion <documentation> element (by flattening the
        content and adding it to the model's ``documentation`` meta data.
        """
        text = self.flatten(element)
        if text:
            if 'documentation' in model.meta:
                model.meta['documentation'] += '\n\n' + text
            else:
                model.meta['documentation'] = text

    def _parse_group(self, element, model):
        """
        Parses a group ``element`` and updates components in the given
        ``model``.
        """

        # Check cmeta id
        self._check_cmeta_id(element)

        # Check contains at least one component_ref and relationship_ref
        if element.find(self._join('component_ref')) is None:
            raise CellMLParsingError(
                'Group must contain at least one component_ref element'
                ' (6.4.1.1).', element)
        if element.find(self._join('relationship_ref')) is None:
            raise CellMLParsingError(
                'Group must contain at least one relationship_ref element'
                ' (6.4.1.1).', element)

        # Check allowed content
        self._check_allowed_content(
            element, ['relationship_ref', 'component_ref'], [])

        # Parse relationship refs
        relationships = set()
        for child in element.findall(self._join('relationship_ref')):
            self._parse_group_relationship_ref(child, relationships)

        # Parse component refs
        for child in element.findall(self._join('component_ref')):
            self._parse_group_component_ref(child, model, relationships)

    def _parse_group_component_ref(
            self, element, model, relationships, parent=None):
        """
        Parses a component_ref ``element``, using the information about its
        groups ``relationships``.

        If this component_ref is nested inside another component_ref, set the
        parent component as ``parent``.
        """
        # Check cmeta id
        self._check_cmeta_id(element)

        # Get component attribute
        try:
            component = element.attrib['component']
        except KeyError:
            raise CellMLParsingError(
                'A component_ref must define a component attribute (6.4.3.1).',
                element)

        # Get component
        try:
            component = model.component(component)
        except KeyError:
            raise CellMLParsingError(
                'A component_ref\'s component attribute must reference a'
                ' component in the same model, got "' + component
                + '" (6.4.3.3).', element)

        # Check allowed content
        self._check_allowed_content(element, ['component_ref'], ['component'])

        # Store encapsulation relationships
        # Ignore all other types of relationship
        if parent is not None and 'encapsulation' in relationships:

            # Check for existing parent
            if component.parent() is not None:
                raise CellMLParsingError(
                    'A component can only have a single encapsulation parent:'
                    ' found ' + str(component) + ' with parents '
                    + str(component.parent()) + ' and ' + str(parent)
                    + ' (6.4.3.2).', element)

            # Set parent (won't raise CellMLErrors)
            component.set_parent(parent)

        # Check child component refs
        kids = element.findall(self._join('component_ref'))
        for child in kids:
            self._parse_group_component_ref(
                child, model, relationships, component)

        # No parent? Then (encapsulation and containment) relationships must
        # have at least one child.
        if len(kids) == 0 and parent is None:
            if ('encapsulation' in relationships
                    or 'containment' in relationships):
                raise CellMLParsingError(
                    'The first component_ref in an encapsulation or'
                    ' containment relationship must have at least one child'
                    ' (6.4.3.2).')

    def _parse_group_relationship_ref(self, element, relationships):
        """
        Parses a relationship_ref ``element`` and adds it to the set of
        ``relationships``.

        Named containment relationships will be added as ``containment, name``.
        """
        # Check cmeta id
        self._check_cmeta_id(element)

        # Check relationship is specified
        ns = None
        rel = element.attrib.get('relationship', None)
        if rel is None:
            # Check for relationship attribute in other namespace
            for at in element.attrib:
                ns, at = split(at)
                if at == 'relationship':
                    rel = 'other'
                    break
            if rel is None:
                raise CellMLParsingError(
                    'Relationship_ref must define a relationship attribute'
                    ' (6.4.2.1).', element)

        # Check type (only if in null namespace)
        if ns is None and rel not in ['encapsulation', 'containment']:
            raise CellMLParsingError(
                'Unknown relationship type: "' + rel + '", expecting either'
                ' "encapsulation" or "containment" (6.4.2.2).', element)

        # Check name, if given
        name = element.attrib.get('name', None)
        if name is not None:
            if rel == 'encapsulation':
                raise CellMLParsingError(
                    'Encapsulation relationships may not define a name'
                    ' attribute (6.4.2.4).', element)

            if not myokit.formats.cellml.v1.is_valid_identifier(name):
                raise CellMLParsingError(
                    'Relationship_ref name must be a valid CellML identifier,'
                    ' but found "' + name + '" (6.4.2.3).', element)
            rel += ', ' + name

        # Check uniqueness of relationship (only in null namespace)
        if ns is None and rel in relationships:
            raise CellMLParsingError(
                'Relationship_refs in each group must have a unique pair of'
                ' (relationship, name) attributes (6.4.2.5).', element)

        # Store relationsip
        relationships.add(rel)

        # Check allowed content
        self._check_allowed_content(element, [], ['relationship', 'name'])

    def _parse_math(self, element, component):
        """
        Parses a mathml:math ``element``, adding equations to the variables of
        the given ``component``.
        """

        # Get variables from component
        def variable_factory(name, element):
            try:
                var = component.variable(name)
            except KeyError:
                raise CellMLParsingError(
                    'Variable references in equation must name a variable from'
                    ' the local component (4.4.2.1).', element)

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
                    ' attribute (4.4.3.1).', element)

            # Find units in component
            try:
                units = component.find_units(units)
                units = units.myokit_unit()
            except myokit.formats.cellml.v1.UnitsError as e:
                warnings.warn(
                    'The units "' + str(units) + '" (referenced inside a'
                    ' MathML equation) are not supported and have been'
                    ' replaced by `dimensionless`. (' + str(e) + ')')
                units = myokit.units.dimensionless
            except myokit.formats.cellml.v1.CellMLError:
                raise CellMLParsingError(
                    'Unknown unit "' + str(units) + '" referenced inside a'
                    ' MathML equation (4.4.3.2).', element)

            # Create and return
            return myokit.Number(value, units)

        # Create parser
        p = myokit.formats.mathml.MathMLParser(
            variable_factory, number_factory, self._free_vars)

        # Iterate over applies, allowing for applies nested inside <semantics>
        # elements
        todo = collections.deque([x for x in element])
        while todo:
            child = todo.popleft()

            # Check each child is in MathML namespace
            ns, el = split(child.tag)
            if ns != cellml.NS_MATHML:
                raise CellMLParsingError(
                    'The contents of a mathml:math element must be in the'
                    ' mathml namespace, found "' + str(child.tag) + '" inside '
                    + str(component) + '.', child)

            # Ignore annotations
            if el in ['annotation', 'annotation-xml']:
                continue

            # Look inside of semantics elements
            if el == 'semantics':
                todo.extendleft(reversed(child))
                continue

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

            # Promote derivative, check non-derivatives have no initial value
            var = lhs.var()
            if isinstance(lhs, myokit.Derivative):
                var.set_is_state(True)
            elif var.initial_value() is not None:
                raise CellMLParsingError(
                    'Initial value and a defining equation found for'
                    ' non-state ' + str(var) + ': ' + self._dae_message,
                    child)

            # Check for double rhs
            if var.rhs() is not None:
                raise CellMLParsingError(
                    'Two defining equations found for ' + str(var) + ': '
                    + self._dae_message,
                    child)

            # Set rhs
            try:
                lhs.var().set_rhs(rhs)
            except myokit.formats.cellml.v1.CellMLError as e:
                raise CellMLParsingError(str(e), child)

    def _parse_model(self, element):
        """
        Parses a CellML model element.
        """
        # Handle document-level validation here.

        # Check namespace
        ns, el = split(element.tag)
        if ns == cellml.NS_CELLML_1_0:
            version = '1.0'
        elif ns == cellml.NS_CELLML_1_1:
            version = '1.1'
        else:
            raise CellMLParsingError(
                'Root node must be in CellML 1.0 or 1.1 namespace.', element)

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
                'Model element must have a name attribute (3.4.1.1).', element)

        # Create model (validates name)
        try:
            model = myokit.formats.cellml.v1.Model(name, version)

            # Check cmeta id
            cmeta_id = self._check_cmeta_id(element)
            if cmeta_id:
                model.set_cmeta_id(cmeta_id)

        except myokit.formats.cellml.v1.CellMLError as e:
            raise CellMLParsingError(str(e), element)

        # Check for imports
        im = element.find(self._join('import'))
        if im is not None:
            if version == '1.1':
                raise CellMLParsingError('Imports are not supported.', im)
            else:
                raise CellMLParsingError(
                    'Imports are not allowed in CellML 1.0.', im)

        # Check allowed content
        self._check_allowed_content(
            element,
            ['component', 'connection', 'group', 'units'],
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
        for child in element.findall(self._join('group')):
            self._parse_group(child, model)

        # Add connections
        connected = set()
        for child in element.findall(self._join('connection')):
            self._parse_connection(child, model, connected)

        # Add equations
        for child in components:
            component = model.component(child.attrib['name'])
            for math in child.findall(self._join('math', cellml.NS_MATHML)):
                self._parse_math(math, component)

        # Check number of free variables
        self._free_vars = set(
            [x.var().value_source() for x in self._free_vars])
        if len(self._free_vars) > 1:
            raise CellMLParsingError(
                'Models that take derivatives with respect to more than one'
                ' variable are not supported.')

        elif len(self._free_vars) == 1:
            # Set free variable
            model.set_free_variable(self._free_vars.pop())

        # Read any rdf annotations
        rdf_tag = self._join('RDF', cellml.NS_RDF)
        for child in element.findall(rdf_tag):
            self._parse_rdf(child, model)

        # Read any documentation
        doc_tag = self._join('documentation', cellml.NS_TMP_DOC)
        for child in element.findall(doc_tag):
            self._parse_documentation(child, model)

        # Perform final validation and return
        model.validate()

        return model

    def _parse_rdf(self, element, model):
        """
        Parses an RDF tag, looks for oxmeta annotations.
        """
        # rdf:Description tag with rdf:about attribute
        dtag = self._join('Description', cellml.NS_RDF)
        aatt = self._join('about', cellml.NS_RDF)

        # bqbiol:is tag with rdf:resource attribute
        itag = self._join('is', cellml.NS_BQBIOL)
        ratt = self._join('resource', cellml.NS_RDF)

        # Oxmeta namespace
        ox = cellml.NS_OXMETA

        # Look for descriptions
        for child in element.findall(dtag):

            # Get variable cmeta id
            about = child.attrib.get(aatt, None)
            if about is None:
                continue

            # Strip leading '#'
            about = about[1:]

            # Look for variable with that cmeta id
            try:
                variable = model.element_with_cmeta_id(about)
            except KeyError:
                continue
            if not isinstance(variable, myokit.formats.cellml.v1.Variable):
                continue

            # Get bqbiol:is element
            eis = child.find(itag)
            if eis is None:
                continue

            # Get resource
            resource = eis.attrib.get(ratt, None)
            if resource is None:
                continue

            # Strip oxmeta from annotation and store
            if not resource.startswith(ox):
                continue
            annotation = resource[len(ox):]
            variable.meta['oxmeta'] = annotation

    def _parse_unit(self, element, owner):
        """
        Parses a unit ``element`` and returns a :class:`myokit.Unit`, using the
        :class:`Model` or :class:`Component` ``owner`` is used to look up
        units definitions.
        """

        # Get units attribute (already checked)
        units = element.attrib['units']

        # Check cmeta id
        self._check_cmeta_id(element)

        # Get prefix, exponent, and multiplier
        prefix = element.attrib.get('prefix', 0)
        exponent = element.attrib.get('exponent', 1)
        multiplier = element.attrib.get('multiplier', 1)

        # Check for offset
        x = element.attrib.get('offset', 0)
        try:
            x = float(x)
        except ValueError:
            raise CellMLParsingError(
                'Unit offset must be a real number (5.4.2.6).', element)
        if x != 0:
            raise myokit.formats.cellml.v1.UnsupportedUnitOffsetError

        # Check allowed content
        self._check_allowed_content(
            element,
            [],
            ['units', 'prefix', 'exponent', 'multiplier', 'offset'],
        )

        # Create and return
        return myokit.formats.cellml.v1.Units.parse_unit_row(
            units, prefix, exponent, multiplier, owner)

    def _parse_units(self, element, owner):
        """
        Parses a units ``element``, adding the resulting units definition to
        the :class:`Model` or :class:`Component` ``owner``.
        """

        # Name has already been checked at this point
        name = element.attrib['name']

        # Check if this is a base unit (not supported)
        base = element.attrib.get('base_units', 'no')
        if base not in ('yes', 'no'):
            raise CellMLParsingError(
                'Base units attribute must be either "yes" or "no".', element)

        # Check cmeta id
        self._check_cmeta_id(element)

        # Check allowed content
        self._check_allowed_content(
            element, ['unit'], ['name', 'base_units'], name)

        # Check the units definition has children
        children = element.findall(self._join('unit'))
        if not children:
            if base == 'yes':
                warnings.warn(
                    'Unable to parse definition for units "' + str(name) + '",'
                    ' using `dimensionless` instead. (Defining new base units'
                    ' is not supported.)')
            else:
                raise CellMLParsingError(
                    'Units element with base_units="no" must contain at least'
                    ' one child unit element.')

        # Parse content
        myokit_unit = myokit.units.dimensionless
        try:
            for child in children:
                myokit_unit *= self._parse_unit(child, owner)
        except myokit.formats.cellml.v1.UnitsError as e:
            warnings.warn(
                'Unable to parse definition for units "' + str(name) + '",'
                ' using `dimensionless` instead. (' + str(e) + ')')
            myokit_unit = myokit.units.dimensionless

        # Add units to owner
        try:
            owner.add_units(name, myokit_unit)
        except myokit.formats.cellml.v1.CellMLError as e:
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
                'Variable element must have a name attribute (3.4.3.1).',
                element)

        # Check units are present
        try:
            units = element.attrib['units']
        except KeyError:
            raise CellMLParsingError(
                'Variable element must have a units attribute (3.4.3.1).',
                element)

        # Get interface
        pub = element.attrib.get('public_interface', 'none')
        pri = element.attrib.get('private_interface', 'none')

        # Create variable (validates name, units, and name uniqueness)
        try:
            try:
                variable = component.add_variable(name, units, pub, pri)
            except myokit.formats.cellml.v1.UnitsError as e:
                warnings.warn(
                    'The units "' + str(units) + '" (assigned to a variable)'
                    ' are not supported and have been replaced by'
                    ' `dimensionless`. (' + str(e) + ')')
                units = 'dimensionless'
                variable = component.add_variable(name, units, pub, pri)

            # Check cmeta id
            cmeta_id = self._check_cmeta_id(element)
            if cmeta_id:
                variable.set_cmeta_id(cmeta_id)

            # Check allowed content
            attr = [
                'initial_value',
                'name',
                'public_interface',
                'private_interface',
                'units',
            ]
            self._check_allowed_content(element, [], attr, name)

            # Set initial value
            variable.set_initial_value(
                element.attrib.get('initial_value', None))

        except myokit.formats.cellml.v1.CellMLError as e:
            raise CellMLParsingError(str(e), element)

    def _sort_units(self, element, model=None):
        """
        Returns all units elements in ``element``, sorted in an order that
        makes them resolvable.

        Arguments

        ``element``
            A model or component element
        ``model``
            If the owner is a component, a
            :class:`myokit.formats.cellml.v1.Model` can be passed in to look up
            any model units.

        """
        # Create a list of resolved and a dict mapping unresolved unit names to
        # their unknown dependencies
        resolved = set()
        unresolved = {}

        # Add SI units to the list of resolved units
        si_units = set(myokit.formats.cellml.v1.Units.si_unit_names())
        resolved.update(si_units)

        # If this is a component, add any model units to the list
        if model is not None:
            for units in model.units():
                resolved.add(units.name())

        # Mapping of local units to their elementtree elements
        local_units = {}

        # Populate the set of unresolved units.
        for units in element.findall(self._join('units')):
            # Get name, complain if it doesn't exist
            try:
                name = units.attrib['name']
            except KeyError:
                raise CellMLParsingError(
                    'Units element must have a name attribute (5.4.1.1).',
                    element)

            # Check doesn't shadow an si unit
            if name in si_units:
                raise CellMLParsingError(
                    'Units name "' + name + '" overlaps with a predefined name'
                    ' in ' + self._tag(element) + ' (5.4.1.2).', element)

            # Check for duplicates
            if name in local_units:
                raise CellMLParsingError(
                    'Duplicate units definition "' + name + '" in '
                    + self._tag(element) + '.', element)
            local_units[name] = units

            # Component units can shadow model units, so if known units are
            # found they will become 'unresolved' at this point.
            if name in resolved:
                resolved.remove(name)

            # Determine dependencies
            deps = set()
            for unit in units.findall(self._join('unit')):
                try:
                    dep = unit.attrib['units']
                except KeyError:
                    raise CellMLParsingError(
                        'Unit elements must have a units attribute (5.4.2.1).',
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
                    + self._tag(element) + ' (5.4.2.2).', element)
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

