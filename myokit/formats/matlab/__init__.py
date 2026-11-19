#
# Provides Matlab/Octave support
#
# This file is part of Myokit.
# See https://github.com/myokit/myokit for copyright, sharing, and licensing.
#
from ._ewriter import MatlabExpressionWriter
from ._exporter import MatlabExporter

# Importers
# Exporters
_exporters = {
    'matlab': MatlabExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
_ewriters = {
    'matlab': MatlabExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)


# Language keywords
keywords = [
    'i',
    'e',
    'pi'
]
