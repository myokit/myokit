#
# Contains functions for the import and export of Myokit objects.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
import os
import sys
import traceback
import warnings

# Constants
DIR_FORMATS = os.path.join(myokit.DIR_MYOKIT, 'formats')

# Hidden lists
_IMPORTERS = None
_EXPORTERS = None
_EWRITERS = None


# Classes & methods
class Exporter(object):
    """
    Abstract base class for exporters.
    """
    def __init__(self):
        super(Exporter, self).__init__()

    def post_export_info(self):
        """
        Optional method that returns a string containing information about this
        exporter, to be shown after the export is completed.
        """
        return ''

    def _test_writable_dir(self, path):
        """
        Ensures the given path is writable, or raises a
        :class:`myokit.ExportError` if it can't be used.
        """
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise myokit.ExportError(
                    'Can\'t create output directory. A file exists at the'
                    ' specified location: ' + path)

        elif path != '' and not os.path.isdir(path):
            os.makedirs(path)

    def model(self, path, model):
        """
        Exports a :class:`myokit.Model`.

        The output will be stored in the **file** ``path``. A
        :class:`myokit.ExportError` will be raised if any errors occur.
        """
        raise NotImplementedError

    def runnable(self, path, model, protocol=None, *args):
        """
        Exports a :class:`myokit.Model` and optionally a
        :class:`myokit.Protocol` to something that can be run or compiled.

        The output will be stored in the **directory** ``path``. A
        :class:`myokit.ExportError` will be raised if any errors occur.
        """
        raise NotImplementedError

    def supports_model(self):
        """
        Returns ``True`` if this exporter supports model export.
        """
        return False

    def supports_runnable(self):
        """
        Returns ``True`` if this exporter supports export of a model and
        optional protocol to a runnable piece of code.
        """
        return False


def exporter(name):
    """
    Creates and returns an instance of the exporter specified by ``name``.
    """
    name = str(name)
    if _EXPORTERS is None:  # pragma: no cover
        _scan_for_internal_formats()
    try:
        return _EXPORTERS[name]()
    except KeyError:
        raise KeyError('Exporter not found: ' + name)


def exporters():
    """
    Returns a list of available exporters by name.
    """
    if _EXPORTERS is None:  # pragma: no cover
        _scan_for_internal_formats()
    return sorted(_EXPORTERS.keys())


