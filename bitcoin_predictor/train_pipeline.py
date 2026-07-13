"""Shared fetch-train-evaluate-save pipeline used by scripts/train.py and by
the auto-retrain check in scripts/run_bot.py."""

import os

from . import config, data, model
from .backtest import simulate
from .features import build_features


def run_training(days, model_path=None, verbose=True):
    """Fetch `days` of history, train a fresh model, evaluate it on a
    held-out time-ordered test slice, and save it. Returns (pipeline, metrics).
    """
    model_path = model_path or config.MODEL_PATH
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    if verbose:
        print(f"Fetching {days} days of {config.SYMBOL} {config.INTERVAL} candles...")
    raw_df = data.fetch_historical_klines(days=days)
    if verbose:
        print(f"Fetched {len(raw_df)} candles.")

    feature_df = build_features(raw_df)
    if verbose:
        print(f"{len(feature_df)} labeled rows after feature engineering.")
        print("Training model (time-ordered train/test split, no shuffling)...")
    pipeline, metrics, test_df = model.train(feature_df)

    if verbose:
        print("\n--- Evaluation on held-out (most recent) test period ---")
        print(f"Train rows: {metrics['n_train']}   Test rows: {metrics['n_test']}")
        print(f"Accuracy:              {metrics['accuracy']:.4f}")
        print(f"Majority-class baseline: {metrics['baseline_majority_accuracy']:.4f}")
        print("Confusion matrix [[TN, FP], [FN, TP]] (up=positive):")
        print(metrics["confusion_matrix"])
        print(metrics["classification_report"])

        summary, _ = simulate(pipeline, test_df)
        print("--- Naive long/cash backtest on the same test period (no fees) ---")
        print(f"Start balance:        ${summary['starting_balance']:.2f}")
        print(f"Strategy end balance: ${summary['strategy_final_balance']:.2f}")
        print(f"Buy & hold end balance: ${summary['buy_hold_final_balance']:.2f}")
        print(f"Fraction of periods spent long: {summary['pct_periods_long']:.2%}")

    saved_path = model.save(pipeline, model_path)
    if verbose:
        print(f"\nModel saved to {saved_path}")

    return pipeline, metrics
