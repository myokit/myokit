#
# Provides Python support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._exporter import PythonExporter
from ._ewriter import PythonExpressionWriter, NumPyExpressionWriter

# Importers
# Exporters

_exporters = {
    'python': PythonExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
_ewriters = {
    'python': PythonExpressionWriter,
    'numpy': NumPyExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)


# Language keywords
keywords = [
    'and',
    'del',
    'from',
    'not',
    'while',
    'as',
    'elif',
    'global',
    'or',
    'with', 'assert', 'else', 'if', 'pass', 'yield', 'break', 'except',
    'import', 'print', 'class', 'exec', 'in', 'raise', 'continue',
    'finally',
    'is',
    'return',
    'def',
    'for',
    'lambda',
    'try',
]