class ExpressionWriter(object):
    """
    Base class for expression writers, that take myokit expressions as input
    and convert them to text or other formats.
    """
    def __init__(self):
        self._op_map = self._build_op_map()

    def _build_op_map(self):
        """
        Returns a mapping from myokit operators to lambda functions on expr.
        """
        return {
            myokit.Name: self._ex_name,
            myokit.Derivative: self._ex_derivative,
            myokit.PartialDerivative: self._ex_partial_derivative,
            myokit.InitialValue: self._ex_initial_value,
            myokit.Number: self._ex_number,
            myokit.PrefixPlus: self._ex_prefix_plus,
            myokit.PrefixMinus: self._ex_prefix_minus,
            myokit.Plus: self._ex_plus,
            myokit.Minus: self._ex_minus,
            myokit.Multiply: self._ex_multiply,
            myokit.Divide: self._ex_divide,
            myokit.Quotient: self._ex_quotient,
            myokit.Remainder: self._ex_remainder,
            myokit.Power: self._ex_power,
            myokit.Sqrt: self._ex_sqrt,
            myokit.Sin: self._ex_sin,
            myokit.Cos: self._ex_cos,
            myokit.Tan: self._ex_tan,
            myokit.ASin: self._ex_asin,
            myokit.ACos: self._ex_acos,
            myokit.ATan: self._ex_atan,
            myokit.Exp: self._ex_exp,
            myokit.Log: self._ex_log,
            myokit.Log10: self._ex_log10,
            myokit.Floor: self._ex_floor,
            myokit.Ceil: self._ex_ceil,
            myokit.Abs: self._ex_abs,
            myokit.Not: self._ex_not,
            myokit.Equal: self._ex_equal,
            myokit.NotEqual: self._ex_not_equal,
            myokit.More: self._ex_more,
            myokit.Less: self._ex_less,
            myokit.MoreEqual: self._ex_more_equal,
            myokit.LessEqual: self._ex_less_equal,
            myokit.And: self._ex_and,
            myokit.Or: self._ex_or,
            myokit.If: self._ex_if,
            myokit.Piecewise: self._ex_piecewise,
        }

    def eq(self, q):
        """
        Converts an equation to a string
        """
        return self.ex(q.lhs) + ' = ' + self.ex(q.rhs)

    def ex(self, e):
        """
        Converts an Expression to a string.
        """
        t = type(e)
        if t not in self._op_map:   # pragma: no cover
            raise ValueError('Unknown expression type: ' + str(t))
        return self._op_map[t](e)

    def _ex_name(self, e):
        raise NotImplementedError

    def _ex_derivative(self, e):
        raise NotImplementedError

    def _ex_partial_derivative(self, e):
        raise NotImplementedError

    def _ex_initial_value(self, e):
        raise NotImplementedError

    def _ex_number(self, e):
        raise NotImplementedError

    def _ex_prefix_plus(self, e):
        raise NotImplementedError

    def _ex_prefix_minus(self, e):
        raise NotImplementedError

    def _ex_plus(self, e):
        raise NotImplementedError

    def _ex_minus(self, e):
        raise NotImplementedError

    def _ex_multiply(self, e):
        raise NotImplementedError

    def _ex_divide(self, e):
        raise NotImplementedError

    def _ex_quotient(self, e):
        raise NotImplementedError

    def _ex_remainder(self, e):
        raise NotImplementedError

    def _ex_power(self, e):
        raise NotImplementedError

    def _ex_sqrt(self, e):
        raise NotImplementedError

    def _ex_sin(self, e):
        raise NotImplementedError

    def _ex_cos(self, e):
        raise NotImplementedError

    def _ex_tan(self, e):
        raise NotImplementedError

    def _ex_asin(self, e):
        raise NotImplementedError

    def _ex_acos(self, e):
        raise NotImplementedError

    def _ex_atan(self, e):
        raise NotImplementedError

    def _ex_exp(self, e):
        raise NotImplementedError

    def _ex_log(self, e):
        raise NotImplementedError

    def _ex_log10(self, e):
        raise NotImplementedError

    def _ex_floor(self, e):
        raise NotImplementedError

    def _ex_ceil(self, e):
        raise NotImplementedError

    def _ex_abs(self, e):
        raise NotImplementedError

    def _ex_not(self, e):
        raise NotImplementedError

    def _ex_equal(self, e):
        raise NotImplementedError

    def _ex_not_equal(self, e):
        raise NotImplementedError

    def _ex_more(self, e):
        raise NotImplementedError

    def _ex_less(self, e):
        raise NotImplementedError

    def _ex_more_equal(self, e):
        raise NotImplementedError

    def _ex_less_equal(self, e):
        raise NotImplementedError

    def _ex_and(self, e):
        raise NotImplementedError

    def _ex_or(self, e):
        raise NotImplementedError

    def _ex_if(self, e):
        raise NotImplementedError

    def _ex_piecewise(self, e):
        raise NotImplementedError

    def set_lhs_function(self, f):
        """
        Sets a naming function, will be called to get the variable name from a
         ``myokit.LhsExpression`` object.

        The argument ``f`` should be a function that takes an ``LhsExpression``
        as input and returns a string.
        """
        raise NotImplementedError


def ewriter(name):
    """
    Creates and returns an instance of the expression writer specified by
    ``name``.
    """
    name = str(name)
    if _EWRITERS is None:   # pragma: no cover
        _scan_for_internal_formats()
    try:
        return _EWRITERS[name]()
    except KeyError:
        raise KeyError('Expression writer not found: ' + name)


def ewriters():
    """
    Returns a list of available expression writers by name.
    """
    if _EWRITERS is None:   # pragma: no cover
        _scan_for_internal_formats()
    return sorted(_EWRITERS.keys())


class Importer(object):
    """
    Abstract base class for importers.
    """
    def __init__(self):
        super(Importer, self).__init__()

    def component(self, path, model):
        """
        Imports a component from the given ``path`` and adds it to the given
        model.

        The importer may pose restraints on the used model. For example, the
        model may be required to contain a variable labelled
        "membrane_potential". For details, check the documentation of the
        individual importers.

        The created :class:`myokit.Component` is returned. A
        :class:`myokit.ImportError` will be raised if any errors occur.
        """
        raise NotImplementedError

    def model(self, path):
        """
        Imports a model from the given ``path``.

        The created :class:`myokit.Model` is returned. A
        :class:`myokit.ImportError` will be raised if any errors occur.
        """
        raise NotImplementedError

    def protocol(self, path):
        """
        Imports a protocol from the given ``path``.

        The created :class:`myokit.Protocol` is returned. A
        :class:`myokit.ImportError` will be raised if any errors occur.
        """
        raise NotImplementedError

    def supports_component(self):
        """
        Returns a bool indicating if component import is supported.
        """
        return False

    def supports_model(self):
        """
        Returns a bool indicating if model import is supported.
        """
        return False

    def supports_protocol(self):
        """
        Returns a bool indicating if protocol import is supported.
        """
        return False


def importer(name):
    """
    Creates and returns an instance of the importer specified by ``name``.
    """
    name = str(name)
    if _IMPORTERS is None:  # pragma: no cover
        _scan_for_internal_formats()
    try:
        return _IMPORTERS[name]()
    except KeyError:
        raise KeyError('Importer not found: ' + name)


def importers():
    """
    Returns a list of available importers by name.
    """
    if _IMPORTERS is None:  # pragma: no cover
        _scan_for_internal_formats()
    return sorted(_IMPORTERS.keys())


class TemplatedRunnableExporter(Exporter):
    """
    *Abstract class, extends:* :class:`Exporter`

    Abstract base class for exporters that turn a model (and optionally a
    protocol) into a runnable chunk of code.
    """
    def __init__(self):
        super(TemplatedRunnableExporter, self).__init__()

    def runnable(self, path, model, protocol=None, *args):
        """
        Exports a :class:`myokit.Model` and optionally a
        :class:`myokit.Protocol` to something that can be run or compiled.

        The output will be stored in the **directory** ``path``.
        """
        # Get and test path
        path = os.path.abspath(os.path.expanduser(path))
        path = myokit.tools.format_path(path)
        self._test_writable_dir(path)

        # Clone the model, allowing changes to be made during export
        model = model.clone()
        model.validate()

        # Ensure we have a protocol
        if protocol is None:
            protocol = myokit.default_protocol()

        # Build and check template path
        tpl_dir = self._dir(DIR_FORMATS)
        if not os.path.exists(tpl_dir):  # pragma: no cover
            # Cover pragma: If this happens it's a bug in the exporter
            msg = 'Template directory not found: ' + tpl_dir
            raise myokit.ExportError(msg)
        if not os.path.isdir(tpl_dir):  # pragma: no cover
            # Cover pragma: If this happens it's a bug in the exporter
            msg = 'Template path is not a directory:' + tpl_dir
            raise Myokit.ExportError(msg)

        # Render all templates
        tpl_vars = self._vars(model, protocol, *args)
        for tpl_name, out_name in self._dict().items():

            # Create any dirs embedded in output file path
            file_dir = os.path.split(out_name)[0]

            if file_dir:
                file_dir = os.path.join(path, file_dir)
                if os.path.exists(file_dir):
                    if not os.path.isdir(file_dir):
                        msg = 'Failed to create directory at: '
                        msg += myokit.tools.format_path(file_dir)
                        msg += ' A file or link with that name already exists.'
                        raise myokit.ExportError(msg)
                else:   # pragma: no cover
                    try:
                        os.makedirs(file_dir)
                    except IOError as e:
                        msg = 'Failed to create directory at: '
                        msg += myokit.tools.format_path(file_dir)
                        msg += ' IOError:' + str(e)
                        raise myokit.ExportError(msg)

            # Check if output file already exists
            out_name = os.path.join(path, out_name)
            if os.path.exists(out_name):
                if os.path.isdir(out_name):
                    msg = 'Directory exists at ' \
                          + myokit.tools.format_path(out_name)
                    raise myokit.ExportError(msg)

            # Check template file
            tpl_name = os.path.join(tpl_dir, tpl_name)
            if not os.path.exists(tpl_name):    # pragma: no cover
                # Cover pragma: If this happens it's a bug in the exporter
                msg = 'File not found: ' + myokit.tools.format_path(tpl_name)
                raise myokit.ExportError(msg)
            if not os.path.isfile(tpl_name):    # pragma: no cover
                # Cover pragma: If this happens it's a bug in the exporter
                msg = 'Directory found, expecting file at '
                msg += myokit.tools.format_path(tpl_name)
                raise myokit.ExportError(msg)

            # Render
            with open(out_name, 'w') as f:
                p = myokit.pype.TemplateEngine()
                p.set_output_stream(f)
                try:
                    p.process(tpl_name, tpl_vars)
                except Exception as e:      # pragma: no cover
                    warnings.warn(
                        'An error ocurred while processing the template at '
                        + myokit.tools.format_path(tpl_name))
                    warnings.warn(traceback.format_exc())
                    if isinstance(e, myokit.pype.PypeError):
                        # Pype error? Then add any error details
                        d = p.error_details()
                        if d:
                            warnings.warn(d)
                    raise myokit.ExportError(   # pragma: no cover
                        'An internal error ocurred while processing a'
                        ' template.')

    def supports_runnable(self):
        """
        Returns ``True`` if this exporter supports export of a model and
        optional protocol to a runnable piece of code.
        """
        return True

    def _dict(self):
        """
        Returns a dict (filename : template_file_name) containing all the
        templates used by this exporter.

        *This should be implemented by each subclass.*
        """
        raise NotImplementedError

    def _dir(self, formats_dir):
        """
        Returns the path to this exporter's data files (as a string).

        *This should be implemented by each subclass. The root directory all
        format extensions are stored in in passed in as ``formats_dir``.*
        """
        raise NotImplementedError

    def _vars(self, model, protocol):
        """
        Returns a dict containing all variables the templates will need.

        Will be called with the arguments `model` and `protocol`, followed by
        any extra arguments passed to :meth:`runnable`.

        *This should be implemented by each subclass.*
        """
        raise NotImplementedError


