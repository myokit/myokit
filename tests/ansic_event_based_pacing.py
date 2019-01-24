#
# Class for testing the event-based pacing system.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os

import myokit

from shared import DIR_TEST


# Location of C template
SOURCE_FILE = 'ansic_event_based_pacing.c'


class AnsicEventBasedPacing(myokit.CModule):
    """
    Class for testing the event-based pacing system.
    """
    _index = 0

    def __init__(self, protocol):
        super(AnsicEventBasedPacing, self).__init__()
        # Unique id
        AnsicEventBasedPacing._index += 1
        module_name = 'myokit_ansic_pacing_' \
            + str(AnsicEventBasedPacing._index)
        # Arguments
        fname = os.path.join(DIR_TEST, SOURCE_FILE)
        # Debug
        if myokit.DEBUG:
            print(
                self._code(fname, args, line_numbers=myokit.DEBUG_LINE_NUMBERS)
            )
            import sys
            sys.exit(1)
        # Create back-end
        args = {'module_name': module_name}
        libs = []
        libd = []
        incd = [DIR_TEST, myokit.DIR_CFUNC]
        self._sys = None
        self._sys = self._compile(module_name, fname, args, libs, libd, incd)
        # Initialize
        self._sys.init(protocol.clone())
        self.advance(0)

    def __del__(self):
        # Free the memory used by the pacing system
        if self._sys is not None:
            self._sys.clean()

    def advance(self, new_time):
        """
        Advances the time in the pacing system to ``new_time``.

        Returns the current value of the pacing variable.
        """
        return self._sys.advance(new_time)

    def next_time(self):
        """
        Returns the next time the value of the pacing variable will be
        updated.
        """
        return self._sys.next_time()

    def pace(self):
        """
        Returns the current value of the pacing variable.
        """
        return self._sys.pace()

    def time(self):
        """
        Returns the current time in the pacing system.
        """
        return self._sys.time()

