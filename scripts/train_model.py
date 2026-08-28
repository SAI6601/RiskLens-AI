from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from risklens.training import train_and_save  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate RiskLens AI.")
    parser.add_argument("--rows", type=int, default=12_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()

    metrics = train_and_save(args.output, rows=args.rows, seed=args.seed)
    print(json.dumps(metrics["held_out_test"], indent=2))


if __name__ == "__main__":
    main()

