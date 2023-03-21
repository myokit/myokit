
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



#include "pacing.h"

/*
This file defines a plain C Model object and interface.

All information about a model is stored in a `Model`, which is a pointer to a
Model_Memory struct.

Variables
=========
Model variables are divided into several (non-overlapping) groups:

States:
    Independent variables, varied during integration.
State derivatives:
    Calculated by the model.
Bound variables:
    External inputs to the model (e.g. time and pacing).
Intermediary variables:
    The remaining variables that depend on state variables.
Constants:
    The remaining variables that don't.

Constants are further divided into four (non-overlapping) groups:

Parameters:
    Any constant used as p in a sensitivity ds/dp. Variables selected as
    parameters may not depend on other variables.
Parameter-derived variables:
    Any constant that depends on a parameter.
Literals:
    The remaining constants without dependencies. (Note they don't need to be
    literal numbers, so `x = 1 + 2` counts as a literal).
Literal-derived variables:
    The remaining constants (which depend on literals, but on on parameters).

Sensitivities
=============
Sensitivities `dy/dx` can be calculated for variables `y` that are either
states or intermediary variables, and with respect to any `x` that's either a
parameter (see above) or a state's initial condition.

A model maintains a list of `parameters` (see above), and a list of pointers to
independent variables, which point either at the parameter values or at the
(current!) state values.

Evaluating derivatives and sensitivities
========================================
To use a model, start by creating a model instance:

    model = Model_Create()

This allocates memory, sets default values for all constants and sets the model
to its initial state. Derivatives and sensitivity outputs are not set at this
point, but can be set by calling the Model_EvaluateX() methods.

To avoid unnecessary evaluations, a model maintains an internal cache of recent
evaluations. Changing variables through the model functions described below
will clear this cache if required. If model variables are changed manually, the
function Model_ClearCache() should be called.

Methods:

Model_ClearCache(model)
    Clears any stored caches.

Model_SetLiteralVariables(model, *literals)
    Sets the values of all literals. If these are different from the previous
    values, the caches are cleared and the literal-derived and
    parameter-derived variables are recalculated.

Model_EvaluateLiteralDerivedVariables(model)
    Recalculates all literal-derived variables. Should be called after any
    manual change to the literals (in addition to calling Model_ClearCache).
    This method has no effect on the caches.

Model_SetParameters(model, *parameters)
    Sets the values of all parameters. If these are different from the previous
    values, the caches are cleared and the parameter-derived variables are
    recalculated.

Model_SetParametersFromIndependents(model, *independents)
    Sets the values of all parameters, using an array of independent variable
    values - any initial states are ignored. If any new parameter values are
    different from the previous values, the caches are cleared and the
    parameter-derived variables are recalculated.

Model_EvaluateParameterDerivedVariables(model)
    Recalculates all parameter-derived variables. Should be called after any
    manual change to the parameters (in addition to calling Model_ClearCache).
    This method has no effect on the caches.

Model_SetBoundVariables(model, time, pace, ...)
    Updates the model's bound variables. If the time or pacing variable are
    changed from their previous value the model caches will be cleared.

Model_SetStates(model, *states)
    Sets the values of all state variables. If these are different from the
    previous values, the caches are cleared.

Model_EvaluateDerivatives(model)
    If the derivatives cache is set, does nothing. Otherwise calculates the new
    derivatives and sets the cache.

Model_SetStateSensitivities(model, i, *s_states)
    Sets the values of the state sensitivities w.r.t. the i-th independent
    variable. If these are different from the previous values, the sensitivity
    output cache is cleared.

Model_EvaluateSensitivityOutputs(model)
    If the sensitivity outputs cache is set, does nothing. Otherwise
    calculates the new sensitivity outputs and sets the cache.

Finally, to free the memory used by a model, call

    Model_Destroy(model)

Logging
=======
A model can log the value of its variables to a Python dict that maps (fully
qualified) variable names to sequence types (e.g. lists). Typically, this dict
will be a myokit.DataLog.

Methods:

Model_InitialiseLogging(Model model, PyObject* log_dict)
    Sets up logging for all variables used as keys in log_dict (assuming fully
    qualified names). Will raise an error if the dict contains keys that do not
    correspond to model variables. The values in the dict should implement the
    sequence interface (and in particular, have an "append" method).

Model_Log(model)
    If logging has been set up, this will log the current values of variables
    to the sequences in the log dict.

Model_DeInitialiseLogging(model)
    De-initialises logging. This only needs to be called if logging needs to be
    set up differently, i.e. before a new call to Model_InitialiseLogging.

Logging sensitivities
=====================
Logging of sensitivity outputs is slightly more primitive than variable
logging, and consists of a single method - no initialisation is needed.

Model_LogSensitivityMatrix(Model model, PyObject* list)
    Creates a matrix (an n-tuple where each entry is an n-tuple of floats)
    containing the current values of the sensitivity outputs, and adds it to
    the given list, which must be a list (PyList).

Error handling
==============
Most methods return a Model_Flag that can be compared to any of the known error
codes to check the return type. E.g.

    if (model_flag != Model_OK) {
        ...
    }

An error message can be set for the Python user by calling Model_SetPyErr:

    if (model_flag != Model_OK) {
        Model_SetPyErr(model_flag);
        clean_up_and_return()
    }

*/

#include <math.h>
#include <stdio.h>

/*
 * Model error flags
 */
