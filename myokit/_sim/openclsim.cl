<?
#
# opencl.cl
#
# A pype template for an OpenCL kernel
#
# Required variables
# ----------------------------------------------------------------------------
# model             A model (cloned) with independent components
# precision         A myokit precision constant
# native_math       True if using native maths
# bound_variables   A dict of bound variables
# inter_log         A list of intermediary variable objects to log
# diffusion         True if diffusion currents are enabled
# heterogeneous     True if heterogeneous conduction is enabled
# connections       True if connections are enabled
# fields            A list of variables to use as scalar fields
# paced_cells       A list of cell id's to pace or a tuple (nx, ny, x, y)
# rl_states         A map {state: (inf, tau)} of states for which to use Rush-
#                   Larsen updates instead of forward Euler
# fiber_tissue      True if the fiber-tissue kernel should be built
# ----------------------------------------------------------------------------
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit
from myokit.formats import opencl
from collections import OrderedDict

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

# Logged intermediary variables and variables with a scalar field are accessed
# from a vector, so can be removed from both lists.
# Bound variables will be passed in to every function as needed, so they can be
# removed from the lists
def clear_io_list(comp_list):
    for comp, clist in comp_list.items():
        for var in bound_variables:
            lhs = var.lhs()
            while lhs in clist:
                clist.remove(lhs)
        for var in inter_log:
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

# Quick check if lhs is a logged intermediary variable
inter_log_lhs = set([x.lhs() for x in inter_log])

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
    if names is not None:
        ptrs = list(names)

def v(var):
    """
    Accepts a variable or a left-hand-side expression and returns its C
    representation.
    """
    if isinstance(var, myokit.Derivative):
        # Explicitly asked for derivative
        pre = '*' if var in ptrs else ''
        return pre + 'D_' + var.var().uname()
    if isinstance(var, myokit.Name):
        var = var.var()
    if var in bound_variables:
        return bound_variables[var]
    pre = '*V_' if myokit.Name(var) in ptrs else 'V_'
    return pre + var.uname()
w.set_lhs_function(v)

# Create set of components to skip
components_to_skip = set()
for c in model.components():
    if comp_out[c]:
        # Has output? Then never skip
        continue

    # Has variable used in logging? Then never skip
    # Logged states are always outputs, so only check intermediary variables
    skip = True
    for var in inter_log:
        if var.parent(myokit.Component) == c:
            skip = False
            break
    if skip:
        components_to_skip.add(c)

# Tab
tab = '    '

# Enable double precision, if required
if precision == myokit.DOUBLE_PRECISION:
    print('/* Enable double precision extensions */')
    print('#pragma OPENCL EXTENSION cl_khr_fp64 : enable')
    if connections:
        print('#pragma OPENCL EXTENSION cl_khr_int64_base_atomics : enable')

?>
/* Number of states */
#define n_state <?=str(model.count_states())?>

/* Number of logged internal variables */
#define n_inter <?=str(len(inter_log))?>

/* Number of scalar fields */
#define n_field <?=str(len(fields))?>

<?
if diffusion:
    print('/* Index of membrane potential in state vector */')
    print('#define i_vm ' + str(model.label('membrane_potential').index()))

if precision == myokit.SINGLE_PRECISION:
    print('/* Using single precision floats */')
    print('typedef float Real;')
    if connections:
        print('typedef unsigned int RealSizedUInt;')
        print('#define Myokit_cmpxchg atomic_cmpxchg')
else:
    print('/* Using double precision floats */')
    print('typedef double Real;')
    if connections:
        print('typedef unsigned long RealSizedUInt;')
        print('#define Myokit_cmpxchg atom_cmpxchg')


print('')
print('/* Constants */')
for group in equations.values():
    for eq in group.equations(const=True):
        if isinstance(eq.rhs, myokit.Number):
            if eq.lhs.var() not in fields:
                print('#define ' + v(eq.lhs) + ' ' + w.ex(eq.rhs))

print('')
print('/* Calculated constants */')
for group in equations.values():
    for eq in group.equations(const=True):
        if not isinstance(eq.rhs, myokit.Number):
            if eq.lhs.var() not in fields:
                print('#define ' + v(eq.lhs) + ' (' + w.ex(eq.rhs) + ')')

print('')
print('/* Aliases of state variables. */')
for var in model.states():
    print('#define ' + v(var) + ' state[of1 + ' + str(var.index()) + ']')

