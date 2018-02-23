.. _formats/sympy:

*****
Sympy
*****

Export and import of SymPy_ expressions

.. _Sympy: http://

Converting to and from SymPy
============================

.. module:: myokit.formats.sympy

.. autofunction:: write

.. autofunction:: read

API
===

The standard interface for exporting and accessing expression writers is
provided:

.. autofunction:: ewriters

.. autoclass:: SymPyExpressionWriter
    :members:
    :inherited-members:

.. autoclass:: SymPyExpressionReader
    :members:
