# Phase 3 Research: Temperature-Dependent Properties & Curie Transition

**Phase:** 03 — Temperature-Dependent Properties & Curie Transition
**Researched:** 2026-07-30
**Confidence:** HIGH

## Curie Point Transition Physics

### Ferromagnetic → Paramagnetic Transition

Below Tc: material is ferromagnetic with high relative permeability (μᵣ = 100-500 for steel)
Above Tc: material is paramagnetic with μᵣ ≈ 1.0

The transition is NOT a step function — it's a smooth phase transition governed by critical exponents.

### Critical Exponents

**Approaching Tc from below (T < Tc):**
```
M ∼ (Tc - T)^β
```
where β ≈ 1/2 for mean-field model (Ising model in 3D: β ≈ 0.365)

**Approaching Tc from above (T > Tc):**
```
χ ∼ 1 / (T - Tc)^γ
```
where γ ≈ 1 for mean-field model

**Curie-Weiss Law (T ≫ Tc):**
```
χ = C / (T - Tc)
μᵣ = 1 + χ
```

**Confidence:** HIGH — standard statistical physics.

## Hopkinson Effect

The Hopkinson effect describes the peak in magnetic permeability just below the Curie temperature. For some steels, μᵣ actually increases slightly as T approaches Tc from below, before dropping sharply.

**For this project:** We can model this as part of the smooth transition curve in the material data files. The PchipInterpolator already handles this correctly since it preserves monotonicity only when needed.

**Confidence:** MEDIUM — effect is real but small for most engineering steels.

## Smooth Transition Modeling Approaches

### Approach 1: Sigmoid Function

```
μᵣ(T) = 1 + (μᵣ₀ - 1) / (1 + exp(k * (T - Tc)))
```

Where:
- μᵣ₀ = permeability at room temperature
- Tc = Curie temperature
- k = steepness parameter (controls transition width)

**Pros:** Simple, smooth, guaranteed to stay ≥ 1
**Cons:** Requires tuning k for each material; may not match actual physics

**Confidence:** HIGH — widely used in engineering approximations.

### Approach 2: Polynomial Transition

```
μᵣ(T) = 1 + (μᵣ₀ - 1) * (1 - ((T - T₁) / (Tc - T₁))^n)  for T₁ < T < Tc
μᵣ(T) = 1  for T ≥ Tc
```

Where T₁ is the temperature where permeability starts dropping.

**Pros:** Easy to control transition start and end
**Cons:** Not smooth at Tc if n is small; discontinuous derivative

**Confidence:** MEDIUM — used in some induction heating software.

### Approach 3: Data-Driven Interpolation (Current Approach)

Use the temperature-dependent data points already in the material JSON files, interpolated with PchipInterpolator.

**Pros:** Matches actual measured data; no assumptions about functional form
**Cons:** Requires accurate data points; interpolation may not capture physics between points

**Current status:** Already implemented in Phase 1. The material data files include points through the Curie transition.

**Confidence:** HIGH — this is what we already have and it works.

### Recommendation

**Use Approach 3 (data-driven) as primary**, with Approach 1 (sigmoid) as a fallback for materials without detailed transition data.

The current material JSON files already include permeability data points through the Curie transition (e.g., for low carbon steel: 20°C→200, 700°C→50, 760°C→5, 770°C→1.0). The PchipInterpolator produces a smooth, monotonic transition that stays ≥ 1.0.

## Temperature-Dependent Resistivity

Resistivity increases approximately linearly with temperature for metals:

```
ρ(T) = ρ₀ * (1 + α * (T - T₀))
```

Where α is the temperature coefficient of resistivity.

For steel: α ≈ 0.006 /°C
For copper: α ≈ 0.0039 /°C
For aluminum: α ≈ 0.0043 /°C

**However:** The linear approximation breaks down at high temperatures and near phase transitions. The cubic spline interpolation from the material data files is more accurate.

**Confidence:** HIGH — standard materials science.

## Temperature-Dependent Specific Heat

Specific heat also varies with temperature, especially near phase transitions:

For steel:
- At 20°C: cp ≈ 450 J/(kg·K)
- At 700°C: cp ≈ 650 J/(kg·K)
- Near Curie point: cp peaks due to latent heat of magnetic transition
- At 900°C: cp ≈ 700 J/(kg·K)

**Confidence:** MEDIUM — values vary by alloy composition.

## Temperature-Dependent Thermal Conductivity

Thermal conductivity generally decreases with temperature for metals:

For steel:
- At 20°C: k ≈ 50 W/(m·K)
- At 500°C: k ≈ 35 W/(m·K)
- At 800°C: k ≈ 25 W/(m·K)

**Confidence:** MEDIUM — values vary by alloy composition.

## Validation Reference Values

### Curie Point Transition (Low Carbon Steel)

| T (°C) | μᵣ (expected) |
|--------|---------------|
| 20 | 200 |
| 400 | 180 |
| 600 | 120 |
| 700 | 50 |
| 750 | 15 |
| 760 | 5 |
| 770 | 1.0 |
| 800 | 1.0 |

**Source:** Rudnev Handbook, Zinn & Semiatin

### Resistivity vs Temperature (Low Carbon Steel)

| T (°C) | ρ (Ω·m) (expected) |
|--------|---------------------|
| 20 | 1.43e-7 |
| 200 | 2.82e-7 |
| 400 | 4.35e-7 |
| 600 | 6.24e-7 |
| 800 | 8.50e-7 |
| 1000 | 1.05e-6 |

**Source:** Rudnev Handbook

## Implementation Considerations

### Interpolation Method Selection

- **Resistivity:** CubicSpline (smooth, well-behaved for monotonic data)
- **Permeability:** PchipInterpolator (monotonicity-preserving, stays ≥ 1.0)
- **Specific heat:** CubicSpline (may have peaks near phase transitions)
- **Thermal conductivity:** CubicSpline (smooth decrease)

### Edge Cases

1. **Temperature below data range:** Raise ValueError (no extrapolation)
2. **Temperature above data range:** Raise ValueError
3. **Temperature exactly at data point:** Return exact value (interpolation passes through data points)
4. **Non-magnetic material:** μᵣ = 1.0 at all temperatures (no interpolation needed)

### Performance

- Interpolation is fast (O(log n) lookup + O(1) evaluation)
- For time-stepped simulations, pre-compute interpolation coefficients
- Consider caching results for common temperature queries

## Key References

1. **"Handbook of Induction Heating"** — Rudnev (CRC Press, 2003)
   - Material properties vs temperature
   - Curie point effects on heating

2. **"Elements of Induction Heating"** — Zinn & Semiatin (ASM International, 1988)
   - Temperature-dependent property modeling
   - Hopkinson effect discussion

3. **Wikipedia: Curie temperature** — Critical exponents, Curie-Weiss law

4. **NIST Materials Data** — Reference values for material properties

---
*Research for Phase 3: Temperature-Dependent Properties & Curie Transition*
*Researched: 2026-07-30*
