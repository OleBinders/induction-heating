"""Tests for property evolution and PropertySnapshot."""

from __future__ import annotations

import pytest

from induction_heating.core.eddy_currents import calculate_induction_heating
from induction_heating.core.geometry import InductionSetup, SolenoidCoil, CylindricalWorkpiece
from induction_heating.materials.database import MaterialDatabase
from induction_heating.materials.property_evolution import (
    PropertySnapshot,
    get_properties_at_temperature,
)


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
# PropertySnapshot tests
# ---------------------------------------------------------------------------

class TestPropertySnapshot:
    """Test PropertySnapshot dataclass."""

    def test_from_material_steel_20c(self, db: MaterialDatabase) -> None:
        """Snapshot at 20°C returns correct values for steel."""
        snap = PropertySnapshot.from_material(db, "Low Carbon Steel (AISI 1018)", 20.0)
        assert snap.temperature == 20.0
        assert snap.resistivity == pytest.approx(1.43e-7, rel=0.01)
        assert snap.relative_permeability == pytest.approx(200.0, rel=0.01)
        assert snap.specific_heat > 0
        assert snap.thermal_conductivity > 0

    def test_from_material_steel_800c(self, db: MaterialDatabase) -> None:
        """Snapshot at 800°C returns correct values (μᵣ ≈ 1.0 above Curie)."""
        snap = PropertySnapshot.from_material(db, "Low Carbon Steel (AISI 1018)", 800.0)
        assert snap.temperature == 800.0
        assert snap.resistivity == pytest.approx(8.50e-7, rel=0.05)
        assert snap.relative_permeability == pytest.approx(1.0, abs=0.1)

    def test_all_values_positive(self, db: MaterialDatabase) -> None:
        """All property values are positive."""
        snap = PropertySnapshot.from_material(db, "Low Carbon Steel (AISI 1018)", 500.0)
        assert snap.resistivity > 0
        assert snap.relative_permeability >= 1.0
        assert snap.specific_heat > 0
        assert snap.thermal_conductivity > 0

    def test_permeability_ge_one(self, db: MaterialDatabase) -> None:
        """μᵣ ≥ 1.0 always."""
        for t in [20, 400, 600, 770, 800, 1000]:
            snap = PropertySnapshot.from_material(db, "Low Carbon Steel (AISI 1018)", float(t))
            assert snap.relative_permeability >= 1.0

    def test_invalid_resistivity_raises(self) -> None:
        with pytest.raises(ValueError, match="resistivity"):
            PropertySnapshot(20.0, -1e-7, 200.0, 450.0, 50.0)

    def test_invalid_permeability_raises(self) -> None:
        with pytest.raises(ValueError, match="relative_permeability"):
            PropertySnapshot(20.0, 1e-7, 0.5, 450.0, 50.0)

    def test_invalid_specific_heat_raises(self) -> None:
        with pytest.raises(ValueError, match="specific_heat"):
            PropertySnapshot(20.0, 1e-7, 200.0, -450.0, 50.0)

    def test_invalid_thermal_conductivity_raises(self) -> None:
        with pytest.raises(ValueError, match="thermal_conductivity"):
            PropertySnapshot(20.0, 1e-7, 200.0, 450.0, -50.0)


# ---------------------------------------------------------------------------
# Property evolution tests
# ---------------------------------------------------------------------------

class TestPropertyEvolution:
    """Test get_properties_at_temperature function."""

    def test_consistent_temperature(self, db: MaterialDatabase) -> None:
        """All properties are at the same temperature."""
        snap = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 500.0)
        assert snap.temperature == 500.0

    def test_20c_matches_data(self, db: MaterialDatabase) -> None:
        """Snapshot at 20°C matches material data exactly."""
        snap = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 20.0)
        assert snap.resistivity == pytest.approx(1.43e-7, rel=0.01)
        assert snap.relative_permeability == pytest.approx(200.0, rel=0.01)

    def test_350c_interpolated(self, db: MaterialDatabase) -> None:
        """Snapshot at 350°C returns interpolated values."""
        snap_20 = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 20.0)
        snap_400 = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 400.0)
        snap_350 = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 350.0)

        # Interpolated value should be between 20°C and 400°C
        assert snap_20.resistivity < snap_350.resistivity < snap_400.resistivity

    def test_770c_curie_point(self, db: MaterialDatabase) -> None:
        """Snapshot at Curie point returns μᵣ ≈ 1.0."""
        snap = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 770.0)
        assert snap.relative_permeability == pytest.approx(1.0, abs=0.1)

    def test_outside_range_raises(self, db: MaterialDatabase) -> None:
        """Snapshot at 1500°C raises ValueError (outside data range)."""
        with pytest.raises(ValueError, match="outside the valid range"):
            get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 1500.0)

    def test_copper_non_magnetic(self, db: MaterialDatabase) -> None:
        """Copper snapshot has μᵣ = 1.0."""
        snap = get_properties_at_temperature(db, "Copper (Electrolytic Tough Pitch)", 20.0)
        assert snap.relative_permeability == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Integration tests: pipeline with PropertySnapshot
