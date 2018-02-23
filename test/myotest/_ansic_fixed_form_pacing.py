#
# Wrapper around test code for ansi-c fixed-form pacing.
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
SOURCE_FILE = '_ansic_fixed_form_pacing.c'


class AnsicFixedFormPacing(myokit.CModule):
    """
    Wrapper around test code for ansi-c fixed-form pacing.
    """
    _index = 0

    def __init__(self, times=None, values=None):
        super(AnsicFixedFormPacing, self).__init__()
        # Unique id
        AnsicFixedFormPacing._index += 1
        module_name = 'myokit_ansic_fpacing_' \
            + str(AnsicFixedFormPacing._index)
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
        self._sys.init(times, values)

    def pace(self, time):
        return self._sys.pace(time)

    def __del__(self):
        # Free the memory used by the pacing system
        try:
            self._sys.clean()
        except AttributeError:
            pass
