/*
 * pacing.h
 *
 * Ansi-C implementation for event-based pacing (using a myokit.Protocol) and
 * time series pacing (using a myokit.TimeSeriesProtocol).
 *
 * How to use event-based pacing:
 *
 *  1. Create a pacing system using ESys_Create
 *  2. Populate it with events using ESys_Populate
 *  3. Set the time in the pacing system with ESys_AdvanceTime.
 *  4. Get the time of the first event with ESys_GetNextTime
 *  5. Get the initial pacing level with ESys_GetLevel
 *  6. Now at each step of a simulation
 *    - Advance the system to the simulation time with ESys_AdvanceTime
 *    - Get the time of the next event start or finish with ESys_GetNextTime
 *    - Get the pacing level using ESys_GetLevel
 *  7. Tidy up using ESys_Destroy
 *
 * Events must always start at t>=0, negative times are not supported.
 *
 * Flags are used to indicate errors. If a flag other than ESys_OK is set, a
 * call to ESys_SetPyErr(flag) can be made to set a Python exception.
 *
 * How to use time series pacing:
 *
 *  1. Create a pacing system using TSys_Create
 *  2. Populate it using two Python lists via TSys_Populate
 *  3. Obtain the pacing value for any time using TSys_GetLevel
 *  4. Tidy up using TSys_Destroy
 *
 * This file is part of Myokit.
 * See http://myokit.org for copyright, sharing, and licensing details.
 *
 */
#ifndef MyokitPacing
#define MyokitPacing

#include <Python.h>
#include <stdio.h>
#include <float.h>

/*
 * Event-based pacing error flags
 */
typedef int ESys_Flag;
#define ESys_OK                              0
#define ESys_OUT_OF_MEMORY                  -1
#define ESys_PYTHON_INTERRUPT               -2
// General
#define ESys_INVALID_SYSTEM                 -10
#define ESys_POPULATED_SYSTEM               -11
#define ESys_UNPOPULATED_SYSTEM             -12
// ESys_Populate
#define ESys_POPULATE_INVALID_PROTOCOL      -20
#define ESys_POPULATE_MISSING_ATTR          -21
#define ESys_POPULATE_INVALID_ATTR          -22
#define ESys_POPULATE_NON_ZERO_MULTIPLIER   -23
#define ESys_POPULATE_NEGATIVE_PERIOD       -24
#define ESys_POPULATE_NEGATIVE_MULTIPLIER   -25
// ESys_AdvanceTime
#define ESys_NEGATIVE_TIME_INCREMENT        -40
// ESys_ScheduleEvent
#define ESys_SIMULTANEOUS_EVENT             -50

/*
 * Calculates the absolute values of a and b and returns whatever's largest.
 */
#define ESys_scale(a, b) (fabs(a) > fabs(b) ? fabs(a) : fabs(b))

/*
 * Tests if `a` and `b` withing float rounding-error distance of each other
 */
#define ESys_eq(a, b) ((a == b) || (fabs(a - b) / ESys_scale(a, b) < DBL_EPSILON))

/*
 * Tests if `a > b` or if `a` and `b` are within float rounding-error distance
 * of each other.
 */
#define ESys_geq(a, b) ((a >= b) || ESys_eq(a, b))

/*
 * Sets a python exception based on an event-based pacing error flag.
 *
 * Arguments
 *  flag : The python error flag to base the message on.
 */
