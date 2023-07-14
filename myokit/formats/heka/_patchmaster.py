#
# This module reads files in HEKA Patchmaster format.
#
# Specifically, it targets the 2x90.2 format.
#
# It has not been extensively tested.
#
# Notes:
#  - HEKA publishes a lot of information about its file format on its FTP
#    server: server.hekahome.de
#    This can be accessed using name and password "anonymous".
#    Unfortunately, it describes all of the fields and gives their names, but
#    gives very little guidance on how to interpret them.
#  - However, PatchMaster is quite "close to the bone", so a lot can be learned
#    from the manual. In particular:
#      - Section 10.9. Channel Settings for DA Output and AD Input
#      - Section 10.10. Segments
#      - Chapter 14. Parameters Window
#  - At the moment, the code interprets "BYTE" in HEKA terms as a "signed char"
#    or 'b': https://docs.python.org/3/library/struct.html#format-characters
#    However, for most fields unsigned would have been more sensible, so maybe
#    it's that?
#  - Stimulus support is minimal: even with the manual it's not very clear what
#    all the increment/decrement types should do. E.g. no examples with odd
#    numbers of steps are given; the manual mentions two types of log
#    interpretation but there is no obvious field to select one; a "toggle"
#    mode is mentioned in the manual but again is not easy to find in the file.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import datetime
import enum
import os
import struct
import warnings

import numpy as np

import myokit


#
# From DataFile_v9.txt
# (* BundleHeader   = RECORD *)
# oSignature        =   0;    (* ARRAY[0..7] OF CHAR *)
# oVersion          =   8;    (* ARRAY[0..31] OF CHAR *)
# oTime             =  40;    (* LONGREAL *)
# oItems            =  48;    (* INT32 *)
# oIsLittleEndian   =  52;    (* BOOLEAN *)
# oReserved         =  53;    (* ARRAY[0..10] OF CHAR *)
# oBundleItems      =  64;    (* ARRAY[0..11] OF BundleItem *)
# BundleHeaderSize  = 256;      (* = 32 * 8 *)
#
# (* BundleItem     = RECORD *)
# oStart            =   0;    (* INT32 *)
# oLength           =   4;    (* INT32 *)
# oExtension        =   8;    (* ARRAY[0..7] OF CHAR *)
# BundleItemSize    =  16;      (* = 2 * 8 *)
#
# See also Manual 14.1.1 Root
#
class PatchMasterFile:
    """
    Provides read-only access to data stored in HEKA PatchMaster ("bundle")
    files (``.dat``), stored at ``filepath``.

    Data loading is "lazy", meaning that data is only read when requested. This
    means the file stays open, and so :meth:`close()` must be called after
    using a `PatchMasterFile`. To ensure this happens, use ``with``::

        with PatchMasterFile('my-file.dat') as f:
            for group in f:
                print(group.label)

    Each file contains a hierarchy of :class:`Group`, :class:`Series`,
    :class:`Sweep` and :class:`Trace` objects. For example, each "group" might
    represent a single cell, and each "series" will be a protocol (called a
    "stimulus") run on that cell. Groups are named by the user. Series are
    named after the "stimulus" they run. Sweeps are usually unnamed (although
    they do have a ``label`` property), and channels are named by the user.

    To access groups, index them by integer, or use the :meth:`group` method to
    find the first group with a given label::

        with PatchMasterFile('my-file.dat') as f:
            group_0 = f[0]
            group_x = f.group('Experiment X')

    Series, sweeps, and traces are accessed with integers::


        with PatchMasterFile('my-file.dat') as f:
            group = f.group('Experiment X')
            series = group[0]
            sweep = series[0]
            trace = sweep[0]

    Each object in the hierarchy can be iterated over::

        with PatchMasterFile('my-file.dat') as f:
            for group in f:
                for series in group:
                    for sweep in series:
                        for trace in sweep:
                            ...

    To see only completed series (where all sweeps were run to finish), use::

        with PatchMasterFile('my-file.dat') as f:
            for group in f:
                for series in group.complete_series():
                    ...

    The :class:`Series` class implements the
    :class:`myokit.formats.SweepSource` interface::

        with PatchMasterFile('my-file.dat') as f:
            for group in f:
                for series in group.complete_series():
                    log = series.log()

    """
    def __init__(self, filepath):
        warnings.warn(
            'PatchMaster file reading is new: There are no unit tests yet.')

        # The path to the file and its basename
        self._filepath = os.path.abspath(filepath)
        self._filename = os.path.basename(filepath)

        # File format version
        self._version = None

        # File handle
        self._handle = f = open(self._filepath, 'rb')

        # Check that this is a "bundle" file.
        sig = f.read(8).decode(_ENC)
        if sig[:4] == 'DATA ':
            raise NotImplementedError(
                'Older version not supported.')
        elif sig[:4] == 'DAT1':
            raise NotImplementedError(
                'Only bundle files are supported.')
        elif sig[:4] != 'DAT2':
            raise NotImplementedError(
                'Older version or not recognised as HEKA PatchMaster'
                ' format.')

        # Read remaining bundle header

        # Version number and software time
        self._version = f.read(32).decode(_ENC)
        try:
            self._version = self._version[:self._version.index('\x00')]
        except ValueError:
            pass

        if not self._version.startswith('v2x90.2'):
            warnings.warn('Only PatchMaster version v2x90.2 is supported.')

        # Endianness
        f.seek(52)
        is_little_endian = struct.unpack('?', f.read(1))
        r = EndianAwareReader(f, is_little_endian)

        # Last time this file was opened for modification
        f.seek(40)
        self._time = r.time()

        # Number of valid bundle items
        n_items = r.read('i')[0]  # Note: Unsigned would make more sense?

        # Skip endianness and "reserved" bits
        f.seek(12, 1)  # 1 = offset from current position

        # Read bundle items
        self._items = {
            '.dat': None,  # Raw data file
            '.pul': None,  # Pulsed Tree file --> Acquisition parameters
                           # and pointer to raw data.
            '.pgf': None,  # Stimulus template Tree file --> Information on the
                           # stimulus protocols.
            '.sol': None,  # Solutions Tree file
            '.onl': None,  # Analysis Tree file
            '.mth': None,  # Method file
            '.mrk': None,  # Marker file
            '.amp': None,  # Amplifier (when multiple amplifiers are used)
            '.txt': None,  # Notebook
        }
        self._f_onl = None    # Analysis file
        for i in range(12):
            start = r.read('i')[0]  # Again, unsigned would make sense
            size = r.read('i')[0]
            ext = r.str(8)
            if size == 0:
                continue

            try:
                item = self._items.get(ext)
            except KeyError:        # pragma: no-cover
                raise NotImplementedError(
                    'Unsupported bundle item: ' + ext)
            if item is not None:    # pragma: no-cover
                raise ValueError(
                    'Invalid or unsupported file. Bundle item appears'
                    ' more than once: ' + ext)
            self._items[ext] = (start, size)

        # Read stimulus template
        f.seek(self._items['.pgf'][0])
        self._stimulus_tree = TreeNode.read(
            self, f, (StimulusFile, Stimulus, StimulusChannel, Segment))

        # Read pulsed tree
        f.seek(self._items['.pul'][0])
        self._pulsed_tree = TreeNode.read(
            self, f, (PulsedFile, Group, Series, Sweep, Trace))

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self._handle.close()

    def __iter__(self):
        return iter(self._pulsed_tree)

    def close(self):
        """
        Closes this file: no new data can be read once this has been called.
        """
        self._handle.close()

    def group(self, label):
        """ Returns the first :class`Group` matching the given ``label``. """
        for g in self:
            if g.label() == label:
                return g
        raise KeyError(f'Group not found: {label}')

    def stimulus_tree(self):
        """ Returns this file's stimulus tree. """
        return self._stimulus_tree


class EndianAwareReader:
    """
    Used by :class:`PatchmasterFile` and its supporting classes when reading
    from an open file handle that may be either big or little endian.

    This class may be useful when extending the patchmaster file reading, or to
    read other HEKA formats. To read a patchmaster file, use the
    ``PatchMasterFile`` class.
    """

    def __init__(self, handle, is_little_endian):
        self._f = handle
        self._e = '<' if is_little_endian else '>'

    def read(self, form):
        """ Read and unpack using the struct format ``form``. """
        #if offset is not None:
        #    f.seek(offset)
        return struct.unpack(
            self._e + form, self._f.read(struct.calcsize(form)))

    def read1(self, form):
        """
        Returns the first item from a call to ``read(form)``.

        This is useful for the many cases where a single number is read.
        """
        return self.read(form)[0]

    def str(self, size):
        """ Read and unpack a string of at most length ``size``. """
        b = struct.unpack(f'{size}s', self._f.read(size))[0]
        b = b.decode(_ENC)
        try:
            return b[:b.index('\x00')]
        except ValueError:
            return b

    def time(self):
        """
        Reads a time in HEKA's seconds-since-1990 format, converts it, and
        returns a ``datetime`` object.
        """
        t = struct.unpack(f'{self._e}d', self._f.read(8))[0]
        return datetime.datetime.fromtimestamp(t + _ts_1990, tz=_tz)


class TreeNode:
    """
    Base class for objects within a PatchMaster file that form a tree.

    This class may be useful when extending the patchmaster file reading, or to
    read other HEKA formats. To read a patchmaster file, use the
    ``PatchMasterFile`` class.

    For subclasses:

    When reading a file, :class:`TreeNode` objects will be created by (1)
    calling the constructor with a ``parent`` but no children. (2) Calling the
    method :meth:`_read_properties` which should read record properties from
    the open file handle and update the ``TreeNode`` accordingly. (3) Calling
    the method :meth:`_read_finalize`, which can handl any actions that require
    children to have been added.
    """
    def __init__(self, parent):
        self._parent = parent
        self._children = []
        try:
            self._file = parent._file
        except AttributeError:
            self._file = parent

    def __len__(self):
        return len(self._children)

    def __getitem__(self, key):
        return self._children[key]

    def __iter__(self):
        return iter(self._children)

    def parent(self):
        """ Returns this tree TreeNode's parent. """
        return self._parent

    @staticmethod
    def read(pfile, handle, levels):
        """
        Reads a full HEKA "Tree" structure.

        Arguments:

        ``pfile``
            A :class:`PatchMasterFile`.
        ``handle``
            An file handle, open at the tree root.
        ``levels``
            The classes to use for each tree level.

        Returns a TreeNode representing the tree's root.
        """
        # Get endianness
        m = handle.read(4).decode(_ENC)
        if m == 'Tree':
            is_little_endian = False
        elif m == 'eerT':
            is_little_endian = True
        else:
            raise ValueError(   # pragma: no-cover
                'Invalid or unsupported file: Unable to read tree.')
        reader = EndianAwareReader(handle, is_little_endian)

        # Number of levels in this tree
        n = reader.read1('i')
        sizes = reader.read(n * 'i')
        if n != len(levels):
            raise ValueError(
                'Unexpected number of levels found in tree: expected'
                f' ({len(levels)}), found ({n}).')

        # Go!
        return TreeNode._read(pfile, handle, reader, levels, sizes)

    @staticmethod
    def _read(parent, handle, reader, levels, sizes, depth=0):
        """
        Recursively reads a node and its children.

        Arguments:

        ``parent``
            The parent node to the one being read. For the root object,
            ``parent`` is the :class:`PatchMasterFile`.
        ``handle``
            A file handle, open at the record contents.
        ``reader``
            A :class:`Reader` object using the handle.
        ``levels``
            A list of classes to use for each level. The current level is
            ``levels[depth]``.
        ``sizes``
            A list of record contents sizes. The current record size is
            ``sizes[depth]``.
        ``depth``
            The current level being read.

        """
        # Create node
        node = levels[depth](parent)

        # Read properties
        pos = handle.tell()
        node._read_properties(handle, reader)

        # Add kids
        handle.seek(pos + sizes[depth])
        n = reader.read1('i')
        for i in range(n):
            node._children.append(TreeNode._read(
                node, handle, reader, levels, sizes, depth + 1))

        # Finalize and return
        node._read_finalize()
        return node

    def _read_properties(self, handle, reader):
        """
        Reads information from the file ``handle``, open at this node's record
        start, and sets any properties not relating to the node's children.

        For arguments meanings, see :meth:`_read`.
        """
        pass

    def _read_finalize(self):
        """
        Performs any initialization actions that require children to have
        already been set.
        """
        pass


#
# From PulsedFile_v9.txt
# RoVersion            =   0; (* INT32 *)
# RoMark               =   4; (* INT32 *)
# RoVersionName        =   8; (* String32Type *)
# RoAuxFileName        =  40; (* String80Type *)
# RoRootText           = 120; (* String400Type *)
# RoStartTime          = 520; (* LONGREAL *)
# RoMaxSamples         = 528; (* INT32 *)
# RoCRC                = 532; (* CARD32 *)
# RoFeatures           = 536; (* SET16 *)
#   RoFiller1         = 538; (* INT16 *)
#   RoFiller2         = 540; (* INT32 *)
# RoTcEnumerator       = 544; (* ARRAY[0..Max_TcKind_M1] OF INT16 *)
# RoTcKind             = 608; (* ARRAY[0..Max_TcKind_M1] OF INT8 *)
# RootRecSize          = 640;      (* = 80 * 8 *)
#
# See also manual 14.1.1 Root
#
class PulsedFile(TreeNode):
    """
    Represents the "pulsed file" section of a PatchMaster bundle (.pul).

    Each ``PulsedFile`` contains zero or more :class:`Group` objects.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._version = None
        self._time = None

    def _read_properties(self, handle, reader):
        # See TreeNode._read_properties
        start = handle.tell()
        handle.seek(start + 8)
        self._version = reader.str(32)
        handle.seek(start + 520)
        self._time = reader.time()

    def time(self):
        """ Returns the time this file was created as a ``datetime``. """
        return self._time

    def version(self):
        """
        Returns a (hard-to-parse) string representation of this file's
        PatchMaster format version.
        """
        return self._version


#
# From PulsedFile_v9.txt
# GrMark               =   0; (* INT32 *)
# GrLabel              =   4; (* String32Size *)
# GrText               =  36; (* String80Size *)
# GrExperimentNumber   = 116; (* INT32 *)
# GrGroupCount         = 120; (* INT32 *)
# GrCRC                = 124; (* CARD32 *)
# GrMatrixWidth        = 128; (* LONGREAL *)        For imaging
# GrMatrixHeight       = 136; (* LONGREAL *)        For imaging
# GroupRecSize         = 144;      (* = 18 * 8 *)
#
# See also manual 14.1.2 Group
#
class Group(TreeNode):
    """
    A PatchMaster group containing zero or more :class:`Series` objects.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._label = None
        self._number = None

    def _read_properties(self, handle, reader):
        # See TreeNode._read_properties
        mark = reader.read1('i')
        self._label = reader.str(32)
        text = reader.str(80)
        self._number = reader.read1('i')

    def __str__(self):
        return f'{self._label} ({len(self)} series)'

    def complete_series(self):
        """
        Returns an iterator over this group's complete series.

        See :meth:`Series.is_complete()`.
        """
        return filter(lambda series: series.is_complete(), self)

    def label(self):
        """ Returns this group's string label. """
        return self._label

    def number(self):
        """ Returns this group's number (an integer index). """
        return self._number

    def series(self, label, n=0, complete_only=False):
        """
        Returns the first series with the given ``label``.

        If ``n`` is specified it returns the n+1th such series (i.e. the first
        for n=0, the second for n=1, etc.).
        """
        i = 0
        for series in (self.complete_series() if complete_only else self):
            if series.label() == label:
                if i == n:
                    return series
                i += 1
        raise ValueError('Unable to find the requested series.')


