"""Tests for geometry dataclasses."""

from __future__ import annotations

import math
import pytest

from induction_heating.core.geometry import (
    SolenoidCoil,
    CylindricalWorkpiece,
    InductionSetup,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_coil() -> SolenoidCoil:
    return SolenoidCoil(
        inner_radius=0.025,
        outer_radius=0.030,
        length=0.10,
        turns=20,
        wire_diameter=0.005,
    )


@pytest.fixture
def valid_workpiece() -> CylindricalWorkpiece:
    return CylindricalWorkpiece(
        radius=0.020,
        length=0.08,
        material_name="Low Carbon Steel (AISI 1018)",
    )


# ---------------------------------------------------------------------------
# SolenoidCoil tests
# ---------------------------------------------------------------------------

class TestSolenoidCoil:
    """Test SolenoidCoil validation and computed properties."""

    def test_valid_coil(self, valid_coil: SolenoidCoil) -> None:
        assert valid_coil.inner_radius == 0.025
        assert valid_coil.outer_radius == 0.030
        assert valid_coil.length == 0.10
        assert valid_coil.turns == 20
        assert valid_coil.wire_diameter == 0.005

    def test_mean_radius(self, valid_coil: SolenoidCoil) -> None:
        assert valid_coil.mean_radius == pytest.approx(0.0275)

    def test_turn_density(self, valid_coil: SolenoidCoil) -> None:
        assert valid_coil.turn_density == pytest.approx(200.0)  # 20 / 0.10

    def test_cross_section_area(self, valid_coil: SolenoidCoil) -> None:
        expected = math.pi * (0.030**2 - 0.025**2)
        assert valid_coil.cross_section_area == pytest.approx(expected)

    def test_negative_inner_radius_raises(self) -> None:
        with pytest.raises(ValueError, match="inner_radius"):
            SolenoidCoil(
                inner_radius=-0.01, outer_radius=0.03,
                length=0.10, turns=20, wire_diameter=0.005,
            )

    def test_zero_inner_radius_raises(self) -> None:
        with pytest.raises(ValueError, match="inner_radius"):
            SolenoidCoil(
                inner_radius=0.0, outer_radius=0.03,
                length=0.10, turns=20, wire_diameter=0.005,
            )

    def test_outer_radius_less_than_inner_raises(self) -> None:
        with pytest.raises(ValueError, match="outer_radius"):
            SolenoidCoil(
                inner_radius=0.03, outer_radius=0.02,
                length=0.10, turns=20, wire_diameter=0.005,
            )

    def test_zero_length_raises(self) -> None:
        with pytest.raises(ValueError, match="length"):
            SolenoidCoil(
                inner_radius=0.025, outer_radius=0.030,
                length=0.0, turns=20, wire_diameter=0.005,
            )

    def test_zero_turns_raises(self) -> None:
        with pytest.raises(ValueError, match="turns"):
            SolenoidCoil(
                inner_radius=0.025, outer_radius=0.030,
                length=0.10, turns=0, wire_diameter=0.005,
            )

    def test_negative_wire_diameter_raises(self) -> None:
        with pytest.raises(ValueError, match="wire_diameter"):
            SolenoidCoil(
                inner_radius=0.025, outer_radius=0.030,
                length=0.10, turns=20, wire_diameter=-0.005,
            )

    def test_equal_inner_outer_radius_valid(self) -> None:
        """Thin coil (inner == outer) should be valid."""
        coil = SolenoidCoil(
            inner_radius=0.025, outer_radius=0.025,
            length=0.10, turns=20, wire_diameter=0.001,
        )
        assert coil.mean_radius == 0.025


# ---------------------------------------------------------------------------
# CylindricalWorkpiece tests
# ---------------------------------------------------------------------------

class TestCylindricalWorkpiece:
    """Test CylindricalWorkpiece validation and computed properties."""

    def test_valid_workpiece(self, valid_workpiece: CylindricalWorkpiece) -> None:
        assert valid_workpiece.radius == 0.020
        assert valid_workpiece.length == 0.08
        assert valid_workpiece.material_name == "Low Carbon Steel (AISI 1018)"

    def test_cross_section_area(self, valid_workpiece: CylindricalWorkpiece) -> None:
        expected = math.pi * 0.020**2
        assert valid_workpiece.cross_section_area == pytest.approx(expected)

    def test_volume(self, valid_workpiece: CylindricalWorkpiece) -> None:
        expected = math.pi * 0.020**2 * 0.08
        assert valid_workpiece.volume == pytest.approx(expected)

    def test_surface_area_lateral(self, valid_workpiece: CylindricalWorkpiece) -> None:
        expected = 2 * math.pi * 0.020 * 0.08
        assert valid_workpiece.surface_area_lateral == pytest.approx(expected)

    def test_negative_radius_raises(self) -> None:
        with pytest.raises(ValueError, match="radius"):
            CylindricalWorkpiece(radius=-0.01, length=0.08, material_name="Steel")

    def test_zero_length_raises(self) -> None:
        with pytest.raises(ValueError, match="length"):
            CylindricalWorkpiece(radius=0.02, length=0.0, material_name="Steel")

    def test_empty_material_name_raises(self) -> None:
        with pytest.raises(ValueError, match="material_name"):
            CylindricalWorkpiece(radius=0.02, length=0.08, material_name="")

    def test_whitespace_material_name_raises(self) -> None:
        with pytest.raises(ValueError, match="material_name"):
            CylindricalWorkpiece(radius=0.02, length=0.08, material_name="   ")


# ---------------------------------------------------------------------------
# InductionSetup tests
# ---------------------------------------------------------------------------

class TestInductionSetup:
    """Test InductionSetup validation and computed properties."""

    def test_valid_setup(self, valid_coil: SolenoidCoil, valid_workpiece: CylindricalWorkpiece) -> None:
        gap = valid_coil.inner_radius - valid_workpiece.radius  # 0.005
        setup = InductionSetup(coil=valid_coil, workpiece=valid_workpiece, gap=gap)
        assert setup.gap == pytest.approx(0.005)

    def test_coupling_factor(self, valid_coil: SolenoidCoil, valid_workpiece: CylindricalWorkpiece) -> None:
        gap = valid_coil.inner_radius - valid_workpiece.radius
        setup = InductionSetup(coil=valid_coil, workpiece=valid_workpiece, gap=gap)
        # wp_area / coil_inner_area = (π*0.02²) / (π*0.025²) = 0.64
        assert setup.coupling_factor == pytest.approx(0.64)

    def test_coupling_factor_between_0_and_1(
        self, valid_coil: SolenoidCoil, valid_workpiece: CylindricalWorkpiece
    ) -> None:
        gap = valid_coil.inner_radius - valid_workpiece.radius
        setup = InductionSetup(coil=valid_coil, workpiece=valid_workpiece, gap=gap)
        assert 0 < setup.coupling_factor < 1

    def test_length_ratio(self, valid_coil: SolenoidCoil, valid_workpiece: CylindricalWorkpiece) -> None:
        gap = valid_coil.inner_radius - valid_workpiece.radius
        setup = InductionSetup(coil=valid_coil, workpiece=valid_workpiece, gap=gap)
        assert setup.length_ratio == pytest.approx(0.08 / 0.10)

    def test_radius_ratio(self, valid_coil: SolenoidCoil, valid_workpiece: CylindricalWorkpiece) -> None:
        gap = valid_coil.inner_radius - valid_workpiece.radius
        setup = InductionSetup(coil=valid_coil, workpiece=valid_workpiece, gap=gap)
        assert setup.radius_ratio == pytest.approx(0.020 / 0.0275)

    def test_workpiece_extends_beyond_coil(self, valid_coil: SolenoidCoil) -> None:
        wp = CylindricalWorkpiece(radius=0.020, length=0.15, material_name="Steel")
        gap = valid_coil.inner_radius - wp.radius
        setup = InductionSetup(coil=valid_coil, workpiece=wp, gap=gap)
        assert setup.workpiece_extends_beyond_coil is True

    def test_workpiece_fits_inside_coil(self, valid_coil: SolenoidCoil) -> None:
        wp = CylindricalWorkpiece(radius=0.020, length=0.08, material_name="Steel")
        gap = valid_coil.inner_radius - wp.radius
        setup = InductionSetup(coil=valid_coil, workpiece=wp, gap=gap)
        assert setup.workpiece_extends_beyond_coil is False

    def test_workpiece_too_large_raises(self, valid_coil: SolenoidCoil) -> None:
        wp = CylindricalWorkpiece(radius=0.030, length=0.08, material_name="Steel")
        with pytest.raises(ValueError, match="Workpiece radius"):
            InductionSetup(coil=valid_coil, workpiece=wp, gap=0.0)

    def test_negative_gap_raises(self, valid_coil: SolenoidCoil, valid_workpiece: CylindricalWorkpiece) -> None:
        with pytest.raises(ValueError, match="gap"):
            InductionSetup(coil=valid_coil, workpiece=valid_workpiece, gap=-0.001)

    def test_gap_inconsistent_raises(self, valid_coil: SolenoidCoil, valid_workpiece: CylindricalWorkpiece) -> None:
        """Gap must match the actual geometric clearance."""
        with pytest.raises(ValueError, match="inconsistent"):
            InductionSetup(coil=valid_coil, workpiece=valid_workpiece, gap=0.020)

    def test_zero_gap_valid(self, valid_coil: SolenoidCoil) -> None:
        """Workpiece touching coil inner surface (gap=0) should be valid."""
        wp = CylindricalWorkpiece(
            radius=valid_coil.inner_radius - 1e-12,
            length=0.08,
            material_name="Steel",
        )
        setup = InductionSetup(coil=valid_coil, workpiece=wp, gap=1e-12)
        assert setup.gap >= 0
