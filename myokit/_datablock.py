#
# Containers for time-series of 1d and 2d rectangular data arrays.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import array
import os
import sys

import myokit

import numpy as np


# Readme file for DataBlock1d binary files
README_SAVE_1D = """
Myokit DataBlock1d Binary File
==============================
This zip file contains simulation data in the form of multiple time series.
Zero-dimensional time series, such as time or a global pace variable are
stored, as well as one-dimensional time series, such as the membrane potential
of a linear sequence of cells, as it varies over time.

This file has the following entries:

header_block1d.txt
------------------
A header file containing the following information (line by line):

  - nt     the number of points in time in each entry
  - nx     the width of each 1d block
  - dtype  the used datatype (either "d" or "f")
  - name   the names of all 0d entries, each on its own line
  - 1      the indication that the 1d entries are starting
  - name   the names of all 1d entries, each on its own line

data.bin
--------
A binary file containing the following data, in the data type specified by the
header, and little-endian:

  - The nt time values
  - All 0d entries
  - All 1d entries, reshaped using numpy order='C'

""".strip()

# Readme file for DataBlock2d binary files
README_SAVE_2D = """
Myokit DataBlock2d Binary File
==============================
This zip file contains simulation data in the form of multiple time series.
Zero-dimensional time series, such as time or a global pace variable are
stored, as well as two-dimensional time series, such as the membrane potential
of a 2d grid of cells, as it varies over time.

This file has the following entries:

header_block2d.txt
------------------
A header file containing the following information (line by line):

  - nt     the number of points in time in each entry
  - ny     the height of each 2d block
  - nx     the width of each 2d block
  - dtype  the used datatype (either "d" or "f")
  - name   the names of all 0d entries, each on its own line
  - 2      the indication that the 2d entries are starting
  - name   the names of all 2d entries, each on its own line

data.bin
--------
A binary file containing the following data, in the data type specified by the
header, and little-endian:

  - The nt time values
  - All 0d entries
  - All 2d entries, reshaped using numpy order='C'

""".strip()

# Encoding used for text portions of zip files
ENC = 'utf-8'


