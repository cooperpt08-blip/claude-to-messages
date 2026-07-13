from prediction_market_bot.edge import find_complementary_edges, find_cross_platform_edges, pricing_errors
from prediction_market_bot.types import Quote


def _quote(source, yes_bid, yes_ask, no_bid=None, no_ask=None, question="will X happen?"):
    if no_bid is None:
        no_bid = 1.0 - yes_ask
    if no_ask is None:
        no_ask = 1.0 - yes_bid
    return Quote(
        source=source,
        market_id=f"{source}-1",
        question=question,
        yes_bid=yes_bid,
        yes_ask=yes_ask,
        no_bid=no_bid,
        no_ask=no_ask,
    )


def test_cross_platform_edge_detects_arbitrage():
    quotes = [
        _quote("polymarket", yes_bid=0.60, yes_ask=0.62),
        _quote("kalshi", yes_bid=0.50, yes_ask=0.52),
    ]
    edges = find_cross_platform_edges("group", quotes, min_edge=0.0)

    assert len(edges) == 1
    edge = edges[0]
    assert edge.sell_source == "polymarket"
    assert edge.buy_source == "kalshi"
    assert edge.edge == 0.60 - 0.52


def test_cross_platform_edge_respects_min_edge_threshold():
    quotes = [
        _quote("polymarket", yes_bid=0.51, yes_ask=0.52),
        _quote("kalshi", yes_bid=0.50, yes_ask=0.51),
    ]
    edges = find_cross_platform_edges("group", quotes, min_edge=0.05)
    assert edges == []


def test_cross_platform_edge_ignores_same_source_pairs():
    quotes = [_quote("polymarket", yes_bid=0.60, yes_ask=0.55)]
    edges = find_cross_platform_edges("group", quotes, min_edge=0.0)
    assert edges == []


def test_complementary_edge_flags_cheap_buy():
    # yes_ask + no_ask = 0.48 + 0.48 = 0.96 < 1.0 -> buying both is profitable
    quotes = [_quote("predictit", yes_bid=0.44, yes_ask=0.48, no_bid=0.44, no_ask=0.48)]
    edges = find_complementary_edges("group", quotes, min_edge=0.0)

    buy_edges = [e for e in edges if e.side == "buy"]
    assert len(buy_edges) == 1
    assert round(buy_edges[0].edge, 2) == 0.04


def test_complementary_edge_flags_rich_sell():
    # yes_bid + no_bid = 0.55 + 0.55 = 1.10 > 1.0 -> selling both is profitable
    quotes = [_quote("predictit", yes_bid=0.55, yes_ask=0.60, no_bid=0.55, no_ask=0.60)]
    edges = find_complementary_edges("group", quotes, min_edge=0.0)

    sell_edges = [e for e in edges if e.side == "sell"]
    assert len(sell_edges) == 1
    assert round(sell_edges[0].edge, 2) == 0.10


def test_complementary_edge_no_signal_when_priced_fairly():
    quotes = [_quote("polymarket", yes_bid=0.49, yes_ask=0.51, no_bid=0.49, no_ask=0.51)]
    edges = find_complementary_edges("group", quotes, min_edge=0.0)
    assert edges == []


def test_pricing_errors_vs_consensus():
    quotes = [
        _quote("polymarket", yes_bid=0.58, yes_ask=0.60),  # mid 0.59
        _quote("kalshi", yes_bid=0.48, yes_ask=0.50),  # mid 0.49
    ]
    errors = pricing_errors(quotes)

    assert round(errors["polymarket"], 2) == 0.05
    assert round(errors["kalshi"], 2) == -0.05


def test_pricing_errors_empty_when_no_mids():
    quotes = [Quote(source="manifold", market_id="m-1", question="q", yes_bid=None, yes_ask=None, no_bid=None, no_ask=None)]
    assert pricing_errors(quotes) == {}
