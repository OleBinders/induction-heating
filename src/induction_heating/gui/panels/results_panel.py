"""Results panel with numerical results and plots."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from induction_heating.materials.database import MaterialDatabase


class ResultsPanel(QGroupBox):
    """Numerical results display panel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Numerical Results", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.skin_depth_label = QLabel("—")
        layout.addRow("Skin Depth:", self.skin_depth_label)

        self.b_field_label = QLabel("—")
        layout.addRow("B-Field (Surface):", self.b_field_label)

        self.total_power_label = QLabel("—")
        layout.addRow("Total Power:", self.total_power_label)

        self.peak_power_label = QLabel("—")
        layout.addRow("Peak Power Density:", self.peak_power_label)

        self.coupling_label = QLabel("—")
        layout.addRow("Coupling Factor:", self.coupling_label)

    def update_results(self, skin_depth: float, b_field: float,
                       total_power: float, peak_power: float,
                       coupling: float) -> None:
        """Update displayed results.

        Args:
            skin_depth: Skin depth in meters.
            b_field: B-field at surface in Tesla.
            total_power: Total absorbed power in Watts.
            peak_power: Peak power density in W/m³.
            coupling: Coupling factor (0-1).
        """
        self.skin_depth_label.setText(f"{skin_depth * 1000:.3f} mm")
        self.b_field_label.setText(f"{b_field * 1000:.3f} mT")
        self.total_power_label.setText(f"{total_power:.2f} W")
        self.peak_power_label.setText(f"{peak_power:.3e} W/m³")
        self.coupling_label.setText(f"{coupling:.3f}")

    def clear(self) -> None:
        """Clear all result labels."""
        for label in [self.skin_depth_label, self.b_field_label,
                      self.total_power_label, self.peak_power_label,
                      self.coupling_label]:
            label.setText("—")


class PropertyPlot(QWidget):
    """Property vs temperature plot widget."""

    def __init__(self, material_db: MaterialDatabase | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = material_db or MaterialDatabase()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def plot_properties(self, material_name: str) -> None:
        """Plot resistivity and permeability vs temperature.

        Args:
            material_name: Name of the material to plot.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        try:
            temps = np.linspace(20, 1000, 100)
            rho = [self._db.get_property_at_temperature(material_name, "resistivity", t)
                   for t in temps]
            mu = [self._db.get_permeability(material_name, t) for t in temps]
        except (KeyError, ValueError):
            ax.text(0.5, 0.5, "No data available", transform=ax.transAxes,
                   ha='center', va='center')
            self.canvas.draw()
            return

        ax.plot(temps, rho, 'b-', label='Resistivity')
        ax.set_xlabel('Temperature (°C)')
        ax.set_ylabel('Resistivity (Ω·m)', color='b')
        ax.tick_params(axis='y', labelcolor='b')
        ax.grid(True, alpha=0.3)

        ax2 = ax.twinx()
        ax2.plot(temps, mu, 'r-', label='Permeability')
        ax2.set_ylabel('Relative Permeability', color='r')
        ax2.tick_params(axis='y', labelcolor='r')

        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        self.figure.tight_layout()
        self.canvas.draw()


class RadialProfilePlot(QWidget):
    """Radial depth profile plots widget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def plot_profiles(self, r: np.ndarray, b_field: np.ndarray,
                      current_density: np.ndarray, power_density: np.ndarray) -> None:
        """Plot B-field, current density, and power density vs radius.

        Args:
            r: Radial positions in meters.
            b_field: B-field values in Tesla.
            current_density: Current density values in A/m².
            power_density: Power density values in W/m³.
        """
        self.figure.clear()
        fig = self.figure

        r_mm = r * 1000  # Convert to mm

        # B-field profile
        ax1 = fig.add_subplot(311)
        ax1.plot(r_mm, np.abs(b_field) * 1000, 'b-')
        ax1.set_ylabel('B (mT)')
        ax1.set_title('B-Field vs Radius')
        ax1.grid(True, alpha=0.3)

        # Current density profile
        ax2 = fig.add_subplot(312, sharex=ax1)
        ax2.plot(r_mm, np.abs(current_density), 'g-')
        ax2.set_ylabel('J (A/m²)')
        ax2.set_title('Current Density vs Radius')
        ax2.grid(True, alpha=0.3)

        # Power density profile
        ax3 = fig.add_subplot(313, sharex=ax1)
        ax3.plot(r_mm, power_density, 'r-')
        ax3.set_xlabel('Radius (mm)')
        ax3.set_ylabel('P (W/m³)')
        ax3.set_title('Power Density vs Radius')
        ax3.grid(True, alpha=0.3)

        fig.tight_layout()
        self.canvas.draw()
