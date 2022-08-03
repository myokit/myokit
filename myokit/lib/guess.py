#
# Methods for guessing the meaning of model variables (and manipulating models
# based on those guesses).
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
import collections
import myokit


def _compatible_units(unit, options):
    """ Checks if ``unit`` is compatible with one of the given ``options``. """
    if unit is None:
        return False
    for option in options:
        if myokit.Unit.can_convert(unit, option):
            return True
    return False


def _deep_deps(variable):
    """
    Finds all variables that ``variable`` depends on, and returns a map
    ``{var: distance to var}``.
    """
    distances = {variable: 0}
    queue = collections.deque([variable])
    while queue:
        root = queue.popleft()
        dist = distances[root] + 1
        for v in root.refs_to():
            if v not in distances:
                distances[v] = dist
                queue.append(v)
    del distances[variable]

    return distances


def _distance_to_bound(variable):
    """
    Finds all variables that depend on a bound ``variable``, but are otherwise
    constant, and returns a map ``{var: distance to var}``.
    """
    # 1. Remove binding
    # 2. Find distances, scanning only constants dependent on `variable`
    # 3. Reinstate binding

    # Remove binding
    binding = variable.binding()
    if binding is None:
        raise ValueError('Argument `variable` must be a bound variable.')
    variable.set_binding(None)

    # Find distances
    try:
        distances = {variable: 0}
        queue = collections.deque([variable])
        while queue:
            root = queue.popleft()
            dist = 1 + distances[root]
            for v in root.refs_by():
                if v.is_constant() and v not in distances:
                    distances[v] = dist
                    queue.append(v)
        del distances[variable]
    finally:
        # Reinstate binding
        variable.set_binding(binding)

    return distances


def _find_conditional(expression):
    """
    Performs a breadth-first search on the given ``expression``, returning the
    first conditional expression it finds (or ``None`` if no conditionals are
    encountered).
    """
    conds = (myokit.If, myokit.Piecewise)
    if isinstance(expression, conds):
        return expression

    queue = collections.deque([expression])
    while queue:
        root = queue.popleft()
        for e in iter(root):
            if isinstance(e, conds):
                return e
            queue.append(e)

    return None


def _remove_nested(variable):
    """
    Removes any nested variables of the given variable.
    """
    kids = [k for k in variable]
    for k in kids:
        k.set_rhs(0)
    for k in kids:
        variable.remove_variable(k, recursive=True)


