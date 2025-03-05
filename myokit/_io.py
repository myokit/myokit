#
# Myokit auxillary functions: This module can be used to gather any
# functions that are important enough to warrant inclusion in the main
# myokit module but don't belong to any specific hidden module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import array
import io
import os
import sys

import myokit


def _examplify(filename):
    """
    If ``filename`` is equal to "example" and there isn't a file with that
    name, this function returns the file specified by myokit.EXAMPLE. In all
    other cases, the original filename is returned.
    """
    if filename == 'example' and not os.path.exists(filename):
        return myokit.EXAMPLE
    else:
        return os.path.expanduser(filename)


def load(filename):
    """
    Reads an ``mmt`` file and returns a tuple ``(model, protocol, embedded
    script)``.

    If the file specified by ``filename`` doesn't contain one of these parts
    the corresponding entry in the tuple will be ``None``.
    """
    f = open(_examplify(filename), 'r')
    try:
        return myokit.parse(f)
    finally:
        f.close()


def load_model(filename):
    """
    Loads the model section from an ``mmt`` file.

    Raises a :class:`SectionNotFoundError` if no model section is found.
    """
    filename = _examplify(filename)
    with open(filename, 'r') as f:
        section = myokit.split(f)[0]
        if not section.strip():
            raise myokit.SectionNotFoundError('Model section not found.')
        return myokit.parse(section.splitlines())[0]


def load_protocol(filename):
    """
    Loads the protocol section from an ``mmt`` file.

    Raises a :class:`SectionNotFoundError` if no protocol section is found.
    """
    filename = _examplify(filename)
    with open(filename, 'r') as f:
        section = myokit.split(f)[1]
        if not section.strip():
            raise myokit.SectionNotFoundError('Protocol section not found.')
        return myokit.parse(section.splitlines())[1]


def load_script(filename):
    """
    Loads the script section from an ``mmt`` file.

    Raises a :class:`SectionNotFoundError` if no script section is found.
    """
    filename = _examplify(filename)
    with open(filename, 'r') as f:
        section = myokit.split(f)[2]
        if not section.strip():
            raise myokit.SectionNotFoundError('Script section not found.')
        return myokit.parse(section.splitlines())[2]


def load_state(filename, model=None):
    """
    Loads a model state from a file in one of the formats specified by
    :func:`myokit.parse_state()`.

    If a :class:`Model` is provided the state will be run through
    :meth:`Model.map_to_state()` and returned as a list of floating point
    numbers.
    """
    filename = os.path.expanduser(filename)
    with open(filename, 'r') as f:
        s = myokit.parse_state(f)
        if model:
            s = model.map_to_state(s)
        return s


def load_state_bin(filename):
    """
    Loads a model state from a file in the binary format used by Myokit.

    See :meth:`save_state_bin` for details.
    """
    filename = os.path.expanduser(filename)

    # Load compression modules
    import zipfile
    try:
        import zlib
        del zlib
    except ImportError:
        raise Exception(
            'This method requires the `zlib` module to be installed.')

    # Open file
    with zipfile.ZipFile(filename, 'r') as f:
        info = f.infolist()

        if len(info) != 1:  # pragma: no cover
            raise Exception('Invalid state file format [10].')

        # Split into parts, get data type and array size
        info = info[0]
        parts = info.filename.split('_')

        if len(parts) != 3:     # pragma: no cover
            raise Exception('Invalid state file format [20].')

        if parts[0] != 'state':     # pragma: no cover
            raise Exception('Invalid state file format [30].')

        code = parts[1]
        if code not in ['d', 'f']:  # pragma: no cover
            raise Exception('Invalid state file format [40].')

        size = int(parts[2])
        if size < 0:    # pragma: no cover
            raise Exception('Invalid state file format [50].')

        # Create array, read bytes into array
        ar = array.array(code)
        ar.frombytes(f.read(info))

        # Always store as little endian
        if sys.byteorder == 'big':  # pragma: no cover
            ar.byteswap()

    return list(ar)


