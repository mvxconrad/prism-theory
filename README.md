# prism-theory

**© 2026 Max Conrad. All rights reserved.**

## what is this

a research project testing whether a passive material structure (like a crystal or metamaterial) can take in a composite light signal carrying data and decompose it into meaningful components that produce a computational result. no electronics, no binary, no voltage thresholds. just light and physics.

## the hypothesis

light goes in carrying data. the structure does the math. correct answer comes out as light.

more specifically: a passive photonic structure can decompose a composite optical signal into distinct components that encode meaningful data, and the interaction of those components can produce a predictable computational result, all without electronic conversion.

## key concepts

how our system works, defined by what we've tested so far.

| concept | definition |
|---------|-----------|
| channels | each wavelength of light is a channel. we currently use 2 (0.8μm and 1.2μm) |
| levels | each channel carries a brightness (amplitude) value. the system can distinguish 70 brightness levels per channel |
| zero | amplitude 0.5. we never turn a channel fully off. the decoder subtracts 0.5 to get the real value |
| usable range | 0.5 to 4.0 amplitude per channel |
| minimum step | 0.05. the smallest brightness difference the system can tell apart under noise |
| states per pulse | 70 x 70 = 4,900 distinguishable combinations across 2 channels. binary gets 2 per switch |
| balanced signals | both channels at similar brightness. this is where the system is most accurate (<2% error) |
| drowning out | when one channel is much brighter than the other, the dim one gets lost in noise. design constraint: keep channels balanced |

## what we need to prove

| question | what it means | status |
|----------|--------------|--------|
| resolution | how many distinguishable levels per channel? | 70 levels/wavelength, 4,900 states/pulse |
| speed | how many operations per second? | not started |
| error rate | how often does decoding fail? | under 2% for balanced signals, ~21% for single-channel |
| energy | photons vs electrons per operation | not started |
| scalability | can operations chain together? | not started |

## experiments

### [01 — decomposition](01_decomposition/)

can a structure separate wavelengths, do it consistently, encode data on them, and how precisely?

| test | question | result |
|------|----------|--------|
| [01 prism separation](01_decomposition/test_01_prism_separation/) | can it split two wavelengths? | PASS (v3) |
| [02 consistency](01_decomposition/test_02_consistency/) | are the ratios stable under noise? | PASS (v2, <3% variation) |
| [03 encoding](01_decomposition/test_03_encoding/) | can we encode and decode data? | PARTIAL (balanced signals work, extreme ratios fragile) |
| [04 resolution](01_decomposition/test_04_resolution/) | how fine-grained can encoding be? | 60 levels/wavelength, 3600 states/pulse, min step 0.05 |

#### key findings

- a wedge prism with dispersive glass separates two wavelengths to different spatial positions. the separation shows up as consistent ratios at each detector, not clean isolation.
- those ratios hold under realistic noise (laser jitter, temperature drift, alignment error) with less than 3% variation.
- data can be encoded as amplitude levels on each wavelength and decoded from detector readings using a calibration matrix. balanced signals decode cleanly. extreme ratios (one wavelength near zero) are fragile because the strong signal drowns out the weak one.
- the system can distinguish amplitude differences as small as 0.05 on a 1.0 to 4.0 range, giving 60 usable levels per wavelength. below 0.05, noise becomes larger than the gap between levels. think of it like blurry vision: two people 10 feet apart are easy to tell apart even with blur, but two people 1 inch apart blur into one. the noise didn't change, the distance did.

[session notes](01_decomposition/session_notes.md)

### [02 — computation](02_computation/)

can a structure perform math on light without electronics?

| test | question | result |
|------|----------|--------|
| [01 addition](02_computation/test_01_addition/) | can two beams add together? | PASS (v2, <5% error when both inputs nonzero) |
| [02 zero floor](02_computation/test_02_zero_floor/) | what's the lowest amplitude that represents zero? | 0.5 (70 levels/wavelength, 4900 states/pulse) |

#### key findings

- a symmetric Y-junction waveguide adds two light signals. output scales with (A+B)² predictably. error under 2% for most input pairs. we're not changing how light works, we're shaping the container so physics can do what it already does.
- the system can't read a signal at amplitude zero. solution: use 0.5 as the baseline "zero." always keep both channels on. usable range becomes 0.5 to 4.0.
- the drowning-out problem: when one signal is much stronger than the other, the weak one gets lost in noise. design constraint: keep signal ratios balanced.

[session notes](02_computation/session_notes.md)

## setup

```bash
conda create -n prism python=3.10 -y
conda activate prism
conda install -c conda-forge pymeep -y
pip install matplotlib h5py numpy
```

## tool

[MEEP](https://meep.readthedocs.io/) (MIT Electromagnetic Equation Propagation) — open source FDTD simulation engine for modeling how light interacts with structures.