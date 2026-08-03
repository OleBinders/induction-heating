# State: Induction Heating Simulator

**Current Phase:** All phases complete — v1.0 MVP ready
**Current Status:** All 7 phases complete, 271 tests passing
**Last Updated:** 2026-07-30

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-30 after initialization)

**Core value:** Accurately predict induction heating behavior for surface hardening and brazing applications using analytical methods with temperature-dependent material properties.

**Current focus:** Project complete — ready for use and future enhancement

## Phase State

| Phase | Status |
|-------|--------|
| 1. Project Foundation | Complete (35 tests pass) |
| 2. Electromagnetic Engine | Complete (111 tests pass) |
| 3. Curie Transition | Complete (159 tests pass) |
| 4. GUI Framework | Complete (201 tests pass) |
| 5. Cross-Section Visualization | Complete (216 tests pass) |
| 6. Results & Export | Complete (238 tests pass) |
| 7. Validation & Testing | Complete (271 tests pass) |

## Active Decisions

- Analytical methods only (no FEM)
- PySide6 for GUI (LGPL license)
- Pint for unit management
- NumPy/SciPy for calculations
- HDF5 for simulation data
- Frequency range: 10-50 kHz
- Focus: surface hardening and brazing
- CubicSpline for resistivity interpolation, PchipInterpolator for permeability
- Partial name matching for material lookup
- Finite solenoid B-field using elliptic integrals (Callaghan & Maslen NASA TN D-465)
- Carlson symmetric forms (elliprf, elliprj) for Π(n,m) — scipy lacks ellippi
- Skin depth: δ = √(2ρ/(ωμ))
- Eddy current: exponential decay for a/δ > 4, Kelvin functions for a/δ ≤ 4
- Trapezoidal integration for total power
- Data-driven Curie transition (PchipInterpolator) with sigmoid fallback
- PropertySnapshot for consistent temperature-dependent property access
- QDoubleSpinBox for all numeric GUI inputs (not QLineEdit)
- Frequency locked to 10-50 kHz in GUI
- Cross-field validation with Run button enabled/disabled
- Matplotlib for visualization (contourf, pcolormesh)
- viridis colormap for B-field, plasma for power density
- NavigationToolbar2QT for pan/zoom
- CSV export for calculation data, JSON for simulation state
- Validation tolerances: ±2% skin depth, ±5% material properties, ±1% B-field

## Next Action

All phases complete. Project is ready for use. Future enhancements could include:
- Phase 8: Time-stepped thermal simulation (temperature evolution over time)
- Phase 9: Additional coil types (pancake, helical, internal)
- Phase 10: Planar/rectangular geometry support
- Phase 11: Geometry importer (DXF/STEP)
