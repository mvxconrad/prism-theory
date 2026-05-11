# 02_computation — session notes

## 2026-05-10

### how we got here

decomposition experiments proved we can separate wavelengths, encode data on them, and distinguish 60-70 levels per wavelength. but the prism only decomposes. we did the math ourselves using detector readings. the hypothesis says the structure should do the math. this is where we test that.

### test 01 — addition

can two beams merge in a Y-junction so the output represents their sum?

**v1 — Y-junction baseline.** FAIL overall (22.6% avg error) but revealing. symmetric inputs (1.0,1.0), (2.0,2.0), (3.0,3.0) all had 2.91% error. asymmetric inputs gave different outputs for the same sum — (2.0,1.0) vs (1.0,2.0) should match but didn't. the structure was lopsided. basically: the math works, the plumbing was crooked.

**v2 — symmetric Y-junction.** near pass. fixed the geometry. (2.0,1.0) vs (1.0,2.0) now differ by only 0.11%. every pair with both inputs nonzero is under 5% error, most under 2%. only failures are single-channel signals at ~21% error. the structure adds correctly when both beams are present. we're not changing how light works, we're just shaping the container so the physics can do what it already does cleanly.

### the zero problem

the system can't read a signal that isn't there. we need a way to represent zero.

**option A — baseline offset.** use 0.5 as "zero." always send both wavelengths. decoder subtracts 0.5 from readings. simple, no protocol needed.

**option B — channel counting.** embed a count in the signal telling the decoder how many channels are active. missing channel = zero. more complex, adds a logic layer.

no decision yet.

### test 02 — zero floor

tested baseline amplitudes from 0.5 down to 0.05, each paired with strong signals (1.0, 2.0, 3.0) under noise.

**v1 — baseline test.** 0.5 is the only viable floor. everything below it has errors larger than half the baseline value — the system can't tell if the dim signal is real data or noise. at 0.5, decoding still works. the drowning-out problem gets worse as the strong signal increases (strong=1.0 reads baselines fine, strong=3.0 struggles even at 0.5).

result: usable range is 0.5 to 4.0. that's 70 distinguishable levels per wavelength, 4,900 states per pulse. for context, one binary switch gives 2 states. this doesn't matter for computation inside the structure (distances are microns, no signal loss). transmission over distance is a separate problem with known solutions.