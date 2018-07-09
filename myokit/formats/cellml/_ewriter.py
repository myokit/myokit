#
# CellML expression writer
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
from myokit.formats.mathml import MathMLExpressionWriter


class CellMLExpressionWriter(MathMLExpressionWriter):
    """
    Writes equations for variables using CellML's version of MathML.

    Differences from normal MathML:

     1. Only content MathML is supported
     2. Variable names are always written as unames.
     3. Every number defines an attribute cellml:units

    The expression writer requires a single argument ``units``. This should be
    a mapping of Myokit units to string unit names.
    """
    def __init__(self, units=None):
        super(CellMLExpressionWriter, self).__init__()
        super(CellMLExpressionWriter, self).set_mode(presentation=False)
        self._units = {} if units is None else units

    def _ex_number(self, e, t):
        x = self._et.SubElement(t, 'cn')
        x.text = self._fnum(e)
        u = e.unit()
        x.attrib['cellml:units'] = self._units[u] if u else 'dimensionless'

    def _ex_name(self, e, t):
        x = self._et.SubElement(t, 'ci')
        x.text = e.var().uname()

    def _ex_quotient(self, e, t):
        # Note that this _must_ round towards minus infinity!
        # See myokit.Quotient !
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])), t)

    def _ex_remainder(self, e, t):
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

    def set_lhs_function(self, f):
        """
        This expression writer always uses unames, setting an LHS function is
        not supported.
        """
        raise NotImplementedError
