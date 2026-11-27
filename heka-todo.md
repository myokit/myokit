# ABF To-do




## Main file

- Current, voltage, protocol
- CSV export of all, E-number in filename
- E-Number, Screenshot of protocol editor, or manually note down
- E-Number, Screenshot of all relevant settings, or manually note down

### Things to write down

- File: version, _time
- PulsedFile: version(), time()
- Group: completeness, label, number
- Series: channel names and units, label, sweep count, time
- Sweep: duration, label, time
- Trace: c_slow, count_samples, label, c_slow, r_seal, r_series, r_pipette, data unit
- Amplifier state:
  - c_fast, c_fast_detailed
  - c_slow, c_slow_auto_settings, 
  - current_gain
  - ljp, v_off
  - r_series, r_series_fraction, r_series_tau
  - v_hold
  - CC:
    - i_hold
  - Enums
    - CC: current_clamp_stimulus_gain (0.1, 1, 10, 100)
    - filter1() (bessel100, bessel30, bessel10, hq30k)
    - filter2() (type: bessel, butterworth, bypass)
    - c_slow_range (off, 30, 100, 100)
    - stimulus_filter (2, 20)
- StimulusFile: version
- Stimulus: label, sampling_interval, sweep_count, sweep_durations, sweep_interal, sweep_samples
- StimulusChannel
  - AmplifierMode (any, VC, CC)
  - protocol!
  - sweep_durations, sweep_samples, zero_segment, unit
- Segment:
    - duration: base, delta, factor, increment_mode, calculate durations
    - SegmentClass: Constant, Ramp, Continuous, ConstSine, Squarewave, Chirpwave
    - SegmentStorage: NotStored, Stored
    - SegmentIncrease: 0--9 !
    - value: base, delta, factor, increment_mode, calculated values
- AmplifierFile: name, version

### To-do

- Set up a short and simple stimulus, with steps
  - Run with: 
    - Rs comp off, Filter1 b100, Filter2 bypass,  Cslow range off, lowest gain
    - Rs comp 100us, Filter1 b10, Filter2 bessel, Cslow range 30, higher gain
      - Changed C slow auto settings
      - Change Vhold
      - Change LJP and offset
    - Rs comp 10us, Filter1 b10, Filter2 butterworth, Cslow range 100, gain up again
      - C slow auto settings back to normal
    - Rs comp 5us, Filter1 b30, Filter2 bypass, stim filter on, Cslow range 1000, gain up again
    - Rs comp 2us, Filter1 hq30k, Filter2 bypass, stim filter off, Cslow range 1000, gain up again
- Set up a short and simple CC experiment
- Set up a few crazy stimuli
  - duration increase
  - value increase in funny modes

### Things to include

- An incomplete series
- A series without channels (how?)
- Single vs multiple amplifier states
- Unequal sweep durations



## Things to investigate, MAYBE



- A "interleave" increase AND decrease, from 1 to 7 steps (manual gives length 6 examples which can be interpreted in different ways...)
- An example where not all segments are recorded. 
- Maybe even a duration-changing segment that isn't recorded?
- An example with a stimulus file
- An example with a ramp
- An example with a sine

