#
# Imports selected types of protocols from files in Axon Binary Format
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit.formats


class AbfImporter(myokit.formats.Importer):
    """
    This :class:`Importer <myokit.formats.Importer>` can import protocols from
    files in Axon Binary Format.
    """

    def supports_protocol(self):
        return True

    def protocol(self, filename, channel=None):
        """
        Attempts to load the protocol from the file at ``filename``.

        If specified, the channel index ``channel`` will be used to select
        which channel in the AbfFile to convert to a protocol
        """
        from myokit.formats.axon import AbfFile
        abf = AbfFile(filename)
        return abf.myokit_protocol(channel)
