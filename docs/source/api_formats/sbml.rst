.. _formats/sbml:

****
SBML
****

Import of model definitions is provided from SBML level 3 version 2 files.

Limitations:

  - The function definition feature of SBML is not supported.
  - The algebraic rule feature of SBML is not supported.
  - The constraint feature of SBML is not supported.
  - The events feature of SBML is not supported. External stimuli can be added by hand with :class:`myokit.Protocol`.

API
===

The standard API for importing is provided:

.. module:: myokit.formats.sbml

.. autofunction:: importers

.. autoclass:: SBMLImporter
    :inherited-members:

.. autoclass:: SBMLError

Parsing
=======

.. autoclass:: SBMLParser
    :inherited-members:

