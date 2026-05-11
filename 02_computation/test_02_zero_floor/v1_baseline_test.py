"""
prism-theory / 02_computation / test 02 — zero floor (v1)

the system fails when one channel is at amplitude 0. we need a
baseline amplitude to represent zero. this test finds the lowest
baseline that still decodes accurately when paired with a strong
signal.

for each baseline level (0.5, 0.3, 0.2, 0.1, 0.05), pair it with
strong signals (1.0, 2.0, 3.0) and try to decode both values.
run each combo 3 times with noise to find where it breaks.

the lowest baseline that consistently decodes under 10% error
becomes our "zero."
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

# baselines to test as "zero"
baselines = [0.5, 0.3, 0.2, 0.1, 0.05]

# strong signal values to pair with
strong_signals = [1.0, 2.0, 3.0]

trials = 3


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
# CALIBRATE
# ============================================================

print("test 02 — zero floor")
print("="*50)
print("\ncalibrating...\n")

cal_w1 = run_sim(1.0, 0.001)  # near-zero instead of actual zero
cal_w2 = run_sim(0.001, 1.0)

M = np.array([
    [cal_w1[det_labels[0]]["w1"] + cal_w1[det_labels[0]]["w2"],
     cal_w2[det_labels[0]]["w1"] + cal_w2[det_labels[0]]["w2"]],
    [cal_w1[det_labels[1]]["w1"] + cal_w1[det_labels[1]]["w2"],
     cal_w2[det_labels[1]]["w1"] + cal_w2[det_labels[1]]["w2"]],
])
M_inv = np.linalg.inv(M)
print("  calibrated.\n")

# ============================================================
# TEST EACH BASELINE
# ============================================================

print(f"testing {len(baselines)} baselines x {len(strong_signals)} strong signals "
      f"x {trials} trials\n")

all_results = {}

for baseline in baselines:
    all_results[baseline] = {}

    for strong in strong_signals:
        errors_baseline = []
        errors_strong = []

        for trial in range(trials):
            np.random.seed(int(baseline * 1000) + int(strong * 100) + trial)

            noisy_strong = strong + np.random.uniform(-amplitude_noise, amplitude_noise)
            noisy_base = baseline + np.random.uniform(-amplitude_noise, amplitude_noise)
            eps_j = np.random.uniform(-epsilon_noise, epsilon_noise)
            pos_j = np.random.uniform(-position_noise, position_noise)

            # send strong on λ1, baseline on λ2
            readings = run_sim(noisy_strong, noisy_base,
                             eps_jitter=eps_j, pos_jitter=pos_j)

            obs = np.array([
                readings[det_labels[0]]["w1"] + readings[det_labels[0]]["w2"],
                readings[det_labels[1]]["w1"] + readings[det_labels[1]]["w2"],
            ])

            decoded_sq = M_inv @ obs
            decoded_a1 = np.sqrt(max(decoded_sq[0], 0))
            decoded_a2 = np.sqrt(max(decoded_sq[1], 0))

            errors_baseline.append(abs(decoded_a2 - baseline))
            errors_strong.append(abs(decoded_a1 - strong))

        avg_err_base = np.mean(errors_baseline)
        avg_err_strong = np.mean(errors_strong)
        max_err_base = np.max(errors_baseline)

        all_results[baseline][strong] = {
            "avg_err_baseline": avg_err_base,
            "avg_err_strong": avg_err_strong,
            "max_err_baseline": max_err_base,
        }

        print(f"  baseline={baseline:<6} strong={strong:<4} "
              f"baseline_err={avg_err_base:.4f} "
              f"strong_err={avg_err_strong:.4f} "
              f"max_base_err={max_err_base:.4f}")

# ============================================================
# FIND THE FLOOR
# ============================================================

print(f"\n{'='*50}")
print("ZERO FLOOR SUMMARY")
print(f"{'='*50}\n")

print(f"{'baseline':<12}{'avg error':<14}{'max error':<14}{'viable?'}")
print("-" * 50)

best_floor = None
for baseline in baselines:
    all_base_errors = []
    for strong in strong_signals:
        all_base_errors.append(all_results[baseline][strong]["max_err_baseline"])

    avg_max = np.mean(all_base_errors)
    worst = np.max(all_base_errors)

    # viable if we can decode the baseline value within 50% of itself
    # (since it represents zero, we just need to know it's "low")
    viable = worst < baseline * 0.5

    status = "YES" if viable else "NO"
    if viable and best_floor is None:
        best_floor = baseline
        status = "YES (best)"

    print(f"{baseline:<12}{avg_max:<14.4f}{worst:<14.4f}{status}")

if best_floor:
    print(f"\nrecommended zero floor: {best_floor}")
    print(f"usable amplitude range: {best_floor} — 4.0")
    levels = int((4.0 - best_floor) / 0.05)
    print(f"distinguishable levels per wavelength: {levels}")
    print(f"two wavelengths: {levels} x {levels} = {levels**2} states")
else:
    print(f"\nno viable baseline found")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# plot 1: error vs baseline for each strong signal
for strong in strong_signals:
    errs = [all_results[b][strong]["avg_err_baseline"] for b in baselines]
    axes[0].plot(baselines, errs, 'o-', label=f"strong={strong}")

axes[0].set_xlabel("baseline amplitude (representing zero)")
axes[0].set_ylabel("avg decoding error of baseline")
axes[0].set_title("how well can we read the 'zero' signal?")
axes[0].legend()
axes[0].grid(True, alpha=0.3)
axes[0].invert_xaxis()

# plot 2: bar chart of viability
max_errors = []
for baseline in baselines:
    worst = max(all_results[baseline][s]["max_err_baseline"] for s in strong_signals)
    max_errors.append(worst)

thresholds = [b * 0.5 for b in baselines]
colors = ["#2d7d46" if me < th else "#c44e52"
          for me, th in zip(max_errors, thresholds)]

axes[1].bar(range(len(baselines)), max_errors, color=colors, alpha=0.7)
axes[1].plot(range(len(baselines)), thresholds, 'r--', label="50% threshold")
axes[1].set_xticks(range(len(baselines)))
axes[1].set_xticklabels([str(b) for b in baselines])
axes[1].set_xlabel("baseline amplitude")
axes[1].set_ylabel("worst decoding error")
axes[1].set_title("green = viable zero floor, red = too noisy")
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("results/v1_results.png", dpi=150, bbox_inches="tight")
print(f"\nsaved: results/v1_results.png")