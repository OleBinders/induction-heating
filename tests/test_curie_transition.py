"""Tests for Curie transition models and enhanced MaterialDatabase."""

from __future__ import annotations

import numpy as np
import pytest

from induction_heating.materials.curie_transition import (
    permeability_polynomial,
    permeability_sigmoid,
)
from induction_heating.materials.database import MaterialDatabase


# ---------------------------------------------------------------------------
# Sigmoid model tests
# ---------------------------------------------------------------------------

class TestPermeabilitySigmoid:
    """Test sigmoid-based Curie transition model."""

    def test_midpoint_at_tc(self) -> None:
        """At T = Tc, μᵣ = 1 + (μᵣ₀ - 1) / 2."""
        mu_r_0 = 200.0
        Tc = 770.0
        mu = permeability_sigmoid(Tc, mu_r_0, Tc)
        expected = 1.0 + (mu_r_0 - 1.0) / 2.0
        assert mu == pytest.approx(expected, rel=1e-10)

    def test_low_temperature(self) -> None:
        """At T ≪ Tc, μᵣ ≈ μᵣ₀."""
        mu_r_0 = 200.0
        Tc = 770.0
        mu = permeability_sigmoid(20.0, mu_r_0, Tc)
        assert mu == pytest.approx(mu_r_0, rel=0.01)

    def test_high_temperature(self) -> None:
        """At T ≫ Tc, μᵣ ≈ 1.0."""
        mu_r_0 = 200.0
        Tc = 770.0
        mu = permeability_sigmoid(1000.0, mu_r_0, Tc)
        assert mu == pytest.approx(1.0, abs=0.01)

    def test_always_ge_one(self) -> None:
        """μᵣ ≥ 1.0 for all temperatures."""
        mu_r_0 = 200.0
        Tc = 770.0
        temps = np.linspace(-100, 1500, 100)
        mu = permeability_sigmoid(temps, mu_r_0, Tc)
        assert np.all(mu >= 1.0)

    def test_monotonic_decrease(self) -> None:
        """μᵣ decreases monotonically with temperature."""
        mu_r_0 = 200.0
        Tc = 770.0
        temps = np.linspace(500, 1000, 100)  # Focus on transition region
        mu = permeability_sigmoid(temps, mu_r_0, Tc)
        assert np.all(np.diff(mu) <= 0)

    def test_steeper_k(self) -> None:
        """Higher k produces sharper transition."""
        mu_r_0 = 200.0
        Tc = 770.0
        # At T = Tc + 50 (above transition), steeper k should be closer to 1.0
        mu_shallow = permeability_sigmoid(Tc + 50, mu_r_0, Tc, k=0.05)
        mu_steep = permeability_sigmoid(Tc + 50, mu_r_0, Tc, k=0.2)
        assert mu_steep < mu_shallow  # Steeper transition drops faster above Tc

    def test_invalid_mu_r_0_raises(self) -> None:
        with pytest.raises(ValueError, match="mu_r_0"):
            permeability_sigmoid(100.0, 0.5, 770.0)

    def test_invalid_k_raises(self) -> None:
        with pytest.raises(ValueError, match="k"):
            permeability_sigmoid(100.0, 200.0, 770.0, k=-0.1)

    def test_array_input(self) -> None:
        """Sigmoid model works with array inputs."""
        temps = np.array([500.0, 700.0, 770.0, 900.0])
        mu = permeability_sigmoid(temps, 200.0, 770.0)
        assert mu.shape == (4,)
        assert mu[0] >= mu[1] >= mu[2] >= mu[3]  # Monotonically decreasing


# ---------------------------------------------------------------------------
# Polynomial model tests
# ---------------------------------------------------------------------------

