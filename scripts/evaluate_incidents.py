"""Run the controlled RiskLens merchant-window safety challenge."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.risklens.incident_benchmark import evaluate_incident_challenges  # noqa: E402


OUTPUT = ROOT / "artifacts" / "incident_challenge.json"


def main() -> None:
    report = evaluate_incident_challenges(ROOT / "artifacts" / "model.joblib")
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Report: {OUTPUT}")
    if report["summary"]["failed"]:
        raise SystemExit("One or more incident-safety challenges failed.")


if __name__ == "__main__":
    main()
