.. _api/library/approx:

**********************
Function approximation
**********************

.. module:: myokit.lib.approx

The module ``myokit.lib.approx`` contains a number of function approximation
algorithms.

*Some functions in this module require a recent version of scipy to be
installed.*

.. autoclass:: FittingError

.. autoclass:: FittedFunction

Simple polynomials
------------------

.. autoclass:: Polynomial

.. autofunction:: fit_remez_polynomial

.. autofunction:: fit_lagrange_polynomial


Piecewise polynomials
---------------------

.. autoclass:: PiecewisePolynomial

.. autoclass:: Spline

.. autofunction:: fit_cubic_spline

.. autofunction:: solve_cubic_spline


Model optimizers
----------------

.. autofunction:: list_fitters

.. autofunction:: suitable_expressions

.. autoclass:: Fitter
    :private-members:

.. autoclass:: CubicSplineFitter

.. autoclass:: PolynomialFitter

