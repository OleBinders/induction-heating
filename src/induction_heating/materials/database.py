"""Material database with loading, querying, and temperature interpolation."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from scipy.interpolate import CubicSpline, PchipInterpolator

from induction_heating.materials.curie_transition import permeability_sigmoid
from induction_heating.materials.schemas import Material


class MaterialDatabase:
    """Loads material data from JSON files and provides interpolated properties."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize and load all material data files.

        Args:
            data_dir: Path to directory containing material JSON files.
                Defaults to the package's data/ directory.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"

        self._materials: dict[str, Material] = {}
        self._interpolators: dict[str, dict[str, Any]] = {}

        self._load_all(data_dir)

    def _load_all(self, data_dir: Path) -> None:
        """Load all JSON files from the data directory."""
        for json_file in sorted(data_dir.glob("*.json")):
            with open(json_file, "r") as f:
                raw = json.load(f)
            material = Material.model_validate(raw)
            key = material.name.lower()
            self._materials[key] = material
            self._build_interpolators(key, material)

    def _build_interpolators(self, key: str, material: Material) -> None:
        """Build interpolation functions for a material's properties."""
        interpolators: dict[str, Any] = {}

        # Resistivity: CubicSpline for smooth interpolation
        rho_temps = [d.temperature for d in material.resistivity.data]
        rho_values = [d.value for d in material.resistivity.data]
        interpolators["resistivity"] = CubicSpline(rho_temps, rho_values)
        interpolators["resistivity_range"] = (rho_temps[0], rho_temps[-1])

        # Permeability: PchipInterpolator for monotonicity (stays positive)
        if material.relative_permeability is not None:
            mu_temps = [d.temperature for d in material.relative_permeability.data]
            mu_values = [d.value for d in material.relative_permeability.data]
            interpolators["relative_permeability"] = PchipInterpolator(
                mu_temps, mu_values
            )
            interpolators["relative_permeability_range"] = (
                mu_temps[0],
                mu_temps[-1],
            )

        self._interpolators[key] = interpolators

    def get_material(self, name: str) -> Material:
        """Get a material by name (case-insensitive, supports partial match).

        Args:
            name: Material name (e.g., "Low Carbon Steel", "copper").

        Returns:
            The matching Material object.

        Raises:
            KeyError: If no material with the given name exists.
        """
        key = name.lower()

        # Exact match first
        if key in self._materials:
            return self._materials[key]

        # Partial match: find materials where the key is a substring
        matches = [
            m for m in self._materials.values() if key in m.name.lower()
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            names = [m.name for m in matches]
            raise KeyError(
                f"Ambiguous material '{name}'. Matches: {', '.join(names)}"
            )

        available = list(m.name for m in self._materials.values())
        raise KeyError(
            f"Material '{name}' not found. Available: {', '.join(available)}"
        )

    def list_materials(self) -> list[str]:
        """Return list of available material names."""
        return [m.name for m in self._materials.values()]

    def _resolve_material_key(self, material_name: str) -> str:
        """Resolve a material name to its canonical database key.

        Delegates to get_material() so the exact/partial-match lookup logic
        lives in one place. self._materials and self._interpolators are always
        keyed identically (both by material.name.lower(), set in _load_all()),
        so the resolved material's own key is always a valid interpolators key.
        """
        return self.get_material(material_name).name.lower()

    def get_property_at_temperature(
        self, material_name: str, property_name: str, temperature: float
    ) -> float:
        """Get interpolated property value at a given temperature.

        Args:
            material_name: Name of the material.
            property_name: Property name ("resistivity" or "relative_permeability").
            temperature: Temperature in °C.

        Returns:
            Interpolated property value.

        Raises:
            KeyError: If material or property not found.
            ValueError: If temperature is outside the data range.
        """
        key = self._resolve_material_key(material_name)

        if property_name not in self._interpolators[key]:
            raise KeyError(
                f"Property '{property_name}' not available for '{material_name}'"
            )

        interp = self._interpolators[key][property_name]
        temp_range = self._interpolators[key][f"{property_name}_range"]

        if temperature < temp_range[0] or temperature > temp_range[1]:
            raise ValueError(
                f"Temperature {temperature}°C is outside the valid range "
                f"[{temp_range[0]}, {temp_range[1]}]°C for {property_name}"
            )

        value = float(interp(temperature))

        # Ensure permeability stays positive
        if property_name == "relative_permeability" and value < 1.0:
            value = 1.0

        return value

    def get_permeability(
        self, material_name: str, temperature: float
    ) -> float:
        """Get relative permeability at a given temperature.

        Uses the best available method:
        1. If material has permeability data points: PchipInterpolator
        2. If material has curie_temperature but no data: sigmoid model
        3. If material is non-magnetic: returns 1.0

        Args:
            material_name: Name of the material.
            temperature: Temperature in °C.

        Returns:
            Relative permeability μᵣ(T), guaranteed ≥ 1.0.
        """
        key = self._resolve_material_key(material_name)
        material = self._materials[key]

        # Method 1: Data-driven interpolation
        if "relative_permeability" in self._interpolators[key]:
            interp = self._interpolators[key]["relative_permeability"]
            temp_range = self._interpolators[key]["relative_permeability_range"]

            if temp_range[0] <= temperature <= temp_range[1]:
                value = float(interp(temperature))
                return max(value, 1.0)

            # Outside data range: fall through to model-based

        # Method 2: Sigmoid model (if curie_temperature available)
        if material.curie_temperature is not None:
            if "relative_permeability" not in self._interpolators[key]:
                # No permeability data at all, so mu_r_0 can't be estimated from
                # this material's own data. Rather than guess a material-agnostic
                # number (e.g. steel's ~200 would badly misrepresent a different
                # ferromagnetic alloy), fail loudly -- same philosophy as the
                # out-of-range ValueError in get_property_at_temperature above.
                raise ValueError(
                    f"'{material.name}' has a Curie temperature "
                    f"({material.curie_temperature}°C) but no relative_permeability "
                    "data, so mu_r_0 cannot be estimated. Add permeability data "
                    "points to the material's JSON file."
                )

            interp = self._interpolators[key]["relative_permeability"]
            mu_r_0 = float(interp(temp_range[0]))
            return permeability_sigmoid(temperature, mu_r_0, material.curie_temperature)

        # Method 3: Non-magnetic
        return 1.0
