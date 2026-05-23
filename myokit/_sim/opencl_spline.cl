<?
#
# opencl_spline.cl
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
    list_all_derivatives = True)

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
        return pre + 'D_' + var.var().uname()
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
    print('#define ' + var.uname() + ' state[off + ' + str(var.indice()) + ']')

print('')
print('/* Spline functions. */')
splines = {}

use_if_tree = True
use_step_sum = False

if use_if_tree:
    # First attempt, using a big if-tree to set the constants
    def print_tree(tree, tabs):
        pre = tabs * tab
        # Print a spline-parameter setting tree
        if type(tree) == myokit.If:
            print(pre + 'if(' + w.ex(tree.condition()) + ') {')
            print_tree(tree.value(True), tabs+1)
            print(pre + '} else {')
            print_tree(tree.value(False), tabs+1)
            print(pre + '}')
        else:
            for k, c in enumerate(tree.coefficients()):
                print(pre + '_p' + str(k) + ' = ' + w.ex(c) + ';')

    for comp, eqs in equations.iteritems():
        for eq in eqs:
            if type(eq.rhs) == myokit.Spline:
                fname = '_spline_' + eq.lhs.var().uname()
                spline = eq.rhs
                splines[spline] = fname

                # Use _x instead of variable name inside function
                lhs = spline.var()
                def v2(ex):
                    if ex == lhs:
                        return '_x'
                    return v(ex)
                w.set_lhs_function(v2)

                # Create function
                print('Real ' + fname + '(Real _x)')
                print('{')
                pre = tab
                n = 1 + spline.degree()
                for i in xrange(0, n):
                    print pre + 'Real _p' + str(i) + ';'
                print_tree(spline.if_tree(), 1)
                p = ['_p' + str(i) for i in xrange(0, n)]
                f = p.pop()
                while p:
                    f = p.pop() + ' + _x * (' + f + ')'
                print(pre + 'return ' + f + ';')
                print('}')
                print('')
    w.set_lhs_function(v)
    
if use_step_sum:
    # Second attempt, params in constant memory, find index with step() funcs
    # Gather splines
    for comp, eqs in equations.iteritems():
        for eq in eqs:
            if type(eq.rhs) == myokit.Spline:
                fname = '_spline_' + eq.lhs.var().uname()
                spline = eq.rhs
                splines[spline] = fname    
    # Create parameter arrays
    for spline, fname in splines.iteritems():
        n = (spline.degree() + 1) * spline.count_pieces()
        pname = '_p' + fname
        print('__constant Real ' + pname + '[' + str(n) + '] = {')
        p = []
        for piece in spline.piecewise().pieces():
            for c in piece.coefficients():
                p.append(tab + w.ex(c))
        print(',\n'.join(p))
        print('};')
    for spline, fname in splines.iteritems():
        pname = '_p' + fname
        
        # Use _x instead of variable name inside function
        lhs = spline.var()
        def v2(ex):
            if ex == lhs:
                return '_x'
            return v(ex)
        w.set_lhs_function(v2)

        # Create function
        print('__private inline Real ' + fname + '(__private const Real _x)')
        print('{')
        pre = tab
        n = 1 + spline.degree()

        """        
        for i in xrange(0, n):
            print pre + 'Real _p' + str(i) + ';'
        print_tree(spline.if_tree(), 1)
        p = ['_p' + str(i) for i in xrange(0, n)]
        f = p.pop()
        while p:
            f = p.pop() + ' + _x * (' + f + ')'
        """
        
        #print(pre + 'return ' + f + ';')
        print(pre + 'return 0;')
        
        print('}')
        print('')
    w.set_lhs_function(v)

print('')
for comp, ilist in comp_in.iteritems():
    olist = comp_out[comp]
    if len(olist) == 0:
        continue

    # Comment
    print('/*')
    print('Component: ' + comp.name())
    if 'desc' in comp.meta:
        print(comp.meta['desc'])
    print('*/')

    # Function header
    args = ['const int off', '__global Real *state']
    args.extend(['Real '  + v(lhs) for lhs in ilist])
    args.extend(['__private Real *' + v(lhs) for lhs in olist])
    set_pointers(olist)
    name = 'calc_' + comp.name()
    print('void ' + name + '(' + ', '.join(args) + ')')
    print('{')

    # Equations
    for eq in equations[comp.name()].equations(const=False):
        var = eq.lhs.var()
        if var in bound_variables:
            continue
        pre = tab
        if not (eq.lhs in ilist or eq.lhs in olist):
            pre += 'Real '
        if eq.rhs in splines:
            fname = splines[eq.rhs]
            vname = w.ex(eq.rhs.var())
            print(pre + w.ex(eq.lhs) + ' = ' + fname + '(' + vname + ');')
        else:
            print(pre + w.eq(eq) + ';')

    print('}')
    print('')
    set_pointers(None)

?>

/*
 * Cell kernel.
 * Computes a single Euler-step for a single cell.
 *
 * Arguments
 *  nx       : The number of cells in the x-direction
 *  ny       : The number of cells in the y-direction
 *  time     : The current simulation time
 *  dt       : The time step to take
 *  nx_paced : The number of cells being paced in the x-direction
 *  ny_paced : The number of cells being paced in the y-direction
 *  pace_in  : The current pacing value
 *  state    : The state vector
 *  idiff_in : The diffusion current vector
 */
__kernel void cell_step(
    const int nx,
    const int ny,
    const Real time,
    const Real dt,
    const int nx_paced,
    const int ny_paced,
    const Real pace_in,
    __global Real *state,
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

    # Skip components without output
    if len(olist) == 0:
        continue

    # Declare any output variables
    for var in comp_out[comp]:
        print(tab + 'Real ' + v(var) + ' = 0;')

    # Function header
    args = ['off', 'state']
    args.extend([v(lhs) for lhs in ilist])
    args.extend(['&' + v(lhs) for lhs in olist])
    print(tab + 'calc_' + comp.name() + '(' + ', '.join(args) + ');')

            
?>
    /* Perform update */
<?
for var in model.states():
    print(tab + v(var) + ' += dt * ' + v(var.lhs()) + ';')
    
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
__kernel void diff_step(
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
    const int nfx,
    const int nfy,
    const int ntx,
    const int ctx,
    const int cty,
    const int nsf,
    const int nst,
    const int ivf,
    const int ivt,
    const Real gft,
    __global Real *state_f,
    __global Real *state_t,
    __global Real *idiff_f,
    __global Real *idiff_t)
{
    const int cid = get_global_id(0);
    const int iff = (nfx - 1) + cid * nfx;
    const int ift = ctx + (cty + cid) * ntx;
    const int off = iff * nsf + ivf;
    const int oft = ift * nst + ivt;
    if (cid < nfy) {
        // Connection
        Real idiff = gft * (state_f[off] - state_t[oft]);        
        idiff_f[iff] += idiff;
        idiff_t[ift] -= idiff;
    }
}

<?
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
