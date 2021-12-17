**************************
Installation and debugging
**************************

The command-line tools listed in this section can be used to install, debug an
installation, or test an installation of Myokit.

- :ref:`compiler <cmd/compiler>`
- :ref:`icons <cmd/icons>`
- :ref:`opencl <cmd/opencl>`
- :ref:`opencl-select <cmd/openclselect>`
- :ref:`reset <cmd/reset>`
- :ref:`sundials <cmd/sundials>`
- :ref:`system <cmd/system>`
- :ref:`test <cmd/test>`
- :ref:`version <cmd/version>`


.. _cmd/compiler:

============
``compiler``
============

Myokit simulations make use of a locally installed compiler.
The ``myokit compiler`` command tests this functionality, by compiling a small
test module that queries the system for the installed compiler.

Example::

    $ myokit compiler

Example output::

    Compilation successful. Found: GCC 11.2.1

If compilation is unsuccessful, more information may be obtained by using::

    $ myokit compiler --debug


.. _cmd/icons:

=========
``icons``
=========

Installs shortcut icons on Linux or Windows.
On Linux, it also creates the ``.mmt`` mime-type and registers Myokit as a tool
to handle ``.mmt`` and various other file types.

Example::

    $ myokit icons


.. _cmd/opencl:

==========
``opencl``
==========

Displays information about the current OpenCL configuration.

See :ref:`opencl-select <cmd/openclselect>` for information about setting a
preferred device.

Example::

    $ myokit opencl

Example output::

    Platform 0
     Current id : 22734896
     Name       : Intel(R) OpenCL
     Vendor     : Intel(R) Corporation
     Version    : OpenCL 1.2 LINUX
     Profile    : FULL_PROFILE
     Extensions : cl_khr_fp64 cl_khr_icd
     Devices    :
      Device 0
       Current id      : 21277656
       Name            : Intel(R) Core(TM) i5-2520M CPU @ 2.50GHz
       Vendor          : Intel(R) Corporation
       Version         : OpenCL 1.2 (Build 67279)
       Driver          : 1.2
       Clock speed     : 2500 MHz
       Global memory   : 7870 MB
       Local memory    : 32 KB
       Constant memory : 128 KB
       Max work groups : 1024
       Max work items  : [1024, 1024, 1024]
       Max param size  : 3840 bytes

For the full syntax, see::

    $ myokit opencl --help


.. _cmd/openclselect:

=================
``opencl-select``
=================

Allows the Myokit-wide OpenCL device selection to be inspected and set.

See :ref:`opencl <cmd/opencl>` for more about obtaining detailed
information about platforms and devices.

Example::

    $ myokit opencl-select

Example output::

    Loading Myokit...
    ======================================================================
    Myokit OpenCL device selection
    ======================================================================
    Selected platform: No preference
    Selected device  : No preference
    ======================================================================
    Available devices:
    ----------------------------------------------------------------------
    (1) Select automatically.
    ----------------------------------------------------------------------
    (2) Platform: NVIDIA CUDA
        Device: GeForce GT 640
        901 MHz, 3.9 GB global, 48.0 KB local, 64.0 KB const
    ----------------------------------------------------------------------
    Please select an OpenCL device by typing 1 or 2
    Leave blank to keep current selection.
    Select device:

If you have multiple OpenCL devices, this will allow a preference to be set.
If no preferred device of platform is set, Myokit is will pick the first
platform and device, but with a preference for GPUs over CPUs.


.. _cmd/reset:

=========
``reset``
=========

Resets all user settings by removing all Myokit configuration files. This will
cause Myokit to recreate the files with default settings the next time Myokit
is run.

Typical use::

    $ myokit reset

This will prompt you to confirm (by typing "yes" or "y") the reset. To bypass
the reset, use::

    $ myokit reset --force


.. _cmd/sundials:

============
``sundials``
============

Compiles a small test module that queries the system for the installed SUNDIALS
version (if any).

Example::

    $ myokit sundials

Example output::

    Found Sundials version 5.6.1


.. _cmd/system:

==========
``system``
==========

Retrieves and prints system information which can be used to debug a Myokit
installation.

Example::

    $ myokit system

Example output::

    == System information ==
    Myokit: 1.33.1
    Python: 3.9.7 (default, Aug 30 2021, 00:00:00)
            [GCC 11.2.1 20210728 (Red Hat 11.2.1-1)]
    OS: Linux (linux, posix)

    == Python requirements ==
    NumPy: 1.20.1
    SciPy: 1.6.2
    Matplotlib: 3.4.3
    ConfigParser: OK
    Setuptools: 53.0.0

    == Python extras ==
    SymPy: 1.8
    MoviePy: 1.0.3

    == GUI ==
    PyQt5: 5.15.2
      Sip: OK
    PyQt4: 4.8.7
      Sip: OK
    PySide: Not found
    PySide2: 5.15.2

    == Development tools ==
    Sphinx: 3.4.3
    Flake8: 3.8.4

    == Simulation tools ==
    Compiler: GCC 11.2.1
    Sundials: 5.6.1
    OpenCL: 2 device(s) found
      Intel(R) Core(TM) i9-10885H CPU @ 2.40GHz on Intel(R) CPU Runtime for OpenCL(TM) Applications
      Intel(R) UHD Graphics [0x9bc4] on Intel(R) OpenCL HD Graphics
      Use `python -m myokit opencl` for more information.

    = /home/michael/.config/myokit/myokit.ini =
    [myokit]
    # This file can be used to set global configuration options for Myokit.

    [time]
    # Date format used throughout Myokit
    # Format should be acceptable for time.strftime
    date_format = %Y-%m-%d %H:%M:%S
    # Time format used throughout Myokit
    time_format = %H:%M:%S

    [debug]
    # Add line numbers to debug output of simulations
    line_numbers = True

    [gui]
    # Backend to use for graphical user interface.
    # Valid options are "pyqt5", "pyqt4" or "pyside".
    # Leave unset for automatic selection.
    #backend = pyqt5
    #backend = pyqt4
    #backend = pyside

    [sundials]
    # Location of sundials shared libary files (.so or .dll).
    # Multiple paths can be set using ; as separator.
    #lib = /usr/local/lib;/opt/local/lib
    # Location of sundials header files (.h).
    #inc = /usr/local/include;/opt/local/include
    version = 50300

    [opencl]
    # Location of opencl shared libary files (.so or .dll).
    # Multiple paths can be set using ; as separator.
    lib = /usr/lib64;/usr/lib64/nvidia;/usr/local/cuda/lib64
    # Location of opencl header files (.h).
    inc = /usr/include/CL;/usr/local/cuda/include


.. _cmd/test:

============
``test``
============

Runs Myokit's unit tests. On a successful installation, these should complete
without failures

Example::

    $ myokit test

When run form a development source tree (i.e. from within a cloned myokit
repository) this command provides additional options, e.g. for style and
documentation checking.


.. _cmd/version:

===========
``version``
===========

Displays the current Myokit version.

    $ myokit version

Example output::

     Myokit version 1.21.0         |/\
    _______________________________|  |______

To leave out the decorations, use::

    $ myokit version --raw

which returns::

    1.21.0

