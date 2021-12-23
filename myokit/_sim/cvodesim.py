#
# CVODE-driven single cell simulation
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import myokit
import platform

# Location of C template
SOURCE_FILE = 'cvodesim.c'


class Simulation(myokit.CModule):
    """
    Runs single cell simulations using the CVODE solver (see [1]); CVODE uses
    an implicit multi-step method to achieve high accuracy and stability with
    adaptive step sizes.

    The model passed to the simulation is cloned and stored internally, so
    changes to the original model object will not affect the simulation. A
    protocol can be passed in as ``protocol`` or set later using
    :meth:`set_protocol`.

    Simulations maintain an internal state consisting of

    - the current simulation time
    - the current state
    - the default state

    When a simulation is created, the simulation time is set to 0 and both the
    current and the default state are copied from the model.
    After each call to :meth:`Simulation.run` the time variable and current
    state are updated, so that each successive call to run continues where the
    previous simulation left off. A :meth:`reset` method is provided that will
    set the time back to 0 and revert the current state to the default state.
    To change the time or state manually, use :meth:`set_time` and
    :meth:`set_state`.

    A pre-pacing method :meth:`pre` is provided that doesn't affect the
    simulation time but will update the current *and the default state*. This
    allows you to pre-pace, run a simulation, reset to the pre-paced state, run
    another simulation etc.

    To get action potential duration (APD) measurements, the simulation can be
    run with threshold crossing detection. To enable this, the membrane
    potential variable *must* be specified when the simulation is created using
    the ``apd_var`` argument. This can be either a variable object or a string
    containing the variable's fully qualified name. When running a simulation a
    threshold value can be passed in. In addition to the usual simulation log
    the run method will then return a list of all times at which ``apd_var``
    crossed the threshold. *Please note this is an APD calculated as the time
    between the crossing of a fixed threshold, it does not calculate dynamic
    thresholds like "90% of max(V) - min(V)".*

    The simulation provides four inputs a model variable can be bound to:

    ``time``
        This input provides the simulation time.
    ``pace``
        This input provides the current value of the pacing variable. This is
        determined using the protocol passed into the Simulation.
    ``evaluations``
        This input provides the number of rhs evaluations used at each point in
        time and can be used to gain some insight into the solver's behaviour.
    ``realtime``
        This input provides the elapsed system time at each logged point.

    No variable labels are required for this simulation type.

    [1] SUNDIALS: Suite of nonlinear and differential/algebraic equation
    solvers. Hindmarsh, Brown, Woodward, et al. (2005) ACM Transactions on
    Mathematical Software.

    """
    _index = 0  # Simulation id

    def __init__(self, model, protocol=None, apd_var=None):
        super(Simulation, self).__init__()

        # Require a valid model
        if not model.is_valid():
            model.validate()
        model = model.clone()
        self._model = model

        # Set protocol
        self._protocol = None
        self._fixed_form_protocol = None
        self.set_protocol(protocol)

        # Check potential and threshold values
        if apd_var is None:
            self._apd_var = None
        else:
            if isinstance(apd_var, myokit.Variable):
                apd_var = apd_var.qname()
            self._apd_var = self._model.get(apd_var)
            if not self._apd_var.is_state():
                raise ValueError('The `apd_var` must be a state variable.')

        # Get state and default state from model
        self._state = self._model.state()
        self._default_state = list(self._state)

        # Last state reached before error
        self._error_state = None

        # Starting time
        self._time = 0

        # Unique simulation id
        Simulation._index += 1
        module_name = 'myokit_sim_' + str(Simulation._index)
        module_name += '_' + str(myokit.pid_hash())

        # Arguments
        args = {
            'module_name': module_name,
            'model': self._model,
            'potential': self._apd_var,
        }
        fname = os.path.join(myokit.DIR_CFUNC, SOURCE_FILE)

        # Define libraries
        libs = [
            'sundials_cvode',
            'sundials_nvecserial',
        ]
        if platform.system() != 'Windows':  # pragma: no windows cover
            libs.append('m')

        # Define library paths
        # Note: Sundials path on windows already includes local binaries
        libd = list(myokit.SUNDIALS_LIB)
        incd = list(myokit.SUNDIALS_INC)
        incd.append(myokit.DIR_CFUNC)

        # Create extension
        self._sim = self._compile(module_name, fname, args, libs, libd, incd)

        # Set default tolerance values
        self._tolerance = None
        self.set_tolerance()

        # Set default min and max step size
        self._dtmax = self._dtmin = None

    def default_state(self):
        """
        Returns the default state.
        """
        return list(self._default_state)

    def last_state(self):
        """
        If the last simulation resulted in an error, this will return the last
        state reached during that simulation. In all other cases, this method
        will return ``None``.
        """
        return list(self._error_state) if self._error_state else None

    def eval_derivatives(self, y=None):
        """
        Evaluates and returns the state derivatives.

        The state to evaluate for can be given as ``y``. If no state is given
        the current simulation state is used.
        """
        if y is None:
            y = list(self._state)
        else:
            y = self._model.map_to_state(y)
        dy = list(self._state)
        self._sim.eval_derivatives(y, dy, 0, 0)
        return dy

    def last_number_of_evaluations(self):
        """
        Returns the number of rhs evaluations performed by the solver during
        the last simulation.
        """
        return self._sim.number_of_evaluations()

    def last_number_of_steps(self):
        """
        Returns the number of steps taken by the solver during the last
        simulation.
        """
        return self._sim.number_of_steps()

    def pre(self, duration, progress=None, msg='Pre-pacing Simulation'):
        """
        This method can be used to perform an unlogged simulation, typically to
        pre-pace to a (semi-)stable orbit.

        After running this method

        - The simulation time is **not** affected
        - The current state and the default state are updated to the final
          state reached in the simulation.

        Calls to :meth:`reset` after using :meth:`pre` will set the current
        state to this new default state.

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as `msg`.
        """
        duration = float(duration)
        self._run(duration, myokit.LOG_NONE, None, None, None, progress, msg)
        self._default_state = self._state

    def __reduce__(self):
        """
        Pickles this Simulation.

        See: https://docs.python.org/3/library/pickle.html#object.__reduce__
        """
        apd_var = None if self._apd_var is None else self._apd_var.qname()
        return (
            self.__class__,
            (self._model, self._protocol, apd_var),
            (
                self._time,
                self._state,
                self._default_state,
                self._fixed_form_protocol,
                self._tolerance,
                self._dtmin,
                self._dtmax,
            ),
        )

    def reset(self):
        """
        Resets the simulation:

        - The time variable is set to 0
        - The state is set to the default state

        """
        self._time = 0
        self._state = list(self._default_state)

    def run(
            self, duration, log=None, log_interval=None, log_times=None,
            apd_threshold=None, progress=None, msg='Running simulation'):
        """
        Runs a simulation and returns the logged results. Running a simulation
        has the following effects:

        - The internal state is updated to the last state in the simulation.
        - The simulation's time variable is updated to reflect the time
            elapsed during the simulation.

        The number of time units to simulate can be set with ``duration``.

        The method returns a :class:`myokit.DataLog` dictionary that maps
        variable names to lists of logged values. The variables to log can be
        indicated using the ``log`` argument. There are several options for its
        value:

        - ``None`` (default), to log all states.
        - An integer flag or a combination of flags. Options:
          ``myokit.LOG_NONE``, ``myokit.LOG_STATE``, ``myokit.LOG_BOUND``,
          ``myokit.LOG_INTER``, ``myokit.LOG_DERIV`` or ``myokit.LOG_ALL``.
        - A sequence of variable names. To log derivatives, use
          "dot(membrane.V)".
        - A :class:`myokit.DataLog` object. In this case, the new data
          will be appended to the existing log.

        For detailed information about the ``log`` argument, see the function
        :meth:`myokit.prepare_log`.

        By default, every step the solver takes is logged. This is usually
        advantageous, since more points are added exactly at the times the
        system gets more interesting. However, if equidistant points are
        required a ``log_interval`` can be set. Alternatively, the
        ``log_times`` argument can be used to specify logging times directly.

        To obtain accurate measurements of the action potential (AP) duration,
        the argument ``apd_threshold`` can be set to a fixed threshold level
        used to define the AP. This functionality is only available for
        simulations created with a valid ``apd_var`` argument. If apd
        measurements are enabled, the value returned by this method has the
        form ``(log, apds)``.

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as ``msg``.

        The ``duration`` argument cannot be negative, and special care needs to
        be taken when very small (positive) values are used. If ``duration`` is
        zero or so small that
        ``simulation.time() + duration == simulation.time()``, then the method
        returns without updating the internal states or time. However, for
        some extremely short durations (approx ``2 epsilon * time``), the
        simulation will try to run but the underlying CVODE engine may return a
        ``CV_TOO_CLOSE`` error, causing a :class:`myokit.SimulationError` to be
        raised.
        """
        duration = float(duration)
        output = self._run(
            duration, log, log_interval, log_times, apd_threshold, progress,
            msg)
        self._time += duration
        return output

    def _run(
            self, duration, log, log_interval, log_times, apd_threshold,
            progress, msg):

        # Reset error state
        self._error_state = None

        # Simulation times
        if duration < 0:
            raise ValueError('Simulation time can\'t be negative.')
        tmin = self._time
        tmax = tmin + duration

        # Parse log argument
        log = myokit.prepare_log(log, self._model, if_empty=myokit.LOG_ALL)

        # Logging period (None or 0 = disabled)
        log_interval = 0 if log_interval is None else float(log_interval)
        if log_interval < 0:
            log_interval = 0

        # Logging points (None or empty list = disabled)
        if log_times is not None:
            log_times = [float(x) for x in log_times]
            if len(log_times) == 0:
                log_times = None
            else:
                # Allow duplicates, but always non-decreasing!
                import numpy as np
                x = np.asarray(log_times)
                if np.any(x[1:] < x[:-1]):
                    raise ValueError(
                        'Values in log_times must be non-decreasing.')
                del(x, np)
        if log_times is not None and log_interval > 0:
            raise ValueError(
                'The arguments log_times and log_interval cannot be used'
                ' simultaneously.')

        # Threshold for APD measurement
        root_list = None
        root_threshold = 0
        if apd_threshold is not None:
            if self._apd_var is None:
                raise ValueError(
                    'Threshold given but Simulation object was'
                    ' created without apd_var argument.')
            else:
                root_list = []
                root_threshold = float(apd_threshold)

        # Get progress indication function (if any)
        if progress is None:
            progress = myokit._Simulation_progress
        if progress:
            if not isinstance(progress, myokit.ProgressReporter):
                raise ValueError(
                    'The argument "progress" must be either a'
                    ' subclass of myokit.ProgressReporter or None.')

        # Determine benchmarking mode, create time() function if needed
        if self._model.binding('realtime') is not None:
            import timeit
            bench = timeit.default_timer
        else:
            bench = None

        # Run simulation
        # The simulation is run only if (tmin + duration > tmin). This is a
        # stronger check than (duration == 0), which will return true even for
        # very short durations (and will cause zero iterations of the
        # "while (t < tmax)" loop below).
        istate = list(self._state)
        if tmin + duration > tmin:

            # Lists to return state in
            rstate = list(istate)
            rbound = [0, 0, 0, 0]  # time, pace, realtime, evaluations

            # Initialize
            self._sim.sim_init(
                tmin,
                tmax,
                istate,
                rstate,
                rbound,
                self._protocol,
                self._fixed_form_protocol,
                log,
                log_interval,
                log_times,
                root_list,
                root_threshold,
                bench,
            )
            t = tmin

            try:
                if progress:
                    # Loop with feedback
                    with progress.job(msg):
                        r = 1.0 / duration if duration != 0 else 1
                        while t < tmax:
                            t = self._sim.sim_step()
                            if not progress.update(min((t - tmin) * r, 1)):
                                raise myokit.SimulationCancelledError()
                else:
                    # Loop without feedback
                    while t < tmax:
                        t = self._sim.sim_step()
            except ArithmeticError as e:
                # Some CVODE errors are set to raise an ArithmeticError,
                # which users may be able to debug.
                self._error_state = list(rstate)
                txt = ['A numerical error occurred during simulation at'
                       ' t = ' + str(t) + '.', 'Last reached state: ']
                txt.extend(['  ' + x for x in
                            self._model.format_state(rstate).splitlines()])
                txt.append('Inputs for binding: ')
                txt.append('  time        = ' + myokit.float.str(rbound[0]))
                txt.append('  pace        = ' + myokit.float.str(rbound[1]))
                txt.append('  realtime    = ' + myokit.float.str(rbound[2]))
                txt.append('  evaluations = ' + myokit.float.str(rbound[3]))
                txt.append(str(e))
                try:
                    self._model.evaluate_derivatives(rstate)
                except myokit.NumericalError as en:
                    txt.append(str(en))
                raise myokit.SimulationError('\n'.join(txt))
            except Exception as e:

                # Store error state
                self._error_state = list(rstate)

                # Check for known CVODE errors
                if 'Function CVode()' in str(e):
                    raise myokit.SimulationError(str(e))

                # Check for zero step error
                if str(e)[:10] == 'ZERO_STEP ':  # pragma: no cover
                    t = float(str(e)[10:])
                    raise myokit.SimulationError(
                        'Maximum number of zero-size steps made at t='
                        + str(t))

                # Unknown exception: re-raise!
                raise
            finally:
                # Clean even after KeyboardInterrupt or other Exception
                self._sim.sim_clean()

            # Update internal state
            self._state = rstate

        # Return
        if root_list is not None:
            # Calculate apds and return (log, apds)
            st = []
            dr = []
            if root_list:
                roots = iter(root_list)
                time, direction = next(roots)
                tlast = time if direction > 0 else None
                for time, direction in roots:
                    if direction > 0:
                        tlast = time
                    else:
                        st.append(tlast)
                        dr.append(time - tlast)
            apds = myokit.DataLog()
            apds['start'] = st
            apds['duration'] = dr
            return log, apds
        else:
            # Return log
            return log

    def set_constant(self, var, value):
        """
        Changes a model constant. Only literal constants (constants not
        dependent on any other variable) can be changed.

        The constant ``var`` can be given as a :class:`Variable` or a string
        containing a variable qname. The ``value`` should be given as a float.
        """
        value = float(value)
        if isinstance(var, myokit.Variable):
            var = var.qname()
        var = self._model.get(var)
        if not var.is_literal():
            raise ValueError(
                'The given variable <' + var.qname() + '> is not a literal.')

        # Update value in internal model: This is required for error handling
        # (to show the correct values), but also takes care of constants in
        # pickled/unpickled simulations.
        self._model.set_value(var.qname(), value)

        # Update value in compiled simulation module
        self._sim.set_constant(var.qname(), value)

    def set_default_state(self, state):
        """
        Allows you to manually set the default state.
        """
        self._default_state = self._model.map_to_state(state)

    def set_max_step_size(self, dtmax=None):
        """
        Sets a maximum step size. To let the solver pick any step size it likes
        use ``dtmax = None``.
        """
        dtmax = 0 if dtmax is None else float(dtmax)
        if dtmax < 0:
            dtmax = 0

        # Store internally
        self._dtmax = dtmax

        # Set in simulation
        self._sim.set_max_step_size(dtmax)

    def set_min_step_size(self, dtmin=None):
        """
        Sets a minimum step size. To let the solver pick any step size it likes
        use ``dtmin = None``.
        """
        dtmin = 0 if dtmin is None else float(dtmin)
        if dtmin < 0:
            dtmin = 0

        # Store internally
        self._dtmin = dtmin

        # Set in simulation
        self._sim.set_min_step_size(dtmin)

    def set_fixed_form_protocol(self, times=None, values=None):
        """
        Configures this simulation to run with a predetermined protocol
        instead of the usual event-based mechanism.

        A 1D time-series should be given as input. During the simulation, the
        value of the pacing variable will be determined by linearly
        interpolating between the two nearest points in the series. If the
        simulation time is outside the bounds of the time-series, the first or
        last value in the series will be used.

        Setting a predetermined protocol clears any previously set (event-based
        or pre-determined) protocol. To clear all protocols, call this method
        with `times=None`. When a simulation is run without any protocol, the
        value of any variables bound to `pace` will be set to 0.

        Arguments:

        ``times``
            A non-decreasing array of times. If any times appear more than
            once, only the value at the highest index will be used.
        ``values``
            An array of values for the pacing variable. Must have the same size
            as ``times``.

        """
        # Check input
        if times is None:
            if values is not None:
                raise ValueError('Values array given, but no times array.')
        else:
            if values is None:
                raise ValueError('Times array given, but no values array.')
            if len(times) != len(values):
                raise ValueError('Times and values array must have same size.')

        # Clear event-based protocol, if set
        self._protocol = None

        # Set new protocol
        if times is None:
            # Clear predetermined protocol
            self._fixed_form_protocol = None
        else:
            # Copy data and set
            self._fixed_form_protocol = (list(times), list(values))

    def set_protocol(self, protocol=None):
        """
        Sets the pacing :class:`Protocol` used by this simulation.

        To run without pacing call this method with ``protocol = None``. In
        this case, the value of any variables bound to `pace` will be set to 0.
        """
        # Clear predetermined protocol, if set
        self._fixed_form_protocol = None

        # Set new protocol
        if protocol is None:
            self._protocol = None
        else:
            self._protocol = protocol.clone()

    def __setstate__(self, state):
        """
        Called after unpickling.

        See: https://docs.python.org/3/library/pickle.html#object.__setstate__
        """
        self._time = state[0]
        self._state = state[1]
        self._default_state = state[2]
        self._fixed_form_protocol = state[3]

        # The following properties need to be set on the internal simulation
        # object
        self.set_tolerance(*state[4])
        self.set_min_step_size(state[5])
        self.set_max_step_size(state[6])

    def set_state(self, state):
        """
        Sets the current state.
        """
        self._state = self._model.map_to_state(state)

    def set_time(self, time=0):
        """
        Sets the current simulation time.
        """
        self._time = float(time)

    def set_tolerance(self, abs_tol=1e-6, rel_tol=1e-4):
        """
        Sets the solver tolerances. Absolute tolerance is set using
        ``abs_tol``, relative tolerance using ``rel_tol``. For more information
        on these values, see the Sundials CVODE documentation.
        """
        abs_tol = float(abs_tol)
        if abs_tol <= 0:
            raise ValueError('Absolute tolerance must be positive float.')
        rel_tol = float(rel_tol)
        if rel_tol <= 0:
            raise ValueError('Relative tolerance must be positive float.')

        # Store tolerance in Python (for pickling)
        self._tolerance = (abs_tol, rel_tol)

        # Set tolerance in simulation
        self._sim.set_tolerance(abs_tol, rel_tol)

    def state(self):
        """
        Returns the current state.
        """
        return list(self._state)

    def time(self):
        """
        Returns the current simulation time.
        """
        return self._time
