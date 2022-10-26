#
# Defines the python classes that represent a Myokit model.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from collections import OrderedDict
import math
import re
import myokit

# StringIO in Python 2 and 3
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str

TAB = ' ' * 4
NAME = re.compile(r'^[a-zA-Z]\w*$')
META = re.compile(r'^[a-zA-Z]\w*(:[a-zA-Z]\w*)*$')


def check_name(name):
    """
    Tests if the given name is a valid myokit name and raises a
    :class:`myokit.InvalidNameError` if it isn't.
    """
    # Note: Names are stored as str (so unicode in Python3)
    # But the regex restriction means their format is compatible with ascii.
    # Check str compatibility
    name = str(name)

    # Check name syntax
    if NAME.match(name) is None:
        raise myokit.InvalidNameError(
            'The name <' + str(name) + '> is  invalid. The first character of'
            ' a name should be a letter from the range [a-zA-Z]. Any'
            ' subsequent characters can be taken from the set [a-zA-Z0-9_].')

    # Check for keywords
    if name in myokit.KEYWORDS:
        raise myokit.InvalidNameError(
            'The name <' + str(name) + '> is a reserved keyword.')

    return name


class MetaDataContainer(dict):
    """
    Dictionary that stores meta-data.
    """

    def __getitem__(self, key):
        # Check key
        if META.match(key) is None:
            raise myokit.InvalidMetaDataNameError(
                'The key <' + str(key) + '>'
                ' is not a valid meta-data property identifier.')
        return super(MetaDataContainer, self).__getitem__(key)

    def __setitem__(self, key, item):
        # Check item
        item = str(item)
        # Check key
        if META.match(key) is None:
            raise myokit.InvalidMetaDataNameError(
                'The key <' + str(key) + '>'
                ' is not a valid meta-data property identifier.')
        super(MetaDataContainer, self).__setitem__(key, item)


class ObjectWithMeta(object):
    """
    Base class for objects with meta data.

    Meta-data properties are all stored in a dict and should be string:string
    mappings.
    """

    def __init__(self):
        super(ObjectWithMeta, self).__init__()
        self.meta = MetaDataContainer()

    def _clone_metadata(self, clone):
        """
        Clones this object's metadata into ``clone``.
        """
        for k, v in self.meta.items():
            clone.meta[str(k)] = str(v)

    def _code_meta(self, b, tabs=0, ignore=None):
        """
        Internal method to format meta data as part of the code() operation.
        Can be used by all subclasses to uniformly format their meta data.
        A list of meta property keys to omit (ignore) can be added.
        """
        if not ignore:
            ignore = []
        for k, v in sorted(self.meta.items()):
            if k in ignore:
                continue
            v = str(v)
            key = TAB * tabs + k.strip() + ': '
            eol = '\n'
            if ('\n' in v) or ('\r' in v) or (v.strip() == ''):
                v.replace('\r\n', '\n')
                v.replace('\r', '\n')
                b.write(key + '"""\n')
                pre = TAB * (1 + tabs)
                for line in v.split(eol):
                    b.write(pre + line + eol)
                b.write(pre + '"""\n')
            else:
                b.write(key + v + eol)


class ModelPart(ObjectWithMeta):
    """
    Base class for model parts.
    """

    def __init__(self, parent, name):
        """
        Creates a new ModelPart

        The given parent should be a ModelPart or None. The name should be
        unique within the set of children for the given parent.
        """
        super(ModelPart, self).__init__()
        self._parent = parent   # This object's parent
        self._model = None      # The model this object belongs to
        self._name = str(name)  # Local name
        self._uname = None      # Globally unique name
        self._token = None      # Parser token for errors, not always set

    def _clone_modelpart_data(self, clone):
        """
        Clones this ModelPart's data into ``clone``.
        """
        clone._uname = str(self._uname)
        self._clone_metadata(clone)

    def code(self):
        """
        Returns this object in ``mmt`` syntax.
        """
        b = StringIO()
        self._code(b, 0)
        return b.getvalue()

    def _code(self, b, t):
        """
        Internal version of _code(), to be implemented by all subclasses.

        The argument ``t`` specifies the number of tabs to indent the code
        with. The argument ``b`` is a cStringIO buffer.
        """
        raise NotImplementedError

    def _delete(self):
        """
        Tells this object it's being deleted. Removes links to parent and/or
        model.
        """
        self._parent = None
        self._model = None

    def has_ancestor(self, obj):
        """
        Returns ``True`` if the given object ``obj`` is an ancestor of this
        :class:`ModelPart`.
        """
        par = self._parent
        try:
            while par is not None:
                if par == obj:
                    return True
                par = par._parent
        except AttributeError:
            return False

    def is_ancestor(self, obj):
        """
        Returns ``True`` if this object is an ancestor of the given
        :class:`ModelPart`` ``object``.
        """
        return obj.has_ancestor(self)

    def model(self):
        """
        Returns the :class:`myokit.Model` this object belongs to (if set).
        """
        if self._model is None:
            self._model = self.parent(Model)
        return self._model

    def name(self):
        """
        Returns this object's name.
        """
        return self._name

    def parent(self, kind=None):
        """
        Returns this object's parent.

        If the optional variable ``kind`` is set, the method will scan until an
        instance of the requested type is found.
        """
        if kind is None:
            return self._parent
        parent = self._parent
        while parent is not None and not isinstance(parent, kind):
            parent = parent._parent
        return parent

    def qname(self, hide=None):
        """
        Returns this object's fully qualified name. That is, an object named
        ``y`` with a parent named ``x`` will return the string ``x.y``. If
        ``y`` has a child ``z`` its qname will be ``x.y.z``.

        If the optional argument ``hide`` is set to this object's parent the
        parent qualifier will be omitted.
        """
        if self._parent is None or self._parent == hide:
            return self._name
        return self._parent.qname(hide) + '.' + self._name

    def __repr__(self):
        return '<' + str(type(self)) + '(' + self.qname() + ')>'

    def __str__(self):
        return self.qname()

    def uname(self):
        """
        Returns a globally unique name for this object.
        """
        return self._uname


class VarProvider(object):
    """
    *Abstract class*

    This class provides an iterator over variables and equations for any object
    that can provide access to an iterator over its variables.
    """

    def _create_variable_stream(self, deep, sort):
        """
        Returns a stream over this object's variables.

        When the argument ``deep`` is set to ``True``, the stream should
        include any nested variables as well. (Only in contexts where this
        makes sense. Otherwise, ``deep`` can be ignored.)

        When the argument ``sort`` is set to ``True``, the stream should be
        returned in a consistent order.
        """
        raise NotImplementedError

    def count_equations(
            self, const=None, inter=None, state=None, bound=None, deep=False):
        """
        Returns the number of equations matching the given criteria. See
        :meth:`equations` for an explanation of the arguments.
        """
        return len(list(self.equations(const, inter, state, bound, deep)))

    def count_variables(
            self, const=None, inter=None, state=None, bound=None, deep=False):
        """
        Returns the number of variables matching the given criteria. See
        :meth:`variables` for an explanation of the arguments.
        """
        return len(list(self.variables(const, inter, state, bound, deep)))

    def has_equations(
            self, const=None, inter=None, state=None, bound=None, deep=False):
        """
        Returns True if there are any equations that can be returned by calling
        :meth:``equations`` with the same arguments.
        """
        for x in self.equations(const, inter, state, bound, deep):
            return True
        return False

    def has_variable(self, name):
        """
        Returns True if the given name corresponds to a variable in this
        object. Accepts both single names ``x`` and qualified names ``x.y`` as
        input.

        This function performs the same search as ``variable``, so in most
        cases it will be more efficient to call ``variable()`` in a
        try-catch block rather than checking for existence explicitly.
        """
        try:
            self.var(name)
        except KeyError:
            return False
        return True

    def has_variables(
            self, const=None, inter=None, state=None, bound=None, deep=False):
        """
        Returns True if there are any variables that can be returned by calling
        :meth:``variables`` with the same arguments.
        """
        for x in self.variables(const, inter, state, bound, deep):
            return True
        return False

    def equations(
            self, const=None, inter=None, state=None, bound=None, deep=False):
        """
        Creates and returns a filtered iterator over the equations of this
        object's variables.

        The returned values can be filtered using the following arguments:

        ``const=True|False|None``
            Set to ``True`` to return only constants' equations. ``False`` to
            exclude all constants and any other value to ignore this check.

            For a definition of "constant variable" see
            :meth:`variables`.

        ``inter=True|False|None``
            Set to ``True`` to return only intermediary variables' equations,
            ``False`` to exclude all intermediary variables and any other value
            to ignore this check.

            For a definition of "intermediary variable" see
            :meth:`variables`.

        ``state=True|False|None``
            Set to ``True`` to return only state variables' equations,
            ``False`` to exclude all state variables and any other value to
            ignore this check.

        ``bound=True|False|None``
            Set to ``True`` to return only bound variables' equations,
            ``False`` to exclude all bound variables and any other value to
            ignore this check.

        ``deep=True|False`` (by default it's ``False``)
             Set to ``True`` to include the equations of nested variables
             meeting all other criteria.
        """
        def viter(stream):
            for x in stream:
                yield x.eq()
        return viter(self.variables(const, inter, state, bound, deep))

    def _resolve(self, name):
        """
        Resolves a local variable name to a variable. Raises an
        :class:`UnresolvedReferenceError` if the name doesn't correspond to any
        variable accessible from this :class:`VarProvider's <VarProvider>`
        scope.
        """
        raise NotImplementedError

    def variables(
            self, const=None, inter=None, state=None, bound=None, deep=False,
            sort=False):
        """
        Creates and returns a filtered iterator over the contained variables.

        The returned values can be filtered using the following arguments:

        ``const=True|False|None``
            Constants are defined as variables that do not depend on state
            variables or derivatives. In other words, any variable whose value
            can be determined before starting an ODE solving routine.

            Set to ``True`` to return only constants, ``False`` to exclude all
            constants and any other value to ignore this check.

        ``inter=True|False|None``
            Intermediary variables are those variables that are not constant
            but are not part of the state. In other words, intermediary
            variables are the variables that need to be calculated at every
            step of an ODE solving routine before calculating the ODE
            derivatives and updating the state.

            Set to ``True`` to return only intermediary variables, ``False`` to
            exclude all intermediary variables and any other value to ignore
            this check.

        ``state=True|False|None``
            Set to True to return only state variables, False to exclude all
            state variables and any other value to ignore this check.

        ``bound=True|False|None``
            Set to True to return only variables bound to an external value,
            False to exclude all bound variables and any other value to forgo
            this check.

        ``deep=True|False`` (by default it's ``False``)
             Set to True to return nested variables meeting all other criteria.

        ``sort=True|False`` (by default it's ``False``)
            Set to True to return the variables in a consistent order. (Note
            that this does _not_ mean alphabetical sorting of all variables,
            just that the order is consistent between calls!)
        """
        def viter(stream, const, inter, state, bound, deep):
            for var in stream:
                # Filter constants
                if const is not None:
                    if const != var._is_constant:
                        continue
                # Filter intermediary variables
                if inter is not None:
                    if inter != var._is_intermediary:
                        continue
                # Filter states
                if state is not None:
                    if state != var._is_state:
                        continue
                # Filter bound variables
                if bound is not None:
                    if bound != var._is_bound:
                        continue
                # Yield this variable
                yield var
        stream = self._create_variable_stream(deep, sort)
        return viter(stream, const, inter, state, bound, deep)

    def var(self, name):
        """
        Searches for the given variable and returns it if found. Accepts both
        single names ``x`` and qualified names ``x.y`` as input.
        """
        names = name.split('.')
        var = self
        for x in names:
            var = var[x]
        return var


class VarOwner(ModelPart, VarProvider):
    """
    Represents a holder of Variables

    Minimal dictionary support is provided: A variable named "x" can be
    obtained from an owner ``m`` using ``m["x"]``. The number of variables in
    ``m`` is given by ``len(m)`` and the presence of "x" in ``m`` can be tested
    using ``if "x" in m:``.
    """

    def __init__(self, parent, name):
        super(VarOwner, self).__init__(parent, name)
        self._variables = {}
        # Set component
        self._component = self
        while type(self._component) != Component:
            self._component = self._component.parent()

    def add_variable(self, name):
        """
        Adds a child variable with the given `name` to this :class:`VarOwner`.

        Returns the newly created :class:`myokit.Variable` object.
        """
        if not self.can_add_variable(name):
            raise myokit.DuplicateName(
                'The name <' + str(name) + '> is already in use within this'
                ' scope.')
        try:
            var = None
            self._variables[name] = var = Variable(self, name)
        finally:
            self.model()._reset_validation()
            if var is not None:
                var._reset_cache()
        return var

    def add_variable_allow_renaming(self, name):
        """
        Attempts to add a child variable with the given `name` to this
        :class:`VarOwner`, but uses a different name if this causes any
        conflicts.

        The new variable's name will be modified by appending `_1`, `_2`, etc.
        until the conflict is resolved.

        This method can be used when symbolically manipulating a model in
        situations where the exact names are unimportant.

        Returns the newly created :class:`myokit.Variable` object.
        """
        try:
            return self.add_variable(name)
        except myokit.DuplicateName:
            # Get similar names
            root = name + '_'
            n = len(name) + 1
            names = set([
                x.name() for x in self.variables() if x.name()[:n] == root])
            # Find unused variant
            for i in range(1, 2 + len(names)):
                name = root + str(i)
                if name not in names:
                    break
            # Add
            return self.add_variable(name)

    def can_add_variable(self, name, variable_whitelist=None):
        """
        Returns ``True`` if a variable can be added to this :class:`VarOwner`
        under the given ``name``.

        This method is automatically called by :meth:`add_variable()` and
        `move_variable()`, there is no need to call it before using these
        methods.

        To ignore clashes with known variables, a list ``variable_whitelist``
        can be passed in.
        """
        name = check_name(name)

        # List of variables to exclude when checking
        if variable_whitelist is None:
            variable_whitelist = []

        # Determine if variable name would clash with an existing name:
        # Scenario 1: There is an alias accessible to this varowner that
        # clashes with this name
        if self._component.has_alias(name):
            return False

        # Scenario 2: One of this VarOwner's ancestors already contains a
        # variable of that name.
        par = self.parent()
        while type(par) != Model:
            if name in par:
                # Return False, unless the variable is whitelisted
                return par[name] in variable_whitelist
            par = par.parent()

        # Scenario 3: One of this VarOwner's descendants already has that name.
        for var in self.variables(deep=True):
            if var.name() == name:
                # Return False, unless the variable is whitelisted
                return var in variable_whitelist

        # It's free!
        return True

    def __contains__(self, key):
        return key in self._variables

    def _create_variable_stream(self, deep, sort):
        if deep:
            if sort:
                def viter(owner):
                    for n, v in sorted(owner._variables.items()):
                        yield v
                        for w in v._create_variable_stream(True, True):
                            yield w
                return viter(self)
            else:
                def viter(owner):
                    for v in owner._variables.values():
                        yield v
                        for w in v._create_variable_stream(True, False):
                            yield w
                return viter(self)
        else:
            if sort:
                def viter(owner):
                    for n, v in sorted(owner._variables.items()):
                        yield v
                return viter(self)
            else:
                return self._variables.values()

    def get(self, name, class_filter=None):
        """
        Searches for a variable with the given ``qname`` and returns it.

        To return only objects of a certain class, pass it in as
        ``class_filter``.

        The qnames are specified relative to the :class:`VarOwner`. For
        example, in a model with a component ``ina`` and a variable ``ina.h``
        we expect the following results

            >>> import myokit
            >>> m = myokit.load_model('example')
            >>> c = m.get('ina')        # Retrieves the component <ina>
            >>> h = c.get('h')          # Retrieves the variable <ina.h>
            >>> x = c.get('ina.h')      # Searches for <ina.ina.h>: KeyError!
            Traceback (most recent call last):
              File "<stdin>", line 1, in <module>
            KeyError: 'ina'

        """
        # Return model part immediatly
        if isinstance(name, ModelPart):
            if name.model() is self._model:
                return name
            raise ValueError(
                'Given argument ' + repr(name) + ' is from a different model.')

        # Find variable
        names = name.split('.')
        x = self
        try:
            for name in names:
                x = x[name]
        except KeyError:
            raise KeyError(str(name))

        # Apply optional class filter
        if class_filter and not isinstance(x, class_filter):
            raise KeyError(str(name) + ' of class ' + str(class_filter))

        return x

    def __getitem__(self, key):
        return self._variables[key]

    def __iter__(self):
        return iter(self._variables.values())

    def __len__(self):
        return len(self._variables)

    def move_variable(self, variable, new_parent, new_name=None):
        """
        Moves the given variable to another :class:`VarOwner` ``new_parent``.
        In addition, this method can be used to rename variables (either with
        or without moving them).
        """
        if variable.parent() != self:
            raise ValueError(
                'move_variable failed: variable <' + variable.qname()
                + '> does not have parent <' + self.qname() + '>.')

        # Check names
        old_name = variable.name()
        if new_name:
            new_name = str(new_name)
        else:
            new_name = old_name

        # Ignore move to same position
        if new_parent == self and new_name == old_name:
            return

        # Check if name is allowed in new parent
        if not new_parent.can_add_variable(new_name, [variable]):
            raise myokit.DuplicateName(
                'The name <' + new_name + '> is already in use as a variable'
                ' name within this scope.')

        # Check state variables aren't made nested
        if variable.is_state():
            if not isinstance(new_parent, myokit.Component):
                raise Exception('State variables cannot be nested.')

        # Move
        try:
            # Change listing in VarOwner objects
            del self._variables[old_name]
            new_parent._variables[new_name] = variable
            # Change variable's _parent and _name attribute
            variable._parent = new_parent
            variable._name = new_name
        finally:
            variable._reset_cache()
            self.model()._reset_validation()

    def remove_variable(self, variable, recursive=False):
        """
        Removes the given variable from this :class:`VarOwner` and from the
        model.

        If ``recursive`` is ``True``, any child variables will be deleted as
        well.

        A :class:`myokit.IntegrityError` will be raised if
        """
        if variable.parent() != self:
            raise ValueError(
                'remove_variable failed: variable <' + variable.qname()
                + '> does not have parent <' + self.qname() + '>.')

        # Handle internal variable deletion steps
        variable._delete(recursive=recursive)
        try:
            # Remove from this VarOwner
            del self._variables[variable.name()]
        finally:
            self.model()._reset_validation()

    def _remove_variable_internal(self, variable):
        """
        Removes the given variable from this :class:`VarOwner` but doesn't do
        any of the bookkeeping steps.
        """
        del self._variables[variable.name()]

    def _resolve(self, name):
        """ See :meth:`VarProvider._resolve(). """
        def sa(name):
            # Suggest alternative
            m = self.model()
            (var, sug, msg) = m.suggest_variable(name)
            return msg

        # Try resolving as an alias
        try:
            return self._component._alias_map[name]
        except KeyError:
            pass

        # Resolve as a local variable name
        dot = name.find('.')
        if dot < 0:
            # Local name given: child of this VarOwner or child of ancestor
            par = self
            while type(par) != Model:
                try:
                    return par[name]
                except KeyError:
                    par = par.parent()
            raise myokit.UnresolvedReferenceError(name, sa(name))
        else:
            # Component given. Resolve as direct child of component
            model = self.model()
            cname = name[0:dot]
            vname = name[1 + dot:]
            try:
                comp = model[cname]
            except KeyError:
                raise myokit.UnresolvedReferenceError(name, sa(name))
            try:
                return comp[vname]
            except KeyError:
                raise myokit.UnresolvedReferenceError(name, sa(name))


