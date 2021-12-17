#
# Easy access to predefined myokit units.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit


def _add(name, unit, quantifiable=False, output=False):
    """
    Adds the given unit to the local namespace and registers it with the myokit
    unit system.
    """
    globals()[name] = unit
    myokit.Unit.register(name, unit, quantifiable, output)


def _rep(name):
    unit = myokit.parse_unit(name)
    myokit.Unit.register_preferred_representation(name, unit)


#
# SI myokit.Units
#
# Dimensionless
_add('dimensionless', myokit.Unit())
# Angles
_add('rad', dimensionless)
_add('radian', dimensionless)
_add('sr', dimensionless)
_add('steradian', dimensionless)
# Basic SI units
_add('kg', myokit.Unit(
    [1, 0, 0, 0, 0, 0, 0], 3), quantifiable=False, output=True)
_add('m', myokit.Unit([0, 1, 0, 0, 0, 0, 0]), quantifiable=True, output=True)
_add('s', myokit.Unit([0, 0, 1, 0, 0, 0, 0]), quantifiable=True, output=True)
_add('A', myokit.Unit([0, 0, 0, 1, 0, 0, 0]), quantifiable=True, output=True)
_add('K', myokit.Unit([0, 0, 0, 0, 1, 0, 0]), quantifiable=True, output=True)
_add('cd', myokit.Unit([0, 0, 0, 0, 0, 1, 0]), quantifiable=True, output=True)
_add('mol', myokit.Unit([0, 0, 0, 0, 0, 0, 1]), quantifiable=True, output=True)
# SI unit aliases
_add('kilogram', kg)
_add('metre', m)
_add('meter', m)
_add('second', s)
_add('ampere', A)
_add('Ampere', A)
_add('kelvin', K)
_add('Kelvin', K)
_add('candela', cd)
_add('mole', mol)
# Derived SI units
# The SI units are added in lowercase, as specified by the SI
# The SI units that are derived from names are also added capitalized, as this
# is a common enough mistake...
_add('Hz', 1 / s, quantifiable=True, output=True)
_add('hertz', Hz)       # frequency
_add('Hertz', Hz)
_add('N', kg * m / s**2, quantifiable=True, output=True)
_add('newton', N)       # force
_add('Newton', N)
_add('Pa', N / m**2, quantifiable=True, output=True)
_add('pascal', Pa)      # pressure
_add('Pascal', Pa)
_add('J', N * m, quantifiable=True, output=True)
_add('joule', J)        # energy
_add('Joule', J)
_add('W', J / s, quantifiable=True, output=True)
_add('watt', W)         # power
_add('Watt', W)
_add('C', s * A, quantifiable=True, output=True)
_add('coulomb', C)      # charge
_add('Coulomb', C)
_add('V', J / C, quantifiable=True, output=True)
_add('volt', V)         # electric potential
_add('Volt', V)
_add('F', C / V, quantifiable=True, output=True)
_add('farad', F)        # electric capacitance
_add('Farad', F)
_add('Ohm', V / A, quantifiable=True, output=True)
_add('ohm', Ohm)        # electric resistance
_add('R', Ohm, quantifiable=True)   # Legacy: Deprecated on May 26th 2020
_add('S', 1 / R, quantifiable=True, output=True)
_add('siemens', S)      # siemens (electric conductivity)
_add('Siemens', S)
_add('Wb', J / A, quantifiable=True, output=True)
_add('weber', Wb)       # magnetic flux
_add('Weber', Wb)
_add('T', Wb / m**2, quantifiable=True, output=True)
_add('tesla', T)        # magnetic flux
_add('Tesla', T)
_add('H', Wb / A, quantifiable=True, output=True)
_add('henry', H)        # magnetic field strength
_add('Henry', H)
_add('lm', cd * sr, quantifiable=True, output=True)
_add('lumen', lm)       # Luminous flux
_add('lx', lm / m**2, quantifiable=True, output=True)
_add('lux', lx)         # Illuminance
_add('Bq', 1 / s, quantifiable=True, output=True)
_add('becquerel', Bq)    # radioactive decays / s
_add('Becquerel', Bq)
_add('Gy', J / kg, quantifiable=True, output=True)
_add('gray', Gy)        # absorbed dose of ionizing radiation
_add('Gray', Gy)
_add('Sv', J / kg, quantifiable=True, output=True)
_add('sievert', Sv)     # equivalent dose of ionizing radiation
_add('Sievert', Sv)
_add('kat', mol / s, quantifiable=True, output=True)
_add('katal', kat)      # catalytic activity
# Commonly quantified SI units
_add('g', kg * 1e-3, quantifiable=True, output=True)
_add('km', m * 1e3, output=True)
_add('hm', m * 1e2, output=False)
_add('dm', m * 1e-1, output=False)
_add('cm', m * 1e-2, output=True)
_add('mm', m * 1e-3, output=True)
_add('um', m * 1e-6, output=True)
_add('nm', m * 1e-9, output=True)
_add('mmol', mol * 1e-3, output=True)
_add('umol', mol * 1e-6, output=True)
_add('nmol', mol * 1e-9, output=True)
_add('ms', s * 1e-3, output=True)
_add('us', s * 1e-6, output=True)
_add('mV', V * 1e-3, output=True)
_add('uV', V * 1e-6, output=True)
_add('mA', A * 1e-3, output=True)
_add('uA', A * 1e-6, output=True)
_add('nA', A * 1e-9, output=True)
_add('pA', A * 1e-12, output=True)
_add('mF', F * 1e-3, output=True)
_add('uF', F * 1e-6, output=True)
_add('nF', F * 1e-9, output=True)
_add('pF', F * 1e-12, output=True)
_add('mS', S * 1e-3, output=True)
_add('uS', S * 1e-6, output=True)
_add('nS', S * 1e-9, output=True)
_add('pS', S * 1e-12, output=True)
_add('MOhm', Ohm * 1e6, output=True)
_add('GOhm', Ohm * 1e9, output=True)

