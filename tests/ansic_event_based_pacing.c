<?
# _ansic_pacing.c
#
# Python-callable test code for pacing.h
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

// Input arguments
PyObject* protocol;

// Pacing
ESys pacing;
double t;
double TMAX = 1e50;


/*
 * De-initializes the pacing mechanism.
 */
static PyObject*
pacing_clean()
{
    if (initialized != 0) {

        // Free pacing system space
        ESys_Destroy(pacing); pacing = NULL;
    }

    // Return 0, allowing the construct
    //  PyErr_SetString(PyExc_Exception, "Oh noes!");
    //  return pacing_clean()
    // to terminate a python function.
    return 0;
}
static PyObject*
py_pacing_clean(PyObject *self, PyObject *args)
{
    pacing_clean();
    Py_RETURN_NONE;
}


/*
 * Initialize the pacing mechanism.
 */
static PyObject*
pacing_init(PyObject *self, PyObject *args)
{
    ESys_Flag flag;

    // Check if already initialized
    if (initialized != 0) {
        PyErr_SetString(PyExc_Exception, "Pacing system already initialized.");
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

    // Set initial time
    t = 0;

    // Set up pacing
    pacing = ESys_Create(&flag);
    if (flag!=ESys_OK) { ESys_SetPyErr(flag); return pacing_clean(); }
    flag = ESys_Populate(pacing, protocol);
    if (flag!=ESys_OK) { ESys_SetPyErr(flag); return pacing_clean(); }

    // Done!
    Py_RETURN_NONE;
}

/*
 * Return the current time
 */
static PyObject*
pacing_time(PyObject *self, PyObject *args)
{
    return PyFloat_FromDouble(t);
}

/*
 * Return the current value of the pacing variable.
 */
static PyObject*
pacing_pace(PyObject *self, PyObject *args)
{
    ESys_Flag flag;
    double pace;
    pace = ESys_GetLevel(pacing, &flag);
    if (flag!=ESys_OK) { ESys_SetPyErr(flag); return pacing_clean(); }
    return PyFloat_FromDouble(pace);
}

/*
 * Return the time of the next pacing event.
 */
static PyObject*
pacing_next_time(PyObject *self, PyObject *args)
{
    ESys_Flag flag;
    double tnext;
    tnext = ESys_GetNextTime(pacing, &flag);
    if (flag!=ESys_OK) { ESys_SetPyErr(flag); return pacing_clean(); }
    return PyFloat_FromDouble(tnext);
}

/*
 * Advance the pacing mechanism to the given point in time.
 *
 * Returns the current value of the pacing variable
 */
static PyObject*
pacing_advance(PyObject *self, PyObject *args)
{
    double tadvance;
    double maxtime;   
    ESys_Flag flag;
    double pace;

    // Check input arguments
    if (!PyArg_ParseTuple(args, "dd", &tadvance, &maxtime)) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        // Nothing allocated yet, no pyobjects _created_, return directly
        return 0;
    }

    // Advance
    flag = ESys_AdvanceTime(pacing, tadvance, maxtime);
    if (flag!=ESys_OK) { ESys_SetPyErr(flag); return pacing_clean(); }
    t = tadvance;

    // Get new pacing value
    pace = ESys_GetLevel(pacing, &flag);
    if (flag!=ESys_OK) { ESys_SetPyErr(flag); return pacing_clean(); }

    return PyFloat_FromDouble(pace);
}

/*
 * Methods in this module
 */
static PyMethodDef PacingMethods[] = {
    {"init", pacing_init, METH_VARARGS, "Initialize the pacing mechanism."},
    {"time", pacing_time, METH_VARARGS, "Return the current time in the pacing system."},
    {"pace", pacing_pace, METH_VARARGS, "Returns the current value of the pacing variable."},
    {"next_time", pacing_next_time, METH_VARARGS, "Return the time of the next pacing event."},
    {"advance", pacing_advance, METH_VARARGS, "Advance the pacing mechanism to the given point in time."},
    {"clean", py_pacing_clean, METH_VARARGS, "De-initializes the pacing mechanism."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Event based pacing test",  /* m_doc */
        -1,                         /* m_size */
        PacingMethods,              /* m_methods */
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
        (void) Py_InitModule("<?= module_name ?>", PacingMethods);
    }

#endif