class Model(ObjectWithMeta, VarProvider):
    """
    Represents an electrophysiological cell model, structured in components.

    Components can be added to the model using :meth:`add_component()`. Access
    to a model's component is provided through the :meth:`get()` method and
    :meth:`components()`.

    Minimal dictionary support is provided: A component named "x" can be
    obtained from a model ``m`` using ``m["x"]``. The number of components in
    ``m`` is given by ``len(m)`` and the presence of "x" in ``m`` can be tested
    using ``if "x" in m:``.

    Variables stored inside components can be accessed using :meth:`get()` or
    :meth:`values()`. Values defined through their derivative make up the
    model state and can be accessed using :meth:`states()`. States have
    initial values accessible through :meth:`inits()`.

    A model's validity can be checked using :meth:`is_valid()`, which returns
    the latest validation status and :meth:`validate()`, which (re)validates
    the model. Warnings can be obtained using :meth:`warnings()`

    The optional constructor argument ``name`` can be used to set a meta
    property "name".

    Meta-data properties can be accessed via the property ``meta``, for example
    ``model.meta['key']= 'value'``.

    For consistency with components, variables, and expressions, models cannot
    be compared with ``==`` (which will only return ``True`` if both operands
    are the same object). Checking if models are the same in other senses can
    be done with :meth:`is_similar`. Models can be serialised with ``pickle``.
    """

    def __init__(self, name=None):
        super(Model, self).__init__()

        # A dictionary of components
        self._components = {}

        # The model's state variables
        self._state = []

        # The model's current state (list of floats)
        self._current_state = []

        # A dict mapping binding names to variables
        self._bindings = {}

        # A dict mapping label names to variables
        self._labels = {}

        # A set of user functions
        self._user_functions = {}

        # A list of warnings about the model's integrity
        self._warnings = []

        # A list of names that can't be used as unames()
        self._reserved_unames = set()
        self.reserve_unique_names(*myokit.KEYWORDS)

        # A dict mapping `prefix` strings to `prepend` strings. When generating
        # unames any uname startinhg with `prefix` will be prepended by
        # `prepend`.
        self._reserved_uname_prefixes = {}

        # A dictionary token_start : (token, object) relating some (not all!)
        #  tokens to a model. Will be filled by parser when reading a model.
        self._tokens = {}

        # Validation status: True, False or None (not tested)
        self._valid = None

        # Name meta property
        if name:
            self.meta['name'] = str(name)

    def add_component(self, name):
        """
        Adds a component with the given ``name`` to this model.

        This method resets the model's validation status.

        Returns the newly created :class:`myokit.Component` object.
        """
        name = check_name(name)
        # Check for duplicate names
        if name in self:
            raise myokit.DuplicateName(
                'There is already a component named <' + str(name)
                + '> in this model.')
        try:
            self._components[name] = comp = Component(self, name)
        finally:
            self._valid = None
        return comp

    def add_component_allow_renaming(self, name):
        """
        Attempts to add a component with the given `name` to this model, but
        uses a different name if this causes any conflicts.

        The new component's name will be modified by appending `_1`, `_2`, etc.
        until the conflict is resolved.

        This method can be used when symbolically manipulating a model in
        situations where the exact names are unimportant.

        Returns the newly created :class:`myokit.Component` object.
        """
        try:
            return self.add_component(name)
        except myokit.DuplicateName:
            # Get similar names
            root = name + '_'
            n = len(name) + 1
            names = set([
                x.name() for x in self.components() if x.name()[:n] == root])
            # Find unused variant
            for i in range(1, 2 + len(names)):
                name = root + str(i)
                if name not in names:
                    break
            # Add
            return self.add_component(name)

    def add_function(self, name, arguments, template):
        """
        Adds a user function to this model.

        Returns the newly created :class:`myokit.UserFunction` object.
        """
        name = check_name(name)

        # Check argument names and uniqueness
        arguments = [myokit.Name(check_name(x)) for x in arguments]
        n = len(arguments)
        if len(set(arguments)) != n:
            for k, arg in enumerate(arguments):
                if arg in arguments[k + 1:]:
                    raise myokit.DuplicateFunctionArgument(
                        'The argument name <' + str(arg)
                        + '> is already in use in this function.')

        # Check template is expression
        if not isinstance(template, myokit.Expression):
            template = myokit.parse_expression(template)

        # TODO: Check name does not conflict with an existing function #584

        # Check signature uniqueness. Add number of arguments to name to allow
        # overloading
        uname = name + '(' + str(n) + ')'
        if uname in self._user_functions:
            raise myokit.DuplicateFunctionName(
                'A function called "' + name + '" with ' + str(n)
                + ' arguments is already defined in this model.')

        # Check template
        refs = template.references()
        for ref in refs:
            if isinstance(ref, myokit.Derivative):
                raise myokit.InvalidFunction(
                    'The dot() operator cannot be used in user functions.')
            if template.contains_type(myokit.PartialDerivative):
                raise myokit.InvalidFunction(
                    'The partial() operator cannot be used in user functions.')
            if template.contains_type(myokit.InitialValue):
                raise myokit.InvalidFunction(
                    'The init() operator cannot be used in user functions.')

        # Check for unused arguments, undeclared arguments
        ref_names = set([x._value for x in refs])
        for arg in arguments:
            arg = arg._value
            if arg not in ref_names:
                raise myokit.InvalidFunction(
                    'The function argument <' + arg
                    + '> is declared but never used.')
            ref_names.remove(arg)
        if ref_names:
            raise myokit.InvalidFunction(
                'The variable <' + ref_names.pop()
                + '> is used in the function but never declared.')

        # Create function and return
        func = UserFunction(name, arguments, template)
        self._user_functions[uname] = func
        return func

    def binding(self, binding):
        """
        Returns the variable with the binding label ``binding``. If no such
        variable is found, ``None`` is returned.
        """
        return self._bindings.get(binding, None)

    def bindings(self):
        """
        Returns an iterator over all (binding label : variable) mappings in
        this model.
        """
        # New dict allows removing labels using this iterator
        return dict(self._bindings).items()

    def bindingx(self, binding):
        """
        Returns the variable with the binding label ``binding``, raising a
        :class:`myokit.IncompatibleModelError` if no such variable is found.

        See :meth:`Model.binding()`.
        """
        try:
            return self._bindings[binding]
        except KeyError:
            raise myokit.IncompatibleModelError(
                self.name(),
                'No variable found with binding "' + str(binding) + '".')

    def check_units(self, mode=myokit.UNIT_TOLERANT):
        """
        Checks the units used in this model.

        Models can specify units in two ways:

        1. By setting variable units. This is done using the ``in`` keyword in
           ``mmt`` syntax or through :meth:`myokit.Variable.set_unit()`. This
           specifies the unit that a variable's value should be in.
        2. By adding units to literals. This is done using square brackets in
           ``mmt`` syntax (for example ``5 [m] / 10 [s]``) or by adding a unit
           when creating a Number object, for example
           ``myokit.Number(2, myokit.units.mV)``.

        When checking a model's units, this method loops over all variables and
        performs two checks:

        1. The unit resulting from the variable's RHS is evaluated. This
           involves checking rules such as "in ``x + y``, ``x`` and ``y`` must
           have the same units, or "in ``exp(x)`` the units of ``x`` must be
           ``dimensionless``". A :class:`myokit.IncompatibleUnitExpression`
           will be raised if any inompatibilities are found.
        2. The calculated unit is compared with the variable unit. An
           ``IncompatibleUnitError`` will be triggered if the two units don't
           match.

        Two unit-checking modes are available.

        In strict mode (``mode=myokit.UNIT_STRICT``), all unspecified units in
        expressions are treated as "dimensionless". For example, the expression
        ``5 * V`` where ``V`` is in ``[mV]`` will be treated as dimensionless
        times millivolt (or ``[1] * [mV]`` in mmt syntax), resulting in the
        unit ``[mV]``.
        The expression ``5 + V`` will be interpreted as dimensionless plus
        millivolt, and will raise an error.
        In strict mode, functions such as ``sin`` and ``exp`` will check that
        their argument is dimensionless (so ``sin(3 [m])`` is never allowed,
        only e.g. ``sin(3 [m] / 1 [m])``).

        In tolerant mode, unspecified units will be treated as whatever makes
        the expression work. So ``? + [mV]`` wil be interpreted as
        ``[mV] + [mV]``. In addition, functions that require dimensionless
        input in strict mode won't perform this check in tolerant mode.

        A note about references:

        In both modes, when a reference is encountered, for example when
        checking the expression ``5 * y``, the system will look up the variable
        y's unit, and will not look at y's rhs.
        Consider the following buggy model:

            x = 5 [mV]      # RHS unit, no variable unit
            y = 3 [A] + x   # RHS unit, no variable unit

        When checking the expression ``y = 3 + x`` the variable ``x`` will be
        treated as unspecified, because no variable unit is set for ``x`` using
        the ``in`` keyword. In strict mode, this will lead to an error when
        checking ``x = 5 [mV]`` because ``x`` is dimensionless while ``5 [mV]``
        has units ``[mV]``. In tolerant mode, no error will be raised. When
        tolerantly evaluating ``y = 3[A] + x`` it will be assumed that ``x`` is
        also in ``[A]``, because no variable unit is given that says otherwise
        (despite the RHS of ``x`` having units ``mV``).
        """
        # Get time unit
        t = self.time_unit(mode)

        # Check variable units against calculated units (and check caluclated
        # units in the process).
        for var in self.variables(deep=True):
            # Get variable unit
            v = var.unit(mode)

            # Get rhs unit
            e = var.rhs()
            if e is None:
                raise myokit.IntegrityError('No RHS set for ' + var.qname())
            e = e.eval_unit(mode)

            # No unit? Then allow (in strict mode v and e are never None)
            if v is None or e is None:  # pragma: no cover
                # Adding a print() here shows this line is hit, coverage still
                # disagrees. Puzzled.
                continue

            # Rhs unit from a state? Then multiply by time to get var's unit
            if t is not None and var.is_state():
                e *= t

            # Compare loosely
            if not myokit.Unit.close(v, e):
                msg = 'Incompatible units in <' + var.qname() + '>'
                if var._token is not None:
                    msg += ' on line ' + str(var._token[2])
                msg += '. Variable unit ' + v.clarify()
                msg += ' differs from calculated unit ' + e.clarify()
                msg += ', by a factor ' + (v / e).clarify() + '.'
                raise myokit.IncompatibleUnitError(msg, var._token)

    def clone(self):
        """
        Returns a (deep) clone of this model.
        """
        clone = Model()

        # Copy meta data
        self._clone_metadata(clone)

        # Clone component/variable structure
        for c in self._components.values():
            c._clone1(clone)

        # Clone state
        for k, v in enumerate(self._state):
            clone.get(v.qname()).promote(self._current_state[k])

        # Create mapping of old var references to new references
        var_map = {}
        lhs_map = {}
        for v in self.variables(deep=True):
            var_map[v] = w = clone.get(v.qname())
            lhs_map[myokit.Name(v)] = myokit.Name(w)
        for v in self.states():
            lhs_map[myokit.Derivative(myokit.Name(v))] = myokit.Derivative(
                myokit.Name(clone.get(v.qname())))

        # Clone component/variable contents (equations, references)
        for k, c in self._components.items():
            c._clone2(clone[k], lhs_map, var_map)

        # Copy unique names and unique name prefixes
        clone.reserve_unique_names(*iter(self._reserved_unames))
        for prefix, prepend in self._reserved_uname_prefixes.items():
            clone.reserve_unique_name_prefix(prefix, prepend)

        # Return
        return clone

    def code(self, line_numbers=False):
        """
        Returns this model in ``mmt`` syntax.

        Line numbers can be added by setting ``line_numbers=True``.
        """
        b = StringIO()
        b.write('[[model]]\n')
        self._code(b, 0)
        if line_numbers:
            lines = b.getvalue().strip().split('\n')
            out = []
            n = int(math.ceil(math.log10(len(lines))))
            for k, line in enumerate(lines):
                out.append('%*d ' % (n, 1 + k) + line)
            return '\n'.join(out) + '\n'
        else:
            return b.getvalue()

    def _code(self, b, t):
        """
        Internal version of Model.code()
        """
        # b = buffer, t = number of tabs
        # Meta properties
        self._code_meta(b, 0)

        # Initial state
        if self._state:
            pre = t * TAB
            b.write(pre + '# Initial values\n')
            names = [eq.lhs.code() for eq in self.inits()]
            n = max([len(name) for name in names])
            names = iter(names)
            for eq in self.inits():
                name = next(names)
                b.write(
                    pre + name + ' ' * (n - len(name)) + ' = ' + eq.rhs.code()
                    + '\n')
            b.write(pre + '\n')
        else:
            # No initial state? Then add newline
            b.write('\n')

        # Components
        for c in self.components(sort=True):
            c._code(b, t)

    def components(self, sort=False):
        """
        Returns an iterator over this model's component objects.
        """
        if sort:
            def i(s):
                for k, v in s:
                    yield v
            return i(sorted(self._components.items()))
        else:
            return self._components.values()

    def component_cycles(self):
        """
        Finds cyclical references between components and returns them. For
        example, if ``a.p`` depends on ``b.q`` while ``b.x`` depends on
        ``a.y``, a cycle ``a > b > a`` will be returned.

        For a faster way to check if there are any interdependent components
        (without returning the exact cycles found), use
        :meth:`has_interdependent_components()`.
        """
        # Collect dependencies between components in a structure:
        # compdeps = {
        #       c1 : set([c2, c3, c4, ...]),
        #       c2 : set([c3, c5, ...]),
        #        :
        #        }
        compdeps = dict([(c, set()) for c in self.components()])
        for var in self.variables(deep=True):
            c1 = var.parent(Component)
            d1 = compdeps[c1]
            for ref in var.rhs().references():
                if not ref.is_state_value():
                    c2 = ref.var().parent(Component)
                    if c1 != c2:
                        d1.add(c2)

        # Follow each component, find cycles
        # Don't inspect any component twice, if cycles exist one will always be
        # detected on the first pass
        cycles = []         # Found cycles, e.g. (a, b, c, a)
        followed = set()    # Prevent inspecting twice

        def follow(comp, trail):
            # Detect cycle:
            if comp in trail:
                cycles.append(trail[trail.index(comp):] + [comp])
                return

            # No cycle detected, append to trail
            trail.append(comp)

            # Follow all (see note about sorting)
            for comp2 in sorted(compdeps[comp], key=lambda x: x.name()):
                follow(comp2, trail)
            trail.pop()
            followed.add(comp)

        # Start following
        # Note: Order seems to be important here to avoid listing cycles more
        # than once.
        for comp in sorted(self.components(), key=lambda x: x.name()):
            if comp not in followed:
                follow(comp, [])

        # Return cycles
        return cycles

    def __contains__(self, key):
        return key in self._components

    def count_components(self):
        """
        Returns the number of components in this model.
        """
        return len(self._components)

    def count_states(self):
        """
        Returns the number of state variables in this model.
        """
        return len(self._state)

    def create_unique_names(self):
        """
        Create a globally unique name for each Component and Variable.

        Ideally, the global name equals the variable or component's basic name.
        If a name is disputed the following strategy will be used:

        1. For variables, the parent name will be added as a prefix to **all**
           variables claiming the disputed name.
        2. If problems persist, a suffix ``_i`` will be added, where ``i`` is
           the first integer which doesn't result in clashing names.

        In addition, the method will avoid names listed using
        :meth:`reserve_unique_names()` and names starting with a prefix listed
        using :meth:`reserve_unique_prefix()`.
        """
        # Don't suggest names started with registered prefixes
        def prepend(name):
            for prefix, prepend in self._reserved_uname_prefixes.items():
                if name.startswith(prefix):
                    return prepend + name
            return name

        # Gather disputed names
        allnames = set(self._reserved_unames)
        disputed = set()
        for comp in self.components():
            name = prepend(comp._name)
            if name not in disputed:
                if name in allnames:
                    disputed.add(name)
                else:
                    allnames.add(name)
            for var in comp.variables(deep=True):
                name = prepend(var._name)
                if name not in disputed:
                    if name in allnames:
                        disputed.add(name)
                    else:
                        allnames.add(name)

        # Set unique names
        for comp in sorted(self.components(), key=lambda x: x.name()):

            # Set names for component
            name = prepend(comp._name)
            if name in disputed:
                i = 1
                root = name + '_'
                name = root + str(i)
                while name in allnames:
                    i += 1
                    name = root + str(i)
                allnames.add(name)
            comp._uname = name

            # Set names for variables
            for var in sorted(comp.variables(deep=True),
                              key=lambda x: x.qname()):
                name = prepend(var._name)
                if name in disputed:
                    name = prepend(var.qname().replace('.', '_'))
                    if name in allnames:
                        i = 1
                        root = name + '_'
                        name = root + str(i)
                        while name in allnames:  # pragma: no cover
                            # Not sure if this is reachable!
                            i += 1
                            name = root + str(i)
                    allnames.add(name)
                var._uname = name

    def _create_variable_stream(self, deep, sort):
        def stream(model):
            for c in model.components(sort=sort):
                for v in c.variables(deep=deep, sort=sort):
                    yield v
        return stream(self)

    def evaluate_derivatives(
            self, state=None, inputs=None, precision=myokit.DOUBLE_PRECISION,
            ignore_errors=False):
        """
        Evaluates and returns the values of all state variable derivatives.
        The values are returned in a list sorted in the same order as the
        state variables.

        Arguments:

        ``state=None``
            If given, the state values given by ``state`` will be used as
            starting point. Here ``state`` can be any object accepted as input
            by :meth:``map_to_state()``.
        ``inputs=None``
            To set the values of external inputs, a dictionary mapping binding
            labels to values can be passed in as ``inputs``.
        ``precision``
            To assist in finding the origins of numerical errors, the equations
            can be evaluated using single-precision floating point. To do this,
            set ``precision=myokit.SINGLE_PRECISION``.
        ``ignore_errors``
            By default, the evaluation routine raises
            :class:`myokit.NumericalError` exceptions for invalid operations.
            To return ``NaN`` instead, set ``ignore_errors=True``.

        """
        values = {}

        # Insert new state (if required)
        if state is not None:
            new_state = self.map_to_state(state)
            for state, value in zip(self._state, new_state):
                values[myokit.Name(state)] = value
            state = None

        # Insert values of inputs (if required)
        if inputs is not None:
            for label, value in inputs.items():
                var = self._bindings.get(label)
                if var is not None:
                    values[myokit.Name(var)] = float(value)

        # Get solvable order
        order = self.solvable_order()

        # Evaluate all variables in solvable order
        if ignore_errors:
            for group in order.values():
                for eq in group:
                    if eq.lhs in values:
                        continue
                    try:
                        value = eq.rhs.eval(values, precision=precision)
                    except myokit.NumericalError:
                        value = float('nan')
                    values[eq.lhs] = value
        else:
            for group in order.values():
                for eq in group:
                    if eq.lhs in values:
                        continue
                    values[eq.lhs] = eq.rhs.eval(values, precision=precision)

        # Return calculated state
        return [values[state.lhs()] for state in self._state]

    def eval_state_derivatives(
            self, state=None, inputs=None, precision=myokit.DOUBLE_PRECISION,
            ignore_errors=False):
        """
        Deprecated alias of :meth:`evaluate_derivatives()`.
        """
        # Deprecated since 2021-08-03
        import warnings
        warnings.warn(
            'The method `eval_state_derivatives` is deprecated. Please use'
            ' `evaluate_derivatives()` instead.')
        return self.evaluate_derivatives(
            state, inputs, precision, ignore_errors)

    def expressions_for(self, *variables):
        """
        Determines the expressions needed to evaluate one or more variables.

        If state variables are included in the list, "evaluating" the variable
        is interpreted as evaluating its derivative.

        Returns a tuple ``(eqs, args)`` where ``eqs`` is a list of Equation
        objects in solvable order containing the minimal set of equations
        needed to evaluate the given ``variable`` and ``args`` is a list of
        the state variables and bound variables these expressions require as
        input.
        """
        # Make sure all variables are (locally owned) Variable objects
        temp = []
        for variable in variables:
            if isinstance(variable, myokit.Variable):
                temp.append(self.get(variable.qname()))
            elif isinstance(variable, myokit.LhsExpression):
                temp.append(self.get(variable.var().qname()))
            else:
                temp.append(self.get(variable))
        variables = temp
        del temp

        # Get shallow dependencies of all required equations
        # Use ordered dict to get consistent output
        shallow = OrderedDict()
        arguments = []
        equations = OrderedDict()

        def add_dep(lhs):
            if lhs in shallow or lhs in arguments:
                return
            var = lhs.var()
            if var.is_bound() or (var.is_state() and not lhs.is_derivative()):
                arguments.append(lhs)
                return
            rhs = var.rhs()
            dps = sorted(rhs.references(), key=str)
            shallow[lhs] = dps
            equations[lhs] = rhs
            for dep in dps:
                add_dep(dep)

        for variable in variables:
            for lhs in sorted(variable.rhs().references(), key=str):
                add_dep(lhs)

        # Filter out dependencies on arguments
        for dps in shallow.values():
            for arg in arguments:
                if arg in dps:
                    dps.remove(arg)

        # Order expressions list of expressions
        eq_list = []
        while len(shallow):
            done = []
            for lhs, dps in shallow.items():
                if len(dps) == 0:
                    eq_list.append(Equation(lhs, equations[lhs]))
                    done.append(lhs)
            if len(done) == 0:
                raise Exception('Failed to solve system of equations.')
            for lhs in done:
                del shallow[lhs]
                for dps in shallow.values():
                    if lhs in dps:
                        dps.remove(lhs)

        # Add final equations and return
        for variable in variables:
            eq = variable.eq()
            if eq not in eq_list:
                eq_list.append(eq)
        eq_list = myokit.EquationList(eq_list)

        return (eq_list, arguments)

    def format_state(self, state=None, state2=None,
                     precision=myokit.DOUBLE_PRECISION):
        """
        Converts the given list of floating point numbers to a string where
        each line has the format ``<full_qualified_name> = <float_value>``.

        Arguments:

        ``state=None``
            The state to show derivatives for. If no state is given the state
            returned by :meth:`state` is used.
        ``state2=None``
            An optional second state, to be shown next to ``state`` for
            comparison.
        ``precision=myokit.DOUBLE_PRECISION``
            An optional precision argument to pass into
            :meth:`myokit.float.str` when formatting the state values.

        """
        n = len(self._state)
        if state is not None:
            if len(state) != n:
                raise ValueError(
                    'Argument `state` must be a list of (' + str(n)
                    + ') floating point numbers.')
        else:
            state = self.state()

        if state2 is not None:
            if len(state2) != n:
                raise ValueError(
                    'Argument `state2` must be a list of (' + str(n)
                    + ') floating point numbers.')

        out = []
        n = max([len(x.qname()) for x in self.states()])
        for k, var in enumerate(self.states()):
            out.append(
                var.qname() + ' ' * (n - len(var.qname()))
                + ' = ' + myokit.float.str(state[k], precision=precision))
        if state2 is not None:
            n = max([len(x) for x in out])
            for k, var in enumerate(self.states()):
                out[k] += (
                    ' ' * (4 + n - len(out[k]))
                    + myokit.float.str(state2[k], precision=precision))

        return '\n'.join(out)

    def format_state_derivatives(self, state=None, derivatives=None,
                                 precision=myokit.DOUBLE_PRECISION):
        """
        Like :meth:`format_state` but displays the derivatives along with
        each state's value.


        Arguments:

        ``state=None``
            The state to display. If no state is given the state returned by
            :meth:`state` is used.
        ``derivatives=None``
            An optional list of evaluated derivatives. If not given, the values
            will be calculed from ``state`` using :meth:`eval_derivatives()`.
        ``precision=myokit.DOUBLE_PRECISION``
            An optional precision argument to use when evaluating the state
            derivatives, and to pass into :meth:`myokit.float.str` when
            formatting the state values and derivatives.

        """
        n = len(self._state)
        if state is None:
            state = self.state()
        elif len(state) != n:
            raise ValueError(
                'Argument `state` must be a list of (' + str(n)
                + ') floating point numbers.')

        if derivatives is None:
            derivatives = self.evaluate_derivatives(
                state, precision=precision)
        elif len(derivatives) != n:
            raise ValueError(
                'Argument `deriv` must be a list of (' + str(n)
                + ') floating point numbers.')

        out = []
        n = max([len(x.qname()) for x in self.states()])
        for i, var in enumerate(self.states()):
            s = myokit.float.str(state[i], precision=precision)
            d = myokit.float.str(derivatives[i], precision=precision)
            out.append(
                var.qname() + ' ' * (n - len(var.qname())) + ' = ' + s
                + ' ' * (24 - len(s)) + '   dot = ' + d)
        return '\n'.join(out)

    def format_warnings(self):
        """
        Formats all warnings generated during the last call to :meth:`validate`
        and returns a string containing the result.
        """
        pre = str(len(self._warnings)) + ' validation warning(s) given'
        if len(self._warnings) == 0:
            return pre
        out = []
        i = 0
        f = ' ({:' + str(1 + int(math.log10(len(self._warnings)))) + '}) '
        for w in self._warnings:
            i += 1
            m = str(w)
            out.append(f.format(i) + m)
        return pre + ':\n' + '\n'.join(out)

    def get(self, name, class_filter=None):
        """
        Searches for a component or variable with the given ``qname`` and
        returns it.

        To return only objects of a certain class, pass it in as
        ``class_filter``.
        """
        # Return model part immediatly
        if isinstance(name, ModelPart):
            if name.model() is self:
                return name
            raise ValueError(
                'Given argument ' + repr(name) + ' is from a different model.')

        # Split name, get different parts
        names = name.split('.')
        x = self
        try:
            for name in names:
                x = x[name]
        except KeyError:
            raise KeyError(str(name))

        # Apply optional class filter
        if class_filter and not isinstance(x, class_filter):
            raise KeyError(str(name) + ' of class ' + str(class_filter))

        return x

    def get_function(self, name, nargs):
        """
        Returns the user function with name ``name`` and ``nargs`` arguments.
        """
        return self._user_functions[str(name) + '(' + str(nargs) + ')']

    def __getitem__(self, key):
        return self._components[key]

    def has_component(self, name):  # has_variable() is an inherited method
        """
        Returns ``True`` if this model has a component with the given ``name``.
        """
        return name in self._components

    def has_interdependent_components(self):
        """
        Returns ``True`` if this model contains mutually dependent components.
        That is, if there exists any component A whose variables depend on
        variables from component B, while variables in component B depend on
        variables in component A.

        To see the variables causing the interdependence, use
        :meth:`component_cycles()`.
        """
        equations = self.solvable_order()
        remaining = equations['*remaining*']
        return len(remaining) > 0

    def has_parse_info(self):
        """
        Returns ``True`` if this model retains parsing information, so that
        methods such as :meth:`item_at_text_position` and :meth:`show_line_of`
        can be used.
        """
        return bool(self._tokens)

    def has_warnings(self):
        """
        Returns ``True`` if this model has any warnings.
        """
        return len(self._warnings)

    def import_component(self, external_component, new_name=None, var_map=None,
                         allow_name_mapping=False, convert_units=False):
        """
        Imports one or multiple components from another model
        (the "source model") into this one (the "target model").

        If variables in the ``external_component`` refer to variables from
        other components they will be mapped on to variables from this model
        by trying the following strategies (in order):

        1. Using the provided dict ``var_map``, which maps variables in the
           source model to variables in this model.
        2. By assuming variables with the same label/binding map onto each
           other.
        3. By assuming that variables with the same qualified names map onto
           each other. This rule is only applied if ``allow_name_mapping`` is
           set to ``True``.

        Arguments:

        ``external_component``
            A :class:`myokit.Component` or a list of
            :class:`components <myokit.Component>` from another model.
        ``new_name``
            An optional new name for the imported component
            or list of names if multiple components are provided.
        ``var_map``
            An optional dict mapping variables in the source model to
            variables from this model (with variables specified as objects or
            as fully qualified names).
        ``allow_name_mapping``
            Set this to ``True`` to allow mapping based on fully qualified
            names, e.g. a variable ``x.y`` in the source model will be mapped
            to a variable ``x.y`` in the target model.
        ``convert_units``
            Set this to ``True`` to convert the units of any mapped variables,
            if required and possible.

        If any variables cannot be mapped, a
        :class:`myokit.VariableMappingError` will be raised. A
        :class:`myokit.DuplicateNameError` will be raised if the component's
        name or ``new_name`` clashes with an existing component name. If unit
        conversion is enabled and variables with incompattible units are
        mapped onto each other, a class:`myokit.IncompatibleUnitsError` will
        be raised.
        """

        # Check component is list or component and new_name is string or list
        if isinstance(external_component, myokit.Component):
            external_component = [external_component]
        else:
            ext_comp_error_str = (
                'Method import_component() expects a myokit.Component '
                'or list of myokit.Components'
            )
            try:
                ok = all(
                    isinstance(c, myokit.Component) for c in external_component
                )
                if not ok:
                    raise TypeError(ext_comp_error_str)
            except TypeError:
                raise TypeError(ext_comp_error_str)

        if new_name is None:
            new_name = []
            for comp in external_component:
                new_name.append(comp.name())

        new_name_error_str = (
            'new_name must be a list of strings the same length '
            'as external_component, or a string if only one '
            'component is provided'
        )
        if isinstance(new_name, basestring):
            if len(external_component) != 1:
                raise TypeError(new_name_error_str)
            new_name = [new_name]
        else:
            try:
                ok = (
                    len(new_name) == len(external_component) and
                    all(isinstance(name, basestring) for name in new_name)
                )
                if not ok:
                    raise TypeError(new_name_error_str)
            except TypeError:
                raise TypeError(new_name_error_str)

        # Get external model
        ext_model = external_component[0].model()

        # checking the model for external components
        # are the same and not this model
        for comp in external_component:
            if not comp.has_ancestor(ext_model):
                raise ValueError((
                    'The imported components must be from the same '
                    'model, <{}> and <{}> are not.'
                ).format(comp.name(), external_component[0].name()))
        if ext_model == self:
            raise ValueError(
                'The component(s) to import are already part of this model.')

        # Check if new names clash with those in this model
        for name in new_name:
            if self.has_component(name):
                raise myokit.DuplicateName(
                    'This model already has a component with the name <' + name
                    + '>.')

        # Check for bindings or labels that are already in use
        for comp in external_component:
            for var in comp.variables():
                if self.label(var.label()) is not None:
                    raise myokit.InvalidLabelError(
                        'This model already has a variable with the label "'
                        + str(var.label()) + '".')
                if self.binding(var.binding()) is not None:
                    raise myokit.InvalidBindingError(
                        'This model already has a variable with the binding "'
                        + str(var.binding()) + '".')

        # Create a list of all external variables that require mapping
        vars_to_map = set()
        for i, comp in enumerate(external_component):
            vars_ref = set()
            for var in comp.variables():
                vars_ref.update(var.refs_to(state_refs=False))
                vars_ref.update(var.refs_to(state_refs=True))
            vars_ref.update(comp._alias_map.values())
            vars_ref -= set(comp.variables())
            vars_ref = [x for x in vars_ref if not x.is_nested()]
            vars_to_map.update(vars_ref)
        map_to_clone = []
        for comp in external_component:
            map_to_clone.append(vars_to_map.intersection(comp.variables()))

        # Rename user-provided mapping to user_var_map, and create a new
        # mapping of the form {external_model.variable: self.variable}
        user_var_map = var_map
        var_map = {}

        # Store local vars that are mapped onto
        used_local_vars = set()

        # Check user-specified mapping
        if user_var_map is not None:
            if not isinstance(user_var_map, dict):
                raise TypeError('var_map needs to be of type dict or None.')
            for ext_var, self_var in user_var_map.items():
                # Check target vars in var map are variables and exist in self
                if isinstance(self_var, myokit.Variable):
                    if not self_var.has_ancestor(self):
                        raise myokit.VariableMappingError(
                            'The variable <' + self_var.qname() + '> in the'
                            ' given var_map\'s values is not part of this'
                            ' model.')
                elif isinstance(self_var, basestring):
                    try:
                        self_var = self.var(self_var)
                    except KeyError:
                        raise myokit.VariableMappingError(
                            'The variable name <' + self_var + '> appears in'
                            ' the var_map\'s values but was not found in this'
                            ' model.')
                else:
                    raise TypeError(
                        'Variables in the var_map need to be specified as'
                        ' Variable objects or fully qualified names. Got '
                        + str(type(self_var)) + '.')

                # Check source variables in var map are variables and exist
                # in external model
                if isinstance(ext_var, myokit.Variable):
                    if not ext_var.has_ancestor(ext_model):
                        raise myokit.VariableMappingError(
                            'The variable <' + ext_var.qname() + '> in the'
                            ' given var_map\'s keys but is not part of the'
                            ' source model.')
                elif isinstance(ext_var, basestring):
                    try:
                        ext_var = ext_model.var(ext_var)
                    except KeyError:
                        raise myokit.VariableMappingError(
                            'The variable name <' + ext_var + '> appears in'
                            ' the var_map\'s keys but was not found in the'
                            ' source model.')
                else:
                    raise TypeError(
                        'Variables in the var_map need to be specified as'
                        ' Variable objects or fully qualified names. Got '
                        + str(type(self_var)) + '.')

                # check for duplicates
                if self_var in used_local_vars:
                    raise myokit.VariableMappingError(
                        'Multiple variables map onto <' + self_var.name()
                        + '>.')
                used_local_vars.add(self_var)

                # Valid mapping: Store, but only if this is a required variable
                if ext_var in vars_to_map:
                    var_map[ext_var] = self_var

        # add variables to var_map that map to other imported components
        # but will be reassigned to the clone later
        for l in map_to_clone:
            for ext_var in l:
                if ext_var not in var_map:
                    var_map[ext_var] = None

        # Add non user-specified variables that require mapping
        for ext_var in vars_to_map:
            if ext_var not in var_map:
                # Match variables by binding, label, or name (if enabled)
                self_bind_var = self.binding(ext_var.binding())
                self_label_var = self.label(ext_var.label())
                if self_bind_var is not None:
                    var_map[ext_var] = self_bind_var
                elif self_label_var is not None:
                    var_map[ext_var] = self_label_var
                elif allow_name_mapping and self.has_variable(ext_var.qname()):
                    var_map[ext_var] = self.get(ext_var.qname())
                else:
                    raise myokit.VariableMappingError(
                        ext_var.qname() + ' is used by the external_component'
                        ' but cannot be mapped onto any of the variables in'
                        ' this model.')

        # Find unit conversion factors
        # Note: conversion factors are stored as myokit.Quantity, so that we
        # can multiply them together in a unit-preserving way (if needed)
        factors = {}
        time_factor = None
        if convert_units:
            # Get conversion factors for all mapped variables
            for ext_var, self_var in var_map.items():
                ext_unit = ext_var.unit(myokit.UNIT_STRICT)
                if self_var is None:
                    self_unit = ext_unit
                else:
                    self_unit = self_var.unit(myokit.UNIT_STRICT)
                if not myokit.Unit.close(ext_unit, self_unit):
                    try:
                        factors[ext_var] = myokit.Unit.conversion_factor(
                            self_unit, ext_unit)
                    except myokit.IncompatibleUnitError as e:
                        raise myokit.VariableMappingError(
                            'Unable to map <' + ext_var.qname() + '> onto <'
                            + self_var.qname() + '>: ' + str(e))

            # Check if time-unit conversion is needed
            need_time_factor = False
            for comp in external_component:
                # any states to import?
                if comp.has_variables(state=True):
                    need_time_factor = True
                    break

                # Any references made to external state variables
                for ext_var in comp.variables(deep=True):
                    for var in ext_var.refs_to(state_refs=False):
                        if var.is_state():
                            need_time_factor = True
                            break
                    if need_time_factor:
                        break
                if need_time_factor:
                    break

            # Get conversion factor for time variable, raise error if can't
            if need_time_factor:
                ext_unit = myokit.units.dimensionless
                self_unit = myokit.units.dimensionless
                ext_var = ext_model.time()
                if ext_var is not None:
                    ext_unit = ext_var.unit(myokit.UNIT_STRICT)
                self_var = self.time()
                if self_var is not None:
                    self_unit = self_var.unit(myokit.UNIT_STRICT)
                if not myokit.Unit.close(ext_unit, self_unit):
                    try:
                        time_factor = myokit.Unit.conversion_factor(
                            ext_unit, self_unit)
                    except myokit.IncompatibleUnitError as e:
                        raise myokit.VariableMappingError(
                            'Unable to map time variables due to unit'
                            ' mismatch: ' + str(e))

        # Clone component pt 1: create, meta data, empty variables
        new_component = []
        for i, comp in enumerate(external_component):
            new_component.append(comp._clone1(self, new_name[i]))

            for var in comp.variables(state=True):
                # Clone states
                # TODO: Not sure why clone() code doesn't do this?
                new_component[i].get(var.qname(comp)).promote(
                    var.state_value())
            # Now we can add variable to var_map if needed
            for var in map_to_clone[i]:
                var_map[var] = new_component[i].get(var.qname(comp))

        # Create mapping of old var references to new references
        # This is a mapping from Name(var) and Derivative(Name(var)) objects
        # to new myokit.Expressions referencing the target model's variables
        lhs_map = {}

        # Start with all variables (including nested variables) inside the
        # imported component.
        for i, comp in enumerate(external_component):
            for ext_var in comp.variables(deep=True):
                self_var = new_component[i].get(ext_var.qname(comp))
                lhs_map[myokit.Name(ext_var)] = myokit.Name(self_var)
                if ext_var.is_state():
                    lhs_map[myokit.Derivative(myokit.Name(ext_var))] = \
                        myokit.Derivative(myokit.Name(self_var))

        # Next, add all entries in the var_map. If unit conversion is enabled,
        # this may include the addition of unit conversion factors

        for ext_var, self_var in var_map.items():
            # Substitute in either a reference to self_var, or an expression
            # that converts self_var to the units ext_var's equation expects.
            ex = myokit.Name(self_var)
            factor = factors.get(ext_var, None)
            if factor is not None:
                ex = myokit.Multiply(ex, myokit.Number(factor))
            lhs_map[myokit.Name(ext_var)] = ex

            # Repeat, but for expressions of the form dot(x)
            # These should also take conversion of time units into account
            if ext_var.is_state():
                ex = myokit.Derivative(myokit.Name(self_var))
                if time_factor is not None:
                    if factor is None:
                        factor = time_factor
                    else:
                        factor *= time_factor
                        if factor == myokit.Quantity(1):
                            factor = None
                if factor is not None:
                    ex = myokit.Multiply(ex, myokit.Number(factor))
                lhs_map[myokit.Derivative(myokit.Name(ext_var))] = ex

        # Clone component/variable contents (equations, references)
        for i, comp in enumerate(external_component):
            comp._clone2(new_component[i], lhs_map, var_map)

        # Time unit conversion? Then update all derivatives.
        if time_factor is not None:
            for comp in new_component:
                for var in comp.variables(state=True):
                    rhs = var.rhs()
                    if rhs is not None:
                        var.set_rhs(
                            myokit.Multiply(rhs, myokit.Number(time_factor)))

    def inits(self):
        """
        Returns an iterator over the ``Equation`` objects defining this model's
        current state.
        """
        def StateDefIterator(model):
            for k, var in enumerate(model._state):
                yield Equation(
                    myokit.Name(var), myokit.Number(self._current_state[k]))
        return StateDefIterator(self)

    def is_similar(self, other, check_unames=False):
        """
        Returns ``True`` if this model has the same code as the ``other``
        model.

        If ``check_unames`` is set to ``True``, the method also checks if the
        defined unique names and unique name prefixes are the same.
        """
        if self is other:
            return True
        if not isinstance(other, Model):
            return False
        if self._reserved_unames != other._reserved_unames:
            return False
        if self._reserved_uname_prefixes != other._reserved_uname_prefixes:
            return False
        return self.code() == other.code()

    def is_valid(self):
        """
        Returns ``True`` if this model is valid, ``False`` if it is invalid and
        ``None`` if the validation status has not been determined with
        :meth:`validate()`.

        Valid models may still have one or more warnings.
        """
        return self._valid

    def item_at_text_position(self, line, char):
        """
        Finds the component, variable, or expression at the position
        ``(line, char)``, and returns a tuple ``(token, object)`` with a
        parser token and the found object, or ``None`` if nothing is found.

        Both ``line`` and ``char`` should be given as integers. The first line
        is line 1, while the first character is char 0.
        """
        if line not in self._tokens:
            return None
            # This will cause problems for multi-line strings...
            # (But at the moment, these don't register tokens anyway)

        tokens = self._tokens[line]
        t = None
        for c in sorted(tokens, reverse=True):
            if c <= char:
                t = tokens[c]
                break

        if t is not None:
            # Test if position is in token
            if char >= t[0][3] + len(t[0][1]):
                t = None

        return t

    def __iter__(self):
        return iter(self._components.values())

    def label(self, label):
        """
        Returns the variable with the given ``label``, or ``None`` if no such
        variable can be found.
        """
        return self._labels.get(label, None)

    def labels(self):
        """
        Returns an iterator over all (label : variable) mappings in this model.
        """
        # New dict allows removing labels using this iterator
        return dict(self._labels).items()

    def labelx(self, label):
        """
        Returns the variable with the label ``label``, raising a
        :class:`myokit.IncompatibleModelError` if no such variable is found.

        See :meth:`Model.label()`.
        """
        try:
            return self._labels[label]
        except KeyError:
            raise myokit.IncompatibleModelError(
                self.name(),
                'No variable found with label "' + str(label) + '".')

    def __len__(self):
        return len(self._components)

    def load_state(self, filename):
        """
        Sets the model state using data from a file formatted in any style
        accepted by :func:`myokit.parse_state`.
        """
        self.set_state(myokit.load_state(filename, self))

    def map_component_dependencies(
            self, omit_states=True, omit_constants=False):
        """
        Scans all equations and creates a map of inter-component dependencies.

        The result is an ordered dictionary with the following structure::

            {
                comp1 : [dep1, dep2, dep3, ...],
                comp2 : [dep1, dep2, dep3, ...],
                ...
            }

        where ``comp1, comp2, ...`` are Components and ``dep1, dep2, ...`` are
        the components they depend upon.

        Only direct dependencies are listed: If ``A`` depends on ``B`` and
        ``B`` depends on ``C`` then the returned value for ``A`` is ``[B]``,
        not ``[B,C]``.

        By default, dependencies on state variables' current values are
        omitted. This behaviour can be changed by setting ``omit_states`` to
        ``False``.

        To omit all dependencies on constants, set ``omit_constants`` to
        ``True``.
        """
        # Map shallow dependencies
        shallow = self.map_shallow_dependencies(
            omit_states=omit_states, omit_constants=omit_constants)

        # Create output structure
        # Use ordered dict to get consistent output
        deps = OrderedDict()
        for comp in self.components():
            deps[comp] = set()

        # Gather dependencies per component
        for lhs, dps in shallow.items():
            c1 = lhs.var().parent(Component)
            for dep in dps:
                c2 = dep.var().parent(Component)
                if c2 != c1:
                    deps[c1].add(c2)

        # Convert sets to sorted lists
        for comp, dps in deps.items():
            deps[comp] = list(dps)
            deps[comp].sort(key=lambda x: x.name())

        # Return
        return deps

    def map_component_io(
            self,
            omit_states=False,
            omit_derivatives=False,
            omit_constants=False,
            rl_states=None):
        """
        Scans all equations and creates a list of input and output variables
        for each component.

        *Input variables* are taken to be any foreign variables the component
        needs to perform its calculations, plus the current values of its own
        state variables if it needs them.

        *Output variables* are taken to be any values calculated by this
        component but used outside it. This includes the derivatives of the
        state variables it calculates. State variables are never given as
        outputs, as it is assumed these are updated by an ODE solver.

        The output can be customized using the following arguments:

        ``omit_states``
            Set to ``True`` to omit state values from the input lists. This can
            be useful in cases where the state is stored in a vector.
        ``omit_derivatives``
            Set to ``True`` to omit derivatives from the input and output
            lists. This can be useful if derivatives are stored in a vector.
        ``omit_constants``
            Set to ``True`` to omit constants from the input and output lists.
            This can be useful if constants are stored globally, e.g. as
            C macros.
        ``rl_states``
            A map ``{state_variable : {inf_variable, tau_variable}`` can be
            passed in to enable mapping for Rush-Larsen schemes. In this case,
            all variables listed as ``inf`` or ``tau_variable`` will be
            included in component output lists, and the derivatives of each
            ``state_variable`` in the mapping will only be added to the output
            list if there are other variables that depend on it.

        The result is a tuple containing two ``OrderedDict`` objects, each of
        the following structure::

            {
                comp1: [lhs1, lhs2, ...],
                comp2: [lhs1, lhs2, ...],
                ...
            }

        The first dict contains the inputs to every component, the second dict
        contains every components output values. The values in the lists are
        :class:``LhsExpression`` objects referring to either a variable or its
        derivative.
        """
        # Map shallow dependencies
        shallow = self.map_shallow_dependencies(
            omit_states=omit_states, omit_constants=omit_constants)

        # Create output structure
        # Using OrderedDict to get consistent results when generating code from
        # this output
        di = OrderedDict()  # Inputs to each component (dependencies)
        do = OrderedDict()  # Outputs from each component
        for comp in self.components():
            di[comp] = set()
            do[comp] = set()

        # Process Rush-Larsen info
        if rl_states:
            # Add infs and taus to the component output lists
            for inf, tau in rl_states.values():
                if not (omit_constants and inf.is_constant()):
                    do[inf.parent(Component)].add(inf.lhs())
                if not (omit_constants and tau.is_constant()):
                    do[tau.parent(Component)].add(tau.lhs())
        else:
            rl_states = {}

        # Add own derivatives, even if not explicitly used
        if not omit_derivatives:
            for var in self.states():
                # Don't add RL-state derivatives (they might still be added
                # below, if some variables depend on them)
                if var not in rl_states:
                    do[var.parent(Component)].add(var.lhs())

        # Add inputs and outputs
        for user, deps in shallow.items():
            c_user = user.var().parent(Component)
            for usee in deps:
                c_usee = usee.var().parent(Component)
                is_deriv = usee.is_derivative()
                is_state = (not is_deriv) and usee.var().is_state()

                # States should be inputs, regardless of their component
                # States are never outputs (the ODE solver sets them)
                if is_state:
                    if not omit_states:
                        di[c_user].add(usee)

                # All others? Check parents
                elif c_user != c_usee and not (is_deriv and omit_derivatives):
                    di[c_user].add(usee)
                    do[c_usee].add(usee)

        # Convert sets to sorted lists
        def sortkey(lhs):
            key = lhs.var().uname()
            return '_' + key if lhs.is_derivative() else key

        for comp in self.components():
            di[comp] = list(di[comp])
            do[comp] = list(do[comp])
            di[comp].sort(key=sortkey)
            do[comp].sort(key=sortkey)

        # Return
        return (di, do)

    def map_deep_dependencies(
            self, collapse=False, omit_states=True, filter_encompassed=False):
        """
        Scans the list of equations stored in this model and creates a map
        relating each equation's left hand side to a list of other
        :class:`LhsExpressions <LhsExpression>` it depends on, either directly
        or through an intermediate variable.

        The method :func:`map_shallow_dependencies` performs a similar check,
        but only returns *direct* dependencies. This method expands the full
        dependency tree.

        The result is an ``OrderedDict`` with the following structure::

          {
            lhs1 : [dep1, dep2, dep3, ...],
            ...
          }

        where ``lhs1`` is a :class:`LhsExpression` and ``dep1``, ``dep2`` and
        ``dep3`` are the :class:`LhsExpression` objects it depends upon.

        If the system is not solvable: that is, if it contains cyclical
        references, a :class:`myokit.IntegrityError` is raised.

        If the optional parameter ``collapse`` is set to ``True``
        nested variables will not be listed separatly. Instead, their
        dependencies will be added to the dependency lists of their parents.

        By default, dependencies on state variables' current values are
        omitted. This behaviour can be changed by setting ``omit_states`` to
        ``False``.

        In case of a dependency such as::

            a = f(b)
            b = g(c)

        the set returned for ``a`` will include ``b`` and ``c``. So while ``a``
        here depends on both ``b`` and ``c``, ``b``'s sole dependency on ``c``
        means ``a`` can be calculated if just ``c`` is known. To filter out the
        dependency on ``b``, set ``filter_encompassed`` to ``True``. Note that
        this will also filter out all dependencies on constants, since a
        constant's dependencies (an empty set) can be said to be included in
        all other sets.
        """
        # Get map of shallow dependencies
        shallow = self.map_shallow_dependencies(omit_states=omit_states)

        # Create map of deep dependencies
        deep = {}

        # Store set of lhs's found by following equations
        equations = dict(
            zip(shallow.keys(), [x.rhs() for x in shallow.keys()]))

        # Add state variables
        if not omit_states:
            for var in self.variables():
                if var.is_state():
                    equations[myokit.Name(var)] = myokit.Number(0)
        unused = set(equations.keys())

        # Tree searching function
        def follow(lhs, deps=None, trail=None):
            if deps is None:
                deps = set()
            if trail is None:
                trail = []

            # Followed already? Return stored result
            if lhs in deep:
                for dep in deep[lhs]:
                    deps.add(dep)
                return deps

            # Cycle check
            if lhs in trail:
                trail = trail[trail.index(lhs):]
                trail.append(lhs)
                raise myokit.CyclicalDependencyError(trail)

            # Not in shallow? Error in dict
            if lhs not in shallow:
                raise RuntimeError(  # pragma: no cover
                    'Variable ' + str(lhs._value) + ' not found in dict of'
                    ' shallow dependencies')

            # Add this var as a dependency
            deps.add(lhs)

            # Follow child dependencies
            trail2 = trail + [lhs]
            for kid in shallow[lhs]:
                follow(kid, deps, trail2)
                if kid in unused:
                    unused.remove(kid)
            return deps

        # Follow every lhs (checks for cycles)
        for lhs in equations:
            deep[lhs] = follow(lhs)
        for lhs in equations:
            deep[lhs].remove(lhs)

        # Collapse nesting
        if collapse:
            nested = []
            for x, y in deep.items():
                var = x.var()
                if var.is_nested():
                    nested.append(x)
                    while isinstance(var.parent(), Variable):
                        var = var.parent()
                    var = deep[var.lhs()]
                    for rhs in y:
                        var.add(rhs)
            for x in nested:
                for y in deep.values():
                    if x in y:
                        y.remove(x)
            for x in nested:
                del deep[x]

        # Filter encompassed variables
        if filter_encompassed:
            for x, xdeps in deep.items():
                tofilter = []
                for y in xdeps:
                    if y.is_state_value():
                        # Don't filter out state values
                        continue
                    ydeps = deep[y]
                    if ydeps <= xdeps:  # <= means is_subset or equal
                        tofilter.append(y)
                for y in tofilter:
                    xdeps.remove(y)

        # Return
        return deep

    def map_shallow_dependencies(
            self, collapse=False, omit_states=True, omit_constants=False):
        """
        Scans the list of equations stored in this model and creates a map
        relating each equation's left hand side to a list of other
        :class:`LhsExpressions <LhsExpression>` it depends on directly.

        In contrast to the method :func:`map_deep_dependencies`, that performs
        a deep search for all nested dependencies, this method only returns
        *direct* dependencies. I.E. LhsExpressions named specifically in the
        equation's right hand side.

        The result is an ``OrderedDict`` with the following structure::

          {
            lhs1 : [dep1, dep2, dep3, ...],
            ...
          }

        where ``lhs1`` is a :class:`LhsExpression` and ``dep1``, ``dep2`` and
        ``dep3`` are the :class:`LhsExpression` objects it depends upon.

        In special cases, the obtained result can differ from the mathematical
        concept of a dependency: if ``x = 0 * y`` the function will return a
        dependency of ``x`` on ``y``. Similarly, for ``x = if(cond, a, b)`` the
        function will report a dependency of ``x`` on ``cond``, ``a`` and
        ``b``.

        If the optional parameter ``collapse`` is set to ``True``
        nested variables will not be listed separatly. Instead, their
        dependencies will be added to the dependency lists of their parents.

        By default, dependencies on state variables' current values are
        omitted. This behaviour can be changed by setting ``omit_states`` to
        ``False``. Dependencies on constants are included by default, but this
        can be changed by setting ``omit_constants`` to ``True``.
        """
        # Find dependencies for every stored equation
        out = {}
        inc = not omit_states
        const = False if omit_constants else None
        for eq in self.equations(deep=True, const=const):
            out[eq.lhs] = deps = set()
            # Bound variable has zero dependencies
            if eq.lhs.var().is_bound():
                continue
            # Find references
            for dep in eq.rhs.references():
                if omit_states and dep.is_state_value():
                    continue
                elif omit_constants and dep.var().is_constant():
                    continue
                else:
                    deps.add(dep)

        # Collapse nested variables
        if collapse:
            nested = []
            for x, y in out.items():
                var = x.var()
                if var.is_nested():
                    nested.append(x)
                    while isinstance(var.parent(), Variable):
                        var = var.parent()
                    var = out[var.lhs()]
                    for rhs in y:
                        var.add(rhs)
            for x in nested:
                for y in out.values():
                    if x in y:
                        y.remove(x)
            for x in nested:
                del out[x]

        # Add empty mappings for state variables
        if inc:
            # State vars are never nested, deep search not needed
            for var in self.states():
                out[myokit.Name(var)] = set()

        # Return
        return out

    def map_to_state(self, state):
        """
        This utility function accepts a number of different input types and
        returns a list of floats in the same order as the model's state
        variables.

        The following types of input are meaningfully handled:

         - A dictionary mapping state variable names or objects to floats
         - A dictionary mapping state variable names or objects to lists. The
           last value in every list will be used. This allows the dictionary
           returned by :meth:`myokit.Simulation.run()` to be used directly.
         - A formatted string declaring each variable's value using the syntax
           ``component.var_name = 1.234`` or simply containing a comma or space
           delimited list of floats.
         - A list of scalars. In this case, the list length will be
           checked and all values converted to float. No re-ordering takes
           place.

        """
        n = self.count_states()
        if isinstance(state, basestring):
            # String given. Parse into name:float map or list
            state = myokit.parse_state(state)
        if isinstance(state, dict):
            # Dictionary (sub)types. Parse into list of floats
            ini = [0] * n
            for k, v in enumerate(self.states()):
                if v in state:
                    value = state[v]
                elif v.qname() in state:
                    value = state[v.qname()]
                else:
                    raise ValueError(
                        'Missing state variable: ' + v.qname())
                # List or similar? Then use last value
                try:
                    ini[k] = float(value[-1])
                except TypeError:
                    ini[k] = float(value)
            state = ini
        # From this point on, assume list
        if len(state) != n:
            raise ValueError(
                'Wrong number of list entries, expecting (' + str(n)
                + ') values, got (' + str(len(state)) + ').')
        # Convert all to float, create new list, return
        return [float(x) for x in state]

    def name(self):
        """
        Returns the model meta property ``name``, or ``None`` if it isn't set.
        """
        try:
            return self.meta['name']
        except KeyError:
            return None

    def prepare_bindings(self, labels):
        """
        Takes a mapping of binding labels to internal references as input and
        returns a mapping of variables to internal references. All variables
        appearing in the map will have their right hand side set to zero. All
        bindings not mapped to any internal reference will be deleted.

        The argument ``mapping`` should take the form::

            labels = {
                'binding_label_1' : internal_name_1,
                'binding_label_2' : internal_name_2,
                ...
                }

        The returned dictionary will have the form::

            variables = {
                variable_x : internal_name_1,
                variable_y : internal_name_2,
                ...
                }

        Unsupported bindings (i.e. bindings not appearing in ``labels``) will
        be ignored.
        """
        unused = []
        variables = {}
        for label, var in self._bindings.items():
            try:
                variables[var] = labels[label]
            except KeyError:
                unused.append(var)
                continue
            var.set_rhs(0)
        for var in unused:
            var.set_binding(None)
        return variables

    def __reduce__(self):
        """
        Pickles the model.

        See: https://docs.python.org/3/library/pickle.html#object.__reduce__
        """
        return (
            myokit.parse_model,
            (self.code(), ),
            (
                self._reserved_unames,
                self._reserved_uname_prefixes,
            ),
        )

    def _register_binding(self, label, variable=None):
        """
        Used by variables to inform the model of the addition or removal of a
        binding label to/from a variable.
        """
        if variable is None:
            # Remove binding
            del self._bindings[label]
        else:
            # Check for existing binding
            if label in self._bindings:
                raise myokit.InvalidBindingError(
                    'Duplicate binding: <'
                    + str(self._bindings[label].qname())
                    + '> is already bound to "' + str(label) + '".')
            # Check for existing label
            if label in self._labels:
                raise myokit.InvalidBindingError(
                    'Duplicate binding: Binding "' + str(label)
                    + '" is already in use as a label for <'
                    + str(self._labels[label].qname()) + '>.')
            # Add binding
            self._bindings[label] = variable

    def _register_label(self, label, variable=None):
        """
        Used by variables to inform the model of the addition or removal of a
        label to/from a variable.
        """
        if variable is None:
            # Remove label
            del self._labels[label]
        else:
            # Check for existing label
            if label in self._labels:
                raise myokit.InvalidLabelError(
                    'Duplicate label: "' + str(label)
                    + '" is already in use as a label for <'
                    + str(self._labels[label].qname()) + '>.')
            # Check for existing binding
            if label in self._bindings:
                raise myokit.InvalidLabelError(
                    'Duplicate label: Label "' + str(label)
                    + '" is already in use as a binding for <'
                    + str(self._bindings[label].qname()) + '>.')
            # Add label
            self._labels[label] = variable

    def reorder_state(self, order):
        """
        Changes the order of this model's state variables. The argument
        ``order`` must be a list of state variables or their qnames.

        This method does not affect the model's validation status.
        """
        n = len(self._state)
        if len(order) != n:
            raise ValueError(
                'The given list must contain the same number of entries as'
                ' there are state variables in this model.')
        state = []
        current = []
        for v in order:
            v = self.get(v)
            if not v.is_state():
                raise ValueError(
                    'The entries of ``order`` must all be state variables or'
                    ' state variable qnames.')
            if v in state:
                raise ValueError(
                    'Duplicate entry in order specification: "'
                    + str(v.qname()) + '".')
            state.append(v)
            current.append(self._current_state[v._indice])
        self._state = state
        self._current_state = current
        for k, v in enumerate(state):
            v._indice = k

    def remove_component(self, component):
        """
        Removes a component from the model.

        This will reset the model's validation status.
        """
        try:
            # Get component object
            if not isinstance(component, Component):
                component = self._components[component]
            # Tell component it's being deleted
            component._delete()
            # Delete component from list
            del self._components[component.qname()]
        finally:
            self._valid = None

    def remove_derivative_references(self):
        """
        Scans this model's RHS for any references to derivatives and removes
        them by introducing a new variable.

        For example, given a (partial) model::

            [ernie]
            dot(x) = (12 - x) / 5

            [bert]
            y = 1 + dot(x)

        this method will update the model to::

            [ernie]
            dot_x = (12 - x) / 5
            dot(x) = dot_x

            [bert]
            y = 1 + dot_x

        """
        # Get time unit
        time = self.time()
        if time is not None:
            time_unit = time.unit()

        # Scan all states
        for state in self._state:

            # Search for references to dot(state)
            refs = list(state.refs_by())

            if refs:
                # If found, add a new variable to represent dot(state)
                var = state.parent().add_variable_allow_renaming(
                    'dot_' + state.name())
                var.set_rhs(state.rhs())

                # Set unit for new variable
                if state.unit() is not None and time_unit is not None:
                    var.set_unit(state.unit() / time_unit)

                # Move nested variables
                for child in list(state.variables()):
                    state.move_variable(child, var)

                # Update state RHS
                state.set_rhs(myokit.Name(var))

                # Update all referring equations
                subst = {state.lhs(): var.lhs()}
                for ref in refs:
                    ref.set_rhs(ref.rhs().clone(subst=subst))

    def __repr__(self):
        """
        Returns a representation of this model in the form
        ``<Model(model_name)>``.
        """
        try:
            return '<Model(' + self.meta['name'] + ')>'
        except KeyError:
            return '<Unnamed Model>'

    def reserve_unique_names(self, *unames):
        """
        Reserves one or more names that won't be used in unique names (unames).

        This function can be used to add keywords to a model before exporting.
        After reserving one or more keywords, use :meth:`create_unique_names`
        to reset the model's unames.

        Adding new names does _not_ clear the previously reserved names.
        """
        for name in unames:
            self._reserved_unames.add(str(name))

    def reserve_unique_name_prefix(self, prefix, prepend):
        """
        Indicates a ``prefix`` that won't be used in unique names (unames).

        When creating a unique name, any variable starting with ``prefix`` will
        be prepended with the string ``prepend``.
        """
        prefix = str(prefix)
        prepend = str(prepend)
        if prefix == '':
            raise ValueError('Unique name prefix cannot be empty.')
        if prepend == '':
            raise ValueError('String to prepend cannot be empty.')
        if prepend.startswith(prefix):
            raise ValueError('String to prepend cannot start with prefix.')
        self._reserved_uname_prefixes[prefix] = prepend

    def _reset_indices(self):
        """
        Resets the indices of this model's state variables.
        """
        for k, v in enumerate(self._state):
            v._indice = k

    def _reset_validation(self):
        """
        Will reset the model's validation status to not validated.
        """
        self._valid = None

    def _resolve(self, name):
        """ See :meth:`VarProvider._resolve(). """
        return self.get(name)

    def resolve_interdependent_components(self):
        """
        Checks if the model contains components that each depend on the other.
        If so, variables from these components will be moved to a new component
        called "remaining" until the issue is resolved.
        """
        equations = self.solvable_order()
        remaining = equations['*remaining*']
        if len(remaining) < 1:
            # Model is already okay
            return

        # Get name for new component
        comp = 'remaining'
        if comp in self._components:
            comp_root = comp + '_'
            i = 1
            while comp in self._components:
                i += 1
                comp = comp_root + str(i)

        # Create new component (resets validation status)
        comp = self.add_component(comp)

        # Move variables to new component
        for eq in remaining:
            var = eq.lhs.var()
            var.parent().move_variable(var, comp, var.uname())
        # Done!

    def save_state(self, filename):
        """
        Saves the model state to a file.
        """
        return myokit.save_state(filename, self.state(), self)

    def set_name(self, name=None):
        """
        Changes the value of the meta-property "name".
        """
        if name is None:
            try:
                del self.meta['name']
            except KeyError:
                pass
        else:
            self.meta['name'] = str(name)

    def __setstate__(self, state):
        """
        Called after unpickling.

        See: https://docs.python.org/3/library/pickle.html#object.__setstate__
        """
        self._reserved_unames = state[0]
        self._reserved_uname_prefixes = state[1]

    def set_state(self, state):
        """
        Changes this model's state. Accepts any type of input handled by
        :meth:`map_to_state`.
        """
        self._current_state = self.map_to_state(state)

    def set_value(self, qname, value):
        """
        Changes a variable's defining expression to the given number or
        :class:`myokit.Expression`.

        For state variables, this updates the expression for their derivative.
        For all other variables, the expression for their value is updated.

        This will reset the model's validation status.
        """
        self.get(qname).set_rhs(value)

    def show_evaluation_of(self, var):
        """
        Returns a string representing the evaluation of a single variable.

        The variable's equation and value are displayed, along with the value
        and formula of any nested variables and the values of all dependencies.
        """
        def format_float(number):
            s = str(number)
            if len(s) < 10:
                return s
            return '%0.17e' % number

        # Add basic info
        spacer = '-' * 60
        var, out = self._var_info(var, spacer)

        # Add initial value
        rhs = var.rhs()
        if var.is_state():
            out.append('Initial value = ' + str(var.state_value()))
            out.append(spacer)
        varname = var.lhs().code()

        # Add references
        deps = list(rhs.references())
        deps.sort(key=lambda x: x.code())
        if deps:
            n = max([len(x.code()) for x in deps])
            for dep in deps:
                out.append(
                    dep.code() + ' ' * (n - len(dep.code())) + ' = '
                    + format_float(dep.eval()))
            out.append(spacer)

        # Add nested variables
        if len(var) > 0:
            n = max(len(x.name()) for x in var.variables(deep=True))
            for tmp in var.variables(deep=True):
                out.append(
                    tmp.name() + ' ' * (n - len(tmp.name())) + ' = '
                    + tmp.rhs().code())
                out.append(' ' * n + ' = ' + format_float(tmp.rhs().eval()))
            out.append(spacer)

        # Add final value
        out.append(varname + ' = ' + rhs.code())
        out.append(' ' * len(varname) + ' = ' + format_float(rhs.eval()))
        return '\n'.join(out)

    def show_expressions_for(self, var):
        """
        Returns a string containing the expressions needed to evaluate the
        given variable from the state variables.
        """
        spacer = '-' * 60
        var, out = self._var_info(var, spacer)
        eqs, args = self.expressions_for(var)
        if args:
            out.append(str(var) + ' is a function of:')
            for arg in args:
                out.append('  ' + str(arg))
            out.append(spacer)
        out.append('Expressions for ' + str(var) + ':')
        for eq in eqs:
            out.append('  ' + str(eq))
        return '\n'.join(out)

    def show_line_of(self, var, raw=False):
        """
        Returns a string containing the type of variable ``var`` is and the
        line it was defined on.

        If ``raw`` is set to ``True`` the method returns an integer with the
        line number, or ``None`` if no line number information is known (i.e.
        if this model wasn't created by parsing).
        """
        if raw:
            return int(var._token[2]) if var._token is not None else None

        var, out = self._var_info(var)
        if var._token is not None:
            out.append('Defined on line ' + str(var._token[2]))
        return '\n'.join(out)

    def solvable_order(self):
        """
        Returns all equations in a solvable order. The resulting output has the
        following structure::

          OrderedDict {
            'comp1' : EquationList([eq1, eq2, eq3, ...]),
            'comp2' : EquationList([eq1, eq2, eq3, ...]),
            ...,
            '*remaining*' : EquationList([eq1, eq2, eq3])
          }

        The ``OrderedDict`` contains each component's name as a key and maps it
        to a list of equations that can be solved for this component, stored in
        an :class:``EquationList`` object which extends the :class:`list` type
        with a number of special iterators.

        The order of the components is such that the components with the fewest
        dependencies are listed first, in an effort to ensure as many equations
        as possible can be solved on a per-component basis.

        The final entry in the ``OrderedDict`` is a list of all remaining
        equations that could not be solved on a per-component basis. For models
        that contain fully separable components (that is, if the model contains
        only components that depend on each other non-cyclically) this list
        will be empty.
        """
        # TODO: Cache this!

        # Get components in solvable order
        # Any components with interdependencies will _not_ be added to this
        # list.
        solvable_comps = []
        cdeps = self.map_component_dependencies()
        while True:
            # Find all components that can be solved (and order alphabetically)
            newly_solvable = []
            for comp, deps in sorted(cdeps.items(), key=lambda c: c[0].name()):
                if len(deps) == 0:
                    solvable_comps.append(comp)
                    newly_solvable.append(comp)

            if len(newly_solvable) == 0:
                # No more solvable components? Then stop.
                # Note that cdeps will not be empty at this point if there are
                # components with interdependencies. This is ok!
                break

            # Remove the components that are now solvable from everybody's
            # dependency lists
            for comp in newly_solvable:
                for deps in cdeps.values():
                    if comp in deps:
                        deps.remove(comp)

            # Remove the solvable components from the component dependency list
            for comp in newly_solvable:
                del cdeps[comp]

        # At this point, we've created a list `solvable_comps`, that contains
        # all independent components, in a solvable order.
        # The components with interdependencies are not in `solvable_comps`,
        # but are listed in `cdeps`.

        # Create component output dict and todo list
        # Both are created here, so that their order will match
        # `solvable_comps`.
        out = OrderedDict()     # Final output dict (comp.name:EquationList)
        todo = OrderedDict()    # Todo dict (comp:{lhs: equation})

        # Add solvable components in the solvable order
        for comp in solvable_comps:
            out[comp.name()] = EquationList()
            todo[comp] = OrderedDict()
        del solvable_comps

        # Add interdependent components in any (consistent) order
        for comp in cdeps.keys():
            out[comp.name()] = EquationList()
            todo[comp] = OrderedDict()
        del cdeps

        # At this point, we have created an ordered dict `out` that contains
        # all components in solvable order, and maps them to (currently empty)
        # equation lists.
        # The next lines create a to-do list of equations that will need to be
        # added to `out`.

        # Populate component todo lists (and order alphabetically)
        for eq in sorted(self.equations(deep=True), key=lambda x: str(x)):
            comp = eq.lhs.var().parent(Component)
            todo[comp][eq.lhs] = eq

        # Get a map of shallow dependencies: {lhs: [lhs1, lhs2, lhs3, ...]}
        # Use this map like cmaps, by removing all 'solved' variables from the
        # lists, so that an lhs is solvable as soon as its dependency list is
        # empty.
        deps = self.map_shallow_dependencies()

        # To get nicer output, nested variables are grouped with their parent.
        # Note: This isn't necessary for solvability, but makes for much more
        # readable exported code.

        # The dict below maps nested variables to their defining equations
        # {var: eq}. When scanning or solvable equations, nested variables will
        # be added to this dict, and then kept until their parent is
        # encountered, at which point they'll be added to `out`.
        nested = OrderedDict()

        def add_nested_equations(eq_list, parent, done=None):
            """
            Recursively adds equations for all children of a given `parent` to
            the output `eq_list`.
            The list `done` is updated to contain all variables whose equation
            was added in this call.
            """
            if done is None:
                done = []
            for var, eq in nested.items():
                if var._parent == parent:
                    add_nested_equations(eq_list, var, done)
                    eq_list.append(eq)
                    done.append(var)
            return done

        def add_equation(eq_list, done, eq):
            """
            Adds the equation `eq` to the equation list `eq_list` or, if the
            equation is for a nested variable, stores it in the global dict
            `nested`.
            If a variable with children is encountered, all its children will
            be added to `eq_list` too.
            The list `done` is updated to contain all `lhs` expressions whose
            equation was added to `eq_list` in this call.
            """
            var = eq.lhs.var()
            if var.is_nested():
                # Nested variable: Store in `nested` to add to `eq_list` later
                nested[var] = eq

            else:

                # Non-nested variable
                # Add any descendants, and remove them from nested
                for kid in add_nested_equations(eq_list, var):
                    del nested[kid]
                # Add the variable itself
                eq_list.append(eq)

            # Mark this lhs as done
            done.append(eq.lhs)

        # Scan over all components
        for comp, eqs in todo.items():
            # For each component, add solvable equations to the `out` list and
            # remove them from `todo`
            eq_list = out[comp.name()]
            while True:
                # Add all equations that can be added
                newly_solvable = []
                for lhs, eq in eqs.items():
                    if len(deps[lhs]) == 0:
                        add_equation(eq_list, newly_solvable, eq)

                # Can't add any more? Then stop
                if len(newly_solvable) == 0:
                    break

                # Remove all added equations from todo list
                # Remove all dependencies on newly solved equations
                for lhs in newly_solvable:
                    # Remove from eqs (which is in `todo`)
                    del eqs[lhs]
                    # Remove lhs from dependency map
                    del deps[lhs]
                    # Remove dependency on lhs from dependency lists in map
                    for dps in deps.values():
                        if lhs in dps:
                            dps.remove(lhs)

        # Get remaining, unsolved equations as {lhs: eq} map.
        unsolved = OrderedDict()
        for comp, eqs in todo.items():
            for lhs, eq in eqs.items():
                unsolved[lhs] = eq
        del todo

        # Add remaining equations
        remaining = out['*remaining*'] = EquationList()
        while True:
            # Add all equations that can be added
            newly_solvable = []
            for lhs, eq in unsolved.items():
                if len(deps[lhs]) == 0:
                    add_equation(remaining, newly_solvable, eq)

            # Can't add any more? Then stop
            if len(newly_solvable) == 0:
                break

            # Remove all added equations from todo list (`unsolved`)
            # Remove all dependencies on newly solved equations
            for lhs in newly_solvable:
                del unsolved[lhs]
                # Remove lhs from dependency map
                del deps[lhs]
                # Remove dependency on lhs from dependency lists in map
                for dps in deps.values():
                    if lhs in dps:
                        dps.remove(lhs)

        # Any unsolved equations left? Then the equations can't be ordered!
        # In normal use, this should have been picked up already in validation.
        if unsolved:
            raise RuntimeError('Equation ordering failed.')

        # Return
        return out

    def state(self):
        """
        Returns the current state of the model as a list of floating point
        numbers.
        """
        return list(self._current_state)

    def states(self):
        """
        Returns an iterator over this model's state :class:`variable
        <myokit.Variable>` objects.
        """
        return iter(self._state)

    def suggest_variable(self, name):
        """
        Returns a tuple ``(found, suggested, msg)``.

        If the requested variable is found, only the ``found`` part of the
        tuple is set. If not, the second and third argument are set. Here
        ``suggested`` will take the form of a suggested variable with a similar
        name, while ``msg`` will be a suggested error message.
        """
        # Return variable or set error message
        name = str(name)
        if '.' not in name:

            # Attempt to Suggest component
            for c in self.components():
                for v in c.variables():
                    if v.name() == name:
                        return (
                            None, v, 'No component specified for: <' + name
                            + '>. Did you mean <' + v.qname() + '> ?'
                        )

            # No alternative component found
            msg = 'Unknown variable: <' + name + '>.'

        else:

            par, var = name.split('.', 1)

            if par not in self._components:
                msg = 'Unknown component: <' + par + '>.'
            else:
                try:
                    names = var.split('.')
                    var = self._components[par]
                    for nm in names:
                        var = var[nm]
                    return (var, None, None)
                except KeyError:
                    msg = 'Unknown variable: <' + name + '>.'

        # Suggest closest match
        qname = name
        d = 1 + name.rfind('.')
        if d > 0:
            name = name[d:]
        name_low = name.lower()
        qname_low = qname.lower()
        mn = 99999
        sg = None
        for v in self.variables(deep=True):
            n1 = v.name()
            n2 = v.qname()
            d = min(myokit.tools.lvsd(name, n1),
                    myokit.tools.lvsd(qname, n2),
                    myokit.tools.lvsd(name_low, n1.lower()),
                    myokit.tools.lvsd(qname_low, n2.lower()))
            if d < mn:
                mn = d
                sg = v

        if sg is not None:
            msg += ' Did you mean "' + sg.qname() + '"?'
            if sg.qname().lower() == qname_low:
                msg += ' (Case mismatch)'
            return (None, sg, msg)

        # At the moment, we're accepting almost everything, so no need to test
        # this line!
        return (None, None, msg)    # pragma: no cover

    def time(self):
        """
        Returns this model's time variable.

        The time variable is identified by it's binding to the external source
        "time". For a valid model, this method always returns a unique
        variable. If no time variable has been declared ``None`` is returned.
        """
        try:
            return self._bindings['time']
        except KeyError:
            return None

    def timex(self):
        """
        Returns this model's time variable, raising a
        :class:`myokit.IncompatibleModelError` if no time variable is found.

        See :meth:`Model.time()`.
        """
        try:
            return self._bindings['time']
        except KeyError:
            raise myokit.IncompatibleModelError(
                self.name(), 'No time variable found.')

    def time_unit(self, mode=myokit.UNIT_TOLERANT):
        """
        Returns the units used by this model's time variable.

        If no time unit is set and ``mode`` is ``myokit.UNIT_TOLERANT``
        (default), then ``None`` is returned. With ``mode`` set to
        ``myokit.UNIT_STRICT`` the returned value in this case is
        ``myokit.units.dimensionless``.
        """
        try:
            time = self._bindings['time']
        except KeyError:
            if mode == myokit.UNIT_STRICT:
                return myokit.units.dimensionless
            return None
        return time.unit(mode)

    def user_functions(self):
        """
        Returns a dictionary mapping this model's user function names to their
        :class:`Expression` objects.
        """
        # Names and expressions are immutable, so ok to return
        return dict(self._user_functions)

    def validate(self, remove_unused_variables=False):
        """
        Attempts to check model validity, raises errors if it isn't.

        Small issues (e.g. unused variables) will generate warnings, which
        can be retrieved using :meth:`Model.warnings()` or
        :meth:`Model.format_warnings()`. Any previously set warnings will be
        erased whenever `validate()` is run.

        If ``remove_unused_variables`` is set to True, any unused variables
        will be removed from this model during validation.
        """
        # Reset warnings
        self._warnings = []

        # Check time variable
        time = self.time()
        if time is None:
            self._valid = False
            raise myokit.MissingTimeVariableError()
        if time.binding() != 'time':    # pragma: no cover
            # Added cover pragma: This can only happen if there is a bug
            # somewhere!
            self._valid = False
            raise myokit.IntegrityError(
                'Invalid time variable set. Time variable must be bound to'
                ' external value "time".')

        # Validation of components, variables
        for c in self.components():
            if c._parent != self:   # pragma: no cover
                # Cover pragma: This can only happen if there's an API bug
                msg = 'Component parent doesn\'t match with enclosing model <'
                msg += c.name() + '>.'
                self._valid = False
                raise myokit.IntegrityError(msg)
            # Deep validation
            c.validate()

        # Test component mapping
        for n, c in self._components.items():
            if n != c.qname():  # pragma: no cover
                # Cover pragma: This can only happen if there's an API bug
                self._valid = False
                raise myokit.IntegrityError(
                    'Component called <' + c.qname() + '> found at index <'
                    + n + '>.')

        # Test current state values
        n = len(self._state)
        if n != len(self._current_state):   # pragma: no cover
            # Cover pragma: This can only happen if there's an API bug
            self._valid = False
            raise myokit.IntegrityError(
                'Current state values list must have same size as state'
                ' variables list.')

        # Find cycles, warn of unused variables
        self._validate_solvability(remove_unused_variables)

        # Create globally unique names
        self.create_unique_names()

        # Return
        self._valid = True

    def _validate_solvability(self, remove_unused_variables=False):
        """
        Tests if all values are used and checks for cycles.

        The method used is straightforward:

          1. All variables are marked as "unused".
          2. For every unused derivative, the dependencies are followed
             recursively, keeping track of the current trail.
          3. Visited variables are marked as used.
          4. If a visited variable occurs in the current trail, a cyclical
             dependency is found and an exception is raised.
          5. When all state variables have been visited, any variables not
             marked as used are unused. A warning is generated for each unused
             variable. Bound and labelled variables are always counted as
             "used".

        If the optional argument ``remove_unused_variables`` is set to true,
        any unused variables will be removed from the model.
        """
        # Mark all variables as unused
        for var in self.variables(deep=True):
            var._used = False

        # Define "following" function
        def follow(lhs, var, trail, mark_used=True):
            if lhs in trail:
                # Catch cycles
                i = trail.index(lhs)
                c = trail[i:]
                c.append(lhs)
                raise myokit.CyclicalDependencyError(c)
            if not var._used:
                trail.append(lhs)
                for d in var.rhs().references():
                    v = d.var()
                    if not v.is_state() and d.is_derivative:
                        follow(d, v, trail, mark_used)
                trail.pop()
                if mark_used:
                    var._used = True

        # Follow all state variables (unless already visited), all bound
        # variables and all used variables.
        used = [x for x in self._state]
        used += [x for x in self._bindings.values()]
        used += [x for x in self._labels.values()]

        # Check for cycles
        trail = []

        # Despite its "slow" is-in check, using a list for this purpose is
        # faster than using an OrderedDict. Tested this. It's probably because
        # the trail is usually quite short and hashing is slow.
        for var in used:
            lhs = var.lhs()
            trail = []
            follow(lhs, var, trail)

        # Check for unused variables
        to_remove = []
        for var in self.variables(deep=True):
            if not var._used:
                # Everything else counts as unused
                if remove_unused_variables:
                    # Option 1, delete unused variables.
                    to_remove.append(var)
                else:
                    # Option 2, warn about it.
                    self._warn(myokit.UnusedVariableError(var))
                    # In this case, the unused variables should also be checked
                    # for cyclical references!
                    lhs = var.lhs()
                    trail = []
                    follow(lhs, var, trail, False)

        # Remove unused variables (if enabled)
        for var in to_remove:
            # Unused variables may still depend on each other
            var.set_rhs(0)
        for var in to_remove:
            self._warn('Removing unused variable: <' + var.qname() + '>.')
            # If a nested set of variables is in to_remove, the parent may be
            # deleted before the kids, which will trigger a delete of the kids.
            # To avoid trying to delete things twice, check if the parent still
            # exists.
            if var._parent:
                var._parent.remove_variable(var, recursive=True)

        # Remove _used attributes
        for var in self.variables(deep=True):
            del (var._used)

    def value(self, qname):
        """
        Returns the value of a variable.
        """
        return self.get(qname).rhs().eval()

    def _var_info(self, var, spacer=None):
        """
        Gathers basic information about a variable. Returns a tuple (var, out)
        where var is the variable (this function will also accept strings and
        uses suggest_variable to find a match) and out is a list of strings
        where each entry is a line of the description.
        """
        out = []
        if not isinstance(var, ModelPart):
            var = self.suggest_variable(var)
            if var[0] is None:
                if var[1] is None:
                    raise Exception(var[2])
                var = var[1]
                out.append(
                    'Variable not found, assuming <' + var.qname() + '>.')
            else:
                var = var[0]
        if var.is_state():
            kind = 'State variable'
        elif var.is_constant():
            if var.rhs().is_literal():
                kind = 'Literal constant'
            else:
                kind = 'Calculated constant'
        else:
            kind = 'Intermediary variable'
        out.append('Showing: ' + var.qname() + '  (' + kind + ')')
        if spacer is not None:
            out.append(spacer)
        unit = var.unit()
        if unit is not None:
            out.append('in ' + str(unit))
            if spacer is not None:
                out.append(spacer)
        desc = var.meta.get('desc')
        if desc is not None:
            out.append('desc: ' + str(desc))
            if spacer is not None:
                out.append(spacer)
        return (var, out)

    def _warn(self, msg):
        """
        Appends a warning to this model's list.
        """
        self._warnings.append(msg)

    def warnings(self):
        """
        Returns a list containing the warnings generated in this model.
        """
        return self._warnings


