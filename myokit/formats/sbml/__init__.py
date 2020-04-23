#
# Provides SBML support
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._importer import SBMLError
from ._importer import SBMLImporter as OldImporter  # noqa
from. _new_importer import SBMLImporter as NewImporter


# Importers
_importers = {
    'sbml': NewImporter,
    'sbmlOld': OldImporter,
}


def importers():
    """
    Returns a dict of all importers available in this module.
    """
    return dict(_importers)

# Exporters
# Expression writers
