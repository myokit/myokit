#
# This module reads files in Axon Binary File format v1 or v2 used by Axon
# Technologies and Molecular Devices.
# The v1 format was used until Clampex version 9.
# Clampex 10 and onwards use the v2 format.
#
# WARNING: This file hasn't been extensively tested.
#
# About ABF
# ---------
# pClamp version 10 introduced a new .abf file format ABF2, with format version
#  numbers 2.0 and up. Older version are referred to a version 1 (even though
#  the actual version number may be, for example, 1.6).
# The version 2 format uses a variable sized header making it a little trickier
#  to read but appears to be more structured overal than the first version.
#
# Trials, runs, sweeps and channels
# ---------------------------------
# In pClamp version 10 and higher, each recorded data segment is termed a
#  'sweep'. In older versions the same concept is called an 'episode'.
# The data in a sweep contains the recordings from one or more channels. The
#  number of channels used throughout a single file is constant. In other
#  words, channel 1 in sweep 1 is a recording from the same channel as channel
#  1 in sweep 10.
# A set of sweeps is called a run. Both abf versions 1 and 2 contain a variable
#  indicating the number of sweeps per run. In abf1 this is found in the
#  header, in abf2 it is stored in a separate 'protocol' section.
# It is possible to record multiple runs, each containing an equal number of
#  sweeps, each containing an equal number of channels. However, in this case
#  the data from run to run is averaged and only a single averaged run is
#  saved. This means there is never more than 1 run in a file, even though this
#  data may have been obtained during multiple runs.
# A set of runs is termed a 'trial'. Each file contains a single trial.
#
# Acquisition modes
# -----------------
# pClamp uses five acquisition modes:
#  Gap-free mode
#    Data is recored continuously, without any interruptions
#  Variable-length events mode
#    Data is recorded in bursts of variable length (for example whenever some
#    condition is met)
#  Fixed-length events mode
#    Data is recored in bursts of fixed length, starting whenever some
#    condition is met. Multiple bursts (sweeps, or episodes in pClamp <10
#    terminology) may overlap.
#  High-speed oscilloscope mode
#    Like fixed-length events mode, but sweeps will never overlap
#  Episodic stimulation mode
#    Some stimulation is applied during which the resulting reaction is
#    recorded. The resulting dataset consists of non-overlapping sweeps.
#
# Stimulus waveforms
# ------------------
# A stimulus signal in pClamp is termed a 'waveform'. Each waveform is divided
#  into a series of steps, ramps or pulse trains. Such a subsection is called
#  an 'epoch'. The protocol section of a file defines one or more stimuli, each
#  containing a list of epochs.
#
#---------------------------------  license  ----------------------------------
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
#---------------------------------  credits  ----------------------------------
#
# A lot of this code uses the (sadly somewhat outdated) information made public
# by Axon, e.g. at https://support.moleculardevices.com/s/article/
#                               Axon-pCLAMP-ABF-File-Support-Pack-Download-Page
# This information comes without a specific license, but states that
# "Permission is granted to freely use, modify and copy the code in this file."
#
# In addition, this module was in part derived from an early version of the
# Neo package for representing electrophysiology data, specifically from a
# Python module authored by sgarcia and jnowacki.
# Neo can be found at: http://neuralensemble.org/trac/neo
#
# The Neo package used was licensed using the following BSD License:
#
#----------------------------------  start  -----------------------------------
# Copyright (c) 2010-2012, Neo authors and contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# Neither the names of the copyright holders nor the names of the contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#-----------------------------------  end  ------------------------------------
# The code used in Neo is itself derived from the publicly contributed matlab
#  script abf2load, again licensed under BSD. The original notice follows
#  below:
#----------------------------------  start  -----------------------------------
# Copyright (c) 2009, Forrest Collman
# Copyright (c) 2004, Harald Hentschke
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#-----------------------------------  end  ------------------------------------
# The abf2load script is available from:
#  http://www.mathworks.com/matlabcentral/fileexchange/22114-abf2load
#------------------------------------------------------------------------------
# Information - but no direct code - from the matlab script get_abf_header.m
# was also used: http://neurodata.hg.sourceforge.net/hgweb/neurodata/neurodata/
#------------------------------------------------------------------------------
import datetime
import os
import struct
import warnings

import numpy as np

import myokit
import myokit.formats


# Encoding for text parts of files
_ENC = 'latin-1'


