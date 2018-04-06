.. _formats/sbml:

****
SBML
****

Import of model definitions is provided from SBML models using only parameters,
rates and units. Species-compartment type models can not be imported.

Limitations:

  - The Species-Compartment features of SBML are not supported.
  - No mechanism to import stimulus currents is implemented. This means models
    will need to be adapted by hand to run in myokit.

API
===

The standard API for importing is provided:

.. module:: myokit.formats.sbml

.. autofunction:: importers

.. autoclass:: SBMLImporter

.. autoclass:: SBMLError

