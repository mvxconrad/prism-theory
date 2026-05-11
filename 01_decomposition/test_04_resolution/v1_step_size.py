"""
prism-theory / 01_decomposition / test 04 — resolution (v1)

we know encoding works. now: how fine-grained can it be?

send pairs of signals where only λ2 changes by a small amount.
keep λ1 fixed at 2.0 as a reference. vary λ2 from 2.0 to 2.5
in decreasing step sizes to find the smallest difference the
system can reliably detect under noise.

if we can distinguish 0.05 apart on a 1.0-4.0 range, that's
60 levels per wavelength. two wavelengths = 3,600 states per pulse.
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

detector_x = 18
det_positions = [0, -4]
det_labels = ["y=0", "y=-4"]
nfreq = 200

amplitude_noise = 0.05
epsilon_noise = 0.03
position_noise = 0.1

# fixed λ1, vary λ2 by these amounts above 2.0
base_amp = 2.0
deltas = [0.5, 0.4, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05, 0.03, 0.01]

trials_per_delta = 5  # run each delta multiple times with noise


def run_sim(amp1, amp2, eps_jitter=0, pos_jitter=0):
    glass = mp.Medium(
        epsilon=1.5 + eps_jitter,
        E_susceptibilities=[
            mp.LorentzianSusceptibility(frequency=3.0, gamma=0.1, sigma=3.0)
        ],
    )

    geometry = [
        mp.Prism(
            vertices=[
                mp.Vector3(-4, -6),
                mp.Vector3(2, -6),
                mp.Vector3(2, 6),
                mp.Vector3(-4, 2),
            ],
            height=mp.inf,
            material=glass,
            center=mp.Vector3(-3, 0),
        )
    ]

    sources = [
        mp.Source(
            mp.GaussianSource(frequency=freq_1, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-20, -1 + pos_jitter),
            size=mp.Vector3(0, 2),
            amplitude=amp1,
        ),
        mp.Source(
            mp.GaussianSource(frequency=freq_2, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-20, -1 + pos_jitter),
            size=mp.Vector3(0, 2),
            amplitude=amp2,
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
    for y_pos in det_positions:
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
    for i, label in enumerate(det_labels):
        flux_vals = np.array(mp.get_fluxes(flux_monitors[i]))
        results[label] = {"w1": flux_vals[idx1], "w2": flux_vals[idx2]}

    sim.reset_meep()
    return results


# ============================================================
# CALIBRATE (clean)
# ============================================================

print("test 04 — resolution")
print("="*50)
print("\ncalibrating...\n")

cal_w1 = run_sim(1.0, 0.0)
cal_w2 = run_sim(0.0, 1.0)

M = np.array([
    [cal_w1[det_labels[0]]["w1"] + cal_w1[det_labels[0]]["w2"],
     cal_w2[det_labels[0]]["w1"] + cal_w2[det_labels[0]]["w2"]],
    [cal_w1[det_labels[1]]["w1"] + cal_w1[det_labels[1]]["w2"],
     cal_w2[det_labels[1]]["w1"] + cal_w2[det_labels[1]]["w2"]],
])
M_inv = np.linalg.inv(M)
print("  calibrated.\n")

# ============================================================
# TEST EACH DELTA
# ============================================================

print(f"testing {len(deltas)} step sizes, {trials_per_delta} noisy trials each")
print(f"λ1 fixed at {base_amp}, λ2 = {base_amp} + delta\n")

results = {}

for delta in deltas:
    target_a2 = base_amp + delta
    decoded_a2_list = []
    errors = []

    for trial in range(trials_per_delta):
        np.random.seed(trial * 100 + int(delta * 1000))

        noisy_a1 = base_amp + np.random.uniform(-amplitude_noise, amplitude_noise)
        noisy_a2 = target_a2 + np.random.uniform(-amplitude_noise, amplitude_noise)
        eps_j = np.random.uniform(-epsilon_noise, epsilon_noise)
        pos_j = np.random.uniform(-position_noise, position_noise)

        readings = run_sim(noisy_a1, noisy_a2, eps_jitter=eps_j, pos_jitter=pos_j)

        obs = np.array([
            readings[det_labels[0]]["w1"] + readings[det_labels[0]]["w2"],
            readings[det_labels[1]]["w1"] + readings[det_labels[1]]["w2"],
        ])

        decoded_sq = M_inv @ obs
        decoded_a2 = np.sqrt(max(decoded_sq[1], 0))
        decoded_a2_list.append(decoded_a2)
        errors.append(abs(decoded_a2 - target_a2))

    # can we tell this apart from base_amp?
    # decoded values should cluster around target_a2, not base_amp
    mean_decoded = np.mean(decoded_a2_list)
    std_decoded = np.std(decoded_a2_list)
    mean_error = np.mean(errors)

    # the signal is distinguishable if the mean decoded value is
    # closer to the target than to the base, and the spread doesn't
    # overlap with the base value
    dist_to_target = abs(mean_decoded - target_a2)
    dist_to_base = abs(mean_decoded - base_amp)
    separable = dist_to_base > 2 * std_decoded and dist_to_target < delta

    results[delta] = {
        "mean_decoded": mean_decoded,
        "std": std_decoded,
        "mean_error": mean_error,
        "separable": separable,
        "all_decoded": decoded_a2_list,
    }

    status = "SEPARABLE" if separable else "NOT SEPARABLE"
    print(f"  delta={delta:<6.2f} target={target_a2:.2f} "
          f"decoded={mean_decoded:.4f}±{std_decoded:.4f} "
          f"err={mean_error:.4f} [{status}]")

# ============================================================
# FIND RESOLUTION LIMIT
# ============================================================

print(f"\n{'='*50}")
print("RESOLUTION SUMMARY")
print(f"{'='*50}\n")

smallest_separable = None
for delta in deltas:
    if results[delta]["separable"]:
        smallest_separable = delta

if smallest_separable:
    usable_range = 3.0  # 1.0 to 4.0
    levels = int(usable_range / smallest_separable)
    states_2ch = levels * levels
    equiv_bits = np.log2(states_2ch) if states_2ch > 0 else 0

    print(f"smallest separable step: {smallest_separable}")
    print(f"usable range: 1.0 — 4.0 ({usable_range} wide)")
    print(f"distinguishable levels per wavelength: {levels}")
    print(f"two wavelengths: {levels} x {levels} = {states_2ch} states")
    print(f"equivalent to: {equiv_bits:.1f} bits per pulse")
    print(f"\n>>> for comparison, binary = 1 bit per switch per cycle")
else:
    print("no step size was reliably separable under noise.")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# plot 1: decoded value vs delta (should track the diagonal)
delta_vals = list(results.keys())
means = [results[d]["mean_decoded"] for d in delta_vals]
stds = [results[d]["std"] for d in delta_vals]
targets = [base_amp + d for d in delta_vals]

axes[0].errorbar(targets, means, yerr=stds, fmt='o', color="#1a3a5c",
                 capsize=4, label="decoded (mean ± std)")
axes[0].plot([base_amp, base_amp + max(deltas) + 0.1],
             [base_amp, base_amp + max(deltas) + 0.1],
             'k--', alpha=0.3, label="perfect")
axes[0].axhline(y=base_amp, color="red", linestyle=":", alpha=0.4,
                label=f"base ({base_amp})")
axes[0].set_xlabel("target amplitude (λ2)")
axes[0].set_ylabel("decoded amplitude (λ2)")
axes[0].set_title("can we decode the difference?")
axes[0].legend(fontsize=8)
axes[0].grid(True, alpha=0.3)

# plot 2: separability — green if separable, red if not
colors_bar = ["#2d7d46" if results[d]["separable"] else "#c44e52"
              for d in delta_vals]
axes[1].bar(range(len(delta_vals)),
            [results[d]["mean_error"] for d in delta_vals],
            color=colors_bar, alpha=0.7)
axes[1].set_xticks(range(len(delta_vals)))
axes[1].set_xticklabels([f"{d}" for d in delta_vals], rotation=45)
axes[1].set_xlabel("step size (delta)")
axes[1].set_ylabel("mean decoding error")
axes[1].set_title("green = separable, red = not separable")
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("results/v1_results.png", dpi=150, bbox_inches="tight")
print(f"\nsaved: results/v1_results.png")