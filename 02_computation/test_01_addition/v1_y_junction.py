"""
prism-theory / 02_computation / test 01 — addition (v1)

can a structure add two light signals together?

how it works:
1. send beam A at some amplitude into a waveguide
2. send beam B at some amplitude into a second waveguide
3. both waveguides merge into one channel through a Y-junction
4. measure the output

if the output power scales predictably with the sum of inputs,
the structure is performing addition. no electronics, no detector
math. the physics does it.

light naturally does this (superposition) so the real question is:
can we build a structure where the addition is clean and measurable?

we test multiple input pairs and check if output = f(A + B) consistently.
"""

import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# PARAMETERS
# ============================================================

sx = 40
sy = 20
resolution = 20

# single wavelength for simplicity — we're testing computation not separation
wavelength = 1.0
freq = 1 / wavelength
nfreq = 100

# input pairs to test: (amplitude_A, amplitude_B)
test_pairs = [
    (1.0, 0.0),
    (0.0, 1.0),
    (1.0, 1.0),
    (2.0, 1.0),
    (1.0, 2.0),
    (1.5, 1.5),
    (2.0, 2.0),
    (3.0, 1.0),
    (1.0, 3.0),
    (2.5, 1.5),
    (0.5, 0.5),
    (3.0, 3.0),
]


def run_addition(amp_a, amp_b):
    """
    two sources feed into a Y-junction waveguide.
    they merge and we measure the combined output.

    the Y-junction is built from three simple waveguide segments:
    - top arm: source A enters from upper left
    - bottom arm: source B enters from lower left
    - merged output: single waveguide going right to detector
    """

    # waveguide material — simple dielectric
    guide_material = mp.Medium(epsilon=12)  # silicon-like

    # waveguide dimensions
    wg_width = 0.8

    # Y-junction geometry:
    # two input arms angled inward, merging into one output arm
    geometry = [
        # top input arm (angled down toward center)
        mp.Block(
            center=mp.Vector3(-8, 2.5),
            size=mp.Vector3(12, wg_width),
            e1=mp.Vector3(1, 0),
            e2=mp.Vector3(0, 1),
            material=guide_material,
        ),
        # bottom input arm (angled up toward center)
        mp.Block(
            center=mp.Vector3(-8, -2.5),
            size=mp.Vector3(12, wg_width),
            e1=mp.Vector3(1, 0),
            e2=mp.Vector3(0, 1),
            material=guide_material,
        ),
        # taper section — connects the two arms to the output
        # top taper
        mp.Block(
            center=mp.Vector3(-1, 1.25),
            size=mp.Vector3(4, 2.5 + wg_width),
            e1=mp.Vector3(1, 0),
            e2=mp.Vector3(0, 1),
            material=guide_material,
        ),
        # output arm (center, going right)
        mp.Block(
            center=mp.Vector3(8, 0),
            size=mp.Vector3(14, wg_width),
            material=guide_material,
        ),
    ]

    # sources — one in each input arm
    sources = []
    if amp_a > 0:
        sources.append(mp.Source(
            mp.GaussianSource(frequency=freq, fwidth=0.2),
            component=mp.Ez,
            center=mp.Vector3(-15, 2.5),
            size=mp.Vector3(0, wg_width),
            amplitude=amp_a,
        ))
    if amp_b > 0:
        sources.append(mp.Source(
            mp.GaussianSource(frequency=freq, fwidth=0.2),
            component=mp.Ez,
            center=mp.Vector3(-15, -2.5),
            size=mp.Vector3(0, wg_width),
            amplitude=amp_b,
        ))

    if not sources:
        return 0.0

    sim = mp.Simulation(
        cell_size=mp.Vector3(sx, sy),
        geometry=geometry,
        sources=sources,
        boundary_layers=[mp.PML(thickness=2)],
        resolution=resolution,
    )

    # detector at the output
    flux_mon = sim.add_flux(
        freq, 0.5, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(16, 0),
            size=mp.Vector3(0, wg_width * 2),
        ),
    )

    sim.run(until=100)

    # total output power
    flux_vals = mp.get_fluxes(flux_mon)
    total_flux = sum(f for f in flux_vals if f > 0)

    sim.reset_meep()
    return total_flux


# ============================================================
# RUN
# ============================================================

print("test 01 — addition")
print("="*50)
print(f"testing {len(test_pairs)} input pairs\n")

results = []

for i, (a, b) in enumerate(test_pairs):
    print(f"  pair {i+1}/{len(test_pairs)}: A={a:.1f}, B={b:.1f} ... ", end="")
    output = run_addition(a, b)
    results.append({"a": a, "b": b, "output": output, "sum": a + b})
    print(f"output={output:.4f}")

# ============================================================
# ANALYZE
# ============================================================

print(f"\n{'='*50}")
print("RESULTS")
print(f"{'='*50}\n")

# check if output is proportional to (a + b)^2
# (power scales with amplitude squared, so if amplitudes add,
# power should scale with the square of the sum)
sums = np.array([r["sum"] for r in results])
sums_sq = sums ** 2
outputs = np.array([r["output"] for r in results])

# find the proportionality constant: output ≈ k * (a+b)^2
# use least squares fit
valid = sums_sq > 0
if np.any(valid):
    k = np.sum(outputs[valid] * sums_sq[valid]) / np.sum(sums_sq[valid] ** 2)
    predicted = k * sums_sq
    residuals = outputs - predicted
    rel_errors = np.abs(residuals / predicted) * 100
    rel_errors = np.where(predicted > 0, rel_errors, 0)
else:
    k = 0
    predicted = np.zeros_like(outputs)
    rel_errors = np.zeros_like(outputs)

print(f"{'A':<8}{'B':<8}{'A+B':<8}{'output':<14}{'predicted':<14}{'error %':<10}")
print("-" * 60)

for i, r in enumerate(results):
    print(f"{r['a']:<8.1f}{r['b']:<8.1f}{r['sum']:<8.1f}"
          f"{r['output']:<14.4f}{predicted[i]:<14.4f}{rel_errors[i]:<10.2f}")

avg_error = np.mean(rel_errors[predicted > 0])
max_error = np.max(rel_errors[predicted > 0]) if np.any(predicted > 0) else 0

print(f"\nproportionality constant k = {k:.6f}")
print(f"avg relative error: {avg_error:.2f}%")
print(f"max relative error: {max_error:.2f}%")

if avg_error < 5:
    print(f"\n>>> PASS — output scales predictably with (A+B)²")
    print(f"    the structure is performing addition.")
elif avg_error < 15:
    print(f"\n>>> PARTIAL — relationship exists but noisy")
else:
    print(f"\n>>> FAIL — no clear relationship between input sum and output")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# plot 1: output vs (A+B)^2
axes[0].scatter(sums_sq, outputs, color="#1a3a5c", s=60, zorder=3)
if k > 0:
    fit_x = np.linspace(0, max(sums_sq) * 1.1, 100)
    axes[0].plot(fit_x, k * fit_x, 'r--', alpha=0.5, label=f"fit: y = {k:.4f}x")
axes[0].set_xlabel("(A + B)²")
axes[0].set_ylabel("output power")
axes[0].set_title("output vs (A+B)² — linear = addition works")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# plot 2: relative error per test
axes[1].bar(range(len(results)), rel_errors, color="#2d7d46", alpha=0.7)
axes[1].axhline(y=5, color="red", linestyle="--", alpha=0.5, label="5% threshold")
axes[1].set_xlabel("test pair")
axes[1].set_ylabel("relative error (%)")
axes[1].set_title("prediction error per input pair")
axes[1].set_xticks(range(len(results)))
axes[1].set_xticklabels([f"({r['a']},{r['b']})" for r in results],
                         rotation=45, fontsize=7)
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("results/v1_results.png", dpi=150, bbox_inches="tight")
print(f"\nsaved: results/v1_results.png")