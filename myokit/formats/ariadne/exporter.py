#
# Exports to the Ariadne framework for hybrid systems analysis
# http://trac.parades.rm.cnr.it/ariadne/
#
# This file is part of Myokit
#  Copyright 2011-2014 Michael Clerx, Maastricht University
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import myokit
from myokit.exporters.ex_ansic import AnsiCExpressionWriter, keywords
info = \
"""
This exporter converts a model definition to the Ariadne syntax.

Only the model definition is exported. A basic pacing mechanism is
added that will need to be customized to match the model's needs.
"""
class AriadneExporter(myokit.TemplateBasedExporter):
    """
    Exports to the Ariadne framework for hybrid systems analysis
    """
    def info(self):
        return info
    def supports(self):
        return (True, False)
    def template_dict(self):
        return {
            'model.cc' : 'model.cc',
            }
    def variables(self, simulation):
        import myokit
        # Pre-process model
        model = simulation.model
        model.reserve_unique_names(*keywords)
        model.reserve_unique_names(
            'system',
            'model',
            'pacing', 'pulse_hi', 'pulse_lo',
        )
        model.create_unique_names()
        # Variable naming function
        def v(var):
            if isinstance(var, myokit.Derivative):
                return 'dot(' + var.var().uname() + ')'
            if isinstance(var, myokit.Name):
                return var.var().uname()
            if type(var) == myokit.External:
                name = var.qname()
                if name == 'engine.time':
                    return 't'
                elif name == 'engine.pace':
                    return 'pace'
                else:
                    raise NotImplementedError
            return var.uname()
        # Expression writer
        e = AnsiCExpressionWriter()
        e.set_lhs_function(v)
        #e.set_condition_function('ifthenelse') #TODO
        # Common variables
        model = simulation.model
        engine = model.engine()
        equations = model.solvable_order()
        components = []
        for comp in equations:
            if comp != '*remaining*':
                components.append(model[comp])
        # Return variables
        return {
            'simulation':simulation,
            'v' : v,            # Name writing function
            'e' : e,            # Expression writer
            'model' : model,
            'engine' : engine,
            'components' : components,
            'equations' : equations,
            }
