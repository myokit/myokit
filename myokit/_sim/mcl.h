/*
 * mcl.h
 *
 * Implements a number of OpenCL utility functions.
 *
 * This file is part of Myokit.
 * See http://myokit.org for copyright, sharing, and licensing details.
 *
 * The string functions rtrim, ltrim and trim were taken from Wikipedia and
 * are not part of Myokit.
 *
 */
#ifndef MyokitOpenCL
#define MyokitOpenCL

#include <Python.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

// Load the opencl libraries.
#ifdef __APPLE__
#include <OpenCL/cl.h>
#else
#include <CL/cl.h>
#endif

// Show debug output
//#define MYOKIT_DEBUG

// Maximum number of platforms/devices to check for.
#define MCL_MAX_PLATFORMS 255
#define MCL_MAX_DEVICES 255

/*
 * String functions, straight from Wikipedia
 * https://en.wikipedia.org/wiki/Trimming_%28computer_programming%29#C.2FC.2B.2B
 */
void rtrim(char *str)
{
  size_t n;
  n = strlen(str);
  while (n > 0 && isspace((unsigned char)str[n - 1])) {
    n--;
  }
  str[n] = '\0';
}
void ltrim(char *str)
{
  size_t n;
  n = 0;
  while (str[n] != '\0' && isspace((unsigned char)str[n])) {
    n++;
  }
  memmove(str, str + n, strlen(str) - n + 1);
}
void trim(char *str)
{
  rtrim(str);
  ltrim(str);
}

/*
 * Checks the given flag for an opencl error, returns 1 if found and sets the
 * error message, else, returns 0.
 *
 * An extra note about the error can be passed in as msg.
 */
