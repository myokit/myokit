<?
#
# opencl_fs.cl
#
# A pype template for an OpenCL kernel
#
# Required variables
# ----------------------------------------------------------------------------
# model           A model (cloned) with independent components
# vmvar           The model variable bound to membrane potential (must be part
#                 of the state)
# precision       A myokit precision constant
# native_math     True or False
# bound_variables A dict of bound variables
# equations       The result of solvable_order()
# components      The components in solvable order
# comp_in         A dict mapping components to lists of their required inputs
# comp_out        A dict mapping components to lists of their required outputs
# fast_components The fast components in solvable order
# fast_cache      The variables that need to be cached as input to the fast
#                 components.
# ----------------------------------------------------------------------------
#
# This file is part of Myokit
#  Copyright 2011-2014 Michael Clerx, Maastricht University
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import myokit
from myokit.formats import opencl

# Get list of components that need to be evaluated
required_components = set()
for c, clist in comp_out.iteritems():
    if c.has_variables(state=True):
        required_components.add(c)
        continue
    for lhs in clist:
        if not lhs.var().is_bound():
            required_components.add(c)
            break

# Remove global variables from component input and output lists
global_vars = set(bound_variables) | set(fast_cache)
def clear_io_list(comp_list):
    for comp, clist in comp_list.iteritems():
        for var in global_vars:
            lhs = var.lhs()
            while lhs in clist:
                clist.remove(lhs)
clear_io_list(comp_in)
clear_io_list(comp_out)
del(global_vars)

# Components that use one of the bound variables should get it as an input
# variable.
for comp, clist in comp_in.iteritems():
    for bound in bound_variables:
        lhs = bound.lhs()
        if lhs in clist:
            continue        
        for var in comp.variables(deep=True):
            if var.rhs().depends_on(lhs):
                clist.append(lhs)
                break

# Get expression writer
w = opencl.OpenCLExpressionWriter(precision=precision, native_math=native_math)

# Define var/lhs function
ptrs = []
def set_pointers(names=None):
    """
    Tells the expression writer to write the given variable names (given as
    LhsExpression objects) as pointers.
    
    Calling set_pointers a second time clears the first list. Calling with
    ``names=None`` unsets all pointers.
    """
    global ptrs
    ptrs = []
    if names != None:
        ptrs = list(names)
def v(var):
    """
    Accepts a variable or a left-hand-side expression and returns its C
    representation.
    """
    if isinstance(var, myokit.Derivative):
        # Explicitly asked for derivative
        pre = '*' if var in ptrs else ''        
        return pre + '_d' + var.var().uname()
    if isinstance(var, myokit.Name):
        var = var.var()
    if var in bound_variables:
        return bound_variables[var]
    pre = '*' if myokit.Name(var) in ptrs else ''        
    return pre + var.uname()
w.set_lhs_function(v)

# Tab
tab = '    '

?>
#define n_state <?=str(model.count_states())?>
#define i_vm <?= vmvar.indice() ?>

<?
if precision == myokit.SINGLE_PRECISION:
    print('/* Using single precision floats */')
    print('typedef float Real;')
else:
    print('/* Using double precision floats */')
    print('typedef double Real;')

print('')
print('/* Constants */')
for group in equations.itervalues():
    for eq in group.equations(const=True):
        if isinstance(eq.rhs, myokit.Number):
            print('#define ' + v(eq.lhs) + ' ' + w.ex(eq.rhs))

print('')
print('/* Calculated constants */')
for group in equations.itervalues():
    for eq in group.equations(const=True):
        if not isinstance(eq.rhs, myokit.Number):
            print('#define ' + v(eq.lhs) + ' (' + w.ex(myokit.Number(eq.rhs.eval())) + ')')

print('')
print('/* Aliases of state variables. */')
for var in model.states():
    print('#define ' + var.uname() + ' state[off + ' + str(var.indice()) + ']')

print('')
print('/* Aliases of state variable derivatives. */')
for var in model.states():
    print('#define _d' + var.uname() + ' dstate[off + ' + str(var.indice()) + ']')

print('')
print('/* Aliases of cached variables to fast derivative calculation. */')
for k, var in enumerate(fast_cache):
    print('#define ' + var.uname() + ' cache[ofc + ' + str(k) + ']')

