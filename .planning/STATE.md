# State: Induction Heating Simulator

**Current Phase:** Phase 3 — Temperature-Dependent Properties & Curie Transition
**Current Status:** Phase 3 planning complete, ready for execution
**Last Updated:** 2026-07-30

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-30 after initialization)

**Core value:** Accurately predict induction heating behavior for surface hardening and brazing applications using analytical methods with temperature-dependent material properties.

**Current focus:** Phase 3 — Temperature-Dependent Properties & Curie Transition

## Phase State

| Phase | Status |
|-------|--------|
| 1. Project Foundation | Complete (35 tests pass) |
| 2. Electromagnetic Engine | Complete (111 tests pass) |
| 3. Curie Transition | Ready to execute (2 plans) |
| 4. GUI Framework | Pending |
| 5. Cross-Section Visualization | Pending |
| 6. Results & Export | Pending |
| 7. Validation & Testing | Pending |

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

## Next Action

Run `/gsd-execute-phase 3` to execute Phase 3: Temperature-Dependent Properties & Curie Transition.
