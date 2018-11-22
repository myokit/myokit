.. _gui/datablock_viewer:

****************
DataBlock Viewer
****************

Viewer for :class:`myokit.DataBlock1d` or :class:`myokit.DataBlock2d` objects.
Allows loading blocks from disk, and then visualising as interactive movies.
Any point in the movie can be clicked to obtain the local action potential (or
other variables).

.. module:: myokit.gui.datablock_viewer

Implementation
==============

.. autoclass:: DataBlockViewer

.. autofunction:: icon

Widgets
-------

.. autoclass:: GraphArea

.. autoclass:: VideoScene

.. autoclass:: VideoView
