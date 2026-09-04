from __future__ import annotations

import unittest
from pathlib import Path

from src.risklens.incident_benchmark import build_challenges, evaluate_incident_challenges


ROOT = Path(__file__).resolve().parents[1]


class IncidentChallengeTests(unittest.TestCase):
    def test_challenge_definitions_are_deterministic(self) -> None:
        left = [item.transactions for item in build_challenges()]
        right = [item.transactions for item in build_challenges()]
        self.assertEqual(left, right)

    def test_controlled_safety_challenge_passes(self) -> None:
        report = evaluate_incident_challenges(ROOT / "artifacts" / "model.joblib")
        self.assertEqual(report["summary"]["scenarios"], 5)
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual(report["summary"]["benign_windows_called_attack"], 0)
        self.assertEqual(report["summary"]["known_attack_windows_detected"], 1)
        self.assertEqual(report["summary"]["degraded_windows_human_gated"], 1)


if __name__ == "__main__":
    unittest.main()
