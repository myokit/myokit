#
# Exports to SBML.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import warnings

import myokit
from myokit.formats.sbml._writer import write_file
import myokit.lib.guess
import myokit.formats.sbml as sbml


class SBMLExporter(myokit.formats.Exporter):
    """
    This :class:`Exporter<myokit.formats.Exporter>` creates an SBML model.
    """

    def __init__(self):
        super().__init__()

    def model(self, path, model, protocol=None):
        """
        Writes an SBML model to the given filename.

        Arguments:

        ``path``
            The path/filename to write the generated code to.
        ``model``
            The model to export.
        ``protocol``
            If given, an attempt will be made to convert the protocol to an
            expression and insert it into the model before exporting. See
            :meth:`myokit.lib.guess.add_embedded_protocol()` for details.

        """
        # Embed protocol
        if protocol is not None:
            model = model.clone()
            if not myokit.lib.guess.add_embedded_protocol(model, protocol):
                warnings.warn("Unable to embed stimulus protocol.")

        # Export
        sbml_model = sbml.Model.from_myokit_model(model)
        write_file(path, sbml_model)

    def supports_model(self):
        """
        Returns ``True``.
        """
        return True
