- `Model.expressions_for` treats bound variables as inputs. We could treat bounds as constants here?
- Sensitivities `dy/dx` cannot have a bound variable as `y`. These variables are set at compile time, so would perhaps be possible to complain when setting paced variables later?
- Allowing bound variables to be logged will be trickier

- [x] OK `./myokit/gui/ide.py:            elif var.is_bound():
- [x] OK `./myokit/gui/ide.py:                    + str(model.count_variables(bound=True, deep=True)))
- [x] Can go `./myokit/_model_api.py:                    if bound != var._is_bound:`
- [x] **Minor issue**: `./myokit/_model_api.py:            if var.is_bound() or (var.is_state() and not lhs.is_derivative()):`
- [x] Can go `./myokit/_model_api.py:            if eq.lhs.var().is_bound():`
- [x] `./myokit/_model_api.py:        self._is_bound = False`
- [x] `./myokit/_model_api.py:    def is_bound(self):`
- [x] `./myokit/_model_api.py:        return self._is_bound`
- [x] `./myokit/_model_api.py:            s_old = (self._is_bound, self._is_state, self._is_intermediary,`
- [x] `./myokit/_model_api.py:        self._is_bound = self._binding is not None`
- [x] `./myokit/_model_api.py:        if self._is_state or self._is_bound or self._rhs is None:`
- [x] `./myokit/_model_api.py:            if s_old != (self._is_bound, self._is_state, self._is_intermediary,`
- [x] Can go `./myokit/_expressions.py:            if ref.is_state_value() or var.is_bound():`
- [x] Can go `./myokit/_expressions.py:            if not var.is_bound():`
- [x] Can go ("log does not support bound variables") `./myokit/_datalog.py:        elif var.is_bound():`
- [ ] **Issue**: `./myokit/_sim/cmodel.py:            elif var.is_bound():`
- [x] Naming of variables: `./myokit/_sim/cmodel.py:            if var.is_bound():`
- [x] OK: `./myokit/_sim/cmodel.h:    for eq in eqs.equations(const=False, bound=False):`
- [x] **Issue** Allowing bound variables to be logged. Would have to become "allowing time and paced variables to be logged"? `for var in bound_variables:`
- [x] `./myokit/_sim/cmodel.h:for var in model.variables(deep=True, state=False, bound=False, const=False):`

- [ ] `./myokit/_sim/openclsim.py:            if var.is_intermediary() and not var.is_bound():
- [ ] `./myokit/_sim/openclsim.py:        if var.is_bound():
- [ ] `./myokit/_sim/openclsim.py:            for var in self._model.variables(bound=True):

- [ ] `./myokit/_sim/fiber_tissue.py:            if var.is_intermediary() and not var.is_bound():
- [ ] `./myokit/_sim/fiber_tissue.py:            if var.is_intermediary() and not var.is_bound():
- [ ] `./myokit/_sim/fiber_tissue.py:            for var in model.variables(bound=True):

- [ ] `./myokit/_sim/cable.c:for var in model.variables(bound=True, deep=True):
- [ ] `./myokit/_sim/cable.c:for var in model.variables(inter=True, bound=False, deep=True):
- [ ] `./myokit/_sim/cable.c:for var in model.variables(const=True, bound=False, deep=True):
- [ ] `./myokit/_sim/cable.c:    for eq in eqs.equations(const=False, bound=False):

- [ ] `./myokit/_sim/rhs.py:                if var.is_bound():

- [ ] `./myokit/_sim/jacobian.cpp:for var in model.variables(state=False, const=False, bound=False, deep=True):
- [ ] `./myokit/_sim/jacobian.cpp:    if eqs.has_equations(const=False, bound=False):
- [ ] `./myokit/_sim/jacobian.cpp:        for eq in eqs.equations(const=False, bound=False):

- [ ] `./myokit/formats/matlab/template/model.m:        if var.is_bound():

- [ ] `./myokit/formats/python/template/sim.py:        if var.is_bound():

- [ ] `./myokit/formats/ansic/template/cable.c:for var in model.variables(bound=True, deep=True):
- [ ] `./myokit/formats/ansic/template/cable.c:for var in model.variables(inter=True, bound=False, deep=True):
- [ ] `./myokit/formats/ansic/template/cable.c:for var in model.variables(const=True, bound=False, deep=True):
- [ ] `./myokit/formats/ansic/template/cable.c:    for eq in eqs.equations(const=False, bound=False):

- [ ] `./myokit/formats/stan/_exporter.py:            if var.is_bound():
- [ ] `./myokit/formats/stan/template/cell.stan:    for eq in eq_list.equations(const=True, bound=False):
- [ ] `./myokit/formats/stan/template/cell.stan:    for eq in eq_list.equations(const=False, bound=False):


