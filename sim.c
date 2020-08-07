/*
Luo-Rudy 1991
Generated on 2020-07-14 13:32:49

Compiling on GCC:
 $ gcc -Wall -lm -lsundials_nvecserial -lsundials_cvode sim.c

Gnuplot example:
set terminal pngcairo enhanced linewidth 2 size 1200, 800;
set output 'V.png'
set size 1.0, 1.0
set xlabel 'time [ms]';
set grid
plot 'V.txt' using 1:2 with lines ls 1 title 'Vm'

*/
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <cvode/cvode.h>
#include <nvector/nvector_serial.h>

#define MYOKIT_SUNDIALS_VERSION 30100
#if MYOKIT_SUNDIALS_VERSION >= 30000
  #include <sunmatrix/sunmatrix_dense.h>
  #include <sundials/sundials_linearsolver.h>
#else
  #include <cvode/cvode_dense.h>
#endif

#include <sundials/sundials_types.h>

#define N_STATE 8

/* Declare intermediary, temporary and system variables */
static realtype t;
static realtype pace;
static realtype AC_C;
static realtype AV_i_ion;
static realtype AV_i_stim;
static realtype AC_stim_amplitude;
static realtype AC_i_diff;
static realtype AV_ik_x_alpha;
static realtype AV_ik_x_beta;
static realtype AV_xi;
static realtype AV_IK;
static realtype AC_gK;
static realtype AC_ik_IK_E;
static realtype AC_PNa_K;
static realtype AC_ENa;
static realtype AV_a;
static realtype AV_ina_m_alpha;
static realtype AV_ina_m_beta;
static realtype AV_ina_h_alpha;
static realtype AV_ina_h_beta;
static realtype AV_ina_j_alpha;
static realtype AV_ina_j_beta;
static realtype AC_gNa;
static realtype AV_INa;
static realtype AC_gKp;
static realtype AV_Kp;
static realtype AV_IKp;
static realtype AV_ica_E;
static realtype AV_ica_d_alpha;
static realtype AV_ica_d_beta;
static realtype AV_ica_f_alpha;
static realtype AV_ica_f_beta;
static realtype AC_gCa;
static realtype AV_ICa;
static realtype AC_ik1_E;
static realtype AC_gK1;
static realtype AV_g;
static realtype AV_ik1_g_alpha;
static realtype AV_ik1_g_beta;
static realtype AV_IK1;
static realtype AC_gb;
static realtype AC_Eb;
static realtype AV_Ib;
static realtype AC_K_o;
static realtype AC_K_i;
static realtype AC_Na_o;
static realtype AC_Na_i;
static realtype AC_Ca_o;
static realtype AC_RTF;
static realtype AC_R;
static realtype AC_T;
static realtype AC_F;
static realtype AV_time;
static realtype AV_pace;

/* Set values of constants */
static void
updateConstants(void)
{
    /* ib */
    AC_Eb = (-59.87);
    AC_gb = 0.03921;
    
    /* cell */
    AC_Ca_o = 1.8;
    AC_K_i = 145.0;
    AC_K_o = 5.4;
    AC_Na_i = 10.0;
    AC_Na_o = 140.0;
    AC_F = 96500.0;
    AC_R = 8314.0;
    AC_T = 310.0;
    AC_RTF = AC_R * AC_T / AC_F;
    
    /* ik */
    AC_PNa_K = 0.01833;
    AC_gK = 0.282 * sqrt(AC_K_o / 5.4);
    AC_ik_IK_E = AC_RTF * log((AC_K_o + AC_PNa_K * AC_Na_o) / (AC_K_i + AC_PNa_K * AC_Na_i));
    
    /* ina */
    AC_ENa = AC_RTF * log(AC_Na_o / AC_Na_i);
    AC_gNa = 16.0;
    
    /* ica */
    AC_gCa = 0.09;
    
    /* ik1 */
    AC_ik1_E = AC_RTF * log(AC_K_o / AC_K_i);
    AC_gK1 = 0.6047 * sqrt(AC_K_o / 5.4);
    
    /* ikp */
    AC_gKp = 0.0183;
    
    /* membrane */
    AC_C = 1.0;
    AC_i_diff = 0.0;
    AC_stim_amplitude = (-80.0);
    
}

