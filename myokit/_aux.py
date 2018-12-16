#
# Myokit auxillary functions: This module can be used to gather any
# functions that are important enough to warrant inclusion in the main
# myokit module but don't belong to any specific hidden module.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import re
import sys
import array
import timeit
import shutil
import fnmatch
import zipfile
import tempfile

# StringIO in Python 2 and 3
try:
    from cStringIO import StringIO
except ImportError:  # pragma: no python 2 cover
    from io import StringIO

# String types in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str

import myokit

# Globally shared numpy expression writer
_numpywriter_ = None

# Globally shared python expression writer
_pywriter_ = None

# Natural sort regex
_natural_sort_regex = re.compile('([0-9]+)')


def date():
    """
    Returns the current date and time, formatted as specified in
    ``myokit.settings``.
    """
    import time
    return time.strftime(myokit.DATE_FORMAT)


def time():
    """
    Returns the current time, formatted as specified in ``myokit.settings``.
    """
    import time as t
    return t.strftime(myokit.TIME_FORMAT)


def _natural_sort_key(s):
    """
    Natural sort key, from: http://stackoverflow.com/questions/4836710/

    Usage example::

        values.sort(key=lambda x: myokit._natural_sort_key(x))

    """
    return [
        int(text) if text.isdigit() else text.lower()
        for text in _natural_sort_regex.split(s)]


class Benchmarker(object):
    """
    Allows benchmarking using the with statement.

    Example::

        m,p,x = myokit.load('example')
        s = myokit.Simulation(m, p)
        b = myokit.Benchmarker()
        s.run()
        print(b.time())
        b.reset()
        s.run()
        print(b.time())

    """
    def __init__(self, output=None):
        self._start = timeit.default_timer()

    def format(self, time):
        """
        Formats a (non-integer) number of seconds, returns a string like
        "5 weeks, 3 days, 1 hour, 4 minutes, 9 seconds", or "0.0019 seconds".
        """
        if time < 60:
            return '1 second' if time == 1 else str(time) + ' seconds'
        output = []
        time = int(round(time))
        units = [
            (604800, 'week'),
            (86400, 'day'),
            (3600, 'hour'),
            (60, 'minute'),
        ]
        for k, name in units:
            f = time // k
            if f > 0 or output:
                output.append(str(f) + ' ' + (name if f == 1 else name + 's'))
            time -= f * k
        output.append('1 second' if time == 1 else str(time) + ' seconds')
        return ', '.join(output)

    def reset(self):
        """
        Resets this timer's start time.
        """
        self._start = timeit.default_timer()

    def time(self):
        """
        Returns the time since benchmarking started.
        """
        return timeit.default_timer() - self._start


class PyCapture(object):
    """
    A context manager that redirects and captures the standard and error output
    of the python interpreter, using pure python techniques.
    """
    def __init__(self, enabled=True):
        super(PyCapture, self).__init__()

        # Generic properties
        self._enabled = enabled     # True if enabled
        self._capturing = False     # True if currently capturing
        self._captured = []         # Array to store captured strings in

        # Python specific properties
        self._stdout = None     # Original stdout
        self._stderr = None     # Original stderr
        self._dupout = None     # String buffer to redirect stdout to
        self._duperr = None     # String buffer to redirect stderr to

    def clear(self):
        """
        Deletes all captured text.
        """
        capturing = self._capturing
        if capturing:
            self._stop_capturing()
        self._captured = []
        if capturing:
            self._start_capturing()

    def disable(self):
        """
        Disables the silencing. Any capturing currently taking place is halted.
        """
        self._enabled = False
        self._stop_capturing()

    def enable(self):
        """
        Enables the context manager and starts capturing output.
        """
        self._enabled = True
        self._start_capturing()

    def __enter__(self):
        """
        Called when the context is entered.
        """
        if self._enabled:
            self._start_capturing()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when exiting the context.
        """
        self._stop_capturing()

    def _start_capturing(self):
        """
        Starts capturing output to stdout and stderr.
        """
        if not self._capturing:
            # If possible, flush current outputs
            try:
                sys.stdout.flush()
            except AttributeError:  # pragma: no cover
                pass
            try:
                sys.stderr.flush()
            except AttributeError:  # pragma: no cover
                pass

            # Save current sys stdout / stderr redirects, if any
            self._stdout = sys.stdout
            self._stderr = sys.stderr

            # Create temporary buffers
            self._dupout = StringIO()
            self._duperr = StringIO()

            # Re-route
            sys.stdout = self._dupout
            sys.stderr = self._duperr

            # Now we're capturing!
            self._capturing = True

    def _stop_capturing(self):
        """
        Stops capturing output. If capturing was already halted, this does
        nothing.
        """
        if self._capturing:
            # Flush any remaining output to streams
            sys.stdout.flush()
            sys.stderr.flush()

            # Restore original stdout and stderr
            sys.stdout = self._stdout
            sys.stderr = self._stderr

            # Get captured output
            self._captured.append(self._dupout.getvalue())
            self._captured.append(self._duperr.getvalue())

            # Delete buffers
            self._dupout = self._duperr = None

            # No longer capturing
            self._capturing = False

    def text(self):
        """
        Returns the captured text.
        """
        capturing = self._capturing
        if capturing:
            self._stop_capturing()

        if sys.hexversion >= 0x03000000:    # pragma: no cover
            text = ''.join(self._captured)
        else:   # pragma: no cover
            # In Python 2, this needs to be decoded from ascii
            text = ''.join(
                [x.decode('ascii', 'ignore') for x in self._captured])

        if capturing:
            self._start_capturing()
        return text


class SubCapture(PyCapture):
    """
    A context manager that redirects and captures the standard and error output
    of the current process, using low-level file descriptor duplication.
    """
    def __init__(self, enabled=True):
        super(SubCapture, self).__init__()
        self._stdout = None     # Original stdout object
        self._stderr = None     # Original stderr object
        self._stdout_fd = None  # Original file descriptor used for output
        self._stderr_fd = None  # Original file descriptor used for errors
        self._dupout_fd = None  # Back-up of file descriptor for output
        self._duperr_fd = None  # Back-up of file descriptor for errors
        self._file_out = None   # Temporary file to write output to
        self._file_err = None   # Temporary file to write errors to

    def _start_capturing(self):
        """
        Starts capturing output to stdout and stderr.
        """
        if not self._capturing:
            # If possible, flush original outputs
            try:
                sys.stdout.flush()
            except AttributeError:  # pragma: no cover
                pass
            try:
                sys.stderr.flush()
            except AttributeError:  # pragma: no cover
                pass

            # Save any redirected output / error streams
            self._stdout = sys.stdout
            self._stderr = sys.stderr

            # Get file descriptors used for output and errors
            self._stdout_fd = sys.__stdout__.fileno()
            self._stderr_fd = sys.__stderr__.fileno()

            # If they're proper streams (so if not pythonw.exe), flush them
            if self._stdout_fd >= 0:
                sys.stdout.flush()
            if self._stderr_fd >= 0:
                sys.stderr.flush()

            # Create temporary files
            # Make sure this isn't opened in binary mode, and specify +
            # for reading and writing.
            self._file_out = tempfile.TemporaryFile(mode='w+')
            self._file_err = tempfile.TemporaryFile(mode='w+')

            # Redirect python-level output to temporary files
            # (Doing this is required to make this work on windows)
            sys.stdout = self._file_out
            sys.stderr = self._file_err

            # If possible, pipe the original output and errors to files
            # On windows, the order is important: First dup both stdout and
            # stderr, then dup2 the new descriptors in. This prevents a weird
            # infinite recursion on windows ipython / python shell.
            self._dupout_fd = None
            self._duperr_fd = None
            if self._stdout_fd >= 0:
                self._dupout_fd = os.dup(self._stdout_fd)
            if self._stderr_fd >= 0:
                self._duperr_fd = os.dup(self._stderr_fd)
            if self._stdout_fd >= 0:
                os.dup2(self._file_out.fileno(), self._stdout_fd)
            if self._stderr_fd >= 0:
                os.dup2(self._file_err.fileno(), self._stderr_fd)

            # Now we're capturing!
            self._capturing = True

    def _stop_capturing(self):
        """
        Stops capturing output. If capturing was already halted, this does
        nothing.
        """
        if self._capturing:
            # Flush any remaining output
            sys.stdout.flush()
            sys.stderr.flush()
            # Undo dupes, if made
            if self._dupout_fd is not None:
                os.dup2(self._dupout_fd, self._stdout_fd)
                os.close(self._dupout_fd)
            if self._duperr_fd is not None:
                os.dup2(self._duperr_fd, self._stderr_fd)
                os.close(self._duperr_fd)
            # Reset python-level redirects
            sys.stdout = self._stdout
            sys.stderr = self._stderr
            # Close temporary files and store capture output
            self._file_out.seek(0)
            self._captured.extend(self._file_out.readlines())
            self._file_out.close()
            self._file_err.seek(0)
            self._captured.extend(self._file_err.readlines())
            self._file_err.close()
            # We've stopped capturing
            self._capturing = False

    def bypass(self):
        """
        Returns a link to stdout, allowing you to bypass capture (for
        example for debug output).
        """
        return self._stdout


def _examplify(filename):
    """
    If ``filename`` is equal to "example" and there isn't a file with that
    name, this function returns the file specified by myokit.EXAMPLE. In all
    other cases, the original filename is returned.
    """
    if filename == 'example' and not os.path.exists(filename):
        return myokit.EXAMPLE
    else:
        return os.path.expanduser(filename)


def format_float_dict(d):
    """
    Takes a dictionary of ``string : float`` mappings and returns a formatted
    string.
    """
    keys = [str(k) for k in d.keys()]
    keys.sort()
    n = max([len(k) for k in keys])
    return '\n'.join(
        [k + ' ' * (n - len(k)) + ' = ' + strfloat(d[k]) for k in keys])


def format_path(path, root='.'):
    """
    Formats a path for use in user messages. If the given path is a
    subdirectory of the current directory this part is chopped off.

    Alternatively, a ``root`` directory may be given explicitly: any
    subdirectory of this path will be formatted relative to ``root``.

    This function differs from os.path.relpath() in the way it handles paths
    *outside* the root: In these cases relpath returns a relative path such as
    '../../' while this function returns an absolute path.
    """
    if path == '':
        path = '.'
    path = os.path.relpath(path, root)
    if '..' in path:
        path = os.path.abspath(os.path.join(root, path))
    return path


def load(filename):
    """
    Reads an ``mmt`` file and returns a tuple ``(model, protocol, embedded
    script)``.

    If the file specified by ``filename`` doesn't contain one of these parts
    the corresponding entry in the tuple will be ``None``.
    """
    f = open(_examplify(filename), 'r')
    try:
        return myokit.parse(f)
    finally:
        f.close()


def load_model(filename):
    """
    Loads the model section from an ``mmt`` file.

    Raises a :class:`SectionNotFoundError` if no model section is found.
    """
    filename = _examplify(filename)
    with open(filename, 'r') as f:
        section = myokit.split(f)[0]
        if not section.strip():
            raise myokit.SectionNotFoundError('Model section not found.')
        return myokit.parse(section.splitlines())[0]


def load_protocol(filename):
    """
    Loads the protocol section from an ``mmt`` file.

    Raises a :class:`SectionNotFoundError` if no protocol section is found.
    """
    filename = _examplify(filename)
    with open(filename, 'r') as f:
        section = myokit.split(f)[1]
        if not section.strip():
            raise myokit.SectionNotFoundError('Protocol section not found.')
        return myokit.parse(section.splitlines())[1]


def load_script(filename):
    """
    Loads the script section from an ``mmt`` file.

    Raises a :class:`SectionNotFoundError` if no script section is found.
    """
    filename = _examplify(filename)
    with open(filename, 'r') as f:
        section = myokit.split(f)[2]
        if not section.strip():
            raise myokit.SectionNotFoundError('Script section not found.')
        return myokit.parse(section.splitlines())[2]


def load_state(filename, model=None):
    """
    Loads an initial state from a file in one of the formats specified by
    :func:`myokit.parse_state()`.

    If a :class:`Model` is provided the state will be run through
    :meth:`Model.map_to_state()` and returned as a list of floating point
    numbers.
    """
    filename = os.path.expanduser(filename)
    with open(filename, 'r') as f:
        s = myokit.parse_state(f)
        if model:
            s = model.map_to_state(s)
        return s


def load_state_bin(filename):
    """
    Loads an initial state from a file in the binary format used by myokit.
    See :meth:`save_state_bin` for details.
    """
    filename = os.path.expanduser(filename)

    # Load compression modules
    import zipfile
    try:
        import zlib
        del(zlib)
    except ImportError:
        raise Exception(
            'This method requires the `zlib` module to be installed.')

    # Open file
    with zipfile.ZipFile(filename, 'r') as f:
        info = f.infolist()

        if len(info) != 1:  # pragma: no cover
            raise Exception('Invalid state file format [10].')

        # Split into parts, get data type and array size
        info = info[0]
        parts = info.filename.split('_')

        if len(parts) != 3:     # pragma: no cover
            raise Exception('Invalid state file format [20].')

        if parts[0] != 'state':     # pragma: no cover
            raise Exception('Invalid state file format [30].')

        code = parts[1]
        if code not in ['d', 'f']:  # pragma: no cover
            raise Exception('Invalid state file format [40].')
        # Convert code to str for Python 2.7.10 (see #225)
        code = str(code)

        size = int(parts[2])
        if size < 0:    # pragma: no cover
            raise Exception('Invalid state file format [50].')

        # Create array, read bytes into array
        ar = array.array(code)
        try:
            ar.frombytes(f.read(info))
        except AttributeError:  # pragma: no python 3 cover
            ar.fromstring(f.read(info))

        # Always store as little endian
        if sys.byteorder == 'big':  # pragma: no cover
            ar.byteswap()

    return list(ar)


def _lvsd(s1, s2):
    """
    Calculates a Levenshtein distance, as found on wikibooks

    :param s1: The first string to compare
    :param s2: The second string to compare
    :returns: int The distance between s1 and s2
    """
    if len(s1) < len(s2):
        return _lvsd(s2, s1)

    if not s1:
        return len(s2)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class ModelComparison(object):
    """
    Compares two models.

    The resulting diff text can be iterated over::

        for line in ModelComparison(m1, m2):
            print(line)

    Differences can be printed directly to ``stdout`` by setting ``live=True``.
    """
    def __init__(self, model1, model2, live=False):
        # Difference list
        self._diff = []

        # Live reporting
        self._live = True if live else False

        # Compare models
        if live:
            print('Comparing:')
            print('  [1] ' + model1.name())
            print('  [2] ' + model2.name())

        # -> Model meta data
        self._meta(model1, model2)

        # -> User functions
        self._userfunc(model1, model2)

        # -> Time variable
        self._time(model1, model2)

        # -> State vector
        self._state(model1, model2)

        # -> Components & Variables
        self._components(model1, model2)

        # Final report
        if live:
            print('Done')
            print('  ' + str(len(self._diff)) + ' differences found')

    def _components(self, m1, m2):
        """
        Compares two models' components.
        """
        seen = set()
        for c1 in m1.components(sort=True):
            seen.add(c1.qname())
            try:
                c2 = m2[c1.qname()]
            except KeyError:
                self._write('[2] Missing Component <' + c1.qname() + '>')
                continue
            self._comp(c1, c2)
        for c2 in m2.components(sort=True):
            if c2.qname() not in seen:
                self._write('[1] Missing Component <' + c2.qname() + '>')

    def _comp(self, c1, c2):
        """
        Compares the contents of two components with the same name.
        """
        assert(c1.qname() == c2.qname())
        # Meta information
        self._meta(c1, c2)
        # Test variables
        seen = set()
        for v1 in c1.variables(deep=True):
            name = v1.qname()
            seen.add(name)
            try:
                v2 = c2.model().get(name)
            except KeyError:
                self._write('[2] Missing Variable <' + name + '>')
                continue
            self._var(v1, v2)
        for v2 in c2.variables(deep=True):
            name = v2.qname()
            if name not in seen:
                self._write('[1] Missing Variable <' + name + '>')

    def equal(self):
        """
        Returns ``True`` if the two models were equal.
        """
        return len(self._diff) == 0

    def __iter__(self):
        """
        Iterate over the found differences.
        """
        return iter(self._diff)

    def __len__(self):
        """
        Returns the length of the difference array.
        """
        return len(self._diff)

    def _meta(self, x1, x2):
        """
        Compares two objects' meta properties.
        """
        assert(type(x1) == type(x2))
        if isinstance(x1, myokit.Model):
            name = ' in model'
        else:
            name = ' in <' + x1.qname() + '>'
        seen = set()
        for key, value in x1.meta.items():
            seen.add(key)
            try:
                if value != x2.meta[key]:
                    self._write(
                        '[x] Mismatched Meta property' + name + ': "'
                        + str(key) + '"')
            except KeyError:
                self._write(
                    '[2] Missing Meta property' + name + ': "' + str(key)
                    + '"')
        for key, value in x2.meta.items():
            if key not in seen:
                self._write(
                    '[1] Missing Meta property' + name + ': "' + str(key)
                    + '"')

    def _state(self, m1, m2):
        """
        Compares two models' states.
        """
        s1 = iter([v.qname() for v in m1.states()])
        s2 = iter([v.qname() for v in m2.states()])
        c1 = m1.state()
        c2 = m2.state()
        for k, v1 in enumerate(s1):
            try:
                v2 = next(s2)
            except StopIteration:
                self._write('[2] Missing state at position ' + str(k))
                continue
            if v1 != v2:
                self._write(
                    '[x] Mismatched State at position ' + str(k) + ': [1]<'
                    + v1 + '> [2]<' + v2 + '>')
                continue
            if c1[k] != c2[k]:
                self._write('[x] Mismatched Initial value for <' + v1 + '>')
        n = m2.count_states()
        for k, v2 in enumerate(s2):
            self._write('[1] Missing state at position ' + str(n + k))

    def text(self):
        """
        Returns the full difference text.
        """
        return '\n'.join(self._diff)

    def _time(self, m1, m2):
        """
        Compares two models' time variables.
        """
        t1 = m1.time()
        t2 = m2.time()
        if t1 is None:
            if t2 is not None:
                self._write('[1] Missing Time variable <' + t2.qname() + '>')
                return
        elif t2 is None:
            self._write('[2] Missing Time variable <' + t1.qname() + '>')
            return
        if t1.qname() != t2.qname():
            self._write(
                '[x] Mismatched Time variable: [1]<' + t1.qname() + '> [2]<'
                + t2.qname() + '>')

    def _userfunc(self, m1, m2):
        """
        Compares two models' user functions.
        """
        u1 = m1.user_functions()
        u2 = m2.user_functions()
        seen = set()
        for name, func in u1.items():
            seen.add(name)
            try:
                if func != u2[name]:
                    self._write('[x] Mismatched User function <' + name + '>')
            except KeyError:
                self._write('[2] Missing User function <' + name + '>')
        for name, func in u2.items():
            if name not in seen:
                self._write('[1] Missing User function <' + name + '>.')

    def _var(self, v1, v2):
        """
        Compares two variables with the same name.
        """
        name = v1.qname()
        assert(v2.qname() == name)
        # Left-hand side expression
        c1, c2 = v1.lhs().code(), v2.lhs().code()
        if c1 != c2:
            self._write('[x] Mismatched LHS <' + name + '>')
        # Right-hand side expression
        c1, c2 = v1.rhs().code(), v2.rhs().code()
        if c1 != c2:
            self._write('[x] Mismatched RHS <' + name + '>')
        # Units
        if v1.unit() != v2.unit():
            self._write('[x] Mismatched unit <' + name + '>')
        # Meta
        self._meta(v1, v2)
        # Don't test nested variables, this is done component wise

    def _write(self, text):
        """
        Writes a line to the difference array.
        """
        if self._live:
            print(text)
        self._diff.append(text)


def numpy_writer():
    """
    Returns a globally shared numpy expression writer.

    LhsExpressions are converted as follows:

    1. Derivatives are indicated as "_d_" + var.uname()
    2. Other names are indicated as var.uname()

    This convention ensures a unique mapping of a model's lhs expressions to
    acceptable python variable names.
    """
    global _numpywriter_
    if _numpywriter_ is None:
        from .formats.python import NumPyExpressionWriter
        _numpywriter_ = NumPyExpressionWriter()

        def name(x):
            u = x.var()
            u = u.uname() if isinstance(u, myokit.ModelPart) else str(u)
            if u is None:
                u = x.var().qname().replace('.', '_')
            return '_d_' + u if x.is_derivative() else u

        _numpywriter_.set_lhs_function(name)

    return _numpywriter_


def pack_snapshot(path, overwrite=True):
    """
    Packs a snapshot of the current myokit module into a zipfile at the given
    path.
    """
    # Import zlib compression
    try:
        import zlib
        del(zlib)
    except ImportError:
        raise Exception(
            'This method requires the `zlib` module to be installed.')
    zmod = zipfile.ZIP_DEFLATED

    # Check given path
    path = os.path.abspath(path)

    # Check if the path exists
    if os.path.exists(path):
        if os.path.isfile(path):
            if not overwrite:
                raise IOError('File already exists at given path.')
        else:
            path = os.path.join(
                path, 'myokit_' + myokit.__version__ + '_snapshot.zip')
            if os.path.isfile(path) and not overwrite:
                raise IOError('File already exists as given path.')

    # List of paths to ignore
    skip_base = [
        '.gitignore',
        '.git',
        '*.pyc',
        '__pycache__',
    ]

    def skip(filename):
        for pattern in skip_base:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    # Directory walking method
    def walk(pre, root, start=None):
        # pre: A path to prepend to every filename in the zipfile
        # root: A path to walk, adding every file it finds to the zip
        # start: The very first path walked, no need to set manually
        if start is None:
            start = root
        for leaf in os.listdir(root):
            # Skip certain files / directories
            if skip(leaf):
                continue
            # Get full filename, partial name starting from zip root
            leaf = os.path.join(root, leaf)
            name = os.path.relpath(leaf, start)
            # Walk directory or add files
            if os.path.isdir(leaf):
                walk(pre, leaf, start)
            elif os.path.isfile(leaf):
                zf.write(leaf, os.path.join(pre, name), zmod)

    # Create zipfile at temporary location
    tf = tempfile.mkstemp()
    try:
        with os.fdopen(tf[0], 'wb') as f:
            with zipfile.ZipFile(f, 'w', compression=zmod) as zf:
                # Add myokit module
                walk('myokit', myokit.DIR_MYOKIT)

                # Add license file
                license = myokit.LICENSE.encode('utf-8')
                zf.writestr('LICENSE', license, zmod)

        shutil.copy(tf[1], path)
    finally:
        if os.path.isfile(tf[1]):
            os.remove(tf[1])

    # Return path to new file
    return path


def python_writer():
    """
    Returns a globally shared python expression writer.

    LhsExpressions are converted as follows:

    1. Derivatives are indicated as "_d_" + var.uname()
    2. Other names are indicated as var.uname()

    This convention ensures a unique mapping of a model's lhs expressions to
    acceptable python variable names.
    """
    global _pywriter_
    if _pywriter_ is None:
        from .formats.python import PythonExpressionWriter
        _pywriter_ = PythonExpressionWriter()

        def name(x):
            u = x.var()
            u = u.uname() if isinstance(u, myokit.ModelPart) else str(u)
            if u is None:
                u = x.var().qname().replace('.', '_')
            return '_d_' + u if x.is_derivative() else u

        _pywriter_.set_lhs_function(name)

    return _pywriter_


def run(model, protocol, script, stdout=None, stderr=None, progress=None):
    """
    Runs a python ``script`` using the given ``model`` and ``protocol``.

    The following functions are provided to the script:

    ``get_model()``
        This returns the model passed to ``run()``. When using the GUI, this
        returns the model currently loaded into the editor.
    ``get_protocol()``
        This returns the protocol passed to ``run()``. When using the GUI, this
        returns the protocol currently loaded into the editor.

    Ordinary and error output can be re-routed by providing objects with a
    file-like interface (``x.write(text)``, ``x.flush()``) as ``stdout`` and
    ``stderr`` respectively. Note that output is only re-routed on the python
    level so that any output generated by C-code will still go to the main
    process's output and error streams.

    An object implementing the ``ProgressReporter`` interface can be passed in.
    This will be made available globally to any simulations (or other methods)
    that provide progress update information.
    """
    # Trim "[[script]]" from script
    script = script.splitlines()
    if script and script[0].strip() == '[[script]]':
        script = script[1:]
    script = '\n'.join(script)

    # Add an empty line at the start of the script. This will make the line
    # numbers reported in any error message correspond to those in the GUI.
    # In other words, a script section
    #
    #   1 [[script]]
    #   2 import myokit
    #   3 x = 1/0
    #
    # will raise an exception on line 3.
    #
    script = '\n' + script

    # Class to run scripts
    class Runner(object):
        def __init__(self, model, protocol, script, stdout, stderr, progress):
            super(Runner, self).__init__()
            self.model = model
            self.protocol = protocol
            self.script = script
            self.stdout = stdout
            self.stderr = stderr
            self.progress = progress
            self.exc_info = None

        def run(self):

            # Create magic functions
            def get_model():
                return self.model

            def get_protocol():
                return self.protocol

            # Re-route standard outputs, execute code
            oldstdout = oldstderr = None
            oldprogress = myokit._Simulation_progress
            myokit._Simulation_progress = self.progress
            try:
                if self.stdout is not None:
                    oldstdout = sys.stdout
                    sys.stdout = self.stdout
                if self.stderr is not None:
                    oldstderr = sys.stderr
                    sys.stderr = self.stderr
                environment = {
                    'get_model': get_model,
                    'get_protocol': get_protocol,
                }
                myokit._exec(self.script, environment)
            finally:
                if oldstdout is not None:
                    sys.stdout = oldstdout
                if oldstderr is not None:
                    sys.stderr = oldstderr
                myokit._Simulation_progress = oldprogress

    r = Runner(model, protocol, script, stdout, stderr, progress)
    r.run()

    # Free some space
    del(r)
    import gc
    gc.collect()


def save(filename=None, model=None, protocol=None, script=None):
    """
    Saves a model, protocol, and embedded script to an ``mmt`` file.

    The ``model`` argument can be given as plain text or a
    :class:`myokit.Model` object. Similarly, ``protocol`` can be either a
    :class:`myokit.Protocol` or its textual represenation.

    If no filename is given the ``mmt`` code is returned as a string.
    """
    if filename:
        filename = os.path.expanduser(filename)
        f = open(filename, 'w')
    else:
        f = StringIO()
    out = None
    try:
        if model is not None:
            if isinstance(model, myokit.Model):
                model = model.code()
            else:
                model = model.strip()
                if model != '' and model[:9] != '[[model]]':
                    f.write('[[model]]\n')
            model = model.strip()
            if model:
                f.write(model)
                f.write('\n\n')

        if protocol is not None:
            if isinstance(protocol, myokit.Protocol):
                protocol = protocol.code()
            else:
                protocol = protocol.strip()
                if protocol != '' and protocol[:12] != '[[protocol]]':
                    f.write('[[protocol]]\n')
            protocol = protocol.strip()
            if protocol:
                f.write(protocol)
                f.write('\n\n')

        if script is not None:
            script = script.strip()
            if script != '' and script[:10] != '[[script]]':
                f.write('[[script]]\n')
            if script:
                f.write(script)
                f.write('\n\n')
    finally:
        if filename:
            f.close()
        else:
            out = f.getvalue()
    return out


def save_model(filename, model):
    """
    Saves a model to a file
    """
    return save(filename, model)


def save_protocol(filename, protocol):
    """
    Saves a protocol to a file
    """
    return save(filename, protocol=protocol)


def save_script(filename, script):
    """
    Saves an embedded script to a file
    """
    return save(filename, script=script)


def save_state(filename, state, model=None):
    """
    Stores the given state in the file at ``filename``.

    If no ``model`` is specified ``state`` should be given as a list of
    floating point numbers and will be stored by simply placing each number on
    a new line.

    If a :class:`Model <myokit.Model>` is provided the state can be in any
    format accepted by :meth:`Model.map_to_state() <myokit.Model.map_to_state>`
    and will be stored in the format returned by
    :meth:`Model.format_state() <myokit.Model.format_state>`.
    """
    # Check filename
    filename = os.path.expanduser(filename)

    # Format
    if model is not None:
        state = model.map_to_state(state)
        state = model.format_state(state)
    else:
        state = [myokit.strfloat(s) for s in state]
        state = '\n'.join(state)

    # Store
    with open(filename, 'w') as f:
        f.write(state)


def save_state_bin(filename, state, precision=myokit.DOUBLE_PRECISION):
    """
    Stores the given state (or any list of floating point numbers) in the file
    at ``filename``, using a binary format.

    The used format is a zip file, containing a single entry: ``state_x_y``,
    where ``x`` is the used data type (``d`` or ``f``) and ``y`` is the number
    of entries. All entries are stored little-endian.
    """
    # Check filename
    filename = os.path.expanduser(filename)

    # Load compression modules
    import zipfile
    try:
        import zlib
        del(zlib)
    except ImportError:
        raise Exception(
            'This method requires the `zlib` module to be installed.')

    # Data type
    # Convert code to str for Python 2.7.10 (see #225)
    code = str('d' if precision == myokit.DOUBLE_PRECISION else 'f')

    # Create array, ensure it's little-endian
    ar = array.array(code, state)
    if sys.byteorder == 'big':  # pragma: no cover
        ar.byteswap()

    # Store precision and data type in internal filename
    name = 'state_' + code + '_' + str(len(state))
    info = zipfile.ZipInfo(name)
    info.compress_type = zipfile.ZIP_DEFLATED

    # Write to compressed file
    with zipfile.ZipFile(filename, 'w') as f:
        f.writestr(info, ar.tostring())


def step(model, initial=None, reference=None, ignore_errors=False):
    """
    Evaluates the state derivatives in a model and compares the results with a
    list of reference values, if given.

    The ``model`` should be given as a valid :class:`myokit.Model`. The state
    values to start from can be given as ``initial``, which should be any item
    that can be converted to a valid state using ``model.map_to_state``.

    The values can be compared to reference output given as a list
    ``reference``. Alternatively, if ``reference`` is a model the two models'
    outputs will be compared.

    By default, the evaluation routine checks for numerical errors
    (divide-by-zeros, invalid operations and overflows). To run an evaluation
    without error checking, set ``ignore_errors=True``.

    Returns a string indicating the results.
    """
    # Get initial state
    if initial is None:
        initial = model.state()

    # Get evaluation at initial state
    values = model.eval_state_derivatives(
        state=initial, ignore_errors=ignore_errors)

    # Log settings
    fmat = myokit.SFDOUBLE
    line_width = 79
    precision = 10

    # Get max variable name width (at least 4, for 'Name' header)
    w = max(4, max([len(v.qname()) for v in model.states()]))

    # Create log header
    log = []
    log.append('Evaluating state vector derivatives...')
    log.append('-' * line_width)
    log.append(('{:<' + str(w) + '}  {:<24}  {:<24}').format(
        'Name', 'Initial value', 'Derivative at t=0'))
    log.append('-' * line_width)

    # Format for states
    f = '{: <' + str(w) + '}  ' + fmat + '  ' + fmat

    if not reference:
        # Default output: intial value and derivative
        for r, v in enumerate(model.states()):
            log.append(f.format(v.qname(), v.state_value(), values[r]))
    else:
        # Comparing output

        # Reference should be a state evaluation, or a model
        if isinstance(reference, myokit.Model):
            reference = reference.eval_state_derivatives(
                state=initial, ignore_errors=ignore_errors)

        h = ' ' * (w + 28)
        i = h + ' ' * 20
        g = h + fmat
        errors = 0
        warnings = 0
        zero = fmat.format(0)[1:]

        for r, v in enumerate(model.states()):
            x = values[r]
            y = reference[r]
            log.append(f.format(v.qname(), v.state_value(), x))
            xx = fmat.format(x)
            yy = fmat.format(y)
            line = g.format(y)

            # Sign error: zero equals minus zero, don't count as error
            if xx[0] != yy[0] and (xx[1:] == yy[1:] == zero):
                log.append(line)
                log.append(h + ' ' * 24)

            # Different exponent, huge error
            elif xx[-4:] != yy[-4:]:
                errors += 1
                log.append(line + ' X !!!')
                log.append(i + '^^^^')

            # No error of smaller error
            else:
                threshold = 3 + precision  # 3 rubbish chars
                if xx[0:threshold] != yy[0:threshold]:
                    errors += 1
                    line += ' X'
                else:
                    if xx[threshold:] != yy[threshold:]:
                        warnings += 1
                log.append(line)
                line2 = h
                pos = 0
                n = len(xx)
                while pos < n and xx[pos] == yy[pos]:
                    line2 += ' '
                    pos += 1
                for pos in range(pos, n):
                    line2 += '^'
                log.append(line2)

        # Show large mismatches between model and reference
        if errors > 0:
            log.append(
                'Found (' + str(errors) + ') large mismatches between output'
                ' and reference values.')
        else:
            log.append('Model check completed without errors.')

        # Show small mismatches between model and reference
        if warnings > 0:
            log.append('Found (' + str(warnings) + ') small mismatches.')

    # Finalise and return
    log.append('-' * line_width)
    return '\n'.join(log)


def strfloat(number):
    """
    Turns the given number into a string, without losing accuracy.
    """
    # Pass through strings
    if isinstance(number, str):
        return number

    # Handle myokit.Numbers
    if isinstance(number, myokit.Number):
        number = number.eval()

    # For most numbers, allow python to format the float
    s = str(number)
    if len(s) < 10:
        return s

    # But if the number is given with lots of decimals, use the highest
    # precision number possible
    return myokit.SFDOUBLE.format(number)

