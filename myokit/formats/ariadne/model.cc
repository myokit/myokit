<?
#
# Ariadne export of myokit model definition
#
# This file is part of Myokit
#  Copyright 2011-2014 Michael Clerx, Maastricht University
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
tab = ' '*4
tab2 = tab*2
?>
#include "ariadne.h"

#include "hybrid_automaton-composite.h"
/*
#include "hybrid_set.h"
#include "hybrid_evolver.h"
#include "hybrid_simulator.h"
#include "hybrid_graphics.h"
*/

using namespace Ariadne;

CompositeHybridAutomaton create_system()
{
    // Constants
    // ---------
<?
# Define all constants here
for label, eq_list in equations.iteritems():
    first = True
    for eq in eq_list.equations(const=True):
        if first:
            print(tab + '')
            print(tab + '// Component: ' + label)
            first = False
        var = eq.lhs.var()
        if 'desc' in var.meta:
            pre = tab + '// '
            print(pre + pre.join(str(var.meta['desc']).splitlines()))
        print(tab + 'RealConstant ' + v(var) + '("' + var.qname() + '", ' + e.ex(eq.rhs) + ');')
?>

    // Variables
    // ----------------------
<?
# List all intermediary variables here
n = 0
for label, eq_list in equations.iteritems():
    first = True
    for eq in eq_list.equations(const=False):
        if first:
            print(tab + '')
            print(tab + '// Component: ' + label)
            first = False
        var = eq.lhs.var()
        if 'desc' in var.meta:
            pre = tab + '// '
            print(pre + pre.join(str(var.meta['desc']).splitlines()))
        print(tab + 'RealVariable ' + v(var) + '("' + var.qname() + '");')
        n += 1
?>

    // Create the unpaced system
    // -------------------------
    HybridAutomaton model;
    // Look it up!
    model.new_mode( ???heating|on, (
<?

# List all equations here
m = 0
for eq_list in equations.itervalues():
    for eq in eq_list.equations(const=False):
        m += 1
        post = ',' if m < n else ''
        print(tab2 + e.eq(eq) + post)
?>
        ));

    // Create pacing
    // -------------
    DiscreteEvent pulse_hi("pulse_hi");
    DiscreteEvent pulse_lo("pulse_lo");
    HybridAutomaton pacing;
<?

# Instead of implementing the full pacing system, create a simple repeating block wave.
# pacing.new_mode( (dot(C)=1.0) );
# pacing.new_transition( midnight, next(C)=0.0, C>=1.0, urgent );

?>

    // Create the composite system
    // ---------------------------
    CompositeHybridAutomaton system((pacing,model));
    //std::cout << "system=" << system << "\n" << "\n";

    return system;
}


int main(int argc, const char* argv[])
{
    // Create the system
    CompositeHybridAutomaton system=create_system();
    std::cerr<<system<<"\n";

    /*
    // Create the analyser classes
    HybridEvolverType evolver=create_evolver(heating_system);
    std::cerr<<evolver<<"\n";

    // Compute the system evolution
    compute_evolution(heating_system,evolver);
    //compute_reachable_sets(evolver);
    */
}
