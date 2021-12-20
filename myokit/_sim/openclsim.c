<?
# opencl.c
#
# A pype template for opencl driven 1d or 2d simulations
#
# Required variables
# -----------------------------------------------------------------------------
# module_name       A module name
# model             A myokit model, cloned with independent components
# precision         A myokit precision constant
# dims              The number of dimensions, either 1 or 2
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
#include <assert.h>
#include <math.h>

<?
if myokit.DEBUG_SM:
    print('// Show debug output')
    print('#ifndef MYOKIT_DEBUG_MESSAGES')
    print('#define MYOKIT_DEBUG_MESSAGES')
    print('#endif')
?>

#include "pacing.h"
#include "mcl.h"

// C89 Doesn't have isnan
#ifndef isnan
    #define isnan(arg) (arg != arg)
#endif

#define n_state <?= str(model.count_states()) ?>

typedef <?= ('double' if precision == myokit.DOUBLE_PRECISION else 'float') ?> Real;
<?
if precision == myokit.DOUBLE_PRECISION:
    print('#define MYOKIT_DOUBLE_PRECISION')
?>

/*
 * Adds a variable to the logging lists. Returns 1 if successful.
 *
 * Arguments
 *  log_dict : The dictionary of logs passed in by the user
 *  logs     : Pointers to a log for each logged variables
 *  vars     : Pointers to each variable to log
 *  i        : The index of the next logged variable
 *  name     : The variable name to search for in the dict
 *  var      : The variable to add to the logs, if its name is present
 * Returns 0 if not added, 1 if added.
 */
static int log_add(PyObject* log_dict, PyObject** logs, Real** vars, unsigned long i, char* name, const Real* var)
{
    int added = 0;
    PyObject* key = PyUnicode_FromString(name);
    if(PyDict_Contains(log_dict, key)) {
        logs[i] = PyDict_GetItem(log_dict, key);
        vars[i] = (Real*)var;
        added = 1;
    }
    Py_DECREF(key);
    return added;
}

/*
 * Simulation variables
 *
 */
// Simulation state
int running = 0;    // 1 if a simulation has been initialized, 0 if it's clean

// Note: OpenCL functions such as get_global_id() all return a size_t defined
// on the device (so different from the .C size_t). This is either a 32 or a
// 64 bit int. To be safe, we just use a ulong everywhere.

// Input arguments
PyObject *platform_name;// A python string specifying the platform to use
PyObject *device_name;  // A python string specifying the device to use
char* kernel_source;    // The kernel code
unsigned long nx;       // The number of cells in the x direction
unsigned long ny;       // The number of cells in the y direction
double gx;              // The cell-to-cell conductance in the x direction
double gy;              // The cell-to-cell conductance in the y direction
double tmin;            // The initial simulation time
double tmax;            // The final simulation time
double default_dt;      // The default time between steps
PyObject* state_in;     // The initial state
PyObject* state_out;    // The final state
PyObject *protocol;     // A pacing protocol
PyObject *log_dict;     // A logging dict
double log_interval;    // The time between log writes
PyObject *inter_log;    // A list of intermediary variables to log
PyObject *field_data;   // A list containing all field data

// OpenCL objects
cl_context context = NULL;
cl_command_queue command_queue = NULL;
cl_program program = NULL;
cl_kernel kernel_cell;
cl_kernel kernel_diff;
cl_kernel kernel_cond;
cl_kernel kernel_arb_reset;
cl_kernel kernel_arb_step;
cl_mem mbuf_state = NULL;
cl_mem mbuf_idiff = NULL;
cl_mem mbuf_inter_log = NULL;
cl_mem mbuf_field_data = NULL;
cl_mem mbuf_gx = NULL;      // Conductance field
cl_mem mbuf_gy = NULL;      // Conductance field
cl_mem mbuf_conn1 = NULL;   // Connections: Cell 1
cl_mem mbuf_conn2 = NULL;   // Connections: Cell 2
cl_mem mbuf_conn3 = NULL;   // Connections: Conductance between 1 and 2

// Input vectors to kernels
Real *rvec_state = NULL;
Real *rvec_idiff = NULL;
Real *rvec_inter_log = NULL;
Real *rvec_field_data = NULL;
Real *rvec_gx = NULL;
Real *rvec_gy = NULL;
unsigned long *rvec_conn1 = NULL;
unsigned long *rvec_conn2 = NULL;
Real *rvec_conn3 = NULL;
size_t dsize_state;
size_t dsize_idiff;
size_t dsize_inter_log;
size_t dsize_field_data;
size_t dsize_gx = 0;
size_t dsize_gy = 0;
size_t dsize_conn1 = 0;
size_t dsize_conn2 = 0;
size_t dsize_conn3 = 0;

/* Timing */
double engine_time;     /* The current simulation time */
double dt;              /* The next step size */
double tnext_pace;      /* The next pacing event start/stop */
double dt_min;          /* The minimal time increase */
unsigned long istep;    /* The index of the current step */
int intermediary_step;  /* True if an intermediary step is being taken */

/* Halt on NaN */
int halt_sim;

/* Pacing */
ESys pacing = NULL;
double engine_pace = 0;

// Diffusion currents enabled/disabled
int diffusion;

// Conductance fields
PyObject* gx_field;
PyObject* gy_field;

// Arbitrary geometry diffusion
PyObject* connections;  // List of connection tuples
unsigned long n_connections;

// OpenCL work group sizes
size_t global_work_size[2];
// Work items for arbitrary geometry diffusion step
size_t global_work_size_conn[1];

// Kernel arguments copied into "Real" type
Real arg_time;
Real arg_pace;
Real arg_dt;
Real arg_gx;
Real arg_gy;

/* Logging */
PyObject** logs = NULL;     /* An array of pointers to a PyObject */
Real** vars = NULL;         /* An array of pointers to values to log */
unsigned long n_vars;       /* Number of logging variables */
double tnext_log;           /* The next logging point */
unsigned long inext_log;    /* The number of logged steps */
int logging_diffusion;      /* True if diffusion current is being logged. */
int logging_states;         /* True if any states are being logged */
int logging_inters;         /* True if any intermediary variables are being logged. */
unsigned long n_inter;      /* The number of intermediary variables to log */
/* The relationship between n_inter and logging_inters isn't straightforward: */
/* n_inter is the number of different model variables (so membrane.V, not */
/* 1.2.membrane.V) being logged, while logging_inters is 1 if at least one */
/* simulation variable (1.2.membrane.V) is listed in the given log. */
unsigned long n_field_data; /* The number of floats in the field data */

/* Temporary objects: decref before re-using for another var */
/* (Unless you got it through PyList_GetItem or PyTuble_GetItem) */
PyObject* flt = NULL;               /* PyObject, various uses */
PyObject* ret = NULL;               /* PyObject, used as return value */
PyObject* list_update_str = NULL;   /* PyUnicode, used to call "append" method */

/*
 * Cleans up after a simulation
 *
 */
static PyObject*
sim_clean()
{
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Clean called.\n");
    #endif

    if(running) {
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("Cleaning.\n");
        #endif

        // Wait for any remaining commands to finish
        clFlush(command_queue);
        clFinish(command_queue);

        // Decref opencl objects
        clReleaseKernel(kernel_cell); kernel_cell = NULL;
        if (connections != Py_None) {
            clReleaseKernel(kernel_arb_reset); kernel_arb_reset = NULL;
            clReleaseKernel(kernel_arb_step); kernel_arb_step = NULL;
        } else if (gx_field != Py_None) {
            clReleaseKernel(kernel_cond); kernel_cond = NULL;
        } else if (diffusion) {
            clReleaseKernel(kernel_diff); kernel_diff = NULL;
        }
        clReleaseProgram(program); program = NULL;
        clReleaseMemObject(mbuf_state); mbuf_state = NULL;
        clReleaseMemObject(mbuf_idiff); mbuf_idiff = NULL;
        clReleaseMemObject(mbuf_inter_log); mbuf_inter_log = NULL;
        clReleaseMemObject(mbuf_field_data); mbuf_field_data = NULL;
        if (gx_field != Py_None) {
            clReleaseMemObject(mbuf_gx); mbuf_gx = NULL;
            clReleaseMemObject(mbuf_gy); mbuf_gy = NULL;
        } else if (connections != Py_None) {
            clReleaseMemObject(mbuf_conn1); mbuf_conn1 = NULL;
            clReleaseMemObject(mbuf_conn2); mbuf_conn2 = NULL;
            clReleaseMemObject(mbuf_conn3); mbuf_conn3 = NULL;
        }
        clReleaseCommandQueue(command_queue); command_queue = NULL;
        clReleaseContext(context); context = NULL;

        // Free pacing system memory
        ESys_Destroy(pacing); pacing = NULL;

        // Free dynamically allocated arrays
        free(rvec_state); rvec_state = NULL;
        free(rvec_idiff); rvec_idiff = NULL;
        free(rvec_inter_log); rvec_inter_log = NULL;
        free(rvec_field_data); rvec_field_data = NULL;
        free(rvec_gx); rvec_gx = NULL;
        free(rvec_gy); rvec_gy = NULL;
        free(rvec_conn1); rvec_conn1 = NULL;
        free(rvec_conn2); rvec_conn2 = NULL;
        free(rvec_conn3); rvec_conn3 = NULL;
        free(logs); logs = NULL;
        free(vars); vars = NULL;

        // No longer need update string
        Py_XDECREF(list_update_str); list_update_str = NULL;

        // No longer running
        running = 0;
    }
    #ifdef MYOKIT_DEBUG_MESSAGES
    else
    {
        printf("Skipping cleaning: not running!\n");
    }
    #endif

    // Return 0, allowing the construct
    //  PyErr_SetString(PyExc_Exception, "Oh noes!");
    //  return sim_clean()
    //to terminate a python function.
    return 0;
}
static PyObject*
py_sim_clean(PyObject *self, PyObject *args)
{
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Python py_sim_clean called.\n");
    #endif

    sim_clean();
    Py_RETURN_NONE;
}

/*
 * Sets up a simulation
 *
 *
 */
