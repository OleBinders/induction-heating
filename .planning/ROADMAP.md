# Roadmap: Induction Heating Simulator

## Overview

Build a scientific Python desktop application for calculating and visualizing induction heating effects. Start with project foundation and material library, then build the electromagnetic calculation engine with temperature-dependent properties and Curie point modeling, followed by the GUI with 2D cross-section visualization and results display. Each phase is validated against published literature reference values.

## Phases

- [x] **Phase 1: Project Foundation** — Project structure, dependencies, unit system, material library with temperature-dependent properties
- [x] **Phase 2: Electromagnetic Calculation Engine** — Skin depth, magnetic field distribution, eddy current density, power density for solenoid coil + cylindrical workpiece
- [ ] **Phase 3: Temperature-Dependent Properties & Curie Transition** — Temperature interpolation, smooth Curie point permeability transition, property evolution
- [ ] **Phase 4: GUI Framework & Parameter Input** — PySide6 main window, parameter panels, material selector, input validation
- [ ] **Phase 5: 2D Cross-Section Visualization** — Interactive cross-section view with field/power density contour overlays, pan/zoom
- [ ] **Phase 6: Results Display & Export** — Numerical results panel, property/field plots, plot export, save/load simulations
- [ ] **Phase 7: Validation & Testing** — Cross-reference all calculations against literature, unit tests with reference values, end-to-end verification

## Phase Details

### Phase 1: Project Foundation
**Goal**: Working project with material library and unit system
**Depends on**: Nothing (first phase)
**Requirements**: REQ-MAT-001, REQ-MAT-003, REQ-MAT-005, REQ-CALC-006
**Success Criteria** (what must be TRUE):
  1. Project runs with `python -m induction_heating` showing a basic window
  2. Material library loads steel, copper, aluminum, brass with temperature-dependent resistivity
  3. All physical quantities use Pint units internally
  4. Material properties can be queried at arbitrary temperatures via interpolation
**Plans**: 3 plans

Plans:
- [ ] 01-01: Project scaffolding — pyproject.toml, directory structure, entry point, basic PySide6 window
- [ ] 01-02: Unit system — Pint integration, SI unit definitions, physical constants
- [ ] 01-03: Material library — JSON data files, pydantic schemas, repository pattern, temperature interpolation

### Phase 2: Electromagnetic Calculation Engine
**Goal**: Core analytical calculations for solenoid coil + cylindrical workpiece
**Depends on**: Phase 1
**Requirements**: REQ-CALC-001, REQ-CALC-002, REQ-CALC-003, REQ-CALC-004, REQ-CALC-005, REQ-GEO-001, REQ-GEO-002, REQ-GEO-003, REQ-GEO-004
**Success Criteria** (what must be TRUE):
  1. Skin depth calculation matches reference values (e.g., copper at 1 MHz ≈ 66 μm)
  2. Magnetic field distribution computed for solenoid coil geometry
  3. Eddy current density and power density calculated for cylindrical workpiece
  4. Geometry validation rejects invalid dimensions
**Plans**: 3 plans

Plans:
- [ ] 02-01: Geometry system — Solenoid coil and cylindrical workpiece dataclasses with validation
- [ ] 02-02: Skin depth and magnetic field — Analytical formulas for solenoid B-field, skin depth with temp-dependent inputs
- [ ] 02-03: Eddy currents and power density — J(r) distribution, P = J²ρ power density, frequency range 10-50 kHz

### Phase 3: Temperature-Dependent Properties & Curie Transition
**Goal**: Accurate modeling of property changes through Curie point
**Depends on**: Phase 2
**Requirements**: REQ-MAT-002, REQ-MAT-004, REQ-MAT-005, REQ-CALC-007, REQ-CALC-008
**Success Criteria** (what must be TRUE):
  1. Permeability transitions smoothly from μr >> 1 to μr ≈ 1 around Curie temperature
  2. No numerical instability during Curie transition
  3. Resistivity interpolation matches published data for steel from 20°C to 800°C+
  4. Calculation results validated against at least 2 literature sources
**Plans**: 2 plans

Plans:
- [ ] 03-01: Curie point model — Smooth permeability transition function (sigmoid/polynomial), Hopkinson effect
- [ ] 03-02: Property evolution engine — Temperature-stepped property updates, validation against literature reference values

