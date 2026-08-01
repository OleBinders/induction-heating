# Phase 6 Research: Results Display & Export

**Phase:** 06 — Results Display & Export
**Researched:** 2026-07-30
**Confidence:** HIGH

## Numerical Results Panel

### Key Metrics to Display

| Metric | Unit | Description |
|--------|------|-------------|
| Skin depth | mm | Penetration depth of eddy currents |
| B-field at surface | mT | Magnetic flux density at workpiece surface |
| Total absorbed power | W | Total Joule heating in workpiece |
| Peak power density | W/m³ | Maximum power density (at surface) |
| Coupling factor | — | Geometric coupling efficiency |
| Efficiency | % | Ratio of absorbed power to input power |

### Display Format

Use QFormLayout with read-only QLineEdit or QLabel for each metric.
Format numbers with appropriate precision and units.

**Confidence:** HIGH — straightforward implementation.

## Property vs Temperature Plots

### Matplotlib Line Plots

```python
fig, ax = plt.subplots()
temps = np.linspace(20, 1000, 100)
rho = [db.get_property_at_temperature(name, "resistivity", t) for t in temps]
mu = [db.get_permeability(name, t) for t in temps]

ax.plot(temps, rho, label='Resistivity')
ax2 = ax.twinx()
ax2.plot(temps, mu, label='Permeability', color='red')
```

**Confidence:** HIGH — standard matplotlib usage.

## Radial Depth Profiles

### Plot B-field, Current Density, Power Density vs Radius

```python
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
axes[0].plot(r, B_r)
axes[1].plot(r, J_r)
axes[2].plot(r, P_r)
```

**Confidence:** HIGH — standard matplotlib subplots.

## Export Functionality

### PNG/SVG Export

Matplotlib's built-in savefig:
```python
fig.savefig("plot.png", dpi=150)
fig.savefig("plot.svg")
```

### CSV Export

```python
import csv
with open("results.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Radius (m)", "B (T)", "J (A/m²)", "P (W/m³)"])
    for r, b, j, p in zip(r_vals, b_vals, j_vals, p_vals):
        writer.writerow([r, b, j, p])
```

### JSON Export (Full Simulation State)

```python
import json
state = {
    "coil": {...},
    "workpiece": {...},
    "frequency": ...,
    "current": ...,
    "material": ...,
    "results": {...}
}
with open("simulation.json", "w") as f:
    json.dump(state, f, indent=2)
```

**Confidence:** HIGH — standard Python file I/O.

## Save/Load Simulation State

### JSON Format

```json
{
  "version": "0.1.0",
  "coil": {
    "inner_radius": 0.025,
    "outer_radius": 0.030,
    "length": 0.10,
    "turns": 20,
    "wire_diameter": 0.005
  },
  "workpiece": {
    "radius": 0.020,
    "length": 0.08,
    "material_name": "Low Carbon Steel (AISI 1018)"
  },
  "operating": {
    "frequency": 10000,
    "current": 100,
    "temperature": 20
  }
}
```

### Load Process

1. Read JSON file
2. Validate schema
3. Populate all GUI panels
4. Update validation state

**Confidence:** HIGH — standard JSON serialization.

## Key References

1. **Matplotlib savefig:** https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html
2. **PySide6 QFileDialog:** https://doc.qt.io/qtforpython/PySide6/QtWidgets/QFileDialog.html
3. **Python json module:** https://docs.python.org/3/library/json.html
4. **Python csv module:** https://docs.python.org/3/library/csv.html

---
*Research for Phase 6: Results Display & Export*
*Researched: 2026-07-30*
