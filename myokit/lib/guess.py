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


# Units that current is often expressed in (give or take a multiplier)
_A = myokit.units.A
_AF = myokit.units.A / myokit.units.F
_Am2 = myokit.units.A / myokit.units.m**2


def _is_current_unit(unit):
    if unit is None:
        return False
    if myokit.Unit.can_convert(unit, _A):
        return True
    if myokit.Unit.can_convert(unit, _AF):
        return True
    if myokit.Unit.can_convert(unit, _Am2):
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




def stimulus_current(model):
    """
    Guesses which model variable (if any) represents the stimulus current and
    returns it.

    If no suitable candidate is found, ``None`` is returned.


    """
    # If labelled, return

    # If oxmeta labelled, return

    # Candidates:
    #  Must depend (indirectly) on engine.pace xor engine.time
    # Must not be a state, or depend on a state

    # Candidate scoring:
    #  Further away from time or pace is better:
    #   score = 1 - 1 / (1 + d), where d is the distance to time or pace
    #   This grows with decreasing distance, but stays within [0.5, 1]
    #  Name is istim or i_stim --> +2 points
    #  In units compat with A, A/F or A/cm^2: +1 point

    # Return any variable labelled as `stimulus_current`
    i_stim = model.label('stimulus_current')
    if i_stim is not None:
        return i_stim

    # Return any variable annotated as `oxmeta: membrane_stimulus_current`
    for v in model.variables(deep=True):
        if v.meta.get('oxmeta', None) == 'membrane_stimulus_current':
            return v

    # Gather list of candidates and initial scores (based on distance to bound
    # variable)
    candidates = {}
    pace = model.binding('pace')
    if pace is not None:
        for var, distance in _distance_to_bound(time).items():
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
        if _is_current_unit(unit):
            candidates[v] += 1
        elif unit is not None:
            incompatible.append(v)
    for v in incompatible:
        #del(candidates[v])
        pass

    # Add points for name (2 points if lower equals istim or i_stim
    for v in candidates:
        name = v.name().lower()
        if name in ('istim', 'i_stim'):
            candidates[v] += 2

    # No options? Return None
    if not candidates:
        return None

    # Order from best to worst
    ranking = sorted(candidates.keys(), key=lambda v: -candidates[v])

    # Don't bother with tie-breaking, as long as something is returned!
    return ranking[0]

