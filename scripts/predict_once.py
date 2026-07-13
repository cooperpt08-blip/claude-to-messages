#!/usr/bin/env python3
"""Load the trained model and print a single up/down prediction for the next
15-minute BTC/USDT candle, using the latest live market data.

Usage:
    python scripts/predict_once.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitcoin_predictor import config, data, model
from bitcoin_predictor.features import latest_feature_row


def main():
    if not os.path.exists(config.MODEL_PATH):
        print(f"No trained model found at {config.MODEL_PATH}. Run scripts/train.py first.")
        sys.exit(1)

    pipeline, _ = model.load()
    raw_df = data.fetch_recent_klines(limit=config.WARMUP_CANDLES + 10)
    row = latest_feature_row(raw_df)

    direction, proba_up = model.predict_direction(pipeline, row)
    candle_time = row["open_time"].iloc[0]
    last_close = row["close"].iloc[0]

    print(f"Latest candle open time (UTC): {candle_time}")
    print(f"Latest close: ${last_close:,.2f}")
    print(f"Prediction for next 15-minute candle: {direction.upper()}")
    print(f"P(up) = {proba_up:.4f}   P(down) = {1 - proba_up:.4f}")


if __name__ == "__main__":
    main()
