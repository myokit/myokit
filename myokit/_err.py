#
# Non-standard exceptions raised by myokit.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Base classes
#
#
class MyokitError(Exception):
    """
    Base class for all exceptions specific to Myokit.

    Note that myokit classes and functions may raise any type of exception, for
    example a :class:``KeyError`` or a :class:`ValueError`. Only new classes of
    exception *defined* by Myokit will extend this base class.

    *Extends:* ``Exception``
    """
    def __init__(self, message):
        super(MyokitError, self).__init__(message)


class IntegrityError(MyokitError):
    """
    Raised if an integrity error is found in a model.

    The error message is stored in the property ``message``. An optional parser
    token may be obtained with :meth:`token()`.

    *Extends:* :class:`myokit.MyokitError`
    """
    def __init__(self, message, token=None):
        super(IntegrityError, self).__init__(message)
        self._token = token

    def token(self):
        """
        Returns a parser token associated with this error, or ``None`` if no
        such token was given.
        """
        return self._token


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Inheriting classes
#
class CompilationError(MyokitError):
    """
    Raised if an auto-compiling class fails to compile. Catching one of these
    is usually a good excuses to email the developers ;-)

    *Extends:* :class:`myokit.MyokitError`
    """


class CyclicalDependencyError(IntegrityError):
    """
    Raised when an variables depend on each other in a cyclical manner.

    The first argument ``cycle`` must be a sequence containing the
    :class:`Variable` objects in the cycle.

    *Extends:* :class:`myokit.IntegrityError`
    """
    def __init__(self, cycle):
        # Set message
        msg = 'Cyclical reference found: (' + ' > '.join(
            [v.var().qname() for v in cycle]) + ').'
        # Set token: First item in cycle is model's defining lhs
        tok = cycle[0].var()._token
        # Raise
        super(CyclicalDependencyError, self).__init__(msg, tok)


class DataBlockReadError(MyokitError):
    """
    Raised when an error is encountered while reading a
    :class:`myokit.DataBlock1d` or :class:`myokit.DataBlock2d`.

    *Extends:* :class:`myokit.MyokitError`.
    """


class DataLogReadError(MyokitError):
    """
    Raised when an error is encountered while reading a
    :class:`myokit.DataLog`.

    *Extends:* :class:`myokit.MyokitError`.
    """


class DuplicateName(MyokitError):
    """
    Raised when an attempt is made to add a component or variable with a name
    that is already in use within the relevant scope.

    *Extends:* :class:`myokit.MyokitError`.
    """


class DuplicateFunctionName(MyokitError):
    """
    Raised when an attempt is made to add a user function to a model when a
    function with the same name and number of arguments already exists.

    *Extends:* :class:`myokit.MyokitError`.
    """


class DuplicateFunctionArgument(MyokitError):
    """
    Raised when an attempt is made to define a user function with duplicate
    argument names.

    *Extends:* :class:`myokit.MyokitError`.
    """


class ExportError(MyokitError):
    """
    Raised when an export to another format fails.

    *Extends:* :class:`myokit.MyokitError`.
    """


class FindNanError(MyokitError):
    """
    Raised by some simulations when a search for the origins of a numerical
    error has failed.

    *Extends:* :class:`myokit.MyokitError`
    """


class GenerationError(MyokitError):
    """
    Raised by simulation engines and other auto-compiled classes if code
    generation fails.

    *Extends:* :class:`myokit.MyokitError`
    """


class IllegalAliasError(MyokitError):
    """
    Raised when an attempt is made to add an alias in an invalid manner.

    *Extends:* :class:`myokit.MyokitError`
    """


class IllegalReferenceError(IntegrityError):
    """
    Raised when a reference is found to a variable ``reference`` that isn't
    accessible from the owning variable ``owner``'s scope.

    *Extends:* :class:`myokit.IntegrityError`
    """
    def __init__(self, reference, owner):
        super(IllegalReferenceError, self).__init__(
            'Illegal reference: The referenced variable <' + reference.qname()
            + '> is outside the scope of <' + owner.qname() + '>.'
        )


class ImportError(MyokitError):
    """
    Raised when an import from another format fails.

    *Extends:* :class:`myokit.MyokitError`.
    """


class IncompatibleModelError(MyokitError):
    """
    Raised if a model is not compatible with some requirement.

    *Extends:* :class:`myokit.MyokitError`.
    """
    def __init__(self, model_name, message):
        msg = 'Incompatible model'
        if model_name:
            msg += ' <' + str(model_name) + '>'
        msg += ': ' + str(message)
        super(IncompatibleModelError, self).__init__(msg)


class IncompatibleUnitError(MyokitError):
    """
    Raised when a unit incompatibility is detected.

    *Extends:* :class:`myokit.MyokitError`.
    """
    def __init__(self, message, token=None):
        super(MyokitError, self).__init__(message)
        self._token = token

    def token(self):
        """
        Returns a parser token associated with this error, or ``None`` if no
        such token was given.
        """
        return self._token


class InvalidBindingError(IntegrityError):
    """
    Raised when an invalid binding is made.

    *Extends:* :class:`myokit.IntegrityError`
    """


