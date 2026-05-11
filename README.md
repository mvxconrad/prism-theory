# prism-theory

**© 2026 Max Conrad. All rights reserved.**

## what is this

a research project testing whether a passive material structure (like a crystal or metamaterial) can take in a composite light signal carrying data and decompose it into meaningful components that produce a computational result. no electronics, no binary, no voltage thresholds. just light and physics.

## the hypothesis

light goes in carrying data. the structure does the math. correct answer comes out as light.

more specifically: a passive photonic structure can decompose a composite optical signal into distinct components that encode meaningful data, and the interaction of those components can produce a predictable computational result, all without electronic conversion.

## what we need to prove

for this to be worth building over binary, we need to answer five questions:

| question | what it means | status |
|----------|--------------|--------|
| resolution | how many distinguishable levels per channel? more levels = more data per pulse | 60 levels per wavelength, 3600 states per pulse |
| speed | how many operations per second? needs to compete with GHz clock speeds | not started |
| error rate | how often does decoding fail? binary gets ~1 in a billion | partially tested |
| energy | photons vs electrons per operation. optics should win here | not started |
| scalability | can the output of one structure feed into another? if yes, you can build logic. if no, it's a sensor not a computer | not started |

the total package (density x speed x reliability) needs to beat transistors at something useful enough to justify new hardware.

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
- 60 levels x 2 wavelengths = 3,600 distinguishable states per pulse. one binary switch gives 2 states per cycle.

[session notes](01_decomposition/session_notes.md)

## setup

```bash
conda create -n prism python=3.10 -y
conda activate prism
conda install -c conda-forge pymeep -y
pip install matplotlib h5py numpy
```

## tool

[MEEP](https://meep.readthedocs.io/) (MIT Electromagnetic Equation Propagation) — open source FDTD simulation engine for modeling how light interacts with structures.