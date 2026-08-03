# State: Induction Heating Simulator

**Current Phase:** Phase 7 — Validation & Testing
**Current Status:** Phase 6 complete, ready for Phase 7
**Last Updated:** 2026-07-30

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-30 after initialization)

**Core value:** Accurately predict induction heating behavior for surface hardening and brazing applications using analytical methods with temperature-dependent material properties.

**Current focus:** Phase 7 — Validation & Testing

## Phase State

| Phase | Status |
|-------|--------|
| 1. Project Foundation | Complete (35 tests pass) |
| 2. Electromagnetic Engine | Complete (111 tests pass) |
| 3. Curie Transition | Complete (159 tests pass) |
| 4. GUI Framework | Complete (201 tests pass) |
| 5. Cross-Section Visualization | Complete (216 tests pass) |
| 6. Results & Export | Complete (238 tests pass) |
| 7. Validation & Testing | Ready to plan |

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

## Next Action

Run `/gsd-plan-phase 7` to create detailed plan for Phase 7: Validation & Testing.
