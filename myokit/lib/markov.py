#
# Tools for working with Markov models of ion channels.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import collections
import numpy as np

import myokit


class LinearModel(object):
    """
    Represents a linear Markov model of an ion channel extracted from a
    :class:`myokit.Model`.

    The class assumes the markov model can be written as::

        dot(x) = A(V,p) * x
        I = B(V,p) * x

    where ``V`` is the membrane potential, ``p`` is a set of parameters and
    ``A`` and ``B`` are the matrices that relate the state ``x`` to its
    derivative ``dot(x)`` and a current ``I``.

    ``A`` and ``B`` can contain non-linear functions, but should be simple
    scalar matrices when evaluated for a fixed ``V`` and ``p``. For example,
    the current equation ``I = g * O * (V - E)`` would have ``p = [g, E]``, so
    that for fixed ``p`` and ``V`` this would resolve to
    ``I = (g * (V - E)) * O``, such that ``g * (V - E)`` is a constant that can
    be included in ``B``.

    The model variables to treat as parameter are specified by the user when
    the model is created. Any other variables, for example state variables such
    as intercellular calcium or constants such as temperature, are fixed when
    the markov model is created and can no longer be changed.

    To create a :class:`Markov`, pass in a :class:`myokit.Model` and select a
    list of states. All other states will be fixed at their current value and
    an attempt will be made to write the remaining state equations as linear
    combinations of the states. If this is not possible, a :class:`ValueError`
    is raised. The membrane potential must be indicated using the label
    ``membrane_potential`` or by passing it in as ``vm``.

    The current variable is optional, if no current is specified by the user
    the relation ``I = B * x`` is dropped and no ``B`` is calculated.

    Example::

        import myokit
        import myokit.lib.markov as markov

        # Load a model from disk
        model = myokit.load_model('some-model.mmt')

        # Select the relevant states and parameters
        states = [
            'ina.C1',
            'ina.C2',
            'ina.O',
            ...
            ]
        parameters = [
            'ina.p1',
            'ina.p2',
            ...
            ]
        current = 'ina.INa'

        # Extract a markov model
        mm = markov.LinearModel(model, states, parameters, current)

        # Get the matrices A and B such that dot(x) = A * x and I = B * x
        # where ``x`` is the state vector and ``I`` is the current.
        A, B = mm.matrices(membrane_potential=-40)
        print(A)

    Alternatively, a LinearModel can be constructed from a single component
    using the method :meth:`from_component() <LinearModel.from_component()>`::

        import myokit
        import myokit.lib.markov as markov

        # Load a model from disk
        model = myokit.load_model('some-model.mmt')

        # Extract a markov model
        mm = markov.LinearModel.from_component(model.get('ina'))

    Arguments:

    ``model``
        The model to work with.
    ``states``
        An ordered list of state variables (or state variable names) from
        ``model``. All remaining state variables will be frozen in place. Each
        state's derivative must be a linear combination of the other states.
    ``parameters``
        A list of parameters to maintain in their symbolic form.
    ``current``
        The markov model's current variable. The current must be a linear
        combination of the states (for example ``g * (V - E) * (O1 + O2)``)
        where ``O1`` and ``O2`` are states. If no current variable is specified
        ``None`` can be used instead.
    ``vm``
        The variable indicating membrane potential. If set to ``None``
        (default) the method will search for a variable with the label
        ``membrane_potential``.

    """
    # NOTE: A LinearModel must be immutable!
    # This ensures that the simulations don't have to clone it (which would be
    # costly and difficult).
    # A LinearModel has a method "matrices()" which can evaluate A and B
    # for its default values or newly passed in values, but it never updates
    # its internal state in any way!
    def __init__(self, model, states, parameters=None, current=None, vm=None):
        super(LinearModel, self).__init__()

        # Get a clone of the model, with all markov models written in full ODE
        # form.
        self._model = convert_markov_models_to_full_ode_form(model)
        del model

        #
        # Check input
        #

        # Check and collect state variables
        self._states = []
        for state in states:
            if isinstance(state, myokit.Variable):
                state = state.qname()
            try:
                state = self._model.get(str(state), myokit.Variable)
            except KeyError:
                raise LinearModelError('Unknown state: <' + str(state) + '>.')
            if not state.is_state():
                raise LinearModelError(
                    'Variable <' + state.qname() + '> is not a state.')
            if state in self._states:
                raise LinearModelError(
                    'State <' + state.qname() + '> was added twice.')
            self._states.append(state)
        del states

        # Check and collect parameter variables
        unique = set()
        self._parameters = []
        if parameters is None:
            parameters = []
        for parameter in parameters:
            if isinstance(parameter, myokit.Variable):
                parameter = parameter.qname()
            try:
                parameter = self._model.get(parameter, myokit.Variable)
            except KeyError:
                raise LinearModelError(
                    'Unknown parameter: <' + str(parameter) + '>.')
            if not parameter.is_literal():
                raise LinearModelError(
                    'Unsuitable parameter: <' + str(parameter) + '>.')
            if parameter in unique:
                raise LinearModelError(
                    'Parameter listed twice: <' + str(parameter) + '>.')
            unique.add(parameter)
            self._parameters.append(parameter)
        del unique
        del parameters

        # Check current variable
        if current is not None:
            if isinstance(current, myokit.Variable):
                current = current.qname()
            current = self._model.get(current, myokit.Variable)
            if current.is_state():
                raise LinearModelError('Current variable can not be a state.')
        self._current = current
        del current

        # Check membrane potential variable
        if vm is None:
            vm = self._model.label('membrane_potential')
        if vm is None:
            raise LinearModelError(
                'A membrane potential must be specified as `vm` or using the'
                ' label `membrane_potential`.')
        if isinstance(vm, myokit.Variable):
            vm = vm.qname()
        self._membrane_potential = self._model.get(vm)
        if self._membrane_potential in self._parameters:
            raise LinearModelError(
                'Membrane potential should not be included in the list of'
                ' parameters.')
        if self._membrane_potential in self._states:
            raise LinearModelError(
                'The membrane potential should not be included in the list of'
                ' states.')
        if self._membrane_potential == self._current:
            raise LinearModelError(
                'The membrane potential should not be the current variable.')
        del vm

        #
        # Demote unnecessary states, remove bindings and validate model.
        #
        # Get values of all states
        # Note: Do this _before_ changing the model!
        self._default_state = np.array([v.state_value() for v in self._states])

        # Freeze remaining, non-markov-model states
        s = self._model.state()   # Get state values before changing anything!
        for k, state in enumerate(self._model.states()):
            if state not in self._states:
                state.demote()
                state.set_rhs(s[k])
        del s

        # Unbind everything except time
        for label, var in self._model.bindings():
            if label != 'time':
                var.set_binding(None)

        # Check if current variable depends on selected states
        # (At this point, anything not dependent on the states is a constant)
        if self._current is not None and self._current.is_constant():
            raise LinearModelError(
                'Current must be a function of the markov model\'s state'
                ' variables.')

        # Validate modified model
        self._model.validate()

        #
        # Create functions:
        #   matrix_function(vm, p1, p2, ...   ) --> A, B
        #       where dot(x) = Ax and I = Bx
        #   rate_list_function(vm, p1, p2, ...) --> R
        #       where R contains tuples (i, j, rij)
        #

        # Create a list of inputs to the functions
        self._inputs = self._parameters + [self._membrane_potential]

        # Get the default values for all inputs
        self._default_inputs = np.array([v.eval() for v in self._inputs])

        # Create functions
        self._matrix_function = None
        self._rate_list_function = None
        self._generate_functions()

        #
        # Partial validation
        #
        # Check if dependencies are bidirectional
        for s in self._states:
            for d in s.refs_to(state_refs=True):
                if s not in d.refs_to(state_refs=True):
                    raise LinearModelError(
                        'State <' + s.qname() + '> depends on <' + d.qname()
                        + '> but not vice versa.')

        # Check the sum of all states is 1
        tolerance = 1e-8
        x = np.sum(self._default_state)
        if np.abs(x - 1) > tolerance:
            raise LinearModelError(
                'The sum of states is not equal to 1: ' + str(x))

        # Check the sum of all derivatives per column
        A, B = self.matrices()
        for k, x in enumerate(np.sum(A, axis=0)):
            if abs(x) > tolerance:
                raise LinearModelError(
                    'Derivatives in column ' + str(1 + k) + ' sum to non-zero'
                    ' value: ' + str(x) + '.')

    def _generate_functions(self):
        """
        Creates a function that takes parameters as input and returns matrices
        A and B.

        (This method is called only once, by the constructor, but it's
        complicated enough to warrant its own method...)
        """
        # Create mapping from states to index
        state_indices = {}
        for k, state in enumerate(self._states):
            state_indices[state] = k

        # Get expressions for state & current variables, but with all
        # references to variables (except states and parameters) replaced by
        # inlined expressions.
        expressions = []
        for v in self._states:
            expressions.append(v.rhs().clone(expand=True, retain=self._inputs))
        if self._current is not None:
            current_expression = self._current.rhs().clone(
                expand=True, retain=self._inputs)

        # Create parametrisable matrices to evaluate the state & current
        # This checks that each state's RHS can be written as a linear
        # combination of the states, and gathers the corresponding multipliers.

        # Matrix of linear factors
        n = len(self._states)
        A = [[myokit.Number(0) for j in range(n)] for i in range(n)]

        # List of transitions
        T = set()

        # Populate A and T
        for row, e in enumerate(expressions):

            # Check if this expression is a linear combination of the states
            try:
                factors = _linear_combination(e, self._states)
            except ValueError:
                raise LinearModelError(
                    'Unable to write expression as linear combination of'
                    ' states: ' + str(e) + '.')

            # Scan factors
            for col, state in enumerate(self._states):
                factor = factors[col]
                if factor is not None:
                    # Add factor to transition matrix
                    A[row][col] = factor

                    # Store transition in transition list
                    if row != col:
                        T.add((col, row))   # A is mirrored

        # Create a parametrisable matrix for the current
        B = [myokit.Number(0) for i in range(n)]
        if self._current is not None:
            try:
                factors = _linear_combination(current_expression, self._states)
            except ValueError:
                raise LinearModelError(
                    'Unable to write expression as linear combination of'
                    ' states: ' + str(e) + '.')

            for col, state in enumerate(self._states):
                factor = factors[col]
                if factor is not None:
                    B[col] = factor

        # Create list of transition rates and associated equations
        T = list(T)
        T.sort()
        R = []
        for i in range(len(A)):
            for j in range(len(A)):
                if (i, j) in T:
                    R.append((i, j, A[j][i]))   # A is mirrored
        del T

        #
        # Create function to create parametrisable matrices
        #
        self._model.reserve_unique_names('A', 'B', 'n', 'numpy')
        writer = myokit.numpy_writer()
        w = writer.ex
        head = 'def matrix_function('
        head += ','.join([w(p.lhs()) for p in self._inputs])
        head += '):'
        body = []
        body.append('A = numpy.zeros((n, n))')
        zero = myokit.Number(0)
        for i, row in enumerate(A):
            for j, e in enumerate(row):
                if e != zero:
                    body.append('A[' + str(i) + ',' + str(j) + '] = ' + w(e))
        body.append('B = numpy.zeros(n)')
        for j, e in enumerate(B):
            if e != zero:
                body.append('B[' + str(j) + '] = ' + w(e))
        body.append('return A, B')
        code = head + '\n' + '\n'.join(['    ' + line for line in body])
        globl = {'numpy': np, 'n': n}
        local = {}

        myokit._exec(code, globl, local)
        self._matrix_function = local['matrix_function']

        #
        # Create function to return list of transition rates
        #
        self._model.reserve_unique_names('R', 'n', 'numpy')
        head = 'def rate_list_function('
        head += ','.join([w(p.lhs()) for p in self._inputs])
        head += '):'
        body = []
        body.append('R = []')
        for i, j, e in R:
            body.append(
                'R.append((' + str(i) + ',' + str(j) + ',' + w(e) + '))')
        body.append('return R')
        code = head + '\n' + '\n'.join(['    ' + line for line in body])
        globl = {'numpy': np}
        local = {}
        myokit._exec(code, globl, local)
        self._rate_list_function = local['rate_list_function']

    def current(self):
        """
        Returns the name of the current variable used by this model, or None if
        no current variable was specified.
        """
        return self._current

    def default_membrane_potential(self):
        """
        Returns this markov model's default membrane potential value.
        """
        return self._default_inputs[-1]

    def default_parameters(self):
        """
        Returns this markov model's default parameter values
        """
        return list(self._default_inputs[:-1])

    def default_state(self):
        """
        Returns this markov model's default state values.
        """
        return list(self._default_state)

    @staticmethod
    def from_component(
            component, states=None, parameters=None, current=None, vm=None):
        """
        Creates a Markov model from a component, using the following rules:

          1. Every state in the component is a state in the Markov model
          2. Every unnested constant in the component is a parameter
          3. The component should contain exactly one unnested intermediary
             variable whose value depends on the model states, this will be
             used as the current variable.
          4. The model contains a variable labeled "membrane_potential".

        Any of the automatically set variables can be overridden using the
        keyword arguments ``states``, ``parameters``, ``current`` and ``vm``.

        The parameters, if determined automatically, will be specified in
        alphabetical order (using a natural sort).
        """
        model = component.model()

        # Get or check states
        if states is None:

            # Get state variables
            states = [x for x in component.variables(state=True)]

            # Sort by state indice
            states.sort(key=lambda x: x.indice())

        else:

            # Make sure states are variables. This is required to automatically
            # find a current variable.
            states_in = states
            states = []
            for state in states_in:
                if isinstance(state, myokit.Variable):
                    state = state.qname()
                states.append(model.get(state))

        # Get parameters
        if parameters is None:

            # Get parameters
            parameters = [
                x for x in component.variables(const=True) if x.is_literal()]
            # Sort by qname, using natural sort
            parameters.sort(
                key=lambda x: myokit.tools.natural_sort_key(x.qname()))

        # Get current
        if current is None:
            currents = []
            for x in component.variables(inter=True):
                for y in x.refs_to(state_refs=True):
                    if y in states:
                        # Found a candidate!
                        currents.append(x)
                        break
            if len(currents) > 1:
                raise LinearModelError(
                    'The given component has more than one variable that could'
                    ' be a current: '
                    + ', '.join(['<' + x.qname() + '>' for x in currents])
                    + '.')
            try:
                current = currents[0]
            except IndexError:
                pass

        # Get membrane potential
        if vm is None:
            vm = model.label('membrane_potential')
            if vm is None:
                raise LinearModelError(
                    'The model must define a variable labeled as'
                    ' "membrane_potential".')

        # Create and return LinearModel
        return LinearModel(model, states, parameters, current, vm)

    def matrices(self, membrane_potential=None, parameters=None):
        """
        For a given value of the ``membrane_potential`` and a list of values
        for the ``parameters``, this method calculates and returns the matrices
        ``A`` and ``B`` such that::

            dot(x) = A * x
            I = B * x

        where ``x`` is the state vector and ``I`` is the current.

        Arguments:

        ``membrane_potential``
            The value to use for the membrane potential, or ``None`` to use the
            value from the original :class:`myokit.Model`.
        ``parameters``
            The values to use for the parameters, given in the order they were
            originally specified in (if the model was created using
            :meth:`from_component()`, this will be alphabetical order).

        """
        inputs = list(self._default_inputs)
        if membrane_potential is not None:
            inputs[-1] = float(membrane_potential)
        if parameters is not None:
            if len(parameters) != len(self._parameters):
                raise ValueError(
                    'Illegal parameter vector size: '
                    + str(len(self._parameters)) + ' required, '
                    + str(len(parameters)) + ' provided.')
            inputs[:-1] = [float(x) for x in parameters]
        return self._matrix_function(*inputs)

    def membrane_potential(self):
        """
        Returns the name of the membrane potential variable used by this model.
        """
        return self._membrane_potential.qname()

    def parameters(self):
        """
        Returns the names of the parameter variables used by this model.
        """
        return [v.qname() for v in self._parameters]

    def rates(self, membrane_potential=None, parameters=None):
        """
        For a given value of the ``membrane_potential`` and a list of values
        for the ``parameters``, this method calculates and returns an ordered
        list of tuples ``(i, j, rij)`` such that ``rij`` is a non-zero
        transition rate from the ``i``-th state to the ``j``-th state.

        Arguments:

        ``membrane_potential``
            The value to use for the membrane potential, or ``None`` to use the
            value from the original :class:`myokit.Model`.
        ``parameters``
            The values to use for the parameters, given in the order they were
            originally specified in (if the model was created using
            :meth:`from_component()`, this will be alphabetical order).

        """
        inputs = list(self._default_inputs)
        if membrane_potential is not None:
            inputs[-1] = float(membrane_potential)
        if parameters is not None:
            if len(parameters) != len(self._parameters):
                raise ValueError(
                    'Illegal parameter vector size: '
                    + str(len(self._parameters)) + ' required, '
                    + str(len(parameters)) + ' provided.')
            inputs[:-1] = [float(x) for x in parameters]
        return self._rate_list_function(*inputs)

    def states(self):
        """
        Returns the names of the state variables used by this model.
        """
        return [v.qname() for v in self._states]

    def steady_state(self, membrane_potential=None, parameters=None):
        """
        Analytically determines a steady state solution for this Markov model.

        ``membrane_potential``
            The value to use for the membrane potential, or ``None`` to use the
            value from the original :class:`myokit.Model`.
        ``parameters``
            The values to use for the parameters, given in the order they were
            originally specified in (if the model was created using
            :meth:`from_component()`, this will be alphabetical order).

        """
        # Calculate Jacobian and derivatives
        A, _ = self.matrices(membrane_potential, parameters)

        # Set up reduced system with full rank: dot(x) = Ay + B
        B = A[:-1, -1:]
        A = A[:-1, :-1] - B

        # Check eigenvalues
        if np.max(np.linalg.eigvals(A) >= 0):
            raise LinearModelError(
                'System has positive eigenvalues: won\'t converge to steady'
                ' state!')

        # Solve system Ax + B = 0 --> Ax = -B
        x = np.linalg.solve(A, -B)

        # Recreate full state vector and return
        x = np.array(x).reshape((len(x),))
        x = np.concatenate((x, [1 - np.sum(x)]))
        return x


