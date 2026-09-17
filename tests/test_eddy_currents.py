"""Tests for eddy current density, power density, and calculation pipeline."""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import special

from induction_heating.core.eddy_currents import (
    calculate_induction_heating,
    calculate_induction_heating_2d,
    eddy_current_density,
    eddy_current_density_2d,
    power_density,
    total_power,
    total_power_2d,
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
        """At surface (r=a), J == J_surface * |Bep(qa)| / |Be(qa)|.

        J is *not* exactly j_surface: j_surface is the order-0 boundary
        condition on H(a), while J(r) = -dH/dr introduces the order-1
        (derivative) Kelvin function in the numerator. The ratio computed
        here comes from an independent call to scipy.special.kelvin (the
        same one the production code uses, since that formula -- not this
        particular scipy call -- is what's being locked in as a regression
        guard; the real independent verification is the Maxwell's-equations
        derivation, confirmed by a from-scratch ODE shooting-method solve).
        """
        b_surf = 0.01  # 10 mT
        f = 10e3
        rho = 1.43e-7
        # Non-magnetic (mu_r=1) so a/delta ~ 10.5 for a=0.020m -- comfortably
        # within the exact/Kelvin-function branch (a/delta <= 50). mu_r=200
        # at this frequency/radius (a/delta ~ 149) would instead exercise the
        # exponential thick-workpiece branch, where J(a) == j_surface exactly
        # by construction and this ratio-based check would not be testing
        # the code path this test is meant to guard.
        mu_r = 1.0
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

        q = math.sqrt(2.0) / delta
        kelvin_a = special.kelvin(q * a)
        bep_a = abs(kelvin_a[2])  # order-1 (derivative) magnitude -- numerator
        be_a = abs(kelvin_a[0])  # order-0 magnitude -- denominator
        expected = j_surface * bep_a / be_a

        assert j[0] == pytest.approx(expected, rel=1e-6)

    def test_current_vanishes_at_axis(self) -> None:
        """J(r=0) must be exactly zero: an azimuthal eddy-current loop of
        zero radius has no circumference to carry current. This is the
        physical law violated by the order-0-in-the-numerator bug (which
        gave J(0)/J(a) ~ 0.75 at a/delta ~ 1.6) and is the most important
        regression guard from that fix."""
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0

        # Exercise several a/delta ratios, all comfortably within the exact
        # (Kelvin-function) branch (a/delta <= 50).
        delta = calculate_skin_depth(rho, mu_r, f)
        for ratio in (0.5, 1.6, 5.0, 20.0, 49.0):
            a = delta * ratio
            j = eddy_current_density(b_surf, f, rho, mu_r, a, np.array([0.0]))
            assert j[0] == pytest.approx(0.0, abs=1e-6)

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
        """A thinner workpiece (smaller a/δ) shows more uniform J than a thick one.

        Uses the midpoint radius (a/2), not the center (r=0), as the
        reference point: J(r=0) is mathematically exactly 0 regardless of
        a/delta (see TestEddyCurrentDensity.test_current_vanishes_at_axis),
        so a variation metric anchored at r=0 is trivially 1.0 for every
        a/delta and can no longer distinguish "thin" from "thick" -- that
        degenerate case is exactly what this test hit before this change.
        """
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 1.0  # Non-magnetic, larger skin depth

        def variation(a: float) -> float:
            r = np.linspace(0, a, 10)
            j = eddy_current_density(b_surf, f, rho, mu_r, a, r)
            j_mid = j[len(j) // 2]
            return (j[-1] - j_mid) / j[-1]

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


# ---------------------------------------------------------------------------
# 2D (r, z) eddy current density tests
# ---------------------------------------------------------------------------

class TestEddyCurrentDensity2D:
    """Test the 2D (z, r) eddy current density grid.

    ``eddy_current_density_2d`` is a "locally quasi-1D per axial slice"
    approximation (see its docstring) built on top of the already-validated,
    unmodified 1D ``eddy_current_density``. These tests check basic shape/
    positivity properties, and -- importantly -- tie the new 2D code back to
    the existing validated 1D physics via a direct consistency check, rather
    than only asserting the 2D function against itself.
    """

    def test_output_shape(self) -> None:
        """Output shape is (n_z, n_r)."""
        n_z, n_r = 7, 50
        b_surface_z = np.full(n_z, 0.01)
        r = np.linspace(0, 0.020, n_r)

        j_zr = eddy_current_density_2d(
            b_surface_z=b_surface_z,
            frequency=10e3,
            resistivity_z=1.43e-7,
            relative_permeability_z=200.0,
            workpiece_radius=0.020,
            radial_positions=r,
        )
        assert j_zr.shape == (n_z, n_r)

    def test_positive(self) -> None:
        """Current density magnitude is positive everywhere."""
        b_surface_z = np.array([0.005, 0.008, 0.01, 0.008, 0.005])
        r = np.linspace(0, 0.020, 30)

        j_zr = eddy_current_density_2d(
            b_surface_z=b_surface_z,
            frequency=10e3,
            resistivity_z=1.43e-7,
            relative_permeability_z=200.0,
            workpiece_radius=0.020,
            radial_positions=r,
        )
        assert np.all(j_zr > 0)

    def test_scalar_properties_broadcast_per_slice(self) -> None:
        """Scalar resistivity/permeability apply uniformly to every slice."""
        b_surface_z = np.full(5, 0.01)
        r = np.linspace(0, 0.020, 20)

        j_zr = eddy_current_density_2d(
            b_surface_z=b_surface_z,
            frequency=10e3,
            resistivity_z=1.43e-7,
            relative_permeability_z=200.0,
            workpiece_radius=0.020,
            radial_positions=r,
        )
        # Same b_surface at every slice + scalar properties -> every row identical.
        for i in range(1, j_zr.shape[0]):
            assert j_zr[i, :] == pytest.approx(j_zr[0, :])

    def test_consistency_with_1d_function_at_matching_slice(self) -> None:
        """A single axial slice of the 2D function must reproduce the 1D
        function's output exactly for the same inputs -- the 2D function is
        just a per-slice loop over the same validated Kelvin-function
        solution, so there is no room for divergence at a single slice."""
        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0
        a = 0.020
        r = np.linspace(0, a, 50)

        j_1d = eddy_current_density(b_surf, f, rho, mu_r, a, r)

        j_2d = eddy_current_density_2d(
            b_surface_z=np.array([b_surf]),
            frequency=f,
            resistivity_z=rho,
            relative_permeability_z=mu_r,
            workpiece_radius=a,
            radial_positions=r,
        )
        assert j_2d[0, :] == pytest.approx(j_1d, rel=1e-10)

    def test_consistency_with_1d_pipeline_at_coil_center(
        self, steel_setup: InductionSetup, db: MaterialDatabase
    ) -> None:
        """For a workpiece centered on the coil's axial middle, the 2D
        pipeline's center-slice power profile should be reasonably close to
        the 1D pipeline's profile (evaluated at z=0) for the same inputs --
        both should be probing essentially the same physical field. This
        ties the new 2D code back to already-validated physics instead of
        just checking it against itself."""
        current = 100.0
        frequency = 10e3

        result_1d = calculate_induction_heating(
            steel_setup, current, frequency, material_db=db
        )
        result_2d = calculate_induction_heating_2d(
            steel_setup, current, frequency, material_db=db, num_axial_points=41,
        )

        z_center_idx = int(np.argmin(np.abs(result_2d["axial_positions"])))
        p_2d_center = result_2d["power_density"][z_center_idx, :]
        p_1d = power_density(result_1d["current_density"], result_1d["snapshot"].resistivity)

        # Not a tight match (the 2D pipeline uses the true off-axis surface
        # field, the 1D pipeline uses the on-axis proxy) but should be the
        # same order of magnitude / broadly consistent shape.
        assert p_2d_center == pytest.approx(p_1d, rel=0.5)


# ---------------------------------------------------------------------------
# 2D total power integration tests
# ---------------------------------------------------------------------------

class TestTotalPower2D:
    """Test the nested radial-then-axial power integration."""

    def test_positive(self) -> None:
        """Total power is positive."""
        n_z, n_r = 10, 50
        r = np.linspace(0, 0.020, n_r)
        z = np.linspace(-0.04, 0.04, n_z)
        p_rz = np.full((n_z, n_r), 1e8)

        p_total = total_power_2d(p_rz, r, z)
        assert p_total > 0

    def test_returns_scalar_float(self) -> None:
        """Return value is a plain float, not an array."""
        r = np.linspace(0, 0.020, 20)
        z = np.linspace(-0.04, 0.04, 5)
        p_rz = np.full((5, 20), 1e8)

        p_total = total_power_2d(p_rz, r, z)
        assert isinstance(p_total, float)

    def test_uniform_along_z_matches_1d_total_power_times_length(self) -> None:
        """If power density is identical at every axial slice, the 2D
        integral must equal the 1D radial integral scaled by the axial
        length -- a direct consistency check against the existing,
        validated ``total_power`` (which scales by workpiece_length)."""
        a = 0.020
        length = 0.08
        n_r = 300
        n_z = 21
        r = np.linspace(0, a, n_r)
        z = np.linspace(-length / 2.0, length / 2.0, n_z)

        b_surf = 0.01
        f = 10e3
        rho = 1.43e-7
        mu_r = 200.0
        j_r = eddy_current_density(b_surf, f, rho, mu_r, a, r)
        p_r = power_density(j_r, rho)

        p_rz = np.tile(p_r, (n_z, 1))

        p_2d = total_power_2d(p_rz, r, z)
        p_1d = total_power(j_r, rho, a, length, num_points=n_r)

        assert p_2d == pytest.approx(p_1d, rel=1e-3)

    def test_scales_with_axial_extent(self) -> None:
        """Doubling the axial extent (with the same power density
        everywhere) doubles total power."""
        r = np.linspace(0, 0.020, 100)
        p_rz_short = np.full((5, 100), 1e8)
        p_rz_long = np.full((5, 100), 1e8)

        z_short = np.linspace(-0.02, 0.02, 5)
        z_long = np.linspace(-0.04, 0.04, 5)

        p_short = total_power_2d(p_rz_short, r, z_short)
        p_long = total_power_2d(p_rz_long, r, z_long)

        assert p_long == pytest.approx(2.0 * p_short, rel=1e-6)


# ---------------------------------------------------------------------------
# calculate_induction_heating_2d pipeline tests
# ---------------------------------------------------------------------------

class TestCalculationPipeline2D:
    """Test the end-to-end 2D induction heating pipeline."""

    def test_pipeline_returns_all_keys(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Pipeline returns all expected keys."""
        result = calculate_induction_heating_2d(
            steel_setup, current=10.0, frequency=10e3, material_db=db
        )
        expected_keys = {
            "skin_depth", "b_field_surface_z", "current_density",
            "power_density", "total_power", "radial_positions",
            "axial_positions", "snapshot",
        }
        assert set(result.keys()) == expected_keys

    def test_grid_shapes(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """current_density/power_density grids match (n_z, n_r)."""
        n_r, n_z = 80, 15
        result = calculate_induction_heating_2d(
            steel_setup, current=10.0, frequency=10e3, material_db=db,
            num_radial_points=n_r, num_axial_points=n_z,
        )
        assert result["current_density"].shape == (n_z, n_r)
        assert result["power_density"].shape == (n_z, n_r)
        assert result["b_field_surface_z"].shape == (n_z,)
        assert result["radial_positions"].shape == (n_r,)
        assert result["axial_positions"].shape == (n_z,)

    def test_positive_total_power(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Total power is positive."""
        result = calculate_induction_heating_2d(
            steel_setup, current=10.0, frequency=10e3, material_db=db
        )
        assert result["total_power"] > 0

    def test_total_power_same_order_of_magnitude_as_1d(
        self, steel_setup: InductionSetup, db: MaterialDatabase
    ) -> None:
        """This is a refinement of the existing on-axis calculation, not a
        wholesale change -- total power should stay in a similar order of
        magnitude, not jump by orders of magnitude."""
        result_1d = calculate_induction_heating(
            steel_setup, current=100.0, frequency=10e3, material_db=db
        )
        result_2d = calculate_induction_heating_2d(
            steel_setup, current=100.0, frequency=10e3, material_db=db
        )
        ratio = result_2d["total_power"] / result_1d["total_power"]
        assert 0.1 < ratio < 10.0

    def test_axial_falloff_power_lower_near_coil_edge_than_center(
        self, db: MaterialDatabase
    ) -> None:
        """The actual point of Phase 1: power density near/beyond the coil's
        axial extent must be measurably LOWER than at the coil's axial
        center, for the same radial position. Without this, the "no axial
        dependence" bug is not actually fixed. Uses a workpiece as long as
        the coil so slices near its ends sit right at/beyond the coil's
        axial extent, where the field is known to fall off sharply."""
        coil = SolenoidCoil(
            inner_radius=0.025, outer_radius=0.030, length=0.10, turns=20, wire_diameter=0.005,
        )
        wp = CylindricalWorkpiece(
            radius=0.020, length=0.10, material_name="Low Carbon Steel (AISI 1018)",
        )
        setup = InductionSetup(coil=coil, workpiece=wp, gap=coil.inner_radius - wp.radius)

        result = calculate_induction_heating_2d(
            setup, current=100.0, frequency=10e3, material_db=db, num_axial_points=41,
        )
        z = result["axial_positions"]
        p_zr = result["power_density"]

        z_center_idx = int(np.argmin(np.abs(z)))
        z_edge_idx = int(np.argmax(z))  # far end of the workpiece (coil edge)

        # Compare at the workpiece surface (last radial index), where power
        # density is largest and the skin-effect signal is clearest.
        p_center_surface = p_zr[z_center_idx, -1]
        p_edge_surface = p_zr[z_edge_idx, -1]

        assert p_edge_surface < p_center_surface

    def test_workpiece_extends_beyond_coil_power_falls_further(
        self, db: MaterialDatabase
    ) -> None:
        """A workpiece that extends past the coil's ends should show even
        lower power density at its extreme ends than a workpiece confined to
        the coil's length -- confirming the falloff continues realistically
        past the coil's active length rather than plateauing."""
        coil = SolenoidCoil(
            inner_radius=0.025, outer_radius=0.030, length=0.10, turns=20, wire_diameter=0.005,
        )
        wp = CylindricalWorkpiece(
            radius=0.020, length=0.16, material_name="Low Carbon Steel (AISI 1018)",
        )
        setup = InductionSetup(coil=coil, workpiece=wp, gap=coil.inner_radius - wp.radius)
        assert setup.workpiece_extends_beyond_coil

        result = calculate_induction_heating_2d(
            setup, current=100.0, frequency=10e3, material_db=db, num_axial_points=41,
        )
        p_zr = result["power_density"]
        z_center_idx = int(np.argmin(np.abs(result["axial_positions"])))

        p_center_surface = p_zr[z_center_idx, -1]
        p_end_surface = p_zr[0, -1]  # extreme end, well beyond the coil

        assert p_end_surface < p_center_surface
        assert np.all(np.isfinite(p_zr))
