.. _formats/cellml:

******
CellML
******

An interface for importing CellML 1.0 and up is provided, as well as an export
to CellML 1.0.

Importing
=========

Myokit can import most models listed in the CellML electrophysiology
repository.

However, most CellML models contain a hard-coded stimulus current which will
cause problems for the solver. These must rewritten manually to use Myokit's
pacing system.

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
        
Model quality
-------------
Please keep in mind that the quality of available CellML models may vary. Some
models are incomplete, contain errors or are not written in valid CellML. In
addition, some models contain experimental features such as random variation
or partial differential equations. These are not currently part of the CellML
standard and are not supported by Myokit.

Limitations
-----------
CellML is built with a larger scope in mind than Myokit and includes a few
oddities such as ``<arccsch>``, which were included " because they are
reasonably straightforward to translate to computer code" (CellML 1.0
specification). Below is a list of the CellML features Myokit does not support.

**CellML 1.0**

Differential algebraic equations (DAEs)
    Myokit has no support for DAEs, so model that contain them cannot be
    imported. However, these models can manually be rewritten to a form
    supported by Myokit.
``<factorial>``
    The factorial operation is not common in cell models or in programming
    math libraries (C for example, does not include it). In addition, note that
    ``13! > 2^32`` and ``21! > 2^64`` so that there is only a very small
    subset of factorials that we can easily compute. At the time of writing,
    July 2015, none of the *cardiac* models in the CellML electrophysiology
    repository use this feature.
``<reaction>``
    The ``<reaction>`` element and its children are used to specify biochemical
    pathways without an explicit mathematical form. Since there are plenty of
    tools for pathways already, Myokit does not support them. At the time of
    writing, July 2015, none of the models in the CellML electrophysiology
    repository use this feature.
``<semantics>``
    The ``<semantics>`` element and its children can be used to specify both
    a meaningful set of equations and a pretty set of equations. Since Myokit
    has only one way of displaying equations, this is not supported. At the
    time of writing, July 2015, none of the models in the CellML
    electrophysiology repository use this feature.

**CellML 1.1**

``<import>``
    The import element introduced in CellML 1.1 is currently not supported,
    but this may change in the future.

**Optional features**

Unit conversion
    Myokit's CellML import does not perform automatic unit conversion, but it
    will warn if inconsistent units are found.
Scripting
    CellML scripting is not supported by Myokit.

Exporting
=========
Myokit provides an export to CellML 1.0. Since Myokit separates the model from
the pacing protocol, but most CellML based tools do not expect this, Myokit has
an option to embed a hardcoded stimulus protocol in exported CellML files.
This is enabled by default but can be disabled when exporting models via the
API (see :class:`CellMLExporter <myokit.formats.cellml.CellMLExporter>`).

Note that the protocol has a default duration of 2ms, making it suitable for
most older models but not the more modern ones. For models that require shorter
stimulus currents, adapt the CellML model by searching for a component named
"stimulus" (or "stimulus\_2" if that name was already taken) and changing the
"duration" variable.

OpenCOR
-------
A few notes about OpenCOR:

1. The OpenCOR manual states that, *"a model that requires a stimulus protocol
   should have the maximum step value of the CVODE solver set to the length of
   the stimulus"*. Since most models have a stimulus protocol you'll usually
   have to set the maximum step size on the "simulation" tab for models to
   work in OpenCOR.
2. OpenCOR has been known to complain about nested piecewise functions. If
   these are present it seems to run anyway.


API
===
The standard interfaces for importing and exporting are provided:

.. module:: myokit.formats.cellml

.. autofunction:: importers

.. autoclass:: CellMLImporter
    :members:
    :inherited-members:

.. autofunction:: exporters

.. autoclass:: CellMLExporter
    :members:
    :inherited-members:

.. autofunction:: ewriters

.. autoclass:: CellMLExpressionWriter
    :members:
    :inherited-members:
    
.. autoclass:: CellMLError
    :members:
