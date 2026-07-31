"""Tests for cross-section view."""

from __future__ import annotations

import pytest

from induction_heating.core.geometry import CylindricalWorkpiece, InductionSetup, SolenoidCoil
from induction_heating.gui.main_window import MainWindow
from induction_heating.gui.views.cross_section_view import CrossSectionView
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
# CrossSectionView tests
# ---------------------------------------------------------------------------

class TestCrossSectionView:
    """Test cross-section view widget."""

    @pytest.fixture
    def view(self, qtbot) -> CrossSectionView:
        v = CrossSectionView()
        qtbot.addWidget(v)
        return v

    def test_creates_without_errors(self, view: CrossSectionView) -> None:
        """CrossSectionView creates without errors."""
        assert view is not None

    def test_canvas_exists(self, view: CrossSectionView) -> None:
        """Matplotlib canvas exists."""
        assert view.canvas is not None

    def test_toolbar_exists(self, view: CrossSectionView) -> None:
        """Navigation toolbar exists."""
        assert view.toolbar is not None

    def test_geometry_renders(self, view: CrossSectionView, steel_setup: InductionSetup) -> None:
        """Geometry renders for valid parameters."""
        view.update_geometry(steel_setup)
        # Check that axes have patches (coil and workpiece rectangles)
        assert len(view.axes.patches) == 2  # Coil + workpiece

    def test_contour_plot_displays(self, view: CrossSectionView, steel_setup: InductionSetup) -> None:
        """Contour plot displays after calculation."""
        view.calculate_and_plot_field(steel_setup, current=100.0)
        # Check that contour collections exist
        assert len(view.axes.collections) > 0

    def test_colorbar_exists(self, view: CrossSectionView, steel_setup: InductionSetup) -> None:
        """Color bar exists after calculation."""
        view.calculate_and_plot_field(steel_setup, current=100.0)
        assert view.colorbar is not None

    def test_view_toggle(self, view: CrossSectionView, steel_setup: InductionSetup) -> None:
        """View toggle switches between B-field and power density."""
        view.calculate_and_plot_field(steel_setup, current=100.0)

        # Switch to power density
        view.set_view("power_density")
        assert view._current_view == "power_density"

        # Switch back to B-field
        view.set_view("b_field")
        assert view._current_view == "b_field"


# ---------------------------------------------------------------------------
# MainWindow integration tests
# ---------------------------------------------------------------------------

class TestMainWindowCrossSection:
    """Test cross-section view integration in MainWindow."""

    @pytest.fixture
    def window(self, qtbot, db: MaterialDatabase) -> MainWindow:
        w = MainWindow(db)
        qtbot.addWidget(w)
        return w

    def test_cross_section_view_exists(self, window: MainWindow) -> None:
        """Cross-section view exists in MainWindow."""
        assert window.cross_section_view is not None

    def test_view_combo_exists(self, window: MainWindow) -> None:
        """View toggle combo box exists."""
        assert window.view_combo is not None
        assert window.view_combo.count() == 2  # B-field and Power Density

    def test_run_button_triggers_calculation(self, window: MainWindow, qtbot) -> None:
        """Run button triggers cross-section calculation."""
        # Default values should be valid
        assert window.run_action.isEnabled()

        # Trigger calculation
        window.run_action.trigger()

        # Check that cross-section view has data
        assert window.cross_section_view._b_field_data is not None

    def test_view_combo_switches_view(self, window: MainWindow, qtbot) -> None:
        """View combo switches between B-field and power density."""
        # Run calculation first
        window.run_action.trigger()

        # Switch to power density
        window.view_combo.setCurrentIndex(1)
        assert window.cross_section_view._current_view == "power_density"

        # Switch back to B-field
        window.view_combo.setCurrentIndex(0)
        assert window.cross_section_view._current_view == "b_field"


# ---------------------------------------------------------------------------
# Additional CrossSectionView tests for colormaps and formatting
# ---------------------------------------------------------------------------

class TestCrossSectionViewFormatting:
    """Test cross-section view colormap and formatting."""

    @pytest.fixture
    def view(self, qtbot) -> CrossSectionView:
        v = CrossSectionView()
        qtbot.addWidget(v)
        return v

    def test_b_field_uses_viridis(self, view: CrossSectionView, steel_setup: InductionSetup) -> None:
        """B-field view uses viridis colormap."""
        view.calculate_and_plot_field(steel_setup, current=100.0)
        view.set_view("b_field")
        collections = view.axes.collections
        assert len(collections) > 0
        cmap = collections[0].get_cmap()
        assert cmap.name == 'viridis'

    def test_power_density_uses_plasma(self, view: CrossSectionView, steel_setup: InductionSetup) -> None:
        """Power density view uses plasma colormap."""
        view.calculate_and_plot_field(steel_setup, current=100.0)
        view.set_view("power_density")
        collections = view.axes.collections
        assert len(collections) > 0
        cmap = collections[0].get_cmap()
        assert cmap.name == 'plasma'

    def test_axis_labels_correct(self, view: CrossSectionView, steel_setup: InductionSetup) -> None:
        """Axis labels have correct units."""
        view.calculate_and_plot_field(steel_setup, current=100.0)
        assert 'Radius' in view.axes.get_xlabel()
        assert 'Axial' in view.axes.get_ylabel()

    def test_plot_title_changes_with_view(self, view: CrossSectionView, steel_setup: InductionSetup) -> None:
        """Plot title changes when switching views."""
        view.calculate_and_plot_field(steel_setup, current=100.0)
        assert 'Magnetic Field' in view.axes.get_title()

        view.set_view("power_density")
        assert 'Power Density' in view.axes.get_title()
