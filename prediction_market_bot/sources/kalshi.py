"""Kalshi adapter, backed by the public trade API.

Market data reads don't require authentication; set KALSHI_API_KEY if
Kalshi later locks this endpoint down further.
API docs: https://trading-api.readme.io/reference/
"""

from .. import config
from ..types import Quote
from .base import SourceError, get_json, to_float

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


def _headers():
    if config.KALSHI_API_KEY:
        return {"Authorization": f"Bearer {config.KALSHI_API_KEY}"}
    return None


def _cents_to_prob(value):
    value = to_float(value)
    return value / 100.0 if value is not None else None


def _market_to_quote(market: dict, ticker: str) -> Quote:
    return Quote(
        source="kalshi",
        market_id=ticker,
        question=market.get("title") or market.get("subtitle") or ticker,
        yes_bid=_cents_to_prob(market.get("yes_bid")),
        yes_ask=_cents_to_prob(market.get("yes_ask")),
        no_bid=_cents_to_prob(market.get("no_bid")),
        no_ask=_cents_to_prob(market.get("no_ask")),
        volume=to_float(market.get("volume")),
        url=f"https://kalshi.com/markets/{ticker.split('-')[0].lower()}/{ticker.lower()}",
    )


def fetch_market(ticker: str) -> Quote:
    """Fetch a single market by its Kalshi `ticker` (e.g. 'FED-24DEC-T4.50')."""
    data = get_json(f"{BASE_URL}/markets/{ticker}", headers=_headers())
    market = data.get("market")
    if not market:
        raise SourceError(f"kalshi: no market found for ticker {ticker}")
    return _market_to_quote(market, ticker)


def search_markets(keyword: str, limit: int = 10) -> list:
    """Best-effort keyword search using Kalshi's market listing endpoint."""
    data = get_json(
        f"{BASE_URL}/markets",
        params={"status": "open", "limit": 200},
        headers=_headers(),
    )
    keyword_lower = keyword.lower()
    markets = data.get("markets", [])
    matches = [m for m in markets if keyword_lower in (m.get("title", "") or "").lower()]
    return [_market_to_quote(m, m.get("ticker")) for m in matches[:limit]]