class AnalyticalSimulation(object):
    """
    Analytically evaluates a :class:`LinearModel`'s state over a given set of
    points in time.

    Solutions are calculated for the "law of large numbers" case, i.e. without
    stochastic behavior. The solution algorithm is based on eigenvalue
    decomposition.

    Each simulation object maintains an internal state consisting of

    * The current simulation time
    * The current state
    * The default state

    When a simulation is created, the simulation time is set to zero and both
    the current and default state are initialized using the ``LinearModel``.
    After each call to :meth:`run()` the time and current state are updated,
    so that each successive call to run continues where the previous simulation
    left off.

    A :class:`protocol <myokit.Protocol>` can be used to set the membrane
    potential during the simulation, or the membrane potential can be adjusted
    manually between runs.

    Example::

        import myokit
        import myokit.lib.markov as markov

        # Create a linear markov model
        m = myokit.load_model('clancy-1999.mmt')
        m = markov.LinearModel.from_component(m.get('ina'))

        # Create an analytical simulation object
        s = markov.AnalyticalSimulation(m)

        # Run a simulation
        s.set_membrane_potential(-30)
        d = s.run(10)

        # Show the results
        import matplotlib.pyplot as plt
        plt.figure()
        plt.subplot(211)
        for state in m.states():
            plt.plot(d.time(), d[state], label=state)
        plt.legend(loc='center right')
        plt.subplot(212)
        plt.plot(d.time(), d[m.current()])
        plt.show()

    """
    def __init__(self, model, protocol=None):
        super(AnalyticalSimulation, self).__init__()
        # Check model
        if not isinstance(model, LinearModel):
            raise ValueError('First parameter must be a `LinearModel`.')
        self._model = model

        # Check protocol
        if protocol is None:
            self._protocol = None
        elif not isinstance(protocol, myokit.Protocol):
            raise ValueError('Protocol must be a myokit.Protocol object')
        else:
            self._protocol = protocol.clone()

        # Time variable
        self._time = 0

        # Check if we have a current variable
        self._has_current = self._model.current() is not None

        # Set state
        self._state = np.array(
            self._model.default_state(), copy=True, dtype=float)

        # Set default state
        self._default_state = np.array(self._state, copy=True)

        # Get membrane potential
        self._membrane_potential = self._model.default_membrane_potential()

        # Get parameters
        self._parameters = np.array(
            self._model.default_parameters(), copy=True, dtype=float)

        # Mapping from parameter names to index in parameter array
        self._parameter_map = {}
        for i, p in enumerate(self._model.parameters()):
            self._parameter_map[p] = i

        # Cached matrices and partial solution (eigenvalue decomposition etc.)
        # Both stored per voltage, but will become invalidated if parameters
        # change
        self._cached_matrices = {}
        self._cached_solution = {}

        # If protocol was given, create pacing system, update vm
        self._pacing = None
        if self._protocol:
            self._pacing = myokit.PacingSystem(self._protocol)
            self._membrane_potential = self._pacing.advance(self._time)

        # Keys for logging
        self._time_key = self._model._model.time().qname()
        self._vm_key = self._model._membrane_potential
        self._log_keys = [self._time_key, self._vm_key] + self._model.states()
        if self._has_current:
            self._log_keys.append(self._model.current())

    def current(self, state):
        """
        Calculates the current for a given state.
        """
        if not self._has_current:
            raise Exception(
                'The used model did not specify a current variable.')
        A, B = self._matrices()
        return B.dot(state)

    def default_state(self):
        """
        Returns the default state used by this simulation.
        """
        return list(self._default_state)

    def _matrices(self):
        """
        Returns the (cached or re-generated) matrices.

        Returns ``(A, B)`` if this simulation's model has a current variable,
        or just ``B`` if it doesn't.
        """
        try:
            return self._cached_matrices[self._membrane_potential]
        except KeyError:
            matrices = self._model.matrices(
                self._membrane_potential, self._parameters)
            self._cached_matrices[self._membrane_potential] = matrices
            return matrices

    def membrane_potential(self):
        """
        Returns the currently set membrane potential.
        """
        return self._membrane_potential

    def parameters(self):
        """
        Returns the currently set parameter values.
        """
        return list(self._parameters)

    def pre(self, duration):
        """
        Performs an unlogged simulation for ``duration`` time units and uses
        the final state as the new default state.

        After the simulation:

        - The simulation time is **not** affected
        - The current state and the default state are updated to the final
          state reached in the simulation.

        Calls to :meth:`reset` after using :meth:`pre` will set the current
        state to this new default state.
        """
        # Check arguments
        duration = float(duration)
        if duration < 0:
            raise ValueError('Duration must be non-negative.')

        # Run
        # This isn't much faster, but this way the simulation's interface is
        # similar to the standard simulation one.
        old_time = self._time
        self.run(duration, log_interval=2 * duration)

        # Update default state
        self._default_state = np.array(self._state, copy=True)

        # Reset time, reset protocol
        self._time = old_time
        if self._protocol:
            self._pacing = myokit.PacingSystem(self._protocol)
            self._membrane_potential = self._pacing.advance(self._time)

    def reset(self):
        """
        Resets the simulation:

        - The time variable is set to zero.
        - The state is set to the default state.

        """
        self._time = 0
        self._state = np.array(self._default_state, copy=True)
        if self._protocol:
            self._pacing = myokit.PacingSystem(self._protocol)
            self._membrane_potential = self._pacing.advance(self._time)

    def run(self, duration, log=None, log_interval=0.01, log_times=None):
        """
        Runs a simulation for ``duration`` time units.

        After the simulation:

        - The simulation time will be increased by ``duration`` time units.
        - The simulation state will be updated to the last reached state.

        Arguments:

        ``duration``
            The number of time units to simulate.
        ``log``
            A log from a previous run can be passed in, in which case the
            results will be appended to this one.
        ``log_interval``
            The time between logged points.
        ``log_times``
            A pre-defined sequence of times to log at. If set, ``log_interval``
            will be ignored.

        Returns a :class:`myokit.DataLog` with the simulation results.
        """
        # Check arguments
        duration = float(duration)
        if duration < 0:
            raise ValueError('Duration must be non-negative.')
        log_interval = float(log_interval)
        if log_interval <= 0:
            raise ValueError('Log interval must be greater than zero.')

        # Check log_times
        if log_times is None:
            log_times = self._time + np.arange(0, duration, log_interval)

        # Set up logging
        if log is None:

            # Create new log
            log = myokit.DataLog()
            log.set_time_key(self._time_key)
            for key in self._log_keys:
                log[key] = np.zeros(log_times.shape)
            offset = 0

        else:

            # Check existing log
            if len(log.keys()) > len(self._log_keys):
                raise ValueError('Invalid log: contains extra keys.')
            try:
                key = self._time_key    # Note: error msg below uses `key`
                offset = len(log[key])
                for key in self._log_keys:
                    log[key] = np.concatenate((
                        log[key], np.zeros(log_times.shape)))
            except KeyError:
                raise ValueError(
                    'Invalid log: missing entry for <' + str(key) + '>.')

        # Run simulation
        if self._protocol is None:

            # User defined membrane potential
            self._run(log, log_times, self._time + duration, offset)

        else:

            # Voltage clamp
            tfinal = self._time + duration
            while self._time < tfinal:
                # Run simulation
                tnext = min(tfinal, self._pacing.next_time())
                times = log_times[np.logical_and(
                    log_times >= self._time, log_times < tnext)]
                self._run(log, times, tnext, offset)
                offset += len(times)

                # Update pacing
                self._membrane_potential = self._pacing.advance(tnext)

        # Return
        return log

    def _run(self, log, times, tnext, offset):
        """
        Runs a simulation with the current membrane potential.

        Arguments:

        ``log``
            The log to append to.
        ``times``
            The times to evaluate at.
        ``tnext``
            The final time to move to.
        ``offset``
            The offset in the ``times`` array to log in

        """
        # Simulate with fixed V
        if self._has_current:
            states, currents = self.solve(times - self._time)
        else:
            states = self.solve(times - self._time)

        # Log results
        lo = offset
        hi = lo + len(times)
        key = log.time_key()
        log[key][lo:hi] = times
        for i, key in enumerate(self._model.states()):
            log[key][lo:hi] = states[i]
        if self._has_current:
            key = self._model.current()
            log[key][lo:hi] = currents
        key = self._model._membrane_potential
        log[key][lo:hi] = self._membrane_potential

        # Now run simulation for final time (which might not be included in the
        # list of logged times, and should not, if you want to be able to
        # append logs without creating duplicate points).
        times = np.array([tnext - self._time])
        if self._has_current:
            states, currents = self.solve(times)
        else:
            states = self.solve(times)

        # Update simulation state
        self._state = np.array(states[:, -1], copy=True)
        self._time = tnext

    def set_constant(self, variable, value):
        """
        Updates a single parameter to a new value.
        """
        self._parameters[self._parameter_map[variable]] = float(value)

    def set_default_state(self, state):
        """
        Changes this simulation's default state.
        """
        state = np.array(state, copy=True, dtype=float)
        if len(state) != len(self._state):
            raise ValueError(
                'Wrong size state vector, expecing (' + str(len(self._state))
                + ') values.')
        if np.any(state < 0):
            raise ValueError(
                'The fraction of channels in a state cannot be negative.')
        if np.abs(np.sum(state) - 1) > 1e-6:
            raise ValueError('The values in `state` must sum to 1.')
        self._default_state = state

    def set_membrane_potential(self, v):
        """
        Changes the membrane potential used in this simulation.
        """
        if self._protocol:
            raise Exception(
                'Membrane potential cannot be set if a protocol is used.')
        self._membrane_potential = float(v)

    def set_parameters(self, parameters):
        """
        Changes the parameter values used in this simulation.
        """
        if len(parameters) != len(self._parameters):
            raise ValueError(
                'Wrong size parameter vector, expecting ('
                + str(len(self._parameters)) + ') values.')
        self._parameters = np.array(parameters, copy=True, dtype=float)

        # Invalidate cache
        self._cached_matrices = {}
        self._cached_solution = {}

    def set_state(self, state):
        """
        Changes the initial state used by in this simulation.
        """
        state = np.array(state, copy=True, dtype=float)
        if len(state) != len(self._state):
            raise ValueError(
                'Wrong size state vector, expecing (' + str(len(self._state))
                + ') values.')
        if np.any(state < 0):
            raise ValueError(
                'The fraction of channels in a state cannot be negative.')
        if np.abs(np.sum(state) - 1) > 1e-6:
            raise ValueError('The values in `state` must sum to 1.')
        self._state = state

    def solve(self, times):
        """
        Evaluates and returns the states at the given times.

        In contrast to :meth:`run()`, this method simply evaluates the states
        (and current) at the given times, using the last known settings for
        the state and membrane potential. It does not use a protocol and does
        not take into account the simulation time. After running this method,
        the state and simulation time are *not* updated.

        Arguments:

        ``times``
            A series of times, where each time must be some ``t >= 0``.

        For models with a current variable, this method returns a tuple
        ``(state, current)`` where ``state`` is a matrix of shape
        ``(len(states), len(times))`` and ``current`` is a vector
        of length ``len(times)``.

        For models without a current variable, only ``state`` is returned.
        """
        n = len(self._state)

        # Solve system, or get cached solution
        try:
            E, P, PI, B = self._cached_solution[self._membrane_potential]
        except KeyError:
            # Get matrices
            A, B = self._matrices()

            # Get eigenvalues, matrix of eigenvectors
            E, P = np.linalg.eig(A)
            E = E.reshape((n, 1))
            PI = np.linalg.inv(P)

            # Cache results
            self._cached_solution[self._membrane_potential] = (E, P, PI, B)

        # Calculate transform of initial state
        y0 = PI.dot(self._state.reshape((n, 1)))

        # Reshape times array
        times = np.array(times, copy=False).reshape((len(times),))

        # Calculate state
        x = P.dot(y0 * np.exp(times * E))

        # Calculate current and/or return
        if self._has_current:
            return x, B.dot(x)
        else:
            return x

    def state(self):
        """
        Returns the initial state used by this simulation.
        """
        return list(self._state)


