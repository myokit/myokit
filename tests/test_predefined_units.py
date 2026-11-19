#!/usr/bin/env python3
#
# Tests all the predefined units are correct.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit
import myokit.units as u


class MyokitPredefinedUnitsTest(unittest.TestCase):

    def assertParses(self, text, unit, *aliases, shadowed_by=None):
        """
        Test that ``text`` parses to ``unit``, and ``unit`` is represented as
        ``text`` and quantifiable.

        If aliases are given it checks that these parse to the same unit, are
        represented as the original unit, and are not quantifiable.
        """
        # Test parsing
        self.assertEqual(myokit.parse_unit(text), unit)

        # Test string representation
        t = f'[{text}]' if shadowed_by is None else f'[{shadowed_by}]'
        self.assertEqual(str(unit), t)

        # Test quantifiable
        self.assertEqual(myokit.parse_unit(f'm{text}'), unit * 1e-3)

        # Test aliases
        for alias in aliases:
            r = myokit.parse_unit(alias)
            self.assertEqual(r, unit)
            self.assertEqual(str(r), t)
            self.assertRaisesRegex(
                myokit.ParseError, f'Unit "{alias}" cannot have quantifier',
                myokit.parse_unit, f'k{alias}')

    def test_dimensionless(self):
        # Test dimensionless and its variants
        self.assertEqual(u.dimensionless.exponents(), [0, 0, 0, 0, 0, 0, 0])

        self.assertEqual(u.dimensionless, u.rad)
        self.assertEqual(u.dimensionless, u.radian)
        self.assertEqual(u.dimensionless, u.steradian)
        self.assertEqual(u.dimensionless, u.sr)

        self.assertEqual(myokit.parse_unit('dimensionless'), u.dimensionless)
        self.assertEqual(myokit.parse_unit('rad'), u.dimensionless)
        self.assertEqual(myokit.parse_unit('radian'), u.dimensionless)
        self.assertEqual(myokit.parse_unit('steradian'), u.dimensionless)
        self.assertEqual(myokit.parse_unit('sr'), u.dimensionless)
        self.assertEqual(str(u.dimensionless), '[1]')
        self.assertEqual(str(u.rad), '[1]')
        self.assertEqual(str(u.radian), '[1]')
        self.assertEqual(str(u.steradian), '[1]')
        self.assertEqual(str(u.sr), '[1]')

        self.assertRaisesRegex(
            myokit.ParseError, 'Unit "dimensionless" cannot have quantifier',
            myokit.parse_unit, 'Mdimensionless')
        self.assertRaisesRegex(
            myokit.ParseError, 'Unit "rad" cannot have quantifier',
            myokit.parse_unit, 'krad')
        self.assertRaisesRegex(
            myokit.ParseError, 'Unit "radian" cannot have quantifier',
            myokit.parse_unit, 'cradian')
        self.assertRaisesRegex(
            myokit.ParseError, 'Unit "steradian" cannot have quantifier',
            myokit.parse_unit, 'ksteradian')
        self.assertRaisesRegex(
            myokit.ParseError, 'Unit "sr" cannot have quantifier',
            myokit.parse_unit, 'Gsr')

    def test_si(self):
        # Basic SI units
        self.assertEqual([1, 0, 0, 0, 0, 0, 0], u.kg.exponents())
        self.assertEqual([0, 1, 0, 0, 0, 0, 0], u.m.exponents())
        self.assertEqual([0, 0, 1, 0, 0, 0, 0], u.s.exponents())
        self.assertEqual([0, 0, 0, 1, 0, 0, 0], u.A.exponents())
        self.assertEqual([0, 0, 0, 0, 1, 0, 0], u.K.exponents())
        self.assertEqual([0, 0, 0, 0, 0, 1, 0], u.cd.exponents())
        self.assertEqual([0, 0, 0, 0, 0, 0, 1], u.mol.exponents())

        self.assertEqual(u.kg.multiplier_log_10(), 3)
        self.assertEqual(u.m.multiplier_log_10(), 0)
        self.assertEqual(u.s.multiplier_log_10(), 0)
        self.assertEqual(u.A.multiplier_log_10(), 0)
        self.assertEqual(u.K.multiplier_log_10(), 0)
        self.assertEqual(u.cd.multiplier_log_10(), 0)
        self.assertEqual(u.mol.multiplier_log_10(), 0)

        self.assertEqual(myokit.parse_unit('kg'), u.kg)
        self.assertEqual(myokit.parse_unit('m'), u.m)
        self.assertEqual(myokit.parse_unit('s'), u.s)
        self.assertEqual(myokit.parse_unit('A'), u.A)
        self.assertEqual(myokit.parse_unit('K'), u.K)
        self.assertEqual(myokit.parse_unit('cd'), u.cd)
        self.assertEqual(myokit.parse_unit('mol'), u.mol)

        self.assertEqual(str(u.kg), '[kg]')
        self.assertEqual(str(u.m), '[m]')
        self.assertEqual(str(u.s), '[s]')
        self.assertEqual(str(u.A), '[A]')
        self.assertEqual(str(u.K), '[K]')
        self.assertEqual(str(u.cd), '[cd]')
        self.assertEqual(str(u.mol), '[mol]')

        # Deal with kg/g weirdness
        self.assertEqual([1, 0, 0, 0, 0, 0, 0], u.g.exponents())
        self.assertEqual(u.g.multiplier_log_10(), 0)
        self.assertEqual(myokit.parse_unit('mg').multiplier_log_10(), -3)
        self.assertEqual(str(u.g), '[g]')
        self.assertRaisesRegex(
            myokit.ParseError, 'Unit "kg" cannot have quantifier',
            myokit.parse_unit, 'mkg')

    def test_si_alias(self):
        # Aliases of SI units
        self.assertEqual(u.kilogram, u.kg)
        self.assertEqual(u.meter, u.m)
        self.assertEqual(u.metre, u.m)
        self.assertEqual(u.second, u.s)
        self.assertEqual(u.ampere, u.A)
        self.assertEqual(u.Ampere, u.A)
        self.assertEqual(u.kelvin, u.K)
        self.assertEqual(u.Kelvin, u.K)
        self.assertEqual(u.candela, u.cd)
        self.assertEqual(u.mole, u.mol)

        self.assertEqual(myokit.parse_unit('kilogram'), u.kg)
        self.assertEqual(myokit.parse_unit('meter'), u.m)
        self.assertEqual(myokit.parse_unit('meter'), u.m)
        self.assertEqual(myokit.parse_unit('second'), u.s)
        self.assertEqual(myokit.parse_unit('ampere'), u.A)
        self.assertEqual(myokit.parse_unit('Ampere'), u.A)
        self.assertEqual(myokit.parse_unit('kelvin'), u.K)
        self.assertEqual(myokit.parse_unit('Kelvin'), u.K)
        self.assertEqual(myokit.parse_unit('candela'), u.cd)
        self.assertEqual(myokit.parse_unit('mole'), u.mol)

    def test_si_derived(self):
        # Derived SI units

        self.assertEqual(u.Hz, 1 / u.s)
        self.assertEqual(u.hertz, u.Hz)
        self.assertEqual(u.Hertz, u.Hz)
        self.assertEqual(u.N, u.kg * u.m / u.s**2)
        self.assertEqual(u.newton, u.N)
        self.assertEqual(u.Newton, u.N)
        self.assertEqual(u.Pa, u.N / u.m**2)
        self.assertEqual(u.pascal, u.Pa)
        self.assertEqual(u.Pascal, u.Pa)
        self.assertEqual(u.J, u.N * u.m)
        self.assertEqual(u.joule, u.J)
        self.assertEqual(u.Joule, u.J)
        self.assertEqual(u.W, u.J / u.s)
        self.assertEqual(u.watt, u.W)
        self.assertEqual(u.Watt, u.W)
        self.assertEqual(u.C, u.s * u.A)
        self.assertEqual(u.coulomb, u.C)
        self.assertEqual(u.Coulomb, u.C)
        self.assertEqual(u.V, u.J / u.C)
        self.assertEqual(u.volt, u.V)
        self.assertEqual(u.Volt, u.V)
        self.assertEqual(u.F, u.C / u.V)
        self.assertEqual(u.farad, u.F)
        self.assertEqual(u.Farad, u.F)
        self.assertEqual(u.ohm, u.V / u.A)
        self.assertEqual(u.Ohm, u.ohm)
        self.assertEqual(u.S, 1 / u.ohm)
        self.assertEqual(u.siemens, u.S)
        self.assertEqual(u.Siemens, u.S)
        self.assertEqual(u.Wb, u.J / u.A)
        self.assertEqual(u.weber, u.Wb)
        self.assertEqual(u.Weber, u.Wb)
        self.assertEqual(u.T, u.Wb / u.m**2)
        self.assertEqual(u.tesla, u.T)
        self.assertEqual(u.Tesla, u.T)
        self.assertEqual(u.H, u.Wb / u.A)
        self.assertEqual(u.henry, u.H)
        self.assertEqual(u.Henry, u.H)

        self.assertEqual(u.lm, u.cd)  # Not output
        self.assertEqual(u.lumen, u.lm)
        self.assertEqual(u.lx, u.lm / u.m**2)
        self.assertEqual(u.lux, u.lx)
        self.assertEqual(u.Bq, 1 / u.s)
        self.assertEqual(u.becquerel, u.Bq)
        self.assertEqual(u.Becquerel, u.Bq)
        self.assertEqual(u.Gy, u.J / u.kg)
        self.assertEqual(u.gray, u.Gy)
        self.assertEqual(u.Gray, u.Gy)
        self.assertEqual(u.Sv, u.J / u.kg)
        self.assertEqual(u.sievert, u.Sv)
        self.assertEqual(u.Sievert, u.Sv)
        self.assertEqual(u.kat, u.mol / u.s)
        self.assertEqual(u.katal, u.kat)

        self.assertParses('Hz', u.Hz, 'hertz', 'Hertz', shadowed_by='S/F')
        self.assertParses('N', u.N, 'newton', 'Newton')
        self.assertParses('Pa', u.Pa, 'pascal', 'Pascal')
        self.assertParses('J', u.J, 'joule', 'Joule')
        self.assertParses('W', u.W, 'watt', 'Watt')
        self.assertParses('C', u.C, 'coulomb', 'Coulomb')
        self.assertParses('V', u.V, 'volt', 'Volt')
        self.assertParses('F', u.F, 'farad', 'Farad')
        self.assertParses('S', u.S, 'siemens', 'Siemens')
        self.assertParses('Wb', u.Wb, 'weber', 'Weber')
        self.assertParses('T', u.T, 'tesla', 'Tesla')
        self.assertParses('H', u.H, 'henry', 'Henry')

        self.assertParses('lm', u.lm, 'lumen', shadowed_by='cd')
        self.assertParses('lx', u.lx, 'lux')
        self.assertParses('Bq', u.Bq, 'becquerel', 'Becquerel',
                          shadowed_by='S/F')
        self.assertParses('Gy', u.Gy, 'gray', 'Gray', shadowed_by='Sv')
        self.assertParses('Sv', u.Sv, 'sievert', 'Sievert')
        self.assertParses('kat', u.kat, 'katal')

        # For ohm/Ohm we allow both to be quantifiable
        self.assertParses('ohm', u.ohm)
        self.assertEqual(myokit.parse_unit('Ohm'), u.ohm)
        self.assertEqual(myokit.parse_unit('mOhm'), u.ohm * 1e-3)

    def test_si_quantified(self):
        # Quantified aliases of SI units

        def test(quantified, units, text, output=True):
            self.assertEqual(quantified, units)

            if output:
                self.assertEqual(str(quantified), f'[{text}]')
            else:
                self.assertNotEqual(str(quantified), f'[{text}]')

            self.assertRaisesRegex(
                myokit.ParseError, 'cannot have quantifier',
                myokit.parse_unit, f'm{text}')

        test(u.km, u.m * 1e3, 'km')
        test(u.hm, u.m * 1e2, 'hm', False)
        test(u.dm, u.m * 1e-1, 'dm', False)
        test(u.cm, u.m * 1e-2, 'cm')
        test(u.mm, u.m * 1e-3, 'mm')
        test(u.um, u.m * 1e-6, 'um')
        test(u.nm, u.m * 1e-9, 'nm')
        test(u.mmol, u.mol * 1e-3, 'mmol')
        test(u.umol, u.mol * 1e-6, 'umol')
        test(u.nmol, u.mol * 1e-9, 'nmol')
        test(u.ms, u.s * 1e-3, 'ms')
        test(u.us, u.s * 1e-6, 'us')
        test(u.mV, u.V * 1e-3, 'mV')
        test(u.uV, u.V * 1e-6, 'uV')
        test(u.mA, u.A * 1e-3, 'mA')
        test(u.uA, u.A * 1e-6, 'uA')
        test(u.nA, u.A * 1e-9, 'nA')
        test(u.pA, u.A * 1e-12, 'pA')
        test(u.mF, u.F * 1e-3, 'mF')
        test(u.uF, u.F * 1e-6, 'uF')
        test(u.nF, u.F * 1e-9, 'nF')
        test(u.pF, u.F * 1e-12, 'pF')
        test(u.mS, u.S * 1e-3, 'mS')
        test(u.uS, u.S * 1e-6, 'uS')
        test(u.nS, u.S * 1e-9, 'nS')
        test(u.pS, u.S * 1e-12, 'pS')
        test(u.Mohm, u.ohm * 1e6, 'Mohm')
        test(u.Gohm, u.ohm * 1e9, 'Gohm')

    def test_non_si(self):
        # Non-SI units

        def test(name, units, equivalent, output=False, quantifiable=False):
            self.assertEqual(myokit.parse_unit(name), units)
            self.assertEqual(units, equivalent)

            if output:
                self.assertEqual(str(units), f'[{name}]')
            else:
                self.assertNotEqual(str(units), f'[{name}]')

            if quantifiable:
                r = myokit.parse_unit(f'k{name}')
                self.assertEqual(r, 1000 * units)
            else:
                self.assertRaisesRegex(
                    myokit.ParseError, 'cannot have quantifier',
                    myokit.parse_unit, f'm{name}')

        test('L', u.L, u.dm**3, True, True)
        test('liter', u.liter, u.L)
        test('litre', u.litre, u.L)

        test('Da', u.Da, u.kg * 1.66053886e-27, True, True)
        test('dalton', u.dalton, u.Da)

        test('M', u.M, u.mol / u.L, True, True)
        test('molar', u.molar, u.M)

        test('minute', u.minute, u.s * 60)
        test('hour', u.hour, u.minute * 60)
        test('hr', u.hr, u.minute * 60)
        test('h', u.h, u.minute * 60)
        test('day', u.day, u.hour * 24)
        test('week', u.week, u.day * 7)
        test('wk', u.wk, u.week)
        test('julian_year', u.julian_year, u.day * 365.25)
        test('year', u.year, u.julian_year)
        test('yr', u.yr, u.julian_year)

        test('parsec', u.parsec, u.m * 30.857e15)
        test('pc', u.pc, u.parsec)
        test('light_year', u.light_year, u.m * 9.4605284e15)
        test('ly', u.ly, u.light_year)
        test('angstrom', u.angstrom, u.m / 1e10)
        test('hectare', u.hectare, u.hm**2)
        test('cc', u.cc, u.cm**3)
        test('tonne', u.tonne, u.kg * 1e3)
        test('bar', u.bar, u.Pa * 1e5)
        test('atm', u.atm, 1.01325 * u.bar)
        test('torr', u.torr, u.atm / 760)

        test('inches', u.inches, u.cm * 2.54)
        test('thou', u.thou, u.inches * 1e-3)
        test('feet', u.feet, u.inches * 12)
        test('yards', u.yards, u.feet * 3)
        test('chains', u.chains, u.yards * 22)
        test('furlongs', u.furlongs, u.chains * 10)
        test('miles', u.miles, u.furlongs * 8)
        test('leagues', u.leagues, u.miles * 3)
        test('nautical_miles', u.nautical_miles, u.feet * 6080)
        test('cables', u.cables, u.nautical_miles * 1e-1)
        test('fathoms', u.fathoms, u.cables * 1e-2)
        test('rods', u.rods, u.chains * 0.25)
        test('links', u.links, u.rods / 25)
        test('perches', u.perches, u.rods**2)
        test('roods', u.roods, u.furlongs * u.rods)
        test('acres', u.acres, u.furlongs * u.chains)

        test('gallons', u.gallons, u.L * 4.54609)
        test('quarts', u.quarts, u.gallons * 0.25)
        test('pints', u.pints, u.quarts * 0.5)
        test('half_pints', u.half_pints, u.pints * 0.5)
        test('gills', u.gills, u.pints * 0.25)
        test('fluid_ounces', u.fluid_ounces, u.pints * 0.05)
        test('floz', u.floz, u.fluid_ounces)

        test('pounds', u.pounds, u.g * 453.59237)
        test('lb', u.lb, u.pounds)
        test('ounces', u.ounces, u.pounds / 16)
        test('oz', u.oz, u.ounces)
        test('drachms', u.drachms, u.ounces / 16)
        test('grains', u.grains, u.pounds / 7000)
        test('stones', u.stones, u.pounds * 14)
        test('quarters', u.quarters, u.stones * 2)
        test('hundredweights', u.hundredweights, u.quarters * 4)
        test('imp_tons', u.imp_tons, u.hundredweights * 20)

        test('dog_year', u.dog_year, u.julian_year / 7)
        test('forthnight', u.forthnight, 14 * u.day)
        test('smoot', u.smoot, u.feet * (5 + 7 / 12))


if __name__ == '__main__':
    unittest.main()
