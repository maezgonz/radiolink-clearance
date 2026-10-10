"""RadioLinkEngine: the mathematical core of the clearance suite.

Implements the ITU-R P.453 tropospheric refraction model (equivalent earth
factor K), the Huygens-Fresnel diffraction model (first-zone radius), and the
ITU-R P.530-18 clearance criteria for terrestrial microwave links.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .models import ClearancePoint, ClearanceSummary

EARTH_RADIUS_KM = 6370.0
STANDARD_K_FACTOR = 4.0 / 3.0


class RadioLinkEngine:
    """Clearance analysis engine for a microwave radiolink profile.

    Args:
        df_terrain: DataFrame with ``dist_km`` and ``cota_m`` columns, plus an
            optional ``obst_m`` column for artificial obstacles on top of the
            terrain (m).
        freq_ghz: Operation frequency in GHz.
        h1_m: Transmitter antenna height above ground (m).
        h2_m: Receiver antenna height above ground (m).
        k_factor: Atmospheric equivalent-earth factor (default 4/3).
        target_ratio: Compliance threshold for C/R1 (default 0.60 - 60%).
    """

    def __init__(
        self,
        df_terrain: pd.DataFrame,
        freq_ghz: float,
        h1_m: float,
        h2_m: float,
        k_factor: float = STANDARD_K_FACTOR,
        target_ratio: float = 0.60,
    ) -> None:
        if freq_ghz <= 0 or h1_m <= 0 or h2_m <= 0:
            raise ValueError("freq_ghz, h1_m and h2_m must be positive")
        if k_factor <= 0:
            raise ValueError("k_factor must be positive")
        if df_terrain.empty or not {"dist_km", "cota_m"}.issubset(df_terrain.columns):
            raise ValueError("df_terrain must contain 'dist_km' and 'cota_m' columns")

        self.df = df_terrain.reset_index(drop=True).copy()
        self.freq_ghz = float(freq_ghz)
        self.h1_m = float(h1_m)
        self.h2_m = float(h2_m)
        self.k_factor = float(k_factor)
        self.target_ratio = float(target_ratio)
        self.d_km = float(self.df["dist_km"].max())

    def ray_height(self, x_km: np.ndarray) -> np.ndarray:
        """Return the straight-ray height (m) at progressive distance x (km).

        The ray is a straight line from the transmitter antenna at x=0 to the
        receiver antenna at x=d_km.
        """
        y1 = float(self.df.loc[0, "cota_m"]) + self.h1_m
        y2 = float(self.df.loc[len(self.df) - 1, "cota_m"]) + self.h2_m
        return y1 + (y2 - y1) * (x_km / self.d_km)

    def bulge_m(self, x_km: np.ndarray) -> np.ndarray:
        """Return the earth-bulge offset (m) at progressive distance x (km).

        ``f(x) = 0.0785 * d1 * d2 / k_factor`` — the parabolic bulge of the
        earth surface toward the ray, which grows with distance and shrinks
        with the atmospheric factor.
        """
        d1 = x_km
        d2 = np.maximum(self.d_km - x_km, 0.0)
        return 0.0785 * d1 * d2 / self.k_factor

    def fresnel_r1(self, x_km: np.ndarray) -> np.ndarray:
        """Return the Fresnel first-zone radius (m) at progressive distance x (km).

        ``R1 = 17.32 * sqrt(d1 * d2 / (f_ghz * d_km))`` with x in km.
        """
        d1 = x_km
        d2 = np.maximum(self.d_km - x_km, 0.0)
        return 17.32 * np.sqrt(np.maximum(d1 * d2, 0.0) / (self.freq_ghz * self.d_km))

    def effective_terrain(self) -> np.ndarray:
        """Return terrain + bulge + artificial obstacles at every point (m)."""
        obs = self.df["obst_m"] if "obst_m" in self.df.columns else 0.0
        return self.df["cota_m"].to_numpy() + np.asarray(obs, dtype=float) + self.bulge_m(
            self.df["dist_km"].to_numpy()
        )

    def points(self) -> list[ClearancePoint]:
        """Return one ClearancePoint per profile row with all metrics."""
        x = self.df["dist_km"].to_numpy()
        terrain = self.df["cota_m"].to_numpy()
        bulge = self.bulge_m(x)
        eff_terrain = self.effective_terrain()
        ray = self.ray_height(x)
        clearance = ray - eff_terrain
        r1 = self.fresnel_r1(x)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(r1 > 0, clearance / r1, np.inf)

        return [
            ClearancePoint(
                dist_km=float(xi),
                terrain_m=float(ti),
                bulge_m=float(bi),
                effective_terrain_m=float(ei),
                ray_m=float(ri),
                clearance_m=float(ci),
                fresnel_r1_m=float(r1i),
                ratio=float(ratio_i),
            )
            for xi, ti, bi, ei, ri, ci, r1i, ratio_i in zip(
                x, terrain, bulge, eff_terrain, ray, clearance, r1, ratio, strict=True
            )
        ]

    def get_summary(self) -> ClearanceSummary:
        """Return the link-wide summary with the critical obstacle."""
        pts = self.points()
        interior = [p for p in pts if 0.0 < p.dist_km < self.d_km]
        if not interior:
            raise ValueError("link profile has no interior points")

        crit = min(interior, key=lambda p: p.ratio)
        is_compliant = crit.ratio >= self.target_ratio

        return ClearanceSummary(
            d_total_km=self.d_km,
            freq_ghz=self.freq_ghz,
            k_factor=self.k_factor,
            crit_dist_km=crit.dist_km,
            crit_cota_total_m=crit.effective_terrain_m,
            crit_clearance_m=crit.clearance_m,
            crit_ratio=crit.ratio,
            is_compliant=is_compliant,
            status_label="CUMPLE" if is_compliant else "OBSTRUIDO (NO CUMPLE)",
        )