#
# From PulsedFile_v9.txt
# (* SeriesRecord      = RECORD *)
# SeMark               =   0; (* INT32 *)
# SeLabel              =   4; (* String32Type *)
# SeComment            =  36; (* String80Type *)
# SeSeriesCount        = 116; (* INT32 *)
# SeNumberSweeps       = 120; (* INT32 *)
# SeAmplStateOffset    = 124; (* INT32 *)
# SeAmplStateSeries    = 128; (* INT32 *)
# SeMethodTag          = 132; (* INT32 *)
# SeTime               = 136; (* LONGREAL *)
# SePageWidth          = 144; (* LONGREAL *)
# SeSwUserParamDescr   = 152; (* ARRAY[0..3] OF UserParamDescrType = 4*40 *)
# SeMethodName         = 312; (* String32Type *)
# SeSeUserParams1      = 344; (* ARRAY[0..3] OF LONGREAL *)
# SeLockInParams       = 376; (* SeLockInSize = 96, see "Pulsed.de" *)
# SeAmplifierState     = 472; (* AmplifierStateSize = 400 *)
# SeUsername           = 872; (* String80Type *)
# SeSeUserParamDescr1  = 952; (* ARRAY[0..3] OF UserParamDescrType = 4*40 *)
#   SeFiller1         = 1112; (* INT32 *)
# SeCRC                = 1116; (* CARD32 *)
# SeSeUserParams2      = 1120; (* ARRAY[0..3] OF LONGREAL *)
# SeSeUserParamDescr2  = 1152; (* ARRAY[0..3] OF UserParamDescrType = 4*40 *)
# SeScanParams         = 1312; (* ScanParamsSize = 96 *)
# SeriesRecSize        = 1408;     (* = 176 * 8 *)
#
# See also manual 14.1.3 Series
#
class Series(TreeNode, myokit.formats.SweepSource):
    """
    A PatchMaster "series", containing zero or more :class:`Sweep` objects.

    The data in a :class:`Series` can be obtained from its child :class:`Sweep`
    and :class:`Trace` objects, or via the unified
    :class:`myokit.formats.SweepSource` interface.

    An example of native access::

        for sweep in series:
            for trace in sweep:
                time, data = trace.times(), trace.values()

    An example using the ``SweepSource`` interface::

        log = trace.log(join_sweeps=False, use_names=False)
        time = log.time()
        data = log['0.0.channel']

    """
    def __init__(self, parent):
        super().__init__(parent)

        self._label = None
        self._time = None

        self._channel_names = None
        self._channel_units = None

        # Info from stimulus file
        self._stimulus = None
        self._intended_sweep_count = None
        self._sweep_interval = None
        self._sweep_durations = None
        self._sweep_starts_s = None

        # Info from sweeps
        self._sweep_starts_r = None

    def _read_properties(self, handle, reader):
        # See TreeNode._read_properties
        i = handle.tell()
        handle.seek(i + 4)      # SeLabel
        self._label = reader.str(32)
        handle.seek(i + 136)    # SeTime
        self._time = reader.time()
        # handle.seek(i + 472)    # SeAmplifierState = 472; (* Size = 400 *)
        # self._amplifier_state = AmplifierState(handle, reader)

    def _read_finalize(self):
        # See TreeNode._read_finalize

        # Recorded channels
        if len(self) == 0 or len(self[0]) == 0:
            self._channel_names = []
            self._channel_units = []
        else:
            self._channel_names = [c.label() for c in self[0]]
            self._channel_units = [c.value_unit() for c in self[0]]

            # Get intended sweep count
            tree = self._file.stimulus_tree()
            self._stimulus = tree[self[0]._stimulus_id]
            self._intended_sweep_count = self._stimulus.sweep_count()

            # Get sweep interval (delay between sweeps)
            self._sweep_interval = self._stimulus.sweep_interval()

            # Get intended sweep durations
            self._sweep_durations = self._stimulus.sweep_durations()

            # Derive sweep starts from stimulus info
            self._sweep_starts_s = np.zeros(self._sweep_durations.shape)
            self._sweep_starts_s[1:] = (
                np.cumsum(self._sweep_durations[:-1]) + self._sweep_interval)

            # Get sweep starts based on time
            t0 = self[0].time()
            self._sweep_starts_r = [
                (s.time() - t0).total_seconds() for s in self]

        # Either 0 or 1 supported D/A output
        c = self._stimulus.supported_channel()
        if c is None:
            self._da_names = []
            self._da_units = []
        else:
            self._da_names = ['Stim-DA']
            self._da_units = [c.unit()]

    def __str__(self):
        if len(self) == self._intended_sweep_count:
            return f'{self._label} ({len(self)} sweeps)'
        return (f'{self._label} (partial: {len(self)} out of'
                f' {self._intended_sweep_count} sweeps)')

    def channel(self, channel_id, join_sweeps=False,
                use_real_start_times=False):
        """
        Implementation of :meth:`myokit.formats.SweepSource.channel`.

        Sweep starts in the Patchmaster format can be derived from the stimulus
        information (the intended start) or from the logged system time at the
        start of each sweep. Ideally these should be the same. By default the
        intended start times are used, but this can be changed to the system
        clock derived times by setting ``use_real_start_times=True``.
        """
        # Check channel id
        if isinstance(channel_id, str):
            channel_id = self._channel_names.index(channel_id)
        else:
            self._channel_names[channel_id]  # IndexError/TypeError to user

        # Get sweep starts
        offsets = self._sweep_starts_s
        if use_real_start_times:
            offset = self._sweep_starts_r

        # Gather data and return
        time, data = [], []
        for sweep, offset in zip(self, offsets):
            time.append(offset + sweep[channel_id].times())
            data.append(sweep[channel_id].values())
        if join_sweeps:
            return (np.concatenate(time), np.concatenate(data))
        return time, data

    def channel_count(self):
        # Docstring in SweepSource
        return len(self._channel_names)

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

    def _da_id(self, output_id=None):
        """ Checks an output_id is OK - just to conform to the interface. """
        if output_id is None:
            output_id = 0

        if isinstance(output_id, str):
            output_id = self._da_names.index(output_id)
        else:
            self._da_names[output_id]  # IndexError/TypeError to user

    def da(self, output_id=None, join_sweeps=False):
        # Docstring in SweepSource
        self._da_id(output_id)
        return self._stimulus.reconstruction(join_sweeps)

    def da_count(self):
        # Docstring in SweepSource
        return len(self._da_names)

    def da_names(self, index=None):
        # Docstring in SweepSource
        if index is None:
            return list(self._da_names)
        return self._da_names[index]

    def da_protocol(self, output_id=None, tu='ms', vu='mV', cu='pA',
                    n_digits=9):
        # Docstring in SweepSource
        self._da_id(output_id)
        return self._stimulus.protocol(tu='ms', vu='mV', cu='pA', n_digits=9)

    def da_units(self, index=None):
        # Docstring in SweepSource
        if index is None:
            return list(self._da_units)
        return self._da_units[index]

    def equal_length_sweeps(self):
        # Docstring in SweepSource

        # Assuming this is always true right now:
        #  - assuming sweeps have same data size in is_complete
        return True

    def is_complete(self):
        """
        Returns ``False`` if this series was aborted before the recording was
        completed.

        At the moment, this only checks if the number of sweeps matches the
        intended sweep count. It does not check if the final sweep contains the
        intended number of data points.

        """
        if len(self) != self._intended_sweep_count:
            return False

        #n0 = [channel._n for channel in self[0]]
        #n1 = [channel._n for channel in self[-1]]
        #return n0 == n1
        return True

    def label(self):
        """ Returns this series's label. """
        return self._label

    def log(self, join_sweeps=False, use_names=False, include_da=True,
            use_real_start_times=False):
        """
        See :meth:`myokit.formats.SweepSource.log`.

        Sweep starts in the Patchmaster format can be derived from the stimulus
        information (the intended start) or from the logged system time at the
        start of each sweep. This method uses the intended start times, but
        this can be changed by setting ``use_real_start_times=True``.
        """

        # Create log
        log = myokit.DataLog()
        ns = len(self)
        if ns == 0:  # pragma: no cover
            return log

        # Get channel names
        channel_names = self._channel_names
        da_names = self._da_names
        if not use_names:
            channel_names = [f'{i}.channel' for i in range(len(channel_names))]
            da_names = [f'{i}.da' for i in range(len(da_names))]

        # Populate log
        if join_sweeps:
            # Join sweeps
            offsets = (self._sweep_starts_r if use_real_start_times
                       else self._sweep_starts_s)
            log['time'] = np.concatenate(
                [offset + s[0].times() for s, offset in zip(self, offsets)])
            for c, name in enumerate(channel_names):
                log[name] = np.concatenate(
                    [sweep[c].values() for sweep in self])
            if include_da and len(da_names) == 1:
                log[da_names[0]] = self.da(join_sweeps=True)[1]

        else:
            # Individual sweeps
            log['time'] = self[0][0].times()
            for i, sweep in enumerate(self):
                for j, name in enumerate(channel_names):
                    log[name, i] = sweep[j].values()
            if include_da and len(da_names) == 1:
                _, vs = self.da(join_sweeps=False)
                for i, v in enumerate(vs):
                    log[da_names[0], i] = v

        log.set_time_key('time')
        return log

    def meta_str(self, verbose=False):
        # Docstring in SweepSource

        # TODO: Can add so much more here!
        return str(self)

    def stimulus(self):
        """ Returns the :class:`Stimulus` linked to this series. """
        return self._stimulus

    def sweep_count(self):
        # Docstring in SweepSource
        return len(self)

    def time(self):
        """ Returns the time this series was created as a ``datetime``. """
        return self._time

    def time_unit(self):
        # Docstring in SweepSource
        return myokit.units.s


#
# From PulsedFile_v9.txt
# (* SweepRecord       = RECORD *)
# SwMark               =   0; (* INT32 *)
# SwLabel              =   4; (* String32Type *)
# SwAuxDataFileOffset  =  36; (* INT32 *)
# SwStimCount          =  40; (* INT32 *)
# SwSweepCount         =  44; (* INT32 *)
# SwTime               =  48; (* LONGREAL *)
# SwTimer              =  56; (* LONGREAL *)
# SwSwUserParams       =  64; (* ARRAY[0..3] OF LONGREAL *)
# SwTemperature        =  96; (* LONGREAL *)    From an external device
# SwOldIntSol          = 104; (* INT32 *)
# SwOldExtSol          = 108; (* INT32 *)
# SwDigitalIn          = 112; (* SET16 *)
# SwSweepKind          = 114; (* SET16 *)
# SwDigitalOut         = 116; (* SET16 *)
#   SwFiller1         = 118; (* INT16 *)
# SwSwMarkers          = 120; (* ARRAY[0..3] OF LONGREAL, see SwMarkersNo *)
#   SwFiller2         = 152; (* INT32 *)
# SwCRC                = 156; (* CARD32 *)
# SwSwHolding          = 160; (* ARRAY[0..15] OF LONGREAL, see SwHoldingNo *)
# SweepRecSize         = 288;      (* = 36 * 8 *)
#
# See also manual 14.1.4 Sweep
#
class Sweep(TreeNode):
    """
    A sweep, containing zero or more :class:`Trace` objects.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._label = None
        self._time = None

        # Seconds since first sweep, based on self._time, set by parent series
        self._time_since_first = None

        #self._data_offset = None
        self._stimulus_id = None

    def _read_properties(self, handle, reader):
        # See TreeNode._read_properties
        i = handle.tell()
        handle.seek(i + 4)  # SwLabel = 4; (* String32Type *)
        self._label = reader.str(32)
        #self._data_offset = reader.read1('i')
        handle.seek(i + 40)     # SwStimCount = 40; (* INT32 *)
        self._stimulus_id = reader.read1('i') - 1
        handle.seek(i + 48)     # SwTime = 48; (* LONGREAL *)
        self._time = reader.time()

    def duration(self):
        """
        Returns the maximum :meth:`duration()` of all this sweep's channels.
        """
        return max(channel.duration() for channel in self)

    def label(self):
        """ Returns this sweep's string label. """
        return self._label

    def time(self):
        """ Returns the time this sweep was recorded as a ``datetime``. """
        return self._time


