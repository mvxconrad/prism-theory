"""
prism-theory / 03_scalability / test 01 — chain (v1)

the big test: can we chain two operations together?

step 1: two beams (different wavelengths) enter a Y-junction and add
step 2: the combined beam hits a prism and gets decomposed
step 3: we read the decomposed output at detectors

if the detectors can tell us what the original inputs were after
the signal passed through BOTH structures, we've proven operations
can chain. light went through two physical transformations without
ever becoming electricity.

this is the difference between a calculator and a computer.
"""

import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# PARAMETERS
# ============================================================

sx = 70   # long sim space — need room for both structures
sy = 20
resolution = 20

wavelength_1 = 0.8
wavelength_2 = 1.2
freq_1 = 1 / wavelength_1
freq_2 = 1 / wavelength_2
nfreq = 200

# test input pairs
test_pairs = [
    (1.0, 1.0),
    (2.0, 1.0),
    (1.0, 2.0),
    (1.5, 1.5),
    (2.0, 2.0),
    (2.5, 1.5),
    (3.0, 2.0),
    (1.5, 2.5),
]


def run_chain(amp1, amp2):
    """
    full chain: Y-junction merge -> prism decomposition

    layout (left to right):
    [source λ1] --arm1--\
                         >-- [merged waveguide] -- [prism] -- [detectors]
    [source λ2] --arm2--/

    the two wavelengths enter from separate arms, merge in the
    Y-junction, travel as one beam into the prism, and get
    separated back out to different detector positions.
    """

    # materials
    guide_material = mp.Medium(epsilon=12)  # silicon-like waveguide
    glass = mp.Medium(
        epsilon=1.5,
        E_susceptibilities=[
            mp.LorentzianSusceptibility(frequency=3.0, gamma=0.1, sigma=3.0)
        ],
    )

    wg_width = 0.6
    half_sep = 1.5

    geometry = []

    # --- Y-JUNCTION (left side) ---

    # top input arm
    geometry.append(mp.Block(
        center=mp.Vector3(-28, half_sep),
        size=mp.Vector3(10, wg_width),
        material=guide_material,
    ))

    # bottom input arm
    geometry.append(mp.Block(
        center=mp.Vector3(-28, -half_sep),
        size=mp.Vector3(10, wg_width),
        material=guide_material,
    ))

    # taper merge
    geometry.append(mp.Prism(
        vertices=[
            mp.Vector3(-23, half_sep + wg_width/2),
            mp.Vector3(-19, wg_width/2),
            mp.Vector3(-19, -wg_width/2),
            mp.Vector3(-23, -(half_sep + wg_width/2)),
        ],
        height=mp.inf,
        material=guide_material,
    ))

    # merged waveguide connecting Y-junction to prism
    geometry.append(mp.Block(
        center=mp.Vector3(-12, 0),
        size=mp.Vector3(14, wg_width),
        material=guide_material,
    ))

    # --- PRISM (right side) ---

    geometry.append(mp.Prism(
        vertices=[
            mp.Vector3(-4, -6),
            mp.Vector3(2, -6),
            mp.Vector3(2, 6),
            mp.Vector3(-4, 2),
        ],
        height=mp.inf,
        material=glass,
        center=mp.Vector3(5, 0),
    ))

    # --- SOURCES ---

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

    # --- DETECTORS (after prism) ---

    det_x = 25
    det_positions = [-6, -3, 0, 3, 6]
    det_labels = ["y=-6", "y=-3", "y=0", "y=+3", "y=+6"]

    flux_monitors = []
    for y_pos in det_positions:
        fm = sim.add_flux(
            (freq_1 + freq_2) / 2, freq_1 - freq_2, nfreq,
            mp.FluxRegion(
                center=mp.Vector3(det_x, y_pos),
                size=mp.Vector3(0, 3),
            ),
        )
        flux_monitors.append(fm)

    sim.run(until=150)  # longer run, signal travels further

    # get flux at target wavelengths
    freqs = np.array(mp.get_flux_freqs(flux_monitors[0]))
    wavelengths = 1 / freqs
    idx1 = np.argmin(np.abs(wavelengths - wavelength_1))
    idx2 = np.argmin(np.abs(wavelengths - wavelength_2))

    results = {}
    for i, label in enumerate(det_labels):
        flux_vals = np.array(mp.get_fluxes(flux_monitors[i]))
        results[label] = {
            "w1": flux_vals[idx1],
            "w2": flux_vals[idx2],
        }

    sim.reset_meep()
    return results, det_labels


# ============================================================
# RUN
# ============================================================

print("test 01 — chain (Y-junction -> prism)")
print("="*50)
print(f"testing {len(test_pairs)} input pairs\n")

all_results = []

for i, (a1, a2) in enumerate(test_pairs):
    print(f"  pair {i+1}/{len(test_pairs)}: λ1={a1:.1f}, λ2={a2:.1f} ... ", end="")
    result, labels = run_chain(a1, a2)
    all_results.append({"a1": a1, "a2": a2, "detectors": result})
    print("done")

# ============================================================
# ANALYZE
# ============================================================

