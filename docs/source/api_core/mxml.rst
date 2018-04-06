.. _api/mxml:

*************
XML Functions
*************

Although Myokit's mmt format is **not** an XML format, Myokit interacts with
XML formats in various ways.  The ``myokit.mxml`` module provides XML tools for
common tasks. This module is imported as part of the main ``myokit`` package.


.. module:: myokit.mxml

Dom traversal
-------------

.. autofunction:: dom_child

.. autofunction:: dom_next


Converting html to ascii
------------------------

.. autofunction:: html2ascii


Writing html documents
----------------------

.. autoclass:: TinyHtmlPage

.. autoclass:: TinyHtmlNode

.. autoclass:: TinyHtmlScheme

.. autofunction:: write_mathml

