#
# Myokit auxillary functions: This module can be used to gather any
# functions that are important enough to warrant inclusion in the main
# myokit module but don't belong to any specific hidden module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit

import sys

# Globally shared numpy expression writer
_numpywriter_ = None

# Globally shared python expression writer
_pywriter_ = None


class Benchmarker(myokit.tools.Benchmarker):
    """Deprecated alias of :class:`myokit.tools.Benchmarker`."""

    def __init__(self):
        # Deprecated since 2021-03-24
        import warnings
        warnings.warn(
            'The class `myokit.Benchmarker` is deprecated.'
            ' Please use `myokit.tools.Benchmarker` instead.')
        super(Benchmarker, self).__init__()


def date():
    """
    Returns the current date and time, in the format used throughout Myokit.
    """
    import time
    return time.strftime(myokit.DATE_FORMAT)


def default_protocol(model=None):
    """
    Returns a default protocol to use when no embedded one is available.
    """
    start = 100
    duration = 0.5
    period = 1000

    # Try to get the time units
    time_units = None
    if model is not None:
        if model.time() is not None:
            time_units = model.time().unit()

    # Adapt protocol if necessary
    default_units = myokit.units.ms
    try:
        start = myokit.Unit.convert(start, default_units, time_units)
        duration = myokit.Unit.convert(duration, default_units, time_units)
        period = myokit.Unit.convert(period, default_units, time_units)
    except myokit.IncompatibleUnitError:
        pass

    # Create and return
    p = myokit.Protocol()
    p.schedule(1, start, duration, period, 0)
    return p


def default_script(model=None):
    """
    Returns a default script to use when no embedded script is available.
    """
    # Defaults
    vm = 'next(m.states()).qname()'
    duration = 1000

    # Try to improve on defaults using model
    if model is not None:
        # Guess membrane potential
        import myokit.lib.guess
        v = myokit.lib.guess.membrane_potential(model)
        if v is not None:
            vm = "'" + v.qname() + "'"

        # Get duration in good units
        default_unit = myokit.units.ms
        time = model.time()
        if time is not None:
            if time.unit() != default_unit:
                try:
                    duration = myokit.Unit.convert(
                        1000, default_unit, time.unit())
                except myokit.IncompatibleUnitError:
                    pass

    # Create and return script
    return '\n'.join((  # pragma: no cover
        "[[script]]",
        "import matplotlib.pyplot as plt",
        "import myokit",
        "",
        "# Get model and protocol, create simulation",
        "m = get_model()",
        "p = get_protocol()",
        "s = myokit.Simulation(m, p)",
        "",
        "# Run simulation",
        "d = s.run(" + str(duration) + ")",
        "",
        "# Display the results",
        "var = " + vm,
        "plt.figure()",
        "plt.plot(d.time(), d[var])",
        "plt.title(var)",
        "plt.show()",
    ))


def format_float_dict(d):
    """
    Takes a dictionary of ``string : float`` mappings and returns a single
    multi-line string, where each line is of the form ``key = value``, where
    key is padded with spaces to make the equals signs align.

    This method is deprecated and will be removed in future versions of Myokit.
    """
    # Deprecated since 2021-03-24
    import warnings
    warnings.warn(
        'The method `myokit.format_float_dict` is deprecated.'
        ' It will be removed in future versions of Myokit.')

    keys = [str(k) for k in d.keys()]
    keys.sort()
    n = max([len(k) for k in keys])
    return '\n'.join([
        k + ' ' * (n - len(k)) + ' = ' + myokit.float.str(d[k]) for k in keys])


def format_path(path, root='.'):
    """Deprecated alias of :class:`myokit.tools.format_path`."""
    # Deprecated since 2021-03-24
    import warnings
    warnings.warn(
        'The method `myokit.format_path` is deprecated.'
        ' Please use `myokit.tools.format_path` instead.')
    return myokit.tools.format_path(path, root)


class ModelComparison(object):
    """
    Compares two models.

    The resulting diff text can be iterated over::

        for line in ModelComparison(m1, m2):
            print(line)

    Differences can be printed directly to ``stdout`` by setting ``live=True``.
    """
    def __init__(self, model1, model2, live=False):
        # Difference list
        self._diff = []

        # Live reporting
        self._live = True if live else False

        # Compare models
        if live:
            print('Comparing:')
            print('  [1] ' + model1.name())
            print('  [2] ' + model2.name())

        # -> Model meta data
        self._meta(model1, model2)

        # -> User functions
        self._userfunc(model1, model2)

        # -> Time variable
        self._time(model1, model2)

        # -> State vector
        self._state(model1, model2)

        # -> Components & Variables
        self._components(model1, model2)

        # Final report
        if live:
            print('Done')
            print('  ' + str(len(self._diff)) + ' differences found')

    def _components(self, m1, m2):
        """
        Compares two models' components.
        """
        seen = set()
        for c1 in m1.components(sort=True):
            seen.add(c1.qname())
            try:
                c2 = m2[c1.qname()]
            except KeyError:
                self._write('[2] Missing Component <' + c1.qname() + '>')
                continue
            self._comp(c1, c2)
        for c2 in m2.components(sort=True):
            if c2.qname() not in seen:
                self._write('[1] Missing Component <' + c2.qname() + '>')

    def _comp(self, c1, c2):
        """
        Compares the contents of two components with the same name.
        """
        assert c1.qname() == c2.qname()
        # Meta information
        self._meta(c1, c2)
        # Test variables
        seen = set()
        for v1 in c1.variables(deep=True):
            name = v1.qname()
            seen.add(name)
            try:
                v2 = c2.model().get(name)
            except KeyError:
                self._write('[2] Missing Variable <' + name + '>')
                continue
            self._var(v1, v2)
        for v2 in c2.variables(deep=True):
            name = v2.qname()
            if name not in seen:
                self._write('[1] Missing Variable <' + name + '>')

    def equal(self):
        """
        Returns ``True`` if the two models were equal.
        """
        return len(self._diff) == 0

    def __iter__(self):
        """
        Iterate over the found differences.
        """
        return iter(self._diff)

    def __len__(self):
        """
        Returns the length of the difference array.
        """
        return len(self._diff)

    def _meta(self, x1, x2):
        """
        Compares two objects' meta properties.
        """
        assert type(x1) == type(x2)
        if isinstance(x1, myokit.Model):
            name = ' in model'
        else:
            name = ' in <' + x1.qname() + '>'
        seen = set()
        for key, value in x1.meta.items():
            seen.add(key)
            try:
                if value != x2.meta[key]:
                    self._write(
                        '[x] Mismatched Meta property' + name + ': "'
                        + str(key) + '"')
            except KeyError:
                self._write(
                    '[2] Missing Meta property' + name + ': "' + str(key)
                    + '"')
        for key, value in x2.meta.items():
            if key not in seen:
                self._write(
                    '[1] Missing Meta property' + name + ': "' + str(key)
                    + '"')

    def _state(self, m1, m2):
        """
        Compares two models' states.
        """
        s1 = iter([v.qname() for v in m1.states()])
        s2 = iter([v.qname() for v in m2.states()])
        c1 = m1.state()
        c2 = m2.state()
        for k, v1 in enumerate(s1):
            try:
                v2 = next(s2)
            except StopIteration:
                self._write('[2] Missing state at position ' + str(k))
                continue
            if v1 != v2:
                self._write(
                    '[x] Mismatched State at position ' + str(k) + ': [1]<'
                    + v1 + '> [2]<' + v2 + '>')
                continue
            if c1[k] != c2[k]:
                self._write('[x] Mismatched Initial value for <' + v1 + '>')
        n = m2.count_states()
        for k, v2 in enumerate(s2):
            self._write('[1] Missing state at position ' + str(n + k))

    def text(self):
        """
        Returns the full difference text.
        """
        return '\n'.join(self._diff)

    def _time(self, m1, m2):
        """
        Compares two models' time variables.
        """
        t1 = m1.time()
        t2 = m2.time()
        if t1 is None:
            if t2 is not None:
                self._write('[1] Missing Time variable <' + t2.qname() + '>')
                return
        elif t2 is None:
            self._write('[2] Missing Time variable <' + t1.qname() + '>')
            return
        if t1.qname() != t2.qname():
            self._write(
                '[x] Mismatched Time variable: [1]<' + t1.qname() + '> [2]<'
                + t2.qname() + '>')

    def _userfunc(self, m1, m2):
        """
        Compares two models' user functions.
        """
        u1 = m1.user_functions()
        u2 = m2.user_functions()
        seen = set()
        for name, func in u1.items():
            seen.add(name)
            try:
                if func != u2[name]:
                    self._write('[x] Mismatched User function <' + name + '>')
            except KeyError:
                self._write('[2] Missing User function <' + name + '>')
        for name, func in u2.items():
            if name not in seen:
                self._write('[1] Missing User function <' + name + '>.')

    def _var(self, v1, v2):
        """
        Compares two variables with the same name.
        """
        name = v1.qname()
        assert v2.qname() == name
        # Left-hand side expression
        c1, c2 = v1.lhs().code(), v2.lhs().code()
        if c1 != c2:
            self._write('[x] Mismatched LHS <' + name + '>')
        # Right-hand side expression
        c1, c2 = v1.rhs().code(), v2.rhs().code()
        if c1 != c2:
            self._write('[x] Mismatched RHS <' + name + '>')
        # Units
        if v1.unit() != v2.unit():
            self._write('[x] Mismatched unit <' + name + '>')
        # Meta
        self._meta(v1, v2)
        # Don't test nested variables, this is done component wise

    def _write(self, text):
        """
        Writes a line to the difference array.
        """
        if self._live:
            print(text)
        self._diff.append(text)


def numpy_writer():
    """
    Returns a globally shared numpy expression writer.

    LhsExpressions are converted as follows:

    1. Derivatives are indicated as "_d_" + var.uname()
    2. Other names are indicated as var.uname()

    This convention ensures a unique mapping of a model's lhs expressions to
    acceptable python variable names.
    """
    global _numpywriter_
    if _numpywriter_ is None:
        from .formats.python import NumPyExpressionWriter
        _numpywriter_ = NumPyExpressionWriter()

        def name(x):
            u = x.var()
            u = u.uname() if isinstance(u, myokit.ModelPart) else str(u)
            if u is None:
                u = x.var().qname().replace('.', '_')
            return '_d_' + u if x.is_derivative() else u

        _numpywriter_.set_lhs_function(name)

    return _numpywriter_


def python_writer():
    """
    Returns a globally shared python expression writer.

    LhsExpressions are converted as follows:

    1. Derivatives are indicated as "_d_" + var.uname()
    2. Other names are indicated as var.uname()

    This convention ensures a unique mapping of a model's lhs expressions to
    acceptable python variable names.
    """
    global _pywriter_
    if _pywriter_ is None:
        from .formats.python import PythonExpressionWriter
        _pywriter_ = PythonExpressionWriter()

        def name(x):
            u = x.var()
            u = u.uname() if isinstance(u, myokit.ModelPart) else str(u)
            if u is None:
                u = x.var().qname().replace('.', '_')
            return '_d_' + u if x.is_derivative() else u

        _pywriter_.set_lhs_function(name)

    return _pywriter_


