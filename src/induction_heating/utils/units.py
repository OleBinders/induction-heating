"""Physical unit management using Pint.

This module provides a singleton UnitRegistry and convenience functions
for creating and manipulating physical quantities with proper units.

In practice, the core numeric pipeline (induction_heating.core.*,
induction_heating.materials.*) works in raw floats/NumPy arrays, always in
SI base units (Ω·m, T, Hz, m, °C as noted per-argument in docstrings) --
not pint.Quantity. That's a deliberate tradeoff: scipy's special functions
(ber/bei, elliptic integrals, etc.) and vectorized NumPy operations don't
accept Quantity objects, so threading Pint through the hot calculation path
would mean unwrapping/rewrapping constantly for little safety benefit there.
This module exists for unit-*conversion* at the edges (e.g. GUI unit display,
import/export of values in non-SI units) where Pint's conversion machinery
is actually useful -- not as a wrapper mandated for internal calculations.
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
