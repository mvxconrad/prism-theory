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

**2026-05-10** — started from a conversation about why computers use binary and whether there's something fundamentally better. explored ternary computing, DNA computing, photonic computing. landed on the idea of data traveling as a unified light signal and being decomposed by a passive structure — like a prism splitting white light. set up the repo. next step: write the first MEEP simulation for test 01.
