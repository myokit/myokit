.. _formats/diffsl:

******
DiffSL
******

Myokit provides export of models to the `DiffSL language <https://martinjrobins.github.io/diffsl/>`_.

**Model-only export** produces a standard DiffSL ODE in ``u_i``/``F_i``/``out_i`` form.

**Protocol export** generates a *hybrid* ODE model using DiffSL's ``N`` and
``stop`` constructs, matching the dosing-schedule pattern
described in the `DiffSL hybrid ODE documentation <https://martinjrobins.github.io/diffsl/odes.html>`_.

Protocol events are expanded to an explicit list of one-off boundary transitions:

* A ``pace_i`` vector holds the pace level for each model phase indexed by ``N``.
* A ``stop_i`` vector encodes each transition time; stop element ``k`` crosses
  zero at time ``t_{k+1}``, triggering a solver stop and setting ``N = k``.
State variables are preserved by default at transitions; pace changes are
communicated through the updated ``N``\→``pace_i[N]`` lookup.

If a protocol is provided, a ``final_time`` must be passed to
:meth:`DiffSLExporter.model` so expansion is always finite.

Exporters and expression writers
================================

.. module:: myokit.formats.diffsl

.. autofunction:: exporters

.. autoclass:: DiffSLExporter
    :inherited-members:

.. autofunction:: ewriters

.. autoclass:: DiffSLExpressionWriter
    :inherited-members:

