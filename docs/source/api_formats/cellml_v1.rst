.. _formats/cellml_api:

.. module:: myokit.formats.cellml.v1

**************
CellML 1.0 API
**************

In addition to the :ref:`CellML importers and exporters <formats/cellml>`,
Myokit contains an API to represent CellML models, along with methods to read
and write CellML 1.0 and 1.1 documents.
These are used under the hood by the importers and exporters.

CellML Model API
================

.. autofunction:: is_valid_identifier

.. autoclass:: Model

.. autoclass:: Component

.. autoclass:: Variable

.. autoclass:: Units

.. autoclass:: AnnotatableElement

.. autoclass:: CellMLError

.. autofunction:: clean_identifier

.. autofunction:: create_unit_name

CellML Parsing
==============

.. autofunction:: parse_file

.. autofunction:: parse_string

.. autoclass:: CellMLParser

.. autoclass:: CellMLParsingError

CellML Writing
==============

.. autofunction:: write_file

.. autofunction:: write_string

.. autoclass:: CellMLWriter

