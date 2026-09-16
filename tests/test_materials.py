"""Tests for the material library (schemas, database, interpolation)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from induction_heating.materials.database import MaterialDatabase
from induction_heating.materials.schemas import Material, TemperatureDataPoint


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestTemperatureDataPoint:
    """Test TemperatureDataPoint schema."""

    def test_valid_point(self) -> None:
        pt = TemperatureDataPoint(temperature=20.0, value=1.68e-8)
        assert pt.temperature == 20.0
        assert pt.value == 1.68e-8

    def test_missing_field(self) -> None:
        with pytest.raises(ValidationError):
            TemperatureDataPoint(temperature=20.0)


class TestMaterialSchema:
    """Test Material schema validation."""

    def test_valid_magnetic_material(self) -> None:
        data = {
            "name": "Test Steel",
            "category": "steel",
            "density": 7870,
            "curie_temperature": 770,
            "resistivity": {
                "data": [
                    {"temperature": 20, "value": 1.43e-7},
                    {"temperature": 800, "value": 8.50e-7},
                ],
                "unit": "ohm*m",
                "temperature_unit": "degC",
            },
            "relative_permeability": {
                "data": [
                    {"temperature": 20, "value": 200},
                    {"temperature": 770, "value": 1.0},
                ],
                "unit": "dimensionless",
                "temperature_unit": "degC",
            },
        }
        mat = Material.model_validate(data)
        assert mat.name == "Test Steel"
        assert mat.curie_temperature == 770
        assert mat.relative_permeability is not None

    def test_valid_non_magnetic_material(self) -> None:
        data = {
            "name": "Test Copper",
            "category": "copper",
            "density": 8960,
            "curie_temperature": None,
            "resistivity": {
                "data": [{"temperature": 20, "value": 1.68e-8}],
                "unit": "ohm*m",
            },
            "relative_permeability": None,
        }
        mat = Material.model_validate(data)
        assert mat.curie_temperature is None
        assert mat.relative_permeability is None

    def test_missing_required_field(self) -> None:
        data = {"name": "Test", "category": "steel"}
        with pytest.raises(ValidationError):
            Material.model_validate(data)


# ---------------------------------------------------------------------------
# Database tests
# ---------------------------------------------------------------------------

class TestMaterialDatabase:
    """Test MaterialDatabase loading and querying."""

    @pytest.fixture
    def db(self) -> MaterialDatabase:
        return MaterialDatabase()

    def test_loads_all_materials(self, db: MaterialDatabase) -> None:
        """Database loads all 5 material files."""
        assert len(db.list_materials()) == 5

    def test_list_materials(self, db: MaterialDatabase) -> None:
        names = db.list_materials()
        assert len(names) == 5
        assert any("Low Carbon" in n for n in names)
        assert any("Copper" in n for n in names)

    def test_get_material_by_name(self, db: MaterialDatabase) -> None:
        mat = db.get_material("Low Carbon Steel (AISI 1018)")
        assert mat.category == "steel"
        assert mat.curie_temperature == 770

    def test_get_material_case_insensitive(self, db: MaterialDatabase) -> None:
        mat = db.get_material("low carbon steel")
        assert mat.category == "steel"

    def test_get_material_not_found(self, db: MaterialDatabase) -> None:
        with pytest.raises(KeyError, match="not found"):
            db.get_material("Nonexistent Material")


# ---------------------------------------------------------------------------
# Interpolation tests
# ---------------------------------------------------------------------------

class TestInterpolation:
    """Test temperature interpolation."""

    @pytest.fixture
    def db(self) -> MaterialDatabase:
        return MaterialDatabase()

    def test_resistivity_at_data_point(self, db: MaterialDatabase) -> None:
        """Interpolation at a known data point returns exact value."""
        rho = db.get_property_at_temperature(
            "Low Carbon Steel (AISI 1018)", "resistivity", 20
        )
        assert rho == pytest.approx(1.43e-7, rel=1e-10)

    def test_resistivity_between_points(self, db: MaterialDatabase) -> None:
        """Interpolation between data points returns reasonable value."""
        rho_350 = db.get_property_at_temperature(
            "Low Carbon Steel (AISI 1018)", "resistivity", 350
        )
        # Should be between 200°C (2.82e-7) and 400°C (4.35e-7)
        assert 2.82e-7 < rho_350 < 4.35e-7

    def test_permeability_at_curie_point(self, db: MaterialDatabase) -> None:
        """Permeability at Curie point is 1.0."""
        mu = db.get_property_at_temperature(
            "Low Carbon Steel (AISI 1018)", "relative_permeability", 770
        )
        assert mu == pytest.approx(1.0, abs=1e-10)

    def test_permeability_above_curie(self, db: MaterialDatabase) -> None:
        """Permeability above Curie point is 1.0."""
        mu = db.get_property_at_temperature(
            "Low Carbon Steel (AISI 1018)", "relative_permeability", 800
        )
        assert mu == pytest.approx(1.0, abs=1e-10)

    def test_permeability_stays_positive(self, db: MaterialDatabase) -> None:
        """Permeability interpolation never goes below 1.0."""
        for t in range(20, 1000, 50):
            mu = db.get_property_at_temperature(
                "Low Carbon Steel (AISI 1018)", "relative_permeability", float(t)
            )
            assert mu >= 1.0, f"Permeability {mu} < 1.0 at {t}°C"

    def test_out_of_range_raises(self, db: MaterialDatabase) -> None:
        """Query outside temperature range raises ValueError."""
        with pytest.raises(ValueError, match="outside the valid range"):
            db.get_property_at_temperature(
                "Low Carbon Steel (AISI 1018)", "resistivity", 1500
            )

    def test_below_range_raises(self, db: MaterialDatabase) -> None:
        """Query below temperature range raises ValueError."""
        with pytest.raises(ValueError, match="outside the valid range"):
            db.get_property_at_temperature(
                "Low Carbon Steel (AISI 1018)", "resistivity", -100
            )

    def test_non_magnetic_no_permeability(self, db: MaterialDatabase) -> None:
        """Non-magnetic material has no permeability property."""
        with pytest.raises(KeyError, match="not available"):
            db.get_property_at_temperature("Copper", "relative_permeability", 20)

    def test_curie_material_without_permeability_data_raises(self, tmp_path: Path) -> None:
        """A material with curie_temperature but no permeability data can't
        estimate mu_r_0 for the sigmoid model, so it should fail loudly
        instead of silently guessing a material-agnostic default."""
        data = {
            "name": "Mystery Alloy",
            "category": "steel",
            "density": 7800,
            "curie_temperature": 700,
            "resistivity": {
                "data": [
                    {"temperature": 20, "value": 1.5e-7},
                    {"temperature": 900, "value": 9.0e-7},
                ],
                "unit": "ohm*m",
            },
            "relative_permeability": None,
        }
        (tmp_path / "mystery.json").write_text(json.dumps(data))
        db = MaterialDatabase(data_dir=tmp_path)

        with pytest.raises(ValueError, match="no relative_permeability data"):
            db.get_permeability("Mystery Alloy", 500.0)

    def test_copper_resistivity_increases(self, db: MaterialDatabase) -> None:
        """Copper resistivity increases with temperature."""
        rho_20 = db.get_property_at_temperature("Copper", "resistivity", 20)
        rho_500 = db.get_property_at_temperature("Copper", "resistivity", 500)
        assert rho_500 > rho_20
