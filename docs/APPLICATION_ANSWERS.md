# Razorpay Buildathon application draft

Review and personalize these answers before final submission.

## Selected track

Track 2: AI Risk Manager

## Project name / title

RiskLens AI — Merchant Risk Twin and Attack Response Simulator

## Project objectives — What does it solve?

RiskLens AI creates a live behavioural twin of a merchant to detect when normal payment activity becomes a coordinated attack. It combines an interpretable fraud-risk model with Attack DNA affinities, a privacy-safe relationship constellation and an intervention simulator. Instead of returning only a black-box score, it explains how the merchant departed from baseline, surfaces shared device or network hubs, compares the customer-friction and loss implications of four responses, and proposes a temporary action contract with an expiry, scope and rollback triggers.

The prototype is evaluated honestly on a chronologically held-out synthetic dataset. It reports precision, recall, F1, false-positive rate, false-positive review cost and missed fraud amount, along with a transparent rule baseline. The goal is to demonstrate how an AI Risk Manager can reduce payment loss without hiding customer-friction costs or automatically making permanent account decisions.

When the primary model is unavailable, RiskLens visibly enters degraded mode, switches to labelled fallback rules, disables automation and human-gates high-impact actions. Attack affinities and intervention projections are explicitly presented as synthetic decision-support estimates, not attacker attribution or production guarantees.

## GitHub repository URL

https://github.com/SAI6601/RiskLens-AI

## Five-minute pitch video link

`PASTE THE PUBLIC YOUTUBE OR GOOGLE DRIVE LINK AFTER UPLOAD`

## Build challenges and technical obstacles

The first challenge was avoiding an unrealistic model that looked accurate only because of label leakage. I created one shared feature contract, excluded IDs, timestamps, attack-type metadata and labels from training, and used a chronological 70/15/15 split so future events never entered training. The operating threshold was selected only on validation data and frozen before the held-out test.

The second challenge was balancing fraud recall against customer friction. Instead of choosing an arbitrary 0.5 threshold, I made the cost assumptions explicit and calibrated the threshold under a recall constraint. The evaluation separately reports false positives, their estimated review cost and missed fraud amount.

The third challenge was making the model useful to an analyst without giving it unsafe authority. I used an interpretable logistic model, generated reason codes from local feature contributions, and placed a policy gate after scoring. The strongest action is only a temporary hold for human review; the system never recommends permanent automatic blocking.

Finally, a single high-risk transaction should not be called a merchant fraud spike. I added minimum-volume, flagged-count and flagged-rate guards, then tested both the insufficient-volume case and a controlled fraud-burst batch.

The final challenge was moving from a score to a responsible incident decision. I added a Merchant Risk Twin, heuristic Attack DNA, pseudonymous relationship hubs and a four-option intervention simulator. Every output remains bounded by a temporary action contract. I also implemented a demonstrable model-failure path that disables automation and requires human review instead of silently fabricating confidence.

## Final-submission checklist

- [ ] Repository is public and cloneable.
- [x] README commands work in a clean environment.
- [x] Held-out metrics match `artifacts/metrics.json`.
- [ ] Architecture diagram renders correctly on GitHub.
- [ ] Five-minute video is publicly viewable.
- [ ] Video demonstrates the Risk Twin, Attack DNA, constellation, intervention comparison and graceful model failure.
- [ ] Personal details and internship-duration choice are confirmed.
- [x] No secrets, private datasets or personal information are committed.
- [x] Project objective and technical-challenge answers are proofread.