#
# From PulsedFile_v9.txt
# (* TraceRecord       = RECORD *)
# TrMark               =   0; (* INT32 *)
# TrLabel              =   4; (* String32Type *)
# TrTraceID            =  36; (* INT32 *)
# TrData               =  40; (* INT32 *)
# TrDataPoints         =  44; (* INT32 *)
# TrInternalSolution   =  48; (* INT32 *)
# TrAverageCount       =  52; (* INT32 *)
# TrLeakID             =  56; (* INT32 *)
# TrLeakTraces         =  60; (* INT32 *)
# TrDataKind           =  64; (* SET16 *)
# TrUseXStart          =  66; (* BOOLEAN *)
# TrTcKind             =  67; (* BYTE *)
# TrRecordingMode      =  68; (* BYTE *)
# TrAmplIndex          =  69; (* CHAR *)
# TrDataFormat         =  70; (* BYTE *)
# TrDataAbscissa       =  71; (* BYTE *)
# TrDataScaler         =  72; (* LONGREAL *)
# TrTimeOffset         =  80; (* LONGREAL *)
# TrZeroData           =  88; (* LONGREAL *)
# TrYUnit              =  96; (* String8Type *)
# TrXInterval          = 104; (* LONGREAL *)
# TrXStart             = 112; (* LONGREAL *)
# TrXUnit              = 120; (* String8Type *)
# TrYRange             = 128; (* LONGREAL *)
# TrYOffset            = 136; (* LONGREAL *)
# TrBandwidth          = 144; (* LONGREAL *)
# TrPipetteResistance  = 152; (* LONGREAL *)  Value when R-memb > R-pip button
#                                              was pressed before run
# TrCellPotential      = 160; (* LONGREAL *)  From an external device
# TrSealResistance     = 168; (* LONGREAL *)
# TrCSlow              = 176; (* LONGREAL *)  "Last" C-slow value
# TrGSeries            = 184; (* LONGREAL *)  "Last" R-series value
# TrRsValue            = 192; (* LONGREAL *)  See manual 14.1.5!
# TrGLeak              = 200; (* LONGREAL *)
# TrMConductance       = 208; (* LONGREAL *)
# TrLinkDAChannel      = 216; (* INT32 *)
# TrValidYrange        = 220; (* BOOLEAN *)
# TrAdcMode            = 221; (* CHAR *)
# TrAdcChannel         = 222; (* INT16 *)
# TrYmin               = 224; (* LONGREAL *)
# TrYmax               = 232; (* LONGREAL *)
# TrSourceChannel      = 240; (* INT32 *)
# TrExternalSolution   = 244; (* INT32 *)
# TrCM                 = 248; (* LONGREAL *)
# TrGM                 = 256; (* LONGREAL *)
# TrPhase              = 264; (* LONGREAL *)
# TrDataCRC            = 272; (* CARD32 *)
# TrCRC                = 276; (* CARD32 *)
# TrGS                 = 280; (* LONGREAL *)
# TrSelfChannel        = 288; (* INT32 *)
# TrInterleaveSize     = 292; (* INT32 *)
# TrInterleaveSkip     = 296; (* INT32 *)
# TrImageIndex         = 300; (* INT32 *)
# TrTrMarkers          = 304; (* ARRAY[0..9] OF LONGREAL *)
# TrSECM_X             = 384; (* LONGREAL *)
# TrSECM_Y             = 392; (* LONGREAL *)
# TrSECM_Z             = 400; (* LONGREAL *)
# TrTrHolding          = 408; (* LONGREAL *)
# TrTcEnumerator       = 416; (* INT32 *)
# TrXTrace             = 420; (* INT32 *)
# TrIntSolValue        = 424; (* LONGREAL *)
# TrExtSolValue        = 432; (* LONGREAL *)
# TrIntSolName         = 440; (* String32Size *)
# TrExtSolName         = 472; (* String32Size *)
# TrDataPedestal       = 504; (* LONGREAL *)
# TraceRecSize         = 512;      (* = 64 * 8 *)
#
# See also manual 14.1.5 Trace
#
class Trace(TreeNode):
    """
    A trace from a :class:`Sweep`.

    Data can be accessed via :meth:`values` (causing it to be read from disk).

    The number of data points can be accessed with :meth:`count_samples()` or
    ``len(trace)`` (this does not require reading anything from disk).
    """
    def __init__(self, parent):
        super().__init__(parent)

        # Handle, for lazy reading
        self._handle = None

        # Label
        self._label = None

        # Raw data
        self._n = None              # Number of points
        self._data_pos = None       # Data offset (in bytes)
        self._data_type = None      # Data type (struct code)
        self._data_size = None      # Size of a point
        self._data_scale = None     # Scaling from raw to with-unit
        self._data_interleave_size = None  # 0 or more if interleaved
        self._data_interleave_skip = None  # distance to next block

        # Time
        self._t0 = None     # Trace start
        self._dt = None     # Sampling interval

        # Units
        self._data_unit = None

    def _read_properties(self, handle, reader):
        # See TreeNode._read_properties
        self._handle = handle
        i = handle.tell()

        # Label
        handle.seek(i + 4)
        self._label = reader.str(32)

        # Raw data
        handle.seek(i + 40)     # TrData
        self._data_pos = reader.read1('i')
        self._n = reader.read1('i')
        dtype = int(reader.read1('b'))
        self._data_type = _data_types[dtype]
        self._data_size = _data_sizes[dtype]
        handle.seek(i + 72)     # TrDataScaler
        self._data_scale = reader.read1('d')
        handle.seek(i + 88)     # TrZeroData
        self._data_zero = reader.read1('d')
        handle.seek(i + 292)    # TrInterleaveSize
        self._data_interleave_size = reader.read1('i')
        self._data_interleave_skip = reader.read1('i')

        # Time
        # Note: There is a boolean field TrUseXStart, but scripts online all
        # seem to be ignoring this and the HEKA demo data sets non-zero
        # TrXStart without ever setting TrUseXStart to true.
        handle.seek(i + 80)     # TrTimeOffset
        self._t0 = reader.read1('d')
        handle.seek(i + 104)    # TrXInterval
        self._dt = reader.read1('d')
        handle.seek(i + 112)    # TrXStart
        self._t0 += reader.read1('d')

        # Units
        handle.seek(i + 96)     # TrYUnit
        self._data_unit = reader.str(8)
        handle.seek(i + 120)    # TrXUnit
        self._time_unit = reader.str(8)

        # Convert units
        assert self._time_unit == 's'
        self._data_unit = myokit.parse_unit(self._data_unit)

    def __len__(self):
        return self._n

    def count_samples(self):
        """ Returns the number of samples in this trace. """
        return self._n

    def duration(self):
        """ Returns the total duration of this sweep's recorded data. """
        return self._n * self._dt

    def label(self):
        """ Returns this trace's label. """
        return self._label

    def times(self):
        """ Recreates and returns a time vector for this trace. """
        return self._t0 + np.arange(self._n) * self._dt

    def time_unit(self):
        """ Returns a string version of the units on the time axis. """
        return myokit.units.s

    def values(self):
        """ Reads and returns this trace's data. """

        if self._data_interleave_size == 0 or self._data_interleave_skip == 0:
            # Read continuous data
            d = np.memmap(self._handle, self._data_type, 'r',
                          offset=self._data_pos, shape=(self._n,))
        else:
            # Read interleaved data
            # points_per_block = self._data_interleave_size / self._data_size
            # n_blocks = np.ceil(self._n / points_per_block)
            raise NotImplementedError('Interleaved data is not supported.')

        return d * self._data_scale - self._data_zero

    def value_unit(self):
        """ Returns a string version of the units on the data axis. """
        return self._data_unit


