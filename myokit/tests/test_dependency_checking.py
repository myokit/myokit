#!/usr/bin/env python3
#
# Tests the dependency resolving and sorting to solvable order in the myokit
# core.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit

from myokit.tests import DIR_DATA

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str


# Extra output
debug = False


class DepTest(unittest.TestCase):
    """
    General dependency test. Loads model and destroys it
    """
    @classmethod
    def setUpClass(cls):
        cls.m = myokit.load_model(
            os.path.join(DIR_DATA, 'lr-1991-dep.mmt'))

    def d(self, name):
        return myokit.Derivative(myokit.Name(self.m.get(name)))

    def n(self, name):
        return myokit.Name(self.m.get(name))

    def has_lhs(self, depmap, key, *deps):
        """
        Check if the depmap entry for lhs contains all deps, and only those
        deps.
        """
        # If a string lhs is given, interpret it as a variable name and get
        # the lhs of its defining equation
        if isinstance(key, basestring):
            key = self.m.get(key)
            if isinstance(key, myokit.Variable):
                key = key.lhs()

        # Convert deps list to list of objects. If a string name is given,
        # convert it to a Name. Ensure no duplicates are given.
        deps = list(set(deps))
        for k, dep in enumerate(deps):
            if isinstance(dep, basestring):
                deps[k] = self.n(dep)

        # Get dep map
        self.assertIn(key, depmap)
        dmap = depmap[key]

        # Show what will be tested
        if debug:
            if deps:
                print('Testing if ' + repr(key) + ' has ')
                print('  [' + ', '.join([repr(d) for d in deps]) + ']')
                print('It has:')
                print('  [' + ', '.join([repr(d) for d in dmap]) + ']')
            else:
                if isinstance(key, myokit.Expression):
                    if key.var().is_state():
                        print(repr(key) + ' is a state')
                    else:
                        print(repr(key) + ' is a constant')
                else:
                    print(repr(key) + ' is empty')

        # Check all dependencies
        for dep in deps:
            self.assertIn(dep, dmap)
        self.assertIs(len(deps), len(dmap))

    def has_comp(self, depmap, comp, *deps):
        """
        Check if the depmap entry for comp contains all deps, and only those
        deps.
        """
        if not isinstance(comp, myokit.Component):
            comp = self.m.get(comp)
        # Convert deps list to list of objects. Remove duplicates
        dps = set()
        for k, dep in enumerate(deps):
            if not isinstance(dep, myokit.Component):
                dep = self.m.get(dep)
            dps.add(dep)
        deps = dps
        # Get dep map, compare lengths
        self.assertIn(comp, depmap)
        dmap = depmap[comp]
        self.assertIs(len(deps), len(dmap))
        # Check all dependencies
        for dep in deps:
            self.assertIn(dep, dmap)
        # Show what was tested
        if debug:
            if deps:
                print(
                    comp.name() + ' has deps ('
                    + ', '.join([d.name() for d in deps]) + ')')
            else:
                print(comp.name() + ' has no dependencies')

    def head(self, text):
        if debug:
            x = int((68 - len(text)) / 2)
            y = 68 - len(text) - x
            print('.' * y + ' ' + text + ' ' + '.' * x)


class BasicReferenceTest(DepTest):
    """
    Tests the basics of reference checking
    """
    def test_references(self):
        # Test the list_reference() method.

        # Test if derivative returns correct reference
        y = myokit.Name('y')
        dy = myokit.Derivative(y)
        r = myokit.Plus(myokit.Number(5), dy)
        r = r.references()
        self.assertEqual(len(r), 1)
        r = next(iter(r))
        self.assertEqual(r, dy)
        # Test in parsed model
        d = self.d

        def has(var_name, *deps):
            lhs = self.m.get(var_name)
            depmap = {lhs: lhs.rhs().references()}
            return self.has_lhs(depmap, lhs, *deps)

        has('ina.m', 'ina.m.inf', 'ina.m.tau', 'ina.m')
        has('ina.h', 'ina.h.inf', 'ina.h.tau', 'ina.h')
        has('ina.x', 'ina.z', d('ina.m'))


class ShallowDepTest(DepTest):
    """
    Tests the shallow dependency mapping.
    """
    def test_shallow(self):
        # Test the basic shallow depmap

        # Easy access to methods
        m = self.m
        d = self.d
        n = self.n
        head = self.head
        depmap = m.map_shallow_dependencies(omit_states=False)

        def has(lhs, *deps):
            return self.has_lhs(depmap, lhs, *deps)

        # Start testing
        head('Shallow dependency mapping')
        head('Testing engine component')
        has('engine.time')
        has('engine.pace')
        head('Testing cell component')
        has('cell.K_o')
        has('cell.K_i')
        has('cell.Na_o')
        has('cell.Na_i')
        has('cell.Ca_o')
        has('cell.R')
        has('cell.T')
        has('cell.F')
        has('cell.RTF', 'cell.R', 'cell.T', 'cell.F')
        head('Testing backround current component')
        has('ib.gb')
        has('ib.Ib', 'ib.gb', 'membrane.V')
        head('Testing ik1 component')
        has('ik1.E', 'cell.RTF', 'cell.K_o', 'cell.K_i')
        has('ik1.gK1.alpha', 'ik1.E', 'membrane.V')
        has('ik1.gK1.beta', 'ik1.E', 'membrane.V')
        has('ik1.gK1', 'cell.K_o', 'ik1.gK1.alpha', 'ik1.gK1.beta')
        has('ik1.IK1', 'ik1.gK1', 'membrane.V', 'ik1.E')
        head('Testing ica component')
        has('ica.gCa')
        has('ica.E', 'ica.Ca_i', 'cell.Ca_o')
        has('ica.Ca_i', 'ica.ICa', 'ica.Ca_i')
        has(n('ica.Ca_i'))
        has('ica.d.alpha', 'membrane.V')
        has('ica.d.beta', 'ica.d.beta.va', 'ica.d.beta.vb')
        has('ica.d.beta.va', 'ica.d.beta.vc')
        has('ica.d.beta.vb', 'ica.d.beta.vc')
        has('ica.d.beta.vc', 'ica.d.beta.vc.vd')
        has('ica.d.beta.vc.vd', 'membrane.V')
        has('ica.d', 'ica.d', 'ica.d.alpha', 'ica.d.beta')
        has(n('ica.d'))
        has('ica.f.alpha')
        has('ica.f.beta')
        has('ica.f.tau', 'ica.f.alpha', 'ica.f.beta')
        has('ica.f.inf', 'ica.f.alpha', 'ica.f.tau')
        has('ica.f', 'ica.f', 'ica.f.inf', 'ica.f.tau')
        has(n('ica.f'))
        has('ica.ICa', 'ica.ICa.nest1', 'ica.E', 'membrane.V')
        has('ica.ICa.nest1', 'ica.gCa', 'ica.d', 'ica.ICa.nest2')
        has('ica.ICa.nest2', 'ica.f')
        head('Testing ikp component')
        has('ikp.gKp')
        has('ikp.IKp', 'ikp.gKp', 'membrane.V')
        head('Testing ik component')
        has('ik.PNa_K')
        has('ik.gK', 'cell.K_o')
        has('ik.E', 'cell.RTF', 'cell.K_o', 'ik.PNa_K', 'cell.Na_o',
            'cell.K_i', 'cell.Na_i')
        has('ik.xi', 'membrane.V')
        has('ik.x.alpha', 'membrane.V')
        has('ik.x.beta', 'membrane.V')
        has('ik.x.tau', 'ik.x.alpha', 'ik.x.beta')
        has('ik.x.inf', 'ik.x.alpha', 'ik.x.tau')
        has('ik.x', 'ik.x.inf', 'ik.x.tau', 'ik.x')
        has(n('ik.x'))
        has('ik.IK', 'ik.gK', 'ik.xi', 'ik.x', 'membrane.V', 'ik.E')
        has('ik.abc', d('ina.m'), d('ina.h'))
        head('Testing ina component')
        has('ina.ENa', 'cell.RTF', 'cell.Na_o', 'cell.Na_i')
        has('ina.a', 'membrane.V')
        has('ina.m.alpha', 'membrane.V')
        has('ina.m.beta', 'membrane.V')
        has('ina.m.tau', 'ina.m.alpha', 'ina.m.beta')
        has('ina.m.inf', 'ina.m.alpha', 'ina.m.tau')
        has('ina.m', 'ina.m.inf', 'ina.m.tau', 'ina.m')
        has(n('ina.m'))
        has('ina.h.alpha', 'membrane.V', 'ina.a')
        has('ina.h.beta', 'membrane.V', 'ina.a')
        has('ina.h.tau', 'ina.h.alpha', 'ina.h.beta')
        has('ina.h.inf', 'ina.h.alpha', 'ina.h.tau')
        has('ina.h', 'ina.h.inf', 'ina.h.tau', 'ina.h')
        has(n('ina.h'))
        has('ina.j.alpha', 'membrane.V', 'ina.a')
        has('ina.j.beta', 'membrane.V', 'ina.a')
        has('ina.j', 'ina.j.alpha', 'ina.j.beta', 'ina.j', 'ina.x', 'ina.y')
        has(n('ina.j'))
        has('ina.gNa')
        has('ina.INa', 'ina.gNa', 'ina.m', 'ina.h', 'ina.j', 'ina.ENa',
            'membrane.V')
        has('ina.x', 'ina.z', d('ina.m'))
        has('ina.y', 'ina.x', d('ina.h'))
        has('ina.z', 'cell.K_o')
        head('Testing membrane component')
        has('membrane.stim_amplitude')
        has('membrane.i_stim', 'membrane.stim_amplitude', 'engine.pace')
        has('membrane.V', 'membrane.i_stim', 'ina.INa', 'ik.IK', 'ib.Ib',
            'ikp.IKp', 'ik1.IK1', 'ica.ICa')
        has(n('membrane.V'))
        has('membrane.x', d('ina.m'))
        head('Testing dot() test component')
        has('test.t1', d('membrane.V'))
        has('test.inter', d('test.t1'))
        has('test.t2', 'test.inter')
        head('Shallow dependency check complete')


