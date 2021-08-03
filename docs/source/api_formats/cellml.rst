.. _formats/cellml:

******
CellML
******

Methods to import and export CellML 1.0, 1.1, and 2.0 are provided.
For further CellML functions, see :ref:`CellML 1 API <formats/cellml_v1>` and
:ref:`CellML 2 API <formats/cellml_v2>`.

Importing
=========

Myokit can import most models listed in the CellML electrophysiology
repository.
(Although take care, some of the CellML versions of models are known to
have issues. This is usually mentioned in their documentation).

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
    3. Have a look at the imported code. You should find a stimulus current
       implemented as ``pace * IstimAmplitude``. This has automatically been
       added when you imported the model.
    4. If you run the code, you should see an action potential!

Now let's import the model in code, without automatic conversion:

    1. In a script, load the Myokit formats module (``import myokit.formats``)
       and create a CellMLImporter: ``i = myokit.formats.importer('cellml')``.
    2. Import the model, using ``i.model('beeler_reuter_1977.cellml')``.
    3. Have a look at the generated code. You should see the hardcoded stimulus
       that was present in the CellML file.
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
    An automated version of this procedure is implemented as
    :meth:`myokit.lib.guess.remove_embedded_protocol()`.


Exporting
=========
Myokit provides an export to CellML 1.0, 1.1, and 2.0.

Since Myokit separates the model from the pacing protocol, but most CellML
based tools do not expect this, Myokit has an option to embed a hardcoded
stimulus protocol in exported CellML files.
This can be done by passing a myokit Protocol to the exporter along with
the model to export.


Imports, exporters, and expression writers
==========================================

.. module:: myokit.formats.cellml

.. autofunction:: importers

.. autoclass:: CellMLImporter

.. autoclass:: CellMLImporterError

.. autofunction:: exporters

.. autoclass:: CellMLExporter
    :inherited-members:

.. autoclass:: CellML1Exporter
    :inherited-members:

.. autoclass:: CellML2Exporter
    :inherited-members:

.. autofunction:: ewriters

.. autoclass:: CellMLExpressionWriter
    :inherited-members:

