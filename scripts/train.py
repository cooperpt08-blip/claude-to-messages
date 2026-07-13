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

from bitcoin_predictor import config
from bitcoin_predictor.train_pipeline import run_training


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=60, help="Days of history to fetch (default: 60)")
    parser.add_argument("--model-path", default=config.MODEL_PATH, help="Where to save the trained model")
    args = parser.parse_args()

    run_training(args.days, model_path=args.model_path)


if __name__ == "__main__":
    main()
