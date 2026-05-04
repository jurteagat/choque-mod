"""Unit tests for physics module."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# Make src/ importable without packaging boilerplate.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from physics import (  # noqa: E402
    ais_category,
    fatality_probability,
    impact_velocity,
    kinetic_energy,
    net_acceleration,
    resolve_mu_r,
    serious_injury_probability,
    simulate,
)


class TestNetAcceleration:

    def test_flat_surface_gives_zero(self):
        # On a flat road, friction beats zero gravity component.
        assert net_acceleration(0.0, 0.013) == 0.0

    def test_critical_slope_is_zero(self):
        # Exactly at tan θ = μ_r, net acceleration should be zero.
        mu_r = 0.013
        critical_deg = math.degrees(math.atan(mu_r))
        assert net_acceleration(critical_deg, mu_r) == pytest.approx(0.0, abs=1e-9)

    def test_steep_slope_positive(self):
        a = net_acceleration(10.0, 0.013)
        # Sanity: a must be between 0 and g.
        assert 0.0 < a < 9.81

    def test_negative_slope_raises(self):
        with pytest.raises(ValueError):
            net_acceleration(-1.0, 0.013)

    def test_negative_mu_raises(self):
        with pytest.raises(ValueError):
            net_acceleration(5.0, -0.01)


class TestImpactVelocity:

    def test_zero_distance(self):
        assert impact_velocity(2.0, 0.0) == 0.0

    def test_zero_acceleration(self):
        assert impact_velocity(0.0, 30.0) == 0.0

    def test_known_value(self):
        # v = sqrt(2 * 1 * 8) = 4 m/s
        assert impact_velocity(1.0, 8.0) == pytest.approx(4.0)

    def test_negative_distance_raises(self):
        with pytest.raises(ValueError):
            impact_velocity(1.0, -5.0)


class TestKineticEnergy:

    def test_known_value(self):
        # 0.5 * 2000 * 10^2 = 100_000 J
        assert kinetic_energy(2000.0, 10.0) == pytest.approx(100_000.0)

    def test_zero_velocity(self):
        assert kinetic_energy(2400.0, 0.0) == 0.0

    def test_non_positive_mass_raises(self):
        with pytest.raises(ValueError):
            kinetic_energy(0.0, 5.0)
        with pytest.raises(ValueError):
            kinetic_energy(-100.0, 5.0)


class TestProbabilities:

    def test_fatality_low_speed_near_zero(self):
        # 5 km/h should give a very low fatality probability.
        assert fatality_probability(5.0) < 0.01

    def test_fatality_monotonic(self):
        # Probability should grow with speed.
        assert (
            fatality_probability(20.0)
            < fatality_probability(50.0)
            < fatality_probability(100.0)
        )

    def test_serious_higher_than_fatal(self):
        # At most speeds, P(serious) >= P(fatal).
        for v in (20.0, 40.0, 60.0, 80.0):
            assert serious_injury_probability(v) >= fatality_probability(v)

    def test_prob_bounded_zero_one(self):
        for v in (0.0, 10.0, 50.0, 200.0, 10_000.0):
            p = fatality_probability(v)
            assert 0.0 <= p <= 1.0


class TestAIS:

    @pytest.mark.parametrize(
        "v_kmh, expected_band",
        [
            (5.0, "AIS 1"),
            (20.0, "AIS 1"),
            (30.0, "AIS 2"),
            (50.0, "AIS 3"),
            (80.0, "AIS 5"),
        ],
    )
    def test_buckets(self, v_kmh, expected_band):
        label, _ = ais_category(v_kmh)
        assert expected_band in label

    def test_negative_speed_raises(self):
        with pytest.raises(ValueError):
            ais_category(-1.0)


class TestSimulate:

    def test_default_case(self):
        # Defaults used by the app.
        result = simulate(
            slope_deg=5.0,
            distance_m=30.0,
            mass_kg=2400.0,
            surface_key="asfalto_seco",
        )
        assert result.will_roll is True
        # Expected ≈ 6.8 m/s at 5° after 30 m on dry asphalt.
        assert 5.0 < result.v_impact_mps < 9.0
        assert result.kinetic_energy_j > 0.0

    def test_mass_scales_energy_linearly(self):
        base = simulate(5.0, 30.0, 2400.0, "asfalto_seco")
        heavy = simulate(5.0, 30.0, 4800.0, "asfalto_seco")
        # Doubling mass doubles energy, velocity unchanged.
        assert heavy.v_impact_mps == pytest.approx(base.v_impact_mps)
        assert heavy.kinetic_energy_j == pytest.approx(2.0 * base.kinetic_energy_j)

    def test_flat_slope_does_not_roll(self):
        result = simulate(0.0, 30.0, 2400.0, "asfalto_seco")
        assert result.will_roll is False
        assert result.v_impact_mps == 0.0
        assert result.kinetic_energy_j == 0.0

    def test_shallow_slope_below_threshold_does_not_roll(self):
        # atan(0.013) ≈ 0.745° — 0.5° is below threshold.
        result = simulate(0.5, 30.0, 2400.0, "asfalto_seco")
        assert result.will_roll is False

    def test_unknown_surface_raises(self):
        with pytest.raises(KeyError):
            simulate(5.0, 30.0, 2400.0, "hielo")


class TestResolveMuR:

    def test_known(self):
        assert resolve_mu_r("asfalto_seco") > 0.0

    def test_unknown(self):
        with pytest.raises(KeyError):
            resolve_mu_r("desconocido")