class DeepDepTest(DepTest):
    """
    Tests deep dependency mapping.
    """
    def test_deep(self):
        #
        # Test with::
        #
        #   omit_states=False
        #

        # Easy access to methods
        m = self.m
        d = self.d
        n = self.n
        head = self.head
        depmap = m.map_deep_dependencies(omit_states=False)

        def has(lhs, *deps):
            return self.has_lhs(depmap, lhs, *deps)

        # Start testing
        head('Deep dependency mapping')
        head('Testing engine component')
        has('engine.time')
        has('engine.pace')
        head('Testing cell component')
        has('cell.K_o')
        has('cell.K_i')
        has('cell.Na_o')
        has('cell.Na_i')
        has('cell.Ca_o')
        has('cell.R')
        has('cell.T')
        has('cell.F')
        RTF = ('cell.RTF', 'cell.R', 'cell.T', 'cell.F')
        has(*RTF)
        head('Testing backround current component')
        has('ib.gb')
        Ib = ('ib.Ib', 'ib.gb', 'membrane.V')
        has(*Ib)
        head('Testing ik1 component')
        E = ('ik1.E', 'cell.K_o', 'cell.K_i') + RTF
        has(*E)
        EV = ('membrane.V',) + E
        has('ik1.gK1.alpha', *EV)
        has('ik1.gK1.beta', *EV)
        ABEV = ('ik1.gK1.alpha', 'ik1.gK1.beta') + EV
        has('ik1.gK1', 'cell.K_o', *ABEV)
        IK1 = ('ik1.IK1', 'ik1.gK1') + ABEV
        has(*IK1)
        head('Testing ica component')
        has('ica.gCa')
        E = 'ica.E', 'ica.Ca_i', 'cell.Ca_o'
        has(*E)
        has('ica.d.alpha', 'membrane.V')
        has('ica.d.beta', 'ica.d.beta.va', 'ica.d.beta.vb', 'ica.d.beta.vc',
            'ica.d.beta.vc.vd', 'membrane.V')
        has('ica.d.beta.va', 'ica.d.beta.vc', 'ica.d.beta.vc.vd', 'membrane.V')
        has('ica.d.beta.vb', 'ica.d.beta.vc', 'ica.d.beta.vc.vd', 'membrane.V')
        has('ica.d.beta.vc', 'ica.d.beta.vc.vd', 'membrane.V')
        has('ica.d.beta.vc.vd', 'membrane.V')
        has('ica.d', 'ica.d', 'ica.d.alpha', 'ica.d.beta', 'ica.d.beta.va',
            'ica.d.beta.vb', 'ica.d.beta.vc', 'ica.d.beta.vc.vd', 'membrane.V')
        has(n('ica.d'))
        has('ica.f.alpha')
        has('ica.f.beta')
        has('ica.f.tau', 'ica.f.alpha', 'ica.f.beta')
        has('ica.f.inf', 'ica.f.tau', 'ica.f.alpha', 'ica.f.beta')
        has('ica.f', 'ica.f', 'ica.f.inf', 'ica.f.tau', 'ica.f.alpha',
            'ica.f.beta')
        has(n('ica.f'))
        has('ica.ICa.nest1', 'ica.gCa', 'ica.d', 'ica.f', 'ica.ICa.nest2')
        has('ica.ICa.nest2', 'ica.f')
        ICa = (
            'ica.ICa', 'ica.ICa.nest1', 'ica.ICa.nest2', 'ica.gCa', 'ica.d',
            'ica.f', 'membrane.V') + E
        has(*ICa)
        has('ica.Ca_i', 'ica.Ca_i', *ICa)
        has(n('ica.Ca_i'))
        head('Testing ikp component')
        has('ikp.gKp')
        IKp = ('ikp.IKp', 'ikp.gKp', 'membrane.V')
        has(*IKp)
        head('Testing ik component')
        has('ik.PNa_K')
        has('ik.gK', 'cell.K_o')
        E = (
            'ik.E', 'cell.K_o', 'ik.PNa_K', 'cell.Na_o', 'cell.K_i',
            'cell.Na_i') + RTF
        has(*E)
        has('ik.abc', d('ina.m'), 'ina.m', 'ina.m.inf', 'ina.m.tau',
            'ina.m.alpha', 'ina.m.beta', 'ina.a', 'membrane.V', d('ina.h'),
            'ina.h', 'ina.h.inf', 'ina.h.tau', 'ina.h.alpha', 'ina.h.beta')
        has('ik.xi', 'membrane.V')
        has('ik.x.alpha', 'membrane.V')
        has('ik.x.beta', 'membrane.V')
        has('ik.x.tau', 'ik.x.alpha', 'ik.x.beta', 'membrane.V')
        has('ik.x.inf', 'ik.x.tau', 'ik.x.alpha', 'ik.x.beta', 'membrane.V')
        has('ik.x', 'ik.x.inf', 'ik.x.tau', 'ik.x.alpha', 'ik.x.beta', 'ik.x',
            'membrane.V')
        has(n('ik.x'))
        IK = ('ik.IK', 'ik.gK', 'ik.xi', 'ik.x', 'membrane.V') + E
        has(*IK)
        head('Testing ina component')
        E = ('ina.ENa', 'cell.Na_o', 'cell.Na_i') + RTF
        has(*E)
        has('ina.a', 'membrane.V')
        has('ina.m.alpha', 'membrane.V')
        has('ina.m.beta', 'membrane.V')
        has('ina.m', 'ina.m.inf', 'ina.m.tau', 'ina.m.alpha', 'ina.m.beta',
            'ina.m', 'membrane.V')
        has(n('ina.m'))
        has('ina.h.alpha', 'membrane.V', 'ina.a')
        has('ina.h.beta', 'membrane.V', 'ina.a')
        has('ina.h', 'ina.h.inf', 'ina.h.tau', 'ina.h.alpha', 'ina.h.beta',
            'ina.h', 'ina.a', 'membrane.V')
        has(n('ina.h'))
        has('ina.j.alpha', 'membrane.V', 'ina.a')
        has('ina.j.beta', 'membrane.V', 'ina.a')
        has('ina.j', 'ina.j.alpha', 'ina.j.beta', 'ina.j', 'ina.a',
            'ina.x', d('ina.m'), 'ina.m.alpha', 'ina.m.beta', 'ina.m',
            'ina.m.inf', 'ina.m.tau',
            'ina.y', d('ina.h'), 'ina.h.alpha', 'ina.h.beta', 'ina.h',
            'ina.h.inf', 'ina.h.tau',
            'ina.z', 'cell.K_o', 'membrane.V',)
        has(n('ina.j'))
        has('ina.x', d('ina.m'), 'ina.m.alpha', 'ina.m.beta', 'ina.m',
            'ina.m.inf', 'ina.m.tau', 'membrane.V', 'ina.z', 'cell.K_o')
        has('ina.y', 'ina.x', d('ina.m'), 'ina.m.alpha', 'ina.m.beta',
            'ina.m.tau', 'ina.m.inf', 'ina.m', 'membrane.V', 'ina.z',
            'cell.K_o', d('ina.h'), 'ina.h.alpha', 'ina.h.beta', 'ina.h',
            'ina.h.inf', 'ina.h.tau', 'ina.a')
        has('ina.z', 'cell.K_o')
        has('ina.gNa')
        INa = (
            'ina.INa', 'ina.gNa', 'ina.m', 'ina.h', 'ina.j', 'membrane.V') + E
        has(*INa)
        head('Testing membrane component')
        has('membrane.stim_amplitude')
        Istim = ('membrane.i_stim', 'membrane.stim_amplitude', 'engine.pace')
        has(*Istim)
        I = INa + IK + Ib + IKp + IK1 + ICa + Istim
        has('membrane.V', *I)
        has(n('membrane.V'))
        has('membrane.x', d('ina.m'), 'ina.m.inf', 'ina.m.tau', 'ina.m.alpha',
            'ina.m.beta', 'ina.m', 'membrane.V')
        head('Testing dot() test component')
        has('test.t1', d('membrane.V'), *I)
        has('test.inter', d('test.t1'), d('membrane.V'), *I)
        has('test.t2', 'test.inter', d('test.t1'), d('membrane.V'), *I)
        has(n('test.t1'))
        has(n('test.t2'))
        head('Deep dependency check complete [with state deps]')

    def test_deep_no_states(self):
        #
        # Test with::
        #
        #   omit_states=True
        #

        # Easy access to methods
        m = self.m
        d = self.d
        n = self.n
        head = self.head
        depmap = m.map_deep_dependencies(omit_states=True)

        def has(lhs, *deps):
            return self.has_lhs(depmap, lhs, *deps)

        def nhas(lhs):
            if isinstance(lhs, basestring):
                lhs = self.m.get(lhs).lhs()
            self.assertNotIn(lhs, depmap)

        # Start testing
        head('Deep dependency mapping')
        head('Testing engine component')
        has('engine.time')
        has('engine.pace')
        head('Testing cell component')
        has('cell.K_o')
        has('cell.K_i')
        has('cell.Na_o')
        has('cell.Na_i')
        has('cell.Ca_o')
        has('cell.R')
        has('cell.T')
        has('cell.F')
        RTF = ('cell.RTF', 'cell.R', 'cell.T', 'cell.F')
        has(*RTF)
        head('Testing backround current component')
        has('ib.gb')
        Ib = ('ib.Ib', 'ib.gb')
        has(*Ib)
        head('Testing ik1 component')
        E = ('ik1.E', 'cell.K_o', 'cell.K_i') + RTF
        has(*E)
        has('ik1.gK1.alpha', *E)
        has('ik1.gK1.beta', *E)
        ABE = ('ik1.gK1.alpha', 'ik1.gK1.beta') + E
        has('ik1.gK1', 'cell.K_o', *ABE)
        IK1 = ('ik1.IK1', 'ik1.gK1') + ABE
        has(*IK1)
        head('Testing ica component')
        has('ica.gCa')
        E = ('ica.E', 'cell.Ca_o')
        has(*E)
        has('ica.d.alpha')
        has('ica.d.beta', 'ica.d.beta.va', 'ica.d.beta.vb', 'ica.d.beta.vc',
            'ica.d.beta.vc.vd')
        has('ica.d.beta.va', 'ica.d.beta.vc', 'ica.d.beta.vc.vd')
        has('ica.d.beta.vb', 'ica.d.beta.vc', 'ica.d.beta.vc.vd')
        has('ica.d.beta.vc', 'ica.d.beta.vc.vd')
        has('ica.d.beta.vc.vd')
        has('ica.d', 'ica.d.alpha', 'ica.d.beta', 'ica.d.beta.va',
            'ica.d.beta.vb', 'ica.d.beta.vc', 'ica.d.beta.vc.vd')
        nhas(n('ica.d'))
        has('ica.f.alpha')
        has('ica.f.beta')
        has('ica.f.tau', 'ica.f.alpha', 'ica.f.beta')
        has('ica.f.inf', 'ica.f.tau', 'ica.f.alpha', 'ica.f.beta')
        has('ica.f', 'ica.f.inf', 'ica.f.tau', 'ica.f.alpha', 'ica.f.beta')
        nhas(n('ica.f'))
        has('ica.ICa.nest1', 'ica.gCa', 'ica.ICa.nest2')
        has('ica.ICa.nest2')
        ICa = ('ica.ICa', 'ica.gCa', 'ica.ICa.nest1', 'ica.ICa.nest2') + E
        has(*ICa)
        has('ica.Ca_i', *ICa)
        nhas(n('ica.Ca_i'))
        head('Testing ikp component')
        has('ikp.gKp')
        IKp = ('ikp.IKp', 'ikp.gKp')
        has(*IKp)
        head('Testing ik component')
        has('ik.PNa_K')
        has('ik.gK', 'cell.K_o')
        E = (
            'ik.E', 'cell.K_o', 'ik.PNa_K', 'cell.Na_o', 'cell.K_i',
            'cell.Na_i') + RTF
        has(*E)
        has('ik.xi')
        has('ik.x.alpha')
        has('ik.x.beta')
        has('ik.x', 'ik.x.inf', 'ik.x.tau', 'ik.x.alpha', 'ik.x.beta')
        nhas(n('ik.x'))
        IK = ('ik.IK', 'ik.gK', 'ik.xi') + E
        has(*IK)
        head('Testing ina component')
        E = ('ina.ENa', 'cell.Na_o', 'cell.Na_i') + RTF
        has(*E)
        has('ina.a')
        has('ina.m.alpha')
        has('ina.m.beta')
        M = ('ina.m.alpha', 'ina.m.beta', 'ina.m.inf', 'ina.m.tau')
        has('ina.m', *M)
        nhas(n('ina.m'))
        has('ina.h.alpha', 'ina.a')
        has('ina.h.beta', 'ina.a')
        H = ('ina.h.alpha', 'ina.h.beta', 'ina.a', 'ina.h.inf', 'ina.h.tau')
        has('ina.h', *H)
        nhas(n('ina.m'))
        has('ik.abc', d('ina.m'), d('ina.h'), *(M + H))
        has('ina.j.alpha', 'ina.a')
        has('ina.j.beta', 'ina.a')
        has('ina.j', 'ina.j.alpha', 'ina.j.beta', 'ina.a', d('ina.m'),
            d('ina.h'), 'cell.K_o', 'ina.m.alpha', 'ina.m.beta', 'ina.m.inf',
            'ina.m.tau', 'ina.h.alpha', 'ina.h.beta', 'ina.h.inf', 'ina.h.tau',
            'ina.x', 'ina.y', 'ina.z')
        nhas(n('ina.m'))
        has('ina.x', d('ina.m'), 'ina.z', 'cell.K_o',
            'ina.m.alpha', 'ina.m.beta', 'ina.m.inf', 'ina.m.tau')
        has('ina.y', 'ina.x', 'ina.z', d('ina.h'), d('ina.m'), 'ina.a',
            'ina.h.alpha', 'ina.h.beta', 'ina.m.alpha', 'ina.m.beta',
            'ina.m.inf', 'ina.m.tau', 'ina.h.inf', 'ina.h.tau', 'cell.K_o')
        has('ina.z', 'cell.K_o')
        has('ina.gNa')
        INa = ('ina.INa', 'ina.gNa') + E
        has(*INa)
        head('Testing membrane component')
        has('membrane.stim_amplitude')
        Istim = ('membrane.i_stim', 'membrane.stim_amplitude', 'engine.pace')
        has(*Istim)
        I = INa + IK + Ib + IKp + IK1 + ICa + Istim
        has('membrane.V', *I)
        nhas(n('membrane.V'))
        has('membrane.x', d('ina.m'), 'ina.m.alpha', 'ina.m.beta', 'ina.m.inf',
            'ina.m.tau')
        head('Testing dot() test component')
        has('test.t1', d('membrane.V'), *I)
        has('test.inter', d('test.t1'), d('membrane.V'), *I)
        has('test.t2', 'test.inter', d('test.t1'), d('membrane.V'), *I)
        nhas(n('test.t1'))
        nhas(n('test.t2'))
        head('Deep dependency check complete [no state deps]')

    # Tests the deep dependency mapping.
    def test_deep_colnesting(self):
        #
        # Test with
        #
        #   omit_states = False
        #   collapse = True
        #

        # Easy access to methods
        m = self.m
        d = self.d
        n = self.n
        head = self.head
        depmap = m.map_deep_dependencies(omit_states=False, collapse=True)

        def has(lhs, *deps):
            return self.has_lhs(depmap, lhs, *deps)

        def nhas(lhs):
            if isinstance(lhs, basestring):
                lhs = self.m.get(lhs).lhs()
            self.assertNotIn(lhs, depmap)

        # Start testing
        head('Deep dependency mapping')
        head('Testing engine component')
        has('engine.time')
        has('engine.pace')
        head('Testing cell component')
        has('cell.K_o')
        has('cell.K_i')
        has('cell.Na_o')
        has('cell.Na_i')
        has('cell.Ca_o')
        has('cell.R')
        has('cell.T')
        has('cell.F')
        RTF = ('cell.RTF', 'cell.R', 'cell.T', 'cell.F')
        has(*RTF)
        head('Testing backround current component')
        has('ib.gb')
        Ib = ('ib.Ib', 'ib.gb', 'membrane.V')
        has(*Ib)
        head('Testing ik1 component')
        E = ('ik1.E', 'cell.K_o', 'cell.K_i') + RTF
        has(*E)
        EV = ('membrane.V',) + E
        nhas('ik1.gK1.alpha')
        nhas('ik1.gK1.beta')
        has('ik1.gK1', 'cell.K_o', *EV)
        IK1 = ('ik1.IK1', 'ik1.gK1') + EV
        has(*IK1)
        head('Testing ica component')
        has('ica.gCa')
        E = 'ica.E', 'ica.Ca_i', 'cell.Ca_o'
        has(*E)
        nhas('ica.d.alpha')
        nhas('ica.d.beta')
        nhas('ica.d.beta.va')
        nhas('ica.d.beta.vb')
        nhas('ica.d.beta.vc')
        nhas('ica.d.beta.vc.vd')
        has('ica.d', 'ica.d', 'membrane.V')
        has(n('ica.d'))
        nhas('ica.f.alpha')
        nhas('ica.f.beta')
        has('ica.f', 'ica.f')
        has(n('ica.f'))
        ICa = ('ica.ICa', 'ica.gCa', 'ica.d', 'ica.f', 'membrane.V') + E
        has(*ICa)
        has('ica.Ca_i', 'ica.Ca_i', *ICa)
        has(n('ica.Ca_i'))
        head('Testing ikp component')
        has('ikp.gKp')
        IKp = ('ikp.IKp', 'ikp.gKp', 'membrane.V')
        has(*IKp)
        head('Testing ik component')
        has('ik.PNa_K')
        has('ik.gK', 'cell.K_o')
        E = (
            'ik.E', 'cell.K_o', 'ik.PNa_K', 'cell.Na_o', 'cell.K_i',
            'cell.Na_i') + RTF
        has(*E)
        has('ik.abc', d('ina.m'), d('ina.h'), 'ina.m', 'ina.h', 'membrane.V',
            'ina.a')
        has('ik.xi', 'membrane.V')
        nhas('ik.x.alpha')
        nhas('ik.x.beta')
        has('ik.x', 'ik.x', 'membrane.V')
        has(n('ik.x'))
        IK = ('ik.IK', 'ik.gK', 'ik.xi', 'ik.x', 'membrane.V') + E
        has(*IK)
        head('Testing ina component')
        E = ('ina.ENa', 'cell.Na_o', 'cell.Na_i') + RTF
        has(*E)
        has('ina.a', 'membrane.V')
        nhas('ina.m.alpha')
        nhas('ina.m.beta')
        has('ina.m', 'ina.m', 'membrane.V')
        has(n('ina.m'))
        nhas('ina.h.alpha')
        nhas('ina.h.beta')
        has('ina.h', 'ina.h', 'ina.a', 'membrane.V')
        has(n('ina.h'))
        nhas('ina.j.alpha')
        nhas('ina.j.beta')
        has('ina.j', 'ina.j', 'ina.a', 'membrane.V', 'ina.z', 'ina.x',
            d('ina.m'), 'ina.m', 'cell.K_o', 'ina.y', d('ina.h'), 'ina.h')
        has(n('ina.j'))
        has('ina.x', d('ina.m'), 'ina.m', 'membrane.V', 'ina.z',
            'cell.K_o')
        has('ina.y', 'ina.x', d('ina.m'), 'ina.m', 'membrane.V', 'ina.z',
            'ina.a', 'cell.K_o', d('ina.h'), 'ina.h')
        has('ina.z', 'cell.K_o')
        has('ina.gNa')
        INa = (
            'ina.INa', 'ina.gNa', 'ina.m', 'ina.h', 'ina.j', 'membrane.V'
        ) + E
        has(*INa)
        head('Testing membrane component')
        has('membrane.stim_amplitude')
        Istim = ('membrane.i_stim', 'membrane.stim_amplitude', 'engine.pace')
        has(*Istim)
        I = INa + IK + Ib + IKp + IK1 + ICa + Istim
        has('membrane.V', *I)
        has(n('membrane.V'))
        has('membrane.x', d('ina.m'), 'ina.m', 'membrane.V')
        head('Testing dot() test component')
        has('test.t1', d('membrane.V'), *I)
        has('test.inter', d('test.t1'), d('membrane.V'), *I)
        has('test.t2', 'test.inter', d('test.t1'), d('membrane.V'), *I)
        has(n('test.t1'))
        has(n('test.t2'))
        head(
            'Deep dependency check complete [with state deps, collapse'
            ' nesting]')

    def test_deep_encompassed(self):
        #
        # Test with::
        #
        #   omit_states = False
        #   filter_encompassed = True
        #

        # Easy access to methods
        m = self.m
        n = self.n
        head = self.head
        depmap = m.map_deep_dependencies(
            omit_states=False, filter_encompassed=True)

        def has(lhs, *deps):
            return self.has_lhs(depmap, lhs, *deps)
        # Start testing
        head('Deep dependency mapping')
        head('Testing cell component')
        has('cell.K_o')
        has('cell.K_i')
        has('cell.Na_o')
        has('cell.Na_i')
        has('cell.Ca_o')
        has('cell.R')
        has('cell.T')
        has('cell.F')
        has('cell.RTF')
        head('Testing backround current component')
        has('ib.gb')
        Ib = ('ib.Ib', 'membrane.V')
        has(*Ib)
        head('Testing ik1 component')
        has('ik1.E')
        has('ik1.gK1.alpha', 'membrane.V')
        has('ik1.gK1.beta', 'membrane.V')
        has('ik1.gK1', 'membrane.V')
        IK1 = ('ik1.IK1', 'membrane.V')
        has(*IK1)
        head('Testing ica component')
        has('ica.gCa')
        has('ica.E', 'ica.Ca_i')
        has('ica.d.alpha', 'membrane.V')
        has('ica.d.beta', 'membrane.V')
        has('ica.d.beta.va', 'membrane.V')
        has('ica.d.beta.vb', 'membrane.V')
        has('ica.d.beta.vc', 'membrane.V')
        has('ica.d.beta.vc.vd', 'membrane.V')
        has('ica.d', 'ica.d', 'membrane.V')
        has(n('ica.d'))
        has('ica.f.alpha')
        has('ica.f.beta')
        has('ica.f', 'ica.f')
        has(n('ica.f'))
        ICa = ('ica.ICa', 'ica.d', 'ica.f', 'membrane.V', 'ica.Ca_i')
        has(*ICa)
        has('ica.Ca_i', 'ica.Ca_i', 'ica.d', 'ica.f', 'membrane.V')
        has(n('ica.Ca_i'))
        head('Testing ikp component')
        has('ikp.gKp')
        IKp = ('ikp.IKp', 'membrane.V')
        has(*IKp)
        head('Testing ik component')
        has('ik.PNa_K')
        has('ik.gK')
        has('ik.E')
        has('ik.xi', 'membrane.V')
        has('ik.x.alpha', 'membrane.V')
        has('ik.x.beta', 'membrane.V')
        has('ik.x', 'ik.x', 'membrane.V')
        has(n('ik.x'))
        has('ik.IK', 'ik.x', 'membrane.V')
        has('ik.abc', 'ina.m', 'ina.h', 'membrane.V')
        head('Testing ina component')
        has('ina.ENa')
        has('ina.a', 'membrane.V')
        has('ina.m.alpha', 'membrane.V')
        has('ina.m.beta', 'membrane.V')
        has('ina.m', 'ina.m', 'membrane.V')
        has(n('ina.m'))
        has('ina.h.alpha', 'membrane.V')
        has('ina.h.beta', 'membrane.V')
        has('ina.h', 'ina.h', 'membrane.V')
        has(n('ina.h'))
        has('ina.j.alpha', 'membrane.V')
        has('ina.j.beta', 'membrane.V')
        has('ina.j', 'ina.j', 'membrane.V', 'ina.m', 'ina.h')
        has(n('ina.j'))
        has('ina.x', 'ina.m', 'membrane.V')
        has('ina.y', 'ina.m', 'membrane.V', 'ina.h')
        has('ina.z')
        has('ina.gNa')
        has('ina.INa', 'ina.m', 'ina.h', 'ina.j', 'membrane.V')
        head('Testing membrane component')
        has('membrane.stim_amplitude')
        V = (
            'membrane.V', 'ina.m', 'ina.h', 'ina.j', 'ik.x', 'ica.d',
            'ica.f', 'ica.Ca_i')
        has('membrane.V', *V)
        has('membrane.x', 'ina.m', 'membrane.V')
        has(n('membrane.V'))
        head('Testing dot() test component')
        has('test.t1', *V)
        has('test.inter', *V)
        has('test.t2', *V)
        has(n('test.t1'))
        has(n('test.t2'))
        head(
            'Deep dependency check complete [with state deps, no encompassed'
            ' vars]')

    def test_deep_cyles(self):
        # Test if the deep test finds cyclical dependencies.

        m = self.m.clone()
        m.get('cell.Na_i').set_rhs('3 * ina.INa')
        self.assertRaises(
            myokit.CyclicalDependencyError, m.map_deep_dependencies)


