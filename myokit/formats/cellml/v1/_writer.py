#
# CellML 1.0/1.1 Writer: Writes a CellML Model to disk
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from lxml import etree

import myokit
import myokit.formats.cellml as cellml

# Quoting URI strings in Python2 and Python3
try:
    from urllib.parse import quote
except ImportError:     # pragma: no python 3 cover
    # Python 2
    from urllib import quote


# Left-over from old exporter. Not sure if this had any function.
# Add name in 'tmp-documentation' format
# emodel.attrib['name'] = 'generated_model'
# if 'name' in model.meta:
#     dtag = et.SubElement(emodel, 'documentation')
#     dtag.attrib['xmlns'] = NS_TMP_DOC
#     atag = et.SubElement(dtag, 'article')
#     ttag = et.SubElement(atag, 'title')
#     ttag.text = model.meta['name']


def write_file(path, model):
    """
    Writes a CellML 1.0 or 1.1 model to the given path.
    """
    return CellMLWriter().write_file(path, model)


def write_string(model):
    """
    Writes a CellML 1.0 or 1.1 model to a string and returns it.
    """
    return CellMLWriter().write_string(model)


class CellMLWriter(object):
    """
    Writes CellML 1.0 or 1.1 documents.
    """

    # List of si unit names corresponding to myokit.Unit exponents
    _exp_si = None

    # Note: Most items are sorted, to get closer to a 'canonical form' CellML
    # document: https://github.com/cellml/libcellml/issues/289

    def _component(self, parent, component):
        """
        Adds an etree ``Element`` to a ``parent`` element, representing the
        given CellML ``component``.
        """

        # Create component element
        element = etree.SubElement(parent, 'component')
        element.attrib['name'] = component.name()

        # Add units
        for units in sorted(component.units(), key=_name):
            self._units(element, units)

        # Add variables
        for variable in sorted(component.variables(), key=_name):
            self._variable(element, variable)

        # Add maths
        self._maths(element, component)

        # Add cmeta id
        cid = component.cmeta_id()
        if cid is not None:
            element.attrib[etree.QName(cellml.NS_CMETA, 'id')] = cid

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
        for cs, vs in sorted(connections.items(), key=lambda x: _names(x[0])):

            # Add connection
            connection = etree.SubElement(parent, 'connection')
            map_components = etree.SubElement(connection, 'map_components')
            map_components.attrib['component_1'] = cs[0].name()
            map_components.attrib['component_2'] = cs[1].name()

            # Add variables
            for v1, v2 in sorted(vs, key=_names):
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
        for component in sorted(model, key=_name):
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
        for child in sorted(component.children(), key=_name):
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
        ewriter = CellMLExpressionWriter(component.model().version())
        ewriter.set_lhs_function(lambda x: x.var().name())
        ewriter.set_unit_function(lambda x: component.find_units_name(x))
        if free is not None:
            ewriter.set_time_variable(free)

        # Reset default namespace to MathML namespace
        nsmap = {None: cellml.NS_MATHML}
        if component.model().version() == '1.0':
            nsmap['cellml'] = cellml.NS_CELLML_1_0
        else:
            nsmap['cellml'] = cellml.NS_CELLML_1_1

        # Create math elements
        math = etree.SubElement(parent, 'math', nsmap=nsmap)

        # Add maths for variables
        for variable in sorted(component, key=_name):
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

        # Load correct namespaces
        version = model.version()
        assert version in ('1.0', '1.1')    # Model ensures this
        if version == '1.0':
            namespaces = {None: cellml.NS_CELLML_1_0}
        else:
            namespaces = {None: cellml.NS_CELLML_1_1}
        namespaces['cellml'] = namespaces[None]
        namespaces['cmeta'] = cellml.NS_CMETA
        namespaces['bqbiol'] = cellml.NS_BQBIOL
        namespaces['rdf'] = cellml.NS_RDF

        # Create model element
        element = etree.Element('model', nsmap=namespaces)

        # Set model name
        element.attrib['name'] = model.name()

        # Add units
        for units in sorted(model.units(), key=_name):
            self._units(element, units)

        # Add components
        for component in sorted(model, key=_name):
            self._component(element, component)

        # Add connections
        self._connections(element, model)

        # Add groups
        self._groups(element, model)

        # Add cmeta id
        cid = model.cmeta_id()
        if cid is not None:
            element.attrib[etree.QName(cellml.NS_CMETA, 'id')] = cid

        # Add oxmeta annotations
        self._oxmeta_annotations(element)

        # Return model element
        return element

    def _oxmeta_annotations(self, parent):
        """
        Adds RDF annotations suitable for use with the web lab, for any
        variable that has an `oxmeta` meta data property and a `cmeta_id`.
        """
        # Check if there's anything to do
        if len(self._oxmeta_variables) == 0:
            return

        # Create parent RDF tag
        rdf = etree.SubElement(parent, etree.QName(cellml.NS_RDF, 'RDF'))

        # Add annotations
        for cid, annotation in sorted(
                self._oxmeta_variables.items(), key=lambda x: x[0]):
            description = etree.SubElement(
                rdf, etree.QName(cellml.NS_RDF, 'Description'))
            description.attrib[etree.QName(cellml.NS_RDF, 'about')] = '#' + cid
            iz = etree.SubElement(
                description, etree.QName(cellml.NS_BQBIOL, 'is'))
            iz.attrib[etree.QName(cellml.NS_RDF, 'resource')] = \
                cellml.NS_OXMETA + quote(annotation)

    def _units(self, parent, units):
        """
        Adds a ``units`` element to ``parent``, for the given cellml units
        object.
        """
        # Get unit exponents on first call
        if self._exp_si is None:
            from myokit.formats.cellml import v1
            self._exp_si = [
                v1.Units._si_units_r[x] for x in myokit.Unit.list_exponents()]

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
        by :class:`myokit.formats.cellml.v1.Variable` ``variable``.
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
            value = myokit.float.str(variable.initial_value()).strip()
            if value[-4:] == 'e+00':
                value = value[:-4]
            element.attrib['initial_value'] = value

        # Add cmeta id
        cid = variable.cmeta_id()
        if cid is not None:
            element.attrib[etree.QName(cellml.NS_CMETA, 'id')] = cid

            # Add oxmeta annotation, if found
            try:
                self._oxmeta_variables[cid] = variable.meta['oxmeta']
            except KeyError:
                pass

    def write(self, model):
        """
        Takes a :class:`myokit.formats.cellml.v1.Model` as input, and creates
        an ElementTree that represents it.

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

            # Temporarily store free variable (in valid models, this is always
            # set if states are used).
            self._time = None
            self._time = model.free_variable()

            # Create model element (with children)
            element = self._model(model)

            # Wrap in ElementTree and return
            return etree.ElementTree(element)

        finally:
            # Delete any temporary properties
            del self._oxmeta_variables, self._time

    def write_file(self, path, model):
        """
        Takes a :class:`myokit.formats.cellml.v1.Model` as input, and writes it
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
        Takes a :class:`myokit.formats.cellml.v1.Model` as input, and converts
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

