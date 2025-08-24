#
# Provides Neuron MOD file support
#
# This file is part of Myokit
#  Copyright 2011-2014 Michael Clerx, Maastricht University
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
# Importers
from _importer import MODImporter
_importers = {
    'mod' : MODImporter,
    }
def importers():
    """
    Returns a list of all importers available in this module.
    """
    return dict(_importers)
# Exporters
#
# Expression writers
#