#
# Common non-SI units
#
# Common time measures
_add('minute', s * 60)
_add('hour', minute * 60)
_add('hr', hour)
_add('h', hour)
_add('day', hour * 24)
_add('week', day * 7)
_add('wk', week)
_add('julian_year', day * 365.25)
_add('year', julian_year)
_add('yr', year)
# Distance
_add('parsec', m * 30.857e15)
_add('pc', parsec)
_add('light_year', m * 9.4605284e15)    # based on julian year
_add('ly', light_year)
_add('angstrom', m / 1e10)
# Area
_add('hectare', hm**2)      # ha
# Volume
_add('L', dm**3, quantifiable=True, output=True)
_add('liter', L)
_add('litre', L)
_add('cc', cm**3)
# Weight / Mass
_add('Da', kg * 1.66053886e-27, quantifiable=True, output=True)
_add('dalton', Da)
_add('tonne', kg * 1e3)
# Pressure
_add('bar', Pa * 1e5)
_add('atm', 1.01325 * bar)
_add('torr', atm / 760)     # Approx. equal to 1 mmHg
# Concentration
_add('M', mol / L, quantifiable=True, output=True)
_add('molar', M)
#
# Imperial units (international version)
#
# For imperial units its customary to use the plural (7 feet, 12 yards etc)
#
# 1959: Yard defined as exactly 0.9144m. Others can be related to yard. But
# 0.9144 / 3 / 12', 0.0254 exactly, so you can build it from a 2.54cm inch as
# well.
#
_add('inches', cm * 2.54)       # in, or "
_add('thou', inches / 1000)
_add('feet', inches * 12)       # ft, or '
_add('yards', feet * 3)         # yd
_add('chains', yards * 22)
_add('furlongs', chains * 10)
_add('miles', furlongs * 8)     # 8 * 10 * 22', 1760 yards
_add('leagues', miles * 3)
_add('nautical_miles', feet * 6080)
_add('cables', nautical_miles / 10)
_add('fathoms', cables / 100)   # commonly rounded to 6 foot
# Surveying units:
_add('rods', chains / 4)
_add('links', rods / 25)
_add('perches', rods * rods)
_add('roods', furlongs * rods)
_add('acres', furlongs * chains)
# Volumes
_add('gallons', 4.54609 * litre)
_add('quarts', gallons / 4)
_add('pints', quarts / 2)
_add('half_pints', pints / 2)
_add('gills', pints / 4)
_add('fluid_ounces', pints / 20)
_add('floz', fluid_ounces)
# Mass (but not for precious metals)
_add('pounds', 453.59237 * g)   # By definition
_add('lb', pounds)
_add('ounces', pounds / 16)
_add('oz', ounces)
_add('drachms', ounces / 16)
_add('grains', pounds / 7000)   # Originally the weight of a grain of cereal
_add('stones', pounds * 14)
_add('quarters', stones * 2)            # 1/4 of a hundredweight
_add('hundredweights', quarters * 4)    # 8 stone, 112 pounds
_add('imp_tons', 20 * hundredweights)
#
# Not-so-common units
#
_add('dog_year', julian_year / 7)
_add('forthnight', 14 * day)
_add('smoot', (5 + 7 / 12) * feet)
#
# Preferred representation for (un)common electrophysiological units
#
# Sizes and speeds
_rep('1/ms')
_rep('1/m')
_rep('1/cm')
_rep('1/mm')
_rep('cm^2')
_rep('cm^3')
_rep('cm^2/s')
_rep('cm^3/s')
_rep('cm/s')
_rep('cm/ms')
_rep('mm^2')
_rep('mm^3')
_rep('um^2')
_rep('um^3')
_rep('nm^2')
_rep('nm^3')
# _rep('m/s')
# Litres
_rep('mL')
_rep('uL')
_rep('nL')
_rep('pL')
# Concentrations
_rep('M')
_rep('mM')
_rep('mM^2')
_rep('mM^3')
_rep('uM')
_rep('1/mM/ms')
_rep('1/mM^2/ms')
_rep('mM/ms')
_rep('mM/mV/ms')
# Voltages
_rep('1/mV')
_rep('1/mV^2')
_rep('1/mV/ms')
_rep('ms/mV')
_rep('mV^2')
# Currents
_rep('A/F')
_rep('nA/cm^2')
_rep('uA/cm^2')
_rep('pA/cm^2')
# Conductances and permeability
_rep('S/F')
_rep('mS/uF')
_rep('mS/cm^2')
_rep('mS/mm^2')
_rep('L/F/ms')
_rep('mA/cm^2')
# Capacitance
_rep('cm^2/uF')
_rep('uF/cm^2')
_rep('uF/mm^2')
_rep('uF*mol/C')
# Various
_rep('J/mol/K')
_rep('mJ/mol/K')
_rep('C/mol')
_rep('C/mmol')
