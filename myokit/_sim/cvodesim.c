<?
# cvodesim.c
#
# A pype template for a single cell CVODE-based simulation.
#
# Required variables
# -----------------------------------------------------------------------------
# module_name A module name
# model       A myokit model
# potential   A variable from the model used to track threshold crossings
# -----------------------------------------------------------------------------
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

# Define lhs function
def v(var):
    # Explicitly asking for derivative?
    if isinstance(var, myokit.Derivative):
        return 'NV_Ith_S(ydot, ' + str(var.var().indice()) + ')'
    # Name given? get variable object from name
    if isinstance(var, myokit.Name):
        var = var.var()
    # Handle states
    if var.is_state():
        return 'NV_Ith_S(y, ' + str(var.indice()) + ')'
    # Handle constants and intermediary variables
    if var.is_constant():
        return 'AC_' + var.uname()
    else:
        return 'AV_' + var.uname()
w.set_lhs_function(v)

# Tab
tab = '    '

# Get mapping of bound variables to internal refs, set the RHS of unbound variables
# to zero and remove any unsupported bindings.
bound_variables = model.prepare_bindings({
    'time'        : 't',
    'pace'        : 'engine_pace',
    'realtime'    : 'engine_realtime',
    'evaluations' : 'engine_evaluations',
    })
#
# About the bindings:
#
# Time is bound to "t", the time variable used in the function. This is
#  required for periodic logging and point-list logging, when "tlog" increases
#  while engine_time stays fixed at the current solver time.
# Pace is bound to engine_pace, since the solver always visits the points where
#  its value changes the same problem as with logging "engine_time" doesn't
#  occur.
# Realtime is only useful without variable logging, so again binding to global
#  is ok.
# Evaluations may increase during interpolation, but this evaluation will be
#  taken into account in the global variable "engine_evaluations", so this is
#  fine.
#

# Get equations
equations = model.solvable_order()
?>
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>
#include <math.h>
#include <string.h>

#include <cvode/cvode.h>
#include <nvector/nvector_serial.h>
#include <sundials/sundials_types.h>
#include <sundials/sundials_config.h>
#ifndef SUNDIALS_VERSION_MAJOR
    #define SUNDIALS_VERSION_MAJOR 2
#endif
#if SUNDIALS_VERSION_MAJOR >= 3
    #include <sunmatrix/sunmatrix_dense.h>
    #include <sunlinsol/sunlinsol_dense.h>
    #include <cvode/cvode_direct.h>
#else
    #include <cvode/cvode_dense.h>
#endif

#include "pacing.h"

#define N_STATE <?= model.count_states() ?>
#define USE_CVODE <?= 1 if model.count_states() > 0 else 0 ?>

/* Pacing */
ESys epacing;               /* Event-based pacing system */
FSys fpacing;               /* Fixed-form pacing system */

/*
 * Check sundials flags, set python error
 *  flagvalue : The value to check
 *  funcname : The name of the function that returned the flag
 *  opt : Mode selector
 *         0 : Error if the flag is null
 *         1 : Error if the flag is < 0
 *         2 : Errir
 */
static int
check_cvode_flag(void *flagvalue, char *funcname, int opt)
{
    if (opt == 0 && flagvalue == NULL) {
        /* Check if sundials function returned null pointer */
        char str[200];
        sprintf(str, "%s() failed - returned NULL pointer", funcname);
        PyErr_SetString(PyExc_Exception, str);
        return 1;
    } else if (opt == 1) {
        /* Check if flag < 0 */
        int flag = *((int*)flagvalue);
        if (flag < 0) {
            if (strcmp(funcname, "CVode") == 0) {
                switch (flag) {
                case -1:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -1 CV_TOO_MUCH_WORK: The solver took mxstep internal steps but could not reach tout.");
                    break;
                case -2:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -2 CV_TOO_MUCH_ACC: The solver could not satisfy the accuracy demanded by the user for some internal step.");
                    break;
                case -3:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -3 CV_ERR_FAILURE: Error test failures occurred too many times during one internal time step or minimum step size was reached.");
                    break;
                case -4:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -4 CV_CONV_FAILURE: Convergence test failures occurred too many times during one internal time step or minimum step size was reached.");
                    break;
                case -5:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -5 CV_LINIT_FAIL: The linear solver's initialization function failed.");
                    break;
                case -6:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -6 CV_LSETUP_FAIL: The linear solver's setup function failed in an unrecoverable manner.");
                    break;
                case -7:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -7 CV_LSOLVE_FAIL: The linear solver's solve function failed in an unrecoverable manner.");
                    break;
                case -8:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -8 CV_RHSFUNC_FAIL: The right-hand side function failed in an unrecoverable manner.");
                    break;
                case -9:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -9 CV_FIRST_RHSFUNC_ERR: The right-hand side function failed at the first call.");
                    break;
                case -10:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -10 CV_REPTD_RHSFUNC_ERR: The right-hand side function had repeated recoverable errors.");
                    break;
                case -11:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -11 CV_UNREC_RHSFUNC_ERR: The right-hand side function had a recoverable error, but no recovery is possible.");
                    break;
                case -12:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -12 CV_RTFUNC_FAIL: The root finding function failed in an unrecoverable manner.");
                    break;
                case -20:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -20 CV_MEM_FAIL: A memory allocation failed.");
                    break;
                case -21:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -21 CV_MEM_NULL: The cvode mem argument was NULL.");
                    break;
                case -22:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -22 CV_ILL_INPUT: One of the function inputs is illegal.");
                    break;
                case -23:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -23 CV_NO_MALLOC: The cvode memory block was not allocated by a call to CVodeMalloc.");
                    break;
                case -24:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -24 CV_BAD_K: The derivative order k is larger than the order used.");
                    break;
                case -25:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -25 CV_BAD_T: The time t is outside the last step taken.");
                    break;
                case -26:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -26 CV_BAD_DKY: The output derivative vector is NULL.");
                    break;
                case -27:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -27 CV_TOO_CLOSE: The output and initial times are too close to each other.");
                    break;
                default: {
                     /* Note: Brackets are required here, default: should be followed by
                        a _statement_ and char str[200]; is technically not a statement... */
                    char str[200];
                    sprintf(str, "Function CVode() failed with unknown flag = %d", flag);
                    PyErr_SetString(PyExc_Exception, str);
                }}
            } else {
                char str[200];
                sprintf(str, "%s() failed with flag = %d", funcname, flag);
                PyErr_SetString(PyExc_Exception, str);
            }
            return 1;
        }
    }
    return 0;
}

/*
 * Declare intermediary, temporary and system variables
 */
