#
# Exports to MathML based formats.
#
# This file is part of Myokit.
# See https://github.com/myokit/myokit for copyright, sharing, and licensing.
#
from lxml import etree

import myokit


class HTMLExporter(myokit.formats.Exporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a HTML file
    displaying a model's equations.

    The equations are encoded using Presentation MathML. This format can be
    viewed in most modern browsers, but is less suitable as an exchange format.
    """

    def model(self, path, model, protocol=None):
        """
        Export to a HTML document.

        A :class:`myokit.ExportError` will be raised if any errors occur.

        Arguments:

        ``path``
            The path to write the generated model to.
        ``model``
            The :class:`myokit.Model` to export.
        ``protocol``
            This will be ignored: protocol export is not supported.

        """
        # Get model name
        try:
            name = model.meta['name']
        except KeyError:
            name = 'Generated model'

        # Create model html element
        html = etree.Element('html')
        head = etree.SubElement(html, 'head')
        title = etree.SubElement(head, 'title')
        title.text = name
        body = etree.SubElement(html, 'body')
        heading = etree.SubElement(body, 'h1')
        heading.text = name

        # Create expression writer
        import myokit.formats.mathml
        writer = myokit.formats.mathml.MathMLExpressionWriter()
        writer.set_mode(presentation=True)
        writer.set_time_variable(model.time())

        # Write equations, per component
        for component in model.components():
            div = etree.SubElement(body, 'div')
            div.attrib['class'] = 'component'
            heading = etree.SubElement(div, 'h2')
            heading.text = component.qname()
            for var in component.variables(deep=True):
                div2 = etree.SubElement(div, 'div')
                div2.attrib['class'] = 'variable'
                math = etree.SubElement(div2, 'math')
                math.attrib['xmlns'] = 'http://www.w3.org/1998/Math/MathML'
                writer.eq(var.eq(), math)

        # Write xml to file
        path = str(path)
        doc = etree.ElementTree(html)
        doc.write(path, encoding='utf-8', method='xml')

        # Pretty output
        import xml.dom.minidom as m
        xml = m.parse(path)
        with open(path, 'wb') as f:
            f.write(xml.toprettyxml(encoding='utf-8'))

    def supports_model(self):
        """ Returns ``True``. """
        return True

