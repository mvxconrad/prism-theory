"""
prism-theory / test 01 — decomposition (v2)

second attempt. v1 confirmed dispersion works but separation was weak.
changes from v1:
- steeper prism angle (narrower triangle = sharper refraction)
- detectors spread further apart (y=+6 and y=-6)
- stronger dispersion (sigma 1.2 -> 2.0)
- larger sim space so beams have room to diverge
- source aimed slightly downward to hit prism face at better angle
"""

import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# PARAMETERS
# ============================================================

sx = 40   # wider sim space
sy = 30   # taller sim space
resolution = 20

wavelength_1 = 0.8
wavelength_2 = 1.2

freq_1 = 1 / wavelength_1
freq_2 = 1 / wavelength_2

# ============================================================
# PRISM — steeper angle this time
# ============================================================

glass = mp.Medium(
    epsilon=1.5,
    E_susceptibilities=[
        mp.LorentzianSusceptibility(
            frequency=3.0,
            gamma=0.1,
            sigma=2.0,  # bumped from 1.2 — stronger dispersion
        )
    ],
)

# narrower, taller triangle = steeper faces = more bending
prism_vertices = [
    mp.Vector3(-2, -5),   # bottom left
    mp.Vector3(2, -5),    # bottom right
    mp.Vector3(0, 5),     # top
]

prism_geometry = [
    mp.Prism(
        vertices=prism_vertices,
        height=mp.inf,
        material=glass,
        center=mp.Vector3(-2, 0),  # shifted left so light hits the face
    )
]

# ============================================================
# SOURCE
# ============================================================

source_x = -16

sources = [
    mp.Source(
        mp.GaussianSource(frequency=freq_1, fwidth=0.1),
        component=mp.Ez,
        center=mp.Vector3(source_x, 0),
        size=mp.Vector3(0, 3),
    ),
    mp.Source(
        mp.GaussianSource(frequency=freq_2, fwidth=0.1),
        component=mp.Ez,
        center=mp.Vector3(source_x, 0),
        size=mp.Vector3(0, 3),
    ),
]

# ============================================================
# DETECTORS — spread further apart
# ============================================================

detector_x = 14
nfreq = 200

det1_center = mp.Vector3(detector_x, 6)   # upper — was y=3
det1_size = mp.Vector3(0, 3)

det2_center = mp.Vector3(detector_x, 0)   # center
det2_size = mp.Vector3(0, 3)

det3_center = mp.Vector3(detector_x, -6)  # lower — was y=-3
det3_size = mp.Vector3(0, 3)

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

flux1 = sim.add_flux(
    (freq_1 + freq_2) / 2, freq_1 - freq_2, nfreq,
    mp.FluxRegion(center=det1_center, size=det1_size),
)
flux2 = sim.add_flux(
    (freq_1 + freq_2) / 2, freq_1 - freq_2, nfreq,
    mp.FluxRegion(center=det2_center, size=det2_size),
)
flux3 = sim.add_flux(
    (freq_1 + freq_2) / 2, freq_1 - freq_2, nfreq,
    mp.FluxRegion(center=det3_center, size=det3_size),
)

print("test 01 v2 — steeper prism, wider detectors, stronger dispersion")
print(f"wavelengths: {wavelength_1} μm, {wavelength_2} μm")
print(f"dispersion sigma: 2.0 (was 1.2)")
print(f"detectors at y = +6, 0, -6 (was +3, -3)")
print("running...\n")

sim.run(until=100)  # longer run time for bigger space

# ============================================================
# RESULTS
# ============================================================

freqs = np.array(mp.get_flux_freqs(flux1))
f1_vals = np.array(mp.get_fluxes(flux1))
f2_vals = np.array(mp.get_fluxes(flux2))
f3_vals = np.array(mp.get_fluxes(flux3))
wavelengths = 1 / freqs

# find flux at target wavelengths
idx1 = np.argmin(np.abs(wavelengths - wavelength_1))
idx2 = np.argmin(np.abs(wavelengths - wavelength_2))

print(f"\n{'='*50}")
print(f"RESULTS")
print(f"{'='*50}")

print(f"\nwavelength 1 ({wavelength_1} μm):")
print(f"  upper (y=+6):  {f1_vals[idx1]:.4f}")
print(f"  center (y=0):  {f2_vals[idx1]:.4f}")
print(f"  lower (y=-6):  {f3_vals[idx1]:.4f}")

print(f"\nwavelength 2 ({wavelength_2} μm):")
print(f"  upper (y=+6):  {f1_vals[idx2]:.4f}")
print(f"  center (y=0):  {f2_vals[idx2]:.4f}")
print(f"  lower (y=-6):  {f3_vals[idx2]:.4f}")

# which detector gets the most of each wavelength?
dets_w1 = [f1_vals[idx1], f2_vals[idx1], f3_vals[idx1]]
dets_w2 = [f1_vals[idx2], f2_vals[idx2], f3_vals[idx2]]
labels = ["upper", "center", "lower"]

peak_w1 = labels[np.argmax(dets_w1)]
peak_w2 = labels[np.argmax(dets_w2)]

print(f"\nwavelength 1 peaks at: {peak_w1} detector")
print(f"wavelength 2 peaks at: {peak_w2} detector")

if peak_w1 != peak_w2:
    print(f"\n>>> PASS — each wavelength peaks at a different detector")
else:
    print(f"\n>>> FAIL — both wavelengths peak at the same detector")
    print(f"    need more dispersion or different geometry")

# ============================================================
# PLOT
# ============================================================

fig, axes = plt.subplots(2, 1, figsize=(10, 8))

axes[0].plot(wavelengths, f1_vals, label="upper (y=+6)", color="#1a3a5c")
axes[0].plot(wavelengths, f2_vals, label="center (y=0)", color="#2d7d46")
axes[0].plot(wavelengths, f3_vals, label="lower (y=-6)", color="#c44e52")
axes[0].axvline(x=wavelength_1, color="gray", linestyle="--", alpha=0.5)
axes[0].axvline(x=wavelength_2, color="gray", linestyle="--", alpha=0.5)
axes[0].set_xlabel("wavelength (μm)")
axes[0].set_ylabel("flux (power)")
axes[0].set_title("v2: light intensity at each detector")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# bar chart comparing detectors at each target wavelength
x = np.arange(3)
width = 0.35
axes[1].bar(x - width/2, dets_w1, width, label=f"λ = {wavelength_1} μm", color="#1a3a5c")
axes[1].bar(x + width/2, dets_w2, width, label=f"λ = {wavelength_2} μm", color="#c44e52")
axes[1].set_xticks(x)
axes[1].set_xticklabels(["upper (y=+6)", "center (y=0)", "lower (y=-6)"])
axes[1].set_ylabel("flux (power)")
axes[1].set_title("v2: flux at target wavelengths by detector")
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("01_decomposition_v2_results.png", dpi=150, bbox_inches="tight")
print("\nsaved: 01_decomposition_v2_results.png")