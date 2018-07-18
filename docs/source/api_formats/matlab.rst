.. _formats/matlab:

*************
Matlab/Octave
*************

Export to a matlab/octave compatible syntax is provided for model definitions
only. An example pacing method is provided that will need to be adapted for
each model.

To run the exported code in octave, the package odepkg_ is required. This
dependency can be dropped if a different set of solvers is used.

.. _odepkg: http://octave.sourceforge.net/odepkg/

Limitations:

  - The pacing mechanism is not exported

API
===

The standard exporting API is provided:

.. module:: myokit.formats.matlab

.. autofunction:: exporters

.. autoclass:: MatlabExporter

.. autofunction:: ewriters

.. autoclass:: MatlabExpressionWriter
    :inherited-members:
