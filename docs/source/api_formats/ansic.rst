.. _formats/ansic:

**
C
**

Export to a simple Ansi-C format is provided based on the sundials_ ODE solver.

.. _sundials: https://computation.llnl.gov/casc/sundials/main.html

Limitations:

  - No plots or other post-processing are included


API
===

The standard interface for exporting and accessing expression writers is
provided:

.. module:: myokit.formats.ansic

.. autofunction:: exporters

.. autoclass:: AnsiCExporter

.. autoclass:: AnsiCCableExporter

.. autoclass:: AnsiCEulerExporter

.. autofunction:: ewriters

.. autoclass:: AnsiCExpressionWriter
    :inherited-members:
