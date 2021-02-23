<?
# cvodessim.c
#
# A pype template for a single cell CVODES-based simulation that can calculate
# sensitivities of variables ``v`` w.r.t. parameters or initial conditions and
# perform root-finding.
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
/*#include <stdio.h>*/
#include <string.h>  /* sprintf */
#include <cvodes/cvodes.h>
#include <nvector/nvector_serial.h>
#define MYOKIT_SUNDIALS_VERSION <?= myokit.SUNDIALS_VERSION ?>
#if MYOKIT_SUNDIALS_VERSION >= 30000
    #include <sunmatrix/sunmatrix_dense.h>
    #include <sunlinsol/sunlinsol_dense.h>
    #include <cvodes/cvodes_direct.h>
#else
    #include <cvodes/cvodes_dense.h>
#endif
#include <sundials/sundials_types.h>

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
 * Model
 */
Model model;                /* A model object */

/*
 * Solver state
 */
static realtype t = 0;        /* Current simulation time */
static realtype time_last = 0;      /* Previous simulation time */
static realtype realtime = 0;       /* Time since start */
static realtype realtime_start = 0; /* Timestamp of sim start */
static long evaluations = 0;
static long steps = 0;

static double tmin;            /* The initial simulation time */
static double tmax;            /* The final simulation time */
static double tnext;           /* Next simulation halting point */

/*
 * Init/Step/Clean
 */
static int initialised = 0;     /* Has the simulation been initialised */

/*
 * Pacing
 */
ESys epacing;               /* Event-based pacing system */
FSys fpacing;               /* Fixed-form pacing system */
static realtype pace = 0;

/*
 * Solver settings
 */
static double abs_tol = 1e-6; /* The absolute tolerance */
static double rel_tol = 1e-4; /* The relative tolerance */
static double dt_max = 0;     /* The maximum step size (0.0 for none) */
static double dt_min = 0;     /* The minimum step size (0.0 for none) */



/*
 * Simulation variables
 */





/* Checking for repeated zero size steps */
int zero_step_count;
int max_zero_step_count = 500;   /* Increased this from 50 */

/* CVode objects */
void *cvode_mem;     /* The memory used by the solver */
UserData udata;      /* UserData struct, used to pass in parameters */

#if MYOKIT_SUNDIALS_VERSION >= 30000
SUNMatrix sundense_matrix;          /* Dense matrix for linear solves */
SUNLinearSolver sundense_solver;    /* Linear solver object */
#endif

N_Vector y;          /* Stores the current position y */
N_Vector y_log;      /* Used to store y when logging */
N_Vector dy_log;     /* Used to store dy when logging */
N_Vector* sy;        /* Vector of state sensitivities, 1 per variable in `variables` */
N_Vector* sy_log;    /* Used to store y sensitivities when logging */
N_Vector* sdy_log;   /* Used to store dy sensitivities when logging */
N_Vector y_last;     /* Used to store previous value of y for error handling */


/* Parameter/initial-condition scales */
realtype* pbar;         /* One number per parameter/initial condition, giving something in the expected magnitude of the param/init */

/* Log timing */
Py_ssize_t ilog;        /* Periodic/point-list logging: Index of next point */
double tlog;            /* Periodic/point-list logging: Next point */
int dynamic_logging;    /* True if logging every point. */

/* Root finding */
int* rf_direction;      /* Direction of root crossings: 1 for up, -1 for down, 0 for no crossing. */


/*
 * Input arguments to sim_init
 */
PyObject* state_in;     /*  2. The initial state */
PyObject* state_out;    /*  3. The final state */
PyObject* s_state_in;   /*  4. The initial state sensitivities */
PyObject* s_state_out;  /*  5. The final state sensitivities */
PyObject* inputs;       /*  6. A vector used to return the bound variables final values */
PyObject* literals;     /*  7. A list of literal constant values */
PyObject* parameters;   /*  8. A list of parameter values */
PyObject* eprotocol;    /*  9. An event-based pacing protocol */
PyObject* fprotocol;    /* 10. A fixed-form pacing protocol */
PyObject* log_dict;     /* 11. The log dict (DataLog) */
double log_interval;    /* 12. Periodic logging: The log interval (0 to disable) */
PyObject* log_times;    /* 13. Point-list logging: List of points (None to disable) */
PyObject* sens_list;    /* 14. List to store sensitivities in (or None if not enabled) */
int rf_indice;          /* 15. Indice of state variable to use in root finding (ignored if not enabled) */
double rf_threshold;    /* 16. Threshold to use for root finding (ignored if not enabled) */
PyObject* rf_list;      /* 17. List to store found roots in (or None if not enabled) */
PyObject* benchtime;    /* 18. Callable time() function or None */



