<?
#
# kernel.cu
#
# A pype template for a CUDA kernel
#
# Required variables
#-------------------
# model    A model
# use_rl   A boolean (use Rush-Larsen yes/no)
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
# Authors:
#  Michael Clerx
#  Enno de Lange
#
import myokit
import myokit.formats.cuda as cuda

# Double or single precision?
precision = myokit.SINGLE_PRECISION

# Check if model has diffusion_current binding
if model.binding('diffusion_current') is None:
    raise ValueError('Model should have a variable with binding `diffusion_current`.')

# Clone model, and adapt to inf-tau form if in RL mode
rl_states = {}
if use_rl:
    # Check vm is known
    if model.label('membrane_potential') is None:
        raise ValueError('Model should have a variable with label `membrane_potential`.')

    # Convert model to inf-tau form (returns clone) and get vm
    import myokit.lib.hh as hh
    model = hh.convert_hh_states_to_inf_tau_form(model)
    vm = model.label('membrane_potential')

    # Get (inf, tau) tuple for every Rush-Larsen state
    for state in model.states():
        res = hh.get_inf_and_tau(state, vm)
        if res is not None:
            rl_states[state] = res

else:
    # Clone model
    model = model.clone()

# Merge interdepdent components
model.resolve_interdependent_components()

# Reserve keywords
model.reserve_unique_names(*cuda.keywords)
model.reserve_unique_names(
    *['calc_' + c.name() for c in model.components()]
    )
model.reserve_unique_names(
    #'time',
    #'pace',
    'I_diff',
    'dt',
    'parameters',
    'state',
    )
model.create_unique_names()

# Get initial values (before time binding is removed and model becomes invalid)
initial_values = model.initial_values(True)

# Process bindings, remove unsupported bindings, get map of bound variables to
# internal names
bound_variables = myokit._prepare_bindings(model, {
    #'time' : 'time',
    #'pace' : 'pace',
    'diffusion_current' : 'I_diff',
})

# Get equations
equations = model.solvable_order()

# Delete "*remaning*" group, guaranteed to be empty with independent components
del(equations['*remaining*'])

# Get component order
comp_order = equations.keys()
comp_order = [model.get(c) for c in comp_order]

# Get component inputs/output arguments
comp_in, comp_out = model.map_component_io(
    omit_states=True,
    omit_derivatives=False,
    omit_constants=True,
    rl_states=rl_states,
)

# Bound variables will be passed in to every function as needed, so they can be
# removed from the input/output lists
def clear_io_list(comp_list):
    for comp, clist in comp_list.items():
        for var in bound_variables:
            lhs = var.lhs()
            while lhs in clist:
                clist.remove(lhs)
clear_io_list(comp_in)
clear_io_list(comp_out)

# Components that use one of the bound variables should get it as an input
# variable.
for comp, clist in comp_in.items():
    for bound in bound_variables:
        lhs = bound.lhs()
        if lhs in clist:
            continue
        for var in comp.variables(deep=True):
            if var.rhs().depends_on(lhs):
                clist.append(lhs)
                break

# Get expression writer
w = cuda.CudaExpressionWriter(precision=precision)

# Define var/lhs function
def v(var):
    """
    Accepts a variable or a left-hand-side expression and returns its C
    representation.
    """
    if isinstance(var, myokit.Derivative):
        # Explicitly asked for derivative
        return 'D_' + var.var().uname()
    if isinstance(var, myokit.Name):
        var = var.var()
    if var in bound_variables:
        return bound_variables[var]
    return var.uname()
w.set_lhs_function(v)

# Tab
tab = '    '

# To render last function inline, set "last_component" to the last component
#last_component = None
last_component = comp_order[-1]


export = 'CUDA export' + (' with RL updates' if use_rl else '')
print('/*')
print(' * CUDA kernel for ' + model.name())
print(' *')
print(' * Generated on ' + myokit.date() + ' by Myokit ' + export)
print(' */')


if precision == myokit.SINGLE_PRECISION:
    print('#include <float.h>')

?>

////////////////////////////////////////////////////////////////////////////////
// Macros and definitions
////////////////////////////////////////////////////////////////////////////////

<?
if precision == myokit.SINGLE_PRECISION:
    print('/* Using single precision floats */')
    print('typedef float Real;')
else:
    print('/* Using double precision floats */')
    print('typedef double Real;')
?>

