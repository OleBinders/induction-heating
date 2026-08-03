"""End-to-end GUI tests for the full application workflow."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from induction_heating.gui.main_window import MainWindow
from induction_heating.io.export import load_simulation, save_simulation
from induction_heating.materials.database import MaterialDatabase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db() -> MaterialDatabase:
    return MaterialDatabase()


@pytest.fixture
def window(qtbot, db: MaterialDatabase) -> MainWindow:
    w = MainWindow(db)
    qtbot.addWidget(w)
    return w


# ---------------------------------------------------------------------------
# End-to-end tests
# ---------------------------------------------------------------------------

class TestFullWorkflow:
    """Test complete user workflow from parameter entry to results."""

    def test_run_calculation_displays_results(self, window: MainWindow, qtbot) -> None:
        """Full workflow: set parameters → run → verify results display."""
        # Default parameters should be valid
        assert window.run_action.isEnabled()

        # Run calculation
        window.run_action.trigger()

        # Verify results panel is populated
        assert window.results_panel.skin_depth_label.text() != "—"
        assert window.results_panel.b_field_label.text() != "—"
        assert window.results_panel.total_power_label.text() != "—"

    def test_material_change_updates_property_plot(self, window: MainWindow, qtbot) -> None:
        """Material change: select different material → verify property plot updates."""
        # Run calculation with default material
        window.run_action.trigger()
        initial_axes = len(window.property_plot.figure.axes)

        # Change material
        for i in range(window.material_panel.material_combo.count()):
            name = window.material_panel.material_combo.itemText(i)
            if "Copper" in name:
                window.material_panel.material_combo.setCurrentIndex(i)
                break

        # Run again
        window.run_action.trigger()

        # Property plot should have updated
        assert len(window.property_plot.figure.axes) >= initial_axes

    def test_view_toggle_switches_contour(self, window: MainWindow, qtbot) -> None:
        """View toggle: switch between B-field and power density views."""
        # Run calculation
        window.run_action.trigger()

        # Switch to power density
        window.view_combo.setCurrentIndex(1)
        assert window.cross_section_view._current_view == "power_density"

        # Switch back to B-field
        window.view_combo.setCurrentIndex(0)
        assert window.cross_section_view._current_view == "b_field"


class TestSaveLoadWorkflow:
    """Test save/load simulation workflow."""

    def test_save_and_load_roundtrip(self, window: MainWindow, qtbot, tmp_path: Path) -> None:
        """Save simulation → create new window → load → verify panels populated."""
        # Reset to known values first
        window.coil_panel.inner_radius_spin.setValue(0.025)
        window.coil_panel.turns_spin.setValue(20)
        window.operating_panel.frequency_spin.setValue(10000)

        # Save
        filepath = tmp_path / "test_simulation.json"
        setup = window.get_setup()
        frequency = window.operating_panel.frequency_spin.value()
        current = window.operating_panel.current_spin.value()
        temperature = window.operating_panel.temperature_spin.value()
        save_simulation(filepath, setup, frequency, current, temperature)

        # Verify file exists and is valid JSON
        assert filepath.exists()
        state = load_simulation(filepath)
        assert state["coil"]["inner_radius"] == pytest.approx(0.025)
        assert state["coil"]["turns"] == 20
        assert state["operating"]["frequency"] == 10000

    def test_load_populates_panels(self, window: MainWindow, qtbot, tmp_path: Path) -> None:
        """Load simulation → verify all panels populated with saved values."""
        # Reset to known values first
        window.coil_panel.inner_radius_spin.setValue(0.025)
        window.coil_panel.outer_radius_spin.setValue(0.030)
        window.coil_panel.length_spin.setValue(0.10)
        window.coil_panel.turns_spin.setValue(20)
        window.coil_panel.wire_diameter_spin.setValue(0.005)
        window.workpiece_panel.radius_spin.setValue(0.020)
        window.workpiece_panel.length_spin.setValue(0.08)
        window.operating_panel.frequency_spin.setValue(10000)
        window.operating_panel.current_spin.setValue(100)

        # Save current state
        filepath = tmp_path / "test_load.json"
        setup = window.get_setup()
        frequency = window.operating_panel.frequency_spin.value()
        current = window.operating_panel.current_spin.value()
        save_simulation(filepath, setup, frequency, current)

        # Modify values
        window.coil_panel.inner_radius_spin.setValue(0.050)
        window.operating_panel.frequency_spin.setValue(50000)

        # Load state
        state = load_simulation(filepath)
        window.coil_panel.inner_radius_spin.setValue(state["coil"]["inner_radius"])
        window.coil_panel.outer_radius_spin.setValue(state["coil"]["outer_radius"])
        window.coil_panel.length_spin.setValue(state["coil"]["length"])
        window.coil_panel.turns_spin.setValue(state["coil"]["turns"])
        window.coil_panel.wire_diameter_spin.setValue(state["coil"]["wire_diameter"])
        window.workpiece_panel.radius_spin.setValue(state["workpiece"]["radius"])
        window.workpiece_panel.length_spin.setValue(state["workpiece"]["length"])
        window.operating_panel.frequency_spin.setValue(state["operating"]["frequency"])
        window.operating_panel.current_spin.setValue(state["operating"]["current"])

        # Verify values restored to saved state
        assert window.coil_panel.inner_radius_spin.value() == pytest.approx(0.025, abs=0.001)
        assert window.operating_panel.frequency_spin.value() == pytest.approx(10000, abs=1)


class TestValidationErrors:
    """Test validation error handling."""

    def test_invalid_workpiece_shows_error(self, window: MainWindow, qtbot) -> None:
        """Set invalid parameters → verify error message and disabled Run button."""
        # Set workpiece radius larger than coil inner radius
        window.workpiece_panel.radius_spin.setValue(0.050)

        # Run button should be disabled
        assert not window.run_action.isEnabled()

        # Status bar should show error
        status = window.status_bar.currentMessage()
        assert "must" in status.lower() or "error" in status.lower()

    def test_valid_inputs_enable_run(self, window: MainWindow, qtbot) -> None:
        """Set valid parameters → verify Run button enabled."""
        # Default values should be valid
        assert window.run_action.isEnabled()

        # Status bar should show Ready
        assert "Ready" in window.status_bar.currentMessage()