def add_embedded_protocol(model, protocol, add_oxmeta_annotations=True):
    """
    Attempts to convert a :class:`myokit.Protocol` to a (discontinuous)
    expression and embed it in the given :class`myokit.Model`.

    Returns ``True`` if the model was succesfully updated.

    This method is designed for protocols that contain a single, indefinitely
    recurring event (e.g. cell pacing protocols), and doesn't handle other
    forms of protocol.

    If ``add_oxmeta_annotations`` is set to ``True``, the method will add
    the relevant ``oxmeta`` annotations to any newly created variables
    """

    # Get time variable
    time = model.time()
    if time is None:
        return False

    # Get pacing variable
    v_pace = model.binding('pace')
    if v_pace is None:
        # Nothing bound to pace: Might be able to add protocol, but there'd be
        # no point to it!
        return False

    # Check protocol has only a single event
    if len(protocol) != 1:
        return False

    # Check it's an indefinitely recurring periodic event
    event = protocol.head()
    if event.period() == 0 or event.multiplier() != 0:
        return False

    # Check for existing stimulus variables
    stim_info = stimulus_current_info(model)
    v_current = stim_info['current']
    v_amplitude = stim_info['amplitude']
    e_amplitude = stim_info['amplitude_expression']
    v_offset = stim_info['offset']
    v_period = stim_info['period']
    v_duration = stim_info['duration']

    # Don't add a stimulus if there's already periodic stimulus variables about
    if v_offset is not None or v_period is not None or v_duration is not None:
        return False
    del v_offset, v_period, v_duration

    # Determine variable to update: pace or i_stim
    if v_current is None or (v_amplitude is None and e_amplitude is None):
        # Unable to set current as (...) * amplitude? Then update v_pace
        updating_current = False

        # VarOwner to add variables to
        parent = v_pace

    else:
        # Able to set current as (...) * amplitude? Then update v_current
        updating_current = True

        # VarOwner to add variables to
        parent = v_current

    # Start modifying model

    # Add new child variables with stimulus properties
    v_offset = parent.add_variable_allow_renaming('offset')
    v_offset.set_unit(time.unit())
    v_offset.set_rhs(myokit.Number(event.start(), time.unit()))

    v_period = parent.add_variable_allow_renaming('period')
    v_period.set_unit(time.unit())
    v_period.set_rhs(myokit.Number(event.period(), time.unit()))

    v_duration = parent.add_variable_allow_renaming('duration')
    v_duration.set_unit(time.unit())
    v_duration.set_rhs(myokit.Number(event.duration(), time.unit()))

    # Add oxmeta annotations for web lab
    if updating_current and add_oxmeta_annotations:
        v_offset.meta['oxmeta'] = 'membrane_stimulus_current_offset'
        v_period.meta['oxmeta'] = 'membrane_stimulus_current_period'
        v_duration.meta['oxmeta'] = 'membrane_stimulus_current_duration'
        if v_amplitude is not None and 'oxmeta' not in v_amplitude.meta:
            v_amplitude.meta['oxmeta'] = 'membrane_stimulus_current_amplitude'

    # Create expression for pacing signal
    pace_term = myokit.If(
        myokit.Less(
            myokit.Remainder(
                myokit.Minus(myokit.Name(time), myokit.Name(v_offset)),
                myokit.Name(v_period)
            ),
            myokit.Name(v_duration)
        ),
        myokit.Number(event.level(), v_pace.unit()),
        myokit.Number(0, v_pace.unit())
    )

    if updating_current:

        # Update current variable
        if e_amplitude is None:
            e_amplitude = myokit.Name(v_amplitude)
        v_current.set_rhs(myokit.Multiply(pace_term, e_amplitude))

        # Unbind pacing variable and remove if unused
        v_pace.set_binding(None)
        v_pace.set_rhs(myokit.Number(0, v_pace.unit()))
        _remove_nested(v_pace)
        if len(list(v_pace.refs_by())) == 0:
            v_pace.parent().remove_variable(v_pace)

    else:

        # Update pacing variable
        v_pace.set_rhs(pace_term)

        # Unbind pacing variable
        v_pace.set_binding(None)

    # It worked!
    return True


def membrane_capacitance(model):
    """
    Guess which model variable (if any) represents the membrane capacitance.

    The following strategy is used:

    1. If a variable is found with the annotation
       ``oxmeta: membrane_capacitance``, this variable is returned.
    2. If not, a list of candidates is drawn up from all constants in the
       model.
    3. 1.5 points are awarded for being referenced by the membrane potential.
    4. A point is awarded for having a unit compatible with ``F``, ``F/m^2``,
       or ``m^2``. A point is subtracted for having a unit other than ``None``
       that's incompatible with any of the above.
    5. A point is awarded for having the name ``C``, ``Cm``, ``C_m``, ``Acap``
       or ``A_cap``, or  having a name including the string 'capacitance'
       (where the checks are made case-insensitively).

    If no suitable candidates are found the method returns ``None``, otherwise
    the highest ranking candidate is returned.
    """
    # Return any variable annotated as `oxmeta: membrane_capacitance`
    for v in model.variables(deep=True):
        if v.meta.get('oxmeta', None) == 'membrane_capacitance':
            return v

    # Gather candidates
    candidates = {v: 0 for v in model.variables(deep=True, const=True)}

    # Points if used by Vm
    vm = membrane_potential(model)
    if vm is not None:
        for ref in vm.refs_to():
            if ref.is_constant():
                candidates[ref] += 1.5

    # Points for units
    def is_compatible(unit1, unit2):
        try:
            myokit.Unit.conversion_factor(unit1, unit2)
            return True
        except myokit.IncompatibleUnitError:
            return False

    cap1 = myokit.units.farad
    cap2 = myokit.units.farad / myokit.units.m**2
    cap3 = myokit.units.m**2
    for v in candidates:
        unit = v.unit()
        if unit is None:
            continue
        elif is_compatible(unit, cap1) or is_compatible(unit, cap2):
            candidates[v] += 1
        elif is_compatible(unit, cap3):
            candidates[v] += 1
        else:
            candidates[v] -= 1

    # Points for names
    names = ['c', 'cm', 'c_m', 'acap', 'a_cap']
    for v in candidates:
        name = v.name().lower()
        if name in names or 'capacitance' in name:
            candidates[v] += 1

    # Find best candidate, with at least some credibility
    if candidates:
        ranking = sorted(candidates.keys(), key=lambda v: -candidates[v])
        v = ranking[0]
        if candidates[v] > 0:
            return v

    # Nothing found!
    return None


