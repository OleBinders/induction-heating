"""Export and persistence functions for simulation data."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from induction_heating.core.geometry import CylindricalWorkpiece, InductionSetup, SolenoidCoil


def export_csv(
    filepath: str | Path,
    r: np.ndarray,
    b_field: np.ndarray,
    current_density: np.ndarray,
    power_density: np.ndarray,
) -> None:
    """Export calculation results to CSV file.

    Args:
        filepath: Path to save CSV file.
        r: Radial positions in meters.
        b_field: B-field values in Tesla.
        current_density: Current density values in A/m².
        power_density: Power density values in W/m³.
    """
    filepath = Path(filepath)
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Radius (m)", "B (T)", "J (A/m²)", "P (W/m³)"])
        for ri, bi, ji, pi in zip(r, b_field, current_density, power_density):
            writer.writerow([f"{ri:.6e}", f"{bi:.6e}", f"{ji:.6e}", f"{pi:.6e}"])


def save_simulation(
    filepath: str | Path,
    setup: InductionSetup,
    frequency: float,
    current: float,
    temperature: float = 20.0,
) -> None:
    """Save simulation state to JSON file.

    Args:
        filepath: Path to save JSON file.
        setup: InductionSetup with coil and workpiece parameters.
        frequency: Operating frequency in Hz.
        current: Coil current in amperes.
        temperature: Workpiece temperature in °C.
    """
    filepath = Path(filepath)
    state = {
        "version": "0.1.0",
        "coil": {
            "inner_radius": setup.coil.inner_radius,
            "outer_radius": setup.coil.outer_radius,
            "length": setup.coil.length,
            "turns": setup.coil.turns,
            "wire_diameter": setup.coil.wire_diameter,
        },
        "workpiece": {
            "radius": setup.workpiece.radius,
            "length": setup.workpiece.length,
            "material_name": setup.workpiece.material_name,
        },
        "operating": {
            "frequency": frequency,
            "current": current,
            "temperature": temperature,
        },
    }
    with open(filepath, "w") as f:
        json.dump(state, f, indent=2)


def load_simulation(filepath: str | Path) -> dict:
    """Load simulation state from JSON file.

    Args:
        filepath: Path to JSON file.

    Returns:
        Dict with simulation state.

    Raises:
        ValueError: If JSON is invalid or missing required fields.
        FileNotFoundError: If file doesn't exist.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Simulation file not found: {filepath}")

    with open(filepath, "r") as f:
        state = json.load(f)

    # Validate required fields
    required_top = {"version", "coil", "workpiece", "operating"}
    if not required_top.issubset(state.keys()):
        missing = required_top - state.keys()
        raise ValueError(f"Missing required fields: {missing}")

    required_coil = {"inner_radius", "outer_radius", "length", "turns", "wire_diameter"}
    if not required_coil.issubset(state["coil"].keys()):
        missing = required_coil - state["coil"].keys()
        raise ValueError(f"Missing coil fields: {missing}")

    required_wp = {"radius", "length", "material_name"}
    if not required_wp.issubset(state["workpiece"].keys()):
        missing = required_wp - state["workpiece"].keys()
        raise ValueError(f"Missing workpiece fields: {missing}")

    required_op = {"frequency", "current", "temperature"}
    if not required_op.issubset(state["operating"].keys()):
        missing = required_op - state["operating"].keys()
        raise ValueError(f"Missing operating fields: {missing}")

    return state


def create_setup_from_state(state: dict) -> InductionSetup:
    """Create InductionSetup from loaded simulation state.

    Args:
        state: Dict from load_simulation().

    Returns:
        InductionSetup with loaded parameters.
    """
    coil = SolenoidCoil(
        inner_radius=state["coil"]["inner_radius"],
        outer_radius=state["coil"]["outer_radius"],
        length=state["coil"]["length"],
        turns=state["coil"]["turns"],
        wire_diameter=state["coil"]["wire_diameter"],
    )
    workpiece = CylindricalWorkpiece(
        radius=state["workpiece"]["radius"],
        length=state["workpiece"]["length"],
        material_name=state["workpiece"]["material_name"],
    )
    gap = coil.inner_radius - workpiece.radius
    return InductionSetup(coil=coil, workpiece=workpiece, gap=gap)
