#
# Tools for working with Hodgkin-Huxley style ion channel models
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import numpy as np
import myokit


class HHModel(object):
    """
    Represents a Hodgkin-Huxley (HH)-style model of an ion channel, extracted
    from a :class:`myokit.Model`.

    The class assumes the HH model can be (re)written as::

        I = prod(x[i]**n[i]) * f(V, p)
        dot(x[i]) = (x_inf[i](V, p) - x[i]) / tau_x[i](V, p)

    for any number of states ``x[i]`` with steady-state ``x_inf[i]`` and time
    constant ``tau_x[i]``, where ``V`` is the membrane potential, ``p`` is a
    set of parameters, ``f`` is an arbitrary function (for example
    ``g_max * (V - E_rev)``).

    The model variables to treat as parameter are specified by the user when
    the model is created. Any other variables, for example state variables such
    as intercellular calcium or constants such as temperature, are fixed when
    the current model is created and can no longer be changed.

    The current variable is optional.

    Arguments:

    ``model``
        The :class:`myokit.Model` to extract a current model from.
    ``states``
        An ordered list of state variables (or state variable names) from
        ``model``. All remaining state variables will be frozen in place.
    ``parameters=None``
        A list of parameters to maintain in their symbolic form.
    ``current=None``
        The current model's current variable, or ``None``.
    ``vm=None``
        The variable indicating membrane potential. If set to ``None``
        (default) the method will search for a variable with the label
        ``membrane_potential``.

    Example::

        import myokit
        import myokit.lib.hh as hh

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

        # Extract an ion current model
        mm = hh.HHModel(model, states, parameters, current)

    Alternatively, a HHModel can be constructed based on a single component
    using the method :meth:`from_component() <HHModel.from_component()>`::

        import myokit
        import myokit.lib.hh as hh

        # Load a model from disk
        model = myokit.load_model('some-model.mmt')

        # Extract a markov model
        mm = hh.HHModel.from_component(model.get('ina'))

    """
    # NOTE: A HHModel must be immutable!
    # This ensures that the simulations don't have to clone it (which would be
    # costly and difficult).
    # A HHModel can return a function to calculate state values, but it never
    # updates its internal state in any way.
    def __init__(self, model, states, parameters=None, current=None, vm=None):
        super(HHModel, self).__init__()

        #
        # Check input
        #
        if not isinstance(model, myokit.Model):
            raise ValueError('First argument must be a myokit.Model.')

        # Check membrane potential variable is known, and is a qname
        if vm is None:
            vm = model.label('membrane_potential')
        if vm is None:
            raise HHModelError(
                'A membrane potential must be specified as `vm` or using the'
                ' label `membrane_potential`.')
        if isinstance(vm, myokit.Variable):
            vm = vm.qname()

        # Ensure all HH-states in the model are written in inf-tau form
        # This returns a clone of the original model
        self._model = convert_hh_states_to_inf_tau_form(model, vm)
        del model

        # Check and collect state variables
        self._states = []
        for state in states:
            if isinstance(state, myokit.Variable):
                state = state.qname()
            try:
                state = self._model.get(str(state), myokit.Variable)
            except KeyError:
                raise HHModelError('Unknown state: <' + str(state) + '>.')
            if not state.is_state():
                raise HHModelError(
                    'Variable <' + state.qname() + '> is not a state.')
            if state in self._states:
                raise HHModelError(
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
                raise HHModelError(
                    'Unknown parameter: <' + str(parameter) + '>.')
            if not parameter.is_literal():
                raise HHModelError(
                    'Unsuitable parameter: <' + str(parameter) + '>.')
            if parameter in unique:
                raise HHModelError(
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
                raise HHModelError('Current variable can not be a state.')
        self._current = current
        del current

        # Check membrane potential variable
        self._membrane_potential = self._model.get(vm)
        if self._membrane_potential in self._parameters:
            raise HHModelError(
                'Membrane potential should not be included in the list of'
                ' parameters.')
        if self._membrane_potential in self._states:
            raise HHModelError(
                'The membrane potential should not be included in the list of'
                ' states.')
        if self._membrane_potential == self._current:
            raise HHModelError(
                'The membrane potential should not be the current variable.')
        del vm

        #
        # Demote unnecessary states and remove bindings
        #
        # Get values of all states
        # Note: Do this _before_ changing the model!
        self._default_state = np.array([v.state_value() for v in self._states])

        # Freeze remaining, non-current-model states
        s = self._model.state()   # Get state values before changing anything!
        # Note: list() cast is required so that we iterate over a static list,
        # otherwise we can get issues because the iterator depends on the model
        # (which we're changing).
        for k, state in enumerate(list(self._model.states())):
            if state not in self._states:
                state.demote()
                state.set_rhs(s[k])

        # Unbind everything except time
        for label, var in self._model.bindings():
            if label != 'time':
                var.set_binding(None)

        # Check if current variable depends on selected states
        # (At this point, anything not dependent on the states is a constant)
        if self._current is not None and self._current.is_constant():
            raise HHModelError(
                'Current must be a function of the selected state variables.')

        # Ensure all states are written in inf-tau form
        for state in self._states:
            if not has_inf_tau_form(state, self._membrane_potential):
                raise HHModelError(
                    'State `' + state.qname() + '` must have "inf-tau form" or'
                    ' "alpha-beta form". See'
                    ' `myokit.lib.hh.has_inf_tau_form()` and'
                    ' `myokit.lib.hh.has_alpha_beta_form()`.'
                )

        #
        # Remove unused variables from internal model, and evaluate any
        # literals.
        #
        # 1. Make sure that current variable is maintained by temporarily
        #    setting it as a state variable.
        # 2. Similarly, make sure parameters and membrane potential are not
        #    evaluated and/or removed
        #
        self._membrane_potential.promote(0)
        if self._current is not None:
            self._current.promote(0)
        for p in self._parameters:
            p.promote(0)

        # Evaluate all constants and remove unused variables
        for var in self._model.variables(deep=True, const=True):
            var.set_rhs(var.rhs().eval())
        self._model.validate(remove_unused_variables=True)

        self._membrane_potential.demote()
        for p in self._parameters:
            p.demote()
        if self._current is not None:
            self._current.demote()

        # Validate modified model
        self._model.validate()

        #
        # Create functions
        #

        # Create a list of inputs to the functions
        self._inputs = [self._membrane_potential] + self._parameters

        # Get the default values for all inputs
        self._default_inputs = np.array([v.eval() for v in self._inputs])

        #
        # Create a function that calculates the states analytically
        #
        # The created self._function has signature _f(_y0, _t, v, params*)
        # and returns a tuple (states, current). If _t is a scalar, states is a
        # sequence of state values and current is a single current value. If _t
        # is a numpy array of times, states is a sequence of arrays, and
        # current is a numpy array. If no current variable is known current is
        # always None.
        #
        f = []
        args = ['_y0', '_t'] + [i.uname() for i in self._inputs]
        f.append('def _f(' + ', '.join(args) + '):')
        f.append('_y = [0]*' + str(len(self._states)))

        # Add equations to calculate all infs and taus
        w = myokit.numpy_writer()
        order = self._model.solvable_order()
        ignore = set(self._inputs + self._states + [self._model.time()])
        for group in order.values():
            for eq in group:
                var = eq.lhs.var()
                if var in ignore or var == self._current:
                    continue
                f.append(w.eq(eq))

        # Add equations to calculate updated state
        for k, state in enumerate(self._states):
            inf, tau = get_inf_and_tau(state, self._membrane_potential)
            inf = w.ex(myokit.Name(inf))
            tau = w.ex(myokit.Name(tau))
            k = str(k)
            f.append(
                '_y[' + k + '] = ' + state.uname() + ' = '
                + inf + ' + (_y0[' + k + '] - ' + inf
                + ') * numpy.exp(-_t / ' + tau + ')')

        # Add current calculation
        if self._current is not None:
            f.append('_i = ' + w.ex(self._current.rhs()))
        else:
            f.append('_i = None')

        # Add return statement and create python function from f
        f.append('return _y, _i')
        for i in range(1, len(f)):
            f[i] = '    ' + f[i]
        f = '\n'.join(f)
        #print(f)
        local = {}
        exec(f, {'numpy': np}, local)
        self._function = local['_f']

        #
        #
        # Create a function that calculates the steady states
        #
        #
        g = []
        args = [i.uname() for i in self._inputs]
        g.append('def _g(' + ', '.join(args) + '):')
        g.append('_y = [0]*' + str(len(self._states)))
        for k, state in enumerate(self._states):
            k = str(k)
            inf, tau = get_inf_and_tau(state, self._membrane_potential)
            inf = inf.rhs().clone(expand=True, retain=self._inputs)
            g.append('_y[' + str(k) + '] = ' + w.ex(inf))

        # Create python function from g
        g.append('return _y')
        for i in range(1, len(g)):
            g[i] = '    ' + g[i]
        g = '\n'.join(g)
        local = {}
        exec(g, {'numpy': np}, local)
        self._steady_state_function = local['_g']

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
        return self._default_inputs[0]

    def default_parameters(self):
        """
        Returns this markov model's default parameter values
        """
        return list(self._default_inputs[1:])

    def default_state(self):
        """
        Returns this markov model's default state values.
        """
        return list(self._default_state)

    @staticmethod
    def from_component(
            component, states=None, parameters=None, current=None, vm=None):
        """
        Creates a current model from a component, using the following rules:

          1. Every state in the component is a state in the current model.
          2. Every (non-nested) constant in the component is a parameter.
          3. The component should contain exactly one non-nested intermediary
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
                raise HHModelError(
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
                raise HHModelError(
                    'The model must define a variable labeled as'
                    ' "membrane_potential".')

        # Create and return LinearModel
        return HHModel(model, states, parameters, current, vm)

    def function(self):
        """
        Returns a function that evaluates the state values at any time.

        The returned function has the signature::

            f(y0, t, p1, p2, p3, ..., V) --> (states, current)

        where ``y0`` is a sequence containing the state values at time 0, where
        ``t`` is a scalar or numpy array of times at which to evaluate, where
        ``p1, p2, p3, ...`` are the model parameters, and where ``V`` is the
        membrane potential.

        The function output is always a tuple ``(states, current)``. If ``t``
        is a single time, then ``states`` will be a list of values (one per
        model state) and current will be a scalar (or ``None`` if no current
        variable was specified). If ``t`` is a numpy array of times then
        ``states`` will be a list of numpy arrays, and current will be a numpy
        array (or ``None`` if no current variable was specified).
        """
        return self._function

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

    def _parse_inputs(self, membrane_potential, parameters):
        """
        Returns a list of inputs based on the given V and parameters. If either
        is ``None`` it will be replaced by the default values.
        """
        inputs = list(self._default_inputs)
        if membrane_potential is not None:
            inputs[0] = float(membrane_potential)
        if parameters is not None:
            if len(parameters) != len(self._parameters):
                raise ValueError(
                    'Illegal parameter vector size: '
                    + str(len(self._parameters)) + ' required, '
                    + str(len(parameters)) + ' provided.')
            inputs[1:] = [float(x) for x in parameters]
        return inputs

    def reduced_model(self):
        """
        Returns a reduced :class:`myokit.Model`, containing only the parts
        necessary to calculate the specified states and current.
        """
        return self._model.clone()

    def states(self):
        """
        Returns the names of the state variables used by this model.
        """
        return [v.qname() for v in self._states]

    def steady_state(self, membrane_potential=None, parameters=None):
        """
        Returns the steady state solution for this model.

        Arguments:

        ``membrane_potential``
            The value to use for the membrane potential, or ``None`` to use the
            value from the original :class:`myokit.Model`.
        ``parameters``
            The values to use for the parameters, given in the order they were
            originally specified in (if the model was created using
            :meth:`from_component()`, this will be alphabetical order), or
            ``None`` to use the values from the original model.

        Returns a list of steady state values.
        """
        inputs = self._parse_inputs(membrane_potential, parameters)
        return self._steady_state_function(*inputs)


class AnalyticalSimulation(object):
    """
    Analytically evaluates a :class:`HHModel`'s state for a given set of points
    in time.

    Each simulation object maintains an internal state consisting of

    * The current simulation time
    * The current state
    * The default state

    When a simulation is created, the simulation time is set to zero and both
    the current and default state are initialized using the :class:`HHModel`.
    After each call to :meth:`run()` the time and current state are updated,
    so that each successive call to run continues where the previous simulation
    left off.

    A :class:`protocol <myokit.Protocol>` can be used to set the membrane
    potential during the simulation, or the membrane potential can be adjusted
    manually between runs.

    Example::

        import myokit
        import myokit.lib.hh as hh

        # Create an ion current model
        m = myokit.load_model('luo-1991.mmt')
        m = hh.HHModel.from_component(m.get('ina'))

        # Create an analytical simulation object
        s = hh.AnalyticalSimulation(m)

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
        if not isinstance(model, HHModel):
            raise ValueError('First parameter must be a `HHModel`.')
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

        # Get function
        self._function = self._model.function()

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

    def default_state(self):
        """
        Returns the default state used by this simulation.
        """
        return list(self._default_state)

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
        if np.any(state < 0) or np.any(state > 1):
            raise ValueError(
                'All states must be in the range [0, 1].')
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

    def set_state(self, state):
        """
        Changes the initial state used by in this simulation.
        """
        state = np.array(state, copy=True, dtype=float)
        if len(state) != len(self._state):
            raise ValueError(
                'Wrong size state vector, expecing (' + str(len(self._state))
                + ') values.')
        if np.any(state < 0) or np.any(state > 1):
            raise ValueError(
                'All states must be in the range [0, 1].')
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
        states, current = self._function(
            self._state,
            times,
            self._membrane_potential,
            *self._parameters
        )

        # Calculate states or states + current
        states = np.array(states)
        if self._has_current:
            return states, current
        else:
            return states

    def state(self):
        """
        Returns the initial state used by this simulation.
        """
        return list(self._state)


def convert_hh_states_to_inf_tau_form(model, v=None):
    """
    Scans a :class:`myokit.Model` for Hodgkin-Huxley style states written in
    "alpha-beta form", and converts them to "inf-tau form".

    For any state ``x`` written in the form
    ``dot(x) = alpha * (1 - x) - beta * x`` this method will calculate the
    steady state and time constant, and add variables for both. Next, the state
    RHS will be replaced by an expression of the form
    ``dot(x) = (x_inf - x) / tau_x``, where ``x_inf`` and ``tau_x`` are the
    new variables.

    See also: :meth:`get_alpha_and_beta()`.

    Arguments:

    ``model``
        A :class:`myokit.Model` object to convert.
    ``v``
        An optional :class:`myokit.Variable`` representing the membrane
        potential. If not given, the method will search for a variable labelled
        ``membrane_potential``. An error is raised if no membrane potential
        variable can be found.

    Returns an updated copy of the given model.
    """
    # Clone the model before editing
    if not isinstance(model, myokit.Model):
        raise ValueError('Given `model` must be a myokit.Model.')
    model = model.clone()

    # Check membrane potential variable is known.
    if v is None:
        v = model.label('membrane_potential')
        if v is None:
            raise ValueError(
                'Membrane potential must be given as `v` or by setting the'
                ' label `membrane_potential` in the model.')
    else:
        # Ensure v is a variable, and from the cloned model
        if isinstance(v, myokit.Variable):
            v = v.qname()
        v = model.get(v)

    # Loop over states
    # - If they're in alpha-beta form, add new (nested) variables inf and tau
    for x in model.states():
        res = get_alpha_and_beta(x, v)
        if res is not None:
            # Create variabless for inf and tau
            a = myokit.Name(res[0])
            b = myokit.Name(res[1])
            tau = x.add_variable_allow_renaming('tau')
            tau.set_rhs(myokit.Divide(myokit.Number(1), myokit.Plus(a, b)))
            inf = x.add_variable_allow_renaming('inf')
            inf.set_rhs(myokit.Multiply(a, myokit.Name(tau)))

            # Update RHS expression for state
            x.set_rhs(myokit.Divide(
                myokit.Minus(myokit.Name(inf), myokit.Name(x)),
                myokit.Name(tau)
            ))

    return model


def get_alpha_and_beta(x, v=None):
    """
    Tests if the given ``x`` is a state variable with an expression of the form
    ``(1 - x) * alpha - x * beta``, and returns the variables for ``alpha`` and
    ``beta`` if so.

    Here, ``alpha(v)`` and ``beta(v)`` represent the forward and backward
    reaction rates for ``x``. Both may depend on ``v``, but not on any (other)
    state variable.

    Note that this method performs a shallow check of the equation's shape,
    and does not perform any simplification or rewriting to see if the
    expression can be made to fit the required form.

    Arguments:

    ``x``
        The :class:`myokit.Variable` to check.
    ``v``
        An optional :class:`myokit.Variable` representing the membrane
        potential. If not given, the label ``membrane_potential`` will be used
        to determine ``v``. If ``v=None`` and no membrane potential can be
        found an error will be raised. Membrane potential is typically
        specified as a state, but this is not a requirement.

    Returns a tuple ``(alpha, beta)`` if successful, or ``None`` if not. Both
    ``alpha`` and ``beta`` are :class:`myokit.Variable` objects.

    """
    #TODO: This method _could_ perhaps be made to allow arbitrary inline
    # expressions for alpha and beta, so that it would recognise that e.g.
    # (1 - x) * 0.5 - x * log(3) is suitable. Guessing this could work if you
    # collected x terms to get e1 - e2 * x, and then use e1 = alpha, and
    # e2 = alpha + beta = e1 + beta; beta = e2 - e1.
    # We could then add new variables for alpha and beta, and return those.

    # Check that ``x`` is a state
    if not x.is_state():
        return None

    # Check shape of RHS is (1 - x) * alpha - beta * x
    rhs = x.rhs()
    if not isinstance(rhs, myokit.Minus):
        return None
    a, b = rhs
    if not (isinstance(a, myokit.Multiply) and isinstance(b, myokit.Multiply)):
        return None

    # Test alpha
    xname = myokit.Name(x)
    xconv = myokit.Minus(myokit.Number(1), xname)
    if a[0] == xconv:
        alpha = a[1]
    elif a[1] == xconv:
        alpha = a[0]
    else:
        return None

    # ...and beta
    if b[0] == xname:
        beta = b[1]
    elif b[1] == xname:
        beta = b[0]
    else:
        return None

    # Check that alpha and beta are variable references
    if not (isinstance(alpha, myokit.Name) and isinstance(beta, myokit.Name)):
        return None

    # Check that alpha and beta are not states
    alpha = alpha.var()
    beta = beta.var()
    if alpha.is_state() or beta.is_state():
        return None

    # Check that, with the possible exception of v, alpha and beta don't depend
    # on any states

    # Get model from state varible
    model = x.model()

    # Check membrane potential variable is known.
    if v is None:
        v = model.label('membrane_potential')
    else:
        # Ensure v is a variable, and from the cloned model
        if isinstance(v, myokit.Variable):
            v = v.qname()
        v = model.get(v)
    if v is None:
        raise ValueError(
            'Membrane potential must be given as `v` or by setting the'
            ' label `membrane_potential` in the model.')

    # Check alpha and beta
    for term in (alpha, beta):

        # Get rhs, with any references to other variables inlined
        rhs = term.rhs().clone(expand=True, retain=(v, ))

        # Check that alpha and beta are not functions of any states (with the
        # possible exception of v).
        for state in model.states():
            if state != v and rhs.depends_on(myokit.Name(state)):
                return None

    # Looks good!
    return (alpha, beta)


def get_inf_and_tau(x, v=None):
    """
    Tests if the given ``x`` is a state variable with an expression of the form
    ``(x_inf - x) / tau_x``, and returns the variables for ``x_inf`` and
    ``x_tau`` if so.

    Here, ``x_inf`` and ``tau_x`` represent the steady-state and time
    constant of ``x``. Both may depend on ``v``, but not on any (other) state
    variable.

    Note that this method performs a shallow check of the equation's shape,
    and does not perform any simplification or rewriting to see if the
    expression can be made to fit the required form.

    Arguments:

    ``x``
        The :class:`myokit.Variable` to check.
    ``v``
        An optional :class:`myokit.Variable` representing the membrane
        potential. If not given, the label ``membrane_potential`` will be used
        to determine ``v``. If ``v=None`` and no membrane potential can be
        found an error will be raised. Membrane potential is typically
        specified as a state, but this is not a requirement.

    Returns:

    A tuple ``(x_inf, tau_x)`` if successful, or ``None`` if not. The returned
    ``x_inf`` and ``tau_x`` are :class:`myokit.Variable` objects.

    """
    #TODO: This method _could_ perhaps be made to accept any expression that
    # can be written in the form ``e1 - x / e2``, so that e2 = tau, and
    # e1*e2 = inf.
    # We could then add new variables for tau and inf, and return those.

    # Check that ``x`` is a state
    if not x.is_state():
        return None

    # Check shape of RHS is (x_inf - x) / tau_x
    rhs = x.rhs()
    if not isinstance(rhs, myokit.Divide):
        return None
    numer, xtau = rhs
    if not isinstance(xtau, myokit.Name):
        return None
    if not isinstance(numer, myokit.Minus):
        return None
    xinf, xname = numer
    if not (isinstance(xinf, myokit.Name) and isinstance(xname, myokit.Name)):
        return None
    if not xname == myokit.Name(x):
        return None

    # Check that inf and tau are not states
    xinf = xinf.var()
    xtau = xtau.var()
    if xinf.is_state() or xtau.is_state():
        return None

    # Check that, with the possible exception of v, xinf and xtau do not depend
    # on any states
    # Get model from state varible
    model = x.model()

    # Check membrane potential variable is known.
    if v is None:
        v = model.label('membrane_potential')
    else:
        # Ensure v is a variable, and from the cloned model
        if isinstance(v, myokit.Variable):
            v = v.qname()
        v = model.get(v)
    if v is None:
        raise ValueError(
            'Membrane potential must be given as `v` or by setting the'
            ' label `membrane_potential` in the model.')

    # Check xinf and xtau
    for term in (xinf, xtau):

        # Get rhs, with any references to other variables inlined
        rhs = term.rhs().clone(expand=True, retain=(v,))

        # Check if x_inf and tau_x are not functions of any states (with
        # the possible exception of v).
        for state in model.states():
            if state != v and rhs.depends_on(myokit.Name(state)):
                return None

    # Looks good!
    return xinf, xtau


def get_rl_expression(x, dt, v=None):
    """
    For states ``x`` with RHS expressions written in the "inf-tau form" (see
    :meth:`has_inf_tau_form`) this returns a Rush-Larsen (RL) update expression
    of the form ``x_inf + (x - x_inf) * exp(-(dt / tau_x))``.

    If the state does not have the "inf-tau form", ``None`` is returned.

    Arguments:

    ``x``
        A state variable for which to return the RL update expression.
    ``dt``
        A :class:`myokit.Name` expression to use for the time step in the RL
        expression.
    ``v``
        An optional variable representing the membrane potential.

    Returns a :class:`myokit.Expression` if succesful, or ``None`` if not.

    Example:

        # Load a Myokit model
        model = myokit.load_model('example')
        v = model.get('membrane.V')

        # Get a copy where all HH-state variables are written in inf-tau form
        model = myokit.lib.hh.convert_hh_states_to_inf_tau_form(model, v)

        # Create an expression for the time step
        dt = myokit.Name('dt')

        # Show an RL-update for the variable ina.h
        h = model.get('ina.h')
        e = myokit.lib.hh.get_rl_expression(h, dt, v)
        print('h[t + dt] = ' + str(e))

    See:

    [1] Rush, Larsen (1978) A Practical Algorithm for Solving Dynamic Membrane
    Equations. IEEE Transactions on Biomedical Engineering,
    https://doi.org/10.1109/TBME.1978.326270

    [2] Marsh, Ziaratgahi, Spiteri (2012) The secrets to the success of the
    Rush-Larsen method and its generalization. IEEE Transactions on Biomedical
    Engineering, https://doi.org/10.1109/TBME.2012.2205575

    """
    # Test dt is an expression
    if not isinstance(dt, myokit.Expression):
        raise ValueError('Argument `dt` must be a myokit.Expression.')

    # Get x_inf and tau_x, if possible
    res = get_inf_and_tau(x, v)
    if res is None:
        return None

    # Create expression for RL update
    # x_inf + (x - x_inf) * exp(-(dt / tau_x))
    x = myokit.Name(x)
    x_inf = myokit.Name(res[0])
    tau_x = myokit.Name(res[1])
    return myokit.Plus(
        x_inf,
        myokit.Multiply(
            myokit.Minus(x, x_inf),
            myokit.Exp(myokit.PrefixMinus(myokit.Divide(dt, tau_x)))
        )
    )


def has_alpha_beta_form(x, v=None):
    """
    Tests if the given ``x`` is a state variable with an expression of the form
    ``(1 - x) * alpha - x * beta``, where ``alpha`` and ``beta`` represent the
    forward and backward reaction rates for ``x``.

    If the optional argument ``v`` is given, the method will (1) check that
    both ``alpha`` and ``beta`` depend on ``v``, and (2) check that they don't
    depend on any state variables (not counting ``v``).

    Note that this method performs a shallow check of the equation's shape,
    and does not perform any simplification or rewriting to see if the
    expression can be made to fit the required form.

    Arguments:

    ``x``
        The :class:`myokit.Variable` to check.
    ``v``
        An optional :class:`myokit.Variable` representing the membrane
        potential.

    Returns ``True`` if the alpha-beta form is found, ``False`` if not.
    """
    try:
        alpha, beta = get_alpha_and_beta(x, v)
        return True
    except TypeError:
        return False


def has_inf_tau_form(x, v=None):
    """
    Tests if the given ``x`` is a state variable with an expression of the form
    ``(x_inf - x) / tau_x``, where ``x_inf`` and ``tau_x`` represent the
    steady-state and time constant of ``x``.

    If the optional argument ``v`` is given, the method will (1) check that
    both ``x_inf`` and ``tau_x`` depend on ``v``, and (2) check that they don't
    depend on any state variables (not counting ``v``).

    Note that this method performs a shallow check of the equation's shape,
    and does not perform any simplification or rewriting to see if the
    expression can be made to fit the required form.

    Arguments:

    ``x``
        The :class:`myokit.Variable` to check.
    ``v``
        An optional :class:`myokit.Variable` representing the membrane
        potential.

    Returns ``True`` if the inf-tau form is found, ``False`` if not.
    """
    try:
        x_inf, tau_x = get_inf_and_tau(x, v)
        return True
    except TypeError:
        return False


class HHModelError(myokit.MyokitError):
    """
    Raised for issues with constructing or using a :class:`LinearModel`.
    """

