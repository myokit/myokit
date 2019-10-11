#
# Provides MathML support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._parser import parse_mathml, parse_mathml_rhs, MathMLError  # noqa
from ._exporter import XMLExporter, HTMLExporter
from ._ewriter import MathMLExpressionWriter


# Importers
# Exporters
_exporters = {
    'xml': XMLExporter,
    'html': HTMLExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
_ewriters = {
    'mathml': MathMLExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)

# Language keywords
# None!
