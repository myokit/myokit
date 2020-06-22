#
# Flattens HTML and attempts to create readable ASCII code.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import re
import sys
import textwrap

# HTML Parser in Python 2 and 3
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser


def html2ascii(html, width=79, indent='  '):
    """
    Flattens HTML and attempts to create readable ASCII code.

    The output will be text-wrapped after ``width`` characters. Each new level
    of nesting will be indented with the text given as ``indent``.
    """
    # Create asciifier and go!
    f = Asciifier(width, indent)
    f.feed(html)
    f.close()
    return f.get_text()


class Asciifier(HTMLParser):
    INDENT = 1
    DEDENT = -1
    WHITE = [' ', '\t', '\f', '\r', '\n']

    def __init__(self, line_width=79, indent='  '):
        if sys.hexversion < 0x03000000:     # pragma: no python 3 cover
            # HTMLParser requires old-school constructor
            HTMLParser.__init__(self)
        else:                               # pragma: no python 2 cover
            super(Asciifier, self).__init__(convert_charrefs=False)

            # Unescape method is deprecated
            import html
            self.unescape = html.unescape

        # In <head> yes/no
        self.inhead = False

        self.text = []  # Current document
        self.line = []  # Current (unwrapped) line

        # Ordered/unorderd lists
        self.limode = []
        self.licount = []

        # Output options
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
        Inserts a blank line.
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
        # Ignore content while in head
        if self.inhead:
            return

        # Convert to ascii and back to remove all non-ascii content
        data = data.encode('ascii', 'ignore').decode('ascii')

        # Non-empty? Then add to line
        if data:
            self.line.append(data)

    def handle_starttag(self, tag, attrs):
        """ Called when a start tag is encountered. """
        if ':' in tag:
            tag = tag[1 + tag.index(':'):]

        if tag == 'head':
            self.inhead = True

        elif tag == 'p':
            self.endline()
            self.blankline()

        elif tag == 'h1':
            self.endline()
            self.blankline()
            self.text.append('=' * self.LW)

        elif tag == 'h2':
            self.endline()
            self.blankline()
            self.text.append('-' * self.LW)

        elif tag == 'h3':
            self.endline()
            self.blankline()
            self.text.append('.' * self.LW)

        elif tag == 'ul' or tag == 'ol':
            self.endline()
            self.blankline()
            self.text.append(self.INDENT)
            self.limode.append(tag)
            self.licount.append(0)

        elif tag == 'li':
            self.endline()
            # Get mode and count, or use default if not set
            if len(self.limode):
                limode = self.limode[-1]
                licount = self.licount[-1]
                self.licount[-1] += 1
            else:
                limode = 'ul'
                licount = 0

            # Add bullet
            if limode == 'ul':
                self.line.append('* ')
            else:
                self.line.append(str(1 + licount) + u' ')

        elif tag == 'em' or tag == 'i':
            self.line.append(' *')

        elif tag == 'strong' or tag == 'b':
            self.line.append(' **')

        elif tag == 'u':
            self.line.append(' _')

    def handle_startendtag(self, tag, attrs):
        """ Called when an open/end tag is encountered. """
        if ':' in tag:
            tag = tag[1 + tag.index(':'):]

        if tag == 'br':
            self.endline()

        elif tag == 'hr':
            self.endline()
            self.text.append('-' * self.LW)
            self.endline()

    def handle_endtag(self, tag):
        """ Called when an endtag is encountered. """
        if ':' in tag:
            tag = tag[1 + tag.index(':'):]

        if tag == 'head':
            self.inhead = False

        elif tag == 'p':
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

            if len(self.limode):
                self.limode.pop()
            if len(self.licount):
                self.licount.pop()

        elif tag == 'li':
            pass

        elif tag == 'em' or tag == 'i':
            self.line.append('* ')

        elif tag == 'strong' or tag == 'b':
            self.line.append('** ')

        elif tag == 'u':
            self.line.append('_ ')

    def handle_entityref(self, name):
        # Ignore content while in head
        if self.inhead:
            return

        # Convert html characters
        data = self.unescape('&' + name + ';')

        # Convert to ascii and back to strip out non-ascii content
        data = data.encode('ascii', 'ignore').decode('ascii')

        # Non-empty? Then add to line
        if data:
            self.line.append(data)

    def get_text(self):
        self.endline()
        buf = []
        pre = ''
        n = self.LW
        ntab = len(self.TAB)
        dent = 0
        white = '[' + ''.join(self.WHITE) + ']+'
        space = ' '
        next_can_be_blank = False
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
                    if next_can_be_blank:
                        buf.append('')
                        next_can_be_blank = False
                else:
                    buf.extend([pre + x for x in textwrap.wrap(line, n)])
                    next_can_be_blank = True
        return ('\n'.join(buf)).strip()

