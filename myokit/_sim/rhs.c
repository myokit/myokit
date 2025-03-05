<?
# rhsbenchmarker.c
#
# Used to benchmark the speed of a full or partial RHS evaluation.
#
# Required variables
# -----------------------------------------------------------------------------
# module_name      A module name
# model            A myokit model
# variables        A list of variables to test separately
# exclude_selected When False (default) the given variables will be the only
#                  ones tested with bench_part. When True, the given variables
#                  will be the only ones _not_ tested with bench_part.
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
        return 'DY_' + var.var().uname()
    # Name given? get variable object from name
    if isinstance(var, myokit.Name):
        var = var.var()
    # Handle states
    if var.is_state():
        return 'SY_' + var.uname()
    # Handle constants and intermediary variables
    if var.is_constant():
        return 'AC_' + var.uname()
    else:
        return 'AV_' + var.uname()
w.set_lhs_function(v)

# Tab
tab = '    '

# Process bindings, remove unsupported bindings, get map of bound variables to
# internal names
bound_variables = myokit._prepare_bindings(model, {
    'time' : 'engine_time',
})

# Get equations
equations = model.solvable_order()
?>
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>
#include <math.h>
#include <string.h>

/* Declare variables */
static double engine_time = 0;
<?
for var in model.variables(deep=True):
    if var.is_literal():
        print('static double ' + v(var) + ' = ' + myokit.float.str(var.rhs().eval()) + ';')
    else:
        print('static double ' + v(var) + ';')
        if var.is_state():
            print('static double ' + v(var.lhs()) + ';')
?>

/* Set values of calculated constants */
static void
updateConstants(void)
{
<?
for label, eqs in equations.items():
    for eq in eqs.equations(const=True):
        if not eq.rhs.is_literal():
            print(tab + w.eq(eq) + ';')
?>}

/* Full right-hand-side  */
static void
rhs(void)
{
<?
for label, eqs in equations.items():
    if eqs.has_equations(const=False):
        print(tab + '/* ' + label + ' */')
        for eq in eqs.equations(const=False):
            var = eq.lhs.var()
            if var in bound_variables:
                print(tab + v(var) + ' = ' + bound_variables[var] + ';')
            else:
                print(tab + w.eq(eq) + ';')
        print(tab)
?>
}

// Partial right-hand-side
static void
partial_rhs(void)
{
<?
for label, eqs in equations.items():
    first = True
    for eq in eqs.equations(const=False):
        var = eq.lhs.var()
        inc = var in variables
        if exclude_selected: inc = not inc
        if inc:
            if first:
                print(tab + '/* ' + label + ' */')
                first = False
            # Bound or constant variables can't be selected
            print(tab + w.eq(eq) + ';')
    if not first:
        print(tab)
?>
}

/*
 * Extracts a variable from the log.
 * Returns 0 and sets the exception string if an error occurs.
 */
static int
log_extract(PyObject* data, const char* name, const int position, double* var)
{
    PyObject* key;
    PyObject* list;
    PyObject* item;

    // Get sequence from dict
    key = PyUnicode_FromString(name);
    if (!PyDict_Contains(data, key)) {
        Py_DECREF(key);
        PyErr_Format(PyExc_Exception, "Variable %s not found in log.", name);
        return 0;
    }
    list = PyDict_GetItem(data, key); // Borrowed ref, don't decref
    Py_DECREF(key);

    // Get float from sequence
    key = PyLong_FromLong(position);
    item = PySequence_GetItem(list, position); // New reference, decref
    if (item == NULL) {
        Py_DECREF(key);
        PyErr_Format(PyExc_Exception, "No item found at position %i of log for %s.", position, name);
        return 0;
    }
    Py_DECREF(key);

    // Get double from float
    if (!PyFloat_Check(item)) {
        Py_XDECREF(item);
        PyErr_Format(PyExc_Exception, "Log for %s can only contain floats (error at index %i).", name, position);
        return 0;
    }

    // Assign value to variable
    *var = PyFloat_AsDouble(item);

    // Decrease reference count of float object
    Py_DECREF(item);

    // Success!
    return 1;
}

/*
 * Sets all state and bound variables to the values found in the provided log.
 */
static int
set_state_and_bound(PyObject* data, const int position)
{
<?
# For state variables, point to y_log
for var in model.states():
    print(tab + 'if (log_extract(data, "' + var.qname() + '", position, &' + v(var)  + ') == 0) return 0;')
for var in bound_variables:
    print(tab + 'if (log_extract(data, "' + var.qname() + '", position, &' + v(var)  + ') == 0) return 0;')
?>
    return 1;
}

/*
 * Benchmarks the given function.
 */
