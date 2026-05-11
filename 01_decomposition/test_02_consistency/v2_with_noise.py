"""
prism-theory / 01_decomposition / test 02 — consistency (v2: with noise)

v1 was useless — MEEP is deterministic so identical runs give identical
results. this version adds real-world noise:

- random amplitude jitter on the input (laser instability)
- random perturbation to prism refractive index (temperature drift)
- random slight shift in source position (alignment error)

each of the 20 runs has different noise. if the ratios stay consistent
despite this, the system is robust. if they drift, we know how much
error to expect.
"""

import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# PARAMETERS
# ============================================================

sx = 50
sy = 30
resolution = 20

wavelength_1 = 0.8
wavelength_2 = 1.2
freq_1 = 1 / wavelength_1
freq_2 = 1 / wavelength_2

num_runs = 20
base_amplitude = 1.0

# noise levels (these are realistic for lab conditions)
amplitude_noise = 0.05    # 5% jitter in laser power
epsilon_noise = 0.03      # 2% variation in material properties (temperature)
position_noise = 0.1      # 0.1 micron alignment error

detector_x = 18
detector_positions = [-8, -4, 0, 4, 8]
detector_labels = ["y=-8", "y=-4", "y=0", "y=+4", "y=+8"]
nfreq = 200

np.random.seed(42)  # reproducible randomness


def run_sim(amp_jitter, eps_jitter, pos_jitter):
    """run wedge prism with noise applied"""

    # material with jittered epsilon
    glass = mp.Medium(
        epsilon=1.5 + eps_jitter,
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

    geometry = [
        mp.Prism(
            vertices=prism_vertices,
            height=mp.inf,
            material=glass,
            center=mp.Vector3(-3, 0),
        )
    ]

    # source with jittered amplitude and position
    sources = [
        mp.Source(
            mp.GaussianSource(frequency=freq_1, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-20, -1 + pos_jitter),
            size=mp.Vector3(0, 2),
            amplitude=base_amplitude + amp_jitter,
        ),
        mp.Source(
            mp.GaussianSource(frequency=freq_2, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-20, -1 + pos_jitter),
            size=mp.Vector3(0, 2),
            amplitude=base_amplitude + amp_jitter,
        ),
    ]

    sim = mp.Simulation(
        cell_size=mp.Vector3(sx, sy),
        geometry=geometry,
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

    freqs = np.array(mp.get_flux_freqs(flux_monitors[0]))
    wavelengths = 1 / freqs
    idx1 = np.argmin(np.abs(wavelengths - wavelength_1))
    idx2 = np.argmin(np.abs(wavelengths - wavelength_2))

    results = {}
    for i, label in enumerate(detector_labels):
        flux_vals = np.array(mp.get_fluxes(flux_monitors[i]))
        f_w1 = flux_vals[idx1]
        f_w2 = flux_vals[idx2]
        ratio = f_w2 / f_w1 if f_w1 > 0.001 else float('nan')
        results[label] = {"w1": f_w1, "w2": f_w2, "ratio": ratio}

    sim.reset_meep()
    return results


# ============================================================
# RUN WITH NOISE
# ============================================================

print(f"test 02 v2 — consistency with realistic noise")
print(f"runs: {num_runs}")
print(f"noise: amplitude ±{amplitude_noise*100:.0f}%, "
      f"epsilon ±{epsilon_noise*100:.0f}%, "
      f"position ±{position_noise}μm")
print(f"running...\n")

all_results = []
noise_log = []

for i in range(num_runs):
    amp_j = np.random.uniform(-amplitude_noise, amplitude_noise)
    eps_j = np.random.uniform(-epsilon_noise, epsilon_noise)
    pos_j = np.random.uniform(-position_noise, position_noise)

    noise_log.append({"amp": amp_j, "eps": eps_j, "pos": pos_j})
    print(f"  run {i+1}/{num_runs} — amp_jitter={amp_j:+.4f}, "
          f"eps_jitter={eps_j:+.4f}, pos_jitter={pos_j:+.4f}")

    result = run_sim(amp_j, eps_j, pos_j)
    all_results.append(result)

print("\ndone. analyzing...\n")

# ============================================================
# ANALYZE
# ============================================================

print(f"{'='*60}")
print(f"RATIO OF λ2/λ1 AT EACH DETECTOR (20 noisy runs)")
print(f"{'='*60}")
print(f"\n{'run':<6}", end="")
for label in detector_labels:
    print(f"{label:<12}", end="")
print()
print("-" * 66)

ratios_by_detector = {label: [] for label in detector_labels}

for i in range(num_runs):
    print(f"{i+1:<6}", end="")
    for label in detector_labels:
        r = all_results[i][label]["ratio"]
        ratios_by_detector[label].append(r)
        if np.isnan(r):
            print(f"{'N/A':<12}", end="")
        else:
            print(f"{r:<12.4f}", end="")
    print()

print(f"\n{'='*60}")
print(f"CONSISTENCY METRICS (avg ± std, coefficient of variation)")
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
    mn = np.min(ratios)
    mx = np.max(ratios)

    print(f"\n{label}:")
    print(f"  mean:      {mean:.4f}")
    print(f"  std dev:   {std:.4f}")
    print(f"  range:     {mn:.4f} — {mx:.4f}")
    print(f"  variation: {cv:.2f}%")

    if cv > 5.0:
        all_consistent = False

print(f"\n{'='*60}")
if all_consistent:
    print(f">>> PASS — ratios consistent under noise (<5% variation)")
    print(f"    system is robust to real-world conditions.")
else:
    print(f">>> MIXED — some detectors show >5% variation")
    print(f"    may need to select only the most stable detectors for encoding.")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(2, 1, figsize=(10, 8))
colors = ["#1a3a5c", "#2d7d46", "#666666", "#c44e52", "#8e6bb0"]

# plot 1: ratio spread per detector (box plot)
ratio_data = []
for label in detector_labels:
    ratios = [r for r in ratios_by_detector[label] if not np.isnan(r)]
    ratio_data.append(ratios)

bp = axes[0].boxplot(ratio_data, labels=detector_labels, patch_artist=True)
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)
axes[0].set_ylabel("λ2/λ1 ratio")
axes[0].set_title(f"ratio spread across {num_runs} noisy runs (tight = consistent)")
axes[0].grid(True, alpha=0.3, axis="y")

# plot 2: all ratios over runs as scatter
for i, label in enumerate(detector_labels):
    ratios = ratios_by_detector[label]
    axes[1].scatter(range(1, num_runs + 1), ratios, label=label,
                    color=colors[i], alpha=0.7, s=30)
    mean = np.mean([r for r in ratios if not np.isnan(r)])
    axes[1].axhline(y=mean, color=colors[i], linestyle="--", alpha=0.3)

axes[1].set_xlabel("run number")
axes[1].set_ylabel("λ2/λ1 ratio")
axes[1].set_title("ratio per run with noise (dashed = mean)")
axes[1].legend(fontsize=8)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("results/v2_results.png", dpi=150, bbox_inches="tight")
print(f"\nsaved: results/v2_results.png")