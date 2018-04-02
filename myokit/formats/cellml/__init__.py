#
# Provides CellML support
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._importer import CellMLImporter, CellMLError  # noqa
from ._exporter import CellMLExporter
from ._ewriter import CellMLExpressionWriter


# Importers
_importers = {
    'cellml': CellMLImporter,
}


def importers():
    """
    Returns a dict of all importers available in this module.
    """
    return dict(_importers)


# Exporters
_exporters = {
    'cellml': CellMLExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
_ewriters = {
    'cellml': CellMLExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)

# Language keywords
