<?
# compiler.c
#
# A pype template to test C compilation and give some rough idea of which
# compiler is being used.
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

/*
 * Returns the detected compiler.
 */
static PyObject*
compiler(PyObject *self, PyObject *args)
{
    char str[4096];

    #if defined __apple_build_version__
        sprintf(str, "Clang (Apple LLVM) %d.%d.%d", __clang_major__, __clang_minor__, __clang_patchlevel__);
    #elif defined __clang__
        sprintf(str, "Clang %d.%d.%d", __clang_major__, __clang_minor__, __clang_patchlevel__);
    #elif defined _MSC_VER
        #if _MSC_VER >= 1910
            sprintf(str, "Microsoft Visual Studio 15.0 (2017) - %d", _MSC_FULL_VER);
        #elif _MSC_VER >= 1900
            sprintf(str, "Microsoft Visual Studio 14.0 (2015) - %d", _MSC_FULL_VER);
        #elif _MSC_VER >= 1800
            sprintf(str, "Microsoft Visual Studio 12.0 (2013) - %d", _MSC_FULL_VER);
        #elif _MSC_VER >= 1700
            sprintf(str, "Microsoft Visual Studio 11.0 (2012) - %d", _MSC_FULL_VER);
        #elif _MSC_VER >= 1600
            sprintf(str, "Microsoft Visual Studio 10.0 (2010) - %d", _MSC_FULL_VER);
        #elif _MSC_VER >= 1500
            sprintf(str, "Microsoft Visual Studio 9.0 (2008) - %d", _MSC_FULL_VER);
        #elif _MSC_VER >= 1400
            sprintf(str, "Microsoft Visual Studio 8.0 (2005) - %d", _MSC_FULL_VER);
        #elif _MSC_VER >= 1310
            sprintf(str, "Microsoft Visual Studio 7.1 (2003) - %d", _MSC_FULL_VER);
        #elif _MSC_VER >= 1300
            sprintf(str, "Microsoft Visual Studio 7.0 - %d", _MSC_FULL_VER);
        #elif _MSC_VER >= 1200
            sprintf(str, "Microsoft Visual Studio 6.0 : %d", _MSC_VER);
        #elif _MSC_VER >= 1100
            sprintf(str, "Microsoft Visual Studio 5.0 : %d", _MSC_VER);
        #elif _MSC_VER >= 1020
            sprintf(str, "Microsoft Visual Studio 4.2 : %d", _MSC_VER);
        #elif _MSC_VER >= 1000
            sprintf(str, "Microsoft Visual Studio 4.0 : %d", _MSC_VER);
        #elif _MSC_VER >= 900
            sprintf(str, "Microsoft Visual Studio 3.0 : %d", _MSC_VER);
        #elif _MSC_VER >= 800
            sprintf(str, "Microsoft Visual Studio 1.0 : %d", _MSC_VER);
        #else
            sprintf(str, "Microsoft Visual Studio : %d", _MSC_VER);
        #endif
    #elif defined __MINGW64__
        sprintf(str, "MinGW-w64 64 bit");
    #elif defined __MINGW32__
        sprintf(str, "MinGW 32 bit");
    #elif defined __GNUC_PATCHLEVEL__
        sprintf(str, "GCC %d.%d.%d", __GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__);
    #elif defined __GNUC__
        sprintf(str, "GCC %d.%d", __GNUC__, __GNUC_MINOR__);
    #else
        sprintf(str, "Unknown C compiler");
    #endif

    return PyUnicode_FromString(str);
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
    {"compiler", compiler, METH_VARARGS, "Return the detected compiler."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Generated Compiler module",/* m_doc */
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