# (* AmplifierState    = RECORD *)
# sStateVersion        = 0;                 (* 8 = SizeStateVersion *)
# sCurrentGain         = 8;                 (* LONGREAL *)
# sF2Bandwidth         = 16;                (* LONGREAL *)
# sF2Frequency         = 24;                (* LONGREAL *)
# sRsValue             = 32;                (* LONGREAL *)
# sRsFraction          = 40;                (* LONGREAL *)
# sGLeak               = 48;                (* LONGREAL *)
# sCFastAmp1           = 56;                (* LONGREAL *)
# sCFastAmp2           = 64;                (* LONGREAL *)
# sCFastTau            = 72;                (* LONGREAL *)
# sCSlow               = 80;                (* LONGREAL *)
# sGSeries             = 88;                (* LONGREAL *)
# sVCStimDacScale      = 96;                (* LONGREAL *)
# sCCStimScale         = 104;               (* LONGREAL *)
# sVHold               = 112;               (* LONGREAL *)
# sLastVHold           = 120;               (* LONGREAL *)
# sVpOffset            = 128;               (* LONGREAL *)
# sVLiquidJunction     = 136;               (* LONGREAL *)
# sCCIHold             = 144;               (* LONGREAL *)
# sCSlowStimVolts      = 152;               (* LONGREAL *)
# sCCTrackVHold        = 160;               (* LONGREAL *)
# sTimeoutCSlow        = 168;               (* LONGREAL *)
# sSearchDelay         = 176;               (* LONGREAL *)
# sMConductance        = 184;               (* LONGREAL *)
# sMCapacitance        = 192;               (* LONGREAL *)
# sSerialNumber        = 200;               (* 8 = SizeSerialNumber *)
#
# sE9Boards            = 208;               (* INT16 *)
# sCSlowCycles         = 210;               (* INT16 *)
# sIMonAdc             = 212;               (* INT16 *)
# sVMonAdc             = 214;               (* INT16 *)
#
# sMuxAdc              = 216;               (* INT16 *)
# sTestDac             = 218;               (* INT16 *)
# sStimDac             = 220;               (* INT16 *)
# sStimDacOffset       = 222;               (* INT16 *)
#
# sMaxDigitalBit       = 224;               (* INT16 *)
# sHasCFastHigh        = 226;               (* BYTE *)
# sCFastHigh           = 227;               (* BYTE *)
# sHasBathSense        = 228;               (* BYTE *)
# sBathSense           = 229;               (* BYTE *)
# sHasF2Bypass         = 230;               (* BYTE *)
# sF2Mode              = 231;               (* BYTE *)
#
# sAmplKind            = 232;               (* BYTE *)
# sIsEpc9N             = 233;               (* BYTE *)
# sADBoard             = 234;               (* BYTE *)
# sBoardVersion        = 235;               (* BYTE *)
# sActiveE9Board       = 236;               (* BYTE *)
# sMode                = 237;               (* BYTE *)
# sRange               = 238;               (* BYTE *)
# sF2Response          = 239;               (* BYTE *)
#
# sRsOn                = 240;               (* BYTE *)
# sCSlowRange          = 241;               (* BYTE *)
# sCCRange             = 242;               (* BYTE *)
# sCCGain              = 243;               (* BYTE *)
# sCSlowToTestDac      = 244;               (* BYTE *)
# sStimPath            = 245;               (* BYTE *)
# sCCTrackTau          = 246;               (* BYTE *)
# sWasClipping         = 247;               (* BYTE *)
#
# sRepetitiveCSlow     = 248;               (* BYTE *)
# sLastCSlowRange      = 249;               (* BYTE *)
#    sOld1             = 250;               (* BYTE *)
# sCanCCFast           = 251;               (* BYTE *)
# sCanLowCCRange       = 252;               (* BYTE *)
# sCanHighCCRange      = 253;               (* BYTE *)
# sCanCCTracking       = 254;               (* BYTE *)
# sHasVmonPath         = 255;               (* BYTE *)
#
# sHasNewCCMode        = 256;               (* BYTE *)
# sSelector            = 257;               (* CHAR *)
# sHoldInverted        = 258;               (* BYTE *)
# sAutoCFast           = 259;               (* BYTE *)
# sAutoCSlow           = 260;               (* BYTE *)
# sHasVmonX100         = 261;               (* BYTE *)
# sTestDacOn           = 262;               (* BYTE *)
# sQMuxAdcOn           = 263;               (* BYTE *)
#
# sImon1Bandwidth      = 264;               (* LONGREAL *)
# sStimScale           = 272;               (* LONGREAL *)
#
# sGain                = 280;               (* BYTE *)
# sFilter1             = 281;               (* BYTE *)
# sStimFilterOn        = 282;               (* BYTE *)
# sRsSlow              = 283;               (* BYTE *)
#    sOld2             = 284;               (* BYTE *)
# sCCCFastOn           = 285;               (* BYTE *)
# sCCFastSpeed         = 286;               (* BYTE *)
# sF2Source            = 287;               (* BYTE *)
#
# sTestRange           = 288;               (* BYTE *)
# sTestDacPath         = 289;               (* BYTE *)
# sMuxChannel          = 290;               (* BYTE *)
# sMuxGain64           = 291;               (* BYTE *)
# sVmonX100            = 292;               (* BYTE *)
# sIsQuadro            = 293;               (* BYTE *)
# sF1Mode              = 294;               (* BYTE *)
#    sOld3             = 295;               (* BYTE *)
#
# sStimFilterHz        = 296;               (* LONGREAL *)
# sRsTau               = 304;               (* LONGREAL *)
# sDacToAdcDelay       = 312;               (* LONGREAL *)
# sInputFilterTau      = 320;               (* LONGREAL *)
# sOutputFilterTau     = 328;               (* LONGREAL *)
# sVmonFactor          = 336;               (* LONGREAL *)
# sCalibDate           = 344;               (* 16 = SizeCalibDate *)
# sVmonOffset          = 360;               (* LONGREAL *)
#
# sEEPROMKind          = 368;               (* BYTE *)
# sVrefX2              = 369;               (* BYTE *)
# sHasVrefX2AndF2Vmon  = 370;               (* BYTE *)
#    sSpare1           = 371;               (* BYTE *)
#    sSpare2           = 372;               (* BYTE *)
#    sSpare3           = 373;               (* BYTE *)
#    sSpare4           = 374;               (* BYTE *)
#    sSpare5           = 375;               (* BYTE *)
#
# sCCStimDacScale      = 376;               (* LONGREAL *)
# sVmonFiltBandwidth   = 384;               (* LONGREAL *)
# sVmonFiltFrequency   = 392;               (* LONGREAL *)
# AmplifierStateSize   = 400;                  (* = 50 * 8 *)
#
# NOTE: Not to be confused with AmplStateRecord, which can contain an
# AmplifierState.
#
#class AmplifierState:
#    """
#    Describes the state of an amplifier used by PatchMaster.
#    """
#    def __init__(self, handle, reader):
#
#        # Read properties
#        start = handle.tell()
#
#        handle.seek(start + 96)  # sVCStimDacScale = 96; (* LONGREAL *)
#        self._vc_stim_dac_scale = reader.read1('d')
#        handle.seek(start + 104)  # sCCStimScale = 104; (* LONGREAL *)
#        self._cc_stim_scale = reader.read1('d')
#        handle.seek(start + 272)  # sStimScale = 272; (* LONGREAL *)
#        self._stim_scale = reader.read1('d')
#        handle.seek(start + 376)  # sCCStimDacScale = 376; (* LONGREAL *)
#        self._cc_stim_dac_scale = reader.read1('d')