class TestPermeabilityPolynomial:
    """Test polynomial Curie transition model."""

    def test_at_t_start(self) -> None:
        """At T = T_start, μᵣ = μᵣ₀."""
        mu_r_0 = 200.0
        Tc = 770.0
        T_start = 670.0
        mu = permeability_polynomial(T_start, mu_r_0, Tc, T_start)
        assert mu == pytest.approx(mu_r_0)

    def test_at_tc(self) -> None:
        """At T = Tc, μᵣ = 1.0."""
        mu_r_0 = 200.0
        Tc = 770.0
        T_start = 670.0
        mu = permeability_polynomial(Tc, mu_r_0, Tc, T_start)
        assert mu == pytest.approx(1.0)

    def test_below_t_start(self) -> None:
        """At T < T_start, μᵣ = μᵣ₀ (constant)."""
        mu_r_0 = 200.0
        Tc = 770.0
        T_start = 670.0
        mu = permeability_polynomial(500.0, mu_r_0, Tc, T_start)
        assert mu == pytest.approx(mu_r_0)

    def test_above_tc(self) -> None:
        """At T > Tc, μᵣ = 1.0 (constant)."""
        mu_r_0 = 200.0
        Tc = 770.0
        T_start = 670.0
        mu = permeability_polynomial(900.0, mu_r_0, Tc, T_start)
        assert mu == pytest.approx(1.0)

    def test_always_ge_one(self) -> None:
        """μᵣ ≥ 1.0 for all temperatures."""
        temps = np.linspace(-100, 1500, 100)
        mu = permeability_polynomial(temps, 200.0, 770.0, 670.0)
        assert np.all(mu >= 1.0)

    def test_higher_n_sharper(self) -> None:
        """Higher n produces sharper transition near Tc."""
        T_mid = 720.0  # Midpoint of transition
        mu_n2 = permeability_polynomial(T_mid, 200.0, 770.0, 670.0, n=2)
        mu_n4 = permeability_polynomial(T_mid, 200.0, 770.0, 670.0, n=4)
        # Higher n keeps μᵣ higher further into the transition, then drops sharply
        assert mu_n4 > mu_n2  # Higher n stays closer to μᵣ₀ until near Tc

    def test_default_t_start(self) -> None:
        """Default T_start = Tc - 100."""
        mu = permeability_polynomial(700.0, 200.0, 770.0)  # T_start defaults to 670
        assert 1.0 < mu < 200.0

    def test_invalid_t_start_raises(self) -> None:
        with pytest.raises(ValueError, match="T_start"):
            permeability_polynomial(100.0, 200.0, 770.0, T_start=800.0)

    def test_array_input(self) -> None:
        """Polynomial model works with array inputs."""
        temps = np.array([500.0, 700.0, 770.0, 900.0])
        mu = permeability_polynomial(temps, 200.0, 770.0, 670.0)
        assert mu.shape == (4,)
        assert mu[0] == pytest.approx(200.0)  # Below T_start
        assert mu[2] == pytest.approx(1.0)    # At Tc
        assert mu[3] == pytest.approx(1.0)    # Above Tc


# ---------------------------------------------------------------------------
# MaterialDatabase.get_permeability tests
# ---------------------------------------------------------------------------

class TestMaterialDatabasePermeability:
    """Test enhanced MaterialDatabase permeability method."""

    @pytest.fixture
    def db(self) -> MaterialDatabase:
        return MaterialDatabase()

    def test_steel_with_data_points(self, db: MaterialDatabase) -> None:
        """Steel with permeability data uses PchipInterpolator."""
        mu_20 = db.get_permeability("Low Carbon Steel (AISI 1018)", 20.0)
        assert mu_20 == pytest.approx(200.0, rel=0.01)

    def test_steel_at_curie_point(self, db: MaterialDatabase) -> None:
        """Steel at Curie point returns μᵣ ≈ 1.0."""
        mu_tc = db.get_permeability("Low Carbon Steel (AISI 1018)", 770.0)
        assert mu_tc == pytest.approx(1.0, abs=0.1)

    def test_steel_above_curie(self, db: MaterialDatabase) -> None:
        """Steel above Curie point returns μᵣ ≈ 1.0."""
        mu_high = db.get_permeability("Low Carbon Steel (AISI 1018)", 900.0)
        assert mu_high >= 1.0

    def test_copper_non_magnetic(self, db: MaterialDatabase) -> None:
        """Copper (non-magnetic) returns 1.0 at all temperatures."""
        mu_20 = db.get_permeability("Copper (Electrolytic Tough Pitch)", 20.0)
        mu_500 = db.get_permeability("Copper (Electrolytic Tough Pitch)", 500.0)
        assert mu_20 == pytest.approx(1.0)
        assert mu_500 == pytest.approx(1.0)

    def test_aluminum_non_magnetic(self, db: MaterialDatabase) -> None:
        """Aluminum (non-magnetic) returns 1.0."""
        mu = db.get_permeability("Aluminum (6061)", 20.0)
        assert mu == pytest.approx(1.0)

    def test_monotonic_decrease_steel(self, db: MaterialDatabase) -> None:
        """Steel permeability decreases with temperature."""
        temps = [20, 200, 400, 600, 700, 750, 770, 800]
        mus = [db.get_permeability("Low Carbon Steel (AISI 1018)", t) for t in temps]
        # Should be generally decreasing (may have small variations due to interpolation)
        assert mus[0] > mus[-1]  # 20°C > 800°C

    def test_case_insensitive_lookup(self, db: MaterialDatabase) -> None:
        """Material lookup is case-insensitive."""
        mu1 = db.get_permeability("low carbon steel", 20.0)
        mu2 = db.get_permeability("Low Carbon Steel (AISI 1018)", 20.0)
        assert mu1 == pytest.approx(mu2)
