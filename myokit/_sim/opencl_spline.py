#
# OpenCL driven simulation, 1d or 2d
#
# This file is part of Myokit
#  Copyright 2011-2014 Michael Clerx, Maastricht University
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import myokit
# Location of C and OpenCL sources
SOURCE_FILE = 'opencl_spline.c'
KERNEL_FILE = 'opencl_spline.cl'
class SimulationOpenCLSpline(myokit.CModule):
    """
    Can run 1d or 2d simulations based on a :class:`model <Model>` using
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
    ``npaced``
        The number of cells that will receive a stimulus from the pacing
        protocol. Must have the same dimension as ``ncells``.
    ``g``
        The cell to cell conductance. Either a scalar or a tuple ``(gx, gy)``,
        must have the same dimension as ``ncells``.
    ``dt``
        The time step to use in the forward-Euler integration scheme.
    ``double_precision``
        Set this to True if your OpenCL device supports double precision. This
        will greatly reduce the chance of a divide-by-zero or other numerical
        error introducing NaNs into the simulation.
    
    The simulation provides the following inputs variables can bind to:
    
    ``time`` (global)
        The simulation time
    ``pace`` (per-cell)
        The pacing level, this is set if a protocol was passed in.
    ``precision``
        Can be set to ``myokit.SINGLE_PRECISION`` (default) or
        ``myokit.DOUBLE_PRECISION`` if the used device supports it.
        
    The variable ``time`` is set globally, meaning each cell uses the same
    value. The variables ``pace`` and ``diffusion_current`` have different 
    values per cell.
        
    The following labeled variables are required for this simulation to work:
    
    ``membrane_potential``
        The variable representing the membrane potential.
        
    The ``diffusion_current`` is calculated as::
    
        i = gx * ((V - V_xnext) - (V_xlast - V))
          + gy * ((V - V_ynext) - (V_ylast - V))
        
    Where the second term ``gy * ...`` is only used for 2d simulations. At the
    boundaries, where either ``V_ilast`` or ``V_inext`` is unavailable, the
    value of ``V`` is substituted, causing the term to go to zero. The values
    of ``gx`` and ``gy`` can be set in the simulation's constructor.
    
    For a typical model with currents in ``[uA/uF]`` and voltage in ``[mV]``, 
    `gx`` and ``gy`` have the unit ``[mS/uF]``.

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
    allows you to pre-pace a model, run a simulation, reset to the pre-paced
    state, run another simulation etc.
    
    The model passed to the simulation is cloned and stored internally, so
    changes to the original model object will not affect the simulation.
    
    Because GPU cores typically have a smaller memory than CPUs, some care is
    needed to reduce the memory footprint of the code that calculates the state
    update for each cell. Myokit tries to accomplish this by placing each
    component's calculations in a separate function. This has the advantage
    that any space occupied by intermediary variables used in the component can
    be freed for re-use once the function has finished. However, this strategy
    has two repercussions:
    
      - Models used in a SimulationOpenCLSpline need to have independent
        components. That is, it should be possible to evaluate the model's
        variables component by component.
      - Intermediary variables (for example currents) are calculated on the
        GPU, used, and then discarded. As a result they are not available for
        logging.
        
    """
    _index = 0 # Unique id for this object
    def __init__(self, model, protocol=None, ncells=256, npaced=5, g=9.5,
            dt=0.005, precision=myokit.SINGLE_PRECISION):
        super(SimulationOpenCLSpline, self).__init__()
        # Which external variables are global?
        self._global = ['time', 'pace']
        # Require a valid model
        model.validate()
        # Require independent components
        if model.has_interdependent_components():
            cycles = '\n'.join([
                '  ' + ' > '.join([x.var().qname() for x in c])
                for c in model.component_cycles()])
            raise Exception('This simulation requires models without'
                ' interdependent components. Please restructure the model and'
                ' re-run.\nCycles:\n' + cycles)
        # Clone model, store
        model = model.clone()
        self._model = model
        # Set protocol
        self.set_protocol(protocol)
        # Get membrane potential variable
        self._vm = model.label('membrane_potential')
        if self._vm is None:
            raise Exception('This simulation requires the membrane potential'
                ' variable to be labelled as "membrane_potential".')
        if not self._vm.is_state():
            raise Exception('The variable labelled as membrane potential must'
                ' be a state variable.')
        if self._vm.is_referenced():
            raise Exception('This simulation requires that no other variables'
                ' depend on the time-derivative of the membrane potential.')
        # Check for binding to diffusion_current
        idiffs = model.bindings_for('diffusion_current')
        if len(idiffs) == 0:
            raise Exception('This simulation requires a variable to be bound'
                ' to "diffusion_current" to pass current from one cell to the'
                ' next.')
        # Check dimensionality, number of cells
        try:
            if len(ncells) != 2:
                raise ValueError('The argument "ncells" must be either a'
                    ' scalar or a tuple (nx, ny).')
            self._dims = 2
        except TypeError:
            self._dims = 1
        # Check dimension dependent arguments
        if self._dims == 1:
            self._nx = int(ncells)
            self._ny = 1
            self._nx_paced = int(npaced)
            self._ny_paced = 1
            self._gx = float(g)
            self._gy = 0
            self._dims = (self._nx,)
        else:
            self._nx = int(ncells[0])
            self._ny = int(ncells[1])
            try:
                self._nx_paced = int(npaced[0])
                self._ny_paced = int(npaced[1])
            except TypeError:
                self._nx_paced = int(npaced)
                self._ny_paced = int(npaced)
            try:
                self._gx = float(g[0])
                self._gy = float(g[1])
            except TypeError:
                self._gx = float(g)
                self._gy = float(g)            
            self._dims = (self._nx, self._ny)
        if self._nx < 1 or self._ny < 1:
            raise ValueError('The number of cells in any direction must be at'
                ' least 1.')
        if self._nx_paced < 1 or self._ny_paced < 1:
            raise ValueError('The number of cells to stimulate can not be'
                ' negative.')
        self._ntotal = self._nx * self._ny
        # Set step size
        dt = float(dt)
        if dt <= 0:
            raise ValueError('The step size must be greater than zero.')
        self._step_size = dt
        # Precision
        if precision not in (myokit.SINGLE_PRECISION, myokit.DOUBLE_PRECISION):
            raise ValueError('Only single and double precision are supported.')
        self._precision = precision
        # Always use native maths
        self._native_math = True
        # Set remaining properties
        self._time = 0
        self._nstate = self._model.count_states()
        # Set state and default state
        self._state = self._model.state() * self._ntotal
        self._default_state = list(self._state)
        # Process bindings, remove unsupported bindings, get map of bound
        # variables to internal names.
        self._bound_variables = model.process_bindings({
            'time'      : 'time',
            'pace'      : 'pace',
            'diffusion_current' : 'idiff',
            })
        # Reserve keywords
        from myokit.formats import opencl
        model.reserve_unique_names(*opencl.keywords)
        model.reserve_unique_names(
            *['calc_' + c.name() for c in model.components()])
        model.reserve_unique_names(
            *['D_' + c.uname() for c in model.states()])
        model.reserve_unique_names(
            'cell_step',
            'cid',
            'ctx',
            'cty',
            'diff_step',
            'dt,'
            'gft',
            'gx',
            'gy',
            'idiff',
            'idiff_f',
            'idiff_in',
            'idiff_t',
            'iff',
            'ift',
            'ivf',
            'ivt',
            'ix',
            'iy',
            'i_vm',
            'nfx',
            'nfy',
            'nsf',
            'nst',
            'ntx',
            'nx',
            'nx_paced',
            'ny',
            'ny_paced',
            'n_state',
            'off',
            'ofm',            
            'ofp',
            'oft',
            'pace',
            'pace_in',
            'Real',
            'state',
            'state_f',
            'state_t',
            'time',
            )
        model.create_unique_names()
        # Create back-end
        self._create_backend()
    def _create_backend(self):
        """
        Creates this simulation's backend.
        """
        # Unique simulation id
        SimulationOpenCLSpline._index += 1
        mname = 'myokit_sim_opencl_' + str(SimulationOpenCLSpline._index)
        fname = os.path.join(myokit.DIR_CFUNC, SOURCE_FILE)
        # Arguments
        self._args = {
            'module_name' : mname,
            'model' : self._model,
            'vmvar' : self._vm,
            'precision' : self._precision,
            'bound_variables' : self._bound_variables,
            'native_math' : self._native_math,
            'dims' : len(self._dims),
            }
        # Create kernel
        self._kernel_file=os.path.join(myokit.DIR_CFUNC, KERNEL_FILE)
        self._kernel = self._export(self._kernel_file, self._args)
        # Debug
        if myokit.DEBUG:
            print(self._code(fname, self._args, line_numbers=True))
            print('-'*79)
            print(self._kernel)
            import sys
            sys.exit(1)
        # Create simulation module
        libs = ['OpenCL']
        libd = list(myokit.OPENCL_LIB)
        incd = list(myokit.OPENCL_INC)
        incd.append(myokit.DIR_CFUNC)
        self._sim = self._compile(mname, fname, self._args, libs, libd, incd)
    def find_nan(self, log, watch_var=None, safe_range=None):
        """
        Searches for the origin of a ``NaN`` (or ``inf``) in a simulation log
        generated by this Simulation.
        
        The log must contain the state of each cell and all bound variables.
        The NaN can occur at any point in time except the first.
        
        Returns a tuple ``(time, icell, variable, value, states, bound)`` where
        ``time`` is the time the first ``NaN`` was found and ``icell`` is the
        index of the cell in which it happened. The variable's name is given as
        ``variable`` and its (illegal) value as ``value``. The current state
        and, if available, any previous states are given in the list
        ``states``. Here, ``states[0]`` points to the current state,
        ``state[1]`` is the previous state and so on. Similarly the values of
        the model's bound variables is given in ``bound``.
        
        To aid in diagnosis, a variable can be selected as ``watch_var`` and a
        ``safe_range`` can be specified. With this option, the function will
        find and report either the first ``NaN`` or the first time the watched
        variable left the safe range, whatever came first. The safe range 
        should be specified as ``(lower, upper)`` where both bounds are assumed
        to be in the safe range. The watched variable must be a state variable.
        """
        import numpy as np
        # Test if log contains all states and bound variables
        t = []
        for v in self._global:
            t.extend([v.qname() for v in self._model.bindings_for(v)])
        t = myokit.prepare_log(myokit.LOG_STATE+myokit.LOG_BOUND,
            self._model, dims=self._dims, global_vars=t)
        for key in t:
            if key not in log:
                raise myokit.FindNanError('Method requires a simulation log'
                    ' containing all states and bound variables. Missing'
                    ' variable <' + key + '>.')
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
                ifirst = None
                kfirst = None
                for key, ar in log.iteritems():
                    if ifirst is None:
                        if not np.isfinite(ar[-1]):
                            # First NaN found
                            kfirst = key
                            ifirst = bisect(ar, 0, len(ar)-1)
                            if ifirst == 0: break                            
                    elif not np.isfinite(ar[ifirst - 1]):
                            # Earlier NaN found
                            kfirst = key
                            ifirst = bisect(ar, 0, ifirst)
                            if ifirst == 0: break
                return ifirst, kfirst
        else:
            # Variable out of bounds detection
            try:
                watch_var = self._model.get(watch_var)
            except KeyError:
                raise myokit.FindNanError('Variable <' + str(watch_var)
                    + '> not found.')
            if not watch_var.is_state():
                raise myokit.FindNanError('The watched variable must be a'
                    ' state.')
            try:
                lo, hi = safe_range
            except Exception:
                raise myokit.FindNanError('A safe range must be specified for'
                    ' the watched variable as a tuple (lower, upper).')
            if lo >= hi:
                raise myokit.FindNanError('The safe range must have a lower'
                    ' bound that is lower than the upper bound.')
            def find_error_position(_log):
                # Find first occurence of out-of-bounds error
                ifirst = None
                kfirst = None
                post = '.' + watch_var.qname()
                lower, upper = safe_range
                for dims in myokit.dimco(*self._dims):
                    key = '.'.join([str(x) for x in dims]) + post
                    ar = np.array(_log[key], copy=False)
                    i = np.where((ar < lower)|(ar > upper)|np.isnan(ar)|
                        np.isinf(ar))[0]
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
        time_var = self._model.bindings_for('time')[0].qname()
        # Deep searching function
        def relog(_log, _dt):
            # Get first occurence of error
            ifirst, kfirst = find_error_position(_log)
            if kfirst is None:
                raise myokit.FindNanError('Error condition not found in log.')
            if ifirst == 0:
                raise myokit.FindNanError('Unable to work with simulation logs'
                    ' where the error condition is met in the very first data'
                    ' point.')
            # Position to start deep search at
            istart = ifirst - 1
            # Get last logged state before error
            state = []
            for dims in myokit.dimco(*self._dims):
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
            _log = self.run(duration, log=myokit.LOG_BOUND+myokit.LOG_STATE,
                log_interval=_dt, report_nan=False)
            # Reset simulation to original state
            self._state = old_state
            self._time = old_time
            # Return new log        
            return _log
        # Get time step
        dt = log[time_var][1] - log[time_var][0]
        # Search with successively fine log interval
        while dt > 0:
            dt *= 0.1
            if dt < 0.5: dt = 0
            log = relog(log, dt)
        # Search for first occurrence of error in the detailed log
        ifirst, kfirst = find_error_position(log)
        # Get indices of cell in state vector
        ndims = len(self._dims)
        icell = [int(x) for x in kfirst.split('.')[0:ndims]]
        nstate = self._model.count_states()
        istate = icell*nstate       
        # Get state & bound before, during and after error
        def state(index, icell):
            s = []
            b = {}
            for var in self._model.states():
                s.append(log.get(var.qname(), *icell)[index])
            for var in self._model.variables(bound=True):
                if var.binding() in self._global:
                    b[var.qname()] = log.get(var.qname())[index]
                else:
                    b[var.qname()] = log.get(var.qname(),*icell)[index]
            return s, b
        # Get error cell's states before, during and after
        #states = state(ifirst-1, ifirst, ifirst+1)
        states = []
        bound = []
        max_states = 3
        for k in xrange(ifirst, ifirst - max_states - 1, -1):
            if k < 0: break
            s, b = state(k, icell)
            states.append(s)
            bound.append(b)
        # Get variable causing error
        var = self._model.get('.'.join(kfirst.split('.')[ndims:]))
        # Get value causing error
        value = states[1][var.indice()]
        var = var.qname()
        # Get time error occurred
        time = log[time_var][ifirst]
        # Return time, icell, variable, value, states, bound
        return time, icell, var, value, states, bound
    def state(self, x=None, y=None):
        """
        Returns the current simulation state as a list of ``len(state) *
        ncells`` floating point values.
        
        If the optional arguments ``x`` and ``y`` specify a valid cell index a
        single cell's state is returned. For example ``state(4)`` can be
        used with a 1d simulation, while ``state(4,2)`` is a valid index in
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
            return self._state[x * self._nstate : (x + 1) * self._nstate]
    def time(self):
        """
        Returns the current simulation time.
        """
        return self._time
    def pre(self, duration, report_nan=True, progress=None,
            msg='Prepacing simulation'):
        """
        This method can be used to perform an unlogged simulation, typically to
        pre-pace a model to a (semi-)stable orbit.

        After running this method

          - The simulation time is **not** affected
          - The model state and the default state are updated to the final
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
    def reset(self):
        """
        Resets the model:

          - The time variable is set to 0
          - The model state is set to the default state (either the model's
            initial state or the last state reached using :meth:`pre`)

        """
        self._time = 0
        self._state = list(self._default_state)
    def run(self, duration, log=None, log_interval=1.0, report_nan=True,
            progress=None, msg='Running simulation'):
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
          ``myokit.LOG_ALL``.
        - A list of qnames or variable objects
        - A :class:`myokit.DataLog` object or another dictionary of
           ``qname : list`` mappings.
           
        For more details on the ``log`` argument, see the function
        :meth:`myokit.prepare_log`.

        Any variables bound to "time" or "pace" will be logged globally, all
        others will be logged per cell. These variables will be prefixed with a
        number indicating the cell index. For example, when using::
        
            s = SimulationOpenCLSpline(m, p, ncells=256)
            d = s.run(1000, log=['engine.time', 'membrane.V']
            
        where <engine.time> is bound to "time" and <membrane.V> is the membrane
        potential variable, the resulting log will contain the following
        variables::
        
            {
                'engine.time'  : [...],
                '0.membrane.V' : [...],
                '1.membrane.V' : [...],
                '2.membrane.V' : [...],
            }
            
        Alternatively, you can specify variables exactly::
        
            d = s.run(1000, log=['engine.time', '0.membrane.V']
            
        For 2d Simulations, the naming scheme ``x.y.name`` is used, for
        example ``0.0.membrane.V``.
       
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
        for v in self._global:
            g.extend([v.qname() for v in self._model.bindings_for(v)])
        # Parse log argument
        log = myokit.prepare_log(
            log,
            self._model,
            dims=self._dims,
            global_vars=g,
            if_empty=myokit.LOG_STATE+myokit.LOG_BOUND,
            allowed_classes=myokit.LOG_STATE+myokit.LOG_BOUND)
        # Logging period (0 = disabled)
        log_interval = 1e-9 if log_interval is None else float(log_interval)
        if log_interval <= 0:
            log_interval = 1e-9
        # Get progress indication function (if any)
        if progress is None:
            progress = myokit._Simulation_progress
        if progress:
            if not isinstance(progress, myokit.ProgressReporter):
                raise ValueError('The argument "progress" must be either a'
                    ' subclass of myokit.ProgressReporter or None.')
        # Run simulation
        if duration > 0:
            # Initialize
            state_in = self._state
            state_out = list(state_in)
            self._sim.sim_init(
                self._kernel,
                self._nx,
                self._ny,
                self._gx,
                self._gy,
                tmin,
                tmax,
                self._step_size,
                state_in,
                state_out,
                self._protocol,
                self._nx_paced,
                self._ny_paced,
                log,
                log_interval)
            t = tmin
            if progress:
                # Loop with feedback
                try:
                    progress.enter(msg)
                    r = 1.0 / duration if duration != 0 else 1
                    while t < tmax:
                        t = self._sim.sim_step()
                        if t < tmin:
                            # A numerical error has occurred.
                            break
                        if not progress.update((t - tmin) * r):
                            # Abort
                            self._sim.sim_clean()
                            return None
                finally:
                    progress.exit()
            else:
                # Loop without feedback
                while t < tmax:
                    t = self._sim.sim_step()
                    if t < tmin:
                        # A numerical error has occurred.
                        break
            # Update state
            self._state = state_out
        # Check for NaN
        if report_nan and log.has_nan():
            msg = 'Numerical error found in simulation logs. Use this'\
                  'Exception\'s message() method to see details.'
            txt = []
            try:
                # NaN encountered, show how it happened
                time, icell, var, value, states, bound = self.find_nan(log)
                txt.append('Encountered numerical error at t=' + str(time)
                    + ' in cell (' + ','.join([str(x) for x in icell])
                    + ') when ' + var + '=' + str(value) + '.')
                n_states = len(states)
                txt.append('Obtained ' + str(n_states) + ' previous state(s).')
                if n_states > 1:
                    txt.append('State before:')
                    txt.append(self._model.format_state(states[1]))
                txt.append('State during:')
                txt.append(self._model.format_state(states[0]))
                if n_states > 1:
                    txt.append('Evaluating derivatives at state before...')
                    try:
                        derivs = self._model.eval_state_derivatives(states[1],
                            precision=self._precision)
                        txt.append(self._model.format_state_derivs(states[1],
                            derivs))
                    except myokit.NumericalError as ee:
                        txt.append(ee.message)
            except myokit.FindNanError as e:
                txt.append('Unable to pinpoint source of NaN, an error'
                    ' occurred:')
                txt.append(e.msg)
            txt = '\n'.join(txt)
            raise myokit.SimulationError(msg, txt)
        # Return log
        return log
    def _set_state(self, state, x, y, update):
        """
        Handles set_state and set_default_state.
        """
        n = len(state)
        if n == self._nstate * self._ntotal:
            return list(state)
        elif n != self._nstate:
            raise ValueError('Given state must have the same size as a'
                ' single cell state or a full simulation state')
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
        update[offset : offset + self._nstate] = state
        return update
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
        Sets the solver step size.
        """
        step_size = float(step_size)
        if step_size <= 0:
            raise ValueError('Step size must be greater than zero.')
        self._step_size = step_size
    def set_protocol(self, protocol=None):
        """
        Changes the pacing protocol used by this simulation.
        """
        if protocol is None:
            self._protocol = None
        else:
            protocol.validate()
            self._protocol = protocol
    def set_time(self, time=0):
        """
        Sets the current simulation time.
        """
        self._time = float(time)
