.. _api/io:

*******************
Reading and writing
*******************

.. currentmodule:: myokit

*This page is about reading and writing the* ``mmt`` *format used by Myokit.
For information about using Myokit with other formats, please check out the*
:ref:`api/formats` *section.*

Myokit models can be loaded form disk using :func:`load()` and stored using
:func:`save()`. Both these functions assume you're working with a full
``(model, protocol, script)`` tuple. Support for partial loading and saving
is provided through functions like :func:`load_model()` and :func:`split()`.

Similar functions are available to load save model states.

Basic commands
==============

.. autofunction:: load

.. autofunction:: save

.. autofunction:: parse

.. autofunction:: run

Using parts of mmt files
========================

.. autofunction:: load_model

.. autofunction:: load_protocol

.. autofunction:: load_script

.. autofunction:: split

.. autofunction:: save_model

.. autofunction:: save_protocol

.. autofunction:: save_script

Default mmt file parts
======================
When generating new ``mmt`` files, default protocols and scripts can be
inserted:

.. autofunction:: default_protocol

.. autofunction:: default_script


Parsing parts mmt files
========================

.. autofunction:: parse_model

.. autofunction:: parse_protocol

Parsing expressions
===================

.. autofunction:: parse_expression

Parsing units
=============

.. autofunction:: parse_unit

Parse errors
============

Errors with the underlying file system (file not found, file corrupt etc) will
result in ordinary Python IO errors. Any other errors occurring during parsing
should be of the type :class:`ParseError`.

.. autofunction:: format_parse_error

Loading and saving states
=========================

.. autofunction:: load_state

.. autofunction:: load_state_bin

.. autofunction:: save_state

.. autofunction:: save_state_bin

.. autofunction:: parse_state

A note about the format
=======================

The ``mmt`` format consists of several sections (each with their own syntax)
stored sequentially in a single, string-based format. In theory, this means
``mmt`` files containing syntax errors cannot be reliably separated into parts.
For example if a string isn't terminated in one section, it is impossible to
tell if a subsequent section header indicates a new section or is part of the
string.

These problems could be avoided in a more complicated format, for example a zip
file containing separate files for each section. However, using a plain-text
format makes ``mmt`` files human readable, loadable in any text editor and
directly suitable for storage in versioning systems.
