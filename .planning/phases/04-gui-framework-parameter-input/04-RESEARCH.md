# Phase 4 Research: GUI Framework & Parameter Input

**Phase:** 04 — GUI Framework & Parameter Input
**Researched:** 2026-07-30
**Confidence:** HIGH

## PySide6 Application Architecture

### Standard Pattern for Scientific Applications

```
MainWindow (QMainWindow)
├── MenuBar (File, Edit, View, Help)
├── ToolBar (Run, Save, Load, Export)
├── Central Widget (QSplitter or QTabWidget)
│   ├── Left Panel (QDockWidget): Parameter Input
│   │   ├── Coil Parameters (QFormLayout)
│   │   ├── Workpiece Parameters (QFormLayout)
│   │   ├── Operating Parameters (QFormLayout)
│   │   └── Material Selector (QComboBox + preview)
│   └── Right Panel (QDockWidget): Results/Visualization
│       ├── Cross-section view (placeholder for Phase 5)
│       └── Results panel (placeholder for Phase 6)
└── Status Bar (calculation status, errors)
```

**Confidence:** HIGH — standard PySide6 pattern.

### Key PySide6 Widgets for This Phase

| Widget | Purpose | Notes |
|--------|---------|-------|
| QMainWindow | Main application window | Supports docked panels, menu bar, status bar |
| QDockWidget | Dockable parameter panels | User can rearrange panels |
| QFormLayout | Parameter input forms | Label + field pairs, ideal for scientific input |
| QDoubleSpinBox | Numeric input with range | Better than QLineEdit for validated numeric input |
| QComboBox | Material selection dropdown | Shows material names, triggers property preview |
| QGroupBox | Group related parameters | Visual grouping of coil/workpiece/operating params |
| QValidator | Input validation | QDoubleValidator for numeric ranges |
| QMessageBox | Error dialogs | For validation errors and warnings |

**Confidence:** HIGH — standard Qt widgets.

### QDoubleSpinBox vs QLineEdit

**QDoubleSpinBox is preferred for scientific input because:**
- Built-in range validation (min, max, decimals)
- Step controls (up/down arrows)
- Automatic formatting
- No need for custom validators
- Clear visual feedback for invalid input

**QLineEdit is needed when:**
- Material name input (string)
- Free-form text input

**Confidence:** HIGH — established Qt best practice.

### Signal/Slot Pattern for Parameter Updates

```python
# When any parameter changes, trigger recalculation
self.coil_radius_spin.valueChanged.connect(self.on_parameter_changed)
self.frequency_spin.valueChanged.connect(self.on_parameter_changed)
self.material_combo.currentTextChanged.connect(self.on_material_changed)

def on_parameter_changed(self) -> None:
    """Recalculate when any parameter changes."""
    if self._validate_inputs():
        self._run_calculation()
```

**Confidence:** HIGH — standard Qt pattern.

### Input Validation Strategy

**Layer 1: Widget-level validation**
- QDoubleSpinBox: min/max/decimals built-in
- QIntSpinBox: integer ranges

**Layer 2: Cross-field validation**
- Workpiece radius < coil inner radius
- Gap must be positive
- Frequency in 10-50 kHz range

**Layer 3: Calculation validation**
- Material properties available at temperature
- Geometry within analytical model validity range

**Confidence:** HIGH — layered validation is standard.

### Material Selector Design

```
Material: [Low Carbon Steel (AISI 1018) ▼]

Properties at 20°C:
  Resistivity:     1.43e-7 Ω·m
  Permeability:    200
  Curie Point:     770°C
  Density:         7870 kg/m³
```

**Implementation:**
- QComboBox populated from MaterialDatabase.list_materials()
- On selection change, update property preview labels
- Properties fetched from MaterialDatabase at default temperature (20°C)

**Confidence:** HIGH — straightforward implementation.

### State Management

**Approach:** Store current parameters in a dataclass, update from GUI, pass to calculation engine.

```python
@dataclass
class GUIState:
    coil_inner_radius: float
    coil_outer_radius: float
    coil_length: float
    coil_turns: int
    workpiece_radius: float
    workpiece_length: float
    frequency: float
    current: float
    material_name: str
    temperature: float
```

**Confidence:** HIGH — clean separation of GUI state from calculation.

### Threading Considerations

For Phase 4, calculations are fast enough to run on the main thread. Threading will be needed in Phase 5/6 for time-stepped simulations.

**For now:** Synchronous calculation on parameter change.

**Confidence:** HIGH — appropriate for current scope.

## Key References

1. **PySide6 Documentation**: https://doc.qt.io/qtforpython/
2. **Qt Layout Management**: https://doc.qt.io/qt-6/layout.html
3. **QDoubleSpinBox**: https://doc.qt.io/qt-6/qdoublespinbox.html
4. **QFormLayout**: https://doc.qt.io/qt-6/qformlayout.html

---
*Research for Phase 4: GUI Framework & Parameter Input*
*Researched: 2026-07-30*