typedef int Model_Flag;
#define Model_OK                             0
#define Model_OUT_OF_MEMORY                 -1
/* General */
#define Model_INVALID_MODEL                 -100
/* Logging */
#define Model_LOGGING_ALREADY_INITIALISED   -200
#define Model_LOGGING_NOT_INITIALISED       -201
#define Model_UNKNOWN_VARIABLES_IN_LOG      -202
#define Model_LOG_APPEND_FAILED             -203
/* Logging sensitivities */
#define Model_NO_SENSITIVITIES_TO_LOG       -300
#define Model_SENSITIVITY_LOG_APPEND_FAILED -303
/* Pacing */
#define Model_INVALID_PACING                -400

/* Caching doesn't help much when running without jacobians etc., so disabled
   for now
#define Model_CACHING
*/

/*
 * Sets a Python exception based on a model flag.
 *
 * Arguments
 *  flag : The model flag to base the message on.
 */
void
Model_SetPyErr(Model_Flag flag)
{
    switch(flag) {
    case Model_OK:
        break;
    /* General */
    case Model_OUT_OF_MEMORY:
        PyErr_SetString(PyExc_Exception, "CModel error: Memory allocation failed.");
        break;
    case Model_INVALID_MODEL:
        PyErr_SetString(PyExc_Exception, "CModel error: Invalid model pointer provided.");
        break;
    /* Logging */
    case Model_LOGGING_ALREADY_INITIALISED:
        PyErr_SetString(PyExc_Exception, "CModel error: Logging initialised twice.");
        break;
    case Model_LOGGING_NOT_INITIALISED:
        PyErr_SetString(PyExc_Exception, "CModel error: Logging not initialised.");
        break;
    case Model_UNKNOWN_VARIABLES_IN_LOG:
        PyErr_SetString(PyExc_Exception, "CModel error: Unknown variables found in logging dictionary.");
        break;
    case Model_LOG_APPEND_FAILED:
        PyErr_SetString(PyExc_Exception, "CModel error: Call to append() failed on logging list.");
        break;
    /* Logging sensitivities */
    case Model_NO_SENSITIVITIES_TO_LOG:
        PyErr_SetString(PyExc_Exception, "CModel error: Sensivity logging called, but sensitivity calculations were not enabled.");
        break;
    case Model_SENSITIVITY_LOG_APPEND_FAILED:
        PyErr_SetString(PyExc_Exception, "CModel error: Call to append() failed on sensitivity matrix logging list.");
        break;
    case Model_INVALID_PACING:
        PyErr_SetString(PyExc_Exception, "CModel error: Invalid pacing provided.");
        break;

    /* Unknown */
    default:
        PyErr_Format(PyExc_Exception, "CModel error: Unlisted error %d", (int)flag);
        break;
    };
}

/*
 * Memory for model object.
 */
struct Model_Memory {
    /* If this is an ODE model this will be 1, otherwise 0. */
    int is_ode;

    /* If this model has sensitivities this will be 1, otherwise 0. */
    int has_sensitivities;

    /* pacing */
    realtype *pace_values;
    char **pace_labels;
    int n_pace;

    /* Bound variables */
    realtype time;
    realtype realtime;
    realtype evaluations;

    /* State variables and derivatives */
    int n_states;
    realtype* states;
    realtype* derivatives;

    /* Intermediary variables */
    int n_intermediary;
    realtype* intermediary;

    /* Parameters (can be changed during simulation) */
    int n_parameters;
    int n_parameter_derived;
    realtype* parameters;
    realtype* parameter_derived;

    /* Literals (should be fixed before a simulation) */
    int n_literals;
    int n_literal_derived;
    realtype* literals;
    realtype* literal_derived;

    /* Number of outputs (y in dy/dx) to calculate sensitivities of */
    int ns_dependents;

    /* Number of parameters and initial states (x in dy/dx) to calculate
       sensitivities w.r.t. */
    int ns_independents;

    /* Pointers to the independent variables */
    realtype** s_independents;

    /* s_is_parameter[i] is 1 if the i-th independent is a parameter, 0
       otherwise */
    int* s_is_parameter;

    /* Sensitivity of state variables w.r.t. independents. */
    realtype* s_states;

    /* Sensitivity of intermediary variables needed to calculate remaining
       sensitivities. */
    int ns_intermediary;
    realtype* s_intermediary;

    /* Logging initialised? */
    int logging_initialised;

    /* Which variables are we logging? */
    int logging_states;
    int logging_derivatives;
    int logging_intermediary;
    int logging_bound;

    /* How many variables are we logging? */
    int n_logged_variables;

    /* String used to call "append" method on sequence types */
    PyObject* _list_update_string;

    /* Array of *PyObjects, each a sequence to log to. */
    PyObject** _log_lists;

    /* Array of pointers to realtype, each a variable to log */
    realtype** _log_vars;

    /* Caching */
    #ifdef Model_CACHING
    int valid_cache_derivatives;
    int valid_cache_sensitivity_outputs;
    #endif
};
typedef struct Model_Memory *Model;

/*
 * Variable aliases
 */

/* Bound variables */
#define B_time model->time
/* States */

/* Derivatives */

/* Intermediary variables */

/* Parameters */

/* Parameter-derived */

/* Literal */
#define C_v model->literals[0]

/* Literal-derived */
#define C_w model->literal_derived[0]

/* Sensitivities of the state vectors */

/* Sensitivities of variables needed to calculate remaining sensitivities */


#ifdef Model_CACHING
/*
 * Cache checking and clearing for internal use
 */
inline int Model__ValidCache(Model model)
{
    return (model->valid_cache_derivatives && model->valid_cache_sensitivity_outputs);
}
inline void Model__InvalidateCache(Model model)
{
    model->valid_cache_derivatives = 0;
    model->valid_cache_sensitivity_outputs = 0;
}
#endif

/*
 * Clears any cached evaluations from a model.
 *
 * Arguments
 *  model : The model whos cache to clear.
 *
 * Returns a model flag.
 *
 */
