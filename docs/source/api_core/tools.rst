.. _api/tools:

*****
Tools
*****

Myokit contains a module ``myokit.tools`` with functions and classes that are
used throughout Myokit, but are not particularly Myokit-specific.
This module is imported automatically when ``import myokit`` is run.

.. currentmodule:: myokit.tools

Benchmarking
============

.. autoclass:: Benchmarker

Capturing printed output
========================

.. autoclass:: capture

File system
===========

.. autofunction:: format_path

.. autofunction:: rmtree

String comparison
=================

.. autofunction:: lvsd

.. autofunction:: natural_sort_key

Deprecated functions
====================
Some of the functions in ``tools`` have deprecated aliases, that will be
removed in future Myokit releases.

.. currentmodule:: myokit

.. autoclass:: Benchmarker

.. autofunction:: format_float_dict

.. autofunction:: format_path

.. autofunction:: strfloat

