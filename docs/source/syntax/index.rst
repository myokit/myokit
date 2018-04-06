.. _syntax:

***************
mmt File syntax
***************

..  toctree::
    :hidden:

    model
    protocol
    script

Each Myokit ``.mmt`` file contains at least one of the following segments:

A model definition, indicated by ``[[model]]``
    This describes a set of model equations using the syntax explained below.
    This contains all model equations, units, meta-information and a set of
    realistic initial values. The syntax for model definitions is explained
    :ref:`here <syntax/model>`.
A pacing protocol, indicated by ``[[protocol]]``
    This describes pacing protocol used to drive the model. The syntax for
    describing protocols is described :ref:`here <syntax/protocol>`.
An embedded script, indicated by ``[[script]]``
    This is a plain python script that sets up a simulation, runs it and then
    processes the results. This includes, but isn't limited to, drawing graphs
    of the logged variables.

The order of these segments is fixed: not every segment needs to appear in an
``mmt`` file, but a ``[[script]]`` header should never come before a 
``[[protocol]]`` one.

When 'executing' an mmt file, the model and protocol are read and parsed. The
magic methods ``get_model`` and ``get_protocol()`` allow the embedded python
script to access these objects and create a simulation. This way, a relevant
view of the simulation data can be provided along with the model definition and
protocol.

The goal of this setup is to provide a complete experiment in a single,
human-readable file. The format is deliberately simple: all ``.mmt`` files are
plain text and so can be edited by people without Myokit software, maintained
in versioning systems and pass through email security without problems.

It is possible to parse only part of an ``.mmt`` file, for example to extract a
model definition, protocol or plot script an import it into another file.
