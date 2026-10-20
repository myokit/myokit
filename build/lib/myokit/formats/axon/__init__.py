#
# Provides support for working with data in formats used by Axon Instruments.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from ._abf import AbfFile, Sweep, Channel  # noqa
from ._atf import AtfFile, load_atf, save_atf  # noqa
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
