#
# Provides C++ support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit.formats.ansic
from ._ewriter import CppExpressionWriter


# Importers
# Exporters
# Expression writers
_ewriters = {
    'cpp': CppExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)


# Language keywords
keywords = list(myokit.formats.ansic.keywords)
# TODO Append more keywords
