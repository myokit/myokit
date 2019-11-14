#
# Methods for guessing the meaning of model variables
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


def _distance_to_bound(variable):
    """
    Finds all variables that depend on ``v``, but are otherwise constant, and
    returns a map ``{variable: distance to v}``.
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
        del(distances[variable])
    finally:
        # Reinstate binding
        variable.set_binding(binding)

    return distances


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
    6. Candidates with a score < 1 are discarded.
    7. The highest scoring candidate is returned (with no particular
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
        del(candidates[v])

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

