.. _formats/cuda_kernel:

****
CUDA
****

Export to a CUDA kernel

Notes:

  - Only a kernel file is exported, no simulation engine, protocol or
    post-processing is included.

API
===

The standard interface for exporting and accessing expression writers is
provided:

.. module:: myokit.formats.cuda

.. autofunction:: exporters

.. autoclass:: CudaKernelExporter
    :members:

.. autofunction:: ewriters

.. autoclass:: CudaExpressionWriter
    :members:
    :inherited-members:
