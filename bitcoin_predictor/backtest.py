"""Simple long/cash walk-forward backtest over a held-out test set.

This is a directional-accuracy sanity check, not a production trading
simulator: it ignores fees, slippage, and spread.
"""

import numpy as np
import pandas as pd

from .features import FEATURE_COLUMNS


def simulate(pipeline, test_df, starting_balance=1000.0, fee_rate=0.0):
    """For each candle in `test_df`, predict direction; if "up", hold BTC for
    that 15-minute period (capturing its actual return), else hold cash.

    Returns (summary_dict, equity_curve_dataframe).
    """
    X = test_df[FEATURE_COLUMNS]
    proba_up = pipeline.predict_proba(X)[:, 1]
    predicted_up = proba_up >= 0.5

    actual_return = test_df["close"].shift(-1) / test_df["close"] - 1
    actual_return = actual_return.fillna(0).to_numpy()

    strategy_return = np.where(predicted_up, actual_return, 0.0)
    if fee_rate:
        # charge a fee whenever the position changes (enter/exit long)
        position_changed = np.diff(np.concatenate([[0], predicted_up.astype(int)])) != 0
        strategy_return = strategy_return - position_changed * fee_rate

    strategy_equity = starting_balance * np.cumprod(1 + strategy_return)
    buy_hold_equity = starting_balance * np.cumprod(1 + actual_return)

    equity_curve = pd.DataFrame(
        {
            "open_time": test_df["open_time"].to_numpy(),
            "predicted_up": predicted_up,
            "proba_up": proba_up,
            "actual_return": actual_return,
            "strategy_equity": strategy_equity,
            "buy_hold_equity": buy_hold_equity,
        }
    )

    summary = {
        "starting_balance": starting_balance,
        "strategy_final_balance": float(strategy_equity[-1]) if len(strategy_equity) else starting_balance,
        "buy_hold_final_balance": float(buy_hold_equity[-1]) if len(buy_hold_equity) else starting_balance,
        "n_periods": len(test_df),
        "pct_periods_long": float(predicted_up.mean()) if len(predicted_up) else 0.0,
    }
    return summary, equity_curve
