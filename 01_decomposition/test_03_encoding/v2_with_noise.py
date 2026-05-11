"""
prism-theory / 01_decomposition / test 03 — encoding (v2: with noise)

v1 proved encoding works in a perfect system. now: does it still work
when we add realistic noise to every run?

same approach as v1 (calibrate, encode, decode) but every run gets:
- amplitude jitter (±5% laser instability)
- epsilon jitter (±2% temperature drift)
- position jitter (±0.1μm alignment error)

calibration is done once (clean), then all 8 messages are decoded
under noisy conditions. we run the full message set 3 times with
different noise seeds to see how much the errors vary.
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

test_messages = [
    (1.0, 0.0),
    (0.0, 1.0),
    (1.0, 1.0),
    (2.0, 1.0),
    (1.0, 3.0),
    (3.5, 2.0),
    (0.5, 4.0),
    (2.5, 2.5),
]

num_trials = 3  # run all messages this many times with different noise


def run_sim(amp1, amp2, eps_jitter=0, pos_jitter=0):
    """run wedge prism with optional noise"""

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

    sources = []
    if amp1 > 0:
        sources.append(mp.Source(
            mp.GaussianSource(frequency=freq_1, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-20, -1 + pos_jitter),
            size=mp.Vector3(0, 2),
            amplitude=amp1,
        ))
    if amp2 > 0:
        sources.append(mp.Source(
            mp.GaussianSource(frequency=freq_2, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-20, -1 + pos_jitter),
            size=mp.Vector3(0, 2),
            amplitude=amp2,
        ))

    if not sources:
        return {label: {"w1": 0, "w2": 0} for label in det_labels}

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
# STEP 1: CALIBRATION (clean, no noise)
# ============================================================

print("test 03 v2 — encoding with noise")
print("="*50)
print("\nSTEP 1: calibrating (clean)...\n")

print("  calibration run 1: λ1 only")
cal_w1 = run_sim(1.0, 0.0)

print("  calibration run 2: λ2 only")
cal_w2 = run_sim(0.0, 1.0)

M = np.array([
    [cal_w1[det_labels[0]]["w1"] + cal_w1[det_labels[0]]["w2"],
     cal_w2[det_labels[0]]["w1"] + cal_w2[det_labels[0]]["w2"]],
    [cal_w1[det_labels[1]]["w1"] + cal_w1[det_labels[1]]["w2"],
     cal_w2[det_labels[1]]["w1"] + cal_w2[det_labels[1]]["w2"]],
])

M_inv = np.linalg.inv(M)
print(f"\n  transfer matrix calibrated.")

# ============================================================
# STEP 2: ENCODE/DECODE WITH NOISE (3 trials)
# ============================================================

print(f"\nSTEP 2: encoding {len(test_messages)} messages x {num_trials} trials with noise...\n")

all_trials = []

for trial in range(num_trials):
    np.random.seed(trial * 42 + 7)
    trial_results = []

    print(f"  --- trial {trial+1}/{num_trials} ---")

    for msg_idx, (sent_a1, sent_a2) in enumerate(test_messages):
        # add noise to the amplitudes
        noisy_a1 = max(sent_a1 + np.random.uniform(-amplitude_noise, amplitude_noise), 0)
        noisy_a2 = max(sent_a2 + np.random.uniform(-amplitude_noise, amplitude_noise), 0)
        eps_j = np.random.uniform(-epsilon_noise, epsilon_noise)
        pos_j = np.random.uniform(-position_noise, position_noise)

        readings = run_sim(noisy_a1, noisy_a2, eps_jitter=eps_j, pos_jitter=pos_j)

        obs = np.array([
            readings[det_labels[0]]["w1"] + readings[det_labels[0]]["w2"],
            readings[det_labels[1]]["w1"] + readings[det_labels[1]]["w2"],
        ])

        decoded_sq = M_inv @ obs
        decoded_a1 = np.sqrt(max(decoded_sq[0], 0))
        decoded_a2 = np.sqrt(max(decoded_sq[1], 0))

        # error relative to what we INTENDED to send (not the noisy version)
        err_a1 = abs(decoded_a1 - sent_a1)
        err_a2 = abs(decoded_a2 - sent_a2)

        print(f"    msg {msg_idx+1} sent({sent_a1:.1f},{sent_a2:.1f}) "
              f"decoded({decoded_a1:.3f},{decoded_a2:.3f}) "
              f"err({err_a1:.3f},{err_a2:.3f})")

        trial_results.append({
            "sent": (sent_a1, sent_a2),
            "decoded": (decoded_a1, decoded_a2),
            "error": (err_a1, err_a2),
        })

    all_trials.append(trial_results)

# ============================================================
# SUMMARY
# ============================================================

print(f"\n{'='*60}")
print(f"SUMMARY ACROSS {num_trials} NOISY TRIALS")
print(f"{'='*60}")
print(f"\n{'message':<20}{'avg err λ1':<14}{'avg err λ2':<14}{'max err':<12}{'status'}")
print("-" * 60)

total_max_err = 0
all_pass = True

for msg_idx in range(len(test_messages)):
    sent = test_messages[msg_idx]
    errs_a1 = [all_trials[t][msg_idx]["error"][0] for t in range(num_trials)]
    errs_a2 = [all_trials[t][msg_idx]["error"][1] for t in range(num_trials)]

    avg_e1 = np.mean(errs_a1)
    avg_e2 = np.mean(errs_a2)
    max_e = max(max(errs_a1), max(errs_a2))
    total_max_err += max_e

    status = "PASS" if max_e < 0.1 else "CLOSE" if max_e < 0.3 else "FAIL"
    if max_e >= 0.1:
        all_pass = False

    s = f"({sent[0]:.1f}, {sent[1]:.1f})"
    print(f"{s:<20}{avg_e1:<14.4f}{avg_e2:<14.4f}{max_e:<12.4f}{status}")

avg_max = total_max_err / len(test_messages)
print(f"\navg max error: {avg_max:.4f}")

if all_pass:
    print(f"\n>>> PASS — all messages decoded within 0.1 error under noise")
else:
    print(f"\n>>> PARTIAL — some messages exceed 0.1 error under noise")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# plot 1: sent vs decoded across all trials
all_sent_a1, all_dec_a1, all_sent_a2, all_dec_a2 = [], [], [], []
for trial_results in all_trials:
    for r in trial_results:
        all_sent_a1.append(r["sent"][0])
        all_dec_a1.append(r["decoded"][0])
        all_sent_a2.append(r["sent"][1])
        all_dec_a2.append(r["decoded"][1])

max_val = max(max(all_sent_a1 + all_dec_a1), max(all_sent_a2 + all_dec_a2)) + 0.5
axes[0].plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label="perfect")
axes[0].scatter(all_sent_a1, all_dec_a1, color="#1a3a5c", s=30, alpha=0.6, label="λ1")
axes[0].scatter(all_sent_a2, all_dec_a2, color="#c44e52", s=30, alpha=0.6, label="λ2")
axes[0].set_xlabel("sent amplitude")
axes[0].set_ylabel("decoded amplitude")
axes[0].set_title(f"sent vs decoded ({num_trials} noisy trials)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)
axes[0].set_aspect('equal')
axes[0].set_xlim(-0.2, max_val)
axes[0].set_ylim(-0.2, max_val)

# plot 2: error distribution
all_errors = []
for trial_results in all_trials:
    for r in trial_results:
        all_errors.append(max(r["error"]))

axes[1].hist(all_errors, bins=15, color="#2d7d46", alpha=0.7, edgecolor="white")
axes[1].axvline(x=0.1, color="red", linestyle="--", label="pass threshold (0.1)")
axes[1].set_xlabel("max error per message")
axes[1].set_ylabel("count")
axes[1].set_title(f"error distribution ({len(all_errors)} total decodings)")
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("results/v2_results.png", dpi=150, bbox_inches="tight")
print(f"\nsaved: results/v2_results.png")