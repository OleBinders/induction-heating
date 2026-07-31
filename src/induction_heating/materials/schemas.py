"""Pydantic schemas for material data validation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TemperatureDataPoint(BaseModel):
    """A single temperature-property data point."""

    temperature: float = Field(..., description="Temperature value")
    value: float = Field(..., description="Property value at this temperature")


class TemperatureDependentProperty(BaseModel):
    """A property with temperature-dependent data points."""

    data: list[TemperatureDataPoint] = Field(
        ..., description="List of temperature-value data points"
    )
    unit: str = Field(..., description="Unit of the property values")
    temperature_unit: str = Field(
        default="degC", description="Unit of temperature values"
    )


class Material(BaseModel):
    """A material with temperature-dependent properties."""

    name: str = Field(..., description="Material name")
    category: str = Field(..., description="Material category (steel, copper, etc.)")
    density: float = Field(..., description="Density in kg/m³")
    curie_temperature: float | None = Field(
        default=None, description="Curie temperature in °C (None for non-magnetic)"
    )
    resistivity: TemperatureDependentProperty = Field(
        ..., description="Temperature-dependent electrical resistivity"
    )
    relative_permeability: TemperatureDependentProperty | None = Field(
        default=None,
        description="Temperature-dependent relative permeability (None for non-magnetic)",
    )
