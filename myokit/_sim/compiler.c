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
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#

?>
#include <Python.h>

/*
 * Returns None.
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
        sprintf(str, "Microsoft Visual Studio %d", _MSC_VER);
        /*
        Version     _MSC_VER        _MSC_FULL_VER
        1.0 	800
        3.0 	900
        4.0 	1000
        4.2 	1020
        5.0 	1100
        6.0 	1200
        6.0 SP6 	1200 	12008804
        7.0 	1300 	13009466
        7.1 (2003) 	1310 	13103077
        8.0 (2005) 	1400 	140050727
        9.0 (2008) 	1500 	150021022
        9.0 SP1 	1500 	150030729
        10.0 (2010) 	1600 	160030319
        10.0 (2010) SP1 	1600 	160040219
        11.0 (2012) 	1700 	170050727
        12.0 (2013) 	1800 	180021005
        14.0 (2015) 	1900 	190023026
        14.0 (2015 Update 1) 	1900 	190023506
        14.0 (2015 Update 2) 	1900 	190023918
        14.0 (2015 Update 3) 	1900 	190024210
        15.0 (2017) 	1910 	191025017
        */
    #elif defined __MINGW64__
        sprintf(str, "MinGW-w64 64 bit");
    #elif defined __MINGW32__
        sprintf(str, "MinGW 32 bit");
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
    {"compiler", compiler, METH_VARARGS, "Return None."},
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
