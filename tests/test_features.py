from bitcoin_predictor.features import FEATURE_COLUMNS, TARGET_COLUMN, build_features, latest_feature_row


def test_build_features_has_no_nans_and_binary_target(synthetic_ohlcv):
    out = build_features(synthetic_ohlcv)

    assert len(out) > 0
    assert not out[FEATURE_COLUMNS + [TARGET_COLUMN]].isna().any().any()
    assert set(out[TARGET_COLUMN].unique()) <= {0, 1}


def test_build_features_drops_warmup_and_last_row(synthetic_ohlcv):
    out = build_features(synthetic_ohlcv)
    # last row of raw data has no future candle to label, so it must be excluded
    assert out["open_time"].max() < synthetic_ohlcv["open_time"].max()
    assert len(out) < len(synthetic_ohlcv)


def test_latest_feature_row_returns_single_row(synthetic_ohlcv):
    row = latest_feature_row(synthetic_ohlcv)
    assert len(row) == 1
    assert row["open_time"].iloc[0] == synthetic_ohlcv["open_time"].iloc[-1]
    assert not row[FEATURE_COLUMNS].isna().any().any()


def test_latest_feature_row_raises_with_insufficient_history():
    import pandas as pd

    tiny_df = pd.DataFrame(
        {
            "open_time": pd.date_range("2024-01-01", periods=3, freq="15min", tz="UTC"),
            "open": [1, 2, 3],
            "high": [1, 2, 3],
            "low": [1, 2, 3],
            "close": [1, 2, 3],
            "volume": [10, 10, 10],
        }
    )
    try:
        latest_feature_row(tiny_df)
        assert False, "expected ValueError"
    except ValueError:
        pass
