"""TowerOptimizer: solve minimum antenna heights to meet the clearance target."""

from __future__ import annotations

from .core import RadioLinkEngine


class TowerOptimizer:
    """Solve the minimum antenna heights needed for the compliance target.

    Args:
        engine: The RadioLinkEngine with the link profile.
    """

    def __init__(self, engine: RadioLinkEngine) -> None:
        if not isinstance(engine, RadioLinkEngine):
            raise TypeError("engine must be a RadioLinkEngine")
        self.engine = engine

    def solve(self, strategy: str = "balanced", tolerance_m: float = 0.5) -> tuple[float, float]:
        """Return the minimum tower heights (h1, h2) that meet the criteria.

        For the balanced strategy, the same height increment is applied to
        both antennas. The clearance at the critical point grows linearly with
        the height increment (ray slope is linear), so a bisection over the
        increment converges quickly to the minimum feasible heights.

        Args:
            strategy: ``"balanced"`` — identical increment at both ends.
            tolerance_m: Convergence tolerance for the bisection (m).

        Returns:
            Tuple of (h1_new, h2_new) antenna heights in meters.

        Raises:
            ValueError: If no feasible solution is found within 500 m.
        """
        if strategy != "balanced":
            raise ValueError("only 'balanced' strategy is implemented")

        h1_0, h2_0 = self.engine.h1_m, self.engine.h2_m

        def feasible(delta_h: float) -> bool:
            test = RadioLinkEngine(
                self.engine.df,
                self.engine.freq_ghz,
                h1_0 + delta_h,
                h2_0 + delta_h,
                self.engine.k_factor,
                self.engine.target_ratio,
            )
            return test.get_summary().is_compliant

        if feasible(0.0):
            return h1_0, h2_0

        low, high = 0.0, 500.0
        for _ in range(60):
            mid = (low + high) / 2.0
            if feasible(mid):
                high = mid
            else:
                low = mid
            if high - low < tolerance_m:
                break

        if not feasible(high):
            raise ValueError("no feasible solution within 500 m")

        return h1_0 + high, h2_0 + high
