"""Central configuration for the Bitcoin direction predictor."""

import os

# --- Market data ---
SYMBOL = os.environ.get("BTC_SYMBOL", "BTCUSDT")
INTERVAL = "15m"
INTERVAL_MINUTES = 15
# api.binance.com returns HTTP 451 (geo-blocked) for US-based requests.
# Override with BINANCE_BASE_URL=https://api.binance.us if you're in the US,
# or any other Binance-compatible mirror.
BINANCE_BASE_URL = os.environ.get("BINANCE_BASE_URL", "https://api.binance.com")
KLINES_ENDPOINT = "/api/v3/klines"
MAX_KLINES_PER_REQUEST = 1000

# --- Feature engineering ---
# Number of warm-up candles needed before indicators stop producing NaNs.
# Keep in sync with the longest lookback window used in features.py.
WARMUP_CANDLES = 60

# --- Model ---
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "direction_model.joblib")
RANDOM_STATE = 42
TEST_SIZE = 0.2  # fraction of most-recent data held out for evaluation (time-ordered split)

# --- Live bot ---
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
PREDICTIONS_LOG_PATH = os.path.join(LOG_DIR, "predictions_log.csv")
