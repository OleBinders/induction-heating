# Phase 5 Research: 2D Cross-Section Visualization

**Phase:** 05 — 2D Cross-Section Visualization
**Researched:** 2026-07-30
**Confidence:** HIGH

## Visualization Approach: PyQtGraph vs Matplotlib

### PyQtGraph
**Pros:**
- Fast rendering (OpenGL-backed, 60fps)
- Built-in pan/zoom
- Interactive crosshairs, region selection
- Good for real-time updates
- Native Qt integration

**Cons:**
- Less publication-quality output
- Smaller ecosystem than matplotlib
- Contour plotting requires additional work (not built-in)

### Matplotlib
**Pros:**
- Excellent contour plotting (contourf, pcolormesh)
- Publication-quality output
- Rich colormap support
- Well-documented

**Cons:**
- Slower rendering (not suitable for real-time)
- Pan/zoom requires embedding in Qt canvas
- Heavier weight

### Recommendation: **Matplotlib with Qt embedding**

For Phase 5, we need contour plots of field and power density distributions. Matplotlib's `contourf` and `pcolormesh` are ideal for this. Pan/zoom is available via `NavigationToolbar2QT`.

For Phase 6 (export), matplotlib's SVG/PNG export is superior.

**Confidence:** HIGH — contour plotting is the primary requirement, and matplotlib excels at this.

## Cross-Section Geometry

### Axisymmetric (Cylindrical) View

For a solenoid coil + cylindrical workpiece, the 2D cross-section shows:
- **Z-axis (vertical):** Axial direction along coil length
- **R-axis (horizontal):** Radial direction from center axis

The view shows:
- Coil cross-section (rectangular ring at given Z positions)
- Workpiece cross-section (rectangle inside coil)
- Field/power density contours overlaid on the geometry

### Coordinate System

```
    Z (axial)
    ↑
    |    ┌─────────────┐  ← Coil outer radius
    |    │  ┌───────┐  │  ← Coil inner radius
    |    │  │       │  │
    |    │  │ Work- │  │  ← Workpiece
    |    │  │ piece │  │
    |    │  │       │  │
    |    │  └───────┘  │
    |    └─────────────┘
    +────────────────────→ R (radial)
   0
```

**Confidence:** HIGH — standard axisymmetric representation.

## Contour Plot Implementation

### Using matplotlib.contourf

```python
import matplotlib.pyplot as plt
import numpy as np

# Create grid
R = np.linspace(0, coil_outer_radius, 100)
Z = np.linspace(-coil_length/2, coil_length/2, 100)
RR, ZZ = np.meshgrid(R, Z)

# Calculate field values on grid
B_values = calculate_b_field_on_grid(RR, ZZ, coil, current)

# Contour plot
fig, ax = plt.subplots()
cf = ax.contourf(RR, ZZ, B_values, levels=50, cmap='viridis')
fig.colorbar(cf, ax=ax, label='B (T)')
ax.set_xlabel('Radius (m)')
ax.set_ylabel('Axial Position (m)')
```

### Using matplotlib.pcolormesh (faster for large grids)

```python
cf = ax.pcolormesh(RR, ZZ, B_values, cmap='viridis', shading='auto')
```

**Confidence:** HIGH — standard matplotlib usage.

## Embedding Matplotlib in PySide6

### Pattern

```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

# In MainWindow:
self.canvas = MplCanvas()
self.toolbar = NavigationToolbar(self.canvas, self)
layout.addWidget(self.toolbar)
layout.addWidget(self.canvas)
```

**Note:** For PySide6, use `backend_qt5agg` (Qt5 backend works with Qt6/PySide6).

**Confidence:** HIGH — standard pattern, well-documented.

## Color Map Selection

For scientific visualization:
- **viridis:** Perceptually uniform, colorblind-friendly (default for field strength)
- **plasma:** Good for power density (high contrast)
- **coolwarm:** Diverging colormap (useful for showing positive/negative values)

**Recommendation:** viridis for B-field, plasma for power density.

**Confidence:** HIGH — matplotlib best practices.

## Pan/Zoom Implementation

Matplotlib's `NavigationToolbar2QT` provides:
- Pan tool
- Zoom tool
- Home (reset view)
- Back/Forward (view history)
- Save figure (PNG, PDF, SVG)

This satisfies REQ-VIZ-004 (pan and zoom) and REQ-VIZ-005 (color scale legend via colorbar).

**Confidence:** HIGH — built-in functionality.

## Geometry Rendering

### Drawing Coil and Workpiece Outlines

```python
# Coil outline (rectangular ring)
from matplotlib.patches import Rectangle

# Coil cross-section
coil_rect_outer = Rectangle(
    (coil_inner_radius, -coil_length/2),
    coil_outer_radius - coil_inner_radius,
    coil_length,
    fill=False, edgecolor='black', linewidth=2
)
ax.add_patch(coil_rect_outer)

# Workpiece
wp_rect = Rectangle(
    (0, -workpiece_length/2),
    workpiece_radius,
    workpiece_length,
    fill=True, facecolor='gray', alpha=0.3, edgecolor='black'
)
ax.add_patch(wp_rect)
```

**Confidence:** HIGH — standard matplotlib patches.

## Performance Considerations

- Grid size: 100x100 points is sufficient for smooth contours
- pcolormesh is faster than contourf for large grids
- For real-time updates, consider downsampling
- Phase 5 doesn't need real-time; calculation on Run button is sufficient

**Confidence:** MEDIUM-HIGH — depends on grid size and calculation complexity.

## Key References

1. **Matplotlib contour docs:** https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.contourf.html
2. **Matplotlib Qt embedding:** https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html
3. **PySide6 + Matplotlib:** https://matplotlib.org/stable/users/explain/backends.html
4. **Colormap selection:** https://matplotlib.org/stable/users/explain/colors/colormaps.html

---
*Research for Phase 5: 2D Cross-Section Visualization*
*Researched: 2026-07-30*
