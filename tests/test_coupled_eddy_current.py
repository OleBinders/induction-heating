"""Validation tests for the bare-coil TREE eigenfunction field machinery.

The load-bearing check in this file is NOT self-consistency against the
new code -- it is a cross-check of ``bare_coil_b_field`` against the
already-validated, independently-derived closed-form solenoid field
functions in ``core/electromagnetic.py`` (Biot-Savart on-axis formula and
the Callaghan & Maslen off-axis elliptic-integral formula), which are
themselves covered by ``tests/test_validation_bfield.py``. If Phase 2b's
eigenfunction machinery doesn't reproduce those, nothing built on top of
it (workpiece coupling, impedance, etc.) can be trusted -- see the module
docstring in ``core/coupled_eddy_current.py`` for the full derivation and
the two transcription-error corrections this implementation makes
relative to the literally-summarized paper equations.

Coil geometries used here are deliberately thin-walled (outer_radius only
slightly larger than inner_radius). The closed-form comparison functions
model the coil as an infinitesimally thin current sheet at the mean
radius; the TREE model here treats the winding as a uniform current
density filling the full [r1, r2] x [-L/2, L/2] cross-section. The two
models only agree closely when the winding is radially thin relative to
its own radius -- a genuinely thick winding is expected to show a real,
larger residual discrepancy that is a model-difference, not a bug (this is
demonstrated explicitly in ``test_thick_winding_shows_expected_model_gap``
below, so a future contributor does not mistake it for a regression).
"""

from __future__ import annotations

import numpy as np
import pytest

from induction_heating.core.coupled_eddy_current import (
    bare_coil_axial_eigenvalues,
    bare_coil_b_field,
    bare_coil_coefficients,
    bare_coil_vector_potential,
    coil_turn_density,
)
from induction_heating.core.electromagnetic import (
    solenoid_b_field_off_axis,
    solenoid_b_field_on_axis,
)
from induction_heating.core.geometry import SolenoidCoil


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _thin_coil(inner_radius: float, length: float, turns: int) -> SolenoidCoil:
    """A thin-walled coil (radial thickness = 2% of inner_radius) so the
    TREE volumetric-current model and the closed-form thin-sheet model
    describe (nearly) the same physical current distribution."""
    wall = 0.02 * inner_radius
    return SolenoidCoil(
        inner_radius=inner_radius,
        outer_radius=inner_radius + wall,
        length=length,
        turns=turns,
        wire_diameter=wall / 4.0,
    )


def _max_relative_error(actual: np.ndarray, expected: np.ndarray) -> float:
    expected = np.asarray(expected)
    actual = np.asarray(actual)
    # Ignore near-zero reference values (e.g. B_rho on-axis, exactly 0 by
    # symmetry) where relative error is not a meaningful metric.
    scale = np.max(np.abs(expected))
    mask = np.abs(expected) > 1e-6 * scale
    if not np.any(mask):
        return 0.0
    return float(np.max(np.abs(actual[mask] - expected[mask]) / np.abs(expected[mask])))


# ---------------------------------------------------------------------------
# Cross-validation against the closed-form solenoid field (the core check)
# ---------------------------------------------------------------------------


