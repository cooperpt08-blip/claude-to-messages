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
