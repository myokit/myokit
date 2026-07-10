#
# Provides C++ support geared towards FPGA implementations
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from ..ansic import keywords as keywords_c
from ._exporter import FPGAExporter


# Importers

# Exporters
_exporters = {
    'fpga': FPGAExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers

# Reserved keywords
keywords = keywords_c + [
]
