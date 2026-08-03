"""Material property validation tests against published reference values.

Reference values from:
- Rudnev, "Handbook of Induction Heating" (CRC Press, 2003)
- Zinn & Semiatin, "Elements of Induction Heating" (ASM International, 1988)
"""

from __future__ import annotations

import pytest

from induction_heating.materials.database import MaterialDatabase


class TestMaterialPropertyValidation:
    """Validate material properties against published reference values."""

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
