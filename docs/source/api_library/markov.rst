.. _api/library/markov:

*************
Markov Models
*************

.. module:: myokit.lib.markov

The module ``myokit.lib.markov`` contains functions for working with
Markov models of ion channel currents.

The class ``LinearModel`` can be used to extract a Markov model from a Myokit
 model.
By fixing the voltage and all other states that aren't part of the
 Markov model a linear system is created.

Fast simulations can then be performed using the
 :class:`AnalyticalSimulation` class, which is particularly useful when trying
 to estimate a Markov model's parameters from a piecewise-linear voltage
 protocol (e.g. a normal step protocol).

Discrete, stochastic simulations can be performed using the
 :class:`DiscreteSimulation` class.

Analytical and discrete simulation
----------------------------------

.. autoclass:: LinearModel

.. autoclass:: LinearModelError

.. autoclass:: AnalyticalSimulation

.. autoclass:: DiscreteSimulation

Finding Markov models
---------------------

.. autofunction:: find_markov_models

Deprecated
----------

The following class was used in previous versions of Myokit (before 1.22.0).
It now exists only as an interface to the newer classes.
The MarkovModel class will be removed in future versions.

.. autoclass:: MarkovModel

