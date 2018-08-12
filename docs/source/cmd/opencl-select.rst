.. _cmd/openclselect:

*****************
``opencl-select``
*****************

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