print(f"\n{'='*50}")
print("RESULTS")
print(f"{'='*50}\n")

# for each test pair, show where each wavelength ended up
for i, r in enumerate(all_results):
    print(f"\ninput: λ1={r['a1']:.1f}, λ2={r['a2']:.1f}")
    print(f"  {'detector':<10}{'λ1 flux':<14}{'λ2 flux':<14}{'ratio λ2/λ1'}")
    print(f"  {'-'*46}")
    for label in labels:
        w1 = r["detectors"][label]["w1"]
        w2 = r["detectors"][label]["w2"]
        ratio = w2 / w1 if w1 > 0.001 else float('nan')
        print(f"  {label:<10}{w1:<14.6f}{w2:<14.6f}{ratio:<14.4f}" 
              if not np.isnan(ratio) else
              f"  {label:<10}{w1:<14.6f}{w2:<14.6f}{'N/A':<14}")

# key question: do the detector readings scale with input amplitudes?
# if we double λ1 input, does λ1 flux at its peak detector also scale?
print(f"\n{'='*50}")
print("SCALING CHECK")
print(f"{'='*50}\n")

# find which detector has most λ1 and most λ2 for reference pair (1.0,1.0)
ref = all_results[0]["detectors"]
w1_fluxes = {l: ref[l]["w1"] for l in labels}
w2_fluxes = {l: ref[l]["w2"] for l in labels}
peak_det_w1 = max(w1_fluxes, key=w1_fluxes.get)
peak_det_w2 = max(w2_fluxes, key=w2_fluxes.get)

print(f"λ1 peaks at: {peak_det_w1}")
print(f"λ2 peaks at: {peak_det_w2}")

if peak_det_w1 != peak_det_w2:
    print("wavelengths separated to different detectors after chain!")

    # check if flux scales with input amplitude
    print(f"\n{'input':<16}{'λ1 at ' + peak_det_w1:<16}{'λ2 at ' + peak_det_w2:<16}")
    print("-" * 48)

    ref_w1 = all_results[0]["detectors"][peak_det_w1]["w1"]
    ref_w2 = all_results[0]["detectors"][peak_det_w2]["w2"]

    consistent = True
    for r in all_results:
        flux_w1 = r["detectors"][peak_det_w1]["w1"]
        flux_w2 = r["detectors"][peak_det_w2]["w2"]

        # expected scaling: flux proportional to amplitude^2
        expected_w1 = ref_w1 * (r["a1"] ** 2)
        expected_w2 = ref_w2 * (r["a2"] ** 2)

        err_w1 = abs(flux_w1 - expected_w1) / expected_w1 * 100 if expected_w1 > 0 else 0
        err_w2 = abs(flux_w2 - expected_w2) / expected_w2 * 100 if expected_w2 > 0 else 0

        print(f"({r['a1']},{r['a2']}){'':<8}"
              f"{flux_w1:<16.6f}{flux_w2:<16.6f}"
              f"  err: {err_w1:.1f}%, {err_w2:.1f}%")

        if err_w1 > 20 or err_w2 > 20:
            consistent = False

    if consistent:
        print(f"\n>>> PASS — signals chain through both structures")
        print(f"    addition + decomposition works in series.")
    else:
        print(f"\n>>> PARTIAL — signals get through but scaling is off")
else:
    print("wavelengths not separated — prism isn't working in the chain")
    print(f"\n>>> FAIL")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# plot 1: for each test pair, show λ1 and λ2 flux at their peak detectors
a1_inputs = [r["a1"] for r in all_results]
a2_inputs = [r["a2"] for r in all_results]
w1_at_peak = [r["detectors"][peak_det_w1]["w1"] for r in all_results]
w2_at_peak = [r["detectors"][peak_det_w2]["w2"] for r in all_results]

x = np.arange(len(all_results))
width = 0.35
axes[0].bar(x - width/2, w1_at_peak, width, label=f"λ1 at {peak_det_w1}", color="#1a3a5c")
axes[0].bar(x + width/2, w2_at_peak, width, label=f"λ2 at {peak_det_w2}", color="#c44e52")
axes[0].set_xticks(x)
axes[0].set_xticklabels([f"({r['a1']},{r['a2']})" for r in all_results],
                         rotation=45, fontsize=7)
axes[0].set_ylabel("flux at peak detector")
axes[0].set_title("output after full chain (Y-junction -> prism)")
axes[0].legend()
axes[0].grid(True, alpha=0.3, axis="y")

# plot 2: input amplitude vs output flux (should be quadratic)
axes[1].scatter([r["a1"]**2 for r in all_results], w1_at_peak,
               color="#1a3a5c", s=60, label="λ1")
axes[1].scatter([r["a2"]**2 for r in all_results], w2_at_peak,
               color="#c44e52", s=60, label="λ2")
axes[1].set_xlabel("input amplitude²")
axes[1].set_ylabel("output flux at peak detector")
axes[1].set_title("input² vs output (linear = signal preserved)")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("results/v1_results.png", dpi=150, bbox_inches="tight")
print(f"\nsaved: results/v1_results.png")