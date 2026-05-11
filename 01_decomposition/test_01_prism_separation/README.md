# test 01 — prism separation

can a dispersive structure separate two wavelengths (0.8μm and 1.2μm) that enter as one beam?

**result: PASS (v3)**

## versions

- **v1** — fixed refractive index, no dispersion. INCONCLUSIVE. both wavelengths bend identically.
- **v2** — added Lorentzian dispersion (sigma=1.2), steeper triangle. FAIL. ratios differ but both peak at same detector.
- **v3** — wedge prism, stronger dispersion (sigma=3.0), 5 detectors. PASS. 0.8μm peaks at y=0, 1.2μm peaks at y=-4.