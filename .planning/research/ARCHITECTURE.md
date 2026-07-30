# Architecture Research

**Domain:** Scientific desktop application — induction heating simulator
**Researched:** 2026-07-30
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         GUI Layer (PySide6)                      │
├──────────────┬──────────────┬──────────────┬─────────────────────┤
│  Main Window │  Param Panel │  Material    │  Results Panel      │
│  & Menu Bar  │  (Inputs)    │  Selector    │  (Plots, Data)      │
├──────────────┴──────────────┴──────────────┴─────────────────────┤
│                    Visualization Layer                           │
├──────────────────────────┬──────────────────────────────────────┤
│  2D Cross-Section View   │  Chart/Plot Views                    │
│  (PyQtGraph/Matplotlib)  │  (Temperature, Field, Current)       │
├──────────────────────────┴──────────────────────────────────────┤
│                    Application Service Layer                     │
├──────────────────┬──────────────────┬───────────────────────────┤
│  Simulation      │  Geometry        │  Material Service         │
│  Orchestrator    │  Manager         │  (Library, Properties)    │
├──────────────────┴──────────────────┴───────────────────────────┤
│                    Calculation Core (Pure Python/NumPy)           │
├──────────────┬──────────────┬──────────────┬─────────────────────┤
│  Magnetic    │  Eddy Current│  Thermal     │  Skin Depth         │
│  Field Calc  │  Calc        │  Calc        │  & Proximity        │
├──────────────┴──────────────┴──────────────┴─────────────────────┤
│                    Data Layer                                     │
├──────────────────┬──────────────────┬─────────────────────────────┤
│  Material DB     │  Simulation      │  Geometry Definitions       │
│  (JSON/HDF5)     │  State (HDF5)    │  (Python dataclasses)       │
└──────────────────┴──────────────────┴─────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| GUI Layer | User interaction, layout, menus, dialogs | PySide6 QMainWindow, QDockWidget, QFormLayout |
| Visualization | 2D rendering of geometry, field contours, temperature maps | PyQtGraph for interactive view, Matplotlib for export |
| Simulation Orchestrator | Coordinates calculation pipeline, manages time stepping | Python class with state machine for run/pause/step |
| Geometry Manager | Defines coil and workpiece shapes, validates dimensions | Dataclasses with validation, factory methods for standard shapes |
| Material Service | Loads, queries, and interpolates material properties | Repository pattern over JSON/HDF5, scipy.interpolate for temp-dependent data |
| Calculation Core | Pure mathematical functions — no UI, no I/O | NumPy/SciPy functions, Numba-jitted for performance |
| Material DB | Persistent storage of material property data | JSON for simple data, HDF5 for large datasets |
| Simulation State | Save/load complete simulation configurations | HDF5 or JSON with pydantic serialization |

## Recommended Project Structure

```
induction_heating/
├── src/
│   ├── induction_heating/
│   │   ├── __init__.py
│   │   ├── __main__.py              # Entry point
│   │   ├── core/                    # Calculation engine (pure math)
│   │   │   ├── __init__.py
│   │   │   ├── electromagnetic.py   # B-field, eddy currents, skin depth
│   │   │   ├── thermal.py           # Heat generation, temperature evolution
│   │   │   ├── materials.py         # Material property models
│   │   │   ├── geometry.py          # Coil and workpiece geometry definitions
│   │   │   └── coil_types.py        # Solenoid, pancake, helical, internal formulations
│   │   ├── materials/               # Material database
│   │   │   ├── __init__.py
│   │   │   ├── database.py          # Material repository
│   │   │   ├── schemas.py           # Pydantic models for material data
│   │   │   └── data/                # JSON/HDF5 material files
│   │   │       ├── steels.json
│   │   │       ├── copper.json
│   │   │       └── ...
│   │   ├── gui/                     # PySide6 GUI
│   │   │   ├── __init__.py
│   │   │   ├── main_window.py       # Main application window
│   │   │   ├── panels/
│   │   │   │   ├── param_panel.py   # Parameter input
│   │   │   │   ├── material_panel.py # Material selection
│   │   │   │   └── results_panel.py # Results display
│   │   │   ├── views/
│   │   │   │   ├── cross_section.py # 2D cross-section view
│   │   │   │   └── charts.py        # Plot views
│   │   │   └── widgets/             # Reusable Qt widgets
│   │   ├── visualization/           # Rendering logic (separate from GUI)
│   │   │   ├── __init__.py
│   │   │   ├── renderer.py          # Field contour rendering
│   │   │   └── exporters.py         # Plot export (PNG, SVG, PDF)
│   │   ├── simulation/              # Simulation orchestration
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            # Simulation runner
│   │   │   └── state.py             # Simulation state management
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── units.py             # Pint unit definitions
│   │       └── constants.py         # Physical constants
├── tests/
│   ├── test_electromagnetic.py
│   ├── test_thermal.py
│   ├── test_materials.py
│   └── test_geometry.py
├── docs/
├── pyproject.toml
└── README.md
```

### Structure Rationale

