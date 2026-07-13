import os

from bitcoin_predictor import config, data
from bitcoin_predictor.train_pipeline import run_training


def test_run_training_fetches_trains_and_saves(synthetic_ohlcv, tmp_path, monkeypatch):
    monkeypatch.setattr(data, "fetch_historical_klines", lambda **kw: synthetic_ohlcv)

    save_path = os.path.join(tmp_path, "model.joblib")
    pipeline, metrics = run_training(days=30, model_path=save_path, verbose=False)

    assert os.path.exists(save_path)
    assert 0.0 <= metrics["accuracy"] <= 1.0