class Component(VarOwner):
    """
    A model component, containing several :class:`variables <Variable>`.

    Components should not be created directly, but only via
    :meth:`Model.add_component()`.

    Variables can be accessed using the ``comp['var_name']`` syntax or through
    the iterator methods.

    Meta-data properties can be accessed via the property ``meta``, for example
    ``model.meta['key']= 'value'``.
    """

    def __init__(self, model, name):
        super(Component, self).__init__(model, name)
        self._alias_map = {}    # Maps variable names to other variables names

    def _clone1(self, model, new_name=None):
        """
        Performs the first part of component cloning: Clones this component's
        variables into the :class:`Model` given as ``model``, but doesn't set
        any references (such as in aliases or expressions.)
        """
        if new_name is None:
            new_name = self.name()
        component = model.add_component(new_name)
        self._clone_modelpart_data(component)
        for v in self.variables():
            v._clone1(component)
        return component

    def _clone2(self, component, lhs_map, alias_map):
        """
        Performs the second part of component cloning: Iterates over the
        variables in the new, incomplete :class:`Component` given as
        ``component`` and adds their expressions. Sets aliases etc.

        The argument ``lhs_map`` should be a dictionary mapping old
        :class:`LhsExpression` objects their equivalents in the new model.
        Similarly, ``alias_map`` should be a dictionary mapping aliased
        variables in the old model to their counterparts in the new model.
        """
        model = component.model()

        # Clone aliases
        for k, v in self._alias_map.items():
            component.add_alias(k, alias_map[v])

        # Clone variable equations
        for v in self.variables():
            v._clone2(component[v.name()], lhs_map)

    def add_alias(self, name, variable):
        """
        Adds an alias to this component: the alias ``name`` will be refer to
        the :class:`Variable` object given as ``variable``.

        Aliases can only be created for variables of other components.
        """
        name = check_name(name)
        if not isinstance(variable, myokit.Variable):
            raise myokit.IllegalAliasError(
                'Aliases can only be created for variables.')
        if not self.can_add_variable(name):
            raise myokit.DuplicateName(
                'The name <' + str(name) + '> is already in use within this'
                ' scope.')
        par = variable.parent()
        if type(par) != Component:
            raise myokit.IllegalAliasError(
                'Aliases can only be created for variables whose parent is a'
                ' Component.')
        if par == self:
            raise myokit.IllegalAliasError(
                'Cannot create an alias for variables in the same component.')
        self._alias_map[name] = variable

    def _delete(self):
        """
        Tells this component it's being deleted.
        """
        # Find all components that reference this one
        reffers = set()
        for var in self.variables():    # No need for deep!
            refs = var._refs_by.union(var._srefs_by)
            for ref in refs:
                c = ref.parent(Component)
                if c != self:
                    reffers.add(c)
        if reffers:
            raise myokit.IntegrityError(
                'Can not delete component <' + self.qname() + '>'
                ' it is used by components '
                + ' and '.join(['<' + c.qname() + '>' for c in reffers]))

        # No problems? Then delete all variables from component
        for var in self.variables():
            var._delete(recursive=True, ignore_siblings=True)

        # Delete links to parent
        super(Component, self)._delete()

    def alias(self, name):
        """
        Returns the :class:`Variable` referred to using the alias ``name``.
        """
        return self._alias_map[name]

    def alias_for(self, variable):
        """
        Returns an alias for the :class:`Variable` variable.

        Raises a ``KeyError`` if no such alias is found.
        """
        for alias, var in self._alias_map.items():
            if var == variable:
                return alias
        raise KeyError('No alias found for <' + variable.qname() + '>.')

    def _code(self, b, t):
        """
        Internal version of Component.code()
        """
        pre = t * TAB
        b.write(pre + '[' + self.name() + ']\n')

        # Append meta properties
        self._code_meta(b, t)

        # Append aliases
        for alias, var in sorted(self._alias_map.items()):
            b.write(pre + 'use ' + var.qname() + ' as ' + alias + '\n')

        # Append values
        for v in self.variables(sort=True):
            v._code(b, t)

        b.write(pre + '\n')

    def qname(self, hide=None):
        """
        Returns this component's ``qname``.

        A component's ``qname`` is simply its name. No model name is prefixed.
        """
        return self._name

    def has_alias(self, name):
        """
        Returns ``True`` if this :class:`Component` contains an alias with the
        given name.
        """
        return name in self._alias_map

    def has_alias_for(self, variable):
        """
        Returns ``True`` if this :class:`Component` has an alias for the given
        :class:`Variable`.
        """
        return variable in self._alias_map.values()

    def remove_alias(self, name):
        """
        Removes an alias from this :class:`Component`.
        """
        del self._alias_map[name]

    def remove_aliases_for(self, var):
        """
        Removes any alias for the given variable from this :class:`Component`.
        """
        todo = []
        for name, avar in self._alias_map.items():
            if avar == var:
                todo.append(name)
        for name in todo:
            del self._alias_map[name]

    def __repr__(self):
        """
        Returns a representation of this component.
        """
        return '<Component(' + self.qname() + ')>'

    def validate(self):
        """
        Attempts to check component validity, raises errors if it isn't.
        """
        m = self.model()
        if m is None:   # pragma: no cover
            # Cover pragma: Can only be reached through an API bug.
            raise myokit.IntegrityError(
                'No model found in hierarchy for <' + self.qname() + '>.')

        # Validate child variables
        for v in self.variables():
            if v._parent != self:   # pragma: no cover
                # Cover pragma: Can only be reached through an API bug
                raise myokit.IntegrityError(
                    'Child variable\'s parent does not match with actual'
                    ' parent: parent of <' + v.qname() + '> is set to <'
                    + str(v._parent.qname()) + '>, but the variable is'
                    ' stored in <' + str(self.qname()) + '>.')

            # Deep validation
            v.validate()