static PyObject*
sim_init(PyObject* self, PyObject* args)
{
    // Pacing flag
    ESys_Flag flag_pacing;

    // OpenCL flag
    cl_int flag;

    // Iteration
    unsigned long i, j, k;

    // Platform and device id
    cl_platform_id platform_id;
    cl_device_id device_id;

    // Compilation options
    char options[1024];

    // Variable names
    char log_var_name[1023];
    unsigned long k_vars;

    // Compilation error message
    size_t blog_size;
    char *blog;

    #ifdef MYOKIT_DEBUG_MESSAGES
    // Don't buffer stdout
    setbuf(stdout, NULL); // Don't buffer stdout
    printf("Starting initialization.\n");
    #endif

    // Check if already running
    if(running != 0) {
        PyErr_SetString(PyExc_Exception, "Simulation already initialized.");
        return 0;
    }

    // Set all pointers used in sim_clean to null
    command_queue = NULL;
    kernel_cell = NULL;
    kernel_diff = NULL;
    kernel_cond = NULL;
    kernel_arb_reset = NULL;
    kernel_arb_step = NULL;
    program = NULL;
    mbuf_state = NULL;
    mbuf_idiff = NULL;
    mbuf_inter_log = NULL;
    mbuf_field_data = NULL;
    mbuf_gx = NULL;
    mbuf_gy = NULL;
    mbuf_conn1 = NULL;
    mbuf_conn2 = NULL;
    mbuf_conn3 = NULL;
    context = NULL;
    pacing = NULL;
    rvec_state = NULL;
    rvec_idiff = NULL;
    rvec_inter_log = NULL;
    rvec_field_data = NULL;
    rvec_gx = NULL;
    rvec_gy = NULL;
    rvec_conn1 = NULL;
    rvec_conn2 = NULL;
    rvec_conn3 = NULL;
    logs = NULL;
    vars = NULL;
    list_update_str = NULL;

    // Check input arguments
    // https://docs.python.org/3.8/c-api/arg.html#c.PyArg_ParseTuple
    if(!PyArg_ParseTuple(args, "OOskkbddOOOdddOOOOdOO",
            &platform_name,     // Must be bytes
            &device_name,       // Must be bytes
            &kernel_source,
            &nx,                // Small 'k' = unsigned long
            &ny,
            &diffusion,
            &gx,
            &gy,
            &gx_field,
            &gy_field,
            &connections,
            &tmin,
            &tmax,
            &default_dt,
            &state_in,
            &state_out,
            &protocol,
            &log_dict,
            &log_interval,
            &inter_log,
            &field_data
            )) {
        PyErr_SetString(PyExc_Exception, "Wrong number of arguments.");
        // Nothing allocated yet, no pyobjects _created_, return directly
        return 0;
    }
    dt = default_dt;
    dt_min = 0;
    arg_dt = (Real)dt;
    arg_gx = (Real)gx;
    arg_gy = (Real)gy;
    halt_sim = 0;

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Retrieved function arguments.\n");
    #endif

    // Now officialy running :)
    running = 1;

    ///////////////////////////////////////////////////////////////////////////
    //
    // From this point on, use "return sim_clean()" to abort.
    //
    //

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Running!\n");
    printf("Checking input arguments.\n");
    #endif

    //
    // Check state in and out lists
    //
    if(!PyList_Check(state_in)) {
        PyErr_SetString(PyExc_Exception, "'state_in' must be a list.");
        return sim_clean();
    }
    if((unsigned long)PyList_Size(state_in) != nx * ny * n_state) {
        PyErr_SetString(PyExc_Exception, "'state_in' must have size nx * ny * n_states.");
        return sim_clean();
    }
    if(!PyList_Check(state_out)) {
        PyErr_SetString(PyExc_Exception, "'state_out' must be a list.");
        return sim_clean();
    }
    if((unsigned long)PyList_Size(state_out) != nx * ny * n_state) {
        PyErr_SetString(PyExc_Exception, "'state_out' must have size nx * ny * n_states.");
        return sim_clean();
    }

    //
    // Check inter_log list of intermediary variables to log
    //
    if(!PyList_Check(inter_log)) {
        PyErr_SetString(PyExc_Exception, "'inter_log' must be a list.");
        return sim_clean();
    }
    n_inter = PyList_Size(inter_log);

    //
    // Check field data
    //
    if(!PyList_Check(field_data)) {
        PyErr_SetString(PyExc_Exception, "'field_data' must be a list.");
        return sim_clean();
    }
    n_field_data = PyList_Size(field_data);

    //
    // Conductance mode
    //
    if((connections != Py_None) && (gx_field != Py_None)) {
        PyErr_SetString(PyExc_Exception, "Connections and conductance fields cannot be used together.");
        return sim_clean();
    }

    //
    // Set up pacing system
    //
    pacing = ESys_Create(&flag_pacing);
    if(flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
    flag_pacing = ESys_Populate(pacing, protocol);
    if(flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
    flag_pacing = ESys_AdvanceTime(pacing, tmin);
    if(flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
    tnext_pace = ESys_GetNextTime(pacing, NULL);
    engine_pace = ESys_GetLevel(pacing, NULL);
    arg_pace = (Real)engine_pace;

    //
    // Set simulation starting time
    //
    engine_time = tmin;
    arg_time = (Real)engine_time;

    //
    // Create opencl environment
    //

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Creating vectors.\n");
    #endif

    // Create state vector, set initial values
    dsize_state = nx * ny * n_state * sizeof(Real);
    rvec_state = (Real*)malloc(dsize_state);
    for(i=0; i<nx * ny * n_state; i++) {
        flt = PyList_GetItem(state_in, i);    // Don't decref!
        if(!PyFloat_Check(flt)) {
            char errstr[200];
            sprintf(errstr, "Item %u in state vector is not a float.", (unsigned int)i);
            PyErr_SetString(PyExc_Exception, errstr);
            return sim_clean();
        }
        rvec_state[i] = (Real)PyFloat_AsDouble(flt);
    }

    // Create diffusion current vector
    if (diffusion) {
        dsize_idiff = nx * ny * sizeof(Real);
        rvec_idiff = (Real*)malloc(dsize_idiff);
        for(i=0; i<nx * ny; i++) rvec_idiff[i] = 0.0;
    } else {
        dsize_idiff = sizeof(Real);
        rvec_idiff = (Real*)malloc(dsize_idiff);
        rvec_idiff[0] = 0.0;
    }

    // Create vector of intermediary variables to log
    if(n_inter) {
        dsize_inter_log = nx * ny * n_inter * sizeof(Real);
        rvec_inter_log = (Real*)malloc(dsize_inter_log);
        for(i=0; i<nx * ny * n_inter; i++) rvec_inter_log[i] = 0.0;
    } else {
        dsize_inter_log = sizeof(Real);
        rvec_inter_log = (Real*)malloc(dsize_inter_log);
        rvec_inter_log[0] = 0.0;
    }

    // Create vector of field data
    if(n_field_data) {
        dsize_field_data = n_field_data * sizeof(Real);
        rvec_field_data = (Real*)malloc(dsize_field_data);
        for(i=0; i<n_field_data; i++) {
            flt = PyList_GetItem(field_data, i);    // No need to decref
            if(!PyFloat_Check(flt)) {
                char errstr[200];
                sprintf(errstr, "Item %u in field data is not a float.", (unsigned int)i);
                PyErr_SetString(PyExc_Exception, errstr);
                return sim_clean();
            }
            rvec_field_data[i] = (Real)PyFloat_AsDouble(flt);
        }
    } else {
        dsize_field_data = sizeof(Real);
        rvec_field_data = (Real*)malloc(dsize_field_data);
        rvec_field_data[0] = 0.0;
    }

    // Conductance options
    if (gx_field != Py_None) {
        // Set up conductance fields
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("Setting up conductance fields.\n");
        #endif

        // Check gx field
        if (!PyList_Check(gx_field)) {
            PyErr_SetString(PyExc_Exception, "gx_field should be None or a list");
            return sim_clean();
        }
        if (PyList_Size(gx_field) != (Py_ssize_t)((nx - 1) * ny)) {
            PyErr_SetString(PyExc_Exception, "gx_field should have length (nx - 1) * ny");
            return sim_clean();
        }

        // Create vector
        dsize_gx = (nx - 1) * ny * sizeof(Real);
        rvec_gx = (Real*)malloc(dsize_gx);

        // Populate gx field vector
        for(i=0; i<(nx - 1)*ny; i++) {
            flt = PyList_GetItem(gx_field, i);   // Borrowed reference
            if(!PyFloat_Check(flt)) {
                PyErr_SetString(PyExc_Exception, "gx field must only contain floats");
                return sim_clean();
            }
            rvec_gx[i] = (Real)PyFloat_AsDouble(flt);
        }

        // Check gy field
        if (ny > 1) {
            if (!PyList_Check(gy_field)) {
                PyErr_SetString(PyExc_Exception, "gy_field should be a list");
                return sim_clean();
            }
            if (PyList_Size(gy_field) != (Py_ssize_t)((ny - 1) * nx)) {
                PyErr_SetString(PyExc_Exception, "gy_field should have length (ny - 1) * nx");
                return sim_clean();
            }

            // Create vector
            dsize_gy = (ny - 1) * nx * sizeof(Real);
            rvec_gy = (Real*)malloc(dsize_gy);

            // Populate gy field vector
            for(i=0; i<(ny - 1)*nx; i++) {
                flt = PyList_GetItem(gy_field, i);   // Borrowed reference
                if(!PyFloat_Check(flt)) {
                    PyErr_SetString(PyExc_Exception, "gy field must only contain floats");
                    return sim_clean();
                }
                rvec_gy[i] = (Real)PyFloat_AsDouble(flt);
            }
        } else {
            dsize_gy = sizeof(Real);
            rvec_gy = (Real*)malloc(dsize_gy);
            rvec_gy[0] = 0.0;
        }

    } else if(connections != Py_None) {
        // Set up arbitrary-geometry diffusion
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("Setting up connections.\n");
        #endif

        // Check connections list
        if(!PyList_Check(connections)) {
            PyErr_SetString(PyExc_Exception, "Connections should be None or a list");
            return sim_clean();
        }
        n_connections = PyList_Size(connections);

        dsize_conn1 = n_connections * sizeof(unsigned long);  // Same type as nx, ny, etc.
        dsize_conn2 = n_connections * sizeof(unsigned long);
        dsize_conn3 = n_connections * sizeof(Real);

        rvec_conn1 = (unsigned long*)malloc(dsize_conn1);
        rvec_conn2 = (unsigned long*)malloc(dsize_conn2);
        rvec_conn3 = (Real*)malloc(dsize_conn3);

        for(i=0; i<n_connections; i++) {
            flt = PyList_GetItem(connections, i);   // Borrowed reference
            if(!PyTuple_Check(flt)) {
                PyErr_SetString(PyExc_Exception, "Connections list must contain all tuples");
                return sim_clean();
            }
            if(PyTuple_Size(flt) != 3) {
                PyErr_SetString(PyExc_Exception, "Connections list must contain only 3-tuples");
                return sim_clean();
            }

            ret = PyTuple_GetItem(flt, 0);  // Borrowed reference
            if(PyLong_Check(ret)) {
                rvec_conn1[i] = (unsigned long)PyLong_AsLong(ret);
            #if PY_MAJOR_VERSION < 3
            } else if (PyInt_Check(ret)) {
                rvec_conn1[i] = (unsigned long)PyInt_AsLong(ret);
            #endif
            } else {
                PyErr_SetString(PyExc_Exception, "First item in each connection tuple must be int");
                return sim_clean();
            }

            ret = PyTuple_GetItem(flt, 1);  // Borrowed reference
            if(PyLong_Check(ret)) {
                rvec_conn2[i] = (unsigned long)PyLong_AsLong(ret);
            #if PY_MAJOR_VERSION < 3
            } else if(PyInt_Check(ret)) {
                rvec_conn2[i] = (unsigned long)PyInt_AsLong(ret);
            #endif
            } else {
                PyErr_SetString(PyExc_Exception, "Second item in each connection tuple must be int");
                return sim_clean();
            }

            ret = PyTuple_GetItem(flt, 2);  // Borrowed reference
            if(!PyFloat_Check(ret)) {
                PyErr_SetString(PyExc_Exception, "Third item in each connection tuple must be float");
                return sim_clean();
            }
            rvec_conn3[i] = (Real)PyFloat_AsDouble(ret);
        }
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created vectors.\n");
    #endif

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Setting work group sizes.\n");
    #endif
    // Work group size and total number of items
    global_work_size[0] = nx;
    global_work_size[1] = ny;
    if (connections != Py_None) {
        global_work_size_conn[0] = n_connections;
    }
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Work group sizes determined.\n");
    #endif

    // Get platform and device id
    if (mcl_select_device(platform_name, device_name, &platform_id, &device_id)) {
        // Error message set by mcl_select_device
        return sim_clean();
    }
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Selected platform and device id.\n");
    #endif

    // Query capabilities
    #ifdef MYOKIT_DOUBLE_PRECISION
    if (!mcl_platform_supports_extension(platform_id, "cl_khr_fp64")) {
        PyErr_WarnEx(PyExc_RuntimeWarning, "The OpenCL extension cl_khr_fp64 is required for double precision simulations, but was reported as unavailable on the current OpenCL platform/device.", 1);
    }
    if ((connections != Py_None) && (!mcl_platform_supports_extension(platform_id, "cl_khr_int64_base_atomics"))) {
        PyErr_WarnEx(PyExc_RuntimeWarning, "The OpenCL extension cl_khr_int64_base_atomics is required for double precision simulations with set_connections(), but was reported as unavailable on the current OpenCL platform/device.", 1);
    }
    #endif

    // Create a context and command queue
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Attempting to create OpenCL context...\n");
    #endif
    cl_context_properties context_properties[] = { CL_CONTEXT_PLATFORM, (cl_context_properties)platform_id, 0};
    context = clCreateContext(context_properties, 1, &device_id, NULL, NULL, &flag);
    if(mcl_flag2("context", flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created context.\n");
    #endif

    // Create command queue
    command_queue = clCreateCommandQueue(context, device_id, 0, &flag);
    if(mcl_flag2("queue", flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created command queue.\n");
    #endif

    // Create memory buffers on the device
    mbuf_state = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_state, NULL, &flag);
    if(mcl_flag2("dsize_state", flag)) return sim_clean();
    mbuf_idiff = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_idiff, NULL, &flag);
    if(mcl_flag2("dsize_diff", flag)) return sim_clean();
    mbuf_inter_log = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_inter_log, NULL, &flag);
    if(mcl_flag2("dsize_inter_log", flag)) return sim_clean();
    mbuf_field_data = clCreateBuffer(context, CL_MEM_READ_ONLY, dsize_field_data, NULL, &flag);
    if(mcl_flag2("dsize_field_data", flag)) return sim_clean();
    if(gx_field != Py_None) {
        mbuf_gx = clCreateBuffer(context, CL_MEM_READ_ONLY, dsize_gx, NULL, &flag);
        if(mcl_flag(flag)) return sim_clean();
        mbuf_gy = clCreateBuffer(context, CL_MEM_READ_ONLY, dsize_gy, NULL, &flag);
        if(mcl_flag(flag)) return sim_clean();
    } else if(connections != Py_None) {
        mbuf_conn1 = clCreateBuffer(context, CL_MEM_READ_ONLY, dsize_conn1, NULL, &flag);
        if(mcl_flag(flag)) return sim_clean();
        mbuf_conn2 = clCreateBuffer(context, CL_MEM_READ_ONLY, dsize_conn2, NULL, &flag);
        if(mcl_flag(flag)) return sim_clean();
        mbuf_conn3 = clCreateBuffer(context, CL_MEM_READ_ONLY, dsize_conn3, NULL, &flag);
        if(mcl_flag(flag)) return sim_clean();
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created buffers.\n");
    printf("State buffer size: %d.\n", (int)dsize_state);
    printf("Idiff buffer size: %d.\n", (int)dsize_idiff);
    printf("Inter-log buffer size: %d.\n", (int)dsize_inter_log);
    printf("Field-data buffer size: %d.\n", (int)dsize_field_data);
    printf("Gx field buffer size: %d.\n", (int)dsize_gx);
    printf("Gy field buffer size: %d.\n", (int)dsize_gy);
    printf("Connections-1 buffer size: %d.\n", (int)dsize_conn1);
    printf("Connections-2 buffer size: %d.\n", (int)dsize_conn2);
    printf("Connections-3 buffer size: %d.\n", (int)dsize_conn3);
    #endif

    /* Copy data into buffers */
    /* Note: using non-blocking writes here, and then waiting for it below (manual queue flush/finish) */
    flag = clEnqueueWriteBuffer(command_queue, mbuf_state, CL_FALSE, 0, dsize_state, rvec_state, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    flag = clEnqueueWriteBuffer(command_queue, mbuf_idiff, CL_FALSE, 0, dsize_idiff, rvec_idiff, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    flag = clEnqueueWriteBuffer(command_queue, mbuf_inter_log, CL_FALSE, 0, dsize_inter_log, rvec_inter_log, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    flag = clEnqueueWriteBuffer(command_queue, mbuf_field_data, CL_FALSE, 0, dsize_field_data, rvec_field_data, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    if (gx_field != Py_None) {
        flag = clEnqueueWriteBuffer(command_queue, mbuf_gx, CL_FALSE, 0, dsize_gx, rvec_gx, 0, NULL, NULL);
        if(mcl_flag(flag)) return sim_clean();
        flag = clEnqueueWriteBuffer(command_queue, mbuf_gy, CL_FALSE, 0, dsize_gy, rvec_gy, 0, NULL, NULL);
        if(mcl_flag(flag)) return sim_clean();
    } else if(connections != Py_None) {
        flag = clEnqueueWriteBuffer(command_queue, mbuf_conn1, CL_FALSE, 0, dsize_conn1, rvec_conn1, 0, NULL, NULL);
        if(mcl_flag(flag)) return sim_clean();
        flag = clEnqueueWriteBuffer(command_queue, mbuf_conn2, CL_FALSE, 0, dsize_conn2, rvec_conn2, 0, NULL, NULL);
        if(mcl_flag(flag)) return sim_clean();
        flag = clEnqueueWriteBuffer(command_queue, mbuf_conn3, CL_FALSE, 0, dsize_conn3, rvec_conn3, 0, NULL, NULL);
        if(mcl_flag(flag)) return sim_clean();
    }
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Enqueued copying of data into buffers.\n");
    #endif

    // Wait for copying to be finished
    clFlush(command_queue);
    clFinish(command_queue);
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Command queue flushed.\n");
    #endif

    // Load and compile the program
    program = clCreateProgramWithSource(context, 1, (const char**)&kernel_source, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Program created.\n");
    #endif
    sprintf(options, "");
    //sprintf(options, "-w"); // Suppress warnings
    flag = clBuildProgram(program, 1, &device_id, options, NULL, NULL);
    if(flag == CL_BUILD_PROGRAM_FAILURE) {
        // Build failed, extract log
        clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, 0, NULL, &blog_size);
        blog = (char*)malloc(blog_size);
        clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, blog_size, blog, NULL);
        fprintf(stderr, "OpenCL Error: Kernel failed to compile.\n");
        fprintf(stderr, "----------------------------------------");
        fprintf(stderr, "---------------------------------------\n");
        fprintf(stderr, "%s\n", blog);
        fprintf(stderr, "----------------------------------------");
        fprintf(stderr, "---------------------------------------\n");
        free(blog);
    }
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Program built.\n");
    #endif

    // Create the kernels
    kernel_cell = clCreateKernel(program, "cell_step", &flag);
    if(mcl_flag(flag)) return sim_clean();
    if(connections != Py_None) {
        // Arbitrary geometry
        kernel_arb_reset = clCreateKernel(program, "diff_arb_reset", &flag);
        if(mcl_flag(flag)) return sim_clean();
        kernel_arb_step = clCreateKernel(program, "diff_arb_step", &flag);
        if(mcl_flag(flag)) return sim_clean();
    } else if (gx_field != Py_None) {
        // Rectangular grid, heterogeneous conduction
        kernel_cond = clCreateKernel(program, "diff_hetero", &flag);
        if(mcl_flag(flag)) return sim_clean();
    } else if (diffusion) {
        // Rectangular grid, homogeneous conduction
        kernel_diff = clCreateKernel(program, "diff_step", &flag);
        if(mcl_flag(flag)) return sim_clean();
    }
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Kernels created.\n");
    #endif

    // Pass arguments into kernels
    i = 0;
    if(mcl_flag(clSetKernelArg(kernel_cell, i++, sizeof(nx), &nx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, i++, sizeof(ny), &ny))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, i++, sizeof(arg_time), &arg_time))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, i++, sizeof(arg_dt), &arg_dt))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, i++, sizeof(arg_pace), &arg_pace))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, i++, sizeof(mbuf_state), &mbuf_state))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, i++, sizeof(mbuf_idiff), &mbuf_idiff))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, i++, sizeof(mbuf_inter_log), &mbuf_inter_log))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, i++, sizeof(mbuf_field_data), &mbuf_field_data))) return sim_clean();

    // Calculate initial diffusion current
    if(connections != Py_None) {
        // Arbitrary geometry
        i = 0;
        if(mcl_flag(clSetKernelArg(kernel_arb_reset, i++, sizeof(nx), &nx))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_arb_reset, i++, sizeof(mbuf_idiff), &mbuf_idiff))) return sim_clean();
        i = 0;
        if(mcl_flag(clSetKernelArg(kernel_arb_step, i++, sizeof(n_connections), &n_connections))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_arb_step, i++, sizeof(mbuf_conn1), &mbuf_conn1))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_arb_step, i++, sizeof(mbuf_conn2), &mbuf_conn2))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_arb_step, i++, sizeof(mbuf_conn3), &mbuf_conn3))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_arb_step, i++, sizeof(mbuf_state), &mbuf_state))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_arb_step, i++, sizeof(mbuf_idiff), &mbuf_idiff))) return sim_clean();
    } else if (gx_field != Py_None) {
        // Heteogeneous, rectangular diffusion
        i = 0;
        if(mcl_flag(clSetKernelArg(kernel_cond, i++, sizeof(nx), &nx))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cond, i++, sizeof(ny), &ny))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cond, i++, sizeof(mbuf_gx), &mbuf_gx))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cond, i++, sizeof(mbuf_gy), &mbuf_gy))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cond, i++, sizeof(mbuf_state), &mbuf_state))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cond, i++, sizeof(mbuf_idiff), &mbuf_idiff))) return sim_clean();
    } else if (diffusion) {
        // Homogeneous, rectangular diffusion
        i = 0;
        if(mcl_flag(clSetKernelArg(kernel_diff, i++, sizeof(nx), &nx))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_diff, i++, sizeof(ny), &ny))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_diff, i++, sizeof(arg_gx), &arg_gx))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_diff, i++, sizeof(arg_gy), &arg_gy))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_diff, i++, sizeof(mbuf_state), &mbuf_state))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_diff, i++, sizeof(mbuf_idiff), &mbuf_idiff))) return sim_clean();
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Arguments passed into kernels.\n");
    #endif

    //
    // Set up logging system
    //

    if(!PyDict_Check(log_dict)) {
        PyErr_SetString(PyExc_Exception, "Log argument must be a dict.");
        return sim_clean();
    }
    n_vars = PyDict_Size(log_dict);
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Number of variables to log:%u.\n", (unsigned int)n_vars);
    #endif
    logs = (PyObject**)malloc(sizeof(PyObject*)*n_vars); // Pointers to logging lists
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Allocated log pointers:.\n");
    #endif
    vars = (Real**)malloc(sizeof(Real*)*n_vars); // Pointers to variables to log
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Allocated var pointers.\n");
    #endif

    // Number of variables in log
    k_vars = 0;

    // Time and pace are set globally
