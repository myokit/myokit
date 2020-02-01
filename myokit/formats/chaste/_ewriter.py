#
# Chaste expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from myokit.formats.cpp import CppExpressionWriter


class ChasteExpressionWriter(CppExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    myokit :class:`expressions <myokit.Expression>` to their C++/Chaste
    equivalent.
    """
    pass
