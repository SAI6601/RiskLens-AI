"""Shared feature contract for training and online inference."""

from __future__ import annotations

import pandas as pd


MODEL_FEATURES = [
    "amount",
    "avg_amount_30d",
    "amount_ratio",
    "customer_tenure_days",
    "device_age_days",
    "distance_from_home_km",
    "failed_attempts_1h",
    "tx_count_10m",
    "shared_cards_24h",
    "shared_devices_24h",
    "merchant_risk_score",
    "hour_of_day",
    "is_international",
    "is_new_device",
    "billing_shipping_mismatch",
]


def prepare_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return model features in a stable order with safe derived values."""
    prepared = frame.copy()
    if "amount_ratio" not in prepared:
        denominator = prepared["avg_amount_30d"].clip(lower=1.0)
        prepared["amount_ratio"] = prepared["amount"] / denominator

    missing = sorted(set(MODEL_FEATURES) - set(prepared.columns))
    if missing:
        raise ValueError(f"Missing required model features: {', '.join(missing)}")

    result = prepared[MODEL_FEATURES].astype(float)
    if result.isna().any().any():
        bad = result.columns[result.isna().any()].tolist()
        raise ValueError(f"Null values are not accepted for: {', '.join(bad)}")
    return result