static int
mcl_flag2(const char* msg, const cl_int flag)
{
    char sub[1024];
    char err[2048];

    if(flag == CL_SUCCESS) {
        return 0;
    }

    if(strcmp(msg, "")) {
        sprintf(sub, " (%s)", msg);
    } else {
        sprintf(sub, "");
    }

    switch(flag) {
        case CL_DEVICE_NOT_FOUND:
            sprintf(err, "OpenCL error%s: CL_DEVICE_NOT_FOUND", sub);
            break;
        case CL_DEVICE_NOT_AVAILABLE:
            sprintf(err, "OpenCL error%s: CL_DEVICE_NOT_AVAILABLE", sub);
            break;
        case CL_COMPILER_NOT_AVAILABLE:
            sprintf(err, "OpenCL error%s: CL_COMPILER_NOT_AVAILABLE", sub);
            break;
        case CL_MEM_OBJECT_ALLOCATION_FAILURE:
            sprintf(err, "OpenCL error%s: CL_MEM_OBJECT_ALLOCATION_FAILURE", sub);
            break;
        case CL_OUT_OF_RESOURCES:
            sprintf(err, "OpenCL error%s: CL_OUT_OF_RESOURCES", sub);
            break;
        case CL_OUT_OF_HOST_MEMORY:
            sprintf(err, "OpenCL error%s: CL_OUT_OF_HOST_MEMORY", sub);
            break;
        case CL_PROFILING_INFO_NOT_AVAILABLE:
            sprintf(err, "OpenCL error%s: CL_PROFILING_INFO_NOT_AVAILABLE", sub);
            break;
        case CL_MEM_COPY_OVERLAP:
            sprintf(err, "OpenCL error%s: CL_MEM_COPY_OVERLAP", sub);
            break;
        case CL_IMAGE_FORMAT_MISMATCH:
            sprintf(err, "OpenCL error%s: CL_IMAGE_FORMAT_MISMATCH", sub);
            break;
        case CL_IMAGE_FORMAT_NOT_SUPPORTED:
            sprintf(err, "OpenCL error%s: CL_IMAGE_FORMAT_NOT_SUPPORTED", sub);
            break;
        case CL_BUILD_PROGRAM_FAILURE:
            sprintf(err, "OpenCL error%s: CL_BUILD_PROGRAM_FAILURE", sub);
            break;
        case CL_MAP_FAILURE:
            sprintf(err, "OpenCL error%s: CL_MAP_FAILURE", sub);
            break;
        case CL_MISALIGNED_SUB_BUFFER_OFFSET:
            sprintf(err, "OpenCL error%s: CL_MISALIGNED_SUB_BUFFER_OFFSET", sub);
            break;
        case CL_EXEC_STATUS_ERROR_FOR_EVENTS_IN_WAIT_LIST:
            sprintf(err, "OpenCL error%s: CL_EXEC_STATUS_ERROR_FOR_EVENTS_IN_WAIT_LIST", sub);
            break;
        case CL_INVALID_VALUE:
            sprintf(err, "OpenCL error%s: CL_INVALID_VALUE", sub);
            break;
        case CL_INVALID_DEVICE_TYPE:
            sprintf(err, "OpenCL error%s: CL_INVALID_DEVICE_TYPE", sub);
            break;
        case CL_INVALID_PLATFORM:
            sprintf(err, "OpenCL error%s: CL_INVALID_PLATFORM", sub);
            break;
        case CL_INVALID_DEVICE:
            sprintf(err, "OpenCL error%s: CL_INVALID_DEVICE", sub);
            break;
        case CL_INVALID_CONTEXT:
            sprintf(err, "OpenCL error%s: CL_INVALID_CONTEXT", sub);
            break;
        case CL_INVALID_QUEUE_PROPERTIES:
            sprintf(err, "OpenCL error%s: CL_INVALID_QUEUE_PROPERTIES", sub);
            break;
        case CL_INVALID_COMMAND_QUEUE:
            sprintf(err, "OpenCL error%s: CL_INVALID_COMMAND_QUEUE", sub);
            break;
        case CL_INVALID_HOST_PTR:
            sprintf(err, "OpenCL error%s: CL_INVALID_HOST_PTR", sub);
            break;
        case CL_INVALID_MEM_OBJECT:
            sprintf(err, "OpenCL error%s: CL_INVALID_MEM_OBJECT", sub);
            break;
        case CL_INVALID_IMAGE_FORMAT_DESCRIPTOR:
            sprintf(err, "OpenCL error%s: CL_INVALID_IMAGE_FORMAT_DESCRIPTOR", sub);
            break;
        case CL_INVALID_IMAGE_SIZE:
            sprintf(err, "OpenCL error%s: CL_INVALID_IMAGE_SIZE", sub);
            break;
        case CL_INVALID_SAMPLER:
            sprintf(err, "OpenCL error%s: CL_INVALID_SAMPLER", sub);
            break;
        case CL_INVALID_BINARY:
            sprintf(err, "OpenCL error%s: CL_INVALID_BINARY", sub);
            break;
        case CL_INVALID_BUILD_OPTIONS:
            sprintf(err, "OpenCL error%s: CL_INVALID_BUILD_OPTIONS", sub);
            break;
        case CL_INVALID_PROGRAM:
            sprintf(err, "OpenCL error%s: CL_INVALID_PROGRAM", sub);
            break;
        case CL_INVALID_PROGRAM_EXECUTABLE:
            sprintf(err, "OpenCL error%s: CL_INVALID_PROGRAM_EXECUTABLE", sub);
            break;
        case CL_INVALID_KERNEL_NAME:
            sprintf(err, "OpenCL error%s: CL_INVALID_KERNEL_NAME", sub);
            break;
        case CL_INVALID_KERNEL_DEFINITION:
            sprintf(err, "OpenCL error%s: CL_INVALID_KERNEL_DEFINITION", sub);
            break;
        case CL_INVALID_KERNEL:
            sprintf(err, "OpenCL error%s: CL_INVALID_KERNEL", sub);
            break;
        case CL_INVALID_ARG_INDEX:
            sprintf(err, "OpenCL error%s: CL_INVALID_ARG_INDEX", sub);
            break;
        case CL_INVALID_ARG_VALUE:
            sprintf(err, "OpenCL error%s: CL_INVALID_ARG_VALUE", sub);
            break;
        case CL_INVALID_ARG_SIZE:
            sprintf(err, "OpenCL error%s: CL_INVALID_ARG_SIZE", sub);
            break;
        case CL_INVALID_KERNEL_ARGS:
            sprintf(err, "OpenCL error%s: CL_INVALID_KERNEL_ARGS", sub);
            break;
        case CL_INVALID_WORK_DIMENSION:
            sprintf(err, "OpenCL error%s: CL_INVALID_WORK_DIMENSION", sub);
            break;
        case CL_INVALID_WORK_GROUP_SIZE:
            sprintf(err, "OpenCL error%s: CL_INVALID_WORK_GROUP_SIZE", sub);
            break;
        case CL_INVALID_WORK_ITEM_SIZE:
            sprintf(err, "OpenCL error%s: CL_INVALID_WORK_ITEM_SIZE", sub);
            break;
        case CL_INVALID_GLOBAL_OFFSET:
            sprintf(err, "OpenCL error%s: CL_INVALID_GLOBAL_OFFSET", sub);
            break;
        case CL_INVALID_EVENT_WAIT_LIST:
            sprintf(err, "OpenCL error%s: CL_INVALID_EVENT_WAIT_LIST", sub);
            break;
        case CL_INVALID_EVENT:
            sprintf(err, "OpenCL error%s: CL_INVALID_EVENT", sub);
            break;
        case CL_INVALID_OPERATION:
            sprintf(err, "OpenCL error%s: CL_INVALID_OPERATION", sub);
            break;
        case CL_INVALID_GL_OBJECT:
            sprintf(err, "OpenCL error%s: CL_INVALID_GL_OBJECT", sub);
            break;
        case CL_INVALID_BUFFER_SIZE:
            sprintf(err, "OpenCL error%s: CL_INVALID_BUFFER_SIZE", sub);
            break;
        case CL_INVALID_MIP_LEVEL:
            sprintf(err, "OpenCL error%s: CL_INVALID_MIP_LEVEL", sub);
            break;
        case CL_INVALID_GLOBAL_WORK_SIZE:
            sprintf(err, "OpenCL error%s: CL_INVALID_GLOBAL_WORK_SIZE", sub);
            break;
        case CL_INVALID_PROPERTY:
            sprintf(err, "OpenCL error%s: CL_INVALID_PROPERTY", sub);
            break;
        default:
            sprintf(err, "Unknown OpenCL error%s: %i", sub, (int)flag);
            break;
    };
    PyErr_SetString(PyExc_Exception, err);
    return 1;
}

