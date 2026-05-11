# 01_decomposition — session notes

## 2026-05-10

### how we got here

started asking why computers use binary. realized it's not because base 2 is optimal — it's because transistors only have two reliable states. every abstraction layer we've built since exists because the foundation isn't expressive enough. what if information never had to stop being information? landed on light as a data carrier, passive structures as interpreters.

### test 01 results

**v1 — basic prism, fixed index.** INCONCLUSIVE. no dispersion = no separation. simulation works though.

**v2 — steep prism, dispersive material (sigma=1.2).** FAIL. both wavelengths still peak at center. ratios differ (2.81 vs 2.27) so dispersion is working, just not enough angular spread.

**v3 — wedge prism, stronger dispersion (sigma=3.0).** PASS. 0.8μm peaks at y=0, 1.2μm peaks at y=-4. separation is real but messy — overlap at every detector, difference is in the ratios not clean isolation.

### what the graph shows

both wavelengths show up everywhere but at different intensities. at y=-4 the 1.2μm signal is ~2.3x stronger than 0.8μm. at y=0 they're nearly equal. this ratio difference is the usable signal.

### next

separation doesn't need to be perfect if it's consistent. plan: vary input amplitudes across multiple runs and check if the ratios at each detector stay constant. if they do, we can calibrate for it and read data reliably.