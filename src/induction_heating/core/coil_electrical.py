"""Coil self-inductance / bare-coil reactance.

New physics for Phase 2b: nothing else in this codebase computes a coil's
own self-inductance. This is deliberately independent of the TREE
eigenfunction machinery in ``coupled_eddy_current.py`` -- it is a classical
closed-form solenoid self-inductance formula, used both as physics in its
own right (part of the coil's total electrical impedance/voltage, per the
project plan) and, in later sub-phases, to normalize the coupled solver's
``delta_Z`` against a known "no workpiece" baseline reactance.
"""

from __future__ import annotations

import math

from induction_heating.core.geometry import SolenoidCoil

_INCH_IN_METERS = 0.0254


def bare_coil_self_inductance(coil: SolenoidCoil) -> float:
    """Single-layer air-core solenoid self-inductance (no workpiece).

    Uses Wheeler's (1928) empirical approximation for a single-layer
    air-core solenoid, which is accurate to within about 1% for coils with
    length > ~0.8 * radius (i.e. not extremely short/"pancake" coils), and
    somewhat worse outside that range.

    Source: H. A. Wheeler, "Simple Inductance Formulas for Radio Coils,"
    Proceedings of the IRE, vol. 16, no. 10, pp. 1398-1400, Oct. 1928.
    Original formula (imperial units -- radius r and length l in inches,
    inductance in microhenries), using the coil's mean radius as "r":

        L[uH] = r^2 * N^2 / (9*r + 10*l)

    This function evaluates the SI-unit-equivalent of that same formula
    (r, l in meters, L in henries), obtained by substituting
    r[in] = r[m]/0.0254, l[in] = l[m]/0.0254 through the original formula
    and simplifying:

        L[H] = 1e-6 * (r[m]/0.0254)^2 * N^2 / (9*(r[m]/0.0254) + 10*(l[m]/0.0254))
             = 1e-6 * N^2 * r[m]^2 / (0.0254 * (9*r[m] + 10*l[m]))

    Sanity check (long-coil limit, l >> r): this reduces to
    L ~ 1e-6 * N^2*r^2 / (0.254*l), matching the standard infinite-solenoid
    formula mu_0*N^2*pi*r^2/l to within ~0.3% (mu_0*pi*0.0254 = 1.0028e-7,
    vs. this formula's implied 1e-7, i.e. 1e-6*(1/0.254)=3.937e-6 per unit
    N^2*r^2/l compared to the exact 3.9478e-6 -- the two constants agree to
    3 significant figures), which is the expected level of agreement for
    this class of empirical formula.

    Args:
        coil: SolenoidCoil geometry. Uses ``coil.mean_radius`` as the
            single-layer winding radius and ``coil.length`` as the axial
            winding length.

    Returns:
        Self-inductance in Henries.
    """
    r = coil.mean_radius
    length = coil.length
    n_turns = coil.turns
    inductance_microhenries = (n_turns**2 * r**2) / (
        _INCH_IN_METERS * (9.0 * r + 10.0 * length)
    )
    return inductance_microhenries * 1e-6


def bare_coil_reactance(coil: SolenoidCoil, frequency: float) -> float:
    """Bare-coil (no workpiece) self-reactance X_L0 = 2*pi*f*L0.

    Args:
        coil: SolenoidCoil geometry.
        frequency: Operating frequency (Hz), > 0.

    Returns:
        Reactance in Ohms.

    Raises:
        ValueError: If frequency is non-positive.
    """
    if frequency <= 0.0:
        raise ValueError(f"frequency must be > 0, got {frequency}")

    inductance = bare_coil_self_inductance(coil)
    return 2.0 * math.pi * frequency * inductance
