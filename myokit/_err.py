#
# Non-standard exceptions raised by myokit.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
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
    *Extends:* ``Exception``

    Base class for all exceptions specific to Myokit.

    Note that myokit classes and functions may raise any type of exception, for
    example a :class:``KeyError`` or a :class:`ValueError`. Only new classes of
    exception *defined* by Myokit will extend this base class.
    """
    def __init__(self, message):
        super(MyokitError, self).__init__(message)


class IntegrityError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised if an integrity error is found in a model.

    The error message is stored in the property ``message``. An optional parser
    token may be obtained with :meth:`token()`.
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
    *Extends:* :class:`myokit.MyokitError`

    Raised if an auto-compiling class fails to compile. Catching one of these
    is usually a good excuses to email the developers ;-)
    """


class CyclicalDependencyError(IntegrityError):
    """
    *Extends:* :class:`myokit.IntegrityError`

    Raised when an variables depend on each other in a cyclical manner.

    The first argument ``cycle`` must be a sequence containing the
    :class:`Variable` objects in the cycle.
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
    *Extends:* :class:`myokit.MyokitError`.

    Raised when an error is encountered while reading a
    :class:`myokit.DataBlock1d` or :class:`myokit.DataBlock2d`.
    """


class DataLogReadError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`.

    Raised when an error is encountered while reading a
    :class:`myokit.DataLog`.
    """


class DuplicateName(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when an attempt is made to add a component or variable with a name
    that is already in use within the relevant scope.
    """


class DuplicateFunctionName(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when an attempt is made to add a user function to a model when a
    function with the same name and number of arguments already exists.
    """


class DuplicateFunctionArgument(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when an attempt is made to define a user function with duplicate
    argument names.
    """


class ExportError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`.

    Raised when an export to another format fails.
    """


class FindNanError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised by some simulations when a search for the origins of a numerical
    error has failed.
    """


class GenerationError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised by simulation engines and other auto-compiled classes if code
    generation fails.
    """


class IllegalAliasError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when an attempt is made to add an alias in an invalid manner.
    """


class IllegalReferenceError(IntegrityError):
    """
    *Extends:* :class:`myokit.IntegrityError`

    Raised when a reference is found to a variable ``reference`` that isn't
    accessible from the owning variable ``owner``'s scope.
    """
    def __init__(self, reference, owner):
        super(IllegalReferenceError, self).__init__(
            'Illegal reference: The referenced variable <' + reference.qname()
            + '> is outside the scope of <' + owner.qname() + '>.'
        )


class ImportError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`.

    Raised when an import from another format fails.
    """


class IncompatibleModelError(MyokitError):
    """
    Raised if a model is not compatible with some requirement.
    """
    def __init__(self, name, message):
        super(IncompatibleModelError, self).__init__(
            'Incompatible model <' + str(name) + '>: ' + str(message))


class IncompatibleUnitError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when a unit incompatibility is detected.
    """


class InvalidBindingError(IntegrityError):
    """
    *Extends:* :class:`myokit.IntegrityError`

    Raised when an invalid binding is made.
    """


class InvalidDataLogError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`.

    Raised during validation of a :class:`myokit.DataLog` if a violation is
    found.
    """


class InvalidFunction(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when a function is declared with invalid arguments or an invalid
    expression.
    """


class InvalidLabelError(IntegrityError):
    """
    *Extends:* :class:`myokit.IntegrityError`

    Raised when an invalid label is set.
    """


class InvalidNameError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when an attempt is made to add a component or variable with a name
    that violates the myokit naming rules.
    """


class InvalidMetaDataNameError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when an attempt is made to add a meta data property with a name
    that violates that the myokit naming rules for meta data properties.
    """


class MissingRhsError(IntegrityError):
    """
    *Extends:* :class:`myokit.IntegrityError`

    Raised when a variable was declared without a defining right-hand side
    equation.

    The first argument ``var`` should be the invalid variable.
    """
    def __init__(self, var):
        msg = 'No rhs set for <' + var.qname() + '>.'
        tok = var._token
        super(MissingRhsError, self).__init__(msg, tok)


class MissingTimeVariableError(IntegrityError):
    """
    *Extends:* :class:`myokit.IntegrityError`

    Raised when no variable was bound to time.
    """
    def __init__(self):
        msg = 'No variable bound to time. At least one of the model\'s' \
              ' variables must be bound to "time".'
        super(MissingTimeVariableError, self).__init__(msg)


class NonLiteralValueError(IntegrityError):
    """
    *Extends:* :class:`myokit.IntegrityError`

    Raised when a literal value is required but not given.
    """


class NumericalError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when a numerical error occurs during the evaluation of a myokit
    :class:`Expression`.
    """


class ParseError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

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
    *Extends:* :class:`myokit.MyokitError`

    Raised when a :class:`ProtocolEvent` is created with invalid parameters.
    """


class ProtocolParseError(ParseError):
    """
    *Extends:* :class:`ParseError`

    Raised when protocol parsing fails.
    """


class SectionNotFoundError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised if a section should be present in a file but is not.
    """


class SimulationError(MyokitError):
    """
    *Extends:* :class:`myokit.MyokitError`

    Raised when a numerical error occurred during a simulation. Contains a
    detailed error message.
    """
    # Only for numerical errors!


class SimulationCancelledError(MyokitError):
    """
    *Extends:* ``MyokitError``

    Raised when a user terminates a simulation.
    """
    def __init__(self, message='Operation cancelled by user.'):
        super(SimulationCancelledError, self).__init__(message)


class SimultaneousProtocolEventError(MyokitError):
    """
    *Extends:* ``MyokitError``

    Raised if two events in a protocol happen at the same time. Raised when
    creating a protocol or when running one.
    """


class UnresolvedReferenceError(IntegrityError):
    """
    *Extends:* :class:`myokit.IntegrityError`

    Raised when a reference to a variable cannot be resolved.
    """
    def __init__(self, reference, extra_message=None):
        super(UnresolvedReferenceError, self).__init__(
            'Unknown variable: <' + reference + '>.'
            + ((' ' + extra_message) if extra_message else '')
        )


class UnusedVariableError(IntegrityError):
    """
    *Extends:* :class:`myokit.IntegrityError`

    Raised when an unused variable is found.

    The unused variable must be passed in as the first argument ``var``.
    """
    def __init__(self, var):
        msg = 'Unused variable: <' + var.qname() + '>.'
        tok = var.lhs()._token
        super(UnusedVariableError, self).__init__(msg, tok)
