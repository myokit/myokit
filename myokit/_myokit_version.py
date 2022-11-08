#
# Myokit's version info
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import sys

# True if this is a release, False for a development version
__release__ = True

# Version as a tuple (major, minor, revision)
#  - Changes to major are rare
#  - Changes to minor indicate new features, possible slight backwards
#    incompatibility
#  - Changes to revision indicate bugfixes, tiny new features
#  - There is no significance to odd/even numbers
__version_tuple__ = 1, 33, 9

# String version of the version number
__version__ = '.'.join([str(x) for x in __version_tuple__])
if not __release__:  # pragma: no cover
    __version_tuple__ += ('dev', )
    __version__ += '.dev'

# Don't expose x on Python2
if sys.hexversion < 0x03000000:  # pragma: no python 3 cover
    del x
