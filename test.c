
#include <Python.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#include <cvodes/cvodes.h>
#include <nvector/nvector_serial.h>
#define MYOKIT_SUNDIALS_VERSION 30100
#if MYOKIT_SUNDIALS_VERSION >= 30000
    #include <sunmatrix/sunmatrix_dense.h>
    #include <sunlinsol/sunlinsol_dense.h>
    #include <cvodes/cvodes_direct.h>
#else
    #include <cvodes/cvodes_dense.h>
#endif
#include <sundials/sundials_types.h>
#include "pacing.h"

#define N_STATE 8
#define N_SENS 3
#define USE_CVODE 1

/* Pacing */
ESys epacing;               /* Event-based pacing system */
FSys fpacing;               /* Fixed-form pacing system */

/*
 * Check sundials flags, set python error
 *  flagvalue : The value to check
 *  funcname : The name of the function that returned the flag
 *  opt : Mode selector
 *         0 : Error if the flag is null
 *         1 : Error if the flag is < 0
 *         2 : Errir
 */
static int
check_cvode_flag(void *flagvalue, char *funcname, int opt)
{
    if (opt == 0 && flagvalue == NULL) {
        /* Check if sundials function returned null pointer */
        char str[200];
        sprintf(str, "%s() failed - returned NULL pointer", funcname);
        PyErr_SetString(PyExc_Exception, str);
        return 1;
    } else if (opt == 1) {
        /* Check if flag < 0 */
        int flag = *((int*)flagvalue);
        if (flag < 0) {
            if (strcmp(funcname, "CVode") == 0) {
                switch (flag) {
                case -1:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -1 CV_TOO_MUCH_WORK: The solver took mxstep internal steps but could not reach tout.");
                    break;
                case -2:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -2 CV_TOO_MUCH_ACC: The solver could not satisfy the accuracy demanded by the user for some internal step.");
                    break;
                case -3:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -3 CV_ERR_FAILURE: Error test failures occurred too many times during one internal time step or minimum step size was reached.");
                    break;
                case -4:
                    PyErr_SetString(PyExc_ArithmeticError, "Function CVode() failed with flag -4 CV_CONV_FAILURE: Convergence test failures occurred too many times during one internal time step or minimum step size was reached.");
                    break;
                case -5:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -5 CV_LINIT_FAIL: The linear solver's initialization function failed.");
                    break;
                case -6:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -6 CV_LSETUP_FAIL: The linear solver's setup function failed in an unrecoverable manner.");
                    break;
                case -7:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -7 CV_LSOLVE_FAIL: The linear solver's solve function failed in an unrecoverable manner.");
                    break;
                case -8:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -8 CV_RHSFUNC_FAIL: The right-hand side function failed in an unrecoverable manner.");
                    break;
                case -9:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -9 CV_FIRST_RHSFUNC_ERR: The right-hand side function failed at the first call.");
                    break;
                case -10:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -10 CV_REPTD_RHSFUNC_ERR: The right-hand side function had repeated recoverable errors.");
                    break;
                case -11:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -11 CV_UNREC_RHSFUNC_ERR: The right-hand side function had a recoverable error, but no recovery is possible.");
                    break;
                case -12:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -12 CV_RTFUNC_FAIL: The rootfinding function failed in an unrecoverable manner.");
                    break;
                case -20:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -20 CV_MEM_FAIL: A memory allocation failed.");
                    break;
                case -21:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -21 CV_MEM_NULL: The cvode mem argument was NULL.");
                    break;
                case -22:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -22 CV_ILL_INPUT: One of the function inputs is illegal.");
                    break;
                case -23:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -23 CV_NO_MALLOC: The cvode memory block was not allocated by a call to CVodeMalloc.");
                    break;
                case -24:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -24 CV_BAD_K: The derivative order k is larger than the order used.");
                    break;
                case -25:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -25 CV_BAD_T: The time t is outside the last step taken.");
                    break;
                case -26:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -26 CV_BAD_DKY: The output derivative vector is NULL.");
                    break;
                case -27:
                    PyErr_SetString(PyExc_Exception, "Function CVode() failed with flag -27 CV_TOO_CLOSE: The output and initial times are too close to each other.");
                    break;
                default: {
                     /* Note: Brackets are required here, default: should be followed by
                        a _statement_ and char str[200]; is technically not a statement... */
                    char str[200];
                    sprintf(str, "Function CVode() failed with unknown flag = %d", flag);
                    PyErr_SetString(PyExc_Exception, str);
                }}
            } else {
                char str[200];
                sprintf(str, "%s() failed with flag = %d", funcname, flag);
                PyErr_SetString(PyExc_Exception, str);
            }
            return 1;
        }
    }
    return 0;
}

/*
 * Declare system variables
 */
static realtype engine_time = 0;        /* Engine time */
static realtype engine_time_last = 0;   /* Previous engine time */
static realtype engine_pace = 0;
static realtype engine_realtime = 0;
static realtype engine_starttime = 0;
static realtype rootfinding_threshold = 0;
static long engine_evaluations = 0;
static long engine_steps = 0;

/*
 * Declare constants and intermediary variables.
 * If doing sensitivity analysis, the default values of the parameters are set
 * here too.
 */
static realtype AC_C = 1.0;
static realtype AV_i_ion;
static realtype AV_i_stim;
static realtype AC_stim_amplitude = -80.0;
static realtype AC_i_diff = 0.0;
static realtype AV_ik_x_alpha;
static realtype AV_ik_x_beta;
static realtype AV_xi;
static realtype AV_IK;
static realtype AC_gK;
static realtype AC_ik_IK_E;
static realtype AC_PNa_K = 0.01833;
static realtype AC_ENa;
static realtype AV_a;
static realtype AV_ina_m_alpha;
static realtype AV_ina_m_beta;
static realtype AV_ina_h_alpha;
static realtype AV_ina_h_beta;
static realtype AV_ina_j_alpha;
static realtype AV_ina_j_beta;
static realtype AP_gNa = 16.0;
static realtype AV_INa;
static realtype AC_p1 = 1.56;
static realtype AC_xp1;
static realtype AC_gKp = 0.0183;
static realtype AV_Kp;
static realtype AV_IKp;
static realtype AV_ica_E;
static realtype AV_ica_d_alpha;
static realtype AV_ica_d_beta;
static realtype AV_ica_f_alpha;
static realtype AV_ica_f_beta;
static realtype AP_gCa = 0.09;
static realtype AV_ICa;
static realtype AC_ik1_E;
static realtype AC_gK1;
static realtype AV_g;
static realtype AV_ik1_g_alpha;
static realtype AV_ik1_g_beta;
static realtype AV_IK1;
static realtype AC_gb = 0.03921;
static realtype AC_Eb = -59.87;
static realtype AV_Ib;
static realtype AC_K_o = 5.4;
static realtype AC_K_i = 145.0;
static realtype AC_Na_o = 140.0;
static realtype AC_Na_i = 10.0;
static realtype AC_Ca_o = 1.8;
static realtype AC_RTF;
static realtype AC_R = 8314.0;
static realtype AC_T = 310.0;
static realtype AC_F = 96500.0;
static realtype AV_time;
static realtype AV_pace;

/*
 * Declare sensitivity output variables
 */
static realtype S0_V_ina_m_alpha;
static realtype S0_V_ina_m_beta;
static realtype S0_V_INa;
static realtype S1_V_ina_m_alpha;
static realtype S1_V_ina_m_beta;
static realtype S1_V_INa;
static realtype S2_V_ina_m_alpha;
static realtype S2_V_ina_m_beta;
static realtype S2_V_INa;

/* Define type for "user data" that will hold parameter values */
typedef struct {
    realtype p[N_SENS];
} *UserData;

/*
 * Set values of calculated constants
 */
static void
update_constants(void)
{
    AC_RTF = AC_R * AC_T / AC_F;
    AC_gK = 0.282 * sqrt(AC_K_o / 5.4);
    AC_ik_IK_E = AC_RTF * log((AC_K_o + AC_PNa_K * AC_Na_o) / (AC_K_i + AC_PNa_K * AC_Na_i));
    AC_ENa = AC_RTF * log(AC_Na_o / AC_Na_i);
    AC_xp1 = 2.0 + AC_p1;
    AC_ik1_E = AC_RTF * log(AC_K_o / AC_K_i);
    AC_gK1 = 0.6047 * sqrt(AC_K_o / 5.4);
}

/*
 * Right-hand-side function of the model ODE
 *
 *  realtype t      Current time
 *  N_Vector y      The current state values
 *  N_Vector ydot   Space to store the calculated derivatives in
 *  void* user_data Extra data (contains the sensitivity parameter values)
 *
 */
static int
rhs(realtype t, N_Vector y, N_Vector ydot, void *user_data)
{
    FSys_Flag flag_fpacing;
    UserData fdata;

    /* Recast user data */
    fdata = (UserData) user_data;

    /* Fixed-form pacing? Then look-up correct value of pacing variable! */
    if (fpacing != NULL) {
        engine_pace = FSys_GetLevel(fpacing, t, &flag_fpacing);
        if (flag_fpacing != FSys_OK) { /* This should never happen */
            FSys_SetPyErr(flag_fpacing);
            return -1;  /* Negative value signals irrecoverable error to CVODE */
        }
    }

    /* ib */
    AV_Ib = AC_gb * (NV_Ith_S(y, 0) - AC_Eb);
    
    /* engine */
    AV_pace = engine_pace;
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
    AV_ina_j_alpha = AV_a * ((-127140.0) * exp(0.2444 * NV_Ith_S(y, 0)) - 3.474e-05 * exp((-0.04391) * NV_Ith_S(y, 0))) * (NV_Ith_S(y, 0) + 37.78) / (1.0 + exp(0.311 * (NV_Ith_S(y, 0) + 79.23)));
    AV_ina_j_beta = AV_a * (0.1212 * exp((-0.01052) * NV_Ith_S(y, 0)) / (1.0 + exp((-0.1378) * (NV_Ith_S(y, 0) + 40.14)))) + (1.0 - AV_a) * (0.3 * exp((-2.535e-07) * NV_Ith_S(y, 0)) / (1.0 + exp((-0.1) * (NV_Ith_S(y, 0) + 32.0))));
    NV_Ith_S(ydot, 3) = AV_ina_j_alpha * (1.0 - NV_Ith_S(y, 3)) - AV_ina_j_beta * NV_Ith_S(y, 3);
    AV_INa = fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(y, 2) * NV_Ith_S(y, 3) * (NV_Ith_S(y, 0) - AC_ENa) + 1e-05 * NV_Ith_S(ydot, 1);
    AV_ina_h_alpha = AV_a * 0.135 * exp((80.0 + NV_Ith_S(y, 0)) / (-6.8));
    AV_ina_h_beta = AV_a * (AC_xp1 * exp(0.079 * NV_Ith_S(y, 0)) + 310000.0 * exp(0.35 * NV_Ith_S(y, 0))) + (1.0 - AV_a) / (0.13 * (1.0 + exp((NV_Ith_S(y, 0) + 10.66) / (-11.1))));
    NV_Ith_S(ydot, 2) = AV_ina_h_alpha * (1.0 - NV_Ith_S(y, 2)) - AV_ina_h_beta * NV_Ith_S(y, 2);
    
    /* ica */
    AV_ica_E = 7.7 - 13.0287 * log(NV_Ith_S(y, 7) / AC_Ca_o);
    AV_ica_d_alpha = 0.095 * exp((-0.01) * (NV_Ith_S(y, 0) - 5.0)) / (1.0 + exp((-0.072) * (NV_Ith_S(y, 0) - 5.0)));
    AV_ica_d_beta = 0.07 * exp((-0.017) * (NV_Ith_S(y, 0) + 44.0)) / (1.0 + exp(0.05 * (NV_Ith_S(y, 0) + 44.0)));
    NV_Ith_S(ydot, 4) = AV_ica_d_alpha * (1.0 - NV_Ith_S(y, 4)) - AV_ica_d_beta * NV_Ith_S(y, 4);
    AV_ica_f_alpha = 0.012 * exp((-0.008) * (NV_Ith_S(y, 0) + 28.0)) / (1.0 + exp(0.15 * (NV_Ith_S(y, 0) + 28.0)));
    AV_ica_f_beta = 0.0065 * exp((-0.02) * (NV_Ith_S(y, 0) + 30.0)) / (1.0 + exp((-0.2) * (NV_Ith_S(y, 0) + 30.0)));
    NV_Ith_S(ydot, 5) = AV_ica_f_alpha * (1.0 - NV_Ith_S(y, 5)) - AV_ica_f_beta * NV_Ith_S(y, 5);
    AV_ICa = fdata->p[1] * NV_Ith_S(y, 4) * NV_Ith_S(y, 5) * (NV_Ith_S(y, 0) - AV_ica_E);
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
    

    engine_evaluations++;
    return 0;
}

/*
 * Right-hand-side function of the model's sensitivity equations.
 *
 *  int Ns          The number of sensitivities
 *  realtype t      Current time
 *  N_Vector y      The current state values
 *  N_Vector ydot   The current state value derivatives
 *  N_Vector* yS    The current values of the sensitivity vectors (see below)
 *  N_Vector* ySdot Space to store the calculated sensitivities of the derivatives
 *  void* user_data Extra data (contains the sensitivity parameter values)
 *  N_Vector tmp1   A length-N N_Vector for use as temporary storage
 *  N_Vector tmp2   A length-N N_Vector for use as temporary storage
 *
 * yS[i] is a vector containing s_i = dy/dp_i
 *  Each entry in yS is for one parameter/initial value
 *  And each entry in yS[i] is for a state
 *
 * ySdot[i] is a vector containing (df/dy) * s_i + df/dp_i
 *  Each entry in ySdot is for one parameter/initial value
 *  And each entry in ySdot[i] is for a state
 */
static int
rhs1(int Ns, realtype t, N_Vector y, N_Vector ydot, N_Vector *yS, N_Vector *ySdot,
   void *user_data, N_Vector tmp1, N_Vector tmp2)
{
    FSys_Flag flag_fpacing;
    UserData fdata;

    /* Recast user data */
    fdata = (UserData) user_data;

    /* Fixed-form pacing? Then look-up correct value of pacing variable! */
    if (fpacing != NULL) {
        engine_pace = FSys_GetLevel(fpacing, t, &flag_fpacing);
        if (flag_fpacing != FSys_OK) { /* This should never happen */
            FSys_SetPyErr(flag_fpacing);
            return -1;  /* Negative value signals irrecoverable error to CVODE */
        }
    }


    return 0;
}

/*
 * Calculate sensitivities for output (starting from sensitivities of states)
 *
 * Assumes that all intermediary variables, derivatives, and sensitivities of
 * the derivatives have already been calculated.
 *
 *  realtype t      Current time
 *  N_Vector y      The current state values
 *  N_Vector ydot   The current state value derivatives
 *  N_Vector* yS    The current values of the sensitivity vectors (see below)
 *  N_Vector* ySdot Space to store any calculated sensitivities of derivatives
 *  void* user_data Extra data (contains the sensitivity parameter values)
 */
static int
calculate_sensitivity_outputs(realtype t, N_Vector y, N_Vector ydot,
                              N_Vector* yS, N_Vector* ySdot, void* user_data)
{
    FSys_Flag flag_fpacing;
    UserData fdata;

    /* Recast user data */
    fdata = (UserData) user_data;

    /* Fixed-form pacing? Then look-up correct value of pacing variable! */
    if (fpacing != NULL) {
        engine_pace = FSys_GetLevel(fpacing, t, &flag_fpacing);
        if (flag_fpacing != FSys_OK) { /* This should never happen */
            FSys_SetPyErr(flag_fpacing);
            return -1;  /* Negative value signals irrecoverable error to CVODE */
        }
    }
    /* Sensitivity w.r.t. ina.gNa */
    S0_V_ina_m_alpha = (0.32 * NV_Ith_S(yS[0], 0) * (1.0 - exp((-0.1) * (NV_Ith_S(y, 0) + 47.13))) - 0.32 * (NV_Ith_S(y, 0) + 47.13) * (-(exp((-0.1) * (NV_Ith_S(y, 0) + 47.13)) * ((-0.1) * NV_Ith_S(yS[0], 0))))) / pow(1.0 - exp((-0.1) * (NV_Ith_S(y, 0) + 47.13)), 2.0);
    S0_V_ina_m_beta = 0.08 * (exp((-NV_Ith_S(y, 0)) / 11.0) * ((-NV_Ith_S(yS[0], 0)) / 11.0));
    NV_Ith_S(ySdot[0], 1) = S0_V_ina_m_alpha * (1.0 - NV_Ith_S(y, 1)) + AV_ina_m_alpha * (-NV_Ith_S(yS[0], 1)) - (S0_V_ina_m_beta * NV_Ith_S(y, 1) + AV_ina_m_beta * NV_Ith_S(yS[0], 1));
    S0_V_INa = (((1.0 * pow(NV_Ith_S(y, 1), 3.0) + fdata->p[0] * (3.0 * pow(NV_Ith_S(y, 1), 2.0) * NV_Ith_S(yS[0], 1))) * NV_Ith_S(y, 2) + fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(yS[0], 2)) * NV_Ith_S(y, 3) + fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(y, 2) * NV_Ith_S(yS[0], 3)) * (NV_Ith_S(y, 0) - AC_ENa) + fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(y, 2) * NV_Ith_S(y, 3) * NV_Ith_S(yS[0], 0) + 1e-05 * NV_Ith_S(ySdot[0], 1);

    /* Sensitivity w.r.t. ica.gCa */
    S1_V_ina_m_alpha = (0.32 * NV_Ith_S(yS[1], 0) * (1.0 - exp((-0.1) * (NV_Ith_S(y, 0) + 47.13))) - 0.32 * (NV_Ith_S(y, 0) + 47.13) * (-(exp((-0.1) * (NV_Ith_S(y, 0) + 47.13)) * ((-0.1) * NV_Ith_S(yS[1], 0))))) / pow(1.0 - exp((-0.1) * (NV_Ith_S(y, 0) + 47.13)), 2.0);
    S1_V_ina_m_beta = 0.08 * (exp((-NV_Ith_S(y, 0)) / 11.0) * ((-NV_Ith_S(yS[1], 0)) / 11.0));
    NV_Ith_S(ySdot[1], 1) = S1_V_ina_m_alpha * (1.0 - NV_Ith_S(y, 1)) + AV_ina_m_alpha * (-NV_Ith_S(yS[1], 1)) - (S1_V_ina_m_beta * NV_Ith_S(y, 1) + AV_ina_m_beta * NV_Ith_S(yS[1], 1));
    S1_V_INa = ((fdata->p[0] * (3.0 * pow(NV_Ith_S(y, 1), 2.0) * NV_Ith_S(yS[1], 1)) * NV_Ith_S(y, 2) + fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(yS[1], 2)) * NV_Ith_S(y, 3) + fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(y, 2) * NV_Ith_S(yS[1], 3)) * (NV_Ith_S(y, 0) - AC_ENa) + fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(y, 2) * NV_Ith_S(y, 3) * NV_Ith_S(yS[1], 0) + 1e-05 * NV_Ith_S(ySdot[1], 1);

    /* Sensitivity w.r.t. init(ica.Ca_i) */
    S2_V_ina_m_alpha = (0.32 * NV_Ith_S(yS[2], 0) * (1.0 - exp((-0.1) * (NV_Ith_S(y, 0) + 47.13))) - 0.32 * (NV_Ith_S(y, 0) + 47.13) * (-(exp((-0.1) * (NV_Ith_S(y, 0) + 47.13)) * ((-0.1) * NV_Ith_S(yS[2], 0))))) / pow(1.0 - exp((-0.1) * (NV_Ith_S(y, 0) + 47.13)), 2.0);
    S2_V_ina_m_beta = 0.08 * (exp((-NV_Ith_S(y, 0)) / 11.0) * ((-NV_Ith_S(yS[2], 0)) / 11.0));
    NV_Ith_S(ySdot[2], 1) = S2_V_ina_m_alpha * (1.0 - NV_Ith_S(y, 1)) + AV_ina_m_alpha * (-NV_Ith_S(yS[2], 1)) - (S2_V_ina_m_beta * NV_Ith_S(y, 1) + AV_ina_m_beta * NV_Ith_S(yS[2], 1));
    S2_V_INa = ((fdata->p[0] * (3.0 * pow(NV_Ith_S(y, 1), 2.0) * NV_Ith_S(yS[2], 1)) * NV_Ith_S(y, 2) + fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(yS[2], 2)) * NV_Ith_S(y, 3) + fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(y, 2) * NV_Ith_S(yS[2], 3)) * (NV_Ith_S(y, 0) - AC_ENa) + fdata->p[0] * pow(NV_Ith_S(y, 1), 3.0) * NV_Ith_S(y, 2) * NV_Ith_S(y, 3) * NV_Ith_S(yS[2], 0) + 1e-05 * NV_Ith_S(ySdot[2], 1);


    return 0;
}

/*
 * Right-hand-side function, bound variables only
 */
static int
update_bindings(realtype t)
{
    AV_time = t;
    AV_pace = engine_pace;

    return 0;
}

/*
 * Update variables bound to engine.realtime
 */
static int
update_realtime_bindings(realtype t)
{

    return 0;
}

/*
 * Root finding function
 */
static int
root_finding(realtype t, N_Vector y, realtype *gout, void *user_data)
{
    gout[0] = NV_Ith_S(y, 0) - rootfinding_threshold;
    return 0;
}

/*
 * Settings
 */
static double abs_tol = 1e-6; /* The absolute tolerance */
static double rel_tol = 1e-4; /* The relative tolerance */
static double dt_max = 0;     /* The maximum step size (0.0 for none) */
static double dt_min = 0;     /* The minimum step size (0.0 for none) */

/*
 * Change the tolerance settings
 */
static PyObject*
sim_set_tolerance(PyObject *self, PyObject *args)
{
    /* Check input arguments */
    double tabs, trel;
    if (!PyArg_ParseTuple(args, "dd", &tabs, &trel)) {
        PyErr_SetString(PyExc_Exception, "Expected input arguments: abs_tol(float), rel_tol(float).");
        return 0;
    }
    abs_tol = tabs;
    rel_tol = trel;
    Py_RETURN_NONE;
}

/*
 * Change the maximum step size (0 for none)
 */
static PyObject*
sim_set_max_step_size(PyObject *self, PyObject *args)
{
    /* Check input arguments */
    double tmax;
    if (!PyArg_ParseTuple(args, "d", &tmax)) {
        PyErr_SetString(PyExc_Exception, "Expected input argument: tmax(float).");
        return 0;
    }
    dt_max = tmax;
    Py_RETURN_NONE;
}

/*
 * Change the minimum step size (0 for none)
 */
static PyObject*
sim_set_min_step_size(PyObject *self, PyObject *args)
{
    /* Check input arguments */
    double tmin;
    if (!PyArg_ParseTuple(args, "d", &tmin)) {
        PyErr_SetString(PyExc_Exception, "Expected input argument: tmin(float).");
        return 0;
    }
    dt_min = tmin;
    Py_RETURN_NONE;
}

/*
 * Add a variable to the logging lists. Returns 1 if successful
 */
static int
log_add(PyObject* log_dict, PyObject** logs, realtype** vars, int i, const char* name, const realtype* var)
{
    /* See first use of log_add for notes on unicode */
    int added = 0;
    PyObject* key = PyUnicode_FromString(name);
    if (PyDict_Contains(log_dict, key)) {
        logs[i] = PyDict_GetItem(log_dict, key);
        vars[i] = (realtype*)var;
        added = 1;
    }
    Py_DECREF(key);
    return added;
}

/*
 * Simulation variables
 */

int running = 0;        /* Running yes or no */

/* Input arguments */
double tmin;            /* The initial simulation time */
double tmax;            /* The final simulation time */
PyObject* state_in;     /* The initial state */
PyObject* state_out;    /* The final state */
PyObject* inputs;       /* A vector used to return the binding inputs` values */
PyObject* eprotocol;    /* An event-based pacing protocol */
PyObject* fprotocol;    /* A fixed-form pacing protocol */
PyObject* log_dict;     /* The log dict */
double log_interval;    /* Periodic logging: The log interval (0 to disable) */
PyObject* log_times;    /* Point-list logging: List of points (None to disable) */
PyObject* sens_list;    /* List to store sensitivities in (or None if not enabled) */
PyObject* root_list;    /* List to store found roots in (or None if not enabled) */
double root_threshold;  /* Threshold to use for root finding */
PyObject* benchtime;    /* Callable time() function or None */

/* Next simulation halting point */
double tnext;

/* Checking for repeated zero size steps */
int zero_step_count;
int max_zero_step_count = 500;   /* Increased this from 50 */

/* CVode objects */
void *cvode_mem;     /* The memory used by the solver */
N_Vector y;          /* Stores the current position y */
N_Vector y_log;      /* Used to store y when logging */
N_Vector dy_log;     /* Used to store dy when logging */
N_Vector* sy;        /* Vector of state sensitivities, 1 per variable in `variables` */
N_Vector* sy_log;    /* Used to store y sensitivities when logging */
N_Vector* sdy_log;   /* Used to store dy sensitivities when logging */
N_Vector y_last;     /* Used to store previous value of y for error handling */
UserData udata;      /* UserData struct, used to pass in parameters */

#if MYOKIT_SUNDIALS_VERSION >= 30000
SUNMatrix sundense_matrix;          /* Dense matrix for linear solves */
SUNLinearSolver sundense_solver;    /* Linear solver object */
#endif

/* Parameter/initial-condition scales */
realtype pbar[N_SENS];  /* One number per parameter/initial condition, giving something in the expected magnitude of the param/init */

/* Root finding */
int* rootsfound;     /* Used to store found roots */

/* Logging */
PyObject** logs;            /* An array of pointers to a PyObject */
realtype** vars;            /* An array of pointers to realtype */
int n_vars;                 /* Number of logging variables */
int log_bound;              /* True if logging bound variables */
int log_inter;              /* True if logging intermediary variables */
int log_deriv;              /* True if logging derivatives */
PyObject* list_update_str;  /* PyUnicode, used to call "append" method */
Py_ssize_t ilog;            /* Periodic/point-list logging: Index of next point */
double tlog;                /* Periodic/point-list logging: Next point */
int dynamic_logging;        /* True if logging every point. */

/*
 * Cleans up after a simulation
 */
static PyObject*
sim_clean()
{
    if (running != 0) {
        /* Done with str="append", decref it */
        Py_XDECREF(list_update_str); list_update_str = NULL;

        /* Free allocated space */
        free(vars); vars = NULL;
        free(logs); logs = NULL;
        free(rootsfound); rootsfound = NULL;

        /* Free CVode space */
        N_VDestroy_Serial(y); y = NULL;
        N_VDestroy_Serial(dy_log); dy_log = NULL;
        if (USE_CVODE && !dynamic_logging) {
            N_VDestroy_Serial(y_log); y_log = NULL;
        }
        if (N_SENS) {
            N_VDestroyVectorArray(sy, N_SENS); sy = NULL;
            N_VDestroyVectorArray(sdy_log, N_SENS); sdy_log = NULL;
            if (USE_CVODE && !dynamic_logging) {
                N_VDestroyVectorArray(sy_log, N_SENS); sy_log = NULL;
            }
        }

        CVodeFree(&cvode_mem); cvode_mem = NULL;
        #if MYOKIT_SUNDIALS_VERSION >= 30000
        SUNLinSolFree(sundense_solver); sundense_solver = NULL;
        SUNMatDestroy(sundense_matrix); sundense_matrix = NULL;
        #endif

        /* Free user data */
        free(udata); udata = NULL;

        /* Free pacing system space */
        ESys_Destroy(epacing); epacing = NULL;
        FSys_Destroy(fpacing); fpacing = NULL;

        /* No longer running */
        running = 0;
    }

    /* Return 0, allowing the construct
        PyErr_SetString(PyExc_Exception, "Oh noes!");
        return sim_clean()
       to terminate a python function. */
    return 0;
}
static PyObject*
py_sim_clean(PyObject *self, PyObject *args)
{
    sim_clean();
    Py_RETURN_NONE;
}

/*
 * Initialise a run
 */