class ComponentDepTest(DepTest):
    """
    Tests the component dependency mapping methods.
    """
    def test_map_component_dependencies(self):
        # Test the method ``map_component_dependencies

        depmap = self.m.map_component_dependencies(
            omit_states=False, omit_constants=False)
        # Shorthand functions
        head = self.head

        def has(comp, *deps):
            return self.has_comp(depmap, comp, *deps)
        # Start testing
        head('omit_states=False, omit_constants=False')
        has('membrane', 'ina', 'ik', 'ib', 'ikp', 'ik1', 'ica', 'engine')
        has('ina', 'membrane', 'cell')
        has('ik', 'membrane', 'cell', 'ina')
        has('ikp', 'membrane')
        has('ica', 'membrane', 'cell')
        has('ik1', 'membrane', 'cell')
        has('ib', 'membrane')
        has('cell')
        has('engine')
        has('test', 'membrane')
        # Next
        head('omit_states=True, omit_constants=False')
        depmap = self.m.map_component_dependencies(
            omit_states=True, omit_constants=False)
        has('membrane', 'ina', 'ik', 'ib', 'ikp', 'ik1', 'ica', 'engine')
        has('ina', 'cell')
        has('ik', 'cell', 'ina')
        has('ikp')
        has('ica', 'cell')
        has('ik1', 'cell')
        has('ib')
        has('cell')
        has('engine')
        has('test', 'membrane')  # dot(v) is a derivative, not a state value :)
        # Next
        head('omit_states=False, omit_constants=True')
        depmap = self.m.map_component_dependencies(
            omit_states=False, omit_constants=True)
        has('membrane', 'ina', 'ik', 'ib', 'ikp', 'ik1', 'ica', 'engine')
        has('ina', 'membrane')
        has('ik', 'membrane', 'ina')
        has('ikp', 'membrane')
        has('ica', 'membrane')
        has('ik1', 'membrane')
        has('ib', 'membrane')
        has('cell')
        has('engine')
        has('test', 'membrane')
        # Next
        head('omit_states=True, omit_constants=True')
        depmap = self.m.map_component_dependencies(
            omit_states=True, omit_constants=True)
        has('membrane', 'ina', 'ik', 'ib', 'ikp', 'ik1', 'ica', 'engine')
        has('ina')
        has('ik', 'ina')
        has('ikp')
        has('ica')
        has('ik1')
        has('ib')
        has('cell')
        has('engine')
        has('test', 'membrane')

    def test_map_component_io(self):
        # Test the method ``map_component_io

        d1, d2 = self.m.map_component_io()

        # Shorthand functions
        head = self.head

        def inn(comp, *deps):
            if debug:
                print('Input:')
            return self.has_lhs(d1, comp, *deps)

        def out(comp, *deps):
            if debug:
                print('Output:')
            return self.has_lhs(d2, comp, *deps)

        def d(var):
            return myokit.Derivative(myokit.Name(self.m.get(var)))

        # 1 FFF: States, Derivatives, Constants
        d1, d2 = self.m.map_component_io(
            omit_states=False,
            omit_derivatives=False,
            omit_constants=False,
        )
        head('1 FFF: States, Derivatives, Constants')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace', d('ina.m'))
        out('membrane', d('membrane.V'))
        inn('ina', 'ina.m', 'ina.h', 'ina.j', 'cell.RTF', 'cell.Na_i',
            'cell.Na_o', 'membrane.V', 'cell.K_o')
        out('ina', 'ina.INa', d('ina.m'), d('ina.h'), d('ina.j'))
        inn('ik', 'ik.x', 'cell.K_o', 'cell.Na_o', 'cell.K_i', 'cell.Na_i',
            'cell.RTF', 'membrane.V', d('ina.m'), d('ina.h'))
        out('ik', d('ik.x'), 'ik.IK')
        inn('ikp', 'membrane.V')
        out('ikp', 'ikp.IKp')
        inn('ica', 'ica.Ca_i', 'ica.d', 'ica.f', 'cell.Ca_o', 'membrane.V')
        out('ica', d('ica.Ca_i'), d('ica.d'), d('ica.f'), 'ica.ICa')
        inn('ik1', 'cell.RTF', 'cell.K_o', 'cell.K_i', 'membrane.V')
        out('ik1', 'ik1.IK1')
        inn('ib', 'membrane.V')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell', 'cell.RTF', 'cell.Na_o', 'cell.Na_i', 'cell.K_o',
            'cell.K_i', 'cell.Ca_o')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test', d('membrane.V'))
        out('test', d('test.t1'), d('test.t2'))

        # 2 FFT: States, Derivatives, No constants
        d1, d2 = self.m.map_component_io(
            omit_states=False,
            omit_derivatives=False,
            omit_constants=True,
        )
        head('2 FFT: States, Derivatives, No constants')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace', d('ina.m'))
        out('membrane', d('membrane.V'))
        inn('ina', 'ina.m', 'ina.h', 'ina.j', 'membrane.V')
        out('ina', 'ina.INa', d('ina.m'), d('ina.h'), d('ina.j'))
        inn('ik', 'ik.x', 'membrane.V', d('ina.m'), d('ina.h'))
        out('ik', d('ik.x'), 'ik.IK')
        inn('ikp', 'membrane.V')
        out('ikp', 'ikp.IKp')
        inn('ica', 'ica.Ca_i', 'ica.d', 'ica.f', 'membrane.V')
        out('ica', d('ica.Ca_i'), d('ica.d'), d('ica.f'), 'ica.ICa')
        inn('ik1', 'membrane.V')
        out('ik1', 'ik1.IK1')
        inn('ib', 'membrane.V')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test', d('membrane.V'))
        out('test', d('test.t1'), d('test.t2'))

        # 3 FTF: States, No derivatives, Constants
        d1, d2 = self.m.map_component_io(
            omit_states=False,
            omit_derivatives=True,
            omit_constants=False,
        )
        head('3 FTF: States, No derivatives, Constants')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace')
        out('membrane')
        inn('ina', 'ina.m', 'ina.h', 'ina.j', 'cell.RTF', 'cell.Na_i',
            'cell.Na_o', 'membrane.V', 'cell.K_o')
        out('ina', 'ina.INa')
        inn('ik', 'ik.x', 'cell.K_o', 'cell.Na_o', 'cell.K_i', 'cell.Na_i',
            'cell.RTF', 'membrane.V')
        out('ik', 'ik.IK')
        inn('ikp', 'membrane.V')
        out('ikp', 'ikp.IKp')
        inn('ica', 'ica.Ca_i', 'ica.d', 'ica.f', 'cell.Ca_o', 'membrane.V')
        out('ica', 'ica.ICa')
        inn('ik1', 'cell.RTF', 'cell.K_o', 'cell.K_i', 'membrane.V')
        out('ik1', 'ik1.IK1')
        inn('ib', 'membrane.V')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell', 'cell.RTF', 'cell.Na_o', 'cell.Na_i', 'cell.K_o',
            'cell.K_i', 'cell.Ca_o')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test')
        out('test')

        # 4 FTT: States, No derivatives, No constants
        d1, d2 = self.m.map_component_io(
            omit_states=False,
            omit_derivatives=True,
            omit_constants=True,
        )
        head('4 FTT: States, No derivatives, No constants')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace')
        out('membrane')
        inn('ina', 'ina.m', 'ina.h', 'ina.j', 'membrane.V')
        out('ina', 'ina.INa')
        inn('ik', 'ik.x', 'membrane.V')
        out('ik', 'ik.IK')
        inn('ikp', 'membrane.V')
        out('ikp', 'ikp.IKp')
        inn('ica', 'ica.Ca_i', 'ica.d', 'ica.f', 'membrane.V')
        out('ica', 'ica.ICa')
        inn('ik1', 'membrane.V')
        out('ik1', 'ik1.IK1')
        inn('ib', 'membrane.V')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test')
        out('test')

        # 5 TFF: No states, Derivatives, Constants
        d1, d2 = self.m.map_component_io(
            omit_states=True,
            omit_derivatives=False,
            omit_constants=False,
        )
        head('5 TFF: No states, Derivatives, Constants')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace', d('ina.m'))
        out('membrane', d('membrane.V'))
        inn('ina', 'cell.RTF', 'cell.Na_i', 'cell.Na_o', 'cell.K_o')
        out('ina', 'ina.INa', d('ina.m'), d('ina.h'), d('ina.j'))
        inn('ik', 'cell.K_o', 'cell.Na_o', 'cell.K_i', 'cell.Na_i', 'cell.RTF',
            d('ina.m'), d('ina.h'))
        out('ik', d('ik.x'), 'ik.IK')
        inn('ikp')
        out('ikp', 'ikp.IKp')
        inn('ica', 'cell.Ca_o')
        out('ica', d('ica.Ca_i'), d('ica.d'), d('ica.f'), 'ica.ICa')
        inn('ik1', 'cell.RTF', 'cell.K_o', 'cell.K_i')
        out('ik1', 'ik1.IK1')
        inn('ib')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell', 'cell.RTF', 'cell.Na_o', 'cell.Na_i', 'cell.K_o',
            'cell.K_i', 'cell.Ca_o')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test', d('membrane.V'))
        out('test', d('test.t1'), d('test.t2'))

        # 6 TFT: No states, Derivatives, No constants
        # This is the realistic use-case!
        d1, d2 = self.m.map_component_io(
            omit_states=True,
            omit_derivatives=False,
            omit_constants=True,
        )
        head('6 TFT: No states, Derivatives, No constants')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace', d('ina.m'))
        out('membrane', d('membrane.V'))
        inn('ina')
        out('ina', 'ina.INa', d('ina.m'), d('ina.h'), d('ina.j'))
        inn('ik', d('ina.m'), d('ina.h'))
        out('ik', d('ik.x'), 'ik.IK')
        inn('ikp')
        out('ikp', 'ikp.IKp')
        inn('ica')
        out('ica', d('ica.Ca_i'), d('ica.d'), d('ica.f'), 'ica.ICa')
        inn('ik1')
        out('ik1', 'ik1.IK1')
        inn('ib')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test', d('membrane.V'))
        out('test', d('test.t1'), d('test.t2'))

        # 7 TTF: No states, No derivatives, Constants
        d1, d2 = self.m.map_component_io(
            omit_states=True,
            omit_derivatives=True,
            omit_constants=False,
        )
        head('7 TTF: No states, No derivatives, Constants')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace')
        out('membrane')
        inn('ina', 'cell.RTF', 'cell.Na_i', 'cell.Na_o', 'cell.K_o')
        out('ina', 'ina.INa')
        inn('ik', 'cell.K_o', 'cell.Na_o', 'cell.K_i', 'cell.Na_i', 'cell.RTF')
        out('ik', 'ik.IK')
        inn('ikp')
        out('ikp', 'ikp.IKp')
        inn('ica', 'cell.Ca_o')
        out('ica', 'ica.ICa')
        inn('ik1', 'cell.RTF', 'cell.K_o', 'cell.K_i')
        out('ik1', 'ik1.IK1')
        inn('ib')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell', 'cell.RTF', 'cell.Na_o', 'cell.Na_i', 'cell.K_o',
            'cell.K_i', 'cell.Ca_o')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test')
        out('test')

        # 8 TTT: No states, No derivatives, No constants
        d1, d2 = self.m.map_component_io(
            omit_states=True,
            omit_derivatives=True,
            omit_constants=True,
        )
        head('8 TTT: No states, No derivatives, No constants')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace')
        out('membrane')
        inn('ina')
        out('ina', 'ina.INa')
        inn('ik')
        out('ik', 'ik.IK')
        inn('ikp')
        out('ikp', 'ikp.IKp')
        inn('ica')
        out('ica', 'ica.ICa')
        inn('ik1')
        out('ik1', 'ik1.IK1')
        inn('ib')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test')
        out('test')

        # A TFF-RL: No states, Derivatives, Constants, in RL mode
        rl_states = {}
        for state in ['ina.m', 'ina.h', 'ik.x', 'ica.f']:
            rl_states[self.m.get(state)] = (
                self.m.get(state + '.inf'), self.m.get(state + '.tau'))
        d1, d2 = self.m.map_component_io(
            omit_states=True,
            omit_derivatives=False,
            omit_constants=False,
            rl_states=rl_states,
        )
        head('A TFF-RL: No states, Derivatives, Constants, in RL mode')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace', d('ina.m'))
        out('membrane', d('membrane.V'))
        inn('ina', 'cell.RTF', 'cell.Na_i', 'cell.Na_o', 'cell.K_o')
        out('ina', 'ina.INa', d('ina.m'), d('ina.h'), d('ina.j'),
            'ina.m.inf', 'ina.m.tau', 'ina.h.inf', 'ina.h.tau')
        inn('ik', 'cell.K_o', 'cell.Na_o', 'cell.K_i', 'cell.Na_i', 'cell.RTF',
            d('ina.m'), d('ina.h'))
        out('ik', 'ik.x.inf', 'ik.x.tau', 'ik.IK')
        inn('ikp')
        out('ikp', 'ikp.IKp')
        inn('ica', 'cell.Ca_o')
        out('ica', d('ica.Ca_i'), d('ica.d'), 'ica.f.inf', 'ica.f.tau',
            'ica.ICa')
        inn('ik1', 'cell.RTF', 'cell.K_o', 'cell.K_i')
        out('ik1', 'ik1.IK1')
        inn('ib')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell', 'cell.RTF', 'cell.Na_o', 'cell.Na_i', 'cell.K_o',
            'cell.K_i', 'cell.Ca_o')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test', d('membrane.V'))
        out('test', d('test.t1'), d('test.t2'))

        # B TFT-RL: No states, Derivatives, No Constants, in RL mode
        # This is the practical use case
        rl_states = {}
        for state in ['ina.m', 'ina.h', 'ik.x', 'ica.f']:
            rl_states[self.m.get(state)] = (
                self.m.get(state + '.inf'), self.m.get(state + '.tau'))
        d1, d2 = self.m.map_component_io(
            omit_states=True,
            omit_derivatives=False,
            omit_constants=True,
            rl_states=rl_states,
        )
        head('B TFT-RL: No states, Derivatives, No constants in RL mode')
        inn('membrane', 'ina.INa', 'ik.IK', 'ib.Ib', 'ikp.IKp',
            'ik1.IK1', 'ica.ICa', 'engine.pace', d('ina.m'))
        out('membrane', d('membrane.V'))
        inn('ina')
        out('ina', 'ina.INa', d('ina.m'), d('ina.h'), d('ina.j'),
            'ina.m.inf', 'ina.m.tau', 'ina.h.inf', 'ina.h.tau')
        inn('ik', d('ina.m'), d('ina.h'))
        out('ik', 'ik.x.inf', 'ik.x.tau', 'ik.IK')
        inn('ikp')
        out('ikp', 'ikp.IKp')
        inn('ica')
        out('ica', d('ica.Ca_i'), d('ica.d'), 'ica.ICa')
        inn('ik1')
        out('ik1', 'ik1.IK1')
        inn('ib')
        out('ib', 'ib.Ib')
        inn('cell')
        out('cell')
        inn('engine')
        out('engine', 'engine.pace')
        inn('test', d('membrane.V'))
        out('test', d('test.t1'), d('test.t2'))

    def test_component_cycles(self):
        # Test Model.component_cycles().

        # Create structure:
        #
        #         C           A on B
        #       / | \         B on C
        # A - B   |  D        C on D and C on E
        #       \ | /         D on E
        #         E           E on B and E on C
        #
        # Should have cycles:
        #  B - C - D - E - B
        #  C - D - E - C
        #  B - C - E - B
        #  C - E - C
        #
        m = myokit.Model('cycles')
        a = m.add_component('a')
        b = m.add_component('b')
        c = m.add_component('c')
        d = m.add_component('d')
        e = m.add_component('e')
        a1 = a.add_variable('a1')
        b1 = b.add_variable('b1')
        c1 = c.add_variable('c1')
        d1 = d.add_variable('d1')
        e1 = e.add_variable('e1')
        a1.set_rhs('b.b1')
        b1.set_rhs('c.c1')
        c1.set_rhs('d.d1 + e.e1')
        d1.set_rhs('e.e1')
        e1.set_rhs('b.b1 + c.c1')

        # Check 4 cycles exist
        cycles = m.component_cycles()
        self.assertEqual(len(cycles), 4)

        # Specific test for the following bug:
        # Calling has_interdependent_components() returned True, but
        # component_cycles found nothing. The reason turned out to be that
        # unused variables were never visited by component_cycles
        m = myokit.Model('bug')
        a = m.add_component('a')
        b = m.add_component('b')
        p = a.add_variable('p')
        q = a.add_variable('q')
        r = b.add_variable('r')
        s = b.add_variable('s')
        p.set_rhs('q')
        q.set_rhs('b.s')
        r.set_rhs('a.q')
        s.set_rhs('0')
        p.promote(0)
        cycles = m.component_cycles()
        try:
            # Try both orders, (each is valid)
            if cycles[0][0] == a:
                self.assertEqual(cycles, [[a, b, a]])
            else:
                self.assertEqual(cycles, [[b, a, b]])
        except KeyError:
            # No cycles found, so just pick a random correct case and fail :)
            self.assertEqual(cycles, [[a, b, a]])

        # Case 1
        m = myokit.Model('bug')
        a = m.add_component('a')
        b = m.add_component('b')
        p = a.add_variable('p')
        q = a.add_variable('q')
        r = b.add_variable('r')
        s = b.add_variable('s')
        p.set_rhs('b.r')
        p.promote(0)
        q.set_rhs(1)
        r.set_rhs(1)
        s.set_rhs('a.q')
        cycles = m.component_cycles()
        try:
            # Try both orders, (each is valid)
            if cycles[0][0] == a:
                self.assertEqual(cycles, [[a, b, a]])
            else:
                self.assertEqual(cycles, [[b, a, b]])
        except KeyError:
            # No cycles found, so just pick a random correct case and fail :)
            self.assertEqual(cycles, [[a, b, a]])


