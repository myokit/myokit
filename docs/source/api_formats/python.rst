.. _formats/python:

******
Python
******

Full simulation export to Python is provided.

Limitations:

  - For running simulations, this method is incredibly slow.

API
===

The standard exporting API is provided:

.. module:: myokit.formats.python

.. autofunction:: exporters

.. autoclass:: PythonExporter

.. autofunction:: ewriters

.. autoclass:: PythonExpressionWriter
    :inherited-members:

.. autoclass:: NumpyExpressionWriter
    :inherited-members:
