<?
#
# Python-callable test code for C-based time-series pacing.
#
# Required variables
# -----------------------------------------------------------------------------
# module_name A module name
# -----------------------------------------------------------------------------
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
?>
#include <Python.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "pacing.h"

// Initialized yes/no
int initialized = 0;

// TIme-series pacing system
TSys pacing;

/*
 * De-initializes the time series pacing mechanism.
 */
static PyObject*
tpacing_clean()
{
    if (initialized != 0) {
        // Free time series pacing system space
        TSys_Destroy(pacing); pacing = NULL;
    }

    // Return 0, allowing the construct
    //  PyErr_SetString(PyExc_Exception, "Oh noes!");
    //  return tpacing_clean()
    // to terminate a python function.
    return 0;
}
static PyObject*
py_tpacing_clean(PyObject *self, PyObject *args)
{
    tpacing_clean();
    Py_RETURN_NONE;
}


/*
 * Initialize the time series pacing mechanism.
 */
static PyObject*
tpacing_init(PyObject *self, PyObject *args)
{
    // Input arguments
    PyObject* protocol;

    TSys_Flag flag;

    // Check if already initialized
    if (initialized != 0) {
        PyErr_SetString(PyExc_Exception, "Time series pacing system already initialized.");
        return 0;
    }

    // Set all pointers used in pacing_clean to null
    pacing = NULL;

    // Check input arguments
    if (!PyArg_ParseTuple(args, "O", &protocol)) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        // Nothing allocated yet, no pyobjects _created_, return directly
        return 0;
    }

    // Now officialy running :)
    initialized = 1;

    // From this point on, no more direct returning! Use pacing_clean()

    // Set up time series pacing
    pacing = TSys_Create(&flag);
    if (flag != TSys_OK) { TSys_SetPyErr(flag); return tpacing_clean(); }
    flag = TSys_Populate(pacing, protocol);
    if (flag != TSys_OK) { TSys_SetPyErr(flag); return tpacing_clean(); }

    // Done!
    Py_RETURN_NONE;
}

/*
 * Return the value of the pacing variable at a given time
 */
static PyObject*
tpacing_pace(PyObject *self, PyObject *args)
{
    TSys_Flag flag;
    double time;
    double pace;

    // Check input arguments
    if (!PyArg_ParseTuple(args, "d", &time)) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        // Nothing allocated yet, no pyobjects _created_, return directly
        return 0;
    }

    pace = TSys_GetLevel(pacing, time, &flag);
    if (flag != TSys_OK) { TSys_SetPyErr(flag); return tpacing_clean(); }
    return PyFloat_FromDouble(pace);
}

/*
 * Methods in this module
 */
static PyMethodDef TPacingMethods[] = {
    {"init", tpacing_init, METH_VARARGS, "Initialize the time series pacing mechanism."},
    {"pace", tpacing_pace, METH_VARARGS, "Returns the value of the pacing variable at time t."},
    {"clean", py_tpacing_clean, METH_VARARGS, "De-initializes the time series pacing mechanism."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Time series pacing test",   /* m_doc */
        -1,                         /* m_size */
        TPacingMethods,             /* m_methods */
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
        (void) Py_InitModule("<?= module_name ?>", TPacingMethods);
    }

#endif
