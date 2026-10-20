#
# This module reads files in Axon Text File format.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import re

import numpy as np

from collections import OrderedDict

import myokit

# Format used for any text
_ENC = 'ascii'


class AtfFile:
    """
    Represents an Axon Text File (ATF) stored on disk.

    This method provides access to the data stored in the ATF as well as any
    meta data stored in the header.

    Access to the data is provided using a dict-like interface: to iterate over
    the file's keys use :meth:`iterkeys`, to select a value use
    ``atf_file['key']``. All iterators return the keys stored in the order they
    were listed in the ATF file.
    """
    def __init__(self, filename):
        # The path to the file and its basename
        self._path = os.path.abspath(filename)
        self._filename = os.path.basename(filename)

        # A version string
        self._version_str = None

        # A (multi-line) string containing meta-data found in this file
        self._meta = None

        # An ordered dict with key-value pairs. The first key is time.
        self._data = None

        # Read data
        self._read()

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def filename(self):
        """ Returns this ATF's filename. """
        return self._filename

    def info(self):
        """ Returns this ATF's header/meta data. """
        # Deprecated since 2023-07-12
        import warnings
        warnings.warn(
            'The method `info` is deprecated. Please use `meta_str` instead.')
        return self.meta_str()

    def items(self):
        """ Returns an iterator over all ``(key, value)`` pairs. """
        return iter(self._data.items())

    def keys(self):
        """ Returns an iterator over all keys in this ATF. """
        return iter(self._data.keys())

    def log(self):
        """
        Returns this file's time series data as a :class:`myokit.DataLog`.
        """
        log = myokit.DataLog()
        if len(self._data) > 0:
            log.set_time_key(next(iter(self._data.keys())))
        for k, v in self._data.items():
            log[k] = v
        return log

    def meta_str(self, verbose=True):
        """
        Returns this ATF's header data as an unstructured multi-line string.

        Note that the ``verbose`` argument doesn't do anything, but provides
        compatibility with similar methods in other files.
        """
        return self._meta

    def myokit_log(self):
        """ Deprecated alias of :meth:`log`. """
        # Deprecated since 2023-06-22
        import warnings
        warnings.warn(
            'The method `myokit_log` is deprecated. Please use `log` instead.')
        return self.log()

    def path(self):
        """ Returns the path to this ATF file. """
        return self._path

    def _read(self):
        """ Reads the data in this file. """
        with open(self._path, 'rb') as f:
            # Check version
            line = f.readline().decode(_ENC)
            line_index = 1
            if line[:3] != 'ATF':
                raise Exception('Unrecognised file type.')
            self._version_str = line[3:].strip()

            # Read number of header lines, number of fields
            line = f.readline().decode(_ENC)
            line_index += 1
            nh, nf = [int(x) for x in line.split()]

            # Read header data
            # If formatted as key-value pairs, format the meta data nicely.
            # Otherwise, just enter as is.
            key = []    # Keys
            val = []    # Values
            raw = []    # Fallback
            key_value_pairs = True
            for i in range(nh):
                line = f.readline().decode(_ENC).strip()
                line_index += 1
                if line[0] != '"' or line[-1] != '"':
                    raise Exception(
                        f'Invalid header on line f{line_index}: expecting '
                        f' lines wrapped in double quotes ("like this").')
                line = line[1:-1].strip()
                raw.append(line)
                if key_value_pairs:
                    try:
                        k, v = line.split('=')
                        key.append(k.strip())
                        val.append(v.strip())
                    except ValueError:
                        key_value_pairs = False
            if key_value_pairs:
                n = max([len(k) for k in key])
                meta = []
                val = iter(val)
                for k in key:
                    v = next(val)
                    meta.append(k + ' ' * (n - len(k)) + ' = ' + v)
                self._meta = '\n'.join(meta)
            else:
                self._meta = '\n'.join(raw)

            # Read time-series data
            self._data = OrderedDict()
            line = f.readline().decode(_ENC).strip()
            line_index += 1

            # Test if comma separated or space/tab separated
            delims = re.compile(r'["]{1}[^"]*["]{1}')
            delims = delims.split(line)

            # First and last delim must be empty (i.e. line starts and ends
            # with '"')
            if delims[0] != '' or delims[-1] != '':
                raise Exception('Unable to parse column headers.')
            delims = delims[1:-1]
            if len(delims) + 1 != nf:
                raise Exception(
                    f'Unable to parse column headers: Expected {nf} headers,'
                    f' found {len(delims) + 1}.')
            commas = ',' in delims[0]
            for delim in delims:
                if commas != (',' in delim):
                    raise Exception('Mixed delimiters are not supported.')

            # Read column headers
            keys = []
            try:
                a, b = 0, 0
                if line[a] != '"':  # pragma: no cover
                    # This should have triggered an earlier error
                    raise Exception('Unable to parse columns headers.')
                for i in range(nf):
                    b = line.index('"', a + 1)
                    keys.append(line[a + 1:b])
                    a = line.index('"', b + 1)
            except ValueError:
                pass
            if len(keys) != nf:     # pragma: no cover
                # This should have been picked up above
                raise Exception(
                    f'Unable to parse column headers: Expected {nf} headers,'
                    f' found {len(keys)}.')

            # Read data
            data = []
            for key in keys:
                col = []
                data.append(col)
                self._data[key] = col
            sep = ',' if commas else None
            for line in f:
                line_index += 1
                line = line.decode(_ENC).strip()
                vals = line.split(sep)
                if len(vals) != nf:
                    raise Exception(
                        f'Invalid data on line f{line_index}: expecting {nf}'
                        f' fields, found {len(vals)}.')
                vals = [float(x) for x in vals]
                for k, d in enumerate(vals):
                    data[k].append(d)

    def values(self):
        """ Returns an iterator over all values in this ATF. """
        return iter(self._data.values())

    def version(self):
        """ Returns a string representation of this file's version number. """
        return self._version_str


