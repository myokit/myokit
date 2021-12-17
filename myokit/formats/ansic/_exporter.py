#
# Exports to Ansi C, using the CVODE libraries for integration
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os

import myokit.formats


class AnsiCExporter(myokit.formats.TemplatedRunnableExporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a runnable ansic
    C model implementation and integrator. The integration is based on the
    Sundials CVODE library, which is required to run the program.

    Both the model definition and pacing protocol are exported and the file
    is set up ready to run a simulation. No post-processing is included.

    Provides the following external variables:

    ``time``
        The current simulation time
    ``pace``
        The current value of the pacing system, implemented using the given
        protocol.
    """
    def post_export_info(self):
        return '\n'.join((
            'To compile in gcc, use::',
            '',
            '    gcc -Wall -lm -lsundials_cvode sim.c -o sim',    # noqa
            '',
            'Example plot script::',
            '',
            '    import matplotlib.pyplot as plt',
            '    with open("v.txt", "r") as f:',
            '      T, V = [], []',
            '      for line in f:',
            '        t, v = [float(x) for x in line.split()]',
            '        T.append(t)',
            '        V.append(v)',
            '    plt.figure()',
            '    plt.plot(T, V)',
            '    plt.show()',
        ))

    def _dir(self, root):
        return os.path.join(root, 'ansic', 'template')

    def _dict(self):
        return {'sim.c': 'sim.c'}

    def _vars(self, model, protocol):
        return {'model': model, 'protocol': protocol}


class AnsiCEulerExporter(myokit.formats.TemplatedRunnableExporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates an ansic C
    implementation using a simple explicit forward-Euler scheme.

    Both the model definition and pacing protocol are exported and the file
    is set up ready to run a simulation. No post-processing is included.

    Provides the following external variables:

    ``time``
        The simulation time
    ``pace``
        The value of the pacing variable, implemented using the given protocol.

    No labeled variables are required.
    """
    def post_export_info(self):
        return '\n'.join((
            'To compile using gcc::',
            '',
            '    gcc -Wall -lm euler.c -o euler',
            '',
            'Example plot script:',
            '',
            '    import matplotlib.pyplot as plt',
            '    with open("v.txt", "r") as f:',
            '        T, V = [], []',
            '        for line in f:',
            '          t, v = [float(x) for x in line.split()]',
            '          T.append(t)',
            '          V.append(v)',
            '    plt.figure()',
            '    plt.plot(T, V)',
            '    plt.show()',
        ))

    def _dir(self, root):
        return os.path.join(root, 'ansic', 'template')

    def _dict(self):
        return {'euler.c': 'euler.c'}

    def _vars(self, model, protocol):
        return {'model': model, 'protocol': protocol}


class AnsiCCableExporter(myokit.formats.TemplatedRunnableExporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a 1d cable
    simulation using a simple forward-Euler scheme in ansi-C.

    Both the model definition and pacing protocol are exported and the file
    is set up ready to run a simulation. No post-processing is included.

    Provides the following external variables:

    ``time``
        The simulation time
    ``pace``
        The value of the pacing variable, implemented using the given protocol.
    ``diffusion_current``
        The current flowing from each cell to its neighbours. This will be
        positive if the cell is acting as a source, negative when it's acting
        as a sink.

    Requires the following labels to be set in the model:

    ``membrane_potential``
        The membrane potential.

    Variables are linked using ``diffusion_current``, this is calculated from
    the membrane potentials as:

        i = g * ((V - V_next) - (V_last - V))

    At the boundaries, V is substituted for V_last or V_next.
    """
    def post_export_info(self):
        return '\n'.join((
            'To compile using gcc::',
            '',
            '    gcc -Wall -lm cable.c -o cable',
            '',
            'Example plot script::',
            '',
            '    import myokit',
            '    import numpy as np',
            '    import matplotlib.pyplot as plt',
            '    from mpl_toolkits.mplot3d import axes3d',
            '    d = myokit.load_csv("data.txt")',
            '    n = 50 # Assuming 50 cells',
            '    f = plt.figure()',
            '    x = f.gca(projection="3d")',
            '    z = np.ones(len(d["time"]))',
            '    for i in range(0, n):',
            '        x.plot(d["time"], z*i, d.get(str(i) + "_V"))',
            '    plt.show()',
        ))

    def _dir(self, root):
        return os.path.join(root, 'ansic', 'template')

    def _dict(self):
        return {'cable.c': 'cable.c'}

    def _vars(self, model, protocol):
        return {'model': model, 'protocol': protocol}
