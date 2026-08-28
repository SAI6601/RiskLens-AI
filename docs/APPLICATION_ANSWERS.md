# Razorpay Buildathon application draft

Review and personalize these answers before final submission.

## Selected track

Track 2: AI Risk Manager

## Project name / title

RiskLens AI — Explainable Payment Fraud-Spike Sentinel

## Project objectives — What does it solve?

RiskLens AI detects suspicious payment events and sudden merchant-level fraud bursts while keeping every intervention explainable, reversible and human-gated. It combines an interpretable fraud-risk model with validation-only threshold calibration, reason codes, merchant spike guards and a privacy-minimized audit trail. Instead of returning only a black-box fraud score, it recommends one bounded action—allow, monitor, step-up authentication or hold for analyst review—and records the evidence behind that recommendation.

The prototype is evaluated honestly on a chronologically held-out synthetic dataset. It reports precision, recall, F1, false-positive rate, false-positive review cost and missed fraud amount, along with a transparent rule baseline. The goal is to demonstrate how an AI Risk Manager can reduce payment loss without hiding customer-friction costs or automatically making permanent account decisions.

## GitHub repository URL

`TO ADD AFTER THE PUBLIC REPOSITORY IS CREATED`

## Five-minute pitch video link

`TO ADD AFTER THE VIDEO IS RECORDED AND UPLOADED`

## Build challenges and technical obstacles

The first challenge was avoiding an unrealistic model that looked accurate only because of label leakage. I created one shared feature contract, excluded IDs, timestamps, attack-type metadata and labels from training, and used a chronological 70/15/15 split so future events never entered training. The operating threshold was selected only on validation data and frozen before the held-out test.

The second challenge was balancing fraud recall against customer friction. Instead of choosing an arbitrary 0.5 threshold, I made the cost assumptions explicit and calibrated the threshold under a recall constraint. The evaluation separately reports false positives, their estimated review cost and missed fraud amount.

The third challenge was making the model useful to an analyst without giving it unsafe authority. I used an interpretable logistic model, generated reason codes from local feature contributions, and placed a policy gate after scoring. The strongest action is only a temporary hold for human review; the system never recommends permanent automatic blocking.

Finally, a single high-risk transaction should not be called a merchant fraud spike. I added minimum-volume, flagged-count and flagged-rate guards, then tested both the insufficient-volume case and a controlled fraud-burst batch.

## Final-submission checklist

- [ ] Repository is public and cloneable.
- [ ] README commands work in a clean environment.
- [ ] Held-out metrics match `artifacts/metrics.json`.
- [ ] Architecture diagram renders correctly on GitHub.
- [ ] Five-minute video is publicly viewable.
- [ ] Video demonstrates normal, single-risk and batch-spike flows.
- [ ] Personal details and internship-duration choice are confirmed.
- [ ] No secrets, private datasets or personal information are committed.
- [ ] Final form answers are proofread before confirmation.

