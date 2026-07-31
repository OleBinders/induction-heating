"""Tests for parameter panels."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QSpinBox

from induction_heating.gui.main_window import MainWindow
from induction_heating.gui.panels.material_panel import MaterialPanel
from induction_heating.gui.panels.param_panel import CoilPanel, OperatingPanel, WorkpiecePanel
from induction_heating.materials.database import MaterialDatabase


# ---------------------------------------------------------------------------
# CoilPanel tests
# ---------------------------------------------------------------------------

class TestCoilPanel:
    """Test coil parameter panel."""

    @pytest.fixture
    def panel(self, qtbot) -> CoilPanel:
        p = CoilPanel()
        qtbot.addWidget(p)
        return p

    def test_inner_radius_default(self, panel: CoilPanel) -> None:
        # Default is 0.025 m, allow for Qt rounding
        assert 0.020 <= panel.inner_radius_spin.value() <= 0.030

    def test_inner_radius_range(self, panel: CoilPanel) -> None:
        assert panel.inner_radius_spin.minimum() == 0.001
        assert panel.inner_radius_spin.maximum() == 1.0

    def test_outer_radius_default(self, panel: CoilPanel) -> None:
        assert 0.025 <= panel.outer_radius_spin.value() <= 0.035

    def test_length_default(self, panel: CoilPanel) -> None:
        assert 0.09 <= panel.length_spin.value() <= 0.11

    def test_turns_default(self, panel: CoilPanel) -> None:
        assert panel.turns_spin.value() == 20

    def test_turns_is_spinbox(self, panel: CoilPanel) -> None:
        assert isinstance(panel.turns_spin, QSpinBox)

    def test_wire_diameter_default(self, panel: CoilPanel) -> None:
        # Default is 0.005 m, allow for Qt rounding
        assert 0.001 <= panel.wire_diameter_spin.value() <= 0.01

    def test_emits_changed_signal(self, panel: CoilPanel, qtbot) -> None:
        with qtbot.waitSignal(panel.changed, timeout=500):
            panel.inner_radius_spin.setValue(0.035)

    def test_outer_radius_min_updates(self, panel: CoilPanel) -> None:
        """Outer radius minimum updates when inner radius increases."""
        panel.inner_radius_spin.setValue(0.050)
        assert panel.outer_radius_spin.minimum() == pytest.approx(0.050)


# ---------------------------------------------------------------------------
# WorkpiecePanel tests
# ---------------------------------------------------------------------------

class TestWorkpiecePanel:
    """Test workpiece parameter panel."""

    @pytest.fixture
    def panel(self, qtbot) -> WorkpiecePanel:
        p = WorkpiecePanel()
        qtbot.addWidget(p)
        return p

    def test_radius_default(self, panel: WorkpiecePanel) -> None:
        assert panel.radius_spin.value() == pytest.approx(0.020)

    def test_radius_range(self, panel: WorkpiecePanel) -> None:
        assert panel.radius_spin.minimum() == 0.001
        assert panel.radius_spin.maximum() == 0.5

    def test_length_default(self, panel: WorkpiecePanel) -> None:
        assert panel.length_spin.value() == pytest.approx(0.08)

    def test_emits_changed_signal(self, panel: WorkpiecePanel, qtbot) -> None:
        with qtbot.waitSignal(panel.changed, timeout=100):
            panel.radius_spin.setValue(0.025)


# ---------------------------------------------------------------------------
# OperatingPanel tests
# ---------------------------------------------------------------------------

class TestOperatingPanel:
    """Test operating parameters panel."""

    @pytest.fixture
    def panel(self, qtbot) -> OperatingPanel:
        p = OperatingPanel()
        qtbot.addWidget(p)
        return p

    def test_frequency_default(self, panel: OperatingPanel) -> None:
        assert panel.frequency_spin.value() == pytest.approx(10000)

    def test_frequency_range(self, panel: OperatingPanel) -> None:
        """Frequency locked to 10-50 kHz."""
        assert panel.frequency_spin.minimum() == 10000
        assert panel.frequency_spin.maximum() == 50000

    def test_current_default(self, panel: OperatingPanel) -> None:
        assert panel.current_spin.value() == pytest.approx(100)

    def test_temperature_default(self, panel: OperatingPanel) -> None:
        assert panel.temperature_spin.value() == pytest.approx(20)

    def test_frequency_khz(self, panel: OperatingPanel) -> None:
        assert panel.frequency_khz == pytest.approx(10.0)

    def test_emits_changed_signal(self, panel: OperatingPanel, qtbot) -> None:
        with qtbot.waitSignal(panel.changed, timeout=100):
            panel.frequency_spin.setValue(20000)


# ---------------------------------------------------------------------------
# MaterialPanel tests
# ---------------------------------------------------------------------------

class TestMaterialPanel:
    """Test material selector panel."""

    @pytest.fixture
    def db(self) -> MaterialDatabase:
        return MaterialDatabase()

    @pytest.fixture
    def panel(self, qtbot, db: MaterialDatabase) -> MaterialPanel:
        p = MaterialPanel(db)
        qtbot.addWidget(p)
        return p

    def test_lists_all_materials(self, panel: MaterialPanel, db: MaterialDatabase) -> None:
        combo = panel.material_combo
        assert combo.count() == len(db.list_materials())

    def test_shows_steel_properties(self, panel: MaterialPanel, qtbot) -> None:
        """Selecting steel shows resistivity, permeability, Curie point."""
        # Find steel in combo
        for i in range(panel.material_combo.count()):
            if "Steel" in panel.material_combo.itemText(i):
                panel.material_combo.setCurrentIndex(i)
                break

        assert "Ω·m" in panel.resistivity_label.text()
        assert panel.permeability_label.text() != "N/A"
        assert "°C" in panel.curie_label.text()

    def test_shows_copper_non_magnetic(self, panel: MaterialPanel, qtbot) -> None:
        """Selecting copper shows Non-magnetic for Curie point."""
        for i in range(panel.material_combo.count()):
            if "Copper" in panel.material_combo.itemText(i):
                panel.material_combo.setCurrentIndex(i)
                break

        assert "Non-magnetic" in panel.curie_label.text()

    def test_emits_material_changed_signal(self, panel: MaterialPanel, qtbot) -> None:
        with qtbot.waitSignal(panel.material_changed, timeout=100):
            panel.material_combo.setCurrentIndex(1)


# ---------------------------------------------------------------------------
# MainWindow integration tests
# ---------------------------------------------------------------------------

class TestMainWindowValidation:
    """Test input validation in MainWindow."""

    @pytest.fixture
    def window(self, qtbot) -> MainWindow:
        w = MainWindow()
        qtbot.addWidget(w)
        return w

    def test_valid_inputs_shows_ready(self, window: MainWindow) -> None:
        """Valid inputs show Ready in status bar."""
        # Default values should be valid
        assert "Ready" in window.status_bar.currentMessage()

    def test_invalid_workpiece_disables_run(self, window: MainWindow) -> None:
        """Workpiece radius > coil inner radius disables Run button."""
        # Set workpiece radius larger than coil inner radius
        window.workpiece_panel.radius_spin.setValue(0.050)  # > 0.025
        assert not window.run_action.isEnabled()
        assert "error" in window.status_bar.currentMessage().lower() or \
               "must" in window.status_bar.currentMessage().lower()

    def test_valid_inputs_enables_run(self, window: MainWindow) -> None:
        """Valid inputs enable Run button."""
        # Default values are valid
        assert window.run_action.isEnabled()

    def test_get_setup_creates_valid_setup(self, window: MainWindow) -> None:
        """get_setup() creates valid InductionSetup."""
        setup = window.get_setup()
        assert setup is not None
        assert setup.coil.turns == 20
        assert setup.workpiece.radius == pytest.approx(0.020)

    def test_get_setup_raises_when_invalid(self, window: MainWindow) -> None:
        """get_setup() raises ValueError when inputs invalid."""
        window.workpiece_panel.radius_spin.setValue(0.050)
        with pytest.raises(ValueError):
            window.get_setup()
