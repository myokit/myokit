.. _formats/cellml_v1:

.. module:: myokit.formats.cellml.v1

**************
CellML 1.0 API
**************

In addition to the :ref:`CellML importers and exporters <formats/cellml>`,
Myokit contains an API to represent CellML models, along with methods to read
and write CellML 1.0 and 1.1 documents.
These methods are used under the hood by the importers and exporters.

In most cases, it's easier to avoid these methods and use the
:ref:`CellML Importer and Exporter <formats/cellml>` instead.

CellML Model API
================

.. autofunction:: is_valid_identifier

.. autoclass:: Model

.. autoclass:: Component

.. autoclass:: Variable

.. autoclass:: Units

.. autoclass:: AnnotatableElement

.. autoclass:: CellMLError

.. autoclass:: UnitsError

.. autoclass:: UnsupportedBaseUnitsError

.. autoclass:: UnsupportedUnitOffsetError

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

