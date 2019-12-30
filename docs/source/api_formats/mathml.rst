.. _formats/mathml:

******
MathML
******

Export of model equations to a Content and Presentation MathML is provided by
the mathml module. In addition, a general purpose MathML parsing method is
included.

Parsing
=======

.. currentmodule:: myokit.formats.mathml

.. autofunction:: parse_mathml_dom

.. autofunction:: parse_mathml_etree

.. autofunction:: parse_mathml_string

.. autoclass:: MathMLError

.. autoclass:: MathMLParser

Exporting
=========

.. autofunction:: exporters

.. autoclass:: HTMLExporter
    :inherited-members:

.. autoclass:: XMLExporter
    :inherited-members:

Writing expressions
===================

.. autofunction:: ewriters

.. autoclass:: MathMLExpressionWriter
    :inherited-members:

