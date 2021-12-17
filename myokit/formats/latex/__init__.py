#
# Provides latex export
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._exporter import PdfExporter, PosterExporter
from ._ewriter import LatexExpressionWriter

_exporters = {
    'latex-article': PdfExporter,
    'latex-poster': PosterExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers

_ewriters = {
    'latex': LatexExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)


#
# Language keywords
#
# None!
