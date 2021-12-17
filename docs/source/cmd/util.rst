*********
Utilities
*********

The command-line tools listed on this page use Myokit to perform various tasks
such as model import or export and model comparison.

- :ref:`compare <cmd/compare>`
- :ref:`debug <cmd/debug>`
- :ref:`export <cmd/export>`
- :ref:`eval <cmd/eval>`
- :ref:`import <cmd/import>`
- :ref:`run <cmd/run>`
- :ref:`step <cmd/step>`
- :ref:`video <cmd/video>`


.. _cmd/compare:

===========
``compare``
===========

Compares two Myokit models, for example::

    $ myokit compare model1.mmt model2.mmt

Example output::

    Comparing:
      [1] decker-2009
      [2] decker-2009
    [1] Missing Variable <calcium.gamma>
    [x] Mismatched RHS <stimulus.amplitude>
    Done
      2 differences found

For the full syntax, see::

    $ myokit compare --help


.. _cmd/debug:

=========
``debug``
=========

Displays the calculation of a single variable from a model.

Example::

    $ myokit debug example.mmt v
    Variable not found, assuming "membrane.V"
    Showing membrane.V  (State variable)
    ------------------------------------------------------------
    unit: mV
    desc: The membrane potential
    ------------------------------------------------------------
    Initial value = -84.5286
    ------------------------------------------------------------
    ica.ICa         = -5.69307557845840514e-05
    membrane.i_stim = 0.0
    ib.Ib           = -9.66863706000000045e-01
    ikp.IKp         = 1.27313823914652343e-08
    ik1.IK1         = 1.03172820596243020e+00
    ik.IK           = -7.99485510998167170e-03
    ina.INa         = -1.19264480675140328e-05
    ------------------------------------------------------------
    dot(membrane.V) = membrane.i_stim - (ina.INa + ik.IK + ib.Ib + ikp.IKp
                        + ik1.IK1 + ica.ICa)
                    = -5.68008003799787276e-02

For the full syntax, see::

    $ myokit debug --help


.. _cmd/export:

==========
``export``
==========

Exports an ``mmt`` file using any of the available exporters.

Syntax::

    $ myokit export <exporter_name> <source_file> <output_directory>

For example, to convert a model to cellml::

    $ myokit export cellml example.mmt example.cellml

Or to create runnable code in the directory ``example_in_c``::

    $ myokit export ansic example.mmt example_in_c

For the full syntax, see::

    $ myokit export --help


.. _cmd/eval:

========
``eval``
========

Evaluates an expression.

Example::

    $ myokit eval "100 / 2 / 2"
    100 / 2 / 2 = 25.0

For the full syntax, see::

    $ myokit eval --help


.. _cmd/import:

==========
``import``
==========

Imports a model definition or protocol using any of the available importers.

Syntax::

    $ myokit import <format> <source_file> -o <output_file>

If no output file is specified, the generated mmt file is simply printed to
the screen.

Examples::

    $ myokit import cellml example.cellml

    $ myokit import cellml example.cellml test.mmt

For the full syntax, see::

    $ myokit import --help


.. _cmd/run:

=======
``run``
=======

Loads an ``mmt`` file and runs the embedded script. If no script is available,
a default script is run using the file's model and/or protocol.

Typical use::

    $ myokit run lr1991.mmt

For the full syntax, see::

    $ myokit run --help


.. _cmd/step:

========
``step``
========

Loads a model  and evaluates the derivatives of the state variables at the
initial time::

    $ myokit step example.mmt
    ---------------------------------------------------------------------------
    Single test step
    Reading model from example.mmt...
    Model LR1991 read successfully
    Evaluating state vector derivatives...
    ---------------------------------------------------------------------------
    Name        Initial value             Derivative at t=0
    ---------------------------------------------------------------------------
    membrane.V  -8.45285999999999973e+01  -5.68008003799787276e-02
    ina.m        1.69999999999999991e-03  -4.94961486033834719e-03
    ina.h        9.83199999999999963e-01   9.02025299127830887e-06
    ina.j        9.95484000000000036e-01  -3.70409866928434243e-04
    ica.d        3.00000000000000008e-06   3.68067721821794798e-04
    ica.f        1.00000000000000000e+00  -3.55010150519739432e-07
    ik.x         5.70000000000000021e-03  -2.04613933160084307e-07
    ica.Ca_i     2.00000000000000010e-04  -6.99430692442154227e-06
    ---------------------------------------------------------------------------

The results can be compared to a file containing reference values using
::

    $ myokit step example.mmt -ref ref_step.txt

To test with different initial values, another file can be included::

    $ myokit step example.mmt -ref ref_step.txt -ini ref_init.txt

For the full syntax, see::

    $ myokit step --help


.. _cmd/video:

=========
``video``
=========

If you have ``moviepy`` (http://zulko.github.io/moviepy/) installed, this
script can be used to generate movies from
:class:`DataBlock1d <myokit.DataBlock1d>` or
:class:`DataBlock2d<myokit.DataBlock2d>` files.

The syntax is

    $ myokit video <inputfile> <variable> -dst <outputfile>

Here, `<inputfile>` should be the name of a DataBlock1d or 2d file. The
variable to visualized should be given as `<variable>` and the output file
should be given as `<outputfile>`. Supported outut formats are `flv`, `gif`,
`mp4`, `mpeg` and `wmv`.

Example::

    $ myokit video results.zip membrane.V -dst movie.mp4

For the full syntax, use::

    $ myokit video --help

