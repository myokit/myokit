#
# Imports a model from an SBML file.
# Only partial SBML support (Based on SBML level 3) is provided.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import xml.etree.ElementTree as ET
import os
import re

from libsbml import SBMLReader, XMLNode

import myokit
import myokit.units
import myokit.formats
from myokit.mxml import html2ascii, split
from myokit.formats.mathml import parse_mathml_etree


info = """
Loads a Model definition from an SBML file. Warning: This importer hasn't been
extensively tested.
"""


class SBMLImporter(myokit.formats.Importer):
    """
    This:class:`Importer <myokit.formats.Importer>` load model definitions
    from files in SBML format.
    """
    def __init__(self):
        super(SBMLImporter, self).__init__()
        self.re_name = re.compile(r'^[a-zA-Z]+[a-zA-Z0-9_]*$')
        self.re_alpha = re.compile(r'[\W]+')
        self.re_white = re.compile(r'[ \t\f\n\r]+')
        self.units = {}

    def info(self):
        return info

    def model(self, path, bind_time=True):
        """
        Returns a :class:myokit.Model based on the SBML file provided.

        Arguments:
            path -- Path to SBML file.
            bind_time -- Flag to create and bind a time bound variable. If
                         False no variable will be bound to time in the
                         :class:myokit.Model.
        """
        # Get logger
        log = self.logger()

        # Read SBML file
        reader = SBMLReader()
        doc = reader.readSBMLFromFile(path)
        if doc.getNumErrors() > 0:
            print('There were some errors')
            # TODO: proper error handling here.

        # Get level and version of SBML file
        lvl = doc.getLevel()
        v = doc.getVersion()

        # check whether file is latest version and upgrade, if possible
        if lvl != 3 or v != 2:
            doc.checkL3v2Compatibility()
            if doc.getNumErrors() > 0:
                log.warn(
                    'SBML file cannot be converted to level 3, version 2.'
                    'This may result in model building errors.')
            else:
                success = doc.setLevelAndVersion(level=3, version=2)
                if success:
                    log.log('Converted SBML file to level 3, version 2.')
                else:
                    log.warn(
                        'Conversion of SBML file to level 3, version 2 was '
                        'attempted but not successful. This may result in '
                        'model building errors.')

        # TODO: level and version conversion
        # If significant changes between levels exist that would influence
        # how models are built, upgrade versions, potentially levels to the
        # latest stage, and build models from there.
        # using doc.setLevelandVersion()
        # problems can be asses with ErrorLog

        # Get model name
        SBMLmodel = doc.getModel()
        name = SBMLmodel.getName()
        if not name:
            name = SBMLmodel.getIdAttribute()
        if not name:
            name = 'Imported SBML model'

        # Create myokit model
        model = myokit.Model(self._convert_name(name))
        log.log('Reading model "' + model.meta['name'] + '"')

        # Add notes, if provided, to model description
        notes = SBMLmodel.getNotes()
        if notes:
            log.log('Converting <model> notes to ascii')
            notes = XMLNode.convertXMLNodeToString(notes)
            model.meta['desc'] = html2ascii(notes, width=75)
            # width = 79 - 4 for tab!

        # Get function definitions
        funcDefs = SBMLmodel.getListOfFunctionDefinitions()
        if funcDefs:
            userFuncDict = dict()
            for funcDef in funcDefs:
                userFuncDict[funcDef.getIdAttribute()] = funcDef

        # Get unit definitions
        unitDefs = SBMLmodel.getListOfUnitDefinitions()
        if unitDefs:
            userUnitDict = dict()
            for unitDef in unitDefs:
                userUnitDict[unitDef.getIdAttribute()] = self._convert_unit(
                    unitDef)
            print(userUnitDict)  # TODO: Upgrading introduces units?

        # Add compartments to model
        compDict = dict()
        comps = SBMLmodel.getListOfCompartments()
        if comps:
            for comp in comps:
                idx = comp.getIdAttribute()
                name = comp.getName()
                if not name:
                    name = idx
                compDict[idx] = model.add_component(
                    self._convert_name(name))

        # Add a generic compartment for anything unassigned
        name = self._convert_name('sbml')
        compDict['sbml'] = model.add_component(name)

        # Initialise parameter and species dictionary
        paramAndSpeciesDict = dict()

        # Add parameters to model
        params = SBMLmodel.getListOfParameters()
        if params:
            for param in params:
                idp = param.getIdAttribute()
                name = param.getName()
                if not name:
                    name = idp
                value = param.getValue()
                unit = param.getUnits()
                if unit in userUnitDict:
                    unit = userUnitDict[unit]
                elif unit in SBML2MyoKitUnitDict:
                    unit = SBML2MyoKitUnitDict[unit]
                else:
                    unit = None

                # add parameter to sbml compartment
                comp = compDict['sbml']
                v = comp.add_variable_allow_renaming(
                    self._convert_name(name))
                v.set_unit(unit)
                v.set_rhs(value)

                # save param in container for later assignments/reactions
                paramAndSpeciesDict[idp] = v

        # Add species to compartments
        species = SBMLmodel.getListOfSpecies()
        if species:
            for s in species:
                ids = s.getIdAttribute()
                name = s.getName()
                idc = s.getCompartment()

            # species.initialAmount or initialConcentration
            # species is constant, stays constant
            # substanceUnits
            # hasOnlySubstanceUnits shows whether amount or concentration
            # constant and boundaryCondition
            # conversionFactor, look up in parameters
            # if size changes concentration has to be recalculated,
            # complexity of this depends on hasOnlySubstanceUnits

        # TODO: add time parameter, if not existent, and bind to time
        # Model attribute timeUnits defines time. If not provided log warning

        # TODO: Potentially get extent units. KineticLaw units are extentUnit/timeUnits

        # TODO: add initial assignments to model
        # initial assignment overrule initial value / concentration

        # TODO: add Rules to model

        # TODO: extract Constraints (cannot be added to model, but should be returned)

        # TODO: add Reactions to model

        # TODO: extract event and convert it to protocol

        return model

    def _convert_name(self, name):
        """
        Converts a name to something acceptable to myokit.
        """
        if not self.re_name.match(name):
            org_name = name
            name = self.re_white.sub('_', name)
            name = self.re_alpha.sub('_', name)
            if not self.re_name.match(name):
                name = 'x_' + name
            self.logger().warn(
                'Converting name <' + org_name + '> to <' + name + '>.')
        return name

    def _convert_unit(self, unitDef):
        """
        Converts unit definition into a myokit unit.
        """
        # Get composing base units
        units = unitDef.getListOfUnits()
        if not units:
            return None

        # instantiate unit definition
        unitDef = myokit.units.dimensionless

        # construct unit definition from base units
        for baseUnit in units:
            sbmlUnit = SBMLBaseUnits[baseUnit.getKind()]
            # getKind() returns index defined by SBML
            myokitUnit = SBML2MyoKitUnitDict[sbmlUnit]
            myokitUnit *= baseUnit.getMultiplier()  # mandatory in l3
            myokitUnit *= 10 ** float(baseUnit.getScale())  # mandatory in l3
            myokitUnit **= float(baseUnit.getExponent())  # mandatory in l3
            # "add" composite unit to unit definition
            unitDef *= myokitUnit

        return unitDef



