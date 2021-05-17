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
#define PY_SSIZE_T_CLEAN
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
 * Tests building a program and returns the
 *
 * If the program builds successfully, None is returned. If the program fails
 * to compile a string containing the compiler output is returned. If something
 * else goes wrong an exception is raised.
 */
static PyObject*
build(PyObject* self, PyObject* args)
{
    // OpenCL flag
    cl_int flag;

    // OpenCL context
    cl_context context;

    // Platform and device name (Python bytes) and ids
    PyObject *platform_name;
    PyObject *device_name;
    cl_platform_id platform_id;
    cl_device_id device_id;

    // Program and source
    cl_program program;
    PyObject *kernel_source;

    // Compilation error message
    size_t blog_size;
    char *blog;

    // Success?
    int exception = 0;

    // Check input arguments
    if(!PyArg_ParseTuple(args, "OOs", &platform_name, &device_name, &kernel_source)) {
        // Nothing allocated yet, no pyobjects _created_, return directly
        PyErr_SetString(PyExc_Exception, "Wrong number of arguments.");
        return 0;
    }

    // Get platform and device id
    if (mcl_select_device(platform_name, device_name, &platform_id, &device_id)) {
        return 0;
    }

    // Create a context
    if (platform_id != NULL) {
        cl_context_properties context_properties[] = { CL_CONTEXT_PLATFORM, (cl_context_properties)platform_id, 0};
        context = clCreateContext(context_properties, 1, &device_id, NULL, NULL, &flag);
    } else {
        context = clCreateContext(NULL, 1, &device_id, NULL, NULL, &flag);
    }
    if(mcl_flag2("context", flag)) {
        return 0;
    }
    // From this point on, clean up if aborting.

    // Compile the program
    program = clCreateProgramWithSource(context, 1, (const char**)&kernel_source, NULL, &flag);
    if(mcl_flag(flag)) {
        exception = 1;
    } else {

        flag = clBuildProgram(program, 1, &device_id, "", NULL, NULL);
        if((flag == CL_SUCCESS) || (flag == CL_BUILD_PROGRAM_FAILURE)) {
            // Extract build log
            clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, 0, NULL, &blog_size);
            blog = (char*)malloc(blog_size);
            clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, blog_size, blog, NULL);
        } else {
            mcl_flag(flag);
            exception = 1;
        }
    }

    // Clean
    clReleaseProgram(program);
    clReleaseContext(context);

    // Return
    if (exception) {
        return 0;
    } else {
        return PyUnicode_FromStringAndSize(blog, (Py_ssize_t)blog_size);
    }
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
    {"info", info, METH_VARARGS, "Get some information about OpenCL devices."},
    {"build", build, METH_VARARGS, "Try building an OpenCL kernel program."},
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
