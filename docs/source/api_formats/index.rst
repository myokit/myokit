.. _api/formats:

**************
API :: Formats
**************

.. module:: myokit.formats

*This page is about importing from and exporting to formats other than*
``mmt``. *If you are interested in the* ``mmt`` *format, please look at the
section* :ref:`api/io`.

One of the main goals of myokit is to provide :ref:`export <api/export>` of
Simulations to other formats (for example C or matlab). To provide a uniform
interface to these functions the :class:`Exporter` class is defined. Import
from other formats is provided through the :class:`Importer` interface.

Exporters to exchange or presentation formats will typically export a bare
model definition, while exporters to programming languages mostly create a full
Simulation including pacing, a simulation engine and even some post processing.

The goal of an :class:`Importer` is to produce a ``(model, protocol, script)``
tuple containing the three main parts of an ``mmt`` file. However, most
importers will only provide a model definition so the remaining entries in the
tuple will be ``None``.

The methods used to import and export programmatically are described below, and
and some example code is given.

The following formats are currently supported:

..  toctree::
    :titlesonly:
    :maxdepth: 1
    :glob:

    ./*

Example
=======
To find out which kinds of import/export are available, the methods
:func:`exporters()` and :func:`importers()` are defined. These
functions return a list of names that can be passed to
:func:`exporter()` or :func:`importer` to obtain the class name
of the requested im- or exporter. This is returned as a ``type`` object, from
which instances can then be constructed::

    import myokit
    from myokit import formats

    # Load a (model, protocol, script) tuple
    m, p, s = myokit.load('example.mmt')

    # Create a simulation
    s = myokit.Simulation(m, p)

    # Create an Ansi-C exporter
    e = formats.exporter('ansic')

    # Get some info about this exporter
    print e.info()

    # Export to the directory /home/michael/test
    # If this directory does not exist, the exporter will attempt to create it.
    e.export_simulation(s, '/home/michael/test')



.. _api/import:

Importing
=========

.. autofunction:: importer

.. autofunction:: importers

.. autoclass:: Importer
    :private-members:

.. _api/export:

Exporting
=========

.. autofunction:: exporter

.. autofunction:: exporters

.. autoclass:: Exporter
    :private-members:

.. autoclass:: TemplatedRunnableExporter
    :private-members:

.. _api/expression_writers:

Expression writers
==================

A number of export classes use :class:`ExpressionWriter` objects to convert
myokit expressions to string representations in the appropriate language. The
base class for expression writers is described below:

.. autofunction:: ewriter

.. autofunction:: ewriters

.. autoclass:: ExpressionWriter
    :private-members:

Registering external formats
============================

The importers, exporters, and expression writers that are packed with Myokit
are automatically detected at start-up. To register classes defined outside of
the ``myokit`` module, use the functions below. After registering, you can
obtain e.g. an :class:`Exporter` via
``myokit.formats.exporter(my_external_exporter)``.

.. autofunction:: register_external_importer

.. autofunction:: register_external_exporter

.. autofunction:: register_external_ewriter

Default expression writers
==========================

Finally, Myokit contains two default expression writers, which are used
internally to write expressions in Python format with or without NumPy support.

.. currentmodule:: myokit

.. autofunction:: python_writer

.. autofunction:: numpy_writer

