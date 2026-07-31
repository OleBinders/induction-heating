"""Physical constants for electromagnetic calculations.

All constants are provided as Pint quantities with proper units,
sourced from scipy.constants for accuracy.
"""

from __future__ import annotations

import scipy.constants

from induction_heating.utils.units import Q_

# Permeability of free space (μ₀) = 4π × 10⁻⁷ H/m
# scipy.constants.mu_0 is defined exactly as 4π × 10⁻⁷
MU_0: float = scipy.constants.mu_0
"""Permeability of free space in H/m."""

# Permittivity of free space (ε₀) = 8.8541878128 × 10⁻¹² F/m
EPSILON_0: float = scipy.constants.epsilon_0
"""Permittivity of free space in F/m."""

# Speed of light in vacuum (c) = 299792458 m/s (exact)
C: float = scipy.constants.c
"""Speed of light in vacuum in m/s."""

# Elementary charge (e) = 1.602176634 × 10⁻¹⁹ C (exact)
ELEMENTARY_CHARGE: float = scipy.constants.elementary_charge
"""Elementary charge in C."""

# Boltzmann constant (k_B) = 1.380649 × 10⁻²³ J/K (exact)
BOLTZMANN: float = scipy.constants.Boltzmann
"""Boltzmann constant in J/K."""


def mu_0() -> float:
    """Return permeability of free space in H/m."""
    return MU_0


def epsilon_0() -> float:
    """Return permittivity of free space in F/m."""
    return EPSILON_0
