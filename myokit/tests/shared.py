#!/usr/bin/env python3
#
# Shared testing module
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
# The TemporaryDirectory class was adapted from Pints
# See: https://github.com/pints-team/pints
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import tempfile
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
OpenCL_FOUND = myokit.OpenCL.supported()


class TemporaryDirectory(object):
    """
    ContextManager that provides a temporary directory to create temporary
    files in. Deletes the directory and its contents when the context is
    exited.
    """
    def __init__(self):
        super(TemporaryDirectory, self).__init__()
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
            myokit._rmtree(self._dir)
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


class WarningCollector(object):
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

