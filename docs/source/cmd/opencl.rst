.. _cmd/opencl:

**********
``opencl``
**********

Displays information about the current OpenCL configuration.

See :ref:`opencl-select <cmd/openclselect>` for information about setting a
preferred device.

Example::

    $ python myo opencl
    
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

    $ python myo opencl --help
