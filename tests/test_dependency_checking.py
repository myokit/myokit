#!/usr/bin/env python3
#
# Tests the dependency resolving and sorting to solvable order in the myokit
# core.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit
from shared import DIR_DATA

# Extra output
debug = False


class DepTest(unittest.TestCase):
    """
    General dependency test. Loads model and destroys it
    """
    @classmethod
    def setUpClass(cls):
        cls.m = myokit.load_model(DIR_DATA / 'beeler-1977-dependencies.mmt')

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
        if isinstance(key, str):
            key = self.m.get(key)
            if isinstance(key, myokit.Variable):
                key = key.lhs()

        # Convert deps list to list of objects. If a string name is given,
        # convert it to a Name. Ensure no duplicates are given.
        deps = list(set(deps))
        for k, dep in enumerate(deps):
            if isinstance(dep, str):
                deps[k] = self.n(dep)

        # Get dep map
        self.assertIn(key, depmap)
        dmap = depmap[key]

        # Show what will be tested
        if debug:
            if deps:
                print(f'Testing if {key!r} has ')
                print('  [' + ', '.join([repr(d) for d in deps]) + ']')
                print('It has:')
                print('  [' + ', '.join([repr(d) for d in dmap]) + ']')
            else:
                if isinstance(key, myokit.Expression):
                    if key.var().is_state():
                        print(f'{key!r} is a state')
                    else:
                        print(f'{key!r} is a constant')
                else:
                    print(f'{key!r} is empty')

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
                print(f'{comp.name()} has no dependencies')

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

        has('ina.m', 'ina.m.alpha', 'ina.m.beta', 'ina.m')
        has('ix1.x1', 'ix1.x1.inf', 'ix1.x1.tau', 'ix1.x1')
        has('test.t1', d('membrane.V'))
        has('test.inter', d('test.t1'))
        has('test.dx1', d('ix1.x1'))


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
        head('Testing stimulus component')
        has('stimulus.amplitude')
        has('stimulus.i_stim', 'engine.pace', 'stimulus.amplitude')
        head('Testing ik1 component')
        has('ik1.IK1', 'membrane.V')
        head('Testing ix1 component')
        has('ix1.Ix1', 'ix1.x1', 'membrane.V')
        has('ix1.x1.alpha', 'membrane.V')
        has('ix1.x1.beta', 'membrane.V')
        has('ix1.x1.tau', 'ix1.x1.alpha', 'ix1.x1.beta')
        has('ix1.x1.inf', 'ix1.x1.alpha', 'ix1.x1.tau')
        has('ix1.x1', 'ix1.x1.inf', 'ix1.x1.tau', 'ix1.x1')
        has(n('ix1.x1'))
        head('Testing ina component')
        has('ina.gNaBar')
        has('ina.gNaC')
        has('ina.ENa')
        has('ina.INa', 'ina.gNaBar', 'ina.m', 'ina.h', 'ina.j', 'ina.gNaC',
            'membrane.V', 'ina.ENa')
        has('ina.m.alpha', 'membrane.V')
        has('ina.m.beta', 'membrane.V')
        has('ina.m', 'ina.m.alpha', 'ina.m.beta', 'ina.m')
        has(n('ina.m'))
        has('ina.h.alpha', 'membrane.V')
        has('ina.h.beta', 'membrane.V')
        has('ina.h', 'ina.h.alpha', 'ina.h.beta', 'ina.h')
        has(n('ina.h'))
        has('ina.j.alpha', 'membrane.V')
        has('ina.j.beta', 'membrane.V', 'ina.j.va')
        has('ina.j.va', 'ina.j.va.vb', 'ina.j.va.vc')
        has('ina.j.va.vb', 'ina.j.va.vc')
        has('ina.j.va.vc', 'ina.j.va.vc.vd')
        has('ina.j.va.vc.vd', 'membrane.V')
        has('ina.j', 'ina.j.alpha', 'ina.j.beta', 'ina.j')
        has(n('ina.j'))
        head('Testing is component')
        has('is.gsBar')
        has('is.Es', 'calcium.Cai', 'cell.Ca_ref')
        has('is.Is', 'is.Is.g', 'membrane.V', 'is.Es')
        has('is.Is.g', 'is.gsBar', 'is.Is.gates')
        has('is.Is.gates', 'is.d', 'is.f')
        has('is.d.alpha', 'membrane.V')
        has('is.d.beta', 'membrane.V')
        has('is.d', 'is.d.alpha', 'is.d.beta', 'is.d')
        has(n('is.d'))
        has('is.f.alpha', 'membrane.V')
        has('is.f.beta', 'membrane.V')
        has('is.f.tau', 'is.f.alpha', 'is.f.beta')
        has('is.f.inf', 'is.f.alpha', 'is.f.tau')
        has('is.f', 'is.f.inf', 'is.f.tau', 'is.f')
        has(n('is.f'))
        head('Testing calcium component')
        has('calcium.Cai', 'is.Is', 'calcium.Cai')
        head('Testing cell component')
        has('cell.Ca_ref')
        has(n('calcium.Cai'))
        head('Testing membrane component')
        has('membrane.C')
        has('membrane.i_diff')
        has('membrane.i_ion', 'ik1.IK1', 'ix1.Ix1', 'ina.INa', 'is.Is')
        has('membrane.V', 'membrane.C', 'membrane.i_ion', 'stimulus.i_stim',
            'membrane.i_diff')
        has(n('membrane.V'))
        head('Testing dot() test component')
        has('test.t1', d('membrane.V'))
        has('test.inter', d('test.t1'))
        has('test.t2', 'test.inter')
        has('test.dx1', d('ix1.x1'))
        has(n('test.t1'))
        has(n('test.t2'))
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
        head('Testing stimulus component')
        has('stimulus.amplitude')
        Istim = ('stimulus.i_stim', 'stimulus.amplitude', 'engine.pace')
        has(*Istim)
        head('Testing ik1 component')
        IK1 = ('ik1.IK1', 'membrane.V')
        has(*IK1)
        head('Testing ix1 component')
        Ix1 = ('ix1.Ix1', 'ix1.x1', 'membrane.V')
        has(*Ix1)
        has('ix1.x1.alpha', 'membrane.V')
        has('ix1.x1.beta', 'membrane.V')
        has('ix1.x1.tau', 'ix1.x1.alpha', 'ix1.x1.beta', 'membrane.V')
        has('ix1.x1.inf', 'ix1.x1.tau', 'ix1.x1.alpha', 'ix1.x1.beta',
            'membrane.V')
        has('ix1.x1', 'ix1.x1', 'ix1.x1.inf', 'ix1.x1.tau', 'ix1.x1.alpha',
            'ix1.x1.beta', 'membrane.V')
        has(n('ix1.x1'))
        head('Testing ina component')
        has('ina.gNaBar')
        has('ina.gNaC')
        has('ina.ENa')
        INa = ('ina.INa', 'ina.gNaBar', 'ina.gNaC', 'ina.ENa', 'ina.m',
               'ina.h', 'ina.j', 'membrane.V')
        has(*INa)
        has('ina.m.alpha', 'membrane.V')
        has('ina.m.beta', 'membrane.V')
        has('ina.m', 'ina.m', 'ina.m.alpha', 'ina.m.beta', 'membrane.V')
        has(n('ina.m'))
        has('ina.h.alpha', 'membrane.V')
        has('ina.h.beta', 'membrane.V')
        has('ina.h', 'ina.h', 'ina.h.alpha', 'ina.h.beta', 'membrane.V')
        has(n('ina.h'))
        has('ina.j.alpha', 'membrane.V')
        has('ina.j.va.vc.vd', 'membrane.V')
        has('ina.j.va.vc', 'ina.j.va.vc.vd', 'membrane.V')
        has('ina.j.va.vb', 'ina.j.va.vc', 'ina.j.va.vc.vd', 'membrane.V')
        VA = ('ina.j.va', 'ina.j.va.vb', 'ina.j.va.vc', 'ina.j.va.vc.vd',
              'membrane.V')
        has(*VA)
        has('ina.j.beta', *VA)
        has('ina.j', 'ina.j', 'ina.j.alpha', 'ina.j.beta', *VA)
        has(n('ina.j'))
        head('Testing is component')
        has('is.gsBar')
        Es = ('is.Es', 'calcium.Cai', 'cell.Ca_ref')
        has(*Es)
        G = ('is.Is.g', 'is.gsBar', 'is.Is.gates', 'is.d', 'is.f')
        has(*G)
        has('is.Is.gates', 'is.d', 'is.f')
        Is = ('is.Is', 'membrane.V') + G + Es
        has(*Is)
        has('is.d.alpha', 'membrane.V')
        has('is.d.beta', 'membrane.V')
        has('is.d', 'is.d', 'is.d.alpha', 'is.d.beta', 'membrane.V')
        has(n('is.d'))
        has('is.f.alpha', 'membrane.V')
        has('is.f.beta', 'membrane.V')
        has('is.f.tau', 'is.f.alpha', 'is.f.beta', 'membrane.V')
        has('is.f.inf', 'is.f.tau', 'is.f.alpha', 'is.f.beta', 'membrane.V')
        has('is.f', 'is.f', 'is.f.inf', 'is.f.tau', 'is.f.alpha', 'is.f.beta',
            'membrane.V')
        has(n('is.f'))
        head('Testing calcium component')
        has('calcium.Cai', 'calcium.Cai', *Is)
        has(n('calcium.Cai'))
        head('Testing cell component')
        has('cell.Ca_ref')
        head('Testing membrane component')
        has('membrane.C')
        has('membrane.i_diff')
        Iion = ('membrane.i_ion',) + IK1 + Ix1 + INa + Is
        has(*Iion)
        I = ('membrane.C', 'membrane.i_diff') + Iion + Istim
        has('membrane.V', *I)
        has(n('membrane.V'))
        head('Testing dot() test component')
        has('test.t1', d('membrane.V'), *I)
        has('test.inter', d('test.t1'), d('membrane.V'), *I)
        has('test.t2', 'test.inter', d('test.t1'), d('membrane.V'), *I)
        has('test.dx1', d('ix1.x1'), 'ix1.x1', 'ix1.x1.inf', 'ix1.x1.tau',
            'ix1.x1.alpha', 'ix1.x1.beta', 'membrane.V')
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
            if isinstance(lhs, str):
                lhs = self.m.get(lhs).lhs()
            self.assertNotIn(lhs, depmap)

        # Start testing
        head('Deep dependency mapping')
        head('Testing engine component')
        has('engine.time')
        has('engine.pace')
        head('Testing stimulus component')
        has('stimulus.amplitude')
        Istim = ('stimulus.i_stim', 'stimulus.amplitude', 'engine.pace')
        has(*Istim)
        head('Testing ik1 component')
        IK1 = ('ik1.IK1', )
        has(*IK1)
        head('Testing ix1 component')
        Ix1 = ('ix1.Ix1', )
        has(*Ix1)
        has('ix1.x1.alpha')
        has('ix1.x1.beta')
        has('ix1.x1.tau', 'ix1.x1.alpha', 'ix1.x1.beta')
        has('ix1.x1.inf', 'ix1.x1.tau', 'ix1.x1.alpha', 'ix1.x1.beta')
        has('ix1.x1', 'ix1.x1.inf', 'ix1.x1.tau', 'ix1.x1.alpha',
            'ix1.x1.beta')
        nhas(n('ix1.x1'))
        head('Testing ina component')
        has('ina.gNaBar')
        has('ina.gNaC')
        has('ina.ENa')
        INa = ('ina.INa', 'ina.gNaBar', 'ina.gNaC', 'ina.ENa')
        has(*INa)
        has('ina.m.alpha')
        has('ina.m.beta')
        has('ina.m', 'ina.m.alpha', 'ina.m.beta')
        nhas(n('ina.m'))
        has('ina.h.alpha')
        has('ina.h.beta')
        has('ina.h', 'ina.h.alpha', 'ina.h.beta')
        nhas(n('ina.h'))
        has('ina.j.alpha')
        has('ina.j.va.vc.vd')
        has('ina.j.va.vc', 'ina.j.va.vc.vd')
        has('ina.j.va.vb', 'ina.j.va.vc', 'ina.j.va.vc.vd')
        VA = ('ina.j.va', 'ina.j.va.vb', 'ina.j.va.vc', 'ina.j.va.vc.vd')
        has(*VA)
        has('ina.j.beta', *VA)
        has('ina.j', 'ina.j.alpha', 'ina.j.beta', *VA)
        nhas(n('ina.j'))
        head('Testing is component')
        has('is.gsBar')
        Es = ('is.Es', 'cell.Ca_ref')
        has(*Es)
        G = ('is.Is.g', 'is.gsBar', 'is.Is.gates')
        has(*G)
        has('is.Is.gates')
        Is = ('is.Is', ) + G + Es
        has(*Is)
        has('is.d.alpha')
        has('is.d.beta')
        has('is.d', 'is.d.alpha', 'is.d.beta')
        nhas(n('is.d'))
        has('is.f.alpha')
        has('is.f.beta')
        has('is.f.tau', 'is.f.alpha', 'is.f.beta')
        has('is.f.inf', 'is.f.tau', 'is.f.alpha', 'is.f.beta')
        has('is.f', 'is.f.inf', 'is.f.tau', 'is.f.alpha', 'is.f.beta')
        nhas(n('is.f'))
        head('Testing calcium component')
        has('calcium.Cai', *Is)
        nhas(n('calcium.Cai'))
        head('Testing cell component')
        has('cell.Ca_ref')
        head('Testing membrane component')
        has('membrane.C')
        has('membrane.i_diff')
        Iion = ('membrane.i_ion',) + IK1 + Ix1 + INa + Is
        has(*Iion)
        I = ('membrane.C', 'membrane.i_diff') + Iion + Istim
        has('membrane.V', *I)
        nhas(n('membrane.V'))
        head('Testing dot() test component')
        has('test.t1', d('membrane.V'), *I)
        has('test.inter', d('test.t1'), d('membrane.V'), *I)
        has('test.t2', 'test.inter', d('test.t1'), d('membrane.V'), *I)
        has('test.dx1', d('ix1.x1'), 'ix1.x1.inf', 'ix1.x1.tau',
            'ix1.x1.alpha', 'ix1.x1.beta')
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
            if isinstance(lhs, str):
                lhs = self.m.get(lhs).lhs()
            self.assertNotIn(lhs, depmap)

        # Start testing
        head('Deep dependency mapping')
        head('Testing engine component')
        has('engine.time')
        has('engine.pace')
        head('Testing stimulus component')
        has('stimulus.amplitude')
        Istim = ('stimulus.i_stim', 'stimulus.amplitude', 'engine.pace')
        has(*Istim)
        head('Testing ik1 component')
        IK1 = ('ik1.IK1', 'membrane.V')
        has(*IK1)
        head('Testing ix1 component')
        Ix1 = ('ix1.Ix1', 'ix1.x1', 'membrane.V')
        has(*Ix1)
        nhas('ix1.x1.alpha')
        nhas('ix1.x1.beta')
        nhas('ix1.x1.tau')
        nhas('ix1.x1.inf')
        has('ix1.x1', 'ix1.x1', 'membrane.V')
        has(n('ix1.x1'))
        head('Testing ina component')
        has('ina.gNaBar')
        has('ina.gNaC')
        has('ina.ENa')
        INa = ('ina.INa', 'ina.gNaBar', 'ina.gNaC', 'ina.ENa', 'ina.m',
               'ina.h', 'ina.j', 'membrane.V')
        has(*INa)
        nhas('ina.m.alpha')
        nhas('ina.m.beta')
        has('ina.m', 'ina.m', 'membrane.V')
        has(n('ina.m'))
        nhas('ina.h.alpha')
        nhas('ina.h.beta')
        has('ina.h', 'ina.h', 'membrane.V')
        has(n('ina.h'))
        nhas('ina.j.alpha')
        nhas('ina.j.beta')
        nhas('ina.j.va')
        nhas('ina.j.va.vb')
        nhas('ina.j.va.vc')
        nhas('ina.j.va.vc.vd')
        has('ina.j', 'ina.j', 'membrane.V')
        has(n('ina.j'))
        head('Testing is component')
        has('is.gsBar')
        Es = ('is.Es', 'calcium.Cai', 'cell.Ca_ref')
        has(*Es)
        Is = ('is.Is', 'is.gsBar', 'is.d', 'is.f', 'membrane.V') + Es
        has(*Is)
        nhas('is.Is.g')
        nhas('is.Is.gates')
        nhas('is.d.alpha')
        nhas('is.d.beta')
        has('is.d', 'is.d', 'membrane.V')
        has(n('is.d'))
        nhas('is.f.alpha')
        nhas('is.f.beta')
        nhas('is.f.tau')
        nhas('is.f.inf')
        has('is.f', 'is.f', 'membrane.V')
        has(n('is.f'))
        head('Testing calcium component')
        has('calcium.Cai', 'calcium.Cai', *Is)
        has(n('calcium.Cai'))
        head('Testing cell component')
        has('cell.Ca_ref')
        head('Testing membrane component')
        has('membrane.C')
        has('membrane.i_diff')
        Iion = ('membrane.i_ion',) + IK1 + Ix1 + INa + Is
        has(*Iion)
        I = ('membrane.C', 'membrane.i_diff') + Iion + Istim
        has('membrane.V', *I)
        has(n('membrane.V'))
        head('Testing dot() test component')
        has('test.t1', d('membrane.V'), *I)
        has('test.inter', d('test.t1'), d('membrane.V'), *I)
        has('test.t2', 'test.inter', d('test.t1'), d('membrane.V'), *I)
        has('test.dx1', d('ix1.x1'), 'ix1.x1', 'membrane.V')
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

        # All states
        S = ('membrane.V', 'ix1.x1', 'ina.m', 'ina.h', 'ina.j', 'is.d',
             'is.f', 'calcium.Cai')

        # Start testing
        head('Deep dependency mapping')
        head('Testing engine component')
        has('engine.time')
        has('engine.pace')
        head('Testing stimulus component')
        has('stimulus.amplitude')
        has('stimulus.i_stim')
        head('Testing ik1 component')
        has('ik1.IK1', 'membrane.V')
        head('Testing ix1 component')
        has('ix1.Ix1', 'ix1.x1', 'membrane.V')
        has('ix1.x1.alpha', 'membrane.V')
        has('ix1.x1.beta', 'membrane.V')
        has('ix1.x1.tau', 'membrane.V')
        has('ix1.x1.inf', 'membrane.V')
        has('ix1.x1', 'ix1.x1', 'membrane.V')
        has(n('ix1.x1'))
        head('Testing ina component')
        has('ina.gNaBar')
        has('ina.gNaC')
        has('ina.ENa')
        has('ina.INa', 'ina.m', 'ina.h', 'ina.j', 'membrane.V')
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
        has('ina.j.va', 'membrane.V')
        has('ina.j.va.vb', 'membrane.V')
        has('ina.j.va.vc', 'membrane.V')
        has('ina.j.va.vc.vd', 'membrane.V')
        has('ina.j', 'ina.j', 'membrane.V')
        has(n('ina.j'))
        head('Testing is component')
        has('is.gsBar')
        has('is.Es', 'calcium.Cai')
        has('is.Is', 'is.d', 'is.f', 'membrane.V', 'calcium.Cai')
        has('is.Is.g', 'is.d', 'is.f')
        has('is.Is.gates', 'is.d', 'is.f')
        has('is.d.alpha', 'membrane.V')
        has('is.d.beta', 'membrane.V')
        has('is.d', 'is.d', 'membrane.V')
        has(n('is.d'))
        has('is.f.alpha', 'membrane.V')
        has('is.f.beta', 'membrane.V')
        has('is.f.tau', 'membrane.V')
        has('is.f.inf', 'membrane.V')
        has('is.f', 'is.f', 'membrane.V')
        has(n('is.f'))
        head('Testing calcium component')
        has('calcium.Cai', 'calcium.Cai', 'is.d', 'is.f', 'membrane.V')
        has(n('calcium.Cai'))
        head('Testing cell component')
        has('cell.Ca_ref')
        head('Testing membrane component')
        has('membrane.C')
        has('membrane.i_diff')
        has('membrane.i_ion', *S)
        has('membrane.V', *S)
        has(n('membrane.V'))
        head('Testing dot() test component')
        has('test.t1', *S)
        has('test.inter', *S)
        has('test.t2', *S)
        has('test.dx1', 'ix1.x1', 'membrane.V')
        has(n('test.t1'))
        has(n('test.t2'))
        head(
            'Deep dependency check complete [with state deps, no encompassed'
            ' vars]')

    def test_deep_cyles(self):
        # Test if the deep test finds cyclical dependencies.

        m = self.m.clone()
        m.get('ina.ENa').set_rhs('3 * ina.INa')
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
        has('membrane', 'stimulus', 'ik1', 'ix1', 'ina', 'is')
        has('stimulus', 'engine')
        has('ik1', 'membrane')
        has('ix1', 'membrane')
        has('ina', 'membrane')
        has('is', 'membrane', 'calcium', 'cell')
        has('calcium', 'is')
        has('cell')
        has('engine')
        has('test', 'membrane', 'ix1')
        # Next
        head('omit_states=True, omit_constants=False')
        depmap = self.m.map_component_dependencies(
            omit_states=True, omit_constants=False)
        has('membrane', 'stimulus', 'ik1', 'ix1', 'ina', 'is')
        has('stimulus', 'engine')
        has('ik1')
        has('ix1')
        has('ina')
        has('is', 'cell')
        has('calcium', 'is')
        has('cell')
        has('engine')
        # dot(v) is a derivative, not a state value :)
        has('test', 'membrane', 'ix1')
        # Next
        head('omit_states=False, omit_constants=True')
        depmap = self.m.map_component_dependencies(
            omit_states=False, omit_constants=True)
        has('membrane', 'stimulus', 'ik1', 'ix1', 'ina', 'is')
        has('stimulus', 'engine')
        has('ik1', 'membrane')
        has('ix1', 'membrane')
        has('ina', 'membrane')
        has('is', 'membrane', 'calcium')
        has('calcium', 'is')
        has('cell')
        has('engine')
        has('test', 'membrane', 'ix1')
        # Next
        head('omit_states=True, omit_constants=True')
        depmap = self.m.map_component_dependencies(
            omit_states=True, omit_constants=True)
        has('membrane', 'stimulus', 'ik1', 'ix1', 'ina', 'is')
        has('stimulus', 'engine')
        has('ik1')
        has('ix1')
        has('ina')
        has('is')
        has('calcium', 'is')
        has('cell')
        has('engine')
        has('test', 'membrane', 'ix1')

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

        # Inputs to membrane and stimulus, outputs from stimulus and ik1, and
        # the inputs and outputs of engine are the same in all cases.
        I = ('stimulus.i_stim', 'ik1.IK1', 'ix1.Ix1', 'ina.INa', 'is.Is')

        def check_shared():
            inn('membrane', *I)
            inn('stimulus', 'engine.pace')
            out('stimulus', 'stimulus.i_stim')
            out('ik1', 'ik1.IK1')
            inn('engine')
            out('engine', 'engine.pace')
            inn('cell')

        # 1 FFF: States, Derivatives, Constants
        # 2 FFT: States, Derivatives, No constants
        for omit_constants in (False, True):
            d1, d2 = self.m.map_component_io(
                omit_states=False,
                omit_derivatives=False,
                omit_constants=omit_constants,
            )
            head(f'1/2 FF{omit_constants}: States, Derivatives')
            C = () if omit_constants else ('cell.Ca_ref', )
            check_shared()
            out('membrane', d('membrane.V'))
            inn('ik1', 'membrane.V')
            inn('ix1', 'ix1.x1', 'membrane.V')
            out('ix1', 'ix1.Ix1', d('ix1.x1'))
            inn('ina', 'ina.m', 'ina.h', 'ina.j', 'membrane.V')
            out('ina', 'ina.INa', d('ina.m'), d('ina.h'), d('ina.j'))
            inn('is', 'is.d', 'is.f', 'membrane.V', 'calcium.Cai', *C)
            out('is', 'is.Is', d('is.d'), d('is.f'))
            inn('calcium', 'calcium.Cai', 'is.Is')
            out('calcium', d('calcium.Cai'))
            out('cell', *C)
            inn('test', d('membrane.V'), d('ix1.x1'))
            out('test', d('test.t1'), d('test.t2'))

        # 3 FTF: States, No derivatives, Constants
        # 4 FTT: States, No derivatives, No constants
        for omit_constants in (False, True):
            d1, d2 = self.m.map_component_io(
                omit_states=False,
                omit_derivatives=True,
                omit_constants=omit_constants,
            )
            head(f'3/4 FT{omit_constants}: States, No derivatives')
            C = () if omit_constants else ('cell.Ca_ref', )
            check_shared()
            out('membrane')
            inn('ik1', 'membrane.V')
            inn('ix1', 'ix1.x1', 'membrane.V')
            out('ix1', 'ix1.Ix1')
            inn('ina', 'ina.m', 'ina.h', 'ina.j', 'membrane.V')
            out('ina', 'ina.INa')
            inn('is', 'is.d', 'is.f', 'membrane.V', 'calcium.Cai', *C)
            out('is', 'is.Is')
            inn('calcium', 'calcium.Cai', 'is.Is')
            out('calcium')
            out('cell', *C)
            inn('test')
            out('test')

        # 5 TFF: No states, Derivatives, Constants
        # 6 TFT: No states, Derivatives, No constants
        # TFT is the realistic use-case!
        for omit_constants in (False, True):
            d1, d2 = self.m.map_component_io(
                omit_states=True,
                omit_derivatives=False,
                omit_constants=omit_constants,
            )
            head(f'5/6 TF{omit_constants}: No states, Derivatives')
            C = () if omit_constants else ('cell.Ca_ref', )
            check_shared()
            out('membrane', d('membrane.V'))
            inn('ik1')
            inn('ix1')
            out('ix1', 'ix1.Ix1', d('ix1.x1'))
            inn('ina')
            out('ina', 'ina.INa', d('ina.m'), d('ina.h'), d('ina.j'))
            inn('is', *C)
            out('is', 'is.Is', d('is.d'), d('is.f'))
            inn('calcium', 'is.Is')
            out('calcium', d('calcium.Cai'))
            out('cell', *C)
            inn('test', d('membrane.V'), d('ix1.x1'))
            out('test', d('test.t1'), d('test.t2'))

        # 7 TTF: No states, No derivatives, Constants
        # 8 TTT: No states, No derivatives, No constants
        for omit_constants in (False, True):
            d1, d2 = self.m.map_component_io(
                omit_states=True,
                omit_derivatives=True,
                omit_constants=omit_constants,
            )
            head(f'7/8 TT{omit_constants}: No states, No derivatives')
            C = () if omit_constants else ('cell.Ca_ref', )
            check_shared()
            out('membrane')
            inn('ik1')
            inn('ix1')
            out('ix1', 'ix1.Ix1')
            inn('ina')
            out('ina', 'ina.INa')
            inn('is', *C)
            out('is', 'is.Is')
            inn('calcium', 'is.Is')
            out('calcium')
            out('cell', *C)
            inn('test')
            out('test')

        # A TFF-RL: No states, Derivatives, Constants, in RL mode
        # B TFT-RL: No states, Derivatives, No Constants, in RL mode
        # TFT-RL is the practical use case
        rl_states = {}
        for state in ['ix1.x1', 'is.f']:
            rl_states[self.m.get(state)] = (
                self.m.get(f'{state}.inf'), self.m.get(f'{state}.tau'))
        for omit_constants in (False, True):
            d1, d2 = self.m.map_component_io(
                omit_states=True,
                omit_derivatives=False,
                omit_constants=omit_constants,
                rl_states=rl_states,
            )
            head(f'A/B TF{omit_constants}-RL: No states, Derivatives, RL mode')
            C = () if omit_constants else ('cell.Ca_ref', )
            check_shared()
            out('membrane', d('membrane.V'))
            inn('ik1')
            inn('ix1')
            # Derivative of RL state x1 is used by test, so still an output
            out('ix1', 'ix1.Ix1', d('ix1.x1'), 'ix1.x1.inf', 'ix1.x1.tau')
            inn('ina')
            out('ina', 'ina.INa', d('ina.m'), d('ina.h'), d('ina.j'))
            inn('is', *C)
            # Derivative of RL state f is not used elsewhere, so not an output
            out('is', 'is.Is', d('is.d'), 'is.f.inf', 'is.f.tau')
            inn('calcium', 'is.Is')
            out('calcium', d('calcium.Cai'))
            out('cell', *C)
            inn('test', d('membrane.V'), d('ix1.x1'))
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
            if isinstance(lhs1, str):
                lhs1 = self.m.get(f'{self.ccomp}.{lhs1}').lhs()
            for lhs2 in lhs2s:
                if isinstance(lhs2, str):
                    lhs2 = self.m.get(f'{self.ccomp}.{lhs2}').lhs()
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
        self.head('Testing stimulus component')
        comp('stimulus')
        cbefore('engine', 'stimulus')
        before('amplitude', 'i_stim')
        self.head('Testing ix1 component')
        comp('ix1')
        before('x1.alpha', 'x1.tau', 'x1.inf')
        before('x1.beta', 'x1.tau')
        before('x1.tau', 'x1.inf', 'x1')
        before('x1.inf', 'x1')
        self.head('Testing ina component')
        comp('ina')
        before('m.alpha', 'm')
        before('m.beta', 'm')
        before('h.alpha', 'h')
        before('h.beta', 'h')
        before('j.va.vc.vd', 'j.va.vc')
        before('j.va.vc', 'j.va.vb', 'j.va')
        before('j.va.vb', 'j.va')
        before('j.va', 'j.beta')
        before('j.alpha', 'j')
        before('j.beta', 'j')
        before('gNaBar', 'INa')
        before('gNaC', 'INa')
        before('ENa', 'INa')
        self.head('Testing is component')
        comp('is')
        before('d.alpha', 'd')
        before('d.beta', 'd')
        cbefore('cell', 'is')
        before('f.alpha', 'f.tau', 'f.inf')
        before('f.beta', 'f.tau')
        before('f.tau', 'f.inf', 'f')
        before('f.inf', 'f')
        before('gsBar', 'Is.g')
        before('Is.gates', 'Is.g')
        before('Is.g', 'Is')
        before('Es', 'Is')
        self.head('Testing calcium component')
        comp('calcium')
        cbefore('is', 'calcium')
        self.head('Testing membrane component')
        comp('membrane')
        cbefore('stimulus', 'membrane')
        cbefore('ik1', 'membrane')
        cbefore('ix1', 'membrane')
        cbefore('ina', 'membrane')
        cbefore('is', 'membrane')
        before('C', 'V')
        before('i_ion', 'V')
        self.head('Testing dot test component')
        comp('test')
        cbefore('membrane', 'test')
        cbefore('ix1', 'test')
        before(self.d('test.t1'), 'inter')
        before('inter', 't2')
        self.head('Finished testing solvable_order')
        del self.ccomp

        # Test caching
        order2 = self.m.solvable_order()
        self.assertEqual(len(self.order), len(order2))
        for k1, v1 in self.order.items():
            self.assertEqual(v1, order2[k1])
        del self.order

        # Test with cycles
        self.m.get('ina.j').demote()
        self.assertRaisesRegex(
            myokit.IntegrityError, 'ina.j > ina.j.', self.m.solvable_order)

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
            if isinstance(lhs1, str):
                if lhs1.startswith('dot('):
                    lhs1 = myokit.Derivative(myokit.Name(
                        self.m.get(lhs1[4:-1])))
                else:
                    lhs1 = myokit.Name(self.m.get(lhs1))
            for lhs2 in lhs2s:
                if isinstance(lhs2, str):
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
        self.eqs, self.vrs = self.m.expressions_for('ix1.x1')
        self.assertEqual(len(self.eqs), 5)
        self.assertEqual(len(self.vrs), 2)
        self.assertIn(myokit.Name(self.m.get('ix1.x1')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('membrane.V')), self.vrs)
        before('dot(ix1.x1)', 'ix1.x1.tau', 'ix1.x1.inf')
        before('ix1.x1.inf', 'ix1.x1.alpha', 'ix1.x1.tau')
        before('ix1.x1.tau', 'ix1.x1.alpha', 'ix1.x1.beta')
        del self.eqs, self.vrs

        # Larger test (and try with LhsExpression instead of string)
        self.eqs, self.vrs = self.m.expressions_for(
            self.m.get('membrane.V').lhs())
        self.assertEqual(len(self.vrs), 10)
        self.assertIn(myokit.Name(self.m.get('engine.pace')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('membrane.i_diff')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('membrane.V')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ix1.x1')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.m')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.h')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.j')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('is.d')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('is.f')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('calcium.Cai')), self.vrs)
        self.assertEqual(len(self.eqs), 17)
        before('dot(membrane.V)', 'membrane.C', 'membrane.i_ion',
               'stimulus.i_stim')
        before('membrane.i_ion', 'ik1.IK1', 'ix1.Ix1', 'ina.INa', 'is.Is')
        before('stimulus.i_stim', 'stimulus.amplitude')
        before('ina.INa', 'ina.gNaBar', 'ina.gNaC', 'ina.ENa')
        before('is.Is', 'is.Is.g', 'is.Es')
        before('is.Is.g', 'is.gsBar', 'is.Is.gates')
        before('is.Es', 'cell.Ca_ref')
        del self.eqs, self.vrs

        # Multiple variables, including nested ones
        self.eqs, self.vrs = self.m.expressions_for('ina.m', 'ina.j')
        self.assertEqual(len(self.eqs), 10)
        self.assertEqual(len(self.vrs), 3)
        self.assertIn(myokit.Name(self.m.get('membrane.V')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.m')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('ina.j')), self.vrs)
        before('dot(ina.m)', 'ina.m.alpha', 'ina.m.beta')
        before('dot(ina.j)', 'ina.j.alpha', 'ina.j.beta')
        before('ina.j.beta', 'ina.j.va')
        before('ina.j.va', 'ina.j.va.vb', 'ina.j.va.vc')
        before('ina.j.va.vb', 'ina.j.va.vc')
        before('ina.j.va.vc', 'ina.j.va.vc.vd')
        del self.eqs, self.vrs

        # Variables that depend on dot() expressions
        self.eqs, self.vrs = self.m.expressions_for('test.t1', 'test.t2')
        self.assertEqual(len(self.eqs), 17 + 3)
        before('dot(test.t2)', 'test.inter')
        before('test.inter', 'dot(test.t1)')
        before('dot(test.t1)', 'dot(membrane.V)')
        del self.eqs, self.vrs

        # Variable that depends on a dot() expression in another component
        self.eqs, self.vrs = self.m.expressions_for('test.dx1')
        self.assertEqual(len(self.eqs), 6)
        self.assertEqual(len(self.vrs), 2)
        self.assertIn(myokit.Name(self.m.get('ix1.x1')), self.vrs)
        self.assertIn(myokit.Name(self.m.get('membrane.V')), self.vrs)
        before('test.dx1', 'dot(ix1.x1)')
        before('dot(ix1.x1)', 'ix1.x1.tau', 'ix1.x1.inf')
        del self.eqs, self.vrs

        # Unsolvable system
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        x.set_rhs('y')
        y.set_rhs('x')
        c.add_variable('t', rhs=0, binding='time')
        self.assertRaisesRegex(
            myokit.IntegrityError, 'c.x > c.y > c.x', m.expressions_for, 'c.x')

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
