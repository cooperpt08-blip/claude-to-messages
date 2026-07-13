"""Fetch OHLCV candle data for BTC/USDT from Binance's public REST API.

No API key is required for market data endpoints. All requests are read-only.
"""

import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

from . import config

_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "num_trades",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore",
]

_NUMERIC_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_asset_volume",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
]


def _request_klines(symbol, interval, start_time_ms=None, end_time_ms=None, limit=1000):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_time_ms is not None:
        params["startTime"] = start_time_ms
    if end_time_ms is not None:
        params["endTime"] = end_time_ms

    resp = requests.get(config.BINANCE_BASE_URL + config.KLINES_ENDPOINT, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _raw_to_dataframe(raw):
    df = pd.DataFrame(raw, columns=_COLUMNS)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df[_NUMERIC_COLUMNS] = df[_NUMERIC_COLUMNS].astype(float)
    df["num_trades"] = df["num_trades"].astype(int)
    return df[
        [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "num_trades",
            "taker_buy_base_volume",
        ]
    ]


def fetch_recent_klines(limit=500, symbol=None, interval=None):
    """Fetch the most recent `limit` candles (single request, limit <= 1000)."""
    symbol = symbol or config.SYMBOL
    interval = interval or config.INTERVAL
    limit = min(limit, config.MAX_KLINES_PER_REQUEST)
    raw = _request_klines(symbol, interval, limit=limit)
    return _raw_to_dataframe(raw)


def fetch_historical_klines(days, symbol=None, interval=None, pause_seconds=0.25):
    """Fetch `days` worth of history by paging backward from now.

    Binance caps a single request at 1000 candles, so for long ranges this
    issues multiple sequential requests.
    """
    symbol = symbol or config.SYMBOL
    interval = interval or config.INTERVAL

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    all_rows = []
    cursor = start_ms
    while cursor < end_ms:
        raw = _request_klines(symbol, interval, start_time_ms=cursor, end_time_ms=end_ms, limit=config.MAX_KLINES_PER_REQUEST)
        if not raw:
            break
        all_rows.extend(raw)
        last_open_time = raw[-1][0]
        next_cursor = last_open_time + 1
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        if len(raw) < config.MAX_KLINES_PER_REQUEST:
            break
        time.sleep(pause_seconds)  # be polite to the public API

    if not all_rows:
        return pd.DataFrame(columns=["open_time", "open", "high", "low", "close", "volume", "close_time", "num_trades", "taker_buy_base_volume"])

    df = _raw_to_dataframe(all_rows)
    df = df.drop_duplicates(subset="open_time").sort_values("open_time").reset_index(drop=True)
    return df
