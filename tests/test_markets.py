import os

import pytest

from prediction_market_bot import markets
from prediction_market_bot.types import Quote

MARKETS_YAML = """
groups:
  - name: test-group
    members:
      - source: polymarket
        params:
          slug: some-market
      - source: kalshi
        params:
          ticker: SOME-TICKER
"""


def test_load_groups_parses_yaml(tmp_path):
    path = tmp_path / "markets.yaml"
    path.write_text(MARKETS_YAML)

    groups = markets.load_groups(str(path))

    assert len(groups) == 1
    group = groups[0]
    assert group.name == "test-group"
    assert len(group.members) == 2
    assert group.members[0].source == "polymarket"
    assert group.members[0].params == {"slug": "some-market"}
    assert group.members[1].source == "kalshi"
    assert group.members[1].params == {"ticker": "SOME-TICKER"}


def test_load_groups_empty_file(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("")
    assert markets.load_groups(str(path)) == []


def test_fetch_group_quotes_skips_failing_members(monkeypatch, tmp_path):
    path = tmp_path / "markets.yaml"
    path.write_text(MARKETS_YAML)
    groups = markets.load_groups(str(path))

    def fake_polymarket(**params):
        return Quote(source="polymarket", market_id=params["slug"], question="q", yes_bid=0.5, yes_ask=0.55, no_bid=0.45, no_ask=0.5)

    def fake_kalshi(**params):
        raise RuntimeError("network error")

    monkeypatch.setitem(markets.SOURCES, "polymarket", fake_polymarket)
    monkeypatch.setitem(markets.SOURCES, "kalshi", fake_kalshi)

    errors = []
    quotes = markets.fetch_group_quotes(groups[0], on_error=lambda g, m, e: errors.append((m.source, str(e))))

    assert len(quotes) == 1
    assert quotes[0].source == "polymarket"
    assert len(errors) == 1
    assert errors[0][0] == "kalshi"


def test_fetch_group_quotes_unknown_source_raises(tmp_path):
    path = tmp_path / "markets.yaml"
    path.write_text("""
groups:
  - name: bad-group
    members:
      - source: not-a-real-source
        params: {}
""")
    group = markets.load_groups(str(path))[0]
    with pytest.raises(ValueError):
        markets.fetch_group_quotes(group)
