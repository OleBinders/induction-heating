"""Validation tests for bare-coil self-inductance / reactance.

Reference: H. A. Wheeler, "Simple Inductance Formulas for Radio Coils,"
Proc. IRE, vol. 16, no. 10, pp. 1398-1400, Oct. 1928 -- see
``core/coil_electrical.py`` for the full formula and unit-conversion
derivation this implementation is based on.
"""

from __future__ import annotations

import math

import pytest

from induction_heating.core.coil_electrical import (
    bare_coil_reactance,
    bare_coil_self_inductance,
)
from induction_heating.core.geometry import SolenoidCoil
from induction_heating.utils.constants import mu_0


class TestBareCoilSelfInductance:
    def test_matches_hand_computed_reference_case(self) -> None:
        """100-turn, ~5cm-diameter (2.5cm mean radius), 10cm-long air-core
        solenoid. Independently recomputes Wheeler's original imperial-unit
        formula L[uH] = r[in]^2 * N^2 / (9*r[in] + 10*l[in]) here (rather
        than importing any constant from the module under test) and checks
        the SI-unit implementation agrees with it -- this is a unit-
        conversion regression guard, not just a symbolic re-statement of
        the same code (see ``bare_coil_self_inductance``'s docstring for
        the derivation connecting the two forms).
        """
        coil = SolenoidCoil(
            inner_radius=0.024, outer_radius=0.026, length=0.10, turns=100, wire_diameter=0.001
        )
        r_in = coil.mean_radius / 0.0254
        l_in = coil.length / 0.0254
        expected_uH = (r_in**2 * coil.turns**2) / (9.0 * r_in + 10.0 * l_in)
        expected_H = expected_uH * 1e-6

        assert bare_coil_self_inductance(coil) == pytest.approx(expected_H, rel=1e-9)
        # Ballpark sanity: this well-known "round numbers" case should
        # land in the low hundreds of microhenries, not nanohenries or
        # millihenries -- catches a gross unit error (e.g. a missing or
        # extra factor of 1e6) that a purely symbolic formula check would
        # not.
        assert 50e-6 < bare_coil_self_inductance(coil) < 500e-6

    def test_bounded_by_infinite_solenoid_approximation(self) -> None:
        """A finite coil's inductance must be strictly less than the
        infinite-solenoid approximation L = mu_0*N^2*pi*R^2/length (which
        ignores fringing/end effects that always reduce inductance below
        that limit) -- a basic physical sanity bound independent of which
        exact finite-length formula is used."""
        coil = SolenoidCoil(
            inner_radius=0.024, outer_radius=0.026, length=0.10, turns=100, wire_diameter=0.001
        )
        finite_L = bare_coil_self_inductance(coil)
        infinite_L = mu_0() * coil.turns**2 * math.pi * coil.mean_radius**2 / coil.length
        assert 0.0 < finite_L < infinite_L

    def test_scales_as_turns_squared(self) -> None:
        """L proportional to N^2 -- the defining signature of self-
        inductance for a fixed geometry (doubling turns quadruples flux
        linkage per unit current)."""
        base = SolenoidCoil(
            inner_radius=0.024, outer_radius=0.026, length=0.10, turns=50, wire_diameter=0.001
        )
        doubled = SolenoidCoil(
            inner_radius=0.024, outer_radius=0.026, length=0.10, turns=100, wire_diameter=0.001
        )
        ratio = bare_coil_self_inductance(doubled) / bare_coil_self_inductance(base)
        assert ratio == pytest.approx(4.0, rel=1e-9)

    def test_longer_coil_has_lower_inductance_at_fixed_turns(self) -> None:
        """Spreading the same number of turns over a longer coil reduces
        flux linkage per turn (weaker mutual coupling between turns) --
        inductance must decrease."""
        short = SolenoidCoil(
            inner_radius=0.024, outer_radius=0.026, length=0.05, turns=100, wire_diameter=0.0005
        )
        long_ = SolenoidCoil(
            inner_radius=0.024, outer_radius=0.026, length=0.20, turns=100, wire_diameter=0.0005
        )
        assert bare_coil_self_inductance(long_) < bare_coil_self_inductance(short)


class TestBareCoilReactance:
    def test_reactance_equals_two_pi_f_l(self) -> None:
        coil = SolenoidCoil(
            inner_radius=0.024, outer_radius=0.026, length=0.10, turns=100, wire_diameter=0.001
        )
        frequency = 10e3
        expected = 2.0 * math.pi * frequency * bare_coil_self_inductance(coil)
        assert bare_coil_reactance(coil, frequency) == pytest.approx(expected, rel=1e-12)

    def test_reactance_scales_linearly_with_frequency(self) -> None:
        coil = SolenoidCoil(
            inner_radius=0.024, outer_radius=0.026, length=0.10, turns=100, wire_diameter=0.001
        )
        x1 = bare_coil_reactance(coil, 10e3)
        x2 = bare_coil_reactance(coil, 20e3)
        assert x2 == pytest.approx(2.0 * x1, rel=1e-9)

    def test_rejects_nonpositive_frequency(self) -> None:
        coil = SolenoidCoil(
            inner_radius=0.024, outer_radius=0.026, length=0.10, turns=100, wire_diameter=0.001
        )
        with pytest.raises(ValueError):
            bare_coil_reactance(coil, 0.0)
        with pytest.raises(ValueError):
            bare_coil_reactance(coil, -1.0)
