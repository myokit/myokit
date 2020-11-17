#
# Helper function for XML parsing.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals


def split(tag):
    """
    Splits a ``tag`` (as used in elementtree) into a namespace and an element
    name part.
    """
    tag = str(tag)
    if tag[:1] != '{':
        return None, tag
    i = tag.index('}')
    return tag[1:i], tag[1 + i:]

