from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


class AuditStore:
    """Privacy-minimized append-only log with a lightweight hash chain."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def append(self, record: dict[str, Any]) -> None:
        safe_record = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "event_type": "transaction_decision",
            "transaction_id": record["transaction_id"],
            "merchant_id": record["merchant_id"],
            "risk_score": record["risk_score"],
            "risk_band": record["risk_band"],
            "recommended_action": record["recommended_action"],
            "reason_codes": [reason["code"] for reason in record["reasons"]],
            "model_version": record["model_version"],
            "decision_source": record.get("decision_source", "risk_model"),
            "automation_eligible": record.get("automation_eligible", False),
        }
        self._append_safe(safe_record)

    def append_incident(self, incident: dict[str, Any], system_mode: str) -> None:
        twin = incident["risk_twin"]
        dna = incident["attack_dna"]
        contract = incident["action_contract"]
        safe_record = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "event_type": "incident_contract",
            "merchant_id": incident["merchant_id"],
            "system_mode": system_mode,
            "twin_status": twin["status"],
            "deviation_score": twin["deviation_score"],
            "attack_fingerprint": dna["fingerprint_id"],
            "dominant_pattern": dna["dominant_pattern"],
            "pattern_confidence": dna["confidence"],
            "contract_id": contract["contract_id"],
            "proposed_action": contract["action"],
            "expires_in_minutes": contract["expires_in_minutes"],
            "transaction_limit": contract["transaction_limit"],
            "human_gate_required": contract["human_gate_required"],
        }
        self._append_safe(safe_record)

    def _append_safe(self, safe_record: dict[str, Any]) -> None:
        with self._lock:
            previous_hash = "GENESIS"
            if self.path.exists():
                lines = self.path.read_text(encoding="utf-8").splitlines()
                if lines:
                    previous_hash = json.loads(lines[-1]).get("record_hash", "UNLINKED")
            safe_record["previous_hash"] = previous_hash
            hash_payload = json.dumps(safe_record, sort_keys=True, separators=(",", ":"))
            safe_record["record_hash"] = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(safe_record, separators=(",", ":")) + "\n")

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self._lock:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines[-limit:] if line.strip()]
        return list(reversed(records))
