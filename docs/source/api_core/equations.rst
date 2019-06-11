.. _api/equations:

*********
Equations
*********

.. currentmodule:: myokit

While the internal storage of equations may differ, when they are returned
equations are usually in the form of an :class:`Equation` object.

.. autoclass:: myokit.Equation
   :undoc-members:
   :inherited-members:

Equation lists
---------------

When returning a list of equations, the ``EquationList`` type is used. This
extends the python ``list`` type with a number of specialized iterators.

.. autoclass:: EquationList
   :undoc-members:
   :inherited-members:
