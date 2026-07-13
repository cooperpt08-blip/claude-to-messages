"""Tests for the pure parsing/normalization logic in each source adapter.
No network access is used -- these exercise `_market_to_quote` /
`_contract_to_quote` directly against sample API response shapes."""

from prediction_market_bot.sources import kalshi, manifold, polymarket, predictit


def test_polymarket_derives_no_prices_from_yes_book():
    market = {
        "question": "Will X happen?",
        "slug": "will-x-happen",
        "bestBid": "0.62",
        "bestAsk": "0.64",
        "volume": "12345.6",
    }
    quote = polymarket._market_to_quote(market, "will-x-happen")

    assert quote.source == "polymarket"
    assert quote.yes_bid == 0.62
    assert quote.yes_ask == 0.64
    # no_bid = 1 - yes_ask, no_ask = 1 - yes_bid
    assert round(quote.no_bid, 2) == 0.36
    assert round(quote.no_ask, 2) == 0.38
    assert quote.volume == 12345.6


def test_kalshi_converts_cents_to_probability():
    market = {
        "title": "Will Y happen?",
        "yes_bid": 55,
        "yes_ask": 58,
        "no_bid": 42,
        "no_ask": 45,
        "volume": 100,
    }
    quote = kalshi._market_to_quote(market, "Y-TICKER")

    assert quote.yes_bid == 0.55
    assert quote.yes_ask == 0.58
    assert quote.no_bid == 0.42
    assert quote.no_ask == 0.45


def test_predictit_maps_buy_sell_cost_to_ask_bid():
    market = {"id": 1234, "name": "Some market", "url": "https://predictit.org/markets/detail/1234"}
    contract = {
        "id": 5678,
        "name": "Some contract",
        "bestBuyYesCost": 0.61,
        "bestSellYesCost": 0.58,
        "bestBuyNoCost": 0.44,
        "bestSellNoCost": 0.40,
    }
    quote = predictit._contract_to_quote(market, contract)

    assert quote.market_id == "1234:5678"
    assert quote.yes_ask == 0.61
    assert quote.yes_bid == 0.58
    assert quote.no_ask == 0.44
    assert quote.no_bid == 0.40


def test_manifold_uses_probability_for_both_sides_of_book():
    market = {"question": "Will Z happen?", "probability": 0.37, "volume": 500, "url": "https://manifold.markets/x"}
    quote = manifold._market_to_quote(market, "abc123")

    assert quote.has_order_book is False
    assert quote.yes_bid == quote.yes_ask == 0.37
    assert round(quote.no_bid, 2) == 0.63
    assert round(quote.no_ask, 2) == 0.63
