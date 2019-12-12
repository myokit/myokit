.. _formats/cellml_api:

**********
CellML API
**********

In addition to the :ref:`CellML importers and exporters <formats/cellml>`,
Myokit contains a CellML Model API to represent CellML models, and a parser to
parse CellML documents.
These are used under the hood by the importers and exporters.

CellML Model API
================

.. module:: myokit.formats.cellml.cellml_1

.. autofunction:: is_valid_identifier

.. autoclass:: Model

.. autoclass:: Component

.. autoclass:: Variable

.. autoclass:: Units

.. autoclass:: AnnotatableElement

.. autoclass:: CellMLError

CellML Parsing
==============

.. module:: myokit.formats.cellml.parser_1

.. autofunction:: parse_file

.. autofunction:: parse_string

.. autofunction:: split

.. autoclass:: CellMLParser

.. autoclass:: CellMLParsingError

