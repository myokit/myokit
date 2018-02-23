.. _api/misc:

*************
Miscellaneous
*************

.. module:: myokit

Model comparison
================

.. autoclass:: ModelComparison
    :members:

.. _api/modelcomparison:


Benchmarking
============

.. autoclass:: Benchmarker
    :members:

.. _api/logging:


Logging
=======
A number of Myokit functions (for example importers and exporters) maintain a
log of their actions using the TextLogger class described below. If anything
goes wrong, these logs should contain a more detailed error message than a
simple exception.

.. autoclass:: TextLogger
    :members:

State i/o
=========

.. autofunction:: load_state

.. autofunction:: load_state_bin

.. autofunction:: parse_state

.. autofunction:: save_state

.. autofunction:: save_state_bin

String functions
================

.. autofunction:: date

.. autofunction:: format_float_dict

.. autofunction:: format_path

.. autofunction:: lvsd

.. autofunction:: strfloat

.. autofunction:: time

.. autofunction:: version

Other functions
===============

.. autofunction:: default_protocol

.. autofunction:: default_script

.. autofunction:: pack_snapshot

.. autofunction:: natural_sort_key

.. autofunction:: numpywriter

.. autofunction:: pywriter

.. autofunction:: run

.. autofunction:: strip_expression_units