class Variable(VarOwner):
    """
    Represents a model variable.

    Variables should not be created directly, but only via
    :meth:`Component.add_variable()` or :meth:`Variable.add_variable()`.

    Each variable has a single defining equation. For state variables, this
    equation has a derivative on the left-hand side (lhs), for all other
    variables the lhs of the defining equation is simply the variable's name.

    Variables can be made into state variables using
    :meth:`Variable.promote()`.

    Variables can be made to represent an externally defined variable using
    :meth:`Variable.set_binding()`. In this case, the right hand side set for
    a variable will be used as an alternative in situations where the external
    input is not available.

    Meta-data properties can be accessed via the property ``meta``, for example
    ``model.meta['key']= 'value'``.
    """

    def __init__(self, parent, name):
        super(Variable, self).__init__(parent, name)

        # Indice, only set if this is a state variable
        self._indice = None

        # This variable's unit, if given, else dimensionless
        self._unit = None

        # This variable's label, if given
        self._label = None

        # This variable's binding label, if given
        self._binding = None

        # Used (created and deleted) by _validate_solvability()
        #   self._used
        # Cached return values for is_constant, etc
        # For internal use only!
        self._is_nested = isinstance(self._parent, Variable)
        self._is_bound = False
        self._is_constant = True
        self._is_intermediary = False
        self._is_literal = True
        self._is_state = False

        # Cached lists of references by and to
        # References are only counted for the variable's defining equation (IE
        # the expression returned by rhs()). References to values of state
        # variables are stored separately. Bound variables are treated as if
        # they were unbound.
        self._refs_by = set()   # Vars that refer to this var
        self._refs_to = set()   # Vars that this var refers to
        self._srefs_by = set()  # Vars that refer to this state var's value
        self._srefs_to = set()  # State var values that this var refers to

        # Left-hand side representation (name or dot)
        self._lhs = myokit.Name(self)

        # Right-hand side representation
        self._rhs = None

    def binding(self):
        """
        Returns this variable's binding label or ``None`` if no binding is set.
        """
        return self._binding

    def clamp(self, value=None):
        """
        Clamps this variable to its current value or the given ``value``.

        This will perform the following actions:

        - The model's RHS will be set to a literal, using
          ``var.set_rhs(var.eval())``.
        - If this is a state variable, it will be demoted.
        - Any child variables will be removed.

        """
        # Set value
        if value is None:
            value = self.state_value() if self._is_state else self._rhs.eval()
        else:
            value = float(value)

        # Demote states (will raise an error if can't)
        if self.is_state():
            self.demote()

        # Fix RHS (do this after demoting, which can raise an error)
        self.set_rhs(myokit.Number(value, self._unit))

        # Remove child variables (should never raise an error after clamping
        # the RHS).
        self.remove_child_variables()

    def _clone1(self, parent):
        """
        Performs step 1 of cloning this variable into the newly created
        :class:`Component` or :class:`Variable` given as ``parent``. Creates a
        variable and the hierarchy of nested variables, but doesn't fill in the
        details.
        """
        v = parent.add_variable(self.name())
        self._clone_modelpart_data(v)
        for k in self.variables():
            k._clone1(v)

    def _clone2(self, v, lhs_map):
        """
        Performs step 2 of cloning this variable into ``v``. Adds equations,
        bindings, unit etc.

        The argument ``lhs_map`` should be a dictionary mapping old
        :class:`LhsExpression` objects their equivalents in the new model.
        """
        # _indice is set by promoting (done by model)
        # _binding
        if self._binding:
            v.set_binding(self._binding)

        # _label
        if self._label:
            v.set_label(self._label)

        # _unit (Units are immutable, no need to clone)
        v._unit = self._unit

        # Cached values are updated automatically.
        # Cached references are set by set_rhs
        # Set RHS
        if self._rhs:
            v.set_rhs(self._rhs.clone(subst=lhs_map))

        # Clone child variables
        for k in self.variables():
            k._clone2(v[k.name()], lhs_map)

    def _code(self, b, t):
        """
        Create the code for this variable and any child variables.
        """
        # Create header line
        c = self.parent(Component)
        lhs = self._lhs.code(c) if self._lhs else 'UNNAMED'
        rhs = self._rhs.code(c) if self._rhs else 'UNDEFINED'
        head = lhs + ' = ' + rhs

        # Get description from meta data
        try:
            desc = self.meta['desc']
        except KeyError:
            desc = None

        # Add bind and description shortcuts
        omit = []
        unit = self._unit
        bind = self._binding
        label = self._label
        if len(head) < 40:
            if self._rhs and self._rhs.is_literal():
                # Append bind
                if bind:
                    text = head + ' bind ' + bind
                    if len(text) < 79:
                        head = text
                        bind = None
                # Append label
                if label:
                    text = head + ' label ' + label
                    if len(text) < 79:
                        head = text
                        label = None
            # Append desc
            if desc:
                text = head + ' : ' + desc
                if len(text) < 79 and '\n' not in desc and '\r' not in desc:
                    head = text
                    omit.append('desc')

        # Append header line
        pre = t * TAB
        eol = '\n'
        b.write(pre + head + eol)

        # Indent!
        t += 1
        pre = t * TAB

        # Append unit
        if unit is not None:
            b.write(pre + 'in ' + str(unit) + eol)

        # Append binding
        if bind:
            b.write(pre + 'bind ' + bind + eol)

        # Append label
        if label:
            b.write(pre + 'label ' + label + eol)

        # Append meta properties
        self._code_meta(b, t, ignore=omit)

        # Append nested variables
        for var in self.variables(sort=True):
            var._code(b, t)

    def convert_unit(self, new_unit, helpers=None):
        """
        Converts the units this variable is expressed in to ``new_unit``, and
        updates the RHS with an appropriate scaling factor.

        Unit conversion proceeds in the following steps:

        1. A scaling factor is determined (see below).
        2. The variable's RHS is multiplied by this factor
        3. For state variables, the current state value is also updated.
        4. All references to the variable in the model equations are divided
           by the scaling factor.
        5. If the time variable is updated, all derivative equations are
           updated.

        The scaling factor is determined using
        :meth:`myokit.Unit.conversion_factor(old_unit, new_unit, helpers)`,
        where ``old_unit`` is the current variable unit (as determined by
        ``variable.unit(myokit.UNIT_STRICT)``).

        For state variables, as with ordinary variables, the ``new_unit``
        should be the unit of the variable itself (and not of its time
        derivative).

        Arguments:

        ``new_unit``
            The new unit this variable should be in. Given either as a
            :class:`myokit.Unit` or as a string that can be converted to a unit
            using :class:`myokit.parse_unit(new_unit)`.
        ``helpers=None``
            An optional list of conversion factors, which the method will
            attempt to use if the new and old units are incompatible. Each
            factor should be specified as a :class:`myokit.Quantity` or
            something that can be converted to a Quantity e.g. a string
            ``1 [uF/cm^2]`` or a :class:`myokit.Number()`.

        Note that this method will assume the expression is currently in the
        unit returned by :meth:`Variable.unit()`. It will not check whether the
        current RHS expression evaluates to the correct units.

        Returns ``True`` if a unit conversion was performed, ``False`` if not.

        Raises a :class:`myokit.IncompatibleUnitError` if the units cannot be
        converted.'
        """
        # Check new unit
        if not isinstance(new_unit, myokit.Unit):
            new_unit = myokit.parse_unit(new_unit)

        # Get current unit
        old_unit = self.unit(myokit.UNIT_STRICT)

        # Check if units are equal
        if new_unit == old_unit:
            return False

        # Determine scaling factor (from old to new)
        fw = myokit.Unit.conversion_factor(old_unit, new_unit, helpers)
        fw = myokit.Number(fw)

        # Update the variable unit
        self.set_unit(new_unit)

        # Update the variable's definition
        self.set_rhs(myokit.Multiply(self.rhs(), fw))

        # For states, update the current/initial value
        if self._is_state:
            self.set_state_value(self.state_value() * float(fw))

        # Update all references to the variable
        old_ref = myokit.Name(self)
        new_ref = myokit.Divide(old_ref, fw)
        for var in list(self.refs_by(self._is_state)):
            var.set_rhs(var.rhs().clone(subst={old_ref: new_ref}))

        # For states, also update references to their derivatives
        if self._is_state:
            old_ref = myokit.Derivative(myokit.Name(self))
            new_ref = myokit.Divide(old_ref, fw)
            for var in list(self.refs_by(False)):
                var.set_rhs(var.rhs().clone(subst={old_ref: new_ref}))

        # For the time variable, update all state RHS's, and any references to
        # derivatives
        model = self.parent(Model)
        if self == model.time():
            for var in model.states():
                var.set_rhs(myokit.Divide(var.rhs(), fw))
                old_ref = myokit.Derivative(myokit.Name(var))
                new_ref = myokit.Multiply(old_ref, fw)
                for ref in list(var.refs_by(False)):
                    ref.set_rhs(ref.rhs().clone(subst={old_ref: new_ref}))

        return True

    def _delete(self, recursive=False, ignore_siblings=False):
        """
        Tells this variable that it's going to be deleted.

        Errors will be raised if other variables depend on this one, unless
        specified differently using the following arguments:

        ``recursive``
            If set to ``True``, no errors will be raised if children of this
            this variable depend on it, and all child variables will be deleted
            as well.
        ``ignore_siblings``
            If set to ``True``, no errors will be raised if sibilings of this
            variable depend on it.

        """
        # First check: Are there child variables that prevent deletion?
        kids = list(self.variables())
        if kids and not recursive:
            raise myokit.IntegrityError(
                'Variable <' + self.qname() + '>'
                ' can not be removed: it has children ' + ' and '.join(
                    ['<' + v.qname() + '>' for v in kids]) + '.')

        # Second check: Are there dependent variables that prevent deletion?
        if self._refs_by or self._srefs_by:
            refs = self._refs_by.union(self._srefs_by)
            if self in refs:
                # Self-ref is allowed
                refs.remove(self)

            if recursive:
                # Refs from child variables are allowed
                refs = refs.difference(
                    set([x for x in refs if x.has_ancestor(self)]))
                # Nested variables can not be referred to by outside variables,
                # so this action doesn't have to be repeated for the nested
                # variables.

            if ignore_siblings:
                # Refs from sibling variables are allowed
                refs = refs.difference(
                    set([x for x in refs if x.has_ancestor(self._parent)]))

            if refs:
                raise myokit.IntegrityError(
                    'Variable <' + self.qname() + '>'
                    ' can not be removed: it is used by ' + ' and '.join(
                        ['<' + v.qname() + '>' for v in refs]) + '.')

        # At this point it's OK to delete. Rest of the code makes changes,
        # shouldn't raise errors.

        # Tell other variables it no longer depends on them
        for var in self._refs_to:
            var._refs_by.remove(self)
        for var in self._srefs_to:
            var._srefs_by.remove(self)
        self._refs_to = set()
        self._srefs_to = set()
        # Note: Don't update refs_by! When deleting a whole component, other
        # variables may still have a _refs_to that they'll need to process,
        # leading to KeyErrors in the lines above.

        if not self._is_nested:
            # State variable? Then demote
            if self.is_state():
                self.demote()

            # Remove any bindings or labels
            self.set_binding(None)
            self.set_label(None)

            # Remove any aliases
            m = self.parent(Model)
            for c in m.components():
                c.remove_aliases_for(self)

        # Delete child variables
        if recursive:
            for kid in kids:
                # Call this method for each kid (and cascade to their kids)
                kid._delete(recursive=True, ignore_siblings=True)
                # Remove kid from list of nested variables
                self._remove_variable_internal(kid)

        # Remove parent links
        super(Variable, self)._delete()

    def demote(self):
        """
        Turns a state variable into an intermediary variable.

        This will reset the validation status of the model this variable
        belongs to.
        """
        if self._indice is None:
            raise Exception('Variable is not a state variable.')

        # Check that nobody has references to this var's derivative
        if self._refs_by:
            refs = ', '.join([r.qname() for r in self._refs_by])
            raise Exception(
                'Unable to demote variable while references to its derivative'
                ' are made by (' + refs + ').')

        model = self.model()
        try:
            # Remove initial value
            del model._current_state[self._indice]

            # Remove this variable from the state
            del model._state[self._indice]

            # Set lhs to name expression
            self._lhs = myokit.Name(self)

            # Remove this variable's indice
            self._indice = None

            # Reset other states' indices
            model._reset_indices()

            # All state refs to this variable are now considered ordinary refs
            # (And _refs_by is emtpy, see check above)
            for r in self._srefs_by:
                r._srefs_to.remove(self)    # No longer an sref to me
                r._refs_to.add(self)        # Now an ordinary ref to me
            self._refs_by = self._srefs_by
            self._srefs_by = set()

        finally:
            model._reset_validation()
            self._reset_cache(bubble=True)

    def eq(self):
        """
        Returns this variable's defining equation.

        For state variables this will be an equation for the variable's
        derivative. For ordinary variables the equation for the variable's
        value is returned.
        """
        return Equation(self._lhs, self._rhs)

    def eval(self):
        """
        Evaluates this variable's defining equation and returns the result.
        """
        return self._rhs.eval()

    def indice(self):
        """
        For state variables, this will return their index in the state vector.
        For all other variables, this will raise an exception.
        """
        if self._indice is None:
            raise Exception('Only state variables have initial values.')
        return self._indice

    def is_bound(self):
        """
        Returns ``True`` if a binding label has been added to this variable.
        """
        return self._is_bound

    def is_constant(self):
        """
        Returns ``True`` if this variable is constant.

        Myokit doesn't discern between mathematical and physical constants,
        parameters etc. Anything that doesn't change during a simulation is
        termed a constant. Note that this specifically excludes variables bound
        to external inputs.
        """
        return self._is_constant

    def is_intermediary(self):
        """
        Returns ``True`` if this variable is an intermediary variable, i.e. not
        a constant or a state variable (and not bound to an external variable).
        """
        return self._is_intermediary

    def is_labelled(self):
        """
        Returns ``True`` if a label has been added to this variable.
        """
        return self._label is not None

    def is_literal(self):
        """
        Returns ``True`` if this variable's expression contains only literal
        values.
        """
        return self._is_literal

    def is_nested(self):
        """
        Returns ``True`` if this variable's parent is another variable.
        """
        return self._is_nested

    def is_referenced(self):
        """
        Returns ``True`` if other variables reference this variable's ``lhs``.
        For states, this means it only returns ``True`` if other variables
        depend on this variable's derivative.
        """
        return len(self._refs_by) > 0

    def is_state(self):
        """
        Returns ``True`` if this variable is a state variable.
        """
        return self._is_state

    def label(self):
        """
        Returns this variable's label or ``None`` if no label is set.
        """
        return self._label

    def lhs(self):
        """
        Returns the left-hand side of the equation defining this variable.

        For state variables this will be a :class:`myokit.Derivative`, for
        all others this should be a :class:`myokit.Name`.
        """
        return self._lhs

    def promote(self, state_value=0):
        """
        Turns this variable into a state variable with a current state value
        given by ``state_value``.

        This will reset the validation status of the model this variable
        belongs to.
        """
        if self._indice is not None:
            raise Exception('Variable is already a state variable')
        if not isinstance(self._parent, Component):
            raise Exception('State variables can only be added to Components.')
        if self._binding is not None:
            raise Exception(
                'State variables cannot be bound to an external value.')

        # Check state value argument
        if isinstance(state_value, myokit.Expression):
            if not state_value.is_literal():
                raise myokit.NonLiteralValueError(
                    'Expressions for state values can not contain references'
                    ' to other variables.')

        model = self.model()
        try:
            # Set lhs to derivative expression
            self._lhs = myokit.Derivative(myokit.Name(self))

            # Get new indice
            self._indice = len(model._state)

            # Add to list of states
            model._state.append(self)

            # Add value to list of current values
            model._current_state.append(float(state_value))

            # All references to this variable are now considered references to
            # its state value
            assert len(self._srefs_by) == 0
            for r in self._refs_by:
                r._refs_to.remove(self)
                r._srefs_to.add(self)
            self._srefs_by = self._refs_by
            self._refs_by = set()

        finally:
            model._reset_validation()
            self._reset_cache(bubble=True)

    def pyfunc(self, use_numpy=True, arguments=False):
        """
        Returns a python function that evaluates this variable as a function of
        the state variables it depends on.

        The argument names used by the returned function will be the variables'
        unames, ordered alphabetically.

        If the function runs in "numpy-mode", which is enabled by default, the
        vector ready versions of ``log``, ``exp`` etc are used and piecewise
        statements are evaluated using an array ready piecewise function. To
        disable this functionality, set ``use_numpy=False``.

        To obtain more information about the arguments in the created function
        handle, set the optional argument ``arguments`` to ``True``. With this
        setting, the function will return a tuple ``(handle, vars)`` where
        ``handle`` is  the function handle and ``vars`` is a list of
        :class:`myokit.LhsExpression` objects in the same order as the function
        arguments.
        """
        # Expression writer uses unames, so must have called validate() since
        # last changes
        model = self.model()
        if not model.is_valid():
            model.validate()

        # Get expression writer
        if use_numpy:
            import numpy
            w = myokit.numpy_writer()
        else:
            import math
            w = myokit.python_writer()

        # Get arguments, equations
        eqs, args = model.expressions_for(self)

        # Handle function arguments
        func = [w.ex(x) for x in args]
        if func:
            # Sort both following func
            func, args = zip(*sorted(zip(func, args)))

        # Create function text
        func = ['def var_pyfunc_generated(' + ','.join(func) + '):']
        tab = '\t'
        if use_numpy:
            func.append(tab + 'with numpy.errstate(all=\'ignore\'):')
            tab += '\t'
        for eq in eqs:
            func.append(tab + w.eq(eq))
        func.append(tab + 'return ' + w.ex(eqs[-1].lhs))
        func = '\n'.join(func) + '\n'

        # Create function
        local = {}
        if use_numpy:
            myokit._exec(func, {'numpy': numpy}, local)
        else:
            myokit._exec(func, {'math': math}, local)
        handle = local['var_pyfunc_generated']

        # Return
        if arguments:
            return (handle, args)
        else:
            return handle

    def refs_by(self, state_refs=False):
        """
        Returns an iterator over the set of :class:`Variables <Variable>`  that
        refer to this variable in their defining equation.

        Note that only references to this variable's defining
        :class:`LhsExpression` (i.e. the one returned by :meth:`lhs()`) are
        returned. For a state variable ``x``, this means the returned result
        contains all variables referring to ``dot(x)``. To get an iterator over
        the variables referring to ``x`` instead, add the optional attribute
        ``state_refs=True``. For non-state variables this setting will trigger
        an :class:`Exception`.
        """
        if state_refs:
            if not self._is_state:
                raise Exception(
                    'The argument "state_refs=True" can only be used on state'
                    ' variables.')
            return iter(self._srefs_by)
        return iter(self._refs_by)

    def refs_to(self, state_refs=False):
        """
        Returns an iterator over the set of :class:`Variables <Variable>` that
        this variable's defining equation refers to.

        By default, this will _not_ include references to a state variable's
        value. To obtain a list of state variables whose value is referenced,
        use ``state_refs=True``.
        """
        if state_refs:
            return iter(self._srefs_to)
        else:
            return iter(self._refs_to)

    def remove_child_variables(self):
        """
        Removes all child variables of this variable.

        A :class:`myokit.IntegrityError` will be raised if the variable depends
        on any of its child variables.
        """
        # Check if this variable depends on any of its children
        deps = set()
        for var in self._refs_to:
            if var._parent is self:
                deps.add(var)
        if deps:
            raise myokit.IntegrityError(
                'Unable to remove all child variables from <'
                + self.qname() + '>: the RHS still depends on '
                + ' and '.join(['<' + var.qname() + '>' for var in deps])
                + '.')

        # No dependencies: ok to delete all children
        for kid in list(self.variables()):
            kid._delete(recursive=True, ignore_siblings=True)
            self._remove_variable_internal(kid)

    def rename(self, new_name):
        """ Renames this variable. """
        assert self._parent is not None
        self._parent.move_variable(self, self._parent, new_name)

    def __repr__(self):
        if self._indice is not None:
            return '<State(' + self.qname() + ')>'
        else:
            return '<Var(' + self.qname() + ')>'

    def _reset_cache(self, bubble=False):
        """
        Updates this variable's cached attributes. If ``bubble`` is set to
        ``True`` and this variable's cache state changes, a cache reset will be
        triggered in all dependent variables.
        """
        if bubble:
            s_old = (self._is_bound, self._is_state, self._is_intermediary,
                     self._is_literal, self._is_constant, self._is_nested)
        self._is_bound = self._binding is not None
        self._is_state = self._indice is not None
        self._is_nested = isinstance(self._parent, Variable)
        if self._is_state or self._is_bound or self._rhs is None:
            self._is_constant = False
            self._is_literal = False
            self._is_intermediary = False
        else:
            self._is_constant = self._rhs.is_constant()
            self._is_literal = self._rhs.is_literal()
            self._is_intermediary = not self._is_constant
        if bubble:
            if s_old != (self._is_bound, self._is_state, self._is_intermediary,
                         self._is_literal, self._is_constant, self._is_nested):
                for ref in self._refs_by:
                    ref._reset_cache(bubble=True)
                for ref in self._srefs_by:
                    ref._reset_cache(bubble=True)

    def rhs(self):
        """
        Returns the right-hand side of the equation defining this variable.

        For state variables this will be the expression for their derivative,
        for all others an expression for their value is returned.
        """
        return self._rhs

    def set_binding(self, binding):
        """
        Adds a unique binding label to this variable, indicating it can be used
        as an entry point for external inputs.

        To remove a binding, call ``set_binding(None)``.

        Adding or removing binding labels resets the model's validation status.
        """
        if binding is not None:
            # Check name
            binding = check_name(binding)

            # Check for existing binding
            if self._binding is not None:
                raise myokit.InvalidBindingError(
                    'The variable <' + self.qname() + '>'
                    ' is already bound to "' + self._binding + '".')

            # Check if not a state
            if self._indice is not None:
                raise myokit.InvalidBindingError(
                    'State variables cannot be bound to an external value.')

        # Set binding (model checks uniqueness)
        model = self.model()
        try:
            if binding is None:
                if self._binding is not None:
                    model._register_binding(self._binding, None)
            else:
                model._register_binding(binding, self)
            self._binding = binding
        finally:
            # Clear cache and cache of dependent variables
            self._reset_cache(bubble=True)

            # Reset model validation
            model._reset_validation()

    def set_label(self, label=None):
        """
        Adds a unique ``label`` for this variable, indicated that its value can
        be read by external users.

        To remove a label call ``set_label(None)``.
        """
        # Remove label?
        if label is None:
            if self._label is not None:
                self.model()._register_label(self._label, None)
                self._label = None
            return

        # Check name
        label = check_name(label)

        # Check for existing label or binding
        if self._label:
            raise myokit.InvalidLabelError(
                'The variable <' + self.qname() + '>'
                ' already has a label "' + self._label + '".')

        # Set label (model checks uniqueness)
        self.model()._register_label(label, self)
        self._label = label

    def set_rhs(self, rhs):
        """
        Changes the expression for this variable's right hand side (rhs).

        For state variables, this updates their derivative. For all others this
        will update the expression for their value.

        Expressions can be specified using :class:`myokit.Expression` objects,
        but floats or strings that can be parsed into expressions are also
        allowed::

            # Ways of setting x = 2
            x.set_rhs(myokit.Number(2))
            x.set_rhs(2)
            x.set_rhs(2.0)
            x.set_rhs('2')
            # Ways of setting x = 1 + y
            x.set_rhs(myokit.Plus(myokit.Number(1), myokit.Name(y)))
            x.set_rhs('1 + y')

        Calling `set_rhs` will reset the validation status of the model this
        variable belongs to.
        """
        # Handle string and number rhs's
        if not isinstance(rhs, myokit.Expression):
            if isinstance(rhs, basestring):
                rhs = myokit.parse_expression(rhs, context=self)
            elif rhs is not None:
                rhs = myokit.Number(rhs)

        # Update the refs-by stored in the old dependencies
        for ref in self._refs_to:
            ref._refs_by.remove(self)
        for ref in self._srefs_to:
            ref._srefs_by.remove(self)

        # Get new references made by this variable, filter out references to
        # to values of state variables.
        if rhs is not None:
            self._refs_to = set(
                [r.var() for r in rhs.references() if not r.is_state_value()])
            self._srefs_to = set(
                [r.var() for r in rhs.references() if r.is_state_value()])

            # Update the refs-by stored in the new dependencies of this var
            for ref in self._refs_to:
                ref._refs_by.add(self)
            for ref in self._srefs_to:
                ref._srefs_by.add(self)
        else:
            self._refs_to = set()
            self._srefs_to = set()

        # Set rhs
        self._rhs = rhs
        self.model()._reset_validation()
        self._reset_cache(bubble=True)

    def set_state_value(self, value):
        """
        If this variable is a state variable, its current value will be
        updated. For all other variables this raises an exception.
        """
        if not self._is_state:
            raise Exception('Only state variables have state values.')
        model = self.model()
        if isinstance(value, myokit.Expression):
            if not value.is_literal():
                raise myokit.NonLiteralValueError(
                    'Expressions for state values can not contain references'
                    ' to other variables.')
        model._current_state[self._indice] = float(value)
        # No need to reset validation status or cache here.

    def set_unit(self, unit=None):
        """
        Changes this variable's unit. The unit can be set to any valid Unit
        object, or ``None`` to remove the unit.
        """
        if unit is None or isinstance(unit, myokit.Unit):
            self._unit = unit
        elif isinstance(unit, basestring):
            self._unit = myokit.parse_unit(unit)
        else:
            raise TypeError('Method set_unit() expects a myokit.Unit or None.')
        # No need to reset validation status or cache. Units are checked only
        # by the model.

    def state_value(self):
        """
        For state variables, this will return their current value.
        For all other variables, this will raise an exception.
        """
        if not self._is_state:
            raise Exception('Only state variables have initial values.')
        return self.model()._current_state[self._indice]

    def unit(self, mode=myokit.UNIT_TOLERANT):
        """
        Returns the unit specified for this variable.

        If no unit was set and ``mode`` is ``myokit.UNIT_TOLERANT``, then None
        is returned. In ``myokit.UNIT_STRICT`` mode the value
        ``myokit.units.dimensionless`` is returned in this case.

        Variables' units are set using :meth:`Variable.set_unit()` or using
        the ``in`` keyword in ``.mmt`` files. The unit set for a variable is
        the unit this variable's expression _should_ have. This allows
        expressions to be validated by computing the resulting unit of an
        expression and comparing it with the value set for the variable.
        """
        if mode == myokit.UNIT_STRICT and self._unit is None:
            return myokit.units.dimensionless
        return self._unit

    def validate(self):
        """
        Attempts to check this variable's validity, raises errors if it isn't.
        """
        # Validate rhs
        if self._rhs is None:
            raise myokit.MissingRhsError(self)
        self._rhs.validate()

        # Partial derivatives are not allowed in an RHS
        if self._rhs.contains_type(myokit.PartialDerivative):
            raise myokit.IntegrityError(
                'Partial derivatives may not appear in expressions set as'
                ' right-hand side of a variable.')

        # Initial values are not allowed in an RHS
        if self._rhs.contains_type(myokit.InitialValue):
            raise myokit.IntegrityError(
                'Initial value operators may not appear in expressions set as'
                ' right-hand side of a variable.')

        # Conditions are not allowed as an RHS
        if isinstance(self._rhs, myokit.Condition):
            raise myokit.IntegrityError(
                'The right-hand side expression for a variable can not be a'
                ' condition.')

        # Check state variables
        is_state = self._indice is not None
        is_deriv = self.lhs().is_derivative()
        if is_state:
            if not is_deriv:        # pragma: no cover
                raise myokit.IntegrityError(
                    'Variable <' + self.qname() + '> is listed as a state'
                    ' variable but its lhs is not a derivative.')
            if self._is_nested:     # pragma: no cover
                raise myokit.IntegrityError(
                    'State variables should not be nested: <'
                    + str(self.qname()) + '>.')
            m = self.model()
            if not m._state[self._indice] == self:  # pragma: no cover
                raise myokit.IntegrityError(
                    'State variable not listed in model state vector at'
                    ' correct indice: <' + self.qname() + '>.')
        elif is_deriv:  # pragma: no cover
            raise myokit.IntegrityError(
                'A derivative was set for <' + self.qname() + '> but this is'
                ' not a state variable.')

        # Check for component as parent
        m = self.parent(Component)
        if m is None:   # pragma: no cover
            raise myokit.IntegrityError(
                'No component found in hierarchy for <' + self.qname() + '>.')

        # Validate references
        for ref in self._refs_to.union(self._srefs_to):
            # References can be made to:
            #  1. This variable's children or any of this variable's
            #     ancestor's children.
            #  2. Any component variable.
            # Quick checks first: sibling or direct child
            if ref._parent == self._parent or ref._parent == self:
                continue

            # Component variable?
            if isinstance(ref._parent, Component):
                continue

            # Child of ancestor of this variable
            if ref._parent.is_ancestor(self):
                continue
            raise myokit.IllegalReferenceError(ref, self)

        # Check no-one thinks this is a state unless it really is.
        if self._srefs_by and not is_state:  # pragma: no cover
            # Cover pragma: Can only be reached through an API bug
            refs = ', '.join([r.qname() for r in self._srefs_by])
            raise myokit.IntegrityError(
                'Variable <' + self.qname() + '> is not a state, but is'
                ' referred to as a state by (' + refs + ').')

        # Validate child variables
        for v in self.variables():
            if v._parent != self:   # pragma: no cover
                # Cover pragma: Can only be reached through an API bug
                raise myokit.IntegrityError(
                    'Child variable\'s parent does not match with actual'
                    ' parent: parent of <' + v.qname() + '> is set to <'
                    + str(v._parent.qname()) + '>, but the variable is'
                    ' stored in <' + self.qname() + '>.')

            # Deep validation
            v.validate()

    def value(self):
        """
        Will return the value of this variable's defining right-hand side
        expression.
        """
        return self._rhs.eval()


