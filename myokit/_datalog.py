#
# Functions relating to the DataLog class for storing time series data.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import re
import sys
import array
import numpy as np
from collections import OrderedDict
import myokit

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str


# Function to split keys into dimension-key,qname-key pairs
ID_NAME_PATTERN = re.compile(r'(\d+.)+')

# Readme file for DataLog binary files
README_SAVE_BIN = """
Myokit DataLog Binary File
--------------------------
This zip file contains binary time series data for one or multiple variables.
The file structure.txt contains structural information about the data in plain
text. The first line lists the number of fields. The second line gives the
length of the data arrays. The third line specifies the data type, either
single ("f") or double ("d") precision. The fourth line indicates which entry
corresponds to a time variable, or is blank if no time variable was explicitly
specified. Each following line contains the name of a data field, in the order
its data occurs in the binary data file "data.bin". All data is stored
little-endian.
""".strip()

# Encoding used for text portions of zip files
ENC = 'utf-8'


class DataLog(OrderedDict):
    """
    A dictionary time-series, for example data logged during a simulation or
    experiment.

    A :class:`DataLog` is expected but not required to contain a single
    entry indicating time and any number of entries representing a variable
    varying over time.

    Single cell data is accessed simply by the variable name::

        v = log['membrane.V']

    Multi-cell data is accessed by appending the index of the cell before the
    variable name. For example::

        v = log['1.2.membrane.V']

    This returns the membrane potential for cell (1, 2). Another way to obtain
    the same result is::

        v = log['membrane.V', 1, 2]

    or, finally::

        v = log['membrane.V', (1, 2)]

    Every array stored in the log must have the same length. This condition can
    be checked by calling the method :meth:`validate`.

    A new ``DataLog`` can be created in a number of ways::

        # Create an empty DataLog:
        d = myokit.DataLog()
        d['time'] = [1, 2, 3]
        d['data'] = [2, 4, 5]
        d.set_time_key('time')

        # Create a clone of d
        e = myokit.DataLog(d)

        # Create a DataLog based on a dictionary
        d = myokit.DataLog({'time':[1, 2, 3], 'data':[2, 4, 5]}, time='time')

    Arguments:

    ``other``
        A DataLog to clone or a dictionary to use as basis.
    ``time``
        The log key to use for the time variable. When cloning a log, adding
        the ``time`` argument will overwrite the cloned value.
    """
    def __init__(self, other=None, time=None):
        """
        Creates a new DataLog.
        """
        if other is None:
            # Create new
            super(DataLog, self).__init__()
            self._time = None
        else:
            # Clone
            super(DataLog, self).__init__(other)
            try:
                self._time = str(other._time)
            except Exception:
                self._time = None
        if time is not None:
            self.set_time_key(time)

    def apd(self, v='membrane.V', threshold=-70):
        """
        Calculates one or more Action Potential Durations (APDs) in a single
        cell's membrane potential.

        *Note 1: More accuracte apd measurements can be created using the*
        :class:`Simulation` *object's APD tracking functionality. See*
        :meth:`Simulation.run()` *for details.*

        *Note 2: This APD is defined by simply checking crossing of a threshold
        potential, and does not look at lowest or highest voltages in a
        signal.*

        The membrane potential data should be listed in the log under the key
        given by ``v``.

        The APD is measured as the time that the membrane potential exceeds a
        certain, fixed, threshold. It does *not* calculate dynamic thresholds
        like "90% of max(V) - min(V)".

        The returned value is a list of tuples (AP_start, APD).
        """
        def crossings(x, y, t):
            """
            Calculates the ``x``-values where ``y`` crosses threshold ``t``.
            Returns a list of tuples ``(xc, sc)`` where ``xc`` is the ``x``
            coordinate of the crossing and ``sc`` is the slope at this point.
            """
            x = np.asarray(x)
            y = np.asarray(y)

            # Get array of places where v exceeds the threshold (1s and 0s)
            h = (y > t) * 1

            # Get array of indices just before a crossing
            c = np.argwhere(h[1:] - h[:-1])

            # Gather crossing times
            crossings = []
            for i in c:
                i = i[0]
                sc = (y[i + 1] - y[i]) / (x[i + 1] - x[i])
                if y[i] == t:
                    xc = x[i]
                else:
                    xc = x[i] + (t - y[i]) / sc
                crossings.append((xc, sc))
            return crossings

        # Check time variable
        t = np.asarray(self.time())

        # Check voltage variable
        v = np.asarray(self[v])

        # Check threshold
        threshold = float(threshold)

        # Initial status: check if already in AP
        apds = myokit.DataLog()
        apds['start'] = []
        apds['duration'] = []
        last = t[0]

        # Evaluate crossings
        for time, slope in crossings(t, v, threshold):
            if slope < 0:
                # End of AP
                if last != t[0]:    # Don't inlcude AP started before t[0]
                    apds['start'].append(last)
                    apds['duration'].append(time - last)
            last = time
        return apds

    def block1d(self):
        """
        Returns a copy of this log as a :class:`DataBlock1d`.
        """
        return myokit.DataBlock1d.from_log(self)

    def block2d(self):
        """
        Returns a copy of this log as a :class:`DataBlock2d`.
        """
        return myokit.DataBlock2d.from_log(self)

    def clone(self, numpy=False):
        """
        Returns a deep clone of this log.

        All lists in the log will be duplicated, but the list contents are
        assumed to be numerical (and thereby immutable) and won't be cloned.

        A log with numpy arrays instead of lists can be created by setting
        ``numpy=True``.
        """
        log = DataLog()
        log._time = self._time
        if numpy:
            for k, v in self.items():
                log[str(k)] = np.array(v, copy=True, dtype=float)
        else:
            for k, v in self.items():
                log[str(k)] = list(v)
        return log

    def __contains__(self, key):
        return super(DataLog, self).__contains__(self._parse_key(key))

    def __delitem__(self, key):
        return super(DataLog, self).__delitem__(self._parse_key(key))

    def extend(self, other):
        """
        Returns a copy of this log, extended with the data of another.

        Both logs must have the same keys and the same time key. The added data
        must be from later time points than in the log being extended.
        """
        if other._time != self._time:
            raise ValueError('Both logs must have the same time key.')
        if other[self._time][0] < self[self._time][-1]:
            raise ValueError(
                'Cannot extend DataLog with data from an earlier time.')
        if set(self.keys()) != set(other.keys()):
            raise ValueError('Both logs must have the same keys.')
        # Create new log
        log = DataLog()
        log._time = self._time
        # Add data
        for k, v1 in self.items():
            v2 = other[k]
            if isinstance(v1, np.ndarray) or isinstance(v2, np.ndarray):
                # Concatenation copies data
                log[k] = np.concatenate((np.asarray(v1), np.asarray(v2)))
            else:
                log[k] = list(v1)   # Copies v1 data
                log[k].extend(v2)   # Copies v2 data
        # Return
        return log

    def find(self, time):
        """
        Deprecated alias of :meth:`find_after()`.
        """
        # Deprecated since 2019-08-16
        import warnings
        warnings.warn(
            'The method `find` is deprecated. Please use `find_after`'
            ' instead.')

        return self.find_after(time)

    def find_after(self, time):
        """
        Returns the lowest indice ``i`` such that

            times[i] >= time

        where ``times`` are the times stored in this ``DataLog``.

        If no such value exists in the log, ``len(time)`` is returned.
        """
        times = self[self._time]

        # Border cases
        n = len(times)
        if n == 0 or time <= times[0]:
            return 0
        if time > times[-1]:
            return n

        # Find t
        def find(lo, hi):
            # lo = first indice, hi = last indice + 1
            if (lo + 1 == hi):
                return lo + 1
            m = int((lo + hi) / 2)
            if time > times[m]:
                return find(m, hi)
            else:
                return find(lo, m)

        return find(0, n)

    def fold(self, period, discard_remainder=True):
        """
        Creates a copy of the log, split with the given period. Split signals
        are given indexes so that "current" becomes "0.current", "1.current"
        "2.current", etc.

        If the logs entries do not divide well by 'period', the remainder will
        be ignored. This happens commonly due to rounding point errors (in
        which case the remainder is a single entry). To disable this behavior,
        set ``discard_remainder=False``.
        """
        # Note: Using closed intervals can lead to logs of unequal length, so
        # it should be disabled here to ensure a valid log
        logs = self.split_periodic(period, adjust=True, closed_intervals=False)
        # Discard remainder if present
        if discard_remainder:
            if len(logs) > 1:
                n = logs[0].length()
                if logs[-1].length() < n:
                    logs = logs[:-1]
        # Create new log with folded data
        out = myokit.DataLog()
        out._time = self._time
        out[self._time] = logs[0][self._time]
        for i, log in enumerate(logs):
            for k, v in log.items():
                if k != self._time:
                    out[k, i] = v
        return out

    def __getitem__(self, key):
        return super(DataLog, self).__getitem__(self._parse_key(key))

    def has_nan(self):
        """
        Returns True if one of the variables in this DataLog has a ``NaN`` as
        its final logged value.
        """
        for k, d in self.items():
            if len(d) > 0 and np.isnan(d[-1]):
                return True
        return False

    def integrate(self, name, *cell):
        """
        Integrates a field from this log and returns it::

            # Run a simulation and calculate the total current carried by INa
            s = myokit.Simulation(m, p)
            d = s.run(1000)
            q = d.integrate('ina.INa')

        Arguments:

        ``name``
            The name of the variable to return, for example 'ik1.IK1' or
            '2.1.membrane.V'.
        ``*cell``
            An optional cell index, for easy access to multi-cellular data, for
            example ``log.integrate('membrane.V', 2, 1)``.

        """
        # Get data to integrate
        key = [str(x) for x in cell]
        key.append(str(name))
        key = '.'.join(key)
        data = np.array(self[key], copy=True)
        time = np.asarray(self.time())

        # Integration using the midpoint Riemann sum:
        #  At point i=0, the value is 0
        #  At each point i>0, the value increases by step[i, i-1]*mean[i, i-1]
        #data[1:] = 0.5 * (data[1:] + data[:-1]) * (time[1:] - time[:-1])
        #data[0]  = 0

        # For discontinuities (esp. with CVODES), it makes more sense to treat
        # the signal as a zero-order hold, IE use the left-point integration
        # rule:
        data[1:] = data[:-1] * (time[1:] - time[:-1])
        data[0] = 0
        return data.cumsum()

    def interpolate_at(self, name, time):
        """
        Returns the value for variable ``name`` at a given ``time``, determined
        using linear interpolation between the nearest matching times.
        """
        t = self[self._time]
        v = self[name]

        # Don't extrapolate
        if time < t[0] or time > t[-1]:
            raise ValueError(
                'Requested time is outside of logged range, would require'
                ' extrapolation.')

        # Get first time *after or at* requested time
        i1 = self.find_after(time)

        # Return directly, if possible
        if t[i1] == time:
            return v[i1]

        # Interpolate
        i0 = i1 - 1
        return v[i0] + (time - t[i0]) * (v[i1] - v[i0]) / (t[i1] - t[i0])

    def isplit(self, i):
        """
        Returns two logs, where the first contains all this log's entries up to
        index ``i``, and the second contains all entries starting from ``i``
        and higher.
        """
        log1 = DataLog()
        log2 = DataLog()
        log1._time = self._time
        log2._time = self._time
        for k, v in self.items():
            if isinstance(v, np.ndarray):
                log1[k] = np.array(v[:i], copy=True, dtype=float)
                log2[k] = np.array(v[i:], copy=True, dtype=float)
            else:
                log1[k] = v[:i]
                log2[k] = v[i:]
        return log1, log2

    def itrim(self, a, b):
        """
        Returns a copy of this log, with all entries trimmed to the region
        between indices ``a`` and ``b`` (similar to performing ``x = x[a:b]``
        on a list).
        """
        log = DataLog()
        log._time = self._time
        for k, v in self.items():
            if isinstance(v, np.ndarray):
                log[k] = np.array(v[a:b], copy=True, dtype=float)
            else:
                log[k] = v[a:b]
        return log

    def itrim_left(self, i):
        """
        Returns a copy of this log, with all entries before indice ``i``
        removed (similar to performing ``x = x[i:]`` on a list).
        """
        log = DataLog()
        log._time = self._time
        for k, v in self.items():
            if isinstance(v, np.ndarray):
                log[k] = np.array(v[i:], copy=True, dtype=float)
            else:
                log[k] = v[i:]
        return log

    def itrim_right(self, i):
        """
        Returns a copy of this log, with all entries starting from indice ``i``
        removed (similar to performing ``x = x[:i]`` on a list).
        """
        log = DataLog()
        log._time = self._time
        for k, v in self.items():
            if isinstance(v, np.ndarray):
                log[k] = np.array(v[:i], copy=True, dtype=float)
            else:
                log[k] = v[:i]
        return log

    def keys_like(self, query):
        """
        Returns all keys that match the pattern ``*.query``, sorted
        alphabetically.

        For example, ``log.keys_like('membrane.V')`` could return a list
        ``['0.membrane.V', '1.membrane.V', '2.membrane,V', ...]``, or
        ``['0.0.membrane.V', '0.1.membrane.V', '1.0.membrane,V', ...]``.
        """
        keys = [x for x in self.keys() if x.endswith('.' + str(query))]
        keys.sort()
        return keys

    def length(self):
        """
        Returns the length of the entries in this log. If the log is empty,
        zero is returned.
        """
        if len(self) == 0:
            return 0
        return len(next(iter(self.values())))

    @staticmethod
    def load(filename, progress=None, msg='Loading DataLog'):
        """
        Loads a :class:`DataLog` from the binary format used by myokit.

        The values in the log will be stored in an :class:`array.array`. The
        data type used by the array will be the one specified in the binary
        file. Notice that an `array.array` storing single precision floats will
        make conversions to ``Float`` objects when items are accessed.

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as `msg`.
        """
        # Check filename
        filename = os.path.expanduser(filename)

        # Load compression modules
        import zipfile
        try:
            # Ensure zlib is available
            import zlib
            del zlib
        except ImportError:
            raise Exception(
                'This method requires the ``zlib`` module to be installed.')

        # Get size of single and double types on this machine
        try:
            dsize = {
                'd': len(array.array('d', [1]).tobytes()),
                'f': len(array.array('f', [1]).tobytes()),
            }
        except (AttributeError, TypeError):  # pragma: no python 3 cover
            # List dtype as str for Python 2.7.10 (see #225)
            dsize = {
                b'd': len(array.array(b'd', [1]).tostring()),
                b'f': len(array.array(b'f', [1]).tostring()),
            }

        # Read data
        try:
            f = None
            f = zipfile.ZipFile(filename, 'r')
            # Get ZipInfo objects
            try:
                body = f.getinfo('data.bin')
            except KeyError:
                raise myokit.DataLogReadError('Invalid log file format.')
            try:
                head = f.getinfo('structure.txt')
            except KeyError:
                raise myokit.DataLogReadError('Invalid log file format.')
            # Read file contents
            head = f.read(head).decode(ENC)
            body = f.read(body)
        except zipfile.BadZipfile:
            raise myokit.DataLogReadError('Unable to read log: bad zip file.')
        except zipfile.LargeZipFile:    # pragma: no cover
            raise myokit.DataLogReadError(
                'Unable to read log: zip file requires zip64 support and this'
                ' has not been enabled on this system.')
        finally:
            if f:
                f.close()

        # Create empty log
        log = DataLog()

        # Parse header
        # Number of fields, length of data arrays, data type, time, fields
        head = iter(head.splitlines())
        n = int(next(head))
        data_size = int(next(head))
        data_type = str(next(head))  # Cast to str for Python 2.7.10 (see #225)
        time = next(head)
        if time:
            # Note, this field doesn't have to be present in the log!
            log._time = time
        fields = [x for x in head]
        if len(fields) != n:
            raise myokit.DataLogReadError(
                'Invalid number of fields specified.')

        # Get size of each entry on disk
        if data_size < 0:
            raise myokit.DataLogReadError(
                'Invalid data size: ' + str(data_size) + '.')
        try:
            data_size *= dsize[data_type]
        except KeyError:
            raise myokit.DataLogReadError(
                'Invalid data type: "' + data_type + '".')

        # Parse read data
        fraction = 1.0 / len(fields)
        start, end = 0, 0
        nbody = len(body)
        try:
            if progress:
                progress.enter(msg)
            for k, field in enumerate(fields):
                if progress and not progress.update(k * fraction):
                    return

                # Get new data position
                start = end
                end += data_size
                if end > nbody:
                    raise myokit.DataLogReadError(
                        'Header indicates larger data size than found in body.'
                    )

                # Read data
                ar = array.array(data_type)
                try:
                    ar.frombytes(body[start:end])
                except AttributeError:  # pragma: no python 3 cover
                    ar.fromstring(body[start:end])
                if sys.byteorder == 'big':  # pragma: no cover
                    ar.byteswap()
                log[field] = ar
        finally:
            if progress:
                progress.exit()
        return log

    @staticmethod
    def load_csv(filename, precision=myokit.DOUBLE_PRECISION):
        """
        Loads a CSV file from disk and returns it as a :class:`DataLog`.

        The CSV file must start with a header line indicating the variable
        names, separated by commas. Each subsequent row should contain the
        values at a single point in time for all logged variables.

        The ``DataLog`` is created using the data type specified by the
        argument ``precision``, regardless of the data type of the stored data.

        The log attempts to set a time variable by searching for a strictly
        increasing variable. In the case of a tie the first strictly increasing
        variable is used. This means logs stored with :meth:`save_csv` can
        safely be read.
        """
        log = DataLog()
        # Check filename
        filename = os.path.expanduser(filename)

        # Typecode dependent on precision
        # Typecode must be str for Python 2.7.10 (see #225)
        typecode = str('d' if precision == myokit.DOUBLE_PRECISION else 'f')

        # Error raising function
        def e(line, char, msg):
            raise myokit.DataLogReadError(
                'Syntax error on line ' + str(line) + ', character '
                + str(1 + char) + ': ' + msg)

        def uopen(filename):
            # Open a filename in 'universal newline' mode, python 2 and 3
            try:
                return open(filename, 'r', newline=None)
            except TypeError:   # pragma: no python 3 cover
                return open(filename, 'U')

        quote = '"'
        delim = ','
        with uopen(filename) as f:
            # Read header
            keys = []   # The log keys, in order of appearance

            # Read first line
            line = f.readline()

            # Ignore comments
            while line.lstrip()[:1] == '#':
                line = f.readline()

            # Stop on EOF (indicated by blank line without line ending)
            if line == '':
                return log

            # Trim end of line
            line = line.rstrip(' \r\n\f;')

            # Get enumerated iterator over characters
            line = enumerate(line)
            try:
                i, c = next(line)
            except StopIteration:
                # Empty line
                return log

            # Whitespace characters to ignore
            whitespace = ' \f\t'

            # Start parsing header fields
            run1 = True
            while run1:
                text = []

                # Skip whitespace
                # (Note: rtrim above and check below mean this will never
                #  raise a StopIteration)
                while c in whitespace:
                    i, c = next(line)

                # Read!
                if c == quote:

                    # Read quoted field + delimiter
                    run2 = True
                    while run2:
                        try:
                            i, c = next(line)
                        except StopIteration:
                            e(1, i, 'Unexpected end-of-line inside quoted'
                                ' string.')

                        if c == quote:
                            try:
                                i, c = next(line)
                                if c == quote:
                                    text.append(quote)
                                elif c == delim or c in whitespace:
                                    run2 = False
                                else:
                                    e(1, i, 'Expecting double quote, delimiter'
                                        ' or end-of-line. Found "' + c + '".')
                            except StopIteration:
                                run1 = run2 = False
                        else:
                            text.append(c)
                else:

                    # Read unquoted field + delimiter
                    while run1 and c != delim:
                        try:
                            text.append(c)
                            i, c = next(line)
                        except StopIteration:
                            run1 = False

                # Append new field to list
                key = ''.join(text)
                if key == '':
                    e(1, i, 'Empty field in header.')
                keys.append(key)

                # Read next character
                try:
                    i, c = next(line)
                except StopIteration:
                    run1 = False

            if c == delim:
                e(1, i, 'Empty field in header.')

            # Create data structure
            m = len(keys)
            lists = []
            for key in keys:
                x = array.array(typecode)
                lists.append(x)
                log[key] = x

            # Read remaining data
            n = 0
            while True:
                row = f.readline()

                # Stop if a blank line is returned: indicates EOF!
                # (Empty line in file still has line ending)
                if row == '':
                    break

                # Strip leading and/or trailing whitespace
                row = row.lstrip().rstrip(' \r\n\f;')

                # Skip blank lines
                if row == '':
                    continue

                # Ignore lines commented with #
                if row[:1] == '#':
                    continue

                # Split row into cells
                row = row.split(delim)
                n += 1
                if len(row) != m:
                    e(
                        n, 0, 'Wrong number of columns found in row '
                        + str(n) + '. Expecting ' + str(m) + ', found '
                        + str(len(row)) + '.')
                try:
                    for k, v in enumerate(row):
                        lists[k].append(float(v))
                except ValueError:
                    e(n, 0, 'Unable to convert found data to floats.')

            # Guess time variable
            for key in keys:
                x = np.array(log[key], copy=False)
                y = x[1:] - x[:-1]
                if np.all(y > 0):
                    log.set_time_key(key)
                    break

            # Return log
            return log

    def npview(self):
        """
        Returns a ``DataLog`` with numpy array views of this log's data.
        """
        log = DataLog()
        log._time = self._time
        for k, v in self.items():
            log[k] = np.asarray(v)
        return log

    def _parse_key(self, key):
        """
        Parses a key used for __getitem__, __setitem__, __delitem__ and
        __contains__.
        """
        if type(key) == tuple:
            name = str(key[0])
            if len(key) == 2 and type(key[1]) not in [int, float]:
                parts = [str(x) for x in key[1]]
            else:
                parts = [str(x) for x in key[1:]]
            parts.append(str(name))
            key = '.'.join(parts)
        return str(key)

    def regularize(self, dt, tmin=None, tmax=None):
        """
        Returns a copy of this DataLog with data points at regularly spaced
        times.

        *Note: While regularize() can be used post-simulation to create fixed
        time-step data from variable time-step data, it is usually better to
        re-run a simulation with fixed time step logging. See*
        :meth:`Simulation.run()` *for details.*

        The first point will be at ``tmin`` if specified or otherwise the first
        time present in the log. All following points will be spaced ``dt``
        time units apart and the final point will be less than or equal to
        ``tmax``. If no value for ``tmax`` is given the final value in the log
        is used.

        This method works by

          1. Finding the indices corresponding to ``tmin`` and ``tmax``.
          2. Creating a spline interpolant with all the data from ``tmin`` to
             ``tmax``. If possible, two points to the left and right of
             ``tmin`` and ``tmax`` will be included in the interpolated data
             set (so *only* if there are at least two values before ``tmin`` or
             two values after ``tmax`` in the data respectively).
          3. Evaluating the interpolant at the regularly spaced points.

        As a result of the cubic spline interpolation, the function may perform
        poorly on large data sets.

        This method requires ``SciPy`` to be installed.
        """
        self.validate()
        from scipy.interpolate import UnivariateSpline as Spline

        # Check time variable
        time = self.time()
        n = len(time)

        # Get left indice for splines
        imin = 0
        if tmin is None:
            tmin = time[0]
        elif tmin > time[0]:
            # Find position of tmin in time list, then add two points to the
            # left so that the spline has 4 points
            imin = max(0, np.searchsorted(time, tmin) - 2)

        # Get right indice for splines
        imax = n
        if tmax is None:
            tmax = time[-1]
        elif tmax < time[-1]:
            imax = min(n, np.searchsorted(time, tmax) + 2)

        # Get time steps
        steps = 1 + np.floor((tmax - tmin) / dt)
        rtime = tmin + dt * np.arange(0, steps)

        # Create output and return
        out = DataLog()
        out._time = self._time
        out[self._time] = rtime
        time_part = time[imin:imax]
        for key, data in self.items():
            if key != self._time:
                s = Spline(time_part, data[imin:imax], k=1, s=0)
                out[key] = s(rtime)
        return out

    def save(self, filename, precision=myokit.DOUBLE_PRECISION):
        """
        Writes this ``DataLog`` to a binary file.

        The resulting file will be a zip file with the following entries:

        ``header.txt``
            A csv file with the fields ``name, dtype, len`` for each variable.
        ``data.bin``
            The binary data in the order specified by the header.
        ``readme.txt``
            A text file explaining the file format.

        The optional argument ``precision`` allows logs to be stored in single
        precision format, which saves space.
        """
        self.validate()

        # Check filename
        filename = os.path.expanduser(filename)

        # Load compression modules
        import zipfile
        try:
            # Make sure zlib is available
            import zlib
            del zlib
        except ImportError:
            raise Exception(
                'This method requires the `zlib` module to be installed.')

        # Data type
        # dtype must be str for Python 2.7.10 (see #225)
        dtype = str('d' if precision == myokit.DOUBLE_PRECISION else 'f')

        # Create data strings
        head_str = []
        body_str = []   # Will be filled with bytes

        # Number of fields, length of data arrays, data type, time, fields
        head_str.append(str(len(self)))
        head_str.append(str(len(next(iter(self.values())))))
        head_str.append(dtype)

        # Note: the time field might not be present in the log!
        head_str.append(self._time if self._time else '')

        # Write field names and data
        enc = 'utf8'
        for k, v in self.items():
            head_str.append(k)
            # Create array, ensure it's litte-endian
            ar = array.array(dtype, v)
            if sys.byteorder == 'big':  # pragma: no cover
                ar.byteswap()
            try:
                body_str.append(ar.tobytes())
            except AttributeError:   # pragma: no python 3 cover
                body_str.append(ar.tostring())
        head_str = '\n'.join(head_str)
        body_str = b''.join(body_str)

        # 2018-07-15: Wondering why I chose body-head-readme ordering now...

        # Write
        head = zipfile.ZipInfo('structure.txt')
        head.compress_type = zipfile.ZIP_DEFLATED
        body = zipfile.ZipInfo('data.bin')
        body.compress_type = zipfile.ZIP_DEFLATED
        read = zipfile.ZipInfo('readme.txt')
        read.compress_type = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(filename, 'w') as f:
            f.writestr(body, body_str)
            f.writestr(head, head_str.encode(enc))
            f.writestr(read, README_SAVE_BIN.encode(enc))

    def save_csv(
            self, filename, precision=myokit.DOUBLE_PRECISION, order=None,
            delimiter=',', header=True):
        """
        Writes this ``DataLog`` to a CSV file, following the syntax
        outlined in RFC 4180 and with a header indicating the field names.

        The resulting file will consist of:

          - A header line containing the names of all logged variables,
            separated by commas. If present, the time variable will be the
            first entry on the line. The remaining keys are ordered using a
            natural sort order.
          - Each following line will be a comma separated list of values in the
            same order as the header line. A line is added for each time point
            logged.

        Arguments:

        ``filename``
            The file to write (existing files will be overwritten without
            warning.
        ``precision``
            If a precision argument (for example ``myokit.DOUBLE_PRECISION``)
            is given, the output will be stored in such a way that this amount
            of precision is guaranteed to be present in the string. If the
            precision argument is set to ``None`` python's default formatting
            is used, which may lead to smaller files.
        ``order``
            To specify the ordering of the log's arguments, pass in a sequence
            ``order`` with the log's keys.
        ``delimiter``
            This field can be used to set an alternative delimiter. To use
            spaces set ``delimiter=' '``, for tabs: ``delimiter='\\t'``. Note
            that some delimiters (for example '\\n' or '1234') will produce an
            unreadable or invalid csv file.
        ``header``
            Set this to ``False`` to avoid adding a header to the file. Note
            that Myokit will no longer be able to read the written csv file
            without this header.

        *A note about locale settings*: On Windows systems with a locale
        setting that uses the comma as a decimal separator, importing CSV files
        into Microsoft Excel can be troublesome. To correctly import a CSV,
        either (1) Change your locale settings to use "." as a decimal
        separator or (2) Use the import wizard under Data > Get External Data
        to manually specify the correct separator and delimiter.
        """
        self.validate()

        # Check filename
        filename = os.path.expanduser(filename)

        # Set precision
        if precision is None:
            fmat = lambda x: str(x)
        elif precision == myokit.DOUBLE_PRECISION:
            fmat = lambda x: myokit.SFDOUBLE.format(x)
        elif precision == myokit.SINGLE_PRECISION:
            fmat = lambda x: myokit.SFSINGLE.format(x)
        else:
            raise ValueError('Precision level not supported.')

        # Write file
        # EOL: CSV files have DOS line endings by convention. On windows,
        # writing '\n' to a file opened in mode 'w' will actually write '\r\n'
        # which means writing '\r\n' writes '\r\r\n'. To prevent this, open the
        # file in mode 'wb'.
        eol = '\r\n'
        quote = '"'
        escape = '""'
        with open(filename, 'wb') as f:
            # Convert dict structure to ordered sequences
            if order:
                order = [str(x) for x in order]
                if set(order) != set(self.keys()):
                    raise ValueError(
                        'The given `order` sequence must contain all the same'
                        ' keys present in the log.')
                keys = order
                data = [self[x] for x in keys]
            else:
                keys = []
                data = []
                if self._time and self._time in self.keys():
                    # Save time as first variable
                    dat = self[self._time]
                    keys.append(self._time)
                    data.append(dat)
                for key, dat in sorted(
                        self.items(),
                        key=lambda i: myokit.tools.natural_sort_key(i[0])):
                    if key != self._time:
                        keys.append(key)
                        data.append(dat)

            # Number of entries
            m = len(keys)
            if m == 0:
                return

            # Get length of entries
            n = self.length()

            # Write header
            if header:
                line = []
                for key in keys:
                    # Escape quotes within strings
                    line.append(quote + key.replace(quote, escape) + quote)
                f.write((delimiter.join(line) + eol).encode('ascii'))

            # Write data
            data = [iter(x) for x in data]
            for i in range(0, n):
                line = []
                for d in data:
                    line.append(fmat(next(d)))
                f.write((delimiter.join(line) + eol).encode('ascii'))

    def set_time_key(self, key):
        """
        Sets the key under which the time data is stored.
        """
        self._time = None if key is None else str(key)

    def __setitem__(self, key, value):
        return super(DataLog, self).__setitem__(
            self._parse_key(key), value)

    def split(self, value):
        """
        Splits the log into a part before and after the time ``value``::

            s = myokit.Simulation(m, p)
            d = s.run(1000)
            d1, d2 = d.split(100)

        In this example, d1 will contain all values up to, but not including,
        t=100. While d2 will contain the values from t=100 and upwards.
        """
        return self.isplit(self.find_after(value))

    def split_periodic(self, period, adjust=False, closed_intervals=True):
        """
        Splits this log into multiple logs, each covering an equal period of
        time. For example a log covering the time span ``[0, 10000]`` can be
        split with period ``1000`` to obtain ten logs covering ``[0, 1000]``,
        ``[1000, 2000]`` etc.

        The split log files can be returned as-is, or with the time variable's
        value adjusted so that all logs appear to cover the same span. To
        enable this option, set ``adjust`` to ``True``.

        By default, the returned intervals are *closed*, so both the left and
        right endpoint are included (if present in the data). This may involve
        the duplication of some data points. To disable this behaviour and
        return half-closed endpoints (containing only the left point), set
        ``closed_intervals`` to ``False``.
        """
        # Validate log before starting
        self.validate()

        # Check time variable
        time = self.time()
        if len(time) < 1:
            raise RuntimeError('DataLog entries have zero length.')

        # Check period
        period = float(period)
        if period <= 0:
            raise ValueError('Period must be greater than zero')

        # Get start, end, etc
        tmin = 0    # time[0]
        tmax = time[len(time) - 1]
        nlogs = int(np.ceil((tmax - tmin) / period))

        # No splitting needed? Return clone!
        if nlogs < 2:
            return self.clone()

        # Find split points
        tstarts = tmin + np.arange(nlogs) * period
        istarts = [0] * nlogs
        k = 0
        for i, t in enumerate(time):
            while k < nlogs and t >= tstarts[k]:
                istarts[k] = i
                k += 1

        # Create logs
        logs = []
        for i in range(0, nlogs - 1):
            log = DataLog()
            log._time = self._time

            # Get indices
            imin = istarts[i]
            imax = istarts[i + 1]

            # Include right point endpoint if needed
            if closed_intervals and time[imax] == tstarts[i + 1]:
                imax += 1

            # Select sections of log and append
            for k, v in self.items():
                d = self[k][imin:imax]
                # NumPy? Then copy data
                if isinstance(d, np.ndarray):
                    d = np.array(d, copy=True, dtype=float)
                log[k] = d
            logs.append(log)

        # Last log
        log = DataLog()
        log._time = self._time
        imin = istarts[-1]
        imax = len(time)

        # Not including right endpoints? Then may be required to omit last pt
        if not closed_intervals and time[-1] >= tmin + nlogs * period:
            imax -= 1

        # Select sections of log and append
        for k, v in self.items():
            d = self[k][imin:imax]
            # NumPy? Then copy data
            if isinstance(d, np.ndarray):
                d = np.array(d, copy=True, dtype=float)
            log[k] = d
        logs.append(log)

        # Adjust
        if adjust:
            if isinstance(time, np.ndarray):
                # Fast method for numpy arrays
                for k, log in enumerate(logs):
                    log[self._time] -= k * period
            else:
                for k, log in enumerate(logs):
                    tlist = log[self._time]
                    tdiff = k * period
                    for i in range(len(tlist)):
                        tlist[i] -= tdiff

        # Return
        return logs

    def time(self):
        """
        Returns this log's time array.

        Raises a :class:`myokit.InvalidDataLogError` if the time variable for
        this log has not been specified or an invalid key was given for the
        time variable.
        """
        try:
            return self[self._time]
        except KeyError:
            if self._time is None:
                raise myokit.InvalidDataLogError('No time variable set.')
            else:
                raise myokit.InvalidDataLogError(
                    'Invalid key <' + str(self._time)
                    + '> set for time variable.')

    def time_key(self):
        """
        Returns the name of the time variable stored in this log, or ``None``
        if no time variable was set.
        """
        return self._time

    def trim(self, a, b, adjust=False):
        """
        Returns a copy of this log, with all data before time ``a`` and after
        (and including) time ``b`` removed.

        If ``adjust`` is set to ``True``, all logged times will be lowered by
        ``a``.
        """
        self.validate()
        log = self.itrim(self.find_after(a), self.find_after(b))
        if adjust and self._time in log:
            if isinstance(log[self._time], np.ndarray):
                log[self._time] -= a
            else:
                log[self._time] = [x - a for x in log[self._time]]
        return log

    def trim_left(self, value, adjust=False):
        """
        Returns a copy of this log, with all data before time ``value``
        removed.

        If ``adjust`` is set to ``True``, all logged times will be lowered by
        ``value``.
        """
        self.validate()
        log = self.itrim_left(self.find_after(value))
        if adjust and self._time in log:
            if isinstance(log[self._time], np.ndarray):
                log[self._time] -= value
            else:
                log[self._time] = [x - value for x in log[self._time]]
        return log

    def trim_right(self, value):
        """
        Returns a copy of this log, with all data at times after and including
        ``value`` removed.
        """
        return self.itrim_right(self.find_after(value))

    def validate(self):
        """
        Validates this ``DataLog``. Raises a
        :class:`myokit.InvalidDataLogError` if the log has inconsistencies.
        """
        if self._time:
            if self._time not in self:
                raise myokit.InvalidDataLogError(
                    'Time variable <' + str(self._time)
                    + '> specified but not found in log.')
            dt = np.asarray(self[self._time])
            if np.any(dt[1:] - dt[:-1] < 0):
                raise myokit.InvalidDataLogError(
                    'Time must be non-decreasing.')
        if len(self) > 0:
            n = set([len(v) for v in self.values()])
            if len(n) > 1:
                raise myokit.InvalidDataLogError(
                    'All entries in a data log must have the same length.')

    def variable_info(self):
        """
        Returns a dictionary mapping fully qualified variable names to
        :class:`LoggedvariableInfo` instances, providing information about the
        logged data.

        Comes with the following constraints:

        - Per variable, the data must have a consistent dimensionality. For
          example having a key ``0.membrane.V`` and a key ``1.1.membrane.V``
          would violate this constraint.
        - Per variable, the data must be regular accross dimensions. For
          example if there are ``n`` entries ``0.x.membrane.V``, and there are
          also entries of the form ``1.x.membrane.V`` then the values of ``x``
          must be the same for both cases.

        An example of a dataset that violates the second constraint is::

            0.0.membrane.V
            0.1.membrane.V
            0.2.membrane.V
            1.0.membrane.V
            1.1.membrane.V

        If either of the constraints is violated a ``ValueError`` is raised.
        """
        # The algorithm for condition 2 works by creating a set of the unique
        # entries in each column. The product of the sizes of these sets should
        # equal the total number of entries for a variable.
        # For example:
        #   0 1
        #   0 2     Results in id_sets [(0,1), (1,2,3,4)]
        #   0 3     2 * 4 = 8 != len(id_list)
        #   1 1     So this data must be irregular.
        #   1 2
        #   1 4
        #
        id_lists = {}
        id_sets = {}
        for key in self:
            # Split key into id / name parts
            idx, name = split_key(key)

            # Create tuple version of id
            idx = idx.split('.')
            idx = idx[:-1]
            idx = tuple([int(i) for i in idx])

            # Find or create entry in dict of id lists
            try:
                id_list = id_lists[name]
                id_set = id_sets[name]
            except KeyError:
                # Create entry in id lists dict
                id_lists[name] = id_list = []

                # Create entry in id sets dict (one set for every dimension)
                id_sets[name] = id_set = [set() for x in idx]

            # Check if the dimensions are the same each time a name occurs.
            if id_list and len(id_list[0]) != len(idx):
                key1 = '.'.join([str(x) for x in id_list[0]]) + '.' + name
                key2 = '.'.join([str(x) for x in idx]) + '.' + name
                raise RuntimeError(
                    'Different dimensions used for the same variable. Found: <'
                    + key1 + '> and <' + key2 + '>.')

            # Update the id list
            id_list.append(idx)

            # Update the id set
            for k, i in enumerate(idx):
                id_set[k].add(i)

        # Create variable info objects
        infos = {}
        for name, id_list in id_lists.items():
            id_set = id_sets[name]

            # Check if the data is regular.
            n = len(id_list)
            m = 1
            for x in id_set:
                m *= len(x)

            if n != m:
                raise RuntimeError(
                    'Irregular data used for variable <' + str(name) + '>')

            # Create variable info object
            infos[name] = info = LoggedVariableInfo()
            info._name = name
            info._dimension = len(id_set)
            info._size = tuple([len(x) for x in id_set])

            # Add sorted ids
            if id_list[0]:
                id_list.sort()
            info._ids = id_list

            # Add sorted keys
            s = '.' + name if id_list[0] else name
            info._keys = ['.'.join([str(x) for x in y]) + s for y in id_list]

        return infos


