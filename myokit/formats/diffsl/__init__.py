#
# Provides DiffSL support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from ._ewriter import DiffSLExpressionWriter
from ._exporter import DiffSLExporter

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
    'dudt',
    'exp',
    'F',
    'G',
    'heaviside',
    'in',
    'log',
    'M',
    'out',
    'pow',
    'sigmoid',
    'sin',
    'sqrt',
    't',
    'tan',
    'u',
]