/* Right-hand-side function of the model ODE */
static int rhs(realtype t, N_Vector y, N_Vector ydot, void *f_data)
{
    /* ib */
    AV_Ib = AC_gb * (NV_Ith_S(y, 0) - AC_Eb);
    
    /* engine */
    AV_pace = pace;
    AV_time = t;
    
    /* ik */
    AV_xi = ((NV_Ith_S(y, 0) < (-100.0)) ? 1.0 : ((NV_Ith_S(y, 0) == (-77.0)) ? 2.837 * 0.04 / exp(0.04 * (NV_Ith_S(y, 0) + 35.0)) : 2.837 * (exp(0.04 * (NV_Ith_S(y, 0) + 77.0)) - 1.0) / ((NV_Ith_S(y, 0) + 77.0) * exp(0.04 * (NV_Ith_S(y, 0) + 35.0)))));
    AV_ik_x_alpha = 0.0005 * exp(0.083 * (NV_Ith_S(y, 0) + 50.0)) / (1.0 + exp(0.057 * (NV_Ith_S(y, 0) + 50.0)));
    AV_ik_x_beta = 0.0013 * exp((-0.06) * (NV_Ith_S(y, 0) + 20.0)) / (1.0 + exp((-0.04) * (NV_Ith_S(y, 0) + 20.0)));
    NV_Ith_S(ydot, 6) = AV_ik_x_alpha * (1.0 - NV_Ith_S(y, 6)) - AV_ik_x_beta * NV_Ith_S(y, 6);
    AV_IK = AC_gK * AV_xi * NV_Ith_S(y, 6) * (NV_Ith_S(y, 0) - AC_ik_IK_E);
    
    /* ina */
    AV_a = 1.0 - 1.0 / (1.0 + exp((-(NV_Ith_S(y, 0) + 40.0)) / 0.24));
    AV_ina_m_alpha = 0.32 * (NV_Ith_S(y, 0) + 47.13) / (1.0 - exp((-0.1) * (NV_Ith_S(y, 0) + 47.13)));
    AV_ina_m_beta = 0.08 * exp((-NV_Ith_S(y, 0)) / 11.0);
    NV_Ith_S(ydot, 1) = AV_ina_m_alpha * (1.0 - NV_Ith_S(y, 1)) - AV_ina_m_beta * NV_Ith_S(y, 1);
    AV_INa = AC_gNa * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(y, 2) * NV_Ith_S(y, 3) * (NV_Ith_S(y, 0) - AC_ENa);
    AV_ina_h_alpha = AV_a * 0.135 * exp((80.0 + NV_Ith_S(y, 0)) / (-6.8));
    AV_ina_h_beta = AV_a * (3.56 * exp(0.079 * NV_Ith_S(y, 0)) + 310000.0 * exp(0.35 * NV_Ith_S(y, 0))) + (1.0 - AV_a) / (0.13 * (1.0 + exp((NV_Ith_S(y, 0) + 10.66) / (-11.1))));
    NV_Ith_S(ydot, 2) = AV_ina_h_alpha * (1.0 - NV_Ith_S(y, 2)) - AV_ina_h_beta * NV_Ith_S(y, 2);
    AV_ina_j_alpha = AV_a * ((-127140.0) * exp(0.2444 * NV_Ith_S(y, 0)) - 3.474e-05 * exp((-0.04391) * NV_Ith_S(y, 0))) * (NV_Ith_S(y, 0) + 37.78) / (1.0 + exp(0.311 * (NV_Ith_S(y, 0) + 79.23)));
    AV_ina_j_beta = AV_a * (0.1212 * exp((-0.01052) * NV_Ith_S(y, 0)) / (1.0 + exp((-0.1378) * (NV_Ith_S(y, 0) + 40.14)))) + (1.0 - AV_a) * (0.3 * exp((-2.535e-07) * NV_Ith_S(y, 0)) / (1.0 + exp((-0.1) * (NV_Ith_S(y, 0) + 32.0))));
    NV_Ith_S(ydot, 3) = AV_ina_j_alpha * (1.0 - NV_Ith_S(y, 3)) - AV_ina_j_beta * NV_Ith_S(y, 3);
    
    /* ica */
    AV_ica_E = 7.7 - 13.0287 * log(NV_Ith_S(y, 7) / AC_Ca_o);
    AV_ica_d_alpha = 0.095 * exp((-0.01) * (NV_Ith_S(y, 0) - 5.0)) / (1.0 + exp((-0.072) * (NV_Ith_S(y, 0) - 5.0)));
    AV_ica_d_beta = 0.07 * exp((-0.017) * (NV_Ith_S(y, 0) + 44.0)) / (1.0 + exp(0.05 * (NV_Ith_S(y, 0) + 44.0)));
    NV_Ith_S(ydot, 4) = AV_ica_d_alpha * (1.0 - NV_Ith_S(y, 4)) - AV_ica_d_beta * NV_Ith_S(y, 4);
    AV_ica_f_alpha = 0.012 * exp((-0.008) * (NV_Ith_S(y, 0) + 28.0)) / (1.0 + exp(0.15 * (NV_Ith_S(y, 0) + 28.0)));
    AV_ica_f_beta = 0.0065 * exp((-0.02) * (NV_Ith_S(y, 0) + 30.0)) / (1.0 + exp((-0.2) * (NV_Ith_S(y, 0) + 30.0)));
    NV_Ith_S(ydot, 5) = AV_ica_f_alpha * (1.0 - NV_Ith_S(y, 5)) - AV_ica_f_beta * NV_Ith_S(y, 5);
    AV_ICa = AC_gCa * NV_Ith_S(y, 4) * NV_Ith_S(y, 5) * (NV_Ith_S(y, 0) - AV_ica_E);
    NV_Ith_S(ydot, 7) = (-0.0001) * AV_ICa + 0.07 * (0.0001 - NV_Ith_S(y, 7));
    
    /* ik1 */
    AV_ik1_g_alpha = 1.02 / (1.0 + exp(0.2385 * (NV_Ith_S(y, 0) - AC_ik1_E - 59.215)));
    AV_ik1_g_beta = (0.49124 * exp(0.08032 * (NV_Ith_S(y, 0) - AC_ik1_E + 5.476)) + 1.0 * exp(0.06175 * (NV_Ith_S(y, 0) - AC_ik1_E - 594.31))) / (1.0 + exp((-0.5143) * (NV_Ith_S(y, 0) - AC_ik1_E + 4.753)));
    AV_g = AV_ik1_g_alpha / (AV_ik1_g_alpha + AV_ik1_g_beta);
    AV_IK1 = AC_gK1 * AV_g * (NV_Ith_S(y, 0) - AC_ik1_E);
    
    /* ikp */
    AV_Kp = 1.0 / (1.0 + exp((7.488 - NV_Ith_S(y, 0)) / 5.98));
    AV_IKp = AC_gKp * AV_Kp * (NV_Ith_S(y, 0) - AC_ik1_E);
    
    /* membrane */
    AV_i_ion = AV_INa + AV_IK + AV_Ib + AV_IKp + AV_IK1 + AV_ICa;
    AV_i_stim = AV_pace * AC_stim_amplitude;
    NV_Ith_S(ydot, 0) = (-(1.0 / AC_C)) * (AV_i_ion + AC_i_diff + AV_i_stim);
    

    return 0;
}

/* Set initial values */
static void
default_initial_values(N_Vector y)
{
    NV_Ith_S(y, 0) = -84.5286;
    NV_Ith_S(y, 1) = 0.0017;
    NV_Ith_S(y, 2) = 0.9832;
    NV_Ith_S(y, 3) = 0.995484;
    NV_Ith_S(y, 4) = 3e-06;
    NV_Ith_S(y, 5) = 1.0;
    NV_Ith_S(y, 6) = 0.0057;
    NV_Ith_S(y, 7) = 0.0002;

}

/* Pacing event (non-zero stimulus) */
struct PacingEventS {
    double level;       /* The stimulus level (dimensionless, normal range [0,1]) */
    double start;       /* The time this stimulus starts */
    double duration;    /* The stimulus duration */
    double period;      /* The period with which it repeats (or 0 if it doesn't) */
    double multiplier;  /* The number of times this period occurs (or 0 if it doesn't) */
    struct PacingEventS* next;
};
typedef struct PacingEventS PacingEvent;

/*
 * Schedules a pacing event.
 * @param top The first event in a stack (the stack's head)
 * @param add The event to schedule
 * @return The new pointer to the head of the stack
 */
static PacingEvent*
PacingEvent_Schedule(PacingEvent* top, PacingEvent* add)
{
    add->next = 0;
    if (add == 0) return top;
    if (top == 0) return add;
    if (add->start <= top->start) {
        add->next = top;
        return add;
    }
    PacingEvent* evt = top;
    while(evt->next != 0 && evt->next->start <= add->start) {
        evt = evt->next;
    }
    add->next = evt->next;
    evt->next = add;
    return top;
}

