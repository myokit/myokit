#
# Exports to CellML.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
import myokit.lib.guess

import warnings


class CellMLExporter(myokit.formats.Exporter):
    """
    This:class:`Exporter <myokit.formats.Exporter>` creates a CellML model.
    """
    def __init__(self):
        super(CellMLExporter, self).__init__()

    def model(self, path, model, protocol=None, version='1.0'):
        """
        Writes a CellML model to the given filename.

        Arguments:

        ``path``
            The path/filename to write the generated code to.
        ``model``
            The model to export
        ``protocol``
            If given, an attempt will be made to convert the protocol to an
            expression and insert it into the model before exporting. See
            :meth:`myokit.lib.guess.add_embedded_protocol()` for details.
        ``version``
            The CellML version to write (1.0, 1.1, or 2.0).

        """
        # Load API and writer
        if version in ('1.0', '1.1'):
            import myokit.formats.cellml.v1 as cellml
        elif version in ('2.0'):
            import myokit.formats.cellml.v2 as cellml
        else:   # pragma: no cover
            raise ValueError(
                'Only versions 1.0, 1.1, and 2.0 are supported.')

        # Embed protocol
        if protocol is not None:
            model = model.clone()
            if not myokit.lib.guess.add_embedded_protocol(model, protocol):
                warnings.warn('Unable to embed stimulus protocol.')

        # Export
        cellml_model = cellml.Model.from_myokit_model(model, version)
        cellml.write_file(path, cellml_model)

    def supports_model(self):
        """
        Returns ``True``.
        """
        return True


class CellML1Exporter(CellMLExporter):
    """
    This:class:`Exporter <myokit.formats.Exporter>` creates a CellML 1.0 model.
    """
    def model(self, path, model, protocol=None):
        super(CellML1Exporter, self).model(path, model, protocol, '1.0')


class CellML2Exporter(CellMLExporter):
    """
    This:class:`Exporter <myokit.formats.Exporter>` creates a CellML 2.0 model.
    """
    def model(self, path, model, protocol=None):
        super(CellML2Exporter, self).model(path, model, protocol, '2.0')

