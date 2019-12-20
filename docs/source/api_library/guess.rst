.. _api/library/guess:

**************************
Guessing variable meanings
**************************

.. module:: myokit.lib.guess

The module ``myokit.lib.guess`` contains functions that can guess the meaning
of model variables.
In general, it's better to use annotation (e.g. labels and binds) for this sort
of thing.

In addition, the module contains methods that can manipulate models using these
guesses or other heuristics.

.. autofunction:: add_embedded_protocol

.. autofunction:: membrane_potential

.. autofunction:: remove_embedded_protocol

.. autofunction:: stimulus_current

.. autofunction:: stimulus_current_info

