<?
# cvodessim.c
#
# A pype template for a single cell CVODES-based simulation that can calculate
# sensitivities of variables ``v`` w.r.t. parameters or initial conditions and
# perform root-finding.
#
# Note: For compatibility with older Python versions on windows, we need to
# stick to a slightly outdated C standard (i.e. C90). For a list of which
# microsoft compilers accept which C standard (and how that matches with python
# versions), see https://bugs.python.org/issue42380
#
# Required variables
# -----------------------------------------------------------------------------
# module_name     A module name
# model_code      Code for a CModel
# -----------------------------------------------------------------------------
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit
?>
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>

#include <cvodes/cvodes.h>
#include <nvector/nvector_serial.h>
#include <sundials/sundials_types.h>
#include <sundials/sundials_config.h>
#ifndef SUNDIALS_VERSION_MAJOR
    #define SUNDIALS_VERSION_MAJOR 2
#endif
#if SUNDIALS_VERSION_MAJOR >= 3
    #include <sunmatrix/sunmatrix_dense.h>
    #include <sunlinsol/sunlinsol_dense.h>
    #include <cvodes/cvodes_direct.h>
#else
    #include <cvodes/cvodes_dense.h>
#endif

<?
if myokit.DEBUG_SM:
    print('// Show debug output')
    print('#ifndef MYOKIT_DEBUG_MESSAGES')
    print('#define MYOKIT_DEBUG_MESSAGES')
    print('#endif')

# Note: When adding profiling messages, write them in past tense so that we can
# show time elapsed for an operation **that has just completed**.
if myokit.DEBUG_SP:
    print('// Show profiling messages')
    print('#ifndef MYOKIT_DEBUG_PROFILING')
    print('#define MYOKIT_DEBUG_PROFILING')
    print('#endif')
?>

#include "pacing.h"

<?= model_code ?>

/*
 * Define type for "user data" that will hold parameter values if doing
 * sensitivity analysis.
 */
typedef struct {
    realtype *p;
} *UserData;

/*
 * Check sundials flags, set python error.
 *  flagvalue : The value to check
 *  funcname : The name of the function that returned the flag
 *  opt : Mode selector
 *         0 : Error if the flag is null
 *         1 : Error if the flag is < 0
 *         2 : Errir
 */
int
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
 * Error and warning message handler for CVODES.
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
        sprintf(errstr, "CVODES: %s", msg);
        PyErr_WarnEx(PyExc_RuntimeWarning, errstr, 1);
    }
}

/*
 * Initialisation status.
 * Proper sequence is init(), repeated step() calls till finished, then clean.
 */
int initialised = 0; /* Has the simulation been initialised */

/*
 * Model
 */
Model model;        /* A model object */

/*
 * Pacing
 */
ESys epacing;           /* Event-based pacing system */
PyObject* eprotocol;    /* An event-based pacing protocol */
FSys fpacing;           /* Fixed-form pacing system */
PyObject* fprotocol;    /* A fixed-form pacing protocol */
double pace = 0;        /* Pacing value */

/*
 * CVODE Memory
 */
void *cvode_mem;     /* The memory used by the solver */
#if SUNDIALS_VERSION_MAJOR >= 3
SUNMatrix sundense_matrix;          /* Dense matrix for linear solves */
SUNLinearSolver sundense_solver;    /* Linear solver object */
#endif
#if SUNDIALS_VERSION_MAJOR >= 6
SUNContext sundials_context; /* A sundials context to run in (for profiling etc.) */
#endif

UserData udata;      /* UserData struct, used to pass in parameters */
realtype* pbar;      /* Vector of independents in user data */

/*
 * Solver settings
 */
double abs_tol = 1e-6;  /* The absolute tolerance */
double rel_tol = 1e-4;  /* The relative tolerance */
double dt_max = 0;      /* The maximum step size (0.0 for none) */
double dt_min = 0;      /* The minimum step size (0.0 for none) */

/*
 * Solver stats
 */
double realtime = 0;        /* Time since start */
long evaluations = 0;       /* Number of evaluations since sim init */
long steps = 0;             /* Number of steps since sim init */

/*
 * Checking for repeated size-zero steps
 */
int zero_step_count;
const int max_zero_step_count = 500;

/*
 * State vectors
 */
N_Vector y;     /* The current position y */
N_Vector* sy;   /* Current state sensitivities, 1 vector per independent */

/* Intermediary positions for logging: these will only be created if using
   interpolation to log. Otherwise they will simply point to y and sy */
N_Vector z;
N_Vector* sz;

/* Previous position, used for error output, always created */
N_Vector ylast;

/*
 * Customisable constants, passed in from Python
 */
PyObject* literals;     /* A list of literal constant values */
PyObject* parameters;   /* A list of parameter values */

/*
 * State and bound variable communication
 */
PyObject* state_py;     /* List: The state passed from and to Python */
PyObject* s_state_py;   /* List: The state sensitivities passed from and to Python */
PyObject* bound_py;     /* List: The bound variables, passed to Python */

/*
 * Timing
 */
double t;       /* Current simulation time */
double tlast;   /* Previous simulation time, for error and progress tracking */
double tnext;   /* Next simulation halting point */
double tmin;    /* The initial simulation time */
double tmax;    /* The final simulation time */

/*
 * Logging
 */
int dynamic_logging;    /* True if logging every point. */
PyObject* log_dict;     /* The log dict (DataLog) */
PyObject* sens_list;    /* Sensitivity logging list */

/* Periodic and point-list logging */
double tlog;            /* Next time to log */
double log_interval;    /* The periodic logging interval */
Py_ssize_t ilog;        /* Index of next point in the point list */
PyObject* log_times;    /* The point list (or None if disabled) */

/*
 * Root finding
 */
int rf_indice;          /* Indice of state variable to use in root finding (ignored if not enabled) */
double rf_threshold;    /* Threshold to use for root finding (ignored if not enabled) */
PyObject* rf_list;      /* List to store found roots in (or None if not enabled) */
int* rf_direction;      /* Direction of root crossings: 1 for up, -1 for down, 0 for no crossing. */

/*
 * Logging realtime and profiling
 */
PyObject* benchmarker;      /* myokit.tools.Benchmarker object */
PyObject* benchmarker_time_str;
int log_realtime;           /* 1 iff we're logging real simulation time */
double realtime_start;      /* time when sim run started */

/*
 * Returns the current time as given by the benchmarker.
 */
double
benchmarker_realtime()
{
    double val;
    PyObject* ret = PyObject_CallMethodObjArgs(benchmarker, benchmarker_time_str, NULL);
    if (!PyFloat_Check(ret)) {
        Py_XDECREF(ret);
        return -1.0;
    }
    val = PyFloat_AsDouble(ret);
    Py_DECREF(ret);
    return val - realtime_start;
}

#ifdef MYOKIT_DEBUG_PROFILING
PyObject* benchmarker_print_str;

/*
 * Prints a message to screen, preceded by the time in ms as given by the benchmarker.
 */
void
benchmarker_print(char* message)
{
    PyObject* pymsg = PyUnicode_FromString(message);
    PyObject_CallMethodObjArgs(benchmarker, benchmarker_print_str, pymsg, NULL);
    Py_DECREF(pymsg);
}
#endif

/*
 * Right-hand-side function of the model ODE
 *
 *  realtype t      Current time
 *  N_Vector y      The current state values
 *  N_Vector ydot   Space to store the calculated derivatives in
 *  void* user_data Extra data (contains the sensitivity parameter values)
 *
 */
int
rhs(realtype t, N_Vector y, N_Vector ydot, void *user_data)
{
    FSys_Flag flag_fpacing;
    UserData fdata;
    int i;

    /* Fixed-form pacing? Then look-up correct value of pacing variable! */
    if (fpacing != NULL) {
        pace = FSys_GetLevel(fpacing, t, &flag_fpacing);
        if (flag_fpacing != FSys_OK) { /* This should never happen */
            FSys_SetPyErr(flag_fpacing);
            return -1;  /* Negative value signals irrecoverable error to CVODE */
        }
    }

    /* Update model state */

    /* Set time, pace, evaluations and realtime */
    evaluations++;
    Model_SetBoundVariables(model, t, pace, realtime, evaluations);

    /* Set sensitivity parameters */
    if (model->has_sensitivities) {
        fdata = (UserData) user_data;
        Model_SetParametersFromIndependents(model, fdata->p);
    }

    /* Set states */
    Model_SetStates(model, N_VGetArrayPointer(y));

    /* Calculate state derivatives */
    Model_EvaluateDerivatives(model);

    /* Fill ydot and return */
    if (ydot != NULL) {
        for (i=0; i<model->n_states; i++) {
            NV_Ith_S(ydot, i) = model->derivatives[i];
        }
    }

    return 0;
}

/*
 * Utility function to set the state sensitivities and evaluate the sensitivity
 * outputs.
 *
 * Assumes the RHS has been evaluated.
 */
void
shs(N_Vector* sy)
{
    int i, j;

    /* Unpack state sensitivities */
    for (i=0; i<model->ns_independents; i++) {
        for (j=0; j<model->n_states; j++) {
            model->s_states[i * model->n_states + j] = NV_Ith_S(sy[i], j);
        }
    }

    /* Calculate intermediary variable sensitivities */
    Model_EvaluateSensitivityOutputs(model);
}

/*
 * Root finding function. Can contain several functions for which a root is to
 * be found, but we only use one.
 */
int
rf_function(realtype t, N_Vector y, realtype *gout, void *user_data)
{
    gout[0] = NV_Ith_S(y, rf_indice) - rf_threshold;
    return 0;
}

/*
 * Cleans up after a simulation
 */
PyObject*
sim_clean()
{
    if (initialised) {
        #ifdef MYOKIT_DEBUG_PROFILING
        benchmarker_print("CP Entered sim_clean.");
        #elif defined MYOKIT_DEBUG_MESSAGES
        printf("CM Cleaning up.\n");
        #endif

        /* CVode arrays */
        if (y != NULL) { N_VDestroy_Serial(y); y = NULL; }
        if (sy != NULL) { N_VDestroyVectorArray(sy, model->ns_independents); sy = NULL; }
        if (model != NULL && model->is_ode && !dynamic_logging) {
            if (z != NULL) { N_VDestroy_Serial(z); z = NULL; }
            if (sz != NULL) { N_VDestroyVectorArray(sz, model->ns_independents); sz = NULL; }
        }

        /* Root finding results */
        free(rf_direction); rf_direction = NULL;

        /* Sundials objects */
        CVodeFree(&cvode_mem); cvode_mem = NULL;
        #if SUNDIALS_VERSION_MAJOR >= 3
        SUNLinSolFree(sundense_solver); sundense_solver = NULL;
        SUNMatDestroy(sundense_matrix); sundense_matrix = NULL;
        #endif
        #if SUNDIALS_VERSION_MAJOR >= 6
        SUNContext_Free(&sundials_context); sundials_context = NULL;
        #endif

        /* User data and parameter scale array*/
        free(pbar);
        if (udata != NULL) {
            free(udata->p);
            free(udata); udata = NULL;
        }

        /* Pacing systems */
        ESys_Destroy(epacing); epacing = NULL;
        FSys_Destroy(fpacing); fpacing = NULL;

        /* CModel */
        Model_Destroy(model); model = NULL;

        /* Benchmarking and profiling */
        #ifdef MYOKIT_DEBUG_PROFILING
        benchmarker_print("CP Completed sim_clean.");
        Py_XDECREF(benchmarker_print_str); benchmarker_print_str = NULL;
        #endif
        Py_XDECREF(benchmarker_time_str); benchmarker_time_str = NULL;

        /* Deinitialisation complete */
        initialised = 0;
    }

    /* Return 0, allowing the construct
        PyErr_SetString(PyExc_Exception, "Oh noes!");
        return sim_clean()
       to terminate a python function. */
    return 0;
}

/*
 * Version of sim_clean that sets a python exception.
 */
PyObject*
sim_cleanx(PyObject* ex_type, const char* msg, ...)
{
    va_list argptr;
    char errstr[1024];

    va_start(argptr, msg);
    vsprintf(errstr, msg, argptr);
    va_end(argptr);

    PyErr_SetString(ex_type, errstr);
    return sim_clean();
}

/*
 * Version of sim_clean to be called from Python
 */
PyObject*
py_sim_clean(PyObject *self, PyObject *args)
{
    sim_clean();
    Py_RETURN_NONE;
}

/*
 * Initialise a run.
 * Called by the Python code's run(), followed by several calls to sim_step().
 */
