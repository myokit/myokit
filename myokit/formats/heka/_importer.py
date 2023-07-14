#
# Imports step protocols from HEKA PatchMaster files.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit.formats


class PatchMasterImporter(myokit.formats.Importer):
    """
    This :class:`Importer <myokit.formats.Importer>` can import (step)
    protocols from "series" inside HEKA PatchMaster files.
    """

    def supports_protocol(self):
        return True

    def protocol(self, filename, group=None, series=None):
        """
        Attempts to load the protocol from the file at ``filename``.

        Because PatchMaster files can contain several experiments, a further
        selection can be made with the arguments:

        ``filename``
            The file to read
        ``group``
            The group to read from (as a string).
        ``series``
            The integer index of the desired series in the specified group.

        """
        from myokit.formats.heka import PatchMasterFile
        with PatchMasterFile(filename) as f:
            group = f.group(group)
            series = group[series]
            return series.stimulus().protocol()

