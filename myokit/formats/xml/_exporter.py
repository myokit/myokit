#
# Exports to a generic XML format.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from lxml import etree

import myokit


class XMLExporter(myokit.formats.Exporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates an XML file
    containing a model's equations, encoded in Content MathML.
    """

    def model(self, path, model, protocol=None):
        """
        Export the model to a generic xml document.

        Arguments:

        ``path``
            The path to store the document.
        ``model``
            The model to export.
        ``protocol``
            This will be ignored: protocol export is not supported.

        """
        # Create model xml element
        root = etree.Element('math')
        root.attrib['xmlns'] = 'http://www.w3.org/1998/Math/MathML'

        # Create expression writer
        import myokit.formats.mathml
        writer = myokit.formats.mathml.MathMLExpressionWriter()
        writer.set_mode(presentation=False)
        writer.set_time_variable(model.time())

        # Write equations
        for var in model.variables(deep=True):
            writer.eq(var.eq(), root)

        # Write xml to file
        path = str(path)
        doc = etree.ElementTree(root)
        doc.write(path, encoding='utf-8', method='xml')

        # Pretty output
        if True:
            import xml.dom.minidom as m
            xml = m.parse(path)
            with open(path, 'wb') as f:
                f.write(xml.toprettyxml(encoding='utf-8'))

    def supports_model(self):
        """
        Returns ``True``.
        """
        return True

