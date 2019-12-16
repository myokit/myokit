#
# CellML 1.0/1.1 Writer: Writes a cellml_1.Model to disk
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
from myokit.formats.cellml import cellml_1 as cellml


# Import lxml or default etree
_lxml = True
try:
    from lxml import etree
except ImportError:
    _lxml = False
    import xml.etree.ElementTree as etree


# List of si unit names corresponding to myokit.Unit exponents
_exp_si = [cellml.Units._si_units_r[x] for x in myokit.Unit.list_exponents()]


def write_file(path, model):
    """
    Writes a CellML 1.0 or 1.1 model to the given path.

    Raises a :class:`CellMLWritingError` if anything goes wrong.
    """
    return CellMLWriter().write_file(path, model)


def write_string(model):
    """
    Writes a CellML 1.0 or 1.1 model to a string and returns it.

    Raises a :class:`CellMLWritingError` if anything goes wrong.
    """
    return CellMLWriter().write_string(model)


class CellMLWritingError(myokit.ImportError):
    """
    Raised if an error occurs during CellML writing.
    """
    def __init__(self, message):
        super(CellMLWritingError, self).__init__(message)


class CellMLWriter(object):
    """
    Writes CellML 1.0 documents.
    """
    def _component(self, parent, component):
        """
        Adds an etree ``Element`` to a ``parent`` element, representing the
        given CellML ``component``.
        """

        # Create component element
        element = etree.SubElement(parent, 'component')
        element.attrib['name'] = component.name()

        # Add units
        for units in component.units():
            self._units(element, units)

        # Add variables
        for variable in component.variables():
            self._variable(element, variable)

        # Add maths
        self._maths(element, component)

    def _connections(self, parent, model):
        """
        Adds ``connections`` elements to the given ``parent`` tag for all
        connections needed in ``model``.
        """

        # Create a dictionary where each key is a pair
        # ``(component_1, component_2)`` ordered alphabetically by name, and
        # each value is a (non-empty) list of ``(variable_1, variable_2)``
        # pairs, such that ``variable_1`` is in ``component_1`` and
        # ``variable_2`` is in ``component_2``.
        connections = {}

        # Scan all variables
        for c in model:
            for v1 in c:
                # Get interface-in variables that require a connection
                v2 = v1.source()
                if v2 is None:
                    continue
                c1 = c  # Copy here, in case we swap c1 and c2 later
                c2 = v2.component()

                # Ensure components are ordered alphabetically
                if c2.name() < c1.name():
                    c1, c2 = c2, c1
                    v1, v2 = v2, v1

                # Add connected variables to list
                try:
                    vrs = connections[(c1, c2)]
                except KeyError:
                    connections[(c1, c2)] = vrs = []
                vrs.append((v1, v2))

        # Add elements
        for cs, vs in connections.items():

            # Add connection
            connection = etree.SubElement(parent, 'connection')
            map_components = etree.SubElement(connection, 'map_components')
            map_components.attrib['component_1'] = cs[0].name()
            map_components.attrib['component_2'] = cs[1].name()

            # Add variables
            for v1, v2 in vs:
                map_variables = etree.SubElement(connection, 'map_variables')
                map_variables.attrib['variable_1'] = v1.name()
                map_variables.attrib['variable_2'] = v2.name()

    def _groups(self, parent, model):
        """
        Adds a ``group`` element to ``parent`` that contains any encapsulation
        relationships present in the given ``model``.
        """

        # Check if this model has encapsulation relationships, if not: return
        has_encapsulation = False
        for component in model:
            if component.parent() is not None:
                has_encapsulation = True
                break
        if not has_encapsulation:
            return

        # Create group
        element = etree.SubElement(parent, 'group')
        relationship_ref = etree.SubElement(element, 'relationship_ref')
        relationship_ref.attrib['relationship'] = 'encapsulation'

        # Add all unencapsulated components that have children
        for component in model:
            if component.parent() is None and component.has_children():
                self._group_component_ref(element, component)

    def _group_component_ref(self, parent, component):
        """
        Adds a ``component_ref`` element for ``component`` to ``parent``, and
        then recurses to any children of the component.
        """

        # Create element
        element = etree.SubElement(parent, 'component_ref')
        element.attrib['component'] = component.name()

        # Add children
        for child in component.children():
            self._group_component_ref(element, child)

    def _maths(self, parent, component):
        """
        Adds a ``math`` element to the given ``parent`` containing the maths
        for the variables in ``component``.
        """

        # Test if this component has maths
        has_maths = False
        for v in component:
            if v.rhs() is not None:
                has_maths = True
                break
        if not has_maths:
            return

        # Find free variable alias in local component
        # In valid models, this will always be set if states are present in
        # this component.
        free = None
        for v in component:
            if v.value_source().is_free():
                free = v
                break

        # Create expression writer for this component
        from myokit.formats.cellml import CellMLExpressionWriter
        ewriter = CellMLExpressionWriter()
        ewriter.set_element_tree_class(etree)
        ewriter.set_lhs_function(lambda x: x.var().name())
        ewriter.set_unit_function(lambda x: component.find_units_name(x))
        if free is not None:
            ewriter.set_time_variable(free)

        # Add math element and reset default namespace to MathML namespace
        math = etree.SubElement(parent, 'math')
        math.attrib['xmlns'] = cellml.NS_MATHML

        # Add maths for variables
        for variable in component:
            # Check RHS
            rhs = variable.rhs()
            if rhs is None:
                continue

            # Get LHS
            lhs = myokit.Name(variable)
            if variable.is_state():
                lhs = myokit.Derivative(lhs)

            ewriter.eq(myokit.Equation(lhs, variable.rhs()), math)

    def _model(self, model):
        """
        Returns an etree ``Element`` representing the given ``model``.
        """
        # Create model element
        #TODO: Be flexible about namespace
        namespaces = {
            None: cellml.NS_CELLML_1_0,
            'cellml': cellml.NS_CELLML_1_0,
        }
        if _lxml:
            element = etree.Element('model', nsmap=namespaces)
        else:
            element = etree.Element('model')
            element.attrib['xmlns'] = cellml.NS_CELLML_1_0
            for prefix, ns in namespaces.items():
                if prefix is not None:
                    print('xmlns:' + prefix)
                    element.attrib['xmlns:' + prefix] = ns

        # Set model name
        element.attrib['name'] = model.name()

        # Add units
        for units in model.units():
            self._units(element, units)

        # Add components
        for component in model:
            self._component(element, component)

        # Add connections
        self._connections(element, model)

        # Add groups
        self._groups(element, model)

        # Return model element
        return element

    def _units(self, parent, units):
        """
        Adds a ``units`` element to ``parent``, for the given cellml units
        object.
        """

        # Create units element
        element = etree.SubElement(parent, 'units')
        element.attrib['name'] = units.name()

        # Get myokit unit
        myokit_unit = units.myokit_unit()

        # Add unit row for each of the 7 SI units needed to make up this unit
        rows = []
        for k, e in enumerate(myokit_unit.exponents()):
            if e != 0:
                row = etree.SubElement(element, 'unit')
                row.attrib['units'] = _exp_si[k]
                if e != 1:
                    row.attrib['exponent'] = str(e)     # Must be an integer
                rows.append(row)

        # Handle dimensionless units with a multiplier
        if not rows:
            row = etree.SubElement(element, 'unit')
            row.attrib['units'] = 'dimensionless'
            rows.append(row)

        # Add multiplier or prefix to first row
        multiplier = myokit_unit.multiplier()
        if multiplier != 1:
            if myokit._feq(multiplier, int(multiplier)):
                rows[0].attrib['multiplier'] = str(int(multiplier))
            else:
                rows[0].attrib['multiplier'] = myokit.strfloat(multiplier)

    def write(self, model):
        """
        Takes a :meth:`myokit.formats.cellml.cellml_1.Model` as input, and
        creates an ElementTree that represents it.
        """
        # Validate model
        model.validate()

        try:
            # Temporarily store free variable (in valid models, this is always
            # set if states are used).
            self._time = model.free_variable()

            # Create model element (with children)
            element = self._model(model)

            # Wrap in ElementTree and return
            return etree.ElementTree(element)

        finally:
            # Delete any temporary properties
            del(self._time)

    def _variable(self, parent, variable):
        """
        Adds a ``variable`` element to ``parent`` for the variable represented
        by :meth:`myokit.formats.cellml.cellml_1.Variable` ``variable``.
        """

        # Create element
        element = etree.SubElement(parent, 'variable')
        element.attrib['name'] = variable.name()

        # Add units
        element.attrib['units'] = variable.units().name()

        # Add interfaces
        if variable.public_interface() != 'none':
            element.attrib['public_interface'] = variable.public_interface()
        if variable.private_interface() != 'none':
            element.attrib['private_interface'] = variable.private_interface()

        # Add initial value
        if variable.initial_value() is not None:
            element.attrib['initial_value'] = myokit.strfloat(
                variable.initial_value())

    def write_file(self, path, model):
        """
        Takes a :meth:`myokit.formats.cellml.cellml_1.Model` as input, and
        writes it to the given ``path``.
        """

        # Create ElementTree
        tree = self.write(model)

        # Write to disk
        kwargs = {
            'encoding': 'utf-8',
            'method': 'xml',
            'xml_declaration': True,
        }
        if _lxml:   # pragma: no cover
            kwargs['pretty_print'] = True
        tree.write(path, **kwargs)

        # Prettify, if not using lxml
        if not _lxml:
            import xml.dom.minidom as m
            xml = m.parse(path)
            with open(path, 'wb') as f:
                f.write(xml.toprettyxml(encoding='utf-8'))

    def write_string(self, model):
        """
        Takes a :meth:`myokit.formats.cellml.cellml_1.Model` as input, and
        converts it to an XML string.
        """

        # Create ElementTree
        tree = self.write(model)

        # Write to string
        kwargs = {
            'encoding': 'utf-8',
            'method': 'xml',
        }
        if _lxml:   # pragma: no cover
            kwargs['pretty_print'] = True
        return etree.tostring(tree, **kwargs)

