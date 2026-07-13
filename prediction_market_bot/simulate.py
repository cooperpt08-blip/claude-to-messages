"""Synthetic multi-platform quote generator, for exercising the scan ->
edge-detection -> backtest pipeline without hitting any live API.

Useful for demos, development, and tests: the real source adapters can't be
verified against live traffic from every environment (some sandboxes block
outbound access to these platforms entirely), so this gives an offline,
deterministic stand-in with the same `Quote` shape the real adapters
produce.
"""

import random
from datetime import datetime, timedelta, timezone

from .types import Quote

DEFAULT_SOURCES = ("polymarket", "kalshi", "predictit", "manifold")


def generate_synthetic_history(
    group_name: str = "synthetic-group",
    sources=DEFAULT_SOURCES,
    n_steps: int = 50,
    step_minutes: int = 15,
    spread: float = 0.01,
    mispricing_prob: float = 0.15,
    mispricing_size: float = 0.03,
    seed: int = None,
) -> list:
    """Returns a list of (timestamp, [Quote, ...]) steps: a shared "true"
    probability random-walks over time, each platform quotes it with its
    own noise and bid/ask spread, and occasionally one platform gets knocked
    off by `mispricing_size` to create a real, detectable edge."""
    rng = random.Random(seed)
    start = datetime.now(timezone.utc) - timedelta(minutes=step_minutes * n_steps)
    true_prob = 0.5
    history = []

    for step in range(n_steps):
        true_prob = min(0.95, max(0.05, true_prob + rng.gauss(0, 0.02)))
        timestamp = start + timedelta(minutes=step_minutes * step)

        quotes = []
        for source in sources:
            mid = true_prob + rng.gauss(0, 0.01)
            if rng.random() < mispricing_prob:
                mid += rng.choice([-1, 1]) * mispricing_size
            mid = min(0.98, max(0.02, mid))

            half_spread = spread / 2
            yes_bid = max(0.0, mid - half_spread)
            yes_ask = min(1.0, mid + half_spread)
            quotes.append(
                Quote(
                    source=source,
                    market_id=f"{source}-synthetic",
                    question=f"[synthetic] {group_name}",
                    yes_bid=round(yes_bid, 4),
                    yes_ask=round(yes_ask, 4),
                    no_bid=round(1.0 - yes_ask, 4),
                    no_ask=round(1.0 - yes_bid, 4),
                    fetched_at=timestamp,
                )
            )
        history.append((timestamp, quotes))

    return history
