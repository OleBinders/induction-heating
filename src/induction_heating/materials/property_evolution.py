"""Property evolution engine for temperature-dependent material properties.

Provides PropertySnapshot dataclass for consistent access to all material
properties at a given temperature, and integration with the electromagnetic
calculation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

from induction_heating.materials.database import MaterialDatabase


@dataclass(frozen=True)
class PropertySnapshot:
    """Material properties at a specific temperature.

    All properties are evaluated at the same temperature to ensure
    consistency in calculations.

    Attributes:
        temperature: Temperature in °C.
        resistivity: Electrical resistivity in Ω·m.
        relative_permeability: Relative magnetic permeability (dimensionless, ≥ 1.0).
        specific_heat: Specific heat capacity in J/(kg·K).
        thermal_conductivity: Thermal conductivity in W/(m·K).
    """

    temperature: float
    resistivity: float
    relative_permeability: float
    specific_heat: float
    thermal_conductivity: float

    def __post_init__(self) -> None:
        if self.resistivity <= 0:
            raise ValueError(
                f"resistivity must be > 0, got {self.resistivity}"
            )
        if self.relative_permeability < 1.0:
            raise ValueError(
                f"relative_permeability must be >= 1.0, got {self.relative_permeability}"
            )
        if self.specific_heat <= 0:
            raise ValueError(
                f"specific_heat must be > 0, got {self.specific_heat}"
            )
        if self.thermal_conductivity <= 0:
            raise ValueError(
                f"thermal_conductivity must be > 0, got {self.thermal_conductivity}"
            )

    @classmethod
    def from_material(
        cls,
        material_db: MaterialDatabase,
        material_name: str,
        temperature: float,
    ) -> PropertySnapshot:
        """Create a PropertySnapshot from the material database.

        Args:
            material_db: Material database instance.
            material_name: Name of the material.
            temperature: Temperature in °C.

        Returns:
            PropertySnapshot with all properties at the given temperature.

        Raises:
            KeyError: If material not found.
            ValueError: If temperature is outside data range.
        """
        resistivity = material_db.get_property_at_temperature(
            material_name, "resistivity", temperature
        )
        relative_permeability = material_db.get_permeability(
            material_name, temperature
        )

        # Specific heat and thermal conductivity: use defaults if not available
        # These will be extended when data files include these properties
        specific_heat = _get_specific_heat(material_db, material_name, temperature)
        thermal_conductivity = _get_thermal_conductivity(
            material_db, material_name, temperature
        )

        return cls(
            temperature=temperature,
            resistivity=resistivity,
            relative_permeability=relative_permeability,
            specific_heat=specific_heat,
            thermal_conductivity=thermal_conductivity,
        )


def _get_specific_heat(
    material_db: MaterialDatabase, material_name: str, temperature: float
) -> float:
    """Get specific heat at temperature, with fallback defaults."""
    try:
        return material_db.get_property_at_temperature(
            material_name, "specific_heat", temperature
        )
    except (KeyError, ValueError):
        # Default values for common materials
        mat = material_db.get_material(material_name)
        if mat.category == "steel":
            # Steel: ~450 J/(kg·K) at 20°C, ~700 J/(kg·K) at 900°C
            return 450.0 + 0.28 * (temperature - 20.0)
        elif mat.category == "copper":
            return 385.0
        elif mat.category == "aluminum":
            return 900.0
        elif mat.category == "brass":
            return 380.0
        return 500.0  # Generic default


def _get_thermal_conductivity(
    material_db: MaterialDatabase, material_name: str, temperature: float
) -> float:
    """Get thermal conductivity at temperature, with fallback defaults."""
    try:
        return material_db.get_property_at_temperature(
            material_name, "thermal_conductivity", temperature
        )
    except (KeyError, ValueError):
        # Default values for common materials
        mat = material_db.get_material(material_name)
        if mat.category == "steel":
            # Steel: ~50 W/(m·K) at 20°C, ~25 W/(m·K) at 800°C
            return max(25.0, 50.0 - 0.031 * (temperature - 20.0))
        elif mat.category == "copper":
            return 400.0
        elif mat.category == "aluminum":
            return 200.0
        elif mat.category == "brass":
            return 120.0
        return 50.0  # Generic default


def get_properties_at_temperature(
    material_db: MaterialDatabase,
    material_name: str,
    temperature: float,
) -> PropertySnapshot:
    """Get all material properties at a given temperature.

    This is the primary interface for retrieving temperature-dependent
    properties. All properties are evaluated at the same temperature
    to ensure consistency.

    Args:
        material_db: Material database instance.
        material_name: Name of the material.
        temperature: Temperature in °C.

    Returns:
        PropertySnapshot with all properties at the given temperature.
    """
    return PropertySnapshot.from_material(material_db, material_name, temperature)
