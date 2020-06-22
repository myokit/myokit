.. _api/myokit.Model:

*********
``Model``
*********

.. currentmodule:: myokit

The central object in Myokit is the :class:`Model`. In most scenario's, models
are created by :ref:`parsing <api/io>` a file in
:ref:`mmt syntax <syntax>`. Once parsed, a model can be
:meth:`validated <Model.validate>` to ensure its integrity. In models with
unsound semantics (for example a cyclical reference between variables) the
``validate()`` method will raise an :class:`IntegrityError`.

For models with a limited number of state variables, validation is fast. In
these cases, the ``validate()`` method is run after parsing as an additional
check. For larger models, validation is costly and avoided until a simulation
is run or another analysis method is used.

Once created and validated, a model can be asked to
:meth:`compute the solvable order of its equations <Model.solvable_order>`
which can then be used by an exporter to generate runnable simulation or
analysis code.


``myokit.Model``
================

.. autoclass:: Model
   :inherited-members:

``myokit.ModelPart``
====================

.. autoclass:: ModelPart

Name validation
===============

.. autofunction:: check_name

