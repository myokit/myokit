#
# Imports a channel model from a Neuron MOD file.
#
# Neuron extension to NMODL:
#   http://www.neuron.yale.edu/neuron/static/new_doc/modelspec/programmatic/
#       mechanisms/nmodl2.html
# NMODL:
#   http://www.neuron.yale.edu/neuron/static/docs/help/neuron/nmodl/nmodl.html
# Aka the "NBSR Model Description Language"
# "MODL (model description language) was originally developed at the NBSR
#  (National Biomedical Simulation Resource) to specify models for simulation
#  with SCoP (Simulation Control Program). With MODL one specifies a physical
#  model in terms of simultaneous nonlinear algebraic equations, differential
#  equations, or kinetic schemes. MODL translates the specification into the C
#  language which is then compiled and linked with the SCoP program. It turned
#  out that only modest extensions to the MODL syntax were necessary to allow
#  it to translate model descriptions into a form suitable for compiling and
#  linking with NEURON V2. The extended version was called NMODL."
# 
# Original language document for SCoPL:
#   http://cns.iaf.cnrs-gif.fr/files/scopman.html
#
#
#
# This file is part of Myokit
#  Copyright 2011-2014 Michael Clerx, Maastricht University
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
# Python imports
#import os
#import re
# Myokit import
import myokit
import myokit.units
import myokit.formats
# Global vars, general importer stuff
info = \
"""
Loads a channel definition from a Neuron MOD file.
"""
raise NotImplementedError

#
# Problem: This is a language with functions etc. It'll require a full parser
# capable of handling expressions to read this.
#
#

class MODError(Exception):
    """
    Thrown if an error occurs when importing a Neuron MOD file.
    """
    pass
# The main class
class MODImporter(myokit.formats.Importer):
    """
    Loads a Model definition from an SBML file.
    """
    def __init__(self):
        super(MODImporter, self).__init__()
        #self.re_name = re.compile(r'^[a-zA-Z]+[a-zA-Z0-9_]*$')
        #self.re_alpha = re.compile(r'[\W]+')
        #self.re_white = re.compile(r'[ \t\f\n\r]+')
        #self.units = {}
    def info(self):
        return info
    def supports_model(self):
        return True
    def model(self, path, options=None):
        # Parse file into blocks
    
        raise NotImplementedError
