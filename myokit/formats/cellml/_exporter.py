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


class CellMLExporter(myokit.formats.Exporter):
    """
    This:class:`Exporter <myokit.formats.Exporter>` creates a CellML model.
    """
    def __init__(self):
        super(CellMLExporter, self).__init__()

    def info(self):
        return inspect.getdoc(self)

    def model(self, path, model, protocol=None, add_hardcoded_pacing=True,
              version='1.0'):
        """
        Writes a CellML model to the given filename.

        Arguments:

        ``path``
            The path/filename to write the generated code too.
        ``model``
            The model to export
        ``protocol``
            This argument will be ignored: protocols are not supported by
            CellML.
        ``add_hardcoded_pacing``
            Set this to ``True`` to add a hardcoded pacing signal to the model
            file. This requires the model to have a variable bound to `pace`.
        ``version``
            The CellML version to write

        Notes about CellML export:

        * CellML expects a unit for every number present in the model. Since
          Myokit allows but does not enforce this, the resulting CellML file
          may only validate with unit checking disabled.
        * Files downloaded from the CellML repository typically have a pacing
          stimulus embedded in them, while Myokit views models and pacing
          protocols as separate things. To generate a model file with a simple
          embbeded protocol, add the optional argument
          ``add_hardcoded_pacing=True``.
        * Variables annotated with an ``oxmeta`` property will be annotated
          using the oxmeta namespace in the created CellML. For example, a
          variable with the meta-data ``oxmeta: time`` will be annotated as
          ``https://chaste.comlab.ox.ac.uk/cellml/ns/oxford-metadata#time`` in
          the CellML file.

        """
        # TODO Use version
        import myokit.formats.cellml.cellml_1 as api
        import myokit.formats.cellml.writer_1 as writer

        m = api.Model.from_myokit_model(model)
        writer.write_file(path, m)

    def supports_model(self):
        """
        Returns ``True``.
        """
        return True

