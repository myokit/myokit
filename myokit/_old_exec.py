#
# Exec function that works with Python versions before 2.7.9 (0x020709F0)
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
def execf(script, globals=None, locals=None):
    exec script in globals, locals
