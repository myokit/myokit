********
``step``
********

Loads a model  and evaluates the derivatives of the state variables at the
initial time::

    $ python myo step example.mmt
    ---------------------------------------------------------------------------
    Single test step
    Reading model from example.mmt...
    Model LR1991 read successfully
    Evaluating state vector derivatives...
    ---------------------------------------------------------------------------
    Name        Initial value             Derivative at t=0
    ---------------------------------------------------------------------------
    membrane.V  -8.45285999999999973e+01  -5.68008003799787276e-02
    ina.m        1.69999999999999991e-03  -4.94961486033834719e-03
    ina.h        9.83199999999999963e-01   9.02025299127830887e-06
    ina.j        9.95484000000000036e-01  -3.70409866928434243e-04
    ica.d        3.00000000000000008e-06   3.68067721821794798e-04
    ica.f        1.00000000000000000e+00  -3.55010150519739432e-07
    ik.x         5.70000000000000021e-03  -2.04613933160084307e-07
    ica.Ca_i     2.00000000000000010e-04  -6.99430692442154227e-06
    ---------------------------------------------------------------------------

The results can be compared to a file containing reference values using
::

    $ python myo step example.mmt -ref ref_step.txt

To test with different initial values, another file can be included::

    $ python myo step example.mmt -ref ref_step.txt -ini ref_init.txt
    
For the full syntax, see::

    $ python myo step --help
