.. _api/simulations/myokit.Protocol:

****************
Pacing protocols
****************

.. module:: myokit
.. autoclass:: Protocol
   :members:

.. _api/myokit.ProtocolEvent:
.. autoclass:: ProtocolEvent
   :members:

.. autoclass:: PacingSystem
    :members:

Protocol factory
================

.. module:: myokit.pacing

The ``myokit.pacing`` module provides a factory methods to facilitate the
creation of :class:`Protocol <myokit.Protocol>` objects directly from python.
This module is imported as part of the main ``myokit`` package.

Periodic pacing
---------------

.. autofunction:: bpm2bcl

.. autofunction:: blocktrain

Step protocols
--------------

.. autofunction:: constant

.. autofunction:: steptrain

.. autofunction:: steptrain_linear

