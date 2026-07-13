import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_ohlcv():
    """Deterministic synthetic 15m OHLCV data (random walk) for tests that
    don't need real network access."""
    rng = np.random.default_rng(seed=7)
    n = 300
    start = pd.Timestamp("2024-01-01", tz="UTC")
    open_times = pd.date_range(start, periods=n, freq="15min")

    returns = rng.normal(loc=0.0, scale=0.003, size=n)
    close = 40000 * np.cumprod(1 + returns)
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.001, size=n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.001, size=n))
    volume = rng.uniform(50, 500, size=n)

    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "close_time": open_times + pd.Timedelta(minutes=15),
            "num_trades": rng.integers(100, 1000, size=n),
            "taker_buy_base_volume": volume * rng.uniform(0.3, 0.7, size=n),
        }
    )
