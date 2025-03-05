<?
# cable.c
#
# A pype template for a cable simulation
#
# Required variables
# ----------------------------------------------
# module_name   A module name
# model         A myokit model
# vmvar         The membrane potential variable
# ncells        The number of cells
# rl_states     A map {state : (inf, tau)}
# ----------------------------------------------
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit
import myokit.formats.ansic as ansic

# Get model
model.reserve_unique_names(*ansic.keywords)
model.create_unique_names()

# Get expression writer
w = ansic.AnsiCExpressionWriter()

# Process bindings, remove unsupported bindings.
bound_variables = myokit._prepare_bindings(model, {
    'time'         : 'engine_time',
    'pace'         : 'engine_pace',
    'diffusion_current' : 'diffusion_current',
})

# Define var/lhs function
def v(var, pre='cell->'):
    """
    Accepts a variable or a left-hand-side expression and returns its C
    representation.
    """
    if isinstance(var, myokit.Derivative):
        # Explicitly asked for derivative
        return pre + 'D_' + var.var().uname()
    if isinstance(var, myokit.Name):
        var = var.var()
    if var.is_state():
        return pre + 'S_' + var.uname()
    elif var.is_constant():
        return pre + 'C_' + var.uname()
    else:
        return pre + 'I_' + var.uname()
w.set_lhs_function(v)

# Get membrane potential
vm = v(vmvar, pre='')

# Tab
tab = '    '

# Get equations
equations = model.solvable_order()
?>
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "pacing.h"

<?
if myokit.DEBUG_SM:
    print('// Show debug output')
    print('#ifndef MYOKIT_DEBUG_MESSAGES')
    print('#define MYOKIT_DEBUG_MESSAGES')
    print('#endif')
?>

/*
 * Engine variables
 */
double engine_time = 0;
double engine_pace = 0;

/*
 * Cell component
 */
#define N_STATE <?=model.count_states()?>
typedef struct Cell {
<?
print(tab + '/* Bound variables */')
for var in model.variables(bound=True, deep=True):
    print(tab + 'double ' + v(var, pre='') + ';')
print(tab + '/* State variables */')
for var in model.states():
    print(tab + 'double ' + v(var, pre='') + ';')
print(tab + '/* State derivatives */')
for var in model.states():
    print(tab + 'double ' + v(var.lhs(), pre='') + ';')
print(tab + '/* Intermediary variables */')
for var in model.variables(inter=True, bound=False, deep=True):
    print(tab + 'double ' + v(var, pre='') + ';')
print(tab + '/* Constants */')
for var in model.variables(const=True, bound=False, deep=True):
    print(tab + 'double ' + v(var, pre='') + ';')
?>} Cell;

/*
 * Add a variable to the logging lists. Returns 1 if successful
 */
static int log_add(PyObject* data, PyObject** logs, double** vars, int i, char* name, const double* var)
{
    int added = 0;
    PyObject* key = PyUnicode_FromString(name);
    if (PyDict_Contains(data, key) == 1) {
        logs[i] = PyDict_GetItem(data, key); /* Borrowed reference */
        vars[i] = (double*)var;
        added = 1;
    }
    Py_DECREF(key);
    return added;
}

/*
 * Variables
 */
/* Input arguments */
int ncells;             /* Number of cells */
int npaced;             /* Number of cells receiving stimulus */
double g;               /* Conductance */
double tmin;            /* The initial simulation time */
double tmax;            /* The final simulation time */
double default_dt;      /* The default step size */
PyObject* state_in;     /* The initial states */
PyObject* state_out;    /* The final states */
PyObject *protocol;     /* The pacing protocol */
PyObject *log_dict;     /* The log dict */
double log_interval;    /* The log interval (0 to disable) */

/* Cells */
Cell *cells;            /* All used cells */

/* Running */
int running = 0;        /* Running yes/no */
double dt;              /* The next step size to use */
double dt_min;          /* The minimum step size to use */
double tnext;           /* The next forced time (event or end of sim) */
unsigned long istep;    /* The index of the current step */
int intermediary_step;  /* True if an intermediary step is being taken */

/* Logging */
PyObject **logs;        /* An array of pointers to a PyObject */
double **vars;          /* An array of pointers to double */
int ivars;              /* Iterate over logging variables */
int nvars;              /* Number of logging variables */
unsigned long ilog;     /* The number of points in the log */
double tlog;            /* Next logging point */

/* Pacing */
double tpace;           /* Next event start or end */
ESys pacing;            /* Pacing system */

/* Temporary objects: decref before re-using for another var :)
   (Unless you got it through PyList_GetItem or PyTuble_GetItem) */
PyObject *flt;              /* PyFloat, various uses */
PyObject *ret;              /* PyFloat, used as return value from python calls */
PyObject *list_update_str;  /* PyUnicode, ssed to call "append" method */