#
# From StimFile_v9.txt
# (* RootRecord        = RECORD *)
# roVersion            =   0; (* INT32 *)
# roMark               =   4; (* INT32 *)
# roVersionName        =   8; (* String32Type *)
# roMaxSamples         =  40; (* INT32 *)
#    roFiller1         =  44; (* INT32 *)
#                               (* StimParams     = 10  *)
#                               (* StimParamChars = 320 *)
# roParams             =  48; (* ARRAY[0..9] OF LONGREAL *)
# roParamText          = 128; (* ARRAY[0..9],[0..31]OF CHAR *)
# roReserved           = 448; (* String128Type *)
#    roFiller2         = 576; (* INT32 *)
# roCRC                = 580; (* CARD32 *)
# RootRecSize          = 584;      (* = 73 * 8 *)
#
class StimulusFile(TreeNode):
    """
    Represents the "stimulus file" section of a PatchMaster bundle (.pgf).

    Each ``PulsedFile`` contains zero or more :class:`Stimulus` objects.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._version = None
        self._time = None

    def _read_properties(self, handle, reader):
        # See TreeNode._read_properties
        start = handle.tell()
        handle.seek(start + 8)
        self._version = reader.str(32)

    def version(self):
        """
        Returns a (hard-to-parse) string representation of this file's
        PatchMaster format version.
        """
        return self._version


#
# From StimFile_v9.txt
# (* StimulationRecord = RECORD *)
# stMark               =   0; (* INT32 *)
# stEntryName          =   4; (* String32Type *)
# stFileName           =  36; (* String32Type *)
# stAnalName           =  68; (* String32Type *)
# stDataStartSegment   = 100; (* INT32 *)
# stDataStartTime      = 104; (* LONGREAL *)
# stSampleInterval     = 112; (* LONGREAL *)
# stSweepInterval      = 120; (* LONGREAL *)
# stLeakDelay          = 128; (* LONGREAL *)
# stFilterFactor       = 136; (* LONGREAL *)
# stNumberSweeps       = 144; (* INT32 *)
# stNumberLeaks        = 148; (* INT32 *)
# stNumberAverages     = 152; (* INT32 *)
# stActualAdcChannels  = 156; (* INT32 *)
# stActualDacChannels  = 160; (* INT32 *)
# stExtTrigger         = 164; (* BYTE *)
# stNoStartWait        = 165; (* BOOLEAN *)
# stUseScanRates       = 166; (* BOOLEAN *)
# stNoContAq           = 167; (* BOOLEAN *)
# stHasLockIn          = 168; (* BOOLEAN *)
#    stOldStartMacKind = 169; (* CHAR *)
#    stOldEndMacKind   = 170; (* BOOLEAN *)
# stAutoRange          = 171; (* BYTE *)
# stBreakNext          = 172; (* BOOLEAN *)
# stIsExpanded         = 173; (* BOOLEAN *)
# stLeakCompMode       = 174; (* BOOLEAN *)
# stHasChirp           = 175; (* BOOLEAN *)
#    stOldStartMacro   = 176; (* String32Type *)
#    stOldEndMacro     = 208; (* String32Type *)
# sIsGapFree           = 240; (* BOOLEAN *)
# sHandledExternally   = 241; (* BOOLEAN *)
#    stFiller1         = 242; (* BOOLEAN *)
#    stFiller2         = 243; (* BOOLEAN *)
# stCRC                = 244; (* CARD32 *)
# StimulationRecSize   = 248;      (* = 31 * 8 *)
#
class Stimulus(TreeNode):
    """
    Represents a "stimulation" record.

    Each ``Stimulus`` contains zero or more :class:`StimulusChannel` objects,
    and each channel is made up out of :class:`Segment` objects.

    For selected stimuli, a reconstruction can be made using :meth:`protocol`
    or :meth:`reconstruction`.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self._entry_name = None
        self._sweep_count = None
        self._sweep_interval = None  # Waiting time between sweeps
        self._dt = None

        # Supported channel: there should be either 0 or 1 supported DAC
        self._supported_channel = None

    def _read_properties(self, handle, reader):
        # See TreeNode._read_properties
        start = handle.tell()

        handle.seek(start + 4)
        self._entry_name = reader.str(32)
        handle.seek(start + 112)  # stSampleInterval = 112; (* LONGREAL *)
        self._dt = reader.read1('d')
        handle.seek(start + 120)  # stSweepInterval = 120; (* LONGREAL *)
        self._sweep_interval = reader.read1('d')
        handle.seek(start + 144)  # stNumberSweeps = 144; (* INT32 *)
        self._sweep_count = reader.read1('i')

    def _read_finalize(self):
        # See TreeNode._read_finalize

        # Find supported channel, if any
        for c in self:
            if c.supported():
                m, u = c.amplifier_mode(), c.unit()
                vc = m is AmplifierMode.VC and u is myokit.units.V
                cc = m is AmplifierMode.CC and u is myokit.units.nA
                if vc or cc:
                    self._supported_channel = c
                    break

    def protocol(self, tu='ms', vu='mV', cu='pA', n_digits=9):
        """
        Generates a :class:`myokit.Protocol` corresponding to this stimulus, or
        raises a ``ValueError`` if unsupported features are required.

        The channel to use is chosen automatically. If no supported channel can
        be found, a :class:`NoSupportedDAChannelError` is raised.

        Support notes:

        - Only stimuli with constant segments are supported (so no ramps,
          continuous, etc.)
        - Deriving values from parameters is not supported.
        - File templates are not supported.
        - Constant segments with a zero duration are ignored.

        """
        if self._supported_channel is None:
            raise NoSupportedDAChannelError()
        return self._supported_channel.protocol(
            self._sweep_count, tu, vu, cu, n_digits)

    def reconstruction(self, join_sweeps=False):
        """
        Returns a reconstructed D/A signal corresponding to this stimulus.

        The channel to use is chosen automatically. If no supported channel can
        be found, a :class:`NoSupportedDAChannelError` is raised.
        """
        if self._supported_channel is None:
            raise NoSupportedDAChannelError()
        return self._supported_channel.reconstruction(
            self._sweep_count, self._sweep_interval, self._dt, join_sweeps)

    def supported_channel(self):
        """
        Returns the channel in this stimulus for which a D/A signal can be
        reconstructed, or returns ``None`` if no such channel is available.
        """
        return self._supported_channel

    def sweep_count(self):
        """ Returns this stimulus's sweep count. """
        return self._sweep_count

    def sweep_durations(self):
        """
        Returns the (intended) durations of this stimulus's sweeps, as a list
        of times in seconds.
        """
        d = np.array(
            [channel.sweep_durations(self._sweep_count) for channel in self])
        # Not sure if all durations should be the same for all channels
        # So returning maximum per sweep
        return np.max(d, axis=0)

    def sweep_interval(self):
        """
        Returns this stimulus's sweep interval (the intentional delay between
        one sweep end and the next sweep start, in seconds).
        """
        return self._sweep_interval


