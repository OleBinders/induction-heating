"""Material selector panel with property preview."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from induction_heating.materials.database import MaterialDatabase


class MaterialPanel(QGroupBox):
    """Material selection panel with property preview."""

    material_changed = Signal(str)

    def __init__(
        self,
        material_db: MaterialDatabase | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Material Selection", parent)
        self._db = material_db or MaterialDatabase()
        self._setup_ui()
        self._populate_materials()
        self._update_preview()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Material selector
        selector_layout = QFormLayout()
        self.material_combo = QComboBox()
        selector_layout.addRow("Material:", self.material_combo)
        layout.addLayout(selector_layout)

        # Property preview
        self.preview_group = QGroupBox("Properties at 20°C")
        preview_layout = QFormLayout(self.preview_group)

        self.resistivity_label = QLabel()
        preview_layout.addRow("Resistivity:", self.resistivity_label)

        self.permeability_label = QLabel()
        preview_layout.addRow("Permeability:", self.permeability_label)

        self.curie_label = QLabel()
        preview_layout.addRow("Curie Point:", self.curie_label)

        self.density_label = QLabel()
        preview_layout.addRow("Density:", self.density_label)

        layout.addWidget(self.preview_group)

        self.material_combo.currentTextChanged.connect(self._on_material_changed)

    def _populate_materials(self) -> None:
        """Populate combo box with available materials."""
        for name in self._db.list_materials():
            self.material_combo.addItem(name)

    def _on_material_changed(self, name: str) -> None:
        """Handle material selection change."""
        self._update_preview()
        self.material_changed.emit(name)

    def _update_preview(self) -> None:
        """Update property preview labels."""
        name = self.material_combo.currentText()
        if not name:
            return

        try:
            material = self._db.get_material(name)
        except KeyError:
            return

        # Resistivity at 20°C
        try:
            rho = self._db.get_property_at_temperature(name, "resistivity", 20.0)
            self.resistivity_label.setText(f"{rho:.3e} Ω·m")
        except (KeyError, ValueError):
            self.resistivity_label.setText("N/A")

        # Permeability at 20°C
        try:
            mu = self._db.get_permeability(name, 20.0)
            self.permeability_label.setText(f"{mu:.1f}")
        except (KeyError, ValueError):
            self.permeability_label.setText("N/A")

        # Curie point
        if material.curie_temperature is not None:
            self.curie_label.setText(f"{material.curie_temperature} °C")
        else:
            self.curie_label.setText("Non-magnetic")

        # Density
        self.density_label.setText(f"{material.density} kg/m³")

    @property
    def selected_material(self) -> str:
        """Currently selected material name."""
        return self.material_combo.currentText()
