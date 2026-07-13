#!/usr/bin/env python3
"""Fetch historical BTC/USDT 15m candles, train the direction model, and
save it to models/direction_model.joblib.

Usage:
    python scripts/train.py --days 60
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitcoin_predictor import config, data, model
from bitcoin_predictor.backtest import simulate
from bitcoin_predictor.features import build_features


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=60, help="Days of history to fetch (default: 60)")
    parser.add_argument("--model-path", default=config.MODEL_PATH, help="Where to save the trained model")
    args = parser.parse_args()

    os.makedirs(config.MODEL_DIR, exist_ok=True)

    print(f"Fetching {args.days} days of {config.SYMBOL} {config.INTERVAL} candles from Binance...")
    raw_df = data.fetch_historical_klines(days=args.days)
    print(f"Fetched {len(raw_df)} candles.")

    print("Building features...")
    feature_df = build_features(raw_df)
    print(f"{len(feature_df)} labeled rows after feature engineering.")

    print("Training model (time-ordered train/test split, no shuffling)...")
    pipeline, metrics, test_df = model.train(feature_df)

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

    saved_path = model.save(pipeline, args.model_path)
    print(f"\nModel saved to {saved_path}")


if __name__ == "__main__":
    main()