/* CVODE Flags */
static int check_flag(void *flagvalue, char *funcname, int opt)
{
    int *errflag;
    /* Check if SUNDIALS function returned NULL pointer - no memory allocated */
    if (opt == 0 && flagvalue == NULL) {
        fprintf(stderr, "\nSUNDIALS_ERROR: %s() failed - returned NULL pointer\n\n", funcname);
        return(1);
    } /* Check if flag < 0 */
    else if (opt == 1) {
        errflag = (int *) flagvalue;
        if (*errflag < 0) {
            fprintf(stderr, "\nSUNDIALS_ERROR: %s() failed with flag = %d\n\n", funcname, *errflag);
            return(1);
        }
    } /* Check if function returned NULL pointer - no memory allocated */
    else if (opt == 2 && flagvalue == NULL) {
        fprintf(stderr, "\nMEMORY_ERROR: %s() failed - returned NULL pointer\n\n", funcname);
        return(1);
    }
    return 0;
}

/* Show output */
static void PrintOutput(realtype t, realtype y)
{
    #if defined(SUNDIALS_EXTENDED_PRECISION)
        printf("%4.1f     %14.6Le\n", t, y);
    #elif defined(SUNDIALS_DOUBLE_PRECISION)
        printf("%4.1f     %14.6le\n", t, y);
    #else
        printf("%4.1f     %14.6e\n", t, y);
    #endif
    return;
}

