"""Electromagnetic calculations for induction heating.

Provides functions for skin depth, solenoid magnetic field (on-axis and off-axis),
using analytical formulas validated against published reference values.
"""

from __future__ import annotations

import math
from typing import overload

import numpy as np
from scipy import special

from induction_heating.utils.constants import mu_0


def calculate_skin_depth(
    resistivity: float | np.ndarray,
    relative_permeability: float | np.ndarray,
    frequency: float,
) -> float | np.ndarray:
    """Calculate skin depth for a given material and frequency.

    The skin depth δ is the depth at which the current density drops to
    1/e of its surface value.

    Formula: δ = √(2ρ / (ωμ)) where ω = 2πf and μ = μ₀μᵣ

    Args:
        resistivity: Electrical resistivity in Ω·m.
        relative_permeability: Relative magnetic permeability (dimensionless).
        frequency: Frequency in Hz.

    Returns:
        Skin depth in meters.

    Raises:
        ValueError: If any input is non-positive.
    """
    if np.any(resistivity <= 0):
        raise ValueError(f"resistivity must be > 0, got {resistivity}")
    if np.any(relative_permeability <= 0):
        raise ValueError(
            f"relative_permeability must be > 0, got {relative_permeability}"
        )
    if frequency <= 0:
        raise ValueError(f"frequency must be > 0, got {frequency}")

    omega = 2.0 * math.pi * frequency
    mu = mu_0() * relative_permeability
    return np.sqrt(2.0 * resistivity / (omega * mu))


def solenoid_b_field_on_axis(
    coil,  # SolenoidCoil
    current: float,
    z_positions: float | np.ndarray,
) -> float | np.ndarray:
    """Calculate axial magnetic field on the symmetry axis of a finite solenoid.

    Formula (from Biot-Savart law):
        B_z(z) = (μ₀NI/2) * [(z+l/2)/(l√(R²+(z+l/2)²)) - (z-l/2)/(l√(R²+(z-l/2)²))]

    Args:
        coil: SolenoidCoil geometry.
        current: Current in amperes.
        z_positions: Axial position(s) in meters relative to coil center (z=0 at center).

    Returns:
        Axial magnetic field B_z in Tesla.
    """
    if current <= 0:
        raise ValueError(f"current must be > 0, got {current}")

    R = coil.mean_radius
    l = coil.length
    N = coil.turns
    mu = mu_0()

    z = np.atleast_1d(np.asarray(z_positions, dtype=float))

    z_plus = z + l / 2.0
    z_minus = z - l / 2.0

    denom_plus = l * np.sqrt(R**2 + z_plus**2)
    denom_minus = l * np.sqrt(R**2 + z_minus**2)

    B_z = (mu * N * current / 2.0) * (z_plus / denom_plus - z_minus / denom_minus)

    if np.isscalar(z_positions):
        return float(B_z[0])
    return B_z


def solenoid_b_field_off_axis(
    coil,  # SolenoidCoil
    current: float,
    rho_positions: float | np.ndarray,
    z_positions: float | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate magnetic field off the symmetry axis using elliptic integrals.

    Implements the Callaghan & Maslen (NASA TN D-465) formulas for a finite
    solenoid with continuous current sheet approximation.

    Args:
        coil: SolenoidCoil geometry.
        current: Current in amperes.
        rho_positions: Radial position(s) in meters from axis.
        z_positions: Axial position(s) in meters relative to coil center.

    Returns:
        Tuple of (B_rho, B_z) arrays in Tesla.
    """
    if current <= 0:
        raise ValueError(f"current must be > 0, got {current}")

    R = coil.mean_radius
    l = coil.length
    N = coil.turns
    mu = mu_0()

    rho = np.atleast_1d(np.asarray(rho_positions, dtype=float))
    z = np.atleast_1d(np.asarray(z_positions, dtype=float))

    # Broadcast to same shape
    rho, z = np.broadcast_arrays(rho, z)
    rho = rho.ravel()
    z = z.ravel()

    B_rho = np.zeros_like(rho)
    B_z = np.zeros_like(rho)

    # Precompute constants
    # Total ampere-turns (the formulas use I as the total current in the sheet)
    ampere_turns = N * current

    # Evaluate at both ends of the solenoid (zeta_plus and zeta_minus)
    for sign in [+1, -1]:
        zeta = z + sign * l / 2.0

        # Parameters for elliptic integrals
        R_plus_rho = R + rho
        R_plus_rho_sq = R_plus_rho**2
        denom = R_plus_rho_sq + zeta**2

        # m = 4Rρ / ((R+ρ)² + ζ²)
        m = 4.0 * R * rho / denom
        # n = 4Rρ / (R+ρ)²
        n = 4.0 * R * rho / R_plus_rho_sq

        # Handle on-axis case (rho=0): m=0, n=0, elliptic integrals simplify
        on_axis = rho < 1e-15

        # Complete elliptic integrals
        K_m = special.ellipk(m)
        E_m = special.ellipe(m)

        # For off-axis points, compute Π(n, m) using Carlson symmetric forms
        # Π(n, m) = R_F(0, 1-m, 1) + (n/3) * R_J(0, 1-m, 1, 1-n)
        # For on-axis points (ρ→0): Π(0, 0) = π/2
        Pi_nm = np.full_like(m, math.pi / 2.0)  # Default: on-axis value
        off_axis = ~on_axis
        if np.any(off_axis):
            n_off = n[off_axis]
            m_off = m[off_axis]
            # Carlson R_F and R_J for complete elliptic integral of third kind
            R_F = special.elliprf(0.0, 1.0 - m_off, 1.0)
            R_J = special.elliprj(0.0, 1.0 - m_off, 1.0, 1.0 - n_off)
            Pi_nm[off_axis] = R_F + (n_off / 3.0) * R_J

        # Common factor
        sqrt_denom = np.sqrt(denom)
        factor = zeta / sqrt_denom

        # B_rho component
        # B_rho = (μ₀I/4π) * (1/(lρ)) * [(m-2)K(m) + 2E(m)] * √((R+ρ)²+ζ²)
        # Handle on-axis: B_rho = 0 by symmetry
        if np.any(off_axis):
            B_rho_term = (m - 2.0) * K_m + 2.0 * E_m
            B_rho[off_axis] += (
                sign * mu * ampere_turns / (4.0 * math.pi * l) * B_rho_term[off_axis] / rho[off_axis] * sqrt_denom[off_axis]
            )

        # B_z component
        # B_z = (μ₀I/2π) * (1/l) * [K(m) + (R-ρ)/(R+ρ)*Π(n,m)] * ζ/√((R+ρ)²+ζ²)
        ratio = (R - rho) / R_plus_rho
        B_z_term = K_m + ratio * Pi_nm
        B_z += sign * mu * ampere_turns / (2.0 * math.pi * l) * B_z_term * factor

    # On-axis points: B_rho must be exactly 0
    B_rho[on_axis] = 0.0

    # Reshape to match input shapes
    rho_shape = np.shape(rho_positions)
    z_shape = np.shape(z_positions)
    out_shape = np.broadcast_shapes(rho_shape, z_shape)

    return B_rho.reshape(out_shape), B_z.reshape(out_shape)