class DataBlock1d:
    """
    Container for time-series of 1d rectangular data arrays.

    Each ``DataBlock1d`` has a fixed width ``w``, and a 0d time series vector
    containing a sequence of ``n`` times.

    One-dimensional time series can be added to the block, provided the data
    also contains ``n`` instances of ``w`` data points. The data should be
    passed in as a numpy array with shape ``(n, w)``.

    Zero-dimensional time series can be added, provided they have length ``n``.

    A "one-dimensional time-series" is a series of equally sized 1d arrays
    (sequences), such that the first corresponds to a time ``t[0]``, the second
    to ``t[1]``, etc. Each array has shape ``(n, w)``.

    A "zero-dimensional time-series" is a series of single values where the
    first corresponds to a time ``t[0]``, the second to ``t[1]``, etc.

    Constructor info:

    ``w``
        Each 1d block should have dimension ``w`` by ``1``.
    ``time``
        A sequence of ``n`` times.
    ``copy``
        By default, a copy of the given time sequence will be stored. To
        prevent this copy, set ``copy=False``.

    """
    def __init__(self, w, time, copy=True):
        # Width
        w = int(w)
        if w < 1:
            raise ValueError('Minimum w is 1.')
        self._nx = w
        # Time
        time = np.array(time, copy=copy)
        if len(time.shape) != 1:
            raise ValueError('Time must be a sequence.')
        if np.any(np.diff(time) < 0):
            raise ValueError('Time must be non-decreasing.')
        self._time = time
        self._nt = len(time)
        # 0d variables
        self._0d = {}
        # 1d variables
        self._1d = {}

    def block2d(self):
        """
        Returns a :class:`myokit.DataBlock2d` based on this 1d data block.
        """
        b = DataBlock2d(self._nx, 1, self._time)
        for k, v in self._0d.items():
            b.set0d(k, v)
        shape = (self._nt, 1, self._nx)
        for k, v in self._1d.items():
            b.set2d(k, v.reshape(shape))
        return b

    def cv(self, name, threshold=-30, length=0.01, time_multiplier=1e-3,
            border=None):
        """
        Calculates conduction velocity (CV) in a cable.

        Accepts the following arguments:

        ``name``
            The name (as string) of the membrane potential variable. This
            should be a 1d variable in this datablock.
        ``threshold``
            The start of an action potential is determined as the first time
            the membrane potential crosses this threshold (default=-30mV) and
            has a positive direction.
        ``length``
            The length of a single cell in cm, in the direction of the cable.
            The default is ``length=0.01cm``.
        ``time_multiplier``
            A multiplier used to convert the used time units to seconds. Most
            simulations use milliseconds, so the default value is 1e-3.
        ``border``
            The number of cells to exclude from the analysis on each end of the
            cable to avoid boundary effects. If not given, 1/3 of the number of
            cells will be used, with a maximum of 50 cells on each side.

        Returns the approximate conduction velocity in cm/s. If no cv can be
        """
        # Check border
        if border is None:
            border = min(50, self._nx // 3)
        else:
            border = int(border)
            if border < 0:
                raise ValueError('The argument `border` cannot be negative.')
            elif border >= self._nx // 2:
                raise ValueError(
                    'The argument `border` must be less than half the number'
                    ' of cells.')

        # Get indices of selected cells
        ilo = border                # First index
        ihi = self._nx - border     # Last index + 1

        # Indices of cells with AP
        i1 = None
        i2 = None

        # Get Vm, reshaped to get each cell's time-series successively.
        v_series = self._1d[name].reshape(self._nt * self._nx, order='F')

        # Split Vm into a series per cell (returns views!)
        v_series = np.split(v_series, self._nx)

        # Find first activation time
        have_crossing = False
        t = []
        for i in range(ilo, ihi):
            v = v_series[i]
            # Get index of first threshold crossing with positive flank
            # Don't include crossings at log index 0
            itime = np.where((v[1:] > -30) & (v[1:] - v[:-1] > 0))[0]
            if len(itime) == 0 or itime[0] == 0:
                # No crossing found
                if have_crossing:
                    # CV calculation ends here
                    i2 = i - 1
                    break
            else:
                # Crossing found!
                if have_crossing:
                    i2 = i
                else:
                    i1 = i
                    have_crossing = True
                itime = 1 + itime[0]
                # Interpolate to get better estimate
                v0 = v[itime - 1]
                v1 = v[itime]
                t0 = self._time[itime - 1]
                t1 = self._time[itime]
                t.append(t0 + (threshold - v0) * (t1 - t0) / (v1 - v0))
        if not have_crossing:
            return 0

        # No propagation: all depolarisations at the same time
        if np.all(t == t[0]):
            return 0

        # Get times in seconds, lengths in cm
        t = np.array(t, copy=False) * time_multiplier
        x = np.arange(i1, 1 + i2, dtype=float) * length

        # Use linear least squares to find the conduction velocity
        A = np.vstack([t, np.ones(len(t))]).T
        try:
            # Newer numpy wants rcond=None
            cv = np.linalg.lstsq(A, x, rcond=None)[0][0]
        except TypeError:   # pragma: no cover
            cv = np.linalg.lstsq(A, x)[0][0]

        # Return
        return cv

    @staticmethod
    def from_DataLog(log):
        """Deprecated alias of :meth:`from_log()`."""
        # Deprecated since 2020-09-14
        import warnings
        warnings.warn(
            'The method `DataBlock1d.from_DataLog` is deprecated. Please use'
            ' `DataBlock1d.from_log` instead.')
        return DataBlock1d.from_log(log)

    @staticmethod
    def from_log(log):
        """
        Creates a DataBlock1d from a :class:`myokit.DataLog`.
        """
        log.validate()

        # Get time variable name
        time = log.time_key()
        if time is None:
            raise ValueError('No time variable set in data log.')

        # Get log info
        infos = log.variable_info()

        # Check time variable
        if time not in infos:
            # Already checked time variable exists, so if not found now must
            # be multi-dimensional
            raise ValueError('Time variable must be 0-dimensional.')

        # Check if everything is 0d or 1d, get size
        size = None
        for name, info in infos.items():
            d = info.dimension()
            if d not in (0, 1):
                raise ValueError(
                    'The given simulation log should only contain 0d or 1d'
                    ' variables. Found <' + str(name) + '> with d = '
                    + str(d) + '.')
            if d == 1:
                if size is None:
                    size = info.size()
                elif info.size() != size:
                    raise ValueError(
                        'The given simulation log contains 1d'
                        ' data sets of different sizes.')

        # Get dimensions
        nt = len(log[time])
        nx = size[0]

        # Create data block
        block = DataBlock1d(nx, log[time], copy=True)
        for name, info in infos.items():
            if info.dimension() == 0:
                # Add 0d time series
                if name == time:
                    continue
                block.set0d(name, log[name], copy=True)

            else:

                # Convert to 1d time series
                data = np.zeros(nt * nx)
                # Iterate over info.keys(), this has the correct order!
                for i, key in enumerate(info.keys()):
                    # Copy data into array (really copies)
                    data[i * nt:(i + 1) * nt] = log[key]
                # Reshape
                data = data.reshape((nt, nx), order='F')
                # If this is a view of existing data, make a copy!
                if data.base is not None:
                    data = np.array(data)
                block.set1d(name, data, copy=False)

        return block

    def get0d(self, name):
        """
        Returns the 0d time-series identified by ``name``. The data is returned
        directly, no copy is made.
        """
        return self._0d[name]

    def get1d(self, name):
        """
        Returns the 1d time-series identified by ``name``. The data is returned
        directly, no copy is made.

        The returned data is a 2d array of the shape given by :meth:`shape`.
        """
        return self._1d[name]

    def grid(self, name, transpose=True):
        """
        Returns a 2d grid representation suitable for plotting color maps or
        contours with ``matplotlib.pyplot`` methods such as ``pcolor`` and
        ``pcolormesh``.

        When used for example with
        ``pyplot.pcolormesh(*block.grid('membrane.V'))`` this will create a 2d
        plot where the horizontal axis shows time and the vertical axis shows
        the cell index.

        Arguments:

        ``name``
            The name identifying the 1d data-values to return.
        ``transpose``
            By default (``transpose=True``) the data is returned so that ``x``
            represents time and ``y`` represents space. To reverse this (and
            use the order used internally in the datablocks), set
            ``transpose=False``.

        The returned format is a tuple ``(x, y, z)`` where ``x``, ``y`` and
        ``z`` are all 2d numpy arrays.
        Here, ``x`` (time) and ``y`` (space) describe the x and y-coordinates
        of rectangles, with a color (data value) given by ``z``.

        In particular, each rectangle ``(x[i, j], y[i, j])``,
        ``(x[i + 1, j], y[i + 1, j])``, ``(x[i, j + 1], y[i, j + 1])``,
        ``(x[i + 1,j + 1], y[i + 1,j + 1])``, has a color given by ``z[i, j]``.

        As a result, for a block of width ``w`` (e.g., ``w`` cells) containing
        ``n`` logged time points, the method returns arrays ``x`` and ``y`` of
        shape ``(w + 1, n + 1)`` and an array ``z`` of shape ``(w, n)``.

        See :meth:`image_grid()` for a method where ``x``, ``y`` and ``z`` all
        have shape ``(w, n)``.
        """
        # Append point in time at pos [-1] + ([-1] - [-2])
        ts = np.append(self._time, 2 * self._time[-1] - self._time[-2])
        # Append one extra cell or node
        xs = np.arange(0, self._nx + 1)
        # Make grid
        return self._grid(ts, xs, self._1d[name], transpose)

    def image_grid(self, name, transpose=True):
        """
        Returns a 2d grid representation of the data.

        The returned format is a tuple ``(x, y, z)`` where ``x``, ``y`` and
        ``z`` are all 2d numpy arrays.
        Here, ``x`` and ``y`` describe the time and space-coordinates of the
        logged points respectively, and ``z`` describes the corresponding data
        value.
        For a block of width ``w`` (e.g., ``w`` cells) containing ``n`` logged
        time points, each returned array has the shape ``(w, n)``.

        Arguments:

        ``name``
            The name identifying the 1d data-values to return.
        ``transpose``
            By default, the data is transposed so that the ``x`` coordinates
            become time and the ``y`` coordinates become space. Use
            ``transpose=False`` to return untransposed results.

        """
        return self._grid(
            self._time, np.arange(0, self._nx), self._1d[name], transpose)

    def _grid(self, ts, xs, vs, transpose):
        """
        Make a grid for the given times, spatial coordinates and data values.
        """
        if transpose:
            x, y = np.meshgrid(ts, xs)
            z = np.reshape(vs, (self._nx * self._nt,), order='F')
            z = np.reshape(z, (self._nx, self._nt), order='C')
        else:
            x, y = np.meshgrid(xs, ts)
            z = np.reshape(vs, (self._nx * self._nt,), order='C')
            z = np.reshape(z, (self._nt, self._nx), order='C')
        # If z is a view, create a copy
        if z.base is not None:
            z = np.array(z, copy=True)
        return x, y, z

    def keys0d(self):
        """
        Returns an iterator over this block's 0d time series.
        """
        return iter(self._0d)

    def keys1d(self):
        """
        Returns an iterator over this block's 1d time series.
        """
        return iter(self._1d)

    def len0d(self):
        """
        Returns the number of 0d time series in this block.
        """
        return len(self._0d)

    def len1d(self):
        """
        Returns the number of 1d time series in this block.
        """
        return len(self._1d)

    @staticmethod
    def load(filename, progress=None, msg='Loading DataBlock1d'):
        """
        Loads a :class:`DataBlock1d` from the specified file.

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as `msg`.
        """
        filename = os.path.expanduser(filename)

        # Load compression modules
        import zipfile
        try:
            import zlib
            del zlib
        except ImportError:
            raise Exception(
                'This method requires the ``zlib`` module to be installed.')

        # Get size of single and double types on this machine
        dsize = {
            'd': len(array.array('d', [1]).tobytes()),
            'f': len(array.array('f', [1]).tobytes()),
        }

        # Read data from file
        try:
            f = None
            f = zipfile.ZipFile(filename, 'r')
            info = f.infolist()
            if len(info) < 3:
                raise myokit.DataBlockReadError(
                    'Invalid DataBlock1d file format: Not enough files in'
                    ' zip.')

            # Get ZipInfo objects
            names = [x.filename for x in info]
            try:
                head = names.index('header_block1d.txt')
            except ValueError:
                raise myokit.DataBlockReadError(
                    'Invalid DataBlock1d file format: Header not found.')
            try:
                body = names.index('data.bin')
            except ValueError:
                raise myokit.DataBlockReadError(
                    'Invalid DataBlock1d file format: Data not found.')

            # Read head and body into memory (let's assume it fits...)
            head = f.read(info[head]).decode(ENC)
            body = f.read(info[body])

        except zipfile.BadZipfile:
            raise myokit.DataBlockReadError(
                'Unable to read DataBlock1d: Bad zip file.')

        except zipfile.LargeZipFile:    # pragma: no cover
            raise myokit.DataBlockReadError(
                'Unable to read DataBlock1d: Zip file requires zip64 support'
                ' and this has not been enabled on this system.')

        finally:
            if f:
                f.close()

        # Parse head
        head = head.splitlines()
        try:
            if progress:
                progress.enter(msg)

                # Avoid divide by zero
                fraction = float(len(head) - 3)
                if fraction > 0:
                    fraction = 1.0 / fraction
                iprogress = 0
                progress.update(iprogress * fraction)
            head = iter(head)
            nt = int(next(head))
            nx = int(next(head))
            dtype = next(head)[1:-1]
            if dtype not in dsize:
                raise myokit.DataBlockReadError(
                    'Unable to read DataBlock1d: Unrecognized data type "'
                    + dtype + '".')
            names_0d = []
            names_1d = []
            name = next(head)
            while name != '1':
                names_0d.append(name[1:-1])
                name = next(head)
            for name in head:
                names_1d.append(name[1:-1])
            del head

            # Parse body
            start, end = 0, 0
            n0 = dsize[dtype] * nt
            n1 = n0 * nx
            nb = len(body)

            # Read time
            end += n0
            if end > nb:
                raise myokit.DataBlockReadError(
                    'Unable to read DataBlock1d: Header indicates larger data'
                    ' than found in the body.')
            data = array.array(dtype)
            data.frombytes(body[start:end])
            if sys.byteorder == 'big':  # pragma: no cover
                data.byteswap()
            data = np.array(data)
            if progress:
                iprogress += 1
                if not progress.update(iprogress * fraction):
                    return

            # Create data block
            block = DataBlock1d(nx, data, copy=False)

            # Read 0d data
            for name in names_0d:
                start = end
                end += n0
                if end > nb:
                    raise myokit.DataBlockReadError(
                        'Unable to read DataBlock1d: Header indicates larger'
                        ' data than found in the body.')
                data = array.array(dtype)
                data.frombytes(body[start:end])
                if sys.byteorder == 'big':  # pragma: no cover
                    data.byteswap()
                data = np.array(data)
                block.set0d(name, data, copy=False)
                if progress:
                    iprogress += 1
                    if not progress.update(iprogress * fraction):
                        return

            # Read 1d data
            for name in names_1d:
                start = end
                end += n1
                if end > nb:
                    raise myokit.DataBlockReadError(
                        'Unable to read DataBlock1d: Header indicates larger'
                        ' data than found in the body.')
                data = array.array(dtype)
                data.frombytes(body[start:end])
                if sys.byteorder == 'big':  # pragma: no cover
                    data.byteswap()
                data = np.array(data).reshape(nt, nx, order='C')
                block.set1d(name, data, copy=False)
                if progress:
                    iprogress += 1
                    if not progress.update(iprogress * fraction):
                        return
            return block
        finally:
            if progress:
                progress.exit()

    def remove0d(self, name):
        """Removes the 0d time-series identified by ``name``."""
        del self._0d[name]

    def remove1d(self, name):
        """Removes the 1d time-series identified by ``name``."""
        del self._1d[name]

    def save(self, filename):
        """
        Writes this ``DataBlock1d`` to a binary file.

        The resulting file will be a zip file with the following entries:

        ``header_block1d.txt``: A header file containing the following
        information (line by line):

        - ``nt`` the number of points in time in each entry
        - ``nx`` the length of each 1d block
        - ``"dtype"`` the used datatype (either "d" or "f")
        - ``"name"`` the names of all 0d entries, each on its own line
        - ``1`` the indication that the 1d entries are starting
        - ``"name"`` the names of all 1d entries, each on its own line

        ``data.bin``: A binary file containing the following data, in the data
        type specified by the header, and little-endian:

        - The ``nt`` time values
        - All 0d entries
        - All 1d entries, reshaped using numpy order='C'

        """
        # Check filename
        filename = os.path.expanduser(filename)
        # Load compression modules
        import zipfile
        try:
            import zlib
            del zlib
        except ImportError:
            raise Exception(
                'This method requires the ``zlib`` module to be installed.')

        # Data type
        dtype = 'd'     # Only supporting doubles right now

        # Create header
        head_str = []
        head_str.append(str(self._nt))
        head_str.append(str(self._nx))
        head_str.append('"' + dtype + '"')
        for name in self._0d:
            head_str.append('"' + name + '"')
        head_str.append(str(1))
        for name in self._1d:
            head_str.append('"' + name + '"')
        head_str = '\n'.join(head_str)

        # Create body
        n = self._nt * self._nx
        body_str = []
        body_str.append(array.array(dtype, self._time))
        for name, data in self._0d.items():
            body_str.append(array.array(dtype, data))
        for name, data in self._1d.items():
            body_str.append(array.array(dtype, data.reshape(n, order='C')))
        if sys.byteorder == 'big':  # pragma: no cover
            for ar in body_str:
                ar.byteswap()
        body_str = b''.join([ar.tobytes() for ar in body_str])

        # Write
        head = zipfile.ZipInfo('header_block1d.txt')
        head.compress_type = zipfile.ZIP_DEFLATED
        body = zipfile.ZipInfo('data.bin')
        body.compress_type = zipfile.ZIP_DEFLATED
        read = zipfile.ZipInfo('readme.txt')
        read.compress_type = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(filename, 'w') as f:
            f.writestr(head, head_str.encode(ENC))
            f.writestr(body, body_str)
            f.writestr(read, README_SAVE_1D.encode(ENC))

    def set0d(self, name, data, copy=True):
        """
        Adds or updates a zero-dimensional time series ``data`` for the
        variable named by the string ``name``.

        The ``data`` must be specified as a sequence of length ``n``, where
        ``n`` is the first value returned by :meth:`DataBlock1d.shape()`.

        By default, a copy of the given data will be stored. To prevent this
        and store a reference instead, set ``copy=False``.
        """
        name = str(name)
        if not name:
            raise ValueError('Name cannot be empty.')
        data = np.array(data, copy=copy)
        if data.shape != (self._nt,):
            raise ValueError(
                'Data must be sequence of length ' + str(self._nt) + '.')
        self._0d[name] = data

    def set1d(self, name, data, copy=True):
        """
        Adds or updates a one-dimensional time series ``data`` for the variable
        named by the string ``name``.

        The ``data`` must be specified as a numpy array with shape ``(n, w)``,
        where ``(n, w)`` is the value returned by :meth:`DataBlock1d.shape()`.

        By default, a copy of the given data will be stored. To prevent this
        and store a reference instead, set ``copy=False``.
        """
        name = str(name)
        if not name:
            raise ValueError('Name cannot be empty.')
        data = np.array(data, copy=copy)
        shape = (self._nt, self._nx)
        if data.shape != shape:
            raise ValueError('Data must have shape ' + str(shape) + '.')
        self._1d[name] = data

    def shape(self):
        """
        Returns the required shape for 1d data passed to this data block. Zero
        dimensional series passed in must have length ``shape()[0]``.
        """
        return (self._nt, self._nx)

    def time(self):
        """
        Returns the time data for this datablock. The data is returned
        directly, no copy is made.
        """
        return self._time

    def to_log(self, copy=True):
        """
        Returns a :class:`myokit.DataLog` containing the same information as
        this block.

        The data will be copied, unless ``copy`` is set to ``False``.
        """
        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = np.array(self._time, copy=copy)
        for k, v in self._0d.items():
            d[k] = np.array(v, copy=copy)
        for k, v in self._1d.items():
            for i in range(self._nx):
                d[str(i) + '.' + k] = np.array(v[:, i], copy=copy)
        return d

    def trace(self, variable, x):
        """
        Returns a 0d time series of the value ``variable``, corresponding to
        the cell at position ``x``. The data is returned directly, no copy is
        made.
        """
        return self._1d[variable][:, x]


class DataBlock2d:
    """
    Container for time-series of 2d rectangular data arrays.

    Each ``DataBlock2d`` has a fixed width ``w`` and height ``h``, and a 0d
    time series vector containing a sequence of ``n`` times.

    Two-dimensional time series can be added to the block, provided the data
    also contains ``n`` instances of ``w`` by ``h`` data points. The
    data should be passed in as a numpy array with shape ``(n, h, w)``.

    Zero-dimensional time series can be added, provided they have length ``n``.

    A "two-dimensional time-series" is a series of equally sized 2d arrays
    (sequences), such that the first corresponds to a time ``t[0]``, the second
    to ``t[1]``, etc.

    A "zero-dimensional time-series" is a series of single values where the
    first corresponds to a time ``t[0]``, the second to ``t[1]``, etc.

    Constructor info:

    ``w``
        The width of a 2d block. Each block should have shape (n, h, w)
    ``h``
        The height of a 2d block. Each block should have shape (n, h, w)
    ``time``
        A sequence of ``n`` times.
    ``copy``
        By default, a copy of the given time sequence will be stored. To
        prevent this copy, set ``copy=False``.

    """
    def __init__(self, w, h, time, copy=True):
        # Width and height
        w, h = int(w), int(h)
        if w < 1:
            raise ValueError('Minimum width is 1.')
        if h < 1:
            raise ValueError('Minimum height is 1.')
        self._ny = h
        self._nx = w
        # Time
        time = np.array(time, copy=copy)
        if len(time.shape) != 1:
            raise ValueError('Time must be a sequence.')
        if not np.all(np.diff(time) >= 0):
            raise ValueError('Time must be non-decreasing.')
        self._time = time
        self._nt = len(time)
        # 0d variables
        self._0d = {}
        # 2d variables
        self._2d = {}

    def colors(self, name, colormap='traditional', lower=None, upper=None,
               multiplier=1):
        """
        Converts the 2d series indicated by ``name`` into a list of ``W*H*RGB``
        arrays, with each entry represented as an 8 bit unsigned integer.

        Arguments:

        ``name``
            The 2d variable to create arrays for.
        ``colormap``
            The colormap to use when converting to RGB.
        ``lower``
            An optional lower bound on the data (anything below this will
            become the lowest index in the colormap).
        ``upper``
            An optional upper bound on the data (anything above this will
            become the highest index in the colormap).
        ``multiplier``
            An optional integer greater than zero. If given, every point in the
            data set will be represented as a square of ``multiplier`` by
            ``multiplier`` pixels.

        """
        data = self._2d[name]
        # Get color map
        color_map = ColorMap.get(colormap)
        # Get lower and upper bounds for colormap scaling
        lower = np.min(data) if lower is None else float(lower)
        upper = np.max(data) if upper is None else float(upper)
        # Get multiplier
        multiplier = int(multiplier) if multiplier > 1 else 1
        # Create images
        frames = []
        for frame in data:
            # Convert 2d array into row-strided array
            frame = frame.reshape(self._ny * self._nx, order='C')
            # Apply colormap
            frame = color_map(
                frame, lower=lower, upper=upper, alpha=False, rgb=True)
            # Reshape to nx * ny * 3 color array
            frame = frame.reshape((self._ny, self._nx, 3))
            # Grow
            if multiplier > 1:
                frame = frame.repeat(multiplier, axis=0)
                frame = frame.repeat(multiplier, axis=1)
            # Append to list
            frames.append(frame)
        return frames

    @staticmethod
    def combine(block1, block2, map2d, map0d=None, pos1=None, pos2=None):
        """
        Combines two blocks, containing information about different areas, into
        a single :class:`DataBlock2d`.

        Both blocks must contain data from the same points in time.

        A mapping from old to new variables must be passed in as a dictionary
        ``map2d``. The blocks can have different sizes but must have the same
        time vector. If any empty space is created it is padded with a value
        taken from one of the data blocks or a padding value specified as part
        of ``map2d``.

        Positions for the datablocks can be specified as ``pos1`` and ``pos2``,
        the new datablock will have indices ranging from ``(0, 0)`` to
        ``(max(pos1[0] + w1, pos2[0] + w2), max(pos1[0] + w1, pos2[0] + w2))``,
        where ``w1`` and ``w2`` are the widths of ``block1`` and ``block2``
        respectively. Negative indices are not supported and the blocks are not
        allowed to overlap.

        Arguments:

        ``block1``
            The first DataBlock2d
        ``block2``
            The second DataBlock2d. This must have the same time vector as the
            first.
        ``map2d``
            A dictionary object showing how to map 2d variables from both
            blocks into the newly created datablock. The format must be:
            ``new_name : (old_name_1, old_name_2, padding_value)``. Here,
            ``new_name`` is the name of the new 2d variable, ``old_name_1`` is
            the name of a 2d variable in ``block1``, ``old_name_2`` is the name
            of a 2d variable in ``block2`` and ``padding_value`` is an optional
            value indicating the value to use for undefined spaces in the new
            block.
        ``map0d=None``,
            A dictionary object showing how to map 0d variables from both
            blocks into the newly created datablock. Each entry must take the
            format: ``new_name : (old_name_1, None)`` or
            ``new_name : (None, old_name_2)``.
        ``pos1=None``
            Optional value indicating the position ``(x, y)`` of the first
            datablock. By default ``(0, 0)`` is used.
        ``pos2=None``
            Optional value indicating the position ``(x, y)`` of the first
            datablock. By default ``(w1, 0)`` is used, where ``w1`` is the
            width of ``block1``.

        """
        # Check time vector
        time = block1.time()
        if not np.allclose(time, block2.time()):
            raise ValueError(
                'Both datablocks must contain data from the same points in'
                ' time.')

        # Check indices
        nt, h1, w1 = block1.shape()
        nt, h2, w2 = block2.shape()

        if pos1:
            x1, y1 = [int(i) for i in pos1]
            if x1 < 0 or y1 < 0:
                raise ValueError(
                    'Negative indices not supported: pos1=('
                    + str(x1) + ', ' + str(y1) + ').')
        else:
            x1, y1 = 0, 0

        if pos2:
            x2, y2 = [int(i) for i in pos2]
            if x2 < 0 or y2 < 0:
                raise ValueError(
                    'Negative indices not supported: pos2=('
                    + str(x2) + ', ' + str(y2) + ').')
        else:
            x2, y2 = x1 + w1, 0

        # Check for overlap
        if not (x1 >= x2 + w2 or x2 >= x1 + w1
                or y1 >= y2 + h2 or y2 >= y1 + h2):
            raise ValueError('The two data blocks indices cannot overlap.')

        # Create new datablock
        nx = max(x1 + w1, x2 + w2)
        ny = max(y1 + h1, y2 + h2)
        block = DataBlock2d(nx, ny, time, copy=True)

        # Enter 0d data
        if map0d:
            for name, old in map0d.items():
                if old[0] is None:
                    b = block2
                    n = old[1]
                elif old[1] is None:
                    b = block1
                    n = old[0]
                else:
                    raise ValueError(
                        'The dictionary map0d must map the names of new 0d'
                        ' entries to a tuple (a, b) where either a or b must'
                        ' be None.')
                block.set0d(name, b.get0d(n))

        # Enter 2d data
        for name, source in map2d.items():
            # Get data sources
            name1, name2 = source[0], source[1]
            source1 = block1.get2d(name1)
            source2 = block2.get2d(name2)

            # Get padding value
            try:
                pad = float(source[2])
            except IndexError:
                # Get lowest value
                pad = min(np.min(source1), np.min(source2))

            # Create new data field
            field = pad * np.ones((nt, ny, nx))
            field[:, y1:y1 + h1, x1:x1 + w1] = source1
            field[:, y2:y2 + h2, x2:x2 + w2] = source2
            block.set2d(name, field)

        # Return new block
        return block

    def dominant_eigenvalues(self, name):
        """
        Takes the 2d data specified by ``name`` and computes the dominant
        eigenvalue for each point in time (this only works for datablocks with
        a square 2d grid).

        The "dominant eigenvalue" is defined as the eigenvalue with the largest
        magnitude (``sqrt(a + bi)``).

        The returned data is a 1d numpy array.
        """
        if self._nx != self._ny:
            raise Exception(
                'Eigenvalues can only be determined for square data blocks.')
        data = self._2d[name]
        dominants = []
        for t in range(self._nt):
            e = np.linalg.eigvals(data[t])
            dominants.append(e[np.argmax(np.absolute(e))])
        return np.array(dominants)

    def eigenvalues(self, name):
        """
        Takes the 2d data specified as ``name`` and computes the eigenvalues of
        its data matrix at every point in time (this only works for datablocks
        with a square 2d grid).

        The returned data is a 2d numpy array where the first axis is time and
        the second axis is the index of each eigenvalue.
        """
        if self._nx != self._ny:
            raise Exception(
                'Eigenvalues can only be determined for square data blocks.')
        data = self._2d[name]
        eigenvalues = []
        for t in range(self._nt):
            eigenvalues.append(np.linalg.eigvals(data[t]))
        return np.array(eigenvalues)

    @staticmethod
    def from_DataLog(log):
        """Deprecated alias of :meth:`from_log()`."""
        # Deprecated since 2020-09-14
        import warnings
        warnings.warn(
            'The method `DataBlock2d.from_DataLog` is deprecated. Please use'
            ' `DataBlock2d.from_log` instead.')
        return DataBlock2d.from_log(log)

    @staticmethod
    def from_log(log):
        """
        Creates a DataBlock2d from a :class:`myokit.DataLog`.
        """
        log.validate()

        # Get time variable name
        time = log.time_key()
        if time is None:
            raise ValueError('No time variable set in data log.')

        # Get log info
        infos = log.variable_info()

        # Check time variable
        if time not in infos:
            # Already checked time variable exists, so if not found now must
            # be multi-dimensional
            raise ValueError('Time variable must be 0-dimensional.')

        # Check if everything is 0d or 2d, get size
        size = None
        for name, info in infos.items():
            d = info.dimension()
            if d not in (0, 2):
                raise ValueError(
                    'The given simulation log should only contain 0d or 2d'
                    ' variables. Found <' + str(name) + '> with d = '
                    + str(d) + '.')
            if d == 2:
                if size is None:
                    size = info.size()
                elif info.size() != size:
                    raise ValueError(
                        'The given simulation log contains 2d data sets of'
                        ' different sizes.')
        # Get dimensions
        nt = len(log[time])
        nx, ny = size
        # Create data block
        block = DataBlock2d(nx, ny, log[time], copy=True)
        for name, info in infos.items():
            if info.dimension() == 0:
                # Add 0d time series
                if name == time:
                    continue
                block.set0d(name, log[name], copy=True)
            else:
                # Convert to 2d time series
                data = np.zeros(nt * ny * nx)
                # Iterate over info.keys()
                for i, key in enumerate(info.keys()):
                    # Copy data into array (really copies)
                    data[i * nt:(i + 1) * nt] = log[key]
                # Reshape
                data = data.reshape((nt, ny, nx), order='F')
                # If this is a view of existing data, make a copy!
                if data.base is not None:
                    data = np.array(data)
                block.set2d(name, data, copy=False)
        return block

    def get0d(self, name):
        """
        Returns the 0d time-series identified by ``name``. The data is returned
        directly, no copy is made.
        """
        return self._0d[name]

    def get2d(self, name):
        """
        Returns the 2d time-series identified by ``name``. The data is returned
        directly, no copy is made.
        """
        return self._2d[name]

    def images(self, name, colormap='traditional', lower=None, upper=None):
        """
        Converts the 2d series indicated by ``name`` into a list of 1d arrays
        in a row-strided image format ``ARGB32``.
        """
        data = self._2d[name]
        # Get color map
        color_map = ColorMap.get(colormap)

        # Get lower and upper bounds for colormap scaling
        lower = np.min(data) if lower is None else float(lower)
        upper = np.max(data) if upper is None else float(upper)
        if upper < lower:  # pragma: no cover
            upper = lower

        # Create images
        frames = []
        for frame in data:
            # Convert 2d array into row-strided array
            frame = frame.reshape(self._ny * self._nx, order='C')
            frames.append(color_map(frame, lower=lower, upper=upper))
        return frames

    def is_square(self):
        """
        Returns True if this data block's grid is square.
        """
        return self._nx == self._ny

    def items0d(self):
        """
        Returns an iterator over ``(name, value)`` pairs for the 0d series
        stored in this block. The given values are references! No copy of the
        data is made.
        """
        return self._0d.items()

    def items2d(self):
        """
        Returns an iterator over ``(name, value)`` pairs for the 2d series
        stored in this block. The given values are references! No copy of the
        data is made.
        """
        return self._2d.items()

    def keys0d(self):
        """
        Returns an iterator over this block's 0d time series.
        """
        return iter(self._0d)

    def keys2d(self):
        """
        Returns an iterator over this block's 2d time series.
        """
        return iter(self._2d)

    def largest_eigenvalues(self, name):
        """
        Takes the 2d data specified by ``name`` and computes the largest
        eigenvalue for each point in time (this only works for datablocks with
        a square 2d grid).

        The "largest eigenvalue" is defined as the eigenvalue with the most
        positive real part. Note that the returned values may be complex.

        The returned data is a 1d numpy array.
        """
        if self._nx != self._ny:
            raise Exception(
                'Eigenvalues can only be determined for square data blocks.')
        data = self._2d[name]
        largest = []
        for t in range(self._nt):
            e = np.linalg.eigvals(data[t])
            largest.append(e[np.argmax(np.real(e))])
        return np.array(largest)

    def len0d(self):
        """
        Returns the number of 0d time series in this block.
        """
        return len(self._0d)

    def len2d(self):
        """
        Returns the number of 2d time series in this block.
        """
        return len(self._2d)

    @staticmethod
    def load(filename, progress=None, msg='Loading DataBlock2d'):
        """
        Loads a :class:`DataBlock2d` from the specified file.

        To obtain feedback on the simulation progress, an object implementing
        the :class:`myokit.ProgressReporter` interface can be passed in.
        passed in as ``progress``. An optional description of the current
        simulation to use in the ProgressReporter can be passed in as `msg`.

        If the given file contains a :class:`DataBlock1d` this is read and
        converted to a 2d block without warning.
        """
        filename = os.path.expanduser(filename)

        # Load compression modules
        import zipfile
        try:
            import zlib
            del zlib
        except ImportError:
            raise Exception(
                'This method requires the ``zlib`` module to be installed.')

        # Get size of single and double types on this machine
        dsize = {
            'd': len(array.array('d', [1]).tobytes()),
            'f': len(array.array('f', [1]).tobytes()),
        }

        # Read data from file
        try:
            f = None
            f = zipfile.ZipFile(filename, 'r')
            info = f.infolist()
            if len(info) < 3:
                raise myokit.DataBlockReadError(
                    'Invalid DataBlock2d file format: Not enough files in'
                    ' zip.')

            # Get ZipInfo objects
            names = [x.filename for x in info]
            try:
                head = names.index('header_block2d.txt')
            except ValueError:
                # Attempt reading as DataBlock1d
                try:
                    names.index('header_block1d.txt')
                except ValueError:
                    raise myokit.DataBlockReadError(
                        'Invalid DataBlock2d file format: Header not found.')

                # It's a DataBlock1d, attempt reading as such
                f.close()
                block1d = DataBlock1d.load(filename, progress, msg)
                return None if block1d is None else block1d.block2d()

            try:
                body = names.index('data.bin')
            except ValueError:
                raise myokit.DataBlockReadError(
                    'Invalid DataBlock2d file format: Data not found.')

            # Read head and body into memory (let's assume it fits...)
            head = f.read(info[head]).decode(ENC)
            body = f.read(info[body])

        except zipfile.BadZipfile:
            raise myokit.DataBlockReadError(
                'Unable to read DataBlock2d: Bad zip file.')

        except zipfile.LargeZipFile:    # pragma: no cover
            raise myokit.DataBlockReadError(
                'Unable to read DataBlock2d: zip file requires zip64 support'
                ' and this has not been enabled on this system.')

        finally:
            if f:
                f.close()

        # Parse head
        head = head.splitlines()
        try:
            if progress:
                progress.enter(msg)
                # Avoid divide by zero
                fraction = float(len(head) - 4)
                if fraction > 0:
                    fraction = 1.0 / fraction
                iprogress = 0
                progress.update(iprogress * fraction)
            head = iter(head)
            nt = int(next(head))
            ny = int(next(head))
            nx = int(next(head))

            # Get dtype
            dtype = next(head)[1:-1]
            if dtype not in dsize:
                raise myokit.DataBlockReadError(
                    'Unable to read DataBlock2d: Unrecognized data type "'
                    + str(dtype) + '".')

            names_0d = []
            names_2d = []
            name = next(head)
            while name != '2':
                names_0d.append(name[1:-1])
                name = next(head)
            for name in head:
                names_2d.append(name[1:-1])
            del head

            # Parse body
            start, end = 0, 0
            n0 = dsize[dtype] * nt
            n2 = n0 * ny * nx
            nb = len(body)

            # Read time
            end += n0
            if end > nb:
                raise myokit.DataBlockReadError(
                    'Unable to read DataBlock2d: Header indicates larger data'
                    ' than found in the body.')

            data = array.array(dtype)
            data.frombytes(body[start:end])
            if sys.byteorder == 'big':  # pragma: no cover
                data.byteswap()
            data = np.array(data)
            if progress:
                iprogress += 1
                if not progress.update(iprogress * fraction):
                    return

            # Create data block
            block = DataBlock2d(nx, ny, data, copy=False)

            # Read 0d data
            for name in names_0d:
                start = end
                end += n0
                if end > nb:
                    raise myokit.DataBlockReadError(
                        'Unable to read DataBlock2d: Header indicates larger'
                        ' data than found in the body.')
                data = array.array(dtype)
                data.frombytes(body[start:end])
                if sys.byteorder == 'big':  # pragma: no cover
                    data.byteswap()
                data = np.array(data)
                block.set0d(name, data, copy=False)
                if progress:
                    iprogress += 1
                    if not progress.update(iprogress * fraction):
                        return

            # Read 2d data
            for name in names_2d:
                start = end
                end += n2
                if end > nb:
                    raise myokit.DataBlockReadError(
                        'Unable to read DataBlock2d: Header indicates larger'
                        ' data than found in the body.')
                data = array.array(dtype)
                data.frombytes(body[start:end])
                if sys.byteorder == 'big':  # pragma: no cover
                    data.byteswap()
                data = np.array(data).reshape(nt, ny, nx, order='C')
                block.set2d(name, data, copy=False)
                if progress:
                    iprogress += 1
                    if not progress.update(iprogress * fraction):
                        return
            return block

        finally:

            if progress:
                progress.exit()

    def remove0d(self, name):
        """Removes the 0d time-series identified by ``name``."""
        del self._0d[name]

    def remove2d(self, name):
        """Removes the 2d time-series identified by ``name``."""
        del self._2d[name]

    def save(self, filename):
        """
        Writes this ``DataBlock2d`` to a binary file.

        The resulting file will be a zip file with the following entries:

        ``header_block2d.txt``: A header file containing the following
        information (line by line):

        - ``nt`` the number of points in time in each entry
        - ``ny`` the height of each 2d block
        - ``nx`` the width of each 2d block
        - ``"dtype"`` the used datatype (either "d" or "f")
        - ``"name"`` the names of all 0d entries, each on its own line
        - ``2`` the indication that the 2d entries are starting
        - ``"name"`` the names of all 2d entries, each on its own line

        ``data.bin``: A binary file containing the following data, in the data
        type specified by the header, and little-endian:

        - The ``nt`` time values
        - All 0d entries
        - All 2d entries, reshaped using numpy order='C'

        """
        # Check filename
        filename = os.path.expanduser(filename)

        # Load compression modules
        import zipfile
        try:
            # Check zlib is available
            import zlib
            del zlib
        except ImportError:
            raise Exception(
                'This method requires the ``zlib`` module to be installed.')

        # Data type
        dtype = 'd'     # Only supporting doubles right now

        # Create header
        head_str = []
        head_str.append(str(self._nt))
        head_str.append(str(self._ny))
        head_str.append(str(self._nx))
        head_str.append('"' + dtype + '"')
        for name in self._0d:
            head_str.append('"' + name + '"')
        head_str.append(str(2))
        for name in self._2d:
            head_str.append('"' + name + '"')
        head_str = '\n'.join(head_str)

        # Create body
        n = self._nt * self._ny * self._nx
        body_str = []
        body_str.append(array.array(dtype, self._time))
        for name, data in self._0d.items():
            body_str.append(array.array(dtype, data))
        for name, data in self._2d.items():
            body_str.append(array.array(dtype, data.reshape(n, order='C')))
        if sys.byteorder == 'big':  # pragma: no cover
            for ar in body_str:
                ar.byteswap()
        body_str = b''.join([ar.tobytes() for ar in body_str])

        # Write
        head = zipfile.ZipInfo('header_block2d.txt')
        head.compress_type = zipfile.ZIP_DEFLATED
        body = zipfile.ZipInfo('data.bin')
        body.compress_type = zipfile.ZIP_DEFLATED
        read = zipfile.ZipInfo('readme.txt')
        read.compress_type = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(filename, 'w') as f:
            f.writestr(head, head_str.encode(ENC))
            f.writestr(body, body_str)
            f.writestr(read, README_SAVE_2D.encode(ENC))

    def save_frame_csv(
            self, filename, name, frame, xname='x', yname='y', zname='value'):
        """
        Stores a single 2d variable's data at a single point in time to disk,
        using a csv format where each point in the frame is stored on a
        separate line as a tuple ``x, y, value``.
        """
        # Check filename
        filename = os.path.expanduser(filename)
        # Save
        delimx = ','
        delimy = '\n'
        data = self._2d[name]
        data = data[frame]
        text = [delimx.join('"' + str(x) + '"' for x in [xname, yname, zname])]
        for y, row in enumerate(data):
            for x, z in enumerate(row):
                text.append(delimx.join([str(x), str(y), myokit.float.str(z)]))
        text = delimy.join(text)
        with open(filename, 'w') as f:
            f.write(text)

    def save_frame_grid(self, filename, name, frame, delimx=' ', delimy='\n'):
        """
        Stores a single 2d variable's data at a single point in time to disk,
        using a simple 2d format where each row of the resulting data file
        represents a row of the frame.

        Data from 2d variable ``name`` at frame ``frame`` will be stored in
        ``filename`` row by row. Each column is separated by ``delimx`` (by
        default a space) and rows are separated by ``delimy`` (by default this
        will be a newline character).
        """
        # Check filename
        filename = os.path.expanduser(filename)
        # Save
        data = self._2d[name]
        data = data[frame]
        text = []
        for row in data:
            text.append(delimx.join([myokit.float.str(x) for x in row]))
        text = delimy.join(text)
        with open(filename, 'w') as f:
            f.write(text)

    def set0d(self, name, data, copy=True):
        """
        Adds or updates a zero-dimensional time series ``data`` for the
        variable named by the string ``name``.

        The ``data`` must be specified as a sequence of length ``n``, where
        ``n`` is the first value returned by :meth:`DataBlock2d.shape()`.

        By default, a copy of the given data will be stored. To prevent this
        and store a reference instead, set ``copy=False``.
        """
        name = str(name)
        if not name:
            raise ValueError('Name cannot be empty.')
        data = np.array(data, copy=copy)
        if data.shape != (self._nt,):
            raise ValueError(
                'Data must be sequence of length ' + str(self._nt) + '.')
        self._0d[name] = data

    def set2d(self, name, data, copy=True):
        """
        Adds or updates a two-dimensional time series ``data`` for the variable
        named by the string ``name``.

        The ``data`` must be specified as a numpy array with shape ``(n, w)``,
        where ``(n, w)`` is the value returned by :meth:`DataBlock2d.shape()`.

        By default, a copy of the given data will be stored. To prevent this
        and store a reference instead, set ``copy=False``.
        """
        name = str(name)
        if not name:
            raise ValueError('Name cannot be empty.')
        data = np.array(data, copy=copy)
        shape = (self._nt, self._ny, self._nx)
        if data.shape != shape:
            raise ValueError('Data must have shape ' + str(shape) + '.')
        self._2d[name] = data

    def shape(self):
        """
        Returns the required shape for 2d data passed to this data block. Zero
        dimensional series passed in must have length ``shape()[0]``.
        """
        return (self._nt, self._ny, self._nx)

    def time(self):
        """
        Returns the time data for this datablock. The data is returned
        directly, no copy is made.
        """
        return self._time

    def to_log(self, copy=True):
        """
        Returns a :class:`myokit.DataLog` containing the same information as
        this block.

        The data will be copied, unless ``copy`` is set to ``False``.
        """
        d = myokit.DataLog()

        # Add 0d vectors
        d.set_time_key('time')
        d['time'] = np.array(self._time, copy=copy)
        for k, v in self._0d.items():
            d[k] = np.array(v, copy=copy)

        # Add 2d fields
        for k, v in self._2d.items():
            for x in range(self._nx):
                s = str(x) + '.'
                for y in range(self._ny):
                    d[s + str(y) + '.' + k] = np.array(v[:, y, x], copy=copy)
        return d

    def trace(self, variable, x, y):
        """
        Returns a 0d time series of the value ``variable``, corresponding to
        the cell at position ``x``, ``y``. The data is returned directly, no
        copy is made.
        """
        return self._2d[variable][:, y, x]


class ColorMap:
    """
    *Abstract class*

    Applies colormap transformations to floating point data and returns RGB
    data.

    :class:`ColorMaps <ColorMap>` are callable objects and take the following
    arguments:

    ``floats``
        A 1-dimensional numpy array of floating point numbers.
    ``lower=None``
        A lower bound for the floats in the input. The ``lower`` and ``upper``
        values are used to normalize the input before applying the colormap. If
        this bound is omitted the lowest value in the input data is used.
    ``upper=None``
        An upper bound for the floats in the input. The ``lower`` and ``upper``
        values are used to normalize the input before applying the colormap. If
        this bound is omitted the highest value in the input data is used.
    ``alpha=True``
        Set to ``False`` to omit an alpha channel from the output.
    ``rgb=None``
        Set to ``True`` to return bytes in the order ``0xARGB``, to ``False``
        to return the order ``0xBGRA`` or to ``None`` to let the system's
        endianness determine the correct order. In the last case, big-endian
        systems will return ``0xARGB`` while little-endian systems use the
        order ``0xBGRA``.

    A 1-dimensional array of ``n`` floating point numbers will be converted to
    a 1-dimensional array of ``4n`` ``uints``, or ``3n`` if the alpha channel
    is disabled. The array will be ordered sequentially: the first four (or
    three) bytes describe the first float, the next four (or three) describe
    the second float and so on.
    """
    _colormaps = {}

    def __call__(self, floats, lower=None, upper=None, alpha=True, rgb=None):
        raise NotImplementedError

    @staticmethod
    def exists(name):
        """
        Returns True if the given name corresponds to a colormap.
        """
        return name in ColorMap._colormaps

    @staticmethod
    def get(name):
        """
        Returns the colormap method indicated by the given name.
        """
        try:
            return ColorMap._colormaps[name]()
        except KeyError:
            raise KeyError('Non-existent ColorMap "' + str(name) + '".')

    @staticmethod
    def hsv_to_rgb(h, s, v):
        """
        Converts hsv values in the range [0, 1] to rgb values in the range
        [0, 255].
        """
        r, g, b = np.empty_like(h), np.empty_like(h), np.empty_like(h)
        i = (h * 6).astype(int) % 6
        f = (h * 6) - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        idx = (i == 0)
        r[idx], g[idx], b[idx] = v[idx], t[idx], p[idx]
        idx = (i == 1)
        r[idx], g[idx], b[idx] = q[idx], v[idx], p[idx]
        idx = (i == 2)
        r[idx], g[idx], b[idx] = p[idx], v[idx], t[idx]
        idx = (i == 3)
        r[idx], g[idx], b[idx] = p[idx], q[idx], v[idx]
        idx = (i == 4)
        r[idx], g[idx], b[idx] = t[idx], p[idx], v[idx]
        idx = (i == 5)
        r[idx], g[idx], b[idx] = v[idx], p[idx], q[idx]
        out = (
            np.array(r * 255, dtype=np.uint8, copy=False),
            np.array(g * 255, dtype=np.uint8, copy=False),
            np.array(b * 255, dtype=np.uint8, copy=False),
        )
        return out

    @staticmethod
    def image(name, x, y):
        """
        Returns image data (such as returned by :meth:`DataBlock2d.images()`)
        representing the colormap specified by ``name``. The image dimensions
        can be set using ``x`` and ``y``.
        """
        data = np.linspace(1, 0, y)
        data = np.tile(data, (x, 1)).transpose()
        data = np.reshape(data, (1, y, x))
        block = myokit.DataBlock2d(x, y, [0])
        block.set2d('colormap', data, copy=False)
        return block.images('colormap', colormap=name)[0]

    @staticmethod
    def names():
        """
        Returns an iterator over the names of all available colormaps.
        """
        return ColorMap._colormaps.keys()

    @staticmethod
    def normalize(floats, lower, upper):
        """
        Normalizes the given float data based on the specified lower and upper
        bounds.
        """
        floats = np.array(floats, copy=True)
        # Enforce lower and upper bounds
        floats[floats < lower] = lower
        floats[floats > upper] = upper
        # Normalize
        n = floats - lower
        r = upper - lower
        if r == 0:
            return n
        else:
            return n / r


class ColorMapBlue(ColorMap):
    """ A plain white-to-blue colormap. """

    def __call__(self, floats, lower=None, upper=None, alpha=True, rgb=None):
        # Normalize floats
        f = ColorMap.normalize(floats, lower, upper)
        # Calculate h,s,v and convert to rgb
        h = np.zeros(f.shape)
        s = f
        v = np.ones(f.shape)
        b, g, r = ColorMap.hsv_to_rgb(h, s, v)
        # Color order
        rgb = (sys.byteorder == 'big') if rgb is None else rgb
        # Offset for first color in (a)rgb or rgb(a)
        m = 1 if (alpha and rgb) else 0
        # Number of bytes per float
        n = 4 if alpha else 3
        # Create output
        out = 255 * np.ones(n * len(floats), dtype=np.uint8)
        out[m + 0::n] = r if rgb else b
        out[m + 1::n] = g
        out[m + 2::n] = b if rgb else r
        return out


class ColorMapGray(ColorMap):
    """ A plain black-to-white colormap. """

    def __call__(self, floats, lower=None, upper=None, alpha=True, rgb=None):
        # Normalize floats
        f = 255 * ColorMap.normalize(floats, lower, upper)
        # Offset for first color in (a)rgb or rgb(a)
        m = 1 if (alpha and rgb) else 0
        # Number of bytes per float
        n = 4 if alpha else 3
        # Create output
        out = 255 * np.ones(n * len(floats), dtype=np.uint8)
        out[m + 0::n] = f
        out[m + 1::n] = f
        out[m + 2::n] = f
        return out


class ColorMapGreen(ColorMap):
    """ A plain white-to-green colormap. """

    def __call__(self, floats, lower=None, upper=None, alpha=True, rgb=None):
        # Normalize floats
        f = ColorMap.normalize(floats, lower, upper)
        # Calculate h,s,v and convert to rgb
        h = np.zeros(f.shape)
        s = f
        v = np.ones(f.shape)
        g, r, b = ColorMap.hsv_to_rgb(h, s, v)
        # Color order
        rgb = (sys.byteorder == 'big') if rgb is None else rgb
        # Offset for first color in (a)rgb or rgb(a)
        m = 1 if (alpha and rgb) else 0
        # Number of bytes per float
        n = 4 if alpha else 3
        # Create output
        out = 255 * np.ones(n * len(floats), dtype=np.uint8)
        out[m + 0::n] = r if rgb else b
        out[m + 1::n] = g
        out[m + 2::n] = b if rgb else r
        return out


class ColorMapRed(ColorMap):
    """ A plain white-to-red colormap. """

    def __call__(self, floats, lower=None, upper=None, alpha=True, rgb=None):
        # Normalize floats
        f = ColorMap.normalize(floats, lower, upper)
        # Calculate h,s,v and convert to rgb
        h = np.zeros(f.shape)
        s = f
        v = np.ones(f.shape)
        r, g, b = ColorMap.hsv_to_rgb(h, s, v)
        # Color order
        rgb = (sys.byteorder == 'big') if rgb is None else rgb
        # Offset for first color in (a)rgb or rgb(a)
        m = 1 if (alpha and rgb) else 0
        # Number of bytes per float
        n = 4 if alpha else 3
        # Create output
        out = 255 * np.ones(n * len(floats), dtype=np.uint8)
        out[m + 0::n] = r if rgb else b
        out[m + 1::n] = g
        out[m + 2::n] = b if rgb else r
        return out


class ColorMapTraditional(ColorMap):
    """
    A traditional hue-cycling colormap.

    Probably best not to use in publications. See e.g.
    https://doi.org/10.1371/journal.pone.0199239
    """
    def __call__(self, floats, lower=None, upper=None, alpha=True, rgb=None):
        # Normalize floats
        f = ColorMap.normalize(floats, lower, upper)
        # Calculate h,s,v and convert to rgb
        g = 0.6
        s = g + (1 - g) * np.sin(f * 3.14)
        h = (0.85 - 0.85 * f) % 1
        r, g, b = ColorMap.hsv_to_rgb(h, s, s)
        # Color order
        rgb = (sys.byteorder == 'big') if rgb is None else rgb
        # Offset for first color in (a)rgb or rgb(a)
        m = 1 if (alpha and rgb) else 0
        # Number of bytes per float
        n = 4 if alpha else 3
        # Create output
        out = 255 * np.ones(n * len(floats), dtype=np.uint8)
        out[m + 0::n] = r if rgb else b
        out[m + 1::n] = g
        out[m + 2::n] = b if rgb else r
        return out


class ColorMapCividis(ColorMap):
    """
    A colormap using "Cividis".

    The values used by this color map are taken from supplement 3 in
    https://doi.org/10.1371/journal.pone.0199239, by Jamie R. Nuñez,
    Christopher R. Anderton, and Ryan S. Renslow.
    """
    _VALUES = np.array((
        (0, 32, 76),
        (0, 32, 78),
        (0, 33, 80),
        (0, 34, 81),
        (0, 35, 83),
        (0, 35, 85),
        (0, 36, 86),
        (0, 37, 88),
        (0, 38, 90),
        (0, 38, 91),
        (0, 39, 93),
        (0, 40, 95),
        (0, 40, 97),
        (0, 41, 99),
        (0, 42, 100),
        (0, 42, 102),
        (0, 43, 104),
        (0, 44, 106),
        (0, 45, 108),
        (0, 45, 109),
        (0, 46, 110),
        (0, 46, 111),
        (0, 47, 111),
        (0, 47, 111),
        (0, 48, 111),
        (0, 49, 111),
        (0, 49, 111),
        (0, 50, 110),
        (0, 51, 110),
        (0, 52, 110),
        (0, 52, 110),
        (1, 53, 110),
        (6, 54, 110),
        (10, 55, 109),
        (14, 55, 109),
        (18, 56, 109),
        (21, 57, 109),
        (23, 57, 109),
        (26, 58, 108),
        (28, 59, 108),
        (30, 60, 108),
        (32, 60, 108),
        (34, 61, 108),
        (36, 62, 108),
        (38, 62, 108),
        (39, 63, 108),
        (41, 64, 107),
        (43, 65, 107),
        (44, 65, 107),
        (46, 66, 107),
        (47, 67, 107),
        (49, 68, 107),
        (50, 68, 107),
        (51, 69, 107),
        (53, 70, 107),
        (54, 70, 107),
        (55, 71, 107),
        (56, 72, 107),
        (58, 73, 107),
        (59, 73, 107),
        (60, 74, 107),
        (61, 75, 107),
        (62, 75, 107),
        (64, 76, 107),
        (65, 77, 107),
        (66, 78, 107),
        (67, 78, 107),
        (68, 79, 107),
        (69, 80, 107),
        (70, 80, 107),
        (71, 81, 107),
        (72, 82, 107),
        (73, 83, 107),
        (74, 83, 107),
        (75, 84, 107),
        (76, 85, 107),
        (77, 85, 107),
        (78, 86, 107),
        (79, 87, 108),
        (80, 88, 108),
        (81, 88, 108),
        (82, 89, 108),
        (83, 90, 108),
        (84, 90, 108),
        (85, 91, 108),
        (86, 92, 108),
        (87, 93, 109),
        (88, 93, 109),
        (89, 94, 109),
        (90, 95, 109),
        (91, 95, 109),
        (92, 96, 109),
        (93, 97, 110),
        (94, 98, 110),
        (95, 98, 110),
        (95, 99, 110),
        (96, 100, 110),
        (97, 101, 111),
        (98, 101, 111),
        (99, 102, 111),
        (100, 103, 111),
        (101, 103, 111),
        (102, 104, 112),
        (103, 105, 112),
        (104, 106, 112),
        (104, 106, 112),
        (105, 107, 113),
        (106, 108, 113),
        (107, 109, 113),
        (108, 109, 114),
        (109, 110, 114),
        (110, 111, 114),
        (111, 111, 114),
        (111, 112, 115),
        (112, 113, 115),
        (113, 114, 115),
        (114, 114, 116),
        (115, 115, 116),
        (116, 116, 117),
        (117, 117, 117),
        (117, 117, 117),
        (118, 118, 118),
        (119, 119, 118),
        (120, 120, 118),
        (121, 120, 119),
        (122, 121, 119),
        (123, 122, 119),
        (123, 123, 120),
        (124, 123, 120),
        (125, 124, 120),
        (126, 125, 120),
        (127, 126, 120),
        (128, 126, 120),
        (129, 127, 120),
        (130, 128, 120),
        (131, 129, 120),
        (132, 129, 120),
        (133, 130, 120),
        (134, 131, 120),
        (135, 132, 120),
        (136, 133, 120),
        (137, 133, 120),
        (138, 134, 120),
        (139, 135, 120),
        (140, 136, 120),
        (141, 136, 120),
        (142, 137, 120),
        (143, 138, 120),
        (144, 139, 120),
        (145, 140, 120),
        (146, 140, 120),
        (147, 141, 120),
        (148, 142, 120),
        (149, 143, 120),
        (150, 143, 119),
        (151, 144, 119),
        (152, 145, 119),
        (153, 146, 119),
        (154, 147, 119),
        (155, 147, 119),
        (156, 148, 119),
        (157, 149, 119),
        (158, 150, 118),
        (159, 151, 118),
        (160, 152, 118),
        (161, 152, 118),
        (162, 153, 118),
        (163, 154, 117),
        (164, 155, 117),
        (165, 156, 117),
        (166, 156, 117),
        (167, 157, 117),
        (168, 158, 116),
        (169, 159, 116),
        (170, 160, 116),
        (171, 161, 116),
        (172, 161, 115),
        (173, 162, 115),
        (174, 163, 115),
        (175, 164, 115),
        (176, 165, 114),
        (177, 166, 114),
        (178, 166, 114),
        (180, 167, 113),
        (181, 168, 113),
        (182, 169, 113),
        (183, 170, 112),
        (184, 171, 112),
        (185, 171, 112),
        (186, 172, 111),
        (187, 173, 111),
        (188, 174, 110),
        (189, 175, 110),
        (190, 176, 110),
        (191, 177, 109),
        (192, 177, 109),
        (193, 178, 108),
        (194, 179, 108),
        (196, 180, 108),
        (197, 181, 107),
        (198, 182, 107),
        (199, 183, 106),
        (200, 184, 106),
        (201, 184, 105),
        (202, 185, 105),
        (203, 186, 104),
        (204, 187, 104),
        (205, 188, 103),
        (206, 189, 103),
        (207, 190, 102),
        (209, 191, 102),
        (210, 192, 101),
        (211, 192, 101),
        (212, 193, 100),
        (213, 194, 99),
        (214, 195, 99),
        (215, 196, 98),
        (216, 197, 98),
        (217, 198, 97),
        (219, 199, 96),
        (220, 200, 96),
        (221, 201, 95),
        (222, 202, 94),
        (223, 203, 93),
        (224, 203, 93),
        (225, 204, 92),
        (227, 205, 91),
        (228, 206, 91),
        (229, 207, 90),
        (230, 208, 89),
        (231, 209, 88),
        (232, 210, 87),
        (233, 211, 86),
        (235, 212, 86),
        (236, 213, 85),
        (237, 214, 84),
        (238, 215, 83),
        (239, 216, 82),
        (240, 217, 81),
        (242, 218, 80),
        (243, 219, 79),
        (244, 220, 78),
        (245, 221, 77),
        (246, 222, 76),
        (247, 223, 75),
        (249, 224, 73),
        (250, 224, 72),
        (251, 225, 71),
        (252, 226, 70),
        (253, 227, 69),
        (255, 228, 67),
        (255, 229, 66),
        (255, 230, 66),
        (255, 231, 67),
        (255, 232, 68),
        (255, 233, 69),
    ))

    def __init__(self):
        self._n = len(self._VALUES)

    def __call__(self, floats, lower=None, upper=None, alpha=True, rgb=None):
        # Normalize floats
        f = ColorMap.normalize(floats, lower, upper)
        # Get RGB
        val = self._VALUES[
            np.minimum(np.round(f * self._n).astype(int), self._n - 1)]
        # Color order
        rgb = (sys.byteorder == 'big') if rgb is None else rgb
        # Offset for first color in (a)rgb or rgb(a)
        m = 1 if (alpha and rgb) else 0
        # Number of bytes per float
        n = 4 if alpha else 3
        # Create output
        out = 255 * np.ones(n * len(floats), dtype=np.uint8)
        out[m + 0::n] = val[:, 0] if rgb else val[:, 2]
        out[m + 1::n] = val[:, 1]
        out[m + 2::n] = val[:, 2] if rgb else val[:, 0]
        return out


class ColorMapViridis(ColorMap):
    """
    A colormap using "Viridis".

    The values used by this color map are taken from
    https://github.com/BIDS/colormap/blob/master/colormaps.py
    and were distributed under a CC0 license.

    Viridis was designed by Eric Firing, Nathaniel J. Smith, and Stefan van der
    Walt.
    """
    _VALUES = np.array((
        (68, 1, 84),
        (69, 2, 86),
        (69, 4, 87),
        (69, 5, 89),
        (70, 7, 90),
        (70, 8, 92),
        (70, 10, 93),
        (71, 11, 95),
        (71, 13, 96),
        (71, 14, 98),
        (71, 16, 99),
        (72, 17, 100),
        (72, 19, 102),
        (72, 20, 103),
        (72, 22, 104),
        (72, 23, 106),
        (72, 24, 107),
        (72, 26, 108),
        (72, 27, 109),
        (72, 28, 110),
        (72, 30, 112),
        (73, 31, 113),
        (72, 32, 114),
        (72, 34, 115),
        (72, 35, 116),
        (72, 36, 117),
        (72, 37, 118),
        (72, 39, 119),
        (72, 40, 120),
        (72, 41, 121),
        (72, 42, 122),
        (72, 44, 123),
        (71, 45, 124),
        (71, 46, 125),
        (71, 47, 125),
        (71, 49, 126),
        (70, 50, 127),
        (70, 51, 128),
        (70, 52, 128),
        (70, 54, 129),
        (69, 55, 130),
        (69, 56, 130),
        (69, 57, 131),
        (68, 58, 132),
        (68, 60, 132),
        (67, 61, 133),
        (67, 62, 133),
        (67, 63, 134),
        (66, 64, 134),
        (66, 66, 135),
        (65, 67, 135),
        (65, 68, 136),
        (65, 69, 136),
        (64, 70, 136),
        (64, 71, 137),
        (63, 73, 137),
        (63, 74, 138),
        (62, 75, 138),
        (62, 76, 138),
        (61, 77, 138),
        (61, 78, 139),
        (60, 79, 139),
        (60, 80, 139),
        (59, 81, 139),
        (59, 83, 140),
        (58, 84, 140),
        (58, 85, 140),
        (57, 86, 140),
        (57, 87, 140),
        (56, 88, 141),
        (56, 89, 141),
        (55, 90, 141),
        (55, 91, 141),
        (54, 92, 141),
        (54, 93, 141),
        (53, 94, 141),
        (53, 95, 142),
        (52, 96, 142),
        (52, 97, 142),
        (52, 98, 142),
        (51, 99, 142),
        (51, 100, 142),
        (50, 101, 142),
        (50, 102, 142),
        (49, 103, 142),
        (49, 104, 142),
        (48, 105, 142),
        (48, 106, 142),
        (48, 107, 143),
        (47, 108, 143),
        (47, 109, 143),
        (46, 110, 143),
        (46, 111, 143),
        (45, 112, 143),
        (45, 113, 143),
        (45, 114, 143),
        (44, 115, 143),
        (44, 116, 143),
        (43, 117, 143),
        (43, 118, 143),
        (43, 119, 143),
        (42, 120, 143),
        (42, 121, 143),
        (42, 122, 143),
        (41, 123, 143),
        (41, 123, 143),
        (40, 124, 143),
        (40, 125, 143),
        (40, 126, 143),
        (39, 127, 143),
        (39, 128, 143),
        (39, 129, 143),
        (38, 130, 143),
        (38, 131, 143),
        (37, 132, 143),
        (37, 133, 142),
        (37, 134, 142),
        (36, 135, 142),
        (36, 136, 142),
        (36, 137, 142),
        (35, 138, 142),
        (35, 139, 142),
        (35, 139, 142),
        (34, 140, 142),
        (34, 141, 142),
        (34, 142, 141),
        (33, 143, 141),
        (33, 144, 141),
        (33, 145, 141),
        (32, 146, 141),
        (32, 147, 141),
        (32, 148, 140),
        (32, 149, 140),
        (31, 150, 140),
        (31, 151, 140),
        (31, 152, 139),
        (31, 153, 139),
        (31, 154, 139),
        (31, 155, 139),
        (31, 156, 138),
        (31, 156, 138),
        (31, 157, 138),
        (31, 158, 137),
        (31, 159, 137),
        (31, 160, 137),
        (31, 161, 136),
        (31, 162, 136),
        (32, 163, 135),
        (32, 164, 135),
        (32, 165, 134),
        (33, 166, 134),
        (33, 167, 134),
        (34, 168, 133),
        (34, 169, 133),
        (35, 170, 132),
        (36, 170, 131),
        (37, 171, 131),
        (38, 172, 130),
        (38, 173, 130),
        (39, 174, 129),
        (40, 175, 128),
        (41, 176, 128),
        (43, 177, 127),
        (44, 178, 126),
        (45, 179, 126),
        (46, 180, 125),
        (48, 180, 124),
        (49, 181, 123),
        (50, 182, 123),
        (52, 183, 122),
        (53, 184, 121),
        (55, 185, 120),
        (56, 186, 119),
        (58, 187, 118),
        (60, 187, 118),
        (61, 188, 117),
        (63, 189, 116),
        (65, 190, 115),
        (67, 191, 114),
        (68, 192, 113),
        (70, 193, 112),
        (72, 193, 111),
        (74, 194, 110),
        (76, 195, 109),
        (78, 196, 108),
        (80, 197, 106),
        (82, 197, 105),
        (84, 198, 104),
        (86, 199, 103),
        (88, 200, 102),
        (90, 200, 101),
        (92, 201, 99),
        (95, 202, 98),
        (97, 203, 97),
        (99, 203, 95),
        (101, 204, 94),
        (103, 205, 93),
        (106, 206, 91),
        (108, 206, 90),
        (110, 207, 89),
        (113, 208, 87),
        (115, 208, 86),
        (117, 209, 84),
        (120, 210, 83),
        (122, 210, 81),
        (125, 211, 80),
        (127, 212, 78),
        (130, 212, 77),
        (132, 213, 75),
        (135, 213, 74),
        (137, 214, 72),
        (140, 215, 71),
        (142, 215, 69),
        (145, 216, 67),
        (147, 216, 66),
        (150, 217, 64),
        (153, 217, 62),
        (155, 218, 61),
        (158, 218, 59),
        (160, 219, 57),
        (163, 219, 55),
        (166, 220, 54),
        (168, 220, 52),
        (171, 221, 50),
        (174, 221, 49),
        (176, 222, 47),
        (179, 222, 45),
        (182, 222, 43),
        (184, 223, 42),
        (187, 223, 40),
        (190, 224, 38),
        (192, 224, 37),
        (195, 224, 35),
        (198, 225, 34),
        (201, 225, 32),
        (203, 225, 31),
        (206, 226, 29),
        (209, 226, 28),
        (211, 226, 27),
        (214, 227, 26),
        (216, 227, 26),
        (219, 227, 25),
        (222, 228, 25),
        (224, 228, 24),
        (227, 228, 24),
        (229, 229, 25),
        (232, 229, 25),
        (235, 229, 26),
        (237, 230, 27),
        (240, 230, 28),
        (242, 230, 29),
        (245, 231, 30),
        (247, 231, 32),
        (249, 231, 33),
        (252, 232, 35),
        (254, 232, 37),
    ))

    def __init__(self):
        self._n = len(self._VALUES)

    def __call__(self, floats, lower=None, upper=None, alpha=True, rgb=None):
        # Normalize floats
        f = ColorMap.normalize(floats, lower, upper)
        # Get RGB
        val = self._VALUES[
            np.minimum(np.round(f * self._n).astype(int), self._n - 1)]
        # Color order
        rgb = (sys.byteorder == 'big') if rgb is None else rgb
        # Offset for first color in (a)rgb or rgb(a)
        m = 1 if (alpha and rgb) else 0
        # Number of bytes per float
        n = 4 if alpha else 3
        # Create output
        out = 255 * np.ones(n * len(floats), dtype=np.uint8)
        out[m + 0::n] = val[:, 0] if rgb else val[:, 2]
        out[m + 1::n] = val[:, 1]
        out[m + 2::n] = val[:, 2] if rgb else val[:, 0]
        return out


class ColorMapInferno(ColorMap):
    """
    A colormap using "Viridis".

    The values used by this color map are taken from
    https://github.com/BIDS/colormap/blob/master/colormaps.py
    and were distributed under a CC0 license.

    Viridis was designed by Eric Firing, Nathaniel J. Smith, and Stefan van der
    Walt.
    """
    _VALUES = np.array((
        (0, 0, 4),
        (1, 0, 5),
        (1, 1, 6),
        (1, 1, 8),
        (2, 1, 10),
        (2, 2, 12),
        (2, 2, 14),
        (3, 2, 16),
        (4, 3, 18),
        (4, 3, 21),
        (5, 4, 23),
        (6, 4, 25),
        (7, 5, 27),
        (8, 6, 29),
        (9, 6, 32),
        (10, 7, 34),
        (11, 7, 36),
        (12, 8, 38),
        (13, 8, 41),
        (14, 9, 43),
        (16, 9, 45),
        (17, 10, 48),
        (18, 10, 50),
        (20, 11, 53),
        (21, 11, 55),
        (22, 11, 58),
        (24, 12, 60),
        (25, 12, 62),
        (27, 12, 65),
        (28, 12, 67),
        (30, 12, 70),
        (31, 12, 72),
        (33, 12, 74),
        (35, 12, 77),
        (36, 12, 79),
        (38, 12, 81),
        (40, 11, 83),
        (42, 11, 85),
        (43, 11, 87),
        (45, 11, 89),
        (47, 10, 91),
        (49, 10, 93),
        (51, 10, 94),
        (52, 10, 96),
        (54, 9, 97),
        (56, 9, 98),
        (58, 9, 99),
        (59, 9, 100),
        (61, 9, 101),
        (63, 9, 102),
        (64, 10, 103),
        (66, 10, 104),
        (68, 10, 105),
        (69, 10, 105),
        (71, 11, 106),
        (73, 11, 107),
        (74, 12, 107),
        (76, 12, 108),
        (78, 13, 108),
        (79, 13, 108),
        (81, 14, 109),
        (83, 14, 109),
        (84, 15, 109),
        (86, 15, 110),
        (87, 16, 110),
        (89, 17, 110),
        (91, 17, 110),
        (92, 18, 110),
        (94, 18, 111),
        (95, 19, 111),
        (97, 20, 111),
        (99, 20, 111),
        (100, 21, 111),
        (102, 21, 111),
        (103, 22, 111),
        (105, 23, 111),
        (107, 23, 111),
        (108, 24, 111),
        (110, 24, 111),
        (111, 25, 111),
        (113, 25, 110),
        (115, 26, 110),
        (116, 27, 110),
        (118, 27, 110),
        (119, 28, 110),
        (121, 28, 110),
        (123, 29, 109),
        (124, 29, 109),
        (126, 30, 109),
        (127, 31, 109),
        (129, 31, 108),
        (130, 32, 108),
        (132, 32, 108),
        (134, 33, 107),
        (135, 33, 107),
        (137, 34, 107),
        (138, 34, 106),
        (140, 35, 106),
        (142, 36, 105),
        (143, 36, 105),
        (145, 37, 105),
        (146, 37, 104),
        (148, 38, 104),
        (150, 38, 103),
        (151, 39, 102),
        (153, 40, 102),
        (154, 40, 101),
        (156, 41, 101),
        (158, 41, 100),
        (159, 42, 100),
        (161, 43, 99),
        (162, 43, 98),
        (164, 44, 98),
        (165, 45, 97),
        (167, 45, 96),
        (169, 46, 95),
        (170, 46, 95),
        (172, 47, 94),
        (173, 48, 93),
        (175, 49, 92),
        (176, 49, 92),
        (178, 50, 91),
        (179, 51, 90),
        (181, 51, 89),
        (182, 52, 88),
        (184, 53, 87),
        (185, 54, 86),
        (187, 54, 85),
        (188, 55, 85),
        (190, 56, 84),
        (191, 57, 83),
        (193, 58, 82),
        (194, 59, 81),
        (196, 60, 80),
        (197, 60, 79),
        (198, 61, 78),
        (200, 62, 77),
        (201, 63, 76),
        (203, 64, 75),
        (204, 65, 74),
        (205, 66, 72),
        (207, 67, 71),
        (208, 68, 70),
        (209, 69, 69),
        (211, 70, 68),
        (212, 72, 67),
        (213, 73, 66),
        (214, 74, 65),
        (216, 75, 64),
        (217, 76, 62),
        (218, 77, 61),
        (219, 79, 60),
        (220, 80, 59),
        (221, 81, 58),
        (223, 82, 57),
        (224, 84, 56),
        (225, 85, 54),
        (226, 86, 53),
        (227, 88, 52),
        (228, 89, 51),
        (229, 90, 50),
        (230, 92, 48),
        (231, 93, 47),
        (232, 95, 46),
        (233, 96, 45),
        (234, 98, 43),
        (235, 99, 42),
        (235, 101, 41),
        (236, 102, 40),
        (237, 104, 38),
        (238, 105, 37),
        (239, 107, 36),
        (240, 109, 35),
        (240, 110, 33),
        (241, 112, 32),
        (242, 113, 31),
        (242, 115, 30),
        (243, 117, 28),
        (244, 118, 27),
        (244, 120, 26),
        (245, 122, 24),
        (246, 123, 23),
        (246, 125, 22),
        (247, 127, 20),
        (247, 129, 19),
        (248, 130, 18),
        (248, 132, 16),
        (249, 134, 15),
        (249, 136, 14),
        (249, 137, 12),
        (250, 139, 11),
        (250, 141, 10),
        (250, 143, 9),
        (251, 145, 8),
        (251, 146, 7),
        (251, 148, 7),
        (252, 150, 6),
        (252, 152, 6),
        (252, 154, 6),
        (252, 156, 6),
        (252, 158, 7),
        (253, 160, 7),
        (253, 161, 8),
        (253, 163, 9),
        (253, 165, 10),
        (253, 167, 12),
        (253, 169, 13),
        (253, 171, 15),
        (253, 173, 17),
        (253, 175, 19),
        (253, 177, 20),
        (253, 179, 22),
        (253, 181, 24),
        (252, 183, 27),
        (252, 185, 29),
        (252, 186, 31),
        (252, 188, 33),
        (252, 190, 35),
        (251, 192, 38),
        (251, 194, 40),
        (251, 196, 43),
        (251, 198, 45),
        (250, 200, 48),
        (250, 202, 50),
        (250, 204, 53),
        (249, 206, 56),
        (249, 208, 58),
        (248, 210, 61),
        (248, 212, 64),
        (247, 214, 67),
        (247, 216, 70),
        (246, 218, 73),
        (246, 220, 76),
        (245, 222, 80),
        (245, 224, 83),
        (244, 226, 86),
        (244, 228, 90),
        (244, 229, 94),
        (243, 231, 97),
        (243, 233, 101),
        (243, 235, 105),
        (242, 237, 109),
        (242, 238, 113),
        (242, 240, 117),
        (242, 241, 122),
        (243, 243, 126),
        (243, 244, 130),
        (244, 246, 134),
        (244, 247, 138),
        (245, 249, 142),
        (246, 250, 146),
        (247, 251, 150),
        (249, 252, 154),
        (250, 253, 158),
        (251, 254, 162),
        (253, 255, 165),
    ))

    def __init__(self):
        self._n = len(self._VALUES)

    def __call__(self, floats, lower=None, upper=None, alpha=True, rgb=None):
        # Normalize floats
        f = ColorMap.normalize(floats, lower, upper)
        # Get RGB
        val = self._VALUES[
            np.minimum(np.round(f * self._n).astype(int), self._n - 1)]
        # Color order
        rgb = (sys.byteorder == 'big') if rgb is None else rgb
        # Offset for first color in (a)rgb or rgb(a)
        m = 1 if (alpha and rgb) else 0
        # Number of bytes per float
        n = 4 if alpha else 3
        # Create output
        out = 255 * np.ones(n * len(floats), dtype=np.uint8)
        out[m + 0::n] = val[:, 0] if rgb else val[:, 2]
        out[m + 1::n] = val[:, 1]
        out[m + 2::n] = val[:, 2] if rgb else val[:, 0]
        return out


ColorMap._colormaps['cividis'] = ColorMapCividis
ColorMap._colormaps['inferno'] = ColorMapInferno
ColorMap._colormaps['viridis'] = ColorMapViridis
ColorMap._colormaps['gray'] = ColorMapGray
ColorMap._colormaps['blue'] = ColorMapBlue
ColorMap._colormaps['green'] = ColorMapGreen
ColorMap._colormaps['red'] = ColorMapRed
ColorMap._colormaps['traditional'] = ColorMapTraditional
