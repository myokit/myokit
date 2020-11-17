.. _formats/sbml:

.. module:: myokit.formats.sbml

****
SBML
****

Methods are provided to import model definitions from SBML, based on the level
3 version 2 specification.
Older versions (level 2 and up) are partially supported, but may raise
warnings.
For further SBML functions, see :ref:`SBML API <formats/sbml_api>`.

Importing
=========

The standard API for importing is provided:

.. autofunction:: importers

.. autoclass:: SBMLImporter

