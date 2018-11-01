#
# Exec function that works with Python versions before 2.7.9 (0x020709F0)
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#


def _exec(script, globals=None, locals=None):
    """
    Wrapper around the built-in function ``exec`` on Python versions 2.7.9 and
    higher 2.7.9, or a function calling the ``exec`` statement on earlier
    versions.
    """
    exec script in globals, locals