class Equation(object):
    """
    Defines an equation: a statement that a left-hand side (LHS) is equal to a
    right-hand side (RHS) expression.

    The sides of an equation are stored in the properties ``lhs`` and ``rhs``.
    Equations are immutable: once created, their LHS and RHS cannot be changed.

    Note: This is not a :class:`myokit.Expression`, for that, see
    :class:`myokit.Equal`.
    """

    def __init__(self, lhs, rhs):
        self._lhs = lhs
        self._rhs = rhs

    def __eq__(self, other):
        if not isinstance(other, Equation):
            return False
        else:
            return self.lhs == other.lhs and self.rhs == other.rhs

    def clone(self, subst=None, expand=False, retain=None):
        """
        Clones this equation.

        See :meth:`myokit.Expression.clone()` for details of the arguments.
        """
        return Equation(
            self._lhs.clone(subst, expand, retain),
            self._rhs.clone(subst, expand, retain),
        )

    def code(self):
        """ Returns an ``.mmt`` representation of this equation. """
        b = StringIO()
        self._lhs._code(b, None)
        b.write(' = ')
        self._rhs._code(b, None)
        return b.getvalue()

    def __hash__(self):
        # Note: Hash should never change during object's lifetime. This is
        # guaranteed if we use the hashes of its operands.
        return hash(self._lhs) + hash(self._rhs)

    def __iter__(self):
        # Having this allows "lhs, rhs = eq"
        return iter((self._lhs, self._rhs))

    @property
    def lhs(self):
        """ This equations left-hand side expression. """
        return self._lhs

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def rhs(self):
        """ This equations right-hand side expression. """
        return self._rhs

    def __str__(self):
        return self.code()

    def __repr__(self):
        return '<Equation ' + str(self) + '>'