print('')
for comp, ilist in comp_in.iteritems():
    if comp not in required_components:
        continue

    # Comment
    print('/*')
    print('Component: ' + comp.name())
    if 'desc' in comp.meta:
        print(comp.meta['desc'])
    print('*/')

    # Function header
    olist = comp_out[comp]
    args = [
        'const int off',
        'const int ofc',
        '__global const Real *state',
        '__global Real *dstate',
        '__global Real *cache',
        ]
    args.extend(['Real '  + v(lhs) for lhs in ilist])
    args.extend(['__private Real *' + v(lhs) for lhs in olist])
    set_pointers(olist)
    name = 'calc_' + comp.name()
    print('void ' + name + '(' + ', '.join(args) + ')')
    print('{')

    # Equations
    for eq in equations[comp.name()].equations(const=False):
        var = eq.lhs.var()
        pre = tab
        if not (eq.lhs.is_derivative() or eq.lhs.var() in fast_cache
                or eq.lhs in ilist or eq.lhs in olist):
            pre += 'Real '
        if var not in bound_variables:
            print(pre + w.eq(eq) + ';')

    print('}')
    print('')
    set_pointers(None)
?>

/*
 * Calculates all derivatives for a single cell
 *
 * Arguments
 *  nx        : The number of cells in the x-direction
 *  ny        : The number of cells in the y-direction
 *  time      : The current simulation time
 *  time_step : The next time step
 *  nx_paced  : The number of cells being paced in the x-direction
 *  ny_paced  : The number of cells being paced in the y-direction
 *  pace_in   : The current pacing value
 *  state     : The state vector
 *  idiff_in  : The diffusion current vector
 *  dstate    : The derivatives for this state
 *  cache     : A cache of inputs to calc_fast_derivs
 */
__kernel void calc_slow_derivs(
    const int nx,
    const int ny,
    const Real time,
    const Real time_step,
    const int nx_paced,
    const int ny_paced,
    const Real pace_in,
    __global const Real *state,
    __global const Real* idiff_in,
    __global Real *dstate,
    __global Real *cache)
{
    const int ix = get_global_id(0);
    const int iy = get_global_id(1);
    if(ix >= nx) return;
    if(iy >= ny) return;
    
    // Offset of this cell's state in the state vector & cache vector
    const int cid = ix + iy * nx;
    const int off = cid * n_state;
    const int ofc = cid * <?= len(fast_cache) ?>;
    
    // Diffusion
    Real idiff = idiff_in[cid];
    
    // Pacing
    Real pace = (ix < nx_paced && iy < ny_paced) ? pace_in : 0;    
    
<?
print(tab + '// Evaluate derivatives')
for comp in components:
    ilist = comp_in[comp]
    olist = comp_out[comp]

    # Skip components without output or derivatives
    if comp not in required_components:
        continue

    # Declare any output variables
    for var in comp_out[comp]:
        print(tab + 'Real ' + v(var) + ' = 0;')

    # Function header
    args = ['off', 'ofc', 'state', 'dstate', 'cache']
    args.extend([v(lhs) for lhs in ilist])
    args.extend(['&' + v(lhs) for lhs in olist])
    print(tab + 'calc_' + comp.name() + '(' + ', '.join(args) + ');')
    
?>
}

/*
 * Calculates fast components.
 *
 * Arguments
 *  nx        : The number of cells in the x-direction
 *  ny        : The number of cells in the y-direction
 *  time      : The current simulation time
 *  time_step : The next time step
 *  nx_paced  : The number of cells being paced in the x-direction
 *  ny_paced  : The number of cells being paced in the y-direction
 *  pace_in   : The current pacing value
 *  state     : The state vector
 *  idiff_in  : The diffusion current vector
 *  dstate    : The derivatives for this state
 *  cache     : A cache of inputs created by calc_slow_derivs
 */
