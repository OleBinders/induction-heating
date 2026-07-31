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

from induction_heating.core.electromagnetic import calculate_skin_depth, solenoid_b_field_on_axis
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

    Uses the exponential decay approximation for thick workpieces (a/δ > 4)
    and the Bessel function solution for thinner workpieces (a/δ ≤ 4).

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

    # Surface current density approximation
    # J_surface ≈ ω * B_surface * a / (2 * ρ) for a >> δ
    omega = 2.0 * math.pi * frequency
    j_surface = omega * b_surface * a / (2.0 * resistivity)

    if ratio > 4.0:
        # Thick workpiece: exponential decay from surface
        # J(r) = J_surface * exp(-(a - r) / δ)
        j_r = j_surface * np.exp(-(a - r) / delta)
    else:
        # Thin workpiece: Bessel function solution
        # J(r) = J_surface * J₀(kr) / J₀(ka) where k = (1-j)/δ
        # For magnitude: |J(r)| = |J_surface| * |ber₀(r/δ) + j*bei₀(r/δ)| / |ber₀(a/δ) + j*bei₀(a/δ)|
        # Simplified: use magnitude of J₀ with complex argument
        k_mag = math.sqrt(2.0) / delta  # |k| = √2/δ
        # Use Kelvin functions for magnitude: |J₀(j^(3/2) * x)| = √(ber₀²(x) + bei₀²(x))
        # For simplicity, use the approximation |J₀(kr)| ≈ exp(-r/δ) for large arguments
        # and the exact Bessel function for small arguments
        x_r = r / delta
        x_a = a / delta

        # Kelvin functions ber and bei: kelvin(x)[0] = ber(x) + j*bei(x)
        kelvin_r = special.kelvin(x_r)
        kelvin_a = special.kelvin(x_a)
        ber_r, bei_r = kelvin_r[0].real, kelvin_r[0].imag
        ber_a, bei_a = kelvin_a[0].real, kelvin_a[0].imag

        mag_r = np.sqrt(ber_r**2 + bei_r**2)
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
