"""Deterministic merchant-window safety challenges for RiskLens.

This suite is deliberately small and controlled. It checks product invariants
that transaction-level precision and recall do not cover; it is not a substitute
for evaluation on independent payment data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.incident_engine import IncidentEngine
from app.risk_engine import RiskEngine
from app.schemas import MerchantIncident, RiskDecision, Transaction


@dataclass(frozen=True)
class Challenge:
    name: str
    category: str
    transactions: list[Transaction]
    simulate_model_failure: bool = False


def _transaction(index: int, merchant_id: str, **overrides: Any) -> Transaction:
    data: dict[str, Any] = {
        "transaction_id": f"txn_{merchant_id}_{index:03d}",
        "merchant_id": merchant_id,
        "amount": 1_100 + index * 9,
        "avg_amount_30d": 1_200,
        "customer_tenure_days": 480 + index * 7,
        "device_age_days": 180 + index * 5,
        "distance_from_home_km": 8 + index,
        "failed_attempts_1h": 0,
        "tx_count_10m": 1 + index % 2,
        "shared_cards_24h": 0,
        "shared_devices_24h": 0,
        "merchant_risk_score": 0.06,
        "hour_of_day": 12 + index % 5,
        "is_international": 0,
        "is_new_device": 0,
        "billing_shipping_mismatch": 0,
        "customer_ref": f"customer_{merchant_id}_{index:03d}",
        "device_ref": f"device_{merchant_id}_{index:03d}",
        "payment_instrument_ref": f"instrument_{merchant_id}_{index:03d}",
        "network_ref": f"network_{merchant_id}_{index:03d}",
    }
    data.update(overrides)
    return Transaction(**data)


def build_challenges() -> list[Challenge]:
    normal = [
        _transaction(index, "normal_window")
        for index in range(8)
    ]
    flash_sale = [
        _transaction(
            index,
            "legitimate_flash_sale",
            amount=780 + index * 13,
            avg_amount_30d=850,
            tx_count_10m=3 + index % 2,
            merchant_risk_score=0.04,
        )
        for index in range(16)
    ]
    ambiguous = [
        _transaction(
            index,
            "ambiguous_shift",
            device_age_days=8 + index,
            distance_from_home_km=35 + index * 4,
            failed_attempts_1h=index % 2,
            tx_count_10m=4 + index % 2,
            is_new_device=1 if index < 3 else 0,
        )
        for index in range(6)
    ]
    attack = [
        _transaction(
            index,
            "card_testing_attack",
            amount=45 + index * 7,
            avg_amount_30d=1_250,
            device_age_days=1,
            distance_from_home_km=10,
            failed_attempts_1h=8,
            tx_count_10m=18 + index % 3,
            is_new_device=1,
            device_ref="device_shared_attack",
            network_ref="network_shared_attack",
        )
        for index in range(8)
    ]
    outage = [
        transaction.model_copy(
            update={
                "transaction_id": transaction.transaction_id.replace(
                    "card_testing_attack", "model_outage_attack"
                ),
                "merchant_id": "model_outage_attack",
            }
        )
        for transaction in attack
    ]
    return [
        Challenge("ordinary merchant window", "benign", normal),
        Challenge("legitimate flash-sale surge", "benign_surge", flash_sale),
        Challenge("ambiguous device shift", "ambiguous", ambiguous),
        Challenge("connected card-testing burst", "attack", attack),
        Challenge("attack during model outage", "degraded", outage, simulate_model_failure=True),
    ]


def _checks(
    challenge: Challenge,
    decisions: list[RiskDecision],
    incident: MerchantIncident,
) -> dict[str, bool]:
    action = incident.action_contract.action
    status = incident.risk_twin.status
    common = {
        "temporary_contract": incident.action_contract.expires_in_minutes <= 30,
        "bounded_scope": incident.action_contract.transaction_limit == len(challenge.transactions),
        "no_permanent_block": action in {
            "allow", "allow_and_monitor", "step_up_auth", "hold_for_review"
        },
    }
    if challenge.category == "benign":
        return {
            **common,
            "no_attack_claim": status in {"normal", "watch"},
            "no_customer_challenge": action in {"allow", "allow_and_monitor"},
        }
    if challenge.category == "benign_surge":
        return {
            **common,
            "surge_not_called_attack": status in {"normal", "watch"},
            "surge_not_high_impact": action in {"allow", "allow_and_monitor"},
        }
    if challenge.category == "ambiguous":
        return {
            **common,
            "uncertainty_not_called_attack": status != "attack",
            "no_temporary_hold": action != "hold_for_review",
        }
    if challenge.category == "attack":
        return {
            **common,
            "attack_detected": status == "attack",
            "card_testing_identified": incident.attack_dna.dominant_pattern == "card_testing",
            "shared_hubs_found": incident.constellation.shared_hubs >= 2,
            "bounded_containment": action in {"step_up_auth", "hold_for_review"},
        }
    return {
        **common,
        "degraded_mode_labelled": all(
            decision.decision_source == "fallback_rules" for decision in decisions
        ),
        "automation_disabled": all(not decision.automation_eligible for decision in decisions),
        "human_gate_required": incident.action_contract.human_gate_required,
        "safe_degraded_action": action == "hold_for_review",
    }


def evaluate_incident_challenges(model_path: Path) -> dict[str, Any]:
    risk_engine = RiskEngine(model_path)
    incident_engine = IncidentEngine()
    results: list[dict[str, Any]] = []

    for challenge in build_challenges():
        scorer = (
            risk_engine.score_many_degraded
            if challenge.simulate_model_failure
            else risk_engine.score_many
        )
        decisions = scorer(challenge.transactions)
        incident = incident_engine.analyze(
            challenge.transactions,
            decisions,
            decisions[0].threshold,
            system_mode="degraded" if challenge.simulate_model_failure else "normal",
        )[0]
        checks = _checks(challenge, decisions, incident)
        results.append(
            {
                "name": challenge.name,
                "category": challenge.category,
                "transactions": len(challenge.transactions),
                "system_mode": "degraded" if challenge.simulate_model_failure else "normal",
                "risk_twin_status": incident.risk_twin.status,
                "average_risk": incident.risk_twin.observed.average_risk,
                "flagged_rate": incident.risk_twin.observed.flagged_rate,
                "dominant_pattern": incident.attack_dna.dominant_pattern,
                "shared_hubs": incident.constellation.shared_hubs,
                "proposed_action": incident.action_contract.action,
                "human_gate_required": incident.action_contract.human_gate_required,
                "checks": checks,
                "passed": all(checks.values()),
            }
        )

    passed = sum(result["passed"] for result in results)
    benign = [result for result in results if result["category"] in {"benign", "benign_surge"}]
    attacks = [result for result in results if result["category"] == "attack"]
    return {
        "evaluation_type": "controlled deterministic incident-safety challenge",
        "evidence_boundary": (
            "Hand-authored synthetic merchant windows test safety invariants; results are not "
            "production accuracy or independently sampled performance."
        ),
        "summary": {
            "scenarios": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "benign_windows_called_attack": sum(
                result["risk_twin_status"] == "attack" for result in benign
            ),
            "known_attack_windows_detected": sum(
                result["risk_twin_status"] == "attack" for result in attacks
            ),
            "degraded_windows_human_gated": sum(
                result["human_gate_required"]
                for result in results
                if result["category"] == "degraded"
            ),
        },
        "scenarios": results,
    }
