from datetime import datetime, timedelta, timezone

from prediction_market_bot import backtest

BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _row(minutes, edge, kind="cross_platform", group="g"):
    return {"timestamp": BASE_TIME + timedelta(minutes=minutes), "kind": kind, "group": group, "detail": "", "edge": edge}


def test_simulate_executes_trades_clearing_cost():
    rows = [_row(0, 0.05), _row(5, 0.03)]
    summary, trades, equity_curve = backtest.simulate(rows, position_size=100.0, assumed_cost=0.01)

    assert summary["n_opportunities"] == 2
    assert summary["n_executed"] == 2
    assert summary["win_rate"] == 1.0
    # net edges: 0.04 and 0.02, profit = *100 each -> 4 + 2 = 6
    assert round(summary["final_balance"], 2) == 6.0
    assert [round(v, 2) for v in equity_curve] == [4.0, 6.0]
    assert equity_curve[-1] == summary["final_balance"]


def test_simulate_skips_trades_below_cost():
    rows = [_row(0, 0.005), _row(5, 0.05)]
    summary, trades, _ = backtest.simulate(rows, position_size=100.0, assumed_cost=0.01)

    assert summary["n_opportunities"] == 2
    assert summary["n_executed"] == 1
    assert summary["win_rate"] == 0.5
    assert not trades[0].executed
    assert trades[0].profit == 0.0
    assert trades[1].executed
    assert round(summary["final_balance"], 2) == 4.0  # (0.05 - 0.01) * 100


def test_simulate_orders_trades_by_timestamp_not_input_order():
    rows = [_row(10, 0.05), _row(0, 0.03)]
    _, trades, _ = backtest.simulate(rows, assumed_cost=0.0)
    assert trades[0].timestamp < trades[1].timestamp


def test_simulate_empty_rows():
    summary, trades, equity_curve = backtest.simulate([])
    assert summary["n_opportunities"] == 0
    assert summary["win_rate"] == 0.0
    assert summary["final_balance"] == 0.0
    assert trades == []
    assert equity_curve == []


def test_load_edge_log_roundtrip(tmp_path):
    path = tmp_path / "edges_log.csv"
    path.write_text(
        "timestamp,kind,group,detail,edge\n"
        "2026-01-01T00:00:00+00:00,cross_platform,g,detail text,0.0300\n"
    )
    rows = backtest.load_edge_log(str(path))

    assert len(rows) == 1
    assert rows[0]["kind"] == "cross_platform"
    assert rows[0]["group"] == "g"
    assert rows[0]["edge"] == 0.03
    assert rows[0]["timestamp"] == datetime(2026, 1, 1, tzinfo=timezone.utc)
