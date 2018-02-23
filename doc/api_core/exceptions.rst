.. _api/exceptions:

**********
Exceptions
**********

.. module:: myokit

Myokit tries to raise errors in a sensible manner. The following classes are
used.

Base classes
============

.. autoclass:: MyokitError
   :members:

.. autoclass:: IntegrityError
   :members:

Inheriting classes
==================

.. autoclass:: CompilationError
    :members:

.. autoclass:: CyclicalDependencyError
    :members:

.. autoclass:: DataBlockReadError
    :members:

.. autoclass:: DataLogReadError
    :members:

.. autoclass:: DuplicateName
    :members:

.. autoclass:: DuplicateFunctionName
    :members:

.. autoclass:: DuplicateFunctionArgument
    :members:

.. autoclass:: ExportError
    :members:

.. autoclass:: FindNanError
    :members:

.. autoclass:: GenerationError
    :members:

.. autoclass:: IllegalAliasError
    :members:

.. autoclass:: IllegalReferenceError
    :members:

.. autoclass:: ImportError
    :members:

.. autoclass:: IncompatibleModelError
    :members:

.. autoclass:: IncompatibleUnitError
    :members:

.. autoclass:: InvalidBindingError
    :members:

.. autoclass:: InvalidDataLogError
    :members:

.. autoclass:: InvalidFunction
    :members:

.. autoclass:: InvalidLabelError
    :members:

.. autoclass:: InvalidMetaDataNameError
    :members:

.. autoclass:: InvalidNameError
    :members:

.. autoclass:: MissingRhsError
    :members:

.. autoclass:: MissingTimeVariableError
    :members:

.. autoclass:: NonLiteralValueError
    :members:

.. autoclass:: NumericalError
    :members:

.. autoclass:: ParseError
    :members:

.. autoclass:: ProtocolEventError
    :members:

.. autoclass:: ProtocolParseError
    :members:

.. autoclass:: SectionNotFoundError
    :members:
    
.. autoclass:: SimulationError
    :members:

.. autoclass:: SimulationCancelledError
    :members:

.. autoclass:: SimultaneousProtocolEventError
    :members:

.. autoclass:: UnresolvedReferenceError
    :members:

.. autoclass:: UnusedVariableError
    :members:


