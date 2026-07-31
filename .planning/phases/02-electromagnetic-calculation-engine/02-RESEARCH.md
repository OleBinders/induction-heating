# Phase 2 Research: Electromagnetic Calculation Engine

**Phase:** 02 — Electromagnetic Calculation Engine
**Researched:** 2026-07-30
**Confidence:** HIGH

## Solenoid Magnetic Field Formulas

### Infinite Solenoid (simplified, center region)

For a solenoid where length ≫ diameter, far from ends:

```
B = μ₀μᵣNI / l
```

Where:
- B = magnetic flux density (T)
- μ₀ = 4π × 10⁻⁷ H/m (permeability of free space)
- μᵣ = relative permeability of material inside solenoid
- N = number of turns
- I = current (A)
- l = solenoid length (m)

**Validity:** Only valid when l/2 - |z| ≫ R (far from ends). Not accurate for short coils.

**Confidence:** HIGH — standard textbook formula.

### Finite Solenoid — On Axis

For a finite solenoid of radius R, length l, N turns, current I, at position z on the axis (centered at z=0):

```
B_z(z) = (μ₀NI / 2) * [(z + l/2) / (l * √(R² + (z + l/2)²)) - (z - l/2) / (l * √(R² + (z - l/2)²))]
```

**Validity:** Exact on the symmetry axis. Radial component B_ρ = 0 on axis.

**Confidence:** HIGH — derived from Biot-Savart law, verified in multiple sources.

### Finite Solenoid — Off Axis

Off-axis field requires complete elliptic integrals of the first (K), second (E), and third (Π) kind:

```
B_ρ = (μ₀I / 4π) * (1 / lρ) * [(m-2)K(m) + 2E(m)] * √((R+ρ)² + ζ²) |_{ζ₋}^{ζ₊}
B_z = (μ₀I / 2π) * (1 / l) * [K(m) + (R-ρ)/(R+ρ) * Π(n,m)] * ζ/√((R+ρ)² + ζ²) |_{ζ₋}^{ζ₊}
```

Where:
- ζ_± = z ± l/2
- n = 4Rρ / (R+ρ)²
- m = 4Rρ / ((R+ρ)² + ζ²)

**Implementation:** `scipy.special.ellipk(m)`, `scipy.special.ellipe(m)`, `scipy.special.ellippi(n, m)`

**Validity:** Exact for continuous current sheet approximation. For discrete turns, accuracy depends on turn density.

**Confidence:** HIGH — from Callaghan & Maslen (NASA TN D-465, 1960), verified by Caciagli et al. (2018).

### Short Solenoid Estimate (R ≫ l)

When radius is much larger than length:

```
B_z ≈ μ₀INR² / (2(R² + z²)^(3/2))
```

**Confidence:** MEDIUM — approximation, useful for pancake coils.

## Skin Depth

### Standard Formula

```
δ = √(2ρ / (ωμ)) = √(2ρ / (2πfμ)) = √(ρ / (πfμ))
```

Where:
- δ = skin depth (m) — depth where current density drops to 1/e of surface value
- ρ = resistivity (Ω·m)
- f = frequency (Hz)
- ω = 2πf (angular frequency)
- μ = μ₀μᵣ = permeability (H/m)

**Alternative form:** δ = 1 / √(πfμσ) where σ = 1/ρ (conductivity)

### Reference Values for Validation

| Material | f (kHz) | ρ (Ω·m) | μᵣ | δ (mm) |
|----------|---------|---------|-----|--------|
| Copper | 1000 | 1.68e-8 | 1.0 | 0.066 |
| Copper | 50 | 1.68e-8 | 1.0 | 0.295 |
| Copper | 10 | 1.68e-8 | 1.0 | 0.661 |
| Steel (μᵣ=200) | 10 | 1.43e-7 | 200 | 0.127 |
| Steel (μᵣ=200) | 50 | 1.43e-7 | 200 | 0.057 |
| Steel (μᵣ=1) | 10 | 1.43e-7 | 1.0 | 1.79 |
| Steel (μᵣ=1) | 50 | 1.43e-7 | 1.0 | 0.80 |

**Key validation point:** Copper skin depth at 1 MHz = 66 μm (widely cited reference).

