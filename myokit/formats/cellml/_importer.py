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


info = """
Creates a myokit.Model definition from a CellML file.

CellML versions 1.0, 1.1, and 2.0 are supported, though with some limitations
(for full support information, see myokit.formats.cellml.v1.api.Model and
myokit.formats.cellml.v2.api.Model).
""".strip()


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
        return info

    def model(self, path):
        """
        Reads a CellML file and returns a:class:`myokit.Model`.
        """
        import myokit.formats.cellml as cellml
        import myokit.formats.cellml.v1 as v1
        import myokit.formats.cellml.v2 as v2
        parsers = {
            cellml.NS_CELLML_1_0: v1.CellMLParser,
            cellml.NS_CELLML_1_1: v1.CellMLParser,
            cellml.NS_CELLML_2_0: v2.CellMLParser,
        }

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

        # Detect namespace, create appropriate parser
        ns, el = myokit.mxml.split(root.tag)
        try:
            parser = parsers[ns]
        except KeyError:
            raise CellMLImporterError(
                'Unknown CellML version or not a CellML document at '
                + str(path) + '.')
        parser = parser()

        try:
            # Parse CellML model
            cellml_model = parser.parse(root)

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
        except v2.CellMLParsingError as e:
            raise CellMLImporterError(str(e))

    def supports_model(self):
        """
        Returns True.
        """
        return True

