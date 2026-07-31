"""Tests for eddy current density, power density, and calculation pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from induction_heating.core.eddy_currents import (
    calculate_induction_heating,
    eddy_current_density,
    power_density,
    total_power,
)
from induction_heating.core.geometry import InductionSetup, SolenoidCoil, CylindricalWorkpiece
from induction_heating.materials.database import MaterialDatabase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db() -> MaterialDatabase:
    return MaterialDatabase()


@pytest.fixture
def steel_setup(db: MaterialDatabase) -> InductionSetup:
    """Standard steel workpiece inside solenoid coil."""
    coil = SolenoidCoil(
        inner_radius=0.025,
        outer_radius=0.030,
        length=0.10,
        turns=20,
        wire_diameter=0.005,
    )
    wp = CylindricalWorkpiece(
        radius=0.020,
        length=0.08,
        material_name="Low Carbon Steel (AISI 1018)",
    )
    gap = coil.inner_radius - wp.radius
    return InductionSetup(coil=coil, workpiece=wp, gap=gap)


# ---------------------------------------------------------------------------
# Eddy current density tests
# ---------------------------------------------------------------------------

class TestEddyCurrentDensity:
    """Test eddy current density distribution."""

    def test_surface_value(self) -> None:
        """At surface (r=a), J ≈ J_surface."""
        b_surf = 0.01  # 10 mT
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0
        a = 0.020
        r = np.array([a])

        j = eddy_current_density(b_surf, f, rho, mu_r, a, r)
        # J_surface = ω * B * a / (2ρ)
        import math
        omega = 2 * math.pi * f
        j_surface = omega * b_surf * a / (2 * rho)
        assert j[0] == pytest.approx(j_surface, rel=0.1)

    def test_center_less_than_surface(self) -> None:
        """At center (r=0), J < J_surface (skin effect)."""
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0
        a = 0.020
        r = np.array([0.0, a])

        j = eddy_current_density(b_surf, f, rho, mu_r, a, r)
        assert j[0] < j[1]

    def test_exponential_decay_thick_workpiece(self) -> None:
        """For a/δ > 4, J drops exponentially from surface."""
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0
        a = 0.020  # a/δ ≈ 150, very thick

        r = np.linspace(0, a, 10)
        j = eddy_current_density(b_surf, f, rho, mu_r, a, r)

        # J should decrease monotonically from center to surface
        # (actually increases from center to surface for thick workpiece)
        assert j[-1] > j[0]  # surface > center

    def test_uniform_thin_workpiece(self) -> None:
        """For a/δ ≤ 4, J is more uniform across cross-section."""
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 1.0  # Non-magnetic, larger skin depth
        a = 0.005  # Small radius

        r = np.linspace(0, a, 10)
        j = eddy_current_density(b_surf, f, rho, mu_r, a, r)

        # Variation should be smaller for thin workpiece
        variation = (j[-1] - j[0]) / j[-1]
        assert variation < 0.5  # Less than 50% variation

    def test_density_increases_with_frequency(self) -> None:
        """Higher frequency → higher current density."""
        b_surf = 0.01
        rho = 1.43e-7
        mu_r = 200.0
        a = 0.020
        r = np.array([a])

        j_10k = eddy_current_density(b_surf, 10e3, rho, mu_r, a, r)
        j_50k = eddy_current_density(b_surf, 50e3, rho, mu_r, a, r)
        assert j_50k[0] > j_10k[0]

    def test_density_increases_with_b_field(self) -> None:
        """Higher B-field → higher current density."""
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0
        a = 0.020
        r = np.array([a])

        j_low = eddy_current_density(0.005, f, rho, mu_r, a, r)
        j_high = eddy_current_density(0.010, f, rho, mu_r, a, r)
        assert j_high[0] > j_low[0]


# ---------------------------------------------------------------------------
# Power density tests
# ---------------------------------------------------------------------------

class TestPowerDensity:
    """Test power density calculations."""

    def test_always_positive(self) -> None:
        """Power density is always positive (J²ρ ≥ 0)."""
        j = np.array([100.0, 200.0, 50.0])
        rho = 1.43e-7
        p = power_density(j, rho)
        assert np.all(p > 0)

    def test_quadratic_with_current(self) -> None:
        """Power density scales as J²."""
        j = np.array([100.0])
        rho = 1.43e-7
        p1 = power_density(j, rho)
        p2 = power_density(2 * j, rho)
        assert p2[0] == pytest.approx(4 * p1[0])

    def test_linear_with_resistivity(self) -> None:
        """Power density scales linearly with resistivity."""
        j = np.array([100.0])
        p1 = power_density(j, 1.43e-7)
        p2 = power_density(j, 2.86e-7)
        assert p2[0] == pytest.approx(2 * p1[0])


# ---------------------------------------------------------------------------
# Total power tests
# ---------------------------------------------------------------------------

class TestTotalPower:
    """Test total power integration."""

    def test_positive(self, steel_setup: InductionSetup) -> None:
        """Total power is positive."""
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0
        a = steel_setup.workpiece.radius
        r = np.linspace(0, a, 200)

        j = eddy_current_density(b_surf, f, rho, mu_r, a, r)
        p = total_power(j, rho, a, steel_setup.workpiece.length)
        assert p > 0

    def test_increases_with_frequency(self, steel_setup: InductionSetup) -> None:
        """Total power increases with frequency."""
        b_surf = 0.01
        rho = 1.43e-7
        mu_r = 200.0
        a = steel_setup.workpiece.radius
        r = np.linspace(0, a, 200)

        j_10k = eddy_current_density(b_surf, 10e3, rho, mu_r, a, r)
        j_50k = eddy_current_density(b_surf, 50e3, rho, mu_r, a, r)

        p_10k = total_power(j_10k, rho, a, steel_setup.workpiece.length)
        p_50k = total_power(j_50k, rho, a, steel_setup.workpiece.length)
        assert p_50k > p_10k

    def test_increases_with_current(self, steel_setup: InductionSetup) -> None:
        """Total power increases with B-field (proportional to current)."""
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0
        a = steel_setup.workpiece.radius
        r = np.linspace(0, a, 200)

        j_low = eddy_current_density(0.005, f, rho, mu_r, a, r)
        j_high = eddy_current_density(0.010, f, rho, mu_r, a, r)

        p_low = total_power(j_low, rho, a, steel_setup.workpiece.length)
        p_high = total_power(j_high, rho, a, steel_setup.workpiece.length)
        assert p_high > p_low


# ---------------------------------------------------------------------------
# Pipeline tests
# ---------------------------------------------------------------------------

class TestCalculationPipeline:
    """Test end-to-end induction heating pipeline."""

    def test_pipeline_returns_all_keys(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Pipeline returns all expected keys."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, material_db=db
        )
        expected_keys = {
            "skin_depth", "b_field_surface", "current_density",
            "power_density", "total_power", "radial_positions",
        }
        assert set(result.keys()) == expected_keys

    def test_positive_total_power(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Total power is positive."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, material_db=db
        )
        assert result["total_power"] > 0

    def test_positive_b_field(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """B-field is positive."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, material_db=db
        )
        assert result["b_field_surface"] > 0

    def test_positive_skin_depth(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Skin depth is positive."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, material_db=db
        )
        assert result["skin_depth"] > 0

    def test_power_density_array_positive(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Power density array is all positive."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, material_db=db
        )
        assert np.all(result["power_density"] > 0)

    def test_current_density_surface_peak(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Current density peaks at surface for thick workpiece."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, material_db=db
        )
        j = result["current_density"]
        assert j[-1] > j[0]  # surface > center

    def test_temperature_affects_results(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Different temperatures produce different results."""
        result_20 = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, temperature=20.0, material_db=db
        )
        result_500 = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, temperature=500.0, material_db=db
        )
        # Resistivity changes with temperature, so results should differ
        assert result_20["skin_depth"] != result_500["skin_depth"]

    def test_frequency_range_10_to_50khz(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Pipeline works at 10 kHz and 50 kHz."""
        for f in [10e3, 25e3, 50e3]:
            result = calculate_induction_heating(
                steel_setup, current=10.0, frequency=f, material_db=db
            )
            assert result["total_power"] > 0
            assert result["skin_depth"] > 0
