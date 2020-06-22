#
# Exports to plain python
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os

import myokit.formats


class PythonExporter(myokit.formats.TemplatedRunnableExporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a python-only
    model implementation and a simple (but slow) integration routine.

    Both the model definition and the pacing protocol are fully exported.

    Provides the following external variables:

    ``time``
        The current simulation time
    ``pace``
        The current value of the pacing system, implemented using the given
        protocol.

    A graph of the results is generated using matplotlib.
    """

    def _dir(self, root):
        return os.path.join(root, 'python', 'template')

    def _dict(self):
        return {'sim.py': 'sim.py'}

    def _vars(self, model, protocol):
        return {'model': model, 'protocol': protocol}