print('')
print('/* Aliases of logged intermediary variables. */')
for k, var in enumerate(inter_log):
    print('#define ' + v(var) + ' inter_log[of2 + ' + str(k) + ']')

print('')
print('/* Aliases of scalar field variables. */')
for k, var in enumerate(fields):
    print('#define ' + v(var) + ' field_data[of3 + ' + str(k) + ']')

print('')
for comp, ilist in comp_in.items():
    # Comment
    print('/*')
    print('Component: ' + comp.name())
    if 'desc' in comp.meta:
        print(comp.meta['desc'])
    print('*/')

    # Skip useless components
    if comp in components_to_skip:
        print('')
        continue

    # Function header
    olist = comp_out[comp]
    args = [
        'const unsigned long of1',
        'const unsigned long of2',
        'const unsigned long of3',
        '__global Real *state',
        '__global Real *inter_log',
        'const __global Real *field_data',
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
        if var in rl_states:
            continue
        pre = tab
        if not (eq.lhs in ilist or eq.lhs in olist or eq.lhs in inter_log_lhs):
            pre += 'Real '
        if var not in bound_variables:
            print(pre + w.eq(eq) + ';')

    print('}')
    print('')
    set_pointers(None)

if diffusion and paced_cells:
    print('/*')
    print(' * Calculate pacing current per cell')
    print(' */')
    print('inline Real calculate_pacing(')
    print(tab + 'const unsigned long cid,')
    print(tab + 'const unsigned long ix,')
    print(tab + 'const unsigned long iy,')
    print(tab + 'const Real pace)')
    print('{')

    if type(paced_cells) == tuple:
        # Pacing rectangle
        nx, ny, x, y = paced_cells
        xlo, ylo = str(x), str(y)
        xhi, yhi = str(x + nx), str(y + ny)

        cond = []
        if x > 0:
           cond.append('ix >= ' + str(x))
        if y > 0:
            cond.append('iy >= ' + str(y))
        cond.append('ix < ' + str(x + nx))
        cond.append('iy < ' + str(y + ny))
        cond = ' && '.join(cond)
        print(tab + 'return (' + cond + ') ? pace : 0;')
    else:
        # Explicit cell selection
        for id in paced_cells:
            print(tab + 'if (cid == ' + str(id) + ') return pace;')
        print('    return 0;')
    print('}')
?>

/*
 * Cell kernel.
 * Computes a single Euler-step for a single cell.
 *
 * Arguments
 *  nx         : The number of cells in the x-direction
 *  ny         : The number of cells in the y-direction
 *  time       : The current simulation time
 *  dt         : The time step to take
 *  pace_in    : The current pacing value
 *  state      : The state vector
 *  idiff_in   : The diffusion vector
 *  inter_log  : A vector containing all logged intermediary variables
 *  field_data : A vector containing all field data
 */
__kernel void cell_step(
    const unsigned long nx,
    const unsigned long ny,
    const Real time,
    const Real dt,
    const Real pace_in,
    __global Real* state,
    const __global Real* idiff_in,
    __global Real* inter_log,
    const __global Real* field_data
    )
{
    const unsigned long ix = get_global_id(0);
    const unsigned long iy = get_global_id(1);
    if(ix >= nx) return;
    if(iy >= ny) return;

    // Offset of this cell's state in the state vector
    const unsigned long cid = ix + iy * nx;
    const unsigned long of1 = cid * n_state;
    const unsigned long of2 = cid * n_inter;
    const unsigned long of3 = cid * n_field;

    // Pacing
<?
if diffusion:
    if paced_cells:
        print('    Real pace = calculate_pacing(cid, ix, iy, pace_in);')
    else:
        print('    Real pace = 0;')
else:
    print('    Real pace = pace_in;')

if diffusion:
    print(tab + '// Diffusion')
    print(tab + 'Real idiff = idiff_in[cid];')
    print('')

print(tab + '// Evaluate derivatives')
for comp in comp_order:
    ilist = comp_in[comp]
    olist = comp_out[comp]

    # Skip uselesss components
    if comp in components_to_skip:
        continue

    # Declare any output variables
    for var in comp_out[comp]:
        print(tab + 'Real ' + v(var) + ' = 0;')

    # Function header
    args = ['of1', 'of2', 'of3', 'state', 'inter_log', 'field_data']
    args.extend([v(lhs) for lhs in ilist])
    args.extend(['&' + v(lhs) for lhs in olist])
    print(tab + 'calc_' + comp.name() + '(' + ', '.join(args) + ');')

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
}

<?
if diffusion and (not connections) and (not heterogeneous):
    print("""
/*
 * Performs a single diffusion step, for a rectangular grid with homogeneous
 * conduction.
 *
 * Arguments
 *  nx    : The number of cells in the x direction
 *  ny    : The number of cells in the y direction
 *  gx    : The cell-to-cell conductance in the x direction
 *  gy    : The cell-to-cell conductance in the y direction
 *  state : The state vector
 *  idiff : The diffusion current vector
 */
__kernel void diff_step(
    const unsigned long nx,
    const unsigned long ny,
    const Real gx,
    const Real gy,
    const __global Real *state,
    __global Real *idiff)
{
    const unsigned long ix = get_global_id(0);
    const unsigned long iy = get_global_id(1);
    if(ix >= nx) return;
    if(iy >= ny) return;

    // Offset of this cell's Vm in the state vector
    const unsigned long cid = ix + iy * nx;
    const unsigned long of1 = cid * n_state + i_vm;

    // Diffusion, x-direction
    unsigned long ofp, ofm;
    if(nx > 1) {
        ofp = of1 + n_state;
        ofm = of1 - n_state;
        if(ix == 0) {
            // First position
            idiff[cid] = gx * (state[of1] - state[ofp]);
        } else if (ix == nx - 1) {
            // Last position
            idiff[cid] = gx * (state[of1] - state[ofm]);
        } else {
            // Middle positions
            idiff[cid] = gx * (2*state[of1] - state[ofm] - state[ofp]);
        }
    } else {
        idiff[cid] = 0;
    }

    // Diffusion, y-direction
    if(ny > 1) {
        ofp = of1 + n_state * nx;
        ofm = of1 - n_state * nx;
        if(iy == 0) {
            // First position
            idiff[cid] += gy * (state[of1] - state[ofp]);
        } else if (iy == ny - 1) {
            // Last position
            idiff[cid] += gy * (state[of1] - state[ofm]);
        } else {
            // Middle positions
            idiff[cid] += gy * (2*state[of1] - state[ofm] - state[ofp]);
        }
    }
}
    """)

if heterogeneous:
    print("""
/*
 * Performs a single diffusion step, for a rectangular grid with heterogeneous
 * conduction.
 *
 * Arguments
 *  nx    : The number of cells in the x direction
 *  ny    : The number of cells in the y direction
 *  gx_field : The cell-to-cell conductances in the x direction
 *  gy_field : The cell-to-cell conductances in the y direction
 *  state : The state vector
 *  idiff : The diffusion current vector
 */
__kernel void diff_hetero(
    const unsigned long nx,
    const unsigned long ny,
    const __global Real* gx,
    const __global Real* gy,
    const __global Real *state,
    __global Real *idiff)
{
    const unsigned long ix = get_global_id(0);
    const unsigned long iy = get_global_id(1);
    if(ix >= nx) return;
    if(iy >= ny) return;

    // Offset of this cell's Vm in the state vector
    const unsigned long cid = ix + iy * nx;
    const unsigned long off = cid * n_state + i_vm;

    // Current & voltage
    Real i = 0.0;
    Real v = state[off];

    // Diffusion, x-direction
    if(nx > 1) {
        if(ix > 0) { i += gx[cid - iy - 1] * (v - state[off - n_state]); }
        if(ix < nx - 1) { i += gx[cid - iy] * (v - state[off + n_state]); }
    }

    // Diffusion, y-direction
    if(ny > 1) {
        if(iy > 0) i += gy[cid - nx] * (v - state[off - n_state * nx]);
        if(iy < ny - 1) i += gy[cid] * (v - state[off + n_state * nx]);
    }

    // Set
    idiff[cid] = i;
}
    """)

if connections:
    print("""
/*
 * Atomic float addition. See:
 *  https://streamhpc.com/blog/2016-02-09/atomic-operations-for-floats-in-opencl-improved/
 *
 * Note that this method relies on comparing the integer representation of the float.
 * For this purpose, a type RealSizedUInt must be defined, that has the same size (in memory) as a Real.
 */
inline void AtomicAdd(volatile __global Real *var, const Real operand)
{
    // Create objects representing the same data as a real-sized integer and as Real (a union)
    union {
        RealSizedUInt u;
        Real f;
    } current, expected, result;

    // Set current value to var
    current.f = *var;

    do {
        // Set the expected value of var
        expected.f = current.f;

        // Calculate the new value
        result.f = expected.f + operand;

        // Check if the variable has the expected value, and if so update it to the calculated sum.
        // After calling this, current will be set to whatever was in the variable.
        current.u = Myokit_cmpxchg((volatile __global RealSizedUInt*)var, expected.u, result.u);

        // If the variable had the expected value, it will now have been updated, so we can stop.
        // If someone else had already modified the variable at this point, the next check will fail and we try again.
    } while(current.u != expected.u);
}

/*
 * Performs an arbitrary-geometry diffusion step
 *
 * Arguments
 *  count : The connection vector size
 *  cell1 : The vector of cells connected to cell2
 *  cell2 : The vector of cells connected to cell1
 *  conductance : The vector of conductance values for each connection
 *  state : The state vector
 *  idiff : The diffusion current vector
 */
__kernel void diff_arb_step(
    const unsigned long count,
    const __global unsigned long *cell1,
    const __global unsigned long *cell2,
    const __global Real *conductance,
    const __global Real *state,
    __global Real *idiff)
{
    const unsigned long ix = get_global_id(0);
    if(ix >= count) return;

    // Cell indices and conductance
    unsigned long i1 = cell1[ix];
    unsigned long i2 = cell2[ix];
    Real i12 = conductance[ix] * (state[i1 * n_state + i_vm] - state[i2 * n_state + i_vm]);

    // Diffusion
    AtomicAdd(&idiff[i1], i12);
    AtomicAdd(&idiff[i2], -i12);
}

/*
 * Resets the diffusion to zero. Required before each arbitrary-geometry
 * diffusion calculation.
 *
 * Arguments
 *  count : The number of cells
 *  idiff : The diffusion current vector
 */
__kernel void diff_arb_reset(
    const unsigned long count,
    __global Real *idiff)
{
    const unsigned long ix = get_global_id(0);
    if(ix >= count) return;
    idiff[ix] = 0;
}
    """)

if fiber_tissue:
    print("""
/*
 * Fiber-to-tissue diffusion program
 * Performs a single diffusion step wherein current flows from a fiber to a
 * single cell on a piece of tissue. This function should only be called once:
 * it isnt't a parallel function but running it on the device prevents an
 * unnecessary memory copy.
 *
 * Arguments
 *  nfx     : The number of fiber cells in the x-direction
 *  nfy     : The number of fiber cells in the y-direction
 *  ntx     : The number of tissue cells in the x-direction
 *  ctx     : The x-index of the first connected tissue cell
 *  cty     : The y-index of the first connected tissue cell
 *  nsf     : The number of state variables in the fiber cell model
 *  nst     : The number of state variables in the tissue cell model
 *  ivf     : The index of the membrane potential in the fiber state vector
 *  ivt     : The index of the membrane potential in the tissue state vector
 *  gft     : The fiber-to-tissue conductance
 *  state_f : The fiber state vector
 *  state_t : The tissue state vector
 *  idiff_f : The diffusion current vector for the fiber model
 *  idiff_t : The diffusion current vector for the tissue model
 */
__kernel void diff_step_fiber_tissue(
    const unsigned long nfx,
    const unsigned long nfy,
    const unsigned long ntx,
    const unsigned long ctx,
    const unsigned long cty,
    const unsigned long nsf,
    const unsigned long nst,
    const int ivf,
    const int ivt,
    const Real gft,
    const __global Real *state_f,
    const __global Real *state_t,
    __global Real *idiff_f,
    __global Real *idiff_t)
{
    const unsigned long cid = get_global_id(0);
    const unsigned long iff = (nfx - 1) + cid * nfx;
    const unsigned long ift = ctx + (cty + cid) * ntx;
    const unsigned long off = iff * nsf + ivf;
    const unsigned long oft = ift * nst + ivt;
    if (cid < nfy) {
        // Connection
        Real idiff = gft * (state_f[off] - state_t[oft]);
        idiff_f[iff] += idiff;
        idiff_t[ift] -= idiff;
    }
}
    """)
