<?
#
# model_wrapper.m :: Creates a wrapper around the model function so that it can
# be used in matlab/octave style ode solvers.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
?>% Function wrapper
function ydot = model_wrapper(t, y, c)
    if (mod(t - c.stim_offset, c.pcl) < c.stim_duration)
        pace = 1;
    else
        pace = 0;
    end
    ydot = model(t, y, c, pace);
end
