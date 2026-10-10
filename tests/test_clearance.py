"""Unit tests for the radiolink clearance suite (analytic references)."""

import numpy as np
import pandas as pd
import pytest

from radiolink import RadioLinkEngine, TowerOptimizer
from radiolink.core import STANDARD_K_FACTOR
from radiolink.io import load_profile_from_csv


def _flat_terrain(total_km: float, step_km: float, cota_m: float) -> pd.DataFrame:
    """Flat terrain helper for analytic tests."""
    xs = np.arange(0.0, total_km + step_km, step_km)
    return pd.DataFrame({"dist_km": xs, "cota_m": cota_m})


def test_fresnel_midpoint_analytic():
    """First-zone radius at the midpoint must match the analytic formula."""
    engine = RadioLinkEngine(_flat_terrain(10.0, 1.0, 150.0), freq_ghz=7.0, h1_m=60.0, h2_m=80.0)
    r1_mid = engine.fresnel_r1(np.array([5.0]))[0]
    expected = 17.32 * np.sqrt((5.0 * 5.0) / (7.0 * 10.0))
    assert abs(r1_mid - expected) < 1e-9


def test_bulge_formula_midpoint():
    """Earth bulge at the midpoint must match f = 0.0785 * d1 * d2 / K."""
    engine = RadioLinkEngine(_flat_terrain(10.0, 1.0, 150.0), freq_ghz=7.0, h1_m=60.0, h2_m=80.0, k_factor=STANDARD_K_FACTOR)
    bulge_mid = engine.bulge_m(np.array([5.0]))[0]
    expected = 0.0785 * 5.0 * 5.0 / STANDARD_K_FACTOR
    assert abs(bulge_mid - expected) < 1e-9


def test_compliance_compliant_flat_terrain():
    """Flat terrain with sufficient heights must be compliant."""
    engine = RadioLinkEngine(_flat_terrain(5.0, 0.5, 100.0), freq_ghz=7.0, h1_m=80.0, h2_m=80.0)
    summary = engine.get_summary()
    assert summary.is_compliant is True
    assert summary.status_label == "CUMPLE"


def test_compliance_obstructed_critical_obstacle():
    """A tall mid obstacle must be detected as the critical one."""
    df = _flat_terrain(10.0, 1.0, 100.0)
    df.loc[5, "cota_m"] = 220.0
    engine = RadioLinkEngine(df, freq_ghz=7.0, h1_m=60.0, h2_m=60.0)
    summary = engine.get_summary()
    assert summary.crit_dist_km == pytest.approx(5.0)


def test_optimizer_blocked_to_compliant():
    """The optimizer must turn a blocked link into a compliant one."""
    df = _flat_terrain(10.0, 1.0, 100.0)
    df.loc[5, "cota_m"] = 220.0
    blocked = RadioLinkEngine(df, freq_ghz=7.0, h1_m=60.0, h2_m=60.0)
    assert not blocked.get_summary().is_compliant

    h1_opt, h2_opt = TowerOptimizer(blocked).solve(strategy="balanced")
    assert h1_opt == pytest.approx(h2_opt)
    fixed = RadioLinkEngine(df, freq_ghz=7.0, h1_m=h1_opt, h2_m=h2_opt)
    assert fixed.get_summary().is_compliant is True


def test_io_csv_load():
    """CSV ingestion must preserve the profile structure."""
    frame = load_profile_from_csv("data/sample_profile.csv")
    assert {"dist_km", "cota_m"}.issubset(frame.columns)
    assert len(frame) > 0