/*
 * Checks the given flag for an opencl error, returns 1 if found and sets the
 * error message, else, returns 0.
 */
static int
mcl_flag(const cl_int flag)
{
    return mcl_flag2("", flag);
}

/*
 * Searches for the preferred platform and device.
 *
 * Arguments:
 *  PyObject* platform  A string representing the platform, or None
 *  PyObject* device    A string representing the device, or None
 *  cl_platform_id* pid The returned cl_platform_id, or NULL
 *  cl_device_id* did   The returned cl_device_id
 * The returned value is 0 if no error occurred, 1 if an error did occur. In
 *  this case a python error message will also be set.
 */
int mcl_select_device(
    PyObject* platform,     // Must be bytes
    PyObject* device,       // Must be bytes
    cl_platform_id* pid,
    cl_device_id* did)
{
    // String containing name of platform/device
    char name[65536];

    // Array of platform ids
    cl_uint n_platforms;
    cl_platform_id platform_ids[MCL_MAX_PLATFORMS];

    // OpenCL return
    cl_int flag;

    // Array of device ids
    cl_device_id device_ids[MCL_MAX_DEVICES];
    cl_uint n_devices;

    // OpenCL ints for iterating
    cl_uint i, j;

    // Check input
    const char* pname;
    const char* dname;
    if (platform != Py_None) {
        if (!PyBytes_Check(platform)) {
            PyErr_SetString(PyExc_Exception, "MCL_SELECT_DEVICE: 'platform' must be bytes or None.");
            return 1;
        }
        pname = PyBytes_AsString(platform);
    } else {
        pname = "";
    }
    if (device != Py_None) {
        if (!PyBytes_Check(device)) {
            PyErr_SetString(PyExc_Exception, "MCL_SELECT_DEVICE: 'device' must be a bytes or None.");
            return 1;
        }
        dname = PyBytes_AsString(device);
    } else {
        dname = "";
    }

    #ifdef MYOKIT_DEBUG
    printf("Attempting to find platform and device.\n");
    if (platform == Py_None) {
        printf("No platform specified.\n");
    } else {
        printf("Selected platform: %s\n", pname);
    }
    if (device == Py_None) {
        printf("No device specified.\n");
    } else {
        printf("Selected device: %s\n", dname);
    }
    #endif

    // Get array of platform ids
    n_platforms = 0;
    flag = clGetPlatformIDs(MCL_MAX_PLATFORMS, platform_ids, &n_platforms);
    if(mcl_flag(flag)) return 1;
    if (n_platforms == 0) {
        PyErr_SetString(PyExc_Exception, "No OpenCL platforms found.");
        return 1;
    }

    // Platform unspecified
    if (platform == Py_None) {

        // Don't recommend a platform
        *pid = NULL;

        // No platform or device specified
        if (device == Py_None) {

            // Find any device on any platform, prefer GPU
            for (i=0; i<n_platforms; i++) {
                flag = clGetDeviceIDs(platform_ids[i], CL_DEVICE_TYPE_GPU, 1, device_ids, &n_devices);
                if(flag == CL_SUCCESS) {
                    // Set selected device and return.
                    *did = device_ids[0];
                    return 0;
                } else if(flag != CL_DEVICE_NOT_FOUND) {
                    mcl_flag(flag);
                    return 1;
                }
            }
            // No GPU found, now scan for any device
            for (i=0; i<n_platforms; i++) {
                flag = clGetDeviceIDs(platform_ids[i], CL_DEVICE_TYPE_ALL, 1, device_ids, &n_devices);
                if(flag == CL_SUCCESS) {
                    // Set selected device and return.
                    *did = device_ids[0];
                    return 0;
                } else if(flag != CL_DEVICE_NOT_FOUND) {
                    mcl_flag(flag);
                    return 1;
                }
            }
            // No device found
            PyErr_SetString(PyExc_Exception, "No OpenCL devices found.");
            return 1;

        // No platform specified, but there is a preferred device
        } else {

            // Find specified device on any platform
            for (i=0; i<n_platforms; i++) {
                flag = clGetDeviceIDs(platform_ids[i], CL_DEVICE_TYPE_ALL, MCL_MAX_DEVICES, device_ids, &n_devices);
                if(flag == CL_SUCCESS) {
                    for (j=0; j<n_devices; j++) {
                        flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_NAME, sizeof(name), name, NULL);
                        if(mcl_flag(flag)) return 1;
                        trim(name);
                        if (strcmp(name, dname) == 0) {
                            // Set selected device and return.
                            *did = device_ids[j];
                            return 0;
                        }
                    }
                } else if(flag != CL_DEVICE_NOT_FOUND) {
                    mcl_flag(flag);
                    return 1;
                }
            }
            // No device found
            PyErr_SetString(PyExc_Exception, "Specified OpenCL device not found.");
            return 1;
        }

    // Platform specified by user
    } else {

        // Find platform id
        cl_uint i;
        int found = 0;
        for (i=0; i<n_platforms; i++) {
            flag = clGetPlatformInfo(platform_ids[i], CL_PLATFORM_NAME, sizeof(name), name, NULL);
            if(mcl_flag(flag)) return 1;
            trim(name);
            if (strcmp(name, pname) == 0) {
                // Set selected platform
                *pid = platform_ids[i];
                found = 1;
                break;
            }
        }
        if (found == 0) {
            PyErr_SetString(PyExc_Exception, "Specified OpenCL platform not found.");
            return 1;
        }

        // Platform specified, but no preference for device
        if (device == Py_None) {

            // Find any device on specified platform, prefer GPU
            cl_device_id device_ids[1];
            cl_uint n_devices = 0;
            flag = clGetDeviceIDs(*pid, CL_DEVICE_TYPE_GPU, 1, device_ids, &n_devices);
            if(flag == CL_SUCCESS) {
                // Set selected device and return.
                *did = device_ids[0];
                return 0;
            } else if(flag != CL_DEVICE_NOT_FOUND) {
                mcl_flag(flag);
                return 1;
            }
            // No GPU found, return any device
            flag = clGetDeviceIDs(*pid, CL_DEVICE_TYPE_ALL, 1, device_ids, &n_devices);
            if(flag == CL_SUCCESS) {
                // Set selected device and return.
                *did = device_ids[0];
                return 0;
            } else if(flag != CL_DEVICE_NOT_FOUND) {
                mcl_flag(flag);
                return 1;
            }
            // No device found
            PyErr_SetString(PyExc_Exception, "No OpenCL devices found on specified platform.");
            return 1;

        // Platform and device specified by user
        } else {

            // Find specified platform/device combo
            cl_device_id device_ids[MCL_MAX_DEVICES];
            cl_uint n_devices = 0;
            cl_uint j;
            flag = clGetDeviceIDs(*pid, CL_DEVICE_TYPE_ALL, MCL_MAX_DEVICES, device_ids, &n_devices);
            if(flag == CL_SUCCESS) {
                for (j=0; j<n_devices; j++) {
                    flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_NAME, sizeof(name), name, NULL);
                    if(mcl_flag(flag)) return 1;
                    trim(name);
                    if (strcmp(name, dname) == 0) {
                        // Set selected device and return.
                        *did = device_ids[j];
                        return 0;
                    }
                }
            } else if(flag != CL_DEVICE_NOT_FOUND) {
                mcl_flag(flag);
                return 1;
            }
            // No device found
            PyErr_SetString(PyExc_Exception, "Specified OpenCL device not found on specified platform.");
            return 1;
        }
    }
}