static PyObject*
bench(PyObject* self, PyObject* args, void (*fnc)(void))
{
    PyObject* bench;    // The benchmarking function to call
    PyObject* data;     // The dictionary of log positions
    int start;          // The first position to use
    int stop;           // The last position to use + 1
    int repeats;        // The number of evaluations to run
    int fastest;        // Set to 1 to get the fastest repeat, 0 for the sum
                        // of repeats.
    int n_positions;
    int ok;
    int i, j, k;
    PyObject* times;

    PyObject* f1;  // Re-usable float objects
    PyObject* f2;
    double time_difference;

    // Check input arguments
    if (!PyArg_ParseTuple(args, "OOiiii",
            &bench,
            &data,
            &start,
            &stop,
            &repeats,
            &fastest)) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }

    // Set calculated constants
    updateConstants();

    // Test benchmarking function
    f1 = PyObject_CallFunction(bench, "");
    if (!PyFloat_Check(f1)) {
        Py_XDECREF(f1);
        PyErr_SetString(PyExc_Exception, "Call to benchmark time function didn't return float.");
        return 0;
    }
    Py_DECREF(f1); f1 = NULL;

    // Test given times
    n_positions = stop - start;
    if (n_positions < 1) {
        PyErr_SetString(PyExc_Exception, "Invalid log position selection: At least 1 position in the logs must be checked.");
        return 0;
    }
    if (start < 0) {
        PyErr_SetString(PyExc_Exception, "Invalid log position selection: Negative list index given.");
        return 0;
    }

    //
    // ALLOCATING MEMORY, FROM THIS POINT ON, USE GOTO ERROR INSTEAD OF RETURN 0
    //
    // Create list for logged results
    ok = 0;
    times = PyList_New(n_positions);

    // Dummy run on first position. Without doing this, the first run always
    // takes longer than the others...
    if (set_state_and_bound(data, start) == 0) goto error;
    rhs();
    for(j = 0; j<repeats; j++) {
        fnc();
    }

    // Loop through selected positions in log
    for(i=0; i<n_positions; i++) {

        // Update state and bound variables to given log position
        if (set_state_and_bound(data, start + i) == 0) goto error;

        /* Call rhs to set remaining variables */
        rhs();

        /* Benchmark function */
        if (fastest) {
            // Save only fastest run
            int n_hidden = 50;
            double t;
            double f = 1.0 / (double)n_hidden;
            f1 = PyObject_CallFunction(bench, "");
            for (k=0; k<n_hidden; k++) {
                fnc();
            }
            f2 = PyObject_CallFunction(bench, "");
            time_difference = f * (PyFloat_AsDouble(f2) - PyFloat_AsDouble(f1));
            Py_DECREF(f1); f1 = NULL;
            Py_DECREF(f2); f2 = NULL;
            for(j=0; j<repeats; j++) {
                f1 = PyObject_CallFunction(bench, "");
                for (k=0; k<n_hidden; k++) {
                    fnc();
                }
                f2 = PyObject_CallFunction(bench, "");
                t = f * (PyFloat_AsDouble(f2) - PyFloat_AsDouble(f1));
                Py_DECREF(f1);
                Py_DECREF(f2);
                if (t < time_difference) { time_difference = t; }
            }
            f1 = f2 = NULL;
        } else {
            // Average over all runs
            double f = 1.0 / (double)repeats;
            f1 = PyObject_CallFunction(bench, "");
            for(j = 0; j<repeats; j++) {
                fnc();
            }
            f2 = PyObject_CallFunction(bench, "");
            time_difference = f * (PyFloat_AsDouble(f2) - PyFloat_AsDouble(f1));
            Py_DECREF(f1);
            Py_DECREF(f2);
            f1 = f2 = NULL;
        }

        // Store time difference in list
        // Steals ref, so no decreffing is needed!
        PyList_SetItem(times, start + i, PyFloat_FromDouble(time_difference));
    }

    ok = 1;
error:
    if (ok) {
        // Return logged times
        // This passes ownership of the reference to times, so no decref is needed.
        return times;
    } else {
        // Discard times array if created
        Py_XDECREF(times);
        // Return none
        Py_RETURN_NONE;
    }
}

/*
 * Runs a full benchmark
 *
 */
static PyObject*
bench_full(PyObject* self, PyObject* args)
{
    return bench(self, args, rhs);
}
/*
 * Runs a partial benchmark
 *
 */
static PyObject*
bench_part(PyObject* self, PyObject* args)
{
    return bench(self, args, partial_rhs);
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
    {"bench_full", bench_full, METH_VARARGS, "Runs a full benchmark."},
    {"bench_part", bench_part, METH_VARARGS, "Runs a partial benchmark."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Generated RHS Benchmarker module",   /* m_doc */
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
