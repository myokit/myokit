#
# Exports to Ansi-C using OpenCL for parallelization
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os

import myokit.formats


class OpenCLExporter(myokit.formats.TemplatedRunnableExporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` creates a cable simulation
    that can run on any OpenCL environment (GPU or CPU).

    A value must be bound to ``diffusion_current`` which represents the current
    flowing from cell to cell. This is defined as positive when the cell is
    acting as a source, negative when it acts like a sink. In other words, it
    is defined as an outward current.

    The membrane potential must be labelled as ``membrane_potential``.

    By default, the simulation is set to log all state variables. This is nice
    to explore results with, but quite slow...

    Please keep in mind that CellML and other downloaded formats are typically
    not directly suitable for GPU simulation. Specifically, when simulating
    on single-precision devices a lot of divide-by-zero errors might crop up
    that remain hidden when using double precision single cell simulations on
    the CPU.
    """
    _use_rl = False

    def _dir(self, root):
        return os.path.join(root, 'opencl', 'template')

    def _dict(self):
        return {
            'cable.c': 'cable.c',
            'kernel.cl': 'kernel.cl',
            'plot.py': 'plot.py',
            'minilog.py': 'minilog.py',
            'test.sh': 'test.sh',
        }

    def _vars(self, model, protocol):
        from myokit.formats.opencl import keywords

        # Check if model has binding to diffusion_current
        if model.binding('diffusion_current') is None:
            raise ValueError('No variable bound to `diffusion_current`.')

        # Check if model has label membrane_potential
        if model.label('membrane_potential') is None:
            raise ValueError('No variable labelled `membrane_potential`.')

        # Clone model, and adapt to inf-tau form if in RL mode
        rl_states = {}
        if self._use_rl:
            # Convert model to inf-tau form (returns clone) and get vm
            import myokit.lib.hh as hh
            model = hh.convert_hh_states_to_inf_tau_form(model)
            vm = model.label('membrane_potential')

            # Get (inf, tau) tuple for every Rush-Larsen state
            for state in model.states():
                res = hh.get_inf_and_tau(state, vm)
                if res is not None:
                    rl_states[state] = res

        else:
            model = model.clone()

        # Merge interdependent components
        model.resolve_interdependent_components()

        # Process bindings, remove unsupported bindings, get map of bound
        # variables to internal names.
        bound_variables = myokit._prepare_bindings(model, {
            'time': 'time',
            'pace': 'pace',
            'diffusion_current': 'idiff',
        })

        # Reserve keywords
        model.reserve_unique_names(*keywords)
        model.reserve_unique_names(
            *['calc_' + c.name() for c in model.components()])
        model.reserve_unique_names(
            'cid',
            'dt',
            'g',
            'idiff',
            'idiff_vec'
            'n_cells',
            'offset',
            'pace',
            'pace_vec',
            'state',
            'time',
        )
        model.create_unique_names()

        # Return variables
        return {
            'model': model,
            'precision': myokit.SINGLE_PRECISION,
            'native_math': True,
            'bound_variables': bound_variables,
            'rl_states': rl_states,
        }


class OpenCLRLExporter(OpenCLExporter):
    """
    Like :class:`OpenCLExporter` but uses a Rush-Larsen update step where
    applicable.
    """
    _use_rl = True

