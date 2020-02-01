#
# Exports to Chaste.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os

import myokit.formats


class ChasteExporter(myokit.formats.TemplatedRunnableExporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a model for use
    with Chaste.
    """
    def info(self):
        import inspect
        return inspect.getdoc(self)

    def _dir(self, root):
        return os.path.join(root, 'chaste', 'template')

    def _dict(self):
        return {
            'model.cpp': 'model.cpp',
            'model.hpp': 'model.hpp',
        }

    def _vars(self, model, protocol):
        return {'model': model, 'protocol': protocol}

