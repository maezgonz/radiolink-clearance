"""Command-line interface for the radiolink clearance suite."""

from __future__ import annotations

import argparse
import sys

from .core import RadioLinkEngine
from .io import load_profile_from_csv, load_profile_from_excel
from .optimizer import TowerOptimizer
from .plotting import plot_link_profile


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="RadioLink Clearance Suite (ITU-R P.530-18)")
    parser.add_argument("--file", required=True, help="Terrain profile (CSV or .xlsx)")
    parser.add_argument("--sheet", type=int, default=1, help="Excel sheet number (1-based)")
    parser.add_argument("--freq", type=float, required=True, help="Frequency (GHz)")
    parser.add_argument("--h1", type=float, required=True, help="TX antenna height (m)")
    parser.add_argument("--h2", type=float, required=True, help="RX antenna height (m)")
    parser.add_argument("--k", type=float, default=4.0 / 3.0, help="K factor (default: 4/3)")
    parser.add_argument("--rf", type=float, default=0.6, help="Target C/R1 ratio (default: 0.60)")
    parser.add_argument("--optimize", action="store_true", help="Run tower optimization if obstructed")
    parser.add_argument("--plot", default=None, help="Save the profile figure to this path")
    return parser.parse_args()


def main() -> int:
    """Entry point. Returns a process exit code."""
    args = parse_args()
    try:
        if args.file.lower().endswith(('.xlsx', '.xls')):
            df = load_profile_from_excel(args.file, args.sheet)
        else:
            df = load_profile_from_csv(args.file)

        engine = RadioLinkEngine(df, args.freq, args.h1, args.h2, args.k, args.rf)
        summary = engine.get_summary()

        print("=" * 73)
        print("           RADIOLINK CLEARANCE ANALYSIS REPORT           ")
        print("=" * 73)
        print(f"Path Length        : {summary.d_total_km:.2f} km")
        print(f"Frequency          : {summary.freq_ghz:.2f} GHz")
        print(f"Atmospheric Factor : K = {summary.k_factor:.3f}")
        print(f"Antenna Heights    : h1 = {args.h1:.1f} m | h2 = {args.h2:.1f} m")
        print(f"Target Clearance   : {args.rf * 100:.0f}% of 1st Fresnel zone")
        print("-" * 73)
        print(f"Critical Obstacle  : Distance = {summary.crit_dist_km:.2f} km | Elevation = {summary.crit_cota_total_m:.1f} m")
        print(f"Net Clearance (C)  : {summary.crit_clearance_m:.2f} m")
        print(f"Clearance Ratio    : {summary.crit_ratio * 100:.1f}% R1")
        print(f"Status             : {summary.status_label}")
        print("=" * 73)

        if args.optimize and not summary.is_compliant:
            optimizer = TowerOptimizer(engine)
            h1_opt, h2_opt = optimizer.solve(strategy="balanced")
            print(f"Optimization (balanced towers): h1 = {h1_opt:.1f} m, h2 = {h2_opt:.1f} m")

        if args.plot:
            plot_link_profile(engine, save_path=args.plot)
            print(f"Profile visualization saved to {args.plot}")

        return 0 if summary.is_compliant else 1
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
