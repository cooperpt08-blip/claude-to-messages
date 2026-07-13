"""Shared data types for the prediction-market edge bot."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class Quote:
    """A normalized snapshot of one market's prices on one platform.

    Prices are always in probability space (0.0-1.0), regardless of whether
    the source platform quotes cents, dollars, or a raw probability.
    """

    source: str
    market_id: str
    question: str
    yes_bid: Optional[float]
    yes_ask: Optional[float]
    no_bid: Optional[float]
    no_ask: Optional[float]
    volume: Optional[float] = None
    url: Optional[str] = None
    # False for AMM-style markets (e.g. Manifold) that report a single
    # probability rather than a real bid/ask order book.
    has_order_book: bool = True
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def yes_mid(self) -> Optional[float]:
        if self.yes_bid is None or self.yes_ask is None:
            return None
        return (self.yes_bid + self.yes_ask) / 2

    @property
    def no_mid(self) -> Optional[float]:
        if self.no_bid is None or self.no_ask is None:
            return None
        return (self.no_bid + self.no_ask) / 2


@dataclass(frozen=True)
class MarketRef:
    """Pointer to one platform's version of a real-world market."""

    source: str
    params: dict


@dataclass(frozen=True)
class MarketGroup:
    """A set of markets on different platforms that resolve on the same
    real-world question, and are therefore comparable to each other."""

    name: str
    members: list


@dataclass(frozen=True)
class CrossPlatformEdge:
    """Opportunity to sell Yes on one platform for more than it costs to
    buy Yes on another -- a cross-platform arbitrage/mispricing signal."""

    group: str
    sell_source: str
    sell_price: float
    buy_source: str
    buy_price: float

    @property
    def edge(self) -> float:
        return self.sell_price - self.buy_price


@dataclass(frozen=True)
class ComplementaryEdge:
    """Opportunity within a single platform: buying both Yes and No costs
    less than the $1 guaranteed payout, or selling both nets more than $1."""

    group: str
    source: str
    side: str  # "buy" (yes_ask + no_ask < 1) or "sell" (yes_bid + no_bid > 1)
    yes_price: float
    no_price: float

    @property
    def cost(self) -> float:
        return self.yes_price + self.no_price

    @property
    def edge(self) -> float:
        if self.side == "buy":
            return 1.0 - self.cost
        return self.cost - 1.0
