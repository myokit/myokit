.. _syntax/protocol:

**********************
Pacing protocol syntax
**********************

In Myokit, pacing is not part of a model but is defined using a separate
pacing syntax. To introduce a pacing current in the model, a variable must be
bound to the external input ``pace``.
The most common use of this mechanism is to specify a stimulus current
``I_stim = amplitude * level`` where
``amplitude`` is a constant stimulus amplitude and ``level`` is the
dimensionless variable bound to the input ``pace``::

    [stimulus]
    amplitude = 60 [uA/cm^2]
    level = 0 bind pace
    current = level * amplitude

Structure
=========
A pacing protocol definition starts with the segment header ``protocol``. Each
successive line defines a pacing event, I.E. a time when the stimulus is
non-zero. The following five parameters must set (separated by any amount of
whitespace):

1. The value of the stimulus variable
2. The time at which this stimulus occurs
3. The duration of this stimulus
4. For periodic stimuli, the fourth column specifies the stimulus period.
   Non-periodic stimuli can be created by entering "0" here.
5. The number of times a periodic stimulus is given can be specified in the
   final column, stimuli that are non-periodic or recur indefinetely can use
   the value "0" here.

Comments may be added by starting lines with ``#``.

When specifying the time an event starts, the keyword "next" may be used to
denote the time at which the previous event ends. This can only be used at the
very start of a protocol or directly after a non-periodic event.

Examples
========
A typical example for 0.5ms stimuli occurring every 1000ms (at 1bpm) is::

    [[protocol]]
    #level  start   length  period  multiplier
    1.0     10      0.5     1000    0

Here, a stimulus of level "1.0" is applied from t=10ms till t=12ms and then
again from t=1010ms to t=1012ms continuing indefinitely.

In the following example the stimulus only occurs 3 times::

    [[protocol]]
    #level  start   length  period  multiplier
    1.0     10      0.5     1000    3

An example for a voltage clamp experiment::

    [[protocol]]
    #level  start   length  period  multiplier
    -80     0       500     0       0
     40     500     500     0       0
    -80     1000    1000    1000    0

In this example, the pacing level is taken to denote a voltage. At t=0 the
voltage is set to -80mV. After 500ms, it changes abrubtly to +40, where it
stays for another 500ms. Finally, at t=1000ms it drops down to -80mV again
where it stays indefinitely.

This example can be written using the "next" keyword::

    [[protocol]]
    #level  start   length  period  multiplier
    -80     0       500     0       0
     40     next    500     0       0
    -80     next    1000    1000    0

