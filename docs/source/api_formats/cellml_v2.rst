.. _formats/cellml_v2:

.. module:: myokit.formats.cellml.v2

**************
CellML 2.0 API
**************

In addition to the :ref:`CellML importers and exporters <formats/cellml>`,
Myokit contains an API to represent CellML models, along with methods to read
and write CellML 2.0 documents.
These methods are used under the hood by the importers and exporters.

In most cases, it's easier to avoid these methods and use the
:ref:`CellML Importer and Exporter <formats/cellml>` instead.

CellML Model API
================

.. autofunction:: is_identifier

.. autofunction:: is_integer_string

.. autofunction:: is_basic_real_number_string

.. autofunction:: is_real_number_string

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

