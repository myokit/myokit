.. _formats/sbml:

****
SBML
****

Import of model definitions is provided from SBML level 3 version 2 files.
Older versions (including level 2) are also partially supported, although this
will raise warnings.

Not all SBML features are supported, as documented in the :class:`SBMLParser`.

API
===

The standard API for importing is provided:

.. module:: myokit.formats.sbml

.. autofunction:: importers

.. autoclass:: SBMLImporter
    :inherited-members:

Parsing
=======

.. autoclass:: SBMLParser

.. autoclass:: SBMLParsingError

