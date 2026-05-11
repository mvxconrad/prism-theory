"""
prism-theory / 01_decomposition / test 03 — encoding (v1: calibration)

the big test. can we encode data onto two wavelengths and decode it
from the detector readings?

how it works:
1. CALIBRATION — run two reference signals to learn the system:
   - send only wavelength 1 (amplitude=1, wavelength 2 off)
   - send only wavelength 2 (amplitude=1, wavelength 1 off)
   - record how much flux each wavelength alone produces at each detector
   - this gives us a transfer matrix: input -> output mapping

2. ENCODING — send both wavelengths at different amplitudes.
   the amplitudes ARE the data. e.g. (3.0, 1.5) means
   wavelength 1 at power 3.0 and wavelength 2 at power 1.5.

3. DECODING — read the flux at two detectors and use the
   calibration matrix to solve for the original amplitudes.
   if decoded values match what we sent, encoding works.

this is the core proof: can a prism turn light into readable data?
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
# using two detectors that showed good separation in test 01
# y=0 (where λ1 peaked) and y=-4 (where λ2 peaked)
det_positions = [0, -4]
det_labels = ["y=0", "y=-4"]
nfreq = 200

# data to encode — pairs of (amplitude_λ1, amplitude_λ2)
test_messages = [
    (1.0, 0.0),   # only wavelength 1
    (0.0, 1.0),   # only wavelength 2
    (1.0, 1.0),   # equal
    (2.0, 1.0),   # λ1 dominant
    (1.0, 3.0),   # λ2 dominant
    (3.5, 2.0),   # arbitrary
    (0.5, 4.0),   # another arbitrary
    (2.5, 2.5),   # equal but louder
]


def build_sim(amp1, amp2):
    """build and run sim with given amplitudes for each wavelength"""

    glass = mp.Medium(
        epsilon=1.5,
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
            center=mp.Vector3(-20, -1),
            size=mp.Vector3(0, 2),
            amplitude=amp1,
        ))
    if amp2 > 0:
        sources.append(mp.Source(
            mp.GaussianSource(frequency=freq_2, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-20, -1),
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
# STEP 1: CALIBRATION
# ============================================================

print("test 03 — encoding/decoding (v1: no noise)")
print("="*50)
print("\nSTEP 1: calibrating system...\n")

# send only λ1 at amplitude 1
print("  calibration run 1: λ1 only (amp=1.0)")
cal_w1 = build_sim(1.0, 0.0)

# send only λ2 at amplitude 1
print("  calibration run 2: λ2 only (amp=1.0)")
cal_w2 = build_sim(0.0, 1.0)

# build transfer matrix
# each detector reads some flux from λ1-only and some from λ2-only
# flux is proportional to amplitude^2 (power = amplitude squared)
#
# at detector d, total flux at frequency f =
#   cal_w1[d][f] * amp1^2 + cal_w2[d][f] * amp2^2
#
# we use flux at freq_1 at both detectors to build a 2x2 system:
# but actually since the system is linear in power, we'll use
# total flux (sum of both frequency readings) at each detector

# transfer matrix: M[detector][source]
# M[0][0] = flux at det0 from λ1 alone
# M[0][1] = flux at det0 from λ2 alone
# M[1][0] = flux at det1 from λ1 alone
# M[1][1] = flux at det1 from λ2 alone

# use total flux (w1 + w2 readings) as the signal
M = np.array([
    [cal_w1[det_labels[0]]["w1"] + cal_w1[det_labels[0]]["w2"],
     cal_w2[det_labels[0]]["w1"] + cal_w2[det_labels[0]]["w2"]],
    [cal_w1[det_labels[1]]["w1"] + cal_w1[det_labels[1]]["w2"],
     cal_w2[det_labels[1]]["w1"] + cal_w2[det_labels[1]]["w2"]],
])

print(f"\n  transfer matrix:")
print(f"    det y=0:  [{M[0][0]:.4f}, {M[0][1]:.4f}]")
print(f"    det y=-4: [{M[1][0]:.4f}, {M[1][1]:.4f}]")

# invert the matrix — this is our decoder
M_inv = np.linalg.inv(M)
print(f"\n  inverse (decoder) matrix:")
print(f"    [{M_inv[0][0]:.4f}, {M_inv[0][1]:.4f}]")
print(f"    [{M_inv[1][0]:.4f}, {M_inv[1][1]:.4f}]")

# ============================================================
# STEP 2: ENCODE AND DECODE
# ============================================================

print(f"\nSTEP 2: encoding {len(test_messages)} messages...\n")

results_table = []

for msg_idx, (sent_a1, sent_a2) in enumerate(test_messages):
    print(f"  message {msg_idx+1}: sent ({sent_a1:.1f}, {sent_a2:.1f})")

    readings = build_sim(sent_a1, sent_a2)

    # total flux at each detector
    obs = np.array([
        readings[det_labels[0]]["w1"] + readings[det_labels[0]]["w2"],
        readings[det_labels[1]]["w1"] + readings[det_labels[1]]["w2"],
    ])

    # decode: solve for original amplitudes squared
    # obs = M * [a1^2, a2^2]  =>  [a1^2, a2^2] = M_inv * obs
    decoded_sq = M_inv @ obs
    decoded_a1 = np.sqrt(max(decoded_sq[0], 0))
    decoded_a2 = np.sqrt(max(decoded_sq[1], 0))

    # error
    err_a1 = abs(decoded_a1 - sent_a1)
    err_a2 = abs(decoded_a2 - sent_a2)

    print(f"           decoded ({decoded_a1:.3f}, {decoded_a2:.3f}) "
          f"error ({err_a1:.3f}, {err_a2:.3f})")

    results_table.append({
        "sent": (sent_a1, sent_a2),
        "decoded": (decoded_a1, decoded_a2),
        "error": (err_a1, err_a2),
    })

# ============================================================
# SUMMARY
# ============================================================

print(f"\n{'='*60}")
print(f"ENCODING RESULTS SUMMARY")
print(f"{'='*60}")
print(f"\n{'sent':<20}{'decoded':<24}{'error':<20}{'status'}")
print("-" * 74)

total_err = 0
all_pass = True
for r in results_table:
    s = f"({r['sent'][0]:.1f}, {r['sent'][1]:.1f})"
    d = f"({r['decoded'][0]:.3f}, {r['decoded'][1]:.3f})"
    e = f"({r['error'][0]:.3f}, {r['error'][1]:.3f})"
    max_err = max(r['error'])
    status = "PASS" if max_err < 0.1 else "CLOSE" if max_err < 0.3 else "FAIL"
    if max_err >= 0.1:
        all_pass = False
    total_err += max_err
    print(f"{s:<20}{d:<24}{e:<20}{status}")

avg_err = total_err / len(results_table)
print(f"\naverage max error: {avg_err:.4f}")

if all_pass:
    print(f"\n>>> PASS — all messages decoded within 0.1 error")
    print(f"    data can be encoded on light and decoded by a prism.")
else:
    print(f"\n>>> PARTIAL — some messages decoded with error > 0.1")
    print(f"    encoding works but accuracy needs improvement.")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# plot 1: sent vs decoded for amplitude 1
sent_a1 = [r["sent"][0] for r in results_table]
dec_a1 = [r["decoded"][0] for r in results_table]
sent_a2 = [r["sent"][1] for r in results_table]
dec_a2 = [r["decoded"][1] for r in results_table]

# perfect line
max_val = max(max(sent_a1 + dec_a1), max(sent_a2 + dec_a2)) + 0.5
axes[0].plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label="perfect")
axes[0].scatter(sent_a1, dec_a1, color="#1a3a5c", s=60, label="λ1 (0.8μm)")
axes[0].scatter(sent_a2, dec_a2, color="#c44e52", s=60, label="λ2 (1.2μm)")
axes[0].set_xlabel("sent amplitude")
axes[0].set_ylabel("decoded amplitude")
axes[0].set_title("sent vs decoded (on the line = perfect)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)
axes[0].set_aspect('equal')
axes[0].set_xlim(-0.2, max_val)
axes[0].set_ylim(-0.2, max_val)

# plot 2: error per message
msg_nums = range(1, len(results_table) + 1)
err_a1 = [r["error"][0] for r in results_table]
err_a2 = [r["error"][1] for r in results_table]

x = np.arange(len(results_table))
width = 0.35
axes[1].bar(x - width/2, err_a1, width, label="λ1 error", color="#1a3a5c")
axes[1].bar(x + width/2, err_a2, width, label="λ2 error", color="#c44e52")
axes[1].axhline(y=0.1, color="green", linestyle="--", alpha=0.5, label="pass threshold")
axes[1].set_xlabel("message number")
axes[1].set_ylabel("absolute error")
axes[1].set_title("decoding error per message")
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("results/v1_results.png", dpi=150, bbox_inches="tight")
print(f"\nsaved: results/v1_results.png")