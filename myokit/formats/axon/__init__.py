#
# Provides support for working with data in formats used by Axon Instruments.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from ._abf import AbfFile, Channel, Sweep  # noqa: F401
from ._atf import AtfFile, load_atf, save_atf  # noqa: F401
from ._importer import AbfImporter

# Importers
_importers = {
    'abf': AbfImporter,
}


def importers():
    """
    Returns a dict of all importers available in this module.
    """
    return dict(_importers)
# Exporters
# Expression writers
