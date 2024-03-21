#!/usr/bin/env python3
#
# Test module
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
# The TemporaryDirectory class was adapted from Pints
# See: https://github.com/pints-team/pints
#
import os
import tempfile
import unittest
import warnings

import myokit


# The test directory
DIR_TEST = os.path.abspath(os.path.dirname(__file__))

# The data directory
DIR_DATA = os.path.join(DIR_TEST, 'data')

# Extra files in the data directory for load/save testing
DIR_IO = os.path.join(DIR_DATA, 'io')

# Extra files in the data directory for format testing
DIR_FORMATS = os.path.join(DIR_DATA, 'formats')

# OpenCL support
OpenCL_FOUND = myokit.OpenCL.available()
OpenCL_DOUBLE_PRECISION = False
OpenCL_DOUBLE_PRECISION_CONNECTIONS = False
if OpenCL_FOUND:
    info = myokit.OpenCL.current_info()
    OpenCL_DOUBLE_PRECISION = info.has_extension('cl_khr_fp64')
    if OpenCL_DOUBLE_PRECISION:
        OpenCL_DOUBLE_PRECISION_CONNECTIONS = info.has_extension(
            'cl_khr_int64_base_atomics')
    del info


class TemporaryDirectory:
    """
    ContextManager that provides a temporary directory to create temporary
    files in. Deletes the directory and its contents when the context is
    exited.
    """
    def __init__(self):
        super().__init__()
        self._dir = None

    def __enter__(self):
        self._dir = os.path.realpath(tempfile.mkdtemp())
        return self

    def path(self, path=None):
        """
        Returns an absolute path to a file or directory name inside this
        temporary directory, that can be used to write to.

        Example::

            with pints.io.TemporaryDirectory() as d:
                filename = d.path('test.txt')
                with open(filename, 'w') as f:
                    f.write('Hello')
                with open(filename, 'r') as f:
                    print(f.read())
        """
        if self._dir is None:
            raise RuntimeError(
                'TemporaryDirectory.path() can only be called from inside the'
                ' context.')

        if path is None:
            return self._dir

        path = os.path.realpath(os.path.join(self._dir, path))
        if path[0:len(self._dir)] != self._dir:
            raise ValueError(
                'Relative path specified to location outside of temporary'
                ' directory: ' + path)

        return path

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            myokit.tools.rmtree(self._dir)
        finally:
            self._dir = None

    def __str__(self):
        if self._dir is None:
            return '<TemporaryDirectory, outside of context>'
        else:
            return self._dir


class TestReporter(myokit.ProgressReporter):
    """
    Progress reporter just for debugging.
    """
    def __init__(self):
        self.entered = False
        self.exited = False
        self.updated = False

    def enter(self, msg=None):
        self.entered = True

    def exit(self):
        self.exited = True

    def update(self, f):
        self.updated = True
        return True


class CancellingReporter(myokit.ProgressReporter):
    """
    Progress reporter just for debugging, dies after `x` updates.
    """
    def __init__(self, okays=0):
        self.okays = int(okays)

    def enter(self, msg=None):
        pass

    def exit(self):
        pass

    def update(self, f):
        self.okays -= 1
        return self.okays >= 0


class WarningCollector:
    """
    Wrapper around warnings.catch_warnings() that gathers all messages into a
    single string.
    """
    def __init__(self):
        self._warnings = []
        self._w = warnings.catch_warnings(record=True)

    def __enter__(self):
        self._warnings = self._w.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self._w.__exit__(type, value, traceback)

    def count(self):
        """Returns the number of warnings caught."""
        return len(self._warnings)

    def has_warnings(self):
        """Returns ``True`` if there were any warnings."""
        return len(self._warnings) > 0

    def text(self):
        """Returns the text of all gathered warnings."""
        return ' '.join(str(w.message) for w in self._warnings)

    def warnings(self):
        """Returns all gathered warning objects."""
        return self._warnings


