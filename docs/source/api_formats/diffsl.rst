.. _formats/diffsl:

******
DiffSL
******

Myokit provides export of models to the `DiffSL language <https://martinjrobins.github.io/diffsl/>`_.

**Model-only export** produces a standard DiffSL ODE in ``u_i``/``F_i``/``out_i`` form.

**Protocol export** generates a *hybrid* ODE model using DiffSL's ``N`` and
``stop`` constructs, see the `DiffSL hybrid ODE documentation <https://martinjrobins.github.io/diffsl/odes.html>`_.

The ``protocol`` argument can be either a single :class:`myokit.Protocol`
for the ``pace`` binding or a ``dict`` mapping binding names to protocols.
Protocol entries for bindings that are not present in the model are ignored.
When multiple bindings are provided, Myokit expands them to a shared
segmented timeline with one emitted ``*_i`` schedule block tensor per binding
(i.e. containing the dosing levels) and one shared ``stop_i`` block for the
transition times between the scheduled blocks.

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
