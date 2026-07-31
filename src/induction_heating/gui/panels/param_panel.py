"""Parameter input panels for coil, workpiece, and operating parameters."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QWidget,
)


class CoilPanel(QGroupBox):
    """Coil parameter input panel."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Coil Parameters", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.inner_radius_spin = QDoubleSpinBox()
        self.inner_radius_spin.setRange(0.001, 1.0)
        self.inner_radius_spin.setValue(0.025)
        self.inner_radius_spin.setDecimals(4)
        self.inner_radius_spin.setSingleStep(0.001)
        self.inner_radius_spin.setSuffix(" m")
        layout.addRow("Inner Radius:", self.inner_radius_spin)

        self.outer_radius_spin = QDoubleSpinBox()
        self.outer_radius_spin.setRange(0.001, 1.0)
        self.outer_radius_spin.setValue(0.030)
        self.outer_radius_spin.setDecimals(4)
        self.outer_radius_spin.setSingleStep(0.001)
        self.outer_radius_spin.setSuffix(" m")
        layout.addRow("Outer Radius:", self.outer_radius_spin)

        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0.01, 5.0)
        self.length_spin.setValue(0.10)
        self.length_spin.setDecimals(3)
        self.length_spin.setSingleStep(0.01)
        self.length_spin.setSuffix(" m")
        layout.addRow("Length:", self.length_spin)

        self.turns_spin = QSpinBox()
        self.turns_spin.setRange(1, 1000)
        self.turns_spin.setValue(20)
        self.turns_spin.setSuffix(" turns")
        layout.addRow("Turns:", self.turns_spin)

        self.wire_diameter_spin = QDoubleSpinBox()
        self.wire_diameter_spin.setRange(0.0001, 0.05)
        self.wire_diameter_spin.setValue(0.005)
        self.wire_diameter_spin.setDecimals(5)
        self.wire_diameter_spin.setSingleStep(0.0001)
        self.wire_diameter_spin.setSuffix(" m")
        layout.addRow("Wire Diameter:", self.wire_diameter_spin)

        # Connect signals
        for spin in [
            self.inner_radius_spin,
            self.outer_radius_spin,
            self.length_spin,
            self.turns_spin,
            self.wire_diameter_spin,
        ]:
            spin.valueChanged.connect(self._on_changed)

        # Ensure outer radius >= inner radius
        self.inner_radius_spin.valueChanged.connect(self._update_outer_radius_min)

    def _update_outer_radius_min(self, value: float) -> None:
        """Update outer radius minimum when inner radius changes."""
        if self.outer_radius_spin.minimum() < value:
            self.outer_radius_spin.setMinimum(value)
            if self.outer_radius_spin.value() < value:
                self.outer_radius_spin.setValue(value)

    def _on_changed(self) -> None:
        self.changed.emit()


class WorkpiecePanel(QGroupBox):
    """Workpiece parameter input panel."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Workpiece Parameters", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.radius_spin = QDoubleSpinBox()
        self.radius_spin.setRange(0.001, 0.5)
        self.radius_spin.setValue(0.020)
        self.radius_spin.setDecimals(4)
        self.radius_spin.setSingleStep(0.001)
        self.radius_spin.setSuffix(" m")
        layout.addRow("Radius:", self.radius_spin)

        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0.01, 5.0)
        self.length_spin.setValue(0.08)
        self.length_spin.setDecimals(3)
        self.length_spin.setSingleStep(0.01)
        self.length_spin.setSuffix(" m")
        layout.addRow("Length:", self.length_spin)

        for spin in [self.radius_spin, self.length_spin]:
            spin.valueChanged.connect(self._on_changed)

    def _on_changed(self) -> None:
        self.changed.emit()


class OperatingPanel(QGroupBox):
    """Operating parameters input panel."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Operating Parameters", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.frequency_spin = QDoubleSpinBox()
        self.frequency_spin.setRange(10000, 50000)
        self.frequency_spin.setValue(10000)
        self.frequency_spin.setDecimals(0)
        self.frequency_spin.setSingleStep(1000)
        self.frequency_spin.setSuffix(" Hz")
        layout.addRow("Frequency:", self.frequency_spin)

        self.current_spin = QDoubleSpinBox()
        self.current_spin.setRange(1, 10000)
        self.current_spin.setValue(100)
        self.current_spin.setDecimals(1)
        self.current_spin.setSingleStep(10)
        self.current_spin.setSuffix(" A")
        layout.addRow("Current:", self.current_spin)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(20, 1500)
        self.temperature_spin.setValue(20)
        self.temperature_spin.setDecimals(0)
        self.temperature_spin.setSingleStep(50)
        self.temperature_spin.setSuffix(" °C")
        layout.addRow("Temperature:", self.temperature_spin)

        for spin in [self.frequency_spin, self.current_spin, self.temperature_spin]:
            spin.valueChanged.connect(self._on_changed)

    @property
    def frequency_khz(self) -> float:
        """Frequency in kHz."""
        return self.frequency_spin.value() / 1000.0

    def _on_changed(self) -> None:
        self.changed.emit()
