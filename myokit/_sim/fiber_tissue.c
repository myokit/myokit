<?
# Fiber tissue simulation using OpenCL
#
# Required variables
# -----------------------------------------------------------------------------
# module_name     A module name
# modelf          A myokit model for the fiber, cloned and with independent
#                 components
# modelt          A myokit model for the tissue, cloned and with independent
#                 components
# vmf             The fiber model variable bound to membrane potential (must be
#                 part of the state)
# vmt             The tissue model variable bound to membrane potential (must
#                 be part of the state)
# boundf          A dict of the bound variables for the fiber model
# boundt          A dict of the bound variables for the tissue model
# precision       A myokit precision constant
# native_math     True if the native maths functions should be used
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

#define n_state_f <?= str(modelf.count_states()) ?>
#define n_state_t <?= str(modelt.count_states()) ?>

typedef <?= ('float' if precision == myokit.SINGLE_PRECISION else 'double') ?> Real;

/*
 * Print function that uses python's stdout
 * (Adapted from http://stackoverflow.com/a/2420977/423420)
 *
 * Not optimised for performance. Use this sparingly!
 */
void pyprint(const char* text)
{
    PyObject *s, *o, *r;
    s = PyImport_ImportModuleNoBlock("sys");
    o = PyObject_GetAttrString(s, "stdout");
    r = PyObject_CallMethod(o, "write", "s", text);
    Py_XDECREF(r);
    Py_XDECREF(o);
    Py_XDECREF(s);
}

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

// Input arguments
PyObject *platform_name;// A python string specifying the platform to use
PyObject *device_name;  // A python string specifying the device to use
char* kernel_source_f;  // The kernel code for the fiber model
char* kernel_source_t;  // The kernel code for the tissue model
unsigned long nfx;      // The number of cells in the x direction (fiber)
unsigned long nfy;      // The number of cells in the y direction (fiber)
unsigned long ntx;      // The number of cells in the x direction (tissue)
unsigned long nty;      // The number of cells in the y direction (tissue)
int i_vm_f;             // The state index of the membrane potential (fiber)
int i_vm_t;             // The state index of the membrane potential (tissue)
double gfx;             // The cell-to-cell conductance in the fiber direction
double gfy;             // The cell-to-cell conductance in the fiber direction
double gtx;             // The cell-to-cell conductance in the x direction
double gty;             // The cell-to-cell conductance in the y direction
double gft;             // The fiber-to-tissue cell conductance
double tmin;            // The initial simulation time
double tmax;            // The final simulation time
double default_dt;      // The default time between steps
PyObject* state_in_f;   // The initial state (fiber)
PyObject* state_in_t;   // The initial state (tissue)
PyObject* state_out_f;  // The final state (fiber)
PyObject* state_out_t;  // The final state (tissue)
PyObject *protocol;     // A pacing protocol
unsigned long cfx;      // The x-coord. on the fiber where the tissue connects
unsigned long ctx;      // The x-coord. on the tissue where the fiber connects
unsigned long cty;      // The first connected y-coord. on the tissue
PyObject *log_dict_f;   // A logging dict for the fiber
PyObject *log_dict_t;   // A logging dict for the tissue
double log_interval;    // The time between log writes
PyObject *inter_log_f;  // A list of intermediary fiber variables to log
PyObject *inter_log_t;  // A list of intermediary tissue variables to log

// OpenCL objects
cl_context context = NULL;
cl_command_queue command_queue = NULL;
cl_program program_f = NULL;
cl_program program_t = NULL;
cl_kernel kernel_cell_f = NULL;
cl_kernel kernel_cell_t = NULL;
cl_kernel kernel_diff_f = NULL;
cl_kernel kernel_diff_t = NULL;
cl_kernel kernel_diff_ft = NULL;
cl_mem mbuf_state_f = NULL;
cl_mem mbuf_state_t = NULL;
cl_mem mbuf_idiff_f = NULL;
cl_mem mbuf_idiff_t = NULL;
cl_mem mbuf_inter_log_f = NULL;
cl_mem mbuf_inter_log_t = NULL;
cl_mem mbuf_field_data = NULL;

// Input vectors to kernels
Real *rvec_state_f;
Real *rvec_state_t;
Real *rvec_idiff_f;
Real *rvec_idiff_t;
Real *rvec_inter_log_f;
Real *rvec_inter_log_t;
size_t dsize_state_f;
size_t dsize_state_t;
size_t dsize_idiff_f;
size_t dsize_idiff_t;
size_t dsize_inter_log_f;
size_t dsize_inter_log_t;
size_t dsize_field_data;

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

/* OpenCL work group sizes */
size_t global_work_size_f[2];
size_t global_work_size_t[2];
/* Number of work items for the connection step */
size_t global_work_size_ft;

/* Kernel arguments copied into "Real" type */
Real arg_time;
Real arg_pace;
Real arg_dt;
Real arg_gfx;
Real arg_gfy;
Real arg_gtx;
Real arg_gty;
Real arg_gft;

/* Logging */
PyObject** logs_f;       // An array of pointers to a PyObject (fiber)
PyObject** logs_t;       // An array of pointers to a PyObject (tissue)
Real** vars_f;           // An array of pointers to values to log (fiber)
Real** vars_t;           // An array of pointers to values to log (tissue)
unsigned long n_vars_f;  // Number of logging variables (fiber)
unsigned long n_vars_t;  // Number of logging variables (tissue)
double tnext_log;        /* The next logging point */
unsigned long inext_log; // The number of logged steps
int logging_states_f;    // True if any states are being logged
int logging_states_t;    // True if any states are being logged
int logging_diffusion_f; // True if diffusion current is being logged.
int logging_diffusion_t; // True if diffusion current is being logged.
int logging_inters_f;    // True if any intermediary vars are being logged
int logging_inters_t;    // True if any intermediary vars are being logged
unsigned long n_inter_f; // The number of unique intermediary variables logged
unsigned long n_inter_t; // The number of unique intermediary variables logged

// Temporary objects: decref before re-using for another var
// (Unless you got it through PyList_GetItem or PyTuble_GetItem)
PyObject* flt;              // PyFloat, various uses
PyObject* ret;              // PyFloat, used as return value
PyObject* list_update_str;  // PyUnicode, used to call "append" method

/*
 * Cleans up after a simulation
 *
 */