static realtype engine_time = 0;        /* Engine time */
static realtype engine_time_last = 0;   /* Previous engine time */
static realtype engine_pace = 0;
static realtype engine_realtime = 0;
static realtype engine_starttime = 0;
static realtype rootfinding_threshold = 0;
static long engine_evaluations = 0;
static long engine_steps = 0;
<?
for var in model.variables(state=False, deep=True):
    if var.is_literal():
        print('static realtype ' + v(var) + ' = ' + myokit.float.str(var.rhs().eval()) + ';')
    else:
        print('static realtype ' + v(var) + ';')
?>
/*
 * Set values of calculated constants
 */
static void
updateConstants(void)
{
<?
for label, eqs in equations.items():
    for eq in eqs.equations(const=True):
        if not eq.rhs.is_literal():
            print(tab + w.eq(eq) + ';')
?>}

/*
 * Right-hand-side function of the model ODE
 */
static int
rhs(realtype t, N_Vector y, N_Vector ydot, void *f_data)
{
    /* Fixed-form pacing? Then look-up correct value of pacing variable! */
    FSys_Flag flag_fpacing;
    if (fpacing != NULL) {
        engine_pace = FSys_GetLevel(fpacing, t, &flag_fpacing);
        if (flag_fpacing != FSys_OK) { /* This should never happen */
            FSys_SetPyErr(flag_fpacing);
            return -1;  /* Negative value signals irrecoverable error to CVODE */
        }
    }
<?
for label, eqs in equations.items():
    if eqs.has_equations(const=False):
        print(tab + '/* ' + label + ' */')
        for eq in eqs.equations(const=False):
            var = eq.lhs.var()
            try:
                print(tab + v(var) + ' = ' + bound_variables[var] + ';')
            except KeyError:
                print(tab + w.eq(eq) + ';')
        print(tab)
?>
    engine_evaluations++;
    return 0;
}

/*
 * Right-hand-side function, bound variables only
 */
static int
update_bindings(realtype t, N_Vector y, N_Vector ydot, void *f_data)
{
<?
for var, internal in bound_variables.items():
    print(tab + v(var) + ' = ' + internal + ';')
?>
    return 0;
}

/*
 * Update variables bound to engine.realtime
 */
static int
update_realtime_bindings(realtype t, N_Vector y, N_Vector ydot, void *f_data)
{
<?
var = model.binding('realtime')
if var is not None:
    print(tab + v(var) + ' = engine_realtime;')
?>
    return 0;
}

/*
 * Root finding function
 */<?
root_finding_indice = potential.indice() if potential is not None else 0
?>
static int
root_finding(realtype t, N_Vector y, realtype *gout, void *f_data)
{
    gout[0] = NV_Ith_S(y, <?=root_finding_indice?>) - rootfinding_threshold;
    return 0;
}

/*
 * Settings
 */
static double abs_tol = 1e-6; /* The absolute tolerance */
static double rel_tol = 1e-4; /* The relative tolerance */
static double dt_max = 0;     /* The maximum step size (0.0 for none) */
static double dt_min = 0;     /* The minimum step size (0.0 for none) */

/*
 * Change the tolerance settings
 */
static PyObject*
sim_set_tolerance(PyObject *self, PyObject *args)
{
    /* Check input arguments */
    double tabs, trel;
    if (!PyArg_ParseTuple(args, "dd", &tabs, &trel)) {
        PyErr_SetString(PyExc_Exception, "Expected input arguments: abs_tol(float), rel_tol(float).");
        return 0;
    }
    abs_tol = tabs;
    rel_tol = trel;
    Py_RETURN_NONE;
}

/*
 * Change the maximum step size (0 for none)
 */
static PyObject*
sim_set_max_step_size(PyObject *self, PyObject *args)
{
    /* Check input arguments */
    double tmax;
    if (!PyArg_ParseTuple(args, "d", &tmax)) {
        PyErr_SetString(PyExc_Exception, "Expected input argument: tmax(float).");
        return 0;
    }
    dt_max = tmax;
    Py_RETURN_NONE;
}

/*
 * Change the minimum step size (0 for none)
 */
static PyObject*
sim_set_min_step_size(PyObject *self, PyObject *args)
{
    /* Check input arguments */
    double tmin;
    if (!PyArg_ParseTuple(args, "d", &tmin)) {
        PyErr_SetString(PyExc_Exception, "Expected input argument: tmin(float).");
        return 0;
    }
    dt_min = tmin;
    Py_RETURN_NONE;
}

/*
 * Add a variable to the logging lists. Returns 1 if successful
 */
static int
log_add(PyObject* log_dict, PyObject** logs, realtype** vars, int i, const char* name, const realtype* var)
{
    /* See first use of log_add for notes on unicode */
    int added = 0;
    PyObject* key = PyUnicode_FromString(name);
    if (PyDict_Contains(log_dict, key)) {
        logs[i] = PyDict_GetItem(log_dict, key);
        vars[i] = (realtype*)var;
        added = 1;
    }
    Py_DECREF(key);
    return added;
}

/*
 * Error and warning message handler for CVODE.
 * Error messages are already set via check_cvode_flag, so this method
 * suppresses error messages.
 * Warnings are passed to Python's warning system, where they can be
 * caught or suppressed using the warnings module.
 */
void
ErrorHandler(int error_code, const char *module, const char *function,
             char *msg, void *eh_data)
{
    char errstr[1024];
    if (error_code > 0) {
        sprintf(errstr, "CVODE: %s", msg);
        PyErr_WarnEx(PyExc_RuntimeWarning, errstr, 1);
    }
}

/*
 * Simulation variables
 */

int running = 0;        /* Running yes or no */

/* Input arguments */
double tmin;            /* The initial simulation time */
double tmax;            /* The final simulation time */
PyObject* state_in;     /* The initial state */
PyObject* state_out;    /* The final state */
PyObject* inputs;       /* A vector used to return the binding inputs` values */
PyObject* eprotocol;    /* An event-based pacing protocol */
PyObject* fprotocol;    /* A fixed-form pacing protocol */
PyObject* log_dict;     /* The log dict */
double log_interval;    /* Periodic logging: The log interval (0 to disable) */
PyObject* log_times;    /* Point-list logging: List of points (None to disable) */
PyObject* root_list;    /* Empty list if root finding should be used */
double root_threshold;  /* Threshold to use for root finding */
PyObject* benchtime;    /* Callable time() function or None */

/* Next simulation halting point */
double tnext;

/* Checking for repeated zero size steps */
int zero_step_count;
int max_zero_step_count = 500;   /* Increased this from 50 */

