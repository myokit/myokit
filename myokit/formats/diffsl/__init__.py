#
# Provides DiffSL support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from ._exporter import DiffSLExporter
from ._ewriter import DiffSLExpressionWriter


# Importers

# Exporters
_exporters = {
    'diffsl': DiffSLExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
_ewriters = {
    'diffsl': DiffSLExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)


#
# Language keywords
#
keywords = [
    'abs',
    'cos',
    'exp',
    'heaviside',
    'log',
    'pow',
    'sigmoid',
    'sin',
    'sqrt',
    'tan',
    'F',
    'G',
    'u'
]
