.. _formats/latex:

*****
Latex
*****

Export of model equations to latex (or even LaTeX) is provided.

Limitations:

  - The pacing mechanism is not included in the resulting documents

API
===

The standard exporting API is provided:

.. module:: myokit.formats.latex

.. autofunction:: exporters

.. autoclass:: PdfExporter
    :members:

.. autoclass:: PosterExporter
    :members:

.. autofunction:: ewriters

.. autoclass:: LatexExpressionWriter
    :members:
    :inherited-members:
