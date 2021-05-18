#
# OpenCL driven simulation, 1d or 2d
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import myokit
import numpy as np
import platform
from collections import OrderedDict


# Location of C and OpenCL sources
SOURCE_FILE = 'openclsim.c'
KERNEL_FILE = 'openclsim.cl'


class SimulationOpenCL(myokit.CModule):
    """
    Can run multi-cellular simulations based on a :class:`model <Model>` using
    OpenCL for parallelization.

    Takes the following input arguments:

    ``model``
        The model to simulate with. This model will be cloned when the
        simulation is created so that no changes to the given model will be
        made.
    ``protocol``
        An optional pacing protocol, used to stimulate a number of cells either
        at the start of a fiber or at the bottom-left of the tissue.
    ``ncells``
        The number of cells. Use a scalar for 1d simulations or a tuple
        ``(nx, ny)`` for 2d simulations.
    ``diffusion``
        Can be set to False to disable diffusion currents. This can be useful
        in combination with :meth:`set_field` to explore the effects of varying
        one or more parameters in a single cell model.
    ``precision``
        Can be set to ``myokit.SINGLE_PRECISION`` (default) or
        ``myokit.DOUBLE_PRECISION`` if the used device supports it.
    ``native_maths``
        On some devices, selected functions (e.g. ``exp``) can be made to run
        faster (but possibly less accurately) by setting ``native_maths=True``.
    ``rl``
        Use Rush-Larsen updates instead of forward Euler for any Hodgkin-Huxley
        gating variables (default=``False``).

    The simulation provides the following inputs variables can bind to:

    ``time``
        The simulation time
    ``pace``
        The pacing level, this is set if a protocol was passed in.
    ``diffusion_current`` (if enabled)
        The current flowing from the cell to its neighbours. This will be
        positive when the cell is acting as a source, negative when it is
        acting as a sink.

    The input ``time`` is set globally: Any variable bound to ``time`` will
    appear in the logs as single, global variable (for example ``engine.time``
    instead of ``1.2.engine.time``. Variables bound to ``pace`` or
    ``diffusion_current`` are logged per cell. (If diffusion currents are
    disabled, the input ``diffusion_current`` will not be used, and any
    variables bound to it will be logged or not according to their default
    value).

    To set the number of cells that will be paced, the methods
    :meth:`set_paced_cells()` and :meth:`set_paced_cell_list()` can be used.

    A single labeled variable is required for this simulation to work:

    ``membrane_potential``
        The variable representing the membrane potential.

    Simulations maintain an internal state consisting of

    - the current simulation time
    - the current state
    - the default state

    When a simulation is created, the simulation time is set to 0 and both the
    current and the default state are equal to the state of the given model,
    copied once for each cell.
    After each call to :meth:`run` the time variable and current state are
    updated, so that each successive call to run continues where the previous
    simulation left off. A :meth:`reset` method is provided that will set the
    time back to 0 and revert the current state to the default state. To change
    the time or state manually, use :meth:`set_time` and :meth:`set_state`.

    A pre-pacing method :meth:`pre` is provided that doesn't affect the
    simulation time but will update the current *and the default state*. This
    allows you to pre-pace, run a simulation, reset to the pre-paced state, run
    another simulation etc.

    To set up a 1d simulation, the argument ``ncells`` should be given as a
    tuple. In this case, any cell ``i`` will be assumed to be connected to
    cells ``i - 1`` and ``i + 1`` (except at the boundaries).
    Similarly, if ``ncells`` is a 2-dimensional tuple ``(nx, ny)`` a grid will
    be assumed so that each (non-boundary) cell is connected to four
    neighbours.
    Finally, arbitrary geometries can be used by passing a scalar to ``ncells``
    and specifying the connections with :meth:`set_connections`.

    The ``diffusion_current`` in any cell is calculated as::

        i = sum[g * (V - V_j)]

    Where the sum is taken over all connected cells ``j`` (see [1]).

    Models used with this simulation need to have independent components: it
    should be possible to evaluate the model's equations one component at a
    time. A model's suitability can be tested using
    :meth:`has_interdependent_components
    <myokit.Model.has_interdependent_components>`.

    Simulations are performed using a forward Euler (FE) method with a fixed
    time step (see :meth:`set_step_size()`). Using smaller step sizes is
    computationally demanding, but gives more accurate results. Using too large
    a step size can also cause a simulation to become unstable, but please note
    that stability does imply accuracy, and always double-check important
    results by re-running with a reduced step size.

    If the optional parameter ``rl`` is set to ``True``, state variables
    written in a Hodgkin-Huxley form will be updated using a Rush-Larsen (RL)
    instead of a forward Euler step (see [2]). This provides greater stability
    (so that the step size can be increased) but not necessarily greater
    accuracy (see [3]), so that care must be taken when using this method.

    [1] Myokit: A simple interface to cardiac cellular electrophysiology.
    Clerx, Collins, de Lange, Volders (2016) Progress in Biophysics and
    Molecular Biology.

    [2] A practical algorithm for solving dynamic membrane equations.
    Rush, Larsen (1978) IEEE Transactions on Biomedical Engineering

    [3] Cellular cardiac electrophysiology modelling with Chaste and CellML
    Cooper, Spiteri, Mirams (2015) Frontiers in Physiology

    """
    _index = 0  # Unique id for the generated module

    def __init__(
            self, model, protocol=None, ncells=256, diffusion=True,
            precision=myokit.SINGLE_PRECISION, native_maths=False, rl=False):
        super(SimulationOpenCL, self).__init__()

        # Require a valid model
        model.validate()

        # Require independent components
        if model.has_interdependent_components():
            cycles = '\n'.join([
                '  ' + ' > '.join([x.name() for x in c])
                for c in model.component_cycles()])
            raise ValueError(
                'This simulation requires models without interdependent'
                ' components. Please restructure the model and re-run.'
                '\nCycles:\n' + cycles)

        # Set protocol
        self.set_protocol(protocol)

        # Check dimensionality, number of cells
        try:
            if len(ncells) != 2:
                raise ValueError(
                    'The argument "ncells" must be either a scalar or a tuple'
                    ' (nx, ny).')
            self._nx = int(ncells[0])
            self._ny = int(ncells[1])
            self._dims = (self._nx, self._ny)
        except TypeError:
            self._nx = int(ncells)
            self._ny = 1
            self._dims = (self._nx,)
        if self._nx < 1 or self._ny < 1:
            raise ValueError(
                'The number of cells in any direction must be at least 1.')
        self._ntotal = self._nx * self._ny

        # Set diffusion mode
        self._diffusion_enabled = True if diffusion else False

        # Set precision
        if precision not in (myokit.SINGLE_PRECISION, myokit.DOUBLE_PRECISION):
            raise ValueError('Only single and double precision are supported.')
        self._precision = precision

        # Set native maths
        self._native_math = bool(native_maths)

        # Set rush-larsen mode
        self._rl = bool(rl)

        # Get membrane potential variable (from pre-cloned model!)
        vm = model.label('membrane_potential')
        if vm is None:
            raise ValueError(
                'This simulation requires the membrane potential'
                ' variable to be labelled as "membrane_potential".')
        if not vm.is_state():
            raise ValueError(
                'The variable labelled as membrane potential must'
                ' be a state variable.')

        #if vm.is_referenced():
        #  raise ValueError('This simulation requires that no other variables'
        #      ' depend on the time-derivative of the membrane potential.')

        # Prepare for Rush-Larsen updates, and/or clone model
        self._rl_states = {}
        if self._rl:
            import myokit.lib.hh as hh

            # Convert alpha-beta formulations to inf-tau forms, cloning model
            self._model = hh.convert_hh_states_to_inf_tau_form(model, vm)
            self._vm = self._model.get(vm.qname())
            del(model, vm)

            # Get (inf, tau) tuple for every Rush-Larsen state
            for state in self._model.states():
                res = hh.get_inf_and_tau(state, self._vm)
                if res is not None:
                    self._rl_states[state] = res

        else:
            # Clone model, store
            self._model = model.clone()
            self._vm = self._model.get(vm.qname())
            del(model, vm)

        # Set default conductance values
        self.set_conductance()

        # Set connections
        self._connections = None

        # Set default paced cells
        self._paced_cells = []
        if diffusion:
            self.set_paced_cells()
        else:
            self.set_paced_cells(self._nx, self._ny, 0, 0)

        # Scalar fields
        self._fields = OrderedDict()

        # Set default time step
        self.set_step_size()

        # Set initial time
        self._time = 0

        # Count number of states
        self._nstate = self._model.count_states()

        # Set state and default state
        self._state = self._model.state() * self._ntotal
        self._default_state = list(self._state)

        # List of globally logged inputs
        self._global = ['time', 'pace']

        # Process bindings: remove unsupported bindings, get map of bound
        # variables to internal names.
        inputs = {'time': 'time', 'pace': 'pace'}
        if self._diffusion_enabled:
            inputs['diffusion_current'] = 'idiff'
        self._bound_variables = self._model.prepare_bindings(inputs)

        # Reserve keywords
        from myokit.formats import opencl
        self._model.reserve_unique_names(*opencl.keywords)
        self._model.reserve_unique_names(
            *['calc_' + c.name() for c in self._model.components()])
        self._model.reserve_unique_names(
            *['D_' + c.uname() for c in self._model.states()])
        self._model.reserve_unique_names(*KEYWORDS)
        self._model.create_unique_names()

        # Create back-end
        SimulationOpenCL._index += 1
        mname = 'myokit_sim_opencl_' + str(SimulationOpenCL._index)
        mname += '_' + str(myokit.pid_hash())
        fname = os.path.join(myokit.DIR_CFUNC, SOURCE_FILE)
        args = {
            'module_name': mname,
            'model': self._model,
            'precision': self._precision,
            'dims': len(self._dims),
        }

        # Debug
        if myokit.DEBUG:
            print(self._code(
                fname, args, line_numbers=myokit.DEBUG_LINE_NUMBERS))
            #import sys
            #sys.exit(1)

        # Define libraries
        libs = []
        flags = []
        plat = platform.system()
        if plat != 'Darwin':    # pragma: no osx cover
            libs.append('OpenCL')
        else:                   # pragma: no cover
            flags.append('-framework')
            flags.append('OpenCL')
        if plat != 'Windows':   # pragma: no windows cover
            libs.append('m')

        # Create extension
        libd = list(myokit.OPENCL_LIB)
        incd = list(myokit.OPENCL_INC)
        incd.append(myokit.DIR_CFUNC)
        self._sim = self._compile(
            mname, fname, args, libs, libd, incd, larg=flags)

    def calculate_conductance(self, r, sx, chi, dx):
        """
        The bidomain and monodomain models both start from the assumption of
        ohmic conductance between cells. In this way, Myokit's diffusion
        current
        ::

            I_diff[ij] = sum[g[ij] * (V[i] - V[j])]

        (where the sum is over all neighbours j of cell i) is equivalent to the
        fundamental assumption of the bidomain model. In some cases it may be
        desirable to work backwards from the bidomain model, via the
        monodomain model, to the Myokit formulation. This can be done under the
        following conditions:

        1. The conductivity tensor sigma has only diagonal components (so cells
           never conduct diagonally).
        2. The zero-flux boundary condution is used: no current flows between
           the simulated tissue and its surroundings.

        Then, using a finite-difference approximation for the second order
        derivative::

            d^2V[i]   V[i-1] - 2*V[i] + V[i+1]
            ------- = ------------------------
             dx^2              dx^2

        we can equate ``I_diff`` and the monodomain model to find::

                   r    sx * chi
            gx = ----- ---------
                 1 + r    dx^2

        with

        ``r``
            The intra- to extracellular conductivity ratio
        ``sx``
            The intracellular conductivity in direction "x"
        ``chi``
            The surface area of the membrane per unit volume
        ``dx``
            The size of the spatial discretisation step in direction ``x``
        ``gx``
            The cell-to-cell conductance in direction ``x``, as used by Myokit

        This method uses the above equation to calculate and return a
        conductance value from the parameters used in monodomain model based
        simulations.
        """
        return r * sx * chi / ((1 + r) * dx * dx)

    def conductance(self):
        """
        Returns the cell-to-cell conductance used in this simulation. The
        returned value will be a single float for 1d simulations and a tuple
        ``(gx, gy)`` for 2d simulations. If a list of connections was passed in
        ``None`` is returned
        """
        if self._connections is not None:
            return None
        if len(self._dims) == 1:
            return self._gx
        return (self._gx, self._gy)

    def find_nan(self, log, watch_var=None, safe_range=None, return_log=False):
        """
        Searches for the origin of a bad value (``NaN`` or ``inf``) in a data
        log generated by this simulation.

        Arguments:

        ``log``
            A :class:`myokit.DataLog` from this simulation. The log must
            contain the state of each cell and all bound variables. The bad
            value can occur at any point in time except the first.
        ``watch_var``
            To aid in diagnosis, a variable can be selected as ``watch_var``
            and a ``safe_range`` can be specified. With this option, the
            function will find and report either the first bad value or the
            first time the watched variable left the safe range, whatever came
            first. The watched variable must be a state variable.
        ``safe_range``
            The safe range to check the ``watch_var`` against. The safe range
            should be specified as ``(lower, upper)`` where both bounds are
            assumed to be in the safe range.
        ``return_log``
            If set to ``True``, a log containing the final points before the
            error occurred will be returned, containing all variables for all
            cells.

        Returns a tuple containing the following six values (or seven values if
        ``return_log=True``):

        ``time``
            The time the first bad value was found.
        ``icell``
            The index of the cell in which the bad value was found, as a tuple
            e.g. ``(3, )`` in a 1d simulation or ``(15, 12)`` in a 2d
            simulation.
        ``variable``
            The name of the variable that was detected to be ``NaN`` or
            ``inf``.
        ``value``
            The bad value detected)
        ``states``
            The state at time ``time`` and, if possible, up to 3 earlier
            states. Here, ``states[0]`` points to the current state,
            ``state[1]`` is the previous state and so on. Each state is
            represented as a list of values.
        ``bounds``
            The bound variables corresponding to the returned ``states``. For
            ``diffusion_current``, this will contain the specific cell's
            current, for ``time`` and ``pace`` the global values are shown.
            Each entry in ``bounds`` is a dictionary from variable names to
            values.
        ``log``
            A :class:`myokit.DataLog` with all variables for the same points as
            ``states`` and ``bounds``. This will only be included if
            ``return_log=True``.

        """
        import numpy as np

        # Test if log contains all states and bound variables
        t = []
        for label in self._global:
            var = self._model.binding(label)
            if var is not None:
                t.append(var.qname())
        t = myokit.prepare_log(
            myokit.LOG_STATE + myokit.LOG_BOUND,
            self._model,
            dims=self._dims,
            global_vars=t)
        for key in t:
            if key not in log:
                raise myokit.FindNanError(
                    'Method requires a simulation log containing all states'
                    ' and bound variables. Missing variable <' + key + '>.')
        del(t)

        # Error criterium
        if watch_var is None:

            # NaN/inf detection
            def bisect(ar, lo, hi):
                if not np.isfinite(ar[lo]):
                    return lo
                md = lo + int(np.ceil(0.5 * (hi - lo)))
                if md == hi:
                    return hi
                if not np.isfinite(ar[md]):
                    return bisect(ar, lo, md)
                else:
                    return bisect(ar, md, hi)

            def find_error_position(log):
                # Search for first occurrence of propagating NaN in the log
                ifirst = None   # Index in time
                kfirst = None   # Variable + cell index
                for key, ar in log.items():
                    if ifirst is None:
                        if not np.isfinite(ar[-1]):
                            # NaN found in the log
                            kfirst = key
                            ifirst = bisect(ar, 0, len(ar) - 1)
                            if ifirst == 0:
                                break
                    elif not np.isfinite(ar[ifirst - 1]):
                        # Earlier NaN found than before
                        kfirst = key
                        ifirst = bisect(ar, 0, ifirst)
                        if ifirst == 0:
                            break
                return ifirst, kfirst

        else:

            # Variable out of bounds detection
            try:
                watch_var = self._model.get(watch_var)
            except KeyError:
                raise myokit.FindNanError(
                    'Variable <' + str(watch_var) + '> not found.')
            if not watch_var.is_state():
                raise myokit.FindNanError(
                    'The watched variable must be a state.')
            try:
                lo, hi = safe_range
            except Exception:
                raise myokit.FindNanError(
                    'A safe range must be specified for the watched variable'
                    ' as a tuple (lower, upper).')
            if lo >= hi:
                raise myokit.FindNanError(
                    'The safe range must have a lower bound that is lower than'
                    ' the upper bound.')

            def find_error_position(_log):
                # Find first occurence of out-of-bounds error
                ifirst = None
                kfirst = None
                post = '.' + watch_var.qname()
                lower, upper = safe_range
                for dims in myokit._dimco(*self._dims):
                    key = '.'.join([str(x) for x in dims]) + post
                    ar = np.array(_log[key], copy=False)
                    i = np.where(
                        (ar < lower)
                        | (ar > upper)
                        | np.isnan(ar)
                        | np.isinf(ar))[0]
                    if len(i) > 0:
                        i = i[0]
                        if ifirst is None:
                            kfirst = key
                            ifirst = i
                        elif i < ifirst:
                            kfirst = key
                            ifirst = i
                        if i == 0:
                            break
                return ifirst, kfirst

        # Get the name of a time variable
        time_var = self._model.time().qname()

        # Deep searching function
        def relog(_log, _dt):
            # Get first occurence of error
            ifirst, kfirst = find_error_position(_log)
            if kfirst is None:
                raise myokit.FindNanError('Error condition not found in log.')
            if ifirst == 0:
                raise myokit.FindNanError(
                    'Unable to work with simulation logs where the error'
                    ' condition is met in the very first data point.')

            # Position to start deep search at
            istart = ifirst - 1

            # Get last logged state before error
            state = []
            for dims in myokit._dimco(*self._dims):
                pre = '.'.join([str(x) for x in dims]) + '.'
                for s in self._model.states():
                    state.append(_log[pre + s.qname()][istart])

            # Get last time before error
            time = _log[time_var][istart]

            # Save current state & time
            old_state = self._state
            old_time = self._time
            self._state = state
            self._time = time

            # Run until next time point, log every step
            duration = _log[time_var][ifirst] - time
            _log = self.run(
                duration, log=myokit.LOG_BOUND + myokit.LOG_STATE,
                log_interval=_dt, report_nan=False)

            # Reset simulation to original state
            self._state = old_state
            self._time = old_time

            # Return new log
            return _log

        # Get time step
        try:
            dt = log[time_var][1] - log[time_var][0]
        except IndexError:
            # Unable to guess dt!
            # So... Nan occurs before the first log interval is reached
            # That probably means dt was relatively large, so guess it was
            # large! Assuming milliseconds, start off with dt=5ms
            dt = 5

        # Search with successively fine log interval
        while dt > 0:
            dt *= 0.1
            if dt < 0.5:
                dt = 0
            log = relog(log, dt)

        # Search for first occurrence of error in the detailed log
        ifirst, kfirst = find_error_position(log)

        # Get indices of cell in state vector
        ndims = len(self._dims)
        icell = [int(x) for x in kfirst.split('.')[0:ndims]]

        # Get state & bound before, during and after error
        def state(index, icell):
            s = []
            b = {}
            for var in self._model.states():
                s.append(log[var.qname(), icell][index])
            for var in self._model.variables(bound=True):
                if var.binding() in self._global:
                    b[var.qname()] = log[var.qname()][index]
                else:
                    b[var.qname()] = log[var.qname(), icell][index]
            return s, b

        # Get error cell's states before, during and after
        times = []
        states = []
        bounds = []
        max_states = 3
        for k in range(ifirst, ifirst - max_states - 1, -1):
            if k < 0:
                break
            times.append(log[time_var][k])
            s, b = state(k, icell)
            states.append(s)
            bounds.append(b)

        # Get variable causing error
        var = self._model.get('.'.join(kfirst.split('.')[ndims:]))

        # Get value causing error
        value = states[1][var.indice()]
        var = var.qname()

        # Get time error occurred
        time = log[time_var][ifirst]

        # Get all variables at shown states
        if return_log:
            # Get earliest state in states/bounds
            state = []
            istart = max(0, ifirst - max_states)
            for dims in myokit._dimco(*self._dims):
                pre = '.'.join([str(x) for x in dims]) + '.'
                for s in self._model.states():
                    state.append(log[pre + s.qname()][istart])

            # Save current state & time, and rewind
            old_state = self._state
            old_time = self._time
            self._state = state
            self._time = times[-1]

            # Run for all states
            duration = len(times) * self._step_size
            log = self.run(
                duration,
                log=myokit.LOG_BOUND + myokit.LOG_STATE + myokit.LOG_INTER,
                log_interval=0,
                report_nan=False)

            # Reset simulation to original state
            self._state = old_state
            self._time = old_time

            # Return
            return time, icell, var, value, states, bounds, log

        return time, icell, var, value, states, bounds

    def is2d(self):
        """Deprecated alias of :meth:`is_2d()`."""
        # Deprecated since 2020-09-10
        import warnings
        warnings.warn('The method SimulationOpenCL.is2d() is deprecated.'
                      ' Please use is_2d() instead.')
        return self.is_2d()

    def is_2d(self):
        """Returns ``True`` if and only if this is a 2d simulation. """
        return len(self._dims) == 2

    def is_paced(self, x, y=None):
        """
        Returns ``True`` if and only if the cell at index ``x`` (or index
        ``(x, y)`` in 2d simulations) will be paced during simulations.
        """
        # Check input
        x = int(x)
        if x < 0 or x >= self._dims[0]:
            raise ValueError('X-coordinate out of range: ' + str(x) + '.')
        if len(self._dims) == 2:
            if y is None:
                raise ValueError(
                    'No y-coordinate specified in 2-dimensional simulation.')
            y = int(y)
            if y < 0 or y >= self._dims[1]:
                raise ValueError('Y-coordinate out of range: ' + str(y) + '.')
        else:
            if not (y is None or y == 0):
                raise ValueError(
                    'Y-coordinate specified in 1-dimensional simulation.')
            y = 0

        # Pacing rectangle
        if type(self._paced_cells) == tuple:
            nx, ny, xmin, ymin = self._paced_cells
            return (x >= xmin and x < xmin + nx and
                    y >= ymin and y < ymin + ny)

        # Explicit cell selection
        cid = x + y * self._dims[0]
        return cid in self._paced_cells

    def neighbours(self, x, y=None):
        """
        Returns a list of indices specifying the neighbours of the cell at
        index ``x`` (or index ``(x, y)`` for 2d simulations).

        Indices are given either as integers (1d or arbitrary geometry) or as
        tuples (2d).
        """
        # Check input
        x = int(x)
        if x < 0 or x >= self._dims[0]:
            raise ValueError('X-coordinate out of range: ' + str(x) + '.')
        if len(self._dims) == 2:
            if y is None:
                raise ValueError(
                    'No y-coordinate specified in 2-dimensional simulation.')
            y = int(y)
            if y < 0 or y >= self._dims[1]:
                raise ValueError('Y-coordinate out of range: ' + str(y) + '.')
        else:
            if not (y is None or y == 0):
                raise ValueError(
                    'Y-coordinate specified in 1-dimensional simulation.')

        # User-specified connections (always 1d)
        if self._connections is not None:
            neighbours = []
            for i, j, c in self._connections:
                if i == x:
                    neighbours.append(j)
                elif j == x:
                    neighbours.append(i)
            return neighbours

        # Left and right neighbours
        neighbours = []
        if x > 0:
            neighbours.append(x - 1)
        if x + 1 < self._dims[0]:
            neighbours.append(x + 1)

        # Top and bottom neighbours
        if len(self._dims) == 2:
            neighbours = [(i, y) for i in neighbours]
            if y > 0:
                neighbours.append((x, y - 1))
            if y + 1 < self._dims[1]:
                neighbours.append((x, y + 1))
        return neighbours

    def pre(self, duration, report_nan=True, progress=None,
            msg='Pre-pacing SimulationOpenCL'):
        """
        This method can be used to perform an unlogged simulation, typically to
        pre-pace to a (semi-)stable orbit.

        After running this method

        - The simulation time is **not** affected
        - The current state and the default state are updated to the final
          state reached in the simulation.

        Calls to :meth:`reset` after using :meth:`pre` will revert the
        simulation to this new default state.

        If numerical errors during the simulation lead to NaNs appearing in the
        result, the ``find_nan`` method will be used to pinpoint their
        location. Next, a call to the model's rhs will be evaluated in python
        using checks for numerical errors to pinpoint the offending equation.
        The results of these operations will be written to ``stdout``. To
        disable this feature, set ``report_nan=False``.

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as `msg`.
        """
        self._run(duration, myokit.LOG_NONE, 1, report_nan, progress, msg)
        self._default_state = list(self._state)

    def remove_field(self, var):
        """
        Removes any field set for the given variable.
        """
        if isinstance(var, myokit.Variable):
            var = var.qname()
        var = self._model.get(var)
        try:
            del(self._fields[var])
        except KeyError:
            pass

    def reset(self):
        """
        Resets the simulations:

        - The time variable is set to 0
        - The current state is set to the default state (either the model's
          initial state or the last state reached using :meth:`pre`)

        """
        self._time = 0
        self._state = list(self._default_state)

    def run(self, duration, log=None, log_interval=1.0, report_nan=True,
            progress=None, msg='Running SimulationOpenCL'):
        """
        Runs a simulation and returns the logged results. Running a simulation
        has the following effects:

        - The internal state is updated to the last state in the simulation.
        - The simulation's time variable is updated to reflect the time
          elapsed during the simulation.

        The number of time units to simulate can be set with ``duration``.

        The variables to log can be indicated using the ``log`` argument. There
        are several options for its value:

        - ``None`` (default), to log all states
        - An integer flag or a combination of flags. Options:
          ``myokit.LOG_NONE``, ``myokit.LOG_STATE``, ``myokit.LOG_BOUND``,
          ``myokit.LOG_INTER`` or ``myokit.LOG_ALL``.
        - A list of qnames or variable objects
        - A :class:`myokit.DataLog` object or another dictionary of
           ``qname : list`` mappings.

        For more details on the ``log`` argument, see the function
        :meth:`myokit.prepare_log`.

        Variables that vary from cell to cell will be logged with a prefix
        indicating the cell index. For example, when using::

            s = SimulationOpenCL(m, p, ncells=256)
            d = s.run(1000, log=['engine.time', 'membrane.V']

        where ``engine.time`` is bound to ``time`` and ``membrane.V`` is the
        membrane potential variable, the resulting log will contain the
        following variables::

            {
                'engine.time'  : [...],
                '0.membrane.V' : [...],
                '1.membrane.V' : [...],
                '2.membrane.V' : [...],
            }

        Alternatively, you can specify variables exactly::

            d = s.run(1000, log=['engine.time', '0.membrane.V']

        For 2d simulations, the naming scheme ``x.y.name`` is used, for
        example ``0.0.membrane.V``.

        A log entry will be made every time *at least* ``log_interval`` time
        units have passed. No guarantee is given about the exact time log
        entries will be made, but the value of any logged time variable is
        guaranteed to be accurate.

        If numerical errors during the simulation lead to NaNs appearing in the
        result, the ``find_nan`` method will be used to pinpoint their
        location. Next, a call to the model's rhs will be evaluated in python
        using checks for numerical errors to pinpoint the offending equation.
        The results of these operations will be written to ``stdout``. To
        disable this feature, set ``report_nan=False``.

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as `msg`.
         """
        r = self._run(duration, log, log_interval, report_nan, progress, msg)
        self._time += duration
        return r

    def _run(self, duration, log, log_interval, report_nan, progress, msg):
        # Simulation times
        if duration < 0:
            raise Exception('Simulation time can\'t be negative.')
        tmin = self._time
        tmax = tmin + duration

        # Gather global variables in model
        g = []
        for label in self._global:
            v = self._model.binding(label)
            if v is not None:
                g.append(v.qname())

        # Parse log argument
        log = myokit.prepare_log(
            log,
            self._model,
            dims=self._dims,
            global_vars=g,
            if_empty=myokit.LOG_STATE + myokit.LOG_BOUND,
            allowed_classes=myokit.LOG_STATE + myokit.LOG_INTER
            + myokit.LOG_BOUND,
            precision=self._precision)

        # Create list of intermediary variables that need to be logged
        inter_log = []
        vars_checked = set()
        for var in log.keys():
            var = myokit.split_key(var)[1]
            if var in vars_checked:
                continue
            vars_checked.add(var)
            var = self._model.get(var)
            if var.is_intermediary() and not var.is_bound():
                inter_log.append(var)

        # Get preferred platform/device combo from configuration file
        platform, device = myokit.OpenCL.load_selection_bytes()

        # Compile template into string with kernel code
        kernel_file = os.path.join(myokit.DIR_CFUNC, KERNEL_FILE)
        args = {
            'model': self._model,
            'precision': self._precision,
            'native_math': self._native_math,
            'bound_variables': self._bound_variables,
            'inter_log': inter_log,
            'diffusion': self._diffusion_enabled,
            'fields': self._fields.keys(),
            'paced_cells': self._paced_cells,
            'rl_states': self._rl_states,
        }
        if myokit.DEBUG:
            print('-' * 79)
            print(
                self._code(kernel_file, args,
                           line_numbers=myokit.DEBUG_LINE_NUMBERS))
            import sys
            sys.exit(1)
        kernel = self._export(kernel_file, args)

        # Logging period (0 = disabled)
        log_interval = 1e-9 if log_interval is None else float(log_interval)
        if log_interval <= 0:
            log_interval = 1e-9

        # Create field values vector
        n = len(self._fields) * self._nx * self._ny
        if n:
            field_data = self._fields.values()
            field_data = [np.array(x, copy=False) for x in field_data]
            field_data = np.vstack(field_data)
            field_data = list(field_data.reshape(n, order='F'))
        else:
            field_data = []

        # Get progress indication function (if any)
        if progress is None:
            progress = myokit._Simulation_progress
        if progress:
            if not isinstance(progress, myokit.ProgressReporter):
                raise ValueError(
                    'The argument "progress" must be either a subclass of'
                    ' myokit.ProgressReporter or None.')

        # Run simulation
        arithmetic_error = False
        if duration > 0:
            # Initialize
            state_in = self._state
            state_out = list(state_in)
            self._sim.sim_init(
                platform,
                device,
                kernel,
                self._nx,
                self._ny,
                self._diffusion_enabled,
                self._gx,
                self._gy,
                self._connections,
                tmin,
                tmax,
                self._step_size,
                state_in,
                state_out,
                self._protocol,
                log,
                log_interval,
                [x.qname().encode('ascii') for x in inter_log],
                field_data,
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
            except ArithmeticError:
                arithmetic_error = True
            finally:
                # Clean even after KeyboardInterrupt or other Exception
                self._sim.sim_clean()
            # Update state
            self._state = state_out

        # Check for NaN
        if report_nan and (arithmetic_error or log.has_nan()):
            txt = ['Numerical error found in simulation logs.']
            try:
                # NaN encountered, show how it happened
                time, icell, var, value, states, bounds, d = self.find_nan(
                    log, return_log=True)
                icell_str = '(' + ','.join([str(x) for x in icell]) + ')'
                txt.append(
                    'Encountered numerical error at t='
                    + myokit.float.str(time, precision=self._precision)
                    + ' in cell ' + icell_str + ' when ' + var + '='
                    + myokit.float.str(value, precision=self._precision) + '.')

                # Check if this cell was paced.
                is_paced = self.is_paced(*icell)
                is_paced_str = (', cell ' + icell_str + ' '
                                + ('IS' if is_paced else 'is NOT') + ' paced')

                # Get the names of the variables used in bindings, to use when
                # calculating the derivatives
                vtime = self._model.time().qname()
                vpace = self._model.binding('pace')
                vpace = None if vpace is None else vpace.qname()
                vdiff = None
                if self._diffusion_enabled:
                    vdiff = self._model.binding('diffusion_current')
                    vdiff = None if vdiff is None else vdiff.qname()

                # List all neighbours for this cell
                neighbours = self.neighbours(*icell)
                if len(self._dims) == 2:
                    neighbours_str = ', '.join(
                        ('(' + ','.join([str(i) for i in j]) + ')')
                        for j in neighbours)
                else:
                    neighbours_str = ', '.join(str(j) for j in neighbours)

                # Show final state
                txt.append('State during:')
                txt.append(self._model.format_state(
                    states[0], precision=self._precision))

                # Show bound variables
                txt.append('Simulation variables during:')
                txt.append('  Time: ' + myokit.float.str(
                    bounds[0][vtime], precision=self._precision))
                if vpace:
                    txt.append(
                        '  Pacing variable: ' + myokit.float.str(
                            bounds[0][vpace], precision=self._precision)
                        + is_paced_str)
                if vdiff:
                    txt.append(
                        '  Diffusion current: ' + myokit.float.str(
                            bounds[0][vdiff], precision=self._precision))
                if neighbours:
                    txt.append('  Connected cells: ' + neighbours_str)

                # Show previous state (and derivatives)
                n_states = len(states)
                txt.append('Obtained ' + str(n_states) + ' previous state(s).')
                if n_states > 1:
                    # Get state and input at previous state
                    state = states[1]
                    bound = {
                        'time': bounds[1][vtime],
                        'pace': 0,
                        'diffusion_current': 0,
                    }
                    if is_paced and vpace is not None:
                        bound['pace'] = bounds[1][vpace]
                    if vdiff is not None:
                        bound['diffusion_current'] = bounds[1][vdiff]

                    # Evaluate state derivatives
                    eval_error = None
                    try:
                        derivs = self._model.eval_state_derivatives(
                            state, bound, self._precision, ignore_errors=False)
                    except myokit.NumericalError as ee:
                        derivs = self._model.eval_state_derivatives(
                            state, bound, self._precision, ignore_errors=True)
                        eval_error = str(ee)

                    # Show state and derivatives
                    txt.append('State before:')
                    txt.append(self._model.format_state_derivatives(
                        state, derivs, self._precision))

                    # Show bound variables
                    txt.append('Simulation variables before:')
                    txt.append('  Time: ' + myokit.float.str(
                        bounds[1][vtime], precision=self._precision))
                    if vpace:
                        txt.append(
                            '  Pacing variable: ' + myokit.float.str(
                                bounds[1][vpace], precision=self._precision)
                            + is_paced_str)
                    if vdiff:
                        txt.append(
                            '  Diffusion current: ' + myokit.float.str(
                                bounds[1][vdiff], precision=self._precision))
                    if neighbours:
                        txt.append('  Connected cells: ' + neighbours_str)

                    # Show all variables with non-finite values
                    txt.append(
                        'Logged all variables for points: ' + ', '.join(
                            myokit.float.str(t, precision=self._precision)
                            for t in d.time()))
                    txt.append(
                        'Non-finite valued variables at t=' + myokit.float.str(
                            d.time()[-2], precision=self._precision))
                    for key, values in d.items():
                        value = values[-2]
                        if not np.isfinite(value):
                            txt.append(
                                '  ' + str(key) + ' = ' + myokit.float.str(
                                    value, precision=self._precision))

                    # Show any error in evaluating derivatives
                    if eval_error is not None:
                        txt.append('Error when evaluating derivatives:')
                        txt.append(eval_error)

            except myokit.FindNanError as e:
                txt.append(
                    'Unable to pinpoint source of NaN, an error occurred:')
                txt.append(str(e))
            raise myokit.SimulationError('\n'.join(txt))

        # Return log
        return log

    def set_conductance(self, gx=10, gy=5):
        """
        Sets the cell-to-cell conductance used in this simulation.

        For 1d simulations, only ``gx`` will be used and the argument ``gy``
        can be omitted. For 2d simulations both arguments should be set.

        The diffusion current is calculated as::

            i = gx * ((V - V_xnext) - (V_xlast - V))
              + gy * ((V - V_ynext) - (V_ylast - V))

        Where the second term ``gy * ...`` is only used for 2d simulations. At
        the boundaries, where either ``V_ilast`` or ``V_inext`` is unavailable,
        the value of ``V`` is substituted, causing the term to go to zero.

        For a model with currents in ``[uA/uF]`` and voltage in ``[mV]``,
        `gx`` and ``gy`` have the unit ``[mS/uF]``.
        """
        self._gx = float(gx)
        self._gy = float(gy)

    def set_connections(self, connections):
        """
        Adds a list of connections between cells, each with their own
        conductance. This allows the creation of arbitrary geometries.

        The ``connections`` list should be given as a list of tuples
        ``(cell1, cell2, conductance)``.

        Connections are only supported for "1d" simulations (even though the
        simulated geometry may have any number of dimensions).

        Setting a connection list overrules the conductances set with
        :meth:`set_conductance`.
        """
        if connections is None:
            self._connections = None
            return
        if len(self._dims) != 1:
            raise ValueError('Connections can only be specified in 1d mode.')
        conns = []
        doubles = set()
        for x in connections:
            try:
                i, j, c = x
            except Exception:
                raise ValueError(
                    'Connections must be None or a list of 3-tuples'
                    ' (cell_index_1, cell_index_2, conductance).')

            # Check indices
            i, j = int(i), int(j)
            if i == j or i < 0 or j < 0 or i >= self._nx or j >= self._nx:
                raise ValueError(
                    'Invalid connection: (' + str(i) + ', ' + str(j) + ', '
                    + str(c) + ')')

            # Order indices, and detect doubles
            i, j = (i, j) if i < j else (j, i)
            if (i, j) in doubles:
                raise ValueError(
                    'Duplicate connection: (' + str(i) + ', ' + str(j) + ', '
                    + str(c) + ')')
            doubles.add((i, j))

            # Check conductance
            c = float(c)
            if c < 0:
                raise ValueError('Invalid conductance: ' + str(c))

            # Store connection
            conns.append((i, j, c))
        del(doubles)
        self._connections = conns

    def set_constant(self, var, value):
        """
        Changes a model constant. Only literal constants (constants not
        dependent on any other variable) can be changed.

        The constant ``var`` can be given as a :class:`Variable` or a string
        containing a variable qname. The ``value`` should be given as a float.

        Note that any scalar fields set for the same variable will overwrite
        this value without warning.
        """
        value = float(value)
        if isinstance(var, myokit.Variable):
            var = var.qname()
        var = self._model.get(var)
        if not var.is_literal():
            raise ValueError(
                'The given variable <' + var.qname() + '> is not a literal.')
        # Update value in internal model (will update its defined value when
        # the kernel is generated before the next run).
        self._model.set_value(var.qname(), value)

    def set_default_state(self, state, x=None, y=None):
        """
        Changes this simulation's default state.

        This can be used in three different ways:

        1. When called with an argument ``state`` of size ``n_states`` and
           ``x=None`` the given state will be set as the new state of all
           cells in the simulation.
        2. Called with an argument ``state`` of size n_states and
           ``x, y`` equal to a valid cell index, this method will update only
           the selected cell's state.
        3. Finally, when called with a ``state`` of size ``n_states * n_cells``
           the method will treat ``state`` as a concatenation of state vectors
           for each cell.

        """
        self._default_state = self._set_state(state, x, y, self._default_state)

    def set_field(self, var, values):
        """
        Can be used to replace a model constant with a scalar field.

        The argument ``var`` must specify a variable from the simulation's
        model. The field itself is given as ``values``, which must have the
        dimensions ``(ny, nx)``. Multiple fields can be added, depending on the
        memory available on the device. If a field is added for a variable
        already associated with a field, the old data will be overwritten.

        With diffusion currents enabled, this method can let you simulate
        heterogeneous tissue properties. With diffusion disabled, it can be
        used to investigate the effects of changing a parameter through the
        parallel simulation of several cells.
        """
        # Check variable
        if isinstance(var, myokit.Variable):
            var = var.qname()
        var = self._model.get(var)
        if not var.is_constant():
            raise ValueError('Only constants can be used for fields.')
        if var.is_bound():
            raise ValueError('Bound values cannot be replaced by fields.')
        # Check values
        values = np.array(values, copy=False, dtype=float)
        if len(self._dims) == 1:
            if values.shape != (self._nx, ):
                raise ValueError(
                    'The argument `values` must have length ' + str(self._nx)
                    + '.')
        else:
            shape = (self._ny, self._nx)
            if values.shape != shape:
                raise ValueError(
                    'The argument `values` must have dimensions' + str(shape)
                    + '.')
        # Add field
        self._fields[var] = list(values.reshape(self._nx * self._ny))

    def set_paced_cells(self, nx=5, ny=5, x=0, y=0):
        """
        Sets the number of cells that will receive a stimulus from the pacing
        protocol. For 1d simulations, the values ``ny`` and ``y`` will be
        ignored.

        This method can only define rectangular pacing areas. To select an
        arbitrary set of cells, use :meth:`set_paced_cell_list`.

        If diffusion is disabled all cells will be paced.

        Arguments:

        ``nx``
            The number of cells/nodes in the x-direction. If a negative number
            of cells is set the cells left of the offset (``x``) are
            stimulated.
        ``ny``
            The number of cells/nodes in the y-direction. If a negative number
            of cells is set the cells left of the offset (``x``) are
            stimulated.
        ``x``
            The offset of the pacing rectangle in the x-direction. If a
            negative offset is given the offset is calculated from right to
            left.
        ``y``
            The offset of the pacing rectangle in the y-direction. If a
            negative offset is given the offset is calculated from bottom to
            top.
        """
        # Check nx and x. Allow cell selections outside of the boders!
        nx = int(nx)
        x = int(x)
        if nx < 0:
            nx = -nx
            x -= nx
        if x < 0:
            x += self._nx

        # Check dimensions
        if len(self._dims) == 1:
            # Use default for y
            ny = 1
            y = 0
        else:
            # Check ny and y
            ny = int(ny)
            if ny < 0:
                ny = -ny
                y -= ny
            if y < 0:
                y += self._ny

        # Set tuple of paced cells
        self._paced_cells = (nx, ny, x, y)

    def set_paced_cell_list(self, cells):
        """
        Selects the cells to be paced using a list of cell indices. In 1d
        simulations a cell index is an integer ``i``, in 2d simulations cell
        indices are specified as tuples ``(i, j)``.

        For large numbers of cells, this method becomes very inefficient. In
        these cases it may be better to use a rectangular pacing area set using
        :meth:`set_paced_cells`.

        If diffusion is disabled all cells will be paced.
        """
        paced_cells = []
        if len(self._dims) == 1:
            for cell in cells:
                cell = int(cell)
                if cell < 0 or cell >= self._nx:
                    raise ValueError(
                        'Cell index out of range: ' + str(cell) + '.')
                paced_cells.append(cell)
        else:
            for i, j in cells:
                i, j = int(i), int(j)
                if i < 0 or j < 0 or i >= self._nx or j >= self._ny:
                    raise ValueError(
                        'Cell index out of range: (' + str(i) + ', ' + str(j)
                        + ').')
                paced_cells.append(i + j * self._nx)
        # Set list of paced cells
        self._paced_cells = paced_cells

    def set_protocol(self, protocol=None):
        """
        Changes the pacing protocol used by this simulation.
        """
        if protocol is None:
            self._protocol = None
        else:
            self._protocol = protocol.clone()

    def _set_state(self, state, x, y, update):
        """
        Handles set_state and set_default_state.
        """
        n = len(state)
        if n == self._nstate * self._ntotal:
            return list(state)
        elif n != self._nstate:
            raise ValueError(
                'Given state must have the same size as a single'
                ' cell state or a full simulation state')
        if x is None:
            # State might not be a list, at this point...
            return list(state) * self._ntotal
        # Set specific cell state
        x = int(x)
        if x < 0 or x >= self._nx:
            raise KeyError('Given x-index out of range.')
        if len(self._dims) == 2:
            y = int(y)
            if y < 0 or y >= self._ny:
                raise KeyError('Given y-index out of range.')
            x += y * self._nx
        offset = x * self._nstate
        update[offset:offset + self._nstate] = state
        return update

    def set_state(self, state, x=None, y=None):
        """
        Changes the state of this simulation's model.

        This can be used in three different ways:

        1. When called with an argument ``state`` of size ``n_states`` and
           ``x=None`` the given state will be set as the new state of all
           cells in the simulation.
        2. Called with an argument ``state`` of size n_states and
           ``x, y`` equal to a valid cell index, this method will update only
           the selected cell's state.
        3. Finally, when called with a ``state`` of size ``n_states * n_cells``
           the method will treat ``state`` as a concatenation of state vectors
           for each cell.

        """
        self._state = self._set_state(state, x, y, self._state)

    def set_step_size(self, step_size=0.005):
        """
        Sets the step size used in the forward Euler solving routine.
        """
        step_size = float(step_size)
        if step_size <= 0:
            raise ValueError('Step size must be greater than zero.')
        self._step_size = step_size

    def set_time(self, time=0):
        """
        Sets the current simulation time.
        """
        self._time = float(time)

    def shape(self):
        """
        Returns the shape of this Simulation's grid of cells as a tuple
        ``(ny, nx)`` for 2d simulations, or a single value ``nx`` for 1d
        simulations.
        """
        if len(self._dims) == 2:
            return (self._ny, self._nx)
        return self._nx

    def state(self, x=None, y=None):
        """
        Returns the current simulation state as a list of ``len(state) *
        ncells`` floating point values.

        If the optional arguments ``x`` and ``y`` specify a valid cell index a
        single cell's state is returned. For example ``state(4)`` can be
        used with a 1d simulation, while ``state(4, 2)`` is a valid index in
        the 2d case.
        """
        if x is None:
            return list(self._state)
        else:
            x = int(x)
            if x < 0 or x >= self._nx:
                raise KeyError('Given x-index out of range.')
            if len(self._dims) == 2:
                y = int(y)
                if y < 0 or y >= self._ny:
                    raise KeyError('Given y-index out of range.')
                x += y * self._nx
            return self._state[x * self._nstate:(x + 1) * self._nstate]

    def step_size(self):
        """
        Returns the current step size.
        """
        return self._step_size

    def time(self):
        """
        Returns the current simulation time.
        """
        return self._time


KEYWORDS = [
    'AtomicAdd',
    'calculate_pacing',
    'cell1',
    'cell2',
    'cell_step',
    'cid',
    'conductance',
    'ctx',
    'cty',
    'diff_step',
    'diff_arb_step',
    'diff_arb_reset',
    'diff_step_fiber_tissue',
    'dt',
    'floatVal',
    'gft',
    'gx',
    'gy',
    'i1',
    'i2',
    'i12',
    'idiff',
    'idiff_f',
    'idiff_in',
    'idiff_t',
    'iff',
    'ift',
    'inter_log',
    'intVal',
    'ivf',
    'ivt',
    'ix',
    'iy',
    'i_vm',
    'newVal',
    'nfx',
    'nfy',
    'nsf',
    'nst',
    'ntx',
    'nx',
    'nx_paced',
    'ny',
    'ny_paced',
    'n_inter',
    'n_state',
    'of1',
    'of2',
    'off',
    'ofm',
    'ofp',
    'oft',
    'operand',
    'pace',
    'pace_in',
    'prevVal',
    'Real',
    'source',
    'state',
    'state_f',
    'state_t',
    'time',
]