class DiscreteSimulation(object):
    """
    Performs stochastic simulations of a :class:`LinearModel`'s behavior for a
    finite number of channels.

    Simulations are run using the "Direct method" proposed by Gillespie [1].

    Each simulation object maintains an internal state consisting of

    * The current simulation time
    * The current state
    * The default state

    When a simulation is created, the simulation time is set to zero and both
    the current and default state are initialized using the ``LinearModel``.
    After each call to :meth:`run()` the time and current state are updated,
    so that each successive call to run continues where the previous simulation
    left off.

    A :class:`protocol <myokit.Protocol>` can be used to set the membrane
    potential during the simulation, or the membrane potential can be adjusted
    manually between runs.

    Example::

        import myokit
        import myokit.lib.markov as markov

        # Create linear markov model
        m = myokit.load_model('clancy-1999.mmt')
        m = markov.LinearModel.from_component(m.get('ina'))

        # Run discrete simulation
        s = markov.DiscreteSimulation(m, nchannels=1000)
        s.set_membrane_potential(-30)
        d = s.run(10)

        import matplotlib.pyplot as plt
        plt.figure()
        for state in m.states():
            plt.step(d.time(), d[state], label=state)
        plt.legend()
        plt.show()

    References

    [1] Gillespie (1976) A General Method for Numerically Simulating the
        stochastic time evolution of coupled chemical reactions
        The Journal of Computational Physics, 22, 403-434.

    Arguments:

    ``model``
        A :class:`LinearModel`.
    ``nchannels``
        The number of channels to simulate.

    """

    def __init__(self, model, protocol=None, nchannels=100):
        # Check model
        if not isinstance(model, LinearModel):
            raise ValueError('First parameter must be a `LinearModel`.')
        self._model = model

        # Check protocol
        if protocol is None:
            self._protocol = None
        elif not isinstance(protocol, myokit.Protocol):
            raise ValueError('Protocol must be a myokit.Protocol object')
        else:
            self._protocol = protocol.clone()

        # Get state and discretize
        nchannels = int(nchannels)
        if nchannels < 1:
            raise ValueError('The number of channels must be at least 1.')
        self._nchannels = nchannels

        # Set state
        self._state = self.discretize_state(self._model.default_state())

        # Set default state
        self._default_state = list(self._state)

        # Set membrane potential
        self._membrane_potential = self._model.default_membrane_potential()

        # Set parameters
        self._parameters = np.array(
            self._model.default_parameters(), copy=True, dtype=float)

        # Mapping from parameter names to index in parameter array
        self._parameter_map = {}
        for i, p in enumerate(self._model.parameters()):
            self._parameter_map[p] = i

        # Cached transition rate list & current matrix
        self._cached_rates = None
        self._cached_matrix = None

        # Set simulation time
        self._time = 0

        # If protocol was given, create pacing system, update vm
        self._pacing = None
        if self._protocol:
            self._pacing = myokit.PacingSystem(self._protocol)
            self._membrane_potential = self._pacing.advance(self._time)

    def default_state(self):
        """
        Returns the default simulation state.
        """
        return list(self._default_state)

    def discretize_state(self, x):
        """
        Converts a list of fractional state occupancies to a list of channel
        counts.

        Arguments:

        ``x``
            A fractional state where ``sum(x) == 1``.

        Returns a discretized state ``y`` where ``sum(y) = nchannels``.
        """
        x = np.array(x, copy=False, dtype=float)
        if (np.abs(1 - np.sum(x))) > 1e-6:
            raise ValueError(
                'The sum of fractions in the state to be discretized must'
                ' equal 1.')
        y = np.round(x * self._nchannels)
        # To make sure it always sums to 1, correct the value found at the
        # indice with the biggest rounding error.
        i = np.argmax(np.abs(x - y))
        y[i] = 0
        y[i] = self._nchannels - np.sum(y)
        return list(y)

    def membrane_potential(self):
        """
        Returns the current membrane potential.
        """
        return self._membrane_potential

    def number_of_channels(self):
        """
        Returns the number of channels used in this simulation.
        """
        return self._nchannels

    def parameters(self):
        """
        Returns the current parameter values.
        """
        return list(self._parameters)

    def pre(self, duration):
        """
        Performs an unlogged simulation for ``duration`` time units and uses
        the final state as the new default state.

        After the simulation:

        - The simulation time is **not** affected
        - The current state and the default state are updated to the final
          state reached in the simulation.

        Calls to :meth:`reset` after using :meth:`pre` will set the current
        state to this new default state.
        """
        # Check arguments
        duration = float(duration)
        if duration < 0:
            raise ValueError('Duration must be non-negative.')

        # Run
        # This isn't much faster, but this way the simulation's interface is
        # similar to the standard simulation one.
        old_time = self._time
        self.run(duration)

        # Update default state
        self._default_state = list(self._state)

        # Reset time, reset protocol
        self._time = old_time
        if self._protocol:
            self._pacing = myokit.PacingSystem(self._protocol)
            self._membrane_potential = self._pacing.advance(self._time)

    def _current_matrix(self):
        """
        Returns the (cached or regenerated) current matrix B.
        """
        if self._cached_matrix is None:
            self._cached_matrix = self._model.matrices(
                self._membrane_potential, self._parameters)[1]
        return self._cached_matrix

    def _rates(self):
        """
        Returns the (cached or regenerated) transition rate list.
        """
        if self._cached_rates is None:
            self._cached_rates = self._model.rates(
                self._membrane_potential, self._parameters)
        return self._cached_rates

    def reset(self):
        """
        Resets the simulation:

        - The time variable is set to zero.
        - The state is set to the default state.

        """
        self._time = 0
        self._state = list(self._default_state)
        if self._protocol:
            self._pacing = myokit.PacingSystem(self._protocol)
            self._membrane_potential = self._pacing.advance(self._time)

    def run(self, duration, log=None):
        """
        Runs a simulation for ``duration`` time units.

        After the simulation:

        - The simulation time will be increased by ``duration`` time units.
        - The simulation state will be updated to the last reached state.

        Arguments:

        ``duration``
            The number of time units to simulate.
        ``log``
            A log from a previous run can be passed in, in which case the
            results will be appended to this one.

        Returns a :class:`myokit.DataLog` with the simulation results.
        """
        # Check arguments
        duration = float(duration)
        if duration < 0:
            raise ValueError('Duration must be non-negative.')

        # Set up logging
        time_key = self._model._model.time().qname()
        log_vars = [time_key, self._model._membrane_potential]
        log_vars.extend(self._model.states())
        cur_key = self._model.current()
        if cur_key is not None:
            log_vars.append(cur_key)

        if log is None:
            # Create new log
            log = myokit.DataLog()
            log.set_time_key(time_key)
            for var in log_vars:
                log[var] = []

        else:

            # Check existing log
            if len(log.keys()) > len(log_vars):
                raise ValueError('Invalid log: contains extra keys.')
            try:
                for key in log_vars:
                    log[key]
            except KeyError:
                raise ValueError(
                    'Invalid log: missing entry for <' + str(key) + '>.')

        if self._protocol is None:
            # Simulate with fixed V
            self._run(duration, log)

        else:

            # Voltage clamp
            tfinal = self._time + duration
            while self._time < tfinal:
                # Run simulation
                tnext = min(tfinal, self._pacing.next_time())
                self._run(tnext - self._time, log)
                # Update pacing
                self._membrane_potential = self._pacing.advance(tnext)
                self._cached_rates = None
                self._cached_matrix = None

        # Return
        return log

    def _run(self, duration, log):
        """
        Runs a simulation with the current membrane potential.
        """
        # Get logging lists
        log_time = log.time()
        log_states = []
        for key in self._model.states():
            log_states.append(log[key])

        # Get current, time and state
        t = self._time
        state = np.array(self._state, copy=True, dtype=int)

        # Get list of transitions
        R = []      # Transition rates
        SI = []     # From state
        SJ = []     # To state
        for i, j, rij in self._rates():
            SI.append(i)
            SJ.append(j)
            R.append(rij)
        R = np.array(R)
        SI = np.array(SI)
        SJ = np.array(SJ)

        # Run
        n_steps = 0
        t_stop = self._time + duration

        # Request for a short time can result in duration=0 at this point,
        # Must set variables otherwise set in loop below here
        if t >= t_stop:
            lambdas = R * state[SI]

        while t < t_stop:
            # Log
            log_time.append(t)
            for i, x in enumerate(state):
                log_states[i].append(x)
            n_steps += 1

            # Get lambdas
            lambdas = R * state[SI]

            # Get sum of lambdas
            lsum = np.sum(lambdas)

            # Sample time until next transition from an exponential
            # distribution with mean 1 / lsum
            tau = np.random.exponential(1 / lsum)

            # Don't step beyond the stopping time!
            if t + tau > t_stop:
                break

            # Get type of transition
            transition = np.random.uniform(0, lsum)
            rsum = 0
            for i, r in enumerate(lambdas):
                rsum += r
                if rsum > transition:
                    break

            # Perform transition
            state[SI[i]] -= 1
            state[SJ[i]] += 1
            t += tau

        # Perform final step using the "brute-force" approach, ensuring we
        # reach self._time + duration exactly.
        # Note that for large tau, the estimates of the probability that
        # something changes may become inaccurate (and > 1)
        # I didn't see this in testing...
        tau = (self._time + duration) - t
        lambdas *= tau
        for i, r in enumerate(lambdas):
            if np.random.uniform(0, 1) < r:
                # Perform transition
                state[SI[i]] -= 1
                state[SJ[i]] += 1

        # Add vm to log
        vm_key = self._model._membrane_potential
        log[vm_key].extend([self._membrane_potential] * n_steps)

        # Add current to log
        c = self._model.current()
        if c is not None:
            B = self._current_matrix()
            x = np.vstack([
                np.array(log_states[i][-n_steps:], dtype=float)
                for i in range(len(state))])
            x /= self._nchannels
            log[c].extend(B.dot(x))

        # Update current state and time
        self._state = list(state)
        self._time += duration

    def set_constant(self, variable, value):
        """
        Updates a single parameter to a new value.
        """
        self._parameters[self._parameter_map[variable]] = float(value)

    def set_default_state(self, state):
        """
        Changes the default state used in the simulation.
        """
        state = np.asarray(state, dtype=int)
        if len(state) != len(self._state):
            raise ValueError(
                'Wrong size state vector, expecing (' + str(len(self._state))
                + ') values.')
        if np.min(state) < 0:
            raise ValueError(
                'The number of channels in a markov model state can not be'
                ' negative.')
        if np.sum(state) != self._nchannels:
            raise ValueError(
                'The number of channels in the default state vector must'
                ' equal ' + str(self._nchannels) + '.')
        self._default_state = list(state)

    def set_membrane_potential(self, v):
        """
        Changes the membrane potential used in this simulation.
        """
        if self._protocol:
            raise Exception(
                'Membrane potential cannot be set if a protocol is used.')
        self._membrane_potential = float(v)
        self._cached_rates = None
        self._cached_matrix = None

    def set_parameters(self, parameters):
        """
        Changes the parameter values used in this simulation.
        """
        if len(parameters) != len(self._parameters):
            raise ValueError(
                'Wrong size parameter vector, expecting ('
                + str(len(self._parameters)) + ') values.')
        self._parameters = np.array(parameters, copy=True, dtype=float)
        self._cached_rates = None
        self._cached_matrix = None

    def set_state(self, state):
        """
        Changes the current state used in the simulation (i.e. the number of
        channels in every markov model state).
        """
        state = np.asarray(state, dtype=int)
        if len(state) != len(self._state):
            raise ValueError(
                'Wrong size state vector, expecing (' + str(len(self._state))
                + ') values.')
        if np.min(state) < 0:
            raise ValueError(
                'The state must be given as a list of non-negative integers.')
        if np.sum(state) != self._nchannels:
            raise ValueError(
                'The number of channels in the state vector must equal '
                + str(self._nchannels) + '.')
        self._state = list(state)

    def state(self):
        """
        Returns the current simulation state.
        """
        return list(self._state)