Model_Flag
Model_ClearCache(Model model)
{
    #ifdef Model_CACHING
    if (model == NULL) return Model_INVALID_MODEL;
    Model__InvalidateCache(model);
    #endif
    return Model_OK;
}

/*
 * Setup the pacing system.
 *
 * Arguments
 *  n_pace: the number of pacing values to use.
 *  labels: an array of n_pace strings, each a label for the corresponding
 *          pacing value.
 *
 * Returns a model flag.
 *
 */
Model_Flag
Model_SetupPacing(Model model, int n_pace)
{
    if (model == NULL) return Model_INVALID_MODEL;
    if (n_pace < 0) return Model_INVALID_PACING;

    /* Free any existing pacing */
    if (model->n_pace > 0) {
        free(model->pace_values);
    }

    /* Allocate new pacing */
    model->n_pace = n_pace;
    model->pace_values = (realtype*)malloc(n_pace * sizeof(realtype));
    if (model->pace_values == NULL) {
        return Model_OUT_OF_MEMORY;
    }

    /* Clear values */
    for (int i = 0; i < n_pace; i++) {
        model->pace_values[i] = 0;
    }

    return Model_OK;
}

/*
 * (Re)calculates the values of all constants that are derived from other
 * constants.
 *
 * Calling this method does not affect the model cache.
 *
 * Arguments
 *  model : The model to update.
 *
 * Returns a model flag.
 */
Model_Flag
Model_EvaluateLiteralDerivedVariables(Model model)
{
    if (model == NULL) return Model_INVALID_MODEL;

    C_w = 2.0 * C_v;

    return Model_OK;
}

/*
 * (Re)calculates the values of all constants that are derived from variables
 * marked as "parameters" in sensitivity calculations.
 *
 * Calling this method does not affect the model cache.
 *
 * Arguments
 *  model : The model to update.
 *
 * Returns a model flag.
 */
Model_Flag
Model_EvaluateParameterDerivedVariables(Model model)
{
    if (model == NULL) return Model_INVALID_MODEL;


    return Model_OK;
}

/*
 * Updates the literal variables to the values given in `literals`.
 *
 * If any of the values are changed
 *  - the model caches are cleared.
 *  - the literal-derived variables are recalculated.
 *  - the parameter-derived variables are recalculated.
 *
 * Arguments
 *  model : The model whose variables to set
 *  literals : An array of size model->n_literals
 *
 * Returns a model flag.
 */
Model_Flag
Model_SetParameters(Model model, const realtype* parameters)
{
    int i;
    if (model == NULL) return Model_INVALID_MODEL;

    /* Scan for changes */
    i = 0;
    #ifdef Model_CACHING
    if (Model__ValidCache(model)) {
        for (; i<model->n_parameters; i++) {
            if (model->parameters[i] != parameters[i]) {
                break;
            }
        }
    }
    #endif

    /* Update remaining */
    if (i < model->n_parameters) {
        for (; i<model->n_parameters; i++) {
            model->parameters[i] = parameters[i];
        }
        #ifdef Model_CACHING
        Model__InvalidateCache(model);
        #endif
        Model_EvaluateParameterDerivedVariables(model);
    }

    return Model_OK;
}


/*
 * Updates the parameter variables to the values given in the vector of
 * `independents`, ignoring the initial values.
 *
 * If any of the parameter values are changed
 *  - the model caches are cleared.
 *  - the parameter-derived variables are recalculated.
 *
 * Arguments
 *  model : The model whose variables to set
 *  independents : An array of size model->ns_independents
 *
 * Returns a model flag.
 */
Model_Flag
Model_SetParametersFromIndependents(Model model, const realtype* independents)
{
    int i, j;
    if (model == NULL) return Model_INVALID_MODEL;

    /* Note: this method assumes that parameters are ordered in the same way
             as independents. */

    /* Scan for changes */
    i = 0;
    j = 0;
    #ifdef Model_CACHING
    if (Model__ValidCache(model)) {
        for (; i<model->ns_independents; i++) {
            if (model->s_is_parameter[i]) {
                if (model->parameters[j] != independents[i]) {
                    break;
                }
                j++;
            }
        }
    }
    #endif

    /* Update remaining */
    if (j < model->n_parameters) {
        for (; i<model->ns_independents; i++) {
            if (model->s_is_parameter[i]) {
                model->parameters[j] = independents[i];
                j++;
            }
        }
        #ifdef Model_CACHING
        Model__InvalidateCache(model);
        #endif
        Model_EvaluateParameterDerivedVariables(model);
    }

    return Model_OK;
}

/*
 * Updates this model's bound variables to the given values.
 * Also updates the model's pacing system.
 *
 * Arguments
 *  model : The model to update
 *  time
 *  pace
 *  realtime
 *  evaluations
 *
 * The model caches are cleared if either the `time` or `pace` variables are
 * changed.
 *
 * Returns a model flag.
 */
Model_Flag
Model_SetBoundVariables(
    Model model,
    const realtype time, const realtype *pace_values,
    const realtype realtime, const realtype evaluations)
{
    int changed;
    if (model == NULL) return Model_INVALID_MODEL;

    changed = 0;
    if (time != model->time) {
        model->time = time;
        changed = 1;
    }

    for (int i = 0; i < model->n_pace; i++) {
        if (pace_values[i] != model->pace_values[i]) {
            model->pace_values[i] = pace_values[i];
            changed = 1;
        }
    }

    #ifdef Model_CACHING
    if (changed) {
        Model__InvalidateCache(model);
    }
    #endif

    /* Update unchecked variables */
    model->realtime = realtime;
    model->evaluations = evaluations;

    return Model_OK;
}