- **core/**: Pure calculation functions — no dependencies on GUI, I/O, or state. This enables unit testing and reuse.
- **materials/**: Separate from core because material data is domain knowledge, not calculation logic.
- **gui/**: All PySide6 code isolated here. Panels, views, and widgets are Qt-specific.
- **visualization/**: Rendering logic separated from GUI widgets — the renderer can be used with different backends.
- **simulation/**: Orchestrates the pipeline — connects core calculations to GUI without coupling them.

## Architectural Patterns

### Pattern 1: Layered Architecture

**What:** Strict separation between GUI, service, calculation, and data layers
**When to use:** Always for scientific applications — keeps math testable
**Trade-offs:** More boilerplate but prevents GUI/math coupling

**Example:**
```python
# core/electromagnetic.py — pure function, no imports from gui/
def calculate_skin_depth(resistivity: float, permeability: float, frequency: float) -> float:
    """Calculate skin depth δ = sqrt(2ρ / ωμ)"""
    omega = 2 * np.pi * frequency
    return np.sqrt(2 * resistivity / (omega * permeability))
```

### Pattern 2: Repository Pattern for Materials

**What:** MaterialService abstracts data source (JSON, HDF5, database)
**When to use:** When material data may come from multiple sources
**Trade-offs:** Adds indirection but enables easy data source swaps

### Pattern 3: Strategy Pattern for Coil Types

**What:** Each coil type (solenoid, pancake, helical, internal) implements a common interface
**When to use:** When different coil geometries require different analytical formulations
**Trade-offs:** Clean extension point for new coil types

**Example:**
```python
class CoilGeometry(ABC):
    @abstractmethod
    def magnetic_field(self, point: np.ndarray, current: float, turns: int) -> np.ndarray: ...

class SolenoidCoil(CoilGeometry): ...
class PancakeCoil(CoilGeometry): ...
```

## Data Flow

### Calculation Flow

```
User sets parameters (frequency, current, geometry)
    ↓
Geometry Manager validates and creates geometry model
    ↓
Material Service loads temperature-dependent properties
    ↓
Calculation Core computes:
    1. Skin depth (from material properties + frequency)
    2. Magnetic field distribution (from coil geometry + current)
    3. Eddy current density (from B-field + material properties)
    4. Power density (from eddy currents + resistivity)
    5. Temperature rise (from power density + thermal properties)
    ↓
If time-stepped: loop back with updated temperature-dependent properties
    ↓
Visualization renders 2D cross-section with field/temperature contours
    ↓
Results Panel displays numerical values and plots
```

### Key Data Flows

1. **Material property lookup:** GUI selects material → MaterialService loads data → interpolates at current temperature → returns to calculation core
2. **Temperature evolution:** Power density calculated → thermal model updates temperature → material properties re-interpolated → next iteration
3. **Curie transition:** Temperature approaches Tc → permeability model transitions from ferromagnetic to paramagnetic → skin depth increases → heating pattern changes

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single user, desktop | Current architecture is sufficient |
| Batch simulations | Add job queue, parallelize with multiprocessing |
| Web-based | Separate calculation core into REST API, keep GUI as web frontend |

### Scaling Priorities

1. **First bottleneck:** Calculation speed for time-stepped simulations — solve with Numba JIT
2. **Second bottleneck:** Material database size — solve with HDF5 instead of JSON

## Anti-Patterns

### Anti-Pattern 1: Mixing GUI and Calculation Code

**What people do:** Put calculation logic in Qt widget classes
**Why it's wrong:** Makes calculations untestable, ties math to specific UI framework
**Do this instead:** Keep core/ as pure Python with no Qt imports

### Anti-Pattern 2: Hardcoding Material Properties

**What people do:** Embed material constants directly in calculation functions
**Why it's wrong:** Makes it impossible to add new materials or update properties
**Do this instead:** Use the MaterialService repository pattern with external data files

### Anti-Pattern 3: Using Global State for Simulation Parameters

**What people do:** Store frequency, current, etc. as module-level globals
**Why it's wrong:** Makes it impossible to run multiple simulations or compare configurations
**Do this instead:** Use SimulationState dataclass passed explicitly to calculation functions

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Material property databases (NIST, MatWeb) | Import scripts to populate local DB | One-time import, not runtime |
| CAD file formats (DXF, STEP) | Optional geometry import via ezdxf, pythonocc | Defer to v2 |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| GUI ↔ Simulation Engine | Qt signals/slots for events, dataclasses for parameters | Never pass Qt objects to core |
| Core ↔ Material Service | Function calls with primitive types or numpy arrays | MaterialService can depend on core types |
| Visualization ↔ Core | Core returns numpy arrays; visualization renders them | No coupling in either direction |

## Sources

- Scientific Python application architecture patterns from SciPy ecosystem
- "Elements of Induction Heating" (Zinn & Semiatin) for calculation pipeline understanding
- Qt application architecture best practices from Riverbank Computing docs

---
*Architecture research for: Induction Heating Simulator*
*Researched: 2026-07-30*
