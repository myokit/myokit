<?
# cmodel.h
#
# A pype template for a C model class, for use in simulations.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
# Required variables
# -----------------------------------------------------------------------------
# model                 A myokit model
# equations             The ordered equations (grouped by component)
# bound_variables       A dict mapping variables to local (model) names.
# s_dependents          The dependent expressions y in dy/sx (as Name objects)
# s_independents        The independent expressions x in dy/dx (as either Name
#                       objects or InitialValue objects).
# s_output_equations    Equations needed to calculate requested sensitivities
#                       of non-state variables.
# initials              A list of state indices for initial values in
#                       s_independents
# parameters            An ordered dict mapping variables to equations.
# parameter_derived     An ordered dict mapping variables to equations.
# literals              An ordered dict mapping variables to equations.
# literal_derived       An ordered dict mapping variables to equations.
# v                     A variable/expression naming method
# w                     An expression writer
#
import myokit

# Tab
tab = '    '

?>/*
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

    /* Unknown */
    default:
    {
        int i = (int)flag;
        char buffer[1024];
        sprintf(buffer, "CModel error: Unlisted error %d", i);
        PyErr_SetString(PyExc_Exception, buffer);
        break;
    }};
}

/*
 * Memory for model object.
 */
struct Model_Memory {
    /* If this is an ODE model this will be 1, otherwise 0. */
    int is_ode;

    /* If this model has sensitivities this will be 1, otherwise 0. */
    int has_sensitivities;

    /* Bound variables */
    realtype time;
    realtype pace;
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

<?
print('/* Bound variables */')
for var, local in bound_variables.items():
    print('#define ' + v(var) + ' model->' + local)

print('/* States */')
for i, var in enumerate(model.states()):
    print('#define ' + v(var) + ' model->states[' + str(i) + ']')

print('\n/* Derivatives */')
for i, var in enumerate(model.states()):
    print('#define ' + v(var.lhs()) + ' model->derivatives[' + str(i) + ']')

print('\n/* Intermediary variables */')
for i, var in enumerate(model.variables(inter=True, deep=True)):
    print('#define ' + v(var) + ' model->intermediary[' + str(i) + ']')

print('\n/* Parameters */')
for i, var in enumerate(parameters):
    print('#define ' + v(var) + ' model->parameters[' + str(i) + ']')

print('\n/* Parameter-derived */')
for i, var in enumerate(parameter_derived):
    print('#define ' + v(var) + ' model->parameter_derived[' + str(i) + ']')

print('\n/* Literal */')
for i, var in enumerate(literals):
    print('#define ' + v(var) + ' model->literals[' + str(i) + ']')

print('\n/* Literal-derived */')
for i, var in enumerate(literal_derived):
    print('#define ' + v(var) + ' model->literal_derived[' + str(i) + ']')

print('\n/* Sensitivities of the state vectors */')
for i, iexp in enumerate(s_independents):
    print('\n/* Sensitivity with respect to ' + str(iexp) + '*/')
    offset = i * model.count_states()
    for j, var in enumerate(model.states()):
        expr = myokit.PartialDerivative(myokit.Name(var), iexp)
        print('#define ' + v(expr) + ' model->s_states[' + str(offset + j) + ']')

print('\n/* Sensitivities of variables needed to calculate remaining sensitivities */')
i = 0
for eqs in s_output_equations:
    for eq in eqs:
        print('#define ' + v(eq.lhs) + ' model->s_intermediary[' + str(i) + ']')
        i += 1
del(i)

?>

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

<?
for eq in literal_derived.values():
    print(tab + w.eq(eq) + ';')
?>
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

<?
for eq in parameter_derived.values():
    print(tab + w.eq(eq) + ';')
?>
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
Model_SetLiteralVariables(Model model, const realtype* literals)
{
    int i;
    if (model == NULL) return Model_INVALID_MODEL;

    /* Scan for changes */
    i = 0;
    #ifdef Model_CACHING
    if (Model__ValidCache(model)) {
        for (i=0; i<model->n_literals; i++) {
            if (model->literals[i] != literals[i]) {
                break;
            }
        }
    }
    #endif

    /* Update remaining */
    if (i < model->n_literals) {
        for (; i<model->n_literals; i++) {
            model->literals[i] = literals[i];
        }
        #ifdef Model_CACHING
        Model__InvalidateCache(model);
        #endif
        Model_EvaluateLiteralDerivedVariables(model);
        Model_EvaluateParameterDerivedVariables(model);
    }

    return Model_OK;
}

/*
 * Updates the parameter variables to the values given in `parameters`.
 *
 * If any of the values are changed
 *  - the model caches are cleared.
 *  - the parameter-derived variables are recalculated.
 *
 * Arguments
 *  model : The model whose variables to set
 *  parameters : An array of size model->n_parameters
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
    const realtype time, const realtype pace,
    const realtype realtime, const realtype evaluations)
{
    int changed;
    if (model == NULL) return Model_INVALID_MODEL;

    changed = 0;
    if (time != model->time) {
        model->time = time;
        changed = 1;
    }

<?
if model.binding('pace') is not None:
    print(tab + 'if (pace != model->pace) {')
    print(tab + '    model->pace = pace;')
    print(tab + '    changed = 1;')
    print(tab + '}')
?>
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
 * Updates the state variables to the values given in `states`.
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

<?
for label, eqs in equations.items():
    need_label = True
    for eq in eqs.equations(const=False, bound=False):
        var = eq.lhs.var()

        # Print label for component
        if need_label:
            print(tab + '/* ' + label + ' */')
            need_label = False

