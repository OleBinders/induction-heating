"""Material property validation tests.

The shipped material data files (src/induction_heating/materials/data/*.json)
are attributed to:
- Rudnev, "Handbook of Induction Heating" (CRC Press, 2003)
- Zinn & Semiatin, "Elements of Induction Heating" (ASM International, 1988)

TestMaterialDataRegression below checks the *shipped data* at its own knot
points -- it will catch accidental data corruption, but every temperature it
checks is an exact knot in the source JSON, so a CubicSpline/PchipInterpolator
returns its own input unchanged there. It is NOT an independent check against
the cited literature (no page/table cross-reference is verified here), and it
would pass even if the knot values themselves were wrong.

TestInterpolationSanity is the independent check: it probes temperatures
*between* knots, where the interpolator's output is not a foregone conclusion,
and asserts properties that must hold for any physically reasonable resistivity
curve regardless of the exact literature numbers -- monotonic increase with
temperature, and no spline overshoot past the bounding knot values.
"""

from __future__ import annotations

import pytest

from induction_heating.materials.database import MaterialDatabase


class TestMaterialDataRegression:
    """Regression-check the shipped data at its own knot points.

    See the module docstring: these are NOT independent literature validation.
    """

    @pytest.fixture
    def db(self) -> MaterialDatabase:
        return MaterialDatabase()

    # Low Carbon Steel (AISI 1018) resistivity values
    # Source: Rudnev Handbook, Table 3.1

    def test_steel_resistivity_20c(self, db: MaterialDatabase) -> None:
        """Steel resistivity at 20°C: 1.43e-7 Ω·m ± 5%."""
        rho = db.get_property_at_temperature("Low Carbon Steel (AISI 1018)", "resistivity", 20.0)
        assert rho == pytest.approx(1.43e-7, rel=0.05)

    def test_steel_resistivity_400c(self, db: MaterialDatabase) -> None:
        """Steel resistivity at 400°C: 4.35e-7 Ω·m ± 5%."""
        rho = db.get_property_at_temperature("Low Carbon Steel (AISI 1018)", "resistivity", 400.0)
        assert rho == pytest.approx(4.35e-7, rel=0.05)

    def test_steel_resistivity_800c(self, db: MaterialDatabase) -> None:
        """Steel resistivity at 800°C: 8.50e-7 Ω·m ± 5%."""
        rho = db.get_property_at_temperature("Low Carbon Steel (AISI 1018)", "resistivity", 800.0)
        assert rho == pytest.approx(8.50e-7, rel=0.05)

    # Copper resistivity values
    # Source: Standard reference data

    def test_copper_resistivity_20c(self, db: MaterialDatabase) -> None:
        """Copper resistivity at 20°C: 1.68e-8 Ω·m ± 5%."""
        rho = db.get_property_at_temperature("Copper (Electrolytic Tough Pitch)", "resistivity", 20.0)
        assert rho == pytest.approx(1.68e-8, rel=0.05)

    def test_copper_resistivity_500c(self, db: MaterialDatabase) -> None:
        """Copper resistivity at 500°C: 4.50e-8 Ω·m ± 5%."""
        rho = db.get_property_at_temperature("Copper (Electrolytic Tough Pitch)", "resistivity", 500.0)
        assert rho == pytest.approx(4.50e-8, rel=0.05)

    # Aluminum resistivity values
    # Source: Standard reference data

    def test_aluminum_resistivity_20c(self, db: MaterialDatabase) -> None:
        """Aluminum resistivity at 20°C: 2.65e-8 Ω·m ± 5%."""
        rho = db.get_property_at_temperature("Aluminum (6061)", "resistivity", 20.0)
        assert rho == pytest.approx(2.65e-8, rel=0.05)

    # Steel permeability at Curie point
    # Source: Physics of Curie transition

    def test_steel_permeability_at_curie(self, db: MaterialDatabase) -> None:
        """Steel permeability at Curie point (770°C): 1.0 ± 0.1."""
        mu = db.get_permeability("Low Carbon Steel (AISI 1018)", 770.0)
        assert mu == pytest.approx(1.0, abs=0.1)


class TestInterpolationSanity:
    """Independent checks at temperatures between data knot points.

    Unlike TestMaterialDataRegression, these don't ask "does the interpolator
    return what's in the JSON" (trivially true at a knot) -- they ask "is the
    interpolated curve physically reasonable" at points where the answer isn't
    already fixed by the input data.
    """

    @pytest.fixture
    def db(self) -> MaterialDatabase:
        return MaterialDatabase()

    @pytest.mark.parametrize(
        "material,knot_below,knot_above",
        [
            ("Low Carbon Steel (AISI 1018)", 200.0, 400.0),
            ("Low Carbon Steel (AISI 1018)", 600.0, 700.0),
            ("Copper (Electrolytic Tough Pitch)", 20.0, 500.0),
        ],
    )
    def test_resistivity_monotonic_between_knots(
        self, db: MaterialDatabase, material: str, knot_below: float, knot_above: float
    ) -> None:
        """Resistivity must increase monotonically as temperature rises between knots."""
        midpoint = (knot_below + knot_above) / 2.0
        rho_below = db.get_property_at_temperature(material, "resistivity", knot_below)
        rho_mid = db.get_property_at_temperature(material, "resistivity", midpoint)
        rho_above = db.get_property_at_temperature(material, "resistivity", knot_above)
        assert rho_below < rho_mid < rho_above

    @pytest.mark.parametrize(
        "material,knot_below,knot_above",
        [
            ("Low Carbon Steel (AISI 1018)", 200.0, 400.0),
            ("Low Carbon Steel (AISI 1018)", 600.0, 700.0),
            ("Copper (Electrolytic Tough Pitch)", 20.0, 500.0),
        ],
    )
    def test_resistivity_no_spline_overshoot(
        self, db: MaterialDatabase, material: str, knot_below: float, knot_above: float
    ) -> None:
        """Interpolated resistivity must stay within the bounding knot values.

        A cubic spline can overshoot past its control points near a change in
        curvature; resistivity vs. temperature for these metals has no physical
        mechanism to dip or spike between measured points, so an overshoot here
        would indicate a genuine interpolation artifact, not real material behavior.
        """
        rho_below = db.get_property_at_temperature(material, "resistivity", knot_below)
        rho_above = db.get_property_at_temperature(material, "resistivity", knot_above)
        for frac in (0.1, 0.3, 0.5, 0.7, 0.9):
            t = knot_below + frac * (knot_above - knot_below)
            rho_t = db.get_property_at_temperature(material, "resistivity", t)
            assert rho_below <= rho_t <= rho_above