class EquationList(list, VarProvider):
    """ An ordered list of :class:`Equation` objects """

    def _create_variable_stream(self, deep, sort):
        # Always sorted
        def stream(lst):
            for eq in lst:
                yield eq.lhs.var()
        return stream(self)


class UserFunction(object):
    """
    Represents a user function.

    ``UserFunction`` objects should not be created directly, but only via
    :meth:`Model.add_function()`.

    User functions are not ``Expression`` objects, but template expressions
    that are converted upon parsing. They allow common functions (for example
    a boltzman function) to be used in string expressions.

    Arguments:

    ``name``
        The user function's name (a string)
    ``arguments``
        A list of function argument names (all of type :class:`Name`)
    ``template``
        The :class:`Expression` evaluating this function.

    """

    def __init__(self, name, arguments, template):
        self._name = str(name)
        self._arguments = list(arguments)
        self._template = template

    def arguments(self):
        """
        Returns an iterator over this user function's arguments.
        """
        return iter(self._arguments)

    def convert(self, arguments):
        """
        Returns an :class:`Expression` object, evaluated using the given
        dictionary mapping argument Name objects to expressions.
        """
        if len(arguments) != len(self._arguments):
            raise ValueError('Wrong number of input arguments.')
        for arg in self._arguments:
            if arg not in arguments:
                raise ValueError('Missing input argument: <' + str(arg) + '>.')
        return self._template.clone(arguments)