### Phase 4: GUI Framework & Parameter Input
**Goal**: Functional GUI with parameter input and material selection
**Depends on**: Phase 1, Phase 2
**Requirements**: REQ-GUI-001, REQ-GUI-002, REQ-GUI-003, REQ-GUI-004, REQ-GUI-005
**Success Criteria** (what must be TRUE):
  1. Main window with docked panels for parameters, materials, and results
  2. User can enter coil parameters (radius, length, turns, current) with validation
  3. User can enter workpiece parameters (radius, length) with validation
  4. User can select frequency (10-50 kHz) and current amplitude
  5. Material selector shows available materials with property preview
  6. Invalid inputs show clear error messages with valid ranges
**Plans**: 2 plans

Plans:
- [ ] 04-01: Main window layout — QMainWindow, docked panels, menu bar, toolbar
- [ ] 04-02: Parameter panels — Form inputs for coil, workpiece, operating params, material selector, validation

### Phase 5: 2D Cross-Section Visualization
**Goal**: Interactive cross-section view with field and power density overlays
**Depends on**: Phase 2, Phase 4
**Requirements**: REQ-VIZ-001, REQ-VIZ-002, REQ-VIZ-003, REQ-VIZ-004, REQ-VIZ-005
**Success Criteria** (what must be TRUE):
  1. 2D cross-section shows coil and workpiece geometry with correct proportions
  2. Magnetic field strength rendered as color contour overlay
  3. Power density rendered as color contour overlay
  4. User can pan and zoom on the cross-section view
  5. Color scale legend shows field/power density values
**Plans**: 2 plans

Plans:
- [ ] 05-01: Cross-section renderer — Geometry rendering, coordinate system, pan/zoom (PyQtGraph)
- [ ] 05-02: Contour overlays — Field strength and power density color maps, legend, toggle between views

### Phase 6: Results Display & Export
**Goal**: Numerical results, plots, export, and save/load
**Depends on**: Phase 4, Phase 5
**Requirements**: REQ-RES-001, REQ-RES-002, REQ-RES-003, REQ-RES-004, REQ-IO-001, REQ-IO-002
**Success Criteria** (what must be TRUE):
  1. Results panel shows skin depth, total power, efficiency numerically
  2. Plot of resistivity and permeability vs. temperature
  3. Plot of field/current/power vs. radial depth
  4. Plots exportable as PNG and SVG
  5. Simulation can be saved to file and reloaded with all parameters restored
**Plans**: 2 plans

Plans:
- [ ] 06-01: Results panel and plots — Numerical display, Matplotlib property curves, radial depth profiles
- [ ] 06-02: Export and persistence — PNG/SVG export, save/load simulation state (JSON/HDF5)

### Phase 7: Validation & Testing
**Goal**: All calculations validated against literature, comprehensive test suite
**Depends on**: Phase 2, Phase 3, Phase 5, Phase 6
**Requirements**: REQ-CALC-008 (full coverage)
**Success Criteria** (what must be TRUE):
  1. Every calculation function has unit tests with known reference values
  2. Skin depth validated against standard tables for multiple materials and frequencies
  3. Magnetic field validated against analytical reference for infinite solenoid
  4. Power density results match published induction heating data within acceptable tolerance
  5. Curie transition produces smooth, stable results verified against literature curves
  6. All tests pass with pytest
**Plans**: 2 plans

Plans:
- [ ] 07-01: Calculation unit tests — Reference value tests for skin depth, B-field, eddy currents, power density, Curie transition
- [ ] 07-02: Integration and end-to-end tests — Full simulation runs, GUI responsiveness, save/load round-trip

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Foundation | 3/3 | Complete | 2026-07-30 |
| 2. Electromagnetic Engine | 3/3 | Complete | 2026-07-30 |
| 3. Curie Transition | 0/2 | Not started | - |
| 4. GUI Framework | 0/2 | Not started | - |
| 5. Cross-Section Visualization | 0/2 | Not started | - |
| 6. Results & Export | 0/2 | Not started | - |
| 7. Validation & Testing | 0/2 | Not started | - |
