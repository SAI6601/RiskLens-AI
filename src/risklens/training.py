"""Train, calibrate and evaluate the explainable payment-risk model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import MODEL_FEATURES, prepare_features
from .synthetic_data import generate_transactions


REVIEW_COST_INR = 35.0
MISSED_FRAUD_LOSS_RATE = 0.65
MODEL_VERSION = "risklens-logistic-v1"


def chronological_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    first = int(len(frame) * 0.70)
    second = int(len(frame) * 0.85)
    return frame.iloc[:first].copy(), frame.iloc[first:second].copy(), frame.iloc[second:].copy()


def business_cost(y_true: np.ndarray, predicted: np.ndarray, amounts: np.ndarray) -> float:
    false_positives = int(((predicted == 1) & (y_true == 0)).sum())
    false_negatives = (predicted == 0) & (y_true == 1)
    missed_amount = float(amounts[false_negatives].sum())
    return false_positives * REVIEW_COST_INR + missed_amount * MISSED_FRAUD_LOSS_RATE


def select_threshold(y_true: np.ndarray, probabilities: np.ndarray, amounts: np.ndarray) -> dict[str, float]:
    candidates: list[dict[str, float]] = []
    for threshold in np.linspace(0.05, 0.95, 181):
        predicted = (probabilities >= threshold).astype(int)
        recall = recall_score(y_true, predicted, zero_division=0)
        candidates.append(
            {
                "threshold": float(threshold),
                "recall": float(recall),
                "precision": float(precision_score(y_true, predicted, zero_division=0)),
                "cost": business_cost(y_true, predicted, amounts),
            }
        )

    recall_safe = [item for item in candidates if item["recall"] >= 0.78]
    pool = recall_safe or candidates
    return min(pool, key=lambda item: (item["cost"], -item["precision"]))


def evaluate(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    threshold: float,
) -> dict[str, Any]:
    y_true = frame["is_fraud"].to_numpy(dtype=int)
    predicted = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    false_positive_rate = fp / max(fp + tn, 1)
    missed_amount = float(frame.loc[(predicted == 0) & (y_true == 1), "amount"].sum())
    caught_amount = float(frame.loc[(predicted == 1) & (y_true == 1), "amount"].sum())

    return {
        "rows": int(len(frame)),
        "fraud_prevalence": round(float(y_true.mean()), 6),
        "threshold": round(float(threshold), 4),
        "precision": round(float(precision_score(y_true, predicted, zero_division=0)), 6),
        "recall": round(float(recall_score(y_true, predicted, zero_division=0)), 6),
        "f1": round(float(f1_score(y_true, predicted, zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 6),
        "pr_auc": round(float(average_precision_score(y_true, probabilities)), 6),
        "brier_score": round(float(brier_score_loss(y_true, probabilities)), 6),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "false_positive_rate": round(float(false_positive_rate), 6),
        "false_positive_review_cost_inr": round(float(fp * REVIEW_COST_INR), 2),
        "caught_fraud_amount_inr": round(caught_amount, 2),
        "missed_fraud_amount_inr": round(missed_amount, 2),
        "estimated_total_cost_inr": round(
            float(fp * REVIEW_COST_INR + missed_amount * MISSED_FRAUD_LOSS_RATE), 2
        ),
    }


def evaluate_rule_baseline(frame: pd.DataFrame) -> dict[str, Any]:
    predicted = (
        (frame["tx_count_10m"] >= 9)
        | (frame["amount_ratio"] >= 4.5)
        | ((frame["shared_cards_24h"] >= 4) & (frame["shared_devices_24h"] >= 3))
    ).astype(int).to_numpy()
    # Binary predictions are used as coarse scores for a transparent baseline.
    return evaluate(frame, predicted.astype(float), threshold=0.5)


def train_and_save(output_dir: Path, rows: int = 12_000, seed: int = 42) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = generate_transactions(rows=rows, seed=seed)
    train, validation, test = chronological_split(frame)

    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2_000,
                    class_weight="balanced",
                    random_state=seed,
                    solver="lbfgs",
                ),
            ),
        ]
    )
    model.fit(prepare_features(train), train["is_fraud"])

    validation_probabilities = model.predict_proba(prepare_features(validation))[:, 1]
    selected = select_threshold(
        validation["is_fraud"].to_numpy(dtype=int),
        validation_probabilities,
        validation["amount"].to_numpy(dtype=float),
    )
    threshold = selected["threshold"]
    test_probabilities = model.predict_proba(prepare_features(test))[:, 1]

    metrics = {
        "model_version": MODEL_VERSION,
        "data": {
            "source": "deterministic synthetic payment transactions",
            "seed": seed,
            "total_rows": rows,
            "split": {"train": len(train), "validation": len(validation), "test": len(test)},
            "leakage_control": "chronological 70/15/15 split; labels and attack_type excluded",
        },
        "threshold_selection": {
            "dataset": "validation only",
            "objective": "minimum estimated business cost with recall >= 0.78",
            **{key: round(float(value), 6) for key, value in selected.items()},
            "review_cost_inr": REVIEW_COST_INR,
            "missed_fraud_loss_rate": MISSED_FRAUD_LOSS_RATE,
        },
        "held_out_test": evaluate(test, test_probabilities, threshold),
        "rule_baseline_test": evaluate_rule_baseline(test),
        "limitations": [
            "Results are from synthetic data and are not production performance claims.",
            "Labels approximate three known fraud archetypes and may not represent novel attacks.",
            "Human review is required for high-risk decisions; the model never permanently blocks an account.",
        ],
    }

    artifact = {
        "model": model,
        "threshold": threshold,
        "features": MODEL_FEATURES,
        "model_version": MODEL_VERSION,
    }
    joblib.dump(artifact, output_dir / "model.joblib")
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    coefficient_frame = pd.DataFrame(
        {
            "feature": MODEL_FEATURES,
            "coefficient": model.named_steps["classifier"].coef_[0],
        }
    ).sort_values("coefficient", ascending=False)
    coefficient_frame.to_csv(output_dir / "feature_coefficients.csv", index=False)

    demo_columns = [
        "transaction_id",
        "timestamp",
        "merchant_id",
        *MODEL_FEATURES,
        "is_fraud",
        "attack_type",
    ]
    test.sample(n=min(200, len(test)), random_state=seed)[demo_columns].to_csv(
        output_dir / "held_out_sample.csv", index=False
    )
    return metrics

