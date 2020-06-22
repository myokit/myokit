.. _api/simulations/myokit.Jacobians:

*********
Jacobians
*********

.. currentmodule:: myokit


Myokit contains two classes designed to calculate Jacobian matrices. Given a
model ``f`` with state ``y`` such that ``dy/dt = f(y)`` the Jacobian is the
matrix of partial derivatives ``df/dy``. The :class:`JacobianCalculator` takes
a point in the state space as input and returns the corresponding Jacobian.
The :class:`JacobianTracer` does the same, but takes a full
:class:`DataLog` as input.

.. autoclass:: JacobianTracer

.. autoclass:: JacobianCalculator
