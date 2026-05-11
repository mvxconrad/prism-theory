"""
prism-theory / 02_computation / test 01 — addition (v2: symmetric)

v1 showed addition works for equal inputs (2.91% error) but the
Y-junction was asymmetric, causing unequal inputs to give skewed
results. (2.0,1.0) and (1.0,2.0) should give the same output
but didn't.

v2 fixes this with a properly symmetric geometry:
- both arms are identical length and angle
- arms are mirrored perfectly about the center axis
- merge region is a smooth taper, not a blocky join
"""

import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# PARAMETERS
# ============================================================

sx = 40
sy = 16
resolution = 20

wavelength = 1.0
freq = 1 / wavelength
nfreq = 100

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
    symmetric Y-junction: two arms at equal angles merging
    into a single output waveguide.

    geometry is built from polygons to ensure perfect mirror
    symmetry about y=0.
    """

    guide_material = mp.Medium(epsilon=12)
    wg_width = 0.6
    arm_sep = 3.0       # vertical separation between input arms
    arm_length = 10.0    # length of each input arm
    taper_length = 6.0   # length of merge region
    output_length = 10.0 # length of output waveguide
    half_sep = arm_sep / 2

    geometry = []

    # top input arm — horizontal waveguide at y = +half_sep
    geometry.append(mp.Block(
        center=mp.Vector3(-10, half_sep),
        size=mp.Vector3(arm_length, wg_width),
        material=guide_material,
    ))

    # bottom input arm — horizontal waveguide at y = -half_sep
    geometry.append(mp.Block(
        center=mp.Vector3(-10, -half_sep),
        size=mp.Vector3(arm_length, wg_width),
        material=guide_material,
    ))

    # taper / merge region — a trapezoid that narrows from both arms
    # down to the output waveguide width
    # built as a prism (polygon) for exact shape control
    taper_vertices = [
        mp.Vector3(-5, half_sep + wg_width/2),    # top left
        mp.Vector3(-5, -(half_sep + wg_width/2)), # bottom left
        mp.Vector3(-5 + taper_length, wg_width/2),  # top right (narrowed)
        mp.Vector3(-5 + taper_length, -wg_width/2), # bottom right (narrowed)
    ]
    # meep Prism needs vertices in order, so rearrange
    geometry.append(mp.Prism(
        vertices=[
            mp.Vector3(-5, half_sep + wg_width/2),
            mp.Vector3(-5 + taper_length, wg_width/2),
            mp.Vector3(-5 + taper_length, -wg_width/2),
            mp.Vector3(-5, -(half_sep + wg_width/2)),
        ],
        height=mp.inf,
        material=guide_material,
    ))

    # output waveguide — centered at y=0
    geometry.append(mp.Block(
        center=mp.Vector3(-5 + taper_length + output_length/2, 0),
        size=mp.Vector3(output_length, wg_width),
        material=guide_material,
    ))

    # sources in each arm
    sources = []
    if amp_a > 0:
        sources.append(mp.Source(
            mp.GaussianSource(frequency=freq, fwidth=0.2),
            component=mp.Ez,
            center=mp.Vector3(-16, half_sep),
            size=mp.Vector3(0, wg_width),
            amplitude=amp_a,
        ))
    if amp_b > 0:
        sources.append(mp.Source(
            mp.GaussianSource(frequency=freq, fwidth=0.2),
            component=mp.Ez,
            center=mp.Vector3(-16, -half_sep),
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

    # detector at the output end
    flux_mon = sim.add_flux(
        freq, 0.5, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(14, 0),
            size=mp.Vector3(0, wg_width * 2),
        ),
    )

    sim.run(until=100)

    flux_vals = mp.get_fluxes(flux_mon)
    total_flux = sum(f for f in flux_vals if f > 0)

    sim.reset_meep()
    return total_flux


# ============================================================
# RUN
# ============================================================

print("test 01 v2 — addition (symmetric Y-junction)")
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

sums = np.array([r["sum"] for r in results])
sums_sq = sums ** 2
outputs = np.array([r["output"] for r in results])

valid = sums_sq > 0
if np.any(valid):
    k = np.sum(outputs[valid] * sums_sq[valid]) / np.sum(sums_sq[valid] ** 2)
    predicted = k * sums_sq
    residuals = outputs - predicted
    rel_errors = np.where(predicted > 0, np.abs(residuals / predicted) * 100, 0)
else:
    k = 0
    predicted = np.zeros_like(outputs)
    rel_errors = np.zeros_like(outputs)

print(f"{'A':<8}{'B':<8}{'A+B':<8}{'output':<14}{'predicted':<14}{'error %':<10}")
print("-" * 60)

for i, r in enumerate(results):
    print(f"{r['a']:<8.1f}{r['b']:<8.1f}{r['sum']:<8.1f}"
          f"{r['output']:<14.4f}{predicted[i]:<14.4f}{rel_errors[i]:<10.2f}")

# symmetry check: do (A,B) and (B,A) give same output?
print(f"\nSYMMETRY CHECK:")
sym_pairs = [(3,4), (5,8)]  # indices of (2.0,1.0)/(1.0,2.0) and (3.0,1.0)/(1.0,3.0)
for i1, i2 in sym_pairs:
    r1 = results[i1]
    r2 = results[i2]
    diff = abs(r1["output"] - r2["output"])
    avg = (r1["output"] + r2["output"]) / 2
    sym_err = (diff / avg * 100) if avg > 0 else 0
    print(f"  ({r1['a']},{r1['b']}) = {r1['output']:.4f} vs "
          f"({r2['a']},{r2['b']}) = {r2['output']:.4f} "
          f"diff = {sym_err:.2f}%")

avg_error = np.mean(rel_errors[predicted > 0])
max_error = np.max(rel_errors[predicted > 0]) if np.any(predicted > 0) else 0

print(f"\navg relative error: {avg_error:.2f}%")
print(f"max relative error: {max_error:.2f}%")

if avg_error < 5:
    print(f"\n>>> PASS — output scales predictably with (A+B)²")
    print(f"    the structure is performing addition.")
elif avg_error < 15:
    print(f"\n>>> PARTIAL — relationship exists but needs work")
else:
    print(f"\n>>> FAIL — no clear relationship")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].scatter(sums_sq, outputs, color="#1a3a5c", s=60, zorder=3)
if k > 0:
    fit_x = np.linspace(0, max(sums_sq) * 1.1, 100)
    axes[0].plot(fit_x, k * fit_x, 'r--', alpha=0.5, label=f"fit: y = {k:.4f}x")
axes[0].set_xlabel("(A + B)²")
axes[0].set_ylabel("output power")
axes[0].set_title("v2: output vs (A+B)² — linear = addition works")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

colors_bar = ["#2d7d46" if e < 5 else "#c44e52" for e in rel_errors]
axes[1].bar(range(len(results)), rel_errors, color=colors_bar, alpha=0.7)
axes[1].axhline(y=5, color="red", linestyle="--", alpha=0.5, label="5% threshold")
axes[1].set_xlabel("test pair")
axes[1].set_ylabel("relative error (%)")
axes[1].set_title("v2: prediction error (green < 5%)")
axes[1].set_xticks(range(len(results)))
axes[1].set_xticklabels([f"({r['a']},{r['b']})" for r in results],
                         rotation=45, fontsize=7)
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("results/v2_results.png", dpi=150, bbox_inches="tight")
print(f"\nsaved: results/v2_results.png")