/* CVode objects */
void *cvode_mem;     /* The memory used by the solver */
N_Vector y;          /* Stores the current position y */
N_Vector y_log;      /* Used to store y when logging */
N_Vector dy_log;     /* Used to store dy when logging */
N_Vector y_last;     /* Used to store previous value of y for error handling */
#if SUNDIALS_VERSION_MAJOR >= 3
SUNMatrix sundense_matrix;          /* Dense matrix for linear solves */
SUNLinearSolver sundense_solver;    /* Linear solver object */
#endif
#if SUNDIALS_VERSION_MAJOR >= 6
SUNContext sundials_context; /* A sundials context to run in (for profiling etc.) */
#endif

/* Root finding */
int* rootsfound;     /* Used to store found roots */

/* Logging */
PyObject** logs;            /* An array of pointers to a PyObject */
realtype** vars;            /* An array of pointers to realtype */
int n_vars;                 /* Number of logging variables */
int log_bound;              /* True if logging bound variables */
int log_inter;              /* True if logging intermediary variables */
int log_deriv;              /* True if logging derivatives */
PyObject* list_update_str;  /* PyUnicode, used to call "append" method */
Py_ssize_t ilog;            /* Periodic/point-list logging: Index of next point */
double tlog;                /* Periodic/point-list logging: Next point */
int dynamic_logging;        /* True if logging every point. */

/*
 * Cleans up after a simulation
 */
static PyObject*
sim_clean()
{
    if (running != 0) {
        /* Done with str="append", decref it */
        Py_XDECREF(list_update_str); list_update_str = NULL;

        /* Free allocated space */
        free(vars); vars = NULL;
        free(logs); logs = NULL;
        free(rootsfound); rootsfound = NULL;

        /* Free CVode space */
        N_VDestroy_Serial(y); y = NULL;
        N_VDestroy_Serial(dy_log); dy_log = NULL;
        if (USE_CVODE && !dynamic_logging) {
            N_VDestroy_Serial(y_log);
            y_log = NULL;
        }
        CVodeFree(&cvode_mem); cvode_mem = NULL;
        #if SUNDIALS_VERSION_MAJOR >= 3
        SUNLinSolFree(sundense_solver); sundense_solver = NULL;
        SUNMatDestroy(sundense_matrix); sundense_matrix = NULL;
        #endif
        #if SUNDIALS_VERSION_MAJOR >= 6
        SUNContext_Free(&sundials_context); sundials_context = NULL;
        #endif

        /* Free pacing system space */
        ESys_Destroy(epacing); epacing = NULL;
        FSys_Destroy(fpacing); fpacing = NULL;

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
py_sim_clean(PyObject *self, PyObject *args)
{
    sim_clean();
    Py_RETURN_NONE;
}

/*
 * Initialise a run
 */
static PyObject*
sim_init(PyObject *self, PyObject *args)
{
    int i, j;
    int flag_cvode;
    int log_first_point;
    ESys_Flag flag_epacing;
    FSys_Flag flag_fpacing;
    Py_ssize_t pos;
    PyObject *flt;
    PyObject *key;
    PyObject* ret;
    PyObject *value;

    #ifndef SUNDIALS_DOUBLE_PRECISION
    PyErr_SetString(PyExc_Exception, "Sundials must be compiled with double precision.");
    /* No memory freeing is needed here, return directly */
    return 0;
    #endif

    /* Check if already running */
    if (running != 0) {
        PyErr_SetString(PyExc_Exception, "Simulation already initialized.");
        return 0;
    }

    /* Set all pointers used in sim_clean to null */
    list_update_str = NULL;
    vars = NULL;
    logs = NULL;
    rootsfound = NULL;
    y = NULL;
    dy_log = NULL;
    y_log = NULL;
    cvode_mem = NULL;
    epacing = NULL;
    fpacing = NULL;
    log_times = NULL;
    #if SUNDIALS_VERSION_MAJOR >= 3
    sundense_matrix = NULL;
    sundense_solver = NULL;
    #endif
    #if SUNDIALS_VERSION_MAJOR >= 6
    sundials_context = NULL;
    #endif

    /* Check input arguments */
    if (!PyArg_ParseTuple(args, "ddOOOOOOdOOdO",
            &tmin,
            &tmax,
            &state_in,
            &state_out,
            &inputs,
            &eprotocol,
            &fprotocol,
            &log_dict,
            &log_interval,
            &log_times,
            &root_list,
            &root_threshold,
            &benchtime)) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }

    /* Now officialy running :) */
    running = 1;

    /*************************************************************************
    From this point on, no more direct returning! Use sim_clean()

    To check if this list is still up to date manually search for cvode
    and python stuff. To find what to free() search for "alloc("
    Initialize all to NULL so that free() will work without errors.

    Notes:
    1. Functions like PyList_New and PyDict_New create a new object with a
       refcount of 1. They pass on the ownership of this reference to the
       caller, IE they return the reference and it becomes the caller's
       responsibility to call PyDECREF
    2. Functions like PyList_Append and PyDict_SetItem create a new reference
       to the items you pass them, IE they increase the ref count and will
       decrease it when they're done with it. This means that you retain
       ownership of your own reference to this items and will also need to
       call decref when you're done with them.
    3. PyList_SetItem and PyTuple_SetItem are exceptions to the rule: they
       "steal" a reference to the item you pass into them. This means they do
       not increase the refcount of the item, but _do_ decrease it when they
       themselves are destructed.
       This _only_ holds for the SetItem functions, and _only_ for list and
       tuple.
       The reasonining behind this is that it's a very common scenario for
       populating lists and tuples.
    4. PyList_GetItem and PyTuple_GetItem are exceptions to the rule: they
       return a "borrowed" reference to an item. This means you should never
       decref them!
       This _only_ holds for list and tuple.
    5. When you return a newly created reference from a function, you pass on
       the ownership of that reference to the calling function. This means you
       don't have to call DECREF on the return value of a function.
    6. References passed _into_ your function as arguments are _borrowed_:
       Their refcount doesn't change and you don't have to increase or decrease
       it. The object they point to is guaranteed to exist for as long as your
       function runs.

    Result:
    A. The log and protocol objects passed to this function are borrowed
       references: no need to change the reference count.
    B. The PyFloat objects that are created have refcount 1. They're added to
       the lists using append, which increases their refcount. So they should
       be decref'd after appending.
    C. The time float that is created has refcount 1. It's ownership is passed
       on to the calling function. No need to decref.
    D. The PyFloat objects in this list are added using PyList_SetItem which
       steals ownership: No need to decref.
    */

    /*
     * Create sundials context
     */
    #if SUNDIALS_VERSION_MAJOR >= 6
    flag_cvode = SUNContext_Create(NULL, &sundials_context);
    if (check_cvode_flag(&flag_cvode, "SUNContext_Create", 1)) {
        PyErr_SetString(PyExc_Exception, "Failed to create Sundials context.");
        return sim_clean();
    }
    #endif

    /*
     * Create state vectors
     */

    /* Create state vector */
    #if SUNDIALS_VERSION_MAJOR >= 6
    y = N_VNew_Serial(N_STATE, sundials_context);
    #else
    y = N_VNew_Serial(N_STATE);
    #endif
    if (check_cvode_flag((void*)y, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create state vector.");
        return sim_clean();
    }

    /* Create state vector copy for error handling */
    #if SUNDIALS_VERSION_MAJOR >= 6
    y_last = N_VNew_Serial(N_STATE, sundials_context);
    #else
    y_last = N_VNew_Serial(N_STATE);
    #endif
    if (check_cvode_flag((void*)y_last, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create last-state vector.");
        return sim_clean();
    }

    /* Determine if dynamic logging is being used (or if it's periodic/point-list logging) */
    dynamic_logging = (log_interval <= 0 && log_times == Py_None);

    /* Create state vector for logging */
    if (dynamic_logging || !USE_CVODE) {
        /* Dynamic logging or cvode-free mode: don't interpolate,
           so let y_log point to y */
        y_log = y;
    } else {
        /* Logging at fixed points:
           Keep y_log as a separate N_Vector for cvode interpolation */
        #if SUNDIALS_VERSION_MAJOR >= 6
        y_log = N_VNew_Serial(N_STATE, sundials_context);
        #else
        y_log = N_VNew_Serial(N_STATE);
        #endif
        if (check_cvode_flag((void*)y_log, "N_VNew_Serial", 0)) {
            PyErr_SetString(PyExc_Exception, "Failed to create logging state vector.");
            return sim_clean();
        }
    }

    /* Create derivative vector for logging */
    #if SUNDIALS_VERSION_MAJOR >= 6
    dy_log = N_VNew_Serial(N_STATE, sundials_context);
    #else
    dy_log = N_VNew_Serial(N_STATE);
    #endif
    if (check_cvode_flag((void*)dy_log, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create logging state derivatives vector.");
        return sim_clean();
    }

    /* Set calculated constants */
    updateConstants();

    /* Set initial values */
    if (!PyList_Check(state_in)) {
        PyErr_SetString(PyExc_Exception, "'state_in' must be a list.");
        return sim_clean();
    }
    for(i=0; i<N_STATE; i++) {
        flt = PyList_GetItem(state_in, i);    /* Don't decref! */
        if (!PyFloat_Check(flt)) {
            char errstr[200];
            sprintf(errstr, "Item %d in state vector is not a float.", i);
            PyErr_SetString(PyExc_Exception, errstr);
            return sim_clean();
        }
        NV_Ith_S(y, i) = PyFloat_AsDouble(flt);
        NV_Ith_S(y_last, i) = NV_Ith_S(y, i);
    }

    /* Periodic or point-list logging? Then set init state in y_log as well */
    #if USE_CVODE
    if (!dynamic_logging) {
        for(i=0; i<N_STATE; i++) {
            NV_Ith_S(y_log, i) = NV_Ith_S(y, i);
        }
    }
    #endif
    /* In cvode-free mode, y_log points to y, so no need */

    /* Root finding list of integers (only contains 1 int...) */
    rootsfound = (int*)malloc(sizeof(int)*1);

    /* Reset evaluation count */
    engine_evaluations = 0;

    /* Reset step count */
    engine_steps = 0;

    /* Zero step tracking */
    zero_step_count = 0;

    /* Check output list */
    if (!PyList_Check(state_out)) {
        PyErr_SetString(PyExc_Exception, "'state_out' must be a list.");
        return sim_clean();
    }

    /* Check for loss-of-precision issue in periodic logging */
    if (log_interval > 0) {
        if (tmax + log_interval == tmax) {
            PyErr_SetString(PyExc_Exception, "Log interval is too small compared to tmax; issue with numerical precision: float(tmax + log_interval) = float(tmax).");
            return sim_clean();
        }
    }

    /* Set up logging */
    log_inter = 0;
    log_bound = 0;
    n_vars = PyDict_Size(log_dict);
    logs = (PyObject**)malloc(sizeof(PyObject*)*n_vars);
    vars = (realtype**)malloc(sizeof(realtype*)*n_vars);
    i = 0;

    /* Note: The variable names are all ascii compatible
       In Python2, they are stored in logs as either unicode or bytes
       In Python3, they are stored exclusively as unicode
       However, in Python2 b'name' matches u'name' so this is ok (in Python it
        does not, but we always use unicode so it's ok).
       The strategy here will be to convert these C-strings to unicode
        inside log_add, before the comparison. */

    /* Check states */
<?
for var in model.states():
    print(tab + 'i += log_add(log_dict, logs, vars, i, "' + var.qname() + '", &NV_Ith_S(y_log, ' + str(var.indice())  + '));')
?>

    /* Check derivatives */
    j = i;
<?
for var in model.states():
    print(tab + 'i += log_add(log_dict, logs, vars, i, "dot(' + var.qname() + ')", &NV_Ith_S(dy_log, ' + str(var.indice())  + '));')
?>
    log_deriv = (i > j);

    /* Check bound variables */
    j = i;
<?
for var, internal in bound_variables.items():
    print(tab + 'i += log_add(log_dict, logs, vars, i, "' + var.qname() + '", &' + v(var)  + ');')
?>
    log_bound = (i > j);

    /* Remaining variables will require an extra rhs() call to evaluate their
       values at every log point */
    j = i;
<?
for var in model.variables(deep=True, state=False, bound=False, const=False):
    print(tab + 'i += log_add(log_dict, logs, vars, i, "' + var.qname() + '", &' + v(var)  + ');')
?>
    log_inter = (i > j);

    /* Check if log contained extra variables */
    if (i != n_vars) {
        PyErr_SetString(PyExc_Exception, "Unknown variables found in logging dictionary.");
        return sim_clean();
    }

    /* Set up event-based pacing */
    if (eprotocol != Py_None) {
        epacing = ESys_Create(&flag_epacing);
        if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
        flag_epacing = ESys_Populate(epacing, eprotocol);
        if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
        flag_epacing = ESys_AdvanceTime(epacing, tmin);
        if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
        tnext = ESys_GetNextTime(epacing, &flag_epacing);
        engine_pace = ESys_GetLevel(epacing, &flag_epacing);
        tnext = (tnext < tmax) ? tnext : tmax;
    } else {
        tnext = tmax;
    }

    /* Set up fixed-form pacing */
    if (eprotocol == Py_None && fprotocol != Py_None) {
        /* Check 'protocol' is tuple (times, values) */
        if (!PyTuple_Check(fprotocol)) {
            PyErr_SetString(PyExc_Exception, "Fixed-form pacing protocol should be tuple or None.");
            return sim_clean();
        }
        if (PyTuple_Size(fprotocol) != 2) {
            PyErr_SetString(PyExc_Exception, "Fixed-form pacing protocol tuple should have size 2.");
            return sim_clean();
        }
        /* Create fixed-form pacing object and populate */
        fpacing = FSys_Create(&flag_fpacing);
        if (flag_fpacing != FSys_OK) { FSys_SetPyErr(flag_fpacing); return sim_clean(); }
        flag_fpacing = FSys_Populate(fpacing,
            PyTuple_GetItem(fprotocol, 0),  /* Borrowed, no decref */
            PyTuple_GetItem(fprotocol, 1));
        if (flag_fpacing != FSys_OK) { FSys_SetPyErr(flag_fpacing); return sim_clean(); }
    }

    /* Set simulation starting time */
    engine_time = tmin;

    /* Check dt_max and dt_min */
    if (dt_max < 0) dt_max = 0.0;
    if (dt_min < 0) dt_min = 0.0;

    /* Create solver
     * Using Backward differentiation and Newton iteration */
    #if USE_CVODE > 0
    #if SUNDIALS_VERSION_MAJOR >= 6
        cvode_mem = CVodeCreate(CV_BDF, sundials_context);
    #elif SUNDIALS_VERSION_MAJOR >= 4
        cvode_mem = CVodeCreate(CV_BDF);
    #else
        cvode_mem = CVodeCreate(CV_BDF, CV_NEWTON);
    #endif
    if (check_cvode_flag((void*)cvode_mem, "CVodeCreate", 0)) return sim_clean();

    /* Set error and warning-message handler */
    flag_cvode = CVodeSetErrHandlerFn(cvode_mem, ErrorHandler, NULL);
    if (check_cvode_flag(&flag_cvode, "CVodeInit", 1)) return sim_clean();

    /* Initialise solver memory, specify the rhs */
    flag_cvode = CVodeInit(cvode_mem, rhs, engine_time, y);
    if (check_cvode_flag(&flag_cvode, "CVodeInit", 1)) return sim_clean();

    /* Set absolute and relative tolerances */
    flag_cvode = CVodeSStolerances(cvode_mem, RCONST(rel_tol), RCONST(abs_tol));
    if (check_cvode_flag(&flag_cvode, "CVodeSStolerances", 1)) return sim_clean();

    /* Set a maximum step size (or 0.0 for none) */

    flag_cvode = CVodeSetMaxStep(cvode_mem, dt_max);
    if (check_cvode_flag(&flag_cvode, "CVodeSetmaxStep", 1)) return sim_clean();

    /* Set a minimum step size (or 0.0 for none) */
    flag_cvode = CVodeSetMinStep(cvode_mem, dt_min);
    if (check_cvode_flag(&flag_cvode, "CVodeSetminStep", 1)) return sim_clean();

    #if SUNDIALS_VERSION_MAJOR >= 6
        /* Create dense matrix for use in linear solves */
        sundense_matrix = SUNDenseMatrix(N_STATE, N_STATE, sundials_context);
        if (check_cvode_flag((void *)sundense_matrix, "SUNDenseMatrix", 0)) return sim_clean();

        /* Create dense linear solver object with matrix */
        sundense_solver = SUNLinSol_Dense(y, sundense_matrix, sundials_context);
        if (check_cvode_flag((void *)sundense_solver, "SUNLinSol_Dense", 0)) return sim_clean();

        /* Attach the matrix and solver to cvode */
        flag_cvode = CVodeSetLinearSolver(cvode_mem, sundense_solver, sundense_matrix);
        if (check_cvode_flag(&flag_cvode, "CVodeSetLinearSolver", 1)) return sim_clean();
    #elif SUNDIALS_VERSION_MAJOR >= 4
        /* Create dense matrix for use in linear solves */
        sundense_matrix = SUNDenseMatrix(N_STATE, N_STATE);
        if (check_cvode_flag((void *)sundense_matrix, "SUNDenseMatrix", 0)) return sim_clean();

        /* Create dense linear solver object with matrix */
        sundense_solver = SUNLinSol_Dense(y, sundense_matrix);
        if (check_cvode_flag((void *)sundense_solver, "SUNLinSol_Dense", 0)) return sim_clean();

        /* Attach the matrix and solver to cvode */
        flag_cvode = CVodeSetLinearSolver(cvode_mem, sundense_solver, sundense_matrix);
        if (check_cvode_flag(&flag_cvode, "CVodeSetLinearSolver", 1)) return sim_clean();
    #elif SUNDIALS_VERSION_MAJOR >= 3
        /* Create dense matrix for use in linear solves */
        sundense_matrix = SUNDenseMatrix(N_STATE, N_STATE);
        if(check_cvode_flag((void *)sundense_matrix, "SUNDenseMatrix", 0)) return sim_clean();

        /* Create dense linear solver object with matrix */
        sundense_solver = SUNDenseLinearSolver(y, sundense_matrix);
        if(check_cvode_flag((void *)sundense_solver, "SUNDenseLinearSolver", 0)) return sim_clean();

        /* Attach the matrix and solver to cvode */
        flag_cvode = CVDlsSetLinearSolver(cvode_mem, sundense_solver, sundense_matrix);
        if(check_cvode_flag(&flag_cvode, "CVDlsSetLinearSolver", 1)) return sim_clean();
    #else
        /* Create dense matrix for use in linear solves */
        flag_cvode = CVDense(cvode_mem, N_STATE);
        if (check_cvode_flag(&flag_cvode, "CVDense", 1)) return sim_clean();
    #endif
    #endif

    /* Benchmarking? Then set engine_realtime to 0.0 */
    if (benchtime != Py_None) {
        /* Store initial time as 0 */
        engine_realtime = 0.0;
        /* Tell sim_step to set engine_starttime */
        engine_starttime = -1;
    }

    /* Set string for updating lists/arrays using Python interface. */
    list_update_str = PyUnicode_FromString("append");

    /* Set logging points */
    if (log_interval > 0) {

        /* Periodic logging */
        ilog = 0;
        tlog = tmin;

    } else if (log_times != Py_None) {

        /* Point-list logging */

        /* Check the log_times list */
        if (!PyList_Check(log_times)) {
            PyErr_SetString(PyExc_Exception, "'log_times' must be a list.");
            return sim_clean();
        }

        /* Read next log point off the list */
        ilog = 0;
        tlog = engine_time - 1;
        while(ilog < PyList_Size(log_times) && tlog < engine_time) {
            flt = PyList_GetItem(log_times, ilog); /* Borrowed */
            if (!PyFloat_Check(flt)) {
                PyErr_SetString(PyExc_Exception, "Entries in 'log_times' must be floats.");
                return sim_clean();
            }
            tlog = PyFloat_AsDouble(flt);
            ilog++;
            flt = NULL;
        }

        /* No points beyond engine_time? Then don't log any future points. */
        if(tlog < engine_time) {
            tlog = tmax + 1;
        }

    } else {

        /*
         * Dynamic logging
         *
         * Log the first entry, but only if not appending to an existing log.
         * This prevents points from appearing twice when a simulation with
         * dynamic logging is stopped and started.
         */

        /*  Check if the log is empty */
        log_first_point = 1;
        pos = 0;
        if(PyDict_Next(log_dict, &pos, &key, &value)) {
            /* Items found in dict, randomly selected list now in "value" */
            /* Both key and value are borrowed references, no need to decref */
            log_first_point = (PyObject_Size(value) <= 0);
        }

        /* If so, log the first point! */
        if (log_first_point) {
            rhs(engine_time, y, dy_log, 0);
            /* At this point, we have y(t), inter(t) and dy(t) */
            /* We've also loaded time(t) and pace(t) */
            for(i=0; i<n_vars; i++) {
                flt = PyFloat_FromDouble(*vars[i]);
                ret = PyObject_CallMethodObjArgs(logs[i], list_update_str, flt, NULL);
                Py_DECREF(flt);
                Py_XDECREF(ret);
                if (ret == NULL) {
                    flt = NULL;
                    PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                    return sim_clean();
                }
            }
            flt = NULL;
            ret = NULL;
        }
    }

    /* Root finding enabled? (cvode-mode only) */
    #if USE_CVODE
    if (PySequence_Check(root_list)) {
        /* Set threshold */
        rootfinding_threshold = root_threshold;
        /* Initialize root function with 1 component */
        flag_cvode = CVodeRootInit(cvode_mem, 1, root_finding);
        if (check_cvode_flag(&flag_cvode, "CVodeRootInit", 1)) return sim_clean();
    }
    #endif

    /* Done! */
    Py_RETURN_NONE;
}

/*
 * Takes the next steps in a simulation run
 */
static PyObject*
sim_step(PyObject *self, PyObject *args)
{
    ESys_Flag flag_epacing;
    int i;
    int steps_taken = 0;    /* Number of integration steps taken in this call */
    int flag_cvode;         /* CVode flag */
    int flag_root;          /* Root finding flag */
    int flag_reinit = 0;    /* Set if CVODE needs to be reset during a simulation step */
    PyObject *flt, *ret;

    /*
     * Benchmarking? Then make sure start time is set.
     * This is handled here instead of in sim_init so it only includes time
     * taken performing steps, not time initialising memory etc.
     */
    if (benchtime != Py_None && engine_starttime < 0) {
        flt = PyObject_CallFunction(benchtime, "");
        if (!PyFloat_Check(flt)) {
            Py_XDECREF(flt); flt = NULL;
            PyErr_SetString(PyExc_Exception, "Call to benchmark time function didn't return float.");
            return sim_clean();
        }
        engine_starttime = PyFloat_AsDouble(flt);
        Py_DECREF(flt); flt = NULL;
    }

    /* Go! */
    while(1) {

        /* Back-up current y (no allocation, this is fast) */
        for(i=0; i<N_STATE; i++) {
            NV_Ith_S(y_last, i) = NV_Ith_S(y, i);
        }

        /* Store engine time before step */
        engine_time_last = engine_time;

        #if USE_CVODE

        /* Take a single ODE step */
        flag_cvode = CVode(cvode_mem, tnext, y, &engine_time, CV_ONE_STEP);

        /* Check for errors */
        if (check_cvode_flag(&flag_cvode, "CVode", 1)) {
            /* Something went wrong... Set outputs and return */
            for(i=0; i<N_STATE; i++) {
                PyList_SetItem(state_out, i, PyFloat_FromDouble(NV_Ith_S(y_last, i)));
                /* PyList_SetItem steals a reference: no need to decref the double! */
            }
            PyList_SetItem(inputs, 0, PyFloat_FromDouble(engine_time));
            PyList_SetItem(inputs, 1, PyFloat_FromDouble(engine_pace));
            PyList_SetItem(inputs, 2, PyFloat_FromDouble(engine_realtime));
            PyList_SetItem(inputs, 3, PyFloat_FromDouble(engine_evaluations));
            return sim_clean();
        }

        #else

        /* Just jump to next event */
        /* Note 1: To stay compatible with cvode-mode, don't jump to the
           next log time (if tlog < tnext) */
        /* Note 2: tnext can be infinity, so don't always jump there. */
        engine_time = (tmax > tnext) ? tnext : tmax;
        flag_cvode = CV_SUCCESS;

        #endif

        /* Check if progress is being made */
        if(engine_time == engine_time_last) {
            if(++zero_step_count >= max_zero_step_count) {
                char errstr[200];
                sprintf(errstr, "ZERO_STEP %f", engine_time);
                PyErr_SetString(PyExc_Exception, errstr);
                return sim_clean();
            }
        } else {
            /* Only count consecutive zero steps! */
            zero_step_count = 0;
        }

        /* Update step count */
        engine_steps++;

        /* If we got to this point without errors... */
        if ((flag_cvode == CV_SUCCESS) || (flag_cvode == CV_ROOT_RETURN)) {

            /* Next event time exceeded? (Can't happen in cvode-free mode) */
            #if USE_CVODE
            if (engine_time > tnext) {

                /* Go back to engine_time=tnext */
                flag_cvode = CVodeGetDky(cvode_mem, tnext, 0, y);
                if (check_cvode_flag(&flag_cvode, "CVodeGetDky", 1)) return sim_clean();
                engine_time = tnext;
                /* Require reinit (after logging) */
                flag_reinit = 1;

            } else if (flag_cvode == CV_ROOT_RETURN) {

                /* Store found roots */
                flag_root = CVodeGetRootInfo(cvode_mem, rootsfound);
                if (check_cvode_flag(&flag_root, "CVodeGetRootInfo", 1)) return sim_clean();
                flt = PyTuple_New(2);
                PyTuple_SetItem(flt, 0, PyFloat_FromDouble(engine_time)); /* Steals reference, so this is ok */
                PyTuple_SetItem(flt, 1, PyLong_FromLong(rootsfound[0]));
                ret = PyObject_CallMethodObjArgs(root_list, list_update_str, flt, NULL);
                Py_DECREF(flt); flt = NULL;
                Py_XDECREF(ret);
                if (ret == NULL) {
                    PyErr_SetString(PyExc_Exception, "Call to append() failed on root finding list.");
                    return sim_clean();
                }
                ret = NULL;
            }
            #endif

            /* Periodic logging or point-list logging */
            if (!dynamic_logging && engine_time > tlog) {
                /* Note: For periodic logging, the condition should be
                   `time > tlog` so that we log half-open intervals (i.e. the
                   final point should never be included). */

                /* Benchmarking? Then set engine_realtime */
                if (benchtime != Py_None) {
                    flt = PyObject_CallFunction(benchtime, "");
                    if (!PyFloat_Check(flt)) {
                        Py_XDECREF(flt); flt = NULL;
                        PyErr_SetString(PyExc_Exception, "Call to benchmark time function didn't return float.");
                        return sim_clean();
                    }
                    engine_realtime = PyFloat_AsDouble(flt) - engine_starttime;
                    Py_DECREF(flt); flt = NULL;
                    /* Update any variables bound to realtime */
                    update_realtime_bindings(engine_time, y, dy_log, 0);
                }

                /* Log points */
                while (engine_time > tlog) {

                    /* Get interpolated y(tlog) */
                    #if USE_CVODE
                    flag_cvode = CVodeGetDky(cvode_mem, tlog, 0, y_log);
                    if (check_cvode_flag(&flag_cvode, "CVodeGetDky", 1)) return sim_clean();
                    #endif
                    /* If cvode-free mode, the state can't change so we don't
                       need to do anything here */

                    /* Calculate intermediate variables & derivatives */
                    rhs(tlog, y_log, dy_log, 0);

                    /* Write to log */
                    for(i=0; i<n_vars; i++) {
                        flt = PyFloat_FromDouble(*vars[i]);
                        ret = PyObject_CallMethodObjArgs(logs[i], list_update_str, flt, NULL);
                        Py_DECREF(flt);
                        Py_XDECREF(ret);
                        if (ret == NULL) {
                            flt = NULL;
                            PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                            return sim_clean();
                        }
                    }
                    ret = flt = NULL;

                    /* Get next logging point */
                    if (log_interval > 0) {
                        /* Periodic logging */
                        ilog++;
                        tlog = tmin + (double)ilog * log_interval;
                        if (ilog == 0) {
                            /* Unsigned int wraps around instead of overflowing, becomes zero again */
                            PyErr_SetString(PyExc_Exception, "Overflow in logged step count: Simulation too long!");
                            return sim_clean();
                        }
                    } else {
                        /* Point-list logging */
                        /* Read next log point off the list */
                        if (ilog < PyList_Size(log_times)) {
                            flt = PyList_GetItem(log_times, ilog); /* Borrowed */
                            if (!PyFloat_Check(flt)) {
                                PyErr_SetString(PyExc_Exception, "Entries in 'log_times' must be floats.");
                                return sim_clean();
                            }
                            tlog = PyFloat_AsDouble(flt);
                            ilog++;
                            flt = NULL;
                        } else {
                            tlog = tmax + 1;
                        }
                    }
                }
            }

            /* Event-based pacing */

            /* At this point we have logged everything _before_ engine_time, so
               it's safe to update the pacing mechanism. */
            if (epacing != NULL) {
                flag_epacing = ESys_AdvanceTime(epacing, engine_time);
                if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
                tnext = ESys_GetNextTime(epacing, NULL);
                engine_pace = ESys_GetLevel(epacing, NULL);
                tnext = (tnext < tmax) ? tnext : tmax;
            }

            /* Dynamic logging: Log every visited point */
            if (dynamic_logging) {

                /* Ensure the logged values are correct for the new time t */
                if (log_deriv || log_inter) {
                    /* If logging derivatives or intermediaries, calculate the
                       values for the current time. */
                    rhs(engine_time, y, dy_log, 0);
                } else if (log_bound) {
                    /* Logging bounds but not derivs or inters: No need to run
                       full rhs, just update bound variables */
                    update_bindings(engine_time, y, dy_log, 0);
                }

                /* Benchmarking? Then set engine_realtime */
                if (benchtime != Py_None) {
                    flt = PyObject_CallFunction(benchtime, "");
                    if (!PyFloat_Check(flt)) {
                        Py_XDECREF(flt); flt = NULL;
                        PyErr_SetString(PyExc_Exception, "Call to benchmark time function didn't return float.");
                        return sim_clean();
                    }
                    engine_realtime = PyFloat_AsDouble(flt) - engine_starttime;
                    Py_DECREF(flt); flt = NULL;
                    /* Update any variables bound to realtime */
                    update_realtime_bindings(engine_time, y, dy_log, 0);
                }

                /* Write to log */
                for(i=0; i<n_vars; i++) {
                    flt = PyFloat_FromDouble(*vars[i]);
                    ret = PyObject_CallMethodObjArgs(logs[i], list_update_str, flt, NULL);
                    Py_DECREF(flt); flt = NULL;
                    Py_XDECREF(ret);
                    if (ret == NULL) {
                        PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                        return sim_clean();
                    }
                    ret = NULL;
                }

            }

            /* Reinitialize if needed (cvode-mode only) */
            #if USE_CVODE
            if (flag_reinit) {
                flag_reinit = 0;
                /* Re-init */
                flag_cvode = CVodeReInit(cvode_mem, engine_time, y);
                if (check_cvode_flag(&flag_cvode, "CVodeReInit", 1)) return sim_clean();
            }
            #endif
        }

        /* Check if we're finished */
        if (ESys_eq(engine_time, tmax)) engine_time = tmax;
        if (engine_time >= tmax) break;

        /* Perform any Python signal handling */
        if (PyErr_CheckSignals() != 0) {
            /* Exception (e.g. timeout or keyboard interrupt) occurred?
               Then cancel everything! */
            return sim_clean();
        }

        /* Report back to python after every x steps */
        steps_taken++;
        if (steps_taken >= 100) {
            return PyFloat_FromDouble(engine_time);
        }
    }

    /* Set final state */
    for(i=0; i<N_STATE; i++) {
        PyList_SetItem(state_out, i, PyFloat_FromDouble(NV_Ith_S(y, i)));
        /* PyList_SetItem steals a reference: no need to decref the double! */
    }

    /* Set state of inputs */
    PyList_SetItem(inputs, 0, PyFloat_FromDouble(engine_time));
    PyList_SetItem(inputs, 1, PyFloat_FromDouble(engine_pace));
    PyList_SetItem(inputs, 2, PyFloat_FromDouble(engine_realtime));
    PyList_SetItem(inputs, 3, PyFloat_FromDouble(engine_evaluations));

    sim_clean();    /* Ignore return value */
    return PyFloat_FromDouble(engine_time);
}

/*
 * Evaluates the state derivatives at the given state
 */
static PyObject*
sim_eval_derivatives(PyObject *self, PyObject *args)
{
    /* Declare variables here for C89 compatibility */
    int i;
    int success;
    int iState;
    int flag_cvode;
    double time_in;
    double pace_in;
    char errstr[200];
    PyObject *state;
    PyObject *deriv;
    PyObject *flt;
    N_Vector y;
    N_Vector dy;
    #if SUNDIALS_VERSION_MAJOR >= 6
    SUNContext sundials_context;
    #endif

    /* Start */
    success = 0;

    /* Check input arguments */
    if (!PyArg_ParseTuple(args, "OOdd", &state, &deriv, &time_in, &pace_in)) {
        PyErr_SetString(PyExc_Exception, "Expecting sequence arguments 'y' and 'dy' followed by floats 'time' and 'pace'.");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }
    if (!PySequence_Check(state)) {
        PyErr_SetString(PyExc_Exception, "First argument must support the sequence interface.");
        return 0;
    }
    if (!PySequence_Check(deriv)) {
        PyErr_SetString(PyExc_Exception, "Second argument must support the sequence interface.");
        return 0;
    }

    /* From this point on, no more direct returning: use goto error */
    y = NULL;      /* A cvode SERIAL vector */
    dy = NULL;     /* A cvode SERIAL vector */

    /* Create sundials context */
    #if SUNDIALS_VERSION_MAJOR >= 6
    flag_cvode = SUNContext_Create(NULL, &sundials_context);
    if (check_cvode_flag(&flag_cvode, "SUNContext_Create", 1)) {
        PyErr_SetString(PyExc_Exception, "Failed to create Sundials context.");
        goto error;
    }
    #endif

    /* Temporary object: decref before re-using for another var :) */
    /* (Unless you get them using PyList_GetItem...) */
    flt = NULL;   /* PyFloat */

    /* Create state vectors */
    #if SUNDIALS_VERSION_MAJOR >= 6
    y = N_VNew_Serial(N_STATE, sundials_context);
    #else
    y = N_VNew_Serial(N_STATE);
    #endif
    if (check_cvode_flag((void*)y, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create state vector.");
        goto error;
    }
    #if SUNDIALS_VERSION_MAJOR >= 6
    dy = N_VNew_Serial(N_STATE, sundials_context);
    #else
    dy = N_VNew_Serial(N_STATE);
    #endif
    if (check_cvode_flag((void*)dy, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create state derivatives vector.");
        goto error;
    }

    /* Set calculated constants */
    updateConstants();

    /* Set initial values */
    for (iState = 0; iState < N_STATE; iState++) {
        flt = PySequence_GetItem(state, iState); /* Remember to decref! */
        if (!PyFloat_Check(flt)) {
            Py_XDECREF(flt); flt = NULL;
            sprintf(errstr, "Item %d in state vector is not a float.", iState);
            PyErr_SetString(PyExc_Exception, errstr);
            goto error;
        }
        NV_Ith_S(y, iState) = PyFloat_AsDouble(flt);
        Py_DECREF(flt);
    }
    flt = NULL;

    /* Set simulation time and pacing variable */
    engine_time = time_in;
    engine_pace = pace_in;

    /* Evaluate derivatives */
    rhs(engine_time, y, dy, 0);

    /* Set output values */
    for(i=0; i<N_STATE; i++) {
        flt = PyFloat_FromDouble(NV_Ith_S(dy, i));
        if (flt == NULL) {
            PyErr_SetString(PyExc_Exception, "Unable to create float.");
            goto error;
        }
        PySequence_SetItem(deriv, i, flt);
        Py_DECREF(flt);
    }
    flt = NULL;

    /* Finished succesfully, free memory and return */
    success = 1;
error:
    /* Free CVODE space */
    N_VDestroy_Serial(y);
    N_VDestroy_Serial(dy);
    #if SUNDIALS_VERSION_MAJOR >= 6
    SUNContext_Free(&sundials_context);
    #endif

    /* Return */
    if (success) {
        Py_RETURN_NONE;
    } else {
        return 0;
    }
}

/*
 * Alters the value of a (literal) constant
 */
static PyObject*
sim_set_constant(PyObject *self, PyObject *args)
{
    double value;
    char* name;
    char errstr[200];

    /* Check input arguments */
    if (!PyArg_ParseTuple(args, "sd", &name, &value)) {
        PyErr_SetString(PyExc_Exception, "Expected input arguments: name (str), value (Float).");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }

<?
for var in model.variables(const=True, deep=True):
    if var.is_literal():
        print(tab + 'if(strcmp("' + var.qname() + '", name) == 0) {')
        print(tab + tab + v(var) + ' = value;')
        print(tab + tab + 'Py_RETURN_NONE;')
        print(tab + '}')
?>
    sprintf(errstr, "Constant not found: <%s>", name);
    PyErr_SetString(PyExc_Exception, errstr);
    return 0;
}

/*
 * Returns the number of steps taken in the last simulation
 */
static PyObject*
sim_steps(PyObject *self, PyObject *args)
{
    return PyLong_FromLong(engine_steps);
}

/*
 * Returns the number of rhs evaluations performed during the last simulation
 */
static PyObject*
sim_evals(PyObject *self, PyObject *args)
{
    return PyLong_FromLong(engine_evaluations);
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
    {"sim_init", sim_init, METH_VARARGS, "Initialize the simulation."},
    {"sim_step", sim_step, METH_VARARGS, "Perform the next step in the simulation."},
    {"sim_clean", py_sim_clean, METH_VARARGS, "Clean up after an aborted simulation."},
    {"eval_derivatives", sim_eval_derivatives, METH_VARARGS, "Evaluate the state derivatives."},
    {"set_constant", sim_set_constant, METH_VARARGS, "Change a (literal) constant."},
    {"set_tolerance", sim_set_tolerance, METH_VARARGS, "Set the absolute and relative solver tolerance."},
    {"set_max_step_size", sim_set_max_step_size, METH_VARARGS, "Set the maximum solver step size (0 for none)."},
    {"set_min_step_size", sim_set_min_step_size, METH_VARARGS, "Set the minimum solver step size (0 for none)."},
    {"number_of_steps", sim_steps, METH_VARARGS, "Returns the number of steps taken in the last simulation."},
    {"number_of_evaluations", sim_evals, METH_VARARGS, "Returns the number of rhs evaluations performed during the last simulation."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Generated CVODESim module",/* m_doc */
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
