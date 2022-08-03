#
# CellML 2.0 Writer: Writes a CellML Model to disk
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from lxml import etree

import myokit
import myokit.formats.cellml as cellml


def write_file(path, model):
    """
    Writes a CellML 2.0 model to the given path.
    """
    return CellMLWriter().write_file(path, model)


def write_string(model):
    """
    Writes a CellML 2.0 model to a string and returns it.
    """
    return CellMLWriter().write_string(model)


class CellMLWriter(object):
    """
    Writes CellML 2.0 documents.
    """

    # List of si unit names corresponding to myokit.Unit exponents
    _exp_si = None

    # Note: Most items are sorted, to get closer to a 'canonical form' CellML
    # document: https://github.com/cellml/libcellml/issues/289

    def _component(self, parent, component, voi):
        """
        Adds an etree ``Element`` to a ``parent`` element, representing the
        given CellML ``component``.
        """

        # Create component element
        element = etree.SubElement(parent, 'component')
        element.attrib['name'] = component.name()

        # Add variables
        for variable in sorted(component.variables(), key=_name):
            self._variable(element, variable)

        # Add maths
        self._maths(element, component, voi)

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

        # Scan all connections
        for v1, v2 in model.connections():
            c1 = v1.component()
            c2 = v2.component()

            # Order components alphabetically
            if c2.name() < c1.name():
                c1, c2 = c2, c1
                v1, v2 = v2, v1

            # Store the connection
            try:
                vrs = connections[(c1, c2)]
            except KeyError:
                connections[(c1, c2)] = vrs = set()
            vrs.add((v1, v2))

        # Add elements
        for cs, vs in sorted(connections.items(), key=lambda x: _names(x[0])):

            # Add connection
            connection = etree.SubElement(parent, 'connection')
            connection.attrib['component_1'] = cs[0].name()
            connection.attrib['component_2'] = cs[1].name()

            # Add variables
            for v1, v2 in sorted(vs, key=_names):
                map_variables = etree.SubElement(connection, 'map_variables')
                map_variables.attrib['variable_1'] = v1.name()
                map_variables.attrib['variable_2'] = v2.name()

    def _encapsulation(self, parent, model):
        """
        Adds an ``encapsulation`` element to ``parent`` that contains all
        encapsulation relationships present in the given ``model``.
        """

        # Check if this model has encapsulation relationships, if not: return
        has_encapsulation = False
        for component in model:
            if component.parent() is not None:
                has_encapsulation = True
                break
        if not has_encapsulation:
            return

        # Create element
        element = etree.SubElement(parent, 'encapsulation')

        # Add all unencapsulated components that have children
        for component in sorted(model, key=_name):
            if component.parent() is None and component.has_children():
                self._encapsulation_component_ref(element, component)

    def _encapsulation_component_ref(self, parent, component):
        """
        Adds a ``component_ref`` element for ``component`` to ``parent``, and
        then recurses to any children of the component.
        """

        # Create element
        element = etree.SubElement(parent, 'component_ref')
        element.attrib['component'] = component.name()

        # Add children
        for child in sorted(component.children(), key=_name):
            self._encapsulation_component_ref(element, child)

    def _maths(self, parent, component, voi):
        """
        Adds a ``math`` element to the given ``parent`` containing the maths
        for the variables in ``component``.

        Derivatives will be written with reference to a local variable in the
        connected variable set of the variable of integration ``voi``.
        """

        # Test if this component has maths
        has_maths = False
        for v in component:
            if v.rhs() is not None:
                has_maths = True
                break
        if not has_maths:
            return

        # Find local alias of the variable of integration (in valid models,
        # this will always be set if states are present in this component).
        if voi is not None:
            if voi.component() is not component:
                for var in voi.connected_variables():
                    if var.component() is component:
                        voi = var
                        break

        # Create expression writer for this component
        from myokit.formats.cellml import CellMLExpressionWriter
        model = component.model()
        ewriter = CellMLExpressionWriter(model.version())
        ewriter.set_lhs_function(lambda x: x.var().name())
        ewriter.set_unit_function(lambda x: model.find_units_name(x))
        if voi is not None:
            ewriter.set_time_variable(voi)

        # Reset default namespace to MathML namespace
        nsmap = {None: cellml.NS_MATHML}
        #if component.model().version() == '2.0':
        nsmap['cellml'] = cellml.NS_CELLML_2_0

        # Create math elements
        math = etree.SubElement(parent, 'math', nsmap=nsmap)

        # Add maths for variables
        for variable in sorted(component, key=_name):
            if variable.equation_variable() is variable:
                ewriter.eq(variable.equation(), math)

    def _model(self, model):
        """
        Returns an etree ``Element`` representing the given ``model``.
        """

        # Load correct namespaces
        version = model.version()
        # if version == '2.0':
        namespaces = {None: cellml.NS_CELLML_2_0}
        namespaces['cellml'] = namespaces[None]

        # Create model element
        element = etree.Element('model', nsmap=namespaces)

        # Set model name
        element.attrib['name'] = model.name()

        # Add units
        for units in sorted(model.units(), key=_name):
            self._units(element, units)

        # Add components
        voi = model.variable_of_integration()
        for component in sorted(model, key=_name):
            self._component(element, component, voi)

        # Add connections
        self._connections(element, model)

        # Add encapsulation
        self._encapsulation(element, model)

        # Return model element
        return element

    def _units(self, parent, units):
        """
        Adds a ``units`` element to ``parent``, for the given CellML units
        object.
        """
        # Get unit exponents on first call
        if self._exp_si is None:
            from myokit.formats.cellml import v2
            self._exp_si = [
                v2.Units._si_units_r[x] for x in myokit.Unit.list_exponents()]

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
                row.attrib['units'] = self._exp_si[k]
                if e != 1:
                    row.attrib['exponent'] = str(e)
                rows.append(row)

        # Handle dimensionless units with a multiplier
        if not rows:
            row = etree.SubElement(element, 'unit')
            row.attrib['units'] = 'dimensionless'
            rows.append(row)

        # Add multiplier or prefix to first row
        multiplier = myokit_unit.multiplier()
        if multiplier != 1:
            if myokit.float.eq(multiplier, int(multiplier)):
                rows[0].attrib['multiplier'] = str(int(multiplier))
            else:
                rows[0].attrib['multiplier'] = myokit.float.str(
                    multiplier).strip()

    def _variable(self, parent, variable):
        """
        Adds a ``variable`` element to ``parent`` for the variable represented
        by :class:`myokit.formats.cellml.v2.Variable` ``variable``.
        """

        # Create element
        element = etree.SubElement(parent, 'variable')
        element.attrib['name'] = variable.name()

        # Add units
        element.attrib['units'] = variable.units().name()

        # Add interfaces
        if variable.interface() != 'none':
            element.attrib['interface'] = variable.interface()

        # Add initial value
        if variable is variable.initial_value_variable():
            value = myokit.float.str(variable.initial_value()).strip()
            if value[-4:] == 'e+00':
                value = value[:-4]
            element.attrib['initial_value'] = value

    def write(self, model):
        """
        Takes a :class:`myokit.formats.cellml.v2.Model` as input, and
        creates an ElementTree that represents it.

        If the model contains any variables that have an `oxmeta` meta data
        property, this will be annotated with RDF tags suitable for use with
        the Cardiac Electrophysiology Web Lab.
        """
        # Validate model
        model.validate()

        try:
            # Variables with an oxmeta annotation and a cmeta:id will get an
            # annotation suitable for use with the web lab. This dict maps
            # cmeta:id strings to oxmeta annotations.
            self._oxmeta_variables = {}

            # Temporarily store variable of integration (in valid models, this
            # is always set if states are used).
            self._time = model.variable_of_integration()

            # Create model element (with children)
            element = self._model(model)

            # Wrap in ElementTree and return
            return etree.ElementTree(element)

        finally:
            # Delete any temporary properties
            del self._oxmeta_variables, self._time

    def write_file(self, path, model):
        """
        Takes a :class:`myokit.formats.cellml.v2.Model` as input, and writes it
        to the given ``path``.

        See :meth:`write()` for details.
        """

        # Create ElementTree
        tree = self.write(model)

        # Write to disk
        tree.write(
            path,
            encoding='utf-8',
            method='xml',
            xml_declaration=True,
            pretty_print=True,
        )
        # Note: Can use method='c14n' to get canonical output, but that also
        # removes the xml declaration, which I quite like having!

    def write_string(self, model):
        """
        Takes a :class:`myokit.formats.cellml.v2.Model` as input, and converts
        it to an XML string.

        See :meth:`write()` for details.
        """

        # Create ElementTree
        tree = self.write(model)

        # Write to string
        return etree.tostring(
            tree,
            encoding='utf-8',
            method='xml',
            pretty_print=True,
        )


def _name(x):
    """ Sort by name. """
    return x.name()


def _names(x):
    """ Sort by names. """
    return x[0].name(), x[1].name()

