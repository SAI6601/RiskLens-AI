from __future__ import annotations

import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.audit import AuditStore
from app.incident_engine import IncidentEngine
from app.main import app
from app.risk_engine import RiskEngine
from app.schemas import Transaction
from src.risklens.synthetic_data import generate_transactions
from src.risklens.training import chronological_split


ROOT = Path(__file__).resolve().parents[1]


def normal_transaction(**overrides) -> Transaction:
    data = {
        "transaction_id": "txn_test_normal",
        "merchant_id": "merchant_test",
        "amount": 1_200,
        "avg_amount_30d": 1_350,
        "customer_tenure_days": 600,
        "device_age_days": 250,
        "distance_from_home_km": 5,
        "failed_attempts_1h": 0,
        "tx_count_10m": 1,
        "shared_cards_24h": 0,
        "shared_devices_24h": 0,
        "merchant_risk_score": 0.08,
        "hour_of_day": 14,
        "is_international": 0,
        "is_new_device": 0,
        "billing_shipping_mismatch": 0,
    }
    data.update(overrides)
    return Transaction(**data)


class SyntheticDataTests(unittest.TestCase):
    def test_generator_is_deterministic_and_has_no_obvious_label_leakage(self) -> None:
        left = generate_transactions(rows=600, seed=9)
        right = generate_transactions(rows=600, seed=9)
        self.assertEqual(left["is_fraud"].tolist(), right["is_fraud"].tolist())
        self.assertGreater(left["is_fraud"].mean(), 0.03)
        self.assertLess(left["is_fraud"].mean(), 0.20)

    def test_chronological_split_keeps_future_out_of_training(self) -> None:
        frame = generate_transactions(rows=600, seed=10)
        train, validation, test = chronological_split(frame)
        self.assertLessEqual(train["timestamp"].max(), validation["timestamp"].min())
        self.assertLessEqual(validation["timestamp"].max(), test["timestamp"].min())
        self.assertEqual(len(train) + len(validation) + len(test), len(frame))


class RiskEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = RiskEngine(ROOT / "artifacts" / "model.joblib")

    def test_low_risk_payment_is_allowed(self) -> None:
        decision = self.engine.score(normal_transaction())
        self.assertIn(decision.recommended_action, {"allow", "allow_and_monitor"})
        self.assertFalse(decision.human_review_required)

    def test_card_testing_burst_is_explained_and_bounded(self) -> None:
        transaction = normal_transaction(
            transaction_id="txn_test_burst",
            amount=75,
            device_age_days=1,
            failed_attempts_1h=7,
            tx_count_10m=20,
            is_new_device=1,
        )
        decision = self.engine.score(transaction)
        codes = {reason.code for reason in decision.reasons}
        self.assertGreaterEqual(decision.risk_score, self.engine.threshold)
        self.assertTrue({"VELOCITY_SPIKE", "REPEATED_FAILURES"} & codes)
        self.assertNotIn("block", decision.recommended_action)

    def test_batch_requires_volume_before_calling_a_spike(self) -> None:
        attack = normal_transaction(
            amount=55,
            device_age_days=1,
            failed_attempts_1h=7,
            tx_count_10m=18,
            is_new_device=1,
        )
        small = self.engine.score_many([attack.model_copy(update={"transaction_id": f"txn_{i}"}) for i in range(2)])
        self.assertFalse(self.engine.detect_merchant_spikes(small)[0].alert)

        large = self.engine.score_many([attack.model_copy(update={"transaction_id": f"txn_{i}"}) for i in range(6)])
        self.assertTrue(self.engine.detect_merchant_spikes(large)[0].alert)

    def test_risk_twin_identifies_card_testing_and_relationship_hubs(self) -> None:
        transactions = [
            normal_transaction(
                transaction_id=f"txn_ring_{index}",
                merchant_id="merchant_007",
                amount=45 + index * 12,
                device_age_days=1,
                failed_attempts_1h=6,
                tx_count_10m=14 + index,
                is_new_device=1,
                device_ref="device_shared_demo",
                network_ref="network_shared_demo",
                payment_instrument_ref=f"instrument_{index}",
            )
            for index in range(7)
        ]
        decisions = self.engine.score_many(transactions)
        incident = IncidentEngine().analyze(
            transactions,
            decisions,
            self.engine.threshold,
        )[0]

        self.assertEqual(incident.risk_twin.status, "attack")
        self.assertEqual(incident.attack_dna.dominant_pattern, "card_testing")
        self.assertGreaterEqual(incident.constellation.shared_hubs, 2)
        self.assertEqual(incident.action_contract.action, "step_up_auth")
        self.assertTrue(any(option.recommended for option in incident.interventions))

    def test_risk_twin_does_not_claim_attack_from_one_payment(self) -> None:
        transaction = normal_transaction(
            transaction_id="txn_single_suspicious",
            failed_attempts_1h=8,
            tx_count_10m=20,
            is_new_device=1,
        )
        decision = self.engine.score(transaction)
        incident = IncidentEngine().analyze(
            [transaction],
            [decision],
            self.engine.threshold,
        )[0]
        self.assertEqual(incident.risk_twin.status, "insufficient_evidence")
        self.assertEqual(incident.attack_dna.dominant_pattern, "no_dominant_attack")


