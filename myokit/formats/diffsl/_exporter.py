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
import myokit.formats.diffsl as diffsl
import myokit.lib.guess as guess
import myokit.lib.hh as hh
import myokit.lib.markov as markov


class DiffSLExporter(myokit.formats.Exporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a DiffSL
    implementation of a Myokit model.

    Only the model definition is exported. All state variables and currents
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
            If set to ``True``, the method will attempt to convert to
            preferred units for voltage (mV), current (A/F), and time (ms).
        """
        # Raise exception if path is unwritable
        self._test_writable_dir(os.path.dirname(path))

        # Check model validity
        try:
            model.validate()
        except myokit.MyokitError as e:
            raise myokit.ExportError(
                'DiffSL export requires a valid model.'
            ) from e

        # Prepare model for export
        model, currents = self._prep_model(model, convert_units)

        # Generate DiffSL model
        diffsl_model = self._generate_diffsl(
            model,
            extra_out_vars=currents,
        )

        # Write DiffSL model to file
        with open(path, 'w') as f:
            f.write(diffsl_model)

    def _prep_model(self, model, convert_units):
        """
        Prepare the model for export to DiffSL.
        """
        # Rewrite model so that any Markov models have a 1-sum(...) state
        # This also clones the model, so that changes can be made
        model = markov.convert_markov_models_to_compact_form(model)

        # Remove all model bindings apart from time and pace
        _ = myokit._prepare_bindings(
            model,
            {
                'time': 't',
                'pace': 'pace',
            },
        )

        # Remove hardcoded stimulus protocol, if any
        guess.remove_embedded_protocol(model)

        # Get / try to guess some model variables
        time = model.time()  # engine.time
        vm = self._guess_membrane_potential(model)  # Vm
        cm = guess.membrane_capacitance(model)  # Cm
        currents = self._guess_currents(model)

        time_factor = time_factor_inv = None
        if convert_units:
            # Convert currents to A/F
            helpers = [] if cm is None else [cm.rhs()]
            for var in currents:
                self._convert_current_unit(var, helpers=helpers)

            # Convert potentials to mV
            self._convert_potential_unit(vm)

            time_factor, time_factor_inv = self._get_time_factor(time)

        # Find HH state variables and their alphas, betas, and taus
        alphas = set()
        betas = set()
        taus = set()

        for var in model.states():
            inf_tau = hh.get_inf_and_tau(var, vm)
            if inf_tau is not None:
                taus.add(inf_tau[1])
                continue

            alpha_beta = hh.get_alpha_and_beta(var, vm)
            if alpha_beta is not None:
                alphas.add(alpha_beta[0])
                betas.add(alpha_beta[1])
                continue

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

        # Add intermediary variables on rhs of state derivatives
        self._prep_derivatives(model)

        return model, currents

    def _generate_diffsl(self, model, extra_out_vars=None):
        """
        Generate a DiffSL model from a prepped Myokit model.
        DiffSL outputs will be set to state variables and extra_out_vars
        """

        # Create DiffSL-compatible variable names
        var_to_name = self._create_diffsl_variable_names(model)

        # Create a naming function
        def var_name(e):
            if isinstance(e, myokit.LhsExpression):
                return var_to_name[e.var()]
            elif isinstance(e, myokit.Variable):
                return var_to_name[e]
            raise ValueError(  # pragma: no cover
                'Not a variable or LhsExpression: ' + str(e)
            )

        # Create an expression writer
        e = diffsl.DiffSLExpressionWriter()
        e.set_lhs_function(var_name)

        export_lines = []  # DiffSL export lines
        tab = '  '  # Tab character

        # Sort equations in solvable order (grouped by component)
        sorted_eqs = model.solvable_order()

        # Variables to be excluded from output or handled separately.
        # Derivatives and their intermediary variables (i.e. dot(x) and dot_x)
        # are handled in dudt_i, F_i and G_i; time is excluded from the output;
        # pace is made Vc.
        time = model.time()
        pace = model.binding('pace')
        special_vars = set(
            [time]
            + [v.rhs().var() for v in model.states()]
            + [v.lhs().var() for v in model.states()]
        )
        if pace is not None:
            special_vars.add(pace)

        # Add metadata
        export_lines.append('/*')
        export_lines.append('This file was generated by Myokit.')
        if model.meta:
            export_lines.append('')
            for key, val in sorted(model.meta.items()):
                export_lines.append(f'{key}: {val}')
            export_lines.append('')
        export_lines.append('*/')
        export_lines.append('')

        # Add empty input parameter list
        export_lines.append('/* Input parameters */')
        export_lines.append('in = [ ]')
        export_lines.append('')

        # Add placeholder protocol
        if pace is not None:
            export_lines.append('/* Voltage protocol [mV] */')
            export_lines.append(
                'Vc { -80 + 120 * heaviside(t-500) - 80 * heaviside(t-1000) }'
            )
            export_lines.append('')

        # Add constants
        const_vars = (
            set(model.variables(const=True, deep=True, state=False))
            - special_vars
        )
        for component_label, eq_list in sorted_eqs.items():
            const_eqs = [
                eq for eq in eq_list.equations() if eq.lhs.var() in const_vars
            ]
            if const_eqs:
                export_lines.append(f'/* Constants: {component_label} */')
                for eq in const_eqs:
                    v = eq.lhs.var()
                    lhs = var_name(v)
                    rhs = e.ex(eq.rhs)
                    qname = v.qname()
                    unit = '' if v.unit() is None else f' {v.unit()}'
                    export_lines.append(
                        f'{lhs} {{ {rhs} }} /* {qname}{unit} */'
                    )
                export_lines.append('')

        # Add initial conditions `u_i`
        export_lines.append('/* Initial conditions */')
        export_lines.append('u_i {')
        for v in model.states():
            lhs = var_name(v)
            rhs = myokit.float.str(v.initial_value(as_float=True))
            qname = v.qname()
            unit = '' if v.unit() is None else f' {v.unit()}'
            export_lines.append(f'{tab}{lhs} = {rhs}, /* {qname}{unit} */')
        export_lines.append('}')
        export_lines.append('')

        # Add initial conditions `dudt_i`
        export_lines.append('dudt_i {')
        for v in model.states():
            lhs = var_name(v.rhs())  # Use intermediary dot_x instead of dot(x)
            rhs = myokit.float.str(v.initial_value(as_float=True))
            export_lines.append(f'{tab}{lhs} = {rhs},')
        export_lines.append('}')
        export_lines.append('')

        # Add remaining variables
        todo_vars = (
            set(model.variables(const=False, deep=True, state=False))
            - special_vars
        )
        for component_label, eq_list in sorted_eqs.items():
            todo_eqs = [
                eq for eq in eq_list.equations() if eq.lhs.var() in todo_vars
            ]
            if todo_eqs:
                export_lines.append(f'/* Variables: {component_label} */')
                for eq in todo_eqs:
                    v = eq.lhs.var()
                    lhs = var_name(v)
                    rhs = e.ex(eq.rhs)
                    qname = v.qname()
                    unit = '' if v.unit() is None else f' {v.unit()}'
                    export_lines.append(
                        f'{lhs} {{ {rhs} }} /* {qname}{unit} */'
                    )
                export_lines.append('')

        # Add `F_i`
        export_lines.append('/* Solve */')
        export_lines.append('F_i {')
        for v in model.states():
            lhs = var_name(v.rhs())  # Use intermediary dot_x instead of dot(x)
            export_lines.append(f'{tab}{lhs},')
        export_lines.append('}')
        export_lines.append('')

        # Add `G_i`
        export_lines.append('G_i {')
        for v in model.states():
            rhs = e.ex(v.rhs().rhs())  # Use rhs of intermediary dot_x
            export_lines.append(f'{tab}{rhs},')
        export_lines.append('}')
        export_lines.append('')

        # Output state variables + extra output variables
        export_lines.append('/* Output */')
        export_lines.append('out_i {')
        vars = set(model.states())
        if extra_out_vars:
            vars = vars.union(extra_out_vars)
        for v in sorted(vars, key=lambda x: x.qname()):
            lhs = var_name(v)
            export_lines.append(f'{tab}{lhs},')
        export_lines.append('}')
        export_lines.append('')

        return '\n'.join(export_lines)

    def _convert_current_unit(self, var, helpers=None):
        """
        Convert a current to A/F if its present unit isn't recommended.
        """
        recommended_units = [
            myokit.parse_unit('pA/pF'),
            myokit.parse_unit('uA/cm^2'),
        ]

        if var.unit() not in recommended_units:
            self._convert_unit(var, 'A/F', helpers=helpers)

    def _convert_potential_unit(self, var, helpers=None):
        """
        Convert a potential to mV if its present unit isn't recommended.
        """
        recommended_units = [myokit.units.mV]

        if var.unit() not in recommended_units:
            self._convert_unit(var, 'mV', helpers=helpers)

    def _convert_unit(self, var, unit, helpers=None):
        """
        Convert a variable to the given unit if possible. Throws a warning if
        the conversion is not possible.
        """
        if var.unit() is None:
            return

        try:
            var.convert_unit(unit, helpers=helpers)
        except myokit.IncompatibleUnitError:
            warnings.warn(
                'Unable to convert ' + var.qname() + ' to recommended'
                ' units of ' + str(unit) + '.'
            )

    def _create_diffsl_variable_names(self, model):
        """
        Create diffsl-compatible names for all variables in the model.

        The following strategy is followed:
         - Fully qualified names are used for all variables.
         - Variables are checked for special names, and changed if necessary.
         - Unsupported characters like '.' and '_' are replaced.
         - Any conflicts are resolved in a final step by appending a number.
        """

        # Detect names with special meanings
        def special_start(name):
            prefixes = ['dudt', 'F', 'G', 'in', 'M', 'out', 'u']
            for prefix in prefixes:
                if name.startswith(prefix + '_'):
                    return True
            return False

        # Replacement characters for underscores and periods
        uscore = 'Z'
        period = 'Z'

        # Create initial variable names
        var_to_name = collections.OrderedDict()
        for var in model.variables(deep=True, sort=True):
            # Start from fully qualified name
            name = var.qname()

            # Avoid names with special meaning
            if special_start(name):
                name = 'var' + uscore + name

            # Replace unsupported characters
            name = name.replace('.', period).replace('_', uscore)

            # Store (initial) name for var
            var_to_name[var] = name

        # Check for conflicts with known keywords
        from . import keywords

        needs_renaming = collections.OrderedDict()

        pace = model.binding('pace')  # Reserve 'Vc' for pace variable
        if pace is not None:
            needs_renaming['Vc'] = []

        for keyword in keywords:
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
            root = name
            for var in variables:
                name = f'{root}{uscore}{i}'
                while name in name_to_var:
                    i += 1
                    name = f'{root}{uscore}{i}'
                var_to_name[var] = name
                name_to_var[name] = var

        if pace is not None:
            var_to_name[pace] = 'Vc'

        return var_to_name

    def _get_time_factor(self, time_var):
        """
        Get factor to convert time to ms.
        time_units * time_factor means going from time_units to ms.
        """
        time_unit = time_var.unit()

        if time_unit is None:
            return None, None

        if time_unit == myokit.units.ms:
            return None, None

        time_factor = time_factor_inv = None

        try:
            time_factor = myokit.Number(
                myokit.Unit.conversion_factor(time_unit, myokit.units.ms)
            )
            time_factor_inv = myokit.Number(
                1 / time_factor.eval(), 1 / time_factor.unit()
            )
        except myokit.IncompatibleUnitError:
            warnings.warn(
                'Unable to convert time units '
                + str(time_unit)
                + ' to recommended units of ms.'
            )

        return time_factor, time_factor_inv

    def _guess_currents(self, model):
        """
        Tries to make a list of membrane currents. Removes potentials
        from the guessed list.
        """
        unmatch_units = [
            myokit.units.mV,
            myokit.units.V,
        ]
        guessed_currents = guess.membrane_currents(model)
        return [x for x in guessed_currents if x.unit() not in unmatch_units]

    def _guess_membrane_potential(self, model):
        """
        Tries to find the membrane potential. If it's not a state, converts it
        to one so that expressions depending on it are not seen as constants.
        """
        vm = guess.membrane_potential(model)
        if not vm.is_state():
            vm.promote(-80)
        return vm

    def _prep_derivatives(self, model):
        """
        Prepares the model for export by adding intermediary variables for
        all state derivatives.

        Before:
            dot(x) = (12 - x) / 5
            y = 1 + dot(x)

        After:
            dxdt =  (12 - x) / 5  # dxdt is the intermediary variable
            dot(x) = dxdt
            y = 1 + dxdt
        """
        # If a derivative doesn't have any rhs references, add a temporary
        # one. Skip derivatives that already have an intermediary variable.
        tmp_vars = []
        for state in model.states():
            if isinstance(state.rhs(), myokit.Name):
                continue  # Derivative already has an intermediary variable

            if list(state.refs_by()):
                continue  # Derivative already has at least one rhs reference

            # Add a temporary rhs reference
            var = state.parent().add_variable_allow_renaming(
                'tmp_DiffSL_' + state.name() + '_Myokit'
            )
            var.set_rhs(state.lhs())
            tmp_vars.append(var)

        # Add intermediary variables for state derivatives with rhs refs
        model.remove_derivative_references()

        # Remove temporary variables
        for var in tmp_vars:
            self._remove_variable(var)

    def _remove_variable(self, var):
        """
        Remove variable from its model.
        """
        if var is None:
            return

        # Replace references to this variable with 0
        refs = list(var.refs_by())
        subst = {var.lhs(): myokit.Number(0)}
        for ref in refs:
            ref.set_rhs(ref.rhs().clone(subst=subst))

        # Remove variable
        var.parent().remove_variable(var)

    def supports_model(self):
        """See :meth:`myokit.formats.Exporter.supports_model()`."""
        return True