class SolvableOrderTest(DepTest):
    """
    Tests if the solvable order of the equations is determined correctly.

    TODO: This test was written with the assumption that the order returned
    could vary in ways that did not affect solvability. This has now been
    changed so that the solvable order returned is consistent for models that
    are equivalent.
    """
    def test_solvable_order(self):
        # Test model.solvable_order()

        # Shared properties
        self.ccomp = None
        self.order = None

        def comp(name):
            """ Set current component """
            self.assertIn(name, self.order)
            self.ccomp = str(name)

        def eq(lhs):
            """ Get equation for lhs """
            if not isinstance(lhs, myokit.Expression):
                lhs = self.m.get(lhs).lhs()
            for eq in self.order[self.ccomp]:
                if eq.lhs == lhs:
                    return eq

        def before(lhs1, *lhs2s):
            """ Asserts lhs1 comes before lhs2 in the current component """
            if isinstance(lhs1, basestring):
                lhs1 = self.m.get(self.ccomp + '.' + lhs1).lhs()
            for lhs2 in lhs2s:
                if isinstance(lhs2, basestring):
                    lhs2 = self.m.get(self.ccomp + '.' + lhs2).lhs()
                i1 = i2 = None
                for i, eq in enumerate(self.order[self.ccomp]):
                    if eq.lhs == lhs1:
                        i1 = i
                        if i2:
                            break
                    if eq.lhs == lhs2:
                        i2 = i
                        if i1:
                            break
                if debug:
                    if i1 < i2:
                        print(lhs1, 'occurs before', lhs2)
                    else:
                        print(lhs1, 'does NOT occur before', lhs2)
                self.assertLess(i1, i2)

        def cbefore(c1, *c2s):
            """ Asserts c1 comes before c2 """
            for c2 in c2s:
                i1 = i2 = None
                for i, c in enumerate(self.order):
                    if c == c1:
                        i1 = i
                        if i2:
                            break
                    if c == c2:
                        i2 = i
                        if i1:
                            break
                if debug:
                    if i1 < i2:
                        print(c1, 'occurs before', c2)
                    else:
                        print(c1, 'does NOT occur before', c2)
                self.assertLess(i1, i2)

        # Start
        # Load model, get order
        self.order = self.m.solvable_order()
        # Start testing
        self.head('Testing cell component')
        comp('cell')
        before('R', 'RTF')
        before('T', 'RTF')
        before('F', 'RTF')
        self.head('Testing backround current component')
        comp('ib')
        before('gb', 'Ib')
        self.head('Testing ik1 component')
        comp('ik1')
        cbefore('cell', 'ik1')
        before('E', 'gK1.alpha', 'gK1.beta')
        before('gK1.alpha', 'gK1')
        before('gK1.beta', 'gK1')
        before('gK1', 'IK1')
        before('E', 'IK1')
        self.head('Testing ica component')
        comp('ica')
        cbefore('cell', 'ica')
        before('d.alpha', 'd')
        before('d.beta', 'd')
        before('d.beta.vc.vd', 'd.beta.vc')
        before('d.beta.vc', 'd.beta.va', 'd.beta.vb')
        before('d.beta.va', 'd.beta')
        before('d.beta.vb', 'd.beta')
        before('f.alpha', 'f')
        before('f.beta', 'f')
        before('gCa', 'ICa.nest1')
        before('ICa.nest2', 'ICa.nest1')
        before('ICa.nest1', 'ICa')
        before('ICa', 'Ca_i')
        self.head('Testing ikp component')
        comp('ikp')
        before('gKp', 'IKp')
        self.head('Testing ik component')
        comp('ik')
        cbefore('cell', 'ik')
        before('x.alpha', 'x')
        before('x.beta', 'x')
        before('PNa_K', 'E')
        before('gK', 'IK')
        before('xi', 'IK')
        before('E', 'IK')
        self.head('Testing ina component')
        comp('ina')
        before('m.alpha', 'm')
        before('m.beta', 'm')
        before('a', 'h.alpha', 'h.beta')
        before('h.alpha', 'h')
        before('h.beta', 'h')
        before('a', 'j.alpha', 'j.beta')
        before('j.alpha', 'j')
        before('j.beta', 'j')
        before('gNa', 'INa')
        before('ENa', 'INa')
        self.head('Testing membrane component')
        comp('membrane')
        cbefore('ina', 'membrane')
        cbefore('ik', 'membrane')
        cbefore('ib', 'membrane')
        cbefore('ikp', 'membrane')
        cbefore('ik1', 'membrane')
        cbefore('ica', 'membrane')
        cbefore('engine', 'membrane')
        before('stim_amplitude', 'i_stim')
        before('i_stim', 'V')
        self.head('Testing dot test component')
        comp('test')
        cbefore('membrane', 'test')
        before(self.d('test.t1'), 'inter')
        before('inter', 't2')
        self.head('Finished testing solvable_order')
        del self.ccomp
        del self.order

        # Test with cycles
        self.m.get('ina.j').demote()
        self.assertRaisesRegex(
            RuntimeError, 'Equation ordering failed.', self.m.solvable_order)

    def test_has_interdependent_components(self):
        # Test Model.has_interdependent_components().

        m = myokit.Model()
        c = m.add_component('c')
        c1 = c.add_variable('c1')
        c1.set_rhs(1)
        c2 = c.add_variable('c2')
        c2.set_rhs(2)
        self.assertFalse(m.has_interdependent_components())
        d = m.add_component('d')
        d1 = d.add_variable('d1')
        d1.set_rhs('c.c1')
        self.assertFalse(m.has_interdependent_components())
        c2.set_rhs('d.d1')
        self.assertTrue(m.has_interdependent_components())

    def test_expressions_for(self):
        # Test Model.expressions_for().

        def before(lhs1, *lhs2s):
            """ Asserts lhs2 comes before lhs1 """
            if isinstance(lhs1, basestring):
                if lhs1.startswith('dot('):
                    lhs1 = myokit.Derivative(myokit.Name(
                        self.m.get(lhs1[4:-1])))
                else:
                    lhs1 = myokit.Name(self.m.get(lhs1))
            for lhs2 in lhs2s:
                if isinstance(lhs2, basestring):
                    if lhs2.startswith('dot('):
                        lhs2 = myokit.Derivative(myokit.Name(
                            self.m.get(lhs2[4:-1])))
                    else:
                        lhs2 = myokit.Name(self.m.get(lhs2))
                i1 = i2 = None
                for i, eq in enumerate(self.eqs):
                    if eq.lhs == lhs1:
                        i1 = i
                        if i2:
                            break
                    if eq.lhs == lhs2:
                        i2 = i
                        if i1:
                            break
                if debug:
                    if i1 < i2:
                        print(lhs1, 'occurs before', lhs2)
                    else:
                        print(lhs1, 'does NOT occur before', lhs2)
                self.assertGreater(i1, i2)

        # Simple test
        self.eqs, self.vrs = self.m.expressions_for('ina.m')
        self.assertEqual(len(self.eqs), 5)
        self.assertEqual(len(self.vrs), 2)
        self.assertIn(myokit.Name(self.m.get('ina.m')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('membrane.V')), self.vrs)
        before('dot(ina.m)', 'ina.m.tau', 'ina.m.inf')
        before('ina.m.inf', 'ina.m.alpha', 'ina.m.tau')
        before('ina.m.tau', 'ina.m.alpha', 'ina.m.beta')
        del self.eqs, self.vrs

        # Larger test (and try with LhsExpression instead of string)
        self.eqs, self.vrs = self.m.expressions_for(
            self.m.get('membrane.V').lhs())
        self.assertEqual(len(self.vrs), 9)
        self.assertIn(myokit.Name(self.m.get('engine.pace')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('membrane.V')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.m')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.h')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.j')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ik.x')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ica.d')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ica.f')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ica.Ca_i')), self.vrs)
        self.assertEqual(len(self.eqs), 34)
        before('dot(membrane.V)', 'membrane.i_stim', 'ina.INa', 'ik.IK',
               'ib.Ib', 'ikp.IKp', 'ik1.IK1', 'ica.ICa')
        before('membrane.i_stim', 'membrane.stim_amplitude')
        before('ina.INa', 'ina.gNa', 'ina.ENa')
        before('ina.ENa', 'cell.RTF', 'cell.Na_o', 'cell.Na_i')
        before('cell.RTF', 'cell.R', 'cell.T', 'cell.F')
        before('ik.IK', 'ik.gK', 'ik.xi', 'ik.E')
        before('ik.gK', 'cell.K_o')
        before('ik.E', 'cell.RTF', 'ik.PNa_K', 'cell.K_o', 'cell.Na_o',
               'cell.K_i', 'cell.Na_i')
        before('ib.Ib', 'ib.gb')
        before('ikp.IKp', 'ikp.gKp')
        before('ik1.IK1', 'ik1.gK1', 'ik1.E')
        before('ik1.gK1', 'ik1.gK1.alpha', 'ik1.gK1.beta', 'cell.K_o')
        before('ik1.gK1.alpha', 'ik1.E')
        before('ik1.gK1.beta', 'ik1.E')
        before('ik1.E', 'cell.RTF', 'cell.K_o', 'cell.K_i')
        before('ica.ICa', 'ica.ICa.nest1', 'ica.E')
        before('ica.ICa.nest1', 'ica.ICa.nest2', 'ica.gCa')
        before('ica.E', 'cell.Ca_o')
        del self.eqs, self.vrs

        # Multiple variables
        self.eqs, self.vrs = self.m.expressions_for('ina.m', 'ina.h')
        self.assertEqual(len(self.eqs), 11)
        self.assertEqual(len(self.vrs), 3)
        self.assertIn(myokit.Name(self.m.get('membrane.V')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.m')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.h')), self.vrs)
        before('dot(ina.m)', 'ina.m.tau', 'ina.m.inf')
        before('ina.m.inf', 'ina.m.alpha', 'ina.m.tau')
        before('ina.m.tau', 'ina.m.alpha', 'ina.m.beta')
        before('dot(ina.h)', 'ina.h.tau', 'ina.h.inf')
        before('ina.h.inf', 'ina.h.alpha', 'ina.h.tau')
        before('ina.h.tau', 'ina.h.alpha', 'ina.h.beta')
        before('ina.h.alpha', 'ina.a')
        before('ina.h.beta', 'ina.a')
        del self.eqs, self.vrs

        # Variables that depend on dot() expressions
        self.eqs, self.vrs = self.m.expressions_for('test.t1', 'test.t2')
        self.assertEqual(len(self.eqs), 34 + 3)
        before('dot(test.t2)', 'test.inter')
        before('test.inter', 'dot(test.t1)')
        before('dot(test.t1)', 'dot(membrane.V)')
        del self.eqs, self.vrs

        # Unsolvable system
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        x.set_rhs('y')
        y.set_rhs('x')
        self.assertRaisesRegex(
            Exception, 'Failed to solve', m.expressions_for, 'c.x')

        # Test without arguments
        eqs, vrs = self.m.expressions_for()
        self.assertEqual(len(eqs), 0)
        self.assertEqual(len(vrs), 0)

    def test_equivalent_models_1(self):
        # Tests that the order returned for equivalent models is the same
        # (This is new 2022-06-22). Tests above do not assume this is the case.

        m1 = myokit.parse_model('''
        [[model]]
        comp_2.h = 1.234

        [engine]
        time = 0 bind time

        [comp_1]
        a = 30
        b = 10
        c = a + b + d
        d = 20

        [comp_2]
        e = 35 - f
        f = 40
        g = 50 - j
        dot(h) = e / f + j
        i = 5 * h
        j = 60 - e
        ''')
        m2 = myokit.parse_model('''
        [[model]]
        comp_2.h = 1.234

        [engine]
        time = 0 bind time

        [comp_2]
        j = 60 - e
        i = 5 * h
        dot(h) = e / f + j
        g = 50 - j
        f = 40
        e = 35 - f

        [comp_1]
        d = 20
        c = a + b + d
        b = 10
        a = 30
        ''')

        # Models are equivalent, despite different ordering internally
        self.assertEqual(m1.code(), m2.code())

        # Get solvable orders as flat lists of variable names
        o1, o2 = [], []
        for eqlist in m1.solvable_order().values():
            for eq in eqlist:
                o1.append(str(eq.lhs))
        for eqlist in m2.solvable_order().values():
            for eq in eqlist:
                o2.append(str(eq.lhs))
        self.assertEqual(len(o1), len(o2))  # If not, we have bigger problems..

        # Compare entries
        for v1, v2 in zip(o1, o2):
            self.assertEqual(v1, v2)

    def test_equivalent_models_2(self):
        # Tests that the order returned for equivalent models is the same
        # (This is new 2022-06-22). Tests above do not assume this is the case.

        m1 = self.m
        m2 = myokit.parse_model(m1.code())

        # Get solvable orders as flat lists of variable names
        o1, o2 = [], []
        for eqlist in m1.solvable_order().values():
            for eq in eqlist:
                o1.append(str(eq.lhs))
        for eqlist in m2.solvable_order().values():
            for eq in eqlist:
                o2.append(str(eq.lhs))
        self.assertEqual(len(o1), len(o2))  # If not, we have bigger problems..

        # Compare entries
        for v1, v2 in zip(o1, o2):
            self.assertEqual(v1, v2)


if __name__ == '__main__':
    print('Add -v for more debug output')
    import sys
    if '-v' in sys.argv:
        debug = True
    unittest.main()
