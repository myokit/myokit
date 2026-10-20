#
# Imports selected types of protocols from files in Axon Binary Format
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit.formats


class AbfImporter(myokit.formats.Importer):
    """
    This :class:`Importer <myokit.formats.Importer>` can import protocols from
    files in Axon Binary Format.
    """

    def supports_protocol(self):
        return True

    def protocol(self, filename, channel=0):
        """
        Attempts to load the protocol from the file at ``filename``.

        If specified, the channel index ``channel`` will be used to select
        which channel in the AbfFile to convert to a protocol
        """
        from myokit.formats.axon import AbfFile
        abf = AbfFile(filename)
        return abf.da_protocol(channel)
