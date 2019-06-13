#
# Provides EasyML (CARP/CARPentry) support
#
# This file is part of Myokit
#  Copyright 2011-2019 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._exporter import EasyMLExporter
from ._ewriter import EasyMLExpressionWriter


# Importers

# Exporters
_exporters = {
    'easyml': EasyMLExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
_ewriters = {
    'easyml': EasyMLExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)


#
# Special variable names
#
special_names = [
    # Differential equations
    'diff_[\w]*',
    'd_[\w]*_dt',
    # Initial value
    '[\w]*_init',
    # Opening rates
    'alpha_[\w]*',
    'a_[\w]*',
    # Closing rates
    'beta_[\w]*',
    'b_[\w]*',
    # Tau and inf
    'tau_[\w]*',
    '[\w]*_inf',
]

#
# Language keywords: Not sure if these are all keywords
#
keywords = [
    'acos',
    'asin',
    'atan',
    'ceil',
    'cos',
    'fabs',
    'floor',
    'pow',
    'sin',
    'tan',
]
