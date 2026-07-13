# Bitcoin 15-Minute Direction Predictor

A bot that predicts whether the BTC/USDT price will go **up** or **down**
over the next 15-minute candle, using historical price/volume data and a
gradient-boosted classifier trained on technical indicators.

> **Disclaimer:** This is an educational project, not financial advice.
> Short-term crypto price direction is extremely hard to predict — in
> backtests this model typically performs close to a coin flip (see
> `baseline_majority_accuracy` printed by training). Do not use this to
> make real trading decisions without your own due diligence, and never
> risk money you can't afford to lose.

## How it works

1. **Data** (`bitcoin_predictor/data.py`) — fetches OHLCV candles for
   `BTCUSDT` at the `15m` interval from Binance's public REST API (no API
   key needed).
2. **Features** (`bitcoin_predictor/features.py`) — engineers technical
   indicators from price/volume alone: returns over multiple lookbacks,
   SMA/EMA relative position, MACD, RSI(14), Bollinger Band %B and width,
   rolling volatility, volume z-score, and momentum. The label is
   `1` if the *next* candle closes higher than the current one, else `0`.
3. **Model** (`bitcoin_predictor/model.py`) — a scaled
   `GradientBoostingClassifier` (scikit-learn), trained on a
   **time-ordered** split (no shuffling, so the test set is always
   chronologically after training data — this avoids leaking future
   information).
4. **Backtest** (`bitcoin_predictor/backtest.py`) — a naive long/cash
   simulation over the held-out test period, compared against buy & hold.
5. **Bot loop** (`scripts/run_bot.py`) — wakes up on each 15-minute
   boundary, predicts the next candle's direction, and once that candle
   closes, scores the previous prediction and logs it to
   `logs/predictions_log.csv`, printing a running accuracy.

## Setup

```bash
pip install -r requirements.txt
```

Requires outbound network access to `api.binance.com`.

**US-based?** `api.binance.com` returns `HTTP 451` (geo-blocked) for US IP
addresses. Point the bot at Binance.US instead:

```bash
export BINANCE_BASE_URL=https://api.binance.us
```

Set this in every terminal session before running the scripts below (or add
it to your shell profile).

## Usage

### 1. Train a model

```bash
python scripts/train.py --days 60
```

Fetches 60 days of 15-minute history, trains the model, prints accuracy /
confusion matrix / a naive backtest vs. buy & hold, and saves the model to
`models/direction_model.joblib`. More days of history generally helps, but
very old data may reflect a different market regime.

### 2. Get a single prediction

```bash
python scripts/predict_once.py
```

Prints the predicted direction and probability for the next 15-minute
candle using the latest live data.

### 3. Run the live bot

```bash
python scripts/run_bot.py                # runs forever, Ctrl+C to stop
python scripts/run_bot.py --iterations 5  # runs 5 cycles then exits
```

Each cycle: sleeps until the next 15-minute boundary, fetches the latest
candle, predicts the next one's direction, and scores the prior
prediction once its outcome is known. All predictions and outcomes are
appended to `logs/predictions_log.csv` for later analysis.

## Retraining

Markets drift, so re-run `scripts/train.py` periodically (e.g. weekly) to
refresh the model on recent data.

## Project layout

```
bitcoin_predictor/
  config.py     # symbol, interval, paths, hyperparameters
  data.py       # Binance klines fetching
  features.py   # technical indicators + labeling
  model.py      # train/save/load/predict
  backtest.py   # long/cash simulation vs. buy & hold
scripts/
  train.py          # fetch data, train, evaluate, save model
  predict_once.py   # one-shot prediction using live data
  run_bot.py         # continuous predict-and-score loop
tests/          # unit tests using synthetic OHLCV data (no network needed)
```

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

---

# Prediction Market Edge Bot

A bot that pulls live buy/sell (bid/ask) prices for the same real-world
question from **multiple prediction market platforms** — Polymarket,
Kalshi, PredictIt, and Manifold Markets — and flags two kinds of pricing
signal:

1. **Cross-platform edge** — one platform's Yes *bid* is higher than
   another platform's Yes *ask*, meaning the two disagree on the odds by
   more than the bid/ask spread alone would explain.
2. **Complementary mispricing** — on a single platform, Yes + No should
   always cost ~$1 together (exactly one side pays out). If buying both
   costs less than $1, or selling both nets more than $1, that's a
   same-platform arbitrage/error.

> **Disclaimer:** All edges are reported gross of fees, slippage, and
> withdrawal/transfer friction between platforms. Manifold trades play
> money and has no real order book (it quotes a single AMM probability),
> so treat its prices as an informational signal, not something you can
> execute against. This is an educational project, not financial advice —
> verify resolution criteria match exactly before trusting any "edge."

## How it works

1. **Sources** (`prediction_market_bot/sources/`) — one adapter per
   platform, each normalizing that platform's quote format into a common
   `Quote` (yes_bid/yes_ask/no_bid/no_ask, all in probability space). All
   four platforms have public, no-API-key read endpoints for market data.
2. **Market matching** (`prediction_market_bot/markets.yaml`) — since
   automatically matching "the same question" across platforms by title
   is unreliable for anything money-related, groups of equivalent markets
   are curated explicitly: you look up each platform's market ID with
   `scripts/list_markets.py` and list them together in one group.
3. **Edge detection** (`prediction_market_bot/edge.py`) — for each group,
   computes cross-platform edges, complementary (Yes+No) mispricing, and
   each platform's pricing error vs. the cross-platform consensus.
4. **Reporting** (`prediction_market_bot/report.py`) — plain-text
   comparison tables and edge summaries used by both CLI scripts below.

## Setup

```bash
pip install -r requirements.txt
```

Requires outbound network access to `gamma-api.polymarket.com`,
`api.elections.kalshi.com`, `www.predictit.org`, and `api.manifold.markets`.

## Usage

### 1. Find market IDs to compare

```bash
python scripts/list_markets.py polymarket "fed rate"
python scripts/list_markets.py kalshi "fed rate"
```

Prints matching markets and the `market_id` value to put in
`prediction_market_bot/markets.yaml`.

### 2. Edit `prediction_market_bot/markets.yaml`

Group markets that resolve on the *same* question, deadline, and criteria
across platforms — see the comments in that file for the format.

### 3. One-shot scan

```bash
python scripts/scan_markets.py
python scripts/scan_markets.py --min-edge 0.03
```

Prints a price comparison table and flagged edges for every group.

### 4. Watch continuously

```bash
python scripts/watch_markets.py                  # every 60s, forever
python scripts/watch_markets.py --interval 300 --iterations 10
```

Re-scans on an interval and appends every flagged edge to
`logs/prediction_market_edges_log.csv` with a timestamp.

## Project layout

```
prediction_market_bot/
  config.py        # thresholds, log paths, HTTP settings
  types.py          # Quote / MarketGroup / edge dataclasses
  markets.py        # loads markets.yaml, fetches quotes per group
  markets.yaml       # curated groups of equivalent markets (edit this)
  edge.py            # cross-platform + complementary edge detection
  report.py          # plain-text table/edge formatting
  sources/
    polymarket.py, kalshi.py, predictit.py, manifold.py
scripts/
  list_markets.py    # keyword search helper to find market IDs
  scan_markets.py    # one-shot scan + report
  watch_markets.py    # continuous scan-and-log loop
```

## Running tests

```bash
pip install pytest
pytest tests/test_edge.py tests/test_markets.py tests/test_sources.py -v
```

All tests use synthetic quotes / sample API response shapes — no network
access needed.
