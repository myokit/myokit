.. _api:

***********
API :: Core
***********

.. currentmodule:: myokit

The heart of Myokit's API has the following components:

- The :class:`Model`-:class:`Component`-:class:`Variable` classes that define
  model structure.
- The :class:`Expression <myokit.Expression>` classes that make up Myokit
  expressions.
- A :class:`Protocol` class that defines a pacing protocol (the input, or
  driver to the system).
- A :class:`Simulation` class containing both a model and a protocol that can
  be run using Myokit's sundials backend or exported to other formats.

These classes define the objects used by Myokit to represent its structures
in memory. To store them on disk, Myokit contains

- A set of parsing functions, accessible through such functions as
  :func:`myokit.load()` and :func:`myokit.parse_expression()`.
- A set of output functions such as :func:`myokit.save()` and
  :func:`myokit.save_state()`.

To produce fast low-level simulation code and export models to other formats,
myokit contains a :class:`tiny templating engine <myokit.pype.TemplateEngine>`
and the infrastructure to create :class:`Exporters <myokit.formats.Exporter>`.
Finally, to load models or protocols from other languages, Myokit has a small
number of :class:`Importers <myokit.formats.Importer>`.

The remaining parts of the API can be found in the :ref:`library <api/lib>`
section of the documentation.


..  toctree::
    :hidden:

    Model
    Component
    Variable
    expressions
    equations
    units
    io
    misc
    settings
    exceptions