__kernel void calc_fast_derivs(
    const int nx,
    const int ny,
    const Real time,
    const Real time_step,
    const int nx_paced,
    const int ny_paced,
    const Real pace_in,
    __global const Real *state,
    __global const Real* idiff_in,
    __global Real *dstate,
    __global Real *cache)
{
    const int ix = get_global_id(0);
    const int iy = get_global_id(1);
    if(ix >= nx) return;
    if(iy >= ny) return;
    
    // Offset of this cell's state in the state vector & cache vector
    const int cid = ix + iy * nx;
    const int off = cid * n_state;
    const int ofc = (ix + iy * nx) * <?= len(fast_cache) ?>;
    
    // Diffusion
    Real idiff = idiff_in[cid];
    
    // Pacing
    Real pace = (ix < nx_paced && iy < ny_paced) ? pace_in : 0;    
    
<?
print(tab + '// Evaluate fast components')
for comp in fast_components:
    ilist = comp_in[comp]
    olist = comp_out[comp]

    # Skip components without output or derivatives
    if len(olist) == 0 and not comp.has_variables(state=True):
        continue

    # Declare any output variables
    for var in comp_out[comp]:
        print(tab + 'Real ' + v(var) + ' = 0;')

    # Function header
    args = ['off', 'ofc', 'state', 'dstate', 'cache']
    args.extend([v(lhs) for lhs in ilist])
    args.extend(['&' + v(lhs) for lhs in olist])
    print(tab + 'calc_' + comp.name() + '(' + ', '.join(args) + ');')
?>
}

/*
 * Performs a forward Euler update step for a single cell.
 *
 * Arguments
 *  nx        : The number of cells in the x-direction
 *  ny        : The number of cells in the y-direction
 *  time_step : The time step to take
 *  state     : The state vector
 *  dstate    : The derivatives for this state
 */
__kernel void perform_step(
    const int nx,
    const int ny,
    const Real time_step,
    __global Real *state,
    __global Real *dstate)
{
    const int ix = get_global_id(0);
    const int iy = get_global_id(1);
    if(ix >= nx) return;
    if(iy >= ny) return;
    
    // Offset of this cell's state in the state vector
    const int off = (ix + iy * nx) * n_state;
    
    // Perform update
<?
for var in model.states():
    print(tab + v(var) + ' += ' + v(var.lhs()) + ' * time_step;')
?>  
}

/*
 * Diffusion kernel program
 * Performs a single diffusion step
 *
 * Arguments
 *  nx    : The number of cells in the x direction
 *  ny    : The number of cells in the y direction
 *  gx    : The cell-to-cell conductance in the x direction
 *  gy    : The cell-to-cell conductance in the y direction
 *  state : The state vector
 *  idiff : The diffusion current vector
 */
__kernel void calc_diff_current(
    const int nx,
    const int ny,
    const Real gx,
    const Real gy,
    __global Real *state,
    __global Real *idiff)
{
    const int ix = get_global_id(0);
    const int iy = get_global_id(1);
    if(ix >= nx) return;
    if (iy >= ny) return;
    
    // Offset of this cell's Vm in the state vector
    const int cid = ix + iy * nx;
    const int off = cid * n_state + i_vm;

    // Diffusion, x-direction
    int ofp, ofm;
    if(nx > 1) {
        ofp = off + n_state;
        ofm = off - n_state;
        if(ix == 0) {
            // First position
            idiff[cid] = gx * (state[off] - state[ofp]);
        } else if (ix == nx - 1) {
            // Last position
            idiff[cid] = gx * (state[off] - state[ofm]);
        } else {
            // Middle positions
            idiff[cid] = gx * (2*state[off] - state[ofm] - state[ofp]);
        }
    } else {
        idiff[cid] = 0;
    }
    
    // Diffusion, y-direction
    if(ny > 1) {
        ofp = off + n_state * nx;
        ofm = off - n_state * nx;
        if(iy == 0) {
            // First position
            idiff[cid] += gy * (state[off] - state[ofp]);
        } else if (iy == ny - 1) {
            // Last position
            idiff[cid] += gy * (state[off] - state[ofm]);
        } else {
            // Middle positions
            idiff[cid] += gy * (2*state[off] - state[ofm] - state[ofp]);
        }
    }
}

<?
print('/* Aliases of cached inputs to fast derivative calculation. */')
for var in fast_cache:
    print('#undef ' + var.uname())
print('')
print('/* Aliases of state variable derivatives. */')
for var in model.states():
    print('#undef _d' + var.uname())
print('')
print('/* Remove aliases of state variables. */')
for var in model.states():
    print('#undef ' + var.uname())
print('')
print('/* Remove constant definitions */')
for group in equations.itervalues():
    for eq in group.equations(const=True):
        print('#undef ' + v(eq.lhs))
?>
#undef n_state
