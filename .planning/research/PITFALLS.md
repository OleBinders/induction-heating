# Pitfalls Research

**Domain:** Scientific desktop application — induction heating simulator
**Resed:** 2026-07-30
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Incorrect Curie Point Transition Modeling

**What goes wrong:**
The permeability drop at the Curie temperature is modeled as a step function (abrupt change from μr >> 1 to μr = 1), which causes numerical instability and unrealistic heating behavior.

**Why it happens:**
The actual permeability transition is gradual and depends on the material's magnetic phase transition physics. A simple step function creates discontinuities in the calculation.

**How to avoid:**
Use a smooth transition function (e.g., sigmoid or polynomial) for permeability vs. temperature around Tc. Reference the Hopkinson effect and use empirically validated transition curves from literature (Rudnev Handbook, Zinn & Semiatin).

**Warning signs:**
- Temperature oscillations near Curie point during time-stepped simulation
- Non-convergence in iterative solver
- Sudden jumps in calculated skin depth

**Phase to address:** Phase 2 (Calculation Engine — Temperature-Dependent Properties)

---

### Pitfall 2: Unit Inconsistency in Electromagnetic Calculations

**What goes wrong:**
Mixing SI units (meters, Henries, Tesla) with CGS or practical units (mm, μH, Gauss) produces wildly incorrect results that are hard to detect.

**Why it happens:**
Electromagnetic formulas are sensitive to units. The skin depth formula δ = 503√(ρ/μf) from Wikipedia uses ρ in Ω·m, but many engineering references use Ω·cm or μΩ·cm.

**How to avoid:**
- Use Pint library for all physical quantities
- Define a single unit system (SI) as the canonical internal representation
- Add unit tests with known reference values (e.g., skin depth of copper at 1 MHz ≈ 66 μm)

**Warning signs:**
- Skin depth values that are orders of magnitude off expected range
- Power densities that don't match physical intuition
- Different results when switching between metric and imperial inputs

**Phase to address:** Phase 1 (Material Library + Unit System)

---

### Pitfall 3: Ignoring Proximity Effect in Coil Calculations

**What goes wrong:**
Only accounting for skin effect in the workpiece while ignoring proximity effect between coil turns leads to incorrect coil resistance and field distribution.

**Why it happens:**
Skin effect is well-known; proximity effect is less discussed but significant at 10-50 kHz, especially for closely spaced coil turns.

**How to avoid:**
- Include proximity effect correction factors in coil resistance calculations
- Reference Dowell's method or other analytical proximity effect models
- Document when proximity effect is significant vs. negligible

**Warning signs:**
- Coil heating predictions that don't match reality
- Efficiency calculations that are too optimistic
- Field distribution that doesn't account for turn-to-turn interaction

**Phase to address:** Phase 2 (Calculation Engine — Electromagnetic)

---

### Pitfall 4: Assuming Constant Properties During Heating

**What goes wrong:**
Using room-temperature material properties for the entire heating simulation, which is grossly inaccurate for surface hardening where temperatures exceed 800°C.

**Why it happens:**
It's simpler to implement, and many introductory texts present formulas with constant properties.

**How to avoid:**
- All material properties must be temperature-dependent functions
- Resistivity of steel increases ~6x from 20°C to 800°C
- Permeability drops sharply at Curie point (~770°C for iron)
- Specific heat and thermal conductivity also vary significantly

**Warning signs:**
- Heating curves that don't match published data
- Power requirements that seem too low or too high
- No change in heating rate as temperature increases

**Phase to address:** Phase 2 (Calculation Engine — Temperature-Dependent Properties)

---

### Pitfall 5: Analytical Model Applied Outside Validity Range

**What goes wrong:**
Using simplified analytical formulas (e.g., infinite solenoid approximation) for geometries where they don't apply (short coils, non-cylindrical workpieces).

**Why it happens:**
Analytical formulas often assume idealized conditions (infinite length, uniform fields) that don't match real setups.

**How to avoid:**
- Document the validity range of each analytical formula
- Apply correction factors for finite-length coils
- Warn users when geometry is outside validated range
- Reference: a/d ratio (workpiece radius / reference depth) should be > 4 for efficient heating

**Warning signs:**
- Results that diverge from known benchmarks
- Warning flags in literature about formula applicability
- Unphysical field distributions

**Phase to address:** Phase 2 (Calculation Engine — Validation)

---

### Pitfall 6: No Validation Against Known Results

**What goes wrong:**
Building the entire calculation engine without comparing results to published data or analytical benchmarks.

**Why it happens:**
No benchmark data was provided by the user, and it's easy to assume the formulas are correct if they compile.

