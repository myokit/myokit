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

        # Find special variables
        vm = None
        time = None
        iion = None
        #TODO istim?
        alphas = set()
        betas = set()
        taus = set()
        infs = set()

        # Run over state variables, check that none of the equations refer to
        # derivatives
        for var in model.states():
            if len(list(var.refs_by())) > 0:
                raise ValueError(
                    'EasyML export does not support models with expressions'
                    ' that depend on derivatives of the state variables.')

        # Get time variable
        time = model.time()

        # Guess membrane potential
        vm = model.label('membrane_potential')
        if vm is None:
            if model.count_states() == 0:
                raise ValueError('EasyML export requires model with ODEs.')

            # Guess Vm
            vm = next(model.states())
            log.warning('Membrane potential variable not annotated. Guessing '
                        + vm.qname())

        # V will be set externally, so can change its RHS to remove
        # dependencies on i_ion, i_stim, etc.
        vm_rhs = vm.rhs()
        vm.set_rhs(0)

        # Remove label from diffusion current, if set
        i_diff = model.label('diffusion_current')
        if i_diff:
            i_diff.set_label(None)
            #TODO: Remove current altogether?

        # Guess transmembrane current variable
        #TODO: Previously used 'cellular_current' label
        #TODO: Make one, based on Vm ???




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
        var_to_name = {}
        name_to_var = {}
        needs_renaming = {}
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

        # Resolve clashes
        for name, variables in needs_renaming:
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
            for c in model.components():
                f.write('# ' + c.name() + eol)
                for v in c.variables(deep=True):
                    f.write(e.eq(v.eq()) + eos)
                f.write(eol)





    def supports_model(self):
        """ See :meth:`myokit.formats.Exporter.supports_model()`. """
        return True


'''
V; .nodal(); .external(Vm);
Iion; .nodal(); .external();

V; .lookup(-800, 800, 0.05);
Ca_i; .lookup(0.001, 30, 0.001);
.units(uM);

V_init = -86.926861;

a_m = ((V < 100)
       ? 0.9*(V+42.65)/(1.-exp(-0.22*(V+42.65)))
       : 890.94379*exp(.0486479163*(V-100.))/
            (1.+5.93962526*exp(.0486479163*(V-100.)))
       );

b_m = ((V < -85)
       ? 1.437*exp(-.085*(V+39.75))
       : 100./(1.+.48640816*exp(.2597503577*(V+85.)))
       );

a_h = ((V>-90.)
       ? 0.1*exp(-.193*(V+79.65))
       : .737097507-.1422598189*(V+90.)
       );

b_h = 1.7/(1.+exp(-.095*(V+20.5)));

APDshorten = 1;

a_d = APDshorten*(0.095*exp(-0.01*(V-5.)))/
  (exp(-0.072*(V-5.))+1.);
b_d = APDshorten*(0.07*exp(-0.017*(V+44.)))/
  (exp(0.05*(V+44.))+1.) ;

a_f = APDshorten*(0.012*exp(-0.008*(V+28.)))/
  (exp(0.15*(V+28.))+1.);
b_f = APDshorten*(0.0065*exp(-0.02*(V+30.)))/
  (exp(-0.2*(V+30.))+1.);

a_X = ((V<400.)
       ? (0.0005*exp(0.083*(V+50.)))/
       (exp(0.057*(V+50.))+1.)
       : 151.7994692*exp(.06546786198*(V-400.))/
       (1.+1.517994692*exp(.06546786198*(V-400.)))
       );

b_X   = (0.0013*exp(-0.06*(V+20.)))/(exp(-0.04*(V+20.))+1.);

xti   = 0.8*(exp(0.04*(V+77.))-1.)/exp(0.04*(V+35.));

I_K = (( V != -23. )
       ? 0.35*(4.*(exp(0.04*(V+85.))-1.)/(exp(0.08*(V+53.))+
                                              exp(0.04*(V+53.)))-
               0.2*(V+23.)/expm1(-0.04*(V+23.)))
       :
       0.35*(4.*(exp(0.04*(V+85.))-1.)/(exp(0.08*(V+53.))+
                                            exp(0.04*(V+53.))) + 0.2/0.04 )
       );

Esi = -82.3-13.0287*log(Ca_i/1.e6);

GNa = 15;
ENa  = 40.0;
I_Na = GNa*m*m*m*h*(V-ENa);
Gsi = 0.09;
I_si = Gsi*d*f*(V-Esi);
I_X  = X*xti;

Iion= I_Na+I_si+I_X+I_K;

Ca_i_init = 3.e-1;
diff_Ca_i = ((V<200.)
             ? (-1.e-1*I_si+0.07*1.e6*(1.e-7-Ca_i/1.e6))
             : 0
             );

group {
  GNa;
  Gsi;
  APDshorten;
}
.param();

group {
  I_Na;
  I_si;
  I_X;
  I_K;
}
.trace();
'''
