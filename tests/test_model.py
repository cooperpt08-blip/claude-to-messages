import os

from bitcoin_predictor import model
from bitcoin_predictor.backtest import simulate
from bitcoin_predictor.features import build_features


def test_train_and_predict_roundtrip(synthetic_ohlcv, tmp_path):
    feature_df = build_features(synthetic_ohlcv)
    pipeline, metrics, test_df = model.train(feature_df)

    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert metrics["n_train"] + metrics["n_test"] == len(feature_df)

    save_path = os.path.join(tmp_path, "model.joblib")
    model.save(pipeline, save_path)
    assert os.path.exists(save_path)

    loaded_pipeline, feature_columns = model.load(save_path)
    direction, proba_up = model.predict_direction(loaded_pipeline, test_df.iloc[[-1]])
    assert direction in {"up", "down"}
    assert 0.0 <= proba_up <= 1.0


def test_backtest_simulate_runs(synthetic_ohlcv):
    feature_df = build_features(synthetic_ohlcv)
    pipeline, _, test_df = model.train(feature_df)

    summary, equity_curve = simulate(pipeline, test_df)
    assert summary["n_periods"] == len(test_df)
    assert len(equity_curve) == len(test_df)
    assert summary["strategy_final_balance"] > 0
