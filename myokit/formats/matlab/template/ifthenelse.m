<?
#
# ifthenelse.m :: Handles piecewise constructs in expressions
#
# This file is part of Myokit.
# See https://github.com/myokit/myokit for copyright, sharing, and licensing.
#
?>% Emulate the ternary operator x = (cond) ? iftrue : iffalse
function y = ifthenelse(cond, iftrue, iffalse)
    if (cond)
        y = iftrue;
    else
        y = iffalse;
    end
end