/*
 * Right-hand-side function of the model ODE
 *
 *  realtype t      Current time
 *  N_Vector y      The current state values
 *  N_Vector ydot   Space to store the calculated derivatives in
 *  void* user_data Extra data (contains the sensitivity parameter values)
 *
 */
static int
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
    Model_SetBoundVariables(
        model, t, pace, realtime, evaluations);

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
    for (i=0; i<model->n_states; i++) {
        NV_Ith_S(ydot, i) = model->derivatives[i];
    }

    return 0;
}








/*
 * TODO: REMOVE THIS UNTIL NECESSARY (CURRENTLY JUST DOES OUTPUTS)
 */
static int
calculate_sensitivity_outputs(
    realtype t, N_Vector y, N_Vector ydot, N_Vector* yS, void* user_data)
{
    int i, j;

    /* TODO: Memoisation */
    rhs(t, y, ydot, user_data);

    /* Unpack state sensitivities */
    for (i=0; i<model->ns_independents; i++) {
        for (j=0; j<model->n_states; j++) {
            model->s_states[i * model->n_states + j] = NV_Ith_S(yS[i], j);
        }
    }

    /* Calculate intermediary variable sensitivities */
    Model_EvaluateSensitivityOutputs(model);

    return 0;
}










/*
 * Root finding function. Can contain several functions for which a root is to
 * be found, but we only use one.
 */
static int
rf_function(realtype t, N_Vector y, realtype *gout, void *user_data)
{
    gout[0] = NV_Ith_S(y, rf_indice) - rf_threshold;
    return 0;
}

/*
 * Cleans up after a simulation
 */
