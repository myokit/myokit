.. _gui/datalog_viewer:

**************
DataLog Viewer
**************

Prototype of a viewer for files that can be read as a DataLog (e.g. patch-clamp
data).
Can currently read CSV and text files, ABF files, WCP files, and some Matlab
files.

.. module:: myokit.gui.datalog_viewer

Implementation
==============

.. autoclass:: DataLogViewer

Widgets
-------

.. autoclass:: AbfTab

.. autoclass:: CsvTab

.. autoclass:: MatTab

.. autoclass:: TxtTab

.. autoclass:: WcpTab
