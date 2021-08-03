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

    Not all SBML features are supported, see
    :class:`myokit.formats.sbml.SBMLParser`.
    """
    def __init__(self):
        super(SBMLImporter, self).__init__()

    def supports_model(self):
        """Returns ``True``."""
        return True

    def model(self, path):
        """
        Reads the SBML model stored at ``path`` and returns a Myokit model.
        """
        parser = myokit.formats.sbml.SBMLParser()
        model = parser.parse_file(path)
        return model.myokit_model()
