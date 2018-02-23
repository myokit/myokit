#
# Wrapper around pacing.h test code.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import myokit
import myotest


# Location of C template
SOURCE_FILE = '_ansic_event_based_pacing.c'


class AnsicEventBasedPacing(myokit.CModule):
    """
    Wrapper around pacing.h test code.
    """
    _index = 0

    def __init__(self, protocol):
        super(AnsicEventBasedPacing, self).__init__()
        # Unique id
        AnsicEventBasedPacing._index += 1
        module_name = 'myokit_ansic_pacing_' \
            + str(AnsicEventBasedPacing._index)
        # Arguments
        fname = os.path.join(myotest.DIR_TEST, SOURCE_FILE)
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
        incd = [myotest.DIR_TEST, myokit.DIR_CFUNC]
        self._sys = self._compile(module_name, fname, args, libs, libd, incd)
        # Initialize
        self._sys.init(protocol.clone())
        self.advance(0)

    def __del__(self):
        # Free the memory used by the pacing system
        self._sys.clean()

    def advance(self, new_time, max_time=None):
        """
        Advances the time in the pacing system to ``new_time``.

        Returns the current value of the pacing variable.
        """
        if max_time is None:
            max_time = float('inf')
        return self._sys.advance(new_time, max_time)

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

    @staticmethod
    def create_log_for_interval(protocol, a, b, for_drawing=False):
        """
        Creates a :class:`myokit.DataLog` containing the entries `time`
        and `pace` representing the value of the pacing stimulus at each point.

        The time points in the log will be on the interval ``[a, b]``, such
        that every time at which the pacing value changes is present in the
        log.

        If ``for_drawing`` is set to ``True`` each time value between ``a`` and
        ``b`` will be listed twice, so that a vertical line can be drawn from
        the old to the new pacing value.
        """
        # Test the input
        a, b = float(a), float(b)
        if b < a:
            raise ValueError('The argument `b` cannot be smaller than `a`')
        # Create a simulation log
        log = myokit.DataLog()
        log.set_time_key('time')
        log['time'] = time = []
        log['pace'] = pace = []
        # Create a pacing system
        p = AnsicEventBasedPacing(protocol)
        # Fill in points
        t = a
        v = p.advance(t, max_time=b)
        time.append(t)
        pace.append(v)
        while t < b:
            t = p.next_time()
            if for_drawing:
                if t != b:
                    time.append(t)
                    pace.append(v)
            v = p.advance(t, max_time=b)
            time.append(t)
            pace.append(v)
        return log
