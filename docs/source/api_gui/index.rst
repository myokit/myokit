.. _api/gui:

********************************
API :: Graphical User Interfaces
********************************

Myokit comes equipeed with a number of graphical user interface components:

- The :ref:`Myokit IDE <gui/ide>` (for *integrated development environment*)
  allows you to create, import and modify mmt files. Simulations can be run and
  some analysis tools can be used directly.
- The :ref:`DataBlock Viewer <gui/datablock_viewer>` visualizes data from 1d
  and 2d datablock files.

..  toctree::
    :hidden:

    datablock_viewer
    datalog_viewer
    explorer
    ide
    progress
    source
    vargrapher

================
Shared functions
================

.. module:: myokit.gui

.. autofunction:: icon

.. autofunction:: run

.. autoclass:: MyokitApplication
    :private-members:

.. autofunction:: qtMonospaceFont

