#
# Provides CellML support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._exporter import CellMLExporter, CellML1Exporter, CellML2Exporter
from ._ewriter import CellMLExpressionWriter
from ._importer import CellMLImporter, CellMLImporterError  # noqa


# Namespaces
NS_BQBIOL = 'http://biomodels.net/biology-qualifiers/'
NS_CELLML_1_0 = 'http://www.cellml.org/cellml/1.0#'
NS_CELLML_1_1 = 'http://www.cellml.org/cellml/1.1#'
NS_CELLML_2_0 = 'http://www.cellml.org/cellml/2.0#'
NS_CMETA = 'http://www.cellml.org/metadata/1.0#'
NS_MATHML = 'http://www.w3.org/1998/Math/MathML'
NS_OXMETA = 'https://chaste.comlab.ox.ac.uk/cellml/ns/oxford-metadata#'
NS_RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
NS_TMP_DOC = 'http://cellml.org/tmp-documentation'


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
    'cellml1': CellML1Exporter,
    'cellml2': CellML2Exporter,
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

