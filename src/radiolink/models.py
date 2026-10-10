"""Immutable data-transfer models for the radiolink clearance suite."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClearancePoint:
    """One point along the link profile with its clearance metrics.

    Attributes:
        dist_km: Progressive distance from the transmitter (km).
        terrain_m: Terrain elevation above sea level (m).
        bulge_m: Earth-bulge offset at this point (m).
        effective_terrain_m: Terrain + bulge + artificial obstacle (m).
        ray_m: Ray height above the horizontal reference (m).
        clearance_m: Net clearance between ray and effective terrain (m).
        fresnel_r1_m: Fresnel first-zone radius at this point (m).
        ratio: Clearance / R1 fraction.
    """

    dist_km: float
    terrain_m: float
    bulge_m: float
    effective_terrain_m: float
    ray_m: float
    clearance_m: float
    fresnel_r1_m: float
    ratio: float


@dataclass(frozen=True)
class ClearanceSummary:
    """Link-wide summary of the clearance analysis.

    Attributes:
        d_total_km: Total link length (km).
        freq_ghz: Operation frequency (GHz).
        k_factor: Atmospheric equivalent-earth factor.
        crit_dist_km: Distance of the critical obstacle (km).
        crit_cota_total_m: Effective elevation of the critical point (m).
        crit_clearance_m: Net clearance at the critical obstacle (m).
        crit_ratio: Clearance ratio C/R1 at the critical obstacle.
        is_compliant: Whether the entire link meets the criteria.
        status_label: Human-readable result label.
    """

    d_total_km: float
    freq_ghz: float
    k_factor: float
    crit_dist_km: float
    crit_cota_total_m: float
    crit_clearance_m: float
    crit_ratio: float
    is_compliant: bool
    status_label: str