/*
 * Rounds up to the nearest multiple of ws_size.
 */
int
mcl_round_total_size(const int ws_size, const int total_size)
{
    int size = (total_size / ws_size) * ws_size;
    if(size < total_size) size += ws_size;
    return size;
}

/* Memory used by mcl_device_info */
static PyObject* platforms = NULL;  // Tuple of platform dicts
static PyObject* platform = NULL;   // Temporary platform dict
static PyObject* devices = NULL;    // Temporary tuple of devices
static PyObject* device = NULL;     // Temporary device dict
static PyObject* items = NULL;      // Temporary tuple of item sizes
static PyObject* val;               // Temporary dictionary value
static size_t* work_item_sizes;     // Temporary array of work item sizes

/*
 * Tidies up if an error occurs in mcl_device_info
 */
PyObject*
mcl_device_info_clean()
{
    Py_XDECREF(platforms); platforms = NULL;
    Py_XDECREF(platform); platform = NULL;
    Py_XDECREF(devices); devices = NULL;
    Py_XDECREF(device); device = NULL;
    Py_XDECREF(val); val = NULL;
    free(work_item_sizes); work_item_sizes = NULL;
    return 0;
}

/*
 * Returns information about the available OpenCL platforms and devices.
 *
 * Returns a reference to a tuple of platform dicts
 *
 * platforms = (
 *      dict(platform) {
 *          'profile'    : str,
 *          'version'    : str,
 *          'name'       : str,
 *          'vendor'     : str,
 *          'extensions' : str,
 *          'devices'    : (
 *              dict(device) {
 *                  'name'       : str,
 *                  'vendor'     : str,
 *                  'version'    : str,
 *                  'driver'     : str,
 *                  'clock'      : int,     # Clock speed, in MHz
 *                  'global'     : int,     # Global memory, in bytes
 *                  'local'      : int,     # Local memory, in bytes
 *                  'const'      : int,     # Const memory, in bytes
 *                  'units'      : int,     # Computing units
 *                  'param'      : int,     # Max size of arguments passed to kernel
 *                  'groups'     : int,     # Max work group size
 *                  'dimensions' : int,     # Max work item dimensions
 *                  'items'      : (ints),  # Max work item sizes
 *                  }
 *              ),
 *              ...
 *          },
 *          ...
 *     )
 */