/*
 * Given a current state, this method calculates all diffusion currents, sets
 * the time and pacing variables and calculates all derivatives.
 */
static void
rhs()
{
    int icell;
    Cell* cell;
    double diffusion_current = 0.0;  // Diffusion current

<?
var = model.binding('diffusion_current')
if var is not None:
    print(tab*1 + '/*')
    print(tab*1 + ' * Set diffusion currents')
    print(tab*1 + ' */')
    print(tab*1 + 'if (ncells > 1) {')
    print(tab*2 + 'Cell *clast, *cnext;')
    print(tab*2 + 'cell = clast = cnext = cells;')
    print(tab*2 + 'cnext++;')
    print(tab*2 + '')
    print(tab*2 + '/* First cell */')
    print(tab*2 + 'diffusion_current = g * (cell->' + vm + ' - cnext->' + vm + ');')
    print(tab*2 + v(var) + ' = diffusion_current;')
    print(tab*2 + 'cnext++;')
    print(tab*2 + 'cell++;')
    print(tab*2 + '/* Doubly-connected cells */')
    print(tab*2 + 'for(icell=2; icell<ncells; icell++) {')
    print(tab*3 + 'diffusion_current = g * (2.0*cell-> ' + vm + ' - clast-> ' + vm + ' - cnext->' + vm + ');')
    print(tab*3 + v(var) + ' = diffusion_current;')
    print(tab*3 + 'clast++;')
    print(tab*3 + 'cnext++;')
    print(tab*3 + 'cell++;')
    print(tab*2 + '}')
    print(tab*2 + '/* Last cell */')
    print(tab*2 + 'diffusion_current = g * (cell->' + vm + ' - clast->' + vm + ');')
    print(tab*2 + v(var) + ' = diffusion_current;')
    print(tab*1 + '}')

var = model.binding('pace')
if var is not None:
    print(tab*1 + '/*')
    print(tab*1 + ' * Set pacing current')
    print(tab*1 + ' */')
    print(tab*1 + 'cell = cells;')
    print(tab*1 + 'for(icell=0; icell<npaced; icell++) {')
    print(tab*2 + v(var) + ' = engine_pace;')
    print(tab*2 + 'cell++;')
    print(tab*1 + '}')

?>

    /*
     * Set time, calculate derivatives
     */
    cell = cells;
    for(icell=0; icell<ncells; icell++) {
<?
var = model.time()
print(tab*2 + v(var) + ' = engine_time;')
for label, eqs in equations.items():
    for eq in eqs.equations(const=False, bound=False):
        print(tab*2 + w.eq(eq) + ';')
?>
        cell++;
    }
}

/*
 * Cleans up after a simulation
 */
static PyObject*
sim_clean()
{
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Clean called.\n");
    #endif

    if (running != 0) {

        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("Cleaning.\n");
        #endif

        /* Done with str="append", decref it */
        Py_XDECREF(list_update_str); list_update_str = NULL;

        /* Free allocated space */
        free(logs); logs = NULL;
        free(vars); vars = NULL;
        free(cells); cells = NULL;

        /* Free pacing system memory */
        ESys_Destroy(pacing); pacing = NULL;

        /* No longer running */
        running = 0;
    }

    /* Return 0, allowing the construct
        PyErr_SetString(PyExc_Exception, "Oh noes!");
        return sim_clean()
       to terminate a python function. */
    return 0;
}
static PyObject*
py_sim_clean()
{
    sim_clean();
    Py_RETURN_NONE;
}

/*
 * Initialize a run
 */
