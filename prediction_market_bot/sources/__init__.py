"""Per-platform adapters that normalize prices into `Quote` objects.

Every adapter exposes:
  - `fetch_market(**params) -> Quote`   (params vary per source; see markets.yaml)
  - `search_markets(keyword, limit=10) -> list[Quote]`  (best-effort discovery helper)
"""

from . import kalshi, manifold, polymarket, predictit

SOURCES = {
    "polymarket": polymarket.fetch_market,
    "kalshi": kalshi.fetch_market,
    "predictit": predictit.fetch_market,
    "manifold": manifold.fetch_market,
}

SEARCHERS = {
    "polymarket": polymarket.search_markets,
    "kalshi": kalshi.search_markets,
    "predictit": predictit.search_markets,
    "manifold": manifold.search_markets,
}
