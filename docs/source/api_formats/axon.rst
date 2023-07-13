.. _formats/abf:

************************
Axon Instruments Formats
************************

.. module:: myokit.formats.axon

Support is provided for reading data and protocols from Axon Binary Files
(ABF versions 1 and 2) and for reading and writing data in the Axon Text File
(ATF) format.

Time series and meta data can be read using the classes :class:`AbfFile` and
:class:`AtfFile`. Stored protocol data can also be retrieved from ABF files.
A :class:`DataLog` can be stored in ATF format using :meth:`save_atf`.

The :class:`AbfFile` class implements Myokit's shared
:class:`myokit.formats.SweepSource` interface.

.. autoclass:: AbfFile

.. autoclass:: Sweep

.. autoclass:: Channel

.. autoclass:: AtfFile

.. autofunction:: load_atf

.. autofunction:: save_atf

Protocols can be read from ABF files using the standard interface:

.. autofunction:: importers

.. autoclass:: AbfImporter

Licensing (ABF)
===============
The standard myokit license applies to this file.
However, it should be noted that the :class:`AbfFile` class is in part derived
from code found in the Neo package for representing electrophysiology data,
specifically from a python module authored by ``sgarcia`` and ``jnowacki``. Neo
can be found at: http://neuralensemble.org/trac/neo

The Neo package is licensed using the following BSD License::

    Copyright (c) 2010-2012, Neo authors and contributors
    All rights reserved.
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    Neither the names of the copyright holders nor the names of the
    contributors may be used to endorse or promote products derived from this
    software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.

The code used in Neo is itself derived from the publicly contributed matlab
script ``abf2load``, again licensed under BSD. The original notice follows::

    Copyright (c) 2009, Forrest Collman
    Copyright (c) 2004, Harald Hentschke
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.

The ``abf2load`` script is available from:
http://www.mathworks.com/matlabcentral/fileexchange/22114-abf2load

Information (but no direct code) from the matlab script ``get_abf_header.m``
was also used: http://neurodata.hg.sourceforge.net/hgweb/neurodata/neurodata/
