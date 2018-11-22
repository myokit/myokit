#
# Provides an export to a CUDA kernel
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._exporter import CudaKernelExporter, CudaKernelRLExporter
from ._ewriter import CudaExpressionWriter
from myokit.formats import ansic


# Importers
# Exporters
_exporters = {
    'cuda-kernel': CudaKernelExporter,
    'cuda-kernel-rl': CudaKernelRLExporter,
}


def exporters():
    """
    Returns a list of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
_ewriters = {
    'cuda': CudaExpressionWriter,
}


def ewriters():
    """
    Returns a list of all expression writers available in this module.
    """
    return dict(_ewriters)


# Keywords
keywords = list(ansic.keywords)
# TODO: Append CUDA keywords
