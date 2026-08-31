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
    # Optional privacy-safe references support relationship analysis without
    # accepting raw PANs, device identifiers, or IP addresses.
    customer_ref: str | None = Field(default=None, min_length=1, max_length=80)
    device_ref: str | None = Field(default=None, min_length=1, max_length=80)
    payment_instrument_ref: str | None = Field(default=None, min_length=1, max_length=80)
    network_ref: str | None = Field(default=None, min_length=1, max_length=80)


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
    decision_source: Literal["risk_model", "fallback_rules"] = "risk_model"
    decision_confidence: float = Field(ge=0, le=1)
    automation_eligible: bool
    disclaimer: str


class BatchRequest(BaseModel):
    transactions: list[Transaction] = Field(min_length=1, max_length=500)
    simulate_model_failure: bool = False


class MerchantSpike(BaseModel):
    merchant_id: str
    transaction_count: int
    flagged_count: int
    flagged_rate: float
    average_risk: float
    alert: bool
    explanation: str


class RiskProfileSnapshot(BaseModel):
    average_risk: float
    flagged_rate: float
    average_velocity_10m: float
    new_device_rate: float


class MerchantRiskTwin(BaseModel):
    merchant_id: str
    status: Literal["normal", "watch", "elevated", "attack", "insufficient_evidence"]
    baseline: RiskProfileSnapshot
    observed: RiskProfileSnapshot
    deviation_score: float = Field(ge=0, le=1)
    evidence_confidence: float = Field(ge=0, le=1)
    explanation: str


class AttackSignal(BaseModel):
    code: str
    label: str
    value: float
    severity: Literal["low", "medium", "high"]


class AttackDNA(BaseModel):
    fingerprint_id: str
    dominant_pattern: Literal[
        "no_dominant_attack",
        "card_testing",
        "account_takeover",
        "abuse_ring",
        "mixed_campaign",
    ]
    pattern_affinities: dict[str, float]
    confidence: float = Field(ge=0, le=1)
    evidence_strength: Literal["weak", "moderate", "strong"]
    signals: list[AttackSignal]
    narrative: str


class ConstellationNode(BaseModel):
    id: str
    kind: Literal["merchant", "transaction", "customer", "device", "instrument", "network"]
    label: str
    transaction_count: int = 0
    suspicious: bool = False


class ConstellationEdge(BaseModel):
    source: str
    target: str
    relationship: str


class FraudConstellation(BaseModel):
    nodes: list[ConstellationNode]
    edges: list[ConstellationEdge]
    shared_hubs: int
    linked_transactions: int
    explanation: str


class InterventionOption(BaseModel):
    action: Literal["allow", "allow_and_monitor", "step_up_auth", "hold_for_review"]
    projected_loss_prevented_inr: float
    projected_residual_loss_inr: float
    estimated_total_cost_inr: float
    friction_exposure_rate: float = Field(ge=0, le=1)
    review_load: int
    reversible: bool
    recommended: bool
    rationale: str


class ActionContract(BaseModel):
    contract_id: str
    action: Literal["allow", "allow_and_monitor", "step_up_auth", "hold_for_review"]
    merchant_id: str
    expires_in_minutes: int
    transaction_limit: int
    human_gate_required: bool
    rollback_triggers: list[str]
    status: Literal["proposed"] = "proposed"


class MerchantIncident(BaseModel):
    merchant_id: str
    risk_twin: MerchantRiskTwin
    attack_dna: AttackDNA
    constellation: FraudConstellation
    interventions: list[InterventionOption]
    action_contract: ActionContract


class BatchResponse(BaseModel):
    decisions: list[RiskDecision]
    merchant_spikes: list[MerchantSpike]
    incidents: list[MerchantIncident]
    system_mode: Literal["normal", "degraded"]
    safety_notice: str
    summary: dict[str, int | float]
