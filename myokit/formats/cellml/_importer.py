#
# Imports a model definition from a CellML file
# Only partial CellML support is provided.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from lxml import etree

import myokit
import myokit.formats
import myokit.mxml


class CellMLImporterError(myokit.ImportError):
    """
    Raised if an error occurs when importing CellML.
    """


class CellMLImporter(myokit.formats.Importer):
    """
    This:class:`Importer <myokit.formats.Importer>` imports a model definition
    from CellML.
    """
    def __init__(self, verbose=False):
        super(CellMLImporter, self).__init__()

    def info(self):
        """
        Returns a string containing information about this importer.
        """
        return 'Creates a myokit.Model definition from a CellML file.'

    def model(self, path):
        """
        Reads a CellML file and returns a:class:`myokit.Model`.
        """
        import myokit.formats.cellml as cellml

        # Clear logger and warnings
        log = self.logger()
        log.clear()
        log.clear_warnings()
        log.log('Importing ' + str(path))

        # Open XML file
        try:
            parser = etree.XMLParser(remove_comments=True)
            tree = etree.parse(path, parser=parser)
        except Exception as e:
            raise CellMLImporterError('Unable to parse XML: ' + str(e))

        # Get root node
        root = tree.getroot()

        # Detect namespace
        ns, el = myokit.mxml.split(root.tag)
        if ns in (cellml.NS_CELLML_1_0, cellml.NS_CELLML_1_1):

            try:
                # Parse CellML1 model
                import myokit.formats.cellml.v1 as v1
                p = v1.CellMLParser()
                cellml_model = p.parse(root)

                # Log warnings, if any
                warnings = cellml_model.validate()
                for warning in warnings:
                    log.warn(warning)

                # Log result
                log.log('Import successful.')

                # Create and return Myokit model
                return cellml_model.myokit_model()

            except v1.CellMLParsingError as e:
                raise CellMLImporterError(str(e))

        raise CellMLImporterError(
            'Unknown CellML version or not a CellML document at ' + str(path)
            + '.')

    def supports_model(self):
        """
        Returns True.
        """
        return True