def save(filename=None, model=None, protocol=None, script=None):
    """
    Saves a model, protocol, and embedded script to an ``mmt`` file.

    The ``model`` argument can be given as plain text or a
    :class:`myokit.Model` object. Similarly, ``protocol`` can be either a
    :class:`myokit.Protocol` or its textual represenation.

    If no filename is given the ``mmt`` code is returned as a string.
    """
    if model is None and protocol is None and script is None:
        raise ValueError(
            'At least one of [model, protocol, script] must not be None.')

    if filename:
        filename = os.path.expanduser(filename)
        f = open(filename, 'w')
    else:
        f = io.StringIO()
    out = None
    try:
        if model is not None:
            if isinstance(model, myokit.Model):
                model = model.code()
            else:
                model = model.strip()
                if model != '' and model[:9] != '[[model]]':
                    f.write('[[model]]\n')
            model = model.strip()
            if model:
                f.write(model)
                f.write('\n\n')

        if protocol is not None:
            if isinstance(protocol, myokit.Protocol):
                protocol = protocol.code()
            else:
                protocol = protocol.strip()
                if protocol != '' and protocol[:12] != '[[protocol]]':
                    f.write('[[protocol]]\n')
            protocol = protocol.strip()
            if protocol:
                f.write(protocol)
                f.write('\n\n')

        if script is not None:
            script = script.strip()
            if script != '' and script[:10] != '[[script]]':
                f.write('[[script]]\n')
            if script:
                f.write(script)
                f.write('\n\n')
    finally:
        if filename:
            f.close()
        else:
            out = f.getvalue()
    return out


def save_model(filename, model):
    """
    Saves a model to a file
    """
    return save(filename, model)


def save_protocol(filename, protocol):
    """
    Saves a protocol to a file
    """
    return save(filename, protocol=protocol)


def save_script(filename, script):
    """
    Saves an embedded script to a file
    """
    return save(filename, script=script)


def save_state(filename, state, model=None):
    """
    Stores a model state to the path ``filename``.

    If no ``model`` is specified ``state`` should be given as a list of
    floating point numbers and will be stored by simply placing each number on
    a new line.

    If a :class:`Model <myokit.Model>` is provided the state can be in any
    format accepted by :meth:`Model.map_to_state() <myokit.Model.map_to_state>`
    and will be stored in the format returned by
    :meth:`Model.format_state() <myokit.Model.format_state>`.
    """
    # Check filename
    filename = os.path.expanduser(filename)

    # Format
    if model is not None:
        state = model.map_to_state(state)
        state = model.format_state(state)
    else:
        state = '\n'.join([myokit.float.str(s) for s in state])

    # Store
    with open(filename, 'w') as f:
        f.write(state)


def save_state_bin(filename, state, precision=myokit.DOUBLE_PRECISION):
    """
    Stores a model state (or any given list of floating point numbers) to the
    path ``filename``, using a binary format.

    The used format is a zip file, containing a single entry: ``state_x_y``,
    where ``x`` is the used data type (``d`` or ``f``) and ``y`` is the number
    of entries. All entries are stored little-endian.
    """
    # Check filename
    filename = os.path.expanduser(filename)

    # Load compression modules
    import zipfile
    try:
        import zlib
        del zlib
    except ImportError:
        raise Exception(
            'This method requires the `zlib` module to be installed.')

    # Data type
    code = 'd' if precision == myokit.DOUBLE_PRECISION else 'f'

    # Create array, ensure it's little-endian
    ar = array.array(code, state)
    if sys.byteorder == 'big':  # pragma: no cover
        ar.byteswap()

    # Store precision and data type in internal filename
    name = 'state_' + code + '_' + str(len(state))
    info = zipfile.ZipInfo(name)
    info.compress_type = zipfile.ZIP_DEFLATED

    # Write to compressed file
    ar = ar.tobytes()
    with zipfile.ZipFile(filename, 'w') as f:
        f.writestr(info, ar)

