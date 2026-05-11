"""
prism-theory / test 01 — decomposition (v3)

v1: fixed index, no separation. v2: dispersion works but both wavelengths
land at center — prism isn't bending enough.

v3 changes:
- wedge prism instead of symmetric triangle. the input face is angled
  so light hits it at a steep angle, maximizing refraction.
- beam enters from the left and hits a tilted face. different wavelengths
  refract at different angles (Snell's law) and diverge as they travel
  to the detectors.
- even stronger dispersion (sigma 3.0)
- detectors arranged in a vertical array to catch wherever light lands
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

# ============================================================
# WEDGE PRISM
# ============================================================

glass = mp.Medium(
    epsilon=1.5,
    E_susceptibilities=[
        mp.LorentzianSusceptibility(
            frequency=3.0,
            gamma=0.1,
            sigma=3.0,  # cranked up again
        )
    ],
)

# wedge shape — like a doorstop
# the left face is angled so the beam hits it at ~30-40 degrees
# the right face is vertical so light exits cleanly
prism_vertices = [
    mp.Vector3(-4, -6),   # bottom left
    mp.Vector3(2, -6),    # bottom right
    mp.Vector3(2, 6),     # top right
    mp.Vector3(-4, 2),    # top left (offset down to create the wedge angle)
]

prism_geometry = [
    mp.Prism(
        vertices=prism_vertices,
        height=mp.inf,
        material=glass,
        center=mp.Vector3(-3, 0),
    )
]

# ============================================================
# SOURCE — aimed at the angled face
# ============================================================

source_x = -20

sources = [
    mp.Source(
        mp.GaussianSource(frequency=freq_1, fwidth=0.1),
        component=mp.Ez,
        center=mp.Vector3(source_x, -1),
        size=mp.Vector3(0, 2),
    ),
    mp.Source(
        mp.GaussianSource(frequency=freq_2, fwidth=0.1),
        component=mp.Ez,
        center=mp.Vector3(source_x, -1),
        size=mp.Vector3(0, 2),
    ),
]

# ============================================================
# DETECTORS — 5 detectors in a vertical array to find where light goes
# ============================================================

detector_x = 18
nfreq = 200

detector_positions = [-8, -4, 0, 4, 8]
detector_labels = ["y=-8", "y=-4", "y=0", "y=+4", "y=+8"]

det_regions = []
flux_monitors = []

# ============================================================
# RUN
# ============================================================

pml = [mp.PML(thickness=2)]

sim = mp.Simulation(
    cell_size=mp.Vector3(sx, sy),
    geometry=prism_geometry,
    sources=sources,
    boundary_layers=pml,
    resolution=resolution,
)

for y_pos in detector_positions:
    fm = sim.add_flux(
        (freq_1 + freq_2) / 2, freq_1 - freq_2, nfreq,
        mp.FluxRegion(center=mp.Vector3(detector_x, y_pos), size=mp.Vector3(0, 3)),
    )
    flux_monitors.append(fm)

print("test 01 v3 — wedge prism, 5 detectors, sigma=3.0")
print(f"wavelengths: {wavelength_1} μm, {wavelength_2} μm")
print("running...\n")

sim.run(until=120)

# ============================================================
# RESULTS
# ============================================================

freqs = np.array(mp.get_flux_freqs(flux_monitors[0]))
wavelengths_arr = 1 / freqs

idx1 = np.argmin(np.abs(wavelengths_arr - wavelength_1))
idx2 = np.argmin(np.abs(wavelengths_arr - wavelength_2))

all_flux = []
for fm in flux_monitors:
    all_flux.append(np.array(mp.get_fluxes(fm)))

print(f"\n{'='*50}")
print(f"RESULTS")
print(f"{'='*50}")

dets_w1 = []
dets_w2 = []

for i, label in enumerate(detector_labels):
    fw1 = all_flux[i][idx1]
    fw2 = all_flux[i][idx2]
    dets_w1.append(fw1)
    dets_w2.append(fw2)
    print(f"\n{label}:")
    print(f"  λ={wavelength_1}μm: {fw1:.4f}")
    print(f"  λ={wavelength_2}μm: {fw2:.4f}")

peak_w1 = detector_labels[np.argmax(dets_w1)]
peak_w2 = detector_labels[np.argmax(dets_w2)]

print(f"\nwavelength 1 peaks at: {peak_w1}")
print(f"wavelength 2 peaks at: {peak_w2}")

if peak_w1 != peak_w2:
    print(f"\n>>> PASS — wavelengths separated to different detectors")
else:
    print(f"\n>>> FAIL — still landing at same detector")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(2, 1, figsize=(10, 8))

colors = ["#1a3a5c", "#2d7d46", "#666666", "#c44e52", "#8e6bb0"]
for i, label in enumerate(detector_labels):
    axes[0].plot(wavelengths_arr, all_flux[i], label=label, color=colors[i])

axes[0].axvline(x=wavelength_1, color="gray", linestyle="--", alpha=0.5)
axes[0].axvline(x=wavelength_2, color="gray", linestyle="--", alpha=0.5)
axes[0].set_xlabel("wavelength (μm)")
axes[0].set_ylabel("flux (power)")
axes[0].set_title("v3: wedge prism — light intensity at 5 detectors")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

x = np.arange(5)
width = 0.35
axes[1].bar(x - width/2, dets_w1, width, label=f"λ = {wavelength_1} μm", color="#1a3a5c")
axes[1].bar(x + width/2, dets_w2, width, label=f"λ = {wavelength_2} μm", color="#c44e52")
axes[1].set_xticks(x)
axes[1].set_xticklabels(detector_labels)
axes[1].set_ylabel("flux (power)")
axes[1].set_title("v3: flux at target wavelengths by detector position")
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("01_decomposition_v3_results.png", dpi=150, bbox_inches="tight")
print("\nsaved: 01_decomposition_v3_results.png")