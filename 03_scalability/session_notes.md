# 03_scalability — session notes

## 2026-05-10

### test 01 — chain (addition then decomposition)

**v1 — strong signals.** PASS. two wavelengths enter Y-junction from separate arms, merge, travel through waveguide, hit prism, separate back to different detectors. λ1 peaks at y=-6, λ2 peaks at y=+6. output scales with input squared at under 1% error across all 8 test pairs. worst error 0.9%. operations chain.

**v2 — zero floor.** PASS. tested 9 pairs including (0.5, 0.5), (0.5, 3.0), (3.0, 0.5) and balanced references. every pair decoded with less than 0.05 absolute error. worst was (0.5, 3.0) at 0.043 error. zero floor survives two structures in series.

### test 02 — full roundtrip

**v1 — can glass do math?** PASS. 10 addition problems encoded as light, computed through shaped glass, decoded back to numbers.

results:
- 1+1: glass says 1.992 (error 0.008) — A
- 2+3: glass says 4.972 (error 0.028) — A
- 1+4: glass says 4.949 (error 0.051) — B
- 3+2: glass says 4.995 (error 0.005) — A
- 0+2: glass says 1.968 (error 0.032) — A
- 2+0: glass says 2.013 (error 0.013) — A
- 0+0: glass says -0.003 (error 0.003) — A
- 1.5+2.5: glass says 3.975 (error 0.025) — A
- 0.5+1: glass says 1.487 (error 0.013) — A
- 2+2: glass says 3.986 (error 0.014) — A

9/10 A grades, 1 B grade, 10/10 within 0.1 error. average error 0.019. no transistors, no binary, no software in the computation loop. light in, correct answer out.