class InvalidDataLogError(MyokitError):
    """
    Raised during validation of a :class:`myokit.DataLog` if a violation is
    found.

    *Extends:* :class:`myokit.MyokitError`.
    """


class InvalidFunction(MyokitError):
    """
    Raised when a function is declared with invalid arguments or an invalid
    expression.

    *Extends:* :class:`myokit.MyokitError`.
    """


class InvalidLabelError(IntegrityError):
    """
    Raised when an invalid label is set.

    *Extends:* :class:`myokit.IntegrityError`
    """


class InvalidNameError(MyokitError):
    """
    Raised when an attempt is made to add a component or variable with a name
    that violates the myokit naming rules.

    *Extends:* :class:`myokit.MyokitError`
    """


class InvalidMetaDataNameError(MyokitError):
    """
    Raised when an attempt is made to add a meta data property with a name
    that violates that the myokit naming rules for meta data properties.

    *Extends:* :class:`myokit.MyokitError`
    """


class MissingRhsError(IntegrityError):
    """
    Raised when a variable was declared without a defining right-hand side
    equation.

    The first argument ``var`` should be the invalid variable.

    *Extends:* :class:`myokit.IntegrityError`
    """
    def __init__(self, var):
        msg = 'No rhs set for <' + var.qname() + '>.'
        tok = var._token
        super(MissingRhsError, self).__init__(msg, tok)


class MissingTimeVariableError(IntegrityError):
    """
    Raised when no variable was bound to time.

    *Extends:* :class:`myokit.IntegrityError`
    """
    def __init__(self):
        msg = 'No variable bound to time. At least one of the model\'s' \
              ' variables must be bound to "time".'
        super(MissingTimeVariableError, self).__init__(msg)


class NonLiteralValueError(IntegrityError):
    """
    Raised when a literal value is required but not given.

    *Extends:* :class:`myokit.IntegrityError`
    """


class NumericalError(MyokitError):
    """
    Raised when a numerical error occurs during the evaluation of a myokit
    :class:`Expression`.

    *Extends:* :class:`myokit.MyokitError`
    """


class ParseError(MyokitError):
    """
    Raised if an error is encountered during a parsing operation.

    A ParseError has five attributes:

    ``name``
        A short name describing the error
    ``line``
        The line the error occurred on (integer, first line is one)
    ``char``
        The character the error ocurred on (integer, first char is zero)
    ``desc``
        A more detailed description of the error.
    ``cause``
        Another exception that triggered this exception (or ``None``).

    *Extends:* :class:`myokit.MyokitError`
    """
    def __init__(self, name, line, char, desc, cause=None):
        self.name = str(name)
        self.line = int(line)
        self.char = int(char)
        self.value = self.name + ' on line ' + str(self.line)
        self.desc = str(desc)
        self.value += ': ' + self.desc
        self.cause = cause
        super(ParseError, self).__init__(self.value)


class ProtocolEventError(MyokitError):
    """
    Raised when a :class:`ProtocolEvent` is created with invalid parameters.

    *Extends:* :class:`myokit.MyokitError`
    """


class ProtocolParseError(ParseError):
    """
    Raised when protocol parsing fails.

    *Extends:* :class:`ParseError`
    """


class SectionNotFoundError(MyokitError):
    """
    Raised if a section should be present in a file but is not.

    *Extends:* :class:`myokit.MyokitError`
    """


class SimulationError(MyokitError):
    """
    Raised when a numerical error occurred during a simulation. Contains a
    detailed error message.

    *Extends:* :class:`myokit.MyokitError`
    """
    # Only for numerical errors!


class SimulationCancelledError(MyokitError):
    """
    Raised when a user terminates a simulation.

    *Extends:* :class:`myokit.MyokitError`
    """
    def __init__(self, message='Operation cancelled by user.'):
        super(SimulationCancelledError, self).__init__(message)


class SimultaneousProtocolEventError(MyokitError):
    """
    Raised if two events in a protocol happen at the same time. Raised when
    creating a protocol or when running one.

    *Extends:* :class:`myokit.MyokitError`
    """


class UnresolvedReferenceError(IntegrityError):
    """
    Raised when a reference to a variable cannot be resolved.

    *Extends:* :class:`myokit.IntegrityError`
    """
    def __init__(self, reference, extra_message=None):
        super(UnresolvedReferenceError, self).__init__(
            'Unknown variable: <' + reference + '>.'
            + ((' ' + extra_message) if extra_message else '')
        )


class UnusedVariableError(IntegrityError):
    """
    Raised when an unused variable is found.

    The unused variable must be passed in as the first argument ``var``.

    *Extends:* :class:`myokit.IntegrityError`
    """
    def __init__(self, var):
        msg = 'Unused variable: <' + var.qname() + '>.'
        tok = var.lhs()._token
        super(UnusedVariableError, self).__init__(msg, tok)


class VariableMappingError(MyokitError):
    """
    Raised when a method needs to map variables from one model onto another,
    but no valid mapping can be made.

    *Extends:* :class:`myokit.MyokitError`.
    """