class MarkovModel(object):
    """
    **Deprecated**: This class has been replaced by the classes
    :class:`LinearModel` and :class:`AnalyticalSimulation`. Please update your
    code to use these classes instead. This class will be removed in
    future versions of Myokit.
    """

    @staticmethod
    def from_component(
            component, states=None, parameters=None, current=None, vm=None):
        """
        Creates and returns an :class:`AnalyticalSimulation` using a
        :class:`LinearModel` based on a Myokit model component.
        """
        # Deprecated since 2016-01-25
        import warnings
        warnings.warn(
            'The method `MarkovModel.from_component` is deprecated.'
            ' Please use `LinearModel.from_component` instead.')
        return AnalyticalSimulation(LinearModel.from_component(
            component, states, parameters, current, vm))

    def __new__(self, model, states, parameters=None, current=None, vm=None):
        # Deprecated since 2016-01-25
        import warnings
        warnings.warn(
            'The `MarkovModel` class is deprecated.'
            ' Please use the `LinearModel` class instead.')
        return AnalyticalSimulation(LinearModel(
            model, states, parameters, current, vm))


class LinearModelError(myokit.MyokitError):
    """
    Raised for issues with constructing or using a :class:`LinearModel`.
    """


def _linear_combination(expression, variables):
    """
    Checks if ``expression`` is a linear combination of the given ``variables``
    and returns the multiplier for each variable.

    See :meth:`_linear_combination_terms` for details.
    """
    return _linear_combination_terms(_split_terms(expression), variables)


def _linear_combination_terms(terms, variables):
    """
    Checks if a list of terms forms linear combination of the given
    ``variables`` and returns the multiplier for each variable.

    If ``expression`` is a linear combination ``a1*v1 + a2*v2 + ...`` where
    ``vi`` is a variable in ``variables``, this method returns a list of
    expressions ``[a1, a2, ...]``. The expressions ``ai`` are not guaranteed to
    be constants, but won't contain any references to the variables in
    ``variables``.

    If the expression cannot be written as a linear combination a
    ``ValueError`` is raised.
    """
    # Multiplier for each variable
    multipliers = [None] * len(variables)

    # Check each term multiplies one of the variables
    for term in terms:
        # Split into name and multiplier
        name, multiplier = _split_factor(term, variables)

        # Update the variable's multiplier
        var = name.var()
        i = variables.index(var)
        if multipliers[i] is None:
            multipliers[i] = multiplier
        else:
            multipliers[i] = myokit.Plus(multipliers[i], multiplier)

    # Return obtained multipliers
    return multipliers


def _split_factor(term, variables):
    """
    Splits ``term`` into two parts that can be multiplied together, so that one
    part is a reference to a variable in ``variables``, and the other part has
    no references to variables in ``variables``.

    Returns a tuple ``(name, multiplier)`` where ``name`` is a
    :class:`myokit.Name` referencing a variable in the list ``variables``, and
    where ``multiplier`` is some other expression such that ``name*multiplier``
    is equivalent to the original term.

    If the term can't be split this way, a ``ValueError`` is raised.
    """

    # Check that the term references exactly one variable from ``variables``
    names = set([myokit.Name(var) for var in variables])
    refs = set(term.references())
    n_refs = len(names & refs)
    if n_refs != 1:
        raise ValueError(
            'The expression `term` must reference exactly one variable from'
            ' the list `variables` (found ' + str(n_refs) + ').')

    # Get Name of variable referenced in this term
    name = (names & refs).pop()

    # Split
    m = None
    positive = True
    while term != name:
        t = type(term)
        if t == myokit.PrefixPlus:
            term = term[0]
        elif t == myokit.PrefixMinus:
            positive = not positive
            term = term[0]
        elif t == myokit.Multiply:
            a, b = term
            if name in b.references():
                a, b = b, a
            term = a
            m = b if m is None else myokit.Multiply(m, b)
        elif t == myokit.Divide:
            a, b = term
            if name in b.references():
                raise ValueError(
                    'Non-linear function (division) of ' + str(name)
                    + ' found in ' + str(term) + '.')
            term = a
            m = myokit.Divide(myokit.Number(1) if m is None else m, b)
        elif t in (myokit.Plus, myokit.Minus):
            raise ValueError(
                'Expression passed to _split_factor must be a single term.')
        else:
            raise ValueError(
                'Non-linear function of ' + str(name) + ' found in '
                + str(term) + '.')

    # Finalise multiplier
    if m is None:
        m = myokit.Number(1)
    if not positive:
        m = myokit.PrefixMinus(m)

    # Return
    return name, m


def _split_terms(expression, terms=None, positive=True):
    """
    Takes an expression tree of :class:`myokit.Plus` and/or
    :class:`myokit.Minus` objects and splits it into terms.

    Arguments:

    ``expression``
        The expression to split.
    ``terms``
        Used internally: A list of terms to append to.
    ``positive``
        Used internally: If false, the terms will be multiplied by -1
        before adding.

    """
    if terms is None:
        terms = []
    if type(expression) == myokit.Plus:
        a, b = expression
        _split_terms(a, terms, positive)
        _split_terms(b, terms, positive)
    elif type(expression) == myokit.Minus:
        a, b = expression
        _split_terms(a, terms, positive)
        _split_terms(b, terms, not positive)
    elif type(expression) == myokit.PrefixPlus:
        _split_terms(expression[0], terms, positive)
    elif type(expression) == myokit.PrefixMinus:
        _split_terms(expression[0], terms, not positive)
    else:
        if positive:
            terms.append(expression)
        else:
            terms.append(myokit.PrefixMinus(expression))
    return terms


def find_markov_models(model):
    """
    Searches a :class:`myokit.Model` for groups of states that constitute a
    Markov model.

    Returns a list of lists, where the inner lists are groups of variables that
    form a Markov model together.

    Note that this method performs a shallow check of the equation shapes,
    and does not perform any simplification or rewriting to see if the
    expressions can be made to fit a Markov form.

    Arguments:

    ``model``
        The :class:`myokit.Model` to search.

    """

    # Models
    models = []

    # Scan model for clusters of states that depend on each other
    seen = set()
    for var in model.states():
        if var in seen:
            continue

        # Get references to other states, made by this state
        group = set(var.refs_to(True))

        # Find group of connected states
        todo = collections.deque(group)
        while todo:
            var = todo.popleft()
            for ref in set(var.refs_to(True)) - group:
                group.add(ref)
                todo.append(ref)

        # All these states now count as 'seen'
        seen |= group

        # Now check if there's a (1 - x1 - x2 - ...) variable:
        # First check if there's a non-state variable that depends on all of
        # these states.
        candidates = set()
        for var in group:
            for ref in var.refs_by(True):
                if set(ref.refs_to(True)) == group:
                    candidates.add(ref)
        candidates -= group

        # Now test the candidates for the correct form
        extra = set()
        for candidate in candidates:
            # Split into terms
            terms = _split_terms(candidate.rhs())

            # Find and remove the '1' term
            i_one = None
            for i, term in enumerate(terms):
                if term.is_constant() and term.eval() == 1:
                    i_one = i
                    break
            if i_one is None:
                continue
            del terms[i_one]

            # Remaining terms must be linear combination of the states in
            # group...
            try:
                factors = _linear_combination_terms(terms, list(group))
            except ValueError:
                continue

            # And each factor must be -1
            ok = True
            for factor in factors:
                if not (factor.is_constant() and factor.eval() == -1):
                    ok = False
                    break
            if not ok:
                continue

            # Passed all tests!
            extra.add(candidate)
        del candidates

        # At this point `extra` should be empty or a single variable, if not,
        # it's not a (normal) Markov model
        if len(extra) > 1:
            continue

        # Must have at least 2 states in total
        states = group | extra
        if len(states) < 2:
            continue

        # Get sorted list of states for output
        states = list(states)
        states.sort(key=lambda x: myokit.tools.natural_sort_key(x.qname()))

        # Check all members of `group` are a linear combination of states
        try:
            for state in group:
                _linear_combination(state.rhs(), states)
        except ValueError:
            continue

        # This looks like a Markov model!
        models.append(states)

    return models


def convert_markov_models_to_compact_form(model):
    """
    Scans a :class:`myokit.Model` for Markov models, and ensures they contain
    one state that's not evaluated as an ODE, but as ``1 - sum(x[i])``, where
    the sum is over all other states ``x[i]``.

    Arguments:

    ``model``
        The :class:`myokit.Model` to scan.

    Returns an updated :class:`myokit.Model`.
    """
    # Clone model
    model = model.clone()

    # Find markov models and convert
    for states in find_markov_models(model):

        # Check if a non-ODE state is already present
        if sum([1 for x in states if not x.is_state()]):
            continue

        # Update final state
        state = states[-1]
        state.demote()
        state.set_rhs('1 - ' + '-'.join([x.qname() for x in states[:-1]]))

    return model


def convert_markov_models_to_full_ode_form(model):
    """
    Scans a :class:`myokit.Model` for Markov models, and ensures they are
    written in a form where every Markov state is evaluated as an ODE.

    Arguments:

    ``model``
        The :class:`myokit.Model` to scan.

    Returns an updated :class:`myokit.Model`.
    """
    # Clone model
    model = model.clone()

    # Find markov models and convert
    for states in find_markov_models(model):

        # Find 1-sum() state
        special = None
        i_special = None
        for i, state in enumerate(states):
            if not state.is_state():
                special = state
                i_special = i
                break

        # No special state: then no need to convert
        if special is None:
            continue

        # Get initial value for special state
        initial_value = special.eval()

        # Gather terms for existing states, see which ones don't cancel out
        sum_of_terms = [[] for _ in states]
        for state in states:
            if state is special:
                continue

            factors = _linear_combination(state.rhs(), states)
            for i, factor in enumerate(factors):
                if factor is None:
                    continue

                # Split terms in factor, add each to sum_of_terms
                for term in _split_terms(factor):

                    # Get negative term
                    if isinstance(term, myokit.PrefixMinus):
                        negative = term[0]
                    else:
                        negative = myokit.PrefixMinus(term)

                    # If negative term is in list, then these cancel out and
                    # should be removed
                    try:
                        sum_of_terms[i].remove(negative)
                    except ValueError:
                        # Negative term isn't in the list, so add this factor
                        # to the list.
                        sum_of_terms[i].append(term)

        # Create RHS from remaining terms
        terms = []
        for i, sums in enumerate(sum_of_terms):
            if not sums:
                continue

            # Combine terms
            term = sums[0]
            for t in sums[1:]:
                term = myokit.Plus(term, t)

            # Negate
            if isinstance(term, myokit.PrefixMinus):
                term = term[0]
            else:
                term = myokit.PrefixMinus(term)

            # Multiply with state and store
            terms.append(myokit.Multiply(term, myokit.Name(states[i])))

        # Combine terms (should always be 2 or more).
        rhs = terms[0]
        for term in terms[1:]:
            rhs = myokit.Plus(rhs, term)

        # Update special state
        special.promote(initial_value)
        special.set_rhs(rhs)

    # Return cloned & updated model
    return model