/*
 * Updates the state variables to the float values given in `states`.
 *
 * If any of the values are changed, the model caches are cleared.
 *
 * Arguments
 *  model : The model whose variables to set
 *  states : An array of size model->n_states
 *
 * Returns a model flag.
 */
Model_Flag
Model_SetStates(Model model, const realtype* states)
{
    int i;
    if (model == NULL) return Model_INVALID_MODEL;

    /* Scan for changes */
    i = 0;
    #ifdef Model_CACHING
    if (Model__ValidCache(model)) {
        for (; i<model->n_states; i++) {
            if (model->states[i] != states[i]) {
                 break;
            }
        }
    }
    #endif

    /* Update remaining */
    if (i < model->n_states) {
        for (; i<model->n_states; i++) {
            model->states[i] = states[i];
        }
        #ifdef Model_CACHING
        Model__InvalidateCache(model);
        #endif
    }

    return Model_OK;
}

/*
 * (Re)calculates the values of all intermediary variables and state
 * derivatives.
 *
 * Arguments
 *  model : The model to update
 *
 * If the model's derivatives cache is set, the method will exit without
 * recalculating. If not, the method will recalculate and the model's
 * derivative cache will be set.
 *
 * Returns a model flag.
 */
Model_Flag
Model_EvaluateDerivatives(Model model)
{
    if (model == NULL) return Model_INVALID_MODEL;

    /*TODO: Skip if cached! */
    /*if (model->valid_cache_derivatives) { */


    #ifdef Model_CACHING
    /* Indicate derivatives values can be trusted. */
    model->valid_cache_derivatives = 1;
    #endif

    return Model_OK;
}

/*
 * Updates the state variable sensitivities w.r.t. the i-th independent to the
 * values given in `s_states`.
 *
 * If any of the values are changed, the model sensitivity cache is cleared.
 *
 * Arguments
 *  model : The model whose variables to set
 *  i : The integer index of the independent whose sensitivities to set
 *  s_states : An array of size model->n_states
 *
 * Returns a model flag.
 */
Model_Flag
Model_SetStateSensitivities(Model model, int i, const realtype* s_states)
{
    int j;
    if (model == NULL) return Model_INVALID_MODEL;

    /* Calculate offset */
    i *= model->n_states;

    /* Scan for changes */
    j = 0;
    #ifdef Model_CACHING
    if (Model__ValidCache(model)) {
        for (; j<model->n_states; j++) {
            if (model->s_states[i + j] != s_states[j]) {
                 break;
            }
        }
    }
    #endif

    /* Update remaining */
    if (j < model->n_states) {
        for (; j<model->n_states; j++) {
            model->s_states[i + j] = s_states[j];
        }
        #ifdef Model_CACHING
        model->valid_cache_sensitivity_outputs = 0;
        #endif
    }

    return Model_OK;
}

/*
 * (Re)calculates all sensitivities where the dependent variable is an
 * intermediary variable (assuming the sensitivities where the dependent
 * variable is a state are already known).
 *
 * If the model's sensitivity output cache is set, the method will exit without
 * recalculating. If not, the method will recalculate and the model's
 * sensitivity output cache will be set.

 * Arguments
 *  model : The model to update
 *
 * Returns a model flag.
 */
Model_Flag
Model_EvaluateSensitivityOutputs(Model model)
{
    if (model == NULL) return Model_INVALID_MODEL;

    /*TODO: Skip if cached! */


    #ifdef Model_CACHING
    /* Indicate sensitivity outputs can be trusted. */
    model->valid_cache_sensitivity_outputs = 1;
    #endif

    return Model_OK;
}

/*
 * Private method: Add a variable to the logging lists. Returns 1 if
 * successful.
 *
 * Note: The variable names are all ascii compatible. In Python2, the strings
 * inside log_dict are either unicode or bytes, but they can be matched
 * without conversion.
 *
 * Arguments
 *  log_dict : A dictionary mapping variable names to sequences.
 *  i : The next indice to add logs and vars.
 *  name : The name to check.
 *  var : A pointer to the variable.
 *
 * Returns 1 if added, 0 if not.
 */
int
Model__AddVariableToLog(
    Model model,
    PyObject* log_dict, int i, const char* name, const realtype* variable)
{
    PyObject* key = PyUnicode_FromString(name);     /* New reference */
    PyObject* val = PyDict_GetItem(log_dict, key);  /* Borrowed reference, or NULL */
    Py_DECREF(key);
    if (val == NULL) { return 0; }

    model->_log_lists[i] = val;
    model->_log_vars[i] = (realtype*)variable;
    return 1;
}

/*
 * Initialises logging, using the given dict. An error is returned if logging
 * is already initialised.
 *
 * Arguments
 *  model : The model whose logging system to initialise.
 *  log_dict : A Python dict mapping fully qualified variable names to sequence
 *             objects to log in.
 *
 * Returns a model flag
 */
Model_Flag
Model_InitialiseLogging(Model model, PyObject* log_dict)
{
    int i, j;

    if (model == NULL) return Model_INVALID_MODEL;
    if (model->logging_initialised) return Model_LOGGING_ALREADY_INITIALISED;

    /* Number of variables to log */
    model->n_logged_variables = PyDict_Size(log_dict);

    /* Allocate pointer lists */
    model->_log_lists = (PyObject**)malloc(sizeof(PyObject*) * model->n_logged_variables);
    model->_log_vars = (realtype**)malloc(sizeof(realtype*) * model->n_logged_variables);

    /* Check states */
    i = 0;

    model->logging_states = (i > 0);

    /* Check derivatives */
    j = i;

    model->logging_derivatives = (i != j);

    /* Check bound variables */
    j = i;
    i += Model__AddVariableToLog(model, log_dict, i, "c.t", &B_time);

    model->logging_bound = (i != j);

    /* Check intermediary variables */
    j = i;

    model->logging_intermediary = (i != j);

    /* Check if log contained extra variables */
    if (i != model->n_logged_variables) return Model_UNKNOWN_VARIABLES_IN_LOG;

    /* Create "append" string. */
    if (model->_list_update_string == NULL) {
        model->_list_update_string = PyUnicode_FromString("append");
    }

    /* All done! */
    model->logging_initialised = 1;
    return Model_OK;
}

