.. _formats/channelml:

*********
ChannelML
*********

Limited support for import from ChannelML is provided.

Importer usage
==============

The ChannelML importer can be used to load a channel model from a ChannelML
file. The extracted model is presented as a full myokit cell model. This is
currently an experimental module.

API
===
The standard interfaces for importing is provided:

.. module:: myokit.formats.channelml

.. autofunction:: importers

.. autoclass:: ChannelMLImporter

.. autoclass:: ChannelMLError