void
ESys_SetPyErr(ESys_Flag flag)
{
    PyObject *mod, *dict, *exception;
    switch(flag) {
    case ESys_OK:
        break;
    case ESys_OUT_OF_MEMORY:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Memory allocation failed.");
        break;
    case ESys_PYTHON_INTERRUPT:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Process interrupted by Python signal.");
        break;
    // General
    case ESys_INVALID_SYSTEM:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Invalid pacing system provided.");
        break;
    case ESys_POPULATED_SYSTEM:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Pacing system already populated.");
        break;
    case ESys_UNPOPULATED_SYSTEM:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Pacing system not populated.");
        break;
    // ESys_ScheduleEvent
    case ESys_SIMULTANEOUS_EVENT:
        mod = PyImport_ImportModule("myokit");   // New ref https://docs.python.org/3/c-api/import.html#c.PyImport_ImportModule
        dict = PyModule_GetDict(mod);            // Borrowed ref https://docs.python.org/3/c-api/module.html#c.PyModule_GetDict
        exception = PyDict_GetItemString(dict, "SimultaneousProtocolEventError");   // Borrowed ref
        PyErr_SetString(exception, "E-Pacing error: Event scheduled or re-occuring at the same time as another event.");
        Py_DECREF(mod);
        break;
    // ESys_Populate
    case ESys_POPULATE_INVALID_PROTOCOL:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Protocol.events() failed to return a list.");
        break;
    case ESys_POPULATE_MISSING_ATTR:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Missing event attribute.");
        break;
    case ESys_POPULATE_INVALID_ATTR:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Failed to convert event attribute to Float.");
        break;
    case ESys_POPULATE_NON_ZERO_MULTIPLIER:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Non-zero multiplier found for non-periodic stimulus.");
        break;
    case ESys_POPULATE_NEGATIVE_PERIOD:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Pacing event period cannot be negative.");
        break;
    case ESys_POPULATE_NEGATIVE_MULTIPLIER:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: Pacing event multiplier cannot be negative.");
        break;
    // ESys_AdvanceTime
    case ESys_NEGATIVE_TIME_INCREMENT:
        PyErr_SetString(PyExc_Exception, "E-Pacing error: New time is before current time.");
        break;
    // Unknown
    default:
        PyErr_Format(PyExc_Exception, "E-Pacing error: Unlisted error %d", (int)flag);
        break;
    };
}

/*
 * Pacing event
 *
 * Pacing event structs hold the information about a single pacing event. Using
 * the Event_Schedule function, pacing events can be ordered into an
 * event queue. Each event may appear only once in such a queue.
 *
 * Events have a starting time `start` at which they are "fired" and considered
 * "active" until a period of time `duration` has passed.
 *
 * Recurring events can be created by specifying a non-zero value of `period`.
 * The value `multiplier` is used to indicate how often an event should recur,
 * where 0 indicates the event repeats indefinitely.
 *
 * Recurring events are implemented as follows: once a recurring event has been
 * deactivated (at time `start` + `duration`), the event is removed from the
 * event queue. The `start` time and possible the `multiplier` are then updated
 * to the new values and the event is rescheduled back into the queue.
 */
struct ESys_Event_mem {
    double level;       // The stimulus level (non-zero, dimensionless, normal range [0,1])
    double duration;    // The stimulus duration
    double start;       // The time this stimulus starts
    double period;      // The period with which it repeats (or 0 if it doesn't)
    double multiplier;  // The number of times this period occurs (or 0 if it doesn't)
    double ostart;      // The event start set when the event was created
    double operiod;     // The period set when the event was created
    double omultiplier; // The multiplier set when the event was created
    struct ESys_Event_mem* next;
};
#define ESys_Event struct ESys_Event_mem*

/*
 * Adds an event to an event queue.
 *
 * Arguments
 *  head  : The head of the event queue
 *  event : The event to schedule
 *  flag : The address of a pacing error flag or NULL
 *
 * Returns the new head of the event queue
 */
static ESys_Event
ESys_ScheduleEvent(ESys_Event head, ESys_Event add, ESys_Flag* flag)
{
    ESys_Event e;    // Needs to be declared here for visual C
    *flag = ESys_OK;
    add->next = 0;
    if (add == 0) return head;
    if (head == 0) return add;
    if (add->start < head->start) {
        add->next = head;
        return add;
    }
    e = head;
    while(e->next != 0 && add->start >= e->next->start) {
        e = e->next;
    }
    if (add->start == e->start) {
        *flag = ESys_SIMULTANEOUS_EVENT;
    }
    add->next = e->next;
    e->next = add;
    return head;
}

/*
 * Pacing system
 */
struct ESys_Mem {
    Py_ssize_t n_events;    // The number of events in this system
    double time;            // The current time
    double initial_time;    // The initial time (used by reset)
    ESys_Event events;      // The events, stored as an array
    ESys_Event head;        // The head of the event queue
    ESys_Event fire;        // The currently active event
    double tnext;   // The time of the next event start or finish
    double tdown;   // The time the active event is over
    double level;   // The current output value
};
typedef struct ESys_Mem* ESys;