class LoggedVariableInfo(object):
    """
    Contains information about the log entries for each variable. These objects
    should only be created by :meth:`DataLog.variable_info()`.
    """
    def __init__(self):
        self._dimension = None
        self._ids = None
        self._keys = None
        self._size = None
        self._name = None

    def dimension(self):
        """
        Returns the dimensions of the logged data for this variable, as an
        integer.
        """
        return self._dimension

    def ids(self):
        """
        Returns an iterator over all available ids for this variable, such
        that the second index (y in the simulation) changes fastest. For
        example, for log entries::

            0.0.membrane.V
            0.1.membrane.V
            0.2.membrane.V
            1.0.membrane.V
            1.1.membrane.V
            1.2.membrane.V

        the returned result would iterate over::

            [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]

        The keys are returned in the same order as the ids.
        """
        return iter(self._ids)

    def is_regular_grid(self):
        """
        Returns True if the following conditions are met:

        - The data 2 dimensional
        - The data is continuous: along each dimension the first data point is
          indexed as ``0`` and the last as ``Ni-1``, where ``Ni`` is the size
          in that dimension.

        """
        nx, ny = self._size
        return (
            self._dimension == 2
            and self._ids[0][0] == 0
            and self._ids[0][1] == 0
            and self._ids[-1][0] == nx - 1
            and self._ids[-1][1] == ny - 1
        )

    def keys(self):
        """
        Returns an iterator over all available keys for this variable, such
        that the second index (y in the simulation) changes fastest. For
        example, for log entries::

            0.0.membrane.V
            1.0.membrane.V
            0.1.membrane.V
            1.1.membrane.V
            0.2.membrane.V
            1.2.membrane.V

        the returned iterator would produce ``"0.0.membrane.V"``, then
        ``"0.1.membrane.V"`` etc.

        The ids are returned in the same order as the keys.
        """
        return iter(self._keys)

    def size(self):
        """
        Returns a tuple containing the size i.e. the number of entries for
        the corresponding variable in each dimension.

        For example, with the following log entries for `membrane.V`::

            0.membrane.V
            1.membrane.V
            2.membrane.V

        the corresponding size would be ``(3)``.

        A size of ``3`` doesn't guarantee the final entry is for cell number
        ``2``. For example::

            0.membrane.V
            10.membrane.V
            20.membrane.V

        would also return size ``(3)``

        In higher dimensions::

            0.0.membrane.V
            0.1.membrane.V
            0.2.membrane.V
            1.0.membrane.V
            1.1.membrane.V
            1.2.membrane.V

        This would return ``(2,3)``.

        Similarly, in a single cell scenario or for global variables, for
        exmaple::

            engine.time

        Would have size ``()``.
        """
        return self._size

    def name(self):
        """
        Returns the variable name.
        """
        return self._name

    def to_long_string(self):   # pragma: no cover (debug function)
        out = [self._name]
        out.append('  dimension: ' + str(self._dimension))
        out.append('  size: ' + ', '.join([str(x) for x in self._size]))
        out.append('  keys:')
        out.extend(['    ' + x for x in self._keys])
        return '\n'.join(out)