PyObject*
sim_init(PyObject *self, PyObject *args)
{
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("CM Entering sim_init.\n");
    #endif

    /* Error checking flags */
    int flag_cvode;
    Model_Flag flag_model;
    ESys_Flag flag_epacing;
    FSys_Flag flag_fpacing;

    /* General purpose ints for iterating */
    int i, j;

    /* Log the first point? Only happens if not continuing from a log */
    int log_first_point;

    /* Python objects, and a python list index variable */
    Py_ssize_t pos;
    PyObject *val;
    PyObject *ret;

    /* Check if already initialised */
    if (initialised) {
        PyErr_SetString(PyExc_Exception, "Simulation already initialised.");
        return 0;
    }

    /* Check for double precision */
    #ifndef SUNDIALS_DOUBLE_PRECISION
    PyErr_SetString(PyExc_Exception, "Sundials must be compiled with double precision.");
    return 0;
    #endif

    /* Set all global pointers to null */
    /* Model and pacing */
    model = NULL;
    epacing = NULL;
    fpacing = NULL;
    /* User data and parameter scaling */
    udata = NULL;
    pbar = NULL;
    /* State vectors */
    y = NULL;
    sy = NULL;
    z = NULL;
    sz = NULL;
    ylast = NULL;
    /* Logging */
    log_times = NULL;
    /* Benchmarking and profiling */
    benchmarker_time_str = NULL;
    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print_str = NULL;
    #endif

    /* CVode objects */
    cvode_mem = NULL;
    #if SUNDIALS_VERSION_MAJOR >= 3
    sundense_matrix = NULL;
    sundense_solver = NULL;
    #endif
    #if SUNDIALS_VERSION_MAJOR >= 6
    sundials_context = NULL;
    #endif

    /* Check input arguments     0123456789012345678 */
    if (!PyArg_ParseTuple(args, "ddOOOOOOOOdOOidOOi",
            &tmin,              /*  0. Float: initial time */
            &tmax,              /*  1. Float: final time */
            &state_py,          /*  2. List: initial and final state */
            &s_state_py,        /*  3. List of lists: state sensitivities */
            &bound_py,          /*  4. List: store final bound variables here */
            &literals,          /*  5. List: literal constant values */
            &parameters,        /*  6. List: parameter values */
            &eprotocol,         /*  7. Event-based protocol */
            &fprotocol,         /*  8. Fixed-form protocol (tuple) */
            &log_dict,          /*  9. DataLog */
            &log_interval,      /* 10. Float: log interval, or 0 */
            &log_times,         /* 11. List of logging times, or None */
            &sens_list,         /* 12. List to store sensitivities in */
            &rf_indice,         /* 13. Int: root-finding state variable */
            &rf_threshold,      /* 14. Float: root-finding threshold */
            &rf_list,           /* 15. List to store roots in or None */
            &benchmarker,       /* 16. myokit.tools.Benchmarker object */
            &log_realtime       /* 17. Int: 1 if logging real time */
    )) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        return 0;
    }

    /* Now officialy initialised */
    initialised = 1;

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

    /* Set simulation starting time */
    t = tmin;

    /* Reset solver stats */
    steps = 0;
    zero_step_count = 0;
    evaluations = 0;
    realtime = 0;
    if (log_realtime) {
        realtime_start = 0; /* Updated after init, in first call to run */
        benchmarker_time_str = PyUnicode_FromString("time");
    }

    /* Set up profiling */
    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print_str = PyUnicode_FromString("print");
    benchmarker_print("CP Initialisation started (entered sim_init()).");
    #endif

    /*
     * Create model
     */
    model = Model_Create(&flag_model);
    if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }
    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Created C model struct.");
    #endif

    /*
     * Create sundials context
     */
    #if SUNDIALS_VERSION_MAJOR >= 6
    flag_cvode = SUNContext_Create(NULL, &sundials_context);
    if (check_cvode_flag(&flag_cvode, "SUNContext_Create", 1)) {
        return sim_cleanx(PyExc_Exception, "Failed to create Sundials context.");
    }
    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Created sundials context.");
    #endif
    #endif

    /*
     * Create state vectors
     */

    /* Create state vector */
    #if SUNDIALS_VERSION_MAJOR >= 6
    y = N_VNew_Serial(model->n_states, sundials_context);
    #else
    y = N_VNew_Serial(model->n_states);
    #endif
    if (check_cvode_flag((void*)y, "N_VNew_Serial", 0)) {
        return sim_cleanx(PyExc_Exception, "Failed to create state vector.");
    }

    /* Create state vector copy for error handling */
    #if SUNDIALS_VERSION_MAJOR >= 6
    ylast = N_VNew_Serial(model->n_states, sundials_context);
    #else
    ylast = N_VNew_Serial(model->n_states);
    #endif
    if (check_cvode_flag((void*)ylast, "N_VNew_Serial", 0)) {
        return sim_cleanx(PyExc_Exception, "Failed to create last-state vector.");
    }

    /* Create sensitivity vector array */
    if (model->has_sensitivities) {
        sy = N_VCloneVectorArray(model->ns_independents, y);
        if (check_cvode_flag((void*)sy, "N_VCloneVectorArray", 0)) {
            return sim_cleanx(PyExc_Exception, "Failed to allocate space to store sensitivities.");
        }
    }

    /*
     * Create state vectors for logging
     */

    /* Determine if dynamic logging is being used (or if it's periodic/point-list logging) */
    dynamic_logging = (log_interval <= 0 && log_times == Py_None);

    /* When using interpolation logging (periodic or point-list), we need a
       state and s_state vector to pass to CVODE's interpolation function.
       When using dynamic logging (or running in CVODE-free mode) we can simply
       log the current state, so z and sz can point to y and sy. */
    if (dynamic_logging || !model->is_ode) {
        z = y;
        sz = sy;
    } else {
        #if SUNDIALS_VERSION_MAJOR >= 6
        z = N_VNew_Serial(model->n_states, sundials_context);
        #else
        z = N_VNew_Serial(model->n_states);
        #endif
        if (check_cvode_flag((void*)z, "N_VNew_Serial", 0)) {
            return sim_cleanx(PyExc_Exception, "Failed to create state vector for logging.");
        }
        if (model->has_sensitivities) {
            sz = N_VCloneVectorArray(model->ns_independents, y);
            if (check_cvode_flag((void*)sz, "N_VCloneVectorArray", 0)) {
                return sim_cleanx(PyExc_Exception, "Failed to create state sensitivity vector array for logging.");
            }
        }
    }

    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Created sundials state vectors.");
    #endif

    /*
     * Set initial state in model and vectors
     */

    /* Set initial state values */
    if (!PyList_Check(state_py)) {
        return sim_cleanx(PyExc_TypeError, "'state_py' must be a list.");
    }
    for (i=0; i<model->n_states; i++) {
        val = PyList_GetItem(state_py, i);    /* Don't decref! */
        if (!PyFloat_Check(val)) {
            return sim_cleanx(PyExc_ValueError, "Item %d in state vector is not a float.", i);
        }
        model->states[i] = PyFloat_AsDouble(val);
        NV_Ith_S(y, i) = model->states[i];
    }

    /* Set initial sensitivity state values */
    if (model->has_sensitivities) {
        if (!PyList_Check(s_state_py)) {
            return sim_cleanx(PyExc_TypeError, "'s_state_py' must be a list.");
        }
        for (i=0; i<model->ns_independents; i++) {
            val = PyList_GetItem(s_state_py, i); /* Don't decref */
            if (!PyList_Check(val)) {
                return sim_cleanx(PyExc_ValueError, "Item %d in state sensitivity matrix is not a list.", i);
            }
            for (j=0; j<model->n_states; j++) {
                ret = PyList_GetItem(val, j);    /* Don't decref! */
                if (!PyFloat_Check(ret)) {
                    return sim_cleanx(PyExc_ValueError, "Item %d, %d in state sensitivity matrix is not a float.", i, j);
                }
                NV_Ith_S(sy[i], j) = PyFloat_AsDouble(ret);
                model->s_states[i * model->n_states + j] = NV_Ith_S(sy[i], j);
            }
        }
    }

    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Set initial state.");
    #endif

    /*
     * Set values of constants (literals and parameters)
     */
    if (!PyList_Check(literals)) {
        return sim_cleanx(PyExc_TypeError, "'literals' must be a list.");
    }
    for (i=0; i<model->n_literals; i++) {
        val = PyList_GetItem(literals, i);    /* Don't decref */
        if (!PyFloat_Check(val)) {
            return sim_cleanx(PyExc_ValueError, "Item %d in literal vector is not a float.", i);
        }
        model->literals[i] = PyFloat_AsDouble(val);
    }

    /* Evaluate calculated constants */
    Model_EvaluateLiteralDerivedVariables(model);

    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Set model constants and calculated derived constants.");
    #endif

    /* Set model parameters */
    if (model->has_sensitivities) {
        if (!PyList_Check(parameters)) {
            return sim_cleanx(PyExc_TypeError, "'parameters' must be a list.");
        }
        for (i=0; i<model->n_parameters; i++) {
            val = PyList_GetItem(parameters, i);    /* Don't decref */
            if (!PyFloat_Check(val)) {
                return sim_cleanx(PyExc_ValueError, "Item %d in parameter vector is not a float.", i);
            }
            model->parameters[i] = PyFloat_AsDouble(val);
        }

        /* Evaluate calculated constants */
        Model_EvaluateParameterDerivedVariables(model);

        #ifdef MYOKIT_DEBUG_PROFILING
        benchmarker_print("CP Setting model sensitivity parameters and calculated derived quantities.");
        #endif
    }

    /* Create UserData with sensitivity vector */
    if (model->has_sensitivities) {
        udata = (UserData)malloc(sizeof *udata);
        if (udata == 0) {
            return sim_cleanx(PyExc_Exception, "Unable to create user data object to store parameter values.");
        }
        udata->p = (realtype*)malloc(sizeof(realtype) * model->ns_independents);
        if (udata->p == 0) {
            return sim_cleanx(PyExc_Exception, "Unable to allocate space to store parameter values.");
        }

        /*
         * Add in values for parameters and initial values
         * Note that the initial values in the user data don't have any effect,
         * so their value isn't important (outside of the scaling set below).
         */
        for (i=0; i<model->ns_independents; i++) {
            udata->p[i] = *model->s_independents[i];
        }

        /* Create parameter scaling vector, for error control */
        /* TODO: Get this from the Python code ? */
        pbar = (realtype*)malloc(sizeof(realtype) * model->ns_independents);
        if (pbar == NULL) {
            return sim_cleanx(PyExc_Exception, "Unable to allocate space to store parameter scales.");
        }
        for (i=0; i<model->ns_independents; i++) {
            pbar[i] = (udata->p[i] == 0.0 ? 1.0 : fabs(udata->p[i]));
        }

        #ifdef MYOKIT_DEBUG_PROFILING
        benchmarker_print("CP Created UserData for sensitivities.");
        #endif
    }

    /*
     * Set up pacing system
     */

    /* Set up event-based pacing */
    if (eprotocol != Py_None) {
        epacing = ESys_Create(&flag_epacing);
        if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
        flag_epacing = ESys_Populate(epacing, eprotocol);
        if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
        flag_epacing = ESys_AdvanceTime(epacing, tmin);
        if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
        tnext = ESys_GetNextTime(epacing, &flag_epacing);
        pace = ESys_GetLevel(epacing, &flag_epacing);
        tnext = (tnext < tmax) ? tnext : tmax;

        #ifdef MYOKIT_DEBUG_PROFILING
        benchmarker_print("CP Created event-based pacing system.");
        #endif
    } else {
        tnext = tmax;
    }

    /* Set up fixed-form pacing */
    if (eprotocol == Py_None && fprotocol != Py_None) {
        /* Check 'protocol' is tuple (times, values) */
        if (!PyTuple_Check(fprotocol)) {
            return sim_cleanx(PyExc_TypeError, "Fixed-form pacing protocol should be tuple or None.");
        }
        if (PyTuple_Size(fprotocol) != 2) {
            return sim_cleanx(PyExc_ValueError, "Fixed-form pacing protocol tuple should have size 2.");
        }
        /* Create fixed-form pacing object and populate */
        fpacing = FSys_Create(&flag_fpacing);
        if (flag_fpacing != FSys_OK) { FSys_SetPyErr(flag_fpacing); return sim_clean(); }
        flag_fpacing = FSys_Populate(fpacing,
            PyTuple_GetItem(fprotocol, 0),  /* Borrowed, no decref */
            PyTuple_GetItem(fprotocol, 1));
        if (flag_fpacing != FSys_OK) { FSys_SetPyErr(flag_fpacing); return sim_clean(); }

        #ifdef MYOKIT_DEBUG_PROFILING
        benchmarker_print("CP Created fixed-form pacing system.");
        #endif
    }

    /*
     * Create solver
     */
    if (model->is_ode) {

        /* Create, using backwards differentiation and newton iterations */
        #if SUNDIALS_VERSION_MAJOR >= 6
        cvode_mem = CVodeCreate(CV_BDF, sundials_context);
        #elif SUNDIALS_VERSION_MAJOR >= 4
        cvode_mem = CVodeCreate(CV_BDF);  /* Newton is still default */
        #else
        cvode_mem = CVodeCreate(CV_BDF, CV_NEWTON);
        #endif
        if (check_cvode_flag((void*)cvode_mem, "CVodeCreate", 0)) return sim_clean();

        /* Set error and warning-message handler */
        flag_cvode = CVodeSetErrHandlerFn(cvode_mem, ErrorHandler, NULL);
        if (check_cvode_flag(&flag_cvode, "CVodeInit", 1)) return sim_clean();

        /* Initialise solver memory, specify the rhs */
        flag_cvode = CVodeInit(cvode_mem, rhs, t, y);
        if (check_cvode_flag(&flag_cvode, "CVodeInit", 1)) return sim_clean();

        /* Set absolute and relative tolerances */
        flag_cvode = CVodeSStolerances(cvode_mem, RCONST(rel_tol), RCONST(abs_tol));
        if (check_cvode_flag(&flag_cvode, "CVodeSStolerances", 1)) return sim_clean();

        /* Set a maximum step size (or 0.0 for none) */
        flag_cvode = CVodeSetMaxStep(cvode_mem, dt_max < 0 ? 0.0 : dt_max);
        if (check_cvode_flag(&flag_cvode, "CVodeSetmaxStep", 1)) return sim_clean();

        /* Set a minimum step size (or 0.0 for none) */
        flag_cvode = CVodeSetMinStep(cvode_mem, dt_min < 0 ? 0.0 : dt_min);
        if (check_cvode_flag(&flag_cvode, "CVodeSetminStep", 1)) return sim_clean();

        #if SUNDIALS_VERSION_MAJOR >= 6
            /* Create dense matrix for use in linear solves */
            sundense_matrix = SUNDenseMatrix(model->n_states, model->n_states, sundials_context);
            if (check_cvode_flag((void *)sundense_matrix, "SUNDenseMatrix", 0)) return sim_clean();

            /* Create dense linear solver object with matrix */
            sundense_solver = SUNLinSol_Dense(y, sundense_matrix, sundials_context);
            if (check_cvode_flag((void *)sundense_solver, "SUNLinSol_Dense", 0)) return sim_clean();

            /* Attach the matrix and solver to cvode */
            flag_cvode = CVodeSetLinearSolver(cvode_mem, sundense_solver, sundense_matrix);
            if (check_cvode_flag(&flag_cvode, "CVodeSetLinearSolver", 1)) return sim_clean();
        #elif SUNDIALS_VERSION_MAJOR >= 4
            /* Create dense matrix for use in linear solves */
            sundense_matrix = SUNDenseMatrix(model->n_states, model->n_states);
            if (check_cvode_flag((void *)sundense_matrix, "SUNDenseMatrix", 0)) return sim_clean();

            /* Create dense linear solver object with matrix */
            sundense_solver = SUNLinSol_Dense(y, sundense_matrix);
            if (check_cvode_flag((void *)sundense_solver, "SUNLinSol_Dense", 0)) return sim_clean();

            /* Attach the matrix and solver to cvode */
            flag_cvode = CVodeSetLinearSolver(cvode_mem, sundense_solver, sundense_matrix);
            if (check_cvode_flag(&flag_cvode, "CVodeSetLinearSolver", 1)) return sim_clean();
        #elif SUNDIALS_VERSION_MAJOR >= 3
            /* Create dense matrix for use in linear solves */
            sundense_matrix = SUNDenseMatrix(model->n_states, model->n_states);
            if (check_cvode_flag((void *)sundense_matrix, "SUNDenseMatrix", 0)) return sim_clean();

            /* Create dense linear solver object with matrix */
            sundense_solver = SUNDenseLinearSolver(y, sundense_matrix);
            if (check_cvode_flag((void *)sundense_solver, "SUNDenseLinearSolver", 0)) return sim_clean();

            /* Attach the matrix and solver to cvode */
            flag_cvode = CVDlsSetLinearSolver(cvode_mem, sundense_solver, sundense_matrix);
            if (check_cvode_flag(&flag_cvode, "CVDlsSetLinearSolver", 1)) return sim_clean();
        #else
            /* Create dense matrix for use in linear solves */
            flag_cvode = CVDense(cvode_mem, model->n_states);
            if (check_cvode_flag(&flag_cvode, "CVDense", 1)) return sim_clean();
        #endif

        #ifdef MYOKIT_DEBUG_PROFILING
        benchmarker_print("CP CVODES solver initialised.");
        #endif

        /* Activate forward sensitivity computations */
        if (model->has_sensitivities) {
            /* TODO: NULL here is the place to insert a user function to calculate the
               RHS of the sensitivity ODE */
            /*flag_cvode = CVodeSensInit(cvode_mem, model->ns_independents, CV_SIMULTANEOUS, rhs1, sy);*/
            flag_cvode = CVodeSensInit(cvode_mem, model->ns_independents, CV_SIMULTANEOUS, NULL, sy);
            if (check_cvode_flag(&flag_cvode, "CVodeSensInit", 1)) return sim_clean();

            /* Attach user data */
            flag_cvode = CVodeSetUserData(cvode_mem, udata);
            if (check_cvode_flag(&flag_cvode, "CVodeSetUserData", 1)) return sim_clean();

            /* Set parameter scales used in tolerances */
            flag_cvode = CVodeSetSensParams(cvode_mem, udata->p, pbar, NULL);
            if (check_cvode_flag(&flag_cvode, "CVodeSetSensParams", 1)) return sim_clean();

            /* Set sensitivity tolerances calculating method (using pbar) */
            flag_cvode = CVodeSensEEtolerances(cvode_mem);
            if (check_cvode_flag(&flag_cvode, "CVodeSensEEtolerances", 1)) return sim_clean();

            #ifdef MYOKIT_DEBUG_PROFILING
            benchmarker_print("CP CVODES sensitivity methods initialised.");
            #endif
        }
    }

    /*
     * Root finding
     * Enabled if rf_list is a PyList
     */
    rf_direction = NULL;

    if (model->is_ode && PyList_Check(rf_list)) {
        /* Initialize root function with 1 component */
        flag_cvode = CVodeRootInit(cvode_mem, 1, rf_function);
        if (check_cvode_flag(&flag_cvode, "CVodeRootInit", 1)) return sim_clean();

        /* Direction of root crossings, one entry per root function, but we only use 1. */
        rf_direction = (int*)malloc(sizeof(int)*1);

        #ifdef MYOKIT_DEBUG_PROFILING
        benchmarker_print("CP CVODES root-finding initialised.");
        #endif
    }

    /*
     * Set up logging, and log first step if needed.
     */

    /* Check for loss-of-precision issue in periodic logging */
    if (log_interval > 0) {
        if (tmax + log_interval == tmax) {
            return sim_cleanx(PyExc_ValueError, "Log interval is too small compared to tmax; issue with numerical precision: float(tmax + log_interval) = float(tmax).");
        }
    }

    /* Set up logging */
    flag_model = Model_InitialiseLogging(model, log_dict);
    if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }
    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Logging initialised.");
    #endif

    /* Check logging list for sensitivities */
    if (model->has_sensitivities) {
        if (!PyList_Check(sens_list)) {
            return sim_cleanx(PyExc_TypeError, "'sens_list' must be a list.");
        }
    }

    /* Set logging points */
    if (log_interval > 0) {

        /* Periodic logging */
        ilog = 0;
        tlog = tmin;

    } else if (log_times != Py_None) {

        /* Point-list logging */

        /* Check the log_times sequence */
        if (!PySequence_Check(log_times)) {
            return sim_cleanx(PyExc_TypeError, "'log_times' must be a sequence type.");
        }

        /* Read next log point off the sequence */
        ilog = 0;
        tlog = t - 1;
        while(ilog < PySequence_Size(log_times) && tlog < t) {
            val = PySequence_GetItem(log_times, ilog); /* Borrowed */
            if (PyFloat_Check(val)) {
                tlog = PyFloat_AsDouble(val);
            } else if (PyNumber_Check(val)) {
                val = PyNumber_Float(val);
                if (val == NULL) {
                    return sim_cleanx(PyExc_ValueError, "Unable to cast entry in 'log_times' to float.");
                } else {
                    tlog = PyFloat_AsDouble(val);
                    Py_DECREF(val);
                }
            } else {
                return sim_cleanx(PyExc_ValueError, "Entries in 'log_times' must be floats.");
            }
            val = NULL;
            ilog++;
        }

        /* No points beyond time? Then don't log any future points. */
        if (tlog < t) {
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

        /* Check if the log is empty */
        log_first_point = 1;
        pos = 0;
        if (PyDict_Next(log_dict, &pos, &ret, &val)) {
            /* Items found in dict, randomly selected list now in "val" */
            /* Both key (ret) and value (val) are borrowed references, no need to decref */
            log_first_point = (PyObject_Size(val) <= 0);
        }

        /* If so, log the first point! */
        if (log_first_point) {
            rhs(t, y, NULL, udata);
            /* At this point, we have y(t), inter(t) and dy(t) */
            /* We've also loaded time(t) and pace(t) */

            flag_model = Model_Log(model);
            if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }

            if (model->has_sensitivities) {
                /* Calculate intermediary variable sensitivities, using
                   initial state sensitivities */
                shs(sy);

                /* Write sensitivity matrix to list */
                flag_model = Model_LogSensitivityMatrix(model, sens_list);
                if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }
            }
        }
    }

    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Logging times and strategy initialised.");
    #endif

    /*
     * Done!
     */
    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Initialisation complete (returning from sim_init).");
    #endif
    Py_RETURN_NONE;
}