class SBMLError(myokit.ImportError):
    """
    Thrown if an error occurs when importing SBML
    """

# SBML base units according to libSBML (order matters for unit identification!)
SBML2MyoKitUnitDict = {
    'ampere': myokit.units.A,
    'avogadro': None,  # TODO: myokit equivalent not yet looked up
    'becquerel': myokit.units.Bq,
    'candela': myokit.units.cd,
    'celsius': myokit.units.C,
    'coulomb': myokit.units.C,
    'dimensionless': myokit.units.dimensionless,
    'farad': myokit.units.F,
    'gram': myokit.units.g,
    'gray': myokit.units.Gy,
    'henry': myokit.units.H,
    'hertz': myokit.units.Hz,
    'item': None,  # TODO: myokit equivalent not yet looked up
    'joule': myokit.units.J,
    'katal': myokit.units.kat,
    'kelvin': myokit.units.K,
    'kilogram': myokit.units.kg,
    'liter': myokit.units.L,
    'litre': myokit.units.L,
    'lumen': myokit.units.lm,
    'lux': myokit.units.lux,
    'meter': myokit.units.m,
    'metre': myokit.units.m,
    'mole': myokit.units.mol,
    'newton': myokit.units.N,
    'ohm': myokit.units.R,
    'pascal': myokit.units.Pa,
    'radian': myokit.units.rad,
    'second': myokit.units.s,
    'siemens': myokit.units.S,
    'sievert': myokit.units.Sv,
    'steradian': myokit.units.sr,
    'tesla': myokit.units.T,
    'volt': myokit.units.V,
    'watt': myokit.units.W,
    'weber': myokit.units.Wb,
    'invalid': None,
}

# SBML base units
SBMLBaseUnits = list(SBML2MyoKitUnitDict.keys())