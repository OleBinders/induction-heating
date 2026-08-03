"""Tests for export and persistence functions."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from induction_heating.core.geometry import CylindricalWorkpiece, InductionSetup, SolenoidCoil
from induction_heating.io.export import (
    create_setup_from_state,
    export_csv,
    load_simulation,
    save_simulation,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def steel_setup() -> InductionSetup:
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
# CSV export tests
# ---------------------------------------------------------------------------

class TestExportCSV:
    """Test CSV export functionality."""

    def test_export_csv_creates_file(self, tmp_path: Path) -> None:
        """CSV file is created with correct content."""
        filepath = tmp_path / "results.csv"
        r = np.array([0.0, 0.01, 0.02])
        b = np.array([0.01, 0.008, 0.005])
        j = np.array([1e6, 8e5, 5e5])
        p = np.array([1e8, 8e7, 5e7])

        export_csv(filepath, r, b, j, p)

        assert filepath.exists()
        content = filepath.read_text()
        assert "Radius (m)" in content
        assert "B (T)" in content
        assert "J (A/m²)" in content
        assert "P (W/m³)" in content

    def test_export_csv_has_correct_rows(self, tmp_path: Path) -> None:
        """CSV has header + data rows."""
        filepath = tmp_path / "results.csv"
        r = np.array([0.0, 0.01, 0.02])
        b = np.array([0.01, 0.008, 0.005])
        j = np.array([1e6, 8e5, 5e5])
        p = np.array([1e8, 8e7, 5e7])

        export_csv(filepath, r, b, j, p)

        lines = filepath.read_text().strip().split("\n")
        assert len(lines) == 4  # Header + 3 data rows


# ---------------------------------------------------------------------------
# JSON save/load tests
# ---------------------------------------------------------------------------

class TestSaveSimulation:
    """Test JSON save functionality."""

    def test_save_creates_valid_json(self, tmp_path: Path, steel_setup: InductionSetup) -> None:
        """Save creates valid JSON with correct structure."""
        filepath = tmp_path / "simulation.json"
        save_simulation(filepath, steel_setup, frequency=10000, current=100)

        assert filepath.exists()
        with open(filepath) as f:
            state = json.load(f)

        assert state["version"] == "0.1.0"
        assert state["coil"]["inner_radius"] == 0.025
        assert state["workpiece"]["material_name"] == "Low Carbon Steel (AISI 1018)"
        assert state["operating"]["frequency"] == 10000

    def test_save_with_temperature(self, tmp_path: Path, steel_setup: InductionSetup) -> None:
        """Save includes temperature field."""
        filepath = tmp_path / "simulation.json"
        save_simulation(filepath, steel_setup, frequency=10000, current=100, temperature=500)

        with open(filepath) as f:
            state = json.load(f)

        assert state["operating"]["temperature"] == 500


class TestLoadSimulation:
    """Test JSON load functionality."""

    def test_load_valid_file(self, tmp_path: Path, steel_setup: InductionSetup) -> None:
        """Load returns correct state from valid file."""
        filepath = tmp_path / "simulation.json"
        save_simulation(filepath, steel_setup, frequency=10000, current=100)

        state = load_simulation(filepath)
        assert state["coil"]["inner_radius"] == 0.025
        assert state["operating"]["current"] == 100

    def test_load_missing_file_raises(self) -> None:
        """Load raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_simulation("/nonexistent/path.json")

    def test_load_missing_fields_raises(self, tmp_path: Path) -> None:
        """Load raises ValueError for missing required fields."""
        filepath = tmp_path / "bad.json"
        with open(filepath, "w") as f:
            json.dump({"version": "0.1.0"}, f)

        with pytest.raises(ValueError, match="Missing required fields"):
            load_simulation(filepath)

    def test_load_missing_coil_fields_raises(self, tmp_path: Path) -> None:
        """Load raises ValueError for missing coil fields."""
        filepath = tmp_path / "bad.json"
        state = {
            "version": "0.1.0",
            "coil": {"inner_radius": 0.025},  # Missing other fields
            "workpiece": {"radius": 0.02, "length": 0.08, "material_name": "Steel"},
            "operating": {"frequency": 10000, "current": 100, "temperature": 20},
        }
        with open(filepath, "w") as f:
            json.dump(state, f)

        with pytest.raises(ValueError, match="Missing coil fields"):
            load_simulation(filepath)


class TestCreateSetupFromState:
    """Test InductionSetup creation from loaded state."""

    def test_creates_valid_setup(self, tmp_path: Path, steel_setup: InductionSetup) -> None:
        """Created setup matches saved parameters."""
        filepath = tmp_path / "simulation.json"
        save_simulation(filepath, steel_setup, frequency=10000, current=100)

        state = load_simulation(filepath)
        setup = create_setup_from_state(state)

        assert setup.coil.inner_radius == pytest.approx(0.025)
        assert setup.workpiece.radius == pytest.approx(0.020)
        assert setup.workpiece.material_name == "Low Carbon Steel (AISI 1018)"
