"""
prism-theory / test 01 — decomposition

can a prism structure separate two wavelengths of light
that enter as a single beam?

what this does:
- creates a 2D simulation space (think of it as a top-down view)
- places a triangular prism made of glass in the middle
- fires a beam containing two different wavelengths at the prism
- measures what comes out the other side at two different detector positions
- if wavelength A is strong at detector 1 and weak at detector 2,
  and wavelength B is the opposite, the prism separated them.

key concepts if you've never done this before:
- wavelength = color of light. shorter = bluer, longer = redder
- refractive index = how much a material slows down and bends light.
  glass is ~1.5, air is 1.0. different wavelengths bend different amounts.
  that's literally why prisms work.
- FDTD = finite-difference time-domain. it simulates electromagnetic waves
  by stepping through time in tiny increments and calculating the fields
  at every point in space. brute force but accurate.
- "resolution" = how many pixels per unit length. higher = more accurate
  but slower.
"""

import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# SIMULATION PARAMETERS
# ============================================================

# simulation space (in microns — 1 micron = 0.001 mm)
# we're working at this scale because that's where light
# wavelengths live (~0.4 to 0.7 microns for visible light)
sx = 30  # width of simulation space
sy = 20  # height of simulation space
resolution = 20  # pixels per micron (higher = more accurate, slower)

# the two wavelengths we want to separate
# using near-infrared because MEEP works well there
# lambda1 and lambda2 in microns
wavelength_1 = 0.8  # "red" channel
wavelength_2 = 1.2  # "infrared" channel

# convert wavelengths to frequencies (MEEP uses frequency, not wavelength)
# frequency = 1 / wavelength in MEEP's units
freq_1 = 1 / wavelength_1  # 1.25
freq_2 = 1 / wavelength_2  # 0.833

# prism properties
# UPDATED: using a dispersive material model instead of fixed index
# real glass has a refractive index that changes with wavelength.
# shorter wavelengths (bluer) have higher refractive index = bend more.
# longer wavelengths (redder) have lower refractive index = bend less.
# that difference is what makes prisms separate colors.
#
# MEEP models dispersion using Lorentzian resonances.
# we set a base epsilon (dielectric constant = n^2) and add a
# resonance that makes the refractive index vary across our
# frequency range. this mimics how real glass (like BK7) behaves.
#
# epsilon = n^2, so n=1.5 means epsilon=2.25 as our baseline.
# the Lorentzian adds frequency-dependent variation on top of that.

# ============================================================
# BUILD THE PRISM
# ============================================================

# dispersive glass material
# - epsilon at infinite frequency (background permittivity)
# - a Lorentzian susceptibility adds the wavelength-dependent part
# - sigma = strength of the resonance (how much index varies)
# - frequency = resonance frequency (set far from our wavelengths
#   so we're in the tail of the resonance, which gives smooth dispersion)
# - gamma = damping (how broad the resonance is, keep small for low loss)
glass = mp.Medium(
    epsilon=1.5,
    E_susceptibilities=[
        mp.LorentzianSusceptibility(
            frequency=3.0,   # resonance far above our frequencies (UV region)
            gamma=0.1,       # low damping = low absorption
            sigma=1.2,       # strength — controls how much n varies with wavelength
        )
    ],
)

# triangular prism — three vertices forming a triangle
# positioned in the center-left of the simulation
prism_vertices = [
    mp.Vector3(-3, -4),   # bottom left
    mp.Vector3(3, -4),    # bottom right
    mp.Vector3(0, 4),     # top
]

prism_geometry = [
    mp.Prism(
        vertices=prism_vertices,
        height=mp.inf,  # infinite in z (it's a 2D sim, this just means "fill the z axis")
        material=glass,
        center=mp.Vector3(0, 0),
    )
]

# ============================================================
# LIGHT SOURCE
# ============================================================

# a gaussian source emits a pulse that contains a range of frequencies
# we'll use two sources at the same position, one for each wavelength
# they combine into a single beam — our "white light"

source_x = -12  # left side of the simulation

sources = [
    mp.Source(
        mp.GaussianSource(frequency=freq_1, fwidth=0.1),
        component=mp.Ez,  # polarization of the light
        center=mp.Vector3(source_x, 0),
        size=mp.Vector3(0, 4),  # source is a line, not a point
    ),
    mp.Source(
        mp.GaussianSource(frequency=freq_2, fwidth=0.1),
        component=mp.Ez,
        center=mp.Vector3(source_x, 0),
        size=mp.Vector3(0, 4),
    ),
]

# ============================================================
# DETECTORS
# ============================================================

# flux monitors — they measure how much light at each frequency
# passes through a given line in space
# we place two detectors at different vertical positions on the
# right side of the prism. if the prism works, wavelength_1 should
# be stronger at one detector and wavelength_2 at the other.

detector_x = 10  # right side of simulation

# number of frequency points to measure across our range
nfreq = 200

# detector 1 — upper position (expecting one wavelength to arrive here)
det1_center = mp.Vector3(detector_x, 3)
det1_size = mp.Vector3(0, 2)

# detector 2 — lower position (expecting the other wavelength here)
det2_center = mp.Vector3(detector_x, -3)
det2_size = mp.Vector3(0, 2)

# ============================================================
# SET UP AND RUN THE SIMULATION
# ============================================================

# absorbing boundaries — without these, light would bounce off the
# edges of the simulation and mess everything up. PML = perfectly
# matched layer, it absorbs outgoing waves.
pml = [mp.PML(thickness=2)]

sim = mp.Simulation(
    cell_size=mp.Vector3(sx, sy),
    geometry=prism_geometry,
    sources=sources,
    boundary_layers=pml,
    resolution=resolution,
)

# add the flux monitors (detectors)
flux1 = sim.add_flux(
    (freq_1 + freq_2) / 2,  # center frequency
    freq_1 - freq_2,         # frequency range
    nfreq,                    # number of points
    mp.FluxRegion(center=det1_center, size=det1_size),
)

flux2 = sim.add_flux(
    (freq_1 + freq_2) / 2,
    freq_1 - freq_2,
    nfreq,
    mp.FluxRegion(center=det2_center, size=det2_size),
)

print("starting simulation...")
print(f"wavelength 1: {wavelength_1} μm (freq {freq_1:.3f})")
print(f"wavelength 2: {wavelength_2} μm (freq {freq_2:.3f})")
print(f"prism material: dispersive glass (Lorentzian model)")
print(f"resolution: {resolution} pixels/μm")
print(f"this might take a minute...\n")

# run until the pulse has passed through
# the time is in MEEP units (roughly: distance / speed of light)
sim.run(until=80)

print("\nsimulation complete. analyzing results...\n")

# ============================================================
# ANALYZE RESULTS
# ============================================================

# get the flux data from both detectors
freqs = np.array(mp.get_flux_freqs(flux1))
flux1_data = np.array(sim.get_flux_data(flux1))
flux2_data = np.array(sim.get_flux_data(flux2))

# get the actual flux values (power through each detector at each frequency)
flux1_values = np.array(mp.get_fluxes(flux1))
flux2_values = np.array(mp.get_fluxes(flux2))

# convert frequencies back to wavelengths for readability
wavelengths = 1 / freqs

# ============================================================
# PLOT RESULTS
# ============================================================

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# plot 1: flux spectrum at each detector
ax1.plot(wavelengths, flux1_values, label="detector 1 (upper, y=+3)", color="#1a3a5c")
ax1.plot(wavelengths, flux2_values, label="detector 2 (lower, y=-3)", color="#c44e52")
ax1.set_xlabel("wavelength (μm)")
ax1.set_ylabel("flux (power)")
ax1.set_title("light intensity at each detector vs wavelength")
ax1.legend()
ax1.grid(True, alpha=0.3)

# mark our two target wavelengths
ax1.axvline(x=wavelength_1, color="#1a3a5c", linestyle="--", alpha=0.5, label=f"λ1 = {wavelength_1} μm")
ax1.axvline(x=wavelength_2, color="#c44e52", linestyle="--", alpha=0.5, label=f"λ2 = {wavelength_2} μm")

# plot 2: ratio of flux between detectors (separation quality)
# if the prism separates perfectly, this ratio should be very different
# at the two wavelengths
with np.errstate(divide="ignore", invalid="ignore"):
    ratio = np.where(flux2_values != 0, flux1_values / flux2_values, 0)

ax2.plot(wavelengths, ratio, color="#2d7d46")
ax2.set_xlabel("wavelength (μm)")
ax2.set_ylabel("detector 1 / detector 2 ratio")
ax2.set_title("separation ratio (>1 means more light at upper detector)")
ax2.axhline(y=1, color="gray", linestyle="--", alpha=0.5)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("01_decomposition_results.png", dpi=150, bbox_inches="tight")
print("saved plot: 01_decomposition_results.png")

# ============================================================
# PASS/FAIL CHECK
# ============================================================

# find flux at our two target wavelengths at each detector
idx1 = np.argmin(np.abs(wavelengths - wavelength_1))
idx2 = np.argmin(np.abs(wavelengths - wavelength_2))

f1_at_det1 = flux1_values[idx1]
f1_at_det2 = flux2_values[idx1]
f2_at_det1 = flux1_values[idx2]
f2_at_det2 = flux2_values[idx2]

print(f"\n{'='*50}")
print(f"RESULTS AT TARGET WAVELENGTHS")
print(f"{'='*50}")
print(f"\nwavelength 1 ({wavelength_1} μm):")
print(f"  detector 1 (upper): {f1_at_det1:.4f}")
print(f"  detector 2 (lower): {f1_at_det2:.4f}")

print(f"\nwavelength 2 ({wavelength_2} μm):")
print(f"  detector 1 (upper): {f2_at_det1:.4f}")
print(f"  detector 2 (lower): {f2_at_det2:.4f}")

# check if separation happened
# we want wavelength 1 to be stronger at one detector
# and wavelength 2 to be stronger at the other
if f1_at_det1 > 0 and f1_at_det2 > 0:
    ratio_w1 = f1_at_det1 / f1_at_det2
else:
    ratio_w1 = 0

if f2_at_det1 > 0 and f2_at_det2 > 0:
    ratio_w2 = f2_at_det1 / f2_at_det2
else:
    ratio_w2 = 0

print(f"\nseparation ratios:")
print(f"  wavelength 1 (det1/det2): {ratio_w1:.4f}")
print(f"  wavelength 2 (det1/det2): {ratio_w2:.4f}")

# if the ratios are meaningfully different, we have separation
if ratio_w1 > 0 and ratio_w2 > 0 and abs(ratio_w1 - ratio_w2) > 0.2:
    print(f"\n>>> PASS — wavelengths are arriving at different ratios across detectors")
    print(f"    the prism is separating them.")
else:
    print(f"\n>>> INCONCLUSIVE — separation not clear enough yet")
    print(f"    might need to adjust prism geometry, material, or detector positions.")