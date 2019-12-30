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


# class CellMLExporterError(myokit.ImportError):
#    """
#    Raised if an error occurs when exporting CellML.
#    """


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
        if version in ('1.0', '1.1'):
            import myokit.formats.cellml.v1 as cellml

        else:   # pragma: no cover
            raise ValueError('Only versions 1.0 and 1.1 are supported.')

        # Embed protocol
        if protocol is not None:
            model = model.clone()
            if myokit.lib.guess.add_embedded_protocol(model, protocol):
                log.log('Added embedded stimulus protocol.')
            else:
                log.warn('Unable to embed stimulus protocol.')

        # Export
        cellml_model = cellml.Model.from_myokit_model(model, version)
        cellml.write_file(path, cellml_model)
        log.log('Model written to ' + str(path))

    def supports_model(self):
        """
        Returns ``True``.
        """
        return True

