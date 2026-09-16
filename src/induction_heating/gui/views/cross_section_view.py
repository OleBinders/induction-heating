"""Cross-section view widget with matplotlib embedded in PySide6."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from induction_heating.core.electromagnetic import solenoid_b_field_off_axis
from induction_heating.core.geometry import InductionSetup


class CrossSectionView(QWidget):
    """2D cross-section visualization with matplotlib.

    Displays coil and workpiece geometry with optional field/power density
    contour overlays.
    """

    # Signal emitted when view type changes
    view_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._setup = None
        self._b_field_data = None
        self._current_density_data = None
        self._power_density_data = None
        self._grid_r = None
        self._grid_z = None
        self._current_view = "b_field"

    def _setup_ui(self) -> None:
        """Set up the matplotlib canvas and toolbar."""
        layout = QVBoxLayout(self)

        # Matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)

        # Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)

        # Canvas
        layout.addWidget(self.canvas)

        # Color bar (created on first plot)
        self.colorbar = None

    def update_geometry(self, setup: InductionSetup) -> None:
        """Update the geometry display with new coil and workpiece parameters.

        Args:
            setup: InductionSetup with current parameters.
        """
        self._setup = setup
        self._plot_geometry()
        self._redraw()

    def _plot_geometry(self) -> None:
        """Draw coil and workpiece geometry on the axes."""
        self.axes.clear()

        if self._setup is None:
            self.axes.text(0.5, 0.5, "Enter parameters and click Run",
                          transform=self.axes.transAxes, ha='center', va='center')
            return

        coil = self._setup.coil
        wp = self._setup.workpiece

        # Set axis limits
        r_max = coil.outer_radius * 1.1
        z_max = coil.length * 0.6
        self.axes.set_xlim(0, r_max)
        self.axes.set_ylim(-z_max, z_max)
        self.axes.set_aspect('equal')
        self.axes.set_xlabel('Radius (m)')
        self.axes.set_ylabel('Axial Position (m)')
        self.axes.grid(True, alpha=0.3)

        # Coil cross-section (rectangular ring)
        coil_width = coil.outer_radius - coil.inner_radius
        coil_rect = Rectangle(
            (coil.inner_radius, -coil.length / 2),
            coil_width,
            coil.length,
            fill=False, edgecolor='black', linewidth=2, linestyle='--'
        )
        self.axes.add_patch(coil_rect)

        # Workpiece cross-section
        wp_rect = Rectangle(
            (0, -wp.length / 2),
            wp.radius,
            wp.length,
            fill=True, facecolor='gray', alpha=0.3, edgecolor='black', linewidth=1.5
        )
        self.axes.add_patch(wp_rect)

        # Labels
        self.axes.text(coil.inner_radius + coil_width / 2, coil.length / 2 + 0.005,
                      'Coil', ha='center', fontsize=9, fontweight='bold')
        self.axes.text(wp.radius / 2, 0, 'Workpiece', ha='center', va='center',
                      fontsize=9, fontweight='bold')

    def calculate_and_plot_field(self, setup: InductionSetup, current: float,
                                  frequency: float = 10000.0, temperature: float = 20.0,
                                  num_points: int = 100, material_db=None) -> dict | None:
        """Calculate B-field on 2D grid and display as contour plot.

        The B-field map uses the exact off-axis solution (elliptic integrals)
        everywhere, so it's physically valid both inside and outside the
        workpiece -- not an on-axis approximation with an ad hoc falloff
        stitched on. The eddy-current/power numbers are not reimplemented here
        -- they come from the tested ``eddy_currents.calculate_induction_heating``
        pipeline, so the plot and the numerical results panel always agree with
        each other and with the test suite.

        Args:
            setup: InductionSetup with current parameters.
            current: Coil current in amperes.
            frequency: Operating frequency in Hz.
            temperature: Workpiece temperature in °C, for material property lookup.
            num_points: Grid resolution (num_points x num_points).
            material_db: Material database to use. Creates a default if None.

        Returns:
            Dict with calculation results, or None if the material/inputs are invalid.
        """
        self._setup = setup
        coil = setup.coil
        wp = setup.workpiece

        # Create grid
        r_max = coil.outer_radius * 1.05
        z_max = coil.length * 0.55
        self._grid_r = np.linspace(0, r_max, num_points)
        self._grid_z = np.linspace(-z_max, z_max, num_points)
        RR, ZZ = np.meshgrid(self._grid_r, self._grid_z)

        # B-field map for visualization: exact off-axis solution over the whole
        # grid (valid on-axis too -- solenoid_b_field_off_axis handles rho=0
        # explicitly, and test_off_axis_consistency checks the two agree there).
        _, B_z = solenoid_b_field_off_axis(coil, current, RR, ZZ)
        self._b_field_data = B_z

        # Authoritative eddy-current/power physics via the tested pipeline.
        from induction_heating.core.eddy_currents import calculate_induction_heating
        from induction_heating.materials.database import MaterialDatabase

        db = material_db or MaterialDatabase()
        try:
            pipeline = calculate_induction_heating(
                setup, current, frequency, temperature=temperature, material_db=db,
            )
        except (KeyError, ValueError):
            self._power_density_data = np.zeros_like(RR)
            self._current_density_data = np.zeros_like(RR)
            return None

        r_profile = pipeline["radial_positions"]
        j_profile = pipeline["current_density"]
        p_profile = pipeline["power_density"]

        # Interpolate the radial profile onto the visualization grid and
        # broadcast across z (the analytical model has no axial dependence).
        j_grid = np.interp(self._grid_r, r_profile, j_profile, right=0.0)
        p_grid = np.interp(self._grid_r, r_profile, p_profile, right=0.0)
        outside = self._grid_r > wp.radius
        j_grid[outside] = 0.0
        p_grid[outside] = 0.0

        J_r = np.tile(j_grid, (num_points, 1))
        P_r = np.tile(p_grid, (num_points, 1))
        self._current_density_data = J_r
        self._power_density_data = P_r

        # Plot
        self._plot_contour()

        peak_power_density = float(np.max(p_profile)) if p_profile.size else 0.0

        return {
            "skin_depth": pipeline["skin_depth"],
            # Full 2D field grid, not a scalar -- deliberately named differently
            # from calculate_induction_heating()'s "b_field_surface" (a scalar
            # on-axis value) so the two aren't confused if a caller ever merges
            # both dicts.
            "b_field_grid": B_z,
            "current_density": J_r,
            "power_density": P_r,
            "total_power": pipeline["total_power"],
            "peak_power_density": peak_power_density,
            "radial_positions": self._grid_r,
            "snapshot": pipeline["snapshot"],
        }

    def _plot_contour(self) -> None:
        """Plot the current view (B-field or power density) as contour."""
        self._plot_geometry()

        if self._b_field_data is None:
            self._redraw()
            return

        if self._current_view == "b_field":
            data = np.abs(self._b_field_data)
            cmap = 'viridis'
            label = 'B (T)'
            title = 'Magnetic Field Distribution'
        else:
            data = self._power_density_data
            cmap = 'plasma'
            label = 'P (W/m³)'
            title = 'Power Density Distribution'

        # Mask zero values for cleaner plot
        data_masked = np.ma.masked_where(data == 0, data)

        cf = self.axes.contourf(
            self._grid_r, self._grid_z, data_masked,
            levels=50, cmap=cmap
        )

        # Color bar: remove old one if it exists, create new one
        if self.colorbar is not None:
            try:
                self.colorbar.remove()
            except (KeyError, AttributeError):
                pass  # Colorbar already removed
        self.colorbar = self.figure.colorbar(cf, ax=self.axes, label=label)
        self.axes.set_title(title)

        self._redraw()

    def set_view(self, view_type: str) -> None:
        """Switch between B-field and power density views.

        Args:
            view_type: 'b_field' or 'power_density'.
        """
        if view_type in ('b_field', 'power_density'):
            self._current_view = view_type
            if self._b_field_data is not None:
                self._plot_contour()
            self.view_changed.emit(view_type)

    def _redraw(self) -> None:
        """Redraw the canvas."""
        self.figure.tight_layout()
        self.canvas.draw()
