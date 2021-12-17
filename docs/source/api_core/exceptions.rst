.. _api/exceptions:

**********
Exceptions
**********

.. currentmodule:: myokit

Myokit tries to raise errors in a sensible manner. The following classes are
used:

Base classes
============

.. autoclass:: MyokitError

.. autoclass:: IntegrityError

Inheriting classes
==================

.. autoclass:: CompilationError

.. autoclass:: CyclicalDependencyError

.. autoclass:: DataBlockReadError

.. autoclass:: DataLogReadError

.. autoclass:: DuplicateName

.. autoclass:: DuplicateFunctionName

.. autoclass:: DuplicateFunctionArgument

.. autoclass:: ExportError

.. autoclass:: FindNanError

.. autoclass:: GenerationError

.. autoclass:: IllegalAliasError

.. autoclass:: IllegalReferenceError

.. autoclass:: ImportError

.. autoclass:: IncompatibleModelError

.. autoclass:: IncompatibleUnitError

.. autoclass:: InvalidBindingError

.. autoclass:: InvalidDataLogError

.. autoclass:: InvalidFunction

.. autoclass:: InvalidLabelError

.. autoclass:: InvalidMetaDataNameError

.. autoclass:: InvalidNameError

.. autoclass:: MissingRhsError

.. autoclass:: MissingTimeVariableError

.. autoclass:: NonLiteralValueError

.. autoclass:: NumericalError

.. autoclass:: ParseError

.. autoclass:: ProtocolEventError

.. autoclass:: ProtocolParseError

.. autoclass:: SectionNotFoundError

.. autoclass:: SimulationError

.. autoclass:: SimulationCancelledError

.. autoclass:: SimultaneousProtocolEventError

.. autoclass:: UnresolvedReferenceError

.. autoclass:: UnusedVariableError

.. autoclass:: VariableMappingError

