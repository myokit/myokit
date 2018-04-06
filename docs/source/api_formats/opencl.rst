.. _formats/opencl:

******
OpenCL
******

Export to an OpenCL simulation. A driver is provided to run cable simulations
and a quick plot script is included.

Notes:

  - The generated code requires OpenCL enabled drivers for the GPU or CPU
    it's runnning on to be pre-installed, as well as an implementation of the
    OpenCL libraries. These can be downloaded from various hardware
    manufacturers' websites.

API
===

The standard interface for exporting and accessing expression writers is
provided:

.. module:: myokit.formats.opencl

.. autofunction:: exporters

.. autoclass:: OpenCLExporter

.. autofunction:: ewriters

.. autoclass:: OpenCLExpressionWriter

