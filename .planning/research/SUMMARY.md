# Project Research Summary

**Domain:** Scientific Python desktop application — induction heating simulator
**Synthesized:** 2026-07-30

## Key Findings

### Stack

**Python + PySide6 + NumPy/SciPy + Pint** is the standard stack for this type of scientific desktop application. Key decisions:

- **PySide6 over PyQt6**: LGPL license is more permissive, same API
- **Pint for units**: Critical for preventing unit errors in electromagnetic calculations
- **NumPy/SciPy for math**: Bessel functions (scipy.special), numerical integration, vectorized operations
- **PyQtGraph for interactive views**: 60fps pan/zoom for cross-section visualization
- **Numba for performance**: JIT compilation for temperature-stepping loops
- **HDF5 (h5py) for data**: Better than JSON for array-valued simulation results

**Avoid**: Pure Python loops for calculations, Tkinter, sympy for runtime math, FEM libraries.

### Table Stakes

The non-negotiable features users expect:
1. Material library with temperature-dependent properties
2. Parameter input (frequency, current, turns, dimensions)
3. 2D cross-section visualization of coil + workpiece
4. Calculation results (temperature, field strength, power density)
5. Save/load simulations
6. SI unit system

### Key Differentiators

What sets this apart from COMSOL/ANSYS:
1. **Temperature-dependent property evolution** through Curie transition (most tools use constant properties)
2. **Fast analytical calculations** vs. slow FEM
3. **Quick setup** — no meshing, no convergence tuning
4. **Curie point transition modeling** as a first-class feature

### Watch Out For

**Critical pitfalls identified:**

1. **Curie transition modeling** — The permeability drop at Tc must be smooth (not a step function) or calculations will be unstable. This is the hardest technical challenge.

2. **Unit consistency** — Electromagnetic formulas are extremely sensitive to units. The skin depth formula has multiple variants with different unit conventions. Use Pint throughout.

3. **No validation data** — The user has no benchmark data. Every formula must be cross-referenced against at least 2 literature sources, and unit tests must be created with known reference values.

4. **Analytical model validity** — Simplified formulas (infinite solenoid, etc.) have limited applicability ranges. Must document and enforce validity conditions.

5. **Temperature-dependent properties** — Resistivity of steel increases ~6x from 20°C to 800°C. Permeability drops sharply at Curie point. Using constant properties gives wrong results.

6. **Proximity effect** — Often ignored but significant at 10-50 kHz for closely spaced coil turns.

## Implications for Roadmap

### Phase Ordering

1. **Foundation first**: Material library with temperature-dependent properties + unit system. Everything else depends on this.
2. **Core calculations**: Electromagnetic engine (skin depth, B-field, eddy currents, power) with validation against literature. This is the highest-risk phase.
3. **GUI and visualization**: 2D cross-section view, parameter panels, results display.
4. **Advanced features**: Additional coil types, planar geometry, time-stepped simulation.

### Risk Mitigation

- **Research phase before each calculation phase**: Verify formulas against multiple sources
- **Unit tests with reference values**: Every calculation function needs known-input/known-output tests
- **Smooth Curie transition**: Use empirically validated transition curves, not step functions
- **Pint from day one**: No "we'll add units later" — unit errors are the most dangerous bug type

### Architecture Decisions

- **Strict layering**: GUI, service, calculation, data — no cross-layer imports
- **Pure math in core/**: No Qt, no I/O, no state — enables unit testing
- **Strategy pattern for coil types**: Clean extension point for solenoid, pancake, helical, internal
- **Repository pattern for materials**: Abstract data source, enable easy additions

## Sources

- STACK.md — Technology stack research
- FEATURES.md — Feature landscape analysis
- ARCHITECTURE.md — System architecture patterns
- PITFALLS.md — Domain-specific pitfalls and prevention strategies
- Wikipedia: Induction heating, Skin effect, Eddy current, Curie temperature
- "Handbook of Induction Heating" (Rudnev, CRC Press 2003)
- "Elements of Induction Heating" (Zinn & Semiatin, ASM International 1988)

---
*Research summary for: Induction Heating Simulator*
*Synthesized: 2026-07-30*
