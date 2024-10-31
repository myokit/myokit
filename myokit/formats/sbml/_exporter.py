#
# Exports to SBML.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit
import myokit.lib.guess
import myokit.formats.sbml as sbml


import warnings


class SBMLExporter(myokit.formats.Exporter):
    """
    This:class:`Exporter <myokit.formats.Exporter>` creates a SBML model.
    """

    def __init__(self):
        super().__init__()

    def model(self, path, model, protocol=None):
        """
        Writes a SBML model to the given filename.

        Arguments:

        ``path``
            The path/filename to write the generated code to.
        ``model``
            The model to export
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
        sbml_model.write_xml(path)

    def supports_model(self):
        """
        Returns ``True``.
        """
        return True
