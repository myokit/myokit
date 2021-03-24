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

The :meth:`version()` method

.. autofunction:: version

