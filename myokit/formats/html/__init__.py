#
# Provides HTML support.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._exporter import HTMLExporter
from ._flatten import html2ascii    # noqa


# Importers
# Exporters
_exporters = {
    'html': HTMLExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
# Language keywords
# None!