PyObject*
mcl_device_info()
{
    // Array of platform ids
    cl_platform_id platform_ids[MCL_MAX_PLATFORMS];

    // Number of platforms
    cl_uint n_platforms;

    // Return from OpenCL
    cl_int flag;

    // Devices & return values from queries
    cl_device_id device_ids[MCL_MAX_DEVICES];
    cl_uint n_devices;
    cl_uint buf_uint;
    cl_ulong buf_ulong;
    size_t wgroup_size;
    size_t max_param;

    // String buffer
    char buffer[65536];

    // Iteration
    cl_uint i, j, k;

    // Set all pointers used by clean() to null
    platforms = NULL;
    platform = NULL;
    devices = NULL;
    device = NULL;
    items = NULL;
    val = NULL;
    work_item_sizes = NULL;

    // Get platforms
    n_platforms = 0;
    flag = clGetPlatformIDs(MCL_MAX_PLATFORMS, platform_ids, &n_platforms);
    if(mcl_flag(flag)) return mcl_device_info_clean();

    // Create platforms tuple
    platforms = PyTuple_New((size_t)n_platforms);

    if (n_platforms == 0) {
        // No platforms found
        return platforms;
    }

    // Check all platforms
    for (i=0; i<n_platforms; i++) {
        // Create platform dict
        platform = PyDict_New();

        // Profile
        flag = clGetPlatformInfo(platform_ids[i], CL_PLATFORM_PROFILE, sizeof(buffer), buffer, NULL);
        if(mcl_flag(flag)) return mcl_device_info_clean();
        val = PyUnicode_FromString(buffer);
        PyDict_SetItemString(platform, "profile", val);
        Py_DECREF(val); val = NULL;

        // Version
        flag = clGetPlatformInfo(platform_ids[i], CL_PLATFORM_VERSION, sizeof(buffer), buffer, NULL);
        if(mcl_flag(flag)) return mcl_device_info_clean();
        val = PyUnicode_FromString(buffer);
        PyDict_SetItemString(platform, "version", val);
        Py_DECREF(val); val = NULL;

        // Name
        flag = clGetPlatformInfo(platform_ids[i], CL_PLATFORM_NAME, sizeof(buffer), buffer, NULL);
        if(mcl_flag(flag)) return mcl_device_info_clean();
        val = PyUnicode_FromString(buffer);
        PyDict_SetItemString(platform, "name", val);
        Py_DECREF(val); val = NULL;

        // Vendor
        flag = clGetPlatformInfo(platform_ids[i], CL_PLATFORM_VENDOR, sizeof(buffer), buffer, NULL);
        if(mcl_flag(flag)) return mcl_device_info_clean();
        val = PyUnicode_FromString(buffer);
        PyDict_SetItemString(platform, "vendor", val);
        Py_DECREF(val); val = NULL;

        // Extensions
        flag = clGetPlatformInfo(platform_ids[i], CL_PLATFORM_EXTENSIONS, sizeof(buffer), buffer, NULL);
        if(mcl_flag(flag)) return mcl_device_info_clean();
        val = PyUnicode_FromString(buffer);
        PyDict_SetItemString(platform, "extensions", val);
        Py_DECREF(val); val = NULL;

        // Devices
        flag = clGetDeviceIDs(platform_ids[i], CL_DEVICE_TYPE_ALL, MCL_MAX_DEVICES, device_ids, &n_devices);
        if (flag == CL_DEVICE_NOT_FOUND) {
            n_devices = 0;
        } else if(mcl_flag(flag)) {
            return mcl_device_info_clean();
        }
        devices = PyTuple_New((size_t)n_devices);

        for (j=0; j<n_devices; j++) {
            // Create device dict
            device = PyDict_New();

            // Name
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_NAME, sizeof(buffer), buffer, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyUnicode_FromString(buffer);
            PyDict_SetItemString(device, "name", val);
            Py_DECREF(val); val = NULL;

            // Vendor
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_VENDOR, sizeof(buffer), buffer, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyUnicode_FromString(buffer);
            PyDict_SetItemString(device, "vendor", val);
            Py_DECREF(val); val = NULL;

            // Device version
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_VERSION, sizeof(buffer), buffer, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyUnicode_FromString(buffer);
            PyDict_SetItemString(device, "version", val);
            Py_DECREF(val); val = NULL;

            // Driver version
            flag = clGetDeviceInfo(device_ids[j], CL_DRIVER_VERSION, sizeof(buffer), buffer, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyUnicode_FromString(buffer);
            PyDict_SetItemString(device, "driver", val);
            Py_DECREF(val); val = NULL;

            // Clock speed (MHz)
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_MAX_CLOCK_FREQUENCY, sizeof(buf_uint), &buf_uint, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyLong_FromLong(buf_uint);
            PyDict_SetItemString(device, "clock", val);
            Py_DECREF(val); val = NULL;

            // Global memory (bytes)
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_GLOBAL_MEM_SIZE, sizeof(buf_ulong), &buf_ulong, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyLong_FromLong(buf_ulong);
            PyDict_SetItemString(device, "global", val);
            Py_DECREF(val); val = NULL;

            // Local memory (bytes)
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_LOCAL_MEM_SIZE, sizeof(buf_ulong), &buf_ulong, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyLong_FromLong(buf_ulong);
            PyDict_SetItemString(device, "local", val);
            Py_DECREF(val); val = NULL;

            // Const memory (bytes)
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_MAX_CONSTANT_BUFFER_SIZE, sizeof(buf_ulong), &buf_ulong, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyLong_FromLong(buf_ulong);
            PyDict_SetItemString(device, "const", val);
            Py_DECREF(val); val = NULL;

            // Computing units
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(buf_uint), &buf_uint, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyLong_FromLong(buf_uint);
            PyDict_SetItemString(device, "units", val);
            Py_DECREF(val); val = NULL;

            // Max workgroup size
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_MAX_WORK_GROUP_SIZE, sizeof(wgroup_size), &wgroup_size, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyLong_FromLong(wgroup_size);
            PyDict_SetItemString(device, "groups", val);
            Py_DECREF(val); val = NULL;

            // Max workitem sizes
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS, sizeof(buf_uint), &buf_uint, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyLong_FromLong(buf_uint);
            PyDict_SetItemString(device, "dimensions", val);
            Py_DECREF(val); val = NULL;

            work_item_sizes = (size_t*)malloc(buf_uint * sizeof(size_t));
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_MAX_WORK_ITEM_SIZES, buf_uint*sizeof(size_t), work_item_sizes, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            items = PyTuple_New((size_t)buf_uint);
            for (k=0; k<buf_uint; k++) {
                PyTuple_SetItem(items, k, PyLong_FromLong(work_item_sizes[k]));
            }
            free(work_item_sizes); work_item_sizes = NULL;
            PyDict_SetItemString(device, "items", items);
            Py_DECREF(items); items = NULL;

            // Maximum size of a kernel parameter
            flag = clGetDeviceInfo(device_ids[j], CL_DEVICE_MAX_PARAMETER_SIZE, sizeof(max_param), &max_param, NULL);
            if(mcl_flag(flag)) return mcl_device_info_clean();
            val = PyLong_FromLong(max_param);
            PyDict_SetItemString(device, "param", val);
            Py_DECREF(val); val = NULL;

            // Add device to devices tuple
            PyTuple_SetItem(devices, j, device);
            device = NULL;
        }

        // Add devices entry to platform dict
        PyDict_SetItemString(platform, "devices", devices);
        Py_DECREF(devices); devices = NULL;

        // Add platform to platforms tuple
        PyTuple_SetItem(platforms, i, platform);
        platform = NULL;
    }

    // Return platforms
    return platforms;
}

#undef MyokitOpenCL
#endif
