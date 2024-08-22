#
# Export as a DiffSL model.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import collections
import os
import warnings

import myokit
import myokit.formats
import myokit.lib.guess as guess
import myokit.lib.hh as hh
import myokit.lib.markov as markov

import myokit.formats.diffsl as diffsl


class DiffSLExporter(myokit.formats.Exporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a DiffSL
    implementation of a Myokit model.

    Only the model definition is exported. All currents and state variables 
    are output, but no inputs are provided.

    For details of the language, see https://martinjrobins.github.io/diffsl/

    """

    def model(self, path, model, protocol=None, convert_units=True):
        """
        Exports a :class:`myokit.Model` in DiffSL format, writing the result to
        the file indicated by ``path``.

        A :class:`myokit.ExportError` will be raised if any errors occur.

        Arguments:

        ``path``
            The path to write the generated model to.
        ``model``
            The :class:`myokit.Model` to export.
        ``protocol``
            Not implemented!
        ``convert_units``
            Not implemented!

        """
        # Check model validity
        try:
            model.validate()
        except myokit.MyokitError:
            raise myokit.ExportError('DiffSL export requires a valid model.')

        # Rewrite model so that any Markov models have a 1-sum(...) state
        # This also clones the model, so that changes can be made
        model = markov.convert_markov_models_to_compact_form(model)

        # Remove all model bindings apart from time and pace
        _ = myokit._prepare_bindings(model, {
            'time': 't',
            'pace': 'pace',
        })

        # Replace state derivatives on rhs with intermediary variables
        # e.g. set `dxdt` = rhs of `dot(x)`; then where `dot(x)` is found in
        # all other rhs's, replace it with `dxdt`; also, set `dot(x) = dxdt`.
        model.remove_derivative_references()

        # Remove hardcoded stimulus protocol, if any
        guess.remove_embedded_protocol(model)

        # Get / try to guess model variables
        time = model.time()  # engine.time
        pace = model.binding('pace')  # engine.pace
        v_m = guess.membrane_potential(model)  # Vm
        c_m = guess.membrane_capacitance(model)  # Cm
        i_diff = model.binding('diffusion_current')  # Idiff
        i_ion = model.label('cellular_current')  # Iion
        membrane_currents = guess.membrane_currents(model)  # [Iion,...]

        # Variables to remove or exclude from output
        vars_to_remove = {pace, i_diff, i_ion}
        vars_to_exclude = {v_m, time}

        # Remove potentials from membrane currents, if present
        i = 0
        while i < len(membrane_currents):
            if membrane_currents[i].unit() in [
                myokit.parse_unit('mV'),
                myokit.parse_unit('V'),
            ]:
                membrane_currents.pop(i)
            else:
                i += 1

        # Ensure Vm is a state, so that expressions
        # depending on it are not seen as constants.
        if not v_m.is_state():
            v_m.promote(-80)  # Make into a state var with initial value -80

        # Unit conversion
        def convert(var, unit, helpers=None):
            if var.unit() is None:
                return
            try:
                var.convert_unit(unit, helpers=helpers)
            except myokit.IncompatibleUnitError:
                warnings.warn(
                    'Unable to convert ' + var.qname() + ' to recommended'
                    ' units of ' + str(unit) + '.'
                )

        # Convert to recommended units
        time_factor = time_factor_inv = None
        if convert_units:
            # Convert membrane currents to A/F
            recommended_current_units = [
                myokit.parse_unit('pA/pF'),
                myokit.parse_unit('uA/cm^2'),
            ]

            helpers = [] if c_m is None else [c_m.rhs()]

            for current in membrane_currents:
                if current.unit() not in recommended_current_units:
                    convert(current, 'A/F', helpers=helpers)

            # Convert membrane potential to mV
            convert(v_m, myokit.units.mV)

            # Get conversion factor for time
            # Multiplying by time_factor = Going from time_units to ms
            time_unit = time.unit()
            if time_unit is not None and time_unit != myokit.units.ms:
                try:
                    time_factor = myokit.Number(
                        myokit.Unit.conversion_factor(
                            time_unit, myokit.units.ms
                        )
                    )
                    time_factor_inv = myokit.Number(
                        1 / time_factor.eval(), 1 / time_factor.unit()
                    )
                except myokit.IncompatibleUnitError:
                    warnings.warn(
                        "Unable to convert time units "
                        + str(time_unit)
                        + " to recommended units of ms."
                    )

        # Remove unwanted variables e.g. pacing, diffusion current, i_ion
        vars_to_remove.discard(None)
        for var in vars_to_remove:
            # Replace references to these variables with 0
            refs = list(var.refs_by())
            subst = {var.lhs(): myokit.Number(0)}
            for ref in refs:
                ref.set_rhs(ref.rhs().clone(subst=subst))

            # Remove variable
            var.parent().remove_variable(var)

            # Remove from currents, if present
            if var in membrane_currents:
                membrane_currents.remove(var)

        # Prepare to remove unused variables
        # Set Vm to the sum of currents so that all currents count as used
        rhs = myokit.Number(0)
        for v in membrane_currents:
            rhs = myokit.Plus(rhs, v.lhs())
        v_m.set_rhs(rhs)

        # Remove all labels so that they register as unused
        for _, var in model.labels():
            var.set_label(None)

        # Remove all unused variables
        model.validate(remove_unused_variables=True)

        # Find special Hodgkin-Huxley variables
        hh_states = set()
        alphas = dict()
        betas = dict()
        taus = dict()
        infs = dict()

        # If an inf/tau/alpha/beta is used by more than one state, we create a
        # copy for each user, so that we can give the variables the appropriate
        # name (e.g. x_inf, y_inf, z_inf) etc.
        def renamable(var):
            srefs = [v for v in var.refs_by() if v.is_state()]
            if len(srefs) > 1:
                v = var.parent().add_variable_allow_renaming(var.name())
                v.set_rhs(myokit.Name(var))
                v.set_unit(var.unit())
                return v
            return var

        # Find HH state variables and their infs, taus, alphas, betas
        for var in model.states():
            inf_tau = hh.get_inf_and_tau(var, v_m)
            if inf_tau is not None:
                vars_to_exclude.add(var)
                hh_states.add(var)
                infs[renamable(inf_tau[0])] = var
                taus[renamable(inf_tau[1])] = var
                continue

            alpha_beta = hh.get_alpha_and_beta(var, v_m)
            if alpha_beta is not None:
                vars_to_exclude.add(var)
                hh_states.add(var)
                alphas[renamable(alpha_beta[0])] = var
                betas[renamable(alpha_beta[1])] = var
                continue

        hh_variables = (set(alphas.keys())
                        | set(betas.keys())
                        | set(taus.keys())
                        | set(infs.keys()))

        # Find Markov models (must be run before time conversion)
        markov_models = markov.find_markov_models(model)

        # Add time conversion factor for states and HH variables
        if time_factor is not None:
            for var in model.states():
                var.set_rhs(myokit.Multiply(var.rhs(), time_factor_inv))
            for var in alphas:
                var.set_rhs(myokit.Multiply(var.rhs(), time_factor_inv))
            for var in betas:
                var.set_rhs(myokit.Multiply(var.rhs(), time_factor_inv))
            for var in taus:
                var.set_rhs(myokit.Multiply(var.rhs(), time_factor))

        # Create variable names
        # The following strategy is followed:
        #  - HH variables are named after their state
        #  - All other variables are checked for special names, and changed if
        #    necessary
        #  - Any conflicts are resolved in a final step

        sep = 'Z'

        # Detect names with special meanings
        def special_start(name):
            prefixes = ['dudt', 'F', 'G', 'in', 'out', 'u']
            for prefix in prefixes:
                if name.startswith(prefix + '_'):
                    return True
                if name.startswith(prefix + '.'):
                    return True
            return False

        def special_end(name):
            suffixes = ['alpha', 'beta', 'tau', 'inf']
            for suffix in suffixes:
                if name.endswith('_' + suffix):
                    return True
                if name.endswith('.' + suffix):
                    return True
            return False

        # Create initial variable names
        var_to_name = collections.OrderedDict()
        for var in model.variables(deep=True, sort=True):

            # Delay naming of HH variables until their state has a name
            if var in hh_variables:
                continue

            # Start from simple variable name
            name = var.name()

            # Add parents
            parent = var.parent()
            while parent:
                name = parent.name() + sep + name
                if isinstance(parent, myokit.Component):
                    break
                parent = parent.parent()

            # Avoid names with special meaning
            if special_start(name):
                name = 'var' + sep + name

            if special_end(name):
                name = name + sep + 'Var'

            # Replace unsupported characters
            name = name.replace('.', sep).replace('_', sep)

            # Store (initial) name for var
            var_to_name[var] = name

        # Check for conflicts with known keywords
        from . import keywords
        reserved = [
            'Iion',
        ]
        needs_renaming = collections.OrderedDict()
        for keyword in keywords:
            needs_renaming[keyword] = []
        for keyword in reserved:
            needs_renaming[keyword] = []

        # Find naming conflicts, create inverse mapping
        name_to_var = collections.OrderedDict()
        for var, name in var_to_name.items():

            # Known conflict?
            if name in needs_renaming.keys():
                needs_renaming[name].append(var)
                continue

            # Test for new conflicts
            var2 = name_to_var.get(name, None)
            if var2 is not None:
                needs_renaming[name] = [var2, var]
                continue

            name_to_var[name] = var

        # Resolve naming conflicts
        for name, variables in needs_renaming.items():
            # Add a number to the end of the name, increasing it until it's
            # unique
            i = 1
            root = name + sep
            for var in variables:
                name = f'{root}{sep}{i}'
                while name in name_to_var:
                    i += 1
                    name = f'{root}{sep}{i}'
                var_to_name[var] = name
                name_to_var[name] = var

        # Remove reverse mappings
        del name_to_var, needs_renaming

        # Create names for HH variables
        for var, state in alphas.items():
            var_to_name[var] = var_to_name[state] + sep + 'alpha'
        for var, state in betas.items():
            var_to_name[var] = var_to_name[state] + sep + 'beta'
        for var, state in taus.items():
            var_to_name[var] = var_to_name[state] + sep + 'tau'
        for var, state in infs.items():
            var_to_name[var] = var_to_name[state] + sep + 'inf'

        # Create naming function
        def lhs(e):
            if isinstance(e, myokit.Derivative):
                return 'd' + var_to_name[e.var()] + 'dt'
            elif isinstance(e, myokit.LhsExpression):
                return var_to_name[e.var()]
            elif isinstance(e, myokit.Variable):
                return var_to_name[e]
            raise ValueError(   # pragma: no cover
                'Not a variable or LhsExpression: ' + str(e))

        # Create expression writer
        e = diffsl.DiffSLExpressionWriter()
        e.set_lhs_function(lhs)

        # Test if can write in dir (raises exception if can't)
        self._test_writable_dir(os.path.dirname(path))

        # Create diffsl string to write to file
        export_str = ''

        # Add metadata
        export_str += '/*\n'
        export_str += 'This file was generated by Myokit.\n'
        if model.meta:
            export_str += '\n'
            for key, val in sorted(model.meta.items()):
                export_str += key + ': ' + val + '\n'
            export_str += '\n'
        export_str += '*/\n\n'

        # Add empty parameter list
        export_str += f'in = [ ]\n\n'

        # Add constants
        constants = list(model.variables(const=True, sort=True))
        if constants:
            export_str += '/* Constants */\n'
            for v in constants:
                export_str += lhs(v) + ' { ' + e.ex(v.eq().rhs) + ' }\n'
            export_str += '\n'

        # Add initial conditions
        export_str += 'u_i {\n'
        for v in model.states():
            initial_value = myokit.float.str(v.initial_value(True))
            export_str += f'  {lhs(v)} = {initial_value},\n'
        export_str += '}\n\n'

        # Add remaining variables
        # TODO: sort variables in order of dependence
        for c in model.components(sort=True):
            todo = c.variables(deep=True, sort=True)
            todo = [v for v in todo if v not in vars_to_exclude]
            if todo:
                export_str += '/* ' + c.name() + ' */\n'
                for v in todo:
                    if isinstance(v, myokit.Derivative):
                        export_str += 'DERIVATIVE'
                    export_str += lhs(v) + ' { ' + e.ex(v.eq().rhs) + ' } '
                    export_str += '/* ' + v.name() + ' */\n'
                export_str += '\n'

        # Add initial conditions
        export_str += 'dudt_i {\n'
        for v in model.states():
            initial_value = myokit.float.str(v.initial_value(True))
            export_str += f'  {lhs(v)} = {initial_value},\n'
        export_str += '}\n\n'

        # Add sum of currents variable
        export_str += '/* Sum of currents */\n'
        export_str += 'Iion { ' + \
            ' + '.join([lhs(v) for v in membrane_currents]) + ' }\n\n'

        # Add solution methods for Markov models
        markov_states = set()
        for states in markov_models:
            export_str += '/* Markov model */\n'
            export_str += '{\n'
            for state in states:
                if state.is_state():
                    export_str += '  ' + lhs(state) + '\n'
                    markov_states.add(state)
            export_str += '}\n\n'

        # Solve all non-Markovian and non-HH variables with CVODE
        cvode_states = [
            x for x in model.states() if not (
                x == v_m or x in markov_states or x in hh_states)]
        if cvode_states:
            export_str += '/* Solve non-HH and non-Markov states with CVODE */\n'
            export_str += 'F_i {\n'
            for v in cvode_states:
                export_str += '  ' + lhs(v) + '\n'
            export_str += '}\n\n'

            export_str += 'G_i {\n'
            for v in cvode_states:
                export_str += '  ' + lhs(v) + ' { ' + e.ex(v.eq().rhs) + ' }\n'
            export_str += '}\n\n'

        # Output all currents and state variables
        export_str += '/* Output all currents and state variables */\n'
        export_str += 'out_i {\n'
        for vlhs in sorted(lhs(v) for v in set(membrane_currents).union(model.states())):
            export_str += f'  {vlhs}\n'
        export_str += '}\n'

        # Write model to file
        with open(path, 'w') as f:
            f.write(export_str)

    def supports_model(self):
        """ See :meth:`myokit.formats.Exporter.supports_model()`. """
        return True
