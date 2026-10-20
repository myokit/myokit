#
# SBML Writer: Writes an SBML Model to disk
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from typing import Tuple
from lxml import etree

import myokit
from myokit._unit import Quantity
from myokit.formats.mathml._ewriter import MathMLExpressionWriter
from myokit.formats.sbml._api import (
    Model, Compartment,
    Parameter, Species,
    Reaction, SpeciesReference
)


def write_file(path: str, model: Model):
    """
    Writes an SBML model to the given path.
    """
    return SBMLWriter.write_file(path, model)


def write_string(model: Model) -> str:
    """
    Writes an SBML model to a string and returns it.
    """
    return SBMLWriter.write_string(model)


class SBMLWriter:
    """
    Writes SBML documents
    """

    @staticmethod
    def write_file(path: str, model: Model):
        tree = SBMLWriter._model(model)
        # Write to disk
        tree.write(
            path,
            encoding='utf-8',
            method='xml',
            xml_declaration=True,
            pretty_print=True,
        )

    @staticmethod
    def write_string(model: Model) -> str:
        tree = SBMLWriter._model(model)
        return etree.tostring(
            tree,
            encoding='utf-8',
            method='xml',
            pretty_print=True,
        )

    @staticmethod
    def _compartment(
            compartment: Compartment,
            unit_to_str: dict
    ) -> etree.Element:
        node = etree.Element('compartment', id=compartment.sid())
        if compartment.size_units() != myokit.units.dimensionless:
            node.attrib['units'] = unit_to_str[compartment.size_units()]
        if compartment.spatial_dimensions() is not None:
            node.attrib['spatialDimensions'] = str(
                compartment.spatial_dimensions()
            )
        return node

    @staticmethod
    def _unit(sid: str, unit: myokit.Unit) -> etree.Element:
        node = etree.Element('unitDefinition', id=sid)
        kinds = [
            'gram', 'metre', 'second',
            'ampere', 'kelvin', 'candela', 'mole'
        ]
        multiplier = unit.multiplier()
        for exponent, kind in zip(unit.exponents(), kinds):
            if exponent != 0:
                child = etree.Element('unit')
                child.attrib['kind'] = kind
                child.attrib['exponent'] = str(exponent)
                if multiplier is not None:
                    child.attrib['multiplier'] = str(multiplier)
                    multiplier = None
                node.append(child)
        # might also have a dimensionless unit and a multiplier
        if multiplier is not None:
            child = etree.Element('unit')
            child.attrib['kind'] = 'dimensionless'
            child.attrib['multiplier'] = str(multiplier)
            node.append(child)
        return node

    @staticmethod
    def _parameter(
            parameter: Parameter,
            unit_to_str_map: dict
    ) -> Tuple[etree.Element, etree.Element, etree.Element]:
        """
        returns the XML representation of this parameter as a tuple of
        (parameter, initial_assignment, rule).
        """
        parameter_xml = etree.Element('parameter', id=parameter.sid())
        if (
            parameter.units() is not None and
            parameter.units() != myokit.units.dimensionless
        ):
            parameter_xml.attrib['units'] = unit_to_str_map[parameter.units()]

        if parameter.is_constant():
            parameter_xml.attrib['constant'] = 'true'

        if parameter.is_literal():
            value = parameter.value().eval()
            parameter_xml.attrib['value'] = str(value)
            return parameter_xml, None, None
        else:
            initial_assignment, rule = SBMLWriter._quantity(parameter)
            return parameter_xml, initial_assignment, rule

    @staticmethod
    def _math(expression: myokit.Expression) -> etree.Element:
        math = etree.Element(
            'math',
            xmlns='http://www.w3.org/1998/Math/MathML'
        )

        def flhs(lhs):
            var = lhs.var()
            if isinstance(var, str):
                return var
            if var.binding() == 'time':
                return "http://www.sbml.org/sbml/symbols/time"
            return var.uname()

        mathml_writer = MathMLExpressionWriter()
        mathml_writer.set_lhs_function(flhs)
        mathml_writer.ex(expression, math)
        return math

    @staticmethod
    def _quantity(quantity: Quantity) -> etree.Element:
        initial_value = quantity.initial_value()
        initial_assignment = None
        if initial_value is not None:
            initial_assignment = etree.Element(
                'initialAssignment', symbol=quantity.sid()
            )
            math = SBMLWriter._math(initial_value)
            initial_assignment.append(math)

        value = quantity.value()
        rule = None
        if value is not None:
            if quantity.is_rate():
                rule_type = 'rateRule'
            else:
                rule_type = 'assignmentRule'
            rule = etree.Element(rule_type, variable=quantity.sid())
            math = SBMLWriter._math(quantity.value())
            rule.append(math)
        return initial_assignment, rule

    @staticmethod
    def _reaction(reaction: Reaction) -> etree.Element:
        reaction_xml = etree.Element('reaction', id=reaction.sid())
        list_of_reactants = etree.Element('listOfReactants')
        for reactant in reaction.reactants():
            node = SBMLWriter._species_reference(reactant)
            list_of_reactants.append(node)
        reaction_xml.append(list_of_reactants)
        list_of_products = etree.Element('listOfProducts')
        for product in reaction.products():
            node = SBMLWriter._species_reference(product)
            list_of_products.append(node)
        reaction_xml.append(list_of_products)
        list_of_modifiers = etree.Element('listOfModifiers')
        for modifier in reaction.modifiers():
            node = SBMLWriter._modifier_species_reference(modifier)
            list_of_modifiers.append(node)
        reaction_xml.append(list_of_modifiers)
        if reaction.kinetic_law() is not None:
            kinetic_law = etree.Element('kineticLaw')
            math = SBMLWriter._math(reaction.kinetic_law())
            kinetic_law.append(math)
            reaction_xml.append(kinetic_law)
        return reaction_xml

    @staticmethod
    def _species(species: Species, unit_to_str_map: dict) -> Tuple[
        etree.Element, etree.Element
    ]:
        """
        Returns the XML representation of this species as a tuple of
        (species, rule).
        """
        species_xml = etree.Element('species', id=species.sid())
        species_xml.attrib['compartment'] = species.compartment().sid()
        initial_value, initial_value_in_amount = species.initial_value()
        if initial_value_in_amount is None:
            if species.is_amount():
                attrib_name = 'initialAmount'
            else:
                attrib_name = 'initialConcentration'
        else:
            if initial_value_in_amount:
                attrib_name = 'initialAmount'
            else:
                attrib_name = 'initialConcentration'
        if initial_value is not None:
            initial_value_eval = initial_value.eval()
            species_xml.attrib[attrib_name] = str(initial_value_eval)
        species_xml.attrib['constant'] = str(species.is_constant())
        if species.substance_units() != myokit.units.dimensionless:
            species_xml.attrib['units'] = unit_to_str_map[
                species.substance_units()
            ]
        species_xml.attrib['boundaryCondition'] = str(species.is_boundary())

        if species.value() is None:
            return species_xml, None

        if species.is_rate():
            rule_type = 'rateRule'
        else:
            rule_type = 'assignmentRule'
        rule = etree.Element(rule_type, variable=species.sid())
        math = SBMLWriter._math(species.value())
        rule.append(math)
        return species_xml, rule

    @staticmethod
    def _species_reference(ref: SpeciesReference) -> etree.Element:
        species_reference = etree.Element(
            'speciesReference',
            species=ref.species().sid()
        )
        if ref.sid() is not None:
            species_reference.attrib['id'] = ref.sid()
        value = ref.value()
        if value is not None:
            value_eval = value.eval()
            species_reference.attrib['stoichiometry'] = str(value_eval)
        return species_reference

    @staticmethod
    def _modifier_species_reference(ref: SpeciesReference) -> etree.Element:
        species_reference = etree.Element(
            'modifierSpeciesReference',
            species=ref.species().sid()
        )
        if ref.sid() is not None:
            species_reference.attrib['id'] = ref.sid()
        return species_reference

    @staticmethod
    def _model(model: Model) -> etree.ElementTree:
        root = etree.Element(
            'sbml',
            xmlns='http://www.sbml.org/sbml/level3/version2/core',
            level='3',
            version='2'
        )

        # setup a map from unit to string
        unit_map_to_str = {
            unit: string for string, unit in Model.base_units.items()
        }
        for unitid, unit in model.units().items():
            unit_map_to_str[unit] = unitid

        name = model.name() if model.name() else 'unnamed_model'
        model_root = etree.Element('model', id=name)
        if model.time_units() != myokit.units.dimensionless:
            model_root.attrib['timeUnits'] = unit_map_to_str[
                model.time_units()
            ]
        if model.area_units() != myokit.units.dimensionless:
            model_root.attrib['areaUnits'] = unit_map_to_str[
                model.area_units()
            ]
        if model.length_units() != myokit.units.dimensionless:
            model_root.attrib['lengthUnits'] = unit_map_to_str[
                model.length_units()
            ]
        if model.substance_units() != myokit.units.dimensionless:
            model_root.attrib['substanceUnits'] = unit_map_to_str[
                model.substance_units()
            ]
        if model.extent_units() != myokit.units.dimensionless:
            model_root.attrib['extentUnits'] = unit_map_to_str[
                model.extent_units()
            ]
        if model.volume_units() != myokit.units.dimensionless:
            model_root.attrib['volumeUnits'] = unit_map_to_str[
                model.volume_units()
            ]

        if model.has_units():
            list_of_units = etree.Element('listOfUnitDefinitions')
            for sid, unit in model.units().items():
                node = SBMLWriter._unit(sid, unit)
                list_of_units.append(node)
            model_root.append(list_of_units)
        if model.compartments():
            list_of_compartments = etree.Element('listOfCompartments')
            for compartment in model.compartments():
                node = SBMLWriter._compartment(compartment, unit_map_to_str)
                list_of_compartments.append(node)
            model_root.append(list_of_compartments)
        list_of_rules = etree.Element('listOfRules')
        list_of_initial_assignments = etree.Element('listOfInitialAssignments')
        if model.parameters():
            list_of_parameters = etree.Element('listOfParameters')
            for parameter in model.parameters():
                param_node, initial_value_node, rule_node = \
                    SBMLWriter._parameter(parameter, unit_map_to_str)
                list_of_parameters.append(param_node)
                if initial_value_node is not None:
                    list_of_initial_assignments.append(initial_value_node)
                if rule_node is not None:
                    list_of_rules.append(rule_node)
            model_root.append(list_of_parameters)
        if model.species_list():
            list_of_species = etree.Element('listOfSpecies')
            for species in model.species_list():
                species_node, rule_node = SBMLWriter._species(
                    species,
                    unit_map_to_str
                )
                if rule_node is not None:
                    list_of_rules.append(rule_node)
                list_of_species.append(species_node)
            model_root.append(list_of_species)
        if model.reactions():
            list_of_reactions = etree.Element('listOfReactions')
            for reaction in model.reactions():
                node = SBMLWriter._reaction(reaction)
                list_of_reactions.append(node)
            model_root.append(list_of_reactions)

        if len(list_of_initial_assignments) > 0:
            model_root.append(list_of_initial_assignments)

        if len(list_of_rules) > 0:
            model_root.append(list_of_rules)

        root.append(model_root)
        return etree.ElementTree(root)
