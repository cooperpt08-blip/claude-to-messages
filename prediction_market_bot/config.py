"""Central configuration for the prediction-market edge bot."""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Market group definitions ---
DEFAULT_MARKETS_CONFIG = os.path.join(_ROOT, "prediction_market_bot", "markets.yaml")

# --- Edge detection thresholds ---
# Minimum edge (in probability points, e.g. 0.02 == 2 cents on a $1 contract)
# before an opportunity is considered worth reporting. Real trading incurs
# fees and slippage the raw quotes don't reflect, so keep this comfortably
# above zero.
DEFAULT_MIN_EDGE = float(os.environ.get("PMB_MIN_EDGE", "0.02"))

# --- Logging ---
LOG_DIR = os.path.join(_ROOT, "logs")
EDGES_LOG_PATH = os.path.join(LOG_DIR, "prediction_market_edges_log.csv")

# --- HTTP ---
REQUEST_TIMEOUT = float(os.environ.get("PMB_REQUEST_TIMEOUT", "10"))
USER_AGENT = "prediction-market-edge-bot/0.1 (+https://github.com/)"

# --- Optional API credentials (all sources here have public read endpoints,
# so these are only needed if a platform starts requiring auth for reads) ---
KALSHI_API_KEY = os.environ.get("KALSHI_API_KEY")
