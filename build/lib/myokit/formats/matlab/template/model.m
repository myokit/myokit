<?
#
# model.m :: This will become the model definition file
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit

?>function ydot = model(t, y, c, pace)

% Create derivatives vector
ydot = zeros(size(y,1), size(y,2));

% Get state variables from vector
<?
i = 0
for var in model.states():
    i += 1
    print(v(var) + ' = y(' + str(i) + ');')

for label, eq_list in equations.items():
    print('%')
    print('% ' + label)
    print('%')
    for eq in eq_list.equations(const=False):
        var = eq.lhs.var()
        if 'desc' in var.meta:
            print('% ' + '% '.join(str(var.meta['desc']).splitlines()))
        if var.is_bound():
            print(v(var) + ' = ' + bound_variables[var] + ';')
        else:
            print(e(eq) + ';')
?>
end
