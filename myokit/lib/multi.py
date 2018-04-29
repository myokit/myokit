#
# Tools for running experiments on multiple models.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
import os


def iterdir(path, guarantee_model_names=True):
    """
    Iterates over a directory yielding tuples ``(model, protocol)`` where
    ``model`` is a :class:`myokit.Model` and ``protocol`` is a
    :class:`myokit.Protocol`.

    Depending on the contents of the found files, some entries might not have a
    protocol. Files without a model are skipped.

    The results will be yielded ordered by filename.
    The method does not descend into child directories.

    If ``guarantee_model_names`` is ``True`` (default), models that do not
    specify a ``name`` meta-attribute will be given their filename as name.
    This ensures every model read by this method has a name meta-property.
    """
    # Fix path
    path = os.path.expanduser(os.path.abspath(path))

    if not os.path.isdir(path):
        raise ValueError('Given path is not a directory.')

    # Scan files
    for fname in sorted(os.listdir(path)):
        fpath = os.path.join(path, fname)

        # Check if it's a model file
        if not os.path.isfile(fpath):
            continue
        base, ext = os.path.splitext(fname)
        if ext != '.mmt':
            continue

        # Read model & protocol
        model, protocol, x = myokit.load(fpath)

        # Skip files without model
        if model is None:
            continue

        # Set name attribute
        if guarantee_model_names:
            if not model.name():
                model.meta['name'] = base

        # Yield
        yield model, protocol


def scandir(path):
    """
    Scans a directory using :meth:`iterdir` and returns a list of
    :class:`myokit.Model` objects and a list of :class:`myokit.Protocol`
    objects. The models (and corresponding protocols) will be ordered by model
    name.
    """
    names = []
    ms = {}
    ps = {}
    for model, protocol in iterdir(path):
        name = model.name()
        names.append(name)
        ms[name] = model
        ps[name] = protocol
    models = []
    protocols = []
    for name in sorted(names):
        models.append(ms[name])
        protocols.append(ps[name])
    return models, protocols


def time(model):
    """
    Returns the time variable from the given :class:`myokit.Model` `model`.

    The method will raise a :class:`myokit.IncompatibleModelError` if no time
    variable is found.
    """
    time = model.time()
    if time is None:
        raise myokit.IncompatibleModelError(
            model.name(), 'No time variable found.')
    return time


def label(model, label):
    """
    Returns the variable labelled `label` from the given :class:`myokit.Model`
    `model`.

    The method will raise a :class:`myokit.IncompatibleModelError` if no such
    variable is found.
    """
    var = model.label(label)
    if var is None:
        raise myokit.IncompatibleModelError(
            model.name(),
            'No variable found with label "' + str(label) + '".')
    return var


def binding(model, binding):
    """
    Returns the variable bound to `binding` from the given
    :class:`myokit.Model` `model`.

    The method will raise a :class:`myokit.IncompatibleModelError` if no such
    variable is found.
    """
    var = model.binding(binding)
    if var is None:
        raise myokit.IncompatibleModelError(
            model.name(),
            'No variable found with binding "' + str(binding) + '".')
    return var


def unit(variable, unit):
    """
    Checks if the given variable's unit can be converted into units `unit` and,
    if so, returns the appropriate conversion factor. If not, a
    :class:`myokit.IncompatibleModelError` is raised.

    Example::

        >>> import myokit
        >>> import myokit.lib.multi as multi
        >>> m,p,x = myokit.load('example')
        >>> print(multi.unit(m.label('membrane_potential'), myokit.units.V))
        0.001

    (Because a millivolt can be converted to a volt by multiplying by 0.001)

    """
    try:
        return myokit.Unit.convert(1, variable.unit(), unit)
    except myokit.IncompatibleUnitError:
        raise myokit.IncompatibleModelError(
            variable.model().name(),
            'Incompatible units: ' + str(variable.unit()) + ' and '
            + str(unit) + '.')