static PyObject*
sim_clean()
{
    if (initialised) {

        /* Root finding */
        free(rf_direction); rf_direction = NULL;

        /* CVode arrays */
        if (y != NULL) { N_VDestroy_Serial(y); y = NULL; }
        if (dy_log != NULL) { N_VDestroy_Serial(dy_log); dy_log = NULL; }
        if (model != NULL && model->is_ode && !dynamic_logging) {
            if (y_log != NULL) { N_VDestroy_Serial(y_log); y_log = NULL; }
        }
        if (model != NULL && model->has_sensitivities) {
            if (sy != NULL) { N_VDestroyVectorArray(sy, model->ns_independents); sy = NULL; }
            if (sdy_log != NULL) { N_VDestroyVectorArray(sdy_log, model->ns_independents); sdy_log = NULL; }
            if (model->is_ode && !dynamic_logging) {
                if (sy_log != NULL) { N_VDestroyVectorArray(sy_log, model->ns_independents); sy_log = NULL; }
            }
        }

        /* CVode objects */
        CVodeFree(&cvode_mem); cvode_mem = NULL;
        #if MYOKIT_SUNDIALS_VERSION >= 30000
        SUNLinSolFree(sundense_solver); sundense_solver = NULL;
        SUNMatDestroy(sundense_matrix); sundense_matrix = NULL;
        #endif

        /* Free user data and parameter scale array*/
        free(pbar);
        if (udata != NULL) {
            free(udata->p);
            free(udata); udata = NULL;
        }

        /* Free pacing system space */
        ESys_Destroy(epacing); epacing = NULL;
        FSys_Destroy(fpacing); fpacing = NULL;

        /* Free model space */
        Model_Destroy(model); model = NULL;

        /* Deinitialisation complete */
        initialised = 0;
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
 * Initialise a run.
 * Called by the Python code's run(), followed by several calls to sim_step().
 */
static PyObject*
sim_init(PyObject *self, PyObject *args)
{
    int flag_cvode;
    Model_Flag flag_model;
    ESys_Flag flag_epacing;
    FSys_Flag flag_fpacing;

    int i, j;
    int log_first_point;

    Py_ssize_t pos;
    PyObject *val;
    PyObject* ret;

    #ifndef SUNDIALS_DOUBLE_PRECISION
    PyErr_SetString(PyExc_Exception, "Sundials must be compiled with double precision.");
    /* No memory freeing is needed here, return directly */
    return 0;
    #endif

    /* Check if already initialised */
    if (initialised) {
        PyErr_SetString(PyExc_Exception, "Simulation already initialised.");
        return 0;
    }

    /* Set all pointers used in sim_clean to null */
    /* Model and pacing */
    model = NULL;
    epacing = NULL;
    fpacing = NULL;
    /* User data and parameter scaling */
    udata = NULL;
    pbar = NULL;
    /* CVode arrays */
    y = NULL;
    y_log = NULL;
    dy_log = NULL;
    sy = NULL;
    sy_log = NULL;
    sdy_log = NULL;
    /* Logging */
    log_times = NULL;
    /* Root finding */
    rf_direction = NULL;
    /* CVode objects */
    cvode_mem = NULL;
    #if MYOKIT_SUNDIALS_VERSION >= 30000
    sundense_matrix = NULL;
    sundense_solver = NULL;
    #endif

    printf("Checking arguments\n");

    /* Check input arguments     0123456789ABCDEF*/
    if (!PyArg_ParseTuple(args, "ddOOOOOOOOOOdOOidOO",
            &tmin,              /*  0. Float: initial time */
            &tmax,              /*  1. Float: final time */
            &state_in,          /*  2. List: initial state */
            &state_out,         /*  3. List: store final state here */
            &s_state_in,        /*  4. List of lists: initial state sensitivities */
            &s_state_out,       /*  5. List of lists: store final state sensitivities here */
            &inputs,            /*  6. List: store final bound variables here */
            &literals,          /*  7. List: literal constant values */
            &parameters,        /*  8. List: parameter values */
            &eprotocol,         /*  9. Event-based protocol */
            &fprotocol,         /* 10. Fixed-form protocol (tuple) */
            &log_dict,          /* 11. DataLog */
            &log_interval,      /* 12. Float: log interval, or 0 */
            &log_times,         /* 13. List of logging times, or None */
            &sens_list,         /* 14. List to store sensitivities in */
            &rf_indice,         /* 15. Int: root-finding state variable */
            &rf_threshold,      /* 16. Float: root-finding threshold */
            &rf_list,           /* 17. List to store roots in or None */
            &benchtime          /* 18. Callable to obtain system time */
            )) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }

    printf("Checked\n");

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

    /* Create model */
    model = Model_Create(&flag_model);
    if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }

    /* Create state vector */
    y = N_VNew_Serial(model->n_states);
    if (check_cvode_flag((void*)y, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create state vector.");
        return sim_clean();
    }

    /* Create state vector copy for error handling */
    y_last = N_VNew_Serial(model->n_states);
    if (check_cvode_flag((void*)y_last, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create last-state vector.");
        return sim_clean();
    }

    printf("Creating sensitivity vector array\n");

    /* Create sensitivity vector array */
    if (model->has_sensitivities) {
        sy = N_VCloneVectorArray(model->ns_independents, y);
        if (check_cvode_flag((void*)sy, "N_VCloneVectorArray", 0)) {
            PyErr_SetString(PyExc_Exception, "Failed to allocate space to store sensitivities.");
            return sim_clean();
        }
    }

   /* Determine if dynamic logging is being used (or if it's periodic/point-list logging) */
    dynamic_logging = (log_interval <= 0 && log_times == Py_None);

    /* Create state vector for logging.
       If we log every visited point (dynamic logging), we can simply log
       values from y as used for the integration. But if we need to interpolate
       times in the past, we need a vector y (and sy if using sensitivities) to
       store the state at time of logging in. */
    if (dynamic_logging || !model->is_ode) {
        /* Dynamic logging or cvode-free mode: don't interpolate,
           so let y_log point to y */
        y_log = y;
        sy_log = sy;
    } else {
        /* Logging at fixed points:
           Keep y_log as a separate N_Vector for cvode interpolation */
        y_log = N_VNew_Serial(model->n_states);
        if (check_cvode_flag((void*)y_log, "N_VNew_Serial", 0)) {
            PyErr_SetString(PyExc_Exception, "Failed to create state vector for logging.");
            return sim_clean();
        }
        if (model->has_sensitivities) {
            sy_log = N_VCloneVectorArray(model->ns_independents, y);
            if (check_cvode_flag((void*)sy_log, "N_VCloneVectorArray", 0)) {
                PyErr_SetString(PyExc_Exception, "Failed to create state sensitivity vector array for logging.");
                return sim_clean();
            }
        }
    }

    /* Create derivative vector for logging.
       In both logging modes, the need arises to call rhs() manually, and so we
       need to create a dy_log vector to pass in (and an sdy_log vector array).
    */
    dy_log = N_VNew_Serial(model->n_states);
    if (check_cvode_flag((void*)dy_log, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create derivatives vector for logging.");
        return sim_clean();
    }
    if (model->has_sensitivities) {
        sdy_log = N_VCloneVectorArray(model->ns_independents, y);
        if (check_cvode_flag((void*)sdy_log, "N_VCloneVectorArray", 0)) {
            PyErr_SetString(PyExc_Exception, "Failed to create derivatives sensitivity vector array for logging.");
            return sim_clean();
        }
    }

    printf("Setting values of literals\n");

    /* Set values of literals */
    if (!PyList_Check(literals)) {
        PyErr_SetString(PyExc_Exception, "'literals' must be a list.");
        return sim_clean();
    }
    for (i=0; i<model->n_literals; i++) {
        val = PyList_GetItem(literals, i);    /* Don't decref */
        if (!PyFloat_Check(val)) {
            char errstr[200];
            sprintf(errstr, "Item %d in literal vector is not a float.", i);
            PyErr_SetString(PyExc_Exception, errstr);
            return sim_clean();
        }
        model->literals[i] = PyFloat_AsDouble(val);
    }

    /* Evaluate calculated constants */
    Model_EvaluateLiteralDerivedVariables(model);

    /* Set model parameters */
    if (model->has_sensitivities) {
        printf("Setting values of parameters\n");

        if (!PyList_Check(parameters)) {
            PyErr_SetString(PyExc_Exception, "'parameters' must be a list.");
            return sim_clean();
        }
        for (i=0; i<model->n_parameters; i++) {
            val = PyList_GetItem(parameters, i);    /* Don't decref */
            if (!PyFloat_Check(val)) {
                char errstr[200];
                sprintf(errstr, "Item %d in parameter vector is not a float.", i);
                PyErr_SetString(PyExc_Exception, errstr);
                return sim_clean();
            }
            model->parameters[i] = PyFloat_AsDouble(val);

            printf("Parameter %d is %f\n", i, model->parameters[i]);
        }

        /* Evaluate calculated constants */
        Model_EvaluateParameterDerivedVariables(model);
    }


    /* TODO: Set states in model instead? */


    printf("Setting initial state\n");

    /* Set initial state values */
    if (!PyList_Check(state_in)) {
        PyErr_SetString(PyExc_Exception, "'state_in' must be a list.");
        return sim_clean();
    }
    for (i=0; i<model->n_states; i++) {
        val = PyList_GetItem(state_in, i);    /* Don't decref! */
        if (!PyFloat_Check(val)) {
            char errstr[200];
            sprintf(errstr, "Item %d in state vector is not a float.", i);
            PyErr_SetString(PyExc_Exception, errstr);
            return sim_clean();
        }
        NV_Ith_S(y, i) = PyFloat_AsDouble(val);
        NV_Ith_S(y_last, i) = NV_Ith_S(y, i);
        /*if (!dynamic_logging) {
            NV_Ith_S(y_log, i) = NV_Ith_S(y, i);
        }*/
    }

    printf("Setting initial state sensitivities\n");

    /* Set initial sensitivity state values */
    if (model->has_sensitivities) {
        if (!PyList_Check(s_state_in)) {
            PyErr_SetString(PyExc_Exception, "'s_state_in' must be a list.");
            return sim_clean();
        }
        for (i=0; i<model->ns_independents; i++) {
            val = PyList_GetItem(s_state_in, i); /* Don't decref */
            if (!PyList_Check(val)) {
                char errstr[200];
                sprintf(errstr, "Item %d in state sensitivity matrix is not a list.", i);
                PyErr_SetString(PyExc_Exception, errstr);
                return sim_clean();
            }
            for (j=0; j<model->n_states; j++) {
                ret = PyList_GetItem(val, j);    /* Don't decref! */
                if (!PyFloat_Check(ret)) {
                    char errstr[200];
                    sprintf(errstr, "Item %d, %d in state sensitivity matrix is not a float.", i, j);
                    PyErr_SetString(PyExc_Exception, errstr);
                    return sim_clean();
                }
                NV_Ith_S(sy[i], j) = PyFloat_AsDouble(ret);
            }
        }
    }

    printf("Creating user data\n");

    /* Create UserData and vector to hold parameter and initial condition values for cvode */
    udata = (UserData)malloc(sizeof *udata);
    if (udata == 0) {
        PyErr_SetString(PyExc_Exception, "Unable to create user data object to store parameter values.");
        return sim_clean();
    }
    udata->p = (realtype*)malloc(sizeof(realtype) * model->ns_independents);
    if (udata->p == 0) {
        PyErr_SetString(PyExc_Exception, "Unable to allocate space to store parameter values.");
        return sim_clean();
    }

    /* Add in values for parameters and initial values */
    /* Note that the initial values in the user data don't have any effect, so
       their value isn't important (outside of the scaling set below). */
    for (i=0; i<model->ns_independents; i++) {
        udata->p[i] = *model->s_independents[i];
    }

    /* TODO: Get this from the Python code ? */
    /* Create parameter scaling vector, for error control */
    pbar = (realtype*)malloc(sizeof(realtype) * model->ns_independents);
    if (pbar == 0) {
        PyErr_SetString(PyExc_Exception, "Unable to allocate space to store parameter scales.");
        return sim_clean();
    }
    for (i=0; i<model->ns_independents; i++) {
        pbar[i] = (udata->p[i] == 0.0 ? 1.0 : fabs(udata->p[i]));
    }

    /* Direction of root crossings, one entry per root function, but we only use 1. */
    rf_direction = (int*)malloc(sizeof(int)*1);

    /* Reset evaluation count */
    evaluations = 0;

    /* Reset step count */
    steps = 0;

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
    flag_model = Model_InitialiseLogging(model, log_dict);
    if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }

    /* Check logging list for sensitivities */
    if (model->has_sensitivities) {
        printf("Sensitivities! YES!\n");
        if (!PyList_Check(sens_list)) {
            PyErr_SetString(PyExc_Exception, "'sens_list' must be a list.");
            return sim_clean();
        }
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
        pace = ESys_GetLevel(epacing, &flag_epacing);
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
    t = tmin;

    /* Check dt_max and dt_min */
    if (dt_max < 0) dt_max = 0.0;
    if (dt_min < 0) dt_min = 0.0;

    /* Create solver
     * Using Backward differentiation and Newton iteration */
    if (model->is_ode) {
        #if MYOKIT_SUNDIALS_VERSION >= 40000
            cvode_mem = CVodeCreate(CV_BDF);
        #else
            cvode_mem = CVodeCreate(CV_BDF, CV_NEWTON);
        #endif
        if (check_cvode_flag((void*)cvode_mem, "CVodeCreate", 0)) return sim_clean();

        /* Initialise solver memory, specify the rhs */
        flag_cvode = CVodeInit(cvode_mem, rhs, t, y);
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

        #if MYOKIT_SUNDIALS_VERSION >= 30000
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
        }

    } /* if model.CVODE */

    /* Benchmarking? Then set realtime to 0.0 */
    if (benchtime != Py_None) {
        /* Store initial time as 0 */
        realtime = 0.0;
        /* Tell sim_step to set realtime_start */
        realtime_start = -1;
    }

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
        tlog = t - 1;
        while(ilog < PyList_Size(log_times) && tlog < t) {
            val = PyList_GetItem(log_times, ilog); /* Borrowed */
            if (!PyFloat_Check(val)) {
                PyErr_SetString(PyExc_Exception, "Entries in 'log_times' must be floats.");
                return sim_clean();
            }
            tlog = PyFloat_AsDouble(val);
            ilog++;
            val = NULL;
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

        /*  Check if the log is empty */
        log_first_point = 1;
        pos = 0;
        if (PyDict_Next(log_dict, &pos, &ret, &val)) {
            /* Items found in dict, randomly selected list now in "val" */
            /* Both key (ret) and value (val) are borrowed references, no need to decref */
            log_first_point = (PyObject_Size(val) <= 0);
        }

        /* If so, log the first point! */
        if (log_first_point) {
            rhs(t, y, dy_log, udata);
            /* At this point, we have y(t), inter(t) and dy(t) */
            /* We've also loaded time(t) and pace(t) */

            flag_model = Model_Log(model);
            if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }

            if (model->has_sensitivities) {
                /* Calculate sensitivities to output */
                /* TODO: Ddon't call this function here, but call model methods directly */
                calculate_sensitivity_outputs(t, y, dy_log, sy, udata);

                /* Write sensitivity matrix to list */
                flag_model = Model_LogSensitivityMatrix(model, sens_list);
                if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }
            }
        }
    }

    /* Root finding enabled? (cvode-mode only) */
    if (model->is_ode && PyList_Check(rf_list)) {
        /* Initialize root function with 1 component */
        flag_cvode = CVodeRootInit(cvode_mem, 1, rf_function);
        if (check_cvode_flag(&flag_cvode, "CVodeRootInit", 1)) return sim_clean();
    }

    printf("Finished initialising\n");

    /* Done! */
    Py_RETURN_NONE;
}

/*
 * Takes the next steps in a simulation run
 */
static PyObject*
sim_step(PyObject *self, PyObject *args)
{
    Model_Flag flag_model;
    ESys_Flag flag_epacing;
    int i, j;
    int steps_taken = 0;    /* Number of integration steps taken in this call */
    int flag_cvode;         /* CVode flag */
    int flag_root;          /* Root finding flag */
    int flag_reinit = 0;    /* Set if CVODE needs to be reset during a simulation step */
    PyObject *val;

    /*
     * Benchmarking? Then make sure start time is set.
     * This is handled here instead of in sim_init so it only includes time
     * taken performing steps, not time initialising memory etc.
     */
    if (benchtime != Py_None && realtime_start < 0) {
        val = PyObject_CallFunction(benchtime, "");
        if (!PyFloat_Check(val)) {
            Py_XDECREF(val); val = NULL;
            PyErr_SetString(PyExc_Exception, "Call to benchmark time function didn't return float.");
            return sim_clean();
        }
        realtime_start = PyFloat_AsDouble(val);
        Py_DECREF(val); val = NULL;
    }

    /* Go! */
    while(1) {

        /* Back-up current y (no allocation, this is fast) */
        for (i=0; i<model->n_states; i++) {
            NV_Ith_S(y_last, i) = NV_Ith_S(y, i);
        }

        /* Store engine time before step */
        time_last = t;

        if (model->is_ode) {

            /* Take a single ODE step */
            flag_cvode = CVode(cvode_mem, tnext, y, &t, CV_ONE_STEP);

            /* Check for errors */
            if (check_cvode_flag(&flag_cvode, "CVode", 1)) {
                /* Something went wrong... Set outputs and return */
                for (i=0; i<model->n_states; i++) {
                    PyList_SetItem(state_out, i, PyFloat_FromDouble(NV_Ith_S(y_last, i)));
                    /* PyList_SetItem steals a reference: no need to decref the double! */
                }
                /* TODO: Have an sy_last as well? */
                PyList_SetItem(inputs, 0, PyFloat_FromDouble(t));
                PyList_SetItem(inputs, 1, PyFloat_FromDouble(pace));
                PyList_SetItem(inputs, 2, PyFloat_FromDouble(realtime));
                PyList_SetItem(inputs, 3, PyFloat_FromDouble(evaluations));
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
        if (t == time_last) {
            if (++zero_step_count >= max_zero_step_count) {
                char errstr[200];
                sprintf(errstr, "ZERO_STEP %f", t);
                PyErr_SetString(PyExc_Exception, errstr);
                return sim_clean();
            }
        } else {
            /* Only count consecutive zero steps! */
            zero_step_count = 0;
        }

        /* Update step count */
        steps++;

        /* If we got to this point without errors... */
        if ((flag_cvode == CV_SUCCESS) || (flag_cvode == CV_ROOT_RETURN)) {

            /* Interpolation and root finding */
            if (model->is_ode) {

                /* Next event time exceeded? */
                if (t > tnext) {

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
                        if (!PyList_Append(rf_list, val)) {    /* Doesn't steal, need to decref */
                            Py_DECREF(val); val = NULL;
                            PyErr_SetString(PyExc_Exception, "Call to append() failed on root finding list.");
                            return sim_clean();
                        }
                        Py_DECREF(val); val = NULL;
                    }
                }
            }

            /* Periodic logging or point-list logging */
            if (!dynamic_logging && t > tlog) {
                /* Note: For periodic logging, the condition should be
                   `t > tlog` so that we log half-open intervals (i.e. the
                   final point should never be included). */

                /* Benchmarking? Then set realtime */
                if (benchtime != Py_None) {
                    val = PyObject_CallFunction(benchtime, "");
                    if (!PyFloat_Check(val)) {
                        Py_XDECREF(val); val = NULL;
                        PyErr_SetString(PyExc_Exception, "Call to benchmark time function didn't return float.");
                        return sim_clean();
                    }
                    realtime = PyFloat_AsDouble(val) - realtime_start;
                    Py_DECREF(val); val = NULL;
                }

                /* Log points */
                while (t > tlog) {

                    /* Get interpolated y(tlog) */
                    if (model->is_ode) {
                        flag_cvode = CVodeGetDky(cvode_mem, tlog, 0, y_log);
                        if (check_cvode_flag(&flag_cvode, "CVodeGetDky", 1)) return sim_clean();
                        if (model->has_sensitivities) {
                            flag_cvode = CVodeGetSensDky(cvode_mem, tlog, 0, sy_log);
                            if (check_cvode_flag(&flag_cvode, "CVodeGetSensDky", 1)) return sim_clean();
                        }
                    }
                    /* If cvode-free mode, the state can't change so we don't
                       need to do anything here */

                    /* Calculate intermediate variables & derivatives */
                    rhs(tlog, y_log, dy_log, udata);

                    /* Write to log */
                    flag_model = Model_Log(model);
                    if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }

                    if (model->has_sensitivities) {
                        /* Calculate sensitivities to output */
                        /* TODO: Use model methods instead */
                        calculate_sensitivity_outputs(t, y_log, dy_log, sy_log, udata);

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
                            PyErr_SetString(PyExc_Exception, "Overflow in logged step count: Simulation too long!");
                            return sim_clean();
                        }
                    } else {
                        /* Point-list logging */
                        /* Read next log point off the list */
                        if (ilog < PyList_Size(log_times)) {
                            val = PyList_GetItem(log_times, ilog); /* Borrowed */
                            if (!PyFloat_Check(val)) {
                                PyErr_SetString(PyExc_Exception, "Entries in 'log_times' must be floats.");
                                return sim_clean();
                            }
                            tlog = PyFloat_AsDouble(val);
                            ilog++;
                            val = NULL;
                        } else {
                            tlog = tmax + 1;
                        }
                    }
                }
            }

            /* Event-based pacing */

            /* At this point we have logged everything _before_ time, so
               it's safe to update the pacing mechanism. */
            if (epacing != NULL) {
                flag_epacing = ESys_AdvanceTime(epacing, t);
                if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
                tnext = ESys_GetNextTime(epacing, NULL);
                pace = ESys_GetLevel(epacing, NULL);
                tnext = (tnext < tmax) ? tnext : tmax;
            }

            /* Dynamic logging: Log every visited point */
            if (dynamic_logging) {

                /* Benchmarking? Then set realtime */
                if (benchtime != Py_None) {
                    val = PyObject_CallFunction(benchtime, "");
                    if (!PyFloat_Check(val)) {
                        Py_XDECREF(val); val = NULL;
                        PyErr_SetString(PyExc_Exception, "Call to benchmark time function did not return float.");
                        return sim_clean();
                    }
                    realtime = PyFloat_AsDouble(val) - realtime_start;
                    Py_DECREF(val); val = NULL;
                }

                /* Ensure the logged values are correct for the new time t */
                if (model->logging_derivatives || model->logging_intermediary) {
                    /* If logging derivatives or intermediaries, calculate the
                       values for the current time. */
                    /*TODO:REPLACE */
                    rhs(t, y, dy_log, udata);
                } else if (model->logging_bound) {
                    /* Logging bounds but not derivs or inters: No need to run
                       full rhs, just update bound variables */
                    Model_SetBoundVariables(
                        model, t, pace,
                        realtime, evaluations);
                }

                /* Write to log */
                flag_model = Model_Log(model);
                if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }

                if (model->has_sensitivities) {
                    /* Calculate sensitivities to output */
                    /* TODO: Use model methods */
                    calculate_sensitivity_outputs(t, y, dy_log, sy, udata);

                    /* Write sensitivity matrix to list */
                    flag_model = Model_LogSensitivityMatrix(model, sens_list);
                    if (flag_model != Model_OK) { Model_SetPyErr(flag_model); return sim_clean(); }
                }
            }

            /* Reinitialize CVODE if needed (cvode-mode only) */
            if (model->is_ode && flag_reinit) {
                flag_reinit = 0;
                /* Re-init */
                flag_cvode = CVodeReInit(cvode_mem, t, y);
                if (check_cvode_flag(&flag_cvode, "CVodeReInit", 1)) return sim_clean();
                if (model->has_sensitivities) {
                    flag_cvode = CVodeSensReInit(cvode_mem, CV_SIMULTANEOUS, sy);
                    if (check_cvode_flag(&flag_cvode, "CVodeSensReInit", 1)) return sim_clean();
                }
            }
        }

        /* Check if we're finished */
        if (ESys_eq(t, tmax)) t = tmax;
        if (t >= tmax) break;

        /* Perform any Python signal handling */
        if (PyErr_CheckSignals() != 0) {
            /* Exception (e.g. timeout or keyboard interrupt) occurred?
               Then cancel everything! */
            return sim_clean();
        }

        /* Report back to python after every x steps */
        steps_taken++;
        if (steps_taken >= 100) {
            return PyFloat_FromDouble(t);
        }
    }

    /* Set final state */
    for (i=0; i<model->n_states; i++) {
        PyList_SetItem(state_out, i, PyFloat_FromDouble(NV_Ith_S(y, i)));
        /* PyList_SetItem steals a reference: no need to decref the double! */
    }

    /* Set final sensitivities */
    if (model->has_sensitivities) {
        for (i=0; i<model->ns_independents; i++) {
            val = PyList_GetItem(s_state_out, i); /* Borrowed */
            for (j=0; j<model->n_states; j++) {
                PyList_SetItem(val, j, PyFloat_FromDouble(NV_Ith_S(sy[i], j)));
            }
        }
    }

    /* Set bound variable values */
    PyList_SetItem(inputs, 0, PyFloat_FromDouble(t));
    PyList_SetItem(inputs, 1, PyFloat_FromDouble(pace));
    PyList_SetItem(inputs, 2, PyFloat_FromDouble(realtime));
    PyList_SetItem(inputs, 3, PyFloat_FromDouble(evaluations));

    sim_clean();    /* Ignore return value */
    return PyFloat_FromDouble(t);
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
 * Returns the number of steps taken in the last simulation
 */
static PyObject*
sim_steps(PyObject *self, PyObject *args)
{
    return PyLong_FromLong(steps);
}

/*
 * Returns the number of rhs evaluations performed during the last simulation
 */
static PyObject*
sim_evals(PyObject *self, PyObject *args)
{
    return PyLong_FromLong(evaluations);
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
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