static PyObject*
sim_init(PyObject *self, PyObject *args)
{
    int i, j;
    int flag;
    int flag_cvode;
    int log_first_point;
    ESys_Flag flag_epacing;
    FSys_Flag flag_fpacing;
    Py_ssize_t pos;
    PyObject *flt;
    PyObject *key;
    PyObject* ret;
    PyObject *value;
    PyObject *l1, *l2;

    #ifndef SUNDIALS_DOUBLE_PRECISION
    PyErr_SetString(PyExc_Exception, "Sundials must be compiled with double precision.");
    /* No memory freeing is needed here, return directly */
    return 0;
    #endif

    /* Check if already running */
    if (running != 0) {
        PyErr_SetString(PyExc_Exception, "Simulation already initialized.");
        return 0;
    }

    /* Set all pointers used in sim_clean to null */
    list_update_str = NULL;
    vars = NULL;
    logs = NULL;
    rootsfound = NULL;
    y = NULL;
    y_log = NULL;
    dy_log = NULL;
    sy = NULL;
    sy_log = NULL;
    sdy_log = NULL;
    cvode_mem = NULL;
    epacing = NULL;
    fpacing = NULL;
    log_times = NULL;
    udata = NULL;
    #if MYOKIT_SUNDIALS_VERSION >= 30000
    sundense_matrix = NULL;
    sundense_solver = NULL;
    #endif

    /* Check input arguments */
    if (!PyArg_ParseTuple(args, "ddOOOOOOdOOOdO",
            &tmin,
            &tmax,
            &state_in,
            &state_out,
            &inputs,
            &eprotocol,
            &fprotocol,
            &log_dict,
            &log_interval,
            &log_times,
            &sens_list,
            &root_list,
            &root_threshold,
            &benchtime)) {
        PyErr_SetString(PyExc_Exception, "Incorrect input arguments.");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }

    /* Now officialy running :) */
    running = 1;

    /*************************************************************************
    From this point on, no more direct returning! Use sim_clean()

    To check if this list is still up to date manually search for cvode
    and python stuff. To find what to free() search for "alloc("
    Initialize all to NULL so that free() will work without errors.

    Notes:
    1. Functions like PyList_New and PyDict_New create a new object with a
       refcount of 1. They pass on the ownership of this reference to the
       caller, IE they return the reference and it becomes the caller's
       responsibility to call PyDECREF
    2. Functions like PyList_Append and PyDict_SetItem create a new reference
       to the items you pass them, IE they increase the ref count and will
       decrease it when they're done with it. This means that you retain
       ownership of your own reference to this items and will also need to
       call decref when you're done with them.
    3. PyList_SetItem and PyTuple_SetItem are exceptions to the rule: they
       "steal" a reference to the item you pass into them. This means they do
       not increase the refcount of the item, but _do_ decrease it when they
       themselves are destructed.
       This _only_ holds for the SetItem functions, and _only_ for list and
       tuple.
       The reasonining behind this is that it's a very common scenario for
       populating lists and tuples.
    4. PyList_GetItem and PyTuple_GetItem are exceptions to the rule: they
       return a "borrowed" reference to an item. This means you should never
       decref them!
       This _only_ holds for list and tuple.
    5. When you return a newly created reference from a function, you pass on
       the ownership of that reference to the calling function. This means you
       don't have to call DECREF on the return value of a function.
    6. References passed _into_ your function as arguments are _borrowed_:
       Their refcount doesn't change and you don't have to increase or decrease
       it. The object they point to is guaranteed to exist for as long as your
       function runs.

    Result:
    A. The log and protocol objects passed to this function are borrowed
       references: no need to change the reference count.
    B. The PyFloat objects that are created have refcount 1. They're added to
       the lists using append, which increases their refcount. So they should
       be decref'd after appending.
    C. The time float that is created has refcount 1. It's ownership is passed
       on to the calling function. No need to decref.
    D. The PyFloat objects in this list are added using PyList_SetItem which
       steals ownership: No need to decref.
    */

    /* Create state vector */
    y = N_VNew_Serial(N_STATE);
    if (check_cvode_flag((void*)y, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create state vector.");
        return sim_clean();
    }

    /* Create state vector copy for error handling */
    y_last = N_VNew_Serial(N_STATE);
    if (check_cvode_flag((void*)y_last, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create last-state vector.");
        return sim_clean();
    }

    /* Create sensitivity vector array */
    if (N_SENS) {
        sy = N_VCloneVectorArray(N_SENS, y);
        if (check_cvode_flag((void*)sy, "N_VCloneVectorArray", 0)) {
            PyErr_SetString(PyExc_Exception, "Failed to allocate space to store sensitivities.");
            return sim_clean();
        }
    }

   /* Determine if dynamic logging is being used (or if it's periodic/point-list logging) */
    dynamic_logging = (log_interval <= 0 && log_times == Py_None);

    /* Create state vector for logging.
       If we log every visited point (dynamic logging), we can simply log
       values from y as used for the integration. But if we need to interpolate
       times in the past, we need a vector y (and sy if using sensitivities) to
       store the state at time of logging in. */
    if (dynamic_logging || !USE_CVODE) {
        /* Dynamic logging or cvode-free mode: don't interpolate,
           so let y_log point to y */
        y_log = y;
        sy_log = sy;
    } else {
        /* Logging at fixed points:
           Keep y_log as a separate N_Vector for cvode interpolation */
        y_log = N_VNew_Serial(N_STATE);
        if (check_cvode_flag((void*)y_log, "N_VNew_Serial", 0)) {
            PyErr_SetString(PyExc_Exception, "Failed to create state vector for logging.");
            return sim_clean();
        }
        if (N_SENS) {
            sy_log = N_VCloneVectorArray(N_SENS, y);
            if (check_cvode_flag((void*)sy_log, "N_VCloneVectorArray", 0)) {
                PyErr_SetString(PyExc_Exception, "Failed to create state sensitivity vector array for logging.");
                return sim_clean();
            }
        }
    }

    /* Create derivative vector for logging.
       In both logging modes, the need arises to call rhs() manually, and so we
       need to create a dy_log vector to pass in (and an sdy_log vector array).
    */
    dy_log = N_VNew_Serial(N_STATE);
    if (check_cvode_flag((void*)dy_log, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create derivatives vector for logging.");
        return sim_clean();
    }
    if (N_SENS) {
        sdy_log = N_VCloneVectorArray(N_SENS, y);
        if (check_cvode_flag((void*)sdy_log, "N_VCloneVectorArray", 0)) {
            PyErr_SetString(PyExc_Exception, "Failed to create derivatives sensitivity vector array for logging.");
            return sim_clean();
        }
    }

    /* Set calculated constants (not including sensitivity parameters) */
    update_constants();

    /* Set initial values */
    if (!PyList_Check(state_in)) {
        PyErr_SetString(PyExc_Exception, "'state_in' must be a list.");
        return sim_clean();
    }
    for(i=0; i<N_STATE; i++) {
        flt = PyList_GetItem(state_in, i);    /* Don't decref! */
        if (!PyFloat_Check(flt)) {
            char errstr[200];
            sprintf(errstr, "Item %d in state vector is not a float.", i);
            PyErr_SetString(PyExc_Exception, errstr);
            return sim_clean();
        }
        NV_Ith_S(y, i) = PyFloat_AsDouble(flt);
        NV_Ith_S(y_last, i) = NV_Ith_S(y, i);
        /*if (!dynamic_logging) {
            NV_Ith_S(y_log, i) = NV_Ith_S(y, i);
        }*/
    }

    /* Set initial sensitivities to zero, or to 1 for initial conditions */
    for(i=0; i<N_SENS; i++) {
        N_VConst(RCONST(0.0), sy[i]);
    }
    NV_Ith_S(sy[2], 7) = 1.0;

    /*
    if (!dynamic_logging) {
        for(i=0; i<N_SENS; i++) {
            N_VConst(RCONST(0.0), sy_log[i]);
        }
        NV_Ith_S(sy_log[2], 7) = 1.0;
    }
    */

    /* Create and fill vector with parameter/initial condition values */
    udata = (UserData)malloc(sizeof *udata);
    if (udata == 0) {
        PyErr_SetString(PyExc_Exception, "Unable to allocate space to store parameter values.");
        return sim_clean();
    }
    udata->p[0] = AP_gNa;
    udata->p[1] = AP_gCa;
    udata->p[2] = NV_Ith_S(y, 7);

    /* Create parameter scaling vector, for error control */
    /* TODO: Let the user provide this? */
    for(i=0; i<N_SENS; i++) {
        pbar[i] = (udata->p[i] == 0.0 ? 1.0 : udata->p[i]);
    }

    /* Root finding list of integers (only contains 1 int...) */
    rootsfound = (int*)malloc(sizeof(int)*1);

    /* Reset evaluation count */
    engine_evaluations = 0;

    /* Reset step count */
    engine_steps = 0;

    /* Zero step tracking */
    zero_step_count = 0;

    /* Check output list */
    if (!PyList_Check(state_out)) {
        PyErr_SetString(PyExc_Exception, "'state_out' must be a list.");
        return sim_clean();
    }

    /* Check for loss-of-precision issue in periodic logging */
    if (log_interval > 0) {
        if (tmax + log_interval == tmax) {
            PyErr_SetString(PyExc_Exception, "Log interval is too small compared to tmax; issue with numerical precision: float(tmax + log_interval) = float(tmax).");
            return sim_clean();
        }
    }

    /* Set up logging */
    log_inter = 0;
    log_bound = 0;
    n_vars = PyDict_Size(log_dict);
    logs = (PyObject**)malloc(sizeof(PyObject*)*n_vars);
    vars = (realtype**)malloc(sizeof(realtype*)*n_vars);
    i = 0;

    /* Note: The variable names are all ascii compatible
       In Python2, they are stored in logs as either unicode or bytes
       In Python3, they are stored exclusively as unicode
       However, in Python2 b'name' matches u'name' so this is ok (in Python it
        does not, but we always use unicode so it's ok).
       The strategy here will be to convert these C-strings to unicode
        inside log_add, before the comparison. */

    /* Check states */
    i += log_add(log_dict, logs, vars, i, "membrane.V", &NV_Ith_S(y_log, 0));
    i += log_add(log_dict, logs, vars, i, "ina.m", &NV_Ith_S(y_log, 1));
    i += log_add(log_dict, logs, vars, i, "ina.h", &NV_Ith_S(y_log, 2));
    i += log_add(log_dict, logs, vars, i, "ina.j", &NV_Ith_S(y_log, 3));
    i += log_add(log_dict, logs, vars, i, "ica.d", &NV_Ith_S(y_log, 4));
    i += log_add(log_dict, logs, vars, i, "ica.f", &NV_Ith_S(y_log, 5));
    i += log_add(log_dict, logs, vars, i, "ik.x", &NV_Ith_S(y_log, 6));
    i += log_add(log_dict, logs, vars, i, "ica.Ca_i", &NV_Ith_S(y_log, 7));


    /* Check derivatives */
    j = i;
    i += log_add(log_dict, logs, vars, i, "dot(membrane.V)", &NV_Ith_S(dy_log, 0));
    i += log_add(log_dict, logs, vars, i, "dot(ina.m)", &NV_Ith_S(dy_log, 1));
    i += log_add(log_dict, logs, vars, i, "dot(ina.h)", &NV_Ith_S(dy_log, 2));
    i += log_add(log_dict, logs, vars, i, "dot(ina.j)", &NV_Ith_S(dy_log, 3));
    i += log_add(log_dict, logs, vars, i, "dot(ica.d)", &NV_Ith_S(dy_log, 4));
    i += log_add(log_dict, logs, vars, i, "dot(ica.f)", &NV_Ith_S(dy_log, 5));
    i += log_add(log_dict, logs, vars, i, "dot(ik.x)", &NV_Ith_S(dy_log, 6));
    i += log_add(log_dict, logs, vars, i, "dot(ica.Ca_i)", &NV_Ith_S(dy_log, 7));

    log_deriv = (i > j);

    /* Check bound variables */
    j = i;
    i += log_add(log_dict, logs, vars, i, "engine.time", &AV_time);
    i += log_add(log_dict, logs, vars, i, "engine.pace", &AV_pace);

    log_bound = (i > j);

    /* Remaining variables will require an extra rhs() call to evaluate their
       values at every log point */
    j = i;
    i += log_add(log_dict, logs, vars, i, "membrane.i_ion", &AV_i_ion);
    i += log_add(log_dict, logs, vars, i, "membrane.i_stim", &AV_i_stim);
    i += log_add(log_dict, logs, vars, i, "ik.x.alpha", &AV_ik_x_alpha);
    i += log_add(log_dict, logs, vars, i, "ik.x.beta", &AV_ik_x_beta);
    i += log_add(log_dict, logs, vars, i, "ik.xi", &AV_xi);
    i += log_add(log_dict, logs, vars, i, "ik.IK", &AV_IK);
    i += log_add(log_dict, logs, vars, i, "ina.a", &AV_a);
    i += log_add(log_dict, logs, vars, i, "ina.m.alpha", &AV_ina_m_alpha);
    i += log_add(log_dict, logs, vars, i, "ina.m.beta", &AV_ina_m_beta);
    i += log_add(log_dict, logs, vars, i, "ina.h.alpha", &AV_ina_h_alpha);
    i += log_add(log_dict, logs, vars, i, "ina.h.beta", &AV_ina_h_beta);
    i += log_add(log_dict, logs, vars, i, "ina.j.alpha", &AV_ina_j_alpha);
    i += log_add(log_dict, logs, vars, i, "ina.j.beta", &AV_ina_j_beta);
    i += log_add(log_dict, logs, vars, i, "ina.INa", &AV_INa);
    i += log_add(log_dict, logs, vars, i, "ikp.Kp", &AV_Kp);
    i += log_add(log_dict, logs, vars, i, "ikp.IKp", &AV_IKp);
    i += log_add(log_dict, logs, vars, i, "ica.E", &AV_ica_E);
    i += log_add(log_dict, logs, vars, i, "ica.d.alpha", &AV_ica_d_alpha);
    i += log_add(log_dict, logs, vars, i, "ica.d.beta", &AV_ica_d_beta);
    i += log_add(log_dict, logs, vars, i, "ica.f.alpha", &AV_ica_f_alpha);
    i += log_add(log_dict, logs, vars, i, "ica.f.beta", &AV_ica_f_beta);
    i += log_add(log_dict, logs, vars, i, "ica.ICa", &AV_ICa);
    i += log_add(log_dict, logs, vars, i, "ik1.g", &AV_g);
    i += log_add(log_dict, logs, vars, i, "ik1.g.alpha", &AV_ik1_g_alpha);
    i += log_add(log_dict, logs, vars, i, "ik1.g.beta", &AV_ik1_g_beta);
    i += log_add(log_dict, logs, vars, i, "ik1.IK1", &AV_IK1);
    i += log_add(log_dict, logs, vars, i, "ib.Ib", &AV_Ib);

    log_inter = (i > j);

    /* Check if log contained extra variables */
    if (i != n_vars) {
        PyErr_SetString(PyExc_Exception, "Unknown variables found in logging dictionary.");
        return sim_clean();
    }

    /* Check logging list for sensitivities */
    if (N_SENS) {
        if (!PyList_Check(sens_list)) {
            PyErr_SetString(PyExc_Exception, "'sens_list' must be a list.");
            return sim_clean();
        }
    }

    /* Set up event-based pacing */
    if (eprotocol != Py_None) {
        epacing = ESys_Create(&flag_epacing);
        if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
        flag_epacing = ESys_Populate(epacing, eprotocol);
        if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
        flag_epacing = ESys_AdvanceTime(epacing, tmin);
        if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
        tnext = ESys_GetNextTime(epacing, &flag_epacing);
        engine_pace = ESys_GetLevel(epacing, &flag_epacing);
        tnext = (tnext < tmax) ? tnext : tmax;
    } else {
        tnext = tmax;
    }

    /* Set up fixed-form pacing */
    if (eprotocol == Py_None && fprotocol != Py_None) {
        /* Check 'protocol' is tuple (times, values) */
        if (!PyTuple_Check(fprotocol)) {
            PyErr_SetString(PyExc_Exception, "Fixed-form pacing protocol should be tuple or None.");
            return sim_clean();
        }
        if (PyTuple_Size(fprotocol) != 2) {
            PyErr_SetString(PyExc_Exception, "Fixed-form pacing protocol tuple should have size 2.");
            return sim_clean();
        }
        /* Create fixed-form pacing object and populate */
        fpacing = FSys_Create(&flag_fpacing);
        if (flag_fpacing != FSys_OK) { FSys_SetPyErr(flag_fpacing); return sim_clean(); }
        flag_fpacing = FSys_Populate(fpacing,
            PyTuple_GetItem(fprotocol, 0),  /* Borrowed, no decref */
            PyTuple_GetItem(fprotocol, 1));
        if (flag_fpacing != FSys_OK) { FSys_SetPyErr(flag_fpacing); return sim_clean(); }
    }

    /* Set simulation starting time */
    engine_time = tmin;

    /* Check dt_max and dt_min */
    if (dt_max < 0) dt_max = 0.0;
    if (dt_min < 0) dt_min = 0.0;

    /* Create solver
     * Using Backward differentiation and Newton iteration */
    #if USE_CVODE > 0
    #if MYOKIT_SUNDIALS_VERSION >= 40000
        cvode_mem = CVodeCreate(CV_BDF);
    #else
        cvode_mem = CVodeCreate(CV_BDF, CV_NEWTON);
    #endif
    if (check_cvode_flag((void*)cvode_mem, "CVodeCreate", 0)) return sim_clean();

    /* Initialise solver memory, specify the rhs */
    flag_cvode = CVodeInit(cvode_mem, rhs, engine_time, y);
    if (check_cvode_flag(&flag_cvode, "CVodeInit", 1)) return sim_clean();

    /* Set absolute and relative tolerances */
    flag_cvode = CVodeSStolerances(cvode_mem, RCONST(rel_tol), RCONST(abs_tol));
    if (check_cvode_flag(&flag_cvode, "CVodeSStolerances", 1)) return sim_clean();

    /* Set a maximum step size (or 0.0 for none) */

    flag_cvode = CVodeSetMaxStep(cvode_mem, dt_max);
    if (check_cvode_flag(&flag_cvode, "CVodeSetmaxStep", 1)) return sim_clean();

    /* Set a minimum step size (or 0.0 for none) */
    flag_cvode = CVodeSetMinStep(cvode_mem, dt_min);
    if (check_cvode_flag(&flag_cvode, "CVodeSetminStep", 1)) return sim_clean();

    #if MYOKIT_SUNDIALS_VERSION >= 30000
        /* Create dense matrix for use in linear solves */
        sundense_matrix = SUNDenseMatrix(N_STATE, N_STATE);
        if(check_cvode_flag((void *)sundense_matrix, "SUNDenseMatrix", 0)) return sim_clean();

        /* Create dense linear solver object with matrix */
        sundense_solver = SUNDenseLinearSolver(y, sundense_matrix);
        if(check_cvode_flag((void *)sundense_solver, "SUNDenseLinearSolver", 0)) return sim_clean();

        /* Attach the matrix and solver to cvode */
        flag_cvode = CVDlsSetLinearSolver(cvode_mem, sundense_solver, sundense_matrix);
        if(check_cvode_flag(&flag_cvode, "CVDlsSetLinearSolver", 1)) return sim_clean();
    #else
        /* Create dense matrix for use in linear solves */
        flag_cvode = CVDense(cvode_mem, N_STATE);
        if (check_cvode_flag(&flag_cvode, "CVDense", 1)) return sim_clean();
    #endif

    /* Activate forward sensitivity computations */
    if (N_SENS) {
        /* TODO: NULL here is the place to insert a user function to calculate the
           RHS of the sensitivity ODE */
        /*flag_cvode = CVodeSensInit(cvode_mem, N_SENS, CV_SIMULTANEOUS, rhs1, sy);*/
        flag_cvode = CVodeSensInit(cvode_mem, N_SENS, CV_SIMULTANEOUS, NULL, sy);
        if (check_cvode_flag(&flag_cvode, "CVodeSensInit", 1)) return sim_clean();

        /* Attach user data */
        flag_cvode = CVodeSetUserData(cvode_mem, udata);
        if (check_cvode_flag(&flag_cvode, "CVodeSetUserData", 1)) return sim_clean();

        /* Set parameter scales used in tolerances */
        flag_cvode = CVodeSetSensParams(cvode_mem, udata->p, pbar, NULL);
        if (check_cvode_flag(&flag_cvode, "CVodeSetSensParams", 1)) return sim_clean();

        /* Set sensitivity tolerances calculating method (using pbar) */
        flag_cvode = CVodeSensEEtolerances(cvode_mem);
        if (check_cvode_flag(&flag_cvode, "CVodeSensEEtolerances", 1)) return sim_clean();
    }

    #endif

    /* Benchmarking? Then set engine_realtime to 0.0 */
    if (benchtime != Py_None) {
        /* Store initial time as 0 */
        engine_realtime = 0.0;
        /* Tell sim_step to set engine_starttime */
        engine_starttime = -1;
    }

    /* Set string for updating lists/arrays using Python interface. */
    list_update_str = PyUnicode_FromString("append");

    /* Set logging points */
    if (log_interval > 0) {

        /* Periodic logging */
        ilog = 0;
        tlog = tmin;

    } else if (log_times != Py_None) {

        /* Point-list logging */

        /* Check the log_times list */
        if (!PyList_Check(log_times)) {
            PyErr_SetString(PyExc_Exception, "'log_times' must be a list.");
            return sim_clean();
        }

        /* Read next log point off the list */
        ilog = 0;
        tlog = engine_time - 1;
        while(ilog < PyList_Size(log_times) && tlog < engine_time) {
            flt = PyList_GetItem(log_times, ilog); /* Borrowed */
            if (!PyFloat_Check(flt)) {
                PyErr_SetString(PyExc_Exception, "Entries in 'log_times' must be floats.");
                return sim_clean();
            }
            tlog = PyFloat_AsDouble(flt);
            ilog++;
            flt = NULL;
        }

        /* No points beyond engine_time? Then don't log any future points. */
        if(tlog < engine_time) {
            tlog = tmax + 1;
        }

    } else {

        /*
         * Dynamic logging
         *
         * Log the first entry, but only if not appending to an existing log.
         * This prevents points from appearing twice when a simulation with
         * dynamic logging is stopped and started.
         */

        /*  Check if the log is empty */
        log_first_point = 1;
        pos = 0;
        if(PyDict_Next(log_dict, &pos, &key, &value)) {
            /* Items found in dict, randomly selected list now in "value" */
            /* Both key and value are borrowed references, no need to decref */
            log_first_point = (PyObject_Size(value) <= 0);
        }

        /* If so, log the first point! */
        if (log_first_point) {
            rhs(engine_time, y, dy_log, udata);
            /* At this point, we have y(t), inter(t) and dy(t) */
            /* We've also loaded time(t) and pace(t) */
            for(i=0; i<n_vars; i++) {
                flt = PyFloat_FromDouble(*vars[i]);
                ret = PyObject_CallMethodObjArgs(logs[i], list_update_str, flt, NULL);
                Py_DECREF(flt);
                Py_XDECREF(ret);
                if (ret == NULL) {
                    flt = NULL;
                    PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                    return sim_clean();
                }
            }
            flt = NULL;
            ret = NULL;

            if (N_SENS) {
                /* Calculate sensitivities to output */

                /* TODO: Call the rhs function that sets sdy_log */
                calculate_sensitivity_outputs(engine_time, y, dy_log, sy, sdy_log, udata);

                /* Write sensitivity matrix to log */
                l1 = PyTuple_New(2);
                if (l1 == NULL) return sim_clean();

                l2 = PyTuple_New(N_SENS);
                if (l2 == NULL) return sim_clean();

                flt = PyFloat_FromDouble(NV_Ith_S(sy[0], 0));
                if (flt == NULL) return sim_clean();
                flag = PyTuple_SetItem(l2, 0, flt); /* Steals reference to flt */
                if (flag < 0) return sim_clean();
                flt = PyFloat_FromDouble(NV_Ith_S(sy[1], 0));
                if (flt == NULL) return sim_clean();
                flag = PyTuple_SetItem(l2, 1, flt); /* Steals reference to flt */
                if (flag < 0) return sim_clean();
                flt = PyFloat_FromDouble(NV_Ith_S(sy[2], 0));
                if (flt == NULL) return sim_clean();
                flag = PyTuple_SetItem(l2, 2, flt); /* Steals reference to flt */
                if (flag < 0) return sim_clean();

                flag = PyTuple_SetItem(l1, 0, l2); /* Steals reference to l2 */
                l2 = NULL; flt = NULL;

                l2 = PyTuple_New(N_SENS);
                if (l2 == NULL) return sim_clean();

                flt = PyFloat_FromDouble(S0_V_INa);
                if (flt == NULL) return sim_clean();
                flag = PyTuple_SetItem(l2, 0, flt); /* Steals reference to flt */
                if (flag < 0) return sim_clean();
                flt = PyFloat_FromDouble(S1_V_INa);
                if (flt == NULL) return sim_clean();
                flag = PyTuple_SetItem(l2, 1, flt); /* Steals reference to flt */
                if (flag < 0) return sim_clean();
                flt = PyFloat_FromDouble(S2_V_INa);
                if (flt == NULL) return sim_clean();
                flag = PyTuple_SetItem(l2, 2, flt); /* Steals reference to flt */
                if (flag < 0) return sim_clean();

                flag = PyTuple_SetItem(l1, 1, l2); /* Steals reference to l2 */
                l2 = NULL; flt = NULL;

                flag = PyList_Append(sens_list, l1);
                Py_XDECREF(l1); l1 = NULL;
                if (flag < 0) return sim_clean();

            }
        }
    }

    /* Root finding enabled? (cvode-mode only) */
    #if USE_CVODE
    if (PySequence_Check(root_list)) {
        /* Set threshold */
        rootfinding_threshold = root_threshold;
        /* Initialize root function with 1 component */
        flag_cvode = CVodeRootInit(cvode_mem, 1, root_finding);
        if (check_cvode_flag(&flag_cvode, "CVodeRootInit", 1)) return sim_clean();
    }
    #endif

    /* Done! */
    Py_RETURN_NONE;
}

/*
 * Takes the next steps in a simulation run
 */
static PyObject*
sim_step(PyObject *self, PyObject *args)
{
    ESys_Flag flag_epacing;
    int i;
    int steps_taken = 0;    /* Number of integration steps taken in this call */
    int flag_cvode;         /* CVode flag */
    int flag_root;          /* Root finding flag */
    int flag_reinit = 0;    /* Set if CVODE needs to be reset during a simulation step */
    int flag;               /* General flag for python operations */
    PyObject *flt, *ret;
    PyObject *l1, *l2;

    /*
     * Benchmarking? Then make sure start time is set.
     * This is handled here instead of in sim_init so it only includes time
     * taken performing steps, not time initialising memory etc.
     */
    if (benchtime != Py_None && engine_starttime < 0) {
        flt = PyObject_CallFunction(benchtime, "");
        if (!PyFloat_Check(flt)) {
            Py_XDECREF(flt); flt = NULL;
            PyErr_SetString(PyExc_Exception, "Call to benchmark time function didn't return float.");
            return sim_clean();
        }
        engine_starttime = PyFloat_AsDouble(flt);
        Py_DECREF(flt); flt = NULL;
    }

    /* Go! */
    while(1) {

        /* Back-up current y (no allocation, this is fast) */
        for(i=0; i<N_STATE; i++) {
            NV_Ith_S(y_last, i) = NV_Ith_S(y, i);
        }

        /* Store engine time before step */
        engine_time_last = engine_time;

        #if USE_CVODE

        /* Take a single ODE step */
        flag_cvode = CVode(cvode_mem, tnext, y, &engine_time, CV_ONE_STEP);

        /* Check for errors */
        if (check_cvode_flag(&flag_cvode, "CVode", 1)) {
            /* Something went wrong... Set outputs and return */
            for(i=0; i<N_STATE; i++) {
                PyList_SetItem(state_out, i, PyFloat_FromDouble(NV_Ith_S(y_last, i)));
                /* PyList_SetItem steals a reference: no need to decref the double! */
            }
            PyList_SetItem(inputs, 0, PyFloat_FromDouble(engine_time));
            PyList_SetItem(inputs, 1, PyFloat_FromDouble(engine_pace));
            PyList_SetItem(inputs, 2, PyFloat_FromDouble(engine_realtime));
            PyList_SetItem(inputs, 3, PyFloat_FromDouble(engine_evaluations));
            return sim_clean();
        }

        #else

        /* Just jump to next event */
        /* Note 1: To stay compatible with cvode-mode, don't jump to the
           next log time (if tlog < tnext) */
        /* Note 2: tnext can be infinity, so don't always jump there. */
        engine_time = (tmax > tnext) ? tnext : tmax;
        flag_cvode = CV_SUCCESS;

        #endif

        /* Check if progress is being made */
        if(engine_time == engine_time_last) {
            if(++zero_step_count >= max_zero_step_count) {
                char errstr[200];
                sprintf(errstr, "ZERO_STEP %f", engine_time);
                PyErr_SetString(PyExc_Exception, errstr);
                return sim_clean();
            }
        } else {
            /* Only count consecutive zero steps! */
            zero_step_count = 0;
        }

        /* Update step count */
        engine_steps++;

        /* If we got to this point without errors... */
        if ((flag_cvode == CV_SUCCESS) || (flag_cvode == CV_ROOT_RETURN)) {

            /* Next event time exceeded? (Can't happen in cvode-free mode) */
            #if USE_CVODE
            if (engine_time > tnext) {

                /* Go back to engine_time=tnext */
                flag_cvode = CVodeGetDky(cvode_mem, tnext, 0, y);
                if (check_cvode_flag(&flag_cvode, "CVodeGetDky", 1)) return sim_clean();
                if (N_SENS) {
                    flag_cvode = CVodeGetSensDky(cvode_mem, tnext, 0, sy);
                    if (check_cvode_flag(&flag_cvode, "CVodeGetSensDky", 1)) return sim_clean();
                }
                engine_time = tnext;
                /* Require reinit (after logging) */
                flag_reinit = 1;

            } else if (flag_cvode == CV_ROOT_RETURN) {

                /* Store found roots */
                flag_root = CVodeGetRootInfo(cvode_mem, rootsfound);
                if (check_cvode_flag(&flag_root, "CVodeGetRootInfo", 1)) return sim_clean();
                flt = PyTuple_New(2);
                PyTuple_SetItem(flt, 0, PyFloat_FromDouble(engine_time)); /* Steals reference, so this is ok */
                PyTuple_SetItem(flt, 1, PyLong_FromLong(rootsfound[0]));
                ret = PyObject_CallMethodObjArgs(root_list, list_update_str, flt, NULL);
                Py_DECREF(flt); flt = NULL;
                Py_XDECREF(ret);
                if (ret == NULL) {
                    PyErr_SetString(PyExc_Exception, "Call to append() failed on root finding list.");
                    return sim_clean();
                }
                ret = NULL;
            }
            #endif

            /* Periodic logging or point-list logging */
            if (!dynamic_logging && engine_time > tlog) {
                /* Note: For periodic logging, the condition should be
                   `time > tlog` so that we log half-open intervals (i.e. the
                   final point should never be included). */

                /* Benchmarking? Then set engine_realtime */
                if (benchtime != Py_None) {
                    flt = PyObject_CallFunction(benchtime, "");
                    if (!PyFloat_Check(flt)) {
                        Py_XDECREF(flt); flt = NULL;
                        PyErr_SetString(PyExc_Exception, "Call to benchmark time function didn't return float.");
                        return sim_clean();
                    }
                    engine_realtime = PyFloat_AsDouble(flt) - engine_starttime;
                    Py_DECREF(flt); flt = NULL;

                    /* Update any variables bound to realtime */
                    update_realtime_bindings(engine_time);
                }

                /* Log points */
                while (engine_time > tlog) {

                    /* Get interpolated y(tlog) */
                    #if USE_CVODE
                    flag_cvode = CVodeGetDky(cvode_mem, tlog, 0, y_log);
                    if (check_cvode_flag(&flag_cvode, "CVodeGetDky", 1)) return sim_clean();
                    if (N_SENS) {
                        flag_cvode = CVodeGetSensDky(cvode_mem, tlog, 0, sy_log);
                        if (check_cvode_flag(&flag_cvode, "CVodeGetSensDky", 1)) return sim_clean();
                    }
                    #endif
                    /* If cvode-free mode, the state can't change so we don't
                       need to do anything here */

                    /* Calculate intermediate variables & derivatives */
                    rhs(tlog, y_log, dy_log, udata);

                    /* Write to log */
                    for(i=0; i<n_vars; i++) {
                        flt = PyFloat_FromDouble(*vars[i]);
                        ret = PyObject_CallMethodObjArgs(logs[i], list_update_str, flt, NULL);
                        Py_DECREF(flt);
                        Py_XDECREF(ret);
                        if (ret == NULL) {
                            flt = NULL;
                            PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                            return sim_clean();
                        }
                    }
                    ret = flt = NULL;

                    if (N_SENS) {
                        /* Calculate sensitivities to output */
                        calculate_sensitivity_outputs(engine_time, y, dy_log, sy_log, sdy_log, udata);

                        /* Write sensitivity matrix to log */
                        l1 = PyTuple_New(2);
                        if (l1 == NULL) return sim_clean();

                        l2 = PyTuple_New(N_SENS);
                        if (l2 == NULL) return sim_clean();

                        flt = PyFloat_FromDouble(NV_Ith_S(sy_log[0], 0));
                        if (flt == NULL) return sim_clean();
                        flag = PyTuple_SetItem(l2, 0, flt); /* Steals reference to flt */
                        if (flag < 0) return sim_clean();
                        flt = PyFloat_FromDouble(NV_Ith_S(sy_log[1], 0));
                        if (flt == NULL) return sim_clean();
                        flag = PyTuple_SetItem(l2, 1, flt); /* Steals reference to flt */
                        if (flag < 0) return sim_clean();
                        flt = PyFloat_FromDouble(NV_Ith_S(sy_log[2], 0));
                        if (flt == NULL) return sim_clean();
                        flag = PyTuple_SetItem(l2, 2, flt); /* Steals reference to flt */
                        if (flag < 0) return sim_clean();

                        flag = PyTuple_SetItem(l1, 0, l2); /* Steals reference to l2 */
                        l2 = NULL; flt = NULL;

                        l2 = PyTuple_New(N_SENS);
                        if (l2 == NULL) return sim_clean();

                        flt = PyFloat_FromDouble(S0_V_INa);
                        if (flt == NULL) return sim_clean();
                        flag = PyTuple_SetItem(l2, 0, flt); /* Steals reference to flt */
                        if (flag < 0) return sim_clean();
                        flt = PyFloat_FromDouble(S1_V_INa);
                        if (flt == NULL) return sim_clean();
                        flag = PyTuple_SetItem(l2, 1, flt); /* Steals reference to flt */
                        if (flag < 0) return sim_clean();
                        flt = PyFloat_FromDouble(S2_V_INa);
                        if (flt == NULL) return sim_clean();
                        flag = PyTuple_SetItem(l2, 2, flt); /* Steals reference to flt */
                        if (flag < 0) return sim_clean();

                        flag = PyTuple_SetItem(l1, 1, l2); /* Steals reference to l2 */
                        l2 = NULL; flt = NULL;

                        flag = PyList_Append(sens_list, l1);
                        Py_XDECREF(l1); l1 = NULL;
                        if (flag < 0) return sim_clean();

                    }

                    /* Get next logging point */
                    if (log_interval > 0) {
                        /* Periodic logging */
                        ilog++;
                        tlog = tmin + (double)ilog * log_interval;
                        if (ilog == 0) {
                            /* Unsigned int wraps around instead of overflowing, becomes zero again */
                            PyErr_SetString(PyExc_Exception, "Overflow in logged step count: Simulation too long!");
                            return sim_clean();
                        }
                    } else {
                        /* Point-list logging */
                        /* Read next log point off the list */
                        if (ilog < PyList_Size(log_times)) {
                            flt = PyList_GetItem(log_times, ilog); /* Borrowed */
                            if (!PyFloat_Check(flt)) {
                                PyErr_SetString(PyExc_Exception, "Entries in 'log_times' must be floats.");
                                return sim_clean();
                            }
                            tlog = PyFloat_AsDouble(flt);
                            ilog++;
                            flt = NULL;
                        } else {
                            tlog = tmax + 1;
                        }
                    }
                }
            }

            /* Event-based pacing */

            /* At this point we have logged everything _before_ engine_time, so
               it's safe to update the pacing mechanism. */
            if (epacing != NULL) {
                flag_epacing = ESys_AdvanceTime(epacing, engine_time);
                if (flag_epacing != ESys_OK) { ESys_SetPyErr(flag_epacing); return sim_clean(); }
                tnext = ESys_GetNextTime(epacing, NULL);
                engine_pace = ESys_GetLevel(epacing, NULL);
                tnext = (tnext < tmax) ? tnext : tmax;
            }

            /* Dynamic logging: Log every visited point */
            if (dynamic_logging) {

                /* Ensure the logged values are correct for the new time t */
                if (log_deriv || log_inter) {
                    /* If logging derivatives or intermediaries, calculate the
                       values for the current time. */
                    rhs(engine_time, y, dy_log, udata);
                } else if (log_bound) {
                    /* Logging bounds but not derivs or inters: No need to run
                       full rhs, just update bound variables */
                    update_bindings(engine_time);
                }

                /* Benchmarking? Then set engine_realtime */
                if (benchtime != Py_None) {
                    flt = PyObject_CallFunction(benchtime, "");
                    if (!PyFloat_Check(flt)) {
                        Py_XDECREF(flt); flt = NULL;
                        PyErr_SetString(PyExc_Exception, "Call to benchmark time function didn't return float.");
                        return sim_clean();
                    }
                    engine_realtime = PyFloat_AsDouble(flt) - engine_starttime;
                    Py_DECREF(flt); flt = NULL;

                    /* Update any variables bound to realtime */
                    update_realtime_bindings(engine_time);
                }

                /* Write to log */
                for(i=0; i<n_vars; i++) {
                    flt = PyFloat_FromDouble(*vars[i]);
                    ret = PyObject_CallMethodObjArgs(logs[i], list_update_str, flt, NULL);
                    Py_DECREF(flt); flt = NULL;
                    Py_XDECREF(ret);
                    if (ret == NULL) {
                        PyErr_SetString(PyExc_Exception, "Call to append() failed on logging list.");
                        return sim_clean();
                    }
                    ret = NULL;
                }

                if (N_SENS) {
                    /* Get current sensitivities */
                    flag_cvode = CVodeGetSens(cvode_mem, &engine_time, sy_log);
                    if (check_cvode_flag(&flag_cvode, "CVodeGetSens", 1)) return sim_clean();

                    /* Calculate sensitivities to output */
                    calculate_sensitivity_outputs(engine_time, y, dy_log, sy, sdy_log, udata);

                    /* Write sensitivity matrix to log */
                    l1 = PyTuple_New(2);
                    if (l1 == NULL) return sim_clean();

                    l2 = PyTuple_New(N_SENS);
                    if (l2 == NULL) return sim_clean();

                    flt = PyFloat_FromDouble(NV_Ith_S(sy[0], 0));
                    if (flt == NULL) return sim_clean();
                    flag = PyTuple_SetItem(l2, 0, flt); /* Steals reference to flt */
                    if (flag < 0) return sim_clean();
                    flt = PyFloat_FromDouble(NV_Ith_S(sy[1], 0));
                    if (flt == NULL) return sim_clean();
                    flag = PyTuple_SetItem(l2, 1, flt); /* Steals reference to flt */
                    if (flag < 0) return sim_clean();
                    flt = PyFloat_FromDouble(NV_Ith_S(sy[2], 0));
                    if (flt == NULL) return sim_clean();
                    flag = PyTuple_SetItem(l2, 2, flt); /* Steals reference to flt */
                    if (flag < 0) return sim_clean();

                    flag = PyTuple_SetItem(l1, 0, l2); /* Steals reference to l2 */
                    l2 = NULL; flt = NULL;

                    l2 = PyTuple_New(N_SENS);
                    if (l2 == NULL) return sim_clean();

                    flt = PyFloat_FromDouble(S0_V_INa);
                    if (flt == NULL) return sim_clean();
                    flag = PyTuple_SetItem(l2, 0, flt); /* Steals reference to flt */
                    if (flag < 0) return sim_clean();
                    flt = PyFloat_FromDouble(S1_V_INa);
                    if (flt == NULL) return sim_clean();
                    flag = PyTuple_SetItem(l2, 1, flt); /* Steals reference to flt */
                    if (flag < 0) return sim_clean();
                    flt = PyFloat_FromDouble(S2_V_INa);
                    if (flt == NULL) return sim_clean();
                    flag = PyTuple_SetItem(l2, 2, flt); /* Steals reference to flt */
                    if (flag < 0) return sim_clean();

                    flag = PyTuple_SetItem(l1, 1, l2); /* Steals reference to l2 */
                    l2 = NULL; flt = NULL;

                    flag = PyList_Append(sens_list, l1);
                    Py_XDECREF(l1); l1 = NULL;
                    if (flag < 0) return sim_clean();

                }

            }

            /* Reinitialize if needed (cvode-mode only) */
            #if USE_CVODE
            if (flag_reinit) {
                flag_reinit = 0;
                /* Re-init */
                flag_cvode = CVodeReInit(cvode_mem, engine_time, y);
                if (check_cvode_flag(&flag_cvode, "CVodeReInit", 1)) return sim_clean();
                flag_cvode = CVodeSensReInit(cvode_mem, CV_SIMULTANEOUS, sy);
                if (check_cvode_flag(&flag_cvode, "CVodeSensReInit", 1)) return sim_clean();
            }
            #endif
        }

        /* Check if we're finished */
        if (ESys_eq(engine_time, tmax)) engine_time = tmax;
        if (engine_time >= tmax) break;

        /* Perform any Python signal handling */
        if (PyErr_CheckSignals() != 0) {
            /* Exception (e.g. timeout or keyboard interrupt) occurred?
               Then cancel everything! */
            return sim_clean();
        }

        /* Report back to python after every x steps */
        steps_taken++;
        if (steps_taken >= 100) {
            return PyFloat_FromDouble(engine_time);
        }
    }

    /* Set final state */
    for(i=0; i<N_STATE; i++) {
        PyList_SetItem(state_out, i, PyFloat_FromDouble(NV_Ith_S(y, i)));
        /* PyList_SetItem steals a reference: no need to decref the double! */
    }

    /* Set state of inputs */
    PyList_SetItem(inputs, 0, PyFloat_FromDouble(engine_time));
    PyList_SetItem(inputs, 1, PyFloat_FromDouble(engine_pace));
    PyList_SetItem(inputs, 2, PyFloat_FromDouble(engine_realtime));
    PyList_SetItem(inputs, 3, PyFloat_FromDouble(engine_evaluations));

    sim_clean();    /* Ignore return value */
    return PyFloat_FromDouble(engine_time);
}

/*
 * Evaluates the state derivatives at the given state
 */
static PyObject*
sim_eval_derivatives(PyObject *self, PyObject *args)
{
    /* Declare variables here for C89 compatibility */
    int i;
    int success;
    int iState;
    double time_in;
    double pace_in;
    char errstr[200];
    PyObject *state;
    PyObject *deriv;
    PyObject *flt;
    N_Vector y;
    N_Vector dy;

    /* Start */
    success = 0;

    /* Check input arguments */
    if (!PyArg_ParseTuple(args, "OOdd", &state, &deriv, &time_in, &pace_in)) {
        PyErr_SetString(PyExc_Exception, "Expecting sequence arguments 'y' and 'dy' followed by floats 'time' and 'pace'.");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }
    if (!PySequence_Check(state)) {
        PyErr_SetString(PyExc_Exception, "First argument must support the sequence interface.");
        return 0;
    }
    if (!PySequence_Check(deriv)) {
        PyErr_SetString(PyExc_Exception, "Second argument must support the sequence interface.");
        return 0;
    }

    /* From this point on, no more direct returning: use goto error */
    y = NULL;      /* A cvode SERIAL vector */
    dy = NULL;     /* A cvode SERIAL vector */
    udata = NULL;  /* The user data, containing parameter values */
    #if MYOKIT_SUNDIALS_VERSION >= 30000
    sundense_matrix = NULL;     /* A matrix for linear solving */
    sundense_solver = NULL;     /* A linear solver */
    #endif

    /* Temporary object: decref before re-using for another var :) */
    /* (Unless you get them using PyList_GetItem...) */
    flt = NULL;   /* PyFloat */

    /* Create state vectors */
    y = N_VNew_Serial(N_STATE);
    if (check_cvode_flag((void*)y, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create state vector.");
        goto error;
    }
    dy = N_VNew_Serial(N_STATE);
    if (check_cvode_flag((void*)dy, "N_VNew_Serial", 0)) {
        PyErr_SetString(PyExc_Exception, "Failed to create state derivatives vector.");
        goto error;
    }

    /* Set calculated constants (not including sensitivity parameters) */
    update_constants();

    /* Set initial values */
    for (iState = 0; iState < N_STATE; iState++) {
        flt = PySequence_GetItem(state, iState); /* Remember to decref! */
        if (!PyFloat_Check(flt)) {
            Py_XDECREF(flt); flt = NULL;
            sprintf(errstr, "Item %d in state vector is not a float.", iState);
            PyErr_SetString(PyExc_Exception, errstr);
            goto error;
        }
        NV_Ith_S(y, iState) = PyFloat_AsDouble(flt);
        Py_DECREF(flt);
    }
    flt = NULL;

    /* Create and fill vector with parameter/initial condition values */
    udata = (UserData)malloc(sizeof *udata);
    if (udata == 0) {
        PyErr_SetString(PyExc_Exception, "Unable to allocate space to store parameter values.");
        return sim_clean();
    }
    udata->p[0] = AP_gNa;
    udata->p[1] = AP_gCa;
    udata->p[2] = NV_Ith_S(y, 7);


    /* Set simulation time and pacing variable */
    engine_time = time_in;
    engine_pace = pace_in;

    /* Evaluate derivatives */
    rhs(engine_time, y, dy, udata);

    /* Set output values */
    for(i=0; i<N_STATE; i++) {
        flt = PyFloat_FromDouble(NV_Ith_S(dy, i));
        if (flt == NULL) {
            PyErr_SetString(PyExc_Exception, "Unable to create float.");
            goto error;
        }
        PySequence_SetItem(deriv, i, flt);
        Py_DECREF(flt);
    }
    flt = NULL;

    /* Finished succesfully, free memory and return */
    success = 1;
error:
    /* Free CVODE space */
    N_VDestroy_Serial(y); y = NULL;
    N_VDestroy_Serial(dy); dy = NULL;

    /* Free udata space */
    free(udata); udata = NULL;

    /* Return */
    if (success) {
        Py_RETURN_NONE;
    } else {
        return 0;
    }
}

/*
 * Alters the value of a (literal) constant
 */
static PyObject*
sim_set_constant(PyObject *self, PyObject *args)
{
    double value;
    char* name;
    char errstr[200];

    /* Check input arguments */
    if (!PyArg_ParseTuple(args, "sd", &name, &value)) {
        PyErr_SetString(PyExc_Exception, "Expected input arguments: name (str), value (Float).");
        /* Nothing allocated yet, no pyobjects _created_, return directly */
        return 0;
    }

    if(strcmp("membrane.C", name) == 0) {
        AC_C = value;
        Py_RETURN_NONE;
    }
    if(strcmp("membrane.i_stim.stim_amplitude", name) == 0) {
        AC_stim_amplitude = value;
        Py_RETURN_NONE;
    }
    if(strcmp("membrane.i_diff", name) == 0) {
        AC_i_diff = value;
        Py_RETURN_NONE;
    }
    if(strcmp("ik.IK.PNa_K", name) == 0) {
        AC_PNa_K = value;
        Py_RETURN_NONE;
    }
    if(strcmp("ina.gNa", name) == 0) {
        AP_gNa = value;
        Py_RETURN_NONE;
    }
    if(strcmp("ina.p1", name) == 0) {
        AC_p1 = value;
        Py_RETURN_NONE;
    }
    if(strcmp("ikp.gKp", name) == 0) {
        AC_gKp = value;
        Py_RETURN_NONE;
    }
    if(strcmp("ica.gCa", name) == 0) {
        AP_gCa = value;
        Py_RETURN_NONE;
    }
    if(strcmp("ib.gb", name) == 0) {
        AC_gb = value;
        Py_RETURN_NONE;
    }
    if(strcmp("ib.Eb", name) == 0) {
        AC_Eb = value;
        Py_RETURN_NONE;
    }
    if(strcmp("cell.K_o", name) == 0) {
        AC_K_o = value;
        Py_RETURN_NONE;
    }
    if(strcmp("cell.K_i", name) == 0) {
        AC_K_i = value;
        Py_RETURN_NONE;
    }
    if(strcmp("cell.Na_o", name) == 0) {
        AC_Na_o = value;
        Py_RETURN_NONE;
    }
    if(strcmp("cell.Na_i", name) == 0) {
        AC_Na_i = value;
        Py_RETURN_NONE;
    }
    if(strcmp("cell.Ca_o", name) == 0) {
        AC_Ca_o = value;
        Py_RETURN_NONE;
    }
    if(strcmp("cell.R", name) == 0) {
        AC_R = value;
        Py_RETURN_NONE;
    }
    if(strcmp("cell.T", name) == 0) {
        AC_T = value;
        Py_RETURN_NONE;
    }
    if(strcmp("cell.F", name) == 0) {
        AC_F = value;
        Py_RETURN_NONE;
    }

    sprintf(errstr, "Constant not found: <%s>", name);
    PyErr_SetString(PyExc_Exception, errstr);
    return 0;
}

/*
 * Returns the number of steps taken in the last simulation
 */
static PyObject*
sim_steps(PyObject *self, PyObject *args)
{
    return PyLong_FromLong(engine_steps);
}

/*
 * Returns the number of rhs evaluations performed during the last simulation
 */
static PyObject*
sim_evals(PyObject *self, PyObject *args)
{
    return PyLong_FromLong(engine_evaluations);
}

/*
 * Methods in this module
 */
static PyMethodDef SimMethods[] = {
    {"sim_init", sim_init, METH_VARARGS, "Initialize the simulation."},
    {"sim_step", sim_step, METH_VARARGS, "Perform the next step in the simulation."},
    {"sim_clean", py_sim_clean, METH_VARARGS, "Clean up after an aborted simulation."},
    {"eval_derivatives", sim_eval_derivatives, METH_VARARGS, "Evaluate the state derivatives."},
    {"set_constant", sim_set_constant, METH_VARARGS, "Change a (literal) constant."},
    {"set_tolerance", sim_set_tolerance, METH_VARARGS, "Set the absolute and relative solver tolerance."},
    {"set_max_step_size", sim_set_max_step_size, METH_VARARGS, "Set the maximum solver step size (0 for none)."},
    {"set_min_step_size", sim_set_min_step_size, METH_VARARGS, "Set the minimum solver step size (0 for none)."},
    {"number_of_steps", sim_steps, METH_VARARGS, "Returns the number of steps taken in the last simulation."},
    {"number_of_evaluations", sim_evals, METH_VARARGS, "Returns the number of rhs evaluations performed during the last simulation."},
    {NULL},
};

/*
 * Module definition
 */
#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "myokit_sim_1_3638055208987718257",       /* m_name */
        "Generated CVODESim module",/* m_doc */
        -1,                         /* m_size */
        SimMethods,                 /* m_methods */
        NULL,                       /* m_reload */
        NULL,                       /* m_traverse */
        NULL,                       /* m_clear */
        NULL,                       /* m_free */
    };

    PyMODINIT_FUNC PyInit_myokit_sim_1_3638055208987718257(void) {
        return PyModule_Create(&moduledef);
    }

#else

    PyMODINIT_FUNC
    initmyokit_sim_1_3638055208987718257(void) {
        (void) Py_InitModule("myokit_sim_1_3638055208987718257", SimMethods);
    }

#endif

