#
# Imports a model from an SBML file.
# Only partial SBML support (Based on SBML level 3 version 2) is provided.
# The file format specifications can be found here
# http://sbml.org/Documents/Specifications.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit.formats


class SBMLImporter(myokit.formats.Importer):
    """
    This :class:`Importer <myokit.formats.Importer>` loads model definitions
    from files in SBML format.
    """
    def __init__(self):
        super(SBMLImporter, self).__init__()

    def supports_model(self):
        """See :meth:`myokit.formats.Importer.supports_model`."""
        return True

    def model(self, path):
        """See :meth:`myokit.formats.Importer.model`."""
        parser = myokit.formats.sbml.SBMLParser()
        return parser.parse_file(path)
