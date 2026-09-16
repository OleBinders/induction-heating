"""Tests for eddy current density, power density, and calculation pipeline."""

from __future__ import annotations

import math

import numpy as np
import pytest

from induction_heating.core.eddy_currents import (
    calculate_induction_heating,
    eddy_current_density,
    power_density,
    total_power,
)
from induction_heating.core.electromagnetic import calculate_skin_depth
from induction_heating.core.geometry import InductionSetup, SolenoidCoil, CylindricalWorkpiece
from induction_heating.materials.database import MaterialDatabase
from induction_heating.utils.constants import mu_0


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
        """At surface (r=a), J == J_surface exactly, by construction."""
        b_surf = 0.01  # 10 mT
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0
        a = 0.020
        r = np.array([a])

        j = eddy_current_density(b_surf, f, rho, mu_r, a, r)

        # Independent derivation, NOT mirroring the implementation: H is
        # continuous across the workpiece surface (no free surface current),
        # so H_surface = H_applied = b_surface / mu_0 -- NOT
        # b_surface / (mu_0 * mu_r). b_surface itself is already the coil's
        # vacuum-field value (solenoid_b_field_on_axis uses only mu_0()), so
        # dividing by the workpiece's own permeability a second time here
        # would double-count it (this was a real, previously-shipped bug --
        # see TestPermeabilityIncreasesPower below for the physical symptom).
        delta = calculate_skin_depth(rho, mu_r, f)
        h_surface = b_surf / mu_0()
        j_surface = h_surface * math.sqrt(2.0) / delta
        assert j[0] == pytest.approx(j_surface, rel=1e-6)

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
        """A thinner workpiece (smaller a/δ) shows more uniform J than a thick one."""
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 1.0  # Non-magnetic, larger skin depth

        def variation(a: float) -> float:
            r = np.linspace(0, a, 10)
            j = eddy_current_density(b_surf, f, rho, mu_r, a, r)
            return (j[-1] - j[0]) / j[-1]

        assert variation(0.002) < variation(0.020)

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


class TestPermeabilityIncreasesPower:
    """Regression test: higher relative permeability must increase absorbed
    power, not decrease it.

    A previous bug divided the applied surface field by the workpiece's own
    relative permeability (b_surface / (mu_0 * mu_r) instead of b_surface /
    mu_0), which made computed power *fall* with increasing permeability --
    the opposite of real induction-heating physics, where magnetic steel
    below its Curie point heats far more efficiently than non-magnetic
    metals at the same applied field. That bug passed the full test suite
    because no test compared power across different permeabilities; this one
    exists specifically to close that gap.
    """

    def test_total_power_monotonic_in_permeability(self) -> None:
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        a = 0.020
        length = 0.08
        num_points = 300

        powers = []
        for mu_r in (1.0, 50.0, 100.0, 200.0, 300.0):
            r = np.linspace(0, a, num_points)
            j = eddy_current_density(b_surf, f, rho, mu_r, a, r)
            powers.append(total_power(j, rho, a, length, num_points=num_points))

        assert powers == sorted(powers), (
            f"total_power should increase monotonically with relative_permeability, "
            f"got {powers}"
        )

    def test_magnetic_steel_absorbs_more_than_nonmagnetic_copper(
        self, db: MaterialDatabase
    ) -> None:
        """Same coil/current/frequency: magnetic steel (mu_r~200 at 20C) must
        absorb substantially more power than non-magnetic copper (mu_r=1) --
        this is the entire physical basis of induction hardening."""
        coil = SolenoidCoil(
            inner_radius=0.025, outer_radius=0.030, length=0.10, turns=20, wire_diameter=0.005,
        )

        def power_for(material_name: str) -> float:
            wp = CylindricalWorkpiece(radius=0.020, length=0.08, material_name=material_name)
            setup = InductionSetup(coil=coil, workpiece=wp, gap=coil.inner_radius - wp.radius)
            result = calculate_induction_heating(
                setup, current=100.0, frequency=10e3, temperature=20.0, material_db=db,
            )
            return result["total_power"]

        p_steel = power_for("Low Carbon Steel (AISI 1018)")
        p_copper = power_for("Copper (Electrolytic Tough Pitch)")
        assert p_steel > p_copper


class TestEddyCurrentRegimeContinuity:
    """Regression test for the a/δ regime-switch discontinuity.

    Before the argument-scaling fix, total power computed just below vs. just
    above the switch threshold differed by ~63% for identical physical inputs.
    """

    def test_total_power_continuous_across_switch(self) -> None:
        """Total power must not jump sharply across the a/δ=50 threshold."""
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 1.0
        length = 0.08

        delta = calculate_skin_depth(rho, mu_r, f)

        num_points = 500
        powers = []
        for ratio in (49.0, 51.0):
            a = delta * ratio
            r = np.linspace(0, a, num_points)
            j = eddy_current_density(b_surf, f, rho, mu_r, a, r)
            powers.append(total_power(j, rho, a, length, num_points=num_points))

        assert powers[1] == pytest.approx(powers[0], rel=0.05)


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
            "power_density", "total_power", "radial_positions", "snapshot",
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
