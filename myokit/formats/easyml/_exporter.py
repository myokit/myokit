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
        # Create expression writer
        e = EasyMLExpressionWriter()

        #TODO: Detect special names in models, and change them or raise errors

        #TODO rhs function

        #TODO Find time

        #TODO Find membrane potential

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
