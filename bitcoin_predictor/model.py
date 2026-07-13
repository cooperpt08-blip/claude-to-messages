"""Train, evaluate, save, and load the direction-prediction model."""

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import config
from .features import FEATURE_COLUMNS, TARGET_COLUMN


def _build_pipeline():
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                GradientBoostingClassifier(
                    n_estimators=200,
                    max_depth=3,
                    learning_rate=0.05,
                    random_state=config.RANDOM_STATE,
                ),
            ),
        ]
    )


def time_ordered_split(feature_df, test_size=None):
    """Split a feature dataframe into train/test preserving time order (no
    shuffling — shuffling would leak future information into training)."""
    test_size = config.TEST_SIZE if test_size is None else test_size
    n = len(feature_df)
    split_idx = int(n * (1 - test_size))
    train_df = feature_df.iloc[:split_idx]
    test_df = feature_df.iloc[split_idx:]
    return train_df, test_df


def train(feature_df):
    """Train on all but the most recent `TEST_SIZE` fraction of rows, then
    evaluate on the held-out (chronologically later) rows.

    Returns (pipeline, metrics_dict, test_df).
    """
    train_df, test_df = time_ordered_split(feature_df)

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[TARGET_COLUMN]

    pipeline = _build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    metrics = {
        "n_train": len(train_df),
        "n_test": len(test_df),
        "accuracy": accuracy_score(y_test, y_pred),
        "baseline_majority_accuracy": max(y_test.mean(), 1 - y_test.mean()),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(y_test, y_pred, target_names=["down", "up"]),
    }
    return pipeline, metrics, test_df


def save(pipeline, path=None):
    path = path or config.MODEL_PATH
    joblib.dump({"pipeline": pipeline, "feature_columns": FEATURE_COLUMNS}, path)
    return path


def load(path=None):
    path = path or config.MODEL_PATH
    bundle = joblib.load(path)
    return bundle["pipeline"], bundle["feature_columns"]


def predict_direction(pipeline, feature_row):
    """feature_row: a single-row dataframe with FEATURE_COLUMNS present.
    Returns (direction: "up"|"down", probability_up: float).
    """
    X = feature_row[FEATURE_COLUMNS]
    proba_up = pipeline.predict_proba(X)[0][1]
    direction = "up" if proba_up >= 0.5 else "down"
    return direction, float(proba_up)
