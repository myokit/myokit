# ABF To-do

## Minimal effort version

- Open Myokit test files in Axon
- Check the meta data in the header
- Export the data as CSV



## Contents of the file

- AD channels: current and voltage
- DA: protocol


### Meta data to note down

- Version
- Date and Time
- Acquisition mode
- Number of trials, runs, sweeps
- Sampling rate
- Channel names and units
- Filtering session
- Telegraphed Cm

Example:
```
Axon Binary File: abf-v2.abf
ABF Format version 2.0.0.0
Recorded on: 2016-01-07 10:51:55.345000
Acquisition mode: 5: Episodic stimulation mode
Protocol set for 1 trials, spaced 0.0s apart.
    with 1 runs per trial, spaced 0.0s apart.
     and 37 sweeps per run, spaced 5.0s apart.
Sampling rate: 20000.0 Hz
A/D Channel 0: "IN 0"
  Unit: [pA]
  Low-pass filter: 10000.0 Hz
  Cm (telegraphed): 11.083984375 pF
D/A Channel 0: "Cmd 0"
  Unit: [mV]
```

### Take photo of protocol

Or note down

### Export data to CSV

From axon software


## Secondary files

- Protocol with ramps (see also `_read_6_da_reconstructions`)
- Mess with gain (InstrumentScaleFactor, ADCProgrammableGain, lADCResolution, fADCRange, fTelegraphAdditGain)
- Empty file (no channels)
- Empty file (no channels or protocol)
- Incomplete file (not all sweeps ran)
- Length zero step in protocol (and length zero ramp)
- Rs in file (how?)
- CC mode





## Things to investigate, MAYBE

### Acquisition modes

Gap free
Rest require triggers

### Epoch types

Pulse train
Biphasic train
Triangle train
Cosine train

Minimum effort version: Record a file with one of these, check for "not supported" warning.

### User lists


### Membrane tests between sweeps

> The Membrane Test Between Sweeps check box enables a Membrane Test to be run
> automatically between every sweep. In this mode the Membrane Test data are written out to
> the Online Statistics window and displayed in the Real Time Controls.


### Sweeps of different lengths

`self._equal_length_sweeps = True` always, atm

