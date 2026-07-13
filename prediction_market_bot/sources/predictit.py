"""PredictIt adapter, backed by PredictIt's public market data API.

Fully public, no API key. API docs: https://www.predictit.org/api/marketdata/all/
"""

from ..types import Quote
from .base import SourceError, get_json, to_float

BASE_URL = "https://www.predictit.org/api/marketdata"


def _contract_to_quote(market: dict, contract: dict) -> Quote:
    market_name = market.get("name", str(market.get("id")))
    contract_name = contract.get("name", str(contract.get("id")))
    question = f"{market_name} — {contract_name}" if contract_name != market_name else market_name
    return Quote(
        source="predictit",
        market_id=f"{market.get('id')}:{contract.get('id')}",
        question=question,
        # PredictIt's "buy" cost is the ask (what it costs you to buy now);
        # its "sell" cost is the bid (what you'd receive selling now).
        yes_ask=to_float(contract.get("bestBuyYesCost")),
        yes_bid=to_float(contract.get("bestSellYesCost")),
        no_ask=to_float(contract.get("bestBuyNoCost")),
        no_bid=to_float(contract.get("bestSellNoCost")),
        volume=None,  # PredictIt's market data API doesn't expose per-contract volume
        url=market.get("url"),
    )


def fetch_market(market_id, contract_id=None) -> Quote:
    """Fetch a single contract. If `contract_id` is omitted, uses the market's
    only contract (for simple yes/no markets with a single contract)."""
    data = get_json(f"{BASE_URL}/markets/{market_id}")
    contracts = data.get("contracts", [])
    if not contracts:
        raise SourceError(f"predictit: no contracts found for market {market_id}")

    if contract_id is None:
        if len(contracts) != 1:
            raise ValueError(
                f"predictit market {market_id} has {len(contracts)} contracts; "
                "pass contract_id to pick one"
            )
        contract = contracts[0]
    else:
        contract = next((c for c in contracts if str(c.get("id")) == str(contract_id)), None)
        if contract is None:
            raise SourceError(f"predictit: contract {contract_id} not found in market {market_id}")

    return _contract_to_quote(data, contract)


def search_markets(keyword: str, limit: int = 10) -> list:
    """Best-effort keyword search across all PredictIt markets/contracts."""
    data = get_json(f"{BASE_URL}/all/")
    keyword_lower = keyword.lower()
    matches = []
    for market in data.get("markets", []):
        if keyword_lower not in (market.get("name", "") or "").lower():
            continue
        for contract in market.get("contracts", []):
            matches.append(_contract_to_quote(market, contract))
            if len(matches) >= limit:
                return matches
    return matches
