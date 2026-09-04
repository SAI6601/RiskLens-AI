from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict

from .schemas import (
    ActionContract,
    AttackDNA,
    AttackSignal,
    ConstellationEdge,
    ConstellationNode,
    FraudConstellation,
    InterventionOption,
    MerchantIncident,
    MerchantRiskTwin,
    RiskDecision,
    RiskProfileSnapshot,
    Transaction,
)


REVIEW_COST_INR = 35.0
MISSED_FRAUD_LOSS_RATE = 0.65


def _clip(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


class IncidentEngine:
    """Turn transaction scores into an explainable merchant-level incident.

    This layer intentionally uses transparent aggregations. It does not retrain
    the transaction model or claim that attack-pattern affinities are calibrated
    probabilities.
    """

    def analyze(
        self,
        transactions: list[Transaction],
        decisions: list[RiskDecision],
        threshold: float,
        system_mode: str = "normal",
    ) -> list[MerchantIncident]:
        grouped_transactions: dict[str, list[Transaction]] = defaultdict(list)
        grouped_decisions: dict[str, list[RiskDecision]] = defaultdict(list)
        for transaction, decision in zip(transactions, decisions, strict=True):
            grouped_transactions[transaction.merchant_id].append(transaction)
            grouped_decisions[decision.merchant_id].append(decision)

        incidents: list[MerchantIncident] = []
        for merchant_id, merchant_transactions in grouped_transactions.items():
            merchant_decisions = grouped_decisions[merchant_id]
            twin = self._build_twin(merchant_id, merchant_transactions, merchant_decisions, threshold)
            dna = self._build_attack_dna(merchant_id, merchant_transactions, twin)
            constellation = self._build_constellation(merchant_id, merchant_transactions, merchant_decisions)
            interventions, recommended_action = self._simulate_interventions(
                merchant_transactions,
                merchant_decisions,
                twin,
                dna,
                system_mode,
            )
            contract = self._build_action_contract(
                merchant_id,
                recommended_action,
                len(merchant_transactions),
                dna,
                system_mode,
            )
            incidents.append(
                MerchantIncident(
                    merchant_id=merchant_id,
                    risk_twin=twin,
                    attack_dna=dna,
                    constellation=constellation,
                    interventions=interventions,
                    action_contract=contract,
                )
            )

        return sorted(
            incidents,
            key=lambda incident: (
                incident.risk_twin.status == "attack",
                incident.risk_twin.deviation_score,
            ),
            reverse=True,
        )

    def _build_twin(
        self,
        merchant_id: str,
        transactions: list[Transaction],
        decisions: list[RiskDecision],
        threshold: float,
    ) -> MerchantRiskTwin:
        count = len(transactions)
        baseline_risk = sum(item.merchant_risk_score for item in transactions) / count
        expected_flagged_rate = _clip(0.015 + baseline_risk * 0.12, upper=0.20)
        expected_velocity = max(1.0, 1.0 + baseline_risk * 3.0)
        observed_risk = sum(item.risk_score for item in decisions) / count
        flagged_rate = sum(item.risk_score >= threshold for item in decisions) / count
        observed_velocity = sum(item.tx_count_10m for item in transactions) / count
        new_device_rate = sum(item.is_new_device for item in transactions) / count
        cluster_strength = sum(
            min((item.shared_cards_24h + item.shared_devices_24h) / 12.0, 1.0)
            for item in transactions
        ) / count

        risk_lift = _clip((observed_risk - baseline_risk) / max(1.0 - baseline_risk, 0.1))
        flag_lift = _clip((flagged_rate - expected_flagged_rate) / max(1.0 - expected_flagged_rate, 0.1))
        velocity_lift = _clip((observed_velocity / expected_velocity - 1.0) / 5.0)
        device_lift = _clip((new_device_rate - 0.08) / 0.92)
        deviation = _clip(
            0.34 * flag_lift
            + 0.26 * risk_lift
            + 0.18 * velocity_lift
            + 0.12 * cluster_strength
            + 0.10 * device_lift
        )

        signal_agreement = sum(
            [flag_lift >= 0.30, risk_lift >= 0.25, velocity_lift >= 0.20, cluster_strength >= 0.25]
        ) / 4.0
        evidence_confidence = _clip(0.42 + 0.33 * min(count / 8.0, 1.0) + 0.25 * signal_agreement)

        if count < 5:
            status = "insufficient_evidence"
            explanation = "The risk twin is observing this merchant, but the current window is too small for an incident claim."
        elif deviation >= 0.62 and flagged_rate >= 0.30:
            status = "attack"
            explanation = (
                f"Merchant behaviour departed sharply from baseline: {flagged_rate:.0%} of the window is flagged "
                f"and velocity is {observed_velocity / expected_velocity:.1f}x expected."
            )
        elif deviation >= 0.40:
            status = "elevated"
            explanation = "Multiple merchant-level signals are elevated; bounded verification is recommended."
        elif deviation >= 0.18:
            status = "watch"
            explanation = "A mild behavioural shift is visible, but evidence does not support an attack claim."
        else:
            status = "normal"
            explanation = "Observed traffic remains close to the merchant's behavioural baseline."

        return MerchantRiskTwin(
            merchant_id=merchant_id,
            status=status,
            baseline=RiskProfileSnapshot(
                average_risk=round(baseline_risk, 4),
                flagged_rate=round(expected_flagged_rate, 4),
                average_velocity_10m=round(expected_velocity, 2),
                new_device_rate=0.08,
            ),
            observed=RiskProfileSnapshot(
                average_risk=round(observed_risk, 4),
                flagged_rate=round(flagged_rate, 4),
                average_velocity_10m=round(observed_velocity, 2),
                new_device_rate=round(new_device_rate, 4),
            ),
            deviation_score=round(deviation, 4),
            evidence_confidence=round(evidence_confidence, 4),
            explanation=explanation,
        )

    def _build_attack_dna(
        self,
        merchant_id: str,
        transactions: list[Transaction],
        twin: MerchantRiskTwin,
    ) -> AttackDNA:
        count = len(transactions)
        average_velocity = sum(item.tx_count_10m for item in transactions) / count
        average_failures = sum(item.failed_attempts_1h for item in transactions) / count
        average_ratio = sum(item.amount / max(item.avg_amount_30d, 1.0) for item in transactions) / count
        small_amount_rate = sum(item.amount <= item.avg_amount_30d * 0.35 for item in transactions) / count
        new_device_rate = sum(item.is_new_device for item in transactions) / count
        international_rate = sum(item.is_international for item in transactions) / count
        mismatch_rate = sum(item.billing_shipping_mismatch for item in transactions) / count
        average_distance = sum(item.distance_from_home_km for item in transactions) / count
        average_cards = sum(item.shared_cards_24h for item in transactions) / count
        average_devices = sum(item.shared_devices_24h for item in transactions) / count
        average_merchant_risk = sum(item.merchant_risk_score for item in transactions) / count

        affinities = {
            "card_testing": _clip(
                0.28 * _clip((average_velocity - 3.0) / 14.0)
                + 0.25 * _clip(average_failures / 6.0)
                + 0.19 * new_device_rate
                + 0.16 * small_amount_rate
                + 0.12 * _clip(average_devices / 6.0)
            ),
            "account_takeover": _clip(
                0.25 * _clip((average_ratio - 1.5) / 4.5)
                + 0.21 * _clip(average_distance / 1_500.0)
                + 0.18 * new_device_rate
                + 0.15 * international_rate
                + 0.13 * mismatch_rate
                + 0.08 * _clip(average_failures / 5.0)
            ),
            "abuse_ring": _clip(
                0.27 * _clip(average_cards / 8.0)
                + 0.27 * _clip(average_devices / 7.0)
                + 0.18 * average_merchant_risk
                + 0.14 * _clip(average_velocity / 10.0)
                + 0.14 * _clip((average_cards + average_devices) / 12.0)
            ),
        }
        ranked = sorted(affinities.items(), key=lambda item: item[1], reverse=True)
        top_name, top_score = ranked[0]
        second_score = ranked[1][1]

        if twin.status in {"normal", "watch", "insufficient_evidence"} or top_score < 0.42:
            dominant_pattern = "no_dominant_attack"
        elif top_score - second_score <= 0.08 and second_score >= 0.48:
            dominant_pattern = "mixed_campaign"
        else:
            dominant_pattern = top_name

        confidence = _clip(top_score * (0.72 + 0.28 * min(count / 8.0, 1.0)))
        if dominant_pattern == "no_dominant_attack":
            confidence = _clip(1.0 - twin.deviation_score)
        evidence_strength = "strong" if confidence >= 0.72 else "moderate" if confidence >= 0.48 else "weak"

        signal_values = [
            ("VELOCITY", "Average transactions per 10-minute window", average_velocity, _clip(average_velocity / 15.0)),
            ("FAILED_ATTEMPTS", "Average failed attempts in the last hour", average_failures, _clip(average_failures / 6.0)),
            ("AMOUNT_DEVIATION", "Average amount relative to customer baseline", average_ratio, _clip((average_ratio - 1.0) / 4.0)),
            ("DEVICE_REUSE", "Average shared-device links", average_devices, _clip(average_devices / 7.0)),
            ("CARD_REUSE", "Average shared-card links", average_cards, _clip(average_cards / 8.0)),
            ("LOCATION_SHIFT", "Average distance from usual location", average_distance, _clip(average_distance / 1_500.0)),
        ]
        strongest = sorted(signal_values, key=lambda item: item[3], reverse=True)[:4]
        signals = [
            AttackSignal(
                code=code,
                label=label,
                value=round(value, 2),
                severity="high" if severity >= 0.70 else "medium" if severity >= 0.35 else "low",
            )
            for code, label, value, severity in strongest
        ]

        fingerprint_payload = "|".join(
            [merchant_id, dominant_pattern, *(f"{name}:{value:.2f}" for name, value in ranked)]
        )
        fingerprint = hashlib.sha256(fingerprint_payload.encode("utf-8")).hexdigest()[:8].upper()
        if dominant_pattern == "no_dominant_attack":
            narrative = "No known attack archetype has enough merchant-level evidence in this window."
        else:
            label = dominant_pattern.replace("_", " ")
            narrative = (
                f"The strongest pattern affinity is {label}; this is an explainable heuristic affinity, "
                "not a claim of attacker identity."
            )

        return AttackDNA(
            fingerprint_id=f"DNA-{fingerprint}",
            dominant_pattern=dominant_pattern,
            pattern_affinities={name: round(value, 4) for name, value in affinities.items()},
            confidence=round(confidence, 4),
            evidence_strength=evidence_strength,
            signals=signals,
            narrative=narrative,
        )

    def _build_constellation(
        self,
        merchant_id: str,
        transactions: list[Transaction],
        decisions: list[RiskDecision],
    ) -> FraudConstellation:
        reference_fields = {
            "customer_ref": "customer",
            "device_ref": "device",
            "payment_instrument_ref": "instrument",
            "network_ref": "network",
        }
        reference_counts: Counter[str] = Counter()
        for transaction in transactions:
            for field in reference_fields:
                value = getattr(transaction, field)
                if value:
                    reference_counts[f"{field}:{value}"] += 1

        nodes: list[ConstellationNode] = [
            ConstellationNode(
                id=f"merchant:{merchant_id}",
                kind="merchant",
                label=merchant_id,
                transaction_count=len(transactions),
                suspicious=False,
            )
        ]
        edges: list[ConstellationEdge] = []
        seen_references: set[str] = set()
        linked_transactions = 0

        for transaction, decision in zip(transactions, decisions, strict=True):
            has_reference = any(getattr(transaction, field) for field in reference_fields)
            if not has_reference and decision.risk_score < decision.threshold:
                continue
            transaction_node_id = f"transaction:{transaction.transaction_id}"
            nodes.append(
                ConstellationNode(
                    id=transaction_node_id,
                    kind="transaction",
                    label=transaction.transaction_id,
                    transaction_count=1,
                    suspicious=decision.risk_score >= decision.threshold,
                )
            )
            edges.append(
                ConstellationEdge(
                    source=f"merchant:{merchant_id}",
                    target=transaction_node_id,
                    relationship="received",
                )
            )
            for field, kind in reference_fields.items():
                value = getattr(transaction, field)
                if not value:
                    continue
                key = f"{field}:{value}"
                reference_node_id = f"{kind}:{value}"
                if reference_node_id not in seen_references:
                    seen_references.add(reference_node_id)
                    nodes.append(
                        ConstellationNode(
                            id=reference_node_id,
                            kind=kind,
                            label=value,
                            transaction_count=reference_counts[key],
                            suspicious=reference_counts[key] >= 3,
                        )
                    )
                edges.append(
                    ConstellationEdge(
                        source=transaction_node_id,
                        target=reference_node_id,
                        relationship=f"uses_{kind}",
                    )
                )
                if reference_counts[key] >= 3:
                    linked_transactions += 1

        shared_hubs = sum(node.suspicious for node in nodes if node.kind not in {"merchant", "transaction"})
        if not seen_references:
            explanation = "No privacy-safe relationship references were supplied for this window."
        elif shared_hubs:
            explanation = f"{shared_hubs} shared relationship hubs connect activity across this merchant window."
        else:
            explanation = "Relationship references are present, but no reference connects three or more transactions."

        return FraudConstellation(
            nodes=nodes,
            edges=edges,
            shared_hubs=shared_hubs,
            linked_transactions=min(linked_transactions, len(transactions)),
            explanation=explanation,
        )

    def _simulate_interventions(
        self,
        transactions: list[Transaction],
        decisions: list[RiskDecision],
        twin: MerchantRiskTwin,
        dna: AttackDNA,
        system_mode: str,
    ) -> tuple[list[InterventionOption], str]:
        count = len(transactions)
        projected_exposure = sum(
            transaction.amount * decision.risk_score * MISSED_FRAUD_LOSS_RATE
            for transaction, decision in zip(transactions, decisions, strict=True)
        )
        legitimate_value = sum(
            transaction.amount * (1.0 - decision.risk_score)
            for transaction, decision in zip(transactions, decisions, strict=True)
        )
        flagged = sum(decision.risk_score >= decision.threshold for decision in decisions)

        definitions = [
            ("allow", 0.00, 0.00, 0),
            ("allow_and_monitor", 0.08, min(0.05, max(1, flagged) / count * 0.08), math.ceil(flagged * 0.10)),
            ("step_up_auth", 0.72, min(1.0, max(1, flagged) / count), 0),
            ("hold_for_review", 0.88, min(1.0, max(1, flagged) / count), flagged),
        ]
        scored: list[tuple[str, float, float, int, float, float, float]] = []
        for action, prevented_fraction, friction, review_load in definitions:
            residual = projected_exposure * (1.0 - prevented_fraction)
            prevented = projected_exposure * prevented_fraction
            friction_cost = legitimate_value * friction * 0.04
            total_cost = residual + friction_cost + review_load * REVIEW_COST_INR
            scored.append((action, prevented, residual, review_load, friction, total_cost, prevented_fraction))

        if system_mode == "degraded":
            recommended_action = "hold_for_review" if twin.status in {"attack", "elevated"} else "allow_and_monitor"
        elif twin.status in {"normal", "watch", "insufficient_evidence"}:
            recommended_action = "allow" if twin.status == "normal" else "allow_and_monitor"
        elif dna.confidence < 0.55:
            recommended_action = "hold_for_review"
        else:
            eligible = [item for item in scored if item[0] in {"step_up_auth", "hold_for_review"}]
            recommended_action = min(eligible, key=lambda item: item[5])[0]

        options: list[InterventionOption] = []
        for action, prevented, residual, review_load, friction, total_cost, _ in scored:
            rationale = {
                "allow": "No payment friction, but the full model-estimated exposure remains.",
                "allow_and_monitor": "Preserves conversion while increasing observation and analyst visibility.",
                "step_up_auth": "Challenges only the risk window and remains reversible when the spike subsides.",
                "hold_for_review": "Highest containment with the largest analyst and customer-friction cost.",
            }[action]
            options.append(
                InterventionOption(
                    action=action,
                    projected_loss_prevented_inr=round(prevented, 2),
                    projected_residual_loss_inr=round(residual, 2),
                    estimated_total_cost_inr=round(total_cost, 2),
                    friction_exposure_rate=round(friction, 4),
                    review_load=review_load,
                    reversible=action != "allow",
                    recommended=action == recommended_action,
                    rationale=rationale,
                )
            )
        return options, recommended_action

    def _build_action_contract(
        self,
        merchant_id: str,
        action: str,
        transaction_count: int,
        dna: AttackDNA,
        system_mode: str,
    ) -> ActionContract:
        expiry = {"allow": 5, "allow_and_monitor": 30, "step_up_auth": 15, "hold_for_review": 10}[action]
        contract_payload = f"{merchant_id}|{action}|{dna.fingerprint_id}|{system_mode}"
        contract_hash = hashlib.sha256(contract_payload.encode("utf-8")).hexdigest()[:10].upper()
        return ActionContract(
            contract_id=f"ACT-{contract_hash}",
            action=action,
            merchant_id=merchant_id,
            expires_in_minutes=expiry,
            transaction_limit=max(transaction_count, 1),
            human_gate_required=action == "hold_for_review" or system_mode == "degraded" or dna.confidence < 0.55,
            rollback_triggers=[
                "Merchant deviation remains below 0.25 for two consecutive windows",
                "Estimated legitimate-customer friction exceeds 5%",
                "An analyst rejects the incident evidence",
            ],
        )
