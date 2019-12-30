#
# Provides MathML support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._exporter import XMLExporter, HTMLExporter
from ._ewriter import MathMLExpressionWriter
from ._parser import (   # noqa
    MathMLError,
    MathMLParser,
    parse_mathml_dom,
    parse_mathml_etree,
    parse_mathml_string,
)

# Namespaces
NS_MATHML_2 = 'http://www.w3.org/1998/Math/MathML'

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