**How to avoid:**
- Cross-reference every formula against at least 2 sources (textbooks, papers)
- Create unit tests with known reference values from literature
- Validate skin depth calculations against standard tables
- Compare power density results with published induction heating data

**Warning signs:**
- No unit tests for calculation functions
- No reference values in test suite
- "It looks right" as the only validation

**Phase to address:** Phase 2 (Calculation Engine — every sub-phase)

---

### Pitfall 7: GUI Blocks During Calculation

**What goes wrong:**
Running calculations on the main Qt thread, causing the GUI to freeze during time-stepped simulations.

**Why it happens:**
It's the simplest implementation — just call the calculation function from a button click handler.

**How to avoid:**
- Use QThread or QRunnable for calculation tasks
- Emit signals to update GUI with intermediate results
- Provide progress indicators for long-running simulations

**Warning signs:**
- GUI becomes unresponsive during simulation
- "Not Responding" in window title
- Can't cancel a running simulation

**Phase to address:** Phase 3 (GUI + Simulation Engine)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode material properties | Fast initial implementation | Can't add materials, can't update values | Never — use data files from start |
| Skip unit testing for calculations | Faster initial development | Undetected calculation errors | Never — calculations are the core value |
| Use constant properties initially | Simpler math | Wrong results for all realistic cases | Only for initial proof-of-concept, fix immediately |
| Single coil type first | Faster MVP | Architecture must support extension | Acceptable for v1, but design for extension |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Pint units with NumPy | Forgetting to use `.magnitude` in calculations | Use `ureg.Quantity` consistently, extract magnitude only for pure math |
| PySide6 signals with numpy arrays | Passing numpy arrays directly through signals | Convert to list or use pyqtSignal with proper type |
| Matplotlib in Qt | Creating new Figure objects repeatedly | Reuse FigureCanvas, update data instead of recreating |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Pure Python loops for temperature stepping | > 10s per simulation step | Use Numba @njit or NumPy vectorization | > 100 time steps |
| Recreating matplotlib figures | Memory leak, slow rendering | Update existing figure data | > 50 plot updates |
| Loading all material data at startup | Slow application launch | Lazy-load materials on demand | > 50 materials |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Executing user-provided geometry files | Code injection if using eval() | Parse geometry data with safe parsers only |
| Unvalidated file imports | Malformed files crash app | Validate all imported data with pydantic schemas |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No feedback during calculation | User thinks app is frozen | Progress bar, estimated time remaining |
| Cryptic error messages | User can't diagnose problems | Show which parameter is invalid and valid range |
| No default material values | User must know all properties | Pre-populate with standard values from library |

## "Looks Done But Isn't" Checklist

- [ ] **Skin depth calculation:** Often missing temperature dependence — verify δ changes with T
- [ ] **Curie transition:** Often modeled as step function — verify smooth transition
- [ ] **Power density:** Often calculated at surface only — verify radial/depth distribution
- [ ] **Coil efficiency:** Often ignores coil losses — verify coil resistance at operating temperature
- [ ] **Unit consistency:** Often mixed units — verify all calculations in SI internally
- [ ] **Material library:** Often missing key properties — verify all needed properties present for each material

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong Curie model | MEDIUM | Replace step function with smooth transition, re-run validation tests |
| Unit errors | HIGH | Audit all calculations, add Pint throughout, re-validate all results |
| No validation data | MEDIUM | Research literature, create reference test cases, compare results |
| GUI blocking | LOW | Move calculations to QThread, add progress indicators |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Incorrect Curie model | Phase 2: Calculation Engine | Unit tests with known Tc transition curves |
| Unit inconsistency | Phase 1: Material Library | Reference value tests (copper skin depth at 1 MHz) |
| Proximity effect ignored | Phase 2: Calculation Engine | Compare with Dowell's method results |
| Constant properties | Phase 2: Calculation Engine | Verify property changes with temperature |
| Analytical model misuse | Phase 2: Calculation Engine | Document validity ranges, add warnings |
| No validation | Phase 2: Every sub-phase | Cross-reference with literature values |
| GUI blocking | Phase 3: GUI + Engine | Test with long simulations, verify responsiveness |

## Sources

- "Handbook of Induction Heating" (Rudnev, CRC Press 2003) — common modeling mistakes
- "Elements of Induction Heating" (Zinn & Semiatin, ASM 1988) — validity ranges for formulas
- Scientific Python community best practices for unit handling and testing
- Qt threading best practices from Riverbank Computing documentation

---
*Pitfalls research for: Induction Heating Simulator*
*Researched: 2026-07-30*
