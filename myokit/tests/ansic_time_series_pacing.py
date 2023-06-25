#!/usr/bin/env python3
#
# Class for testing the time-series pacing system.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os

import myokit

from myokit.tests import DIR_TEST

# Location of C template
SOURCE_FILE = 'ansic_time_series_pacing.c'


class AnsicTimeSeriesPacing(myokit.CModule):
    """
    Class for testing the time-series pacing system.
    """
    _index = 0

    def __init__(self, protocol):
        super().__init__()

        # Unique id
        AnsicTimeSeriesPacing._index += 1
        module_name = \
            'myokit_ansic_fpacing_' + str(AnsicTimeSeriesPacing._index)

        # Arguments
        fname = os.path.join(DIR_TEST, SOURCE_FILE)

        # Create back-end
        args = {'module_name': module_name}
        libs = []
        libd = []
        incd = [DIR_TEST, myokit.DIR_CFUNC]
        self._sys = self._compile(module_name, fname, args, libs, libd, incd)

        # Initialize
        self._sys.init(protocol)

    def pace(self, time):
        return self._sys.pace(time)

    def __del__(self):
        # Free the memory used by the pacing system
        try:
            self._sys.clean()
        except AttributeError:
            pass
