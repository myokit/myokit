<?
#
# sim.c
# A pype template for a C++ simulation on FPGAs
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
?>#include "model.hpp"
#include <cmath>	// comment when import in VITIS
// #include "hls_math.h"	// Uncomment when import in VITIS

<?= signature ?>
{
<?
tab = '    '

# Constants and calculated constants
for group in equations.values():
    for eq in group.equations(const=True):
        if eq.lhs.var() not in parameters:
            print(f'{tab}float {e.eq(eq)};')
print()

# All intermediaries
for group in equations.values():
    for eq in group.equations(inter=True):
        print(f'{tab}float {e.eq(eq)};')
print()

# Derivatives
for group in equations.values():
    for eq in group.equations(state=True):
        if eq.lhs.var() not in rl_states:
            print(f'{tab}float {e.eq(eq)};')

# State updates
for var in model.states():
    i = var.index()
    if var in rl_states:
        inf, tau = rl_states[var]
        inf, tau, var = v(inf), v(tau), v(var)
        exp = 'expf'  # Only support single for now
        print(f'{tab}*SV_{i} = {inf} + ({var} - {inf}) * expf(-dt / {tau});')
    else:
        print(f'{tab}*SV_{i} = Y_{i} + dY_{i} * dt;')

?>
	return 0;
}
