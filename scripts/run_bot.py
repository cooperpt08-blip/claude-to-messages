#!/usr/bin/env python3
"""Continuously predict BTC/USDT direction for each upcoming 15-minute
candle, logging every prediction and scoring it once the candle closes.

Usage:
    python scripts/run_bot.py                # run forever
    python scripts/run_bot.py --iterations 5  # run 5 cycles then stop
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitcoin_predictor import config, data, model
from bitcoin_predictor.features import latest_feature_row

LOG_FIELDS = ["candle_open_time", "close_at_prediction", "predicted_direction", "proba_up", "actual_direction", "correct"]


def _seconds_until_next_boundary(buffer_seconds=20):
    now = datetime.now(timezone.utc)
    minute_block = (now.minute // config.INTERVAL_MINUTES + 1) * config.INTERVAL_MINUTES
    next_boundary = now.replace(second=0, microsecond=0) + timedelta(minutes=minute_block - now.minute)
    return (next_boundary - now).total_seconds() + buffer_seconds


def _ensure_log_file():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    if not os.path.exists(config.PREDICTIONS_LOG_PATH):
        with open(config.PREDICTIONS_LOG_PATH, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=LOG_FIELDS).writeheader()


def _append_log(row):
    with open(config.PREDICTIONS_LOG_PATH, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=LOG_FIELDS).writerow(row)


def _score_previous_prediction(pending, latest_close):
    actual_direction = "up" if latest_close > pending["close_at_prediction"] else "down"
    correct = actual_direction == pending["predicted_direction"]
    pending["actual_direction"] = actual_direction
    pending["correct"] = correct
    _append_log(pending)
    return correct


def run(iterations=None):
    if not os.path.exists(config.MODEL_PATH):
        print(f"No trained model found at {config.MODEL_PATH}. Run scripts/train.py first.")
        sys.exit(1)

    pipeline, _ = model.load()
    _ensure_log_file()

    pending = None
    n_correct = 0
    n_scored = 0
    cycle = 0

    print(f"Starting bot: predicting {config.SYMBOL} direction every {config.INTERVAL_MINUTES} minutes.")
    print(f"Logging predictions to {config.PREDICTIONS_LOG_PATH}")
    print("Press Ctrl+C to stop.\n")

    try:
        while iterations is None or cycle < iterations:
            wait_s = _seconds_until_next_boundary()
            print(f"Sleeping {wait_s:.0f}s until next candle boundary...")
            time.sleep(max(wait_s, 0))

            raw_df = data.fetch_recent_klines(limit=config.WARMUP_CANDLES + 10)
            row = latest_feature_row(raw_df)
            close_now = float(row["close"].iloc[0])
            candle_time = row["open_time"].iloc[0]

            if pending is not None:
                correct = _score_previous_prediction(pending, close_now)
                n_scored += 1
                n_correct += int(correct)
                acc = n_correct / n_scored
                print(f"  Previous prediction ({pending['predicted_direction']}) was "
                      f"{'CORRECT' if correct else 'WRONG'}. Running accuracy: {acc:.2%} ({n_scored} scored)")

            direction, proba_up = model.predict_direction(pipeline, row)
            print(f"[{candle_time}] close=${close_now:,.2f}  prediction={direction.upper()}  P(up)={proba_up:.3f}")

            pending = {
                "candle_open_time": candle_time,
                "close_at_prediction": close_now,
                "predicted_direction": direction,
                "proba_up": proba_up,
            }
            cycle += 1
    except KeyboardInterrupt:
        print("\nStopped by user.")

    if n_scored:
        print(f"\nFinal running accuracy: {n_correct / n_scored:.2%} over {n_scored} predictions.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=None, help="Stop after N cycles instead of running forever")
    args = parser.parse_args()
    run(iterations=args.iterations)


if __name__ == "__main__":
    main()
