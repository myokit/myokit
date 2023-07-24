#
# This module reads files in WCP format
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import struct
import numpy as np

import myokit

# Encoding of text portions of wcp file
_ENC = 'ascii'


class WcpFile(myokit.formats.SweepSource):
    """
    Represents a read-only WinWCP file (``.wcp``), stored at ``path``.

    Only files in the newer file format version 9 can be read. This version of
    the format was introduced in 2010. New versions of WinWCP can read older
    files and will convert them to the new format automatically when opened.

    WinWCP is a tool for recording electrophysiological data written by John
    Dempster of Strathclyde University. For more information, see
    https://documentation.help/WinWCP-V5.3.8/IDH_Topic750.htm

    WinWCP files contain a number of records ``NR``, each containing data from
    ``NC`` channels. Every channel has the same length, ``NP`` samples.
    Sampling happens at a fixed sampling rate.

    When a :class:`WcpFile` is created, the file at ``path`` is read in its
    entirety and the file handle is closed. No try-catch or ``with`` statements
    are required.
    """
    def __init__(self, path):
        # The path to the file and its basename
        path = str(path)
        self._path = os.path.abspath(path)
        self._filename = os.path.basename(path)

        # Header info, per file, per record, and per channel
        self._version_str = None
        self._header = {}
        self._header_raw = {}
        self._record_headers = []
        self._channel_headers = []

        # Records
        self._records = []
        self._nr = None     # Records in file
        self._nc = None     # Channels per record
        self._np = None     # Samples per channel
        self._dt = None     # Sampling interval (s)

        # Channels
        self._channel_names = []
        self._channel_name_map = {}

        # Time signal
        self._time = None

        # Units
        self._time_unit = None
        self._channel_units = []
        self._unit_cache = {}

        # Read the file
        with open(path, 'rb') as f:
            self._read(f)

    def _read(self, f):
        """ Reads the file header & data. """
        # Header size is between 1024 and 16380, depending on number of
        # channels in the file following:
        #   n = (int((n_channels - 1)/8) + 1) * 1024
        # Read first part of header, determine version and number of channels
        # in the file
        data = f.read(1024).decode(_ENC)
        h = [x.strip().split('=') for x in data.split('\n')]
        h = dict([(x[0].lower(), x[1]) for x in h if len(x) == 2])
        if int(h['ver']) != 9:
            raise NotImplementedError(
                'Only able to read format version 9. Given file is in format'
                ' version ' + h['ver'])
        self._version_str = h['ver']

        # Get header size
        try:
            # Get number of 512 byte sectors in header
            #header_size = 512 * int(h['nbh'])
            # Seems to be size in bytes!
            header_size = int(h['nbh'])
        except KeyError:    # pragma: no cover
            # Calculate header size based on number of channels
            header_size = (int((int(h['nc']) - 1) / 8) + 1) * 1024

        # Read remaining header data
        if header_size > 1024:  # pragma: no cover
            data += f.read(header_size - 1024).decode(_ENC)
            h = [x.strip().split('=') for x in data.split('\n')]
            h = dict([(x[0].lower(), x[1]) for x in h if len(x) == 2])

        # Tidy up read data
        for k, v in h.items():
            # Convert to appropriate data type
            try:
                t = HEADER_FIELDS[k]
                if t == float:
                    # Allow for windows locale stuff
                    v = v.replace(',', '.')
                self._header[k] = t(v)
            except KeyError:
                self._header_raw[k] = v

        # Convert time
        # No, don't. It's in different formats depending on... user locale?
        # if 'ctime' in header:
        #    print(header['ctime'])
        #    ctime = time.strptime(header['ctime'], "%d/%m/%Y %H:%M:%S")
        #    header['ctime'] = time.strftime('%Y-%m-%d %H:%M:%S', ctime)

        # Get vital fields from header
        self._dt = self._header['dt']       # Sampling interval
        self._nr = self._header['nr']       # Records in file
        self._nc = self._header['nc']       # Channels per record
        try:
            self._np = self._header['np']   # Samples per channel
        except KeyError:
            self._np = (self._header['nbd'] * 512) // (2 * self._nc)

        # Get time units
        self._time_unit = myokit.units.s
        # Time as set by dt (which is what we need) is _always_ in seconds.
        # John Dempster says: "The TU= value referred to the time units which
        # were displayed in early versions of WinWCP and no longer exists in
        # recent WCP data files." (Email to michael, 2023-07-12).

        # Get channel-specific fields
        for i in range(self._nc):
            c = {}
            for k, t in HEADER_CHANNEL_FIELDS.items():
                c[k] = t(h[k + str(i)])
            self._channel_headers.append(c)
            self._channel_names.append(c['yn'])
            self._channel_name_map[c['yn']] = i
            self._channel_units.append(self._unit(c['yu']))

        # Analysis block size and data block size
        # Data is stored as 16 bit integers (little-endian)
        try:
            rab_size = 512 * self._header['nba']
        except KeyError:    # pragma: no cover
            rab_size = header_size
        try:
            rdb_size = 512 * self._header['nbd']
        except KeyError:    # pragma: no cover
            rdb_size = 2 * self._nc * self._np

        # Maximum A/D sample value at vmax
        adcmax = self._header['adcmax']

        # Read data records
        offset = header_size
        for i in range(self._nr):
            # Read analysis block
            f.seek(offset)

            # Status of signal (Accepted or rejected, as string)
            rstatus = f.read(8).decode(_ENC)

            # Type of recording, as string
            rtype = f.read(4).decode(_ENC)

            # Leak subtraction group number (float set by the user)
            group_number = struct.unpack(str('<f'), f.read(4))[0]

            # Time of recording, as float, not sure how to interpret
            rtime = struct.unpack(str('<f'), f.read(4))[0]

            # Sampling interval
            # It is technically possible to have different dts for different
            # records (see email J.D. 2023-07-12), but rare.
            # Not supported here!
            rint = round(struct.unpack(str('<f'), f.read(4))[0], 6)
            if rint != self._dt:  # pragma: no cover
                raise ValueError(
                    'Unsupported feature: WCP file contains more than one'
                    ' sampling rate.')

            # Maximum positive limit of A/D converter voltage range
            vmax = struct.unpack(
                str('<' + 'f' * self._nc), f.read(4 * self._nc))

            # String marker set by user
            marker = f.read(16).decode(_ENC).strip('\x00')

            # Store
            self._record_headers.append({
                'status': rstatus,
                'type': rtype,
                'rtime': rtime,
                'marker': marker,
            })

            # Delete unused
            del rstatus, rtype, group_number, rtime, rint, marker

            # Increase offset beyond analysis block
            offset += rab_size

            # Get data from data block
            data = np.memmap(
                self._path, np.dtype('<i2'), 'r',
                shape=(self._np, self._nc),
                offset=offset,
            )

            # Separate channels and apply scaling
            record = [
                vmx / (adcmax * h['yg']) * data[:, h['yo']].astype('f4')
                for h, vmx in zip(self._channel_headers, vmax)]

            self._records.append(record)

            # Increase offset beyong data block
            offset += rdb_size

        # Create time signal
        self._time = np.arange(self._np) * self._dt

    def __getitem__(self, key):
        return self._records[key]

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return self._nr

    def _channel_id(self, channel_id):
        """ Checks an int or str channel id and returns a valid int. """
        if self._nr == 0:  # pragma: no cover
            raise KeyError(f'Channel {channel_id} not found (empty file).')

        # Handle string
        if isinstance(channel_id, str):
            return self._channel_name_map[channel_id]  # Pass KeyError to user

        int_id = int(channel_id)  # TypeError for user
        if int_id < 0 or int_id >= self._nc:
            raise IndexError(f'channel_id out of range: {channel_id}')
        return int_id

    def channel(self, channel_id, join_sweeps=False):
        # Docstring in SweepSource
        channel_id = self._channel_id(channel_id)
        time, data = [], []
        for r, h in zip(self._records, self._record_headers):
            time.append(self._time + h['rtime'])
            data.append(r[channel_id])
        if join_sweeps:
            return (np.concatenate(time), np.concatenate(data))
        return time, data

    def channels(self):
        """ Deprecated alias of :meth:`channel_count`. """
        # Deprecated since 2023-06-22
        import warnings
        warnings.warn(
            'The method `channels` is deprecated. Please use'
            ' WcpFile.channel_count() instead.')
        return self._nc

    def channel_count(self):
        # Docstring in SweepSource
        return self._nc

    def channel_names(self, index=None):
        # Docstring in SweepSource
        if index is None:
            return list(self._channel_names)
        return self._channel_names[index]

    def channel_units(self, index=None):
        # Docstring in SweepSource
        if index is None:
            return list(self._channel_units)
        return self._channel_units[index]

    def da_count(self):
        # Docstring in SweepSource. Rest is allowed raise NotImplementedError
        return 0

    def equal_length_sweeps(self):
        # Docstring in SweepSource
        return True

    def filename(self):
        """ Returns this file's name. """
        return self._filename

    def info(self):
        """ Deprecated alias of :meth:`meta_str` """
        # Deprecated since 2023-07-12
        import warnings
        warnings.warn(
            'The method `info` is deprecated. Please use `meta_str` instead.')
        return self.meta_str(False)

    def log(self, join_sweeps=False, use_names=False, include_da=True):
        # Docstring in SweepSource

        # Create log
        log = myokit.DataLog()
        if self._nr == 0:  # pragma: no cover
            return log

        # Get channel names
        channel_names = self._channel_names
        if not use_names:
            channel_names = [f'{i}.channel' for i in range(self._nc)]

        # Gather data and return
        if join_sweeps:
            log['time'] = np.concatenate(
                [self._time + h['rtime'] for h in self._record_headers])
            log.cmeta['time']['unit'] = self._time_unit
            for c, name in enumerate(channel_names):
                log[name] = np.concatenate([r[c] for r in self._records])
                log.cmeta[name]['unit'] = self._channel_units[c]
        else:
            # Return individual sweeps
            log['time'] = self._time
            log.cmeta['time']['unit'] = self._time_unit
            for r, record in enumerate(self._records):
                for c, name in enumerate(channel_names):
                    name = f'{r}.{name}'
                    log[name] = record[c]
                    log.cmeta[name]['unit'] = self._channel_units[c]

        # Add meta data
        log.set_time_key('time')
        log.meta['original_format'] = f'WinWCP {self._version_str}'
        log.meta['recording_time'] = self._header['rtime']

        return log

    def matplotlib_figure(self):
        """ Creates and returns a matplotlib figure with this file's data. """
        import matplotlib.pyplot as plt
        f = plt.figure()
        axes = [f.add_subplot(self._nc, 1, 1 + i) for i in range(self._nc)]
        for record in self._records:
            for ax, channel in zip(axes, record):
                ax.plot(self._time, channel)
        return f

    def meta_str(self, verbose=False):
        # Docstring in SweepSource
        h = self._header
        out = []

        # Add file info
        out.append(f'WinWCP file: {self._filename}')
        out.append(f'WinWCP Format version {self._version_str}')
        out.append(f'Recorded on: {h["rtime"]}')

        # Basic records info
        out.append(f'  Number of records: {self._nr}')
        out.append(f'  Channels per record: {self._nc}')
        out.append(f'  Samples per channel: {self._np}')
        out.append(f'  Sampling interval: {self._dt} s')

        # Channel info
        for c in self._channel_headers:
            out.append(f'A/D channel: {c["yn"]}')
            out.append(f'  Unit: {c["yu"]}')

        # Record info
        out.append(
            'Records: Type, Status, Sampling Interval, Start, Marker')
        for i, r in enumerate(self._record_headers):
            out.append(f'Record {i}: {r["type"]}, {r["status"]},'
                       f' {r["rtime"]}, "{r["marker"]}"')

        # Parsed and unparsed header
        if verbose:
            out.append(f'{"-" * 35} header {"-" * 35}')
            for k, v in self._header.items():
                out.append(f'{k}: {v}')

            out.append(f'{"-" * 33} raw header {"-" * 33}')
            for k, v in self._header_raw.items():
                out.append(f'{k}: {v}')

        return '\n'.join(out)

    def myokit_log(self):
        """
        Deprecated method. Please use ``WcpFile.log(use_names=True)`` instead.
        """
        # Deprecated since 2023-06-22
        import warnings
        warnings.warn(
            'The method `myokit_log` is deprecated. Please use'
            ' WcpFile.log(use_names=True) instead.')
        return self.log(self)

    def path(self):
        """ Returns the path to this file. """
        return self._path

    def plot(self):
        """
        Deprecated method, please use :meth:`matplotlib_figure()` instead.

        Creates and shows a matplotlib figure of all data in this file.
        """
        # Deprecated since 2023-06-22
        import warnings
        warnings.warn(
            'The method `plot` is deprecated. Please use'
            ' WcpFile.matplotlib_figure() instead.')

        import matplotlib.pyplot as plt
        self.matplotlib_figure()
        plt.show()

    def record_count(self):
        """ Alias of :meth:`sweep_count`. """
        return self._nr

    def records(self):
        """ Deprecated alias of :meth:`sweep_count`. """
        # Deprecated since 2023-06-22
        import warnings
        warnings.warn(
            'The method `records` is deprecated. Please use'
            ' WcpFile.record_count() instead.')

        return self._nr

    def sample_count(self):
        """ Returns the number of samples in each channel. """
        return self._np

    def sweep_count(self):
        # Docstring in SweepSource
        return self._nr

    def time_unit(self):
        # Docstring in SweepSource
        return self._time_unit

    def times(self):
        """ Returns the time points sampled at. """
        return np.array(self._time)

    def _unit(self, unit_string):
        """ Parses a unit string and returns a :class:`myokit.Unit`. """
        try:
            return self._unit_cache[unit_string]
        except KeyError:
            unit = myokit.parse_unit(unit_string)
            self._unit_cache[unit_string] = unit
            return unit

    def values(self, record, channel):
        """
        Returns the values of channel ``channel``, recorded in record
        ``record``.
        """
        return self._records[record][channel]

    def version(self):
        """ Returns this file's version, as a string. """
        return self._version_str


HEADER_FIELDS = {
    'ver': int,        # WCP data file format version number
    'ctime': str,      # Create date/time
    'rtime': str,      # Start of recording time
    'nc': int,         # No. of channels per record
    'nr': int,         # No. of records in the file.
    'nbh': int,        # No. of 512 byte sectors in file header block
    'nba': int,        # No. of 512 byte sectors in a record analysis block
    'nbd': int,        # No. of 512 byte sectors in a record data block
    'ad': float,       # A/D converter input voltage range (V)
    'adcmax': int,     # Maximum A/D sample value
    'np': int,         # No. of A/D samples per channel
    'dt': float,       # A/D sampling interval (s)
    'nz': int,         # No. of samples averaged to calculate a zero level.
    'id': str,         # Experiment identification line
}


HEADER_CHANNEL_FIELDS = {
    'yn': str,         # Channel name
    'yu': str,         # Channel units
    'yg': float,       # Channel gain factor mV/units
    'yz': int,         # Channel zero level (A/D bits)
    'yo': int,         # Channel offset into sample group in data block
    'yr': int,         # ADCZeroAt, probably for old files
}
#TODO: Find out if we need to do something with yz and yg
