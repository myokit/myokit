.. _formats/diffsl:

******
DiffSL
******

Myokit provides export of models to the `DiffSL language <https://martinjrobins.github.io/diffsl/>`_.

**Model-only export** produces a standard DiffSL ODE in ``u_i``/``F_i``/``out_i`` form.

**Protocol export** generates a *hybrid* ODE model using DiffSL's ``N`` and
``stop`` constructs, see the `DiffSL hybrid ODE documentation <https://martinjrobins.github.io/diffsl/odes.html>`_.

Periodic protocol events are expanded to an explicit list of one-off dose transitions. If a protocol is provided, a ``final_time`` must be passed to
:meth:`DiffSLExporter.model` so this expansion is always finite.

Exporters and expression writers
================================

.. module:: myokit.formats.diffsl

.. autofunction:: exporters

.. autoclass:: DiffSLExporter
    :inherited-members:

.. autofunction:: ewriters

.. autoclass:: DiffSLExpressionWriter
    :inherited-members:

