#
# Exports to Ansi C, using the CVODE libraries for integration
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import re

import myokit.formats
import myokit.lib.guess as guess
import myokit.lib.hh as hh

from ._ewriter import FPGAExpressionWriter


_valid_name = re.compile('^[a-zA-Z_]+[a-zA-Z0-9_]*$')


class FPGAExporter(myokit.formats.TemplatedRunnableExporter):
    """
    This:class:`Exporter <myokit.formats.Exporter>` generates runnable C code
    in a format suitable for specific FPGA applications.

    The generated code is in C99 format, with all equations in a single
    function call, in single precision and using either a Rush-Larsen or an
    Euler update (depending on the state variable equation).

    The following inputs are provided:

    ``time``
        The current simulation time
    ``pace``
        The current value of the pacing system, implemented using a simple
        pacing mechanism.

    """
    def _dir(self, root):
        return os.path.join(root, 'fpga', 'template')

    def _dict(self):
        return {
            'model.hpp': 'model.hpp',
            'model.cpp': 'model.cpp',
            'model_main.cpp': 'model_main.cpp',
            'compile': 'compile.sh',
            'plot': 'plot.py',
        }

    def post_export_info(self):
        return '\n'.join((
            'To compile in gcc, use::',
            '',
            '    gcc -Wall -lm model_main.cpp model.cpp -o run',
            '',
            'Example plot script::',
            '',
            '    with open(\'result.golden.dat\', \'r\') as f:',
            '        v = [float(x) for x in f.readlines()]',
            '    fig = plt.figure()',
            '    ax = fig.add_subplot()',
            '    ax.plot(v)',
            '    plt.show()',
        ))

    def runnable(
            self, path, model, protocol=None, parameters=None, name=None,
            precision = myokit.SINGLE_PRECISION):
        """
        Exports a:class:`myokit.Model` and optional protocol (a single
        indefinitely recurring event) to compilable code.

        Arguments:

        ``path``
            A string representing the **directory** to store the output in.
        ``model``
            A Myokit model to export
        ``protocol``
            Not implemented!
        ``parameters``
            A list of variables or variable names, specifying the model
            constants to retain as changeable parameters.
        ``name``
            A short name to use for the main files and main callable function.

        """
        # Note: This overwrite just exists to make the new parameters explicit
        # and provide documentation
        super().runnable(path, model, protocol, parameters, name)

    def _vars(self, model, protocol, parameters, name):
        import myokit.formats.fpga as fpga

        # Check model
        model.validate(remove_unused_variables=True)

        # Check protocol
        event = None
        sim_duration = 1000
        sim_step = 0.05
        if protocol is not None:
            if not isinstance(protocol, myokit.Protocol):
                raise ValueError('Protocol must be a myokit.Protocol or None.')
            if len(protocol) > 1:
                raise ValueError(
                    'Only protocols with a single event are supported.')
            event = protocol.events()[0]
            if event.multiplier() != 0:
                raise ValueError(
                    'Only protocols with a single, indefinitely recurring,'
                    ' event are supported.')

            sim_duration = event.period()
            sim_step = sim_step * (sim_duration / 1000)

        # Check parameter list (do rest later, when new model is created)
        if parameters is None:
            parameters = []

        # Check name
        if name is None:
            name = model.name()
            if not _valid_name.match(name):
                raise ValueError(
                    'No name given and model name is not a valid C function'
                    f' name: {name}')
        else:
            if not _valid_name.match(name):
                raise ValueError(
                    f'Not a valid C function name: {name}')

        # Process bound variables
        bound_variables = myokit._prepare_bindings(model, {
            'time': 'time',
            'pace': 'pace',
        })

        # Adapt to inf-tau form for Rush-Larsen
        vm = myokit.lib.guess.membrane_potential(model)
        model = hh.convert_hh_states_to_inf_tau_form(
            model, vm, state_name_in_var_name=True)

        # Convert parameter names etc to variables in the new model object
        parameters = [model.get(str(x)) for x in parameters]
        for p in parameters:
            if not p.is_literal():
                raise ValueError(
                    'Only literals (right-hand side expression is a'
                    ' number) can be parameters.')

        # Reserve unique names
        model.reserve_unique_names(*fpga.keywords)
        model.reserve_unique_names(
            # Only bound variable names and variables (not functions) used in
            # the main functions need to be added here.
            'time',
            'pace',
            'dt',
            name,
        )
        model.create_unique_names()

        # Get (inf, tau) tuple for every Rush-Larsen state
        rl_states = {}
        for state in model.states():
            res = hh.get_inf_and_tau(state, vm)
            if res is not None:
                rl_states[state] = res

        # Solvable order
        equations = model.solvable_order()

        # Main function signature
        sig = ['float pace', 'float dt']
        sig += [f'float {v.uname()}' for v in parameters]
        sig += [f'float Y_{v.index()}' for v in model.states()]
        sig += [f'float* SV_{v.index()}' for v in model.states()]
        sig = ', '.join(sig)
        sig = f'int {name.lower()}({sig})'

        call = ['pace', 'dt']
        call += [f'{v.uname()}' for v in parameters]
        call += [f'Y_{v.index()}' for v in model.states()]
        call += [f'&SV_{v.index()}' for v in model.states()]
        call = ', '.join(call)
        call = f'{name.lower()}({call})'

        # Variable naming function
        def v(var):
            if isinstance(var, myokit.Derivative):
                return f'dY_{var.var().index()}'
            if isinstance(var, myokit.Name):
                var = var.var()
            if var.is_state():
                return f'Y_{var.index()}'
            if var.is_bound():
                return 'time' if var.binding() == ' time' else 'pace'
            return var.uname()

        # Expression writer
        e = FPGAExpressionWriter()
        e.set_lhs_function(v)

        # Return variables
        return {
            'v': v,
            'e': e,
            'name': name,
            'model': model,
            'equations': equations,
            #'bound_variables': bound_variables,
            'rl_states': rl_states,
            'parameters': parameters,
            'vm': vm,
            'signature': sig,
            'call': call,
            'event': event,
            'sim_duration': sim_duration,
            'sim_step': sim_step,
        }
