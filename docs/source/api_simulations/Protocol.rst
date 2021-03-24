.. _api/simulations/myokit.Protocol:

****************
Pacing protocols
****************

.. currentmodule:: myokit
.. autoclass:: Protocol

.. _api/myokit.ProtocolEvent:
.. autoclass:: ProtocolEvent

.. autoclass:: PacingSystem

Protocol factory
================

.. module:: myokit.pacing

The ``myokit.pacing`` module provides a factory methods to facilitate the
creation of :class:`Protocol <myokit.Protocol>` objects directly from python.
This module is imported automatically when ``import myokit`` is run.

Periodic pacing
---------------

.. autofunction:: bpm2bcl

.. autofunction:: blocktrain

Step protocols
--------------

.. autofunction:: constant

.. autofunction:: steptrain

.. autofunction:: steptrain_linear

