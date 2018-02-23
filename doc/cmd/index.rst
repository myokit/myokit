.. _cmd/index:

******************
Command line tools
******************

Myokit comes with a script called ``myo`` that can be used to perform
various tasks from the command line.

On linux, the script can be run directly by typing::

    $ ./myo
    
from the command line, in the myokit directory. On other systems, use::

    $ python myo
    
Run without any additional arguments, the script loads the myokit model editing
GUI. By adding arguments several other commands can be selected. To get a full
overview, type::

    $ python myo -h

To get help on a subcommand, the same argument is used. For example, to get
help about the ``export`` command, use::

    $ python myo export -h
    
..  toctree::
    :hidden:

    block
    compare
    debug
    eval
    export
    gde
    ide
    import
    log
    opencl
    opencl-select
    reset
    run
    step
    update
    version
    video

