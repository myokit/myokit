<?
# opencl_heun.c
#
# A pype template for opencl driven 1d or 2d simulations, using Heun's method
# instead of Euler's.
#
# Required variables
# -----------------------------------------------------------------------------
# module_name     A module name
# model           A myokit model, cloned with independent components
# vmvar           The model variable bound to membrane potential (must be part
#                 of the state)
# precision       A myokit precision constant
# bound_variables A dict of the bound variables
# dims            The number of dimensions, either 1 or 2
# -----------------------------------------------------------------------------
#
# This file is part of Myokit
#  Copyright 2011-2014 Michael Clerx, Maastricht University
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import myokit
import myokit.formats.opencl as opencl

tab = '    '
?>
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "pacing.h"
#include "mcl.h"

// Show debug output
//#define MYOKIT_DEBUG

#define n_state <?= str(model.count_states()) ?>

typedef <?= ('float' if precision == myokit.SINGLE_PRECISION else 'double') ?> Real;

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
static int log_add(PyObject* log_dict, PyObject** logs, Real** vars, int i, char* name, const Real* var)
{
    int added = 0;
    PyObject* key = PyString_FromString(name);
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
char* kernel_source;    // The kernel code
int nx;                 // The number of cells in the x direction
int ny;                 // The number of cells in the y direction
double gx;              // The cell-to-cell conductance in the x direction
double gy;              // The cell-to-cell conductance in the y direction
double tmin;            // The initial simulation time
double tmax;            // The final simulation time
double default_dt;      // The default time between steps
PyObject* state_in;     // The initial state
PyObject* state_out;    // The final state
PyObject *protocol;     // A pacing protocol
int nx_paced;           // The number of cells to stimulate in the x direction
int ny_paced;           // The number of cells to stimulate in the y direction
PyObject *log_dict;     // A logging dict
double log_interval;    // The time between log writes

// OpenCL objects
cl_context context = NULL;
cl_command_queue command_queue = NULL;
cl_program program = NULL;
cl_kernel kernel_cell;
cl_kernel kernel_diff;
cl_kernel kernel_feul;
cl_kernel kernel_heun;
cl_mem mbuf_y = NULL;
cl_mem mbuf_y2 = NULL;
cl_mem mbuf_dy = NULL;
cl_mem mbuf_dy2 = NULL;
cl_mem mbuf_idiff = NULL;

// Input vectors to kernels
Real *rvec_state = NULL;
Real *rvec_idiff = NULL;
int dsize_state;
int dsize_idiff;

// Timing
double engine_time;     // The current simulation time
double dt;              // The next step size
double tnext_pace;      // The next pacing event start/stop
double tnext_log;       // The next logging point
double dt_min;          // The minimal time increase

// Pacing
PSys pacing = NULL;
double engine_pace = 0;

// OpenCL work group size
size_t lws[2]; 
size_t lws2;
// Total number of work items rounded up to a multiple of the local size
size_t gws[2];
size_t gws2;

// Total number of cells and states
int n_total;

// Kernel arguments copied into "Real" type
Real arg_time;
Real arg_pace;
Real arg_dt;
Real arg_gx;
Real arg_gy;

// Logging
PyObject** logs = NULL; // An array of pointers to a PyObject
Real** vars = NULL;     // An array of pointers to values to log
int n_vars;             // Number of logging variables
double tlog;            // Time of next logging point (for periodic logging)
int logging_diffusion;  // True if diffusion current is being logged.
int logging_states;     // True if any states are being logged

// Temporary objects: decref before re-using for another var
// (Unless you got it through PyList_GetItem or PyTuble_GetItem)
PyObject* flt = NULL;               // PyFloat, various uses
PyObject* ret = NULL;               // PyFloat, used as return value
PyObject* list_update_str = NULL;   // PyString, ssed to call "append" method

/*
 * Cleans up after a simulation
 *
 */
static PyObject*
sim_clean()
{
    if(running) {
        #ifdef MYOKIT_DEBUG
        printf("Cleaning.\n");
        #endif

        // Wait for any remaining commands to finish        
        clFlush(command_queue);
        clFinish(command_queue);
    
        // Release all opencl objects (ignore errors due to null pointers)
        clReleaseMemObject(mbuf_y);
        clReleaseMemObject(mbuf_y2);
        clReleaseMemObject(mbuf_dy);
        clReleaseMemObject(mbuf_dy2);
        clReleaseMemObject(mbuf_idiff);
        clReleaseKernel(kernel_cell);
        clReleaseKernel(kernel_diff);
        clReleaseKernel(kernel_feul);
        clReleaseKernel(kernel_heun);
        clReleaseProgram(program);
        clReleaseCommandQueue(command_queue);
        clReleaseContext(context);
        
        // Free pacing system memory
        PSys_Destroy(pacing);
        
        // Free dynamically allocated arrays
        free(rvec_state);
        free(rvec_idiff);
        free(logs);
        free(vars);
        
        // No longer running
        running = 0;
    }
    #ifdef MYOKIT_DEBUG
    else
    {
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
    #ifdef MYOKIT_DEBUG
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
    #ifdef MYOKIT_DEBUG
    printf("Starting initialization.\n");
    #endif

    // Check if already running
    if(running != 0) {
        PyErr_SetString(PyExc_Exception, "Simulation already initialized.");
        return 0;
    }

    // Check input arguments
    if(!PyArg_ParseTuple(args, "siidddddOOOiiOd",
            &kernel_source,
            &nx,
            &ny,
            &gx,
            &gy,
            &tmin,
            &tmax,
            &default_dt,
            &state_in,
            &state_out,
            &protocol,
            &nx_paced,
            &ny_paced,
            &log_dict,
            &log_interval
            )) {
        PyErr_SetString(PyExc_Exception, "Wrong number of arguments.");
        // Nothing allocated yet, no pyobjects _created_, return directly
        return 0;
    }
    dt = default_dt;
    dt_min = dt * 1e-2;
    arg_dt = (Real)dt;
    arg_gx = (Real)gx;
    arg_gy = (Real)gy;
    n_total = nx * ny * n_state;
    
    // Reset all pointers
    rvec_state = NULL;
    rvec_idiff = NULL;
    logs = NULL;
    vars = NULL;
    flt = NULL;
    ret = NULL;
    list_update_str = NULL;
    pacing = NULL;

    // Get device id //
    cl_int flag;
    cl_device_id device_id = mcl_get_device_id();
    if(device_id == 0) {
        // Error message set by mcl_get_device_id
        return 0;
    } else {
        // Write info message
	    char buffer[65536];
        flag = clGetDeviceInfo(device_id, CL_DEVICE_NAME, sizeof(buffer), buffer, NULL);
        if(mcl_flag(flag)) return 0;
        printf("Using device: %s\n", buffer);
    }
    
    // Now officialy running :)
    running = 1;
    
    ///////////////////////////////////////////////////////////////////////////
    //
    // From this point on, use "return sim_clean()" to abort.
    //
    //
    
    int i, j;
    
    //
    // Check state in and out lists 
    //
    if(!PyList_Check(state_in)) {
        PyErr_SetString(PyExc_Exception, "'state_in' must be a list.");
        return sim_clean();
    }
    if(PyList_Size(state_in) != n_total) {
        PyErr_SetString(PyExc_Exception, "'state_in' must have size nx * ny * n_states.");
        return sim_clean();
    }
    if(!PyList_Check(state_out)) {
        PyErr_SetString(PyExc_Exception, "'state_out' must be a list.");
        return sim_clean();
    }
    if(PyList_Size(state_out) != n_total) {
        PyErr_SetString(PyExc_Exception, "'state_out' must have size nx * ny * n_states.");
        return sim_clean();
    }

    //
    // Set up pacing system
    //
    PSys_Flag flag_pacing;
    pacing = PSys_Create(&flag_pacing);
    if(flag_pacing!=PSys_OK) { PSys_SetPyErr(flag_pacing); return sim_clean(); }
    flag_pacing = PSys_Populate(pacing, protocol);
    if(flag_pacing!=PSys_OK) { PSys_SetPyErr(flag_pacing); return sim_clean(); }
    flag_pacing = PSys_AdvanceTime(pacing, tmin, tmax);
    if(flag_pacing!=PSys_OK) { PSys_SetPyErr(flag_pacing); return sim_clean(); }
    tnext_pace = PSys_GetNextTime(pacing, NULL);
    engine_pace = PSys_GetLevel(pacing, NULL);
    arg_pace = (Real)engine_pace;
    
    //
    // Set simulation starting time 
    //
    engine_time = tmin;
    arg_time = (Real)engine_time;

    //
    // Create opencl environment
    //
    
    // Work group size and total number of items
    // TODO: Set this in a more sensible way (total must be less than CL_DEVICE_MAX_WORK_GROUP_SIZE in clDeviceGetInfo)
    lws[0] = 8;    
    lws[1] = (ny > 1) ? 8 : 1;
    gws[0] = mcl_round_total_size(lws[0], nx);
    gws[1] = mcl_round_total_size(lws[1], ny);
    lws2 = 8;
    gws2 = mcl_round_total_size(lws2, n_total);
    
    // Create state vector, set initial values
    dsize_state = n_total * sizeof(Real);
    rvec_state = (Real*)malloc(dsize_state);
    for(i=0; i<n_total; i++) {
        flt = PyList_GetItem(state_in, i);    // Don't decref! 
        if(!PyFloat_Check(flt)) {
            char errstr[200];
            sprintf(errstr, "Item %d in state vector is not a float.", i);
            PyErr_SetString(PyExc_Exception, errstr);
            return sim_clean();
        }
        rvec_state[i] = (Real)PyFloat_AsDouble(flt);
    }
    
    // Create diffusion current vector and copy to device
    dsize_idiff = nx*ny * sizeof(Real);
    rvec_idiff = (Real*)malloc(dsize_idiff);
    for(i=0; i<nx*ny; i++) rvec_idiff[i] = 0.0;
    
    #ifdef MYOKIT_DEBUG
    printf("Created vectors.\n");
    #endif

    // Create a context and command queue
    context = clCreateContext(NULL, 1, &device_id, NULL, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG
    printf("Created context.\n");
    #endif  

    // Create command queue
    command_queue = clCreateCommandQueue(context, device_id, 0, &flag);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG
    printf("Created command queue.\n");
    #endif  
        
    // Create memory buffers on the device
    mbuf_y = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_state, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_y2 = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_state, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_dy = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_state, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_dy2 = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_state, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    mbuf_idiff = clCreateBuffer(context, CL_MEM_READ_WRITE, dsize_idiff, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG
    printf("Created buffers.\n");
    #endif  

    // Copy data into buffers
    flag = clEnqueueWriteBuffer(command_queue, mbuf_y, CL_TRUE, 0, dsize_state, rvec_state, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    flag = clEnqueueWriteBuffer(command_queue, mbuf_idiff, CL_TRUE, 0, dsize_idiff, rvec_idiff, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG
    printf("Enqueued data into buffers.\n");
    #endif
    
    // Load and compile the kernel program(s)
    program = clCreateProgramWithSource(context, 1, (const char**)&kernel_source, NULL, &flag);
    if(mcl_flag(flag)) return sim_clean();    
    flag = clBuildProgram(program, 1, &device_id, NULL, NULL, NULL);
    if(flag == CL_BUILD_PROGRAM_FAILURE) {
        // Build failed, extract log
        size_t blog_size;
        clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, 0, NULL, &blog_size);
        char *blog = (char*)malloc(blog_size);
        clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, blog_size, blog, NULL);
        fprintf(stderr, "OpenCL Error: Kernel failed to compile.\n");
        fprintf(stderr, "----------------------------------------");
        fprintf(stderr, "---------------------------------------\n");
        fprintf(stderr, "%s\n", blog);
        fprintf(stderr, "----------------------------------------");
        fprintf(stderr, "---------------------------------------\n");
    }
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG
    printf("Program created and built.\n");
    #endif
    
    // Create the kernels
    kernel_diff = clCreateKernel(program, "diff_step", &flag);
    if(mcl_flag(flag)) return sim_clean();
    kernel_cell = clCreateKernel(program, "cell_step", &flag);
    if(mcl_flag(flag)) return sim_clean();
    kernel_feul = clCreateKernel(program, "feul_step", &flag);
    if(mcl_flag(flag)) return sim_clean();
    kernel_heun = clCreateKernel(program, "heun_step", &flag);
    if(mcl_flag(flag)) return sim_clean();
    #ifdef MYOKIT_DEBUG
    printf("Kernels created.\n");
    #endif

    // Pass arguments into kernels

    if(mcl_flag(clSetKernelArg(kernel_diff, 0, sizeof(nx), &nx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff, 1, sizeof(ny), &ny))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff, 2, sizeof(arg_gx), &arg_gx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff, 3, sizeof(arg_gy), &arg_gy))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff, 4, sizeof(mbuf_y), &mbuf_y))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_diff, 5, sizeof(mbuf_idiff), &mbuf_idiff))) return sim_clean();
    
    if(mcl_flag(clSetKernelArg(kernel_cell, 0, sizeof(nx), &nx))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, 1, sizeof(ny), &ny))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, 2, sizeof(arg_time), &arg_time))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, 3, sizeof(nx_paced), &nx_paced))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, 4, sizeof(ny_paced), &ny_paced))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, 5, sizeof(arg_pace), &arg_pace))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, 6, sizeof(mbuf_y), &mbuf_y))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, 7, sizeof(mbuf_dy), &mbuf_dy))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_cell, 8, sizeof(mbuf_idiff), &mbuf_idiff))) return sim_clean();

    if(mcl_flag(clSetKernelArg(kernel_feul, 0, sizeof(n_total), &n_total))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_feul, 1, sizeof(arg_dt), &arg_dt))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_feul, 2, sizeof(mbuf_y), &mbuf_y))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_feul, 3, sizeof(mbuf_y2), &mbuf_y2))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_feul, 4, sizeof(mbuf_dy), &mbuf_dy))) return sim_clean();

    if(mcl_flag(clSetKernelArg(kernel_heun, 0, sizeof(n_total), &n_total))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_heun, 1, sizeof(arg_dt), &arg_dt))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_heun, 2, sizeof(mbuf_y), &mbuf_y))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_heun, 3, sizeof(mbuf_dy), &mbuf_dy))) return sim_clean();
    if(mcl_flag(clSetKernelArg(kernel_heun, 4, sizeof(mbuf_dy2), &mbuf_dy2))) return sim_clean();

    #ifdef MYOKIT_DEBUG
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
    logs = (PyObject**)malloc(sizeof(PyObject*)*n_vars); // Pointers to logging lists 
    vars = (Real**)malloc(sizeof(Real*)*n_vars); // Pointers to variables to log 

    char log_var_name[1023];    // Variable names
    int k_vars = 0;             // Counting number of variables in log

    // Time and pace are set globally
<?
for var in model.bindings_for('time'):
    print(tab + 'k_vars += log_add(log_dict, logs, vars, k_vars, "' + var.qname() + '", &arg_time);')
for var in model.bindings_for('pace'):
    print(tab + 'k_vars += log_add(log_dict, logs, vars, k_vars, "' + var.qname() + '", &arg_pace);')
?>

    // Diffusion current
    logging_diffusion = 0;
    for(i=0; i<ny; i++) {
        for(j=0; j<nx; j++) {
<?
for var in model.bindings_for('diffusion_current'):
    if dims == 1:
        print(3*tab + 'sprintf(log_var_name, "%d.' + var.qname() + '", j);')
    else:
        print(3*tab + 'sprintf(log_var_name, "%d.%d.' + var.qname() + '", j, i);')
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
        print(3*tab + 'sprintf(log_var_name, "%d.' + var.qname() + '", j);')
    else:
        print(3*tab + 'sprintf(log_var_name, "%d.%d.' + var.qname() + '", j, i);' )
    print(3*tab + 'if(log_add(log_dict, logs, vars, k_vars, log_var_name, &rvec_state[(i*nx+j)*n_state+' + str(var.indice()) + '])) {')
    print(4*tab + 'logging_states = 1;')
    print(4*tab + 'k_vars++;')
    print(3*tab + '}')
?>
        }
    }

    // Check if log contained extra variables 
    if(k_vars != n_vars) {
        PyErr_SetString(PyExc_Exception, "Unknown variables found in logging dictionary.");
        return sim_clean();
    }
    
    #ifdef MYOKIT_DEBUG
    printf("Created log for %d variables.\n", n_vars);
    #endif  
    
    // Store initial position in logs
    list_update_str = PyString_FromString("append");
    for(i=0; i<n_vars; i++) {
        flt = PyFloat_FromDouble(*vars[i]);
        ret = PyObject_CallMethodObjArgs(logs[i], list_update_str, flt, NULL);
        Py_DECREF(flt);
        Py_XDECREF(ret);
        if(ret == NULL) {
            PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
            return sim_clean();
        }
    }
    
    // Next logging position
    tnext_log = engine_time + log_interval;

    //
    // Done!
    //
    #ifdef MYOKIT_DEBUG
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
    long steps_left_in_run = 500 / (0.01 * nx * ny);
    if(steps_left_in_run < 10) steps_left_in_run = 10;
    cl_int flag;
    int i;
    double d = 0;
    while(1) {
    
        // Update cells, advancing them to t+dt
        // 1. Evaluate idiff for y
        if(mcl_flag(clSetKernelArg(kernel_diff, 4, sizeof(mbuf_y), &mbuf_y))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_diff, 5, sizeof(mbuf_idiff), &mbuf_idiff))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_diff, 2, NULL, gws, lws, 0, NULL, NULL))) return sim_clean();
        // 2. Evaluate derivatives f(y)
        if(mcl_flag(clSetKernelArg(kernel_cell, 2, sizeof(arg_time), &arg_time))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell, 5, sizeof(arg_pace), &arg_pace))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell, 6, sizeof(mbuf_y), &mbuf_y))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell, 7, sizeof(mbuf_dy), &mbuf_dy))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_cell, 2, NULL, gws, lws, 0, NULL, NULL))) return sim_clean();
        // 3. Update time, advancing it to t+dt
        // Note: Pacing is kept as it was. If the system is about to hit a
        // pacing discontinuity, the solution predicted by Heun won't be more
        // accurate if we take the situation at y2+pacing into account. Instead
        // we use a modified y2' with pacing kept as it was at y.
        engine_time += dt;
        arg_time = (Real)engine_time;
        // 4. Calculate y2 = y + dt*f(y)
        if(mcl_flag(clSetKernelArg(kernel_feul, 1, sizeof(arg_dt), &arg_dt))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_feul, 1, NULL, &gws2, &lws2, 0, NULL, NULL))) return sim_clean();
        // 5. Evaluate idiff for y2
        if(mcl_flag(clSetKernelArg(kernel_diff, 4, sizeof(mbuf_y2), &mbuf_y2))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_diff, 5, sizeof(mbuf_idiff), &mbuf_idiff))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_diff, 2, NULL, gws, lws, 0, NULL, NULL))) return sim_clean();
        // 6. Evaluate derivatives f(y2)
        if(mcl_flag(clSetKernelArg(kernel_cell, 2, sizeof(arg_time), &arg_time))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell, 6, sizeof(mbuf_y2), &mbuf_y2))) return sim_clean();
        if(mcl_flag(clSetKernelArg(kernel_cell, 7, sizeof(mbuf_dy2), &mbuf_dy2))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_cell, 2, NULL, gws, lws, 0, NULL, NULL))) return sim_clean();
        // 4. Calculate y = y + 0.5*dt*(dy + dy2)
        if(mcl_flag(clSetKernelArg(kernel_heun, 1, sizeof(arg_dt), &arg_dt))) return sim_clean();
        if(mcl_flag(clEnqueueNDRangeKernel(command_queue, kernel_heun, 1, NULL, &gws2, &lws2, 0, NULL, NULL))) return sim_clean();
        
        // Advance pacing mechanism, advancing it to t+dt
        PSys_AdvanceTime(pacing, engine_time, tmax);
        tnext_pace = PSys_GetNextTime(pacing, NULL);
        engine_pace = PSys_GetLevel(pacing, NULL);
        arg_pace = (Real)engine_pace;
        
        // Log new situation at t+dt
        if(engine_time >= tnext_log) {
            if(logging_diffusion) {
                flag = clEnqueueReadBuffer(command_queue, mbuf_idiff, CL_TRUE, 0, dsize_idiff, rvec_idiff, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();
            }
            if(logging_states) {
                flag = clEnqueueReadBuffer(command_queue, mbuf_y, CL_TRUE, 0, dsize_state, rvec_state, 0, NULL, NULL);
                if(mcl_flag(flag)) return sim_clean();
            }
            for(i=0; i<n_vars; i++) {
                flt = PyFloat_FromDouble(*vars[i]);
                ret = PyObject_CallMethodObjArgs(logs[i], list_update_str, flt, NULL);
                Py_DECREF(flt);
                Py_XDECREF(ret);
                if(ret == NULL) {
                    PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                    return sim_clean();
                }
            }
            tnext_log += log_interval;
        }

        // Check if we're finished
        if(engine_time >= tmax) break;
        
        // Determine next timestep
        // Ensure next pacing event is simulated.
        // Taking too small a step can be dangerous, so ignore tnext_log
        // Also, tnext_log is allowed be zero to log each step.
        dt = default_dt;
        d = tmax - engine_time; if(d > dt_min && d < dt) dt = d;
        d = tnext_pace - engine_time; if(d > dt_min && d < dt) dt = d;
        arg_dt = (Real)dt;
                
        // Report back to python
        if(--steps_left_in_run == 0) {
            return PyFloat_FromDouble(engine_time);
        }
    }

    #ifdef MYOKIT_DEBUG
    printf("Simulation finished.\n");
    #endif  

    // Set final state
    flag = clEnqueueReadBuffer(command_queue, mbuf_y, CL_TRUE, 0, dsize_state, rvec_state, 0, NULL, NULL);
    if(mcl_flag(flag)) return sim_clean();
    for(i=0; i<n_total; i++) {
        PyList_SetItem(state_out, i, PyFloat_FromDouble(rvec_state[i]));
        // PyList_SetItem steals a reference: no need to decref the double!
    }
    
    #ifdef MYOKIT_DEBUG
    printf("Final state copied.\n");
    #endif  

    // Finish any remaining commands (shouldn't happen)
    clFlush(command_queue);
    clFinish(command_queue);

    sim_clean();    // Ignore return value
    
    #ifdef MYOKIT_DEBUG
    printf("Tidied up, ending simulation.\n");
    #endif  
    return PyFloat_FromDouble(engine_time);
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
    {"sim_init", sim_init, METH_VARARGS, "Initialize the simulation."},
    {"sim_step", sim_step, METH_VARARGS, "Perform the next step in the simulation."},
    {"sim_clean", py_sim_clean, METH_VARARGS, "Clean up after an aborted simulation."},
    {NULL},
};

/*
 * Module definition
 */
PyMODINIT_FUNC
init<?=module_name?>(void) {
    (void) Py_InitModule("<?= module_name ?>", SimMethods);
}
