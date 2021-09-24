.. _cmd/index:

******************
Command line tools
******************

Myokit comes with a command line utility that can be used to perform
various tasks from the command line.

This can be run by typing

    $ python -m myokit

from the command line, in the myokit directory. If you have installed Myokit
using pip or setup.py, you can also use

    $ myokit

from anywhere in your system.

Run without any additional arguments, the script loads the myokit model editing
GUI. By adding arguments several other commands can be selected. To get a full
overview, type::

    $ myokit -h

To get help on a subcommand, the same argument is used. For example, to get
help about the ``export`` command, use::

    $ myokit export -h

The documentation for these commands in split into the following sections:

..  toctree::

    gui
    util
    system

