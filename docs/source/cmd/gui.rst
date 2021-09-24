*********
GUI tools
*********

The command-line tools in this section each launch one of Myokit's graphical
user interface (GUI) components.

- :ref:`block <cmd/block>`
- :ref:`ide <cmd/ide>`
- :ref:`log <cmd/log>`

.. _cmd/block:

=========
``block``
=========

Launches the :ref:`DataBlock Viewer <gui/datablock_viewer>`.

Example::

    $ myokit block

Viewing a file::

    $ myokit block results.zip

For the full syntax, see::

    $ myokit block --help


.. _cmd/ide:

=======
``ide``
=======

Launches the :ref:`Myokit IDE <gui/ide>`, which can be used to edit models and
run simulations.

Example::

    $ myokit ide

Loading a file::

    $ myokit ide br-1977.mmt

For the full syntax, see::

    $ myokit ide --help


.. _cmd/log:

=======
``log``
=======

Launches the :ref:`Myokit DataLog Viewer <gui/datablock_viewer>`.

Example::

    $ myokit log

Loading a file::

    $ myokit log results.csv

For the full syntax, see::

    $ myokit log --help
