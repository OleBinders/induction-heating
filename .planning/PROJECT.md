# Induction Heating Simulator

## What This Is

A scientific Python application for calculating and visualizing the effects of resistance heating of metallic objects using induction coils and eddy currents at high frequency (10–50 kHz). It provides analytical calculations for magnetic field strength, eddy current density, skin depth, power absorption, and temperature evolution — including temperature-dependent material properties and Curie point transitions. The application features a PyQt/PySide-based GUI with 2D cross-sectional visualization, a material library, and support for multiple coil geometries.

## Core Value

Accurately predict induction heating behavior for surface hardening and brazing applications using analytical methods with temperature-dependent material properties.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] REQ-1: Material library with temperature-dependent properties (resistivity, permeability, specific heat, thermal conductivity) including Curie point transitions
- [ ] REQ-2: Analytical calculation engine for magnetic field strength, eddy current density, skin depth, and power absorption
- [ ] REQ-3: Support for axisymmetric (cylindrical) and planar/rectangular 2D cross-sectional geometries
- [ ] REQ-4: Support for solenoid, pancake, helical, internal, and custom coil shapes
- [ ] REQ-5: Frequency range 10–50 kHz
- [ ] REQ-6: Temperature-dependent calculations accounting for material property changes and Curie point effects
- [ ] REQ-7: PyQt/PySide-based GUI with 2D cross-sectional visualization of coil and workpiece
- [ ] REQ-8: Ability to design or import coil and workpiece geometries
- [ ] REQ-9: Surface hardening and brazing application focus
- [ ] REQ-10: Scientific-grade calculations validated against electromagnetic theory

### Out of Scope

- Full 3D FEM simulation — analytical/semi-analytical methods only
- Frequency range beyond 50 kHz (for now)
- Melting applications — surface hardening and brazing only
- Real-time thermal simulation with convection/radiation heat loss (initial version)

## Context

This is a greenfield scientific computing project. The user has no existing benchmark data for validation, so calculations will need to be cross-referenced against published electromagnetic theory and literature. The key technical challenge is modeling temperature-dependent permeability through the Curie transition, which significantly affects heating behavior in ferromagnetic materials.

## Constraints

- **[Tech Stack]**: Python with PyQt/PySide for GUI — user preference
- **[Math Approach]**: Analytical/semi-analytical methods only — no FEM
- **[Frequency]**: 10–50 kHz range — user-defined scope
- **[Applications]**: Surface hardening and brazing only

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Analytical over FEM | User wants closed-form/semi-analytical solutions for speed and transparency | — Pending |
| PyQt/PySide for GUI | User preference for desktop application | — Pending |
| Temperature-dependent properties | Essential for accurate modeling through Curie transition | — Pending |
| 2D cross-section visualization | Balance between usability and computational tractability | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-30 after initialization*