def membrane_currents(model):
    """
    Gueses which model variables represent ionic currents through the outer
    membrane and returns them.

    This method assumes that all currents follow the same sign convention.

    Currents defined as sums of currents (or multiples of fluxes) are not
    expanded.
    """
    # Get membrane potential
    vm = membrane_potential(model)

    # Get expression that refers to currents (possibly indirectly)
    i_ion = model.label('cellular_current')
    if i_ion is not None:
        e_currents = i_ion.rhs()
    else:
        e_currents = vm.rhs()
    del i_ion

    # Assume that e_currents is an expression such as:
    #  INa + ICaL + IKr + ...
    #  i_ion + i_diff + i_stim
    #  -1/C * (...)
    currents = []
    for term in e_currents.references():
        if term.is_constant():
            continue

        # Get current variable
        current = term.var()
        currents.append(current)

    # Sort and return
    currents.sort(key=lambda x: x.name())
    return currents


def membrane_potential(model):
    """
    Gueses which model variable (if any) represents the membrane potential and
    returns it.

    Three strategies can be attempted.

    First, variables annotated as membrane potential will be returned,
    regardless of name, units, etc. In order of priority this method will
    search for (1) the label ``membrane_potential``, (2) the meta data property
    ``oxmeta: membrane_voltage``.

    If no annotated variables are found, the following strategy is used:

    1. A list of candidates is compiled, consisting of all non-nested
       variables.
    2. Candidates with a unit compatible with voltage get +1 points
    3. Candidates that define a unit (not ``None``) incompatible with voltage
       are discarded
    4. Candidates in a component with a common name for membrane potential
       variables get +1 point. Similarly candidates in a common component for
       membrane potential get +1 point, with an additional +0.5 point if both
       conditions are met.
    5. State variables get +1 point.
    6. The candidate that is used in the most equations gets +0.1 point.
    7. Candidates with a score < 1 are discarded.
    8. The highest scoring candidate is returned (with no particular
       tie-breaking rules).

    If all strategies fail the method returns ``None``.
    """
    # Return any variable labelled as `membrane_potential'
    v = model.label('membrane_potential')
    if v is not None:
        return v

    # Return any variable annotated as `oxmeta: membrane_stimulus_current`
    for v in model.variables(deep=True):
        if v.meta.get('oxmeta', None) == 'membrane_voltage':
            return v

    # Common units for the membrane potential
    common_units = [myokit.units.V]

    # Non-dimensionalised (e.g. Mitchell-Schaeffer) use [1]
    # But this causes too many false positives
    # common_units.append(myokit.units.dimensionless)

    # Common names for the membrane potential
    common_component_names = [
        'membrane',
        'cell',
    ]
    common_names = [
        'v',
        'vm',
        'v_m',
    ]

    # Create a list of candidates, with initial scores based on units
    candidates = {}
    for c in model.components():
        for v in model.variables():  # No nested variables
            # Ignore time variable
            if v.binding() == 'time':
                continue
            unit = v.unit()
            if unit is None:
                candidates[v] = 0
            elif _compatible_units(unit, common_units):
                candidates[v] = 1

    # Easy case: no candidates or a single candidate
    if len(candidates) == 0:
        return None
    elif len(candidates) == 1:
        return candidates.popitem()[0]

    # Award points for names
    for v in candidates:
        cname = v.parent().name().lower() in common_component_names
        vname = v.name().lower() in common_names
        score = int(cname) + int(vname)
        if cname and vname:
            score += 0.5
        if score:
            candidates[v] += score

    # Award point for states
    for v in candidates:
        if v.is_state():
            candidates[v] += 1

    # Award tie-breaking point for most references
    ranking = list(candidates)
    ranking.sort(key=lambda v: -len(list(v.refs_by())))
    candidates[ranking[0]] += 0.1

    # Find (one of) best candidate
    ranking.sort(key=lambda v: -candidates[v])

    # Check candidate has at least 1 full point and return
    v = ranking[0]
    if candidates[v] < 1:
        return None
    return v