#define NDIM <?=str(model.count_states())?>

/* Accessor macros */
#define N_FREE_PARAMETERS 0

<?
print('/* Constants */')
for group in equations.values():
    for eq in group.equations(const=True):
        if isinstance(eq.rhs, myokit.Number):
            print('#define ' + v(eq.lhs) + ' ' + w.ex(eq.rhs))

print('')
print('/* Calculated constants */')
for group in equations.values():
    for eq in group.equations(const=True):
        if not isinstance(eq.rhs, myokit.Number):
            print('#define ' + v(eq.lhs) + ' (' + w.ex(eq.rhs) + ')')

print('')
print('/* Aliases of state variables. */')
for var in model.states():
    print('#define ' + var.uname() + ' state[' + str(var.index()) + ']')

?>

////////////////////////////////////////////////////////////////////////////////
// Local function declarations
////////////////////////////////////////////////////////////////////////////////

<?
print('')
print('/* Components */')
for comp, ilist in comp_in.items():
    if comp == last_component:
        continue
    olist = comp_out[comp]
    if len(olist) == 0:
        continue

    # Function header
    args = ['Real *state']
    args.extend(['Real '  + v(lhs) for lhs in ilist])
    args.extend(['Real& ' + v(lhs) for lhs in olist])
    name = 'calc_' + comp.name()
    print('__device__ void ' + name + '(' + ', '.join(args) + ')')
    print('{')

    # Equations
    for eq in equations[comp.name()].equations(const=False):
        var = eq.lhs.var()
        pre = tab
        if not (eq.lhs in ilist or eq.lhs in olist):
            if var in rl_states:
                continue
            pre += 'Real '
        if var not in bound_variables:
            print(pre + w.eq(eq) + ';')

    print('}')
    print('')
?>

////////////////////////////////////////////////////////////////////////////////
//! Compute an Euler step of the model.
////////////////////////////////////////////////////////////////////////////////
__device__ int iterate_euler_cu(const Real dt, Real *state, Real I_diff,
                                    Real *parameters)
{
<?
print(tab + '/* Evaluate derivatives */')
for comp in comp_order:
    ilist = comp_in[comp]
    olist = comp_out[comp]

    # Skip components without output
    if len(olist) == 0:
        continue

    # Skip last component (if in inline mode)
    if comp == last_component:
        continue

    # Declare any output variables
    for var in comp_out[comp]:
        print(tab + 'Real ' + v(var) + ' = 0;')

    # Function header
    args = ['state']
    args.extend([v(lhs) for lhs in ilist])
    args.extend([v(lhs) for lhs in olist])
    print(tab + 'calc_' + comp.name() + '(' + ', '.join(args) + ');')

if last_component:
    print(tab)
    print(tab + '/* Evaluate ' + last_component.name() + ' */')
    olist = comp_out[last_component]
    ilist = comp_in[last_component]
    for eq in equations[last_component.name()].equations(const=False):
        var = eq.lhs.var()
        pre = tab
        if not eq.lhs in ilist:
            pre += 'Real '
        if var not in bound_variables:
            print(pre + w.eq(eq) + ';')

?>
    /* Perform update */
<?
for var in model.states():
    if var in rl_states:
        inf, tau = rl_states[var]
        inf, tau, var = v(inf), v(tau), v(var)
        print(tab + var + ' = ' + inf + ' - (' + inf + ' - ' + var + ') * exp(-dt / ' + tau + ');')
    else:
        print(tab + v(var) + ' += dt * ' + v(var.lhs()) + ';')
?>

    return 0;
}

/* Set the standard initial conditions */
int get_default_initial_state(Real *state)
{
    if (state == 0) return(-1);

<?
for var, val in zip(model.states(), initial_values):
    if 'desc' in var.meta:
        print(tab + '// ' + var.meta['desc'])
    print(tab + v(var) + ' = ' + myokit.float.str(val) + ';')
?>

    return(0);
}

/* Function to initialize the parameter array in the model structure. */
int get_default_parameters(Real *parameters)
{
    if (parameters == NULL) return(1);
    return(0);
}

<?
print('/* Remove constant definitions */')
for group in equations.values():
    for eq in group.equations(const=True):
        print('#undef ' + v(eq.lhs))

print('')
print('/* Remove aliases of state variables. */')
for var in model.states():
    print('#undef ' + var.uname())

?>
