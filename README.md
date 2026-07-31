# Induction Heating Simulator

Scientific desktop application for calculating and visualizing the effects of resistance heating of metallic objects using induction coils and eddy currents at high frequency (10–50 kHz).

## Features

- Analytical calculations for magnetic field strength, eddy current density, skin depth, and power absorption
- Temperature-dependent material properties including Curie point transitions
- 2D cross-sectional visualization of coil and workpiece
- Material library with temperature-dependent resistivity and permeability
- Support for surface hardening and brazing applications

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```bash
python -m induction_heating
```

## Development

```bash
# Run tests
pytest tests/ -v

# Run the application
python -m induction_heating
```

## Tech Stack

- **Python 3.11+** — Core language
- **PySide6** — GUI framework (Qt6)
- **NumPy/SciPy** — Scientific computing
- **Pint** — Physical unit management
- **Pydantic** — Data validation
