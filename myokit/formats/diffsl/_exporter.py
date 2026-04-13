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

    For details of the DiffSL language, see
    https://martinjrobins.github.io/diffsl/
    """

    def model(self, path, model, protocol=None, convert_units=True,
              inputs=None, outputs=None, final_time=None):
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
            An optional :class:`myokit.Protocol` that defines a pacing or
            dosing schedule.  When given, the exporter generates a hybrid ODE
            model using DiffSL's ``N``, ``stop``, and ``reset`` constructs.
            All events are expanded to one-off transitions; periodic events
            require ``final_time`` to be set.
        ``convert_units``
            If set to ``True`` (default), the method will attempt to convert to
            preferred units for voltage (mV), current (A/F), and time (ms).
        ``inputs``
            Optional list of model variables to include in the input parameter
            list (in = [ ... ]). If ``None`` (default), an empty input list
            will be generated. All input variables must be constants.
        ``outputs``
            Optional list of model variables to include in the output list
            (out_i { ... }). If ``None`` (default), all state variables will
            be included in alphabetical order. All output variables must be
            time-varying (not constants).
        ``final_time``
            Required when ``protocol`` is provided. Events are expanded up to
            (but not including) this time. Must be a finite positive number.
            Ignored when ``protocol`` is ``None``.
        """
        # Validate protocol / final_time combination
        if protocol is not None:
            import math
            if final_time is None:
                raise myokit.ExportError(
                    'A final_time must be provided when exporting with a '
                    'protocol so events can be expanded to a finite list of '
                    'transitions.'
                )
            if final_time is not None:
                final_time = float(final_time)
                if not math.isfinite(final_time) or final_time <= 0:
                    raise myokit.ExportError(
                        'final_time must be a finite positive number.'
                    )

        # Check model validity
        try:
            model.validate()
        except myokit.MyokitError as e:
            raise myokit.ExportError(
                'DiffSL export requires a valid model.'
            ) from e

        # Store qualified names of inputs/outputs before model prep
        # and validate that they are appropriate for DiffSL export
        if inputs is None:
            input_qnames = None  # Will use empty input list
        else:
            input_qnames = []
            for v in inputs:
                # Validate that the variable belongs to this model
                if v.model() != model:
                    raise myokit.ExportError(
                        f'Input variable {v.qname()} does not belong to the '
                        f'model being exported.'
                    )
                # Validate that inputs are constants (pace binding is allowed)
                if not v.is_constant() and v.binding() != 'pace':
                    raise myokit.ExportError(
                        f'Input variable {v.qname()} must be a constant.'
                    )
                input_qnames.append(v.qname())

        if outputs is None:
            output_qnames = None  # Will use all states
        else:
            output_qnames = []
            for v in outputs:
                # Validate that the variable belongs to this model
                if v.model() != model:
                    raise myokit.ExportError(
                        f'Output variable {v.qname()} does not belong to the '
                        f'model being exported.'
                    )
                # Validate that outputs are not constants
                if v.is_constant():
                    raise myokit.ExportError(
                        f'Output variable {v.qname()} must be time-varying. '
                        f'Constant variables cannot be used as outputs.'
                    )
                output_qnames.append(v.qname())

        # Prepare model for export (this clones the model)
        model = self._prep_model(model, convert_units)

        # Create DiffSL-compatible variable names and store for introspection
        self._var_to_name = self._create_diffsl_variable_names(model)

        # Store the state order (as qnames) for introspection
        # This preserves the order from model.states()
        self._state_qnames = [v.qname() for v in model.states()]

        # Map inputs/outputs to the prepped model
        if input_qnames is None:
            # Default to empty input list
            inputs = []
        else:
            inputs = [model.get(qname) for qname in input_qnames]

        if output_qnames is None:
            # Use all states, sorted alphabetically by DiffSL name
            outputs = sorted(
                model.states(), key=lambda x: self._var_name(x).swapcase()
            )
        else:
            outputs = [model.get(qname) for qname in output_qnames]

        # Expand protocol to hybrid phase boundaries (if supplied)
        phases = None
        if protocol is not None:
            phases = self._expand_protocol(protocol, final_time)

        # Generate DiffSL model
        diffsl_model = self._generate_diffsl(model, inputs, outputs, phases)

        # Write DiffSL model to file
        with open(path, 'w') as f:
            f.write(diffsl_model)

    def _expand_protocol(self, protocol, final_time):
        """
        Expand a :class:`myokit.Protocol` directly into hybrid phase
        boundaries ``(t_boundary, level_after)``.

        Expansion is performed by stepping a :class:`myokit.PacingSystem`
        through its event boundaries until the expansion horizon is reached.

        Returns a list of ``(t_boundary, level_after)`` tuples in ascending
        order of ``t_boundary``.

        If pacing is already non-zero at ``t = 0``, a boundary ``(0.0, level)``
        is included. If pacing remains non-zero at ``final_time``, a terminal
        boundary ``(final_time, 0.0)`` is appended.
        """
        horizon = float(final_time)

        pacing = myokit.PacingSystem(protocol)
        current_level = pacing.pace()
        phases = []

        # Immediate transition at t=0 if pace starts non-zero.
        if current_level != 0:
            phases.append((0.0, current_level))

        # Step through all pacing boundaries up to the horizon.
        while True:
            t_next = pacing.next_time()
            if t_next >= horizon:
                break
            old_level = current_level
            current_level = pacing.advance(t_next)
            if current_level != old_level:
                phases.append((t_next, current_level))

        # Ensure return to baseline at final_time if pace remains active.
        if current_level != 0:
            phases.append((horizon, 0.0))

        return phases

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

        if convert_units:
            # Convert currents to A/F
            helpers = [] if cm is None else [cm.rhs()]
            for var in currents:
                self._convert_current_unit(var, helpers=helpers)

            # Convert potentials to mV
            if vm is not None:
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

    def _var_name(self, e):
        """
        Get the DiffSL-compatible name for a variable or expression.

        Arguments:

        ``e``
            A :class:`myokit.Variable`, :class:`myokit.Derivative`, or
            :class:`myokit.LhsExpression`.
        """
        if isinstance(e, myokit.LhsExpression):
            return self._var_to_name[e.var()]
        elif isinstance(e, myokit.Variable):
            return self._var_to_name[e]
        raise ValueError(  # pragma: no cover
            'Not a variable or LhsExpression: ' + str(e)
        )

    def _generate_diffsl(self, model, inputs, outputs, phases=None):
        """
        Generate a DiffSL model from a prepped Myokit model.

        Arguments:

        ``model``
            The prepared Myokit model.
        ``inputs``
            List of model variables to include in the input parameter list.
        ``outputs``
            List of model variables to include in the output list.
        ``phases``
            Optional list of ``(t_boundary, level_after)`` tuples produced by
            :meth:`_expand_protocol`. When provided, hybrid
            ``pace_i``/``stop`` blocks are appended and the model
            is expected to reference ``pace_i[N]`` for the current pace level.
        """

        # Create an expression writer
        e = diffsl.DiffSLExpressionWriter()
        e.set_lhs_function(self._var_name)

        export_lines = []  # DiffSL export lines
        tab = '  '  # Tab character

        # Sort equations in solvable order (grouped by component)
        sorted_eqs = model.solvable_order()

        # Variables to be excluded from output or handled separately.
        # State derivatives are handled in F_i; time is excluded from the
        # output; pace is handled separately; inputs are in the in block.
        time = model.time()
        pace = model.binding('pace')
        special_vars = set(v for v in model.states())
        special_vars.add(time)
        if pace is not None:
            special_vars.add(pace)
        # Add inputs to special_vars so they're excluded from constants
        for v in inputs:
            special_vars.add(v)

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

        # Add input parameter block
        export_lines.append('/* Input parameters */')
        if inputs:
            export_lines.append('in_i {')
            for v in inputs:
                lhs = self._var_name(v)
                rhs = e.ex(v.rhs())
                qname = v.qname()
                unit = '' if v.unit() is None else f' {v.unit()}'
                export_lines.append(f'{tab}{lhs} = {rhs}, /* {qname}{unit} */')
            export_lines.append('}')
        else:
            export_lines.append('in_i { }')
        export_lines.append('')

        # Add pace (skipped if pace is provided as an explicit input)
        if pace is not None and pace not in inputs:
            export_lines.append('/* Engine: pace */')
            export_lines.append('/* E.g.')
            export_lines.append('  -80 * (1 - sigmoid((t-100)*5000))')
            export_lines.append(
                '  -120 * (sigmoid((t-100)*5000) - sigmoid((t-200)*5000))'
            )
            export_lines.append('*/')

            lhs = self._var_name(pace)
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
                    lhs = self._var_name(v)
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
            lhs = self._var_name(v)
            rhs = v.initial_value()
            qname = v.qname()
            unit = '' if v.unit() is None else f' {v.unit()}'
            export_lines.append(f'{tab}{lhs} = {rhs}, /* {qname}{unit} */')
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
                    lhs = self._var_name(v)
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
            rhs = e.ex(v.rhs())
            export_lines.append(f'{tab}{rhs},')
        export_lines.append('}')
        export_lines.append('')

        # Output variables
        export_lines.append('/* Output */')
        export_lines.append('out_i {')
        for v in outputs:
            lhs = self._var_name(v)
            export_lines.append(f'{tab}{lhs},')
        export_lines.append('}')
        export_lines.append('')

        # --- Hybrid protocol blocks (emitted when a protocol is supplied) ---
        if phases is not None:
            # phases: [(t_boundary, level_after), ...] sorted by t_boundary.
            #
            # DiffSL hybrid convention used here:
            #   N = 0           before the first boundary
            #   N = k (k >= 1) after boundary index k-1 fires
            #
            # pace_i[N] gives the pace level active in phase N.
            # Phase 0 starts at t=0 (pace = 0, before any event).
            # Phase k (k >= 1) is entered when stop element k-1 crosses zero.

            # Collect pace levels: phase 0 is baseline (0.0), then one per
            # boundary transition.
            pace_levels = [0.0] + [lev for _, lev in phases]

            # Emit pace level vector indexed by N
            export_lines.append('/* Protocol: pace level per model index N */')
            export_lines.append('pace_i {')
            for lev in pace_levels:
                export_lines.append(f'{tab}{lev},')
            export_lines.append('}')
            export_lines.append('')

            # Emit stop conditions: stop[k] = t - t_{k+1}
            # When element k crosses zero the solver stops and N is set to k.
            export_lines.append(
                '/* Protocol: stop conditions (stop[k] = t - t_{k+1}) */'
            )
            export_lines.append('stop_i {')
            for t_boundary, _ in phases:
                export_lines.append(f'{tab}t - {t_boundary},')
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

        time = model.time()
        var_to_name[time] = 't'  # DiffSL built-in time variable

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

    def get_state_index(self, variable):
        """
        Returns the index of a state variable in the DiffSL state vector.

        This method can be called after :meth:`model()` to determine the
        position of a state variable in the exported DiffSL state vector.

        Arguments:

        ``variable``
            A :class:`myokit.Variable` from the model that was exported.

        Returns the zero-based index of the variable in the state vector if it
        is a state variable, or ``None`` if it is not a state variable.

        Note: The state vector order in DiffSL follows the order returned by
        :meth:`myokit.Model.states()` from the exported model.
        """
        if not hasattr(self, '_state_qnames'):
            raise RuntimeError(
                'get_state_index() can only be called after model() has been '
                'called to export a model.'
            )

        # Find the index using the variable's qualified name
        try:
            return self._state_qnames.index(variable.qname())
        except ValueError:
            return None

    def supports_model(self):
        """See :meth:`myokit.formats.Exporter.supports_model()`."""
        return True