def run(model, protocol, script, stdout=None, stderr=None, progress=None):
    """
    Runs a python ``script`` using the given ``model`` and ``protocol``.

    The following functions are provided to the script:

    ``get_model()``
        This returns the model passed to ``run()``. When using the GUI, this
        returns the model currently loaded into the editor.
    ``get_protocol()``
        This returns the protocol passed to ``run()``. When using the GUI, this
        returns the protocol currently loaded into the editor.

    Ordinary and error output can be re-routed by providing objects with a
    file-like interface (``x.write(text)``, ``x.flush()``) as ``stdout`` and
    ``stderr`` respectively. Note that output is only re-routed on the python
    level so that any output generated by C-code will still go to the main
    process's output and error streams.

    An object implementing the ``ProgressReporter`` interface can be passed in.
    This will be made available globally to any simulations (or other methods)
    that provide progress update information.
    """
    # Trim "[[script]]" from script
    script = script.splitlines()
    if script and script[0].strip() == '[[script]]':
        script = script[1:]
    script = '\n'.join(script)

    # Add an empty line at the start of the script. This will make the line
    # numbers reported in any error message correspond to those in the GUI.
    # In other words, a script section
    #
    #   1 [[script]]
    #   2 import myokit
    #   3 x = 1/0
    #
    # will raise an exception on line 3.
    #
    script = '\n' + script

    # Class to run scripts
    class Runner(object):
        def __init__(self, model, protocol, script, stdout, stderr, progress):
            super(Runner, self).__init__()
            self.model = model
            self.protocol = protocol
            self.script = script
            self.stdout = stdout
            self.stderr = stderr
            self.progress = progress
            self.exc_info = None

        def run(self):

            # Create magic functions
            def get_model():
                return self.model

            def get_protocol():
                return self.protocol

            # Re-route standard outputs, execute code
            oldstdout = oldstderr = None
            oldprogress = myokit._Simulation_progress
            myokit._Simulation_progress = self.progress
            try:
                if self.stdout is not None:
                    oldstdout = sys.stdout
                    sys.stdout = self.stdout
                if self.stderr is not None:
                    oldstderr = sys.stderr
                    sys.stderr = self.stderr
                environment = {
                    'get_model': get_model,
                    'get_protocol': get_protocol,
                }
                myokit._exec(self.script, environment)
            finally:
                if oldstdout is not None:
                    sys.stdout = oldstdout
                if oldstderr is not None:
                    sys.stderr = oldstderr
                myokit._Simulation_progress = oldprogress

    r = Runner(model, protocol, script, stdout, stderr, progress)
    r.run()

    # Free some space
    del r
    import gc
    gc.collect()


