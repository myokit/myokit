.. _api/simulations/myokit.SimulationOpenCL:

*****************
OpenCL Simulation
*****************
.. module:: myokit

Myokit provides a simulation engine for parallelized multi-cellular
simulations, implemented using OpenCL. The engine can handle 1d and 2d
rectangular tissue or networks of arbitrarily connected cells. Heterogeneity
can be introduced by replacing model constants with fields, using the method
:meth:`set_field <SimulationOpenCL.set_field>`.

A two-model fiber and tissue simulation can be run using the
:class:`FiberTissueSimulation`.

Information about the available OpenCL devices can be obtained using the
:class:`OpenCL` class, which also allows the preferred device to be selected.
Note that this functionality is also accessible through the command-line
``myo`` script (see :ref:`opencl-select <cmd/openclselect>`).

.. autoclass:: SimulationOpenCL
    :members:

Fiber-Tissue Simulation
=======================

.. autoclass:: FiberTissueSimulation
    :members:

OpenCL utility classes
======================

.. autoclass:: OpenCL
    :members:
    
.. autoclass:: OpenCLInfo
    :members:
    
.. autoclass:: OpenCLPlatformInfo
    :members:
    
.. autoclass:: OpenCLDeviceInfo
    :members:
    

