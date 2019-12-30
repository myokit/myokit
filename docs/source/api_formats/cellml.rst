.. _formats/cellml:

******
CellML
******

An interface for importing CellML 1.0 and up is provided, as well as an export
to CellML 1.0.
For further CellML functions, see :ref:`CellML API <formats/cellml_v1>`

Importing
=========

Myokit can import most models listed in the CellML electrophysiology
repository.
(Although take care, some of the CellML versions of models are known issues.
This is usually mentioned in their documentation).

Adapting an embedded stimulus current
-------------------------------------

Most CellML models contain a hard-coded stimulus current.
Myokit will try to detect these stimulus currents and replace them by an
appropriate :class:`myokit.Protocol`.
However, if this fails, the stimulus will need to be converted by hand, which
is described below.

In the following example we show how to import the Beeler-Reuter model from
the CellML database.

    1. Find and download the model file (``beeler_reuter_1977.cellml``).
    2. Open the GUI and select ``Convert > Import model from CellML``.
    3. Have a look at the imported code. Apart from the messy representation
       of the meta-data, everything should be in order.
    4. Run the embedded script or explorer. You should see something like this:

    .. figure:: ../_static/br_cellml_bad_thumb.png
        :target: ../_static/br_cellml_bad.png
        :align: center

    5. To fix this, scroll down to the stimulus section. It should look like
       this::

        [stimulus_protocol]
        Istim = piecewise(engine.time >= IstimStart and engine.time <= ...
            in [A/m^2]
        IstimStart = 10 [ms]
        IstimEnd = 50000 [ms]
        IstimAmplitude = 0.5 [A/m^2]
        IstimPeriod = 1000 [ms]
        IstimPulseDuration = 1 [ms]

       Replace the ``piecewise`` statement with a formulation using the
       external ``pace`` variable::

        [stimulus_protocol]
        IstimAmplitude = 0.5 [A/m^2]
        level = 0 bind pace
        Istim = level * IstimAmplitude [A/m^2]

       Next, use the information from ``IstimStart``, ``IStimPeriod`` and
       ``IStimPulseDuration`` to update the pacing protocol on the next tab::

        # Level  Start    Length   Period   Multiplier
        1.0      10.0     1.0      1000.0   0

    6. Validate the model and try again. Now that the simulation engine knows
       where the discontinuities are, you should get the expected result:

    .. figure:: ../_static/br_cellml_good_thumb.png
        :target: ../_static/br_cellml_good.png
        :align: center

    The same procedure can be followed for any other valid model in the
    database.


Exporting
=========
Myokit provides an export to CellML 1.0.
Since Myokit separates the model from the pacing protocol, but most CellML
based tools do not expect this, Myokit has an option to embed a hardcoded
stimulus protocol in exported CellML files.
This is enabled by default but can be disabled when exporting models via the
API (see :class:`CellMLExporter <myokit.formats.cellml.CellMLExporter>`).

Note that the protocol has a default duration of 2ms, making it suitable for
most older models but not the more modern ones.
For models that require shorter stimulus currents, adapt the CellML model by
searching for a component named "stimulus" (or "stimulus\_2" if that name was
already taken) and changing the "duration" variable.


Imports, exporters, and expression writers
==========================================

.. module:: myokit.formats.cellml

.. autofunction:: importers

.. autoclass:: CellMLImporter
    :inherited-members:

.. autoclass:: CellMLImporterError

.. autofunction:: exporters

.. autoclass:: CellMLExporter
    :inherited-members:

.. autofunction:: ewriters

.. autoclass:: CellMLExpressionWriter
    :inherited-members:

