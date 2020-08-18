.. _formats/sbml_api:

.. currentmodule:: myokit.formats.sbml

********
SBML API
********

In addition to the :ref:`SBML importer <formats/sbml>`, Myokit contains an API
to represent SBML models, along with methods to read SBML documents.
These methods are used under the hood by the importer.

In most cases, it's easier to avoid these methods and use the
:ref:`SBML Importer <formats/sbml>` instead.


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


SBML Parsing
============

.. autoclass:: SBMLParser

.. autoclass:: SBMLParsingError

