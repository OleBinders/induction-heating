"""Geometry definitions for induction heating calculations.

Provides dataclasses for solenoid coils, cylindrical workpieces, and
the combined induction setup with geometric validation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SolenoidCoil:
    """A solenoid coil geometry for induction heating.

    Attributes:
        inner_radius: Inner radius of the coil (m).
        outer_radius: Outer radius of the coil (m).
        length: Axial length of the coil (m).
        turns: Number of turns (positive integer).
        wire_diameter: Diameter of the coil wire (m).
    """

    inner_radius: float
    outer_radius: float
    length: float
    turns: int
    wire_diameter: float

    def __post_init__(self) -> None:
        if self.inner_radius <= 0:
            raise ValueError(f"inner_radius must be > 0, got {self.inner_radius}")
        if self.outer_radius < self.inner_radius:
            raise ValueError(
                f"outer_radius ({self.outer_radius}) must be >= inner_radius ({self.inner_radius})"
            )
        if self.length <= 0:
            raise ValueError(f"length must be > 0, got {self.length}")
        if self.turns <= 0:
            raise ValueError(f"turns must be > 0, got {self.turns}")
        if self.wire_diameter <= 0:
            raise ValueError(f"wire_diameter must be > 0, got {self.wire_diameter}")

    @property
    def mean_radius(self) -> float:
        """Mean coil radius: (inner_radius + outer_radius) / 2."""
        return (self.inner_radius + self.outer_radius) / 2.0

    @property
    def turn_density(self) -> float:
        """Turns per unit length (turns/m)."""
        return self.turns / self.length

    @property
    def cross_section_area(self) -> float:
        """Cross-sectional area of the coil winding (m²)."""
        return math.pi * (self.outer_radius**2 - self.inner_radius**2)


@dataclass(frozen=True)
class CylindricalWorkpiece:
    """A cylindrical workpiece for induction heating.

    Attributes:
        radius: Workpiece radius (m).
        length: Workpiece length (m).
        material_name: Name of the material (must exist in material database).
    """

    radius: float
    length: float
    material_name: str

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError(f"radius must be > 0, got {self.radius}")
        if self.length <= 0:
            raise ValueError(f"length must be > 0, got {self.length}")
        if not self.material_name or not self.material_name.strip():
            raise ValueError("material_name must be a non-empty string")

    @property
    def cross_section_area(self) -> float:
        """Cross-sectional area (m²)."""
        return math.pi * self.radius**2

    @property
    def volume(self) -> float:
        """Volume (m³)."""
        return self.cross_section_area * self.length

    @property
    def surface_area_lateral(self) -> float:
        """Lateral surface area (m²), excluding end caps."""
        return 2 * math.pi * self.radius * self.length


@dataclass(frozen=True)
class InductionSetup:
    """Complete induction heating setup: coil + workpiece + gap.

    Attributes:
        coil: The solenoid coil geometry.
        workpiece: The cylindrical workpiece geometry.
        gap: Radial clearance between coil inner radius and workpiece radius (m).
    """

    coil: SolenoidCoil
    workpiece: CylindricalWorkpiece
    gap: float = field(default=0.0)

    def __post_init__(self) -> None:
        if self.gap < 0:
            raise ValueError(f"gap must be >= 0, got {self.gap}")
        if self.workpiece.radius >= self.coil.inner_radius:
            raise ValueError(
                f"Workpiece radius ({self.workpiece.radius} m) must be less than "
                f"coil inner radius ({self.coil.inner_radius} m)"
            )
        # Verify gap is consistent with geometry
        expected_gap = self.coil.inner_radius - self.workpiece.radius
        if abs(expected_gap - self.gap) > 1e-12:
            raise ValueError(
                f"gap ({self.gap} m) is inconsistent with coil inner radius "
                f"({self.coil.inner_radius} m) and workpiece radius "
                f"({self.workpiece.radius} m). Expected gap: {expected_gap} m"
            )

    @property
    def coupling_factor(self) -> float:
        """Geometric coupling factor (0 to 1).

        Approximated as the ratio of workpiece cross-section to coil
        inner cross-section. Higher values indicate better magnetic coupling.
        """
        coil_area = math.pi * self.coil.inner_radius**2
        wp_area = self.workpiece.cross_section_area
        return min(wp_area / coil_area, 1.0)

    @property
    def length_ratio(self) -> float:
        """Ratio of workpiece length to coil length."""
        return self.workpiece.length / self.coil.length

    @property
    def radius_ratio(self) -> float:
        """Ratio of workpiece radius to coil mean radius."""
        return self.workpiece.radius / self.coil.mean_radius

    @property
    def workpiece_extends_beyond_coil(self) -> bool:
        """Whether the workpiece is longer than the coil."""
        return self.workpiece.length > self.coil.length
