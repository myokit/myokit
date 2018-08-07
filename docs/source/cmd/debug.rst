*********
``debug``
*********

Displays the calculation of a single variable from a model.

Example::

    $ myokit debug example.mmt v
    Variable not found, assuming "membrane.V"
    Showing membrane.V  (State variable)
    ------------------------------------------------------------
    unit: mV
    desc: The membrane potential
    ------------------------------------------------------------
    Initial value = -84.5286
    ------------------------------------------------------------
    ica.ICa         = -5.69307557845840514e-05
    membrane.i_stim = 0.0
    ib.Ib           = -9.66863706000000045e-01
    ikp.IKp         = 1.27313823914652343e-08
    ik1.IK1         = 1.03172820596243020e+00
    ik.IK           = -7.99485510998167170e-03
    ina.INa         = -1.19264480675140328e-05
    ------------------------------------------------------------
    dot(membrane.V) = membrane.i_stim - (ina.INa + ik.IK + ib.Ib + ikp.IKp
                        + ik1.IK1 + ica.ICa)
                    = -5.68008003799787276e-02

For the full syntax, see::

    $ myokit debug --help