<?
var = model.binding('time')
print(tab + 'k_vars += log_add(log_dict, logs, vars, k_vars, "' + var.qname() + '", &arg_time);')
var = model.binding('pace')
if var is not None:
    print(tab + 'k_vars += log_add(log_dict, logs, vars, k_vars, "' + var.qname() + '", &arg_pace);')
?>

    // Diffusion current
    logging_diffusion = 0;
    for(i=0; i<ny; i++) {
        for(j=0; j<nx; j++) {
<?
var = model.binding('diffusion_current')
if var is not None:
    if dims == 1:
        print(3*tab + 'sprintf(log_var_name, "%u.' + var.qname() + '", (unsigned int)j);')
    else:
        print(3*tab + 'sprintf(log_var_name, "%u.%u.' + var.qname() + '", (unsigned int)j, (unsigned int)i);')
    print(3*tab + 'if(log_add(log_dict, logs, vars, k_vars, log_var_name, &rvec_idiff[i*nx+j])) {')
    print(4*tab + 'logging_diffusion = 1;')
    print(4*tab + 'k_vars++;')
    print(3*tab + '}')
?>
        }
    }

    // States
    logging_states = 0;
    for(i=0; i<ny; i++) {
        for(j=0; j<nx; j++) {
<?
for var in model.states():
    if dims == 1:
        print(3*tab + 'sprintf(log_var_name, "%u.' + var.qname() + '", (unsigned int)j);')
    else:
        print(3*tab + 'sprintf(log_var_name, "%u.%u.' + var.qname() + '", (unsigned int)j, (unsigned int)i);' )
    print(3*tab + 'if(log_add(log_dict, logs, vars, k_vars, log_var_name, &rvec_state[(i*nx+j)*n_state+' + str(var.indice()) + '])) {')
    print(4*tab + 'logging_states = 1;')
    print(4*tab + 'k_vars++;')
    print(3*tab + '}')
?>
        }
    }

    // Intermediary variables
    logging_inters = 0;
    for(i=0; i<ny; i++) {
        for(j=0; j<nx; j++) {
            for(k=0; k<n_inter; k++) {
                ret = PyList_GetItem(inter_log, k); // Don't decref
<?
if dims == 1:
    print(4*tab + 'sprintf(log_var_name, "%u.%s", (unsigned int)j, PyBytes_AsString(ret));')
else:
    print(4*tab + 'sprintf(log_var_name, "%u.%u.%s", (unsigned int)j, (unsigned int)i, PyBytes_AsString(ret));')

print(4*tab + 'if(log_add(log_dict, logs, vars, k_vars, log_var_name, &rvec_inter_log[(i*nx+j)*n_inter+k])) {')
print(5*tab + 'logging_inters = 1;')
print(5*tab + 'k_vars++;')
print(4*tab + '}')
?>
            }
        }
    }
    ret = NULL;

    /* Check if log contained extra variables */
    if(k_vars != n_vars) {
        PyErr_SetString(PyExc_Exception, "Unknown variables found in logging dictionary.");
        return sim_clean();
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created log for %u variables.\n", (unsigned int)n_vars);
    #endif

    /* Log update method: */
    list_update_str = PyUnicode_FromString("append");

    /* First point to step to */
    istep = 1;

    /* Next logging position: current time */
    inext_log = 0;
    tnext_log = tmin;

    /*
     * Done!
     */
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Finished initialization.\n");
    #endif
    Py_RETURN_NONE;
}

