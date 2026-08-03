---
phase: 7
plan: 07-01
name: Calculation Unit Tests
status: complete
tasks_completed: 4
tasks_total: 4
duration: ~3 min
completed: 2026-07-30
---

# Summary: Plan 07-01 — Calculation Unit Tests

## Completed

- [x] Created skin depth validation tests against 6 published reference values (all ±2%)
- [x] Created material property validation tests against 7 published reference values (all ±5%)
- [x] Created B-field validation tests against analytical solutions (±1% for infinite solenoid)
- [x] Updated copper material data to include 500°C reference point
- [x] All 18 new validation tests pass

## Verification

- Copper at 1 MHz: δ = 66 μm ✓ (±2%)
- Copper at 50 kHz: δ = 0.295 mm ✓ (±2%)
- Copper at 10 kHz: δ = 0.661 mm ✓ (±2%)
- Steel (μᵣ=200) at 10 kHz: δ = 0.135 mm ✓ (±2%)
- Steel (μᵣ=1) at 10 kHz: δ = 1.90 mm ✓ (±2%)
- Steel (μᵣ=1) at 50 kHz: δ = 0.85 mm ✓ (±2%)
- Steel resistivity at 20/400/800°C ✓ (±5%)
- Copper resistivity at 20/500°C ✓ (±5%)
- Aluminum resistivity at 20°C ✓ (±5%)
- Steel permeability at Curie point (770°C) = 1.0 ✓ (±0.1)
- Infinite solenoid B-field: 12.57 mT ✓ (±1%)
- Coil end field ≈ half center ✓ (±5%)
- Far field < 1% of center ✓
- Off-axis consistency at ρ=0 ✓

## Artifacts Produced

- `tests/test_validation_skin_depth.py` — 6 skin depth validation tests
- `tests/test_validation_materials.py` — 7 material property validation tests
- `tests/test_validation_bfield.py` — 5 B-field validation tests
- `src/induction_heating/materials/data/copper.json` — Updated with 500°C data point
