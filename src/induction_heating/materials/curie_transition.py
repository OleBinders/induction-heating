"""Curie point transition models for magnetic permeability.

Provides sigmoid-based and polynomial models for the ferromagnetic →
paramagnetic transition at the Curie temperature, used as fallbacks when
detailed temperature-dependent permeability data is not available.
"""

from __future__ import annotations

import numpy as np


def permeability_sigmoid(
    temperature: float | np.ndarray,
    mu_r_0: float,
    Tc: float,
    k: float = 0.1,
) -> float | np.ndarray:
    """Calculate relative permeability using a sigmoid transition model.

    Formula: μᵣ(T) = 1 + (μᵣ₀ - 1) / (1 + exp(k * (T - Tc)))

    This produces a smooth, C∞-continuous transition from μᵣ₀ at low
    temperatures to 1.0 (paramagnetic) at high temperatures.

    Args:
        temperature: Temperature in °C.
        mu_r_0: Relative permeability at room temperature (T ≪ Tc).
        Tc: Curie temperature in °C.
        k: Steepness parameter. Higher values produce sharper transitions.
            Default k=0.1 gives a transition width of ~20°C.

    Returns:
        Relative permeability μᵣ(T), guaranteed ≥ 1.0.
    """
    if mu_r_0 < 1.0:
        raise ValueError(f"mu_r_0 must be >= 1.0, got {mu_r_0}")
    if k <= 0:
        raise ValueError(f"k must be > 0, got {k}")

    T = np.asarray(temperature, dtype=float)
    exponent = k * (T - Tc)

    # Use exp(-x) / (1 + exp(-x)) = 1 / (1 + exp(x)) for numerical stability
    # when exponent is large positive
    sigmoid = np.where(
        exponent > 0,
        np.exp(-exponent) / (1.0 + np.exp(-exponent)),
        1.0 / (1.0 + np.exp(exponent)),
    )

    return 1.0 + (mu_r_0 - 1.0) * sigmoid


def permeability_polynomial(
    temperature: float | np.ndarray,
    mu_r_0: float,
    Tc: float,
    T_start: float | None = None,
    n: int = 2,
) -> float | np.ndarray:
    """Calculate relative permeability using a polynomial transition model.

    Formula:
        μᵣ(T) = μᵣ₀                              for T ≤ T_start
        μᵣ(T) = 1 + (μᵣ₀ - 1) * (1 - ((T - T_start) / (Tc - T_start))^n)
                                                   for T_start < T < Tc
        μᵣ(T) = 1.0                              for T ≥ Tc

    Args:
        temperature: Temperature in °C.
        mu_r_0: Relative permeability at room temperature (T ≤ T_start).
        Tc: Curie temperature in °C.
        T_start: Temperature where permeability starts dropping.
            Defaults to Tc - 100 (100°C transition width).
        n: Polynomial exponent. Higher values produce sharper transitions
            near Tc. Default n=2 gives a quadratic transition.

    Returns:
        Relative permeability μᵣ(T), guaranteed ≥ 1.0.
    """
    if mu_r_0 < 1.0:
        raise ValueError(f"mu_r_0 must be >= 1.0, got {mu_r_0}")
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    if T_start is None:
        T_start = Tc - 100.0

    if T_start >= Tc:
        raise ValueError(f"T_start ({T_start}) must be < Tc ({Tc})")

    T = np.asarray(temperature, dtype=float)
    result = np.full_like(T, 1.0, dtype=float)

    # Region 1: T ≤ T_start → μᵣ = μᵣ₀
    below_start = T <= T_start
    result[below_start] = mu_r_0

    # Region 2: T_start < T < Tc → polynomial transition
    in_transition = (T > T_start) & (T < Tc)
    if np.any(in_transition):
        t_norm = (T[in_transition] - T_start) / (Tc - T_start)
        result[in_transition] = 1.0 + (mu_r_0 - 1.0) * (1.0 - t_norm**n)

    # Region 3: T ≥ Tc → μᵣ = 1.0 (already set by default)

    return result
