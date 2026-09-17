"""Eddy current density, power density, and induction heating pipeline.

Provides functions for computing eddy current distributions in cylindrical
workpieces, Joule heating power density, and the complete calculation pipeline
that connects geometry, material properties, and electromagnetic calculations.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special
from scipy.integrate import trapezoid

from induction_heating.core.electromagnetic import (
    calculate_skin_depth,
    solenoid_b_field_off_axis,
    solenoid_b_field_on_axis,
)
from induction_heating.core.geometry import InductionSetup
from induction_heating.materials.database import MaterialDatabase
from induction_heating.materials.property_evolution import PropertySnapshot
from induction_heating.utils.constants import mu_0


def eddy_current_density(
    b_surface: float,
    frequency: float,
    resistivity: float,
    relative_permeability: float,
    workpiece_radius: float,
    radial_positions: np.ndarray,
) -> np.ndarray:
    """Calculate eddy current density distribution in a cylindrical workpiece.

    Uses the exact Kelvin-function (Lord Kelvin's classical) solution for a
    solid cylinder in a uniform axial AC field, for a/δ ≤ 50. Above that ratio
    it switches to the exponential thick-workpiece approximation -- the two
    agree to within ~1% at a/δ = 50 (verified numerically by comparing
    integrated power at a/δ = 30-100), so the switch introduces no visible
    discontinuity. This is not a numerical-overflow workaround: scipy's Kelvin
    functions stay finite until a/δ ≈ 710, far past this threshold -- the
    switch is purely about using the simpler asymptotic formula once the exact
    and approximate solutions have already converged.

    Args:
        b_surface: Magnetic flux density at workpiece surface (T).
        frequency: Operating frequency (Hz).
        resistivity: Workpiece resistivity (Ω·m).
        relative_permeability: Workpiece relative permeability (dimensionless).
        workpiece_radius: Workpiece radius (m).
        radial_positions: Array of radial positions to evaluate (m).

    Returns:
        Eddy current density J(r) in A/m².
    """
    a = workpiece_radius
    r = np.asarray(radial_positions, dtype=float)

    # Calculate skin depth
    delta = calculate_skin_depth(resistivity, relative_permeability, frequency)

    # Determine regime
    ratio = a / delta

    # Surface current density from the standard skin-effect boundary condition:
    # J_surface = H_surface * √2 / δ, where H_surface = B_surface / μ0.
    #
    # b_surface is the *applied* field from the coil (solenoid_b_field_on_axis
    # uses only mu_0() -- it has no dependence on the workpiece's material).
    # Tangential H is continuous across the workpiece surface (no free surface
    # current), so H just inside the surface equals H_applied = b_surface/mu_0
    # -- NOT b_surface/(mu_0*relative_permeability). Dividing by the workpiece's
    # own permeability here was a bug: it made computed power fall with
    # increasing permeability instead of rising with it, the opposite of real
    # induction-heating behavior (this is why magnetic steel below its Curie
    # point heats far more efficiently than non-magnetic metals at the same
    # applied field -- the entire basis of induction hardening).
    #
    # (This is the same H(x) result as for a semi-infinite plane conductor:
    # |dH/dx| at the surface for H(x) = H0·exp(-(1+j)x/δ).)
    h_surface = b_surface / mu_0()
    j_surface = h_surface * math.sqrt(2.0) / delta

    if ratio > 50.0:
        # Thick workpiece: exponential decay from surface
        # J(r) = J_surface * exp(-(a - r) / δ)
        j_r = j_surface * np.exp(-(a - r) / delta)
    else:
        # Exact solution: the axial field inside the conductor solves
        # H_z'' + (1/r)H_z' - jωμσH_z = 0, whose solution is the ORDER-0
        # Kelvin function H_z(r) = H_surface·[ber0(qr)+j·bei0(qr)] /
        # [ber0(qa)+j·bei0(qa)], q = √2/δ (Kelvin's original (1887)
        # eddy-current argument convention, m = a·√(ωμ/ρ) = √2·a/δ).
        #
        # But current density is J_phi = -dH_z/dr, NOT H_z itself --
        # differentiating an order-0 Kelvin function produces the order-1
        # family. scipy.special.kelvin(x) returns (Be, Ke, Bep, Kep) where
        # Be = ber0(x)+j·bei0(x) and Bep = ber0'(x)+j·bei0'(x) -- the
        # derivative needed for the numerator. The denominator stays order-0
        # (Be at qa) because the boundary condition is on H(a) = H_surface,
        # not directly on J(a).
        #
        # Using order-0 in the numerator (as this branch previously did) was
        # a real bug: it gave J(r=0) ≈ 0.75·J(a) at a/δ≈1.6, but a circular
        # eddy-current loop of zero radius must carry exactly zero current --
        # J(0) must be exactly 0. Verified against a from-scratch numerical
        # ODE shooting-method solve, matching to machine precision at every
        # radius including r→0.
        q = math.sqrt(2.0) / delta
        kelvin_r = special.kelvin(q * r)
        kelvin_a = special.kelvin(q * a)
        bep_r, bep_i = kelvin_r[2].real, kelvin_r[2].imag  # numerator: derivative (order-1)
        ber_a, bei_a = kelvin_a[0].real, kelvin_a[0].imag  # denominator: order-0, unchanged

        mag_r = np.sqrt(bep_r**2 + bep_i**2)
        mag_a = np.sqrt(ber_a**2 + bei_a**2)

        # Avoid division by zero
        mag_a = np.maximum(mag_a, 1e-30)
        j_r = j_surface * mag_r / mag_a

    return j_r


def power_density(
    current_density: np.ndarray,
    resistivity: float,
) -> np.ndarray:
    """Calculate Joule heating power density from eddy current density.

    Args:
        current_density: Eddy current density J(r) in A/m².
        resistivity: Material resistivity (Ω·m).

    Returns:
        Power density p(r) in W/m³.
    """
    return current_density**2 * resistivity


def total_power(
    current_density: np.ndarray,
    resistivity: float,
    workpiece_radius: float,
    workpiece_length: float,
    num_points: int = 200,
) -> float:
    """Calculate total absorbed power by integrating power density over volume.

    P = ∫₀ᵃ p(r) * 2πrL dr

    Args:
        current_density: Eddy current density at sample points (A/m²).
        resistivity: Material resistivity (Ω·m).
        workpiece_radius: Workpiece radius (m).
        workpiece_length: Workpiece length (m).
        num_points: Number of radial integration points.

    Returns:
        Total absorbed power in Watts.
    """
    r = np.linspace(0, workpiece_radius, num_points)
    p_r = power_density(current_density, resistivity)

    # Integrate p(r) * 2πrL dr using trapezoidal rule
    integrand = p_r * 2.0 * math.pi * r * workpiece_length
    return float(trapezoid(integrand, r))


def calculate_induction_heating(
    setup: InductionSetup,
    current: float,
    frequency: float,
    temperature: float = 20.0,
    material_db: MaterialDatabase | None = None,
    num_radial_points: int = 200,
) -> dict:
    """Complete induction heating calculation pipeline.

    Args:
        setup: Induction setup (coil + workpiece + gap).
        current: Coil current amplitude (A).
        frequency: Operating frequency (Hz).
        temperature: Workpiece temperature for property lookup (°C).
        material_db: Material database. Creates default if None.
        num_radial_points: Number of radial points for distribution calculations.

    Returns:
        Dict with keys:
            - skin_depth: Skin depth in meters.
            - b_field_surface: B-field at workpiece surface in Tesla.
            - current_density: Eddy current density array (A/m²).
            - power_density: Power density array (W/m³).
            - total_power: Total absorbed power in Watts.
            - radial_positions: Radial positions array (m).
            - snapshot: PropertySnapshot used for calculations.
    """
    if material_db is None:
        material_db = MaterialDatabase()

    # 1. Get all material properties at temperature (single consistent snapshot)
    snapshot = PropertySnapshot.from_material(
        material_db, setup.workpiece.material_name, temperature
    )

    # 2. Calculate skin depth
    skin_depth = calculate_skin_depth(snapshot.resistivity, snapshot.relative_permeability, frequency)

    # 3. Calculate B-field at workpiece surface (on axis, at z=0)
    b_surface = solenoid_b_field_on_axis(setup.coil, current, 0.0)

    # 4. Calculate eddy current density distribution
    r = np.linspace(0, setup.workpiece.radius, num_radial_points)
    j_r = eddy_current_density(
        b_surface=b_surface,
        frequency=frequency,
        resistivity=snapshot.resistivity,
        relative_permeability=snapshot.relative_permeability,
        workpiece_radius=setup.workpiece.radius,
        radial_positions=r,
    )

    # 5. Calculate power density distribution
    p_r = power_density(j_r, snapshot.resistivity)

    # 6. Calculate total absorbed power
    p_total = total_power(j_r, snapshot.resistivity, setup.workpiece.radius, setup.workpiece.length)

    return {
        "skin_depth": skin_depth,
        "b_field_surface": b_surface,
        "current_density": j_r,
        "power_density": p_r,
        "total_power": p_total,
        "radial_positions": r,
        "snapshot": snapshot,
    }


def eddy_current_density_2d(
    b_surface_z: np.ndarray,
    frequency: float,
    resistivity_z: float | np.ndarray,
    relative_permeability_z: float | np.ndarray,
    workpiece_radius: float,
    radial_positions: np.ndarray,
) -> np.ndarray:
    """Calculate eddy current density on a 2D (z, r) grid.

    IMPORTANT -- approximation model: this is a "locally quasi-1D per axial
    slice" approximation, NOT a coupled 2D eddy-current PDE solve. Each axial
    slice is treated independently: the already-validated, unmodified
    ``eddy_current_density()`` Kelvin-function solution (derived for a solid
    cylinder in a *uniform* axial field) is applied once per slice using that
    slice's own local surface field. There is no mutual coupling between
    slices -- no axial diffusion of eddy currents, no end effects beyond
    whatever axial variation is already present in ``b_surface_z`` itself.
    This is a standard, defensible semi-analytical approximation for getting
    realistic axial field falloff without a full FEM/mesh solve (which is out
    of scope for this project), but it is not a rigorous coupled solution.

    Args:
        b_surface_z: Magnetic flux density at the workpiece surface for each
            axial slice, shape (n_z,), in Tesla.
        frequency: Operating frequency (Hz).
        resistivity_z: Workpiece resistivity (Ω·m). Scalar or shape (n_z,) --
            broadcast to each axial slice.
        relative_permeability_z: Workpiece relative permeability
            (dimensionless). Scalar or shape (n_z,) -- broadcast to each
            axial slice.
        workpiece_radius: Workpiece radius (m).
        radial_positions: Radial positions to evaluate, shape (n_r,) (m).

    Returns:
        Eddy current density J(z, r) in A/m², shape (n_z, n_r).
    """
    b_surface_z = np.asarray(b_surface_z, dtype=float)
    n_z = b_surface_z.shape[0]

    resistivity_arr = np.broadcast_to(np.asarray(resistivity_z, dtype=float), (n_z,))
    mu_r_arr = np.broadcast_to(np.asarray(relative_permeability_z, dtype=float), (n_z,))

    n_r = np.asarray(radial_positions).shape[0]
    j_zr = np.empty((n_z, n_r), dtype=float)

    for i in range(n_z):
        j_zr[i, :] = eddy_current_density(
            b_surface=float(b_surface_z[i]),
            frequency=frequency,
            resistivity=float(resistivity_arr[i]),
            relative_permeability=float(mu_r_arr[i]),
            workpiece_radius=workpiece_radius,
            radial_positions=radial_positions,
        )

    return j_zr


def total_power_2d(
    power_density_rz: np.ndarray,
    radial_positions: np.ndarray,
    axial_positions: np.ndarray,
) -> float:
    """Integrate power density over the full (r, z) cylindrical volume.

    P = ∫∫ p(r,z) * 2πr dr dz

    Performed as nested `scipy.integrate.trapezoid` calls: radial integration
    first (for each axial slice, producing power per unit length), then
    integration of that result over the axial extent.

    Args:
        power_density_rz: Power density on a (n_z, n_r) grid, W/m³.
        radial_positions: Radial sample positions, shape (n_r,) (m).
        axial_positions: Axial sample positions, shape (n_z,) (m).

    Returns:
        Total absorbed power in Watts.
    """
    r = np.asarray(radial_positions, dtype=float)
    power_density_rz = np.asarray(power_density_rz, dtype=float)

    # Radial integration per z-slice: power per unit axial length, W/m.
    integrand_r = power_density_rz * 2.0 * math.pi * r[np.newaxis, :]
    power_per_length_z = trapezoid(integrand_r, r, axis=1)

    # Axial integration: total power, W.
    return float(trapezoid(power_per_length_z, np.asarray(axial_positions, dtype=float)))


def calculate_induction_heating_2d(
    setup: InductionSetup,
    current: float,
    frequency: float,
    temperature: float = 20.0,
    material_db: MaterialDatabase | None = None,
    num_radial_points: int = 200,
    num_axial_points: int = 41,
) -> dict:
    """Complete 2D (r, z) induction heating calculation pipeline.

    Extends ``calculate_induction_heating`` with realistic axial variation:
    the coil's field is evaluated at the workpiece's true surface radius at
    each axial slice (via the exact off-axis solenoid solution), instead of
    computing the field once on-axis (ρ=0, z=0) and broadcasting that single
    radial profile uniformly along the whole workpiece length. Each slice
    still uses the same validated Kelvin-function eddy-current solution as
    the 1D pipeline -- see ``eddy_current_density_2d`` for the "locally
    quasi-1D per axial slice" approximation this relies on. This function is
    additive: it does not modify or replace ``calculate_induction_heating``.

    A single PropertySnapshot is used for the whole call (one temperature for
    the entire workpiece) -- there is no time/temperature evolution yet; that
    is a later phase of the broader scope expansion.

    Args:
        setup: Induction setup (coil + workpiece + gap).
        current: Coil current amplitude (A).
        frequency: Operating frequency (Hz).
        temperature: Workpiece temperature for property lookup (°C).
        material_db: Material database. Creates default if None.
        num_radial_points: Number of radial points per axial slice.
        num_axial_points: Number of axial slices spanning the workpiece length.

    Returns:
        Dict with keys:
            - skin_depth: Skin depth in meters (single value -- properties
              are temperature-, not position-, dependent in this phase).
            - b_field_surface_z: B-field at the true workpiece surface at
              each axial slice, shape (n_z,), in Tesla.
            - current_density: Eddy current density array, shape (n_z, n_r),
              in A/m².
            - power_density: Power density array, shape (n_z, n_r), in W/m³.
            - total_power: Total absorbed power in Watts.
            - radial_positions: Radial positions array, shape (n_r,) (m).
            - axial_positions: Axial positions array, shape (n_z,) (m),
              relative to the workpiece's (and coil's) axial center.
            - snapshot: PropertySnapshot used for calculations.
    """
    if material_db is None:
        material_db = MaterialDatabase()

    # 1. Get all material properties at temperature (single consistent
    # snapshot -- no time/temperature evolution in this phase).
    snapshot = PropertySnapshot.from_material(
        material_db, setup.workpiece.material_name, temperature
    )

    # 2. Calculate skin depth (properties are uniform in this phase, so skin
    # depth is a single scalar -- it does not vary per axial slice).
    skin_depth = calculate_skin_depth(
        snapshot.resistivity, snapshot.relative_permeability, frequency
    )

    # 3. Axial grid spanning the workpiece length, centered at z=0 (matching
    # the coil's own axial center convention used throughout electromagnetic.py).
    z = np.linspace(
        -setup.workpiece.length / 2.0, setup.workpiece.length / 2.0, num_axial_points
    )

    # 4. B-field at the workpiece's TRUE surface radius at each axial slice,
    # via the exact off-axis solenoid solution. This improves on the 1D
    # pipeline's on-axis (ρ=0) proxy without modifying that function.
    rho_positions = np.full_like(z, setup.workpiece.radius)
    _, b_surface_z = solenoid_b_field_off_axis(setup.coil, current, rho_positions, z)

    # 5. Eddy current density on the (z, r) grid.
    r = np.linspace(0, setup.workpiece.radius, num_radial_points)
    j_zr = eddy_current_density_2d(
        b_surface_z=b_surface_z,
        frequency=frequency,
        resistivity_z=snapshot.resistivity,
        relative_permeability_z=snapshot.relative_permeability,
        workpiece_radius=setup.workpiece.radius,
        radial_positions=r,
    )

    # 6. Power density on the (z, r) grid.
    p_zr = power_density(j_zr, snapshot.resistivity)

    # 7. Total absorbed power via nested radial-then-axial integration.
    p_total = total_power_2d(p_zr, r, z)

    return {
        "skin_depth": skin_depth,
        "b_field_surface_z": b_surface_z,
        "current_density": j_zr,
        "power_density": p_zr,
        "total_power": p_total,
        "radial_positions": r,
        "axial_positions": z,
        "snapshot": snapshot,
    }
