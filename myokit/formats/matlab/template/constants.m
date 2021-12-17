<?
#
# constants.m :: Contains the model constants / parameters
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
?>%
% Constants for <?= model.name() ?>
%
function c = constants()
<?
for label, eq_list in equations.items():
    print('')
    print('% ' + label)
    for eq in eq_list.equations(const=True):
        var = eq.lhs.var()
        if 'desc' in var.meta:
            print('% ' + '% '.join(str(var.meta['desc']).splitlines()))
        print(e(eq) + ';')
?>
end
