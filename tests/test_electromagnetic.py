"""Tests for electromagnetic calculations (skin depth, B-field)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from induction_heating.core.electromagnetic import (
    calculate_skin_depth,
    solenoid_b_field_on_axis,
    solenoid_b_field_off_axis,
)
from induction_heating.core.geometry import SolenoidCoil
from induction_heating.utils.constants import mu_0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def long_solenoid() -> SolenoidCoil:
    """Long solenoid (l ≫ R) for testing infinite solenoid approximation."""
    return SolenoidCoil(
        inner_radius=0.010,
        outer_radius=0.012,
        length=0.50,  # l/R ≈ 45, very long
        turns=500,
        wire_diameter=0.001,
    )


@pytest.fixture
def short_solenoid() -> SolenoidCoil:
    """Short solenoid for testing finite-length effects."""
    return SolenoidCoil(
        inner_radius=0.025,
        outer_radius=0.030,
        length=0.10,
        turns=20,
        wire_diameter=0.005,
    )


# ---------------------------------------------------------------------------
# Skin depth tests
# ---------------------------------------------------------------------------

class TestSkinDepth:
    """Test skin depth calculations against reference values."""

    def test_copper_1mhz(self) -> None:
        """Copper at 1 MHz: δ ≈ 66 μm (widely cited reference)."""
        rho = 1.68e-8  # Ω·m
        mu_r = 1.0
        f = 1e6  # Hz
        delta = calculate_skin_depth(rho, mu_r, f)
        assert delta == pytest.approx(66e-6, rel=0.02)  # within 2%

    def test_copper_50khz(self) -> None:
        """Copper at 50 kHz: δ ≈ 0.295 mm."""
        rho = 1.68e-8
        mu_r = 1.0
        f = 50e3
        delta = calculate_skin_depth(rho, mu_r, f)
        assert delta == pytest.approx(0.295e-3, rel=0.02)

    def test_copper_10khz(self) -> None:
        """Copper at 10 kHz: δ ≈ 0.661 mm."""
        rho = 1.68e-8
        mu_r = 1.0
        f = 10e3
        delta = calculate_skin_depth(rho, mu_r, f)
        assert delta == pytest.approx(0.661e-3, rel=0.02)

    def test_steel_magnetic_10khz(self) -> None:
        """Steel (μᵣ=200) at 10 kHz: δ ≈ 0.135 mm."""
        rho = 1.43e-7
        mu_r = 200.0
        f = 10e3
        delta = calculate_skin_depth(rho, mu_r, f)
        # δ = √(2ρ/(ωμ)) = √(2*1.43e-7 / (2π*10000 * 4πe-7 * 200))
        assert delta == pytest.approx(0.135e-3, rel=0.02)

    def test_steel_nonmagnetic_10khz(self) -> None:
        """Steel (μᵣ=1, above Curie) at 10 kHz: δ ≈ 1.90 mm."""
        rho = 1.43e-7
        mu_r = 1.0
        f = 10e3
        delta = calculate_skin_depth(rho, mu_r, f)
        assert delta == pytest.approx(1.90e-3, rel=0.02)

    def test_steel_nonmagnetic_50khz(self) -> None:
        """Steel (μᵣ=1) at 50 kHz: δ ≈ 0.85 mm."""
        rho = 1.43e-7
        mu_r = 1.0
        f = 50e3
        delta = calculate_skin_depth(rho, mu_r, f)
        assert delta == pytest.approx(0.85e-3, rel=0.02)

    def test_skin_depth_decreases_with_frequency(self) -> None:
        """Higher frequency → smaller skin depth."""
        rho = 1.68e-8
        mu_r = 1.0
        d_10k = calculate_skin_depth(rho, mu_r, 10e3)
        d_50k = calculate_skin_depth(rho, mu_r, 50e3)
        assert d_50k < d_10k

    def test_skin_depth_decreases_with_permeability(self) -> None:
        """Higher permeability → smaller skin depth."""
        rho = 1.43e-7
        f = 10e3
        d_low_mu = calculate_skin_depth(rho, 1.0, f)
        d_high_mu = calculate_skin_depth(rho, 200.0, f)
        assert d_high_mu < d_low_mu

    def test_skin_depth_increases_with_resistivity(self) -> None:
        """Higher resistivity → larger skin depth."""
        mu_r = 1.0
        f = 10e3
        d_low_rho = calculate_skin_depth(1.68e-8, mu_r, f)  # copper
        d_high_rho = calculate_skin_depth(1.43e-7, mu_r, f)  # steel
        assert d_high_rho > d_low_rho

    def test_negative_resistivity_raises(self) -> None:
        with pytest.raises(ValueError, match="resistivity"):
            calculate_skin_depth(-1e-8, 1.0, 10e3)

    def test_negative_permeability_raises(self) -> None:
        with pytest.raises(ValueError, match="relative_permeability"):
            calculate_skin_depth(1e-8, -1.0, 10e3)

    def test_negative_frequency_raises(self) -> None:
        with pytest.raises(ValueError, match="frequency"):
            calculate_skin_depth(1e-8, 1.0, -10e3)

    def test_array_input(self) -> None:
        """Skin depth works with array inputs."""
        rho = np.array([1.68e-8, 1.43e-7])
        mu_r = np.array([1.0, 200.0])
        f = 10e3
        deltas = calculate_skin_depth(rho, mu_r, f)
        assert deltas.shape == (2,)
        assert deltas[0] > deltas[1]  # copper > steel (magnetic)


# ---------------------------------------------------------------------------
# On-axis B-field tests
# ---------------------------------------------------------------------------

class TestSolenoidBFieldOnAxis:
    """Test on-axis magnetic field calculations."""

    def test_center_long_solenoid(self, long_solenoid: SolenoidCoil) -> None:
        """At center of long solenoid, B ≈ μ₀NI/l."""
        current = 10.0
        B = solenoid_b_field_on_axis(long_solenoid, current, 0.0)
        expected = mu_0() * long_solenoid.turns * current / long_solenoid.length
        assert B == pytest.approx(expected, rel=0.01)

    def test_center_short_solenoid(self, short_solenoid: SolenoidCoil) -> None:
        """At center of short solenoid, B < μ₀NI/l (end effects)."""
        current = 10.0
        B = solenoid_b_field_on_axis(short_solenoid, current, 0.0)
        infinite_approx = mu_0() * short_solenoid.turns * current / short_solenoid.length
        assert B < infinite_approx
        assert B > 0

    def test_at_coil_end(self, long_solenoid: SolenoidCoil) -> None:
        """At coil end (z=l/2), B ≈ half of center value."""
        current = 10.0
        B_center = solenoid_b_field_on_axis(long_solenoid, current, 0.0)
        B_end = solenoid_b_field_on_axis(long_solenoid, current, long_solenoid.length / 2)
        assert B_end == pytest.approx(B_center / 2.0, rel=0.05)

    def test_far_from_coil(self, short_solenoid: SolenoidCoil) -> None:
        """Far from coil (|z| ≫ l), B → 0."""
        current = 10.0
        B_far = solenoid_b_field_on_axis(short_solenoid, current, 1.0)  # 1 m away
        B_center = solenoid_b_field_on_axis(short_solenoid, current, 0.0)
        assert B_far < B_center * 0.01  # < 1% of center value

    def test_field_decreases_with_distance(self, short_solenoid: SolenoidCoil) -> None:
        """B-field decreases monotonically with distance from center."""
        current = 10.0
        z_vals = np.linspace(0, 0.5, 10)
        B_vals = solenoid_b_field_on_axis(short_solenoid, current, z_vals)
        assert np.all(np.diff(B_vals) < 0)  # strictly decreasing

    def test_array_input(self, short_solenoid: SolenoidCoil) -> None:
        """On-axis field works with array inputs."""
        current = 10.0
        z_vals = np.array([0.0, 0.025, 0.05])
        B_vals = solenoid_b_field_on_axis(short_solenoid, current, z_vals)
        assert B_vals.shape == (3,)
        assert B_vals[0] > B_vals[1] > B_vals[2]

    def test_negative_current_raises(self, short_solenoid: SolenoidCoil) -> None:
        with pytest.raises(ValueError, match="current"):
            solenoid_b_field_on_axis(short_solenoid, -10.0, 0.0)


# ---------------------------------------------------------------------------
# Off-axis B-field tests
# ---------------------------------------------------------------------------

class TestSolenoidBFieldOffAxis:
    """Test off-axis magnetic field calculations."""

    def test_on_axis_consistency(self, short_solenoid: SolenoidCoil) -> None:
        """At ρ=0, off-axis B_z matches on-axis function, B_rho=0."""
        current = 10.0
        z_vals = np.array([0.0, 0.025, 0.05])
        rho_vals = np.zeros_like(z_vals)

        B_rho, B_z = solenoid_b_field_off_axis(short_solenoid, current, rho_vals, z_vals)
        B_z_on_axis = solenoid_b_field_on_axis(short_solenoid, current, z_vals)

        assert np.allclose(B_rho, 0.0, atol=1e-15)
        assert np.allclose(B_z, B_z_on_axis, rtol=1e-10)

    def test_b_rho_zero_on_axis(self, short_solenoid: SolenoidCoil) -> None:
        """Radial component is exactly zero on the symmetry axis."""
        current = 10.0
        B_rho, _ = solenoid_b_field_off_axis(short_solenoid, current, 0.0, 0.0)
        assert np.asarray(B_rho).item() == pytest.approx(0.0, abs=1e-15)

    def test_b_z_decreases_with_rho(self, short_solenoid: SolenoidCoil) -> None:
        """Axial field changes with radial position (stronger near coil windings)."""
        current = 10.0
        z = np.array([0.0])
        rho_vals = np.linspace(0.0, 0.024, 5)  # inside coil
        _, B_z = solenoid_b_field_off_axis(short_solenoid, current, rho_vals, z)
        # Inside coil, B_z increases with rho (closer to windings)
        assert np.all(np.diff(B_z) > 0)

    def test_b_rho_nonzero_off_axis(self, short_solenoid: SolenoidCoil) -> None:
        """Radial component is non-zero off axis (at z != 0)."""
        current = 10.0
        # At z=0, B_rho=0 by symmetry; test at z != 0
        B_rho, _ = solenoid_b_field_off_axis(short_solenoid, current, 0.015, 0.03)
        assert abs(np.asarray(B_rho).item()) > 1e-15

    def test_field_at_coil_center(self, long_solenoid: SolenoidCoil) -> None:
        """At coil center (ρ=0, z=0), B_z ≈ μ₀NI/l."""
        current = 10.0
        _, B_z = solenoid_b_field_off_axis(long_solenoid, current, 0.0, 0.0)
        expected = mu_0() * long_solenoid.turns * current / long_solenoid.length
        assert np.asarray(B_z).item() == pytest.approx(expected, rel=0.01)

    def test_array_input(self, short_solenoid: SolenoidCoil) -> None:
        """Off-axis field works with array inputs."""
        current = 10.0
        rho_vals = np.array([0.0, 0.010, 0.020])
        z_vals = np.array([0.0, 0.0, 0.0])
        B_rho, B_z = solenoid_b_field_off_axis(short_solenoid, current, rho_vals, z_vals)
        assert B_rho.shape == (3,)
        assert B_z.shape == (3,)
