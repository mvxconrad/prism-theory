# 01_decomposition — session notes

## 2026-05-10

### how we got here

started asking why computers use binary. realized it's not because base 2 is optimal, it's because transistors only have two reliable states. every abstraction layer we've built since exists because the foundation isn't expressive enough. what if information never had to stop being information? landed on light as a data carrier, passive structures as interpreters.

### test 01 — prism separation

can a structure separate two wavelengths entering as one beam?

**v1 — fixed index.** INCONCLUSIVE. no dispersion = no separation.

**v2 — steep prism, dispersion (sigma=1.2).** FAIL. ratios differ but both peak at same detector.

**v3 — wedge prism, stronger dispersion (sigma=3.0).** PASS. 0.8μm peaks at y=0, 1.2μm peaks at y=-4. separation is in the ratios not clean isolation.

### test 02 — consistency

are the separation ratios constant across different conditions?

**v1 — varying amplitude.** PASS but meaningless. MEEP is deterministic so identical physics = identical output. same as solving 2+2 ten times.

**v2 — with noise (laser jitter ±5%, temp drift ±2%, alignment ±0.1μm).** PASS. worst variation 2.65%, best 0.88%. the ratios hold up under realistic physical noise.

### test 03 — encoding

can we encode data as amplitudes on two wavelengths and decode it from detector readings?

**v1 — calibration.** 7/8 messages decoded within 0.1 error. avg max error 0.039. the one miss was (0.5, 4.0) → decoded as (0.307, 4.019). when one wavelength is very weak and the other is very strong, the strong signal drowns out the weak one. basically: encoding works but keep signal ratios balanced.

**v2 — with noise.** PARTIAL. avg max error 0.1137. balanced signals like (1.0, 1.0) and (2.0, 1.0) decode cleanly even with noise. single-wavelength messages like (1.0, 0.0) and extreme ratios like (0.5, 4.0) are fragile. not a physics limitation, it's a design constraint we can work around.

### test 04 — resolution

how small of an amplitude difference can the system distinguish under noise?

**v1 — step size test.** smallest separable step: 0.05. on a usable range of 1.0 to 4.0, that gives us 60 distinguishable levels per wavelength. two wavelengths = 60 x 60 = 3,600 states per pulse. for context, one binary switch gives you 2 states per cycle. basically: each pulse of light through this system carries as much information as ~12 binary switches flipping at once. the limit is noise at small deltas. 0.05 apart is readable, 0.03 is not.