        # Print equation
        print(tab + w.eq(eq) + ';')

    if not need_label:
        print(tab)
?>
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

<?
for eqs in s_output_equations:
    for i, eq in enumerate(eqs):
        if i == 0:
            print(tab + '/* Sensitivity w.r.t. ' + eq.lhs.independent_expression().code() + ' */')
        print(tab + w.eq(eq) + ';')
    print('')
?>
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
    PyObject* log_dict, int i, const char* name, const realtype* var)
{
    int added = 0;
    PyObject* key = PyUnicode_FromString(name);     /* TODO: Remove double lookup */
    if (PyDict_Contains(log_dict, key)) {
        model->_log_lists[i] = PyDict_GetItem(log_dict, key);
        model->_log_vars[i] = (realtype*)var;
        added = 1;
    }
    Py_DECREF(key);
    return added;
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
<?
for var in model.states():
    print(tab + 'i += Model__AddVariableToLog(model, log_dict, i, "' + var.qname() + '", &' + v(var)  + ');')
?>
    model->logging_states = (i > 0);

    /* Check derivatives */
    j = i;
<?
for var in model.states():
    print(tab + 'i += Model__AddVariableToLog(model, log_dict, i, "dot(' + var.qname() + ')", &' + v(var.lhs())  + ');')
?>
    model->logging_derivatives = (i != j);

    /* Check bound variables */
    j = i;
<?
for var in bound_variables:
    print(tab + 'i += Model__AddVariableToLog(model, log_dict, i, "' + var.qname() + '", &' + v(var)  + ');')
?>
    model->logging_bound = (i != j);

    /* Check intermediary variables */
    j = i;
<?
for var in model.variables(deep=True, state=False, bound=False, const=False):
    print(tab + 'i += Model__AddVariableToLog(model, log_dict, i, "' + var.qname() + '", &' + v(var)  + ');')
?>
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
<?
for i, e1 in enumerate(s_dependents):
    var = e1.var()
    print('')
    print(tab + 'l2 = PyTuple_New(model->ns_independents);')
    print(tab + 'if (l2 == NULL) goto nomem;')
    for j, e2 in enumerate(s_independents):
        pd = myokit.PartialDerivative(e1, e2)
        print(tab + 'val = PyFloat_FromDouble(' + v(pd) + ');')
        print(tab + 'if (val == NULL) goto nomem;')
        print(tab + 'PyTuple_SetItem(l2, ' + str(j) + ', val);')
    print(tab + 'PyTuple_SetItem(l1, ' + str(i) + ', l2);')
    print(tab + 'l2 = NULL; val = NULL;')
?>

    /* Add matrix to list (must be a PyList, no advantage here to using a
       buffer). */
    flag = PyList_Append(list, l1);
    Py_DECREF(l1);
    if (flag < 0) return Model_SENSITIVITY_LOG_APPEND_FAILED;

    return Model_OK;

nomem:
    /* l2 is either NULL or has a single reference to it in l1, so decreffing
       l1 should be enough. */
    /* Assuming val is NULL or has had its reference stolen. */
    Py_XDECREF(l1);
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
    model->is_ode = <?= 1 if model.count_states() > 0 else 0 ?>;
    model->has_sensitivities = <?= 1 if s_independents else 0 ?>;

    /*
     * Variables
     */

    /* States and derivatives */
    model->n_states = <?= model.count_states() ?>;
    model->states = (realtype*)malloc(model->n_states * sizeof(realtype));
    model->derivatives = (realtype*)malloc(model->n_states * sizeof(realtype));

    /* Intermediary variables */
    model->n_intermediary = <?= model.count_variables(inter=True, deep=True) ?>;
    model->intermediary = (realtype*)malloc(model->n_intermediary * sizeof(realtype));

    /* Parameters */
    model->n_parameters = <?= len(parameters) ?>;
    model->n_parameter_derived = <?= len(parameter_derived) ?>;
    model->parameters = (realtype*)malloc(model->n_parameters * sizeof(realtype));
    model->parameter_derived = (realtype*)malloc(model->n_parameter_derived * sizeof(realtype));

    /* Literals */
    model->n_literals = <?= len(literals) ?>;
    model->n_literal_derived = <?= len(literal_derived) ?>;
    model->literals = (realtype*)malloc(model->n_literals * sizeof(realtype));
    model->literal_derived = (realtype*)malloc(model->n_literal_derived * sizeof(realtype));

    /*
     * Sensitivities
     */

    /* Total number of dependents to output sensitivities of */
    model->ns_dependents = <?= len(s_dependents) ?>;

    /* Total number of independent to calculate sensitivities w.r.t. */
    model->ns_independents = <?= len(s_independents) ?>;

    /* Pointers to independent variables */
    /* Note that, for sensitivities w.r.t. initial values, the entry in this
       list points to the _current_, not the initial value. */
    model->s_independents = (realtype**)malloc(model->ns_independents * sizeof(realtype));
<?
for i, expr in enumerate(s_independents):
    print(tab + 'model->s_independents[' + str(i) + '] = &' + v(expr.var()) + ';')
?>
    /* Type of independents (1 for parameter, 0 for initial) */
    model->s_is_parameter = (int*)malloc(model->ns_independents * sizeof(int));
<?
for i, expr in enumerate(s_independents):
    print(tab + 'model->s_is_parameter[' + str(i) + '] = ' + str(1 if isinstance(expr, myokit.Name) else 0) + ';')
?>
    /* Sensitivities of state variables */
    model->s_states = (realtype*)malloc(model->n_states * model->ns_independents * sizeof(realtype));

    /* Sensitivities of intermediary variables needed in calculations */
    model->ns_intermediary = <?= sum(len(x) for x in s_output_equations) ?>;
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
    model->pace = 0;
    model->realtime = 0;
    model->evaluations = 0;

    /* Literal values */
<?
for eq in literals.values():
    print(tab + w.eq(eq) + ';')
?>
    flag = Model_EvaluateLiteralDerivedVariables(model);
    if (flag != Model_OK) {
        if (flagp != NULL) { *flagp = flag; }
        return NULL;
    }

    /* Parameter values */
<?
for eq in parameters.values():
    print(tab + w.eq(eq) + ';')
?>
    flag = Model_EvaluateParameterDerivedVariables(model);
    if (flag != Model_OK) {
        if (flagp != NULL) { *flagp = flag; }
        return NULL;
    }

    /* States */
<?
for var in model.states():
    print(tab + v(var) + ' = ' + myokit.float.str(var.state_value()) + ';')
?>
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

