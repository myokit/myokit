<?
# _ansic_pacing_fixed_form.c
#
# Python-callable test code for ansi-c fixed-form pacing.
#
# Required variables
# -----------------------------------------------------------------------------
# module_name A module name
# -----------------------------------------------------------------------------
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
?>
#include <Python.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "pacing.h"

// Initialized yes/no
int initialized = 0;

// Fixed-form pacing system
FSys pacing;

/*
 * De-initializes the fixed-form pacing mechanism.
 */
static PyObject*
fpacing_clean()
{
    if (initialized != 0) {
        // Free fixed-form pacing system space
        FSys_Destroy(pacing); pacing = NULL;
    }

    // Return 0, allowing the construct
    //  PyErr_SetString(PyExc_Exception, "Oh noes!");
    //  return fpacing_clean()
    // to terminate a python function.
    return 0;
}
static PyObject*
py_fpacing_clean(PyObject *self, PyObject *args)
{
    fpacing_clean();
    Py_RETURN_NONE;
}


/*
 * Initialize the fixed-form pacing mechanism.
 */
static PyObject*
fpacing_init(PyObject *self, PyObject *args)
{
    // Input arguments
    PyObject* times;
    PyObject* values;

    FSys_Flag flag;

    // Check if already initialized
    if (initialized != 0) {
        PyErr_SetString(PyExc_Exception, "Fixed-form pacing system already initialized.");
        return 0;
    }

    // Set all pointers used in pacing_clean to null
    pacing = NULL;

    // Check input arguments
    if (!PyArg_ParseTuple(args, "OO", &times, &values)) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        // Nothing allocated yet, no pyobjects _created_, return directly
        return 0;
    }

    // Now officialy running :)
    initialized = 1;

    // From this point on, no more direct returning! Use pacing_clean()

    // Set up fixed-form pacing
    pacing = FSys_Create(&flag);
    if (flag != FSys_OK) { FSys_SetPyErr(flag); return fpacing_clean(); }
    flag = FSys_Populate(pacing, times, values);
    if (flag != FSys_OK) { FSys_SetPyErr(flag); return fpacing_clean(); }

    // Done!
    Py_RETURN_NONE;
}

/*
 * Return the value of the pacing variable at a given time
 */
static PyObject*
fpacing_pace(PyObject *self, PyObject *args)
{
    FSys_Flag flag;
    double time;
    double pace;

    // Check input arguments
    if (!PyArg_ParseTuple(args, "d", &time)) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        // Nothing allocated yet, no pyobjects _created_, return directly
        return 0;
    }

    pace = FSys_GetLevel(pacing, time, &flag);
    if (flag != FSys_OK) { FSys_SetPyErr(flag); return fpacing_clean(); }
    return PyFloat_FromDouble(pace);
}

/*
 * Methods in this module
 */
static PyMethodDef FPacingMethods[] = {
    {"init", fpacing_init, METH_VARARGS, "Initialize the fixed-form pacing mechanism."},
    {"pace", fpacing_pace, METH_VARARGS, "Returns the value of the pacing variable at time t."},
    {"clean", py_fpacing_clean, METH_VARARGS, "De-initializes the fixed-form pacing mechanism."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Fixed-form pacing test",   /* m_doc */
        -1,                         /* m_size */
        FPacingMethods,             /* m_methods */
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
        (void) Py_InitModule("<?= module_name ?>", FPacingMethods);
    }

#endif
