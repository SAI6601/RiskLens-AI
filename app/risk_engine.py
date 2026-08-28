from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.risklens.features import MODEL_FEATURES, prepare_features

from .schemas import MerchantSpike, RiskDecision, Transaction


REASON_LABELS = {
    "amount": ("UNUSUAL_AMOUNT", "Transaction amount increases estimated risk"),
    "avg_amount_30d": ("CUSTOMER_AMOUNT_PROFILE", "Customer amount profile increases estimated risk"),
    "amount_ratio": ("AMOUNT_DEVIATION", "Amount is high relative to the customer's recent average"),
    "customer_tenure_days": ("LIMITED_TENURE", "Limited customer history increases uncertainty"),
    "device_age_days": ("NEW_DEVICE_AGE", "Recently observed device increases estimated risk"),
    "distance_from_home_km": ("LOCATION_ANOMALY", "Transaction is far from the customer's usual location"),
    "failed_attempts_1h": ("REPEATED_FAILURES", "Recent failed attempts resemble an automated burst"),
    "tx_count_10m": ("VELOCITY_SPIKE", "Transaction velocity is unusually high"),
    "shared_cards_24h": ("SHARED_CARD_CLUSTER", "Multiple cards are linked to a recent activity cluster"),
    "shared_devices_24h": ("SHARED_DEVICE_CLUSTER", "Multiple devices are linked to a recent activity cluster"),
    "merchant_risk_score": ("MERCHANT_RISK", "Merchant's recent risk baseline is elevated"),
    "hour_of_day": ("TIME_PATTERN", "Transaction time increases estimated risk"),
    "is_international": ("INTERNATIONAL_CONTEXT", "International context increases estimated risk"),
    "is_new_device": ("NEW_DEVICE", "A newly observed device is being used"),
    "billing_shipping_mismatch": ("ADDRESS_MISMATCH", "Billing and shipping signals do not match"),
}


class RiskEngine:
    def __init__(self, artifact_path: Path) -> None:
        artifact = joblib.load(artifact_path)
        self.model = artifact["model"]
        self.threshold = float(artifact["threshold"])
        self.features = list(artifact["features"])
        self.model_version = str(artifact["model_version"])
        if self.features != MODEL_FEATURES:
            raise ValueError("Model feature contract does not match the application.")

    @staticmethod
    def _frame(transactions: list[Transaction]) -> pd.DataFrame:
        frame = pd.DataFrame([transaction.model_dump(mode="json") for transaction in transactions])
        frame["amount_ratio"] = frame["amount"] / frame["avg_amount_30d"].clip(lower=1.0)
        return frame

    def _reason_codes(self, frame: pd.DataFrame, row_index: int) -> list[dict[str, Any]]:
        scaler = self.model.named_steps["scale"]
        classifier = self.model.named_steps["classifier"]
        standardized = scaler.transform(prepare_features(frame.iloc[[row_index]]))[0]
        contributions = standardized * classifier.coef_[0]
        ranked = np.argsort(contributions)[::-1]

        reasons: list[dict[str, Any]] = []
        for index in ranked:
            contribution = float(contributions[index])
            if contribution <= 0.05:
                continue
            feature = MODEL_FEATURES[index]
            code, label = REASON_LABELS[feature]
            reasons.append({"code": code, "label": label, "contribution": round(contribution, 4)})
            if len(reasons) == 3:
                break

        if not reasons:
            reasons.append(
                {
                    "code": "NO_DOMINANT_RISK_SIGNAL",
                    "label": "No single feature materially increased the estimated risk",
                    "contribution": 0.0,
                }
            )
        return reasons

    def _band_and_action(self, score: float) -> tuple[str, str]:
        if score < 0.20:
            return "low", "allow"
        if score < self.threshold:
            return "medium", "allow_and_monitor"
        if score < 0.82:
            return "high", "step_up_auth"
        return "critical", "hold_for_review"

    def score_many(self, transactions: list[Transaction]) -> list[RiskDecision]:
        frame = self._frame(transactions)
        probabilities = self.model.predict_proba(prepare_features(frame))[:, 1]
        decisions: list[RiskDecision] = []

        for index, (transaction, score) in enumerate(zip(transactions, probabilities, strict=True)):
            score = float(score)
            band, action = self._band_and_action(score)
            decisions.append(
                RiskDecision(
                    transaction_id=transaction.transaction_id,
                    merchant_id=transaction.merchant_id,
                    risk_score=round(score, 6),
                    threshold=round(self.threshold, 4),
                    risk_band=band,
                    recommended_action=action,
                    reasons=self._reason_codes(frame, index),
                    model_version=self.model_version,
                    human_review_required=action == "hold_for_review",
                    disclaimer="Decision support only; never a permanent account block.",
                )
            )
        return decisions

    def score(self, transaction: Transaction) -> RiskDecision:
        return self.score_many([transaction])[0]

    def detect_merchant_spikes(self, decisions: list[RiskDecision]) -> list[MerchantSpike]:
        grouped: dict[str, list[RiskDecision]] = defaultdict(list)
        for decision in decisions:
            grouped[decision.merchant_id].append(decision)

        results: list[MerchantSpike] = []
        for merchant_id, items in grouped.items():
            flagged = sum(item.risk_score >= self.threshold for item in items)
            count = len(items)
            rate = flagged / count
            average = sum(item.risk_score for item in items) / count
            # A minimum volume prevents one transaction from being called a spike.
            alert = count >= 5 and rate >= 0.30 and flagged >= 3
            explanation = (
                f"{flagged} of {count} transactions exceeded the calibrated threshold."
                if alert
                else "Insufficient volume or flagged rate for a merchant-level spike."
            )
            results.append(
                MerchantSpike(
                    merchant_id=merchant_id,
                    transaction_count=count,
                    flagged_count=flagged,
                    flagged_rate=round(rate, 4),
                    average_risk=round(average, 4),
                    alert=alert,
                    explanation=explanation,
                )
            )
        return sorted(results, key=lambda item: (item.alert, item.flagged_rate), reverse=True)

