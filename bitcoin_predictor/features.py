"""Technical-indicator feature engineering for 15-minute BTC/USDT candles.

Every indicator here is computed from OHLCV data alone (no external
dependency like ta-lib) so the project only needs pandas/numpy.
"""

import numpy as np

FEATURE_COLUMNS = [
    "return_1",
    "return_3",
    "return_6",
    "sma_5_rel",
    "sma_10_rel",
    "sma_20_rel",
    "ema_12_rel",
    "ema_26_rel",
    "macd",
    "macd_signal",
    "macd_hist",
    "rsi_14",
    "bb_pct",
    "bb_width",
    "volatility_10",
    "volume_change",
    "volume_zscore_20",
    "high_low_range",
    "momentum_5",
]

TARGET_COLUMN = "target"


def _rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _add_indicators(df):
    """Add all FEATURE_COLUMNS to a copy of `df`. Does not add the target."""
    out = df.copy().reset_index(drop=True)
    close = out["close"]
    volume = out["volume"]

    out["return_1"] = close.pct_change(1)
    out["return_3"] = close.pct_change(3)
    out["return_6"] = close.pct_change(6)

    sma_5 = close.rolling(5).mean()
    sma_10 = close.rolling(10).mean()
    sma_20 = close.rolling(20).mean()
    out["sma_5_rel"] = close / sma_5 - 1
    out["sma_10_rel"] = close / sma_10 - 1
    out["sma_20_rel"] = close / sma_20 - 1

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    out["ema_12_rel"] = close / ema_12 - 1
    out["ema_26_rel"] = close / ema_26 - 1

    macd = ema_12 - ema_26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    out["macd"] = macd / close
    out["macd_signal"] = macd_signal / close
    out["macd_hist"] = (macd - macd_signal) / close

    out["rsi_14"] = _rsi(close, 14)

    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    bb_range = (bb_upper - bb_lower).replace(0, np.nan)
    out["bb_pct"] = (close - bb_lower) / bb_range
    out["bb_width"] = bb_range / bb_mid

    out["volatility_10"] = close.pct_change().rolling(10).std()

    out["volume_change"] = volume.pct_change()
    vol_mean_20 = volume.rolling(20).mean()
    vol_std_20 = volume.rolling(20).std().replace(0, np.nan)
    out["volume_zscore_20"] = (volume - vol_mean_20) / vol_std_20

    out["high_low_range"] = (out["high"] - out["low"]) / close

    out["momentum_5"] = close / close.shift(5) - 1

    return out.replace([np.inf, -np.inf], np.nan)


def build_features(df):
    """Given a raw OHLCV dataframe (sorted ascending by open_time), return a
    new dataframe with engineered features and a binary `target` column:
    1 if the *next* candle closes higher than the current candle, else 0.

    Rows without enough history for the longest indicator window, and the
    final row (which has no future candle to label), are dropped.
    """
    out = _add_indicators(df)
    future_close = out["close"].shift(-1)
    # NaN comparisons evaluate to False rather than NaN, so the final row
    # (no future candle) must be masked back to NaN explicitly before it can
    # be dropped by dropna below.
    target = (future_close > out["close"]).astype(float)
    target[future_close.isna()] = np.nan
    out[TARGET_COLUMN] = target
    out = out.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).reset_index(drop=True)
    out[TARGET_COLUMN] = out[TARGET_COLUMN].astype(int)
    return out


def latest_feature_row(df):
    """Build features on the full history and return the last row's feature
    vector (the most recent complete candle), suitable for live prediction.

    Unlike `build_features`, this does not require a future candle to exist,
    since the target for the newest row is unknown.
    """
    out = _add_indicators(df)
    last_row = out.iloc[[-1]]
    if last_row[FEATURE_COLUMNS].isna().any(axis=None):
        raise ValueError("Not enough history to compute all features for the latest candle; fetch more candles.")
    return last_row