/*
 * Creates a pacing system
 *
 * Arguments
 *  flag : The address of an event-based pacing error flag or NULL
 *
 * Returns the newly created pacing system
 */
ESys
ESys_Create(double initial_time, ESys_Flag* flag)
{
    ESys sys = (ESys)malloc(sizeof(struct ESys_Mem));
    if (sys == 0) {
        if(flag != 0) *flag = ESys_OUT_OF_MEMORY;
        return 0;
    }

    sys->time = initial_time;
    sys->initial_time = initial_time;
    sys->n_events = -1; // Used to indicate unpopulated system
    sys->events = NULL;
    sys->head = NULL;
    sys->fire = NULL;
    sys->tnext = initial_time;
    sys->tdown = initial_time;
    sys->level = 0;

    if(flag != 0) *flag = ESys_OK;
    return sys;
}

/*
 * Destroys a pacing system and frees the memory it occupies.
 *
 * Arguments
 *  sys : The event-based pacing system to destroy
 *
 * Returns a pacing error flag.
 */
ESys_Flag
ESys_Destroy(ESys sys)
{
    if(sys == NULL) return ESys_INVALID_SYSTEM;
    if(sys->events != NULL) {
        free(sys->events);
        sys->events = NULL;
    }
    free(sys);
    return ESys_OK;
}

/*
 * Resets this pacing system to time=0.
 *
 * Arguments
 *  sys : The event-based pacing system to reset
 *
 * Returns a pacing error flag.
 */
ESys_Flag
ESys_Reset(ESys sys)
{
    ESys_Event next;     // Need to be declared here for C89 Visual C
    ESys_Event head;
    int i;
    ESys_Flag flag;

    if(sys == 0) return ESys_INVALID_SYSTEM;
    if(sys->n_events < 0) return ESys_UNPOPULATED_SYSTEM;

    // Reset all events
    next = sys->events;
    for(i=0; i<sys->n_events; i++) {
        next->start = next->ostart;
        next->period = next->operiod;
        next->multiplier = next->omultiplier;
        next->next = 0;
    }

    // Set up the event queue
    head = sys->events;
    next = head + 1;
    for(i=1; i<sys->n_events; i++) {
        head = ESys_ScheduleEvent(head, next++, &flag);
        if (flag != ESys_OK) { return flag; }
    }

    // Reset the properties of the event system
    sys->time = sys->initial_time;
    sys->head = head;
    sys->fire = 0;
    sys->tnext = sys->initial_time;
    sys->tdown = sys->initial_time;
    sys->level = 0;

    return ESys_OK;
}

/*
 * Populates an event system using the events from a myokit.Protocol
 * Returns an error if the system already contains events.
 *
 * Arguments
 *  sys      : The pacing system to schedule the events in.
 *  protocol : A pacing protocol or NULL
 *
 * Returns a pacing error flag.
 */
