from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import pickle
import unittest

import myokit

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
Auto_PKPD_model.import_component(PD_model["PD"])
print(Auto_PKPD_model.code())