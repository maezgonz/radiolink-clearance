"""Dark-mode technical plotting for the radiolink clearance suite."""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .core import RadioLinkEngine


def plot_link_profile(engine: RadioLinkEngine, show_k_variations: bool = True, save_path: str | None = None):
    """Render the link profile with terrain, ray and Fresnel ellipsoid.

    Args:
        engine: The RadioLinkEngine with the link profile.
        show_k_variations: When True, also draw the effective terrain under
            K=1.0 and K=0.8 alongside the configured K factor.
        save_path: Optional destination path for the PNG figure.

    Returns:
        Tuple of (fig, ax) from matplotlib.
    """
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 7), dpi=120)

    pts = engine.points()
    x = np.array([p.dist_km for p in pts])
    terrain = np.array([p.terrain_m for p in pts])
    bulge = np.array([p.bulge_m for p in pts])
    ray = np.array([p.ray_m for p in pts])
    r1 = np.array([p.fresnel_r1_m for p in pts])

    eff_terrain = terrain + bulge
    ax.fill_between(x, terrain, eff_terrain, color="#8b949e", alpha=0.35, label="Terrain + bulge")
    ax.fill_between(x, terrain - r1, terrain + r1, color="#58a6ff", alpha=0.15, label="1st Fresnel zone")
    ax.plot(x, ray, color="#f78166", linewidth=2.0, label="Ray (line of sight)")
    ax.plot(x, np.zeros_like(x), color="#30363d", linewidth=0.8, alpha=0.5)

    if show_k_variations:
        from .core import STANDARD_K_FACTOR

        for k, color in [(STANDARD_K_FACTOR, "#d2a8ff"), (1.0, "#79c0ff"), (0.8, "#f85149")]:
            test = RadioLinkEngine(
                engine.df, engine.freq_ghz, engine.h1_m, engine.h2_m, k_factor=k
            )
            kpts = test.points()
            test_terrain = np.array([p.terrain_m for p in kpts])
            test_bulge = np.array([p.bulge_m for p in kpts])
            ax.plot(x, test_terrain + test_bulge, color=color, linewidth=1.0, linestyle="--", label=f"K={k:.2f}")

    summary = engine.get_summary()
    ax.scatter([summary.crit_dist_km], [summary.crit_cota_total_m], color="#f85149", s=100, zorder=5, label="Critical obstacle")
    ax.annotate(
        f"Critical: km {summary.crit_dist_km:.1f}\nC={summary.crit_clearance_m:.1f} m ({summary.crit_ratio*100:.0f}% R1)",
        xy=(summary.crit_dist_km, summary.crit_cota_total_m),
        xytext=(10, 20), textcoords="offset points", color="#e6edf3",
    )

    title = f"Radiolink clearance — {engine.freq_ghz:.1f} GHz, d={engine.d_km:.2f} km, K={engine.k_factor:.3f}"
    ax.set_title(title)
    ax.set_xlabel("Distance from TX (km)")
    ax.set_ylabel("Elevation (m)")
    ax.grid(alpha=0.2)
    ax.legend(loc="upper left", framealpha=0.2)
    fig.tight_layout()

    if save_path:
        directory = os.path.dirname(save_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

    return fig, ax