#
# From StimFile_v9.txt
# (* ChannelRecord     = RECORD *)
# chMark               =   0; (* INT32 *)
# chLinkedChannel      =   4; (* INT32 *)
# chCompressionFactor  =   8; (* INT32 *)
# chYUnit              =  12; (* String8Type *)
# chAdcChannel         =  20; (* INT16 *)
# chAdcMode            =  22; (* BYTE *)
# chDoWrite            =  23; (* BOOLEAN *)
# stLeakStore          =  24; (* BYTE *)
# chAmplMode           =  25; (* BYTE *)
# chOwnSegTime         =  26; (* BOOLEAN *)
# chSetLastSegVmemb    =  27; (* BOOLEAN *)
# chDacChannel         =  28; (* INT16 *)
# chDacMode            =  30; (* BYTE *)
# chHasLockInSquare    =  31; (* BYTE *)
# chRelevantXSegment   =  32; (* INT32 *)
# chRelevantYSegment   =  36; (* INT32 *)
# chDacUnit            =  40; (* String8Type *)
# chHolding            =  48; (* LONGREAL *)
# chLeakHolding        =  56; (* LONGREAL *)
# chLeakSize           =  64; (* LONGREAL *)
# chLeakHoldMode       =  72; (* BYTE *)
# chLeakAlternate      =  73; (* BOOLEAN *)
# chAltLeakAveraging   =  74; (* BOOLEAN *)
# chLeakPulseOn        =  75; (* BOOLEAN *)
# chStimToDacID        =  76; (* SET16 *)
# chCompressionMode    =  78; (* SET16 *)
# chCompressionSkip    =  80; (* INT32 *)
# chDacBit             =  84; (* INT16 *)
# chHasLockInSine      =  86; (* BOOLEAN *)
# chBreakMode          =  87; (* BYTE *)
# chZeroSeg            =  88; (* INT32 *)
# chStimSweep          =  92; (* INT32 *)
# chSine_Cycle         =  96; (* LONGREAL *)
# chSine_Amplitude     = 104; (* LONGREAL *)
# chLockIn_VReversal   = 112; (* LONGREAL *)
# chChirp_StartFreq    = 120; (* LONGREAL *)
# chChirp_EndFreq      = 128; (* LONGREAL *)
# chChirp_MinPoints    = 136; (* LONGREAL *)
# chSquare_NegAmpl     = 144; (* LONGREAL *)
# chSquare_DurFactor   = 152; (* LONGREAL *)
# chLockIn_Skip        = 160; (* INT32 *)
# chPhoto_MaxCycles    = 164; (* INT32 *)
# chPhoto_SegmentNo    = 168; (* INT32 *)
# chLockIn_AvgCycles   = 172; (* INT32 *)
# chImaging_RoiNo      = 176; (* INT32 *)
# chChirp_Skip         = 180; (* INT32 *)
# chChirp_Amplitude    = 184; (* LONGREAL *)
# chPhoto_Adapt        = 192; (* BYTE *)
# chSine_Kind          = 193; (* BYTE *)
# chChirp_PreChirp     = 194; (* BYTE *)
# chSine_Source        = 195; (* BYTE *)
# chSquare_NegSource   = 196; (* BYTE *)
# chSquare_PosSource   = 197; (* BYTE *)
# chChirp_Kind         = 198; (* BYTE *)
# chChirp_Source       = 199; (* BYTE *)
# chDacOffset          = 200; (* LONGREAL *)
# chAdcOffset          = 208; (* LONGREAL *)
# chTraceMathFormat    = 216; (* BYTE *)
# chHasChirp           = 217; (* BOOLEAN *)
# chSquare_Kind        = 218; (* BYTE *)
#    chFiller1         = 219; (* ARRAY[0..5] OF CHAR *)
# chSquare_BaseIncr    = 224; (* LONGREAL *)
# chSquare_Cycle       = 232; (* LONGREAL *)
# chSquare_PosAmpl     = 240; (* LONGREAL *)
# chCompressionOffset  = 248; (* INT32 *)
# chPhotoMode          = 252; (* INT32 *)
# chBreakLevel         = 256; (* LONGREAL *)
# chTraceMath          = 264; (* String128Type *)
#    chFiller2         = 392; (* INT32 *)
# chCRC                = 396; (* CARD32 *)
# ChannelRecSize       = 400;     (* = 50 * 8 *)
#
class StimulusChannel(TreeNode):
    """
    Represents a channel inside a :class:`Stimulus`.

    Each ``StimulusChannel`` contains zero or more :class:`StimulusSegment`
    objects.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self._unit = None
        self._amplifier_mode = None

        # Interpretation of "voltage" in segments
        self._holding = None
        self._use_stim_scale = None
        self._use_relative = None
        self._use_file_template = None

    def _read_properties(self, handle, reader):
        # See TreeNode._read_properties
        start = handle.tell()

        handle.seek(start + 25)     # chAmplMode = 25; (* BYTE *)
        self._amplifier_mode = AmplifierMode(reader.read1('b'))

        handle.seek(start + 40)     # chDacUnit = 40; (* String8Type *)
        self._unit = reader.str(8)
        self._holding = reader.read1('d')

        handle.seek(start + 76)     # chStimToDacID = 76; (* SET16 *)
        flags = StimulusChannelDACFlags(reader.read('?' * 16))
        self._use_stim_scale = flags.use_stim_scale
        self._use_relative = flags.use_relative
        self._use_file_template = flags.use_file_template

        # Convert unit
        if self._unit == 'A':
            # It appears that segments stored as 'A' are in nA
            self._unit = myokit.units.nA
        elif self._unit == 'V':
            self._unit = myokit.units.V
        else:
            self._unit = f'Unsupported units {self._unit}'

    def __str__(self):
        return (f'StimulusChannel in {self._amplifier_mode} mode and units'
                f' {self._unit}')

    def amplifier_mode(self):
        """
        Returns the :class:`AmplifierMode` that this channel was recorded in.
        """
        return self._amplifier_mode

    def protocol(self, sweep_count, tu='ms', vu='mV', cu='pA', n_digits=9):
        """
        Generates a :class:`myokit.Protocol` corresponding to this channel, or
        raises a ``NotImplementedError`` if unsupported features are required.

        See :meth:`Stimulus.protocol()` for details.
        """
        self._supported()

        # Get durations and values
        durations = []
        values = []
        for seg in self:    # Guaranteed to be constant by _supported() call
            # These can throw further NotImplementedErrors:
            durations.append(seg.durations(sweep_count))
            values.append(seg.values(
                sweep_count, self._holding, self._use_relative))

        # Get unit conversion factors
        tf = float(myokit.Unit.conversion_factor(myokit.units.s, tu))
        if self._unit is myokit.units.V:
            df = float(myokit.Unit.conversion_factor(self._unit, vu))
        else:  # Guaranteed to be nA by _supported() call
            df = float(myokit.Unit.conversion_factor(self._unit, cu))

        # Generate and return
        t = 0
        p = myokit.Protocol()
        for sweep in range(sweep_count):
            for segment in range(len(self)):
                d = durations[segment][sweep]
                v = values[segment][sweep]

                if d != 0:  # Silently ignore duration=0 steps
                    p.schedule(
                        level=round(v * df, n_digits),
                        start=round(t * tf, n_digits),
                        duration=round(d * tf, n_digits),
                    )
                    t += d
        return p

    def reconstruction(self, sweep_count, sweep_interval, dt,
                       join_sweeps=False):
        """
        Returns a reconstructed D/A signal corresponding to this stimulus
        channel, with the given number of sweeps.

        Note: The full signal is reconstructed, regardless of whether segments
        were set to be recorded or not.

        Arguments:

        ``sweep_count``
            The number of sweeps in the reconstruction.
        ``sweep_interval``
            The delay between one sweep's end and the next sweep's start.
        ``dt``
            The sampling interval.
        ``join_sweeps``
            Set to ``True`` to return a tuple (``time``, ``values``) where
            ``time`` and ``values`` are 1d arrays.

        """
        self._supported()

        # Get durations and values
        durations = []
        values = []
        for seg in self:    # Guaranteed to be constant by _supported() call
            # These can throw further NotImplementedErrors:
            durations.append(seg.durations(sweep_count))
            values.append(seg.values(
                sweep_count, self._holding, self._use_relative))

        # Generate
        t = 0
        nseg = len(self)
        time, data = [], []
        for sweep in range(sweep_count):
            # Sweep duration and sample count
            sw_duration = np.sum([durations[s][sweep] for s in range(nseg)])
            n_samples = int(round(sw_duration / dt))

            # Time
            time.append(t + np.arange(n_samples) * dt)
            t += sw_duration + sweep_interval

            # Values
            vs = np.zeros(n_samples)
            i = 0
            for segment in range(nseg):
                d = durations[segment][sweep]
                v = values[segment][sweep]
                n = int(round(d / dt))
                vs[i: i + n] = v
                i += n
            data.append(vs)

        # Return
        if join_sweeps:
            return np.concatenate(time), np.concatenate(data)
        return time, data

    def _supported(self):
        """
        Check for unsupported features and raises a NotImplementedError if they
        are encountered.
        """
        # Scaling has to use the "standard conversion" method
        if not self._use_stim_scale:
            # See "10.9.1 DA output channel settings" in the manual
            raise NotImplementedError(
                'Unsupported feature: non-standard D/A conversion.')

        # File templates are not supported
        if self._use_file_template:
            raise NotImplementedError(
                'Unsupported feature: channel uses a stimulus file.')

        # All segments are constant
        for seg in self:
            if seg.segment_class() is not SegmentClass.Constant:
                raise NotImplementedError(
                    'Unsupported segment type: {seg.segment_class()}')

        # Units are of a supported type
        if self._unit not in (myokit.units.V, myokit.units.nA):
            raise NotImplementedError(self._unit)

    def supported(self):
        """
        Returns ``True`` if this channel's D/A signal can be reconstructed.
        """
        try:
            self._supported()
        except NotImplementedError:
            return False
        return True

    def sweep_durations(self, sweep_count):
        """
        Returns the (intended) durations of this channel's sweeps, as a list
        of times in seconds.
        """
        d = np.array([seg.durations(sweep_count) for seg in self])
        return d.sum(axis=0)

    def unit(self):
        """ Returns the units that this channel's output is in. """
        return self._unit


#
# From StimFile_v9.txt
# (* StimToDacID : Specifies how to convert the Segment "Voltage" to the actual
#                  voltage sent to the DAC
#    -> meaning of bits:
#        bit 0 (UseStimScale)    -> use StimScale
#        bit 1 (UseRelative)     -> relative to Vmemb
#        bit 2 (UseFileTemplate) -> use file template
#        bit 3 (UseForLockIn)    -> use for LockIn computation
#        bit 4 (UseForWavelength)
#        bit 5 (UseScaling)
#        bit 6 (UseForChirp)
#        bit 7 (UseForImaging)
#        bit 14 (UseReserved)
#        bit 15 (UseReserved)
# *)
#
class StimulusChannelDACFlags:
    """
    Takes a ``chStimToDacID`` list of bools and sets them as named properties.

    See "10.9.1 DA output channel settings" in the manual.
    """
    def __init__(self, bools):
        self.use_stim_scale = bools[0]      # Apply "standard conversion"
        self.use_relative = bools[1]        # Relative to holding
        self.use_file_template = bools[2]   # Use recorded wave form
        #self.use_for_lock_in = bools[3]
        #self.use_for_wavelength = bools[4]
        #self.use_scaling = bools[5]
        #self.use_for_chirp = bools[6]
        #self.use_for_imaging = bools[7]


class AmplifierMode(enum.Enum):
    """ Amplifier mode """
    Any = 0
    VC = 1
    CC = 2
    IDensity = 3

    def __str__(self):
        if self is AmplifierMode.Any:
            return 'any'
        elif self is AmplifierMode.VC:
            return 'voltage clamp'
        elif self is AmplifierMode.CC:
            return 'current clamp'
        else:
            return 'I density'  # Can't find in manual


