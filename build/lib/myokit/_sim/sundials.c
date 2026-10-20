<?
# sundials.c
#
# A pype template to test for Sundials support.
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
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <sundials/sundials_config.h>

/*
 * Returns the detected sundials version.
 */
static PyObject*
sundials_version(PyObject *self, PyObject *args)
{
    #ifdef SUNDIALS_PACKAGE_VERSION
    return PyUnicode_FromString(SUNDIALS_PACKAGE_VERSION);
    #else
    return PyUnicode_FromString(SUNDIALS_VERSION);
    #endif
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
    {"sundials_version", sundials_version, METH_VARARGS, "Return the detected sundials version."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Generated Sundials module",/* m_doc */
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
