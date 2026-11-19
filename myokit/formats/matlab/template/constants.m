<?
#
# constants.m :: Contains the model constants / parameters
#
# This file is part of Myokit.
# See https://github.com/myokit/myokit for copyright, sharing, and licensing.
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
