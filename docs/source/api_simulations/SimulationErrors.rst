.. _api/simulations/myokit.SimulationError:

*****************
Simulation errors
*****************

.. currentmodule:: myokit

Occasionally, a simulation will encounter a numerical error. Some simulation
types attempt to catch these errors and raise a :class:`SimulationError`. These
provide detailed error messages that can help diagnose the source of the error.

A common source of numerical errors is division by some term ``(x - c)``,
where ``x`` is a variable and ``c`` is a constant. Using double precision, this
should only happen very rarely and try-catch blocks around a simulation are not
typically necessary. This error is much more common when using single precision
(for example during a GPU enabled simulation) or when applying a step protocol
(for example, a term (V - 40) will not cause problems in most simulations, but
can trigger errors if V is stepped to exactly 40 mV. In these scenarios, it is
advised to add a try-catch block around a simulation::

    import myokit
    m,p,x = myokit.load('model.mmt')
    s = myokit.SimulationOpenCL(m, p, 64)
    try:
        s.run(1000)
    except myokit.SimulationError as e:
        print(str(e))

Example result::

    Encountered numerical error at t=411.054992676 in cell (55) when membrane.V=-77.0.
    Obtained 4 previous state(s).
    State before:
    membrane.V = -77.0
    ina.m      =  5.76317822560667992e-03
    ina.h      =  3.50723683834075928e-01
    ina.j      =  1.33311852812767029e-01
    ica.d      =  6.89173266291618347e-02
    ica.f      =  7.21855103969573975e-01
    ik.x       =  3.83078485727310181e-01
    ica.Ca_i   =  2.27514933794736862e-03
    State during:
    membrane.V = nan
    ina.m      =  5.75887179002165794e-03
    ina.h      =  3.50991368293762207e-01
    ina.j      =  1.33416950702667236e-01
    ica.d      =  6.88845962285995483e-02
    ica.f      =  7.21879780292510986e-01
    ik.x       =  3.83071571588516235e-01
    ica.Ca_i   =  2.27477238513529301e-03
    Evaluating derivatives at state before...
    invalid value encountered in float_scalars
    Encountered when evaluating
      if(membrane.V < -100.0, 1.0, 2.837 * (exp(0.04 * (membrane.V + 77.0))
                                   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            - 1.0) / ((membrane.V + 77.0) * exp(0.04 * (membrane.V + 35.0))))
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    With the following operands:
      (1) 0.0
      (2) 0.0
    And the following variables:
      membrane.V = -77.0
                 = -77.0

