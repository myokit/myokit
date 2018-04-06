.. _guide/model-debugging:

****************
Debugging models
****************

.. module:: myokit

This guide section is all about comparing and debugging model implementations.
    
Comparing models numerically
----------------------------
The ``step`` method (or script) can be used to look at the derivatives
evaluated at a particular point in the state space::

    import myokit

    m1, p1, x = myokit.load('model_original.mmt')
    print(myokit.step(m1))
    
Result::

    Evaluating state vector derivatives...
    ---------------------------------------------------------------------------
    Name            Initial value             Derivative at t=0       
    ---------------------------------------------------------------------------
    membrane.V      -8.70000000000000000e+01   5.84012300615631905e-02
    if.y             2.00000000000000011e-01   8.14452812298453017e-04
    ik.x             1.00000000000000002e-02  -2.56856173779845835e-05
    ito.s            1.00000000000000000e+00  -2.17972078020338114e-06
    ina.m            1.00000000000000002e-02  -1.66828885378598246e-01
    ina.h            8.00000000000000044e-01   1.64222013568998335e-02
    isi.d            5.00000000000000010e-03  -4.08446523700718538e-03
    isi.f            1.00000000000000000e+00  -8.80171606671242855e-08
    isi.f2           1.00000000000000000e+00  -2.50000000000000222e-04
    sodium.Nai       8.00000000000000000e+00   1.30497167052043201e-06
    calcium.p        1.00000000000000000e+00  -8.80171606671242788e-09
    calcium.Ca_up    2.00000000000000000e+00  -1.75999999999999995e-04
    calcium.Ca_rel   1.00000000000000000e+00   4.50124688279301759e-04
    calcium.Cai      5.00000000000000024e-05  -7.54432063211346664e-07
    potassium.Kc     4.00000000000000000e+00  -2.73354844368036108e-05
    potassium.Ki     1.40000000000000000e+02   3.03573627901683266e-06
    ---------------------------------------------------------------------------

To compare two models (with the same state), you can specify a reference::

    import myokit

    m1, p1, x = myokit.load('model_original.mmt')
    m2, p2, x = myokit.load('model_modified.mmt')
    print(myokit.step(m1, reference=m2))

Result::

    Evaluating state vector derivatives...
    ---------------------------------------------------------------------------
    Name            Initial value             Derivative at t=0       
    ---------------------------------------------------------------------------
    membrane.V      -8.70000000000000000e+01   5.84012300615631905e-02
                                              -2.13880621883592078e-03 X !!!
                                                                  ^^^^
    if.y             2.00000000000000011e-01   8.14452812298453017e-04
                                               8.14452812298453017e-04
                                                                      
    ik.x             1.00000000000000002e-02  -2.56856173779845835e-05
                                              -2.56856173779845835e-05
                                                                      
    ito.s            1.00000000000000000e+00  -2.17972078020338114e-06
                                              -2.17972078020338114e-06
                                                                      
    ina.m            1.00000000000000002e-02  -1.66828885378598246e-01
                                              -1.66828885378598246e-01
                                                                      
    ina.h            8.00000000000000044e-01   1.64222013568998335e-02
                                               1.64222013568998335e-02
                                                                      
    isi.d            5.00000000000000010e-03  -4.08446523700718538e-03
                                              -4.08446523700718538e-03
                                                                      
    isi.f            1.00000000000000000e+00  -8.80171606671242855e-08
                                              -8.80171606671242855e-08
                                                                      
    isi.f2           1.00000000000000000e+00  -2.50000000000000222e-04
                                              -2.50000000000000222e-04
                                                                      
    sodium.Nai       8.00000000000000000e+00   1.30497167052043201e-06
                                              -8.76114615347809492e-06 X
                                              ^^^^^^^^^^^^^^^^^^^^^^^^
    calcium.p        1.00000000000000000e+00  -8.80171606671242788e-09
                                              -8.80171606671242788e-09
                                                                      
    calcium.Ca_up    2.00000000000000000e+00  -1.75999999999999995e-04
                                              -1.75999999999999995e-04
                                                                      
    calcium.Ca_rel   1.00000000000000000e+00   4.50124688279301759e-04
                                               4.50124688279301759e-04
                                                                      
    calcium.Cai      5.00000000000000024e-05  -7.54432063211346664e-07
                                               2.60094054478816253e-06 X !!!
                                                                  ^^^^
    potassium.Kc     4.00000000000000000e+00  -2.73354844368036108e-05
                                              -2.73354844368036108e-05
                                                                      
    potassium.Ki     1.40000000000000000e+02   3.03573627901683266e-06
                                               3.03573627901683266e-06
                                                                      
    Found (3) large mismatches between output and reference values.
    ---------------------------------------------------------------------------

Instead of using a second myokit model as a reference, a state can be read from
a file generated by an alternative implementation. An easy to way to access
this functionality is through the command-line script ``step``.

