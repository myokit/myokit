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
        sub[0] = 0;
    }

    switch(flag) {
        // OpenCL 1.0 Errors
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
        // OpenCL 1.1 etc. codes can not be assumed to be defined
        // Might be good to have ifdefs or something
        // OpenCL extensions
        case -1001:     // CL_PLATFORM_NOT_FOUND_KHR
            sprintf(err, "OpenCL error%s: CL_PLATFORM_NOT_FOUND_KHR", sub);
            break;
        // Unknown error
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
 *  cl_platform_id* pid The returned cl_platform_id
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

    // By default, don't recommend a platform or device
    *pid = NULL;
    *did = NULL;

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

    #ifdef MYOKIT_DEBUG_MESSAGES
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
    // This can raisee an error CL_PLATFORM_NOT_FOUND_KHR (code -1001) if no
    // platforms are found and the cl_khr_icd extension is enabled:
    // https://www.khronos.org/registry/OpenCL/sdk/2.0/docs/man/xhtml/clGetPlatformIDs.html
    n_platforms = 0;
    flag = clGetPlatformIDs(MCL_MAX_PLATFORMS, platform_ids, &n_platforms);
    if ((flag != -1001) && mcl_flag(flag)) return 1;
    if (n_platforms == 0) {
        PyErr_SetString(PyExc_Exception, "No OpenCL platforms found.");
        return 1;
    }

    // Platform unspecified
    if (platform == Py_None) {

        // No platform or device specified
        if (device == Py_None) {

            // Find any device on any platform, prefer GPU
            for (i=0; i<n_platforms; i++) {
                flag = clGetDeviceIDs(platform_ids[i], CL_DEVICE_TYPE_GPU, 1, device_ids, &n_devices);
                if(flag == CL_SUCCESS) {
                    // Set selected platform and device and return.
                    *pid = platform_ids[i];
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
                    // Set selected platform and device and return.
                    *pid = platform_ids[i];
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
                            // Set selected platform device and return.
                            *pid = platform_ids[i];
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

/*
 * Checks whether a given platform supports a given extension.
 *
 * Arguments:
 *  cl_platform_id platform_id  The id of the platform to query
 *  char* extension             The extension name, as a string.
 *
 * Returns 1 if support is detected, else 0.
 */
int mcl_platform_supports_extension(cl_platform_id platform_id, const char* extension)
{
    // Return from OpenCL
    cl_int flag;

    // String buffer
    char buffer[65536];

    // Extensions
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Querying extensions\n");
    #endif
    flag = clGetPlatformInfo(platform_id, CL_PLATFORM_EXTENSIONS, sizeof(buffer), buffer, NULL);
    if(mcl_flag(flag)) return 0;
    return (strstr(buffer, extension) != NULL);
}

/*
 * Creates and returns a platform information dict, not including a devices
 * entry.
 *
 * Arguments:
 *  cl_platform_id platform_id  The id of the platform to query
 *  char* buffer                An initialised string buffer, that can be used
 *                              to read and write string information.
 *
 * Returns NULL and sets an error message if any exception occurs.
 */
PyObject* mcl_info_platform_dict(cl_platform_id platform_id, size_t bufsize, char* buffer)
{
    // Return from OpenCL
    cl_int flag;

    // Platform dict (decref on exception)
    PyObject* platform;

    // Value to insert into the dict (decref immediatly after)
    PyObject* val;

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Creating platform info dict\n");
    #endif

    // Create platform dict
    platform = PyDict_New();
    if(platform == NULL) {
        PyErr_SetString(PyExc_Exception, "Unable to create dict for platform info.");
        return NULL;
    }

    // Add profile
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("  Querying profile\n");
    #endif
    flag = clGetPlatformInfo(platform_id, CL_PLATFORM_PROFILE, bufsize, buffer, NULL);
    if(mcl_flag(flag)) { Py_DECREF(platform); return NULL; }
    val = PyUnicode_FromString(buffer);
    PyDict_SetItemString(platform, "profile", val);
    Py_CLEAR(val);

    // Version
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("  Querying version\n");
    #endif
    flag = clGetPlatformInfo(platform_id, CL_PLATFORM_VERSION, bufsize, buffer, NULL);
    if(mcl_flag(flag)) { Py_DECREF(platform); return NULL; }
    val = PyUnicode_FromString(buffer);
    PyDict_SetItemString(platform, "version", val);
    Py_CLEAR(val);

    // Name
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("  Querying name\n");
    #endif
    flag = clGetPlatformInfo(platform_id, CL_PLATFORM_NAME, bufsize, buffer, NULL);
    if(mcl_flag(flag)) { Py_DECREF(platform); return NULL; }
    val = PyUnicode_FromString(buffer);
    PyDict_SetItemString(platform, "name", val);
    Py_CLEAR(val);

    // Vendor
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("  Querying vendor\n");
    #endif
    flag = clGetPlatformInfo(platform_id, CL_PLATFORM_VENDOR, bufsize, buffer, NULL);
    if(mcl_flag(flag)) { Py_DECREF(platform); return NULL; }
    val = PyUnicode_FromString(buffer);
    PyDict_SetItemString(platform, "vendor", val);
    Py_CLEAR(val);

    // Extensions
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("  Querying extensions\n");
    #endif
    flag = clGetPlatformInfo(platform_id, CL_PLATFORM_EXTENSIONS, bufsize, buffer, NULL);
    if(mcl_flag(flag)) { Py_DECREF(platform); return NULL; }
    val = PyUnicode_FromString(buffer);
    PyDict_SetItemString(platform, "extensions", val);
    Py_CLEAR(val);

    // Finished!
    return platform;
}


/*
 * Creates and returns a device information dict, not including a devices
 * entry.
 *
 * Arguments:
 *  cl_device_id device_id  The id of the device to query.
 *  size_t bufsize          Size of the string `buffer`.
 *  char* buffer            An initialised string buffer, that can be used to
 *                          read and write string information.
 *
 * Returns NULL and sets an error message if any exception occurs.
 */
PyObject* mcl_info_device_dict(cl_device_id device_id, size_t bufsize, char* buffer)
{
    // Return from OpenCL
    cl_int flag;

    // Device dict (decref on exception)
    PyObject* device;

    // Value to insert into the dict (decref immediately after)
    PyObject* val;

    // Placeholders for return values
    cl_uint buf_uint;
    cl_ulong buf_ulong;
    size_t buf_size_t;

    // Placeholder for work item sizes, must be freed before returning
    size_t* work_item_sizes;

    // Item sizes tuple to insert into the dict (decref immediately after)
    PyObject* items_sizes_tuple;

    // Iteration
    size_t i;

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Creating device info dict\n");
    #endif

    // Create device dict
    device = PyDict_New();
    if(device == NULL) {
        PyErr_SetString(PyExc_Exception, "Unable to create dict for device info.");
        return NULL;
    }

    // Name
    flag = clGetDeviceInfo(device_id, CL_DEVICE_NAME, bufsize, buffer, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyUnicode_FromString(buffer);
    PyDict_SetItemString(device, "name", val);
    Py_CLEAR(val);

    // Vendor
    flag = clGetDeviceInfo(device_id, CL_DEVICE_VENDOR, bufsize, buffer, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyUnicode_FromString(buffer);
    PyDict_SetItemString(device, "vendor", val);
    Py_CLEAR(val);

    // Device version
    flag = clGetDeviceInfo(device_id, CL_DEVICE_VERSION, bufsize, buffer, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyUnicode_FromString(buffer);
    PyDict_SetItemString(device, "version", val);
    Py_CLEAR(val);

    // Driver version
    flag = clGetDeviceInfo(device_id, CL_DRIVER_VERSION, bufsize, buffer, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyUnicode_FromString(buffer);
    PyDict_SetItemString(device, "driver", val);
    Py_CLEAR(val);

    // Clock speed (MHz)
    flag = clGetDeviceInfo(device_id, CL_DEVICE_MAX_CLOCK_FREQUENCY, sizeof(buf_uint), &buf_uint, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyLong_FromLong(buf_uint);
    PyDict_SetItemString(device, "clock", val);
    Py_CLEAR(val);

    // Global memory (bytes)
    flag = clGetDeviceInfo(device_id, CL_DEVICE_GLOBAL_MEM_SIZE, sizeof(buf_ulong), &buf_ulong, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyLong_FromLong(buf_ulong);
    PyDict_SetItemString(device, "global", val);
    Py_CLEAR(val);

    // Local memory (bytes)
    flag = clGetDeviceInfo(device_id, CL_DEVICE_LOCAL_MEM_SIZE, sizeof(buf_ulong), &buf_ulong, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyLong_FromLong(buf_ulong);
    PyDict_SetItemString(device, "local", val);
    Py_CLEAR(val);

    // Const memory (bytes)
    flag = clGetDeviceInfo(device_id, CL_DEVICE_MAX_CONSTANT_BUFFER_SIZE, sizeof(buf_ulong), &buf_ulong, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyLong_FromLong(buf_ulong);
    PyDict_SetItemString(device, "const", val);
    Py_CLEAR(val);

    // Computing units
    flag = clGetDeviceInfo(device_id, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(buf_uint), &buf_uint, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyLong_FromLong(buf_uint);
    PyDict_SetItemString(device, "units", val);
    Py_CLEAR(val);

    // Max workgroup size
    flag = clGetDeviceInfo(device_id, CL_DEVICE_MAX_WORK_GROUP_SIZE, sizeof(buf_size_t), &buf_size_t, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyLong_FromLong(buf_size_t);
    PyDict_SetItemString(device, "groups", val);
    Py_CLEAR(val);

    // Max workitem sizes
    flag = clGetDeviceInfo(device_id, CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS, sizeof(buf_uint), &buf_uint, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyLong_FromLong(buf_uint);
    PyDict_SetItemString(device, "dimensions", val);
    Py_CLEAR(val);

    work_item_sizes = (size_t*)malloc(buf_uint * sizeof(size_t));
    flag = clGetDeviceInfo(device_id, CL_DEVICE_MAX_WORK_ITEM_SIZES, buf_uint * sizeof(size_t), work_item_sizes, NULL);
    if(mcl_flag(flag)) { free(work_item_sizes); Py_DECREF(device); return NULL; }
    items_sizes_tuple = PyTuple_New((size_t)buf_uint);
    for (i=0; i<buf_uint; i++) {
        PyTuple_SetItem(items_sizes_tuple, i, PyLong_FromLong(work_item_sizes[i]));
    }
    free(work_item_sizes); work_item_sizes = NULL;
    PyDict_SetItemString(device, "items", items_sizes_tuple);
    Py_CLEAR(items_sizes_tuple);

    // Maximum size of a kernel parameter
    flag = clGetDeviceInfo(device_id, CL_DEVICE_MAX_PARAMETER_SIZE, sizeof(buf_size_t), &buf_size_t, NULL);
    if(mcl_flag(flag)) { Py_DECREF(device); return NULL; }
    val = PyLong_FromLong(buf_size_t);
    PyDict_SetItemString(device, "param", val);
    Py_CLEAR(val);

    // Done!
    return device;
}

/*
 * Returns information about the available OpenCL platforms and devices.
 *
 * Returns a reference to a tuple of platform dicts.
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
mcl_info()
{
    // Return from OpenCL
    cl_int flag;

    // Array of platform ids, number of platforms
    cl_platform_id platform_ids[MCL_MAX_PLATFORMS];
    cl_uint n_platforms;

    // Array of device ids, number of ids
    cl_device_id device_ids[MCL_MAX_DEVICES];
    cl_uint n_devices;

    // String buffer for returned strings
    char buffer[65536];

    // Iteration
    cl_uint i, j;

    // Python objects
    PyObject* platforms;     // Tuple of platform dicts, to be returned
    PyObject* platform;      // Temporary platform dict
    PyObject* devices;       // Temporary tuple of devices
    PyObject* device;        // Temporary device dict

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Querying OpenCL driver\n");
    #endif

    // Get platforms
    // This can raisee an error CL_PLATFORM_NOT_FOUND_KHR (code -1001) if no
    // platforms are found and the cl_khr_icd extension is enabled:
    // https://www.khronos.org/registry/OpenCL/sdk/2.0/docs/man/xhtml/clGetPlatformIDs.html
    n_platforms = 0;
    flag = clGetPlatformIDs(MCL_MAX_PLATFORMS, platform_ids, &n_platforms);
    if ((flag != -1001) && mcl_flag(flag)) return NULL;
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Found %d platforms\n", n_platforms);
    #endif

    // Create platforms tuple, must decref on exception
    platforms = PyTuple_New((size_t)n_platforms);

    // No platforms found
    if (n_platforms == 0) {
        return platforms;
    }

    // Check all platforms
    for (i=0; i<n_platforms; i++) {

        // Create platform dict
        platform = mcl_info_platform_dict(platform_ids[i], sizeof(buffer), buffer);
        if (platform == NULL) { Py_DECREF(platforms); return NULL; }

        // Count devices
        flag = clGetDeviceIDs(platform_ids[i], CL_DEVICE_TYPE_ALL, MCL_MAX_DEVICES, device_ids, &n_devices);
        if (flag == CL_DEVICE_NOT_FOUND) {
            n_devices = 0;
        } else if (mcl_flag(flag)) {
            Py_DECREF(platforms);
            return NULL;
        }

        // Create devices tuple, must decref on exception
        devices = PyTuple_New((size_t)n_devices);

        // Add devices
        for (j=0; j<n_devices; j++) {

            // Create device dict, must decref on exception
            device = mcl_info_device_dict(device_ids[j], sizeof(buffer), buffer);
            if (device == NULL) { Py_DECREF(platforms); Py_DECREF(devices); return NULL; }

            // Add device to devices tuple (steals reference)
            PyTuple_SetItem(devices, j, device);
            device = NULL;
        }

        // Add devices entry to platform dict
        PyDict_SetItemString(platform, "devices", devices);
        Py_CLEAR(devices);

        // Add platform to platforms tuple (steals reference)
        PyTuple_SetItem(platforms, i, platform);
        platform = NULL;
    }

    // Return platforms
    return platforms;
}

/*
 * Returns information about the currently selected or default OpenCL platform
 * and device.
 *
 * Arguments:
 *  PyObject* platform_name  A string naming the selected platform, or None
 *  PyObject* device_name    A string naming the selected device, or None
 *
 * Returns: a platform dict similar to those returned in a tuple by mcl_info,
 * but with a single "device" entry instead of a "devices" list.
 */
PyObject*
mcl_info_current(
    PyObject* platform_name,
    PyObject* device_name)
{
    // The current platform and device id
    cl_platform_id platform_id;
    cl_device_id device_id;

    // The platform and device dicts (may need decref on exception)
    PyObject* platform;
    PyObject* device;

    // String buffer
    char buffer[65536];

    // Get platform and device id
    if (mcl_select_device(platform_name, device_name, &platform_id, &device_id)) {
        return NULL;
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Found platform %d\n", platform_id);
    printf("Found device %d\n", device_id);
    #endif

    // Create platform dict
    platform = mcl_info_platform_dict(platform_id, sizeof(buffer), buffer);
    if (platform == NULL) return NULL;

    // Add device dict
    device = mcl_info_device_dict(device_id, sizeof(buffer), buffer);
    if (device == NULL) { Py_DECREF(platform); return NULL; }
    PyDict_SetItemString(platform, "device", device);
    Py_DECREF(device);

    // Return platform dict
    return platform;
}

#undef MyokitOpenCL
#endif
