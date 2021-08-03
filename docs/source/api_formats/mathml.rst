.. _formats/mathml:

******
MathML
******

Methods are provided to parse and generate expressions in Content MathML.
Presentation MathML can also be generated (but not parsed).

Parsing
=======

.. currentmodule:: myokit.formats.mathml

.. autofunction:: parse_mathml_etree

.. autofunction:: parse_mathml_string

.. autoclass:: MathMLError

.. autoclass:: MathMLParser

Writing expressions
===================

.. autofunction:: ewriters

.. autoclass:: MathMLExpressionWriter
    :inherited-members:

