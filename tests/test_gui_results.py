"""Tests for results panel and plots."""

from __future__ import annotations

import numpy as np
import pytest

from induction_heating.core.geometry import CylindricalWorkpiece, InductionSetup, SolenoidCoil
from induction_heating.gui.main_window import MainWindow
from induction_heating.gui.panels.results_panel import PropertyPlot, RadialProfilePlot, ResultsPanel
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
# ResultsPanel tests
# ---------------------------------------------------------------------------

class TestResultsPanel:
    """Test numerical results panel."""

    @pytest.fixture
    def panel(self, qtbot) -> ResultsPanel:
        p = ResultsPanel()
        qtbot.addWidget(p)
        return p

    def test_creates_without_errors(self, panel: ResultsPanel) -> None:
        assert panel is not None

    def test_update_results(self, panel: ResultsPanel) -> None:
        """Results update correctly."""
        panel.update_results(
            skin_depth=1e-4,
            b_field=0.01,
            total_power=100.5,
            peak_power=1e8,
            coupling=0.64,
        )
        assert "0.100 mm" in panel.skin_depth_label.text()
        assert "10.000 mT" in panel.b_field_label.text()
        assert "100.50 W" in panel.total_power_label.text()

    def test_clear(self, panel: ResultsPanel) -> None:
        """Clear resets all labels."""
        panel.update_results(1e-4, 0.01, 100.5, 1e8, 0.64)
        panel.clear()
        assert panel.skin_depth_label.text() == "—"


# ---------------------------------------------------------------------------
# PropertyPlot tests
# ---------------------------------------------------------------------------

class TestPropertyPlot:
    """Test property vs temperature plot."""

    @pytest.fixture
    def plot(self, qtbot, db: MaterialDatabase) -> PropertyPlot:
        p = PropertyPlot(db)
        qtbot.addWidget(p)
        return p

    def test_creates_without_errors(self, plot: PropertyPlot) -> None:
        assert plot is not None

    def test_plot_properties(self, plot: PropertyPlot) -> None:
        """Plot creates without errors."""
        plot.plot_properties("Low Carbon Steel (AISI 1018)")
        assert len(plot.figure.axes) > 0


# ---------------------------------------------------------------------------
# RadialProfilePlot tests
# ---------------------------------------------------------------------------

class TestRadialProfilePlot:
    """Test radial depth profile plots."""

    @pytest.fixture
    def plot(self, qtbot) -> RadialProfilePlot:
        p = RadialProfilePlot()
        qtbot.addWidget(p)
        return p

    def test_creates_without_errors(self, plot: RadialProfilePlot) -> None:
        assert plot is not None

    def test_plot_profiles(self, plot: RadialProfilePlot) -> None:
        """Profiles create without errors."""
        r = np.linspace(0, 0.02, 50)
        b = np.exp(-r / 0.005) * 0.01
        j = np.exp(-r / 0.005) * 1e6
        p = j**2 * 1.43e-7
        plot.plot_profiles(r, b, j, p)
        assert len(plot.figure.axes) == 3


# ---------------------------------------------------------------------------
# MainWindow integration tests
# ---------------------------------------------------------------------------

class TestMainWindowResults:
    """Test results integration in MainWindow."""

    @pytest.fixture
    def window(self, qtbot, db: MaterialDatabase) -> MainWindow:
        w = MainWindow(db)
        qtbot.addWidget(w)
        return w

    def test_results_panel_exists(self, window: MainWindow) -> None:
        assert window.results_panel is not None

    def test_property_plot_exists(self, window: MainWindow) -> None:
        assert window.property_plot is not None

    def test_radial_plot_exists(self, window: MainWindow) -> None:
        assert window.radial_plot is not None

    def test_run_populates_results(self, window: MainWindow, qtbot) -> None:
        """Running calculation populates results panel."""
        window.run_action.trigger()
        # Results should be updated (not "—")
        assert window.results_panel.skin_depth_label.text() != "—"

    def test_run_creates_property_plot(self, window: MainWindow, qtbot) -> None:
        """Running calculation creates property plot."""
        window.run_action.trigger()
        assert len(window.property_plot.figure.axes) > 0

    def test_run_creates_radial_plots(self, window: MainWindow, qtbot) -> None:
        """Running calculation creates radial profile plots."""
        window.run_action.trigger()
        assert len(window.radial_plot.figure.axes) == 3
