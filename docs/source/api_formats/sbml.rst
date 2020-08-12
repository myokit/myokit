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

SBML Model API
==============

.. autoclass:: Compartment
    :inherited-members:

.. autoclass:: Model

.. autoclass:: ModifierSpeciesReference
    :inherited-members:

.. autoclass:: Parameter
    :inherited-members:

.. autoclass:: Quantity
    :inherited-members:

.. autoclass:: Reaction

.. autoclass:: SBMLError
    :inherited-members:

.. autoclass:: Species
    :inherited-members:

.. autoclass:: SpeciesReference
    :inherited-members:

