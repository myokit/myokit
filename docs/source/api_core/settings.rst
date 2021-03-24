.. _api/settings:

********
Settings
********

.. currentmodule:: myokit

myokit.ini
----------

Myokit can be configured by editing the configuration file
``~/.config/myokit/myokit.ini``, where ``~`` denotes the user home directory.
This file is generated automatically when Myokit is installed, and can be
modified to indicate e.g. the version and location of the Sundials (CVODES)
library or the location of OpenCL libraries and header files.

System information
------------------

The :meth:`system()` method can be used to check if the system meets the
requirements to use Myokit and run simulations.

.. autofunction:: system

The :meth:`version()` method provides information about the current Myokit
version.

.. autofunction:: version

Myokit uses standard formats for date and time. The current date and time can
be obtained using :meth:`date()` and :meth:`time()`.

.. autofunction:: date

.. autofunction:: time

