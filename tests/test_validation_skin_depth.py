"""Skin depth validation tests against published reference values.

Reference values from:
- Wikipedia: Skin effect (copper at 1 MHz = 66 μm)
- Zinn & Semiatin, "Elements of Induction Heating" (ASM International, 1988)
"""

from __future__ import annotations

import pytest

from induction_heating.core.electromagnetic import calculate_skin_depth


class TestSkinDepthValidation:
    """Validate skin depth calculations against published reference values."""

    # Copper reference values (μᵣ = 1.0, ρ = 1.68e-8 Ω·m)
    # Source: Wikipedia Skin effect article

    def test_copper_1mhz(self) -> None:
        """Copper at 1 MHz: δ = 66 μm ± 2%."""
        delta = calculate_skin_depth(1.68e-8, 1.0, 1e6)
        assert delta == pytest.approx(66e-6, rel=0.02)

    def test_copper_50khz(self) -> None:
        """Copper at 50 kHz: δ = 0.295 mm ± 2%."""
        delta = calculate_skin_depth(1.68e-8, 1.0, 50e3)
        assert delta == pytest.approx(0.295e-3, rel=0.02)

    def test_copper_10khz(self) -> None:
        """Copper at 10 kHz: δ = 0.661 mm ± 2%."""
        delta = calculate_skin_depth(1.68e-8, 1.0, 10e3)
        assert delta == pytest.approx(0.661e-3, rel=0.02)

    # Steel reference values (ρ = 1.43e-7 Ω·m)
    # Source: Zinn & Semiatin, "Elements of Induction Heating"

    def test_steel_magnetic_10khz(self) -> None:
        """Steel (μᵣ=200) at 10 kHz: δ = 0.135 mm ± 2%."""
        delta = calculate_skin_depth(1.43e-7, 200.0, 10e3)
        assert delta == pytest.approx(0.135e-3, rel=0.02)

    def test_steel_nonmagnetic_10khz(self) -> None:
        """Steel (μᵣ=1) at 10 kHz: δ = 1.90 mm ± 2%."""
        delta = calculate_skin_depth(1.43e-7, 1.0, 10e3)
        assert delta == pytest.approx(1.90e-3, rel=0.02)

    def test_steel_nonmagnetic_50khz(self) -> None:
        """Steel (μᵣ=1) at 50 kHz: δ = 0.85 mm ± 2%."""
        delta = calculate_skin_depth(1.43e-7, 1.0, 50e3)
        assert delta == pytest.approx(0.85e-3, rel=0.02)
