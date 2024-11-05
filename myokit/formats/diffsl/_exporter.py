#
# Export as a DiffSL model.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import collections
import warnings

import myokit
import myokit.formats
import myokit.formats.diffsl as diffsl
import myokit.lib.guess as guess
import myokit.lib.markov as markov


class DiffSLExporter(myokit.formats.Exporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a DiffSL
    implementation of a Myokit model.

    Only the model definition is exported. No inputs are provided, there is
    no protocol defined, and only state variables are output.

    For details of the language, see https://martinjrobins.github.io/diffsl/
    """

    def model(self, path, model, protocol=None, convert_units=True):
        """
        Exports a :class:`myokit.Model` in DiffSL format, writing the result to
        the file indicated by ``path``.

        A :class:`myokit.ExportError` will be raised if any errors occur.
        Warnings will be generated if unsupported functions (e.g. atan) are
        used in the model. For a full list, see
        :class:`myokit.formats.diffsl.DiffSLExpressionWriter
        <DiffSLExpressionWriter>`.

        Arguments:

        ``path``
            The path to write the generated model to.
        ``model``
            The :class:`myokit.Model` to export.
        ``protocol``
            Not implemented!
        ``convert_units``
            If set to ``True`` (default), the method will attempt to convert to
            preferred units for voltage (mV), current (A/F), and time (ms).
        """
        # Raise exception if protocol is set
        if protocol is not None:
            raise ValueError(
                'DiffSL export does not support an input protocol.'
            )

        # Check model validity
        try:
            model.validate()
        except myokit.MyokitError as e:
            raise myokit.ExportError(
                'DiffSL export requires a valid model.'
            ) from e

        # Prepare model for export
        model = self._prep_model(model, convert_units)

        # Generate DiffSL model
        diffsl_model = self._generate_diffsl(model)

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
        vm = guess.membrane_potential(model)  # Vm
        cm = guess.membrane_capacitance(model)  # Cm
        currents = self._guess_currents(model)

        # Check for explicit time dependence
        time_refs = list(time.refs_by())
        if time_refs:
            raise myokit.ExportError(
                'DiffSL export does not support explicit time dependence:\n'
                + '\n'.join([f'{v} = {v.rhs()}' for v in time_refs])
            )

        if convert_units:
            # Convert currents to A/F
            helpers = [] if cm is None else [cm.rhs()]
            for var in currents:
                self._convert_current_unit(var, helpers=helpers)

            # Convert potentials to mV
            self._convert_potential_unit(vm)

            # Convert time to ms
            if time.unit() != myokit.units.ms:
                self._convert_unit(time, 'ms')

        # Add intermediary variables for state derivatives with rhs references
        # Before:
        #   dot(x) = x / 5
        #   y = 1 + dot(x)
        # After:
        #   dot_x =  x / 5
        #   dot(x) = dot_x
        #   y = 1 + dot_x
        model.remove_derivative_references()

        return model

    def _generate_diffsl(self, model):
        """
        Generate a DiffSL model from a prepped Myokit model.
        DiffSL inputs will be left empty, and outputs will be set to
        state variables in alphabetical order.
        """

        # Create DiffSL-compatible variable names
        var_to_name = self._create_diffsl_variable_names(model)

        # Create a naming function
        def var_name(e):
            if isinstance(e, myokit.Derivative):
                return var_to_name[e]
            elif isinstance(e, myokit.LhsExpression):
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
        # State derivatives are handled in dudt_i, F_i and G_i; time is
        # excluded from the output; pace is handled separately.
        time = model.time()
        pace = model.binding('pace')
        special_vars = set(v for v in model.states())
        special_vars.add(time)
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
        export_lines.append('/* E.g. in = [ varZero, varOne, varTwo ] */')
        export_lines.append('in = [ ]')
        export_lines.append('')

        # Add pace
        if pace is not None:
            export_lines.append('/* Engine: pace */')
            export_lines.append('/* E.g.')
            export_lines.append('  -80 * (1 - sigmoid((t-100)*5000))')
            export_lines.append(
                '  -120 * (sigmoid((t-100)*5000) - sigmoid((t-200)*5000))'
            )
            export_lines.append('*/')

            lhs = var_name(pace)
            rhs = e.ex(pace.rhs())
            qname = pace.qname()
            unit = '' if pace.unit() is None else f' {pace.unit()}'
            export_lines.append(f'{lhs} {{ {rhs} }} /* {qname}{unit} */')
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
            rhs = v.initial_value()
            qname = v.qname()
            unit = '' if v.unit() is None else f' {v.unit()}'
            export_lines.append(f'{tab}{lhs} = {rhs}, /* {qname}{unit} */')
        export_lines.append('}')
        export_lines.append('')

        # Add state derivatives `dudt_i`
        export_lines.append('dudt_i {')
        for v in model.states():
            lhs = var_name(v.lhs())
            export_lines.append(f'{tab}{lhs} = 0,')
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
            lhs = var_name(v.lhs())
            export_lines.append(f'{tab}{lhs},')
        export_lines.append('}')
        export_lines.append('')

        # Add `G_i`
        export_lines.append('G_i {')
        for v in model.states():
            rhs = e.ex(v.rhs())
            export_lines.append(f'{tab}{rhs},')
        export_lines.append('}')
        export_lines.append('')

        # Output state variables in alphabetical order
        export_lines.append('/* Output */')
        export_lines.append('out_i {')
        vars = list(model.states())
        for v in sorted(vars, key=lambda x: var_name(x).swapcase()):
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
        Create DiffSL-compatible names for all variables in the model.

        The following strategy is followed:
         - Fully qualified names are used for all variables.
         - Variables are checked for special names, and changed if necessary.
         - Unsupported characters like '.' and '_' are replaced.
         - Any conflicts are resolved in a final step by appending a number.
        """

        # Convert name to a DiffSL-compatible variable name
        def convert_name(name):
            # Remove unsupported chars like '_' and '.', and stagger case.
            # Preserves existing staggered case in names e.g.
            # voltage_clamp.R_seal_MOhm -> voltageClampRSealMOhm
            # voltageClamp.RSealMOhm -> voltageClampRSealMOhm
            name_chars = []
            caps_flag = False
            for ch in name:
                if ch.isalpha():
                    if caps_flag:
                        name_chars.append(ch.upper())
                        caps_flag = False
                    else:
                        name_chars.append(ch)
                elif ch.isdigit():
                    name_chars.append(ch)
                    caps_flag = True
                else:
                    caps_flag = True

            return ''.join(name_chars)

        var_to_name = collections.OrderedDict()

        # Store initial names for variables
        for var in model.variables(deep=True, sort=True):
            var_to_name[var] = convert_name(var.qname())
            if var.is_state():
                var_to_name[var.lhs()] = convert_name('diff_' + var.qname())

        # Check for conflicts with known keywords
        from . import keywords

        needs_renaming = collections.OrderedDict()
        for keyword in keywords:
            needs_renaming[keyword] = []

        # Find naming conflicts, create inverse mapping
        name_to_var = collections.OrderedDict()
        for var, name in var_to_name.items():

            # Known conflict?
            if name in needs_renaming:
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
            # Add a number to the end of the name, increasing until unique
            i = 1
            root = name
            for var in variables:
                name = f'{root}{i}'
                while name in name_to_var:
                    i += 1
                    name = f'{root}{i}'
                var_to_name[var] = name
                name_to_var[name] = var

        return var_to_name

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

    def supports_model(self):
        """See :meth:`myokit.formats.Exporter.supports_model()`."""
        return True
