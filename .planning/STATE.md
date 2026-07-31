# State: Induction Heating Simulator

**Current Phase:** Phase 2 — Electromagnetic Calculation Engine
**Current Status:** Phase 2 planning complete, ready for execution
**Last Updated:** 2026-07-30

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-30 after initialization)

**Core value:** Accurately predict induction heating behavior for surface hardening and brazing applications using analytical methods with temperature-dependent material properties.

**Current focus:** Phase 2 — Electromagnetic Calculation Engine

## Phase State

| Phase | Status |
|-------|--------|
| 1. Project Foundation | Complete (35 tests pass) |
| 2. Electromagnetic Engine | Ready to execute (3 plans) |
| 3. Curie Transition | Pending |
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
- Skin depth: δ = √(2ρ/(ωμ))
- Eddy current: exponential decay for a/δ > 4, Bessel function for a/δ ≤ 4

## Next Action

Run `/gsd-execute-phase 2` to execute Phase 2: Electromagnetic Calculation Engine.
