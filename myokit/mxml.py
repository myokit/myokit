#
# Provides helper functions for import and export of XML based formats
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import re
import xml.dom
import textwrap
import HTMLParser


def dom_child(node, selector=None):
    """
    Returns the first child element of the given DOM node.

    If the optional selector is given it searches for an element of a
    particular type.

    Returns ``None`` if no such node is found.
    """
    enode = xml.dom.Node.ELEMENT_NODE
    e = node.firstChild
    if selector:
        while e is not None:
            if e.nodeType == enode and e.tagName == selector:
                return e
            e = e.nextSibling
    else:
        while e is not None:
            if e.nodeType == enode:
                return e
            e = e.nextSibling
    return None


def dom_next(node, selector=False):
    """
    Returns the next sibling element after the given DOM node.

    If the optional selector is given it searches for an element of a
    particular type.

    Returns ``None`` if no such node is found.
    """
    enode = xml.dom.Node.ELEMENT_NODE
    e = node.nextSibling
    if selector:
        while e is not None:
            if e.nodeType == enode and e.tagName == selector:
                return e
            e = e.nextSibling
    else:
        while e is not None:
            if e.nodeType == enode:
                return e
            e = e.nextSibling
    return None


def html2ascii(html, width=79, indent='  '):
    """
    Flattens HTML and attempts to create readable ASCII code.

    The ascii will be text-wrapped after ``width`` characters. Each new level
    of nesting will be indented with the text given as ``indent``.
    """
    class Asciifier(HTMLParser.HTMLParser):
        INDENT = 1
        DEDENT = -1
        WHITE = [' ', '\t', '\f', '\r', '\n']

        def __init__(self, line_width=79, indent='  '):
            HTMLParser.HTMLParser.__init__(self)  # HTMLParser is old school
            self.text = []  # Current document
            self.line = []  # Current (unwrapped) line
            self.limode = None
            self.licount = 0
            self.LW = line_width
            self.TAB = indent

        def endline(self):
            """
            End the current line.
            """
            line = ''.join(self.line)
            self.line = []
            if line:
                self.text.append(line)

        def blankline(self):
            """
            Inserts a blank line
            """
            i = -1
            last = self.text[-1:]
            while last in [[self.INDENT], [self.DEDENT]]:
                i -= 1
                last = self.text[i:1 + i]
            if last != ['']:
                self.text.append('')

        def handle_data(self, data):
            """
            Handle text between tags
            """
            data = str(data.strip().encode('ascii', 'ignore'))
            if data:
                self.line.append(data)

        def handle_starttag(self, tag, attrs):
            """
            Opening tags
            """
            if tag == 'p':
                self.blankline()
            elif tag == 'h1':
                self.text.append('=' * self.LW)
            elif tag == 'h2':
                self.blankline()
                self.text.append('-' * self.LW)
            elif tag == 'h3':
                self.blankline()
                self.text.append('.' * self.LW)
            elif tag == 'ul' or tag == 'ol':
                self.endline()
                self.text.append(self.INDENT)
                self.limode = tag
                self.licount = 0
            elif tag == 'li':
                if self.limode == 'ul':
                    self.line.append('* ')
                else:
                    self.licount += 1
                    self.line.append(str(self.licount) + ' ')
            elif tag == 'em' or tag == 'i':
                self.line.append(' *')
            elif tag == 'strong' or tag == 'b':
                self.line.append(' **')
            elif tag == 'u':
                self.line.append(' _')

        def handle_startendtag(self, tag, attrs):
            if tag == 'br':
                self.endline()
            elif tag == 'hr':
                self.text.append('-' * self.LW)

        def handle_endtag(self, tag):
            if tag == 'p':
                self.endline()
                self.blankline()
            elif tag == 'h1':
                self.endline()
                self.text.append('=' * self.LW)
                self.blankline()
            elif tag == 'h2':
                self.endline()
                self.text.append('-' * self.LW)
                self.blankline()
            elif tag == 'h3':
                self.endline()
                self.text.append('.' * self.LW)
                self.blankline()
            elif tag == 'ul' or tag == 'ol':
                self.endline()
                self.text.append(self.DEDENT)
                self.blankline()
            elif tag == 'li':
                self.endline()
            elif tag == 'em' or tag == 'i':
                self.line.append('* ')
            elif tag == 'strong' or tag == 'b':
                self.line.append('** ')
            elif tag == 'u':
                self.line.append('_ ')

        def gettext(self):
            self.endline()
            buf = []
            pre = ''
            n = self.LW
            ntab = len(self.TAB)
            dent = 0
            white = '[' + ''.join(self.WHITE) + ']+'
            space = ' '
            for line in self.text:
                if line == self.INDENT:
                    dent += 1
                    pre = dent * self.TAB
                    n -= ntab
                elif line == self.DEDENT:
                    dent -= 1
                    pre = dent * self.TAB
                    n += ntab
                else:
                    line = re.sub(white, space, line).strip()
                    if line == '':
                        buf.append('')
                    else:
                        buf.extend([pre + x for x in textwrap.wrap(line, n)])
            return ('\n'.join(buf)).strip()
    f = Asciifier(width, indent)
    f.feed(html)
    f.close()
    return f.gettext()


def write_mathml(expression, presentation):
    """
    Converts a myokit :class:`Expression` to a mathml expression.

    The boolean argument ``presentation`` can be used to select between
    Presentation MathML and Content MathML.
    """
    from myokit.formats.mathml import MathMLExpressionWriter
    w = MathMLExpressionWriter()
    w.set_mode(presentation=presentation)
    return w.ex(expression)
