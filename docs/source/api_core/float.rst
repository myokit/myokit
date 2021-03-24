.. _api/float:

**********************
Floating point numbers
**********************

Myokit includes a module ``myokit.float`` that contains methods to work with
floating point numbers.
These are used for example when checking if a pacing event has started or ended
*to within machine precision*, or when checking if two units are equivalent.
This module is imported automatically when ``import myokit`` is run.

.. currentmodule:: myokit.float

Comparison
==========

.. autofunction:: eq

.. autofunction:: geq

.. autofunction:: close

Rounding to integer
===================

.. autofunction:: cround

.. autofunction:: round

Conversion to string
====================

.. autofunction:: str

