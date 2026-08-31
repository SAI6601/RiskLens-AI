from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


class AuditStore:
    """Minimal append-only audit log with intentionally limited fields."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def append(self, record: dict[str, Any]) -> None:
        safe_record = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
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
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(safe_record, separators=(",", ":")) + "\n")

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self._lock:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines[-limit:] if line.strip()]
        return list(reversed(records))
