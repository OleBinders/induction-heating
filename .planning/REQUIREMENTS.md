# Requirements

**Project:** Induction Heating Simulator
**Version:** v1 Scope
**Created:** 2026-07-30

## v1 Requirements

### Material Library

- [ ] REQ-MAT-001: Material database with temperature-dependent resistivity for common metals (steel, copper, aluminum, brass)
- [ ] REQ-MAT-002: Temperature-dependent magnetic permeability with Curie point transition modeling
- [ ] REQ-MAT-003: Material data stored in external files (JSON) for easy extension
- [ ] REQ-MAT-004: Material selection UI with search/filter
- [ ] REQ-MAT-005: Interpolation of material properties at arbitrary temperatures

### Calculation Engine — Electromagnetic

- [ ] REQ-CALC-001: Skin depth calculation δ = √(2ρ / ωμ) with temperature-dependent inputs
- [ ] REQ-CALC-002: Magnetic field distribution for solenoid coil geometry (analytical)
- [ ] REQ-CALC-003: Eddy current density distribution in cylindrical workpiece
- [ ] REQ-CALC-004: Power density calculation (Joule heating P = J²ρ)
- [ ] REQ-CALC-005: Frequency range support: 10–50 kHz
- [ ] REQ-CALC-006: All calculations use SI units internally (enforced via Pint)
- [ ] REQ-CALC-007: Curie point transition — smooth permeability drop from ferromagnetic (μr >> 1) to paramagnetic (μr ≈ 1)
- [ ] REQ-CALC-008: Calculation validation against published reference values from literature

### Geometry System

- [ ] REQ-GEO-001: Solenoid coil geometry definition (inner radius, outer radius, length, turns)
- [ ] REQ-GEO-002: Cylindrical workpiece geometry definition (radius, length)
- [ ] REQ-GEO-003: Axisymmetric (cylindrical) 2D cross-section representation
- [ ] REQ-GEO-004: Geometry validation (dimensions must be physically valid)

### GUI — Parameter Input

- [ ] REQ-GUI-001: Input panel for coil parameters (radius, length, turns, current)
- [ ] REQ-GUI-002: Input panel for workpiece parameters (radius, length)
- [ ] REQ-GUI-003: Input panel for operating parameters (frequency, current amplitude)
- [ ] REQ-GUI-004: Material selection dropdown with property preview
- [ ] REQ-GUI-005: Input validation with error messages and valid ranges

### GUI — Visualization

- [ ] REQ-VIZ-001: 2D cross-section view showing coil and workpiece geometry
- [ ] REQ-VIZ-002: Magnetic field strength contour overlay on cross-section
- [ ] REQ-VIZ-003: Power density contour overlay on cross-section
- [ ] REQ-VIZ-004: Pan and zoom on cross-section view
- [ ] REQ-VIZ-005: Color scale legend for field/power density maps

### GUI — Results Display

- [ ] REQ-RES-001: Numerical results panel (skin depth, total power, efficiency)
- [ ] REQ-RES-002: Plot of property vs. temperature (resistivity, permeability curves)
- [ ] REQ-RES-003: Plot of field/current/power vs. radial depth
- [ ] REQ-RES-004: Export plots as PNG/SVG

### Save/Load

- [ ] REQ-IO-001: Save simulation configuration (geometry, parameters, materials) to file
- [ ] REQ-IO-002: Load simulation configuration from file

## v2 Requirements (Deferred)

- [ ] REQ-V2-001: Pancake coil geometry
- [ ] REQ-V2-002: Helical coil geometry
- [ ] REQ-V2-003: Internal coil geometry
- [ ] REQ-V2-004: Planar/rectangular geometry support
- [ ] REQ-V2-005: Time-stepped thermal simulation (temperature evolution over time)
- [ ] REQ-V2-006: Custom coil geometry designer
- [ ] REQ-V2-007: Geometry import (DXF/STEP)
- [ ] REQ-V2-008: Parameter sweep / optimization
- [ ] REQ-V2-009: Multi-material workpieces
- [ ] REQ-V2-010: Export results as CSV

## Out of Scope

- Full 3D FEM simulation — analytical/semi-analytical methods only
- Frequency range beyond 50 kHz (for now)
- Melting applications — surface hardening and brazing only
- Real-time thermal simulation with convection/radiation heat loss (initial version)
- Multi-physics (stress, phase transformation)

## Definition of Done

- [ ] All calculation functions have unit tests with reference values from literature
- [ ] Skin depth calculation validated against standard tables (e.g., copper at 1 MHz ≈ 66 μm)
- [ ] Magnetic field calculation validated against analytical reference for infinite solenoid
- [ ] Curie transition produces smooth, numerically stable results
- [ ] All physical quantities use Pint units internally
- [ ] GUI is responsive during calculation (no blocking)
- [ ] Material library includes at least: low-carbon steel, medium-carbon steel, copper, aluminum, brass

---
*Requirements for: Induction Heating Simulator v1*
*Created: 2026-07-30*
