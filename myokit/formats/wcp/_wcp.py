#
# This module reads files in WCP format
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import struct
import numpy as np

import myokit

# Encoding of text portions of wcp file
_ENC = 'ascii'


class WcpFile(object):
    """
    Represents a read-only WinWCP file (``.wcp``), stored at the location
    pointed to by ``filepath``.

    Only files in the newer file format version 9 can be read. This version of
    the format was introduced in 2010. New versions of WinWCP can read older
    files and will convert them to the new format automatically when opened.

    WinWCP is a tool for recording electrophysiological data written by John
    Dempster of Strathclyde University.

    WinWCP files contain a number of records ``NR``, each containing data from
    ``NC`` channels. Every channel has the same length, ``NP`` samples.
    Sampling happens at a fixed sampling rate.
    """
    def __init__(self, filepath):
        # The path to the file and its basename
        # Ensure it's a `str` for Python2/3 compatibility
        filepath = str(filepath)
        self._filepath = os.path.abspath(filepath)
        self._filename = os.path.basename(filepath)

        # Records
        self._records = None
        self._channel_names = None
        self._nr = None     # Records in file
        self._nc = None     # Channels per record
        self._np = None     # Samples per channel
        #self._dt = None     # Sampling interval

        # Time signal
        self._time = None

        # Read the file
        with open(filepath, 'rb') as f:
            self._read(f)

    def _read(self, f):
        """
        Reads the file header & data.
        """
        # Header size is between 1024 and 16380, depending on number of
        # channels in the file following:
        #   n = (int((n_channels - 1)/8) + 1) * 1024
        # Read first part of header, determine version and number of channels
        # in the file
        data = f.read(1024)
        h = [x.strip().split(b'=') for x in data.split(b'\n')]
        h = dict([(x[0].lower(), x[1]) for x in h if len(x) == 2])
        if int(h[b'ver']) != 9:
            raise NotImplementedError(
                'Only able to read format version 9. Given file is in format'
                ' version ' + str(h[b'ver']))

        # Get header size
        try:
            # Get number of 512 byte sectors in header
            #header_size = 512 * int(h[b'nbh'])
            # Seems to be size in bytes!
            header_size = int(h[b'nbh'])
        except KeyError:    # pragma: no cover
            # Calculate header size based on number of channels
            header_size = (int((int(h[b'nc']) - 1) / 8) + 1) * 1024

        # Read remaining header data
        if header_size > 1024:  # pragma: no cover
            data += f.read(header_size - 1024)
            h = [x.strip().split(b'=') for x in data.split(b'\n')]
            h = dict([(x[0].lower(), x[1]) for x in h if len(x) == 2])

        # Tidy up read data
        header = {}
        header_raw = {}
        for k, v in h.items():
            # Convert to appropriate data type
            try:
                t = HEADER_FIELDS[k]
                if t == float:
                    # Allow for windows locale stuff
                    v = v.replace(b',', b'.')
                header[k] = t(v)
            except KeyError:
                header_raw[k] = v

        # Convert time
        # No, don't. It's in different formats depending on... the version?
        # if 'ctime' in header:
        #    print(header[b'ctime'])
        #    ctime = time.strptime(header[b'ctime'], "%d/%m/%Y %H:%M:%S")
        #    header[b'ctime'] = time.strftime('%Y-%m-%d %H:%M:%S', ctime)

        # Get vital fields from header
        # Records in file
        self._nr = header[b'nr']

        # Channels per record
        self._nc = header[b'nc']
        try:
            # Samples per channel
            self._np = header[b'np']
        except KeyError:
            self._np = (header[b'nbd'] * 512) // (2 * self._nc)

        # Get channel specific fields
        channel_headers = []
        self._channel_names = []
        for i in range(self._nc):
            j = str(i).encode(_ENC)
            c = {}
            for k, t in HEADER_CHANNEL_FIELDS.items():
                c[k] = t(h[k + j])
            channel_headers.append(c)
            self._channel_names.append(c[b'yn'].decode(_ENC))

        # Analysis block size and data block size
        # Data is stored as 16 bit integers (little-endian)
        try:
            rab_size = 512 * header[b'nba']
        except KeyError:    # pragma: no cover
            rab_size = header_size
        try:
            rdb_size = 512 * header[b'nbd']
        except KeyError:    # pragma: no cover
            rdb_size = 2 * self._nc * self._np

        # Maximum A/D sample value at vmax
        adcmax = header[b'adcmax']

        # Read data records
        records = []
        offset = header_size
        for i in range(self._nr):
            # Read analysis block
            f.seek(offset)

            # Status of signal (Accepted or rejected, as string)
            rstatus = f.read(8)

            # Type of recording, as string
            rtype = f.read(4)

            # Group number (float set by the user)
            # Note: First argument to struct.unpack must be a str (so bytes on
            # Python 2).
            group_number = struct.unpack(str('<f'), f.read(4))[0]

            # Time of recording, as float, not sure how to interpret
            rtime = struct.unpack(str('<f'), f.read(4))[0]

            # Sampling interval: pretty sure this should be the same as the
            # file wide one in header[b'dt']
            rint = struct.unpack(str('<f'), f.read(4))[0]

            # Maximum positive limit of A/D converter voltage range
            vmax = struct.unpack(
                str('<' + 'f' * self._nc), f.read(4 * self._nc))

            # String marker set by user
            marker = f.read(16)

            # Delete unused
            del rstatus, rtype, group_number, rtime, rint, marker

            # Increase offset beyond analysis block
            offset += rab_size

            # Get data from data block
            data = np.memmap(
                self._filepath, np.dtype('<i2'), 'r',
                shape=(self._np, self._nc),
                offset=offset,
            )

            # Separate channels and apply scaling
            record = []
            for j in range(self._nc):
                h = channel_headers[j]
                s = float(vmax[j]) / float(adcmax) / float(h[b'yg'])
                d = np.array(data[:, h[b'yo']].astype('f4') * s)
                record.append(d)
            records.append(record)

            # Increase offset beyong data block
            offset += rdb_size

        self._records = records

        # Create time signal
        self._time = np.arange(self._np) * header[b'dt']

    def channels(self):
        """
        Returns the number of channels in this file.
        """
        return self._nc

    def channel_names(self):
        """
        Returns the names of the channels in this file.
        """
        return list(self._channel_names)

    def filename(self):
        """
        Returns the current file's name.
        """
        return self._filename

    def myokit_log(self):
        """
        Creates and returns a:class:`myokit.DataLog` containing all the
        data from this file.

        Each channel is stored under its own name, with an indice indicating
        the record it was from. Time is stored under ``time``.
        """
        log = myokit.DataLog()
        log.set_time_key('time')
        log['time'] = np.array(self._time)
        for i, record in enumerate(self._records):
            for j, data in enumerate(record):
                name = self._channel_names[j]
                log[name, i] = np.array(data)
        return log

    def path(self):
        """
        Returns the path to the currently opened file.
        """
        return self._filepath

    def plot(self):
        """
        Creates matplotlib plots of all data in this file.
        """
        import matplotlib.pyplot as plt
        for record in self._records:
            plt.figure()
            for k, channel in enumerate(record):
                plt.subplot(self._nc, 1, 1 + k)
                plt.plot(self._time, channel)
        plt.show()

    def records(self):
        """
        Returns the number of records in this file.
        """
        return self._nr

    #def sampling_interval(self):
    #    """
    #    Returns the sampling interval used in this file.
    #    """
    #    return self._dt

    def times(self):
        """
        Returns the time points sampled at.
        """
        return np.array(self._time)

    def values(self, record, channel):
        """
        Returns the values of channel ``channel``, recorded in record
        ``record``.
        """
        return self._records[record][channel]


HEADER_FIELDS = {
    b'ver': int,        # WCP data file format version number
    b'ctime': bytes,    # Create date/time
    b'nc': int,         # No. of channels per record
    b'nr': int,         # No. of records in the file.
    b'nbh': int,        # No. of 512 byte sectors in file header block
    b'nba': int,        # No. of 512 byte sectors in a record analysis block
    b'nbd': int,        # No. of 512 byte sectors in a record data block
    b'ad': float,       # A/D converter input voltage range (V)
    b'adcmax': int,     # Maximum A/D sample value
    b'np': int,         # No. of A/D samples per channel
    b'dt': float,       # A/D sampling interval (s)
    b'nz': int,         # No. of samples averaged to calculate a zero level.
    b'tu': bytes,       # Time units
    b'id': bytes,       # Experiment identification line
}


HEADER_CHANNEL_FIELDS = {
    b'yn': bytes,       # Channel name
    b'yu': bytes,       # Channel units
    b'yg': float,       # Channel gain factor mV/units
    b'yz': int,         # Channel zero level (A/D bits)
    b'yo': int,         # Channel offset into sample group in data block
    b'yr': int,         # ADCZeroAt, probably for old files
}
#TODO: Find out if we need to do something with yz and yg