def _scan_for_internal_formats():
    """
    Scans for importers, exporters and expression writers.
    """
    global _IMPORTERS, _EXPORTERS, _EWRITERS
    if _IMPORTERS is None:
        _IMPORTERS = {}
    if _EXPORTERS is None:
        _EXPORTERS = {}
    if _EWRITERS is None:
        _EWRITERS = {}
    for fname in os.listdir(DIR_FORMATS):
        d = os.path.join(DIR_FORMATS, fname)
        if not os.path.isdir(d):
            continue

        # Only check modules
        f = os.path.join(d, '__init__.py')
        if not os.path.isfile(f):
            continue     # pragma: no cover

        # Dynamically load module
        name = 'myokit.formats.' + fname
        __import__(name)
        m = sys.modules[name]

        # Add importers, exporters and expression writers to global list
        try:
            x = m.importers()
        except AttributeError:
            x = {}
        for k, v in x.items():
            if k in _IMPORTERS:     # pragma: no cover
                raise Exception('Duplicate importer name: "' + str(k) + '".')
            _IMPORTERS[k] = v

        try:
            x = m.exporters()
        except AttributeError:
            x = {}
        for k, v in x.items():
            if k in _EXPORTERS:     # pragma: no cover
                raise Exception('Duplicate exporter name: "' + str(k) + '".')
            _EXPORTERS[k] = v

        try:
            x = m.ewriters()
        except AttributeError:
            x = {}
        for k, v in x.items():
            if k in _EWRITERS:     # pragma: no cover
                raise Exception(
                    'Duplicate expression writer name: "' + str(k) + '".')
            _EWRITERS[k] = v


def register_external_importer(name, importer_class):
    """
    Registers an external :class:`Importer` for use with Myokit.

    Arguments:

    ``name``
        A short descriptive string name.
    ``importer_class``
        The class to register (must be a :class:`myokit.Importer`).
        Importers can be unregistered by passing in ``None``.

    """
    if importer_class is None:
        if _IMPORTERS is not None and name in _IMPORTERS:
            del _IMPORTERS[name]
    else:
        if _IMPORTERS is None:  # pragma: no cover
            _scan_for_internal_formats()
        _IMPORTERS[name] = importer_class


def register_external_exporter(name, exporter_class):
    """
    Registers an external :class:`Exporter` for use with Myokit.

    Arguments:

    ``name``
        A short descriptive string name.
    ``exporter_class``
        The class to register (must be a :class:`myokit.Exporter`).
        Exporters can be unregistered by passing in ``None``.

    """
    if exporter_class is None:
        if _EXPORTERS is not None and name in _EXPORTERS:
            del _EXPORTERS[name]
    else:
        if _EXPORTERS is None:  # pragma: no cover
            _scan_for_internal_formats()
        _EXPORTERS[name] = exporter_class


def register_external_ewriter(name, ewriter_class):
    """
    Registers an external :class:`ExpressionWriter` for use with Myokit.

    Arguments:

    ``name``
        A short descriptive string name.
    ``ewriter_class``
        The class to register (must be a :class:`myokit.ExpressionWriter`).
        Expression writers can be unregistered by passing in ``None``.

    """
    if ewriter_class is None:
        if _EWRITERS is not None and name in _EWRITERS:
            del _EWRITERS[name]
    else:
        if _EWRITERS is None:  # pragma: no cover
            _scan_for_internal_formats()
        _EWRITERS[name] = ewriter_class

