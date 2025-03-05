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

<?
if myokit.DEBUG_SM:
    print('// Show debug output')
    print('#ifndef MYOKIT_DEBUG_MESSAGES')
    print('#define MYOKIT_DEBUG_MESSAGES')
    print('#endif')
?>

#include "mcl.h"

/*
 * Returns a tuple with information about the available OpenCL platforms and
 * devices.
 */
static PyObject*
info(PyObject *self, PyObject *args)
{
    return mcl_info();
}


/*
 * Returns a tuple with information about the selected OpenCL platform and
 * device.
 */
static PyObject*
current(PyObject* self, PyObject* args)
{
    // Platform and device name (Python bytes)
    PyObject *platform_name;
    PyObject *device_name;

    // Check input arguments
    if(!PyArg_ParseTuple(args, "OO", &platform_name, &device_name)) {
        // Nothing allocated yet, no pyobjects _created_, return directly
        PyErr_SetString(PyExc_Exception, "Wrong number of arguments.");
        return 0;
    }

    return mcl_info_current(platform_name, device_name);
}

/*
 * Tests building a program and returns the output.
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
    {"build", build, METH_VARARGS, "Try building an OpenCL kernel program."},
    {"current", current, METH_VARARGS, "Get information about the currently selected OpenCL platform and device."},
    {"info", info, METH_NOARGS, "Get information about available OpenCL platforms and devices."},
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
