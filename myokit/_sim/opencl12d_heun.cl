<?
#
# opencl_kernel.cl
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
# ----------------------------------------------------------------------------
#
# This file is part of Myokit
#  Copyright 2011-2014 Michael Clerx, Maastricht University
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import myokit
from myokit.formats import opencl
   
# Get equations
equations = model.solvable_order()

# Delete "*remaning*" group, guaranteed to be empty with independent components
del(equations['*remaining*'])

# Get component order
comp_order = equations.keys()
comp_order = [model.get(c) for c in comp_order]

# Get component inputs/output arguments
comp_in, comp_out = model.map_component_io(
    omit_states = True,
    omit_constants = True,
    omit_derivatives = True)

# Bound variables will be passed in to every function as needed, so they can be
# removed from the input/output lists
def clear_io_list(comp_list):
    for comp, clist in comp_list.iteritems():
        for var in bound_variables:
            lhs = var.lhs()
            while lhs in clist:
                clist.remove(lhs)
clear_io_list(comp_in)
clear_io_list(comp_out)

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
            print('#define ' + v(eq.lhs) + ' (' + w.ex(eq.rhs) + ')')

print('')
print('/* Aliases of state variables. */')
for var in model.states():
    print('#define ' + var.uname() + ' y[off + ' + str(var.indice()) + ']')

print('')
print('/* Aliases of state variable derivatives. */')
for var in model.states():
    print('#define _d' + var.uname() + ' dy[off + ' + str(var.indice()) + ']')


print('')
for comp, ilist in comp_in.iteritems():
    olist = comp_out[comp]
    if len(olist) == 0 and not comp.has_variables(state=True):
        continue

    # Comment
    print('/*')
    print('Component: ' + comp.name())
    if 'desc' in comp.meta:
        print(comp.meta['desc'])
    print('*/')

    # Function header
    args = ['const int cid', 'const int off', '__global Real *y', '__global Real *dy']
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
        if not (eq.lhs.is_derivative() or eq.lhs in ilist or eq.lhs in olist):
            pre += 'Real '
        if var not in bound_variables:
            print(pre + w.eq(eq) + ';')

    print('}')
    print('')
    set_pointers(None)
?>

/*
 * Cell kernel.
 * Computes the derivatives for a given state
 *
 * Arguments
 *  nx       : The number of cells in the x-direction
 *  ny       : The number of cells in the y-direction
 *  time     : The current simulation time
 *  nx_paced : The number of cells being paced in the x-direction
 *  ny_paced : The number of cells being paced in the y-direction
 *  pace_in  : The current pacing value
 *  y        : The state vector
 *  dy       : The state derivatives vector
 *  idiff_in : The diffusion current vector
 */
__kernel void cell_step(
    const int nx,
    const int ny,
    const Real time,
    const int nx_paced,
    const int ny_paced,
    const Real pace_in,
    __global Real *y,
    __global Real *dy,
    __global const Real* idiff_in)
{
    const int ix = get_global_id(0);
    const int iy = get_global_id(1);
    if(ix >= nx) return;
    if(iy >= ny) return;
    
    // Offset of this cell's state in the state vector
    const int cid = ix + iy * nx;
    const int off = cid * n_state;
    
    // Diffusion
    Real idiff = idiff_in[cid];
    
    // Pacing
    Real pace = (ix < nx_paced && iy < ny_paced) ? pace_in : 0;    
    
<?
print(tab + '// Evaluate derivatives')
for comp in comp_order:
    ilist = comp_in[comp]
    olist = comp_out[comp]

    # Skip components without output or derivatives
    if len(olist) == 0 and not comp.has_variables(state=True):
        continue

    # Declare any output variables
    for var in comp_out[comp]:
        print(tab + 'Real ' + v(var) + ' = 0;')

    # Function header
    args = ['cid', 'off', 'y', 'dy']
    args.extend([v(lhs) for lhs in ilist])
    args.extend(['&' + v(lhs) for lhs in olist])
    print(tab + 'calc_' + comp.name() + '(' + ', '.join(args) + ');')

?>
}

/*
 * Computes a single forward Euler step.
 *
 * Arguments
 *  nx       : The numer of elements in the vector
 *  y        : The input state vector
 *  y2       : The output state vector
 *  dy       : The state derivatives vector
 */
__kernel void feul_step(
    const int nx,
    const Real dt,
    __global Real *y,
    __global Real *y2,
    __global Real *dy
    )
{
    const int cid = get_global_id(0);
    if(cid < nx) {
        y2[cid] = y[cid] + dt * dy[cid];
    }
}

/*
 * Computes a single Heun step.
 *
 * Arguments
 *  nx       : The numer of elements in the vector
 *  y2       : The output state vector
 *  dy       : The derivatives of y
 *  dy2      : The derivatives of y2
 */
__kernel void heun_step(
    const int nx,
    const Real dt,
    __global Real *y,
    __global Real *dy,
    __global Real *dy2
    )
{
    const int cid = get_global_id(0);
    if(cid < nx) {
        y[cid] += 0.5 * dt * (dy[cid] + dy2[cid]);
    }
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
 *  y     : The state vector
 *  idiff : The diffusion current vector
 */
__kernel void diff_step(
    const int nx,
    const int ny,
    const Real gx,
    const Real gy,
    __global Real *y,
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
            idiff[cid] = gx * (y[off] - y[ofp]);
        } else if (ix == nx - 1) {
            // Last position
            idiff[cid] = gx * (y[off] - y[ofm]);
        } else {
            // Middle positions
            idiff[cid] = gx * (2*y[off] - y[ofm] - y[ofp]);
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
            idiff[cid] += gy * (y[off] - y[ofp]);
        } else if (iy == ny - 1) {
            // Last position
            idiff[cid] += gy * (y[off] - y[ofm]);
        } else {
            // Middle positions
            idiff[cid] += gy * (2*y[off] - y[ofm] - y[ofp]);
        }
    }
}

<?
print('/* Remove aliases of state variables. */')
for var in model.states():
    print('#undef ' + var.uname())
print('')
print('/* Remove aliases of state variable derivatives. */')
for var in model.states():
    print('#undef _d' + var.uname())
print('')
print('/* Remove constant definitions */')
for group in equations.itervalues():
    for eq in group.equations(const=True):
        print('#undef ' + v(eq.lhs))
?>
#undef n_state