def step(model, initial=None, reference=None, ignore_errors=False):
    """
    Evaluates the state derivatives in a model and compares the results with a
    list of reference values, if given.

    The ``model`` should be given as a valid :class:`myokit.Model`. The state
    values to start from can be given as ``initial``, which should be any item
    that can be converted to a valid state using ``model.map_to_state``.

    The values can be compared to reference output given as a list
    ``reference``. Alternatively, if ``reference`` is a model the two models'
    outputs will be compared.

    By default, the evaluation routine checks for numerical errors
    (divide-by-zeros, invalid operations and overflows). To run an evaluation
    without error checking, set ``ignore_errors=True``.

    Returns a string indicating the results.
    """
    # Get initial state
    if initial is None:
        initial = model.state()

    # Get evaluation at initial state
    values = model.evaluate_derivatives(
        state=initial, ignore_errors=ignore_errors)

    # Log settings
    fmat = myokit.SFDOUBLE
    line_width = 79

    # Get max variable name width (at least 4, for 'Name' header)
    w = max(4, max([len(v.qname()) for v in model.states()]))

    # Create log header
    log = []
    log.append('Evaluating state vector derivatives...')
    log.append('-' * line_width)
    log.append(('{:<' + str(w) + '}  {:<24}  {:<24}').format(
        'Name', 'Initial value', 'Derivative at t=0'))
    log.append('-' * line_width)

    # Format for states
    f = '{: <' + str(w) + '}  ' + fmat + '  ' + fmat

    if not reference:
        # Default output: intial value and derivative
        for r, v in enumerate(model.states()):
            log.append(f.format(v.qname(), initial[r], values[r]))
    else:
        # Comparing output

        # Reference should be a state evaluation, or a model
        if isinstance(reference, myokit.Model):
            reference = reference.evaluate_derivatives(
                state=initial, ignore_errors=ignore_errors)

        h = ' ' * (w + 28)
        i = h + ' ' * 20
        g = h + fmat
        errors = 0
        warnings = 0

        for r, v in enumerate(model.states()):
            x = values[r]
            y = reference[r]
            log.append(f.format(v.qname(), initial[r], x))
            xx = fmat.format(x)
            yy = fmat.format(y)
            line = g.format(y)

            # Sign error
            if xx[0] != yy[0]:

                # Ignore if zero
                if (myokit.float.eq(x, 0) and myokit.float.eq(y, 0)):
                    log.append(line)
                    log.append('')
                else:
                    errors += 1
                    log.append(line + ' sign')
                    log.append(h + '^' * 24)

            # Different exponent, huge error
            elif xx[-4:] != yy[-4:]:
                errors += 1
                log.append(line + ' exponent')
                log.append(i + '^^^^')

            # Large error, small error, or no error
            else:
                mark_error = False
                threshold = 13
                if xx[:threshold] != yy[:threshold]:
                    # "Large" error
                    errors += 1
                    line += ' X'
                    mark_error = True
                elif xx != yy:
                    # "Small" error, or numerical error
                    rel_err = abs(x - y) / max(abs(x), abs(y))
                    n_eps = rel_err / sys.float_info.epsilon
                    if n_eps > 1:
                        line += ' ~ ' + str(round(n_eps, 1)) + ' eps'
                    else:
                        line += ' <= 1 eps'
                    if n_eps > 1:
                        warnings += 1
                        mark_error = True
                log.append(line)

                if mark_error:
                    line2 = h
                    pos = 0
                    n = len(xx)
                    while pos < n and xx[pos] == yy[pos]:
                        line2 += ' '
                        pos += 1
                    for pos in range(pos, n):
                        line2 += '^'
                    log.append(line2)
                else:
                    log.append('')

        # Show large mismatches between model and reference
        if errors > 0:
            log.append(
                'Found (' + str(errors) + ') large mismatches between output'
                ' and reference values.')
        else:
            log.append('Model check completed without errors.')

        # Show small mismatches between model and reference
        if warnings > 0:
            log.append('Found (' + str(warnings) + ') small mismatches.')

    # Finalise and return
    log.append('-' * line_width)
    return '\n'.join(log)


def strfloat(number, full=False, precision=myokit.DOUBLE_PRECISION):
    """Deprecated alias of :class:`myokit.float.str`."""
    # Deprecated since 2021-03-24
    import warnings
    warnings.warn(
        'The method `myokit.strfloat` is deprecated.'
        ' Please use `myokit.float.str` instead.')
    return myokit.float.str(number, full, precision)


def time():
    """
    Returns the current time, in the format used throughout Myokit.
    """
    import time as t
    return t.strftime(myokit.TIME_FORMAT)


def version(raw=False):
    """
    Returns the current Myokit version.

    By default, a formatted multi-line string is returned. To get a simpler
    one-line string set the optional argument ``raw=True``.

    The same version info can be accessed using ``myokit.__version__``.
    Unformatted info is available in ``myokit.__version_tuple__``, which
    contains the major, minor, and revision number respectively, all as
    ``int`` objects. For development versions of Myokit, it may contain a 4th
    element ``"dev"``.
    """
    if raw:
        return myokit.__version__
    else:
        t1 = ' Myokit ' + myokit.__version__ + ' '
        t2 = '_' * len(t1)
        t1 += '|/\\'
        t2 += '|  |' + '_' * 5
        return '\n' + t1 + '\n' + t2