static PyObject*
sim_init(PyObject *self, PyObject *args)
{
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Initialising.\n");
    #endif

    int icell;
    Cell* cell;
    int i_state;
    char log_var_name[1000];
    ESys_Flag flag_pacing;

    /* Check if already running */
    if (running != 0) {
        PyErr_SetString(PyExc_Exception, "Simulation already initialized.");
        return 0;
    }

    /* Set all pointers used by sim_clean to null */
    list_update_str = NULL;
    logs = NULL;
    vars = NULL;
    cells = NULL;
    pacing = NULL;

    /* Check input arguments (borrowed references) */
    if (!PyArg_ParseTuple(args, "iddddOOOiOd",
            &ncells,
            &g,
            &tmin,
            &tmax,
            &default_dt,
            &state_in,
            &state_out,
            &protocol,
            &npaced,
            &log_dict,
            &log_interval)) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }

    /* Now officialy running :) */
    running = 1;

    /***************************************************************
     *
     * From this point on, no more direct returning! Use sim_clean()
     *
     */

    /* Create cell structs */
    cells = (Cell*)malloc(ncells*sizeof(Cell));
    if (cells == 0) {
        PyErr_SetString(PyExc_Exception, "Number of cells must be greater than zero.");
        return sim_clean();
    }

    /* Check number of paced cells */
    if (npaced > ncells) {
        PyErr_SetString(PyExc_Exception, "'npaced' cannot exceed ncells.");
        return sim_clean();
    } /* If this is violated you get random segfaults */

    /* Check state in and out lists */
    if (!PyList_Check(state_in)) {
        PyErr_SetString(PyExc_Exception, "'state_in' must be a list.");
        return sim_clean();
    }
    if (PyList_Size(state_in) != ncells * N_STATE) {
        PyErr_SetString(PyExc_Exception, "'state_in' must have size ncells * n_states.");
        return sim_clean();
    }
    if (!PyList_Check(state_out)) {
        PyErr_SetString(PyExc_Exception, "'state_out' must be a list.");
        return sim_clean();
    }
    if (PyList_Size(state_out) != ncells * N_STATE) {
        PyErr_SetString(PyExc_Exception, "'state_out' must have size ncells * n_states.");
        return sim_clean();
    }
    for(i_state=0; i_state<ncells * N_STATE; i_state++) {
        flt = PyList_GetItem(state_in, i_state);    /* Borrowed reference */
        if (!PyFloat_Check(flt)) {
            PyErr_Format(PyExc_Exception, "Item %d in state vector is not a float.", i_state);
            return sim_clean();
        }
    }

    /* Set minimum step size */
    dt_min = 1e-2 * default_dt;

    /* Set up logging */
    list_update_str = PyUnicode_FromString("append");
    if (!PyDict_Check(log_dict)) {
        PyErr_SetString(PyExc_Exception, "Log argument must be a dict.");
        return sim_clean();
    }
    nvars = PyDict_Size(log_dict);
    logs = (PyObject**)malloc(sizeof(PyObject*)*nvars); /* Pointers to logging lists */
    vars = (double**)malloc(sizeof(double*)*nvars); /* Pointers to variables to log */

    ivars = 0;
    cell = cells;
<?

# Time and pace are set globally, use only the value from the first cell
var_time = model.time()
print(tab + 'ivars += log_add(log_dict, logs, vars, ivars, "' + var_time.qname() + '", &' + v(var_time) + ');')
var_pace = model.binding('pace')
if var_pace is not None:
    print(tab + 'ivars += log_add(log_dict, logs, vars, ivars, "' + var_pace.qname() + '", &' + v(var_pace) + ');')

# Add remaining variables
print(tab + 'for(icell=0; icell<ncells; icell++) {')
for var in model.variables(deep=True, const=False):
    if var in (var_time, var_pace):
        continue
    print(tab * 2 + 'sprintf(log_var_name, "%d.' + var.qname() + '", icell);')
    print(tab * 2 + 'ivars += log_add(log_dict, logs, vars, ivars, log_var_name, &' + v(var) + ');')
print(tab * 2 + 'cell++;')
print(tab + '}')

