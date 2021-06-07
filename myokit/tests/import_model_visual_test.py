from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
import myokit.formats.sbml as sbml

PK_model = sbml.SBMLImporter().model("/home/rumney/Documents/PK_two_comp.xml")
PD_model = sbml.SBMLImporter().model("/home/rumney/Documents/PD_myelotoxicity_friberg_model.xml")
Full_PKPD_model = sbml.SBMLImporter().model("/home/rumney/Documents/PKPD_myelotoxicity_friberg_model.xml")

print("----------------PK Model---------------------")
print(PK_model.code())
print("----------------PD Model---------------------")
print(PD_model.code())
print("----------------PKPD Model (from SBML)----------------------")
print(Full_PKPD_model.code())

print("----------------PKPD Model (from import function)----------------------")

drug_effect_compartment = 'central'
auto_PKPD_model = PD_model.clone()
var_map = {}
temp = auto_PKPD_model.add_component('Temp')
PK_model.create_unique_names()
for var in PK_model.variables():
    # for name in var.qname().split('.'):
    #     x = x + '_' + name
    temp_var = temp.add_variable(var.uname())
    temp_var.set_unit(unit=var.unit())
    var_map[var.qname()] = temp_var.qname()
var_map[drug_effect_compartment + '.drug_c_concentration'] = 'myokit.drug_concentration'

for component in PK_model.components():
    if component.name() == 'myokit':
        auto_PKPD_model.import_component(component, new_name='PK', var_map=var_map, convert_units=True, allow_name_mapping=True)
        for var in component.variables():
            var_map[var.qname()] = 'PK.' + var.name()
    else:
        auto_PKPD_model.import_component(component, var_map=var_map, convert_units=True, allow_name_mapping=True)
        for var in component.variables():
            var_map[var.qname()] = var.qname()

auto_PKPD_model.remove_component(temp)

print(auto_PKPD_model.code()) 
print(auto_PKPD_model.validate())
print(auto_PKPD_model.warnings())

p = myokit.load_protocol('/home/rumney/Documents/TwoCompModelTest/protocol_New.mmt')#path for the protocol file(e.g. dose regimen)

sim_full = myokit.Simulation(Full_PKPD_model, p)  # set up myokit model: input model and protocol
d_full = sim_full.run(10)

sim_auto = myokit.Simulation(auto_PKPD_model, p)  # set up myokit model: input model and protocol
d_auto = sim_auto.run(10)

import matplotlib.pyplot as plt
# plt.figure()
# plt.plot(d_man['environment.t'], d_man['PD.biomarker_conc'], label="wthout import component")
# plt.plot(d_auto['environment.t'], d_auto['PD.biomarker_conc'], label="with import component")
# plt.legend()
# plt.show()

# print(m1.code())
