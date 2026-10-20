#
# Export as a DiffSL model.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import collections
import warnings
import math
from collections import abc

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

    def model(
        self,
        path,
        model,
        protocol=None,
        convert_units=True,
        inputs=None,
        outputs=None,
        final_time=None,
    ):
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
            An optional :class:`myokit.Protocol` or ``dict`` mapping binding
            names to :class:`myokit.Protocol` objects that define pacing or
            dosing schedules. If a map is not given then the binding name is
            assumed to be ``pace``. When given, the exporter generates a
            hybrid ODE model using DiffSL's ``N`` and ``stop`` constructs.
            All events are
            expanded to one-off transitions; periodic events require
            ``final_time`` to be set. Protocol entries whose binding names are
            not present in the model are ignored.
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
        # Check model validity
        try:
            model.validate()
        except myokit.MyokitError as e:
            raise myokit.ExportError(
                'DiffSL export requires a valid model.'
            ) from e

        # Normalize protocols to a binding -> Protocol mapping
        protocols = self._normalize_protocols(protocol, model)
        protocol_bindings = set(protocols.keys())

        # Validate protocol / final_time combination
        if protocols:
            if final_time is None:
                raise myokit.ExportError(
                    'A final_time must be provided when exporting with a '
                    'protocol so events can be expanded to a finite list of '
                    'transitions.'
                )
            else:
                final_time = float(final_time)
                if not math.isfinite(final_time) or final_time <= 0:
                    raise myokit.ExportError(
                        'final_time must be a finite positive number.'
                    )

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
                # Validate that inputs are constants (bound inputs are allowed)
                if (
                    not v.is_constant()
                    and v.binding() not in protocol_bindings
                ):
                    raise myokit.ExportError(
                        f'Input variable {v.qname()} must be a constant.'
                    )
                if v.binding() in protocol_bindings:
                    raise myokit.ExportError(
                        f'Input variable {v.qname()} cannot be both an input '
                        f'and be driven by protocol binding "{v.binding()}".'
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
        bindings_to_keep = list(protocols) if protocols else []
        model = self._prep_model(model, convert_units, bindings_to_keep)

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
                model.states(),
                key=lambda x: self._var_name(x).swapcase(),
            )
        else:
            outputs = [model.get(qname) for qname in output_qnames]

        # Collect preserved bound variables after model prep
        bound_variables = collections.OrderedDict(
            (label, model.binding(label))
            for label in bindings_to_keep
            if model.binding(label) is not None
        )

        # Expand protocol to hybrid phase boundaries (if supplied)
        protocol_data = None
        if protocols:
            protocol_data = self._expand_protocols(protocols, final_time)

        # Generate DiffSL model
        diffsl_model = self._generate_diffsl(
            model, inputs, outputs, bound_variables, protocol_data
        )

        # Write DiffSL model to file
        with open(path, 'w') as f:
            f.write(diffsl_model)

    def _expand_protocols(self, protocols, final_time):
        """
        Expand one or more :class:`myokit.Protocol` objects into an initial
        level vector and hybrid phase boundaries
        ``(t_boundary, levels_after)``.

        Expansion is performed by stepping one :class:`myokit.PacingSystem`
        per binding through its event boundaries until the expansion horizon is
        reached.

        Returns a tuple ``(initial_levels, phases)`` where ``initial_levels``
        is the level vector active at ``t = 0`` and ``phases`` is a list of
        ``(t_boundary, levels_after)`` tuples in ascending order of
        ``t_boundary``. Level vectors are aligned with the insertion order of
        ``protocols``.

        If any protocol remains non-zero at ``final_time``, a terminal
        boundary ``(final_time, zeros)`` is appended.
        """
        horizon = float(final_time)
        pacings = [
            myokit.PacingSystem(protocol) for protocol in protocols.values()
        ]
        current_levels = [float(pacing.pace()) for pacing in pacings]
        initial_levels = tuple(current_levels)
        phases = []

        # Step through all pacing boundaries up to the horizon.
        while True:
            t_next = min(pacing.next_time() for pacing in pacings)
            if t_next >= horizon:
                break
            for i, pacing in enumerate(pacings):
                if abs(pacing.next_time() - t_next) <= 1e-6:
                    current_levels[i] = float(pacing.advance(t_next))
            phases.append((t_next, tuple(current_levels)))

        # Ensure return to baseline at final_time if any pace remains active.
        if any(level != 0 for level in current_levels):
            phases.append((horizon, tuple(0.0 for _ in current_levels)))

        return initial_levels, phases

    def _prep_model(self, model, convert_units, bindings_to_keep):
        """
        Prepare the model for export to DiffSL.
        """
        # Rewrite model so that any Markov models have a 1-sum(...) state
        # This also clones the model, so that changes can be made
        model = markov.convert_markov_models_to_compact_form(model)

        # Remove all model bindings apart from time and requested bindings
        labels = collections.OrderedDict([('time', 't')])
        for label in bindings_to_keep:
            labels[label] = label
        _ = myokit._prepare_bindings(model, labels)

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

    def _generate_diffsl(
        self, model, inputs, outputs, bound_variables, protocol_data=None
    ):
        """
        Generate a DiffSL model from a prepped Myokit model.

        Arguments:

        ``model``
            The prepared Myokit model.
        ``inputs``
            List of model variables to include in the input parameter list.
        ``outputs``
            List of model variables to include in the output list.
        ``bound_variables``
            Ordered mapping of binding labels to preserved bound variables.
        ``protocol_data``
            Optional tuple ``(initial_levels, phases)`` produced by
            :meth:`_expand_protocols`. When provided, hybrid schedule
            ``*_i``/``stop_i`` blocks are appended and bound variables are
            expected to reference ``*_i[N]`` for the current phase level.
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
        # output; bound variables are handled separately; inputs are in the in
        # block.
        time = model.time()
        special_vars = set(v for v in model.states())
        special_vars.add(time)
        for variable in bound_variables.values():
            special_vars.add(variable)
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

        phases = None
        initial_levels = None
        protocol_schedule_names = None
        if protocol_data is not None:
            initial_levels, phases = protocol_data
            protocol_schedule_names = self._create_protocol_schedule_names(
                bound_variables.keys()
            )

        # Hybrid protocol blocks must be defined before bound variables use
        # their tensors.
        if phases is not None:
            # phases: [(t_boundary, level_after), ...] sorted by t_boundary.
            #
            # DiffSL hybrid convention used here:
            #   N = 0           at t=0 with the initial protocol levels
            #   N = k (k >= 1) after boundary index k-1 fires
            #
            # schedule_i[N] gives the binding level active in phase N.
            # Phase 0 starts at t=0 and may already be non-zero.
            # Phase k (k >= 1) is entered when stop element k-1 crosses zero.
            labels = list(bound_variables)

            # Emit one level vector per binding, indexed by N
            for i, label in enumerate(labels):
                level_name = protocol_schedule_names[label]
                levels = [initial_levels[i]]
                levels.extend(phase_levels[i] for _, phase_levels in phases)
                export_lines.append(
                    f'/* Protocol: {label} level per model index N */'
                )
                export_lines.append(f'{level_name}_i {{')
                for level in levels:
                    export_lines.append(f'{tab}{level},')
                export_lines.append('}')
                export_lines.append('')

            export_lines.append('')

        # Add preserved bound variables
        for label, variable in bound_variables.items():
            export_lines.append(f'/* Bound variable: {label} */')

            lhs = self._var_name(variable)
            rhs = f'{protocol_schedule_names[label]}_i[N]'
            qname = variable.qname()
            unit = '' if variable.unit() is None else f' {variable.unit()}'
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
            rhs = e.ex(v.initial_value())
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

        # Emit stop and reset conditions at the end of the file.
        if phases is not None:
            # stop[0] is a positive sentinel because N starts at 0 and the
            # solver should never trigger on the initial phase.
            export_lines.append(
                '/* Protocol: stop conditions (stop[k] = t - t_{k+1}) */'
            )
            export_lines.append('stop_i {')
            export_lines.append(f'{tab}1.0,')
            for t_boundary, _ in phases:
                export_lines.append(f'{tab}t - {t_boundary},')
            export_lines.append('}')
            export_lines.append('')

            # diffsol requires a reset for a hybrid model
            # so just put in a unit reset that leaves the
            # state unchanged at the boundary.
            export_lines.append('/* Protocol: reset conditions (reset = u) */')
            export_lines.append('reset_i { u_i }')

        return '\n'.join(export_lines)

    def _normalize_protocols(self, protocol, model):
        """
        Normalize a protocol specification to an ordered binding map.
        """
        if protocol is None:
            return collections.OrderedDict()

        if isinstance(protocol, myokit.Protocol):
            protocols = collections.OrderedDict()
            if model.binding('pace') is not None:
                protocols['pace'] = protocol
            return protocols

        if not isinstance(protocol, abc.Mapping):
            raise myokit.ExportError(
                'protocol must be a myokit.Protocol or a dict mapping binding'
                ' names to myokit.Protocol objects.'
            )

        protocols = collections.OrderedDict()
        for label, value in protocol.items():
            if not isinstance(label, str):
                raise myokit.ExportError(
                    'Protocol dictionary keys must be binding names.'
                )
            if not isinstance(value, myokit.Protocol):
                raise myokit.ExportError(
                    'Protocol dictionary values must be'
                    ' myokit.Protocol instances.'
                )
            if model.binding(label) is not None:
                protocols[label] = value
        return protocols

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

        var_to_name = collections.OrderedDict()

        # Store initial names for variables
        for var in model.variables(deep=True, sort=True):
            var_to_name[var] = self._convert_name(var.qname())
            if var.is_state():
                var_to_name[var.lhs()] = self._convert_name(
                    'diff_' + var.qname()
                )

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

    def _create_protocol_schedule_names(self, labels):
        """
        Create DiffSL-compatible schedule names for protocol bindings.
        """
        from . import keywords

        reserved = set(self._var_to_name.values())
        reserved.update(keywords)
        reserved.update(['N', 'reset', 'stop'])

        names = collections.OrderedDict()
        used = set()
        for label in labels:
            root = self._convert_name(label)
            name = root
            i = 1
            while name in reserved or name in used:
                name = f'{root}{i}'
                i += 1
            names[label] = name
            used.add(name)
        return names

    def _convert_name(self, name):
        """
        Convert a name to a DiffSL-compatible identifier fragment.
        """
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
