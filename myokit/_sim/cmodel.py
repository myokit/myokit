#
# Myokit symbolic expression classes. Defines different expressions, equations
# and the unit system.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import traceback

from collections import OrderedDict

import myokit
import myokit.formats.ansic
import myokit.pype

# Location of source file
SOURCE_FILE = 'cmodel.h'


class CModel(object):
    """
    Generates ansi-C code for a model.

    Example::

        model = myokit.parse_model('example')
        cmodel = CModel(model)
        print(cmodel.code)

    Arguments:

    ``model``
        A :class:`myokit.Model`.
    ``sensitivities``
        Either ``None`` or a tuple ``(dependents, independents)``. See
        :class:`myokit.Simulation` for details.

    The following properties are all public for easy access. But note that they
    do not interact with the compiled header so changing them will have little
    effect.

    ``model``
        The myokit.Model this CModel was compiled for.
    ``code``
        The generated model code. Can be placed in a header file or
        incorporated directly.

    Sensitivities:

    ``has_sensitivities``
        True if this model was created with sensitivity calculations enabled.
    ``dependents``
        A list of "dependent variables" for sensitivity calculations, all
        specified as expressions (:class:`myokit.Name` or
        :class:`myokit.Derivative`).
    ``independents``
        A list of "independent variables" for sensitivity calculations, all
        specified as expressions (:class:`myokit.Name` or
        :class:`myokit.InitialValue`).

    Constants (and parameters) are all stored inside ordered dicts mapping
    variable objects onto equations. Each dict is stored in a solvable order.

    ``parameters``
        Constants used as "independent variable" in sensitivity calculations.
    ``parameter_derived``
        Constants that depend on parameters (and possibly on literals too).
    ``literals``
        Constants that do not depend on any other constants (and are not
        parameters).
    ``literal_derived``
        Constants that depend on literals, but not on parameters.

    """
    def __init__(self, model, sensitivities):

        # Parse sensitivity arguments
        has_sensitivities, dependents, independents = \
            self._parse_sensitivities(model, sensitivities)

        # Set unique names in model: variable names will be prepended so don't
        # bother with keywords.
        model.create_unique_names()

        # Remove any unused bindings, and get mapping from variables to C
        # variable names as used in model.h
        #TODO: Think about best way to do this for model re-use with different
        # sets of bound variables... Presumably the model would simply support
        # all bindings used by any of the simulations based on model.h ?
        bound_variables = model.prepare_bindings({
            'time': 'time',
            'pace': 'pace',
            'realtime': 'realtime',
            'evaluations': 'evaluations',
        })

        # Get equations in solvable order (grouped by component)
        equations = model.solvable_order()

        # Derive sensitivity equations
        if has_sensitivities:
            output_equations = self._derive_sensitivity_equations(
                model, dependents, independents)
        else:
            output_equations = []

        # Partition constants into 4 types

        literals, literal_derived, parameters, parameter_derived = \
            self._partition_constants(equations, independents)

        # Get naming function and expression writer
        v, w = self._create_expression_writer(independents, parameters)

        # Generate code
        code = self._generate_code(
            model, equations, bound_variables, dependents, independents,
            output_equations, literals, literal_derived, parameters,
            parameter_derived, v, w)

        # Provide public properties
        self.model = model
        self.code = code
        self.has_sensitivities = has_sensitivities
        self.dependents = dependents
        self.independents = independents

        # Literals, literal-derived, parameters, and parameter-derived, all in
        # solvable order. Parameters use the ordering given in `independents`
        # (which is sortable, as parameters are independent).
        self.literals = literals
        self.literal_derived = literal_derived
        self.parameters = parameters
        self.parameter_derived = parameter_derived

    def _parse_sensitivities(self, model, sensitivities):
        """
        Parses the ``sensitivities`` constructor argument and returns a tuple
        ``(has_sensitivities, dependents, independents)``, where
        ``has_sensitivities`` is a boolean and the other two entries are lists
        containing :class:`myokit.Expression` objects.

        Acceptable input for dependents (y in dy/dx):

        - Variable (state or intermediary)
        - Name or Derivative
        - "ina.INa" or "dot(membrane.V)"

        Acceptable input for independents (x in dy/dx):

        - Variable (literal)
        - Name or InitialValue
        - "ikr.gKr" or "init(membrane.V)"

        The resulting lists contain Expression objects.
        """
        if sensitivities is None:
            return False, [], []

        # Get lists
        try:
            deps, indeps = sensitivities
            deps = list(deps)
            indeps = list(indeps)
        except Exception:
            raise ValueError(
                'The argument `sensitivities` must be None, or a tuple'
                ' containing two lists.')
        if len(deps) == 0 or len(indeps) == 0:
            return False, [], []

        # Create output lists
        dependents = []
        independents = []

        # Check dependents, make sure all are Name or Derivative objects from
        # the cloned model.
        for x in deps:
            deriv = False
            if isinstance(x, myokit.Variable):
                var = model.get(x.qname())
            elif isinstance(x, myokit.Name):
                var = model.get(x.var().qname())
            elif isinstance(x, myokit.Derivative):
                deriv = True
                var = model.get(x.var().qname())
            else:
                x = str(x)
                if x[:4] == 'dot(' and x[-1:] == ')':
                    deriv = True
                    var = x = x[4:-1]
                var = model.get(x)
            lhs = myokit.Name(var)
            if deriv:
                lhs = myokit.Derivative(lhs)
                if not var.is_state():
                    raise ValueError(
                        'Sensitivity of ' + lhs.code() + ' requested, but '
                        + var.qname() + ' is not a state variable.')
            elif var.is_bound():
                raise ValueError(
                    'Sensitivities cannot be calculated for bound'
                    ' variables (got ' + str(var.qname()) + ').')
            # Note: constants are fine, just not very useful! But may be
            # easy, e.g. when working with multiple models.
            dependents.append(lhs)

        # Check independents, make sure all are Name or InitialValue
        # objects from the cloned model.
        for x in indeps:
            init = False
            if isinstance(x, myokit.Variable):
                var = model.get(x.qname())
            elif isinstance(x, myokit.Name):
                var = model.get(x.var().qname())
            elif isinstance(x, myokit.InitialValue):
                init = True
                var = model.get(x.var().qname())
            else:
                x = str(x)
                if x[:5] == 'init(' and x[-1:] == ')':
                    init = True
                    x = x[5:-1]
                var = model.get(x)
            lhs = myokit.Name(var)
            if init:
                lhs = myokit.InitialValue(myokit.Name(var))
                if not var.is_state():
                    raise ValueError(
                        'Sensitivity with respect to ' + lhs.code() +
                        ' requested, but ' + var.qname() + ' is not a'
                        ' state variable.')
            elif not var.is_literal():
                raise ValueError(
                    'Sensitivity with respect to ' + var.qname() +
                    ' requested, but this is not a literal variable (it'
                    ' depends on other variables).')
            independents.append(lhs)

        return True, dependents, independents

    def _derive_sensitivity_equations(self, model, deps, indeps):
        """
        Derive expressions needed to evaluate the variables we want to output
        partial derivatives of.
        """
        # Derive equations needed to calculate the requested sensitivities,
        # assuming that the sensitivities of the state variables are known.
        s_output_equations = []

        # First, get variables instead of LhsExpressions. Ignore Name(state),
        # as we already have these, and convert Derivative(Name(state)) into
        # variables.
        output_variables = [
            lhs.var() for lhs in deps
            if not (isinstance(lhs, myokit.Name) and lhs.var().is_state())]

        # Now call expressions_for, which will return expressions to evaluate
        # the rhs for each variable (i.e. the dot(x) rhs for states).
        output_equations, _ = model.expressions_for(*output_variables)
        del output_variables, _

        # Gather output expressions for each parameter or initial value we want
        # sensitivities w.r.t.
        for expr in indeps:
            eqs = []
            for eq in output_equations:
                rhs = eq.rhs.diff(expr, independent_states=False)
                if rhs.is_number(0) and eq.lhs not in deps:
                    continue
                lhs = myokit.PartialDerivative(eq.lhs, expr)
                eqs.append(myokit.Equation(lhs, rhs))
            s_output_equations.append(eqs)

        return s_output_equations

    def _partition_constants(self, equations, independents):
        """
        Partitions the model's constants into four (non-overlapping) groups,
        each stored in solvable order.
        """
        # NOTE: Some methods in cmodel.h require the ordering of parameters and
        #       literals to match that in the independents ordered-dict.
        literals = OrderedDict()
        literal_derived = OrderedDict()
        parameters = OrderedDict()
        parameter_derived = OrderedDict()

        # Get all parameters, in the same order as independents
        p = set()
        for lhs in independents:
            if isinstance(lhs, myokit.Name):
                p.add(lhs)
                parameters[lhs.var()] = None

        # Scan over equations
        for label, eqs in equations.items():
            for eq in eqs.equations(const=True):
                var = eq.lhs.var()
                if eq.lhs in p:
                    parameters[var] = eq
                elif var.is_literal():
                    literals[var] = eq
                elif eq.rhs.references().intersection(p):
                    p.add(eq.lhs)
                    parameter_derived[var] = eq
                else:
                    literal_derived[var] = eq

        return literals, literal_derived, parameters, parameter_derived

    def _create_expression_writer(self, independents, parameters):
        """
        Creates a variable/expression naming function and an expression writer.
        """

        def v(var):
            """
            Returns a readable variable name to use in code (which will be
            mapped to a model entry by a C define).

            C Variable names:

            - State: Y_x
            - Derivative: D_x
            - Bound: B_x
            - Intermediary: V_x
            - Parameter: P_x
            - Other constant: C_x

            Where `x` is the uname of the Myokit variable.

            For sensitivities `x` represents the name of the independent
            variable (x in dy/dx), and `i` represents the index of the
            dependent variable in the list of dependent variables. This is used
            in place of a name, because that would require stringing two unames
            together in some way that ensures the result does not overlap with
            any unames.

            - State sensitivity: Si_Y_x
            - Derivative sensitivity: Si_D_x (todo)
            - Intermediary sensitivity: Si_V_x

            """
            if not isinstance(var, (myokit.LhsExpression, myokit.Variable)):
                raise ValueError(  # pragma: no cover
                    'v() called with ' + str(var) + ' of type '
                    + str(type(var)))

            # Partial derivative
            if isinstance(var, myokit.PartialDerivative):
                i = var.dependent_expression()
                j = str(independents.index(var.independent_expression()))
                if isinstance(i, myokit.Derivative):
                    return 'S' + j + '_D_' + i.var().uname()
                if i.var().is_state():
                    return 'S' + j + '_Y_' + i.var().uname()
                return 'S' + j + '_V_' + i.var().uname()

            # Derivative
            if isinstance(var, myokit.Derivative):
                return 'D_' + var.var().uname()

            # Name given? get variable object from name
            if isinstance(var, myokit.Name):
                var = var.var()

            # State
            if var.is_state():
                return 'Y_' + var.uname()

            # Parameter
            if var in parameters:
                return 'P_' + var.uname()

            # Constant (parameter derived, literal, literal derived)
            if var.is_constant():
                return 'C_' + var.uname()

            # Bound variable
            if var.is_bound():
                return 'B_' + var.binding()

            # Intermediary variable
            return 'V_' + var.uname()

        # Create expression writer
        w = myokit.formats.ansic.AnsiCExpressionWriter()
        w.set_lhs_function(v)

        return v, w

    def _generate_code(
            self, model, equations, bound_variables, dependents, independents,
            output_equations, literals, literal_derived, parameters,
            parameter_derived, v, w):
        """ Generates and returns the model code. """

        # Get states whose initial value is used in sensivitity calculations
        initials = [p.var().indice() for p in independents
                    if isinstance(p, myokit.InitialValue)]

        # Arguments
        args = {
            'model': model,
            'equations': equations,
            'bound_variables': bound_variables,
            's_dependents': dependents,
            's_independents': independents,
            's_output_equations': output_equations,
            'initials': initials,
            'parameters': parameters,
            'parameter_derived': parameter_derived,
            'literals': literals,
            'literal_derived': literal_derived,
            'v': v,
            'w': w,
        }

        # Path
        path = os.path.join(myokit.DIR_CFUNC, SOURCE_FILE)

        # Parse template
        p = myokit.pype.TemplateEngine()
        try:
            return p.process(path, args)
        except myokit.pype.PypeError:  # pragma: no cover
            msg = ['An error ocurred while processing the template']
            msg.append(traceback.format_exc())
            extra = p.error_details()
            if extra:
                msg.append(extra)
            raise myokit.GenerationError('\n'.join(msg))

