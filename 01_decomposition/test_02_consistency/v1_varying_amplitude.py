"""
prism-theory / 01_decomposition / test 02 — consistency (v1)

test 01 proved a wedge prism can separate two wavelengths.
now: is the separation ratio consistent when we change input power?

we run the same wedge prism 10 times, each time with a different
amplitude (brightness) for the input beam. if the ratio between
wavelengths at each detector stays the same regardless of how
bright the input is, the system is linear and predictable —
meaning we can reliably decode data from it.

if the ratios drift with amplitude, the system is nonlinear and
harder to use for data encoding.
"""

import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# PARAMETERS (same as v3 wedge prism)
# ============================================================

sx = 50
sy = 30
resolution = 20

wavelength_1 = 0.8
wavelength_2 = 1.2
freq_1 = 1 / wavelength_1
freq_2 = 1 / wavelength_2

# amplitudes to test — ranging from dim to bright
amplitudes = [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]

# detector positions (same as v3)
detector_x = 18
detector_positions = [-8, -4, 0, 4, 8]
detector_labels = ["y=-8", "y=-4", "y=0", "y=+4", "y=+8"]
nfreq = 200


def build_prism():
    """same wedge prism from v3"""
    glass = mp.Medium(
        epsilon=1.5,
        E_susceptibilities=[
            mp.LorentzianSusceptibility(
                frequency=3.0,
                gamma=0.1,
                sigma=3.0,
            )
        ],
    )

    prism_vertices = [
        mp.Vector3(-4, -6),
        mp.Vector3(2, -6),
        mp.Vector3(2, 6),
        mp.Vector3(-4, 2),
    ]

    return [
        mp.Prism(
            vertices=prism_vertices,
            height=mp.inf,
            material=glass,
            center=mp.Vector3(-3, 0),
        )
    ]


def run_sim(amplitude):
    """run the wedge prism sim with a given input amplitude"""

    sources = [
        mp.Source(
            mp.GaussianSource(frequency=freq_1, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-20, -1),
            size=mp.Vector3(0, 2),
            amplitude=amplitude,
        ),
        mp.Source(
            mp.GaussianSource(frequency=freq_2, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-20, -1),
            size=mp.Vector3(0, 2),
            amplitude=amplitude,
        ),
    ]

    sim = mp.Simulation(
        cell_size=mp.Vector3(sx, sy),
        geometry=build_prism(),
        sources=sources,
        boundary_layers=[mp.PML(thickness=2)],
        resolution=resolution,
    )

    flux_monitors = []
    for y_pos in detector_positions:
        fm = sim.add_flux(
            (freq_1 + freq_2) / 2, freq_1 - freq_2, nfreq,
            mp.FluxRegion(
                center=mp.Vector3(detector_x, y_pos),
                size=mp.Vector3(0, 3),
            ),
        )
        flux_monitors.append(fm)

    sim.run(until=120)

    # get flux at target wavelengths
    freqs = np.array(mp.get_flux_freqs(flux_monitors[0]))
    wavelengths = 1 / freqs
    idx1 = np.argmin(np.abs(wavelengths - wavelength_1))
    idx2 = np.argmin(np.abs(wavelengths - wavelength_2))

    results = {}
    for i, label in enumerate(detector_labels):
        flux_vals = np.array(mp.get_fluxes(flux_monitors[i]))
        f_w1 = flux_vals[idx1]
        f_w2 = flux_vals[idx2]
        # ratio of wavelength 2 to wavelength 1 at this detector
        ratio = f_w2 / f_w1 if f_w1 > 0.001 else float('nan')
        results[label] = {
            "w1": f_w1,
            "w2": f_w2,
            "ratio": ratio,
        }

    sim.reset_meep()
    return results


# ============================================================
# RUN ALL AMPLITUDES
# ============================================================

print(f"test 02 — consistency check")
print(f"running {len(amplitudes)} simulations with varying amplitude...")
print(f"amplitudes: {amplitudes}\n")

all_results = []

for i, amp in enumerate(amplitudes):
    print(f"  run {i+1}/{len(amplitudes)} — amplitude = {amp}")
    result = run_sim(amp)
    all_results.append(result)

print("\ndone. analyzing...\n")

# ============================================================
# ANALYZE — are ratios consistent?
# ============================================================

print(f"{'='*60}")
print(f"RATIO OF λ2/λ1 AT EACH DETECTOR ACROSS AMPLITUDES")
print(f"{'='*60}")
print(f"\n{'amp':<8}", end="")
for label in detector_labels:
    print(f"{label:<12}", end="")
print()
print("-" * 68)

# collect ratios per detector for stats
ratios_by_detector = {label: [] for label in detector_labels}

for i, amp in enumerate(amplitudes):
    print(f"{amp:<8.1f}", end="")
    for label in detector_labels:
        r = all_results[i][label]["ratio"]
        ratios_by_detector[label].append(r)
        if np.isnan(r):
            print(f"{'N/A':<12}", end="")
        else:
            print(f"{r:<12.4f}", end="")
    print()

# compute standard deviation and coefficient of variation for each detector
print(f"\n{'='*60}")
print(f"CONSISTENCY METRICS")
print(f"{'='*60}")

all_consistent = True
for label in detector_labels:
    ratios = [r for r in ratios_by_detector[label] if not np.isnan(r)]
    if len(ratios) < 2:
        print(f"\n{label}: not enough data")
        continue

    mean = np.mean(ratios)
    std = np.std(ratios)
    cv = (std / mean * 100) if mean != 0 else float('inf')

    print(f"\n{label}:")
    print(f"  mean ratio:  {mean:.4f}")
    print(f"  std dev:     {std:.4f}")
    print(f"  variation:   {cv:.2f}%")

    if cv > 5.0:
        all_consistent = False

# pass/fail
print(f"\n{'='*60}")
if all_consistent:
    print(">>> PASS — ratios are consistent across amplitudes (<5% variation)")
    print("    the system is linear and predictable.")
else:
    print(">>> FAIL — ratios vary too much across amplitudes (>5% variation)")
    print("    system may be nonlinear at some amplitudes.")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(2, 1, figsize=(10, 8))

colors = ["#1a3a5c", "#2d7d46", "#666666", "#c44e52", "#8e6bb0"]

# plot 1: ratio vs amplitude for each detector
for i, label in enumerate(detector_labels):
    ratios = ratios_by_detector[label]
    valid = [(a, r) for a, r in zip(amplitudes, ratios) if not np.isnan(r)]
    if valid:
        amps_v, rats_v = zip(*valid)
        axes[0].plot(amps_v, rats_v, 'o-', label=label, color=colors[i])

axes[0].set_xlabel("input amplitude")
axes[0].set_ylabel("λ2/λ1 ratio")
axes[0].set_title("separation ratio vs input amplitude (flat = consistent)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# plot 2: flux at each detector scales with amplitude (linearity check)
for i, label in enumerate(detector_labels):
    w2_flux = [all_results[j][label]["w2"] for j in range(len(amplitudes))]
    axes[1].plot(amplitudes, w2_flux, 'o-', label=label, color=colors[i])

axes[1].set_xlabel("input amplitude")
axes[1].set_ylabel("flux at λ=1.2μm")
axes[1].set_title("output power vs input amplitude (linear = predictable)")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("results/v1_results.png", dpi=150, bbox_inches="tight")
print("\nsaved: results/v1_results.png")