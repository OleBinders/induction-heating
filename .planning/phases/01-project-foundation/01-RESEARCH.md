# Phase 1 Research: Project Foundation

**Phase:** 01 — Project Foundation
**Researched:** 2026-07-30
**Confidence:** HIGH

## Python Project Structure

**Recommendation:** Use `src` layout with `pyproject.toml` (Hatchling backend).

```
induction_heating/
├── src/
│   └── induction_heating/
│       ├── __init__.py
│       ├── __main__.py
│       ├── core/
│       ├── materials/
│       └── gui/
├── tests/
├── pyproject.toml
└── README.md
```

**Rationale:**
- `src` layout prevents import confusion during development (you import the installed package, not the local directory)
- `pyproject.toml` is the modern standard (PEP 621), replacing `setup.py`
- Hatchling is lightweight and fast; uv is recommended for dependency management
- `__main__.py` enables `python -m induction_heating` entry point

**Confidence:** HIGH — this is the current Python packaging standard.

## Pint Unit System Integration

**Recommendation:** Create a centralized `units.py` module that initializes the UnitRegistry and defines custom units.

```python
# src/induction_heating/utils/units.py
import pint

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# Define electromagnetic units explicitly
ureg.define("tesla = kilogram / (second**2 * ampere) = T")
```

**Key patterns:**
- Always create ONE UnitRegistry instance (singleton pattern) — multiple registries are incompatible
- Use `Q_(value, "unit")` for creating quantities
- Use `.to("target_unit")` for conversion
- Use `.magnitude` to extract raw number for NumPy operations
- Pint works with NumPy arrays natively

**Common pitfalls:**
- Creating multiple UnitRegistry instances causes `ValueError` when comparing quantities
- Forgetting to extract `.magnitude` before passing to NumPy/SciPy functions that don't understand Pint
- Performance overhead: Pint adds ~2-5x overhead vs raw floats. Use `.magnitude` in tight loops

**Confidence:** HIGH — well-documented library with established patterns.

## Material Property Data Design

**Recommendation:** JSON files with pydantic validation, structured as temperature-property pairs.

```json
{
  "name": "Low Carbon Steel (AISI 1018)",
  "category": "steel",
  "density": {
    "value": 7870,
    "unit": "kg/m^3"
  },
  "curie_temperature": {
    "value": 770,
    "unit": "degC"
  },
  "resistivity": {
    "data": [
      {"temperature": 20, "value": 1.43e-7},
      {"temperature": 100, "value": 2.05e-7},
      {"temperature": 200, "value": 2.82e-7},
      {"temperature": 400, "value": 4.35e-7},
      {"temperature": 600, "value": 6.24e-7},
      {"temperature": 800, "value": 8.50e-7},
      {"temperature": 1000, "value": 1.05e-6}
    ],
    "unit": "ohm*m",
    "temperature_unit": "degC"
  },
  "relative_permeability": {
    "data": [
      {"temperature": 20, "value": 200},
      {"temperature": 400, "value": 180},
      {"temperature": 600, "value": 120},
      {"temperature": 700, "value": 50},
      {"temperature": 760, "value": 10},
      {"temperature": 770, "value": 1.0},
      {"temperature": 800, "value": 1.0},
      {"temperature": 1000, "value": 1.0}
    ],
    "dimensionless": true,
    "temperature_unit": "degC"
  }
}
```

**Rationale:**
- JSON is human-readable and editable
- Pydantic validates schema on load
- Temperature-property pairs enable interpolation
- Separate files per material category (steels.json, copper.json, etc.)

**Confidence:** HIGH — standard pattern for scientific data files.

## Temperature Interpolation

**Recommendation:** `scipy.interpolate.CubicSpline` for smooth interpolation, with `extrapolate=False` to prevent invalid extrapolation.

```python
from scipy.interpolate import CubicSpline

temps = [20, 100, 200, 400, 600, 800, 1000]
resistivities = [1.43e-7, 2.05e-7, 2.82e-7, 4.35e-7, 6.24e-7, 8.50e-7, 1.05e-6]

cs = CubicSpline(temps, resistivities, extrapolate=False)
rho_at_350 = cs(350)  # interpolated value
```

**Alternatives considered:**
- Linear interpolation: Simpler but less smooth; acceptable for resistivity
- PCHIP (`scipy.interpolate.PchipInterpolator`: Monotonicity-preserving; good for permeability which must stay positive
- Nearest neighbor: Too coarse for scientific calculations

**Recommendation:** Use `PchipInterpolator` for permeability (must stay positive and monotonic near Curie), `CubicSpline` for resistivity (smooth, well-behaved).

**Confidence:** MEDIUM-HIGH — scipy interpolation is well-tested; choice between CubicSpline and PCHIP depends on property behavior.

## PySide6 Bootstrap Pattern

**Recommendation:** Standard QApplication bootstrap in `__main__.py`:

```python
# src/induction_heating/__main__.py
import sys
from PySide6.QtWidgets import QApplication
from induction_heating.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Induction Heating Simulator")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**Confidence:** HIGH — standard Qt pattern.

## Reference Material Properties

**Key materials for induction heating (from literature):**

| Material | ρ at 20°C (Ω·m) | ρ at 800°C (Ω·m) | Curie T (°C) | μr at 20°C |
|----------|-----------------|-------------------|--------------|------------|
| Low carbon steel | 1.43e-7 | 8.50e-7 | 770 | 200-500 |
| Medium carbon steel | 1.70e-7 | 9.50e-7 | 760 | 200-400 |
| Stainless steel (304) | 7.20e-7 | 1.10e-6 | — (non-magnetic) | 1.0 |
| Copper | 1.68e-8 | 4.10e-8 | — | 1.0 |
| Aluminum | 2.65e-8 | 5.50e-8 | — | 1.0 |
| Brass (70/30) | 6.20e-8 | 1.20e-7 | — | 1.0 |

**Sources:**
- "Handbook of Induction Heating" (Rudnev, CRC Press 2003)
- "Elements of Induction Heating" (Zinn & Semiatin, ASM 1988)
- Wikipedia: Electrical resistivity and conductivity

**Confidence:** HIGH for room-temperature values, MEDIUM for high-temperature curves (vary by alloy composition).

## Physical Constants

Required constants for electromagnetic calculations:
- μ₀ = 4π × 10⁻⁷ H/m (permeability of free space)
- ε₀ = 8.854 × 10⁻¹² F/m (permittivity of free space)
- These are available in `scipy.constants` (`scipy.constants.mu_0`, `scipy.constants.epsilon_0`)

**Confidence:** HIGH — fundamental constants.

## Dependency Versions

| Package | Version | Purpose |
|---------|---------|---------|
| Python | >= 3.11 | Core language |
| PySide6 | >= 6.6 | GUI framework |
| NumPy | >= 2.0 | Array operations |
| SciPy | >= 1.13 | Interpolation, constants |
| Pint | >= 0.23 | Unit management |
| pydantic | >= 2.0 | Data validation |
| pytest | >= 8.0 | Testing |

**Confidence:** HIGH — current stable versions.

## Pitfalls for This Phase

1. **Multiple UnitRegistry instances** — Must use singleton pattern
2. **Pint + NumPy compatibility** — Pint 0.23+ supports NumPy 2.x; ensure versions align
3. **JSON schema validation** — Pydantic v2 has different syntax from v1; use `model_validate()` not `parse_obj()`
4. **Interpolation boundaries** — Must handle queries outside data range gracefully (return None or raise, not extrapolate)

---
*Research for Phase 1: Project Foundation*
*Researched: 2026-07-30*
