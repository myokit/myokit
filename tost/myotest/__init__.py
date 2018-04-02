#!/usr/bin/env python2
#
# Tests!
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import sys
import fnmatch
import unittest

# Dedicated test classes
from _ansic_event_based_pacing import AnsicEventBasedPacing  # noqa
from _ansic_fixed_form_pacing import AnsicFixedFormPacing  # noqa


# Set this to True to debug the tests
DEBUG = False

# The test directory
DIR_TEST = os.path.abspath(os.path.dirname(__file__))

# The data directory
DIR_DATA = os.path.join(DIR_TEST, '_data')

# The output directory
DIR_OUT = os.path.join(DIR_TEST, '_out')

# Ensure output directory exists
if os.path.exists(DIR_OUT):
    if not os.path.isdir(DIR_OUT):
        raise Exception('Output path is not a directory: ' + DIR_OUT)
else:
    os.makedirs(DIR_OUT)


def cmd():
    """
    Runs tests from the command line.

    Returns ``True`` if tests were run without errors or failures.
    """
    args = sys.argv[1:]
    if args:
        if '-?' in args:
            # Print explanation
            print('Usage:')
            print('  Run without arguments to run all tests')
            print('  Or select one or more from:')
            glob = '*.py'
            for fn in fnmatch.filter(os.listdir(DIR_TEST), glob):
                name = fn[:-3]
                mod = __import__(name, globals(), locals(), ['suite'])
                if 'suite' in dir(mod):
                    print('    ' + name)
            return False
        else:
            return run(*args)
    else:
        return run_all()


def run(*tests):
    """
    Runs selected tests.
    """
    print('Scanning for tests: ' + ', '.join([str(x) for x in tests]))
    suite = unittest.TestSuite()
    for name in tests:
        path = os.path.join(DIR_TEST, name + '.py')
        try:
            mod = __import__(name, globals(), locals(), ['suite'])
        except ImportError:
            print('Test <' + name + '> not found.')
            continue
        if 'suite' not in dir(mod):
            print('Test <' + name + '> has no method suite().')
            continue
        suite.addTests(mod.suite())
    print('Running selected tests')
    result = unittest.TextTestRunner().run(suite)
    issues = len(result.failures) + len(result.errors)
    return issues == 0


def run_all(exclude=None):
    """
    Runs all tests.

    A list of filenames to exclude can be given in ``exclude``.
    """
    exclude = set(exclude) if exclude else set()

    print('Scanning for tests')
    suite = unittest.TestSuite()
    glob = '*.py'
    for fn in fnmatch.filter(os.listdir(DIR_TEST), glob):
        if fn in exclude:
            continue

        name = fn[:-3]
        mod = __import__(name, globals(), locals(), ['suite'])
        if 'suite' in dir(mod):
            print('Adding ' + name)
            suite.addTests(mod.suite())

    print('Running all tests')
    result = unittest.TextTestRunner().run(suite)
    issues = len(result.failures) + len(result.errors)
    return issues == 0
