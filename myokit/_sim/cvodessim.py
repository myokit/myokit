#
# CVODES-driven single cell simulation with optional sensitivities and root
# finding
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import platform
import tempfile

from collections import OrderedDict

import myokit

# Location of C template
SOURCE_FILE = 'cvodessim.c'


class Simulation(myokit.CModule):
    """
    Runs single cell simulations using the CVODES solver (see [1]); CVODES uses
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
    - (optional) the current and default state's sensitivities with respect to
      the selected independent variables.

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

    **Sensitivities**

    Sensitivities of model variables with respect to parameters (any unbound
    model variable defined as a literal constant) or initial values of states
    can be calculated using the ``sensitivities`` argument. If set, this should
    be a tuple ``(ys, xs)`` containing the "dependent" and "independent"
    expressions used to make up the calculated sensitivities (partial
    derivatives) ``dy/dx``.

    The "dependent variables" must refer to state variables, time-derivatives
    of state variables, or intermediary variables. These can be specified as
    :class:`myokit.Variable` objects, as :class:`myokit.Name` or
    :class:`myokit.Derivative` expressions, or as strings e.g. ``"ina.INa"`` or
    ``"dot(membrane.V)"``.

    The "independent variables" in sensitivities must refer to either literal
    variables (variables with no dependencies) or initial values of state
    variables. These can be specified as :class:`myokit.Variable` objects, as
    :class:`myokit.Name` or :class:`myokit.InitialValue` expressions, or as
    strings e.g. ``"ikr.gKr"`` or ``"init(membrane.V)"``.

    **Bound variables and labels**

    The simulation provides four inputs a model variable can be bound to:

    ``time``
        This input provides the simulation time.
    ``pace``
        This input provides the current value of the pacing variable. This is
        determined using the protocol passed into the Simulation.
    ``evaluations``
        This input provides the number of rhs evaluations used at each point in
        time and can be used to gain some insight into the solver's behavior.
    ``realtime``
        This input provides the elapsed system time at each logged point.

    No variable labels are required for this simulation type.

    **Multiple protocols or no protocol**

    This simulation supports pacing with more than one protocol. To this end,
    pass in a dictionary mapping pacing labels (bindings) to :class:`Protocol`
    or :class:`TimeSeriesProtocol` objects, e.g.
    ``protocol={'pace_1': protocol_1, 'pace_2': protocol_2}``.

    For backwards compatibility, if no protocol is set and ``protocol=None``,
    then the pacing label ``pace`` is still registered (allowing later calls to
    add a protocol with ``set_protocol``. Alternatively, if ``protocol={}``
    then no pacing labels will be registered, and any subsequent calls to
    ``set_protocol`` will fail.

    **Storing and loading simulation objects**

    There are two ways to store Simulation objects to the file system: 1.
    using serialisation (the ``pickle`` module), and 2. using the ``path``
    constructor argument.

    Each time a simulation is created, a C module is compiled, imported, and
    deleted in the background. This means that part of a ``Simulation`` object
    is a reference to an imported C extension, and cannot be serialized. When
    using ``pickle`` to serialize the simulation, this compiled part is not
    stored. Instead, when the pickled simulation is read from disk the
    compilation is repeated. Unpickling simulations also restores their state:
    variables such as model state, simulation time, and tolerance are preserved
    when pickling.

    As an alternative to serialisation, Simulations can be created with a
    ``path`` variable that specifies a location where the generated module can
    be stored. For example, calling ``Simulation(model, path='my-sim.zip')``
    will create a file called ``my-sim.zip`` in which the C extension is
    stored. To load, use ``Simulation.from_path('my-sim.zip')``. Unlike
    pickling, simulations stored and loaded this way do not maintain state:
    variables such as model state, simulation time, and tolerance are not
    preserved with this method. Finally, note that (again unlike pickled
    simulations), the generated zip files are highly platform dependent: a zip
    file generated on one machine may not work on another.

    **Arguments**

    ``model``
        The model to simulate
    ``protocol``
        A :class:`myokit.Protocol` or :class:`myokit.TimeSeriesProtocol` to use
        for the variable with binding ``pace``. Atlernatively, a dictionary
        mapping binding labels to :class:`myokit.Protocol` objects can be used
        to run with multiple protocols. Finally, can be ``None`` to run without
        a protocol.
    ``sensitivities``
        An optional tuple ``(dependents, independents)`` where ``dependents``
        is a list of variables or expressions to take derivatives of (``y`` in
        ``dy/dx``) and ``independents`` is a list of variables or expressions
        to calculate derivatives to (``x`` in ``dy/dx``).
        Each entry in ``dependents`` must be a :class:`myokit.Variable`, a
        :class:`myokit.Name`, a :class:`myokit.Derivative`, or a string with
        either a fully qualified variable name or a ``dot()`` expression.
        Each entry in ``independents`` must be a :class:`myokit.Variable`, a
        :class:`myokit.Name`, a :class:`myokit.InitialValue`, or a string with
        either a fully qualified variable name or an ``init()`` expression.
    ``path``
        An optional path used to load or store compiled simulation objects. See
        "Storing and loading simulation objects", above.

    **References**

    [1] SUNDIALS: Suite of nonlinear and differential/algebraic equation
    solvers. Hindmarsh, Brown, Woodward, et al. (2005) ACM Transactions on
    Mathematical Software.

    """
    _index = 0  # Simulation id

    def __init__(self, model, protocol=None, sensitivities=None, path=None):
        super().__init__()

        # Require a valid model
        if not model.is_valid():
            model.validate()
        self._model = model.clone()
        del model

        # Set protocol
        self._protocols = []
        self._pacing_labels = []
        if isinstance(protocol, (myokit.Protocol, myokit.TimeSeriesProtocol)):
            protocol = {'pace': protocol}
        elif protocol is None:
            # For backwards compatibility, we still register 'pace'. This
            # means users can call `set_protocol` at a later time to set a
            # protocol.
            protocol = {'pace': None}
        for label, protocol in protocol.items():
            self._protocols.append(None)
            self._pacing_labels.append(label)
            self.set_protocol(protocol, label)

        # Generate C Model code, get sensitivity and constants info
        cmodel = myokit.CModel(self._model, self._pacing_labels, sensitivities)
        if cmodel.has_sensitivities:
            self._sensitivities = (cmodel.dependents, cmodel.independents)

            # Check for sensitivities w.r.t. variables used in initial state
            # expressions. This is not implemented yet.
            inits = self._model.initial_values()
            for i in self._sensitivities[1]:  # Expressions
                if isinstance(i, myokit.Name):
                    for e in inits:
                        if e.depends_on(i, deep=True):
                            raise NotImplementedError(
                                'Sensitivities with respect to parameters used'
                                ' in initial conditions is not implemented ('
                                + e.code() + ' depends on ' + i.code() + ').')
        else:
            self._sensitivities = None

        # Ordered dicts mapping Variable objects to float values
        self._literals = OrderedDict()
        self._parameters = OrderedDict()
        for var, eq in cmodel.literals.items():
            self._literals[var] = eq.rhs.eval()
        for var, eq in cmodel.parameters.items():
            self._parameters[var] = eq.rhs.eval()

        # Compile or load simulation
        if type(path) == tuple:
            path, self._sim = path
        else:
            self._create_simulation(cmodel.code, path)
        del cmodel

        # Get state and default state from model
        self._state = self._model.initial_values(as_floats=True)
        self._default_state = list(self._state)

        # Set state and default state for sensitivities
        self._s_state = self._s_default_state = None
        if self._sensitivities:
            # Outer index: number of independent variables
            # Inner index: number of states
            self._s_state = []
            for expr in self._sensitivities[1]:
                row = [0.0] * len(self._state)
                if isinstance(expr, myokit.InitialValue):
                    row[expr.var().index()] = 1.0
                self._s_state.append(row)
            self._s_default_state = [list(x) for x in self._s_state]

        # Last state reached before error
        self._error_state = None
        self._error_inputs = None

        # Starting time
        self._time = 0

        # Set default min and max step size
        self._dtmax = self._dtmin = None

        # Set default tolerance values
        self._tolerance = None
        self.set_tolerance()

    def _create_simulation(self, cmodel_code, path):
        """
        Creates and compiles the C simulation module.

        If ``path`` is set, also stores the built extension in a zip file at
        ``path``, along with a serialisation of the Python Simulation object.
        """
        # Unique simulation id
        Simulation._index += 1
        module_name = 'myokit_sim_' + str(Simulation._index)
        module_name += '_' + str(myokit.pid_hash())

        # Arguments
        args = {
            'module_name': module_name,
            'model_code': cmodel_code,
        }
        fname = os.path.join(myokit.DIR_CFUNC, SOURCE_FILE)

        # Define libraries
        libs = [
            'sundials_cvodes',
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
        store = path is not None
        res = self._compile(
            module_name, fname, args, libs, libd, incd, store_build=store)

        # Store module and return
        if store:
            self._sim, d_build = res
            self._store_build(path, d_build, module_name)
        else:
            self._sim = res

    def _store_build(self, path, d_build, name):
        """
        Stores this simulation to ``path``, including all information from the
        build directory ``d_build`` and the generated backend module's
        ``name``.
        """
        try:
            import zipfile
            try:
                import zlib     # noqa
            except ImportError:
                raise Exception('Storing simulations requires the zlib module'
                                ' to be available.')

            # Sensitivity constructor argument. Don't pass in expressions, as
            # they will need to pickle the variables as well, which in turn
            # will need a component, model, etc.
            sens_arg = None
            if self._sensitivities:
                sens_arg = [[x.code() for x in y] for y in self._sensitivities]

            # Store serialized name and constructor args
            fname = os.path.join(d_build, '_simulation.pickle')
            import pickle
            with open(fname, 'wb') as f:
                pickle.dump(str(name), f)
                pickle.dump(self._model, f)
                pickle.dump(self._protocols, f)
                pickle.dump(self._pacing_labels, f)
                pickle.dump(sens_arg, f)

            # Zip it all in
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as f:
                for root, dirs, files in os.walk(d_build):
                    for fname in files:
                        org = os.path.join(root, fname)
                        new = os.path.relpath(org, d_build)
                        f.write(org, new)
        finally:
            myokit.tools.rmtree(d_build, silent=True)

    @staticmethod
    def from_path(path):
        """
        Loads a simulation from the zip file in ``path``.

        The file at ``path`` must have been created by :class:`Simulation` and
        on the same platform (e.g. the same operating system, processor
        architecture, Myokit version etc.).

        Note that the simulation state (e.g. time, model state, solver
        tolerance etc. is not restored).

        Returns a :class:`Simulation` object.
        """
        import zipfile
        try:
            import zlib     # noqa
        except ImportError:
            raise Exception('Loading simulations requires the zlib module to'
                            ' be available.')

        # Unpack the zipped information
        d_build = tempfile.mkdtemp('myokit_build')
        try:
            with zipfile.ZipFile(path, 'r', zipfile.ZIP_DEFLATED) as f:
                f.extractall(d_build)

            # Load serialized name and constructor args
            fname = os.path.join(d_build, '_simulation.pickle')
            import pickle
            with open(fname, 'rb') as f:
                name = pickle.load(f)
                model = pickle.load(f)
                protocols = pickle.load(f)
                pacing_labels = pickle.load(f)
                sensitivities = pickle.load(f)

            # Load module
            from myokit._sim import load_module
            module = load_module(name, d_build)

            # Create and return simulation
            labeled_protocols = {
                k: v for k, v in zip(pacing_labels, protocols)
            }
            return Simulation(
                model, labeled_protocols, sensitivities, (path, module)
            )

        finally:
            myokit.tools.rmtree(d_build, silent=True)

    def crash_inputs(self):
        """
        If the last call to :meth:`Simulation.pre()` or
        :meth:`Simulation.run()` resulted in an error, this will return the
        last "inputs" (time, pace, etc) reached during that simulation.

        Will return ``None`` if no simulation was run or the simulation did not
        result in an error.
        """
        return dict(self._error_inputs) if self._error_inputs else None

    def crash_state(self):
        """
        If the last call to :meth:`Simulation.pre()` or
        :meth:`Simulation.run()` resulted in an error, this will return the
        last state reached during that simulation.

        Will return ``None`` if no simulation was run or the simulation did not
        result in an error.
        """
        return list(self._error_state) if self._error_state else None

    def default_state(self):
        """
        Returns the default state.
        """
        return list(self._default_state)

    def default_state_sensitivities(self):
        """
        Returns the default sensitivities with respect to state variables, or
        ``None`` if sensitivities are not enabled.
        """
        if self._sensitivities:
            return [list(x) for x in self._s_default_state]
        return None

    def eval_derivatives(self, y=None, pacing=None):
        """
        Deprecated alias of :meth:`evaluate_derivatives`.

        Note that while :meth:`eval_derivatives` used the :meth:`state()` as
        default, the new method uses :meth:`default_state()`.
        """
        # Deprecated on 2024-03-08
        import warnings
        warnings.warn(
            'The method `myokit.Simulation.eval_derivatives` is deprecated,'
            ' please use `evaluate_derivatives(state=sim.state())` instead.'
        )
        if y is None:
            y = self.state()
        return self.evaluate_derivatives(y, pacing)

    def evaluate_derivatives(self, state=None, inputs=None):
        """
        Evaluates and returns the state derivatives for the given ``state`` and
        ``inputs``.

        If no ``state`` is given, the value returned by :meth:`default_state()`
        is used.

        An optional dict ``inputs`` can be passed in to set the values of
        time and other inputs (e.g. pacing values). If "time" is not set in
        ``inputs``, the value 0 will be used, regardless of the current
        simulation. Similarly, if pacing values are not set in ``inputs``, 0
        will be used regardless of the protocols or the current time.

        If any variables have been changed with `set_constant` their new value
        will be used.
        """
        # Get state
        if state is None:
            y = list(self._default_state)
        else:
            y = self._model.map_to_state(state)

        # Get inputs
        time = realtime = evaluations = 0
        pacing_values = [0.0] * len(self._pacing_labels)
        if inputs is not None:
            if 'time' in inputs:
                time = float(inputs['time'])
                del inputs['time']
            if 'realtime' in inputs:  # User really shouldn't, but can do this
                realtime = float(inputs['realtime'])
                del inputs['realtime']
            if 'evaluations' in inputs:
                evaluations = float(inputs['evaluations'])
                del inputs['evaluations']
            for k, v in inputs.items():
                try:
                    ki = self._pacing_labels.index(k)
                except ValueError:
                    raise ValueError(f'Unknown binding or pacing label `{k}`.')
                pacing_values[ki] = float(v)

        # Literals and parameters: Can be changed with set_constant
        literals = list(self._literals.values())
        parameters = list(self._parameters.values())

        # Create space to store derivatives
        dy = list(self._state)

        # Evaluate and return
        self._sim.evaluate_derivatives(
            time,               # 0. Time
            pacing_values,      # 1. Pacing values
            realtime,           # 2. Realtime
            evaluations,        # 3. Evaluations
            literals,           # 4. Literals
            parameters,         # 5. Parameters
            y,                  # 6. State
            dy,                 # 7. Derivatives (out)
        )
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

    def last_state(self):
        """
        If the last call to :meth:`Simulation.pre()` or
        :meth:`Simulation.run()` resulted in an error, this will return the
        last state reached during that simulation.

        Will return ``None`` if no simulation was run or the simulation did not
        result in an error.
        """
        # Deprecated on 2024-03-08
        import warnings
        warnings.warn('The method `myokit.Simulation.last_state` is'
                      ' deprecated. Please use `crash_state` instead.')
        return self.crash_state()

    def pre(self, duration, progress=None, msg='Pre-pacing simulation'):
        """
        This method can be used to perform an unlogged simulation, typically to
        pre-pace to a (semi-)stable orbit.

        After running this method

        - The simulation time is **not** affected
        - The current state and the default state are updated to the final
          state reached in the simulation.
        - The current state-sensitivities and default state-sensitivities are
          updated to the final state reached in the simulation, except for
          state-sensitivities with respect to initial conditions, which are
          reset (see below).

        Calls to :meth:`reset` after using :meth:`pre` will set the current
        state to this new default state.

        When calculating sensitivities with respect to the initial value of
        some state variable with index ``i``, the sensitivity of that state
        w.r.t. the initial value will be ``1`` at time zero. Similarly, the
        sensitivity of any other state to that initial value at this time will
        be ``0``. Because :meth:`pre()` is used to set a new state for time
        zero, this method will set the current and default state sensitivities
        for initial value sensitivities to 0 or 1 as above, instead of using
        the values reached in the simulation.

        The number of time units to simulate can be set with ``duration``.
        The ``duration`` argument cannot be negative, and special care needs to
        be taken when very small (positive) values are used. For some very
        short (but non-zero) durations, a :class:`myokit.SimulationError` may
        be raised.

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as `msg`.
        """
        duration = float(duration)
        self._run(
            duration, myokit.LOG_NONE, None, None, None, None, None, progress,
            msg)
        self._default_state = list(self._state)
        if self._sensitivities:
            # Reset to time 0, so need to reset initial-value sensitivities
            for i, expr in enumerate(self._sensitivities[1]):
                if isinstance(expr, myokit.InitialValue):
                    self._s_state[i] = [0.0] * len(self._state)
                    self._s_state[i][expr.var().index()] = 1.0
            # Update default state
            self._s_default_state = [list(x) for x in self._s_state]

    def __reduce__(self):
        """
        Pickles this Simulation.

        See: https://docs.python.org/3/library/pickle.html#object.__reduce__
        """
        sens_arg = None
        if self._sensitivities:
            # Don't pass in expressions, as they'll need to pickle the
            # variables as well, which in turn will need a component, model,
            # etc.
            sens_arg = [[x.code() for x in y] for y in self._sensitivities]

        protocols = {
            k: p for k, p in zip(self._pacing_labels, self._protocols)
        }

        return (
            self.__class__,
            (self._model, protocols, sens_arg),
            (
                self._time,
                self._state,
                self._default_state,
                self._s_state,
                self._s_default_state,
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
        - The state sensitivities are set to the default state sensitivities

        """
        self._time = 0
        self._state = list(self._default_state)
        if self._sensitivities:
            self._s_state = [list(x) for x in self._s_default_state]

    def run(self, duration, log=None, log_interval=None, log_times=None,
            sensitivities=None, apd_variable=None, apd_threshold=None,
            progress=None, msg='Running simulation'):
        """
        Runs a simulation and returns the logged results. Running a simulation
        has the following effects:

        - The internal state is updated to the last state in the simulation.
        - The simulation's time variable is updated to reflect the time
            elapsed during the simulation.

        The number of time units to simulate can be set with ``duration``.
        The ``duration`` argument cannot be negative, and special care needs to
        be taken when very small (positive) values are used. For some very
        short (but non-zero) durations, a :class:`myokit.SimulationError` may
        be raised.

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

        To get action potential duration (APD) measurements, the simulation can
        be run with threshold crossing detection. To enable this, pass in a
        state variable as ``apd_variable`` and a threshold value as
        ``apd_threshold``.
        *Please note the APD calculation implemented here uses a fixed
        threshold, and so differs from the often used dynamical thresholds such
        as "90% of max(V) - min(V)".*

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as ``msg``.

        Arguments:

        ``duration``
            The time to simulate.
        ``log``
            The variables to log (see detailed description above).
        ``log_interval``
            An optional fixed size log interval. Must be ``None`` if
            ``log_times`` is used. If both are ``None`` every step is logged.
        ``log_times``
            An optional sequence (e.g. a list or a numpy array) of
            pre-determined logging times. Must be ``None`` if ``log_interval``
            is used. If both are ``None`` every step is logged.
        ``sensitivities``
            An optional list-of-lists to append the calculated sensitivities
            to.
        ``apd_variable``
            An optional :class:`myokit.Variable` or fully-qualified variable
            name to use in APD calculations. If set, an ``apd_threshold`` must
            also be specified.
        ``apd_threshold``
            An optional (fixed) threshold to use in APD calculations. Must be
            set if and ``apd_variable`` is set, and ``None`` if not.
        ``progress``
            An optional :class:`myokit.ProgressReporter` used to obtain
            feedback about simulation progress.
        ``msg``
            An optional message to pass to any progress reporter.

        By default, this method returns a :class:`myokit.DataLog` containing
        the logged variables.

        However, if sensitivity calculations are enabled a tuple is returned,
        where the first entry is the :class:`myokit.DataLog` and the second
        entry is a matrix of sensitivities ``dy/dx``, where the first index
        specifies the dependent variable ``y``, and the second index specifies
        the independent variable ``x``.

        Finally, if APD calculation is enabled, the method returns a tuple
        ``(log, apds)`` or ``(log, sensitivities, apds)`` where ``apds`` is a
        :class:`myokit.DataLog` with entries ``start`` and ``duration``,
        representing the start and duration of all measured APDs.
        """
        duration = float(duration)
        output = self._run(
            duration, log, log_interval, log_times, sensitivities,
            apd_variable, apd_threshold, progress, msg)
        self._time += duration
        return output

    def _run(self, duration, log, log_interval, log_times, sensitivities,
             apd_variable, apd_threshold, progress, msg):

        # Create benchmarker for profiling and realtime logging
        # Note: When adding profiling messages, write them in past tense so
        # that we can show time elapsed for an operation **that has just
        # completed**.
        if myokit.DEBUG_SP or self._model.binding('realtime') is not None:
            b = myokit.tools.Benchmarker()
            if myokit.DEBUG_SP:
                b.print('PP Entered _run method.')
        else:
            b = None

        # Reset error state
        self._error_state = None
        self._error_inputs = None

        # Simulation times
        if duration < 0:
            raise ValueError('Simulation time can\'t be negative.')
        tmin = self._time
        tmax = tmin + duration

        # Logging interval (None or 0 = disabled)
        log_interval = 0 if log_interval is None else float(log_interval)
        if log_interval < 0:
            log_interval = 0
        if log_times is not None and log_interval > 0:
            raise ValueError(
                'The arguments `log_times` and `log_interval` cannot be used'
                ' simultaneously.')

        # Check user-specified logging times.
        # (An empty list of log points counts as disabled)
        # Note: Checking of values inside the list (converts to float, is non
        # decreasing) happens in the C code.
        if log_times is not None:
            if len(log_times) == 0:
                log_times = None

        # List of sensitivity matrices
        if self._sensitivities:
            if sensitivities is None:
                sensitivities = []
            else:
                # Must be list (of lists of lists)
                if not isinstance(sensitivities, list):
                    raise ValueError(
                        'The argument `sensitivities` must be None or a list.')
        else:
            sensitivities = None

        # APD measuring
        root_list = None
        root_index = 0
        root_threshold = 0
        if apd_variable is None:
            if apd_threshold is not None:
                raise ValueError(
                    'APD Threshold given but no `apd_variable` specified.')
        else:
            # Get apd variable from this model
            if isinstance(apd_variable, myokit.Variable):
                apd_variable = apd_variable.qname()
            apd_variable = self._model.get(apd_variable)
            if not apd_variable.is_state():
                raise ValueError(
                    'The `apd_variable` must be a state variable.')

            # Set up root finding
            root_list = []
            root_index = apd_variable.index()
            root_threshold = float(apd_threshold)

        # Get progress indication function (if any)
        if progress is None:
            progress = myokit._simulation_progress
        if progress:
            if not isinstance(progress, myokit.ProgressReporter):
                raise ValueError(
                    'The argument `progress` must be either a'
                    ' subclass of myokit.ProgressReporter or None.')
        if myokit.DEBUG_SP:
            b.print('PP Checked arguments.')

        # Parse log argument
        log = myokit.prepare_log(log, self._model, if_empty=myokit.LOG_ALL)
        if myokit.DEBUG_SP:
            b.print('PP Called prepare_log.')

        # Run simulation
        # The simulation is run only if (tmin + duration > tmin). This is a
        # stronger check than (duration == 0), which will return true even for
        # very short durations (and will cause zero iterations of the
        # "while (t < tmax)" loop below).
        if tmin + duration > tmin:

            # Initial state and sensitivities
            state = list(self._state)
            s_state = None
            if self._sensitivities:
                s_state = [list(x) for x in self._s_state]

            # List to store final bound variables in (for debugging)
            bound = [0, 0, 0] + [0] * len(self._pacing_labels)

            # Initialize
            if myokit.DEBUG_SP:
                b.print('PP Ready to call sim_init.')
            self._sim.sim_init(
                # 0. Initial time
                tmin,
                # 1. Final time
                tmax,
                # 2. Initial and final state
                state,
                # 3. Initial and final state sensitivities
                s_state,
                # 4. Space to store the bound variable values
                bound,
                # 5. Literal values
                list(self._literals.values()),
                # 6. Parameter values
                list(self._parameters.values()),
                # 7. Pacing protocols
                self._protocols,
                # 8. A DataLog
                log,
                # 9. The log interval, or 0
                log_interval,
                # 10. A list of predetermind logging times, or None
                log_times,
                # 11. A list to store calculated sensitivities in
                sensitivities,
                # 12. The state variable index for root finding (only used if
                #     root_list is a list)
                root_index,
                # 13. The threshold for root crossing (can be 0 too, only used
                #     if root_list is a list).
                root_threshold,
                # 14. A list to store calculated root crossing times and
                #     directions in, or None
                root_list,
                # 15. A myokit.tools.Benchmarker or None (if not used)
                b,
                # 16. Boolean/int: 1 if we are logging realtime
                int(self._model.binding('realtime') is not None),
            )
            t = tmin

            # Run
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
                # Some CVODE(S) errors are set to raise an ArithmeticError,
                # which users may be able to debug.
                if myokit.DEBUG_SP:
                    b.print('PP Caught ArithmeticError.')

                # Store error state
                self._error_state = state
                self._error_inputs = {'time': bound[0]}
                for i, label in enumerate(('realtime', 'evaluations')):
                    if self._model.binding(label) is not None:
                        self._error_inputs[label] = bound[1 + i]
                for i, label in enumerate(self._pacing_labels):
                    self._error_inputs[label] = bound[3 + i]

                # Create long error message
                txt = ['A numerical error occurred during simulation at'
                       ' t = ' + myokit.float.str(bound[0]) + '.',
                       'Last reached state: ']
                txt.extend(['  ' + x for x
                            in self._model.format_state(state).splitlines()])
                txt.append('Inputs for binding:')
                for key, value in self._error_inputs.items():
                    txt.append(f'  {key} = {myokit.float.str(value)}')
                txt.append(str(e))

                # Check if state derivatives can be evaluated in Python, if
                # not, add the error to the error message.
                try:
                    self._model.evaluate_derivatives(state, self._error_inputs)
                except Exception as en:
                    txt.append(str(en))

                # Raise numerical simulation error
                raise myokit.SimulationError('\n'.join(txt))

            except Exception as e:
                if myokit.DEBUG_SP:
                    b.print('PP Caught exception.')

                # Store error state
                self._error_state = state

                # Cast known CVODE errors as SimulationError
                if 'Function CVode()' in str(e):
                    raise myokit.SimulationError(str(e))

                # Unknown exception: re-raise
                raise
            finally:
                # Clean even after KeyboardInterrupt or other Exception
                self._sim.sim_clean()

            # Update internal state
            # Both lists were newly created, so this is OK.
            self._state = state
            self._s_state = s_state

        # Simulation complete
        if myokit.DEBUG_SP:
            b.print('PP Simulation complete.')

        # Calculate apds
        if root_list is not None:
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
            if myokit.DEBUG_SP:
                b.print('PP Root-finding data processed.')

        # Return
        if myokit.DEBUG_SP:
            b.print('PP Call to _run() complete. Returning.')
        if self._sensitivities is not None:
            if root_list is not None:
                return log, sensitivities, apds
            else:
                return log, sensitivities
        elif root_list is not None:
            return log, apds
        return log

    def set_constant(self, var, value):
        """
        Changes a model constant. Only literal constants (constants not
        dependent on any other variable) can be changed.

        The constant ``var`` can be given as a :class:`Variable` or a string
        containing a variable qname. The ``value`` should be given as a float.
        """
        # Get variable
        value = float(value)
        if isinstance(var, myokit.Variable):
            var = var.qname()
        var = self._model.get(var)

        # Update value in literal or parameter map
        if var in self._literals:
            self._literals[var] = value
        elif var in self._parameters:
            self._parameters[var] = value
        else:
            raise ValueError(
                'The given variable <' + var.qname() + '> is not a literal.')

        # Update value in internal model: This is required for error handling,
        # when self._model.evaluate_derivatives is called.
        # It also ensures the modified value is retained when pickling.
        self._model.set_value(var, value)

    def set_default_state(self, state):
        """
        Change the default state to ``state``.
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
        Sets a :class:`TimeSeriesProtocol` specified by ``times`` and
        ``values`` for the label ``pace``.

        This method is provided for backwards compatibility with older
        versions, please use :meth:`set_protocol` and the
        :class:`TimeSeriesProtocol` class instead.
        """
        # Deprecated on 2023-06-02
        import warnings
        warnings.warn(
            'The method `myokit.Simulation.set_fixed_form_protocol` is '
            'deprecated. It will be removed in future versions of Myokit.'
        )

        if times is None and values is None:
            self.set_protocol(None)
            return
        if times is None:
            raise ValueError('No times given.')
        if values is None:
            raise ValueError('No values given.')

        self.set_protocol(myokit.TimeSeriesProtocol(times, values))

    def set_protocol(self, protocol, label='pace'):
        """
        Set an event-based pacing :class:`Protocol` or a
        :class:`TimeSeriesProtocol` for the given ``label``.

        To remove a previously set binding call this method with ``protocol =
        None``. In this case, the value of any variables bound to ``label``
        will be set to 0.

        The label must be one of the pacing labels set in the constructor.
        """
        try:
            index = self._pacing_labels.index(label)
        except ValueError:
            raise ValueError('Unknown pacing label: ' + str(label))

        # Set new protocol
        self._protocols[index] = None if protocol is None else protocol.clone()

    def __setstate__(self, state):
        """
        Called after unpickling, to set any variables not set by the
        constructor.

        See: https://docs.python.org/3/library/pickle.html#object.__setstate__
        """
        self._time = state[0]
        self._state = state[1]
        self._default_state = state[2]
        self._s_state = state[3]
        self._s_default_state = state[4]

        # The following properties need to be set on the internal simulation
        # object
        self.set_tolerance(*state[5])
        self.set_min_step_size(state[6])
        self.set_max_step_size(state[7])

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
        on these values, see the Sundials CVODES documentation.
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
