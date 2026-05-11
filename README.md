# prism-theory

**© 2026 Max Conrad. All rights reserved.**

## what is this

a research project testing whether a passive material structure (like a crystal or metamaterial) can take in a composite light signal carrying data and decompose it into meaningful components that produce a computational result — no electronics, no binary, no voltage thresholds. just light and physics.

## the hypothesis

light goes in carrying data. the structure does the math. correct answer comes out as light.

more specifically: a passive photonic structure can decompose a composite optical signal into distinct components that encode meaningful data, and the interaction of those components can produce a predictable computational result — all without electronic conversion.

## test 01 — decomposition

the simplest possible starting point. send two wavelengths of light into a simulated structure as one beam. do they come out separated on the other side?

if we can't split light cleanly in simulation, nothing else matters. if we can, we've proven the "prism" works and we'll know enough to figure out what's next.

**tool:** MEEP (MIT Electromagnetic Equation Propagation) — an open source FDTD simulation engine for modeling how light interacts with structures.

## setup

```bash
# WSL/Linux
conda create -n prism python=3.10
conda activate prism
conda install -c conda-forge pymeep
pip install matplotlib h5py numpy
```

## session log

**2026-05-10** — started from a conversation about why computers use binary and whether there's something fundamentally better. explored ternary computing, DNA computing, photonic computing. landed on the idea of data traveling as a unified light signal and being decomposed by a passive structure — like a prism splitting white light. set up the repo. installed MEEP on WSL via miniconda. wrote and ran test 01.

first run used a fixed refractive index (n=1.5 for all wavelengths). both wavelengths bent the same amount and landed in the same spot. result: inconclusive. this makes sense — if the material treats all colors the same, there's nothing to separate.

second run added a dispersive material model (Lorentzian susceptibility) so the refractive index changes with wavelength, like real glass. result: PASS. separation ratios were 2.81 for 0.8μm vs 2.27 for 1.2μm — different enough to confirm the mechanism works.

what the graph shows: both wavelengths are still mostly going to the same detector (upper), just at different intensities. the prism is bending light and dispersion is real, but the angular separation is too small with this geometry. it's like a prism that works but the rainbow is too narrow to read. next step is tuning the prism angle and detector positions to get cleaner separation.