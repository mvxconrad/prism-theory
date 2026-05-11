# prism-theory

**© 2026 Max Conrad. All rights reserved.**

## what is this

a research project testing whether a passive material structure (like a crystal or metamaterial) can take in a composite light signal carrying data and decompose it into meaningful components that produce a computational result. no electronics, no binary, no voltage thresholds. just light and physics.

## the hypothesis

light goes in carrying data. the structure does the math. correct answer comes out as light.

more specifically: a passive photonic structure can decompose a composite optical signal into distinct components that encode meaningful data, and the interaction of those components can produce a predictable computational result, all without electronic conversion.

## why this matters

every computer built since the 1940s works the same way: electricity flips tiny switches on and off. each switch is one bit. on or off. two states. we've spent 80 years making the switches smaller and faster, but the foundation hasn't changed.

this project asks: what if instead of flipping one switch at a time, you send a beam of light through a piece of shaped glass and that single pulse carries thousands of distinguishable values? not on or off, but many shades of brightness across multiple colors of light, all at once, at the speed of light.

we built simulations, ran tests, and measured the results. a single pulse through our system carries 4,900 distinguishable states. one binary switch carries 2. we asked the system to solve 10 addition problems and it got all 10 right with an average error of 0.019. the data survived passing through multiple physical structures in sequence. no electrons, no transistors, no software in the loop.

we're not claiming this replaces transistors tomorrow. we're showing that the physics works, the math checks out, and the concept is worth investigating further with real hardware.

## key concepts

| concept | definition |
|---------|-----------|
| channels | each wavelength of light is a channel. we use 2 (0.8μm and 1.2μm) |
| levels | each channel carries a brightness (amplitude) value. the system distinguishes 70 levels per channel |
| zero | amplitude 0.5. we never turn a channel fully off. the decoder subtracts 0.5 to get the real value |
| usable range | 0.5 to 4.0 amplitude per channel |
| minimum step | 0.05. smallest brightness difference the system can tell apart under noise |
| states per pulse | 70 x 70 = 4,900 distinguishable combinations across 2 channels |
| balanced signals | both channels at similar brightness. most accurate (<2% error) |
| drowning out | when one channel is much brighter than the other, the dim one gets lost. design constraint: keep channels reasonably balanced |

## what we need to prove

| question | what it means | status |
|----------|--------------|--------|
| resolution | how many distinguishable levels per channel? | 70 levels/wavelength, 4,900 states/pulse |
| speed | how many operations per second? | not started |
| error rate | how often does decoding fail? | avg 0.019 error on addition, <3% variation under noise |
| energy | photons vs electrons per operation | not started |
| scalability | can operations chain together? | PASS, 10/10 math problems solved through full chain |

## experiments

### [01 — decomposition](01_decomposition/)

can a structure separate wavelengths, do it consistently, encode data on them, and how precisely?

| test | question | result |
|------|----------|--------|
| [01 prism separation](01_decomposition/test_01_prism_separation/) | can it split two wavelengths? | PASS |
| [02 consistency](01_decomposition/test_02_consistency/) | are the ratios stable under noise? | PASS (<3% variation) |
| [03 encoding](01_decomposition/test_03_encoding/) | can we encode and decode data? | PARTIAL (balanced works, extreme ratios fragile) |
| [04 resolution](01_decomposition/test_04_resolution/) | how fine-grained can encoding be? | 60 levels/wavelength, min step 0.05 |

#### key findings

- a wedge prism with dispersive glass separates 0.8μm and 1.2μm wavelengths to different detector positions. separation shows up as consistent ratios at each detector, not clean isolation.
- ratios hold under realistic noise (laser jitter ±5%, temperature drift ±2%, alignment error ±0.1μm) with less than 3% variation across 20 noisy runs.
- data encoded as amplitude levels decodes cleanly when balanced. the (0.5, 4.0) pair was the main failure point because the strong signal drowns out the weak one. not a physics problem, a design constraint.
- smallest distinguishable amplitude step is 0.05 on a 1.0-4.0 range. below that, noise is larger than the gap between levels.

[session notes](01_decomposition/session_notes.md)

### [02 — computation](02_computation/)

can a structure perform math on light without electronics?

| test | question | result |
|------|----------|--------|
| [01 addition](02_computation/test_01_addition/) | can two beams add together? | PASS (<2% error balanced, <5% all nonzero pairs) |
| [02 zero floor](02_computation/test_02_zero_floor/) | lowest amplitude that represents zero? | 0.5 (70 levels/wavelength, 4,900 states/pulse) |

#### key findings

- a symmetric Y-junction waveguide adds two light signals. output power scales with (A+B)² predictably. error under 2% for most pairs. the v1 asymmetric junction failed because the structure was lopsided, not because the physics was wrong. fixing the geometry fixed the math.
- single-channel inputs (one wavelength at zero) fail at ~21% error. solution: use 0.5 as the baseline "zero" so both channels are always on. the decoder subtracts 0.5 from readings.
- tested baselines from 0.5 down to 0.05. only 0.5 is viable. everything below has errors larger than half the baseline value. usable range: 0.5 to 4.0.

[session notes](02_computation/session_notes.md)

### [03 — scalability](03_scalability/)

can operations chain together? can glass actually solve math problems?

| test | question | result |
|------|----------|--------|
| [01 chain](03_scalability/test_01_chain/) | does data survive two structures in series? | PASS (<1% error) |
| | does zero floor work in a chain? | PASS (worst error 0.043) |
| [02 full roundtrip](03_scalability/test_02_full_roundtrip/) | can glass solve addition problems? | PASS (10/10, avg error 0.019) |

#### key findings

- light passes through Y-junction then prism and data comes out intact. wavelengths merge, travel, hit the prism, separate back to different detectors. output scales with input at under 1% error.
- zero floor (0.5) survives the full chain. all 7 zero-floor pairs decoded with less than 0.05 error.
- full roundtrip test: 10 addition problems, 10 correct answers. 9 A grades (<0.05 error), 1 B grade (<0.1 error). the glass said 2+3=4.972, 0+0=-0.003, 2+2=3.986. average error 0.019. no transistors involved.

[session notes](03_scalability/session_notes.md)

## setup

```bash
conda create -n prism python=3.10 -y
conda activate prism
conda install -c conda-forge pymeep -y
pip install matplotlib h5py numpy
```

## tool

[MEEP](https://meep.readthedocs.io/) (MIT Electromagnetic Equation Propagation) — open source FDTD simulation engine for modeling how light interacts with structures.