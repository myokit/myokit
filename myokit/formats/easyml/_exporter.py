#
# Export as an EasyML model.
#
# This file is part of Myokit
#  Copyright 2011-2019 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import logging

import myokit.formats
from ._ewriter import EasyMLExpressionWriter


class EasyMLExporter(myokit.formats.Exporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a ``.model``
    file in the EasyML format used by CARP/CARPEntry.
    """
    def info(self):
        """ See :meth:`myokit.formats.Exporter.info()`. """
        import inspect
        return inspect.getdoc(self)

    def model(self, path, model):
        """
        Exports a :class:`myokit.Model` in EasyML format, writing the result to
        the file indicated by ``path``.

        A :class:`myokit.ExportError` will be raised if any errors occur.
        """
        log = logging.getLogger(__name__)

        # Clone model so that changes can be made
        model = model.clone()
        model.validate()
        if not model.is_valid():
            raise ValueError('EasyML export requires a valid model.')

        # List of variables not to output
        ignore = set()

        # Find membrane potential
        vm = model.label('membrane_potential')
        if vm is None:
            if model.count_states() == 0:
                raise ValueError('EasyML export requires model with ODEs.')

            # Guess Vm
            vm = next(model.states())
            log.warning('Membrane potential variable not annotated. Guessing '
                        + vm.qname())

        # Make sure vm is a state --> So that expressions depending on V are
        # not seen as constants
        if not vm.is_state():
            vm.promote(-80)

        # Don't output vm
        ignore.add(vm)

        # Get time variable
        time = model.time()

        # Find pacing variable
        i_pace = model.binding('pace')

        # Find diffusion current
        i_diff = model.binding('diffusion_current')

        # Guess transmembrane current
        i_ion = model.label('cellular_current')

        # Find expression to extract currents from
        if i_ion is not None:
            e_currents = i_ion.rhs()
        else:
            e_currents = vm.rhs()

        # Remove time, pacing variable, diffusion current, and i_ion
        for var in [time, i_pace, i_diff, i_ion]:
            if var is None:
                continue

            refs = list(var.refs_by())
            subst = {var.lhs(): myokit.Number(0)}
            for ref in refs:
                ref.set_rhs(ref.rhs().clone(subst=subst))
            var.parent().remove_variable(var)

        # Guess currents
        # Assume that e_currents is an expression such as:
        #  INa + ICaL + IKr + ...
        #  i_ion + i_diff + i_stim
        #  -1/C * (...)
        currents = []
        for term in e_currents.references():
            if term.is_constant():
                continue
            currents.append(term.var())

        # Run over state variables, check that none of the equations refer to
        # derivatives
        for var in model.states():
            if len(list(var.refs_by())) > 0:
                raise ValueError(
                    'EasyML export does not support models with expressions'
                    ' that depend on derivatives of the state variables.')

        # Remove unused variables
        # Start by setting V's rhs to the sum of currents, so all currents
        # count as used
        rhs = myokit.Number(0)
        for v in currents:
            rhs = myokit.Plus(rhs, v.lhs())
        vm.set_rhs(rhs)
        model.validate(remove_unused_variables=True)

        # Find HH state variables, infs, taus, alphas, betas
        #TODO
        # Find special variables
        #alphas = set()
        #betas = set()
        #taus = set()
        #infs = set()

        # Detect names with special meanings
        def special_start(name):
            if name.startswith('diff_') or name.startswith('d_'):
                return True
            if name.startswith('alpha_') or name.startswith('a_'):
                return True
            if name.startswith('beta_') or name.startswith('b_'):
                return True
            if name.startswith('tau_'):
                return True
            return False

        def special_end(name):
            return name.endswith('_init') or name.endswith('_inf')

        # Create variable names

        # Initialise dict of name clashes with known keywords
        from . import keywords
        reserved = [
            'Iion',
        ]
        needs_renaming = {}
        for keyword in keywords:
            needs_renaming[keyword] = []
        for keyword in reserved:
            needs_renaming[keyword] = []

        # Create initial variable names
        var_to_name = {}
        name_to_var = {}
        for var in model.variables(deep=True):
            # Choose name that doesn't have a special meaning in EasyML
            name = var.name()
            if name in ['alpha', 'beta', 'inf', 'tau']:
                name = var.parent().name() + '_' + name
            if special_start(name):
                name = var.parent().name() + '_' + name
                if special_start(name):
                    name = var.qname().replace('.', '_')
                if special_start(name):
                    name = 'var_' + name
            if special_end(name):
                name += '_var'

            # Update name to have special meaning if needed
            #TODO: Add alpha_ for alphas etc.
            #TODO: If an alpha var is called e.g. x_alpha, change its name to
            #      alpha_x

            # Store (initial) name for var
            var_to_name[var] = name

            # Check for clashes, and create reverse mapping
            if name in needs_renaming:
                needs_renaming[name].append(var)
            else:
                var2 = name_to_var.get(name, None)
                if var2:
                    needs_renaming[name] = [var2, var]
                else:
                    name_to_var[name] = var

        # Resolve naming conflicats
        for name, variables in needs_renaming.items():
            # Add a number to the end of the name, increasing it until it's
            # unique
            i = 1
            root = name + '_'
            for var in variables:
                name = root + str(i)
                while name in name_to_var:
                    i += 1
                    name = root + str(i)
                var_to_name[var] = name
                name_to_var[name] = var

        # Remove reverse mappings
        del(name_to_var, needs_renaming)

        # Create naming function
        def lhs(e):
            if isinstance(e, myokit.Derivative):
                return 'd_' + var_to_name[e.var()]
            elif isinstance(e, myokit.LhsExpression):
                return var_to_name[e.var()]
            elif isinstance(e, myokit.Variable):
                return var_to_name[e]
            raise ValueError('Not a variable or LhsExpression: ' + str(e))

        # Create expression writer
        e = EasyMLExpressionWriter()
        e.set_lhs_function(lhs)

        # Test if can write in dir (raises exception if can't)
        self._test_writable_dir(os.path.dirname(path))

        # Write equations
        eol = '\n'
        eos = ';\n'
        with open(path, 'w') as f:
            # Write membrane potential
            f.write(lhs(vm) + '; .nodal(); .external(Vm);' + eol)

            # Write current
            f.write('Iion; .nodal(); .external();' + eol)
            f.write(eol)

            # Write remaining variables
            for c in model.components():
                todo = [v for v in c.variables(deep=True) if v not in ignore]
                if todo:
                    f.write('# ' + c.name() + eol)
                    for v in todo:
                        f.write(e.eq(v.eq()) + eos)
                    f.write(eol)

            # Write sum of currents variable
            f.write('Iion = ')
            f.write(' + '.join([lhs(v) for v in currents]))
            f.write(eos)
            f.write(eol)

            # Write current group
            f.write('group {' + eol)
            for v in currents:
                f.write('  ' + lhs(v) + eos)
            f.write('}' + eol)
            f.write(eol)






    def supports_model(self):
        """ See :meth:`myokit.formats.Exporter.supports_model()`. """
        return True