/*
 * Takes the next steps in a simulation run
 */
PyObject*
sim_step(PyObject *self, PyObject *args)
{
    /* Error flags */
    Model_Flag flag_model;
    ESys_Flag flag_epacing;
    int flag_cvode;         /* CVode flag */
    int flag_root;          /* Root finding flag */
    int flag_reinit = 0;    /* Set if CVODE needs to be reset during a simulation step */

    /* Multi-purpose ints for iterating */
    int i, j;

    /* Number of integration steps taken in this call */
    int steps_taken = 0;

    /* Proposed next logging point */
    double proposed_tlog;

    /* Multi-purpose Python object */
    PyObject *val;

    /*
     * Set start time for logging of realtime.
     * This is handled here instead of in sim_init so it only includes time
     * taken performing steps, not time initialising memory etc.
     */
    if (log_realtime && realtime_start == 0) {
        realtime_start = benchmarker_realtime();
        if (realtime_start <= 0) {
            return sim_cleanx(PyExc_Exception, "Failed to set realtime_start.");
        }
    }

    /* Go! */
    while(1) {

        /* Back-up current y */
        for (i=0; i<model->n_states; i++) {
            NV_Ith_S(ylast, i) = NV_Ith_S(y, i);
        }

        /* Store engine time before step */
        tlast = t;

        if (model->is_ode) {

            /* Take a single ODE step */
            #ifdef MYOKIT_DEBUG_MESSAGES
            printf("\nCM Taking CVODE step from time %f to %f\n", t, tnext);
            #endif
            flag_cvode = CVode(cvode_mem, tnext, y, &t, CV_ONE_STEP);

            /* Check for errors */
            if (check_cvode_flag(&flag_cvode, "CVode", 1)) {
                /* Something went wrong... Set outputs and return */
                for (i=0; i<model->n_states; i++) {
                    PyList_SetItem(state_py, i, PyFloat_FromDouble(NV_Ith_S(ylast, i)));
                    /* PyList_SetItem steals a reference: no need to decref the double! */
                }
                PyList_SetItem(bound_py, 0, PyFloat_FromDouble(tlast));
                PyList_SetItem(bound_py, 1, PyFloat_FromDouble(pace));
                PyList_SetItem(bound_py, 2, PyFloat_FromDouble(realtime));
                PyList_SetItem(bound_py, 3, PyFloat_FromDouble(evaluations));
                return sim_clean();
            }

        } else {

            /* Just jump to next event */
            /* Note 1: To stay compatible with cvode-mode, don't jump to the
               next log time (if tlog < tnext) */
            /* Note 2: tnext can be infinity, so don't always jump there. */
            t = (tmax > tnext) ? tnext : tmax;
            flag_cvode = CV_SUCCESS;
        }

        /* Check if progress is being made */
        if (t == tlast) {
            if (++zero_step_count >= max_zero_step_count) {
                return sim_cleanx(PyExc_ArithmeticError, "Maximum number of zero-length steps taken at t=%f", t);
            }
        } else {
            /* Only count consecutive zero steps */
            zero_step_count = 0;
        }

        /* Update step count */
        steps++;

        /* If we got to this point without errors... */
        if ((flag_cvode == CV_SUCCESS) || (flag_cvode == CV_ROOT_RETURN)) {

            /*
             * Rewinding to tnext, and root finding
             */
            if (model->is_ode) {

                /* Next event time exceeded? */
                if (t > tnext) {
                    #ifdef MYOKIT_DEBUG_MESSAGES
                    printf("CM Event time exceeded, rewinding to %f\n", tnext);
                    #endif

                    /* Go back to time=tnext */
                    flag_cvode = CVodeGetDky(cvode_mem, tnext, 0, y);
                    if (check_cvode_flag(&flag_cvode, "CVodeGetDky", 1)) return sim_clean();
                    if (model->has_sensitivities) {
                        flag_cvode = CVodeGetSensDky(cvode_mem, tnext, 0, sy);
                        if (check_cvode_flag(&flag_cvode, "CVodeGetSensDky", 1)) return sim_clean();
                    }
                    t = tnext;
                    /* Require reinit (after logging) */
                    flag_reinit = 1;

                } else {

                    /* Get current sensitivity vector */
                    if (model->has_sensitivities) {
                        flag_cvode = CVodeGetSens(cvode_mem, &t, sy);
                        if (check_cvode_flag(&flag_cvode, "CVodeGetSens", 1)) return sim_clean();
                    }

                    /* Root found */
                    if (flag_cvode == CV_ROOT_RETURN) {

                        /* Get directions of root crossings (1 per root function) */
                        flag_root = CVodeGetRootInfo(cvode_mem, rf_direction);
                        if (check_cvode_flag(&flag_root, "CVodeGetRootInfo", 1)) return sim_clean();
                        /* We only have one root function, so we know that rf_direction[0] is non-zero at this point. */

                        /* Store tuple (time, direction) for the found root */
                        val = PyTuple_New(2);
                        PyTuple_SetItem(val, 0, PyFloat_FromDouble(t)); /* Steals reference, so this is ok */
                        PyTuple_SetItem(val, 1, PyLong_FromLong(rf_direction[0]));
                        if (PyList_Append(rf_list, val)) {    /* Doesn't steal, need to decref */
                            Py_DECREF(val);
                            return sim_cleanx(PyExc_Exception, "Call to append() failed on root finding list.");
                        }
                        Py_DECREF(val); val = NULL;
                    }
                }
            }

            /*
             * Logging interpolated points (periodic logging or point-list logging)
             */
            if (!dynamic_logging && t > tlog) {
                /* Note: For periodic logging, the condition should be `t > tlog`
                 * so that we log half-open intervals (i.e. the final point should
                 * never be included).
                 */

                /* Log points */
                while (t > tlog) {
                    #ifdef MYOKIT_DEBUG_MESSAGES
                    printf("CM Interpolation-logging for t=%f\n", t);
                    #endif

                    /* Benchmarking? Then set realtime */
                    if (log_realtime) {
                        realtime = benchmarker_realtime();
                        if (realtime < 0) return sim_cleanx(PyExc_Exception, "Failed to set realtime during interpolation logging.");
                    }

                    /* Get interpolated y(tlog) */
                    if (model->is_ode) {
                        flag_cvode = CVodeGetDky(cvode_mem, tlog, 0, z);
                        if (check_cvode_flag(&flag_cvode, "CVodeGetDky", 1)) return sim_clean();
                        if (model->has_sensitivities) {
                            flag_cvode = CVodeGetSensDky(cvode_mem, tlog, 0, sz);
                            if (check_cvode_flag(&flag_cvode, "CVodeGetSensDky", 1)) return sim_clean();
                        }
                    }
                    /* If cvode-free mode, the states can't change so we don't
                       need to do anything here */

                    /* Calculate intermediate variables & derivatives */
                    rhs(tlog, z, NULL, udata);

                    /* Write to log */
                    flag_model = Model_Log(model);
                    if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }

                    if (model->has_sensitivities) {
                        /* Calculate sensitivities to output */
                        shs(sz);

                        /* Write sensitivity matrix to list */
                        flag_model = Model_LogSensitivityMatrix(model, sens_list);
                        if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }
                    }

                    /* Get next logging point */
                    if (log_interval > 0) {
                        /* Periodic logging */
                        ilog++;
                        tlog = tmin + (double)ilog * log_interval;
                        if (ilog == 0) {
                            /* Unsigned int wraps around instead of overflowing, becomes zero again */
                            return sim_cleanx(PyExc_OverflowError, "Overflow in logged step count: Simulation too long!");
                        }
                    } else {
                        /* Point-list logging */
                        /* Read next log point off the sequence */
                        if (ilog < PySequence_Size(log_times)) {
                            val = PySequence_GetItem(log_times, ilog); /* Borrowed */
                            if (PyFloat_Check(val)) {
                                proposed_tlog = PyFloat_AsDouble(val);
                            } else if (PyNumber_Check(val)) {
                                val = PyNumber_Float(val);  /* New reference */
                                if (val == NULL) {
                                    return sim_cleanx(PyExc_ValueError, "Unable to cast entry in 'log_times' to float.");
                                } else {
                                    proposed_tlog = PyFloat_AsDouble(val);
                                    Py_DECREF(val);
                                }
                            } else {
                                return sim_cleanx(PyExc_ValueError, "Entries in 'log_times' must be floats.");
                            }
                            if (proposed_tlog < tlog) {
                                return sim_cleanx(PyExc_ValueError, "Values in log_times must be non-decreasing.");
                            }
                            tlog = proposed_tlog;
                            ilog++;
                            val = NULL;
                        } else {
                            tlog = tmax + 1;
                        }
                    }
                }
            }

            /*
             * Event-based pacing
             *
             * At this point we have logged everything _before_ time t, so it
             * is safe to update the pacing mechanism to time t.
             */
            if (epacing != NULL) {
                flag_epacing = ESys_AdvanceTime(epacing, t);
                if (flag_epacing != ESys_OK) {
                    ESys_SetPyErr(flag_epacing); return sim_clean();
                }
                tnext = ESys_GetNextTime(epacing, NULL);
                tnext = (tnext < tmax) ? tnext : tmax;
                pace = ESys_GetLevel(epacing, NULL);
            }

            /* Dynamic logging: Log every visited point */
            if (dynamic_logging) {

                /* Benchmarking? Then set realtime */
                if (log_realtime) {
                    realtime = benchmarker_realtime();
                    if (realtime < 0) return sim_cleanx(PyExc_Exception, "Failed to set realtime during dynamic logging.");
                }

                /* Ensure the logged values are correct for the new time t */
                if (model->logging_derivatives || model->logging_intermediary || model->has_sensitivities) {
                    /* If logging derivatives or intermediaries, calculate the
                       values for the current time. Similarly, if calculating
                       sensitivities this is needed. */
                    #ifdef MYOKIT_DEBUG_MESSAGES
                    printf("CM Calling RHS to log derivs/inter/sens at time %f\n", t);
                    #endif
                    rhs(t, y, NULL, udata);
                } else if (model->logging_bound) {
                    /* Logging bounds but not derivs or inters: No need to run
                       full rhs, just update bound variables */
                    Model_SetBoundVariables(model, t, pace, realtime, evaluations);
                }

                /* Write to log */
                flag_model = Model_Log(model);
                if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }

                if (model->has_sensitivities) {
                    /* Calculate sensitivities to output */
                    shs(sy);

                    /* Write sensitivity matrix to list */
                    flag_model = Model_LogSensitivityMatrix(model, sens_list);
                    if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }
                }
            }

            /*
             * Reinitialize CVODE if needed
             */
            if (model->is_ode && flag_reinit) {
                flag_cvode = CVodeReInit(cvode_mem, t, y);
                if (check_cvode_flag(&flag_cvode, "CVodeReInit", 1)) return sim_clean();
                if (model->has_sensitivities) {
                    flag_cvode = CVodeSensReInit(cvode_mem, CV_SIMULTANEOUS, sy);
                    if (check_cvode_flag(&flag_cvode, "CVodeSensReInit", 1)) return sim_clean();
                }
                flag_reinit = 0;
            }
        }

        /*
         * Check if we're finished
         */
        if (ESys_eq(t, tmax)) t = tmax;
        if (t >= tmax) break;

        /*
         * Perform any Python signal handling
         */
        if (PyErr_CheckSignals() != 0) {
            /* Exception (e.g. timeout or keyboard interrupt) occurred?
               Then cancel everything! */
            return sim_clean();
        }

        /*
         * Report back to python after every x steps
         */
        steps_taken++;
        if (steps_taken >= 100) {
            #ifdef MYOKIT_DEBUG_PROFILING
            benchmarker_print("CP Completed 100 steps, passing control back to Python.");
            #endif
            return PyFloat_FromDouble(t);
        }
    }
    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Completed remaining simulation steps.");
    #endif

    /*
     * Finished! Set final state
     */

    /* Set final state */
    for (i=0; i<model->n_states; i++) {
        PyList_SetItem(state_py, i, PyFloat_FromDouble(NV_Ith_S(y, i)));
        /* PyList_SetItem steals a reference: no need to decref the PyFloat */
    }

    /* Set final sensitivities */
    if (model->has_sensitivities) {
        for (i=0; i<model->ns_independents; i++) {
            val = PyList_GetItem(s_state_py, i); /* Borrowed */
            for (j=0; j<model->n_states; j++) {
                PyList_SetItem(val, j, PyFloat_FromDouble(NV_Ith_S(sy[i], j)));
            }
        }
    }

    /* Set bound variable values */
    PyList_SetItem(bound_py, 0, PyFloat_FromDouble(t));
    PyList_SetItem(bound_py, 1, PyFloat_FromDouble(pace));
    PyList_SetItem(bound_py, 2, PyFloat_FromDouble(realtime));
    PyList_SetItem(bound_py, 3, PyFloat_FromDouble(evaluations));

    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Set final state and bound variable values.");
    #endif

    sim_clean();    /* Ignore return value */
    return PyFloat_FromDouble(t);
}

/*
 * Evaluates the state derivatives at the given state
 */
PyObject*
sim_eval_derivatives(PyObject *self, PyObject *args)
{
    /* Declare variables here for C89 compatibility */
    int i;
    int success;
    double time_in;
    double pace_in;
    Model model;
    Model_Flag flag_model;
    PyObject *state;
    PyObject *deriv;
    PyObject *literals;
    PyObject *parameters;
    PyObject *val;
    char errstr[200];

    /* Start */
    success = 0;

    /* Check input arguments */
    /* Check input arguments     0123456789ABCDEF*/
    if (!PyArg_ParseTuple(args, "ddOOOO",
            &time_in,           /* 0. Float: time */
            &pace_in,           /* 1. Float: pace */
            &state,             /* 2. List: state */
            &deriv,             /* 3. List: store derivatives here */
            &literals,          /* 4. List: literal constant values */
            &parameters         /* 5. List: parameter values */
            )) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments in sim_eval_derivatives.");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }

    /* Check lists are sequences */
    if (!PyList_Check(state)) {
        PyErr_SetString(PyExc_Exception, "State argument must be a list.");
        return 0;
    }
    if (!PyList_Check(deriv)) {
        PyErr_SetString(PyExc_Exception, "Derivatives argument must be a list.");
        return 0;
    }
    if (!PyList_Check(literals)) {
        PyErr_SetString(PyExc_Exception, "Literals argument must be a list.");
        return 0;
    }
    if (!PyList_Check(parameters)) {
        PyErr_SetString(PyExc_Exception, "Parameters argument must be a list.");
        return 0;
    }

    /* From this point on, no more direct returning: use goto error */
    model = NULL;

    /* Temporary object: decref before re-using for another var :) */
    /* (Unless you get them using PyList_GetItem...) */
    val = NULL;

    /* Create model */
    model = Model_Create(&flag_model);
    if (flag_model != Model_OK) {
        Model_SetPyErr(flag_model);
        goto error;
    }

    /* Set bound variables */
    Model_SetBoundVariables(model, time_in, pace_in, 0, 0);

    /* Set literal values */
    for (i=0; i<model->n_literals; i++) {
        val = PyList_GetItem(literals, i);    /* Don't decref */
        if (!PyFloat_Check(val)) {
            sprintf(errstr, "Item %d in literal vector is not a float.", i);
            PyErr_SetString(PyExc_Exception, errstr);
            goto error;
        }
        model->literals[i] = PyFloat_AsDouble(val);
    }

    /* Evaluate literal-derived variables */
    Model_EvaluateLiteralDerivedVariables(model);

    /* Set parameter values */
    for (i=0; i<model->n_parameters; i++) {
        val = PyList_GetItem(parameters, i);    /* Don't decref */
        if (!PyFloat_Check(val)) {
            sprintf(errstr, "Item %d in parameter vector is not a float.", i);
            PyErr_SetString(PyExc_Exception, errstr);
            goto error;
        }
        model->parameters[i] = PyFloat_AsDouble(val);
    }

    /* Evaluate parameter-derived variables */
    Model_EvaluateParameterDerivedVariables(model);

    /* Set initial values */
    for (i=0; i < model->n_states; i++) {
        val = PyList_GetItem(state, i); /* Don't decref */
        if (!PyFloat_Check(val)) {
            sprintf(errstr, "Item %d in state vector is not a float.", i);
            PyErr_SetString(PyExc_Exception, errstr);
            goto error;
        }
        model->states[i] = PyFloat_AsDouble(val);
    }

    /* Evaluate derivatives */
    Model_EvaluateDerivatives(model);

    /* Set output values */
    for (i=0; i<model->n_states; i++) {
        val = PyFloat_FromDouble(model->derivatives[i]);
        if (val == NULL) {
            PyErr_SetString(PyExc_Exception, "Unable to create float.");
            goto error;
        }
        PyList_SetItem(deriv, i, val);
        /* PyList_SetItem steals a reference: no need to decref the double! */
    }

    /* Finished succesfully, free memory and return */
    success = 1;
error:
    /* Free model space */
    Model_Destroy(model);

    /* Return */
    if (success) {
        Py_RETURN_NONE;
    } else {
        return 0;
    }
}

/*
 * Change the tolerance settings
 */
PyObject*
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
PyObject*
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
PyObject*
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
 * Returns the number of steps taken in the last simulation
 */
PyObject*
sim_steps(PyObject *self, PyObject *args)
{
    return PyLong_FromLong(steps);
}

/*
 * Returns the number of rhs evaluations performed during the last simulation
 */
PyObject*
sim_evals(PyObject *self, PyObject *args)
{
    return PyLong_FromLong(evaluations);
}

/*
 * Methods in this module
 */
PyMethodDef SimMethods[] = {
    {"sim_init", sim_init, METH_VARARGS, "Initialize the simulation."},
    {"sim_step", sim_step, METH_VARARGS, "Perform the next step in the simulation."},
    {"sim_clean", py_sim_clean, METH_VARARGS, "Clean up after an aborted simulation."},
    {"eval_derivatives", sim_eval_derivatives, METH_VARARGS, "Evaluate the state derivatives."},
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

struct PyModuleDef moduledef = {
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
