"""Physical unit management using Pint.

This module provides a singleton UnitRegistry and convenience functions
for creating and manipulating physical quantities with proper units.

All electromagnetic calculations in this project MUST use quantities
from this module — never raw floats for physical values.
"""

from __future__ import annotations

import pint

# Singleton UnitRegistry — created once at module import.
# All code must import `ureg` or `Q_` from this module; never create
# additional UnitRegistry instances (they are incompatible with each other).
ureg: pint.UnitRegistry = pint.UnitRegistry()

# Convenience alias for creating quantities: Q_(1.0, "tesla")
Q_ = ureg.Quantity

# Ensure electromagnetic units are available
# Pint includes these by default, but we verify them here
_TESLA = ureg.tesla
_HENRY = ureg.henry
_OHM_METER = ureg.ohm * ureg.meter
_AMPERE = ureg.ampere
_HERTZ = ureg.hertz


def quantity(value: float, unit: str) -> pint.Quantity:
    """Create a physical quantity with the given value and unit.

    This is an explicit alternative to Q_() that makes the intent clearer
    in calculation code.

    Args:
        value: Numerical value.
        unit: Unit string (e.g., "tesla", "ohm*m", "degC").

    Returns:
        Pint Quantity with the specified value and unit.
    """
    return Q_(value, unit)


def to_si(qty: pint.Quantity) -> float:
    """Convert a quantity to SI base units and return the magnitude.

    Args:
        qty: Pint Quantity to convert.

    Returns:
        Magnitude in SI base units.
    """
    return qty.to_base_units().magnitude
