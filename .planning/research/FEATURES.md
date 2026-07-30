# Feature Research

**Domain:** Scientific desktop application — induction heating simulator
**Researched:** 2026-07-30
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Material library with properties | Core to any simulation tool | MEDIUM | Must include temperature-dependent data, Curie points |
| Parameter input panel | Users need to specify coil geometry, frequency, power | LOW | Frequency, current, turns, gap, workpiece dimensions |
| 2D cross-section visualization | Users need to see the setup | MEDIUM | Coil + workpiece geometry, field contours |
| Calculation results display | The whole point of the tool | MEDIUM | Temperature profiles, penetration depth, power density |
| Save/load simulations | Users iterate on designs | LOW | File format for complete simulation state |
| Unit system (SI) | Scientific tool requirement | LOW | Use Pint for consistent unit handling |
| Material selection from library | Users shouldn't type properties manually | LOW | Dropdown/search for materials |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Temperature-dependent property evolution | Most tools use constant properties | HIGH | Critical for accuracy through Curie transition |
| Multiple coil geometry types | Solenoid, pancake, helical, internal, custom | HIGH | Each requires different analytical formulations |
| Both axisymmetric and planar geometries | Covers more use cases | HIGH | Different mathematical treatments needed |
| Curie point transition modeling | Ferromagnetic → paramagnetic transition | HIGH | Non-linear permeability drop is the hardest part |
| Time-stepped thermal simulation | Shows heating over time, not just steady-state | HIGH | Requires iterative solver with property updates |
| Geometry designer/importer | Users can define custom shapes | HIGH | DXF/STEP import or built-in shape designer |
| Export results (CSV, plots) | For reports and further analysis | LOW | Matplotlib export, CSV data dump |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full 3D simulation | "More dimensions = more accurate" | Analytical 3D is intractable; FEM is a different product | Stick to 2D axisymmetric + planar as specified |
| Real-time physics animation | Looks impressive | Analytical calculations are fast but not real-time at 60fps | Pre-compute and show time-lapse instead |
| Automatic coil optimization | "Find the best coil for my part" | Requires inverse problem solving + FEM or ML | Provide parameter sweep tools instead |
| Multi-physics (stress, phase transformation) | Comprehensive analysis | Each physics domain is a major project | Export data to specialized tools |

## Feature Dependencies

```
Material Library
    └──required──> Temperature-Dependent Properties
                       └──required──> Curie Point Modeling

Geometry System
    └──required──> 2D Cross-Section Visualization
    └──enhances──> Coil Geometry Types (solenoid, pancake, etc.)

Calculation Engine
    └──required──> Material Library
    └──required──> Geometry System
    └──required──> Parameter Input
    └──enhances──> Time-Stepped Thermal Simulation

Time-Stepped Simulation
    └──required──> Temperature-Dependent Properties
    └──required──> Calculation Engine

Results Display
    └──required──> Calculation Engine
    └──enhances──> Export (CSV, plots)
```

### Dependency Notes

- **Material Library is foundational:** Everything depends on having accurate material data
- **Calculation Engine is the core:** All other features serve or extend it
- **Geometry System enables visualization:** Can't show cross-sections without geometry definitions
- **Time-stepped simulation is the most complex:** It chains all other subsystems together

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Material library with temperature-dependent properties — core to all calculations
- [ ] Solenoid coil + cylindrical workpiece (axisymmetric) — simplest geometry case
- [ ] Analytical calculation engine (skin depth, field strength, eddy current density, power) — the core value
- [ ] 2D cross-section visualization — users need to see results
- [ ] Parameter input (frequency, current, turns, dimensions) — basic configuration
- [ ] Curie point transition modeling — essential for surface hardening accuracy
- [ ] Save/load simulations — basic workflow requirement

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Additional coil types (pancake, helical, internal) — triggered by user demand
- [ ] Planar/rectangular geometry — triggered by brazing use cases
- [ ] Time-stepped thermal simulation — triggered by need for heating curves
- [ ] Export results (CSV, plots) — triggered by reporting needs

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Geometry importer (DXF/STEP) — why defer: complex CAD integration
- [ ] Custom coil designer — why defer: requires significant UI work
- [ ] Parameter sweep / optimization — why defer: computationally expensive
- [ ] Multi-material workpieces — why defer: adds complexity to analytical model

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Material library (temp-dependent) | HIGH | MEDIUM | P1 |
| Solenoid + cylindrical geometry | HIGH | MEDIUM | P1 |
| Calculation engine (analytical) | HIGH | HIGH | P1 |
| 2D cross-section visualization | HIGH | MEDIUM | P1 |
| Curie point transition modeling | HIGH | HIGH | P1 |
| Parameter input panel | HIGH | LOW | P1 |
| Save/load simulations | MEDIUM | LOW | P2 |
| Additional coil types | MEDIUM | HIGH | P2 |
| Planar geometry | MEDIUM | HIGH | P2 |
| Time-stepped thermal simulation | HIGH | HIGH | P2 |
| Export results | MEDIUM | LOW | P2 |
| Geometry designer/importer | LOW | HIGH | P3 |

## Competitor Feature Analysis

| Feature | COMSOL | ANSYS Maxwell | Open-source (FEMM) | Our Approach |
|---------|--------|---------------|-------------------|--------------|
| FEM simulation | Yes | Yes | Yes | No — analytical only |
| Temperature-dependent properties | Yes | Yes | Limited | Yes — core feature |
| Curie point modeling | Yes (with effort) | Yes | No | Yes — explicit support |
| 2D cross-section | Yes | Yes | Yes | Yes — primary view |
| Quick setup | No (complex) | No (complex) | Moderate | Yes — key differentiator |
| Material library | Extensive | Extensive | Minimal | Curated for induction heating |
| Speed | Slow (FEM) | Slow (FEM) | Moderate | Fast (analytical) |
| Cost | $$$$ | $$$$ | Free | Free/open-source |

## Sources

- COMSOL Multiphysics feature set: https://www.comsol.com/
- ANSYS Maxwell capabilities: https://www.ansys.com/products/electronics/ansys-maxwell
- FEMM (Finite Element Method Magnetics): https://www.femm.info/
- "Handbook of Induction Heating" (Rudnev, CRC Press 2003)
- User expectations inferred from scientific simulation tool conventions

---
*Feature research for: Induction Heating Simulator*
*Researched: 2026-07-30*