class AbfFile(myokit.formats.SweepSource):
    """
    Represents a read-only Axon Binary Format file (``.abf``), stored at the
    location pointed to by ``filepath``.

    Files in the "ABF" format and the newer "ABF2" format can be read. If the
    given ``filepath`` ends in ``.pro`` a protocol file is assumed. This
    assumption can be overruled by setting the ``is_protocol_file`` argument
    to either ``True`` or ``False``.

    Data in ABF files is recorded in *sweeps*, where each sweep contains one or
    more *channels* with recorded (A/D) data. In addition, zero or more output
    waveforms may be defined (also called "protocol" or D/A channels). Where
    possible, the :class`AbfFile` class will convert these embedded protocols
    to time series and include them as additional channels.

    For example::

        abf = AbfFile('some_file.abf')
        for sweep in abf:
            for channel in sweep:
                print(channel.name())
            break

    might show

        IN 0
        10xVm
        Cmd 0

    where the first two channels are recorded A/D channels and the final one is
    a reconstructed D/A output channel.

    Sweeps and channels are represented by :class:`Sweep` and :class:`Channel`
    objects respectively, and these can be used to obtain the data from a
    file::

        abf = AbfFile('some_file.abf')
        for sweep in abf:
            for channel in sweep:
                plot(channel.times(), channel.values())

    In addition the ``AbfFile`` class implements the
    :class`myokit.formats.SweepSource` interface. Note that this interface
    treats A/D and D/A as separate things, so :meth:`channel_count` returns the
    number of A/D channels, not the total number of channels in a
    :class:`Sweep` object (which can include D/A channels).

    Support notes:

    - Protocol (D/A) conversion is only supported for "episodic stimulation"
      with constant valued steps (so e.g. no ramps) and without "user lists".
    - Protocols with more than one sampling rate are not supported.
    - The publicly available information on the ABF format is not great, so
      there will be several other issues and shortcomings.

    When an :class:`AbfFile` is created, the file at ``filepath`` is read in
    its entirety and the file handle is closed. No try-catch or ``with``
    statements are required.

    Arguments:

    ``filepath``
        The path to load the data from. Data will be read into memory
        immediately upon construction.
    ``is_protocol_file``
        If set to ``True``, no attempt to read A/D data will be made and only
        D/A "protocol" information will be read. If left at its default value
        of ``None`` files with the extension ``.pro`` will be recognized as
        protocol files.

    """
    def __init__(self, filepath, is_protocol_file=None):
        # The path to the file and its basename
        filepath = str(filepath)
        self._filepath = os.path.abspath(filepath)
        self._filename = os.path.basename(filepath)

        # Read as protocol file yes?
        if is_protocol_file is None:
            self._is_protocol_file = os.path.splitext(filepath)[1] == '.pro'
        else:
            self._is_protocol_file = bool(is_protocol_file)

        # Cached string-to-unit conversions
        self._unit_cache = {}

        # Read the file header as an ordered dictionary
        self._header = None
        self._strings = None
        self._version = None
        self._version_str = None
        self._read_1_header()

        # Read the time of recording
        self._datetime = None
        self._read_2_time_of_recording()

        # Read the protocol information
        self._n_adc = None
        self._n_dac = None

        self._rate = None
        self._mode = None

        self._number_of_trials = None
        self._trial_start_to_start = None
        self._runs_per_trial = None
        self._run_start_to_start = None
        self._sweeps_per_run = None
        self._sweep_start_to_start = None
        self._samples_per_channel = None

        # To be able to treat v1 and v2 slightly more easily, we define 3
        # functions read epoch info from episodic stimulation protocols
        self._epoch_functions = None

        # Not all D/A channels can be converted, so we maintain an array with
        # the original indices of the channels in the da_sweeps. (Note that
        # this differs again from the "index" labels for user display, which
        # are stored in the channels themselves).
        self._dac_indices = []

        # Read protocol information and create empty sweep objects
        # Sweeps contain both A/D channels and D/A reconstructions. Some files
        # will have A/D but no (or no supported) D/A. Conversely protocol files
        # will have D/A only. So all in one sweep is easiest.
        self._sweeps = None

        self._read_3_protocol_information()

        # Read and calculate conversion factors for integer data in ADC
        self._adc_factors = None
        self._adc_offsets = None
        self._read_4_ad_conversion_factors()

        # Read the A/D channel data and add it to the sweeps
        if self._n_adc:
            self._read_5_ad_data()

        # Reconstruct D/A signals as additional channels and add to the sweeps
        self._read_6_da_reconstructions()

        # Copy channel names and units, for easier SweepSource implementation
        self._ad_names = {}
        self._da_names = {}
        self._ad_units = []
        self._da_units = []
        for sweep in self._sweeps:
            for i, channel in enumerate(sweep[:self._n_adc]):
                self._ad_names[channel.name()] = i
                self._ad_units.append(channel.unit())
            for i, channel in enumerate(sweep[self._n_adc:]):
                self._da_names[channel.name()] = i
                self._da_units.append(channel.unit())
            break

    def _read_1_header(self):
        """ Read the file header. """

        def read_f(f, form, offset=None):
            """ Read and unpack a file section in the format ``form``. """
            form = str(form)
            if offset is not None:
                f.seek(offset)
            return struct.unpack(form, f.read(struct.calcsize(form)))

        def ups(val):
            """
            Parses tuples, unpacking single values:

            1. Tuples with a single entry are converted to that entry (e.g.
               ``(5, )`` gets turned into ``5``.
            2. Any bytes objects are converted to string.
            3. Strings containing only \\x00 are replaced by ``None``

            """
            # Convert bytes
            values = [0] * len(val)
            for i, v in enumerate(val):
                if isinstance(v, bytes):
                    v = v.decode(_ENC).strip()
                    # Handle long \x00 lists
                    if v and ord(v[0]) == 0:
                        return None
                values[i] = v
            del val

            # Unpack single
            if len(values) == 1:
                return values[0]
            return values

        with open(self._filepath, 'rb') as f:

            # Get ABF Format version (pClamp < 10 is version 1, after is
            # version 2)
            sig = f.read(4).decode(_ENC)
            if sig == 'ABF ':
                version = 1
            elif sig == 'ABF2':
                version = 2
            else:
                raise NotImplementedError('Unknown ABF Format "{sig}".')

            # Gather header fields
            header = {}
            for key, offset, form in HEADER_FIELDS[version]:
                header[key] = ups(read_f(f, form, offset))

            # Get uniform file version number
            if version < 2:
                self._version = np.round(header['fFileVersionNumber'], 5)
                self._version_str = str(self._version)
            else:
                v = header['fFileVersionNumber']
                self._version = v[3]
                self._version_str = '.'.join([str(v) for v in reversed(v)])

            # Get file start time in seconds
            if version < 2:
                header['lFileStartTime'] += (
                    header['nFileStartMillisecs'] / 1000)
            else:
                header['lFileStartTime'] = header['uFileStartTimeMS'] / 1000

            if version < 2:

                # Version 1: Only read tags
                tags = []
                for i in range(header['lNumTagEntries']):  # pragma: no cover
                    # Cover pragma: Don't have appropriate test file
                    f.seek(header['lTagSectionPtr'] + i * 64)
                    tag = {}
                    for key, form in ABF2_TAG_INFO_DESCRIPTION:
                        tag[key] = ups(read_f(f, form))
                    tags.append(tag)
                header['tags'] = tags
                self._strings = []

            else:

                # Version 2
                # Find location of file sections
                sections = {}
                for i, s in enumerate(ABF2_FILE_SECTIONS):
                    index, data, length = read_f(f, 'IIl', 76 + i * 16)
                    sections[s] = {}
                    sections[s]['index'] = index
                    sections[s]['data'] = data
                    sections[s]['length'] = length
                header['sections'] = sections

                # String section contains channel names and units
                f.seek(sections['Strings']['index'] * BLOCKSIZE)
                strings = f.read(sections['Strings']['data'])

                # Starts with header we need to skip
                # DWORD dwSignature;    4 bytes
                # DWORD dwVersion;      4 bytes
                # UINT  uNumStrings;    4 bytes
                # UINT  uMaxSize;       4 bytes
                # ABFLONG  lTotalBytes; 4 bytes
                # UINT  uUnused[6];     24 bytes
                # Total: 44 bytes
                strings = strings[44:]

                # C-style string termination
                strings = strings.split(b'\x00')
                strings = [s.decode(_ENC).strip() for s in strings]
                self._strings = strings

                # Read tag section
                tags = []
                offs = sections['Tag']['index'] * BLOCKSIZE
                size = sections['Tag']['data']
                for i in range(sections['Tag']['length']):  # pragma: no cover
                    # Cover pragma: Don't have appropriate test file
                    f.seek(offs + i * size)
                    tag = {}
                    for key, form in ABF2_TAG_INFO_DESCRIPTION:
                        tag[key] = ups(read_f(f, form))
                    tags.append(tag)
                header['tags'] = tags

                # Read protocol section
                protocol = {}
                offs = sections['Protocol']['index'] * BLOCKSIZE
                f.seek(offs)
                for key, form in ABF2_PROTOCOL_FIELDS:
                    protocol[key] = ups(read_f(f, form))
                header['protocol'] = protocol

                # Read analog-digital conversion sections
                adc = []
                offs = sections['ADC']['index'] * BLOCKSIZE
                size = sections['ADC']['data']
                for i in range(sections['ADC']['length']):
                    ADC = {}
                    f.seek(offs + i * size)
                    for key, form in ABF2_ADC_FIELDS:
                        ADC[key] = ups(read_f(f, form))
                    # Get channel name and unit
                    ADC['ADCChNames'] = (
                        strings[ADC['lADCChannelNameIndex'] - 1])
                    ADC['ADCChUnits'] = strings[ADC['lADCUnitsIndex'] - 1]
                    adc.append(ADC)
                header['listADCInfo'] = adc

                # Read DAC section
                dac = []
                offs = sections['DAC']['index'] * BLOCKSIZE
                size = sections['DAC']['data']
                for i in range(sections['DAC']['length']):
                    f.seek(offs + size * i)
                    DAC = {}
                    for key, form in ABF2_DAC_FIELDS:
                        DAC[key] = ups(read_f(f, form))
                    DAC['sDACChannelName'] = \
                        strings[DAC['lDACChannelNameIndex'] - 1]
                    DAC['sDACChannelUnits'] = \
                        strings[DAC['lDACChannelUnitsIndex'] - 1]
                    dac.append(DAC)
                header['listDACInfo'] = dac

                # Read UserList section
                user_lists = []
                offs = sections['UserList']['index'] * BLOCKSIZE
                size = sections['UserList']['data']
                r = range(sections['UserList']['length'])
                for i in r:  # pragma: no cover
                    # Cover pragma: User lists are not supported
                    f.seek(offs + size * i)
                    user_list = {}
                    for key, form in ABF2_USER_LIST_FIELDS:
                        user_list[key] = ups(read_f(f, form))
                    user_lists.append(user_list)
                header['listUserListInfo'] = user_lists

                # Read epoch-per-DAC section
                # The resulting OrderedDict has the following structure:
                #  - the first index is the DAC number
                #  - the second index is the epoch number
                header['epochInfoPerDAC'] = {}
                offs = sections['EpochPerDAC']['index'] * BLOCKSIZE
                size = sections['EpochPerDAC']['data']
                info = {}
                for i in range(sections['EpochPerDAC']['length']):
                    f.seek(offs + size * i)
                    einf = {}
                    for key, form in ABF2_EPOCH_INFO_PER_DAC_FIELD:
                        einf[key] = ups(read_f(f, form))
                    DACNum = einf['nDACNum']
                    EpochNum = einf['nEpochNum']
                    if DACNum not in info:
                        info[DACNum] = {}
                    info[DACNum][EpochNum] = einf
                header['epochInfoPerDAC'] = info

        self._header = header

    def _read_2_time_of_recording(self):
        """ Read and process the time when this file was recorded. """

        if self._version < 2:
            t1 = str(self._header['lFileStartDate'])
            t2 = float(self._header['lFileStartTime'])
        else:
            t1 = str(self._header['uFileStartDate'])
            t2 = float(self._header['uFileStartTimeMS']) / 1000

        YY = int(t1[0:4])
        MM = int(t1[4:6])
        DD = int(t1[6:8])
        hh = int(t2 / 3600)
        mm = int((t2 - hh * 3600) / 60)
        ss = t2 - hh * 3600 - mm * 60
        ms = int((ss % 1) * 1e6)
        ss = int(ss)

        self._datetime = datetime.datetime(YY, MM, DD, hh, mm, ss, ms)

    def _read_3_protocol_information(self):
        """
        Reads the header fields detailing the number of runs, sweeps, and the
        type of protocol used. Create empty sweeps.
        """
        h = self._header

        # Number of channels, sampling rate (Hz) and acquisition mode
        # Note: Number of A/D channels will be set to 0 if this is a
        #       protocol-only file
        # Note: Number of D/A channels will be adjusted after checking support
        if self._version < 2:
            # In (newer versions of) version 1.x, only 2 D/A channels have
            # full "waveform" support. There are still 4 D/A channels but I
            # don't understand what the other 2 do.
            # 1.x versions only seem to have 1 DAC channel, but this is not
            # supported here.
            self._n_adc = int(h['nADCNumChannels'])
            self._n_dac = min(len(h['sDACChannelName']), 2)
            self._rate = 1e6 / (h['fADCSampleInterval'] * self._n_adc)
            self._mode = h['nOperationMode']
        else:
            # In version 2, there are up to 8 "waveform" D/A channels

            self._n_adc = int(h['sections']['ADC']['length'])
            self._n_dac = int(h['sections']['DAC']['length'])
            self._rate = 1e6 / h['protocol']['fADCSequenceInterval']
            self._mode = h['protocol']['nOperationMode']

        if self._mode not in acquisition_modes:  # pragma: no cover
            raise NotImplementedError(f'Unknown acquisition mode: {mode}')

        # Protocol files don't have A/D channels by definition
        if self._is_protocol_file:
            self._n_adc = 0

        # Only episodic stimulation is supported.
        if self._mode != ACMODE_EPISODIC_STIMULATION:  # pragma: no cover
            warnings.warn(
                'Unsupported acquisition method '
                + acquisition_modes[self._mode] + '; unable to read D/A'
                ' channels.')

            # Remaining code is all about reading D/A info for episodic
            # stimulation, so return
            self._n_dac = 0
            return

        # Gather protocol information
        if self._version < 2:

            # Before version 2: Sections are fixed length, locations absolute
            self._number_of_trials = h['lNumberOfTrials']
            self._trial_start_to_start = h['fTrialStartToStart']
            self._runs_per_trial = h['lRunsPerTrial']
            self._run_start_to_start = h['fRunStartToStart']
            self._sweeps_per_run = h['lSweepsPerRun']
            self._sweep_start_to_start = h['fEpisodeStartToStart']

            # Number of samples in a channel for each sweep
            # (Only works for fixed-length, high-speed-osc or episodic)
            self._samples_per_channel = \
                h['lNumSamplesPerEpisode'] // h['nADCNumChannels']

            def dinfo(index, name):
                """ Return DAC channel info, ABF1 version. """
                return h[name][index]

            def einfo_exists(index):
                """ Check that epoch info exists for a DAC, ABF1 version. """
                # Fields always exist for 2 channels, not always set.
                # But not useful to look at unset ones, so using n_dac instead
                # of hardcoded 2!
                return 0 <= index < self._n_dac

            def einfo(index):
                """ Return epoch info for a DAC, ABF1 version. """
                lo = index * 8
                hi = lo + 8
                for i in range(lo, hi):
                    yield {
                        'type': h['nEpochType'][i],
                        'init_duration': h['lEpochInitDuration'][i],
                        'duration_inc': h['lEpochDurationInc'][i],
                        'init_level': h['fEpochInitLevel'][i],
                        'level_inc': h['fEpochLevelInc'][i],
                    }
            self._epoch_functions = (dinfo, einfo_exists, einfo)

        else:

            # Version 2 uses variable length sections
            p = h['protocol']

            # Trials, runs, sweeps
            # (According to the manual, there should only be 1 trial!)
            self._number_of_trials = p['lNumberOfTrials']
            self._trial_start_to_start = p['fTrialStartToStart']
            self._runs_per_trial = p['lRunsPerTrial']
            self._run_start_to_start = p['fRunStartToStart']
            self._sweeps_per_run = p['lSweepsPerRun']
            self._sweep_start_to_start = p['fSweepStartToStart']

            # Number of samples in a channel in a single sweep
            self._samples_per_channel = \
                p['lNumSamplesPerEpisode'] // h['sections']['ADC']['length']

            # Compatibility functions
            def dinfo(index, name):
                """ Return DAC info, ABF2 version. """
                return h['listDACInfo'][index][name]

            def einfo_exists(index):
                """ Check that epoch info exists for a DAC, ABF2 version. """
                return index in h['epochInfoPerDAC']

            def einfo(index):
                """ Return epoch info for a DAC, ABF2 version. """
                for e in h['epochInfoPerDAC'][index].values():
                    yield {
                        'type': e['nEpochType'],
                        'init_duration': e['lEpochInitDuration'],
                        'duration_inc': e['lEpochDurationInc'],
                        'init_level': e['fEpochInitLevel'],
                        'level_inc': e['fEpochLevelInc'],
                    }
            self._epoch_functions = (dinfo, einfo_exists, einfo)

        # If sweepStartToStart == 0, we set it to the duration of a sweep
        if self._sweep_start_to_start == 0:    # pragma: no cover
            self._sweep_start_to_start = self._samples_per_channel / self._rate

        # Create empty sweeps
        n = h['lActualSweeps']
        if self._is_protocol_file:
            n = self._sweeps_per_run
        self._sweeps = [Sweep() for i in range(n)]

        # User lists are not supported for D/A reconstruction
        # I haven't been able to figure out how you see if a user list is
        # being used, or which channel is using it. There is an 'enable' field
        # but that's been 0 in files that definitely used a UserList...
        # So for now not reading ANY DAC if a userlist even exists.
        user_lists = False
        if self._version < 2:   # pragma: no cover
            user_lists = any(self._header['nULEnable'])
        else:                   # pragma: no cover
            user_lists = len(self._header['listUserListInfo']) > 0
        if user_lists:          # pragma: no cover
            warnings.warn(
                'Unsupported acquisition method: episodic with user lists;'
                ' unable to read D/A channels.')
            self._n_dac = 0
            return

        # Get indices of enabled and supported DAC reconstructions
        supported = {EPOCH_DISABLED, EPOCH_STEPPED}
        for i_dac in range(self._n_dac):
            if einfo_exists(i_dac):
                i = einfo(i_dac)
                use = False

                # Check for unsupported features (or disabled waveforms/epochs)
                # Version 1 files can only have two waveform channels
                if self._version < 2 and i_dac > 1:  # pragma: no cover
                    source = DAC_DISABLED
                else:
                    source = dinfo(i_dac, 'nWaveformSource')
                if source == DAC_EPOCHTABLEWAVEFORM:
                    # Any epoch types besides disabled/stepped? Then don't use
                    # Also don't use if exclusively disabled
                    for e in i:
                        t = e['type']
                        if t == EPOCH_STEPPED:
                            use = True
                        elif t != EPOCH_DISABLED:  # pragma: no cover
                            use = False
                            warnings.warn(
                                f'Unsupported epoch type: {epoch_types(t)}')
                            break
                elif source == DAC_DACFILEWAVEFORM:  # pragma: no cover
                    # Stimulus file? Then don't use
                    warnings.warn('Stimulus file D/A channel not supported.')

                if use:
                    self._dac_indices.append(i_dac)

        # Set true number of D/A outputs
        self._n_dac = len(self._dac_indices)

    def _read_4_ad_conversion_factors(self):
        """ Calculate the factors to convert any integer data to float. """
        self._adc_factors = []
        self._adc_offsets = []
        h = self._header
        if self._version < 2:
            for i in range(self._n_adc):
                j = h['nADCSamplingSeq'][i]

                # Multiplier
                f = (
                    h['fInstrumentScaleFactor'][j]
                    * h['fADCProgrammableGain'][j]
                    * h['lADCResolution']
                    / h['fADCRange'])

                # Signal conditioner used?
                if h['nSignalType'] != 0:   # pragma: no cover
                    # Cover pragma: Don't have appropriate test file
                    f *= h['fSignalGain'][j]

                # Additional gain?
                if h['nTelegraphEnable'][j]:
                    f *= h['fTelegraphAdditGain'][j]

                # Set final gain factor
                self._adc_factors.append(1 / f)

                # Shift
                s = h['fInstrumentOffset'][j]

                # Signal conditioner used?
                if h['nSignalType'] != 0:   # pragma: no cover
                    # Cover pragma: Don't have appropriate test file
                    s -= h['fSignalOffset'][j]

                # Set final offset
                self._adc_offsets.append(s)

        else:

            a = h['listADCInfo']
            p = h['protocol']
            for i in range(self._n_adc):
                # Multiplier
                f = (
                    a[i]['fInstrumentScaleFactor']
                    * a[i]['fADCProgrammableGain']
                    * p['lADCResolution']
                    / p['fADCRange'])

                # Signal conditioner used?
                if h.get('nSignalType', 0) != 0:  # pragma: no cover
                    # Cover pragma: Don't have appropriate test file
                    f *= a[i]['fSignalGain']

                # Additional gain?
                if a[i]['nTelegraphEnable']:
                    f *= a[i]['fTelegraphAdditGain']

                # Set final gain factor
                self._adc_factors.append(1 / f)

                # Shift
                s = a[i]['fInstrumentOffset']

                # Signal conditioner used?
                if h.get('nSignalType', 0) != 0:  # pragma: no cover
                    # Cover pragma: Don't have appropriate test file
                    s -= a[i]['fSignalOffset']

                # Set final offset
                self._adc_offsets.append(s)

    def _read_5_ad_data(self):
        """ Reads the A/D data and appends it to the list of sweeps. """

        h = self._header

        # Sampling rate is constant for all sweeps and channels
        # TODO: This won't work for 2-rate protocols
        rate = self._rate

        # Get binary integer format
        dt = np.dtype('i2') if h['nDataFormat'] == 0 else np.dtype('f4')

        # Get number of channels, create a numpy memory map
        if self._version < 2:
            # Old files, get info from fields stored directly in header
            o = h['lDataSectionPtr'] * BLOCKSIZE \
                + h['nNumPointsIgnored'] * dt.itemsize
            n = h['lActualAcqLength']
        else:
            # New files, get info from appropriate header section
            o = h['sections']['Data']['index'] * BLOCKSIZE
            n = h['sections']['Data']['length']
        data = np.memmap(self._filepath, dt, 'r', shape=(n,), offset=o)

        # Load list of sweeps (Sweeps are called 'episodes' in ABF < 2)
        if self._version < 2:
            n = h['lSynchArraySize']
            o = h['lSynchArrayPtr'] * BLOCKSIZE
        else:
            n = h['sections']['SynchArray']['length']
            o = h['sections']['SynchArray']['index'] * BLOCKSIZE
        if n > 0:
            dt = [(str('offset'), str('i4')), (str('len'), str('i4'))]
            sweep_data = np.memmap(
                self._filepath, dt, 'r', shape=(n,), offset=o)
        else:   # pragma: no cover
            # Cover pragma: Don't have appropriate test file
            sweep_data = np.empty((1), dt)
            sweep_data[0]['len'] = data.size
            sweep_data[0]['offset'] = 0

        # Number of sweeps must equal n
        if n != h['lActualSweeps']:
            raise NotImplementedError(
                'Unable to read file with different sizes per sweep.')

        # Time-offset at start of first sweep
        start = sweep_data[0]['offset'] / rate

        # Get data
        pos = 0
        for i_sweep, sdat in enumerate(sweep_data):

            # Get the number of data points
            size = sdat['len']

            # Calculate the correct size for variable-length event mode
            if self._mode == ACMODE_VARIABLE_LENGTH_EVENTS:  # pragma: no cover
                # Cover pragma: Only episodic stimulus is supported.
                if self._version < 2:
                    f = float(h['fSynchTimeUnit'])
                else:
                    f = float(h['protocol']['fSynchTimeUnit'])
                if f != 0:
                    size /= f

            # Get a memory map to the relevant part of the data
            part = data[pos: pos + size]
            pos += size
            part = part.reshape(
                (part.size // self._n_adc, self._n_adc)).astype('f')

            # If needed, reformat the integers
            if h['nDataFormat'] == 0:
                # Data given as integers? Convert to floating point

                for i in range(self._n_adc):
                    part[:, i] *= self._adc_factors[i]
                    part[:, i] += self._adc_offsets[i]

            # Get start in other modes
            if self._mode != ACMODE_EPISODIC_STIMULATION:  # pragma: no cover
                # All modes except episodic stimulation
                start = data['offset'] / rate

            # Create and populate sweep
            sweep = self._sweeps[i_sweep]
            for i in range(self._n_adc):
                c = Channel(self)
                c._data = part[:, i]    # Actually store the data
                c._rate = rate
                c._start = start
                c._is_reconstruction = False

                if self._version < 2:
                    j = h['nADCSamplingSeq'][i]

                    c._name = h['sADCChannelName'][j]
                    c._index = int(h['nADCPtoLChannelMap'][j])
                    c._unit = self._unit(h['sADCUnits'][j])

                    # Get telegraphed info
                    def get(field):
                        try:
                            return float(h[field][j])
                        except KeyError:
                            return None

                    if get('nTelegraphEnable'):
                        c._type = int(get('nTelegraphMode') or 0)
                        c._cm = get('fTelegraphMembraneCap')
                        c._rs = get('fTelegraphAccessResistance')
                        c._lopass = get('fTelegraphFilter')

                    # Updated low-pass cutoff
                    if h['nSignalType'] != 0:  # pragma: no cover
                        # Cover pragma: Don't have appropriate test file
                        # If a signal conditioner is used, the cutoff frequency
                        # is an undescribed "complex function" of both low-pass
                        # settings...
                        c._lopass = None

                else:
                    c._name = h['listADCInfo'][i]['ADCChNames']
                    c._index = int(h['listADCInfo'][i]['nADCNum'])
                    c._unit = self._unit(h['listADCInfo'][i]['ADCChUnits'])

                    # Get telegraphed info
                    if h['listADCInfo'][i]['nTelegraphEnable']:
                        c._type = int(h['listADCInfo'][i]['nTelegraphMode'])
                        c._cm = float(
                            h['listADCInfo'][i]['fTelegraphMembraneCap'])
                        c._rs = float(
                            h['listADCInfo'][i]['fTelegraphAccessResistance'])
                        c._lopass = float(
                            h['listADCInfo'][i]['fTelegraphFilter'])

                    # Updated low-pass cutoff
                    if 'nSignalType' in h['protocol']:  # pragma: no cover
                        # Cover pragma: Don't have appropriate test file
                        if h['protocol']['nSignalType'] != 0:
                            # If a signal conditioner is used, the cutoff
                            # frequency is an undescribed "complex function" of
                            # both low-pass settings...
                            c._lopass = None

                sweep._channels.append(c)

            if self._mode == ACMODE_EPISODIC_STIMULATION:
                # Increase time according to sweeps in episodic stim. mode
                start += self._sweep_start_to_start

    def _read_6_da_reconstructions(self):
        """
        Convert supported D/A waveforms to channels.

        Only works for episodic stimulation, with step protocols and no
        user lists.

        The resulting analog signal has the same size as the recorded
        signals, so not always the full length of the protocol!

        """
        dinfo, einfo_exists, einfo = self._epoch_functions

        ns = self._samples_per_channel
        start = 0
        for i_sweep, sweep in enumerate(self._sweeps):
            for i_dac in self._dac_indices:

                # Create a channel
                c = Channel(self)
                c._name = dinfo(i_dac, 'sDACChannelName')
                if self._version < 2:
                    c._index = i_dac
                else:
                    c._index = int(dinfo(i_dac, 'lDACChannelNameIndex'))
                c._data = np.ones(ns) * dinfo(i_dac, 'fDACHoldingLevel')
                c._rate = self._rate
                c._start = start
                c._unit = self._unit(dinfo(i_dac, 'sDACChannelUnits'))
                c._is_reconstruction = True

                # Find start of first epoch. This is defined as being at t=0
                # but axon likes to add some samples before the first and after
                # the last epoch. We can find out the number of samples using
                # a procedure found in ABF v1's _GetHoldingLength()
                if self._is_protocol_file:
                    i2 = 0
                else:
                    i2 = ns // 64  # ABFH_HOLDINGFRACTION = 64
                    i2 -= i2 % self._n_adc
                    if (i2 < self._n_adc):  # pragma: no cover
                        i2 = self._n_adc

                # For each 'epoch' in the stimulation signal
                for e in einfo(i_dac):
                    if e['type'] == EPOCH_STEPPED:
                        dur = e['init_duration']
                        inc = e['duration_inc']
                        i1 = i2
                        i2 += dur + i_sweep * inc
                        level = e['init_level'] + e['level_inc'] * i_sweep
                        c._data[i1:i2] = level * np.ones(len(range(i2 - i1)))

                # Store channel
                sweep._channels.append(c)

            # Update start for next sweep
            start += self._sweep_start_to_start

    def __getitem__(self, key):
        return self._sweeps[key]

    def __iter__(self):
        return iter(self._sweeps)

    def __len__(self):
        return len(self._sweeps)

    def _channel_id(self, channel_id):
        """ Checks an int or str channel id and returns a valid int. """
        if len(self._sweeps) == 0:  # pragma: no cover
            raise KeyError(f'Channel {channel_id} not found (empty file).')

        # Handle string
        if isinstance(channel_id, str):
            int_id = self._ad_names[channel_id]  # Bubble KeyError to user
        else:
            int_id = int(channel_id)    # Propagate TypeError
            if int_id < 0 or int_id >= self._n_adc:
                raise IndexError(f'channel_id out of range: {channel_id}')

        return int_id

    def channel(self, channel_id, join_sweeps=False):
        # Docstring in SweepSource
        channel_id = self._channel_id(channel_id)
        time, data = [], []
        for i, sweep in enumerate(self._sweeps):
            time.append(sweep[channel_id].times())
            data.append(sweep[channel_id].values())
        if join_sweeps:
            return (np.concatenate(time), np.concatenate(data))
        return time, data

    def channel_count(self):
        # Docstring in SweepSource
        return self._n_adc

    def channel_names(self, index=None):
        # Docstring in SweepSource
        if index is None:
            return list(self._ad_names.keys())
        return list(self._ad_names.keys())[index]

    def channel_units(self, index=None):
        # Docstring in SweepSource
        if index is None:
            return list(self._ad_units)
        return self._ad_units[index]

    def _da_id(self, output_id):
        """
        Checks an int or str D/A channel id and returns a valid int.

        Note: The integer here is from 0 to da_count(), so not equal to the
        channel :meth:`index()` shown in pclamp.
        """
        if len(self._sweeps) == 0:  # pragma: no cover
            raise KeyError(f'D/A output {output_id} not found (empty file).')

        # Handle string
        if isinstance(output_id, str):
            int_id = self._da_names[output_id]  # Propagate KeyError to user
        else:
            int_id = int(output_id)  # Propagate TypeError
            if int_id < 0 or int_id >= self._n_dac:
                raise IndexError(f'output_id out of range: {output_id}')

        return int_id

    def da(self, output_id, join_sweeps=False):
        # Docstring in SweepSource
        channel_id = self._n_adc + self._da_id(output_id)
        time, data = [], []
        for i, sweep in enumerate(self._sweeps):
            time.append(sweep[channel_id].times())
            data.append(sweep[channel_id].values())
        if join_sweeps:
            return (np.concatenate(time), np.concatenate(data))
        return time, data

    def da_count(self):
        # Docstring in SweepSource
        return self._n_dac

    def da_names(self, index=None):
        # Docstring in SweepSource
        if index is None:
            return list(self._da_names.keys())
        return list(self._da_names.keys())[index]

    def da_protocol(self, output_id=None, tu='ms', vu='mV', cu='pA',
                    n_digits=9, include_initial_holding=False):
        """
        See :meth:`myokit.formats.SweepSource.da_protocol()`.

        This implementation adds a keyword argument ``include_initial_holding``
        that lets you switch between the declared protocol (``False``) and the
        protocol as actually implemented (``True``). In the latter case, a
        short holding time is added before the first epoch in every sweep.
        """

        # Check the output id. This also raises an error if no supported D/A
        # channels are present.
        output_id = self._da_id(output_id or 0)

        # Get the index in dinfo
        i_dac = self._dac_indices[output_id]
        dinfo, einfo_exists, einfo = self._epoch_functions

        # Get the time and data conversion factors
        units = myokit.units
        tf = myokit.Unit.conversion_factor(units.s, tu)
        if myokit.Unit.can_convert(self._da_units[output_id], units.V):
            df = myokit.Unit.conversion_factor(self._da_units[output_id], vu)
        elif myokit.Unit.can_convert(
                self._da_units[output_id], units.A):  # pragma: no cover
            df = myokit.Unit.conversion_factor(self._da_units[output_id], cu)
        else:  # pragma: no cover
            # Not a voltage or current? Then don't convert
            df = 1
        tf, df = float(tf), float(df)

        # Axon has the annoying habit of adding some extra holding at the start
        # We can include this if we want. See _read_6 for details.
        if self._is_protocol_file:
            offset = 0
        else:
            offset = self._samples_per_channel // 64
            offset -= offset % self._n_adc
            if (offset < self._n_adc):  # pragma: no cover
                # Don't have a test for this, but this is part of the
                # established procedure.
                offset = self._n_adc
            offset /= self._rate

        # Holding level (converted and rounded)
        holding = round(df * dinfo(i_dac, 'fDACHoldingLevel'), n_digits)

        # Create protocol
        p = myokit.Protocol()
        start = 0
        next_start = self._sweep_start_to_start
        for i_sweep in range(self._sweeps_per_run):
            # Start of sweep: secret event at holding potential
            if include_initial_holding:
                e_start = round(tf * start, n_digits)
                e_length = round(tf * offset, n_digits)
                p.schedule(holding, e_start, e_length)
                start += offset

            for e in einfo(i_dac):
                if e['type'] == EPOCH_STEPPED:
                    dur = e['init_duration'] / self._rate
                    inc = e['duration_inc'] / self._rate
                    duration = dur + i_sweep * inc
                    level = e['init_level'] + e['level_inc'] * i_sweep

                    e_level = round(df * level, n_digits)
                    e_start = round(tf * start, n_digits)
                    e_length = round(tf * duration, n_digits)
                    p.schedule(e_level, e_start, e_length)

                    start += duration
                # Note: Only other type can be EPOCH_DISABLED at this point

            # End of sweep: event at holding potential
            e_start = round(tf * start, n_digits)
            e_length = round(tf * (next_start - start), n_digits)
            p.schedule(holding, e_start, e_length)
            start = next_start
            next_start += self._sweep_start_to_start

        return p

    def da_units(self, index=None):
        # Docstring in SweepSource
        if index is None:
            return list(self._da_units)
        return self._da_units[index]

    def equal_length_sweeps(self):
        # Always true for ABF
        return True

    def filename(self):
        """ Returns this ABF file's filename. """
        return self._filename

    def log(self, join_sweeps=False, use_names=False, include_da=True):
        # Docstring in SweepSource

        # Create log, return if no sweeps or channels
        log = myokit.DataLog()
        ns = len(self._sweeps)
        if ns == 0 or (self._n_adc + self._n_dac) == 0:  # pragma: no cover
            return log

        # Get channel names
        if use_names:
            nc = self._n_adc + (self._n_dac if include_da else 0)
            names = [c.name() for c in self._sweeps[0][:nc]]
        else:
            names = [f'{i}.channel' for i in range(self._n_adc)]
            if include_da:
                names += [f'{i}.da' for i in range(self._n_dac)]

        # Channel meta data adding function
        def add_channel_meta(channel, cmeta):
            if channel._is_reconstruction:
                cmeta['channel_type'] = 'Reconstructed D/A signal'
                cmeta['original_name'] = channel._name
                cmeta['original_index'] = channel._index
                cmeta['unit'] = channel._unit
                if channel._type:  # pragma: no cover
                    cmeta['DAC type'] = type_mode_names[channel._type]
            else:
                cmeta['channel_type'] = 'Recorded signal'
                cmeta['original_name'] = channel._name
                cmeta['original_index'] = channel._index
                cmeta['unit'] = channel._unit
                if channel._lopass:
                    cmeta['low_pass_Hz'] = channel._lopass
                if channel._cm:
                    cmeta['Cm_pF'] = channel._cm
                if channel._rs:   # pragma: no cover
                    cmeta['Rs'] = channel._rs

        # Gather data
        t = self._sweeps[0][0].times()
        if not join_sweeps:
            log['time'] = t
            log.cmeta['time']['unit'] = myokit.units.s
            for i_sweep, sweep in enumerate(self._sweeps):
                for channel, name in zip(sweep, names):
                    name = f'{i_sweep}.{name}'
                    log[name] = channel.values()
                    add_channel_meta(channel, log.cmeta[name])
        else:
            log['time'] = np.concatenate(
                [t + i * self._sweep_start_to_start for i in range(ns)])
            log.cmeta['time']['unit'] = myokit.units.s
            for i_channel, name in enumerate(names):
                log[name] = np.concatenate(
                    [sweep[i_channel].values() for sweep in self._sweeps])
                add_channel_meta(self._sweeps[0][i_channel], log.cmeta[name])

        # Add meta data
        log.set_time_key('time')
        log.meta['original_format'] = f'ABF {self._version_str}'
        log.meta['recording_time'] = self._datetime
        log.meta['acquisition_mode'] = acquisition_modes[self._mode]

        return log

    def matplotlib_figure(self):
        """ Creates and returns a matplotlib figure with this file's data. """
        import matplotlib.pyplot as plt
        f = plt.figure()
        plt.suptitle(self.filename())

        # Plot AD channels
        ax = plt.subplot(2, 1, 1)
        ax.set_title('Measured data')
        times = None
        for sweep in self._sweeps:
            for channel in sweep[:self._n_adc]:
                if times is None:
                    times = channel.times()
                plt.plot(times, channel.values())

        # Plot DA channels
        n = self._n_dac
        ax = [plt.subplot(2, n, n + 1 + i) for i in range(n)]
        for sweep in self._sweeps:
            for i, channel in enumerate(sweep[self._n_adc:]):
                ax[i].set_title(channel.name())
                ax[i].plot(times, channel.values())

        return f

    def meta_str(self, show_header=False):
        """
        Returns a multi-line string with meta data about this file.

        The optional argument ``show_header`` can be used to add the full
        header contents to the output.
        """
        out = []

        # File info
        if self._is_protocol_file:
            out.append(f'Axon Protocol File: {self._filename}')
        else:
            out.append(f'Axon Binary File: {self._filename}')
        out.append(f'ABF Format version {self._version_str}')
        out.append(f'Recorded on: {self._datetime}')

        # AProtocol info
        out.append(
            f'Acquisition mode: {self._mode}: {acquisition_modes[self._mode]}')
        if self._number_of_trials:
            out.append(
                f'Protocol set for {self._number_of_trials} trials,'
                f' spaced {self._trial_start_to_start}s apart.')
            out.append(
                f'    with {self._runs_per_trial} runs per trial,'
                f' spaced {self._run_start_to_start}s apart.')
            out.append(
                f'     and {self._sweeps_per_run} sweeps per run,'
                f' spaced {self._sweep_start_to_start}s apart.')
        else:   # pragma: no cover
            out.append('Protocol data could not be determined.')
        out.append(f'Sampling rate: {self._rate} Hz')

        # Channel info
        if len(self._sweeps) > 0:

            # A/D recordings
            for i, c in enumerate(self._sweeps[0][:self._n_adc]):
                out.append(f'A/D Channel {i}: "{c._name}"')
                out.append(f'  Unit: {c._unit}')
                if c._lopass:
                    out.append(f'  Low-pass filter: {c._lopass} Hz')
                if c._cm:
                    out.append(f'  Cm (telegraphed): {c._cm} pF')
                if c._rs:   # pragma: no cover
                    # Cover pragma: Don't have appropriate test file
                    out.append(f'  Rs (telegraphed): {c._rs}')

            # Reconstructed D/A outputs
            for i, c in enumerate(self._sweeps[0][self._n_adc:]):
                out.append(f'D/A Channel {i}: "{c._name}"')
                out.append(f'  Unit: {c._unit}')
                if c._type:  # pragma: no cover
                    # Cover pragma: Don't have appropriate test file
                    out.append('  Type: {type_mode_names[c._type]}')

        # Add full header info
        if show_header:
            if self._strings:
                dict_to_string(out, 'Strings', {'strings': self._strings})
            dict_to_string(out, 'file header', self._header)

        return '\n'.join(out)

    def path(self):
        """ Returns the path to the underlying ABF file. """
        return self._filepath

    def sweep_count(self):
        # Docstring in SweepSource
        return len(self._sweeps)

    def time_unit(self):
        # Docstring in SweepSource
        # For ABF, this is always seconds
        return myokit.units.s

    def _unit(self, unit_string):
        """ Parses a unit string and returns a :class:`myokit.Unit`. """
        try:
            return self._unit_cache[unit_string]
        except KeyError:
            unit = myokit.parse_unit(unit_string.replace(MU, 'u'))
            self._unit_cache[unit_string] = unit
            return unit

    def version(self):
        """ Returns a string representation of this file's version number. """
        return self._version_str


class Sweep:
    """
    Represents a single sweep (also called an *episode*).

    Each sweep contains a fixed number of :class:`channels<Channel>`.
    """
    def __init__(self):
        self._channels = []

    def __getitem__(self, key):
        return self._channels[key]  # Handles slices etc.

    def __iter__(self):
        return iter(self._channels)

    def __len__(self):
        return len(self._channels)


class Channel:
    """
    Represents a signal for a single channel.

    To obtain its data, use :meth:`times` and :meth:`values`.
    """
    def __init__(self, parent_file):
        self._parent_file = parent_file  # The abf file this channel is from
        self._type = TYPE_UNKNOWN   # Type of recording

        # This channel's name
        self._name = None

        # Is this a reconstructed D/A output?
        self._is_reconstruction = None

        # This channel's index in the file. This is basically a name, and does
        # not correspond to e.g. its index in the ADC/DAC info or its index in
        # the sweep's list of channels.
        self._index = None

        # The units this channel's data is in
        self._unit = None

        # The raw data points
        self._data = None

        # Sampling rate in Hz
        self._rate = None

        # The signal start time
        self._start = None

        # The reported membrane capacitance
        self._cm = None

        # The reported access resistance
        self._rs = None

        # The reported low-pass filter cut-off frequency
        self._lopass = None

    def index(self):
        """ Returns the index set for this channel. """
        return self._index

    def name(self):
        """ Returns the name set for this channel. """
        return self._name

    def __str__(self):
        return (
            f'Channel({self._index} "{self._name}"); {len(self._data)} points'
            f' sampled at {self._rate}Hz, starts at t={self._start}.')

    def times(self):
        """ Returns a copy of the values on the time axis. """
        n = len(self._data)
        f = 1 / self._rate
        return np.arange(self._start, self._start + n * f, f)[0:n]

    def unit(self):
        """ Returns the units this channel is in. """
        return self._unit

    def values(self):
        """ Returns a copy of the values on the data axis. """
        return np.copy(self._data)


def dict_to_string(out, name, d, tab=''):
    """ Used by AbfFile.info(). """
    m = max(0, 38 - len(tab) - int(0.1 + len(name) / 2))
    out.append(f'{tab}{"-" * m}  {name}  {"-" * m}')
    for n, v in d.items():
        n = str(n)
        if type(v) == dict:
            dict_to_string(out, n, v, f'{tab}  ')
        elif type(v) == list:
            list_to_string(out, n, v, tab)
        else:
            out.append(f'{tab}{n}: {v}')
    m = max(0, 80 - 2 * len(tab))
    out.append(f'{tab}{m * "-"}')


def list_to_string(out, name, d, tab=''):
    """ Used by AbfFile.info(). """
    for index, item in enumerate(d):
        n = f'{name}[{index}]'
        if type(item) == dict:
            dict_to_string(out, n, item, tab)
        elif type(item) == list:    # pragma: no cover
            # Cover pragma: Don't have appropriate test file
            list_to_string(out, n, item, tab)
        else:
            out.append(f'{tab}{n}: {item}')


# Some python struct types:
#   f   float
#   h   short
#   i   int
#   s   string
# Size of block alignment in ABF Files
BLOCKSIZE = 512


# A mu, sometimes found in unit strings
MU = '\u00b5'


# Header fields for versions 1 and 2
# Stored as (key, offset, format) where format corresponds to a struct
#  unpacking format as documented in:
#  http://docs.python.org/library/struct.html#format-characters
HEADER_FIELDS = {
    # Note that a lot of the groups in the version 1 header start with obsolete
    # fields, followed later by their newer equivalents.
    1: [
        ('fFileSignature', 0, '4s'),       # Coarse file version indication
        # Group 1, File info and sizes
        ('fFileVersionNumber', 4, 'f'),    # Version number as float
        ('nOperationMode', 8, 'h'),        # Acquisition mode
        ('lActualAcqLength', 10, 'i'),
        ('nNumPointsIgnored', 14, 'h'),
        ('lActualSweeps', 16, 'i'),
        ('lFileStartDate', 20, 'i'),
        ('lFileStartTime', 24, 'i'),
        ('lStopWatchTime', 28, 'i'),
        ('fHeaderVersionNumber', 32, 'f'),
        ('nFileType', 36, 'h'),
        ('nMSBinFormat', 38, 'h'),
        # Group 2, file structure
        ('lDataSectionPtr', 40, 'i'),
        ('lTagSectionPtr', 44, 'i'),
        ('lNumTagEntries', 48, 'i'),
        ('lScopeConfigPtr', 52, 'i'),
        ('lNumScopes', 56, 'i'),
        ('x_lDACFilePtr', 60, 'i'),
        ('x_lDACFileNumEpisodes', 64, 'i'),
        ('lDeltaArrayPtr', 72, 'i'),
        ('lNumDeltas', 76, 'i'),
        ('lVoiceTagPtr', 80, 'i'),
        ('lVoiceTagEntries', 84, 'i'),
        ('lSynchArrayPtr', 92, 'i'),
        ('lSynchArraySize', 96, 'i'),
        ('nDataFormat', 100, 'h'),
        ('nSimultaneousScan', 102, 'h'),
        # Group 3, Trial hierarchy
        ('nADCNumChannels', 120, 'h'),
        ('fADCSampleInterval', 122, 'f'),
        ('fADCSecondSampleInterval', 126, 'f'),
        ('fSynchTimeUnit', 130, 'f'),
        ('fSecondsPerRun', 134, 'f'),
        ('lNumSamplesPerEpisode', 138, 'i'),
        ('lPreTriggerSamples', 142, 'i'),
        ('lSweepsPerRun', 146, 'i'),        # Number of sweeps/episodes per run
        ('lRunsPerTrial', 150, 'i'),
        ('lNumberOfTrials', 154, 'i'),
        ('nAveragingMode', 158, 'h'),
        ('nUndoRunCount', 160, 'h'),
        ('nFirstEpisodeInRun', 162, 'h'),
        ('fTriggerThreshold', 164, 'f'),
        ('nTriggerSource', 168, 'h'),
        ('nTriggerAction', 170, 'h'),
        ('nTriggerPolarity', 172, 'h'),
        ('fScopeOutputInterval', 174, 'f'),
        ('fEpisodeStartToStart', 178, 'f'),
        ('fRunStartToStart', 182, 'f'),
        ('fTrialStartToStart', 186, 'f'),
        ('lAverageCount', 190, 'f'),
        ('lClockChange', 194, 'f'),
        ('nAutoTriggerStrategy', 198, 'h'),
        # Group 4, Display parameters
        # Group 5, Hardware info
        ('fADCRange', 244, 'f'),
        ('lADCResolution', 252, 'i'),
        # Group 6, Environment info
        ('nFileStartMillisecs', 366, 'h'),
        # Group 7, Multi-channel info
        ('nADCPtoLChannelMap', 378, '16h'),
        ('nADCSamplingSeq', 410, '16h'),
        ('sADCChannelName', 442, '10s' * 16),
        ('sADCUnits', 602, '8s' * 16),
        ('fADCProgrammableGain', 730, '16f'),
        ('fADCDisplayAmplification', 794, '16f'),
        ('fADCDisplayOffset', 858, '16f'),
        ('fInstrumentScaleFactor', 922, '16f'),
        ('fInstrumentOffset', 986, '16f'),
        # The fSignal fields are only relevant if a signal conditioner was used
        ('fSignalGain', 1050, '16f'),
        ('fSignalOffset', 1114, '16f'),
        ('fSignalLowpassFilter', 1178, '16f'),
        ('fSignalHighpassFilter', 1242, '16f'),
        ('sDACChannelName', 1306, '10s' * 4),
        ('sDACChannelUnits', 1346, '8s' * 4),
        ('fDACScaleFactor', 1378, '4f'),
        ('fDACHoldingLevel', 1394, '4f'),
        # 1 if a "CyberAmp 320/380" signal conditioner was used
        ('nSignalType', 1410, 'h'),
        # Group 8, There doesn't seem to be a group 8
        # Group 9, Wave data
        ('nDigitalEnable', 1436, 'h'),
        ('x_nWaveformSource', 1438, 'h'),
        ('nActiveDACChannel', 1440, 'h'),
        ('x_nInterEpisodeLevel', 1442, 'h'),
        ('x_nEpochType', 1444, '10h'),
        ('x_fEpochInitLevel', 1464, '10f'),
        ('x_fEpochLevelInc', 1504, '10f'),
        ('x_nEpochInitDuration', 1544, '10h'),
        ('x_nEpochDurationInc', 1564, '10h'),
        ('nDigitalHolding', 1584, 'h'),
        ('nDigitalInterEpisode', 1586, 'h'),
        ('nDigitalValue', 2588, '10h'),
        ('lDACFilePtr', 2048, '2i'),
        ('lDACFileNumEpisodes', 2056, '2i'),
        ('fDACCalibrationFactor', 2074, '4f'),
        ('fDACCalibrationOffset', 2090, '4f'),
        ('nWaveformEnable', 2296, '2h'),
        ('nWaveformSource', 2300, '2h'),
        ('nInterEpisodeLevel', 2304, '2h'),
        ('nEpochType', 2308, '20h'),       # 2 CMD channels with 10 values each
        ('fEpochInitLevel', 2348, '20f'),
        ('fEpochLevelInc', 2428, '20f'),
        ('lEpochInitDuration', 2508, '20i'),
        ('lEpochDurationInc', 2588, '20i'),
        # Group 10, DAC Output file (Stimulus file)
        ('fDACFileScale', 2708, 'd'),
        ('fDACFileOffset', 2716, 'd'),
        ('lDACFileEpisodeNum', 2724, 'i'),
        ('nDACFileADCNum', 2732, '2h'),
        ('sDACFilePath', 2736, '256s' * 2),     # Two strings
        # Group 11,
        # Group 12, User list parameters
        ('nULEnable', 3360, '4h'),
        ('nULParamToVary', 3368, '4h'),
        ('nULParamValueList0', 3376, '256s' * 4),
        ('nULRepeat', 4400, '4h'),
        # Group 13,
        # Group 14,
        # Group 15, Leak subtraction
        # Group 16, Misc
        # Group 17, Trains
        # Group 18, Application version data
        # Group 19
        # Group 20
        # Group 21 Skipped
        # Group 22
        # Group 23 Post-processing
        # Group 24 Legacy stuff
        # Group 6 extended
        ('nTelegraphEnable', 4512, '16h'),
        ('fTelegraphAdditGain', 4576, '16f'),
    ],
    2: [
        ('fFileSignature', 0, '4s'),       # Coarse file version indication
        ('fFileVersionNumber', 4, '4b'),   # Version number as 4 signed chars
        ('uFileInfoSize', 8, 'I'),
        ('lActualSweeps', 12, 'I'),
        ('uFileStartDate', 16, 'I'),       # File start data YYYYMMDD
        ('uFileStartTimeMS', 20, 'I'),     # Time of day in ms ?
        ('uStopwatchTime', 24, 'I'),
        ('nFileType', 28, 'H'),
        ('nDataFormat', 30, 'H'),
        ('nSimultaneousScan', 32, 'H'),
        ('nCRCEnable', 34, 'H'),
        ('uFileCRC', 36, 'I'),
        ('FileGUID', 40, 'I'),
        ('uCreatorVersion', 56, 'I'),
        ('uCreatorNameIndex', 60, 'I'),
        ('uModifierVersion', 64, 'I'),
        ('uModifierNameIndex', 68, 'I'),
        ('uProtocolPathIndex', 72, 'I')
    ]
}


# ABF2 File sections
ABF2_FILE_SECTIONS = [
    'Protocol',
    'ADC',
    'DAC',
    'Epoch',
    'ADCPerDAC',
    'EpochPerDAC',
    'UserList',
    'StatsRegion',
    'Math',
    'Strings',
    'Data',
    'Tag',
    'Scope',
    'Delta',
    'VoiceTag',
    'SynchArray',
    'Annotation',
    'Stats',
]


# ABF2 Fields in the tag section
ABF2_TAG_INFO_DESCRIPTION = [
    ('lTagTime', 'i'),
    ('sComment', '56s'),
    ('nTagType', 'h'),
    ('nVoiceTagNumber_or_AnnotationIndex', 'h'),
]


# ABF2 Fields in the protocol section
ABF2_PROTOCOL_FIELDS = [
    ('nOperationMode', 'h'),                # 0
    ('fADCSequenceInterval', 'f'),          # 2
    ('bEnableFileCompression', 'b'),        # 6
    ('sUnused1', '3s'),                     # 7
    ('uFileCompressionRatio', 'I'),         # 10
    ('fSynchTimeUnit', 'f'),                # 14
    ('fSecondsPerRun', 'f'),                # 18
    ('lNumSamplesPerEpisode', 'i'),         # 22
    ('lPreTriggerSamples', 'i'),            # 26
    ('lSweepsPerRun', 'i'),                 # 30
    ('lRunsPerTrial', 'i'),                 # 34
    ('lNumberOfTrials', 'i'),               # 38
    ('nAveragingMode', 'h'),                # 42
    ('nUndoRunCount', 'h'),                 # 44
    ('nFirstEpisodeInRun', 'h'),            # 46
    ('fTriggerThreshold', 'f'),             # 48
    ('nTriggerSource', 'h'),                # 52
    ('nTriggerAction', 'h'),                # 54
    ('nTriggerPolarity', 'h'),              # 56
    ('fScopeOutputInterval', 'f'),          # 58
    ('fSweepStartToStart', 'f'),            # 62
    ('fRunStartToStart', 'f'),
    ('lAverageCount', 'i'),
    ('fTrialStartToStart', 'f'),
    ('nAutoTriggerStrategy', 'h'),
    ('fFirstRunDelayS', 'f'),
    ('nChannelStatsStrategy', 'h'),
    ('lSamplesPerTrace', 'i'),
    ('lStartDisplayNum', 'i'),
    ('lFinishDisplayNum', 'i'),
    ('nShowPNRawData', 'h'),
    ('fStatisticsPeriod', 'f'),
    ('lStatisticsMeasurements', 'i'),
    ('nStatisticsSaveStrategy', 'h'),
    ('fADCRange', 'f'),
    ('fDACRange', 'f'),
    ('lADCResolution', 'i'),
    ('lDACResolution', 'i'),
    ('nExperimentType', 'h'),
    ('nManualInfoStrategy', 'h'),
    ('nCommentsEnable', 'h'),
    ('lFileCommentIndex', 'i'),
    ('nAutoAnalyseEnable', 'h'),
    ('nSignalType', 'h'),
    ('nDigitalEnable', 'h'),
    ('nActiveDACChannel', 'h'),
    ('nDigitalHolding', 'h'),
    ('nDigitalInterEpisode', 'h'),
    ('nDigitalDACChannel', 'h'),
    ('nDigitalTrainActiveLogic', 'h'),
    ('nStatsEnable', 'h'),
    ('nStatisticsClearStrategy', 'h'),
    ('nLevelHysteresis', 'h'),
    ('lTimeHysteresis', 'i'),
    ('nAllowExternalTags', 'h'),
    ('nAverageAlgorithm', 'h'),
    ('fAverageWeighting', 'f'),
    ('nUndoPromptStrategy', 'h'),
    ('nTrialTriggerSource', 'h'),
    ('nStatisticsDisplayStrategy', 'h'),
    ('nExternalTagType', 'h'),
    ('nScopeTriggerOut', 'h'),
    ('nLTPType', 'h'),
    ('nAlternateDACOutputState', 'h'),
    ('nAlternateDigitalOutputState', 'h'),
    ('fCellID', '3f'),
    ('nDigitizerADCs', 'h'),
    ('nDigitizerDACs', 'h'),
    ('nDigitizerTotalDigitalOuts', 'h'),
    ('nDigitizerSynchDigitalOuts', 'h'),
    ('nDigitizerType', 'h'),
]


# ABF2 Fields in the ADC section
ABF2_ADC_FIELDS = [
    ('nADCNum', 'h'),
    ('nTelegraphEnable', 'h'),
    ('nTelegraphInstrument', 'h'),
    ('fTelegraphAdditGain', 'f'),
    ('fTelegraphFilter', 'f'),
    ('fTelegraphMembraneCap', 'f'),
    ('nTelegraphMode', 'h'),
    ('fTelegraphAccessResistance', 'f'),
    ('nADCPtoLChannelMap', 'h'),
    ('nADCSamplingSeq', 'h'),
    ('fADCProgrammableGain', 'f'),
    ('fADCDisplayAmplification', 'f'),
    ('fADCDisplayOffset', 'f'),
    ('fInstrumentScaleFactor', 'f'),
    ('fInstrumentOffset', 'f'),
    ('fSignalGain', 'f'),      # The fSignal fields are only relevant if a
    ('fSignalOffset', 'f'),    # signal conditioner was used
    ('fSignalLowpassFilter', 'f'),
    ('fSignalHighpassFilter', 'f'),
    ('nLowpassFilterType', 'b'),
    ('nHighpassFilterType', 'b'),
    ('fPostProcessLowpassFilter', 'f'),
    ('nPostProcessLowpassFilterType', 'c'),
    ('bEnabledDuringPN', 'b'),
    ('nStatsChannelPolarity', 'h'),
    ('lADCChannelNameIndex', 'i'),
    ('lADCUnitsIndex', 'i'),
]


# ABF2 Fields in the DAC section
ABF2_DAC_FIELDS = [
    ('nDACNum', 'h'),
    ('nTelegraphDACScaleFactorEnable', 'h'),
    ('fInstrumentHoldingLevel', 'f'),
    ('fDACScaleFactor', 'f'),
    ('fDACHoldingLevel', 'f'),
    ('fDACCalibrationFactor', 'f'),
    ('fDACCalibrationOffset', 'f'),
    ('lDACChannelNameIndex', 'i'),
    ('lDACChannelUnitsIndex', 'i'),
    ('lDACFilePtr', 'i'),
    ('lDACFileNumSweeps', 'i'),
    ('nWaveformEnable', 'h'),
    ('nWaveformSource', 'h'),
    ('nInterEpisodeLevel', 'h'),
    ('fDACFileScale', 'f'),
    ('fDACFileOffset', 'f'),
    ('lDACFileEpisodeNum', 'i'),
    ('nDACFileADCNum', 'h'),
    ('nConditEnable', 'h'),
    ('lConditNumPulses', 'i'),
    ('fBaselineDuration', 'f'),
    ('fBaselineLevel', 'f'),
    ('fStepDuration', 'f'),
    ('fStepLevel', 'f'),
    ('fPostTrainPeriod', 'f'),
    ('fPostTrainLevel', 'f'),
    ('nMembTestEnable', 'h'),
    ('nLeakSubtractType', 'h'),
    ('nPNPolarity', 'h'),
    ('fPNHoldingLevel', 'f'),
    ('nPNNumADCChannels', 'h'),
    ('nPNPosition', 'h'),
    ('nPNNumPulses', 'h'),
    ('fPNSettlingTime', 'f'),
    ('fPNInterpulse', 'f'),
    ('nLTPUsageOfDAC', 'h'),
    ('nLTPPresynapticPulses', 'h'),
    ('lDACFilePathIndex', 'i'),
    ('fMembTestPreSettlingTimeMS', 'f'),
    ('fMembTestPostSettlingTimeMS', 'f'),
    ('nLeakSubtractADCIndex', 'h'),
    ('sUnused', '124s'),
]


# ABF2 Fields in the DAC-Epoch section
ABF2_EPOCH_INFO_PER_DAC_FIELD = [
    ('nEpochNum', 'h'),
    ('nDACNum', 'h'),
    ('nEpochType', 'h'),
    ('fEpochInitLevel', 'f'),
    ('fEpochLevelInc', 'f'),
    ('lEpochInitDuration', 'i'),
    ('lEpochDurationInc', 'i'),
    ('lEpochPulsePeriod', 'i'),
    ('lEpochPulseWidth', 'i'),
    ('sUnused', '18s'),
]

# ABF2 User list fields
ABF2_USER_LIST_FIELDS = [
    ('nListNum', 'h'),
    ('nULEnable', 'h'),
    ('nULParamToVary', 'h'),
    ('nULRepeat', 'h'),
    ('lULParamValueListIndex', 'i'),
    ('sUnused', '52s'),
]


# Types of epoch (see head of file for description)
EPOCH_DISABLED = 0
EPOCH_STEPPED = 1
EPOCH_RAMPED = 2
EPOCH_RECTANGLE = 3
EPOCH_TRIANGLE = 4
EPOCH_COSINE = 5
EPOCH_UNUSED = 6     # Legacy issue: "was ABF_EPOCH_TYPE_RESISTANCE"
EPOCH_BIPHASIC = 7
epoch_types = {
    EPOCH_DISABLED: 'Disabled',
    EPOCH_STEPPED: 'Stepped waveform (square pulse)',
    EPOCH_RAMPED: 'Ramp waveform (fixed-angle in- or decrease)',
    EPOCH_RECTANGLE: 'Rectangular pulse train',
    EPOCH_TRIANGLE: 'Triangular waveform',
    EPOCH_COSINE: 'Cosine waveform',
    EPOCH_UNUSED: 'Unused',
    EPOCH_BIPHASIC: 'Biphasic pulse train',
}


# Fields in the epoch section (abf2)
# EpochInfoDescription = [
#       ('nEpochNum', 'h'),
#       ('nDigitalValue', 'h'),
#       ('nDigitalTrainValue', 'h'),
#       ('nAlternateDigitalValue', 'h'),
#       ('nAlternateDigitalTrainValue', 'h'),
#       ('bEpochCompression', 'b'),
#       ('sUnused', '21s'),
#   ]
ACMODE_VARIABLE_LENGTH_EVENTS = 1
ACMODE_FIXED_LENGTH_EVENTS = 2
ACMODE_GAP_FREE = 3
ACMODE_HIGH_SPEED_OSCILLOSCOPE = 4
ACMODE_EPISODIC_STIMULATION = 5
acquisition_modes = {
    # Variable length sweeps, triggered by some event
    ACMODE_VARIABLE_LENGTH_EVENTS: 'Variable-length events mode',
    # Fixed length sweeps, triggered by some event, may overlap
    ACMODE_FIXED_LENGTH_EVENTS: 'Event-driven fixed-length mode',
    # Continuous recording
    ACMODE_GAP_FREE: 'Gap free mode',
    # Fixed length non-overlapping, sweeps, triggered by some event
    ACMODE_HIGH_SPEED_OSCILLOSCOPE: 'High-speed oscilloscope mode',
    # Fixed length non-overlapping sweeps
    ACMODE_EPISODIC_STIMULATION: 'Episodic stimulation mode'
}


# DAC channel types
TYPE_UNKNOWN = 0
TYPE_VOLTAGE_CLAMP = 1
TYPE_CURRENT_CLAMP = 2
TYPE_CURRENT_CLAMP_ZERO = 4
type_modes = {
    0: TYPE_UNKNOWN,
    1: TYPE_VOLTAGE_CLAMP,
    2: TYPE_CURRENT_CLAMP,
    4: TYPE_CURRENT_CLAMP_ZERO,
}
type_mode_names = {
    0: 'Unknown',
    1: 'Voltage clamp',
    2: 'Current clamp',
    4: 'Current clamp zero',
}


# DAC waveform types
DAC_DISABLED = 0
DAC_EPOCHTABLEWAVEFORM = 1  # Epochs
DAC_DACFILEWAVEFORM = 2     # Stimulus file


# User list parameter to vary
'''
CONDITNUMPULSES 0
CONDITBASELINEDURATION 1
CONDITBASELINELEVEL 2
CONDITSTEPDURATION 3
CONDITSTEPLEVEL 4
CONDITPOSTTRAINDURATION 5
CONDITPOSTTRAINLEVEL 6
EPISODESTARTTOSTART 7
INACTIVEHOLDING 8
DIGITALINTEREPISODE 9
PNNUMPULSES 10
PARALLELVALUE(0-9) 11-20
EPOCHINITLEVEL(0-9) 21-30
EPOCHINITDURATION(0-9) 31-40
EPOCHTRAINPERIOD(0-9) 41-50
EPOCHTRAINPULSEWIDTH(0-9) 51-60
'''
