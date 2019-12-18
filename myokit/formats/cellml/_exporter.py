#
# Exports to CellML
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import inspect

import myokit
import myokit.lib.guess


class CellMLExporter(myokit.formats.Exporter):
    """
    This:class:`Exporter <myokit.formats.Exporter>` creates a CellML model.
    """
    def __init__(self):
        super(CellMLExporter, self).__init__()

    def info(self):
        return inspect.getdoc(self)

    def model(self, path, model, protocol=None, version='1.0'):
        """
        Writes a CellML model to the given filename.

        Arguments:

        ``path``
            The path/filename to write the generated code too.
        ``model``
            The model to export
        ``protocol``
            If given, an attempt will be made to convert the protocol to an
            expression and insert it into the model before exporting. See
            :meth:`myokit.lib.guess.add_embedded_protocol()` for details.
        ``version``
            The CellML version to write

        """
        # Clear log
        log = self.logger()
        log.clear()
        log.clear_warnings()
        log.log('Exporting model to CellML...')

        # Load API and writer
        # TODO Use version
        import myokit.formats.cellml.cellml_1 as api
        import myokit.formats.cellml.writer_1 as writer

        # Embed protocol
        if protocol is not None:
            model = model.clone()
            if myokit.lib.guess.add_embedded_protocol(model, protocol):
                log.log('Added embedded stimulus protocol.')
            else:
                log.warn('Unable to embed stimulus protocol.')

        # Export
        cellml_model = api.Model.from_myokit_model(model)
        writer.write_file(path, cellml_model)
        log.log('Model written to ' + str(path))

    def supports_model(self):
        """
        Returns ``True``.
        """
        return True

