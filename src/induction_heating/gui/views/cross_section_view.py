"""Cross-section view widget with matplotlib embedded in PySide6."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from induction_heating.core.electromagnetic import solenoid_b_field_on_axis
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
                                  num_points: int = 100) -> None:
        """Calculate B-field on 2D grid and display as contour plot.

        Args:
            setup: InductionSetup with current parameters.
            current: Coil current in amperes.
            num_points: Grid resolution (num_points x num_points).
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

        # Calculate B-field on grid (on-axis approximation for each R column)
        # For simplicity, use on-axis formula at each Z position
        # This gives the axial component B_z
        B_z = np.zeros_like(RR)
        for i, r in enumerate(self._grid_r):
            # For each radial position, calculate B-field
            # Using the on-axis formula as approximation (valid near axis)
            if r <= wp.radius:
                # Inside workpiece: use on-axis formula
                B_z[:, i] = solenoid_b_field_on_axis(coil, current, ZZ[:, i])
            else:
                # Outside workpiece: field drops off
                B_z[:, i] = solenoid_b_field_on_axis(coil, current, ZZ[:, i]) * (wp.radius / max(r, 1e-10))

        self._b_field_data = B_z

        # Calculate power density
        from induction_heating.core.eddy_currents import (
            eddy_current_density,
            power_density,
        )
        from induction_heating.materials.database import MaterialDatabase

        db = MaterialDatabase()
        try:
            rho = db.get_property_at_temperature(wp.material_name, "resistivity", 20.0)
            mu_r = db.get_permeability(wp.material_name, 20.0)
        except (KeyError, ValueError):
            rho = 1.43e-7
            mu_r = 200.0

        # Calculate eddy current density at each radial position inside workpiece
        J_r = np.zeros_like(RR)
        P_r = np.zeros_like(RR)
        for i, r in enumerate(self._grid_r):
            if r <= wp.radius:
                B_surf = float(np.max(np.abs(B_z[:, i])))
                if B_surf > 0:
                    j_vals = eddy_current_density(
                        B_surf, 10000, rho, mu_r, wp.radius,
                        np.array([r])
                    )
                    J_r[:, i] = j_vals[0]
                    P_r[:, i] = power_density(j_vals, rho)[0]

        self._power_density_data = P_r

        # Plot
        self._plot_contour()

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
