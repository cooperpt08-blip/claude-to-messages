#!/usr/bin/env python3
"""Continuously predict BTC/USDT direction for each upcoming 15-minute
candle, logging every prediction and scoring it once the candle closes.

Also auto-retrains the model on a schedule (default: every 24 hours, on the
most recent `--train-days` of history) so it doesn't go stale while running
for long stretches. This is a full batch retrain, not incremental/online
learning -- it refits from scratch on fresh data each time.

Usage:
    python scripts/run_bot.py                          # run forever, default schedule
    python scripts/run_bot.py --iterations 5            # run 5 cycles then stop
    python scripts/run_bot.py --retrain-every-hours 12  # retrain twice a day
    python scripts/run_bot.py --no-auto-retrain         # never retrain automatically
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
from bitcoin_predictor.train_pipeline import run_training

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


def _hours_since_model_saved(model_path):
    if not os.path.exists(model_path):
        return float("inf")
    return (time.time() - os.path.getmtime(model_path)) / 3600


def run(iterations=None, retrain_every_hours=24.0, train_days=60, model_path=None, auto_retrain=True):
    model_path = model_path or config.MODEL_PATH

    if not os.path.exists(model_path):
        print(f"No trained model found at {model_path}. Run scripts/train.py first.")
        sys.exit(1)

    pipeline, _ = model.load(model_path)
    _ensure_log_file()

    pending = None
    n_correct = 0
    n_scored = 0
    cycle = 0

    print(f"Starting bot: predicting {config.SYMBOL} direction every {config.INTERVAL_MINUTES} minutes.")
    print(f"Logging predictions to {config.PREDICTIONS_LOG_PATH}")
    if auto_retrain:
        print(f"Auto-retrain: every {retrain_every_hours}h, on the last {train_days} days of data.")
    else:
        print("Auto-retrain: disabled.")
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

            if auto_retrain and _hours_since_model_saved(model_path) >= retrain_every_hours:
                print(f"\n>>> {retrain_every_hours}h elapsed since last training -- auto-retraining now...")
                try:
                    pipeline, _ = run_training(train_days, model_path=model_path, verbose=False)
                    print(">>> Retrain complete; now predicting with the refreshed model.\n")
                except Exception as exc:  # network hiccup, etc. -- keep serving the old model
                    print(f">>> Retrain failed ({exc}); continuing with the current model.\n")
    except KeyboardInterrupt:
        print("\nStopped by user.")

    if n_scored:
        print(f"\nFinal running accuracy: {n_correct / n_scored:.2%} over {n_scored} predictions.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--iterations", type=int, default=None, help="Stop after N cycles instead of running forever")
    parser.add_argument("--retrain-every-hours", type=float, default=24.0, help="Hours between auto-retrains (default: 24)")
    parser.add_argument("--train-days", type=int, default=60, help="Days of history used for each auto-retrain (default: 60)")
    parser.add_argument("--no-auto-retrain", action="store_true", help="Disable automatic retraining")
    parser.add_argument("--model-path", default=config.MODEL_PATH, help="Model file to load/save")
    args = parser.parse_args()
    run(
        iterations=args.iterations,
        retrain_every_hours=args.retrain_every_hours,
        train_days=args.train_days,
        model_path=args.model_path,
        auto_retrain=not args.no_auto_retrain,
    )


if __name__ == "__main__":
    main()
