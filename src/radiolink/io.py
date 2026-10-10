"""Data ingestion for the radiolink clearance suite (CSV + Excel)."""

from __future__ import annotations

import pandas as pd


def load_profile_from_csv(path: str) -> pd.DataFrame:
    """Load a terrain profile from a CSV file.

    The CSV must contain ``dist_km`` and ``cota_m`` columns; an optional
    ``obst_m`` column adds artificial obstacles on top of the terrain.

    Args:
        path: Destination CSV path.

    Returns:
        DataFrame with the terrain profile.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If required columns are missing.
    """
    frame = pd.read_csv(path)
    if not {"dist_km", "cota_m"}.issubset(frame.columns):
        raise ValueError("CSV must contain 'dist_km' and 'cota_m' columns")
    return frame


def load_profile_from_excel(path: str, sheet_num: int = 1) -> pd.DataFrame:
    """Load a terrain profile from an Excel workbook.

    Expected columns: ``dist_km`` and ``cota_m`` (plus optional ``obst_m``).
    Works with the 022/023 exercise sheets of the course as well — the
    generic column layout is what matters.

    Args:
        path: Destination Excel path.
        sheet_num: 1-based sheet index to read.

    Returns:
        DataFrame with the terrain profile.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If required columns are missing.
    """
    frame = pd.read_excel(path, sheet_name=sheet_num - 1)
    if not {"dist_km", "cota_m"}.issubset(frame.columns):
        raise ValueError("Excel must contain 'dist_km' and 'cota_m' columns")
    return frame