def prepare_log(
        log, model, dims=None, global_vars=None, if_empty=myokit.LOG_NONE,
        allowed_classes=myokit.LOG_ALL, precision=myokit.DOUBLE_PRECISION):
    """
    Returns a :class:`DataLog` for simulation classes based on a ``log``
    argument passed in by the user. The model the simulations will be based on
    should be passed in as ``model``.

    The ``log`` argument can take on one of four forms:

    An existing simulation log
        In this case, the log is tested for compatibility with the given model
        and simulation dimensions. For single-cell simulations all keys in the
        log must correspond to the qname of a loggable variable (IE not a
        constant). For multi-cellular simulations this means all keys in the
        log must have the form "x.component.variable" where "x" is the cell
        index (for example "1" or "0.3").
    A list (or other sequence) of variable names to log.
        In this case, the list is converted to a DataLog object. All
        arguments in the list must be either strings corresponding to the
        variables' qnames (so "membrane.V") or variable objects from the given
        model.
        In multi-cell scenarios, passing in the qname of a variable (for
        example "membrane.V") will cause every cell's instance of this variable
        to be logged. To log only specific cells' values, pass in the indexed
        name (for example "1.2.membrane.V").
    An integer flag
        One of the following integer flags:

        ``myokit.LOG_NONE``
            Don't log any variables.
        ``myokit.LOG_STATE``
            Log all state variables.
        ``myokit.LOG_BOUND``
            Log all variables bound to an external value. The method will
            assume any bound variables still present in the model will be
            provided by the simulation engine.
        ``myokit.LOG_INTER``
            Log all intermediary variables.
        ``myokit.LOG_DERIV``
            Log the derivatives of the state variables.
        ``myokit.LOG_ALL``
            Combines all the previous flags.

        Flags can be chained together, for example
        ``log=myokit.LOG_STATE+myokit.LOG_BOUND`` will log all bound variables
        and all states.
    ``None``
        In this case the value from ``if_empty`` will be copied into log before
        the function proceeds to build a log.

    For multi-dimensional logs the simulation dimensions can be passed in as a
    tuple of dimension sizes, for example (10,) for a cable of 10 cells and
    (30,20) for a 30 by 20 piece of tissue.

    Simulations can define variables to be either `per-cell` or `global`. Time,
    for example, is typically a global variable while membrane potential will
    be stored per cell. To indicate which is which, a list of global variables
    can be passed in as ``global_vars``.

    The argument ``if_empty`` is used to set a default argument if ``log`` is
    is given as ``None``.

    The argument ``allowed_classes`` is an integer flag that determines which
    type of variables are allowed in this log.

    When a new DataLog is created by this method, the internal storage
    uses arrays from the array module. The data type for these new arrays can
    be specified using the ``precision`` argument.
    """
    # Typecode dependent on precision
    # Note: Cast to str() here makes it work with older versions of 2.7.x,
    # where unicode isn't accepted (Python 3 of course doesn't accept bytes)
    typecode = str('d' if precision == myokit.DOUBLE_PRECISION else 'f')

    # Get all options for dimensionality
    if dims is None:
        dims = ()
    ndims = len(dims)
    if ndims == 0:
        dcombos = ['']
    else:
        dcombos = ['.'.join([str(y) for y in x]) + '.' for x in _dimco(*dims)]

    # Check given list of global variables
    if global_vars is None:
        global_vars = []
    else:
        for var in global_vars:
            try:
                v = model.get(var)
            except KeyError:
                raise ValueError(
                    'Unknown variable specified in global_vars <'
                    + str(var) + '>.')
            if v.is_state():
                raise ValueError('State cannot be global variable.')

    # Function to check if variable is allowed (doesn't handle derivatives)
    def check_if_allowed_class(var):
        if var.is_constant():
            raise ValueError(
                'This log does not support constants, got <'
                + str(var) + '>.')
        elif var.is_state():
            if not myokit.LOG_STATE & allowed_classes:
                raise ValueError(
                    'This log does not support state variables, got <'
                    + str(var) + '>.')
        elif var.is_bound():
            if not myokit.LOG_BOUND & allowed_classes:
                raise ValueError(
                    'This log does not support bound variables, got <'
                    + str(var) + '>.')
        elif not myokit.LOG_INTER & allowed_classes:
            raise ValueError(
                'This log does not support intermediary variables, got <'
                + str(var) + '>.')

    #
    # First option, no log argument given, use the "if_empty" option
    #

    if log is None:
        # Check if if_empty matches allowed_classes
        # (AKA test if ``if_empty`` is contained in ``allowed_classes``)
        if if_empty & allowed_classes == if_empty:
            log = if_empty
        else:
            # This one's only for programmers :-)
            raise ValueError(
                'The option given for `if_empty` should be an allowed class.')

    #
    # Second option, log given as integer flag: create a simulation log and
    # return it.
    #

    if type(log) == int:

        # Log argument given as flag
        flag = log
        log = myokit.DataLog()
        if flag == myokit.LOG_ALL:
            flag = allowed_classes

        if myokit.LOG_STATE & flag:

            # Check if allowed
            if not (myokit.LOG_STATE & allowed_classes):
                raise ValueError('This log does not support state variables.')

            # Add states
            for s in model.states():
                name = s.qname()
                for c in dcombos:
                    log[c + name] = array.array(typecode)
            flag -= myokit.LOG_STATE

        if myokit.LOG_BOUND & flag:

            # Check if allowed
            if not (myokit.LOG_BOUND & allowed_classes):
                raise ValueError('This log does not support bound variables.')

            # Add bound variables
            for label, var in model.bindings():
                name = var.qname()
                if name in global_vars:
                    log[name] = array.array(typecode)
                else:
                    for c in dcombos:
                        log[c + name] = array.array(typecode)
            flag -= myokit.LOG_BOUND

        if myokit.LOG_INTER & flag:

            # Check if allowed
            if not (myokit.LOG_INTER & allowed_classes):
                raise ValueError(
                    'This log does not support intermediary variables.')

            # Add intermediary variables
            for var in model.variables(inter=True, deep=True):
                name = var.qname()
                if name in global_vars:
                    log[name] = array.array(typecode)
                else:
                    for c in dcombos:
                        log[c + name] = array.array(typecode)
            flag -= myokit.LOG_INTER

        if myokit.LOG_DERIV & flag:

            # Check if allowed
            if not (myokit.LOG_DERIV & allowed_classes):
                raise ValueError('This log does not support time-derivatives.')

            # Add state derivatives
            for var in model.states():
                name = var.qname()
                for c in dcombos:
                    log['dot(' + c + name + ')'] = array.array(typecode)
            flag -= myokit.LOG_DERIV

        if flag != 0:
            raise ValueError('One or more unknown flags given as log.')

        # Set time variable
        time = model.time().qname()
        if time in log:
            log.set_time_key(time)

        # Return
        return log

    #
    # Third option, a dict or DataLog is given. Test if it's suitable for this
    # simulation.
    #

    if isinstance(log, dict):

        # Ensure it's a DataLog
        if not isinstance(log, myokit.DataLog):
            log = myokit.DataLog(log)

        # Set time variable
        time = model.time().qname()
        if time in log:
            log.set_time_key(time)

        # Ensure the log is valid
        log.validate()

        # Check dict keys
        keys = set(log.keys())
        if len(keys) == 0:
            return log

        for key in keys:
            # Handle derivatives
            deriv = key[0:4] == 'dot(' and key[-1:] == ')'
            if deriv:
                key = key[4:-1]

            # Split of index / name
            kdims, kname = split_key(key)

            # Test name-key
            try:
                var = model.get(kname)
            except KeyError:
                raise ValueError(
                    'Unknown variable <' + str(kname) + '> in log.')

            # Check if in class of allowed variables
            if deriv:
                if not myokit.LOG_DERIV & allowed_classes:
                    raise ValueError(
                        'This log does not support derivatives, got <'
                        + key + '>.')
                if not var.is_state():
                    raise ValueError(
                        'Cannot log time derivative of non-state <'
                        + var.qname() + '>.')
            else:
                check_if_allowed_class(var)

            # Check dimensions
            if kdims:

                # Raise error if global
                if kname in global_vars:
                    raise ValueError(
                        'Cannot specify a cell index for global logging'
                        ' variable <' + str(kname) + '>.')

                # Test dim key
                if kdims not in dcombos:
                    raise ValueError(
                        'Invalid index <' + str(kdims) + '> in log.')

            elif dims:

                # Raise error if non-global variable is used in multi-cell log
                if kname not in global_vars:
                    raise ValueError(
                        'DataLog contains non-indexed entry for'
                        ' cell-specific variable <' + str(kname) + '>.')

        # Check dict values can be appended to
        m = 'append'
        for v in log.values():
            if not (hasattr(v, m) and callable(getattr(v, m))):
                raise ValueError(
                    'Logging dict must map qnames to objects'
                    ' that support the append() method.')

        # Return
        return log

    #
    # Fourth option, a sequence of variable names, either global or local.
    #

    # Check if list interface works
    # If not, then raise exception
    try:
        if len(log) > 0:
            log[0]
    except Exception:
        raise ValueError(
            'Argument `log` has unexpected type. Expecting None, integer flag,'
            ' sequence of names, dict or DataLog.')

    if isinstance(log, basestring):
        raise ValueError(
            'String passed in as `log` argument, should be list'
            ' or other sequence containing strings.')

    # Parse log argument as list
    lst = log
    log = myokit.DataLog()
    checked_knames = set()
    for key in lst:

        # Allow variable objects and LhsExpressions
        if isinstance(key, myokit.Variable):
            key = key.qname()
        elif isinstance(key, myokit.LhsExpression):
            key = str(key)

        # Handle derivatives
        deriv = key[0:4] == 'dot(' and key[-1:] == ')'
        if deriv:
            key = key[4:-1]

        # Split off cell indexes
        kdims, kname = split_key(key)

        # Don't re-test multi-dim vars
        if kname not in checked_knames:

            # Test if name key points to valid variable
            try:
                var = model.get(kname)
            except KeyError:
                raise ValueError(
                    'Unknown variable <' + str(kname) + '> in list.')

            # Check if in class of allowed variables
            if deriv:
                if not myokit.LOG_DERIV & allowed_classes:
                    raise ValueError(
                        'This log does not support derivatives, got <'
                        + key + '>.')

                if not var.is_state():
                    raise ValueError(
                        'Cannot log time derivative of non-state <'
                        + var.qname() + '>.')
            else:
                check_if_allowed_class(var)
            checked_knames.add(kname)

        # Add key to log
        if kdims:

            # Raise error if global
            if kname in global_vars:
                raise ValueError(
                    'Cannot specify a cell index for global logging variable'
                    ' <' + str(kname) + '>.')

            # Test dim key
            if kdims not in dcombos:
                raise ValueError(
                    'Invalid index <' + str(kdims) + '> in list.')

            key = kdims + kname if not deriv else 'dot(' + kdims + kname + ')'
            log[key] = array.array(typecode)

        else:

            if kname in global_vars:
                key = kname if not deriv else 'dot(' + kname + ')'
                log[key] = array.array(typecode)
            else:
                for c in dcombos:
                    key = c + kname if not deriv else 'dot(' + c + kname + ')'
                    log[key] = array.array(typecode)

    # Set time variable
    time = model.time().qname()
    if time in log:
        log.set_time_key(time)

    # Return
    return log


def _dimco(*dims):
    """
    Generates all the combinations of a certain set of integer dimensions. For
    example given ``dims=(2, 3)`` it returns::

        (0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)

    """
    n = len(dims) - 1
    """
    def inner(dims, index, prefix):
        if index == n:
            for i in range(0,dims[index]):
                yield prefix + (i,)
        else:
            for i in range(0,dims[index]):
                prefix2 = prefix + (i, )
                for y in inner(dims, index + 1, prefix2):
                    yield y
    return inner(dims, 0, ())
    """
    def inner(dims, index, postfix):
        if index == 0:
            for i in range(0, dims[index]):
                yield (i,) + postfix
        else:
            for i in range(0, dims[index]):
                postfix2 = (i, ) + postfix
                for y in inner(dims, index - 1, postfix2):
                    yield y
    return inner(dims, n, ())


def split_key(key):
    """
    Splits a log entry name into a cell index part and a variable name part.

    The cell index will be an empty string for 0d entries or global variables.
    For higher dimensional cases it will be the cell index in each dimension,
    followed by a period, for example: ``15.2.``.

    The two parts returned by split_key may always be concatenated to obtain
    the original entry.
    """
    m = ID_NAME_PATTERN.match(key, 0)
    if m:
        return key[:m.end()], key[m.end():]
    else:
        return '', key
