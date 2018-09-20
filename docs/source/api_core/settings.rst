.. _api/settings:

********
Settings
********

A configuration file ``~/.config/myokit/myokit.ini`` (where ~ denotes the user
home directory) can be used to configure Myokit. Specifically, this file can be
used to indicate the location of Sundials and OpenCL shared libraries and
header files.


System information
------------------

The :meth:`system()` method can be used to check if the system meets the
requirements to use Myokit and run simulations.

.. module:: myokit

.. autofunction:: system
