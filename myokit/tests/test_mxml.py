#!/usr/bin/env python
#
# Tests some methods from myokit.mxml
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit


class AsciifierTest(unittest.TestCase):
    """
    Tests the method to convert html to ascii.
    """
    def test_asciify(self):
        html = """
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
    <title>Myokit &amp; an entity test</title>
    <base href="http://myokit.org/" />
    <link rel="stylesheet" type="text/css" media="all"
        href="http://myokit.org/static/css/myokit-16.css" />
    <script src="http://myokit.org/static/js/rainbow-custom.min.js"
        type="text/javascript"></script>
</head>
<body>
    <!--[if lt IE 7]> <div>Don't use IE.</div><![endif]-->
    <div class="header">
        <h1>Myokit</h1>
        <p>Text example 1</p>
        <!-- Image link -->
        <a href="http://myokit.org/">
            <img src="static/img/logo.png" alt="Logo" />
        </a>
        <!-- Text link -->
        <a href="link">This should be visible</a>
        <p>More text.</p>
        <p>Issue
    </div>
    <div>
        <h2>Software</h2>
        <strong>This is strong</strong> &amp; this is an ampersand.
        <hr />
        <ul>
            <li>One</li>
            <li><a href="http://myokit.org/download">Two</a></li>
        </ul>
        <h3>Resources</h3>
        <ol>
            <li>Numbered A.</li>
            <li><em>Numbered B is italic.</em></li>
            <li>
                <ul>
                    <li>C is double indented</li>
                    <li>So is D</li>
                </ul>
            </li>
            <li>E is normal again</li>
        </ol>
        <b>Bold</b><u>Underlined <i>And italic</i></u>.
        <li>This item had no list :(</li>
    </div>
</body>
</html>"""
        ascii = """
===============================================================================
Myokit
===============================================================================

Text example 1

This should be visible

More text.

Issue

-------------------------------------------------------------------------------
Software
-------------------------------------------------------------------------------

**This is strong** & this is an ampersand.
-------------------------------------------------------------------------------

  * One
  * Two

...............................................................................
Resources
...............................................................................

  1 Numbered A.
  2 *Numbered B is italic.*
  3

    * C is double indented
    * So is D

  4 E is normal again

**Bold** _Underlined *And italic* _ .
* This item had no list :(
""".strip()

        # Compare line by line
        ascii = iter(ascii.splitlines())
        for line1 in myokit.mxml.html2ascii(html).splitlines():
            # Next line will raise exception if the result is longer than ascii
            line2 = next(ascii)
            # Check if lines are equal
            self.assertEqual(line1, line2)
        # Next line will raise exception if ascii is longer than the result
        self.assertRaises(StopIteration, next, ascii)

    def test_write_mathml(self):
        """
        Test method `myokit.mxml.write_mathml`.
        """
        e = myokit.parse_expression('5 + log(x)')

        # Content MathML
        self.assertEqual(
            myokit.mxml.write_mathml(e, False),
            '<apply>'
            '<plus /><cn>5.0</cn><apply><ln /><ci>x</ci></apply>'
            '</apply>'
        )

        # Presentation MathML
        self.assertEqual(
            myokit.mxml.write_mathml(e, True),
            '<mrow>'
            '<mn>5.0</mn>'
            '<mo>+</mo>'
            '<mrow><mi>ln</mi><mfenced><mi>x</mi></mfenced></mrow>'
            '</mrow>'
        )


if __name__ == '__main__':
    unittest.main()