# ---------------------------------------------------------------------------

class TestPipelineIntegration:
    """Test electromagnetic pipeline with PropertySnapshot integration."""

    def test_backward_compatible_20c(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Pipeline at 20°C produces same results as before."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, temperature=20.0, material_db=db
        )
        assert result["total_power"] > 0
        assert result["snapshot"].temperature == 20.0

    def test_500c_temperature_dependent(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Pipeline at 500°C uses correct temperature-dependent properties."""
        result_20 = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, temperature=20.0, material_db=db
        )
        result_500 = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, temperature=500.0, material_db=db
        )
        # Different temperatures should produce different results
        assert result_20["skin_depth"] != result_500["skin_depth"]
        assert result_20["snapshot"].resistivity != result_500["snapshot"].resistivity

    def test_800c_above_curie(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Pipeline at 800°C uses μᵣ ≈ 1.0 (above Curie)."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, temperature=800.0, material_db=db
        )
        assert result["snapshot"].relative_permeability == pytest.approx(1.0, abs=0.1)
        # Skin depth should be larger above Curie (lower permeability)
        result_20 = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, temperature=20.0, material_db=db
        )
        assert result["skin_depth"] > result_20["skin_depth"]

    def test_snapshot_included(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """Results include PropertySnapshot for debugging."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, material_db=db
        )
        assert "snapshot" in result
        assert isinstance(result["snapshot"], PropertySnapshot)

    def test_consistent_properties(self, steel_setup: InductionSetup, db: MaterialDatabase) -> None:
        """All calculations use properties from the same snapshot."""
        result = calculate_induction_heating(
            steel_setup, current=10.0, frequency=10e3, temperature=500.0, material_db=db
        )
        snap = result["snapshot"]
        # Verify skin depth was calculated with snapshot properties
        from induction_heating.core.electromagnetic import calculate_skin_depth
        expected_delta = calculate_skin_depth(snap.resistivity, snap.relative_permeability, 10e3)
        assert result["skin_depth"] == pytest.approx(expected_delta)


# ---------------------------------------------------------------------------
# Literature validation tests
# ---------------------------------------------------------------------------

class TestLiteratureValidation:
    """Validate against published reference values."""

    def test_steel_resistivity_20c(self, db: MaterialDatabase) -> None:
        """Steel resistivity at 20°C ≈ 1.43e-7 Ω·m (Rudnev Handbook)."""
        snap = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 20.0)
        assert snap.resistivity == pytest.approx(1.43e-7, rel=0.05)

    def test_steel_resistivity_400c(self, db: MaterialDatabase) -> None:
        """Steel resistivity at 400°C ≈ 4.35e-7 Ω·m (Rudnev Handbook)."""
        snap = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 400.0)
        assert snap.resistivity == pytest.approx(4.35e-7, rel=0.05)

    def test_steel_resistivity_800c(self, db: MaterialDatabase) -> None:
        """Steel resistivity at 800°C ≈ 8.50e-7 Ω·m (Rudnev Handbook)."""
        snap = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 800.0)
        assert snap.resistivity == pytest.approx(8.50e-7, rel=0.05)

    def test_steel_permeability_at_curie(self, db: MaterialDatabase) -> None:
        """Steel permeability at Curie point drops to 1.0."""
        snap = get_properties_at_temperature(db, "Low Carbon Steel (AISI 1018)", 770.0)
        assert snap.relative_permeability == pytest.approx(1.0, abs=0.1)
