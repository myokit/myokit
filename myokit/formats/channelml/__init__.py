#
# Provides support for the ChannelML format
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._importer import ChannelMLImporter, ChannelMLError  # noqa


# Importers
_importers = {
    'channelml': ChannelMLImporter,
}


def importers():
    """
    Returns a dict of all importers available in this module.
    """
    return dict(_importers)

# Exporters
# Expression writers