class AuditTests(unittest.TestCase):
    def test_audit_log_excludes_raw_transaction_features(self) -> None:
        store = AuditStore(ROOT / "data" / "audit" / "test_decisions.jsonl")
        store.append(
            {
                "transaction_id": "txn_1",
                "merchant_id": "merchant_1",
                "risk_score": 0.8,
                "risk_band": "high",
                "recommended_action": "step_up_auth",
                "reasons": [{"code": "VELOCITY_SPIKE"}],
                "model_version": "test",
                "amount": 99_999,
            }
        )
        record = store.recent(1)[0]
        self.assertNotIn("amount", record)
        self.assertEqual(record["reason_codes"], ["VELOCITY_SPIKE"])
        self.assertEqual(record["event_type"], "transaction_decision")
        self.assertIn("record_hash", record)

    def test_audit_records_are_hash_linked(self) -> None:
        store = AuditStore(ROOT / "data" / "audit" / "test_hash_chain.jsonl")
        record = {
            "transaction_id": "txn_hash",
            "merchant_id": "merchant_hash",
            "risk_score": 0.4,
            "risk_band": "medium",
            "recommended_action": "allow_and_monitor",
            "reasons": [{"code": "VELOCITY_SPIKE"}],
            "model_version": "test",
        }
        store.append(record)
        store.append({**record, "transaction_id": "txn_hash_2"})
        newest, previous = store.recent(2)
        self.assertEqual(newest["previous_hash"], previous["record_hash"])


class ApiTests(unittest.TestCase):
    def test_health_score_metrics_and_validation(self) -> None:
        with TestClient(app) as client:
            health = client.get("/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()["status"], "healthy")

            response = client.post("/api/score", json=normal_transaction().model_dump(mode="json"))
            self.assertEqual(response.status_code, 200)
            self.assertIn("reasons", response.json())

            metrics = client.get("/api/metrics")
            self.assertEqual(metrics.status_code, 200)
            self.assertIn("held_out_test", metrics.json())

            invalid = normal_transaction().model_dump(mode="json")
            invalid["amount"] = -1
            rejected = client.post("/api/score", json=invalid)
            self.assertEqual(rejected.status_code, 422)

    def test_degraded_batch_disables_automation_and_requires_safe_contract(self) -> None:
        transactions = [
            normal_transaction(
                transaction_id=f"txn_degraded_{index}",
                merchant_id="merchant_degraded",
                failed_attempts_1h=8,
                tx_count_10m=20,
                is_new_device=1,
            ).model_dump(mode="json")
            for index in range(6)
        ]
        with TestClient(app) as client:
            response = client.post(
                "/api/batch",
                json={"transactions": transactions, "simulate_model_failure": True},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["system_mode"], "degraded")
        self.assertTrue(all(not item["automation_eligible"] for item in payload["decisions"]))
        self.assertTrue(payload["incidents"][0]["action_contract"]["human_gate_required"])


if __name__ == "__main__":
    unittest.main()