def remove_embedded_protocol(model):
    """
    Searches the given model for a hardcoded periodic stimulus current and, if
    one is found, removes it and returns a :class:`myokit.Protocol` instead.

    For this method to work, :meth:`stimulus_current_info` should return at
    least a current variable, a period and duration variable, and either an
    amplitude variable or an amplitude expression.

    Returns a :class:`myokit.Protocol` if succesful, or ``None`` if not.
    """

    # Get stimulus current info from model
    info = stimulus_current_info(model)

    # Must have a stimulus current
    v_current = info['current']
    if v_current is None:
        return None

    # Must have a period and duration
    v_duration = info['duration']
    v_period = info['period']
    if v_period is None or v_duration is None:
        return None
    period = v_period.eval()
    duration = v_duration.eval()

    # Check values are sensible
    if period <= 0 or duration <= 0:
        return None

    # Offset is optional
    v_offset = info['offset']
    if v_offset is None:
        offset = 0
    else:
        offset = v_offset.eval()

    # Must have an amplitude or an amplitude expression
    v_amplitude = info['amplitude']
    e_amplitude = info['amplitude_expression']
    if e_amplitude is None:
        if v_amplitude is None:
            return None
        e_amplitude = myokit.Name(v_amplitude)

    # Start modifying model

    # Get pacing variable
    v_pace = model.binding('pace')
    if v_pace is None:
        v_pace = v_current.parent(
            myokit.Component).add_variable_allow_renaming('pace')
        v_pace.set_unit(myokit.units.dimensionless)
        v_pace.set_rhs(myokit.Number(0, myokit.units.dimensionless))
        v_pace.set_binding('pace')

    # Set new RHS for stimulus variable
    v_current.set_rhs(myokit.Multiply(myokit.Name(v_pace), e_amplitude))

    # Remove stimulus variables, if unused
    for v in (v_period, v_duration, v_offset, v_amplitude):
        if v is not None and len(list(v.refs_by())) == 0:
            v.parent().remove_variable(v, recursive=True)

    # Return periodic protocol
    return myokit.pacing.blocktrain(
        period=period, duration=duration, offset=offset)