/*
 * Takes the next steps in a simulation run
 */
static PyObject*
sim_step(PyObject *self, PyObject *args)
{
    ESys_Flag flag_pacing;
    long steps_left_in_run;
    cl_int flag;
    unsigned long i;
    double d;
    int logging_condition;

    steps_left_in_run = 500 + 200000 / (nx * ny);
    if(steps_left_in_run < 1000) steps_left_in_run = 1000;
    d = 0;
    logging_condition = 0;

    while(1) {

        /* Check if we need to log at this point in time */
        logging_condition = (engine_time >= tnext_log);

        /* Determine next timestep, ensuring next event is simulated */
        intermediary_step = 0;
        dt = tmin + (double)istep * default_dt - engine_time;
        d = tmax - engine_time; if (d > dt_min && d < dt) {dt = d; intermediary_step = 1; }
        d = tnext_pace - engine_time; if (d > dt_min && d < dt) {dt = d; intermediary_step = 1; }
        d = tnext_log - engine_time; if (d > dt_min && d < dt) {dt = d; intermediary_step = 1; }
        if (!intermediary_step) istep++;
        arg_dt = (Real)dt;

        /* Update diffusion current, calculating it for time t */
        if(connections != Py_None) {
            /* Arbitrary geometry */
            if(mcl_flag2("kernel_arb_reset", clEnqueueNDRangeKernel(command_queue, kernel_arb_reset, 2, NULL, global_work_size, NULL, 0, NULL, NULL))) return sim_clean();
            if(mcl_flag2("kernel_arb_step", clEnqueueNDRangeKernel(command_queue, kernel_arb_step, 1, NULL, global_work_size_conn, NULL, 0, NULL, NULL))) return sim_clean();
        } else if (gx_field != Py_None) {
            /* Heterogeneous rectangular diffusion */
            if(mcl_flag2("kernel_cond", clEnqueueNDRangeKernel(command_queue, kernel_cond, 2, NULL, global_work_size, NULL, 0, NULL, NULL))) return sim_clean();
        } else if (diffusion) {
            /* Homogeneous rectangular diffusion */
            if(mcl_flag2("kernel_diff", clEnqueueNDRangeKernel(command_queue, kernel_diff, 2, NULL, global_work_size, NULL, 0, NULL, NULL))) return sim_clean();
        }

        /* Logging at time t? Then download the state from the device */
        if(logging_condition && logging_states) {
            /* Note the 3d argument CL_TRUE ensures this is a "blocking_read" */
            /* i.e. the call doesn't return until the copying has completed, */
            /* we don't need to manually flush/finish the command queue */
            flag = clEnqueueReadBuffer(command_queue, mbuf_state, CL_TRUE, 0, dsize_state, rvec_state, 0, NULL, NULL);
            if(mcl_flag(flag)) return sim_clean();

            /* Check for NaNs in the state */
            if(isnan(rvec_state[0])) {
                halt_sim = 1;
            }
        }

        /* Calculate intermediary variables at t, update device states to t+dt */
        if(mcl_flag(clSetKernelArg(kernel_cell, 2, sizeof(Real), &arg_time))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell, 3, sizeof(Real), &arg_dt))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell, 4, sizeof(Real), &arg_pace))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_cell, 2, NULL, global_work_size, NULL, 0, NULL, NULL))) return sim_clean();

        /* At this point, we have
         *  - engine_time  : the time t
         *  - engine_pace  : the pacing signal at t
         *  - rvec_state   : The state at t
         *  - device state : The state at t+dt
         *  - device inter : The intermediary variables at t
         *  - device diff  : The diffusion currents at t
         */

        /* Log situation at time t */
        if(logging_condition) {
            /* Download diffusion at time t from device */
            if(logging_diffusion) {
                flag = clEnqueueReadBuffer(command_queue, mbuf_idiff, CL_TRUE, 0, dsize_idiff, rvec_idiff, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();
            }

            /* Download intermediary variables at time t from device */
            if(logging_inters) {
                flag = clEnqueueReadBuffer(command_queue, mbuf_inter_log, CL_TRUE, 0, dsize_inter_log, rvec_inter_log, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();
            }

            /* Write everything to the log */
            for(i=0; i<n_vars; i++) {
                flt = PyFloat_FromDouble(*vars[i]);
                ret = PyObject_CallMethodObjArgs(logs[i], list_update_str, flt, NULL);
                Py_CLEAR(flt);
                Py_XDECREF(ret);
                if(ret == NULL) {
                    PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                    return sim_clean();
                }
            }
            ret = NULL;

            /* Set next logging point */
            inext_log++;
            tnext_log = tmin + (double)inext_log * log_interval;

            /* Check for overflow in inext_log */
            /* Note: Unsigned int wraps around instead of overflowing, becomes zero again */
            if (inext_log == 0) {
                PyErr_SetString(PyExc_Exception, "Overflow in logged step count: Simulation too long!");
                return sim_clean();
            }
        }

        /* Update time, advancing it to t+dt */
        engine_time += dt;
        arg_time = (Real)engine_time;

        /* Update pacing system, advancing it to t+dt */
        flag_pacing = ESys_AdvanceTime(pacing, engine_time);
        if (flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
        tnext_pace = ESys_GetNextTime(pacing, NULL);
        engine_pace = ESys_GetLevel(pacing, NULL);
        arg_pace = (Real)engine_pace;

        /* Check if we're finished
         * Do this before logging, to ensure we don't log the final time position!
         * Logging with fixed time steps should always be half-open: including the
         * first but not the last point in time.
         */
        if(engine_time >= tmax || halt_sim) break;

        /* Perform any Python signal handling */
        if (PyErr_CheckSignals() != 0) {
            /* Exception (e.g. timeout or keyboard interrupt) occurred?
               Then cancel everything! */
            return sim_clean();
        }

        /* Report back to python */
        if(--steps_left_in_run == 0) {
            /* For some reason, this clears memory */
            clFlush(command_queue);
            clFinish(command_queue);
            return PyFloat_FromDouble(engine_time);
        }
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Simulation finished.\n");
    #endif

    /* Set final state (at engine_time) --> blocking read */
    flag = clEnqueueReadBuffer(command_queue, mbuf_state, CL_TRUE, 0, dsize_state, rvec_state, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    for(i=0; i<n_state*nx*ny; i++) {
        PyList_SetItem(state_out, i, PyFloat_FromDouble(rvec_state[i]));
        /* PyList_SetItem steals a reference: no need to decref the double! */
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Final state copied.\n");
    printf("Tyding up...\n");
    #endif

    sim_clean();    /* Ignore return value */

    if (halt_sim) {
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("Finished tidiying up, ending simulation with nan.\n");
        #endif
        PyErr_SetString(PyExc_ArithmeticError, "Encountered nan in simulation.");
        return 0;
    } else {
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("Finished tidiying up, ending simulation.\n");
        #endif
        return PyFloat_FromDouble(engine_time);
    }
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
    {"sim_init", sim_init, METH_VARARGS, "Initialize the simulation."},
    {"sim_step", sim_step, METH_NOARGS, "Perform the next step in the simulation."},
    {"sim_clean", py_sim_clean, METH_NOARGS, "Clean up after an aborted simulation."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "<?= module_name ?>",       /* m_name */
        "Generated OpenCL sim module",   /* m_doc */
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
