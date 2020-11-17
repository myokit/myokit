#!/usr/bin/env python3
#
# Tests the HTML support functions.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit.formats.html


html = """
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:xhtml="http://www.w3.org/1999/xhtml"
      lang="en">
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
        This has a<xhtml:br />
        line break.
        <ol>
            <xhtml:li>Numbered A.</xhtml:li>
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

This has a
line break.

  1 Numbered A.
  2 *Numbered B is italic.*
  3

    * C is double indented
    * So is D

  4 E is normal again

**Bold** _Underlined *And italic* _ .
* This item had no list :(
""".strip()


class AsciifierTest(unittest.TestCase):
    """
    Tests the method to convert html to ascii.
    """
    def test_asciify(self):

        # Compare line by line
        asc = iter(ascii.splitlines())
        for line1 in myokit.formats.html.html2ascii(html).splitlines():
            # Next line will raise exception if the result is longer than ascii
            line2 = next(asc)
            # Check if lines are equal
            self.assertEqual(line1, line2)

        # Next line will raise exception if ascii is longer than the result
        self.assertRaises(StopIteration, next, asc)


if __name__ == '__main__':
    unittest.main()