ESys_Flag
ESys_Populate(ESys sys, PyObject* protocol)
{
    int i;
    Py_ssize_t n;
    ESys_Event events;
    ESys_Event e;

    if(sys == 0) return ESys_INVALID_SYSTEM;
    if (sys->n_events != -1) return ESys_POPULATED_SYSTEM;

    // Default values
    n = 0;
    events = 0;

    if (protocol != Py_None) {

        // Get PyList from protocol (will need to decref!)
        PyObject* list = PyObject_CallMethod(protocol, "events", NULL); // Returns a new reference
        if(list == NULL) return ESys_POPULATE_INVALID_PROTOCOL;
        if(!PyList_Check(list)) {
            Py_DECREF(list);
            return ESys_POPULATE_INVALID_PROTOCOL;
        }
        n = PyList_Size(list);

        // Translate python pacing events
        // Note: A lot of the tests here shouldn't really make a difference,
        // since they are tested by the Python code already!
        if(n > 0) {
            PyObject *item, *attr;
            events = (ESys_Event)malloc((size_t)n * sizeof(struct ESys_Event_mem));
            e = events;
            for(i=0; i<n; i++) {
                item = PyList_GetItem(list, i); // Don't decref!
                // Level
                attr = PyObject_GetAttrString(item, "_level");
                if (attr == NULL) { // Not a string
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_MISSING_ATTR;
                }
                e->level = PyFloat_AsDouble(attr);
                Py_DECREF(attr); attr = NULL;
                if (PyErr_Occurred() != NULL) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_INVALID_ATTR;
                }

                // duration
                attr = PyObject_GetAttrString(item, "_duration");
                if (attr == NULL) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_MISSING_ATTR;
                }
                e->duration = PyFloat_AsDouble(attr);
                Py_DECREF(attr); attr = NULL;
                if (PyErr_Occurred() != NULL) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_INVALID_ATTR;
                }

                // start
                attr = PyObject_GetAttrString(item, "_start");
                if (attr == NULL) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_MISSING_ATTR;
                }
                e->start = PyFloat_AsDouble(attr);
                Py_DECREF(attr); attr = NULL;
                if (PyErr_Occurred() != NULL) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_INVALID_ATTR;
                }

                // Period
                attr = PyObject_GetAttrString(item, "_period");
                if (attr == NULL) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_MISSING_ATTR;
                }
                e->period = PyFloat_AsDouble(attr);
                Py_DECREF(attr); attr = NULL;
                if (PyErr_Occurred() != NULL) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_INVALID_ATTR;
                }

                // multiplier
                attr = PyObject_GetAttrString(item, "_multiplier");
                if (attr == NULL) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_MISSING_ATTR;
                }
                e->multiplier = PyFloat_AsDouble(attr);
                Py_DECREF(attr); attr = NULL;
                if (PyErr_Occurred() != NULL) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_INVALID_ATTR;
                }

                // Original values
                e->ostart = e->start;
                e->operiod = e->period;
                e->omultiplier = e->multiplier;
                e->next = 0;
                if (e->period == 0 && e->multiplier != 0) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_NON_ZERO_MULTIPLIER;
                }
                if (e->period < 0) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_NEGATIVE_PERIOD;
                }
                if (e->multiplier < 0) {
                    free(events); Py_DECREF(list);
                    return ESys_POPULATE_NEGATIVE_MULTIPLIER;
                }
                e++;
            }
        }

        /* Finished with list */
        Py_DECREF(list);
    }

    // Add the events to the system
    sys->n_events = n;
    sys->events = events;

    // Set all remaining properties using reset
    return ESys_Reset(sys);
}

/*
 * Advances the pacing system to the next moment in time.
 *
 * Arguments
 *  sys      : The pacing system to advance.
 *  new_time : The time to increment the system to. Must be more than or equal
 *             to the current pacing system time.
 *
 * Returns a pacing error flag.
 */
ESys_Flag
ESys_AdvanceTime(ESys sys, double new_time)
{
    ESys_Flag flag;     /* Need to be declared here for C89 Visual C */
    if(sys == 0) return ESys_INVALID_SYSTEM;
    if(sys->n_events < 0) return ESys_UNPOPULATED_SYSTEM;

    /* Check new_time isn't in the past */
    if(new_time < sys->time) return ESys_NEGATIVE_TIME_INCREMENT;

    /* Update internal time */
    sys->time = new_time;

    /* Advance */
    while (ESys_geq(sys->time, sys->tnext)) {

        /* Active event finished */
        if (sys->fire != 0 && ESys_geq(sys->tnext, sys->tdown)) {
            sys->fire = 0;
            sys->level = 0;
        }

        /* New event starting */
        if (sys->head != 0 && ESys_geq(sys->tnext, sys->head->start)) {
            sys->fire = sys->head;
            sys->head = sys->head->next;
            sys->tdown = sys->fire->start + sys->fire->duration;
            sys->level = sys->fire->level;

            /* Reschedule recurring event */
            if (sys->fire->period > 0) {
                if (sys->fire->multiplier != 1) {
                    if (sys->fire->multiplier > 1) sys->fire->multiplier--;
                    /* TODO: Replace by int-multiplication */
                    sys->fire->start += sys->fire->period;
                    sys->head = ESys_ScheduleEvent(sys->head, sys->fire, &flag);
                    if (flag != ESys_OK) { return flag; }
                } else {
                    sys->fire->period = 0;
                }
            }

            /*
             * Check if tdown is indistinguishable from the next event start
             * If so, then set tdown (which is always calculated) to the next
             * event start (which may be user-specified).
             */
            if (sys->head != 0 && ESys_eq(sys->head->start, sys->tdown)) {
                sys->tdown = sys->head->start;
            }
        }

        /* Set next stopping time */
        sys->tnext = HUGE_VAL;
        if (sys->fire != 0 && sys->tnext > sys->tdown)
            sys->tnext = sys->tdown;
        if (sys->head != 0 && sys->tnext > sys->head->start)
            sys->tnext = sys->head->start;

        /* Allow interrupting if something goes wrong */
        if (PyErr_CheckSignals() != 0) {
            return ESys_PYTHON_INTERRUPT;
        }
    }

    return ESys_OK;
}

