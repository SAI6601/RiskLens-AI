from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=1, max_length=80)
    merchant_id: str = Field(min_length=1, max_length=80)
    timestamp: datetime | None = None
    amount: float = Field(gt=0, le=10_000_000)
    avg_amount_30d: float = Field(gt=0, le=10_000_000)
    customer_tenure_days: float = Field(ge=0, le=20_000)
    device_age_days: float = Field(ge=0, le=20_000)
    distance_from_home_km: float = Field(ge=0, le=50_000)
    failed_attempts_1h: int = Field(ge=0, le=100)
    tx_count_10m: int = Field(ge=1, le=1_000)
    shared_cards_24h: int = Field(ge=0, le=1_000)
    shared_devices_24h: int = Field(ge=0, le=1_000)
    merchant_risk_score: float = Field(ge=0, le=1)
    hour_of_day: int = Field(ge=0, le=23)
    is_international: Literal[0, 1]
    is_new_device: Literal[0, 1]
    billing_shipping_mismatch: Literal[0, 1]


class ReasonCode(BaseModel):
    code: str
    label: str
    contribution: float


class RiskDecision(BaseModel):
    transaction_id: str
    merchant_id: str
    risk_score: float
    threshold: float
    risk_band: Literal["low", "medium", "high", "critical"]
    recommended_action: Literal["allow", "allow_and_monitor", "step_up_auth", "hold_for_review"]
    reasons: list[ReasonCode]
    model_version: str
    human_review_required: bool
    disclaimer: str


class BatchRequest(BaseModel):
    transactions: list[Transaction] = Field(min_length=1, max_length=500)


class MerchantSpike(BaseModel):
    merchant_id: str
    transaction_count: int
    flagged_count: int
    flagged_rate: float
    average_risk: float
    alert: bool
    explanation: str


class BatchResponse(BaseModel):
    decisions: list[RiskDecision]
    merchant_spikes: list[MerchantSpike]
    summary: dict[str, int | float]