/*
 * De-initialises logging, undoing the effects of Model_InitialiseLogging() and
 * allowing logging to be initialised again.
 *
 * Arguments
 *  model : The model whos logging to deinitialise.
 *
 * Returns a model flag.
 */
Model_Flag
Model_DeInitialiseLogging(Model model)
{
    if (model == NULL) return Model_INVALID_MODEL;
    if (!model->logging_initialised) return Model_LOGGING_NOT_INITIALISED;

    /* Free memory */
    if (model->_log_vars != NULL) {
        free(model->_log_vars);
        model->_log_vars = NULL;
    }
    if (model->_log_lists != NULL) {
        free(model->_log_lists);
        model->_log_lists = NULL;
    }

    /* Reset */
    model->logging_initialised = 0;
    model->n_logged_variables = 0;
    model->logging_states = 0;
    model->logging_derivatives = 0;
    model->logging_intermediary = 0;
    model->logging_bound = 0;

    return Model_OK;
}

/*
 * Logs the current state of the model to the logging dict passed in to
 * Model_InitialiseLogging.
 *
 * Note: This method does not update the state in any way, e.g. to make sure
 * that what is logged is sensible.
 *
 * Arguments
 *  model : The model whose state to log
 *
 * Returns a model flag.
 */
Model_Flag
Model_Log(Model model)
{
    int i;
    PyObject *val, *ret;

    if (model == NULL) return Model_INVALID_MODEL;
    if (!model->logging_initialised) return Model_LOGGING_NOT_INITIALISED;

    for (i=0; i<model->n_logged_variables; i++) {
        val = PyFloat_FromDouble(*(model->_log_vars[i]));
        ret = PyObject_CallMethodObjArgs(model->_log_lists[i], model->_list_update_string, val, NULL);
        Py_DECREF(val);
        Py_XDECREF(ret);
        if (ret == NULL) {
            return Model_LOG_APPEND_FAILED;
        }
    }

    return Model_OK;
}

/*
 * Creates a matrix of sensitivities and adds it to a Python sequence.
 *
 * The created matrix is a (Python) tuple of tuples, where the first (outer)
 * indice is for the dependent variable (y in dy/dx) and the second (inner)
 * indice is for the independent variable (x in dy/dx).
 *
 * model : The model whose sensitivities to log (must have sensitivity
 *         calculations enabled).
 * list : A PyList to add the newly created matrix of sensitivities to.
 *
 * Returns a model flag.
 */
Model_Flag
Model_LogSensitivityMatrix(Model model, PyObject* list)
{
    PyObject *l1, *l2;
    PyObject *val;
    int flag;

    if (model == NULL) return Model_INVALID_MODEL;

    /* Create outer tuple */
    l1 = PyTuple_New(model->ns_dependents);
    if (l1 == NULL) goto nomem;

    /* Note that PyTuple_SetItem steals a reference */


    /* Add matrix to list (must be a PyList, no advantage here to using a
       buffer). */
    flag = PyList_Append(list, l1);
    Py_DECREF(l1);
    if (flag < 0) return Model_SENSITIVITY_LOG_APPEND_FAILED;

    return Model_OK;

nomem:
    /* Assuming val is NULL or has had its reference stolen. */
    Py_XDECREF(l1);
    Py_XDECREF(l2);
    return Model_OUT_OF_MEMORY;
}

/*
 * Creates and returns a model struct.
 *
 * Arguments
 *  flag : The address of a model flag or NULL.
 *
 * Returns a Model pointer.
 */
