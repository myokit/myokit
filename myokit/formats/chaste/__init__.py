#
# Provides Chaste support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit.formats.cpp

from ._exporter import ChasteExporter
from ._ewriter import ChasteExpressionWriter


# Importers

# Exporters
_exporters = {
    'chaste': ChasteExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
_ewriters = {
    'chaste': ChasteExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)


# Language keywords
keywords = list(myokit.formats.cpp.keywords)
# TODO Append more keywords
