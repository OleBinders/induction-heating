# Phase 7 Research: Validation & Testing

**Phase:** 07 — Validation & Testing
**Researched:** 2026-07-30
**Confidence:** HIGH

## Validation Strategy

### Reference Values from Literature

**Skin Depth (from Wikipedia, Zinn & Semiatin):**

| Material | f (kHz) | ρ (Ω·m) | μᵣ | δ (mm) expected |
|----------|---------|---------|-----|-----------------|
| Copper | 1000 | 1.68e-8 | 1.0 | 0.066 |
| Copper | 50 | 1.68e-8 | 1.0 | 0.295 |
| Copper | 10 | 1.68e-8 | 1.0 | 0.661 |
| Steel (μᵣ=200) | 10 | 1.43e-7 | 200 | 0.135 |
| Steel (μᵣ=1) | 10 | 1.43e-7 | 1.0 | 1.90 |

**Material Properties (from Rudnev Handbook):**

| Material | T (°C) | ρ (Ω·m) expected |
|----------|--------|-------------------|
| Low Carbon Steel | 20 | 1.43e-7 |
| Low Carbon Steel | 400 | 4.35e-7 |
| Low Carbon Steel | 800 | 8.50e-7 |
| Copper | 20 | 1.68e-8 |
| Copper | 500 | 4.50e-8 |
| Aluminum | 20 | 2.65e-8 |
| Aluminum | 400 | 5.20e-8 |

**B-Field (analytical verification):**

For infinite solenoid: B = μ₀NI/l
- N=500, I=10A, l=0.5m → B = 4π×10⁻⁷ × 500 × 10 / 0.5 = 0.01257 T = 12.57 mT

### Validation Approach

1. **Unit-level validation**: Each calculation function tested against known reference values
2. **Integration validation**: Full pipeline produces physically reasonable results
3. **Cross-reference validation**: Compare against published data from at least 2 sources
4. **Edge case validation**: Test boundary conditions (T=Tc, a/δ=4, etc.)

### Tolerance Levels

- Skin depth: ±2% (analytical formula is exact)
- Material properties: ±5% (varies by alloy composition)
- B-field: ±1% for infinite solenoid, ±5% for finite solenoid
- Power density: ±10% (analytical approximations)

**Confidence:** HIGH — well-established reference values.

## End-to-End Testing

### GUI Integration Tests

- Full workflow: set parameters → run → verify results display
- Material change: select material → verify property plot updates
- Save/load: save simulation → load → verify all panels populated
- Export: run → export CSV → verify file content

### Performance Tests

- Calculation time for 100x100 grid should be < 1 second
- GUI should remain responsive during calculation
- Memory usage should be reasonable (< 100 MB)

**Confidence:** MEDIUM — performance depends on hardware.

## Key References

1. **"Elements of Induction Heating"** — Zinn & Semiatin (ASM International, 1988)
2. **"Handbook of Induction Heating"** — Rudnev (CRC Press, 2003)
3. **Wikipedia: Skin effect** — Reference skin depth values
4. **Wikipedia: Electrical resistivity** — Reference resistivity values

---
*Research for Phase 7: Validation & Testing*
*Researched: 2026-07-30*