class TestBareCoilBFieldAgreesWithClosedForm:
    """Cross-check bare_coil_b_field against solenoid_b_field_on_axis /
    solenoid_b_field_off_axis for several coil aspect ratios, at on-axis,
    off-axis-inside-bore, and off-axis-outside-coil points."""

    @pytest.mark.parametrize(
        "coil,truncation_factor,num_eigenvalues,tolerance",
        [
            # Short/medium coil (length ~ 4x mean radius): converges well
            # at a modest truncation length and eigenvalue count.
            (_thin_coil(0.025, 0.10, 100), 5.0, 150, 0.01),
            # Long, thin coil (length ~ 20x radius): needs more
            # eigenvalues to resolve near-source off-axis points.
            (_thin_coil(0.02, 0.40, 400), 5.0, 400, 0.02),
        ],
    )
    def test_on_axis_matches_biot_savart(
        self, coil, truncation_factor, num_eigenvalues, tolerance
    ) -> None:
        current = 10.0
        h = truncation_factor * coil.length
        z = np.linspace(-0.45, 0.45, 7) * coil.length

        b_true = solenoid_b_field_on_axis(coil, current, z)
        _, b_z = bare_coil_b_field(
            coil, current, h, np.zeros_like(z), z, num_eigenvalues=num_eigenvalues
        )

        err = _max_relative_error(b_z, b_true)
        assert err < tolerance, f"on-axis B_z max relative error {err:.4%} >= {tolerance:.0%}"

    @pytest.mark.parametrize(
        "coil,truncation_factor,num_eigenvalues,tolerance",
        [
            (_thin_coil(0.025, 0.10, 100), 5.0, 150, 0.01),
            (_thin_coil(0.02, 0.40, 400), 5.0, 400, 0.02),
        ],
    )
    def test_off_axis_inside_bore_matches_closed_form(
        self, coil, truncation_factor, num_eigenvalues, tolerance
    ) -> None:
        current = 10.0
        h = truncation_factor * coil.length
        z = np.linspace(-0.45, 0.45, 7) * coil.length
        rho = np.full_like(z, 0.6 * coil.inner_radius)

        b_rho_true, b_z_true = solenoid_b_field_off_axis(coil, current, rho, z)
        b_rho, b_z = bare_coil_b_field(
            coil, current, h, rho, z, num_eigenvalues=num_eigenvalues
        )

        err_z = _max_relative_error(b_z, b_z_true)
        err_rho = _max_relative_error(b_rho, b_rho_true)
        assert err_z < tolerance, f"inside-bore B_z error {err_z:.4%} >= {tolerance:.0%}"
        assert err_rho < tolerance, f"inside-bore B_rho error {err_rho:.4%} >= {tolerance:.0%}"

    @pytest.mark.parametrize(
        "coil,truncation_factor,num_eigenvalues,tolerance",
        [
            (_thin_coil(0.025, 0.10, 100), 5.0, 150, 0.01),
            (_thin_coil(0.02, 0.40, 400), 5.0, 400, 0.02),
        ],
    )
    def test_off_axis_outside_coil_matches_closed_form(
        self, coil, truncation_factor, num_eigenvalues, tolerance
    ) -> None:
        current = 10.0
        h = truncation_factor * coil.length
        z = np.linspace(-0.45, 0.45, 7) * coil.length
        rho = np.full_like(z, 1.8 * coil.outer_radius)

        b_rho_true, b_z_true = solenoid_b_field_off_axis(coil, current, rho, z)
        b_rho, b_z = bare_coil_b_field(
            coil, current, h, rho, z, num_eigenvalues=num_eigenvalues
        )

        err_z = _max_relative_error(b_z, b_z_true)
        err_rho = _max_relative_error(b_rho, b_rho_true)
        assert err_z < tolerance, f"outside-coil B_z error {err_z:.4%} >= {tolerance:.0%}"
        assert err_rho < tolerance, f"outside-coil B_rho error {err_rho:.4%} >= {tolerance:.0%}"

    def test_short_fat_coil_needs_larger_truncation_length(self) -> None:
        """A short, 'fat' coil (length comparable to its own radius) is a
        documented harder case: h=5*length is not enough to converge a
        near-field off-axis point, but h=20*length is. This isn't a bug --
        it demonstrates the truncation-length sensitivity documented in
        the module docstring, and guards against a future change silently
        breaking that documented behavior.
        """
        coil = _thin_coil(0.03, 0.02, 20)  # length == 0.67 * inner_radius
        current = 10.0
        z = np.linspace(-0.45, 0.45, 5) * coil.length
        rho = np.full_like(z, 1.8 * coil.outer_radius)
        b_rho_true, b_z_true = solenoid_b_field_off_axis(coil, current, rho, z)

        _, b_z_small_h = bare_coil_b_field(
            coil, current, 5.0 * coil.length, rho, z, num_eigenvalues=150
        )
        _, b_z_large_h = bare_coil_b_field(
            coil, current, 20.0 * coil.length, rho, z, num_eigenvalues=150
        )

        err_small_h = _max_relative_error(b_z_small_h, b_z_true)
        err_large_h = _max_relative_error(b_z_large_h, b_z_true)

        assert err_large_h < err_small_h, (
            "increasing the truncation length should reduce error for a "
            f"short/fat coil (got small-h err={err_small_h:.4%}, "
            f"large-h err={err_large_h:.4%})"
        )
        assert err_large_h < 0.005


class TestConvergence:
    """The discrepancy against the closed-form field must shrink as
    num_eigenvalues increases -- this is the phase's explicit "don't paper
    over a non-convergent result" check."""

    def test_error_shrinks_monotonically_with_num_eigenvalues(self) -> None:
        coil = _thin_coil(0.025, 0.10, 100)
        current = 10.0
        h = 5.0 * coil.length
        z = np.linspace(-0.45, 0.45, 7) * coil.length

        b_true = solenoid_b_field_on_axis(coil, current, z)

        errors = []
        for num_eigenvalues in (20, 80, 200):
            _, b_z = bare_coil_b_field(
                coil, current, h, np.zeros_like(z), z, num_eigenvalues=num_eigenvalues
            )
            errors.append(_max_relative_error(b_z, b_true))

        assert errors[1] < errors[0], (
            f"error should shrink from 20 to 80 eigenvalues, got {errors}"
        )
        assert errors[2] <= errors[1] * 1.01, (
            f"error should not grow from 80 to 200 eigenvalues, got {errors}"
        )
        # Converged (80+ eigenvalues) result should be well under 1%.
        assert errors[1] < 0.01, f"80-eigenvalue error {errors[1]:.4%} should be < 1%"


# ---------------------------------------------------------------------------
# Unit-level checks on the building blocks
# ---------------------------------------------------------------------------


class TestBuildingBlocks:
    def test_coil_turn_density_is_areal_not_linear(self) -> None:
        """n = N / [(r2-r1)*length] -- turns per unit AREA, not per unit
        length (that's SolenoidCoil.turn_density). Regression guard against
        silently swapping in the linear turn density, which has different
        units and would desync the whole prefactor."""
        coil = SolenoidCoil(
            inner_radius=0.02, outer_radius=0.025, length=0.10, turns=100, wire_diameter=0.001
        )
        n = coil_turn_density(coil)
        expected = 100 / ((0.025 - 0.02) * 0.10)
        assert n == pytest.approx(expected)
        # Sanity: areal density must differ from (and be larger than) the
        # linear turns/length already exposed by SolenoidCoil.
        assert n != pytest.approx(coil.turn_density)

    def test_eigenvalues_are_quarter_wave_family(self) -> None:
        """kappa_m = (2m-1)*pi/(2h) -- the Dirichlet/Neumann eigenbasis
        this module actually uses (see the module docstring for why this
        differs from the literally-summarized j*pi/h)."""
        h = 0.5
        kappa = bare_coil_axial_eigenvalues(h, 5)
        expected = (2 * np.arange(1, 6) - 1) * np.pi / (2 * h)
        np.testing.assert_allclose(kappa, expected)
        # Each eigenfunction cos(kappa*z) must vanish at z=h (the
        # truncation boundary) -- this is the actual defining property.
        np.testing.assert_allclose(np.cos(kappa * h), 0.0, atol=1e-12)

    def test_eigenvalues_reject_invalid_inputs(self) -> None:
        with pytest.raises(ValueError):
            bare_coil_axial_eigenvalues(0.0, 10)
        with pytest.raises(ValueError):
            bare_coil_axial_eigenvalues(1.0, 0)

    def test_coefficients_shape_matches_eigenvalues(self) -> None:
        coil = _thin_coil(0.025, 0.10, 100)
        h = 0.5
        kappa = bare_coil_axial_eigenvalues(h, 12)
        coeffs = bare_coil_coefficients(coil, h, kappa)
        assert coeffs.shape == kappa.shape
        assert np.all(np.isfinite(coeffs))


# ---------------------------------------------------------------------------
# Input validation / documented scope limits
# ---------------------------------------------------------------------------


class TestScopeAndValidation:
    def test_rejects_points_inside_the_winding_cross_section(self) -> None:
        """The field inside the coil's own winding (r1 < rho < r2) is out
        of scope for Phase 2b (see module docstring) -- must raise, not
        silently return a wrong/undefined value."""
        coil = _thin_coil(0.025, 0.10, 100)
        h = 5.0 * coil.length
        rho_inside_winding = (coil.inner_radius + coil.outer_radius) / 2.0

        with pytest.raises(ValueError, match="winding"):
            bare_coil_b_field(coil, 10.0, h, rho_inside_winding, 0.0)

        with pytest.raises(ValueError, match="winding"):
            bare_coil_vector_potential(coil, 10.0, h, rho_inside_winding, 0.0)

    def test_rejects_nonpositive_current(self) -> None:
        coil = _thin_coil(0.025, 0.10, 100)
        with pytest.raises(ValueError):
            bare_coil_b_field(coil, -1.0, 0.5, 0.0, 0.0)
        with pytest.raises(ValueError):
            bare_coil_vector_potential(coil, 0.0, 0.5, 0.0, 0.0)

    def test_boundary_points_are_included_in_bore_and_outside_regions(self) -> None:
        """rho == inner_radius and rho == outer_radius are the edges of
        the two defined ('air') regions, not the excluded winding
        interior -- must not raise."""
        coil = _thin_coil(0.025, 0.10, 100)
        h = 5.0 * coil.length
        bare_coil_b_field(coil, 10.0, h, coil.inner_radius, 0.0)
        bare_coil_b_field(coil, 10.0, h, coil.outer_radius, 0.0)


class TestThickWindingModelGap:
    def test_thick_winding_shows_expected_model_gap(self) -> None:
        """A genuinely thick winding (outer_radius = 1.4x inner_radius) is
        physically NOT the same current distribution as the closed-form
        thin-current-sheet model, so a larger residual discrepancy here is
        expected and correct -- not a regression. This test documents that
        expectation explicitly instead of leaving it as tribal knowledge.
        """
        coil = SolenoidCoil(
            inner_radius=0.025, outer_radius=0.035, length=0.10, turns=100, wire_diameter=0.005
        )
        current = 10.0
        h = 5.0 * coil.length
        z = np.linspace(-0.45, 0.45, 7) * coil.length
        # On-axis evaluation is nearly insensitive to how the current is
        # spread radially at fixed mean radius (the leading correction is
        # second-order in winding thickness), so the model gap barely
        # shows up there -- use an off-axis, outside-the-coil point close
        # to the winding instead, where the gap is genuinely visible.
        rho = np.full_like(z, 1.8 * coil.outer_radius)

        _, b_z_true = solenoid_b_field_off_axis(coil, current, rho, z)
        errors = []
        for num_eigenvalues in (80, 200, 400):
            _, b_z = bare_coil_b_field(
                coil, current, h, rho, z, num_eigenvalues=num_eigenvalues
            )
            errors.append(_max_relative_error(b_z, b_z_true))

        # A real (not a bug) discrepancy driven by the winding-thickness
        # model difference: noticeably larger than the thin-coil cases
        # above (< 1-2%), but still a modest fraction (~few percent) --
        # and, crucially, it does NOT shrink with more eigenvalues (that
        # is what distinguishes a real model-difference floor from
        # under-converged truncation error).
        assert 0.01 < errors[-1] < 0.10, (
            f"expected a modest, real model-difference discrepancy for a "
            f"thick winding, got {errors[-1]:.4%}"
        )
        assert errors[0] == pytest.approx(errors[-1], rel=0.05), (
            f"model-difference discrepancy should NOT shrink with more "
            f"eigenvalues (it's not a truncation-error effect), got {errors}"
        )