?>
    /* Check if log contained extra variables */
    if (ivars != nvars) {
        PyErr_SetString(PyExc_Exception, "Unknown variables found in logging dictionary.");
        return sim_clean();
    }

    /* Set up pacing */
    pacing = ESys_Create(tmin, &flag_pacing);
    if (flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
    flag_pacing = ESys_Populate(pacing, protocol);
    if (flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
    flag_pacing = ESys_AdvanceTime(pacing, tmin);
    if (flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
    tpace = ESys_GetNextTime(pacing, &flag_pacing);
    engine_pace = ESys_GetLevel(pacing, &flag_pacing);

    /* Set simulation starting time */
    engine_time = tmin;

    /* Initialize cells: set constants, calculated constants, initial values,
       zeros for pacing and stimulus */
    cell = cells;
    for(icell=0; icell<ncells; icell++) {
        /* Literal values & calculated constants */
<?
for label, eqs in equations.items():
    for eq in eqs.equations(const=True):
        print(tab*2 + w.eq(eq) + ';')
?>
        /* Initial values */
<?
for var in model.states():
    print(tab*2 + v(var) + ' = PyFloat_AsDouble(PyList_GetItem(state_in, icell * N_STATE + ' + str(var.index()) + '));')
?>
        /* Zeros for pacing and diffusion current */
<?
var = model.binding('pace')
if var is not None:
    print(tab*2 + v(var) + ' = 0;')
var = model.binding('diffusion_current')
if var is not None:
    print(tab*2 + v(var) + ' = 0;')
?>
        cell++;
    }

    /* Calculate rhs at initial time */
    rhs();

    /* Set first point to step to */
    istep = 1;

    /* Set first logging point */
    ilog = 0;
    tlog = tmin + (double)ilog * log_interval;

    /* Done! */
    Py_RETURN_NONE;
}

/*
 * Takes the next steps in a simulation run
 */
static PyObject*
sim_step(PyObject *self, PyObject *args)
{
    ESys_Flag flag_pacing;
    int icell;
    Cell* cell;
    int steps_taken = 0;
    double d;

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Entering sim_step.\n");
    #endif

    /* Start simulation */
    while(1) {

        /* Log if we've reached or passed a logging point */
        /* Note: rhs has already been calculated by init or previous step */
        if (engine_time >= tlog) {
            for(ivars = 0; ivars<nvars; ivars++) {
                flt = PyFloat_FromDouble(*vars[ivars]);
                ret = PyObject_CallMethodObjArgs(logs[ivars], list_update_str, flt, NULL);
                Py_DECREF(flt); flt = NULL;
                Py_XDECREF(ret);
                if (ret == NULL) {
                    PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                    return sim_clean();
                }
            }
            ret = NULL;

            /* Set next logging point */
            ilog++;
            tlog = tmin + (double)ilog * log_interval;
        }

        /* Determine appropriate time step */
        dt = tmin + (double)istep * default_dt - engine_time;
        intermediary_step = 0;
        d = tpace - engine_time; if (d > dt_min && d < dt) {dt = d; intermediary_step = 1; }
        d = tmax - engine_time; if (d > dt_min && d < dt) {dt = d; intermediary_step = 1; }
        d = tlog - engine_time; if (d > dt_min && d < dt) {dt = d; intermediary_step = 1; }
        if (!intermediary_step) istep++;

        /* Move to next time (1) Update the time variable */
        engine_time += dt;
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("t=%f, dt=%f\n", engine_time, dt);
        #endif

        /* Move to next time (2) Update the pacing variable */
        flag_pacing = ESys_AdvanceTime(pacing, engine_time);
        if (flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
        tpace = ESys_GetNextTime(pacing, NULL);
        engine_pace = ESys_GetLevel(pacing, NULL);

        /* Move to next time (3) Update the states */
        cell = cells;
        for(icell=0; icell<ncells; icell++) {
<?
for var in model.states():
    if var in rl_states:
        inf, tau = rl_states[var]
        inf, tau, var = v(inf), v(tau), v(var)
        print(tab*3 + var + ' = ' + inf + ' - (' + inf + ' - ' + var + ') * exp(-dt / ' + tau + ');')
    else:
        print(tab*3 + v(var) + ' += dt * ' + v(var.lhs()) + ';')
?>
            cell++;
        }

        /* Move to next time (4) Calculate the new derivatives, intermediaries etc. */
        rhs();

        /*
         * Are we done?
         * Check this *before* logging: Last point reached should not be
         * logged (half-open convention for fixed interval logging!)
         */
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("t=%f, tmax=%f, t>=tmax %d\n", engine_time, tmax, engine_time>=tmax);
        #endif
        if (engine_time >= tmax) break;

        /* Perform any Python signal handling */
        if (PyErr_CheckSignals() != 0) {
            /* Exception (e.g. timeout or keyboard interrupt) occurred?
               Then cancel everything! */
            return sim_clean();
        }

        /* Report back to python after every x steps */
        steps_taken++;
        if (steps_taken > 100) {
            steps_taken = 0;
            if(engine_time < tmax) {
                return PyFloat_FromDouble(engine_time);
            }
        }
    }

    /* Set final state */
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Setting final state.\n");
    #endif
    cell = cells;
    for(icell=0; icell<ncells; icell++) {
<?
for var in model.states():
    print(tab*2 + 'PyList_SetItem(state_out, icell * N_STATE + ' + str(var.index()) + ', PyFloat_FromDouble(' + v(var) + '));')
?>
        cell++;
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Done, tidying up and returning.\n");
    #endif

    sim_clean();    /* Ignore return value */
    return PyFloat_FromDouble(engine_time);
}

/* Methods in this module */
static PyMethodDef SimMethods[] = {
    {"sim_init", sim_init, METH_VARARGS, "Initialize the simulation."},
    {"sim_step", sim_step, METH_VARARGS, "Perform the next step in the simulation."},
    {"sim_clean", py_sim_clean, METH_VARARGS, "Clean up after an aborted simulation."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Generated Cable module",   /* m_doc */
        -1,                         /* m_size */
        SimMethods,                 /* m_methods */
        NULL,                       /* m_reload */
        NULL,                       /* m_traverse */
        NULL,                       /* m_clear */
        NULL,                       /* m_free */
    };

    PyMODINIT_FUNC PyInit_<?=module_name?>(void) {
        return PyModule_Create(&moduledef);
    }

#else

    PyMODINIT_FUNC
    init<?=module_name?>(void) {
        (void) Py_InitModule("<?= module_name ?>", SimMethods);
    }

#endif
