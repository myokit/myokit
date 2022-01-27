#
# CellML expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from lxml import etree

import myokit
import myokit.formats.cellml

from myokit.formats.mathml import MathMLExpressionWriter


class CellMLExpressionWriter(MathMLExpressionWriter):
    """
    Writes equations for variables using CellML's version of MathML.

    To use, create an expression writer, then pass in a method to set good
    variable names with :meth:`set_lhs_function()`, and a method to look up
    unit names with :meth:`set_unit_function()`.
    """
    def __init__(self, version='1.0'):
        super(CellMLExpressionWriter, self).__init__()
        super(CellMLExpressionWriter, self).set_mode(presentation=False)

        # Units lookup method
        self._funits = None

        # Use unames by default
        self._flhs = lambda x: x.var().uname()

        # Get namespace based on version
        if version == '1.0':
            self._ns = myokit.formats.cellml.NS_CELLML_1_0
        elif version == '1.1':
            self._ns = myokit.formats.cellml.NS_CELLML_1_1
        elif version == '2.0':
            self._ns = myokit.formats.cellml.NS_CELLML_2_0
        else:
            raise ValueError('Unknown CellML version: ' + str(version))

        # Namespaces for element creation
        self._nsmap['cellml'] = self._ns

    def set_unit_function(self, f):
        """
        Sets a unit lookup function, which will be used to convert a
        :class:`myokit.Unit` to a CellML units name.
        """
        self._funits = f

    def _ex_number(self, e, t):
        x = super(CellMLExpressionWriter, self)._ex_number(e, t)
        unit = e.unit()
        if self._funits is not None and unit is not None:
            units = self._funits(e.unit())
        else:
            units = 'dimensionless'
        x.attrib[etree.QName(self._ns, 'units')] = units

    def _ex_quotient(self, e, t):
        # CellML 1.0 subset doesn't contain quotient
        # Note that this _must_ round towards minus infinity!
        # See myokit.Quotient !
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])), t)

    def _ex_remainder(self, e, t):
        # CellML 1.0 subset doesn't contain remainder
        # Note that this _must_ use the same round-to-neg-inf convention as
        # myokit.Quotient! Implementation below is consistent with Python
        # convention:
        return self.ex(myokit.Minus(
            e[0], myokit.Multiply(e[1], myokit.Quotient(e[0], e[1]))), t)

    def set_mode(self, presentation=False):
        """
        This expression writer only supports content MathML.
        """
        if presentation:
            raise RuntimeError(
                'Presentation MathML is not supported in CellML.')

