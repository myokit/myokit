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
        # Test if can write in dir (raises exception if can't)
        self._test_writable_dir(os.path.dirname(path))

        # Check model validity
        try:
            model.validate()
        except myokit.MyokitError:
            raise myokit.ExportError('DiffSL export requires a valid model.')

        model = model.clone()

        # Remove all model bindings apart from time and pace
        _ = myokit._prepare_bindings(model, {
            'time': 't',
            'pace': 'pace',
        })

        # Prepare to replace all state derivatives on the rhs with intermediary
        # variables. First, add a temporary rhs reference for all state
        # derivatives that do not already have an rhs reference or an
        # intermediary variable.
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

        # Replace state derivatives on rhs with intermediary variables
        # e.g. set `dxdt` = rhs of `dot(x)`; then where `dot(x)` is found in
        # all other rhs's, replace it with `dxdt`; also, set `dot(x) = dxdt`.
        model.remove_derivative_references()

        # Reset temporary rhs references
        for var in tmp_vars:
            var.set_rhs(0)

        # Remove hardcoded stimulus protocol, if any
        guess.remove_embedded_protocol(model)

        # Get / try to guess some model variables
        time = model.time()  # engine.time
        pace = model.binding('pace')  # engine.pace
        i_diff = model.binding('diffusion_current')
        v_m = guess.membrane_potential(model)  # Vm
        c_m = guess.membrane_capacitance(model)  # Cm

        # Guess membrane currents, excluding potentials if present
        membrane_currents = {
            x
            for x in guess.membrane_currents(model)
            if x.unit()
            not in [
                myokit.parse_unit('mV'),
                myokit.parse_unit('V'),
            ]
        }  # {Iion,...}

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
                        'Unable to convert time units '
                        + str(time_unit)
                        + ' to recommended units of ms.'
                    )

        # Remove unwanted variables e.g. pacing, diffusion current
        vars_to_remove = {pace, i_diff}
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
            membrane_currents.discard(var)

        # Prepare to remove unused vars - sum currents so they're all 'used'
        curr_sum_var = v_m.parent().add_variable_allow_renaming(
            'tmp_DiffSL_SuM_oF_cUrReNtS_Myokit'
        )
        rhs = myokit.Number(0)
        for v in sorted(membrane_currents, key=lambda x: x.qname()):
            rhs = myokit.Plus(rhs, v.lhs())
        curr_sum_var.set_rhs(rhs)

        # Remove all labels so that they register as unused
        for _, var in model.labels():
            var.set_label(None)

        # Remove all unused variables
        model.validate(remove_unused_variables=True)

        # Create variable names
        # The following strategy is followed:
        #  - Variables are named after their state
        #  - Variables are checked for special names, and changed if necessary
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

        needs_renaming = collections.OrderedDict()
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

        # Sort equations in solvable order (grouped by component)
        sorted_eqs = model.solvable_order()

        # Variables to be excluded from output or handled separately
        handled_vars = (
            {time}
            | set([v.rhs().var() for v in model.states()])
            | set([v.lhs().var() for v in model.states()])
        )

        # Lines to export to file
        file_lines = []
        tab = '  '

        # Add metadata
        file_lines.append('/*')
        file_lines.append('This file was generated by Myokit.')
        if model.meta:
            file_lines.append('')
            for key, val in sorted(model.meta.items()):
                file_lines.append(key + ': ' + val)
            file_lines.append('')
        file_lines.append('*/')
        file_lines.append('')

        # Add empty input parameter list
        file_lines.append('/* Input parameters */')
        file_lines.append('in = [ ]')
        file_lines.append('')

        # Add constants
        constants = set(model.variables(deep=True, const=True)) - handled_vars
        for label, eq_list in sorted_eqs.items():
            const_eqs = [
                eq for eq in eq_list.equations() if eq.lhs.var() in constants
            ]
            if const_eqs:
                file_lines.append(f'/* Constants: {label} */')
                for eq in const_eqs:
                    v = eq.lhs.var()
                    rhs = e.ex(eq.rhs)
                    unit = '' if v.unit() is None else f' {v.unit()}'
                    file_lines.append(
                        lhs(v) + ' { ' + rhs + ' } ' +
                        f'/* {v.name()}{unit} */'
                    )
                file_lines.append('')

        # Add initial conditions `u_i`
        file_lines.append('/* Initial conditions */')
        file_lines.append('u_i {')
        for v in model.states():
            initial_value = myokit.float.str(v.initial_value(True))
            unit = '' if v.unit() is None else f' {v.unit()}'
            file_lines.append(
                f'{tab}{lhs(v)} = {initial_value}, /* {v.name()}{unit} */'
            )
        file_lines.append('}')
        file_lines.append('')

        # Add initial conditions `dudt_i`
        file_lines.append('dudt_i {')
        for v in model.states():
            initial_value = myokit.float.str(v.initial_value(True))
            file_lines.append(
                f'{tab}{lhs(v.rhs())} = {initial_value},'
            )
        file_lines.append('}')
        file_lines.append('')

        # Add remaining variables
        todo = set(model.variables(deep=True, const=False)) - handled_vars
        for label, eq_list in sorted_eqs.items():
            todo_eqs = [
                eq for eq in eq_list.equations() if eq.lhs.var() in todo
            ]
            if todo_eqs:
                file_lines.append(f'/* Variables: {label} */')
                for eq in todo_eqs:
                    v = eq.lhs.var()
                    rhs = e.ex(eq.rhs)
                    unit = '' if v.unit() is None else f' {v.unit()}'
                    file_lines.append(
                        lhs(v) + ' { ' + rhs + ' } ' +
                        f'/* {v.name()}{unit} */'
                    )
                file_lines.append('')

        # Solve
        file_lines.append('F_i {')
        for v in model.states():
            file_lines.append(f'{tab}{lhs(v.rhs())},')
        file_lines.append('}')
        file_lines.append('')

        file_lines.append('G_i {')
        for v in model.states():
            file_lines.append(f'{tab}{e.ex(v.eq().rhs.rhs())},')
        file_lines.append('}')
        file_lines.append('')

        # Output all currents and state variables
        file_lines.append('/* Output all currents and state variables */')
        file_lines.append('out_i {')
        out_vars = sorted(membrane_currents.union(model.states()), key=lambda x: x.qname())
        for v in out_vars:
            file_lines.append(f'{tab}{lhs(v)},')
        file_lines.append('}')
        file_lines.append('')

        # Write model to file
        file_str = '\n'.join(file_lines)
        with open(path, 'w') as f:
            f.write(file_str)

    def supports_model(self):
        """ See :meth:`myokit.formats.Exporter.supports_model()`. """
        return True
