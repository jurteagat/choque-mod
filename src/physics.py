"""Pure physics helpers for the rolling-truck impact simulator.

All functions are stateless and unit-checked in comments so they can be
reused from both the Shiny server and the test suite.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from constants import AIS_THRESHOLDS, G, ROSEN_SANDER_COEFS, SURFACE_MU_R


@dataclass(frozen=True)
class SimulationResult:
    """Container with every derived quantity the UI needs."""

    will_roll: bool
    acceleration: float           # m/s^2 along the slope
    v_impact_mps: float           # m/s
    v_impact_kmh: float           # km/h
    kinetic_energy_j: float       # J
    fatality_probability: float   # 0..1
    serious_injury_probability: float
    ais_label: str
    ais_color: str


def net_acceleration(slope_deg: float, mu_r: float) -> float:
    """Return net downhill acceleration (m/s^2) including rolling friction.

    If the slope is too shallow to overcome friction, the result is 0
    (the truck stays at rest).
    """
    # Guard against nonsensical inputs early — keeps downstream math simple.
    if slope_deg < 0 or mu_r < 0:
        raise ValueError("slope_deg and mu_r must be non-negative")

    theta = math.radians(slope_deg)
    a = G * (math.sin(theta) - mu_r * math.cos(theta))
    # Clamp to 0 so impact_velocity never sees a negative argument.
    return max(a, 0.0)


def impact_velocity(acceleration: float, distance_m: float) -> float:
    """Return impact speed (m/s) after rolling `distance_m` under `acceleration`.

    Uses v = sqrt(2·a·d) (kinematics, zero initial velocity).
    """
    if distance_m < 0:
        raise ValueError("distance_m must be non-negative")
    if acceleration <= 0.0 or distance_m == 0.0:
        return 0.0
    return math.sqrt(2.0 * acceleration * distance_m)


def kinetic_energy(mass_kg: float, velocity_mps: float) -> float:
    """Return kinetic energy (J) for a given mass and speed."""
    if mass_kg <= 0:
        raise ValueError("mass_kg must be positive")
    return 0.5 * mass_kg * velocity_mps**2


def _logistic(v_kmh: float, a: float, b: float) -> float:
    """Shared logistic used for both fatality and serious-injury curves."""
    # Clamp exponent to avoid overflow for very large/small speeds.
    z = a - b * v_kmh
    z = max(min(z, 50.0), -50.0)
    return 1.0 / (1.0 + math.exp(z))


def fatality_probability(v_kmh: float) -> float:
    """Probability of pedestrian fatality given vehicle impact speed in km/h."""
    return _logistic(
        v_kmh,
        ROSEN_SANDER_COEFS["a_fatal"],
        ROSEN_SANDER_COEFS["b_fatal"],
    )


def serious_injury_probability(v_kmh: float) -> float:
    """Probability of AIS3+ (serious) injury given impact speed in km/h."""
    return _logistic(
        v_kmh,
        ROSEN_SANDER_COEFS["a_serious"],
        ROSEN_SANDER_COEFS["b_serious"],
    )


def ais_category(v_kmh: float) -> tuple[str, str]:
    """Return (label, color) for the qualitative AIS band at `v_kmh`."""
    if v_kmh < 0:
        raise ValueError("v_kmh must be non-negative")
    # AIS_THRESHOLDS is ordered by upper bound — walk in order.
    for upper, label, color in AIS_THRESHOLDS:
        if v_kmh <= upper:
            return label, color
    # Unreachable because the last bucket is +inf, but keep mypy happy.
    return AIS_THRESHOLDS[-1][1], AIS_THRESHOLDS[-1][2]


def resolve_mu_r(surface_key: str) -> float:
    """Look up μ_r for a surface key; raise if unknown (surfaces are closed-set)."""
    if surface_key not in SURFACE_MU_R:
        raise KeyError(f"Unknown surface: {surface_key!r}")
    return SURFACE_MU_R[surface_key]


def simulate(
    slope_deg: float,
    distance_m: float,
    mass_kg: float,
    surface_key: str,
) -> SimulationResult:
    """Run the full simulation and return a SimulationResult.

    Centralising the call graph here lets the Shiny server consume a single
    reactive value and keeps the UI layer free of physics logic.
    """
    mu_r = resolve_mu_r(surface_key)
    a = net_acceleration(slope_deg, mu_r)
    will_roll = a > 0.0

    v_mps = impact_velocity(a, distance_m) if will_roll else 0.0
    v_kmh = v_mps * 3.6
    e_kin = kinetic_energy(mass_kg, v_mps) if will_roll else 0.0

    p_fatal = fatality_probability(v_kmh) if will_roll else 0.0
    p_serious = serious_injury_probability(v_kmh) if will_roll else 0.0
    ais_label, ais_color = ais_category(v_kmh)

    return SimulationResult(
        will_roll=will_roll,
        acceleration=a,
        v_impact_mps=v_mps,
        v_impact_kmh=v_kmh,
        kinetic_energy_j=e_kin,
        fatality_probability=p_fatal,
        serious_injury_probability=p_serious,
        ais_label=ais_label,
        ais_color=ais_color,
    )