def test_case_pk_model(parameters, times):
    """
    This function returns the analytic solution of the state dynamics and
    partial derivatives for a repeated bolus infusion into a compartment with
    linear clearance.

    For details of the derivation please see the technical notes.

    Parameters
    ----------
    parameters
        A list with the initial drug amount, the elimination rate and the
        dose rate and the infusion duration at each injection.
    times
        The times for evaluation.
    """
    import numpy as np

    times = np.asarray(times)

    # Unpack parameters
    a_0, elimination_rate, dose_rate, duration = parameters

    # Compute time since start last infusion
    delta_times = times - np.floor(times)

    # Create a mask for unfinished doses
    mask = delta_times % 1 < duration

    # Compute times since stop last infusion
    delta_times -= duration

    # Compute a max and da_max / delimination_rate
    a_max = \
        dose_rate * (1 - np.exp(-elimination_rate * duration)) \
        / elimination_rate / (1 - np.exp(-elimination_rate))
    da_max = \
        - a_max * (
            1 / elimination_rate
            + np.exp(-elimination_rate) / (
                1 - np.exp(-elimination_rate))) \
        + duration * dose_rate * (
            np.exp(-elimination_rate * duration)
            / (1 - np.exp(-elimination_rate))
            / elimination_rate)

    # Compute amount
    amount = a_0 * np.exp(-elimination_rate * times)
    amount[mask] += \
        a_max * (
            np.exp(-elimination_rate * (delta_times[mask] + 1))
            - np.exp(-elimination_rate * (times[mask] - duration + 1))) \
        + dose_rate / elimination_rate * (
            1 - np.exp(-elimination_rate * (delta_times[mask] + duration)))
    amount[~mask] += \
        a_max * (
            np.exp(-elimination_rate * delta_times[~mask])
            - np.exp(-elimination_rate * (times[~mask] - duration + 1)))

    # Compute partials
    damount_dinitial_amount = np.exp(-elimination_rate * times)
    damount_delimination_rate = \
        -times * a_0 * np.exp(-elimination_rate * times)
    damount_delimination_rate[mask] += \
        - a_max * (
            (delta_times[mask] + 1)
            * np.exp(-elimination_rate * (delta_times[mask] + 1))
            - (times[mask] - duration + 1)
            * np.exp(-elimination_rate * (times[mask] - duration + 1))) \
        + da_max * (
            np.exp(-elimination_rate * (delta_times[mask] + 1))
            - np.exp(-elimination_rate * (times[mask] - duration + 1))) \
        + dose_rate / elimination_rate * (
            delta_times[mask] + duration + 1 / elimination_rate) \
        * np.exp(-elimination_rate * (delta_times[mask] + duration)) \
        - dose_rate / elimination_rate**2
    damount_delimination_rate[~mask] += \
        - a_max * (
            delta_times[~mask]
            * np.exp(-elimination_rate * delta_times[~mask])
            - (times[~mask] - duration + 1) *
            np.exp(-elimination_rate * (times[~mask] - duration + 1))) \
        + da_max * (
            np.exp(-elimination_rate * delta_times[~mask])
            - np.exp(-elimination_rate * (times[~mask] - duration + 1)))
    partials = np.vstack([damount_dinitial_amount, damount_delimination_rate])

    return amount, partials


class ExpressionWriterTestCase(unittest.TestCase):
    """ Abstract class for expression writer tests. """

    _name = None
    _target = None
    _update_lhs_function = True

    @classmethod
    def setUpClass(cls):
        # Create a model with some variables for testing
        cls.model = m = myokit.Model()
        cls.component = c = m.add_component('comp')
        cls.a = myokit.Name(c.add_variable('a', rhs=1))
        cls.b = myokit.Name(c.add_variable('b', rhs=2))
        cls.c = myokit.Name(c.add_variable('c', rhs=3))
        cls.d = myokit.Name(c.add_variable('d', rhs=4))
        cls.e = myokit.Name(c.add_variable('e', rhs=5))
        cls.f = myokit.Name(c.add_variable('f', rhs=6))
        cls.g = myokit.Name(c.add_variable('g', rhs=7))
        cls.t = c.add_variable('t', rhs=0, binding='time')

        # Set unames
        m.validate()

        # Create writer
        cls.w = cls._target()
        if cls._update_lhs_function:
            cls.w.set_lhs_function(cls.lhs)

        # Easy access to properties
        cls.ab = (cls.a, cls.b)
        cls.abc = (cls.a, cls.b, cls.c)
        cls.abcd = (cls.a, cls.b, cls.c, cls.d)
        cls.efg = (cls.e, cls.f, cls.g)

    @classmethod
    def lhs(cls, ex):
        """
        Easier to read LHS function: ignores components.

        All LHS types are supported here: Lack of support for e.g. partial
        derivatives should be implemented in the expression writers themselves.
        """
        if isinstance(ex, myokit.Name):
            return ex.var().name()
        elif isinstance(ex, myokit.Derivative):
            return f'dot({ex.var().name()})'
        elif isinstance(ex, myokit.InitialValue):
            return f'initial({ex.var().name()})'
        elif isinstance(ex, myokit.PartialDerivative):
            v1 = ex.dependent_expression()
            v2 = ex.independent_expression()
            return f'partial({v1.var().name()}, {v2.var().name()})'
        raise ValueError(f'Untested LHS type {type(ex)}')

    def test_fetching(self):
        # Test fetching using ewriter method
        w = myokit.formats.ewriter(self._name)
        self.assertIsInstance(w, self._target)

    def test_bad_argument(self):
        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', self.w.ex, 7)

    def eq(self, expression, expected_output):
        self.assertEqual(self.w.ex(expression), expected_output)
