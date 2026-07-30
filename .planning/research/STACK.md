# Stack Research

**Domain:** Scientific Python desktop application — induction heating simulator
**Researched:** 2026-07-30
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Core language | Dominant in scientific computing; NumPy/SciPy ecosystem |
| PySide6 | 6.6+ | GUI framework | Qt6 bindings, LGPL license (more permissive than PyQt), same API as PyQt6 |
| NumPy | 2.x | Array operations & numerical computing | Foundation for all scientific Python; vectorized Bessel functions, complex arithmetic |
| SciPy | 1.13+ | Special functions, integration, optimization | Bessel functions (scipy.special), numerical integration (scipy.integrate), root finding |
| Matplotlib | 3.8+ | 2D plotting and visualization | Publication-quality plots, contour plots, cross-section visualization |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyQtGraph | 0.13+ | Real-time 2D visualization | For interactive cross-section views with pan/zoom; faster than matplotlib for live updates |
| Pint | 0.23+ | Physical unit management | Critical for scientific apps — prevents unit errors in electromagnetic calculations |
| h5py | 3.10+ | HDF5 file I/O | For saving/loading simulation results, material databases |
| pydantic | 2.x | Data validation & settings management | For material property schemas, simulation parameter validation |
| pytest | 8.x | Unit testing | Essential for validating calculation correctness |
| Numba | 0.59+ | JIT compilation | For performance-critical calculation loops (iterative temperature stepping) |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| poetry or uv | Dependency management | uv is faster; poetry is more mature. uv recommended for new projects |
| mypy | Static type checking | Scientific code benefits from type safety, especially for complex number handling |
| ruff | Linting & formatting | Fast, modern linter |
| Sphinx | Documentation generation | For API docs and calculation reference |

## Installation

```bash
# Core
pip install numpy scipy matplotlib PySide6 pint pydantic

# Supporting
pip install pyqtgraph h5py numba pytest mypy ruff

# Dev dependencies
pip install sphinx sphinx-rtd-theme pytest-cov
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| PySide6 | PyQt6 | If you need commercial PyQt support or existing PyQt codebase |
| Matplotlib + PyQtGraph | Plotly | Only if web-based visualization is needed later |
| Pint | astropy.units | If you also need astronomical units (overkill for this project) |
| Numba | Cython | If you need C-level control and are willing to compile |
| HDF5 (h5py) | SQLite | If you need relational queries on material data (HDF5 is better for array data) |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Pure Python loops for calculations | Too slow for iterative temperature stepping | NumPy vectorization + Numba JIT |
| Tkinter | Too limited for scientific visualization | PySide6 |
| sympy for runtime calculations | Symbolic math is too slow; use for derivation only | Pre-derived formulas with NumPy/SciPy |
| FEniCS / FEM libraries | User wants analytical methods, not FEM | Custom analytical solvers |
| pandas for material data | Overkill; material properties are structured arrays, not tabular | NumPy structured arrays + pydantic models |

## Stack Patterns by Variant

**If real-time interactive visualization is needed:**
- Use PyQtGraph for the 2D cross-section view
- Because it handles pan/zoom/redraw at 60fps, matplotlib is too slow for interactive use

**If publication-quality output is needed:**
- Use Matplotlib for export/rendering
- Because it produces vector-quality SVG/PDF output

**If calculation performance is critical:**
- Use Numba @njit for temperature-stepping loops
- Because iterative thermal calculations with temperature-dependent properties need JIT speed

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| PySide6 6.6+ | Python 3.9–3.12 | Qt6 LTS recommended for stability |
| NumPy 2.x | SciPy 1.13+ | NumPy 2.0 has API changes; SciPy 1.13+ is compatible |
| Pint 0.23+ | NumPy 2.x | Pint 0.23+ supports NumPy 2.x |
| PyQtGraph 0.13+ | PySide6 6.x | PyQtGraph supports both PyQt and PySide backends |

## Sources

- NumPy docs: https://numpy.org/doc/ — verified array operations and Bessel function support
- SciPy docs: https://scipy.org/doc/ — verified scipy.special for Bessel functions (j0, j1, etc.)
- PySide6 docs: https://doc.qt.io/qtforpython/ — verified LGPL licensing
- Pint docs: https://pint.readthedocs.io/ — verified unit handling for SI electromagnetic units
- "Handbook of Induction Heating" (Rudnev, CRC Press 2003) — referenced for calculation approach
- "Elements of Induction Heating" (Zinn & Semiatin, ASM International 1988) — referenced for analytical formulas

---
*Stack research for: Induction Heating Simulator (Python/PySide6)*
*Researched: 2026-07-30*
