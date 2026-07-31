"""Tests for the unit system and physical constants."""

from __future__ import annotations

import scipy.constants
import pytest

from induction_heating.utils import constants
from induction_heating.utils.units import Q_, ureg, quantity, to_si


class TestUnitRegistry:
    """Test singleton UnitRegistry behavior."""

    def test_singleton_registry(self) -> None:
        """Multiple imports return the same registry instance."""
        from induction_heating.utils.units import ureg as ureg2

        assert ureg is ureg2

    def test_quantity_alias(self) -> None:
        """Q_ creates valid quantities."""
        q = Q_(1.0, "tesla")
        assert q.magnitude == 1.0
        assert str(q.units) == "tesla"

    def test_quantity_function(self) -> None:
        """quantity() creates valid quantities."""
        q = quantity(1.0, "tesla")
        assert q.magnitude == 1.0
        assert str(q.units) == "tesla"


class TestElectromagneticUnits:
    """Test electromagnetic unit support."""

    def test_tesla(self) -> None:
        """Tesla unit works correctly."""
        q = Q_(1.0, "tesla")
        assert q.magnitude == 1.0

    def test_ohm_meter(self) -> None:
        """Ohm-meter unit works correctly."""
        q = Q_(1e-7, "ohm * meter")
        assert q.magnitude == 1e-7

    def test_ohm_meter_to_ohm_cm(self) -> None:
        """Ohm-meter to ohm-cm conversion is correct."""
        q = Q_(1.0, "ohm * meter")
        converted = q.to("ohm * centimeter")
        assert converted.magnitude == pytest.approx(100.0, rel=1e-10)

    def test_henry(self) -> None:
        """Henry unit works correctly."""
        q = Q_(1.0, "henry")
        assert q.magnitude == 1.0

    def test_ampere(self) -> None:
        """Ampere unit works correctly."""
        q = Q_(1.0, "ampere")
        assert q.magnitude == 1.0

    def test_hertz(self) -> None:
        """Hertz unit works correctly."""
        q = Q_(1000.0, "hertz")
        assert q.magnitude == 1000.0

    def test_magnitude_extraction(self) -> None:
        """Magnitude extraction returns raw number."""
        q = Q_(1e-7, "ohm * meter")
        assert q.magnitude == 1e-7


class TestToSI:
    """Test SI conversion utility."""

    def test_to_si_resistivity(self) -> None:
        """Resistivity converts to SI base units."""
        q = Q_(1.0, "ohm * centimeter")
        si_value = to_si(q)
        assert si_value == pytest.approx(0.01, rel=1e-10)


class TestPhysicalConstants:
    """Test physical constant values."""

    def test_mu_0(self) -> None:
        """Permeability of free space matches scipy."""
        assert constants.mu_0() == pytest.approx(scipy.constants.mu_0, rel=1e-15)

    def test_epsilon_0(self) -> None:
        """Permittivity of free space matches scipy."""
        assert constants.epsilon_0() == pytest.approx(scipy.constants.epsilon_0, rel=1e-15)

    def test_mu_0_value(self) -> None:
        """μ₀ = 4π × 10⁻⁷ H/m."""
        expected = 4 * scipy.constants.pi * 1e-7
        assert constants.MU_0 == pytest.approx(expected, rel=1e-15)

    def test_speed_of_light(self) -> None:
        """Speed of light matches scipy."""
        assert constants.C == pytest.approx(scipy.constants.c, rel=1e-15)

    def test_elementary_charge(self) -> None:
        """Elementary charge matches scipy."""
        assert constants.ELEMENTARY_CHARGE == pytest.approx(
            scipy.constants.elementary_charge, rel=1e-15
        )
