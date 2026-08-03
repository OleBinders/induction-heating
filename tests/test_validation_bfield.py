"""B-field validation tests against analytical solutions.

Reference values from:
- Standard solenoid formula: B = μ₀NI/l (infinite solenoid approximation)
- Callaghan & Maslen, "The magnetic field of a finite solenoid" (NASA TN D-465, 1960)
"""

from __future__ import annotations

import numpy as np
import pytest

from induction_heating.core.electromagnetic import (
    solenoid_b_field_on_axis,
    solenoid_b_field_off_axis,
)
from induction_heating.core.geometry import SolenoidCoil
from induction_heating.utils.constants import mu_0


class TestBFieldValidation:
    """Validate B-field calculations against analytical solutions."""

    def test_infinite_solenoid_approximation(self) -> None:
        """Long solenoid: B = μ₀NI/l at center ± 1%.

        For N=500, I=10A, l=0.5m: B = 4π×10⁻⁷ × 500 × 10 / 0.5 = 0.01257 T = 12.57 mT
        """
        coil = SolenoidCoil(
            inner_radius=0.01,
            outer_radius=0.012,
            length=0.5,  # l/R ≈ 45, very long
            turns=500,
            wire_diameter=0.001,
        )
        B = solenoid_b_field_on_axis(coil, 10.0, 0.0)
        expected = mu_0() * 500 * 10.0 / 0.5
        assert B == pytest.approx(expected, rel=0.01)

    def test_coil_end_field(self) -> None:
        """Coil end field ≈ half of center value ± 5%."""
        coil = SolenoidCoil(
            inner_radius=0.01,
            outer_radius=0.012,
            length=0.5,
            turns=500,
            wire_diameter=0.001,
        )
        B_center = solenoid_b_field_on_axis(coil, 10.0, 0.0)
        B_end = solenoid_b_field_on_axis(coil, 10.0, coil.length / 2)
        assert B_end == pytest.approx(B_center / 2.0, rel=0.05)

    def test_far_field(self) -> None:
        """Far field (|z| ≫ l): B < 1% of center value."""
        coil = SolenoidCoil(
            inner_radius=0.025,
            outer_radius=0.030,
            length=0.10,
            turns=20,
            wire_diameter=0.005,
        )
        B_center = solenoid_b_field_on_axis(coil, 10.0, 0.0)
        B_far = solenoid_b_field_on_axis(coil, 10.0, 1.0)  # 1m away (10x coil length)
        assert B_far < B_center * 0.01

    def test_off_axis_consistency(self) -> None:
        """Off-axis B_z at ρ=0 matches on-axis function."""
        coil = SolenoidCoil(
            inner_radius=0.025,
            outer_radius=0.030,
            length=0.10,
            turns=20,
            wire_diameter=0.005,
        )
        z_vals = np.array([0.0, 0.025, 0.05])
        B_on_axis = solenoid_b_field_on_axis(coil, 10.0, z_vals)
        _, B_off = solenoid_b_field_off_axis(coil, 10.0, np.zeros_like(z_vals), z_vals)
        assert np.allclose(B_off, B_on_axis, rtol=1e-10)

    def test_off_axis_b_rho_zero(self) -> None:
        """B_ρ = 0 on symmetry axis."""
        coil = SolenoidCoil(
            inner_radius=0.025,
            outer_radius=0.030,
            length=0.10,
            turns=20,
            wire_diameter=0.005,
        )
        B_rho, _ = solenoid_b_field_off_axis(coil, 10.0, 0.0, 0.0)
        assert np.asarray(B_rho).item() == pytest.approx(0.0, abs=1e-15)
