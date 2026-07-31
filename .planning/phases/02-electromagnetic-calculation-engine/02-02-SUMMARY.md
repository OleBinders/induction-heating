---
phase: 2
plan: 02-02
name: Skin Depth and Magnetic Field
status: complete
tasks_completed: 4
tasks_total: 4
duration: ~5 min
completed: 2026-07-30
---

# Summary: Plan 02-02 — Skin Depth and Magnetic Field

## Completed

- [x] Implemented skin depth calculation: δ = √(2ρ/(ωμ)) with validation
- [x] Implemented solenoid B-field on axis: exact finite solenoid formula
- [x] Implemented solenoid B-field off axis: elliptic integrals (Callaghan & Maslen NASA TN D-465)
- [x] Created 26 unit tests with reference value validation

## Verification

**Skin depth reference values (all within 2%):**
- Copper at 1 MHz: δ = 66 μm ✓
- Copper at 50 kHz: δ = 0.295 mm ✓
- Copper at 10 kHz: δ = 0.661 mm ✓
- Steel (μᵣ=200) at 10 kHz: δ = 0.135 mm ✓
- Steel (μᵣ=1) at 10 kHz: δ = 1.90 mm ✓

**B-field validations:**
- Long solenoid center: B ≈ μ₀NI/l ✓
- Coil end: B ≈ half of center value ✓
- Far from coil: B → 0 ✓
- Off-axis on-axis consistency: B_z matches on-axis function at ρ=0 ✓
- Off-axis B_ρ = 0 on symmetry axis ✓

## Key Implementation Details

- Off-axis B-field uses Carlson symmetric forms (elliprf, elliprj) for Π(n,m) since scipy.special lacks ellippi
- On-axis limit handled correctly (Π(0,0) = π/2)
- Both scalar and array inputs supported
- `pytest tests/test_electromagnetic.py -v` — 26 passed

## Artifacts Produced

- `src/induction_heating/core/electromagnetic.py` — Skin depth, on-axis B-field, off-axis B-field
- `tests/test_electromagnetic.py` — 26 electromagnetic calculation tests
