#
# Provides latex export
#
# This file is part of Myokit.
# See https://github.com/myokit/myokit for copyright, sharing, and licensing.
#
from ._ewriter import LatexExpressionWriter
from ._exporter import LatexArticleExporter, LatexPosterExporter

_exporters = {
    'latex-article': LatexArticleExporter,
    'latex-poster': LatexPosterExporter,
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
