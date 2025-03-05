#
# Exports to stan (a package for statistical inference)
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os

import myokit.formats


class StanExporter(myokit.formats.TemplatedRunnableExporter):
    """
    This:class:`Exporter <myokit.formats.Exporter>` generates a Stan
    implementation of a Myokit model.

    Only the model definition is exported. An interpolating pacing input method
    is added.
    No post-processing is included.

    The following inputs are provided:

    ``time``
        The current simulation time
    ``pace``
        The current value of the pacing system, implemented using a very simple
        pacing mechanism.

    """
    def _dir(self, root):
        return os.path.join(root, 'stan', 'template')

    def _dict(self):
        return {
            'cell.stan': 'cell.stan',
            'run.py': 'run.py',
        }

    def runnable(
            self, path, model, protocol=None, parameters=None, output=None):
        """
        Exports a:class:`myokit.Model` to a Stan model with a parameter
        estimation file.

        Arguments:

        ``path``
            A string representing the **directory** to store the output in.
        ``model``
            A Myokit model to export
        ``protocol``
            Not implemented!
        ``parameters``
            A list of variables or variable names, specifying the model
            variables to be estimated by stan.
        ``output``
            A single variable to be used as the model output (for example an
            ion current).

        """
        super().runnable(
            path, model, protocol, parameters, output)

    def _vars(self, model, protocol, parameters, output):
        import myokit.formats.stan as stan

        # Check parameter list
        if parameters is None:
            parameters = []
        else:
            parameters = [model.get(str(x)) for x in parameters]

        # Check model output variable
        if output is None:
            output = next(model.states())
        else:
            output = model.get(str(output))

        # Reserve unique names
        model.reserve_unique_names(*stan.keywords)
        model.reserve_unique_names(
            # Only bound variable names and variables (not functions!) listed
            # in derivatives() need to be added here.
            'time',
            'pace',
            'state',
            'parameters',
            'xr',
            'xi',
            'derivatives'
        )
        model.create_unique_names()

        # Variable naming function
        def v(var):
            if isinstance(var, myokit.Derivative):
                return 'd_' + var.var().uname()
            if isinstance(var, myokit.Name):
                var = var.var()
            if var.is_bound():
                return 'time' if var.binding() == ' time' else 'pace'
            return var.uname()

        # Expression writer
        ew = stan.StanExpressionWriter()
        ew.set_lhs_function(v)

        # Process bound variables
        bound_variables = myokit._prepare_bindings(model, {
            'time': 'time',
            'pace': 'pace',
        })

        # Common variables
        equations = model.solvable_order()
        components = []
        for comp in equations:
            if comp != '*remaining*':
                components.append(model[comp])

        # Return variables
        return {
            'v': v,
            'e': ew.eq,
            'model': model,
            'components': components,
            'equations': equations,
            'bound_variables': bound_variables,
            'parameters': parameters,
            'output': output,
        }