/*
 * Returns the next time a pacing event starts or finishes in the given system.
 *
 * Arguments
 *  sys : The pacing system to query for a time
 *  flag : The address of a pacing error flag or NULL
 *
 * Returns the next time a pacing event starts or finishes
 */
double
ESys_GetNextTime(ESys sys, ESys_Flag* flag)
{
    if(sys == 0) {
        if(flag != 0) *flag = ESys_INVALID_SYSTEM;
        return -1;
    }
    if(sys->n_events < 0) {
        if(flag != 0) *flag = ESys_UNPOPULATED_SYSTEM;
        return -1;
    }
    if(flag != 0) *flag = ESys_OK;
    return sys->tnext;
}

/*
 * Returns the current pacing level.
 *
 * Arguments
 *  sys : The pacing system to query for a time
 *  flag : The address of a pacing error flag or NULL
 *
 * Returns the next time a pacing event starts or finishes
 */
double
ESys_GetLevel(ESys sys, ESys_Flag* flag)
{
    if(sys == 0) {
        if(flag != 0) *flag = ESys_INVALID_SYSTEM;
        return -1;
    }
    if(sys->n_events < 0) {
        if(flag != 0) *flag = ESys_UNPOPULATED_SYSTEM;
        return -1;
    }
    if(flag != 0) *flag = ESys_OK;
    return sys->level;
}

/*
 *
 * Time-series code starts here
 *
 */

/*
 * Time series pacing error flags
 */
typedef int TSys_Flag;
#define TSys_OK                             0
#define TSys_OUT_OF_MEMORY                  -1
// General
#define TSys_INVALID_SYSTEM                 -10
#define TSys_POPULATED_SYSTEM               -11
#define TSys_UNPOPULATED_SYSTEM             -12
// Populating the system
#define TSys_POPULATE_INVALID_TIMES         -20
#define TSys_POPULATE_INVALID_VALUES        -21
#define TSys_POPULATE_SIZE_MISMATCH         -22
#define TSys_POPULATE_NOT_ENOUGH_DATA       -23
#define TSys_POPULATE_INVALID_TIMES_DATA    -24
#define TSys_POPULATE_INVALID_VALUES_DATA   -25
#define TSys_POPULATE_DECREASING_TIMES_DATA -26
#define TSys_POPULATE_INVALID_PROTOCOL      -27

/*
 * Sets a python exception based on a time-series pacing error flag.
 *
 * Arguments
 *  flag : The python error flag to base the message on.
 */
void
TSys_SetPyErr(TSys_Flag flag)
{
    switch(flag) {
    case TSys_OK:
        break;
    case TSys_OUT_OF_MEMORY:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Memory allocation failed.");
        break;
    // General
    case TSys_INVALID_SYSTEM:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Invalid pacing system provided.");
        break;
    case TSys_POPULATED_SYSTEM:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Pacing system already populated.");
        break;
    case TSys_UNPOPULATED_SYSTEM:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Pacing system not populated.");
        break;
    // Populate
    case TSys_POPULATE_INVALID_PROTOCOL:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Invalid protocol python object passed.");
        break;
    case TSys_POPULATE_INVALID_TIMES:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Invalid times array passed.");
        break;
    case TSys_POPULATE_INVALID_VALUES:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Invalid values array passed.");
        break;
    case TSys_POPULATE_SIZE_MISMATCH:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Sizes of times and values arrays don't match.");
        break;
    case TSys_POPULATE_NOT_ENOUGH_DATA:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Time-series must contain at least two data points.");
        break;
    case TSys_POPULATE_INVALID_TIMES_DATA:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Times array must contain only floats.");
        break;
    case TSys_POPULATE_INVALID_VALUES_DATA:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Values array must contain only floats.");
        break;
    case TSys_POPULATE_DECREASING_TIMES_DATA:
        PyErr_SetString(PyExc_Exception, "T-Pacing error: Times array must be non-decreasing.");
        break;
    // Unknown
    default:
        PyErr_Format(PyExc_Exception, "T-Pacing error: Unlisted error %d", (int)flag);
        break;
    };
}

