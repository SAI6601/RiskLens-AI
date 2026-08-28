"""Deterministic synthetic payment data for a safe, reproducible demo.

The generator models three defensive fraud scenarios. It is deliberately
synthetic: no cardholder data, credentials, or real Razorpay transactions are
used. Fraud labels are never passed into the model as features.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd


ATTACK_TYPES = np.array(["legitimate", "card_testing", "account_takeover", "abuse_ring"])


def generate_transactions(
    rows: int = 12_000,
    seed: int = 42,
    start: datetime | None = None,
) -> pd.DataFrame:
    if rows < 500:
        raise ValueError("At least 500 rows are required for a stable evaluation.")

    rng = np.random.default_rng(seed)
    start = start or datetime(2026, 7, 1, tzinfo=timezone.utc)
    seconds = np.sort(rng.integers(0, 45 * 24 * 3600, size=rows))
    timestamps = [start + timedelta(seconds=int(value)) for value in seconds]

    frame = pd.DataFrame(
        {
            "transaction_id": [f"txn_demo_{i:06d}" for i in range(rows)],
            "timestamp": timestamps,
            "merchant_id": rng.choice([f"merchant_{i:03d}" for i in range(60)], rows),
            "amount": np.clip(rng.lognormal(6.0, 0.9, rows), 20, 60_000),
            "avg_amount_30d": np.clip(rng.lognormal(6.0, 0.65, rows), 50, 25_000),
            "customer_tenure_days": np.clip(rng.gamma(2.5, 150, rows), 0, 2_500),
            "device_age_days": np.clip(rng.gamma(2.0, 90, rows), 0, 1_500),
            "distance_from_home_km": np.clip(rng.exponential(18, rows), 0, 5_000),
            "failed_attempts_1h": np.clip(rng.poisson(0.25, rows), 0, 12),
            "tx_count_10m": np.clip(rng.poisson(1.2, rows) + 1, 1, 35),
            "shared_cards_24h": np.clip(rng.poisson(0.15, rows), 0, 15),
            "shared_devices_24h": np.clip(rng.poisson(0.2, rows), 0, 15),
            "merchant_risk_score": np.clip(rng.beta(2, 9, rows), 0, 1),
            "hour_of_day": [stamp.hour for stamp in timestamps],
            "is_international": rng.binomial(1, 0.05, rows),
            "is_new_device": rng.binomial(1, 0.08, rows),
            "billing_shipping_mismatch": rng.binomial(1, 0.06, rows),
        }
    )

    attack_type = rng.choice(ATTACK_TYPES, rows, p=[0.91, 0.035, 0.035, 0.02])
    frame["attack_type"] = attack_type

    card_testing = frame["attack_type"] == "card_testing"
    frame.loc[card_testing, "amount"] = rng.uniform(10, 350, card_testing.sum())
    frame.loc[card_testing, "tx_count_10m"] = rng.integers(7, 30, card_testing.sum())
    frame.loc[card_testing, "failed_attempts_1h"] = rng.integers(2, 9, card_testing.sum())
    frame.loc[card_testing, "device_age_days"] = rng.uniform(0, 8, card_testing.sum())
    frame.loc[card_testing, "is_new_device"] = rng.binomial(1, 0.82, card_testing.sum())

    takeover = frame["attack_type"] == "account_takeover"
    frame.loc[takeover, "amount"] = (
        frame.loc[takeover, "avg_amount_30d"] * rng.uniform(2.5, 8, takeover.sum())
    ).clip(upper=60_000)
    frame.loc[takeover, "distance_from_home_km"] = rng.uniform(250, 5_000, takeover.sum())
    frame.loc[takeover, "device_age_days"] = rng.uniform(0, 15, takeover.sum())
    frame.loc[takeover, "is_new_device"] = rng.binomial(1, 0.8, takeover.sum())
    frame.loc[takeover, "is_international"] = rng.binomial(1, 0.65, takeover.sum())
    frame.loc[takeover, "billing_shipping_mismatch"] = rng.binomial(1, 0.55, takeover.sum())

    abuse_ring = frame["attack_type"] == "abuse_ring"
    frame.loc[abuse_ring, "shared_cards_24h"] = rng.integers(3, 13, abuse_ring.sum())
    frame.loc[abuse_ring, "shared_devices_24h"] = rng.integers(3, 11, abuse_ring.sum())
    frame.loc[abuse_ring, "merchant_risk_score"] = rng.uniform(0.55, 0.98, abuse_ring.sum())
    frame.loc[abuse_ring, "tx_count_10m"] = rng.integers(3, 14, abuse_ring.sum())

    # Labels include overlap and noise so the evaluation is not artificially perfect.
    fraud_probability = np.where(frame["attack_type"] == "legitimate", 0.008, 0.86)
    fraud_probability = np.where(card_testing & (frame["failed_attempts_1h"] < 3), 0.62, fraud_probability)
    fraud_probability = np.where(takeover & (frame["is_new_device"] == 0), 0.58, fraud_probability)
    frame["is_fraud"] = rng.binomial(1, fraud_probability).astype(int)
    frame["amount_ratio"] = frame["amount"] / frame["avg_amount_30d"].clip(lower=1)

    # An unseen merchant burst in the final period tests production-like drift.
    cutoff = frame["timestamp"].quantile(0.88)
    spike_candidates = frame.index[
        (frame["timestamp"] >= cutoff) & (frame["merchant_id"].isin(["merchant_007", "merchant_021"]))
    ]
    if len(spike_candidates):
        chosen = rng.choice(spike_candidates, size=max(1, len(spike_candidates) // 3), replace=False)
        frame.loc[chosen, "tx_count_10m"] = rng.integers(8, 24, len(chosen))
        frame.loc[chosen, "failed_attempts_1h"] = rng.integers(2, 7, len(chosen))
        frame.loc[chosen, "is_new_device"] = 1
        frame.loc[chosen, "is_fraud"] = rng.binomial(1, 0.78, len(chosen))
        frame.loc[chosen, "attack_type"] = "merchant_fraud_spike"

    return frame.sort_values("timestamp").reset_index(drop=True)

