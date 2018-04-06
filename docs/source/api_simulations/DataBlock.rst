.. _api/simulations/myokit.DataBlocks:

***********
Data blocks
***********
.. module:: myokit

Data blocks provide a useful representation for data logged in rectangular 1d
or 2d simulations. They can be created from :class:`DataLog` objects containing
data in a suitable form.

In ``DataLogs``, the data is stored per variable, per cell. That means the
time-series for the membrane potential of cell ``(x,y)`` is stored in one list
and the time-series for the same variable of cell ``(u,v)`` is stored in
another. In some cases, it can be beneficial to have a reshaped view of the
data, where the membrane potential has a single time-series of 2d (or 1d)
values. This representation is provided by the ``DataBlock`` classes.

An additional feature of data blocks is that they make strong assumptions about
the stored data:

- Each 1d or 2d series has the same dimensions ``(w)`` or ``(w, h)``.
- The data represents a rectangular grid of cells.
- The cell indices run from ``0`` to ``w-1`` in the x-direction, and ``0`` to
  ``h-1`` in the y-direction.

By contrast, the :class:`DataLog` class only assumes that each time series it
contains has the same length.

The class
:class:`DataBlockViewer <myokit.gui.datablock_viewer.DataBlockViewer>` provides
a GUI for visualising :class:`DataBlock1d` and :class:`DataBlock2d` objects.

.. autoclass:: DataBlock1d

.. autoclass:: DataBlock2d

.. autoclass:: ColorMap