def load_atf(filename):
    """
    Reads an ATF file and returns its data as a :class:`myokit.DataLog`.
    """
    filename = os.path.expanduser(filename)
    return AtfFile(filename).log()


def save_atf(log, filename, fields=None):
    """
    Saves the :class:`myokit.DataLog` ``log`` to ``filename`` in ATF format.

    ATF requires that the times in the log be regularly spaced.

    The first column in an ATF file should always be time. Remaining fields
    will be written in a random order. To indicate an order or make a selection
    of fields, pass in a sequence ``fields`` containing the field names.
    """
    log.validate()
    import myokit

    # Check filename
    filename = os.path.expanduser(filename)

    # Delimiters
    # Dos-style EOL: Open file in 'wb' mode to stop windows writing \r\r\n
    eol = '\r\n'
    delim = '\t'

    # Create data and keys lists
    data = [iter(log.time())]
    time = log.time_key()
    keys = [time]

    # Check fields
    if fields:
        for field in fields:
            field = str(field)
            if field == time:
                continue
            keys.append(field)
            try:
                data.append(iter(log[field]))
            except KeyError:
                raise ValueError('Variable <' + field + '> not found in log.')
    else:
        for k, v in log.items():
            if k != time:
                keys.append(k)
                data.append(iter(v))

    for k in keys:
        if '"' in k:
            raise ValueError('Column names must not contain double quotes.')
        if '\r' in k or '\n' in k:
            raise ValueError(
                'Column names must not contain newlines or carriage returns.')

    # Check if time is equally spaced
    t = np.asarray(log.time())
    dt = t[1:] - t[:-1]
    dt_ref = dt[0]
    dt_err = dt_ref * 1e-6
    if np.any(np.abs(dt - dt_ref) > dt_err):
        raise ValueError('The time variable must be regularly spaced.')

    # Create header
    header = []
    header.append(('myokit-version', 'Myokit ' + myokit.version(raw=True)))
    header.append(('date-created', myokit.date()))
    header.append(('sampling-interval', dt_ref))

    # Get sizes
    nh = len(header)
    nf = len(keys)
    nd = log.length()

    # Write file
    with open(filename, 'wb') as f:
        # Write version number
        f.write(('ATF 1.0' + eol).encode(_ENC))

        # Write number of header lines, number of fields
        f.write(f'{nh}{delim}{nf}{eol}'.encode(_ENC))
        for k, v in header:
            f.write(f'"{k}={v}"{eol}'.encode(_ENC))

        # Write field names
        f.write((delim.join([f'"{k}"' for k in keys]) + eol).encode(_ENC))

        # Write data
        for i in range(nd):
            f.write((
                delim.join([myokit.float.str(next(d)) for d in data]) + eol
            ).encode(_ENC))

