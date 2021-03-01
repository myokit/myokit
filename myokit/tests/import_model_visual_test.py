from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import pickle
import unittest

import myokit
import numpy as np

from shared import TemporaryDirectory, WarningCollector

PK_model = myokit.load_model("/home/rumney/Documents/TwoCompModelTest/TwoCompartment_IV_Model.mmt")
PD_model = myokit.load_model("/home/rumney/Documents/TwoCompModelTest/Generic_PD.mmt")
manual_PKPD_model = myokit.load_model("/home/rumney/Documents/TwoCompModelTest/Generic_PKPD.mmt")

print(PK_model.code())
print("--------------------------------------")
print(PD_model.code())
print("--------------------------------------")
print(manual_PKPD_model.code())
print("----------------Import Component Function----------------------")

Auto_PKPD_model = PK_model.clone()
Auto_PKPD_model.import_component(PD_model["PD"], var_map={PD_model["tempPK"]["Drug_Concentration_Central"]:Auto_PKPD_model["AllCompartment"]["Drug_Concentration_Central"]})
print(Auto_PKPD_model.code())

print(Auto_PKPD_model.validate())
print(Auto_PKPD_model.warnings())

p = myokit.load_protocol('/home/rumney/Documents/TwoCompModelTest/protocol_New.mmt')#path for the protocol file(e.g. dose regimen)

print("manual")
sim_man = myokit.Simulation(manual_PKPD_model, p) #set up myokit model: input model and protocol 
d_man = sim_man.run(10)


print("automatic")
sim_auto = myokit.Simulation(Auto_PKPD_model, p) #set up myokit model: input model and protocol 
d_auto = sim_auto.run(10)

import matplotlib.pyplot as plt
plt.figure()
plt.plot(d_man['environment.t'], d_man['PD.biomarker_conc'], label="wthout import component")
plt.plot(d_auto['environment.t'], d_auto['PD.biomarker_conc'], label="with import component")
plt.legend()
plt.show()