def stimulus_current(model):
    """
    Guesses which model variable (if any) represents the stimulus current and
    returns it.

    Three strategies are tried to find the stimulus current.

    Firstly, annotated variables are searched for. If found, these are returned
    without further checking of names, units etc. Supported annotations (in
    order of priority) are (1) the label ``stimulus_current``, (2) the meta
    data property ``oxmeta: membrane_stimulus_current``.

    If no annotated variables are found, the following strategy is followed:

    1. A list of candidate variables that depend (in)directly on ``time`` or
       ``pace`` is compiled. Variables that depend (in)directly on states are
       discounted.
    2. Each candidate is assign an initial score ``1 - 1 / (1 + d)``, where
       ``d`` is the distance (in the variable graph) to ``time`` or ``pace``.
       As a result, if we define ``t_beat = engine.time % 1000`` then this gets
       a lower score than ``I = if(t_beat > 100...)``.
    3. Candidates that have a unit compatible with current get +1 point.
    4. Candidates that define a unit (not ``None``) incompatible with current
       are discarded.
    5. Candidates whose name (case-insensitively) matches a known common
       stimulus current variable name get +2 points.
    6. Remaining candidates are ranked, and the highest scoring candidate is
       returned. If there is more than one highest scoring candidate an
       arbitrary one is selected.

    If no candiates are found with this approach, a third strategy is tried:

    1. All constants are scanned for variables with a known common name and a
       current unit (or None). The first such variable is returned.

    If all strategies fail, ``None`` is returned.
    """
    # Return any variable labelled as `stimulus_current`
    i_stim = model.label('stimulus_current')
    if i_stim is not None:
        return i_stim

    # Return any variable annotated as `oxmeta: membrane_stimulus_current`
    for v in model.variables(deep=True):
        if v.meta.get('oxmeta', None) == 'membrane_stimulus_current':
            return v

    # Units that current is often expressed in (give or take a multiplier)
    common_units = [
        myokit.units.A,
        myokit.units.A / myokit.units.F,
        myokit.units.A / myokit.units.m**2,
    ]

    # Non-dimensionalised (e.g. Mitchell-Schaeffer) use [mS/uF]
    # But this causes too many false positives
    # common_units.append(myokit.units.S / myokit.units.F)

    # Common names for stimulus current variables (lowercase)
    common_names = [
        'istim',
        'i_stim',
        'i_st',
        'ist',
    ]

    # Gather list of candidates and initial scores (based on distance to bound
    # variable)
    candidates = {}
    pace = model.binding('pace')
    if pace is not None:
        for var, distance in _distance_to_bound(pace).items():
            candidates[var] = 1 - 1 / (1 + distance)
        candidates.update()
    time = model.time()
    if time is not None:
        for var, distance in _distance_to_bound(time).items():
            candidates[var] = 1 - 1 / (1 + distance)

    # Add points for units (1 point if compatible with current), and filter out
    # any variables that explicitly specify a current incompatible unit
    incompatible = []
    for v in candidates:
        unit = v.unit()
        if unit is not None:
            if _compatible_units(unit, common_units):
                candidates[v] += 1
            else:
                incompatible.append(v)
    for v in incompatible:
        del candidates[v]

    # Add points for name (2 points if name matches common name)
    for v in candidates:
        name = v.name().lower()
        if name in common_names:
            candidates[v] += 2

    # Return candidates found with strategy 1
    if candidates:
        # Order from best to worst
        ranking = sorted(candidates.keys(), key=lambda v: -candidates[v])

        # Don't bother with tie-breaking, as long as something is returned!
        return ranking[0]

    # Back-up strategy: scan for constants with right name/unit
    for var in model.variables(const=True):
        name = var.name().lower()
        if name in common_names:
            unit = var.unit()
            if unit is None or _compatible_units(unit, common_units):
                return var
    return None


