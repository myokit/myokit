#
# OpenCL driven simulation, 1d or 2d, using Heun's explicit integration method.
#
# This file is part of Myokit
#  Copyright 2011-2014 Michael Clerx, Maastricht University
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import myokit
# Location of C and OpenCL sources
SOURCE_FILE = 'opencl_heun.c'
KERNEL_FILE = 'opencl_heun.cl'
class SimulationOpenCLHeun(myokit.CModule):
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
    ``precision``
        Can be set to ``myokit.SINGLE_PRECISION`` (default) or
        ``myokit.DOUBLE_PRECISION`` if the used device supports it.
    
    The simulation provides the following inputs variables can bind to:
    
    ``time`` (global)
        The simulation time
    ``pace`` (per-cell)
        The pacing level, this is set if a protocol was passed in.
    ``diffusion_current`` (per-cell)
        The current flowing from the cell to its neighbours. This will be
        positive when the cell is acting as a source, negative when it is
        acting as a sink.
        
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
    
      - Models used in a SimulationOpenCL need to have independent
        components. That is, it should be possible to evaluate the model's
        variables component by component.
      - Intermediary variables (for example currents) are calculated on the
        GPU, used, and then discarded. As a result they are not available for
        logging.
        
    """
    _index = 0 # Unique id for this object
    def __init__(self, model, protocol=None, ncells=256, npaced=5, g=9.5,
            dt=0.005, precision=myokit.SINGLE_PRECISION):
        super(SimulationOpenCLHeun, self).__init__()
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
        #for idiff in idiffs:
        #    x = model.expressions_between(idiff, self._vm)
        #    print('-'*70)
        #    print '\n'.join(str(y) for y in x)
        #    print('-'*70)
        #raise Exception
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
            'cell_step',
            'diff_step',
            'nx',
            'ny',
            'time',
            'dt',
            'nx_paced',
            'ny_paced',
            'pace_in',
            'y',
            'y2',
            'dy',
            'dy2',
            'idiff_in',
            'cid',
            'ix',
            'iy',
            'off',
            'ofp',
            'ofm',            
            'idiff',
            'pace',
            'i_vm',
            'gx',
            'gy',
            'n_state',
            )
        model.create_unique_names()
        # Create back-end
        self._create_backend()
    def _create_backend(self):
        """
        Creates this simulation's backend.
        """
        # Unique simulation id
        SimulationOpenCLHeun._index += 1
        mname = 'myokit_sim_opencl_heun_' + str(SimulationOpenCLHeun._index)
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
    def pre(self, duration, progress=None, msg='Prepacing simulation'):
        """
        This method can be used to perform an unlogged simulation, typically to
        pre-pace a model to a (semi-)stable orbit.

        After running this method

          - The simulation time is **not** affected
          - The model state and the default state are updated to the final
            state reached in the simulation.

        Calls to :meth:`reset` after using :meth:`pre` will revert the
        simulation to this new default state.

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as `msg`.
        """
        self._run(duration, myokit.LOG_NONE, 1, progress, msg)
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
    def run(self, duration, log=None, log_interval=1.0, progress=None,
            msg='Running simulation'):
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
        
            s = SimulationOpenCL(m, p, ncells=256)
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
        
        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as `msg`.
        """
        r = self._run(duration, log, log_interval, progress, msg)
        self._time += duration
        return r
    def _run(self, duration, log, log_interval, progress, msg):
        # Simulation times
        if duration < 0:
            raise Exception('Simulation time can\'t be negative.')
        tmin = self._time
        tmax = tmin + duration
        # Gather global variables in model
        g = []
        for v in ['time', 'pace']:
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
                try:
                    # Loop with feedback
                    progress.enter(msg)
                    r = 1.0 / duration if duration != 0 else 1
                    while t < tmax:
                        t = self._sim.sim_step()
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
            # Update state
            self._state = state_out
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
