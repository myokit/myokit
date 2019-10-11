#
# Exec function that works with Python versions before 2.7.9 (0x020709F0)
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#


def _exec(script, globals=None, locals=None):
    """
    Wrapper around the built-in function ``exec`` on Python versions 2.7.9 and
    higher 2.7.9, or a function calling the ``exec`` statement on earlier
    versions.
    """
    exec script in globals, locals
