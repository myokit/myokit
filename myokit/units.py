#
# Easy access to predefined myokit units.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit


def _ra(name, *aliases, quantifiable=False, output=False):
    """
    Registers a unit with the myokit unit system.

    Any aliases will also be registered, using
    ``quantifiable = output = False`` regardless of the setting for ``name``.
    """
    myokit.Unit.register(name, globals()[name], quantifiable, output)
    for alias in aliases:
        myokit.Unit.register(alias, globals()[alias], False, False)


def _rm(*names, quantifiable=False, output=False):
    """
    Registers multiple units with the given ``quantifiable`` and ``output``
    settings.
    """
    for name in names:
        myokit.Unit.register(name, globals()[name], quantifiable, output)


def _rep(name):
    unit = myokit.parse_unit(name)
    myokit.Unit.register_preferred_representation(name, unit)


#
# SI myokit.Units
#

# Dimensionless and angles
dimensionless = myokit.Unit()
rad = radian = sr = steradian = dimensionless
_ra('dimensionless', 'rad', 'radian', 'sr', 'steradian')

# Basic SI units (and g) and aliases
g = myokit.Unit([1, 0, 0, 0, 0, 0, 0])
m = myokit.Unit([0, 1, 0, 0, 0, 0, 0])
s = myokit.Unit([0, 0, 1, 0, 0, 0, 0])
A = myokit.Unit([0, 0, 0, 1, 0, 0, 0])
K = myokit.Unit([0, 0, 0, 0, 1, 0, 0])
cd = myokit.Unit([0, 0, 0, 0, 0, 1, 0])
mol = myokit.Unit([0, 0, 0, 0, 0, 0, 1])
kg = kilogram = g * 1e3
metre = meter = m
second = s
ampere = Ampere = A
kelvin = Kelvin = K
candela = cd
mole = mol
_ra('kg', 'kilogram', quantifiable=False, output=True)
_ra('g', quantifiable=True, output=True)
_ra('m', 'metre', 'meter', quantifiable=True, output=True)
_ra('s', 'second', quantifiable=True, output=True)
_ra('A', 'ampere', 'Ampere', quantifiable=True, output=True)
_ra('K', 'kelvin', 'Kelvin', quantifiable=True, output=True)
_ra('cd', 'candela', quantifiable=True, output=True)
_ra('mol', 'mole', quantifiable=True, output=True)

# Derived SI units
# The SI units are added in lowercase, as specified by the SI
# The SI units that are derived from names are also added capitalized, as this
# is a common enough mistake...
Hz = hertz = Hertz = 1 / s
N = newton = Newton = kg * m / s**2
Pa = pascal = Pascal = N / m**2
J = joule = Joule = N * m
W = watt = Watt = J / s
C = coulomb = Coulomb = s * A
V = volt = Volt = J / C
F = farad = Farad = C / V
ohm = Ohm = V / A
S = siemens = Siemens = 1 / ohm
Wb = weber = Weber = J / A      # magnetic flux
T = tesla = Tesla = Wb / m**2       # magnetic flux
H = henry = Henry = Wb / A          # magnetic field strength
lm = lumen = cd * sr                # Luminous flux
lx = lux = lm / m**2                # Illuminance
Bq = becquerel = Becquerel = 1 / s  # radioactive decays / s
Gy = gray = Gray = J / kg           # absorbed dose of ionizing radiation
Sv = sievert = Sievert = J / kg     # equivalent dose of ionizing radiation
kat = katal = mol / s   # catalytic activity
_ra('Hz', 'hertz', 'Hertz', quantifiable=True, output=True)
_ra('N', 'newton', 'Newton', quantifiable=True, output=True)
_ra('Pa', 'pascal', 'Pascal', quantifiable=True, output=True)
_ra('J', 'joule', 'Joule', quantifiable=True, output=True)
_ra('W', 'watt', 'Watt', quantifiable=True, output=True)
_ra('C', 'coulomb', 'Coulomb', quantifiable=True, output=True)
_ra('V', 'volt', 'Volt', quantifiable=True, output=True)
_ra('F', 'farad', 'Farad', quantifiable=True, output=True)
_ra('S', 'siemens', 'Siemens', quantifiable=True, output=True)
_ra('Wb', 'weber', 'Weber', quantifiable=True, output=True)
_ra('T', 'tesla', 'Tesla', quantifiable=True, output=True)
_ra('H', 'henry', 'Henry', quantifiable=True, output=True)
_ra('lm', 'lumen', quantifiable=True, output=False)
_ra('lx', 'lux', quantifiable=True, output=True)
_ra('Bq', 'becquerel', 'Becquerel', quantifiable=True, output=True)
_ra('Gy', 'gray', 'Gray', quantifiable=True, output=True)
_ra('Sv', 'sievert', 'Sievert', quantifiable=True, output=True)
_ra('kat', 'katal', quantifiable=True, output=True)
# For Ohm allow correct "ohm" and incorrect "Ohm" to be quantifiable
_ra('ohm', quantifiable=True, output=True)
_ra('Ohm', quantifiable=True)

# Commonly quantified SI units
km = m * 1e3
hm = m * 1e2
dm = m * 1e-1
cm = m * 1e-2
mm = m * 1e-3
um = m * 1e-6
nm = m * 1e-9
_rm('km', 'cm', 'mm', 'um', 'nm', output=True)
_rm('hm', 'dm')
mmol = mol * 1e-3
umol = mol * 1e-6
nmol = mol * 1e-9
_rm('mmol', 'umol', 'nmol', output=True)
ms = s * 1e-3
us = s * 1e-6
_rm('ms', 'us', output=True)
mV = V * 1e-3
uV = V * 1e-6
_rm('mV', 'uV', output=True)
mA = A * 1e-3
uA = A * 1e-6
nA = A * 1e-9
pA = A * 1e-12
_rm('mA', 'uA', 'nA', 'pA', output=True)
mF = F * 1e-3
uF = F * 1e-6
nF = F * 1e-9
pF = F * 1e-12
_rm('mF', 'uF', 'nF', 'pF', output=True)
mS = S * 1e-3
uS = S * 1e-6
nS = S * 1e-9
pS = S * 1e-12
_rm('mS', 'uS', 'nS', 'pS', output=True)
Mohm = MOhm = Ohm * 1e6
Gohm = GOhm = Ohm * 1e9
_ra('Mohm', 'MOhm', output=True)
_ra('Gohm', 'GOhm', output=True)

#
# Common non-SI units
#

# Time
minute = s * 60
hour = hr = h = minute * 60
day = hour * 24
week = wk = day * 7
year = yr = julian_year = day * 365.25
_rm('minute', 'hour', 'hr', 'h', 'day', 'week', 'wk')
_rm('year', 'yr', 'julian_year')

# Distance
parsec = pc = m * 30.857e15
light_year = ly = m * 9.4605284e15  # based on julian year
angstrom = m / 1e10
_rm('parsec', 'pc', 'light_year', 'ly', 'angstrom')

# Area
hectare = hm**2
_rm('hectare')

# Volume
L = liter = litre = dm**3
_ra('L', 'liter', 'litre', quantifiable=True, output=True)
cc = cm**3
_rm('cc')

# Weight / Mass
Da = dalton = kg * 1.66053886e-27
_ra('Da', 'dalton', quantifiable=True, output=True)
tonne = kg * 1e3
_rm('tonne')

# Pressure
bar = Pa * 1e5
atm = 1.01325 * bar
torr = atm / 760        # Approx. equal to 1 mmHg
_rm('bar', 'atm', 'torr')

# Concentration
M = molar = mol / L
_ra('M', 'molar', quantifiable=True, output=True)

#
# Imperial units (international version)
#
# For imperial units its customary to use the plural (7 feet, 12 yards etc)
#
# 1959: Yard defined as exactly 0.9144m. Others can be related to yard. But
# 0.9144 / 3 / 12', 0.0254 exactly, so you can build it from a 2.54cm inch as
# well.
#

# Distance
inches = cm * 2.54      # in, or "
thou = inches / 1000
feet = inches * 12      # ft, or '
yards = feet * 3        # yd
chains = yards * 22
furlongs = chains * 10
miles = furlongs * 8    # 8 * 10 * 22 = 1760 yards
leagues = miles * 3
nautical_miles = feet * 6080
cables = nautical_miles / 10
fathoms = cables / 100  # commonly rounded to 6 foot
_rm('inches', 'thou', 'feet', 'yards', 'chains', 'furlongs', 'miles',
    'leagues', 'nautical_miles', 'cables', 'fathoms')

# Surveying units
rods = chains / 4
links = rods / 25
perches = rods * rods
roods = furlongs * rods
acres = furlongs * chains
_rm('rods', 'links', 'perches', 'roods', 'acres')

# Volumes
gallons = 4.54609 * litre
quarts = gallons / 4
pints = quarts / 2
half_pints = pints / 2
gills = pints / 4
fluid_ounces = pints / 20
floz = fluid_ounces
_rm('gallons', 'quarts', 'pints', 'half_pints', 'gills', 'fluid_ounces',
    'floz')

# Mass (but not for precious metals)
pounds = 453.59237 * g  # By definition
lb = pounds
ounces = pounds / 16
oz = ounces
drachms = ounces / 16
grains = pounds / 7000  # Originally the weight of a grain of cereal
stones = pounds * 14
quarters = stones * 2           # 1/4 of a hundredweight
hundredweights = quarters * 4   # 8 stone, 112 pounds
imp_tons = 20 * hundredweights
_rm('pounds', 'lb', 'ounces', 'oz', 'drachms', 'grains', 'stones', 'quarters',
    'hundredweights', 'imp_tons')

# Just for fun
#
dog_year = julian_year / 7
forthnight = 14 * day
smoot = (5 + 7 / 12) * feet
_rm('dog_year', 'forthnight', 'smoot')

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
_rep('mM^4')
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
_rep('L/F/s')
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
_rep('J/K')  # Boltzmann
_rep('J*s')  # Planck
_rep('J*ms')
