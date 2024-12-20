.. _formats/sbml:

.. module:: myokit.formats.sbml

****
SBML
****

Methods are provided to import model definitions from SBML, based on the level
3 version 2 specification.
Older versions (level 2 and up) are partially supported, but may raise
warnings.
Export of models is provided (level 3 version 2), but note that all variables
will be represented as parameters (no compartments, species, or reactions) are
created.

For further SBML functions, see :ref:`SBML API <formats/sbml_api>`.

Importing
=========

The standard API for importing is provided:

.. autofunction:: importers

.. autoclass:: SBMLImporter

Exporting
=========

The standard API for exporting is provided:

.. autofunction:: exporters

.. autoclass:: SBMLExporter