/*
 * Time series pacing system
 */
struct TSys_Mem {
    Py_ssize_t n_points;   // The number of entries in the time and pace arrays
    double* times;  // The time array
    double* values; // The values array
    Py_ssize_t last_index; // The index of the most recently returned value
    //double level;   // The current output value
};
typedef struct TSys_Mem* TSys;

/*
 * Creates a time series pacing system
 *
 * Arguments
 *  flag : The address of a time series pacing error flag or NULL
 *
 * Returns the newly created time series pacing system
 */
TSys
TSys_Create(TSys_Flag* flag)
{
    TSys sys = (TSys)malloc(sizeof(struct TSys_Mem));
    if (sys == 0) {
        if(flag != 0) *flag = TSys_OUT_OF_MEMORY;
        return 0;
    }

    sys->n_points = -1;
    sys->times = NULL;
    sys->values = NULL;
    sys->last_index = 0;

    if(flag != 0) *flag = TSys_OK;
    return sys;
}

/*
 * Destroys a time series pacing system and frees the memory it occupies.
 *
 * Arguments
 *  sys : The time series pacing system to destroy
 *
 * Returns a time series pacing error flag.
 */
TSys_Flag
TSys_Destroy(TSys sys)
{
    if(sys == 0) return TSys_INVALID_SYSTEM;
    if(sys->times != NULL) {
        free(sys->times);
        sys->times = NULL;
    }
    if(sys->values != NULL) {
        free(sys->values);
        sys->values = NULL;
    }
    free(sys);
    return TSys_OK;
}

/*
 * Populates a time series pacing system using two Python list objects
 * containing an equal number of floating point numbers.
 * Returns an error if the system already has data.
 *
 * Arguments
 *  sys    : The time series pacing system to add the data to.
 *  times  : A Python list of (non-decreasing) floats.
 *  values : An equally sized Python list of floats.
 *
 * Returns a time series pacing error flag.
 */
TSys_Flag
TSys_Populate(TSys sys, PyObject* protocol)
{
    int i;
    Py_ssize_t n;
    PyObject *times_list, *values_list;

    // Check ESys
    if(sys == 0) return TSys_INVALID_SYSTEM;
    if (sys->n_points != -1) return TSys_POPULATED_SYSTEM;
    if (protocol == Py_None) return TSys_POPULATE_INVALID_PROTOCOL;

    // Get PyList from protocol (will need to decref!)
    times_list = PyObject_CallMethod(protocol, "times", NULL); // Returns a new reference
    if(times_list == NULL) return TSys_POPULATE_INVALID_PROTOCOL;
    if(!PyList_Check(times_list)) {
        Py_DECREF(times_list);
        return TSys_POPULATE_INVALID_TIMES;
    }

    // Check and convert times list
    n = PyList_Size(times_list);
    sys->times = (double*)malloc((size_t)n * sizeof(double));
    for(i=0; i<n; i++) {
        // GetItem and convert --> Borrowed reference so ok not to decref!
        sys->times[i] = PyFloat_AsDouble(PyList_GetItem(times_list, i));
    }
    Py_DECREF(times_list);  // Finished with the times_list

    if (PyErr_Occurred()) {
        free(sys->times); sys->times = NULL;
        return TSys_POPULATE_INVALID_TIMES_DATA;
    }
    for(i=1; i<n; i++) {
        if(sys->times[i] < sys->times[i-1]) {
            free(sys->times); sys->times = NULL;
            return TSys_POPULATE_DECREASING_TIMES_DATA;
        }
    }

    // Check and convert values list
    values_list = PyObject_CallMethod(protocol, (char*)"values", NULL); // Returns a new reference
    if(values_list == NULL) {
        free(sys->times); sys->times = NULL;
        return TSys_POPULATE_INVALID_PROTOCOL;
    }
    if(!PyList_Check(values_list) || PyList_Size(values_list) != n) {
        free(sys->times); sys->times = NULL;
        Py_DECREF(values_list);
        return TSys_POPULATE_INVALID_VALUES;
    }
    sys->values = (double*)malloc((size_t)n * sizeof(double));
    for(i=0; i<n; i++) {
        // GetItem and convert --> Borrowed reference so ok not to decref!
        sys->values[i] = PyFloat_AsDouble(PyList_GetItem(values_list, i));
    }
    Py_DECREF(values_list); // Finished with the values list

    if (PyErr_Occurred()) {
        free(sys->times); sys->times = NULL;
        free(sys->values); sys->values = NULL;
        return TSys_POPULATE_INVALID_VALUES_DATA;
    }

    // Update pacing system and return
    sys->n_points = n;
    sys->last_index = 0;
    return TSys_OK;
}

/*
 * Returns the pacing level at the given time.
 *
 * Arguments
 *  sys : The pacing system to query for a value.
 *  time : The time to find a value for.
 *  flag : The address of a pacing error flag or NULL.
 *
 * Returns the value of the pacing level at the given time.
 * Will return -1 if an error occurs, so errors should always be checked for
 * using the flag argument!
 */
double
TSys_GetLevel(TSys sys, double time, TSys_Flag* flag)
{
    // Index and time at left, mid and right point, plus guessed point
    Py_ssize_t ileft, imid, iright, iguess;
    double tleft, tmid, tright, tguess;
    double vleft;

    // Check system
    if(sys == 0) {
        if(flag != 0) *flag = TSys_INVALID_SYSTEM;
        return -1;
    }
    if(sys->n_points < 0) {
        if(flag != 0) *flag = TSys_UNPOPULATED_SYSTEM;
        return -1;
    }

    // Find the highest index `i` of sorted array `times` such that
    // `times[i] <= time`, or `-1` if no such index can be found.
    // A guess can be given, which will be used to speed things up

    // Get left point, check value
    ileft = 0;
    tleft = sys->times[ileft];
    if (tleft > time) {
        // Out-of-bounds on the left, return left-most value
        if(flag != 0) *flag = TSys_OK;
        return sys->values[ileft];
    }

    // Get right point, check value
    iright = sys->n_points - 1;
    tright = sys->times[iright];
    if (tright <= time) {
        // Out-of-bounds on the right, return right-most value
        if(flag != 0) *flag = TSys_OK;
        return sys->values[iright];
    }

    // Have a quick guess at better boundaries, using last
    iguess = sys->last_index - 1; // -1 is heuristic! Could be smaller
    if (iguess > ileft) {
        tguess = sys->times[iguess];
        if (tguess <= time) {
            ileft = iguess;
            tleft = tguess;
        }
    }
    iguess = sys->last_index + 2;   // +2 is heuristic!
    if (iguess < iright) {
        tguess = sys->times[iguess];
        if (tguess > time) {
            iright = iguess;
            tright = tguess;
        }
    }

    // Start bisection
    imid = ileft + (iright - ileft) / 2;
    while (ileft != imid) {
        tmid = sys->times[imid];
        if (tmid < time) {
            ileft = imid;
            tleft = tmid;
        } else {
            iright = imid;
            tright = tmid;
        }
        imid = ileft + (iright - ileft) / 2;
    }

    // At this stage, tleft < time <= tright

    // Handle special case of time == tright
    // (Because otherwise it can happen that tleft == tright, which would give
    //  a divide-by-zero in the interpolation)
    if (time == tright) {
        if(flag != 0) *flag = TSys_OK;
        sys->last_index = iright;
        return sys->values[iright];
    }

    // Find the correct value using linear interpolation
    if(flag != 0) *flag = TSys_OK;
    sys->last_index = ileft;
    vleft = sys->values[ileft];
    return vleft + (sys->values[iright] - vleft) * (time - tleft) / (tright - tleft);
}

/*
 * Pacing types
 */
union PSys {
    ESys esys;
    TSys tsys;
};

enum PSysType {
    PSys_NOT_SET,
    ESys_TYPE,
    TSys_TYPE
};

#endif
