"""
prism-theory / 03_scalability / test 01 — chain (v2: zero floor)

v1 proved chaining works with strong signals. now: does our zero
floor (0.5) survive the full chain?

send pairs where one or both channels are at 0.5 (our "zero")
through Y-junction -> prism and check if we can decode them.
no noise yet, just testing the zero concept in a chain.
"""

import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# PARAMETERS
# ============================================================

sx = 70
sy = 20
resolution = 20

wavelength_1 = 0.8
wavelength_2 = 1.2
freq_1 = 1 / wavelength_1
freq_2 = 1 / wavelength_2
nfreq = 200

test_pairs = [
    (0.5, 0.5),   # both "zero"
    (0.5, 1.0),   # λ1 zero, λ2 low
    (1.0, 0.5),   # λ1 low, λ2 zero
    (0.5, 2.0),   # λ1 zero, λ2 mid
    (2.0, 0.5),   # λ1 mid, λ2 zero
    (0.5, 3.0),   # λ1 zero, λ2 high
    (3.0, 0.5),   # λ1 high, λ2 zero
    (1.0, 1.0),   # reference balanced
    (2.0, 2.0),   # reference balanced
]


def run_chain(amp1, amp2):
    guide_material = mp.Medium(epsilon=12)
    glass = mp.Medium(
        epsilon=1.5,
        E_susceptibilities=[
            mp.LorentzianSusceptibility(frequency=3.0, gamma=0.1, sigma=3.0)
        ],
    )

    wg_width = 0.6
    half_sep = 1.5

    geometry = [
        mp.Block(
            center=mp.Vector3(-28, half_sep),
            size=mp.Vector3(10, wg_width),
            material=guide_material,
        ),
        mp.Block(
            center=mp.Vector3(-28, -half_sep),
            size=mp.Vector3(10, wg_width),
            material=guide_material,
        ),
        mp.Prism(
            vertices=[
                mp.Vector3(-23, half_sep + wg_width/2),
                mp.Vector3(-19, wg_width/2),
                mp.Vector3(-19, -wg_width/2),
                mp.Vector3(-23, -(half_sep + wg_width/2)),
            ],
            height=mp.inf,
            material=guide_material,
        ),
        mp.Block(
            center=mp.Vector3(-12, 0),
            size=mp.Vector3(14, wg_width),
            material=guide_material,
        ),
        mp.Prism(
            vertices=[
                mp.Vector3(-4, -6),
                mp.Vector3(2, -6),
                mp.Vector3(2, 6),
                mp.Vector3(-4, 2),
            ],
            height=mp.inf,
            material=glass,
            center=mp.Vector3(5, 0),
        ),
    ]

    sources = [
        mp.Source(
            mp.GaussianSource(frequency=freq_1, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-32, half_sep),
            size=mp.Vector3(0, wg_width),
            amplitude=amp1,
        ),
        mp.Source(
            mp.GaussianSource(frequency=freq_2, fwidth=0.1),
            component=mp.Ez,
            center=mp.Vector3(-32, -half_sep),
            size=mp.Vector3(0, wg_width),
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

    det_labels = ["y=-6", "y=+6"]
    flux_monitors = []
    for y_pos in [-6, 6]:
        fm = sim.add_flux(
            (freq_1 + freq_2) / 2, freq_1 - freq_2, nfreq,
            mp.FluxRegion(
                center=mp.Vector3(25, y_pos),
                size=mp.Vector3(0, 3),
            ),
        )
        flux_monitors.append(fm)

    sim.run(until=150)

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
# CALIBRATE through the full chain
# ============================================================

print("test 01 v2 — chain with zero floor")
print("="*50)
print("\ncalibrating through full chain...\n")

cal_w1 = run_chain(1.0, 0.01)
cal_w2 = run_chain(0.01, 1.0)

det_labels = ["y=-6", "y=+6"]

M = np.array([
    [cal_w1[det_labels[0]]["w1"] + cal_w1[det_labels[0]]["w2"],
     cal_w2[det_labels[0]]["w1"] + cal_w2[det_labels[0]]["w2"]],
    [cal_w1[det_labels[1]]["w1"] + cal_w1[det_labels[1]]["w2"],
     cal_w2[det_labels[1]]["w1"] + cal_w2[det_labels[1]]["w2"]],
])
M_inv = np.linalg.inv(M)
print("  calibrated.\n")

# ============================================================
# TEST
# ============================================================

print(f"testing {len(test_pairs)} pairs...\n")

results_table = []

for i, (sent_a1, sent_a2) in enumerate(test_pairs):
    print(f"  pair {i+1}: ({sent_a1}, {sent_a2}) ... ", end="")

    readings = run_chain(sent_a1, sent_a2)

    obs = np.array([
        readings[det_labels[0]]["w1"] + readings[det_labels[0]]["w2"],
        readings[det_labels[1]]["w1"] + readings[det_labels[1]]["w2"],
    ])

    decoded_sq = M_inv @ obs
    decoded_a1 = np.sqrt(max(decoded_sq[0], 0))
    decoded_a2 = np.sqrt(max(decoded_sq[1], 0))

    err_a1 = abs(decoded_a1 - sent_a1)
    err_a2 = abs(decoded_a2 - sent_a2)

    print(f"decoded ({decoded_a1:.3f}, {decoded_a2:.3f}) "
          f"err ({err_a1:.3f}, {err_a2:.3f})")

    results_table.append({
        "sent": (sent_a1, sent_a2),
        "decoded": (decoded_a1, decoded_a2),
        "error": (err_a1, err_a2),
    })

# ============================================================
# SUMMARY
# ============================================================

print(f"\n{'='*50}")
print("SUMMARY")
print(f"{'='*50}\n")

print(f"{'sent':<16}{'decoded':<22}{'error':<18}{'status'}")
print("-" * 66)

for r in results_table:
    s = f"({r['sent'][0]:.1f}, {r['sent'][1]:.1f})"
    d = f"({r['decoded'][0]:.3f}, {r['decoded'][1]:.3f})"
    e = f"({r['error'][0]:.3f}, {r['error'][1]:.3f})"
    max_err = max(r['error'])
    status = "PASS" if max_err < 0.1 else "CLOSE" if max_err < 0.3 else "FAIL"
    print(f"{s:<16}{d:<22}{e:<18}{status}")

# zero floor specific check
print(f"\nZERO FLOOR CHECK:")
zero_pairs = [r for r in results_table if 0.5 in r["sent"]]
zero_errors = [max(r["error"]) for r in zero_pairs]
avg_zero_err = np.mean(zero_errors)
max_zero_err = np.max(zero_errors)
print(f"  avg max error on zero-floor pairs: {avg_zero_err:.4f}")
print(f"  worst error on zero-floor pairs: {max_zero_err:.4f}")

if max_zero_err < 0.3:
    print(f"  >>> PASS — zero floor survives the chain")
else:
    print(f"  >>> FAIL — zero floor doesn't survive the chain")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

sent_a1 = [r["sent"][0] for r in results_table]
dec_a1 = [r["decoded"][0] for r in results_table]
sent_a2 = [r["sent"][1] for r in results_table]
dec_a2 = [r["decoded"][1] for r in results_table]

max_val = max(max(sent_a1 + dec_a1), max(sent_a2 + dec_a2)) + 0.5
axes[0].plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label="perfect")
axes[0].scatter(sent_a1, dec_a1, color="#1a3a5c", s=60, label="λ1")
axes[0].scatter(sent_a2, dec_a2, color="#c44e52", s=60, label="λ2")
axes[0].set_xlabel("sent amplitude")
axes[0].set_ylabel("decoded amplitude")
axes[0].set_title("sent vs decoded through full chain")
axes[0].legend()
axes[0].grid(True, alpha=0.3)
axes[0].set_aspect('equal')
axes[0].set_xlim(-0.1, max_val)
axes[0].set_ylim(-0.1, max_val)

# highlight zero floor region
axes[0].axvline(x=0.5, color="orange", linestyle=":", alpha=0.4, label="zero floor")
axes[0].axhline(y=0.5, color="orange", linestyle=":", alpha=0.4)

errors = [max(r["error"]) for r in results_table]
labels_plot = [f"({r['sent'][0]},{r['sent'][1]})" for r in results_table]
colors = ["#2d7d46" if e < 0.1 else "#e8a838" if e < 0.3 else "#c44e52" for e in errors]

axes[1].bar(range(len(results_table)), errors, color=colors, alpha=0.7)
axes[1].axhline(y=0.1, color="green", linestyle="--", alpha=0.5, label="pass (0.1)")
axes[1].axhline(y=0.3, color="orange", linestyle="--", alpha=0.5, label="close (0.3)")
axes[1].set_xticks(range(len(results_table)))
axes[1].set_xticklabels(labels_plot, rotation=45, fontsize=7)
axes[1].set_ylabel("max error")
axes[1].set_title("decoding error per pair through chain")
axes[1].legend(fontsize=8)
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("results/v2_results.png", dpi=150, bbox_inches="tight")
print(f"\nsaved: results/v2_results.png")