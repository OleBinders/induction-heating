"""Integration tests for the full calculation pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from induction_heating.core.eddy_currents import calculate_induction_heating
from induction_heating.core.geometry import CylindricalWorkpiece, InductionSetup, SolenoidCoil
from induction_heating.materials.database import MaterialDatabase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db() -> MaterialDatabase:
    return MaterialDatabase()


@pytest.fixture
def steel_setup(db: MaterialDatabase) -> InductionSetup:
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
# Integration tests
# ---------------------------------------------------------------------------

class TestPipelineIntegration:
    """Test full calculation pipeline produces physically reasonable results."""

    def test_skin_depth_decreases_with_frequency(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Higher frequency → smaller skin depth."""
        result_10k = calculate_induction_heating(steel_setup, current=100, frequency=10e3, material_db=db)
        result_50k = calculate_induction_heating(steel_setup, current=100, frequency=50e3, material_db=db)
        assert result_50k["skin_depth"] < result_10k["skin_depth"]

    def test_skin_depth_increases_with_resistivity(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Higher resistivity → larger skin depth."""
        # Steel at 20°C vs 800°C (higher resistivity at higher temp)
        result_20 = calculate_induction_heating(steel_setup, current=100, frequency=10e3, temperature=20.0, material_db=db)
        result_800 = calculate_induction_heating(steel_setup, current=100, frequency=10e3, temperature=800.0, material_db=db)
        assert result_800["skin_depth"] > result_20["skin_depth"]

    def test_skin_depth_decreases_with_permeability(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Higher permeability → smaller skin depth."""
        # Below Curie (high μᵣ) vs above Curie (μᵣ=1)
        result_below = calculate_induction_heating(steel_setup, current=100, frequency=10e3, temperature=20.0, material_db=db)
        result_above = calculate_induction_heating(steel_setup, current=100, frequency=10e3, temperature=800.0, material_db=db)
        assert result_below["skin_depth"] < result_above["skin_depth"]

    def test_total_power_increases_with_frequency(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Higher frequency → more power absorbed."""
        result_10k = calculate_induction_heating(steel_setup, current=100, frequency=10e3, material_db=db)
        result_50k = calculate_induction_heating(steel_setup, current=100, frequency=50e3, material_db=db)
        assert result_50k["total_power"] > result_10k["total_power"]

    def test_total_power_increases_with_current(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Higher current → more power absorbed."""
        result_50a = calculate_induction_heating(steel_setup, current=50, frequency=10e3, material_db=db)
        result_100a = calculate_induction_heating(steel_setup, current=100, frequency=10e3, material_db=db)
        assert result_100a["total_power"] > result_50a["total_power"]

    def test_power_density_peaks_at_surface(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Power density peaks at workpiece surface (skin effect)."""
        result = calculate_induction_heating(steel_setup, current=100, frequency=10e3, material_db=db)
        p = result["power_density"]
        r = result["radial_positions"]
        wp_radius = steel_setup.workpiece.radius

        # Find indices inside workpiece
        inside = r <= wp_radius
        assert np.any(inside), "radial_positions should always include points inside the workpiece"
        p_inside = p[inside]
        r_inside = r[inside]
        # Peak should be near surface (largest r)
        peak_idx = np.argmax(p_inside)
        assert r_inside[peak_idx] > np.mean(r_inside)

    def test_permeability_drops_at_curie(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Permeability drops to ~1.0 at Curie point."""
        result_below = calculate_induction_heating(steel_setup, current=100, frequency=10e3, temperature=20.0, material_db=db)
        result_above = calculate_induction_heating(steel_setup, current=100, frequency=10e3, temperature=800.0, material_db=db)
        # Skin depth should be much larger above Curie (lower permeability)
        assert result_above["skin_depth"] > result_below["skin_depth"] * 5

    def test_all_results_positive(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """All calculation results are positive."""
        result = calculate_induction_heating(steel_setup, current=100, frequency=10e3, material_db=db)
        assert result["skin_depth"] > 0
        assert result["b_field_surface"] > 0
        assert result["total_power"] > 0
        assert np.all(result["power_density"] >= 0)