#
# From StimFile_v9.txt
# (* StimSegmentRecord = RECORD *)
# seMark               =   0; (* INT32 *)
# seClass              =   4; (* BYTE *)
# seStoreKind          =   5; (* BYTE *)
# seVoltageIncMode     =   6; (* BYTE *)
# seDurationIncMode    =   7; (* BYTE *)
# seVoltage            =   8; (* LONGREAL *)
# seVoltageSource      =  16; (* INT32 *)
# seDeltaVFactor       =  20; (* LONGREAL *)
# seDeltaVIncrement    =  28; (* LONGREAL *)
# seDuration           =  36; (* LONGREAL *)
# seDurationSource     =  44; (* INT32 *)
# seDeltaTFactor       =  48; (* LONGREAL *)
# seDeltaTIncrement    =  56; (* LONGREAL *)
#    seFiller1         =  64; (* INT32 *)
# seCRC                =  68; (* CARD32 *)
# seScanRate           =  72; (* LONGREAL *)
# StimSegmentRecSize   =  80;      (* = 10 * 8 *)
#
class Segment(TreeNode):
    """
    Represents a segment of a stimulus.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self._class = None
        self._storage = None

        # Value, usually voltage in V
        self._value = None
        self._value_increment = None
        self._value_delta = None
        self._value_factor = None
        self._value_from_holding = False
        self._value_from_parameter = None

        # Duration, in s
        self._duration = None
        self._duration_increment = None
        self._duration_delta = None
        self._duration_factor = None
        self._duration_from_holding = False
        self._duration_from_parameter = None

    def _read_properties(self, handle, reader):
        # See TreeNode._read_properties

        start = handle.tell()
        handle.seek(start + 4)
        self._class = SegmentClass(reader.read1('b'))
        self._storage = SegmentStorage(reader.read1('b'))
        self._value_increment = SegmentIncrement(reader.read1('b'))
        self._duration_increment = SegmentIncrement(reader.read1('b'))

        self._value = reader.read1('d')
        value_source = reader.read1('i')
        self._value_from_holding = (value_source == 1)
        self._value_from_parameter = (value_source > 1)
        self._value_factor = reader.read1('d')
        self._value_delta = reader.read1('d')

        self._duration = reader.read1('d')
        duration_source = reader.read1('i')
        self._duration_from_holding = (duration_source == 1)  # Can't happen ?
        self._duration_from_parameter = (duration_source > 1)
        self._duration_factor = reader.read1('d')
        self._duration_delta = reader.read1('d')

    def __str__(self):
        if self._value_from_holding:
            v = 'Value from holding'
        elif self._value_from_parameter:
            v = 'Value from parameter'
        else:
            v = self._value_increment.format(
                self._value, self._value_delta, self._value_factor)
            v = f'Value {v}'

        if self._duration_from_parameter:
            t = 'Duration from parameter'
        else:
            t = self._duration_increment.format(
                self._duration, self._duration_delta, self._duration_factor)
            t = f'Duration {t}'

        return f'{t}; {v}'

    def durations(self, sweep_count):
        """
        Returns the (intended) durations of this segment, for the given number
        of sweeps.

        For example, if this segment is used in a stimulus with 3 sweeps, and
        its duration increases with 1s per sweep from a base duration of 2s,
        the returned values would be ``[2, 3, 4]``.

        If unsupported features are encountered, a ``NotImplementedError`` is
        raised.
        """
        if self._duration_from_parameter:
            # Note: Could get these from the Series?
            raise NotImplementedError('Segment duration set as parameter.')
        if self._duration_from_holding:
            raise NotImplementedError('Segment duration set as holding.')

        return self._duration_increment.sweep_values(
            sweep_count,
            self._duration,
            self._duration_delta,
            self._duration_factor,
        )

    def segment_class(self):
        """ Returns this segment's :class:`SegmentClass`. """
        return self._class

    def values(self, sweep_count, holding, relative):
        """
        Returns the target values of this segment, for the given number of
        sweeps.

        For example, if this is a ``Constant`` segment in a stimulus with 4
        sweeps, and its value increases with 0.02 V per sweep from a base value
        of -0.08 V, the returned values are ``[-0.08, -0.06, -0.04, -0.02]``.

        Note: These are the values for ``Constant`` segments. The
        interpretation for other segment classes is unclear.

        If unsupported features are encountered, a ``NotImplementedError`` is
        raised.

        Arguments:

        ``sweep_count``
            The number of sweeps
        ``holding``
            The holding potential; used if the segment is defined as "at
            holding potential" or if ``relative==True``.
        ``relative``
            Set to ``True`` if this segment's value is set relative to the
            holding potential.

        """
        if self._value_from_parameter:
            # Note: Could get these from the Series?
            raise NotImplementedError('Segment value set as parameter.')

        # Always at holding potential (can ignore ``relative`` here).
        if self._value_from_holding:
            return [holding] * sweep_count

        # Get values, add holding if necessary
        values = self._value_increment.sweep_values(
            sweep_count,
            self._value,
            self._value_delta,
            self._value_factor,
        )
        if relative:
            return holding + values
        return values


class SegmentClass(enum.Enum):
    """ Type of segment """
    Constant = 0
    Ramp = 1
    Continuous = 2
    ConstSine = 3
    Squarewave = 4
    Chirpwave = 5

    _ignore_ = ['_names']
    _names = ['Constant', 'Ramp', 'Continuous', 'Sine', 'Square wave', 'Chirp']

    def __str__(self):
        return SegmentClass._names[self.value]


class SegmentStorage(enum.Enum):
    """ Segment storage mode """
    NoStore = 0
    SegStore = 1
    SegStoreStart = 2
    SegStoreEnd = 3


class SegmentIncrement(enum.Enum):
    """ Segment increment mode (for time or voltage) """
    Increase = 0
    Decrease = 1
    IncreaseInterleaved = 2
    DecreaseInterleaved = 3
    Alternate = 4
    LogIncrease = 5
    LogDecrease = 6
    LogIncreaseInterleaved = 7
    LogDecreaseInterleaved = 8
    LogAlternate = 9
    # Note: The manual mentions a "toggle" mode, for V only

    def format(self, base, delta, factor):
        """
        Formats this increment.

        Note: The manual explains about a "t * factor" and a "dt * factor"
        mode, but it's not clear where this is stored in the file.
        """
        if self.value < 5:
            if delta == 0:
                return f'constant at {base}'
            return f'{self.name} from {base} with step {delta}'

        if factor == 1:
            return f'constant at {base}'

        return f'{self.name} from {base} with dt {delta} and factor {factor}'

    def sweep_order(self, n_sweeps):
        """
        Returns a list of array indices in the order specified by this segment
        increment mode.

        For example, for 6 sweeps and mode ``Increase``, it returns
        ``[0, 1, 2, 3, 4, 5]``. For 5 sweeps and mode ``Alternate`` it returns
        ``[0, 4, 1, 3, 2]``.

        If unsupported features are encountered, a ``NotImplementedError`` is
        raised.
        """
        S = SegmentIncrement
        if self in (S.Increase, S.LogIncrease):
            return np.arange(n_sweeps)
        elif self in (S.Decrease, S.LogDecrease):
            return np.arange(n_sweeps - 1, -1, -1)
        elif self in (S.IncreaseInterleaved, S.LogIncreaseInterleaved):
            # Interleaved
            # The pattern given in the manual is not explained and only
            # length-6 examples are given. Easy to come up with different
            # interpretations of what an odd-numbered sequence looks like...
            #indices = np.arange(n_sweeps)
            #indices[1:-1:2] = range(2, n_sweeps, 2)
            #indices[2::2] = range(1, n_sweeps - 1, 2)
            #return indices
            raise NotImplementedError('Segment with interleaved increase')
        elif self in (S.DecreaseInterleaved, S.LogDecreaseInterleaved):
            # Interleaved
            # The pattern given in the manual is not explained and only
            # length-6 examples are given. Easy to come up with different
            # interpretations of what an odd-numbered sequence looks like...
            #indices = np.zeros(n_sweeps) - 1#, -1, -1) - 1
            #indices[1:-1:2] = range(n_sweeps - 3, -1, -2)
            #indices[2:-2:2] = range(n_sweeps - 2, 2, -2)
            #return indices
            raise NotImplementedError('Segment with interleaved decrease')
        elif self is S.Alternate:
            indices = np.zeros(n_sweeps) * np.nan
            nh = (1 + n_sweeps) // 2
            indices[::2] = range(0, nh, 1)
            indices[1::2] = range(n_sweeps - 1, nh - 1, -1)
            return indices

    def sweep_values(self, n_sweeps, base, delta, factor):
        """
        Returns the sequence specified by this order for the given number of
        sweeps, base level, and "delta" or "factor" increments.

        For example, for mode "Increasing" with a base of -80, a delta of 10,
        and 4 sweeps, it returns [-80, -70, -60, -50].
        """
        # Logarithmic increments are not supported (because I don't understand
        # how to select between the two logarithmic equations given in the
        # manual).
        if self.value > 4:
            if factor == 1:
                return np.ones(n_sweeps) * base
            raise NotImplementedError(
                'Segment with logarithmic increments or decrements.')
        elif delta == 0:
            return np.ones(n_sweeps) * base

        values = base + delta * np.arange(n_sweeps)
        return values[self.sweep_order(n_sweeps)]


class NoSupportedDAChannelError(myokit.MyokitError):
    """
    Raised if no channel can be found in a stimulus to convert to a D/A
    signal or protocol.
    """
    pass


# Encoding for text parts of files
_ENC = 'latin-1'

# Time offset since 1990, utc
_tz = datetime.timezone.utc
_ts_1990 = datetime.datetime(1990, 1, 1, tzinfo=_tz).timestamp()

_data_types = (np.int16, np.int32, np.float32, np.float64)
_data_sizes = (2, 4, 4, 8)

