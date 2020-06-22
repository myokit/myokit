<?
# opencl_info.c
#
# A pype template for an opencl information object
#
# Required variables
# -----------------------------------------------------------------------------
# module_name       A module name
# -----------------------------------------------------------------------------
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit
import myokit.formats.opencl as opencl

tab = '    '
?>
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include "mcl.h"

/*
 * Returns a tuple with information about the available opencl platforms and
 * devices.
 */
static PyObject*
info(PyObject *self, PyObject *args)
{
    mcl_device_info();
    return mcl_device_info();
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
    {"info", info, METH_VARARGS, "Get some information about OpenCL devices."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Generated OpenCL info module",   /* m_doc */
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