static PyObject*
sim_clean()
{
    if(running) {
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("Cleaning.\n");
        #endif

        // Wait for any remaining commands to finish
        clFlush(command_queue);
        clFinish(command_queue);

        // Decref all opencl objects (ignore errors due to null pointers)
        clReleaseMemObject(mbuf_state_f); mbuf_state_f = NULL;
        clReleaseMemObject(mbuf_state_t); mbuf_state_t = NULL;
        clReleaseMemObject(mbuf_idiff_f); mbuf_idiff_f = NULL;
        clReleaseMemObject(mbuf_idiff_t); mbuf_idiff_t = NULL;
        clReleaseMemObject(mbuf_inter_log_f); mbuf_inter_log_f = NULL;
        clReleaseMemObject(mbuf_inter_log_t); mbuf_inter_log_t = NULL;
        clReleaseKernel(kernel_cell_f); kernel_cell_f = NULL;
        clReleaseKernel(kernel_cell_t); kernel_cell_t = NULL;
        clReleaseKernel(kernel_diff_f); kernel_diff_f = NULL;
        clReleaseKernel(kernel_diff_t); kernel_diff_t = NULL;
        clReleaseKernel(kernel_diff_ft); kernel_diff_ft = NULL;
        clReleaseProgram(program_f); program_f = NULL;
        clReleaseProgram(program_t); program_t = NULL;
        clReleaseCommandQueue(command_queue); command_queue = NULL;
        clReleaseContext(context); context = NULL;

        // Free pacing system memory
        ESys_Destroy(pacing); pacing = NULL;

        // Free dynamically allocated arrays
        free(rvec_state_f); rvec_state_f = NULL;
        free(rvec_state_t); rvec_state_t = NULL;
        free(rvec_idiff_f); rvec_idiff_f = NULL;
        free(rvec_idiff_t); rvec_idiff_t = NULL;
        free(rvec_inter_log_f); rvec_inter_log_f = NULL;
        free(rvec_inter_log_t); rvec_inter_log_t = NULL;
        free(logs_f); logs_f = NULL;
        free(logs_t); logs_t = NULL;
        free(vars_f); vars_f = NULL;
        free(vars_t); vars_t = NULL;

        // No longer need update string
        Py_XDECREF(list_update_str); list_update_str = NULL;

        // No longer running
        running = 0;
    }
    #ifdef MYOKIT_DEBUG_MESSAGES
    else {
        printf("Skipping cleaning: not running!");
    }
    #endif

    // Return 0, allowing the construct
    //  PyErr_SetString(PyExc_Exception, "Oh noes!");
    //  return sim_clean()
    //to terminate a python function.
    return 0;
}
static PyObject*
py_sim_clean()
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

    // Variable names
    char log_var_name[1023];
    unsigned long k_vars;

    // Compilation error message
    size_t blog_size;
    char *blog;

    // Cell coupling
    unsigned long nsf, nst;

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Starting initialization.\n");
    #endif

    // Check if already running
    if(running != 0) {
        PyErr_SetString(PyExc_Exception, "Simulation already initialized.");
        return 0;
    }

    // Set all pointers used by sim_clean to null
    list_update_str = NULL;
    command_queue = NULL;
    mbuf_state_f = NULL;
    mbuf_state_t = NULL;
    mbuf_idiff_f = NULL;
    mbuf_idiff_t = NULL;
    mbuf_inter_log_f = NULL;
    mbuf_inter_log_t = NULL;
    kernel_cell_f = NULL;
    kernel_cell_t = NULL;
    kernel_diff_f = NULL;
    kernel_diff_t = NULL;
    kernel_diff_ft = NULL;
    program_f = NULL;
    program_t = NULL;
    context = NULL;
    pacing = NULL;
    rvec_state_f = NULL;
    rvec_state_t = NULL;
    rvec_idiff_f = NULL;
    rvec_idiff_t = NULL;
    rvec_inter_log_f = NULL;
    rvec_inter_log_t = NULL;
    logs_f = NULL;
    logs_t = NULL;
    vars_f = NULL;
    vars_t = NULL;

    // Check input arguments
    if(!PyArg_ParseTuple(args, "OOsskkkkiidddddkkkdddOOOOOOOdOO",
            &platform_name,
            &device_name,
            &kernel_source_f,
            &kernel_source_t,
            &nfx,       // Small 'k' = unsigned long
            &nfy,
            &ntx,
            &nty,
            &i_vm_f,
            &i_vm_t,
            &gfx,
            &gfy,
            &gtx,
            &gty,
            &gft,
            &cfx,
            &ctx,
            &cty,
            &tmin,
            &tmax,
            &default_dt,
            &state_in_f,
            &state_in_t,
            &state_out_f,
            &state_out_t,
            &protocol,
            &log_dict_f,
            &log_dict_t,
            &log_interval,
            &inter_log_f,
            &inter_log_t
            )) {
        PyErr_SetString(PyExc_Exception, "Wrong number of arguments.");
        // Nothing allocated yet, no pyobjects _created_, return directly
        return 0;
    }
    dt = default_dt;
    dt_min = 0; /*dt * 1e-2; Not sure why this was >0. Causes issues with timing sometimes. */
    arg_dt = (Real)dt;
    arg_gfx = (Real)gfx;
    arg_gfy = (Real)gfy;
    arg_gtx = (Real)gtx;
    arg_gty = (Real)gty;
    arg_gft = (Real)gft;
    halt_sim = 0;

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Parsed input arguments.\n");
    #endif

    /*
        // Write info message
	    char buffer[65500];
	    char buffer2[65536];
        flag = clGetDeviceInfo(device_id, CL_DEVICE_NAME, sizeof(buffer), buffer, NULL);
        if(mcl_flag(flag)) return 0;
        sprintf(buffer2, "Using device: %s\n", buffer);
        pyprint(buffer2);
    */

    // Now officialy running :)
    running = 1;

    ///////////////////////////////////////////////////////////////////////////
    //
    // From this point on, use "return sim_clean()" to abort.
    //
    //

    //
    // Check state in and out lists
    //
    if(!PyList_Check(state_in_f)) {
        PyErr_SetString(PyExc_Exception, "'state_in_f' must be a list.");
        return sim_clean();
    }
    if(!PyList_Check(state_in_t)) {
        PyErr_SetString(PyExc_Exception, "'state_in_t' must be a list.");
        return sim_clean();
    }
    if(!PyList_Check(state_out_f)) {
        PyErr_SetString(PyExc_Exception, "'state_out_f' must be a list.");
        return sim_clean();
    }
    if(!PyList_Check(state_out_t)) {
        PyErr_SetString(PyExc_Exception, "'state_out_t' must be a list.");
        return sim_clean();
    }
    if((unsigned long)PyList_Size(state_in_f) != nfx * nfy * n_state_f) {
        PyErr_SetString(PyExc_Exception, "'state_in_f' must have size nfx * nfy * n_states_f.");
        return sim_clean();
    }
    if((unsigned long)PyList_Size(state_in_t) != ntx * nty * n_state_t) {
        PyErr_SetString(PyExc_Exception, "'state_in_t' must have size ntx * nty * n_states_t.");
        return sim_clean();
    }
    if((unsigned long)PyList_Size(state_out_f) != nfx * nfy * n_state_f) {
        PyErr_SetString(PyExc_Exception, "'state_out_f' must have size nfx * nfy * n_states_f.");
        return sim_clean();
    }
    if((unsigned long)PyList_Size(state_out_t) != ntx * nty * n_state_t) {
        PyErr_SetString(PyExc_Exception, "'state_out_t' must have size ntx * nty * n_states_t.");
        return sim_clean();
    }

    //
    // Check inter_log lists of intermediary variables to log
    //
    if(!PyList_Check(inter_log_f)) {
        PyErr_SetString(PyExc_Exception, "'inter_log_f' must be a list.");
        return sim_clean();
    }
    n_inter_f = PyList_Size(inter_log_f);
    if(!PyList_Check(inter_log_t)) {
        PyErr_SetString(PyExc_Exception, "'inter_log_t' must be a list.");
        return sim_clean();
    }
    n_inter_t = PyList_Size(inter_log_t);

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Checked input and output states.\n");
    #endif

    //
    // Set up pacing system
    //
    pacing = ESys_Create(tmin, &flag_pacing);
    if(flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
    flag_pacing = ESys_Populate(pacing, protocol);
    if(flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
    flag_pacing = ESys_AdvanceTime(pacing, tmin);
    if(flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
    tnext_pace = ESys_GetNextTime(pacing, NULL);
    engine_pace = ESys_GetLevel(pacing, NULL);
    arg_pace = (Real)engine_pace;

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Set up pacing system.\n");
    #endif

    //
    // Set simulation starting time
    //
    engine_time = tmin;
    arg_time = (Real)engine_time;

    //
    // Create opencl environment
    //

    // Work group size and total number of items
    // TODO: Check against CL_DEVICE_MAX_WORK_GROUP_SIZE in clDeviceGetInfo
    global_work_size_f[0] = nfx;
    global_work_size_f[1] = nfy;
    global_work_size_t[0] = ntx;
    global_work_size_t[1] = nty;
    global_work_size_ft = nfy;

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Global work sizes set.\n");
    #endif

    // Create state vectors, set initial values
    dsize_state_f = nfx * nfy * n_state_f * sizeof(Real);
    rvec_state_f = (Real*)malloc(dsize_state_f);
    for(i=0; i < nfx * nfy * n_state_f; i++) {
        flt = PyList_GetItem(state_in_f, i);    // Don't decref!
        if(!PyFloat_Check(flt)) {
            PyErr_Format(PyExc_Exception, "Item %u in fiber state vector is not a float.", (unsigned int)i);
            return sim_clean();
        }
        rvec_state_f[i] = (Real)PyFloat_AsDouble(flt);
    }
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created fiber state vector, set initial values.\n");
    #endif

    dsize_state_t = ntx * nty * n_state_t * sizeof(Real);
    rvec_state_t = (Real*)malloc(dsize_state_t);
    for(i=0; i < ntx * nty * n_state_t; i++) {
        flt = PyList_GetItem(state_in_t, i);
        if(!PyFloat_Check(flt)) {
            PyErr_Format(PyExc_Exception, "Item %u in tissue state vector is not a float.", (unsigned int)i);
            return sim_clean();
        }
        rvec_state_t[i] = (Real)PyFloat_AsDouble(flt);
    }
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created tissue state vector, set initial values.\n");
    #endif

    // Create diffusion current vectors, set initial values
    dsize_idiff_f = nfx * nfy * sizeof(Real);
    dsize_idiff_t = ntx * nty * sizeof(Real);
    rvec_idiff_f = (Real*)malloc(dsize_idiff_f);
    rvec_idiff_t = (Real*)malloc(dsize_idiff_t);
    for(i=0; i < nfx * nfy; i++) rvec_idiff_f[i] = 0.0;
    for(i=0; i < ntx * nty; i++) rvec_idiff_t[i] = 0.0;

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created diffusion vectors.\n");
    #endif

    // Create intermediary variable logging vectors
    dsize_inter_log_f = nfx * nfy * n_inter_f * sizeof(Real);
    dsize_inter_log_t = ntx * nty * n_inter_t * sizeof(Real);
    // Zero length buffers is not allowed:
    if(dsize_inter_log_f == 0) { dsize_inter_log_f = sizeof(Real); }
    if(dsize_inter_log_t == 0) { dsize_inter_log_t = sizeof(Real); }
    rvec_inter_log_f = (Real*)malloc(dsize_inter_log_f);
    rvec_inter_log_t = (Real*)malloc(dsize_inter_log_t);
    for(i=0; i < nfx * nfy * n_inter_f; i++) rvec_inter_log_f[i] = 0.0;
    for(i=0; i < ntx * nty * n_inter_t; i++) rvec_inter_log_t[i] = 0.0;

    // Unused heterogeneity vector
    dsize_field_data = sizeof(Real);

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created intermediary variable logging vectors.\n");
    #endif

    // Get platform and device id
    platform_id = NULL;
    device_id = NULL;
    if (mcl_select_device(platform_name, device_name, &platform_id, &device_id)) {
        // Error message set by mcl_select_device
        return sim_clean();
    }
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Selected platform and device id.\n");
    if (platform_id == NULL) {
        printf("No preferred platform set.\n");
    } else {
        printf("Preferred platform set.\n");
    }
    if (device_id == NULL) {
        printf("No preferred device set.\n");
    } else {
        printf("Preferred device set.\n");
    }
    #endif

    // Create a context and command queue
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Attempting to create OpenCL context...\n");
    #endif
    if (platform_id != NULL) {
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("Creating context with context_properties\n");
        #endif
        cl_context_properties context_properties[] =
            { CL_CONTEXT_PLATFORM, (cl_context_properties)platform_id, 0};
        context = clCreateContext(context_properties, 1, &device_id, NULL, NULL, &flag);
    } else {
        context = clCreateContext(NULL, 1, &device_id, NULL, NULL, &flag);
    }
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created context.\n");
    #endif

    /* Create command queue */
    command_queue = clCreateCommandQueue(context, device_id, 0, &flag);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created command queue.\n");
    #endif

    /* Create memory buffers on the device */
    mbuf_state_f = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_state_f, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_state_t = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_state_t, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_idiff_f = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_idiff_f, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_idiff_t = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_idiff_t, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_inter_log_f = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_inter_log_f, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_inter_log_t = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_inter_log_t, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_field_data = clCreateBuffer(context, CL_MEM_READ_ONLY, dsize_field_data, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created buffers.\n");
    #endif

    /* Copy data into buffers */
    /* Notice: Using blocking writes here */
    flag = clEnqueueWriteBuffer(command_queue, mbuf_state_f, CL_TRUE, 0, dsize_state_f, rvec_state_f, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    flag = clEnqueueWriteBuffer(command_queue, mbuf_state_t, CL_TRUE, 0, dsize_state_t, rvec_state_t, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    flag = clEnqueueWriteBuffer(command_queue, mbuf_idiff_f, CL_TRUE, 0, dsize_idiff_f, rvec_idiff_f, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    flag = clEnqueueWriteBuffer(command_queue, mbuf_idiff_t, CL_TRUE, 0, dsize_idiff_t, rvec_idiff_t, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    flag = clEnqueueWriteBuffer(command_queue, mbuf_inter_log_f, CL_TRUE, 0, dsize_inter_log_f, rvec_inter_log_f, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    flag = clEnqueueWriteBuffer(command_queue, mbuf_inter_log_t, CL_TRUE, 0, dsize_inter_log_t, rvec_inter_log_t, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Copied data into buffers.\n");
    #endif

    /* Load and compile the fiber program */
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Building fiber program on device...");
    #endif
    program_f = clCreateProgramWithSource(context, 1, (const char**)&kernel_source_f, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    flag = clBuildProgram(program_f, 1, &device_id, NULL, NULL, NULL);
    if(flag == CL_BUILD_PROGRAM_FAILURE) {
        /* Build failed, extract log */
        clGetProgramBuildInfo(program_f, device_id, CL_PROGRAM_BUILD_LOG, 0, NULL, &blog_size);
        blog = (char*)malloc(blog_size);
        clGetProgramBuildInfo(program_f, device_id, CL_PROGRAM_BUILD_LOG, blog_size, blog, NULL);
        fprintf(stderr, "OpenCL Error: Fiber kernel failed to compile.\n");
        fprintf(stderr, "----------------------------------------");
        fprintf(stderr, "---------------------------------------\n");
        fprintf(stderr, "%s\n", blog);
        fprintf(stderr, "----------------------------------------");
        fprintf(stderr, "---------------------------------------\n");
        free(blog);
    }
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("done\n");
    #endif

    /* Load and compile the tissue program */
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Building tissue program on device...");
    #endif
    program_t = clCreateProgramWithSource(context, 1, (const char**)&kernel_source_t, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    flag = clBuildProgram(program_t, 1, &device_id, NULL, NULL, NULL);
    if(flag == CL_BUILD_PROGRAM_FAILURE) {
        /* Build failed, extract log */
        clGetProgramBuildInfo(program_t, device_id, CL_PROGRAM_BUILD_LOG, 0, NULL, &blog_size);
        blog = (char*)malloc(blog_size);
        clGetProgramBuildInfo(program_t, device_id, CL_PROGRAM_BUILD_LOG, blog_size, blog, NULL);
        fprintf(stderr, "OpenCL Error: Tissue kernel failed to compile.\n");
        fprintf(stderr, "----------------------------------------");
        fprintf(stderr, "---------------------------------------\n");
        fprintf(stderr, "%s\n", blog);
        fprintf(stderr, "----------------------------------------");
        fprintf(stderr, "---------------------------------------\n");
        free(blog);
    }
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("done\n");
    #endif

    // Create the kernels
    kernel_cell_f = clCreateKernel(program_f, "cell_step", &flag);
    if(mcl_flag(flag)) return sim_clean();
    kernel_cell_t = clCreateKernel(program_t, "cell_step", &flag);
    if(mcl_flag(flag)) return sim_clean();
    kernel_diff_f = clCreateKernel(program_f, "diff_step", &flag);
    if(mcl_flag(flag)) return sim_clean();
    kernel_diff_t = clCreateKernel(program_t, "diff_step", &flag);
    if(mcl_flag(flag)) return sim_clean();
    kernel_diff_ft = clCreateKernel(program_f, "diff_step_fiber_tissue", &flag);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Kernels created.\n");
    #endif

    // Pass arguments into kernels
    i = 0;
    if(mcl_flag(clSetKernelArg(kernel_cell_f, i++, sizeof(nfx), &nfx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_f, i++, sizeof(nfy), &nfy))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_f, i++, sizeof(arg_time), &arg_time))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_f, i++, sizeof(arg_dt), &arg_dt))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_f, i++, sizeof(arg_pace), &arg_pace))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_f, i++, sizeof(mbuf_state_f), &mbuf_state_f))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_f, i++, sizeof(mbuf_idiff_f), &mbuf_idiff_f))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_f, i++, sizeof(mbuf_inter_log_f), &mbuf_inter_log_f))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_f, i++, sizeof(mbuf_field_data), &mbuf_field_data))) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Set up cell kernel for fiber model.\n");
    #endif

    i = 0;
    if(mcl_flag(clSetKernelArg(kernel_diff_f, i++, sizeof(nfx), &nfx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_f, i++, sizeof(nfy), &nfy))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_f, i++, sizeof(arg_gfx), &arg_gfx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_f, i++, sizeof(arg_gfy), &arg_gfy))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_f, i++, sizeof(mbuf_state_f), &mbuf_state_f))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_f, i++, sizeof(mbuf_idiff_f), &mbuf_idiff_f))) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Set up diffusion kernel for fiber model.\n");
    #endif

    i = 0;
    if(mcl_flag(clSetKernelArg(kernel_cell_t, i++, sizeof(ntx), &ntx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_t, i++, sizeof(nty), &nty))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_t, i++, sizeof(arg_time), &arg_time))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_t, i++, sizeof(arg_dt), &arg_dt))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_t, i++, sizeof(arg_pace), &arg_pace))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_t, i++, sizeof(mbuf_state_t), &mbuf_state_t))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_t, i++, sizeof(mbuf_idiff_t), &mbuf_idiff_t))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_t, i++, sizeof(mbuf_inter_log_t), &mbuf_inter_log_t))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell_t, i++, sizeof(mbuf_field_data), &mbuf_field_data))) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Set up cell kernel for tissue model.\n");
    #endif

    i = 0;
    if(mcl_flag(clSetKernelArg(kernel_diff_t, i++, sizeof(ntx), &ntx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_t, i++, sizeof(nty), &nty))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_t, i++, sizeof(arg_gtx), &arg_gtx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_t, i++, sizeof(arg_gty), &arg_gty))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_t, i++, sizeof(mbuf_state_t), &mbuf_state_t))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_t, i++, sizeof(mbuf_idiff_t), &mbuf_idiff_t))) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Set up diffusion kernel for tissue model.\n");
    #endif

    /* Set indices of coupled cell indexes in state and diff vectors */
    nsf = n_state_f;
    nst = n_state_t;
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  0, sizeof(nfx), &nfx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  1, sizeof(nfy), &nfy))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  2, sizeof(ntx), &ntx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  3, sizeof(ctx), &ctx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  4, sizeof(cty), &cty))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  5, sizeof(nsf), &nsf))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  6, sizeof(nst), &nst))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  7, sizeof(i_vm_f), &i_vm_f))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  8, sizeof(i_vm_t), &i_vm_t))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft,  9, sizeof(arg_gft), &arg_gft))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft, 10, sizeof(mbuf_state_f), &mbuf_state_f))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft, 11, sizeof(mbuf_state_t), &mbuf_state_t))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft, 12, sizeof(mbuf_idiff_f), &mbuf_idiff_f))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff_ft, 13, sizeof(mbuf_idiff_t), &mbuf_idiff_t))) return sim_clean();
    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Set up fiber-tissue diffusion kernel.\n");
    #endif

    /*
     * Set up logging system
     */

    if(!PyDict_Check(log_dict_f)) {
        PyErr_SetString(PyExc_Exception, "Fiber log argument must be a dict.");
        return sim_clean();
    }
    if(!PyDict_Check(log_dict_t)) {
        PyErr_SetString(PyExc_Exception, "Tissue log argument must be a dict.");
        return sim_clean();
    }
    n_vars_f = PyDict_Size(log_dict_f);
    n_vars_t = PyDict_Size(log_dict_t);
    logs_f = (PyObject**)malloc(sizeof(PyObject*)*n_vars_f); /* Pointers to logging lists */
    logs_t = (PyObject**)malloc(sizeof(PyObject*)*n_vars_t);
    vars_f = (Real**)malloc(sizeof(Real*)*n_vars_f); /* Pointers to variables to log */
    vars_t = (Real**)malloc(sizeof(Real*)*n_vars_t);

    /* Number of variables in log */
    k_vars = 0;

    /* Logging: Time and pacing are set globally (fiber) */
<?
var = modelf.time()
print(tab + 'k_vars += log_add(log_dict_f, logs_f, vars_f, k_vars, "' + var.qname() + '", &arg_time);')
var = modelf.binding('pace')
if var is not None:
    print(tab + 'k_vars += log_add(log_dict_f, logs_f, vars_f, k_vars, "' + var.qname() + '", &arg_pace);')
?>

    /* Logging: Diffusion current (fiber) */
    logging_diffusion_f = 0;
    for(i=0; i<nfy; i++) {
        for(j=0; j<nfx; j++) {
<?
var = modelf.binding('diffusion_current')
if var is not None:
    print(3*tab + 'sprintf(log_var_name, "%u.%u.' + var.qname() + '", (unsigned int)j, (unsigned int)i);')
    print(3*tab + 'if(log_add(log_dict_f, logs_f, vars_f, k_vars, log_var_name, &rvec_idiff_f[i*nfx+j])) {')
    print(4*tab + 'logging_diffusion_f = 1;')
    print(4*tab + 'k_vars++;')
    print(3*tab + '}')
?>
        }
    }

    /* Logging: States (fiber) */
    logging_states_f = 0;
    for(i=0; i<nfy; i++) {
        for(j=0; j<nfx; j++) {
<?
for var in modelf.states():
    print(3*tab + 'sprintf(log_var_name, "%u.%u.' + var.qname() + '", (unsigned int)j, (unsigned int)i);' )
    print(3*tab + 'if(log_add(log_dict_f, logs_f, vars_f, k_vars, log_var_name, &rvec_state_f[(i*nfx+j)*n_state_f+' + str(var.index()) + '])) {')
    print(4*tab + 'logging_states_f = 1;')
    print(4*tab + 'k_vars++;')
    print(3*tab + '}')
?>
        }
    }

    /* Logging: Intermediary variables (fiber) */
    logging_inters_f = 0;
    for(i=0; i<nfy; i++) {
        for(j=0; j<nfx; j++) {
            for(k=0; k<n_inter_f; k++) {
                ret = PyList_GetItem(inter_log_f, k); /* Don't decref */
<?
print(4*tab + 'sprintf(log_var_name, "%u.%u.%s", (unsigned int)j, (unsigned int)i, PyBytes_AsString(ret));')
print(4*tab + 'if(log_add(log_dict_f, logs_f, vars_f, k_vars, log_var_name, &rvec_inter_log_f[(i*nfx+j)*n_inter_f+k])) {')
print(5*tab + 'logging_inters_f = 1;')
print(5*tab + 'k_vars++;')
print(4*tab + '}')
?>
            }
        }
    }
    ret = NULL;

    /* Check if log contained extra variables (fiber) */
    if(k_vars != n_vars_f) {
        PyErr_SetString(PyExc_Exception, "Unknown variables found in fiber logging dictionary.");
        return sim_clean();
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created log for %u fiber variables.\n", (unsigned int)n_vars_f);
    #endif

    /* Now set up tissue logging */
    k_vars = 0;

    /* Logging: Time and pacing are set globally (tissue) */
<?
var = modelt.time()
print(tab + 'k_vars += log_add(log_dict_t, logs_t, vars_t, k_vars, "' + var.qname() + '", &arg_time);')
var = modelt.binding('pace')
if var is not None:
    print(tab + 'k_vars += log_add(log_dict_t, logs_t, vars_t, k_vars, "' + var.qname() + '", &arg_pace);')
?>

    /* Logging: Diffusion current (tissue) */
    logging_diffusion_t = 0;
    for(i=0; i<nty; i++) {
        for(j=0; j<ntx; j++) {
<?
var = modelt.binding('diffusion_current')
if var is not None:
    print(3*tab + 'sprintf(log_var_name, "%u.%u.' + var.qname() + '", (unsigned int)j, (unsigned int)i);')
    print(3*tab + 'if(log_add(log_dict_t, logs_t, vars_t, k_vars, log_var_name, &rvec_idiff_t[i*ntx+j])) {')
    print(4*tab + 'logging_diffusion_t = 1;')
    print(4*tab + 'k_vars++;')
    print(3*tab + '}')
?>
        }
    }

    /* Logging: States (tissue) */
    logging_states_t = 0;
    for(i=0; i<nty; i++) {
        for(j=0; j<ntx; j++) {
<?
for var in modelt.states():
    print(3*tab + 'sprintf(log_var_name, "%u.%u.' + var.qname() + '", (unsigned int)j, (unsigned int)i);' )
    print(3*tab + 'if(log_add(log_dict_t, logs_t, vars_t, k_vars, log_var_name, &rvec_state_t[(i*ntx+j)*n_state_t+' + str(var.index()) + '])) {')
    print(4*tab + 'logging_states_t = 1;')
    print(4*tab + 'k_vars++;')
    print(3*tab + '}')
?>
        }
    }

    /* Logging: Intermediary variables (tissue) */
    logging_inters_t = 0;
    for(i=0; i<nty; i++) {
        for(j=0; j<ntx; j++) {
            for(k=0; k<n_inter_t; k++) {
                ret = PyList_GetItem(inter_log_t, k); /* Don't decref */
<?
print(4*tab + 'sprintf(log_var_name, "%u.%u.%s", (unsigned int)j, (unsigned int)i, PyBytes_AsString(ret));')
print(4*tab + 'if(log_add(log_dict_t, logs_t, vars_t, k_vars, log_var_name, &rvec_inter_log_t[(i*ntx+j)*n_inter_t+k])) {')
print(5*tab + 'logging_inters_t = 1;')
print(5*tab + 'k_vars++;')
print(4*tab + '}')
?>
            }
        }
    }
    ret = NULL;

    /* Check if log contained extra variables (tissue) */
    if(k_vars != n_vars_t) {
        PyErr_SetString(PyExc_Exception, "Unknown variables found in tissue logging dictionary.");
        return sim_clean();
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Created log for %u tissue variables.\n", (unsigned int)n_vars_t);
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
    unsigned long steps_left_in_run;
    cl_int flag;
    unsigned long i;
    double d;
    int logging_condition;

    steps_left_in_run = 6e6 / (nfx * nfy + ntx * nty);
    if(steps_left_in_run < 40) steps_left_in_run = 40;
    d = 0;
    logging_condition = 0;

    while(1) {

        /* Check if we need to log at this point in time */
        logging_condition = engine_time >= tnext_log;

        /* Determine next timestep, ensuring next event is simulated */
        intermediary_step = 0;
        dt = tmin + (double)istep * default_dt - engine_time;
        d = tmax - engine_time; if (d > dt_min && d < dt) {dt = d; intermediary_step = 1; }
        d = tnext_pace - engine_time; if (d > dt_min && d < dt) {dt = d; intermediary_step = 1; }
        d = tnext_log - engine_time; if (d > dt_min && d < dt) {dt = d; intermediary_step = 1; }
        if (!intermediary_step) istep++;
        arg_dt = (Real)dt;

        /* Update diffusion current, calculating it for time t */
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_diff_f, 2, NULL, global_work_size_f, NULL, 0, NULL, NULL))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_diff_t, 2, NULL, global_work_size_t, NULL, 0, NULL, NULL))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_diff_ft, 1, NULL, &global_work_size_ft, NULL, 0, NULL, NULL))) return sim_clean();

        /* Logging at time t? Then download the states from the device */
        if(logging_condition) {
            if(logging_states_f) {
                /* 3d argument CL_TRUE = Blocking read */
                flag = clEnqueueReadBuffer(command_queue, mbuf_state_f, CL_TRUE, 0, dsize_state_f, rvec_state_f, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();

                /* Check for NaNs in the state */
                if(isnan(rvec_state_f[0])) { halt_sim = 1; }
            }
            if(logging_states_t) {
                flag = clEnqueueReadBuffer(command_queue, mbuf_state_t, CL_TRUE, 0, dsize_state_t, rvec_state_t, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();

                /* Check for NaNs in the state */
                if(isnan(rvec_state_t[0])) { halt_sim = 1; }
            }
        }

        /* Calculate intermediary variables at t, update states to t + dt */
        if(mcl_flag(clSetKernelArg(kernel_cell_f, 2, sizeof(Real), &arg_time))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell_f, 3, sizeof(Real), &arg_dt))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell_f, 4, sizeof(Real), &arg_pace))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_cell_f, 2, NULL, global_work_size_f, NULL, 0, NULL, NULL))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell_t, 2, sizeof(Real), &arg_time))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell_t, 3, sizeof(Real), &arg_dt))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell_t, 4, sizeof(Real), &arg_pace))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_cell_t, 2, NULL, global_work_size_t, NULL, 0, NULL, NULL))) return sim_clean();

        /* Log situation at time t (so just before the last update) */
        if(logging_condition) {
            /* Download diffusion at time t from device (blocking read) */
            if(logging_diffusion_f) {
                flag = clEnqueueReadBuffer(command_queue, mbuf_idiff_f, CL_TRUE, 0, dsize_idiff_f, rvec_idiff_f, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();
            }
            if(logging_diffusion_t) {
                flag = clEnqueueReadBuffer(command_queue, mbuf_idiff_t, CL_TRUE, 0, dsize_idiff_t, rvec_idiff_t, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();
            }

            /* Download intermediary variables at time t from device */
            if(logging_inters_f) {
                flag = clEnqueueReadBuffer(command_queue, mbuf_inter_log_f, CL_TRUE, 0, dsize_inter_log_f, rvec_inter_log_f, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();
            }
            if(logging_inters_t) {
                flag = clEnqueueReadBuffer(command_queue, mbuf_inter_log_t, CL_TRUE, 0, dsize_inter_log_t, rvec_inter_log_t, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();
            }

            /* Write everything to the logs */
            for(i=0; i<n_vars_f; i++) {
                flt = PyFloat_FromDouble(*vars_f[i]);
                ret = PyObject_CallMethodObjArgs(logs_f[i], list_update_str, flt, NULL);
                Py_DECREF(flt);
                Py_XDECREF(ret);
                if(ret == NULL) {
                    flt = NULL;
                    PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                    return sim_clean();
                }
            }
            flt = ret = NULL;
            for(i=0; i<n_vars_t; i++) {
                flt = PyFloat_FromDouble(*vars_t[i]);
                ret = PyObject_CallMethodObjArgs(logs_t[i], list_update_str, flt, NULL);
                Py_DECREF(flt); flt = NULL;
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

        /* Update pacing mechanism, advancing it to t+dt */
        flag_pacing = ESys_AdvanceTime(pacing, engine_time);
        if (flag_pacing!=ESys_OK) { ESys_SetPyErr(flag_pacing); return sim_clean(); }
        tnext_pace = ESys_GetNextTime(pacing, NULL);
        engine_pace = ESys_GetLevel(pacing, NULL);
        arg_pace = (Real)engine_pace;

        /* Check if we're finished */
        if(engine_time >= tmax || halt_sim) break;

        /* Perform any Python signal handling */
        if (PyErr_CheckSignals() != 0) {
            /* Exception (e.g. timeout or keyboard interrupt) occurred?
               Then cancel everything! */
            return sim_clean();
        }

        /* Report back to python */
        if(--steps_left_in_run == 0) {
            /* Clear some memory */
            clFlush(command_queue);
            clFinish(command_queue);
            return PyFloat_FromDouble(engine_time);
        }
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Simulation finished.\n");
    #endif

    /* Set final states */
    flag = clEnqueueReadBuffer(command_queue, mbuf_state_f, CL_TRUE, 0, dsize_state_f, rvec_state_f, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    for(i=0; i<nfx*nfy*n_state_f; i++) {
        PyList_SetItem(state_out_f, i, PyFloat_FromDouble(rvec_state_f[i]));
        /* PyList_SetItem steals a reference: no need to decref the double! */
    }
    flag = clEnqueueReadBuffer(command_queue, mbuf_state_t, CL_TRUE, 0, dsize_state_t, rvec_state_t, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    for(i=0; i<ntx*nty*n_state_t; i++) {
        PyList_SetItem(state_out_t, i, PyFloat_FromDouble(rvec_state_t[i]));
    }

    #ifdef MYOKIT_DEBUG_MESSAGES
    printf("Final state copied.\n");
    printf("Tyding up...\n");
    #endif

    /* Finish any remaining commands (shouldn't happen) */
    clFlush(command_queue);
    clFinish(command_queue);

    sim_clean();    /* Ignore return value */

    if (halt_sim) {
        #ifdef MYOKIT_DEBUG_MESSAGES
        printf("Finished tidiying up, ending simulation with nan.\n");
        #endif
        return PyFloat_FromDouble(tmin - 1);
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
        "Generated OpenCL FiberTissue sim module",   /* m_doc */
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
