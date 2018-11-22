.. _api/library/hh:

*****************************
Hodgkin-Huxley current models
*****************************

.. module:: myokit.lib.hh

The module ``myokit.lib.hh`` contains functions for working with Hodgkin-Huxley
models of ion channel currents.

The class ``HHModel`` can be used to extract a current model from a Myokit
 model.
By fixing the voltage and all other states that aren't part of the current
 model a linear system is created.

Fast simulations can then be performed using the
 :class:`AnalyticalSimulation` class, which is particularly useful when trying
 to estimate a current model's parameters from a piecewise-linear voltage
 protocol (e.g. a voltage step protocol).

In addition, several methods are provided to find and manipulate Hodgkin-Huxley
style gating variables.

Analytical simulation
---------------------

.. autoclass:: HHModel

.. autoclass:: HHModelError

.. autoclass:: AnalyticalSimulation


Finding and manipulating HH-states
----------------------------------

.. autofunction:: convert_hh_states_to_inf_tau_form

.. autofunction:: has_alpha_beta_form

.. autofunction:: has_inf_tau_form

.. autofunction:: get_alpha_and_beta

.. autofunction:: get_inf_and_tau

.. autofunction:: get_rl_expression

