.. _api/simulations/myokit.Protocol:

****************
Pacing protocols
****************

Myokit provides two "pacing" (or "driving") mechanisms to provide stimuli
during whole-cell or multi-cell simulations, or voltages during ion channel
simulations.

In most situations, you'll want the :class:`Protocol` class, which provides
"event-based" pacing. This can be used, for example, to specify a short pulse
every 1000ms for a single cell simulation, or to create a sequence of voltage
steps to apply in an ion channel simulation.

For applications like "action-potential clamping", a
:class:`TimeSeriesProtocol` can be used to drive the system with a
predetermined waveform.

.. currentmodule:: myokit
.. autoclass:: Protocol

.. _api/myokit.ProtocolEvent:
.. autoclass:: ProtocolEvent

.. autoclass:: PacingSystem

.. _api/myokit.TimeSeriesProtocol:
.. autoclass:: TimeSeriesProtocol

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