Model Model_Create(Model_Flag* flagp)
{
    Model_Flag flag;

    /* Allocate model memory (not including arrays) */
    Model model = (Model)malloc(sizeof(struct Model_Memory));
    if (model == NULL) {
        if (flagp != NULL) { *flagp = Model_OUT_OF_MEMORY; }
        return NULL;
    }

    /* Model info */
    model->is_ode = 0;
    model->has_sensitivities = 0;

    /*
     * Variables
     */

    /* States and derivatives */
    model->n_states = 0;
    model->states = (realtype*)malloc(model->n_states * sizeof(realtype));
    model->derivatives = (realtype*)malloc(model->n_states * sizeof(realtype));

    /* Intermediary variables */
    model->n_intermediary = 0;
    model->intermediary = (realtype*)malloc(model->n_intermediary * sizeof(realtype));

    /* Parameters */
    model->n_parameters = 0;
    model->n_parameter_derived = 0;
    model->parameters = (realtype*)malloc(model->n_parameters * sizeof(realtype));
    model->parameter_derived = (realtype*)malloc(model->n_parameter_derived * sizeof(realtype));

    /* Literals */
    model->n_literals = 1;
    model->n_literal_derived = 1;
    model->literals = (realtype*)malloc(model->n_literals * sizeof(realtype));
    model->literal_derived = (realtype*)malloc(model->n_literal_derived * sizeof(realtype));

    /*
     * Sensitivities
     */

    /* Total number of dependents to output sensitivities of */
    model->ns_dependents = 0;

    /* Total number of independent to calculate sensitivities w.r.t. */
    model->ns_independents = 0;

    /* Pointers to independent variables */
    /* Note that, for sensitivities w.r.t. initial values, the entry in this
       list points to the _current_, not the initial value. */
    model->s_independents = (realtype**)malloc(model->ns_independents * sizeof(realtype));

    /* Type of independents (1 for parameter, 0 for initial) */
    model->s_is_parameter = (int*)malloc(model->ns_independents * sizeof(int));

    /* Sensitivities of state variables */
    model->s_states = (realtype*)malloc(model->n_states * model->ns_independents * sizeof(realtype));

    /* Sensitivities of intermediary variables needed in calculations */
    model->ns_intermediary = 0;
    model->s_intermediary = (realtype*)malloc(model->ns_intermediary * sizeof(realtype));

    /*
     * Logging
     */

    /* Logging configured? */
    model->logging_initialised = 0;
    model->n_logged_variables = 0;

    /* Logged variables and logged types */
    model->logging_states = 0;
    model->logging_derivatives = 0;
    model->logging_intermediary = 0;
    model->logging_bound = 0;

    /* Logging list update string */
    model->_list_update_string = NULL;

    /* Logging pointer lists */
    model->_log_lists = NULL;
    model->_log_vars = NULL;

    /*
     * Default values
     */

    /* Bound variables */
    model->time = 0;
    model->realtime = 0;
    model->evaluations = 0;

    /* Literal values */
    C_v = 0.0;

    flag = Model_EvaluateLiteralDerivedVariables(model);
    if (flag != Model_OK) {
        if (flagp != NULL) { *flagp = flag; }
        return NULL;
    }

    /* Parameter values */

    flag = Model_EvaluateParameterDerivedVariables(model);
    if (flag != Model_OK) {
        if (flagp != NULL) { *flagp = flag; }
        return NULL;
    }

    /* State values */

    /*
     * Caching.
     * At this point, we don't have derivatives or sensitivity outputs, so
     * both cache flags are set to invalid.
     */
    #ifdef Model_CACHING
    model->valid_cache_derivatives = 0;
    model->valid_cache_sensitivity_outputs = 0;
    #endif

    /*
     * Finalise
     */

    /* Set flag to indicate success */
    if (flagp != NULL) { *flagp = Model_OK; }

    /* Return newly created model */
    return model;
}

/*
 *
 *
 * Arguments
 *  model : The model to destroy.
 *
 * Returns a model flag.
 */
Model_Flag
Model_Destroy(Model model)
{
    if (model == NULL) return Model_INVALID_MODEL;

    /* Variables */
    free(model->states); model->states = NULL;
    free(model->derivatives); model->derivatives = NULL;
    free(model->intermediary); model->intermediary = NULL;
    free(model->parameters); model->parameters = NULL;
    free(model->parameter_derived); model->parameter_derived = NULL;
    free(model->literals); model->literals = NULL;
    free(model->literal_derived); model->literal_derived = NULL;

    /* Sensitivities */
    free(model->s_independents); model->s_independents = NULL;
    free(model->s_is_parameter); model->s_is_parameter = NULL;
    free(model->s_states); model->s_states = NULL;
    free(model->s_intermediary); model->s_intermediary = NULL;

    /* Logging */
    free(model->_log_vars); model->_log_vars = NULL;
    free(model->_log_lists); model->_log_lists = NULL;
    Py_XDECREF(model->_list_update_string); model->_list_update_string = NULL;

    /* Model itself */
    free(model);
    return Model_OK;
}



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
        PyErr_Format(PyExc_Exception, "%s() failed - returned NULL pointer", funcname);
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
                default:
                    PyErr_Format(PyExc_Exception, "Function CVode() failed with unknown flag = %d", flag);
                }
            } else {
                PyErr_Format(PyExc_Exception, "%s() failed with flag = %d", funcname, flag);
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
        /* Python 3.2+: PyErr_WarnFormat(PyExc_RuntimeWarning, 1, "CVODES: %s", msg); */
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
union PSys {
    ESys event;
    FSys fixed;
};
enum PSysType {
    EVENT,
    FIXED
};
union PSys *pacing_systems;   /* array of pacing system (event or fixed) */
enum PSysType *pacing_types; /* array of pacing system types */
PyObject *protocols;         /* The protocols used to generate the pacing systems */
double* pacing;         /* Pacing values, same size as pacing_systems and pacing_types*/
int n_pace;              /* The number of pacing systems */

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
    for (int i = 0; i < n_pace; i++) {
        if (pacing_types[i] == FIXED) {
            pacing[i] = FSys_GetLevel(pacing_systems[i].fixed, t, &flag_fpacing);
            if (flag_fpacing != FSys_OK) { /* This should never happen */
                FSys_SetPyErr(flag_fpacing);
                return -1;  /* Negative value signals irrecoverable error to CVODE */
            }
        }
    }

    /* Update model state */

    /* Set time, pace, evaluations and realtime */
    evaluations++;
    Model_SetBoundVariables(model, t, pacing, realtime, evaluations);

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
        if (ylast != NULL) { N_VDestroy_Serial(ylast); ylast = NULL; }
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
        for (int i = 0; i < n_pace; i++) {
            if (pacing_types[i] == FIXED) {
                FSys_Destroy(pacing_systems[i].fixed);
            } else if (pacing_types[i] == EVENT) {
                ESys_Destroy(pacing_systems[i].event);
            }
        }
        free(pacing_systems); pacing_systems = NULL;
        free(pacing_types); pacing_types = NULL;
        free(pacing); pacing = NULL;

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
    pacing_types = NULL;
    pacing_systems = NULL;
    pacing = NULL;
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

    /* Check input arguments     012345678901234567 */
    if (!PyArg_ParseTuple(args, "ddOOOOOOOdOOidOOi",
            &tmin,              /*  0. Float: initial time */
            &tmax,              /*  1. Float: final time */
            &state_py,          /*  2. List: initial and final state */
            &s_state_py,        /*  3. List of lists: state sensitivities */
            &bound_py,          /*  4. List: store final bound variables here */
            &literals,          /*  5. List: literal constant values */
            &parameters,        /*  6. List: parameter values */
            &protocols,        /*   7. Event-based or fixed protocols */
            &log_dict,          /*  8. DataLog */
            &log_interval,      /*  9. Float: log interval, or 0 */
            &log_times,         /* 10. List of logging times, or None */
            &sens_list,         /* 11. List to store sensitivities in */
            &rf_indice,         /* 12. Int: root-finding state variable */
            &rf_threshold,      /* 13. Float: root-finding threshold */
            &rf_list,           /* 14. List to store roots in or None */
            &benchmarker,       /* 15. myokit.tools.Benchmarker object */
            &log_realtime       /* 16. Int: 1 if logging real time */
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

    /* Print info about simulation to undertake */
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("CM Preparing to simulate from %g to %g.\n", tmin, tmax);
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

    /* Print initial state */
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("CM Initial state vector (CVODES):\n");
    for (i=0; i<model->n_states; i++) {
        printf("CM   %g\n", NV_Ith_S(y, i));
    }
    #endif

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

    /* Print initial sensitivities */
    #ifdef MYOKIT_DEBUG_MESSAGES
    if (model->has_sensitivities) {
        printf("CM Initial state sensitivities (CVODES):\n");
        for (i=0; i<model->ns_independents; i++) {
            printf("CM   %d.\n", i);
            for (j=0; j<model->n_states; j++) {
                printf("CM     %g\n", NV_Ith_S(sy[i], j));
            }
        }
    }
    #endif

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

    /* Print initial sensitivities */
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("CM Literals:\n");
    for (i=0; i<model->n_literals; i++) {
        printf("CM   %g\n", model->literals[i]);
    }
    #endif

    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Set values of literal variables.");
    #endif

    /* Evaluate calculated constants */
    Model_EvaluateLiteralDerivedVariables(model);

    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Set values of calculated constants.");
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
    n_pace = 0;
    if (protocols != Py_None) {
        if (!PyList_Check(protocols)) {
            return sim_cleanx(PyExc_TypeError, "'protocols' must be a list.");
        }
        n_pace = PyList_Size(protocols);
    }
    model->n_pace = n_pace;
    pacing_systems = (union PSys*)malloc(sizeof(union PSys) * n_pace);
    if (pacing_systems == NULL) {
        return sim_cleanx(PyExc_Exception, "Unable to allocate space to store pacing systems.");
    }
    pacing_types = (enum PSysType *)malloc(sizeof(enum PSysType) * n_pace);
    if (pacing_types == NULL) {
        return sim_cleanx(PyExc_Exception, "Unable to allocate space to store pacing types.");
    }
    pacing = (realtype*)malloc(sizeof(realtype) * n_pace);
    if (pacing == NULL) {
        return sim_cleanx(PyExc_Exception, "Unable to allocate space to store pacing values.");
    }
    Model_SetupPacing(model, n_pace);

    /*
     *  unless set by pacing, tnext is set to tmax
     */
    tnext = tmax;

    /* Set up event-based or fixed pacing */
    if (protocols != Py_None) {
        for (int i = 0; i < PyList_Size(protocols); i++) {
            PyObject *protocol = PyList_GetItem(protocols, i);
            const char* protocol_type_name = Py_TYPE(protocol)->tp_name;
            if (strcmp(protocol_type_name, "Protocol") == 0) {
                pacing_systems[i].event = ESys_Create(&flag_epacing);
                ESys epacing = pacing_systems[i].event;
                if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
                flag_epacing = ESys_Populate(epacing, protocol);
                if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
                flag_epacing = ESys_AdvanceTime(epacing, tmin);
                if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
                const double ptnext = ESys_GetNextTime(epacing, &flag_epacing);
                pacing[i] = ESys_GetLevel(epacing, &flag_epacing);
                tnext = fmin(ptnext, tnext);

                #ifdef MYOKIT_DEBUG_PROFILING
                benchmarker_print("CP Created event-based pacing system.");
                #endif
            } else if (strcmp(protocol_type_name, "FixedProtocol") == 0) {
                pacing_systems[i].fixed = FSys_Create(&flag_fpacing);
                FSys fpacing = pacing_systems[i].fixed;
                if (flag_fpacing != FSys_OK) { FSys_SetPyErr(flag_fpacing); return sim_clean(); }
                flag_fpacing = FSys_Populate(fpacing, protocol);
                if (flag_fpacing != FSys_OK) { FSys_SetPyErr(flag_fpacing); return sim_clean(); }


                #ifdef MYOKIT_DEBUG_PROFILING
                benchmarker_print("CP Created fixed-form pacing system.");
                #endif
            } else {
                printf("protocol_type_name: %s", protocol_type_name);
                return sim_cleanx(PyExc_TypeError, "Item %d in 'protocols' is not a myokit.Protocol or myokit.FixedProtocol object.", i);
            }

        }
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
            val = PySequence_GetItem(log_times, ilog); /* New reference */
            if (PyFloat_Check(val)) {
                tlog = PyFloat_AsDouble(val);
                Py_DECREF(val);
            } else if (PyNumber_Check(val)) {
                ret = PyNumber_Float(val); /* New reference */
                Py_DECREF(val);            /* Done with val */
                if (ret == NULL) {
                    return sim_cleanx(PyExc_ValueError, "Unable to cast entry in 'log_times' to float.");
                } else {
                    tlog = PyFloat_AsDouble(ret);
                    Py_DECREF(ret);
                }
            } else {
                Py_DECREF(val);
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

    /* Multi-purpose Python objects */
    PyObject *val;
    PyObject* ret;

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
            printf("\nCM Taking CVODE step from time %g to %g.\n", t, tnext);
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
                PyList_SetItem(bound_py, 1, PyFloat_FromDouble(realtime));
                PyList_SetItem(bound_py, 2, PyFloat_FromDouble(evaluations));
                for (int i = 0; i < n_pace; i++) {
                    PyList_SetItem(bound_py, 3 + i, PyFloat_FromDouble(pacing[i]));
                }
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
                return sim_cleanx(PyExc_ArithmeticError, "Maximum number of zero-length steps taken at t=%g", t);
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
                    printf("CM Event time exceeded, rewinding to %g.\n", tnext);
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
                    printf("CM Interpolation-logging for t=%g.\n", t);
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
                            val = PySequence_GetItem(log_times, ilog); /* New reference */
                            if (PyFloat_Check(val)) {
                                proposed_tlog = PyFloat_AsDouble(val);
                                Py_DECREF(val);
                            } else if (PyNumber_Check(val)) {
                                ret = PyNumber_Float(val);  /* New reference */
                                Py_DECREF(val);
                                if (ret == NULL) {
                                    return sim_cleanx(PyExc_ValueError, "Unable to cast entry in 'log_times' to float.");
                                } else {
                                    proposed_tlog = PyFloat_AsDouble(ret);
                                    Py_DECREF(ret);
                                }
                            } else {
                                Py_DECREF(val);
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
            tnext = tmax;
            for (int i = 0; i < n_pace; i++) {
                if (pacing_types[i] != EVENT) continue;
                ESys epacing = pacing_systems[i].event;
                flag_epacing = ESys_AdvanceTime(epacing, t);
                if (flag_epacing != ESys_OK) {
                    ESys_SetPyErr(flag_epacing); return sim_clean();
                }
                const double ptnext = ESys_GetNextTime(epacing, NULL);
                tnext = fmin(tnext, ptnext);
                pacing[i] = ESys_GetLevel(epacing, NULL);
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
                    printf("CM Calling RHS to log derivs/inter/sens at time %g.\n", t);
                    #endif
                    rhs(t, y, NULL, udata);
                } else if (model->logging_bound) {
                    /* Logging bounds but not derivs or inters: No need to run
                       full rhs, just update bound variables */
                    Model_SetBoundVariables(model, t, pacing, realtime, evaluations);
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
            // Return new reference
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
    PyList_SetItem(bound_py, 1, PyFloat_FromDouble(realtime));
    PyList_SetItem(bound_py, 2, PyFloat_FromDouble(evaluations));
    for (int i = 0; i < n_pace; i++) {
        PyList_SetItem(bound_py, 3 + i, PyFloat_FromDouble(pacing[i]));
    }

    #ifdef MYOKIT_DEBUG_PROFILING
    benchmarker_print("CP Set final state and bound variable values.");
    #endif

    sim_clean();    /* Ignore return value */
    return PyFloat_FromDouble(t);  // Return new reference
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
    PyObject *pace_in;
    double *pacing_in;
    Model model;
    Model_Flag flag_model;
    PyObject *state;
    PyObject *deriv;
    PyObject *literals;
    PyObject *parameters;
    PyObject *val;

    /* Start */
    success = 0;

    /* Check input arguments */
    /* Check input arguments     0123456789ABCDEF*/
    if (!PyArg_ParseTuple(args, "ddOOOO",
            &time_in,           /* 0. Float: time */
            &pace_in,           /* 1. List: pace */
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
    if (!PyList_Check(pace_in)) {
        PyErr_SetString(PyExc_Exception, "Pace argument must be a list.");
        return 0;
    }
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

    /* Set pacing values */
    pacing_in = (double*)malloc(sizeof(double) * n_pace);
    for (i=0; i < n_pace; i++) {
        val = PyList_GetItem(pace_in, i); /* Don't decref */
        if (!PyFloat_Check(val)) {
            PyErr_Format(PyExc_Exception, "Item %d in pace vector is not a float.", i);
            goto error;
        }
        pacing_in[i] = PyFloat_AsDouble(val);
    }

    /* Set bound variables */
    Model_SetBoundVariables(model, time_in, pacing_in, 0, 0);

    /* Set literal values */
    for (i=0; i<model->n_literals; i++) {
        val = PyList_GetItem(literals, i);    /* Don't decref */
        if (!PyFloat_Check(val)) {
            PyErr_Format(PyExc_Exception, "Item %d in literal vector is not a float.", i);
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
            PyErr_Format(PyExc_Exception, "Item %d in parameter vector is not a float.", i);
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
            PyErr_Format(PyExc_Exception, "Item %d in state vector is not a float.", i);
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
    "myokit_sim_2_5654382963843775677",       /* m_name */
    "Generated CVODESim module",/* m_doc */
    -1,                         /* m_size */
    SimMethods,                 /* m_methods */
    NULL,                       /* m_reload */
    NULL,                       /* m_traverse */
    NULL,                       /* m_clear */
    NULL,                       /* m_free */
};

PyMODINIT_FUNC PyInit_myokit_sim_2_5654382963843775677(void) {
    return PyModule_Create(&moduledef);
}

#else

PyMODINIT_FUNC
initmyokit_sim_2_5654382963843775677(void) {
    (void) Py_InitModule("myokit_sim_2_5654382963843775677", SimMethods);
}

#endif
