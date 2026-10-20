<?
#
# ifthenelse.m :: Handles piecewise constructs in expressions
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
?>% Emulate the ternary operator x = (cond) ? iftrue : iffalse
function y = ifthenelse(cond, iftrue, iffalse)
    if (cond)
        y = iftrue;
    else
        y = iffalse;
    end
end
