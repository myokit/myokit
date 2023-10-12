.. _formats/heka:

****************
HEKA PatchMaster
****************

.. module:: myokit.formats.heka

Support is provided for reading data and protocols from HEKA PatchMaster files
in the 2x90.2 format.

PatchMaster files can contain several experiments, ordered into "groups" and
"series". The :class:`Series` class implements Myokit's shared
:class:`myokit.formats.SweepSource` interface.

Importer
========

Protocols can be imported via the :class:`PatchMasterFile` class, or using the
:class:`PatchMasterImporter`.

.. autofunction:: importers

.. autoclass:: PatchMasterImporter

PatchMasterFile
===============

.. autoclass:: PatchMasterFile

Related classes
===============

PatchMaster files are structured as several trees, each starting at a virtual
"file". These can be accessed using the classes documented below.

"Pulsed file" classes
---------------------

A "pulsed file" provides access to data, structured in groups, series, sweeps,
and traces.

.. autoclass:: PulsedFile

.. autoclass:: Group

.. autoclass:: Series

.. autoclass:: Sweep

.. autoclass:: Trace

"Stimulus file" classes
-----------------------

A "stimulus file" provides access to stimulus information, structured in
stimuli, channels, and segments.

.. autoclass:: StimulusFile

.. autoclass:: Stimulus

.. autoclass:: StimulusChannel

.. autoclass:: Segment

.. autoclass:: SegmentClass

.. autoclass:: SegmentIncrement

.. autoclass:: SegmentStorage

.. autoclass:: AmplifierMode

.. autoclass:: NoSupportedDAChannelError

"Amplifier file" classes
------------------------

An "amplifier file" provides access to amplifier information in situations
where more than one amplifier was used.

.. autoclass:: AmplifierFile

.. autoclass:: AmplifierSeries

.. autoclass:: AmplifierState

.. autoclass:: AmplifierStateRecord


Internals
=========

PatchMaster files are structured as several trees.
These are read using the :class:`TreeNode` class, which makes use of the
:class:`EndianAwareReader` class.

.. autoclass:: TreeNode

.. autoclass:: EndianAwareReader

