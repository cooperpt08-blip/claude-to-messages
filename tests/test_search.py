"""Tests for the multi-word, paginated keyword search in each source
adapter's search_markets, using monkeypatched get_json (no network)."""

from prediction_market_bot.sources import kalshi, polymarket, predictit


def test_polymarket_search_matches_words_in_any_order(monkeypatch):
    page = [
        {"question": "Will the WNBA Finals go to Game 5?", "slug": "wnba-finals-game-5", "bestBid": "0.4", "bestAsk": "0.42"},
        {"question": "Will it rain in Miami tomorrow?", "slug": "rain-miami", "bestBid": "0.1", "bestAsk": "0.12"},
    ]

    def fake_get_json(url, params=None, **kwargs):
        if params.get("offset", 0) > 0:
            return []
        return page

    monkeypatch.setattr(polymarket, "get_json", fake_get_json)

    results = polymarket.search_markets("finals wnba", limit=10)
    assert len(results) == 1
    assert results[0].market_id == "wnba-finals-game-5"


def test_polymarket_search_paginates_until_exhausted(monkeypatch):
    calls = []

    def fake_get_json(url, params=None, **kwargs):
        calls.append(params["offset"])
        if params["offset"] == 0:
            return [{"question": f"filler {i}", "slug": f"filler-{i}"} for i in range(500)]
        if params["offset"] == 500:
            return [{"question": "Will the WNBA champion repeat?", "slug": "wnba-repeat", "bestBid": "0.3", "bestAsk": "0.35"}]
        return []

    monkeypatch.setattr(polymarket, "get_json", fake_get_json)

    results = polymarket.search_markets("wnba", limit=5)
    assert len(results) == 1
    assert results[0].market_id == "wnba-repeat"
    assert calls == [0, 500]


def test_kalshi_search_matches_words_and_paginates(monkeypatch):
    def fake_get_json(url, params=None, **kwargs):
        if params.get("cursor") is None:
            return {
                "markets": [
                    {"title": "Will the Fed hold its July policy meeting?", "ticker": "FED-26JUL-T", "yes_bid": 40, "yes_ask": 42},
                ],
                "cursor": "page2",
            }
        return {"markets": [{"title": "Fed rate decision September", "ticker": "FED-26SEP-T", "yes_bid": 50, "yes_ask": 52}], "cursor": None}

    monkeypatch.setattr(kalshi, "get_json", fake_get_json)

    results = kalshi.search_markets("fed rate", limit=10)
    assert len(results) == 1
    assert results[0].market_id == "FED-26SEP-T"


def test_predictit_search_matches_words_in_any_order(monkeypatch):
    payload = {
        "markets": [
            {
                "id": 1,
                "name": "Fed interest rate decision in 2026?",
                "contracts": [{"id": 11, "name": "Yes", "bestBuyYesCost": 0.5, "bestSellYesCost": 0.48, "bestBuyNoCost": 0.5, "bestSellNoCost": 0.48}],
            },
            {"id": 2, "name": "Who wins the 2026 election?", "contracts": [{"id": 21, "name": "Yes"}]},
        ]
    }
    monkeypatch.setattr(predictit, "get_json", lambda url, **kwargs: payload)

    results = predictit.search_markets("rate fed", limit=10)
    assert len(results) == 1
    assert results[0].market_id == "1:11"


def test_predictit_search_returns_nothing_for_sports_keyword(monkeypatch):
    payload = {"markets": [{"id": 1, "name": "Who wins the 2026 election?", "contracts": [{"id": 11, "name": "Yes"}]}]}
    monkeypatch.setattr(predictit, "get_json", lambda url, **kwargs: payload)

    assert predictit.search_markets("wnba", limit=10) == []
