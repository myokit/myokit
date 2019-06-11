.. _api/simulations:

******************
API :: Simulations
******************

.. currentmodule:: myokit

Single cell Simulations can be run using the :class:`Simulation` class. This
wraps around a model and a protocol object and provides an interface to the
on-the-fly generated C module. A similar class is provided to perform a
:class:`1d Simulation<Simulation1d>`. Parallelized 1d and 2d simulations can be
run using the class :class:`SimulationOpenCL` which can utilise all cores of a
CPU or GPU. This simulation type can also be used to investigate the effects of
parameter variations (in grids of uncoupled cells) or heterogeneity (in coupled
grids of cells).

Simulation results for all simulations are stored in a :class:`DataLog`. This
specialized dict type can be stored to disk using
:meth:`save <DataLog.save>` or :meth:`save_csv <DataLog.save_csv>`. One
or two-dimensional logs often take the shape of a rectangular grid. While the
:class:`DataLog` class is built for maximum flexibility and allows irregular
shapes, it can often be useful to exploit the rectangular grid shape of the
data. For these cases, the data logs can be converted to specialised structures
called :class:`DataBlock1d` and :class:`DataBlock2d`.

A few specialized classes are included in the simulations package. The
:class:`RhsBenchmarker` can be used to rapidly evaluate the running time of a
model's equations which can be useful to optimise model running times. The
:class:`JacobianCalculator` can be used to calculate a single Jacobian matrix,
while the :class:`JacobianTracer` can be run after a single cell simulation to
calculate the Jacobian matrix and (dominant) eigenvalues at every visited point
of the state space. The :class:`ICSimulation` goes a step further and runs a
full simulation where the jacobian is integrated along with the state
derivatives to calculate the partial derivatives of the state with respect to
the initial state values.


..  toctree::
    :hidden:

    Simulation
    SimulationOpenCL
    Simulation1d
    Protocol
    DataLog
    DataBlock
    Jacobians
    ICSimulation
    PSimulation
    RhsBenchmarker
    SimulationErrors
    LongSimulations
    backend