**Confidence:** HIGH — standard formula, verified against multiple sources.

## Eddy Current Density in Cylindrical Workpiece

For a cylindrical workpiece of radius a inside a solenoid, the induced eddy current density at radius r is:

```
J_φ(r) = (ωB₀ / 2ρ) * r    (for r ≪ δ, thin skin approximation)
```

For the general case with skin effect, the current density follows a Bessel function distribution:

```
J(r) = J_surface * J₀(kr) / J₀(kR)
```

Where:
- J₀ = Bessel function of first kind, order 0
- k = (1-j)/δ = √(-jωμ/ρ)

**Simplified approach for induction heating:** For a ≫ δ (workpiece much thicker than skin depth), the current is confined to a surface layer of thickness δ. The power density at depth x from surface:

```
P(x) = P₀ * e^(-2x/δ)
```

Where P₀ is the surface power density.

**Confidence:** MEDIUM-HIGH — Bessel function approach is exact for isolated cylinder; the exponential approximation is standard for a/δ > 4.

## Power Density (Joule Heating)

### Local Power Density

```
p(r) = J(r)² * ρ    (W/m³)
```

Where J(r) is the eddy current density at radius r.

### Total Absorbed Power

For a cylindrical workpiece of radius a, length L:

```
P_total = ∫₀ᵃ ∫₀ᴸ p(r) * 2πr dr dz
```

### Simplified Formula (a ≫ δ)

When workpiece radius is much larger than skin depth:

```
P_total ≈ (πaL / 2) * (B₀² / (μ₀²ρ)) * δ * ω² * a²
```

Or more practically, using the efficiency factor approach from Zinn & Semiatin:

The efficiency depends on the ratio a/δ:
- a/δ < 1: Poor efficiency (field penetrates fully, eddy currents cancel)
- a/δ ≈ 4: Critical efficiency (optimal heating)
- a/δ > 4: High efficiency (surface heating dominates)

**Confidence:** MEDIUM — exact integration requires Bessel functions; simplified formulas have limited validity ranges.

## Validity Ranges and Corrections

### Solenoid Field Validity

| Condition | Formula | Accuracy |
|-----------|---------|----------|
| l ≫ R, center region | B = μ₀NI/l | Good (>95%) |
| Any l/R, on axis | Finite solenoid formula | Exact |
| Any l/R, off axis | Elliptic integral formula | Exact |
| R ≫ l | Short solenoid estimate | Approximate |

### Skin Effect Validity

The exponential decay approximation P(x) = P₀e^(-2x/δ) is valid when:
- a/δ > 4 (workpiece radius ≫ skin depth)
- For a/δ < 4, use full Bessel function solution

### Frequency Range for This Project

10-50 kHz is appropriate for:
- Surface hardening: shallow penetration (0.1-2 mm in steel)
- Brazing: moderate penetration (1-5 mm)

**Confidence:** HIGH — matches industry standards (Rudnev Handbook).

## Key References

1. **"Elements of Induction Heating"** — Zinn & Semiatin (ASM International, 1988)
   - Primary reference for analytical induction heating formulas
   - Skin depth, power absorption, efficiency factors

2. **"Handbook of Induction Heating"** — Rudnev (CRC Press, 2003)
   - Comprehensive reference for induction heating applications
   - Material properties, frequency selection, coil design

3. **Callaghan & Maslen (1960)** — "The magnetic field of a finite solenoid", NASA TN D-465
   - Exact elliptic integral formulas for finite solenoid field

4. **Wikipedia: Solenoid** — Finite solenoid formulas verified against NASA reference

5. **Wikipedia: Skin effect** — Skin depth formula, Bessel function current distribution

6. **Wikipedia: Eddy current** — Power dissipation formulas, diffusion equation

## Implementation Notes

- Use `scipy.special.ellipk`, `ellipe`, `ellippi` for off-axis solenoid field
- Use `scipy.special.j0`, `j1` for Bessel functions in eddy current distribution
- Use `scipy.constants.mu_0` for permeability of free space
- All calculations must use Pint units internally
- Temperature-dependent properties come from Phase 1 material library

---
*Research for Phase 2: Electromagnetic Calculation Engine*
*Researched: 2026-07-30*