def stimulus_current_info(model):
    """
    Guesses the stimulus current variable and related variables representing
    the stimulus amplitude, duration, period, and offset.

    Returns a dict with entries ``current``, ``amplitude``, ``duration``,
    ``period``, ``offset``, and ``amplitude_expression``, any of which may be
    ``None``.

    The field ``amplitude_expression`` will be used if no variable representing
    the stimulus amplitude can be detected, but a literal expression for it can
    be found, e.g. from ``i_stim = -5 [pA]``.

    The method starts by guessing the stimulus current, and looking for
    annotations:

    1. The stimulus current is guessed using :meth:`stimulus_current()`. If no
       stimulus current is found the method terminates and returns a dict of
       ``None`` objects.
    2. Any variables annotated with oxmeta stimulus terms are found.

    If all fields (except ``amplitude_expression``) are filled now, the method
    returns. If not, the following strategy is used:

    1. The (direct and indirect) dependencies of the stimulus current are
       gathered in a list of candidate variables. Whenever a variable is used
       (e.g. as stimulus duration) it is removed from the list of candidates.
    2. The list is scanned for variables that don't declare a unit, or that
       declare a unit compatible with time. The first such variable containing
       the string ``duration`` (if any) is set as the duration variable, and
       the first containing either ``offset`` or ``start`` is used for the
       stimulus offset.
    3. The first candidate that has ``period`` in its name and has no units,
       time units, or is dimensionless, is used for the stimulus period.

    The stimulus amplitude is determined as follows:

    1. All remaining candidates are assigned a score ``1 / (1 + d)`` where
       ``d`` is the distance to the stimulus current variable (for a score in
       the range (0, 0.5]).
    2. Any candidates with unit other than None or the unit of the stimulus
       current are rejected.
    3. Candidates in the same unit as the stimulus current are given +1 points.
    4. Candidates with a name containing ``amplitude`` or ``current`` are given
       +1 points.
    5. If there are one or more candidates, the best is set as stimulus
       amplitude and the method returns.

    If the stimulus amplitude variable has not been determined, the following
    strategy is used to find a stimulus current _expression_:

    1. If the expression for the stimulus current is a constant, this is set as
       the amplitude expression.
    2. Otherwise, if the expression is a conditional (an if or a piecewise),
       then the first piece that isn't a literal which evaluates to zero is
       returned.

    At this point the method returns, with any undetermined fields left set to
    ``None``.
    """
    info = {
        'current': None,
        'amplitude': None,
        'duration': None,
        'period': None,
        'offset': None,
        'amplitude_expression': None,
    }

    # Guess stimulus current, return immediately if not found
    istim = stimulus_current(model)
    if istim is None:
        return info
    info['current'] = istim
    n_todo = 4

    # Check for oxmeta annotations
    used = set()
    oxmeta = [
        ('amplitude', 'membrane_stimulus_current_amplitude'),
        ('duration', 'membrane_stimulus_current_duration'),
        ('period', 'membrane_stimulus_current_period'),
        ('offset', 'membrane_stimulus_current_offset'),
    ]
    for v in model.variables(deep=True):
        ox = v.meta.get('oxmeta', None)
        if ox is not None:
            for k, annotation in oxmeta:
                if info[k] is None and ox == annotation:
                    info[k] = v
                    used.add(v)
                    n_todo -= 1

    # Stop if nothing left to do
    if n_todo == 0:
        return info

    # Time units
    time_units = [myokit.units.second]

    # Current unit: from stimulus current variable
    current_unit = istim.unit()

    # Gather dependencies of istim, and calculate distance-based score between
    # 0 and 0.5 (closer is better)
    candidates = {}
    for v, distance in _deep_deps(istim).items():
        if v not in used and v.binding() is None:
            candidates[v] = 1 / (1 + distance)

    # Guess time variables
    used = set()
    for v in candidates:

        # Find variables with potential time units
        unit = v.unit()
        good_unit = unit is None or _compatible_units(unit, time_units)

        # Duration & offset: must have time unit
        name = v.name().lower()
        if good_unit and info['duration'] is None:
            if 'duration' in name:
                info['duration'] = v
                used.add(v)
                n_todo -= 1
                continue
        if good_unit and info['offset'] is None:
            if 'offset' in name or 'start' in name:
                info['offset'] = v
                used.add(v)
                n_todo -= 1
                continue

        # Period is dimensionless is many models (not sure why)
        if good_unit or unit == myokit.units.dimensionless:
            if info['period'] is None and 'period' in name:
                info['period'] = v
                used.add(v)
                n_todo -= 1
                continue

    # Check if anything left to do
    if n_todo == 0:
        return info

    # Search remaining candidates for amplitude
    for v in used:
        del candidates[v]

    # Filter out incompatible units, award points for compatible ones
    rejected = set()
    for v in candidates:
        unit = v.unit()
        if unit is not None:
            if unit == current_unit:
                candidates[v] += 1
            else:
                rejected.add(v)
    for v in rejected:
        del candidates[v]

    # Award points for names
    for v in candidates:
        name = v.name().lower()
        if 'amplitude' in name or 'current' in name:
            candidates[v] += 1

    # Attempt to use highest ranked candidate
    if candidates:
        # Order from best to worst
        # Don't bother with tie-breaking, as long as something is returned!
        ranking = sorted(candidates.keys(), key=lambda v: -candidates[v])
        info['amplitude'] = ranking[0]
        return info

    # Back-up strategy: find an `amplitude_expression`

    # Option 1: Constant expression for i_stim
    e = istim.rhs()
    if e.is_constant():
        info['amplitude_expression'] = e

    # Option 2: Conditional expression (with condition depending on some
    # variable): find branch leading to a non-zero literal
    else:
        e = _find_conditional(e)
        if e is not None:
            if isinstance(e, myokit.If):
                e = e.piecewise()
            for piece in e.pieces():
                if not (piece.is_literal() and piece.eval() == 0):
                    info['amplitude_expression'] = piece
                    break

    return info