/* Run a simulation */
int main()
{
    int success = -1;

    /* Sundials error flag */
    int flag;

    /* Declare variables that will need freeing */
    PacingEvent* events = NULL;
    N_Vector y = NULL;
    N_Vector dy = NULL;
    void *cvode_mem = NULL;

    #if MYOKIT_SUNDIALS_VERSION >= 30000
      SUNMatrix sundials_dense_matrix;
      SUNLinearSolver sundials_linear_solver;
    #endif

    /* Create state vector */
    y = N_VNew_Serial(N_STATE);
    if (check_flag((void*)y, "N_VNew_Serial", 0)) goto error;
    dy = N_VNew_Serial(N_STATE);
    if (check_flag((void*)dy, "N_VNew_Serial", 0)) goto error;

    /* Set calculated constants */
    updateConstants();

    /* Set initial values */
    default_initial_values(y);

    /* Set integration times */
    double tMin = 0;
    double tMax = 1000;
    double tLog = 0;

    /* Create pacing events */

    int nPacing = 1;
    events = (PacingEvent*)malloc(sizeof(PacingEvent)*nPacing);
    if (events == 0) goto error;
    int iPacing = 0;
    events[iPacing].level = 1.0;
    events[iPacing].start = 50.0;
    events[iPacing].duration = 0.5;
    events[iPacing].period = 1000.0;
    events[iPacing].multiplier = 0;
    iPacing++;

    /* Schedule events, make "next" point to the first event */
    PacingEvent* next = events;
    PacingEvent* fire = events + 1;
    for(iPacing=1; iPacing<nPacing; iPacing++) {
        next = PacingEvent_Schedule(next, fire++);
    }

    /* Fast forward events to starting time */
    double tNext = next->start;
    double tDown = 0.0;
    fire = 0;
    while (tNext <= tMin) {
        /* Event over? */
        if (fire != 0 && tNext >= tDown) {
            fire = 0;
        }
        /* New event? */
        if (next != 0 && tNext >= next->start) {
            fire = next;
            next = next->next;
            tDown = fire->start + fire->duration;
            if (fire->period > 0) {
                if (fire->multiplier != 1) {
                    if (fire->multiplier > 1) fire->multiplier--;
                    fire->start += fire->period;
                    next = PacingEvent_Schedule(next, fire);
                } else {
                    fire->period = 0;
                }
            }
        }
        /* Set next time */
        tNext = tMax;
        if (fire != 0 && tDown < tNext) tNext = tDown;
        if (next != 0 && next->start < tNext) tNext = next->start;
    }
    if (fire != 0) {
        pace = fire->level;
    } else {
        pace = 0.0;
    }

    /* Set simulation starting time */
    t = tMin;

    /* Create solver */
    #if MYOKIT_SUNDIALS_VERSION >= 40000
    cvode_mem = CVodeCreate(CV_BDF);
    #else
    cvode_mem = CVodeCreate(CV_BDF, CV_NEWTON);
    #endif
    if (check_flag((void*)cvode_mem, "CVodeCreate", 0)) goto error;
    flag = CVodeInit(cvode_mem, rhs, t, y);
    if (check_flag(&flag, "CVodeInit", 1)) goto error;

    #if MYOKIT_SUNDIALS_VERSION >= 30000

    sundials_dense_matrix = SUNDenseMatrix(N_STATE,N_STATE);
    if(check_flag((void *)sundials_dense_matrix, "SUNDenseMatrix", 0)) goto error;
    /* Create dense SUNLinearSolver object for use by CVode */
    sundials_linear_solver = SUNDenseLinearSolver(y, sundials_dense_matrix);
    if(check_flag((void *)sundials_linear_solver, "SUNDenseLinearSolver", 0)) goto error;
    /* Call CVDlsSetLinearSolver to attach the matrix and linear solver to CVode */
    flag = CVDlsSetLinearSolver(cvode_mem, sundials_linear_solver, sundials_dense_matrix);
    if(check_flag(&flag, "CVDlsSetLinearSolver", 1)) goto error;

    #else

    flag = CVDense(cvode_mem, N_STATE);
    if (check_flag(&flag, "CVDense", 1)) goto error;

    #endif

    /* Set tolerances */
    double reltol = RCONST(1.0e-4);
    double abstol = RCONST(1.0e-6);
    flag = CVodeSStolerances(cvode_mem, reltol, abstol);
    if (check_flag(&flag, "CVodeSStolerances", 1)) goto error;

    /* Go! */
    while(1) {
        if (tMax < tNext) tNext = tMax;
        flag = CVode(cvode_mem, tNext, y, &t, CV_ONE_STEP);
        if (check_flag(&flag, "CVode", 1)) break;
        if (flag == CV_SUCCESS) {
            /* Shot past next discontinuity? */
            if (t > tNext) {
                flag = CVodeGetDky(cvode_mem, tNext, 0, y);
                if (check_flag(&flag, "CVodeGetDky", 1)) goto error;
                t = tNext;
                flag = CVodeReInit(cvode_mem, t, y);
                if (check_flag(&flag, "CVodeReInit", 1)) goto error;
                /* Recalculate logging values at this point in time */
                rhs(t, y, dy, 0);
            }
            /* Event over? */
            if (fire != 0 && t >= tDown) {
                pace = 0;
                fire = 0;
                flag = CVodeReInit(cvode_mem, t, y);
                if (check_flag(&flag, "CVodeReInit", 1)) goto error;
            }
            /* New event? */
            if (next != 0 && t >= next->start) {
                fire = next;
                next = next->next;
                pace = fire->level;
                tDown = fire->start + fire->duration;
                if (fire->period > 0) {
                    if (fire->multiplier == 1) {
                        fire->period = 0;
                    } else {
                        if (fire->multiplier > 1) fire->multiplier--;
                        fire->start += fire->period;
                        next = PacingEvent_Schedule(next, fire);
                    }
                }
                flag = CVodeReInit(cvode_mem, t, y);
                if (check_flag(&flag, "CVodeReInit", 1)) goto error;
            }
            /* Set next time */
            tNext = tMax;
            if (fire != 0 && tDown < tNext) tNext = tDown;
            if (next != 0 && next->start < tNext) tNext = next->start;
            /* Log */
            if (t >= tLog) {
                /* Log current position */
                PrintOutput(t, NV_Ith_S(y, 0));
            }
        }
        if (t >= tMax) break;
    }

    /* Success! */
    success = 0;

error:
    /* Free allocated space */
    free(events);

    /* Free CVODE space */
    N_VDestroy_Serial(y);
    N_VDestroy_Serial(dy);
    CVodeFree(&cvode_mem);

    /* Return */
    return success;
}
