#
# Provides CellML support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._importer import CellMLImporter, CellMLError  # noqa
from ._exporter import CellMLExporter
from ._ewriter import CellMLExpressionWriter

import re


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


# Valid CellML identifiers
# Official docs allow silly things, e.g. 1e2 or 123 or _123
# re.compile('^_*[a-zA-Z0-9][a-zA-Z0-9_]*$')
# So let's be more strict:
#  - At least one letter
#  - Can't start with a number
_cellml_identifier = re.compile('^([_][0-9_]*)?[a-zA-Z][a-zA-Z0-9_]*$')
# Future versions will have:
#   - Must start with at least one letter


def is_valid_identifier(name):
    """
    Tests if the given ``name`` is a valid CellML 1 identifier.
    """
    return _cellml_identifier.match(name) is not None


# Don't expose imported modules
del(re)
