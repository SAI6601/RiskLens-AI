# Model card: RiskLens Logistic v1

## Summary

RiskLens Logistic v1 estimates the probability that a synthetic payment event belongs to a known fraud pattern. It supports analyst decision-making and demonstration of a measurable fraud-risk workflow.

It is **not approved for production use** and must not be used as the sole basis for denying service, closing an account or making a legal determination.

## Intended use

- Demonstrate defensive detection of card-testing, account-takeover and abuse-ring signals.
- Compare a learned risk model with a transparent rule baseline.
- Recommend reversible, bounded interventions.
- Explain each decision using ranked local feature contributions.

## Out-of-scope use

- Real payment authorization without further validation.
- Permanent automated account blocking.
- Customer profiling using protected or demographic attributes.
- Offensive testing, credential misuse or payment bypass.

## Training data

- Source: deterministic synthetic generator.
- Rows: 12,000.
- Seed: 42.
- Period: simulated 45-day event stream.
- Split: chronological 70% train, 15% validation, 15% test.
- Labels: probabilistic outcomes for three attack archetypes with legitimate overlap and noise.
- Excluded from features: label, attack type, transaction ID, merchant ID and timestamp.

Synthetic data protects privacy and makes the demonstration reproducible, but it cannot establish performance on real payments.

## Model

- Standard scaling.
- Logistic regression with balanced class weights.
- Validation-only threshold calibration.
- Threshold objective: minimum estimated cost subject to recall of at least 78%.
- Prototype review cost: ₹35 per false positive.
- Prototype missed-loss estimate: 65% of missed fraudulent transaction amount.

These cost assumptions are explicit demonstration parameters, not Razorpay business figures.

## Held-out results

| Metric | Result |
|---|---:|
| Precision | 0.756098 |
| Recall | 0.879433 |
| F1 | 0.813115 |
| ROC-AUC | 0.927312 |
| PR-AUC | 0.791757 |
| Brier score | 0.037528 |
| False-positive rate | 0.024111 |

Confusion matrix: TN 1,619, FP 40, FN 17, TP 124.

### Transparent baseline comparison

| Metric | Learned model | Rule baseline |
|---|---:|---:|
| Precision | 0.756098 | 0.400000 |
| Recall | 0.879433 | 0.751773 |
| F1 | 0.813115 | 0.522167 |
| False-positive rate | 0.024111 | 0.095841 |
| Estimated cost | ₹8,339.75 | ₹23,177.32 |

The estimated-cost comparison depends on the explicit prototype assumptions above and should not be generalized to a real business without validation.

## Controlled incident safety challenge

Five deterministic, hand-authored merchant windows exercise end-to-end safety behaviour around the transaction model:

- ordinary activity remains `normal` and is allowed;
- a legitimate flash-sale surge remains `normal` and is allowed;
- an ambiguous device shift becomes `watch` and is monitored rather than held;
- a connected card-testing burst becomes `attack` and receives bounded step-up authentication;
- the attack under a simulated model outage uses labelled fallback rules and a human-gated temporary hold.

All five currently pass. This is a regression and product-invariant suite, not an independently sampled benchmark. See [`../artifacts/incident_challenge.json`](../artifacts/incident_challenge.json).

## Explainability

For each prediction, standardized feature values are multiplied by their logistic coefficients. The three strongest positive contributions become human-readable reason codes. This explains the model's local evidence but does not prove causality.

## Incident-intelligence layer

The Merchant Risk Twin, Attack DNA, Fraud Constellation and Intervention Simulator are transparent decision-support logic around the transaction model; they are not additional trained models.

- Risk Twin deviation combines flagged-rate lift, average-risk lift, velocity, device novelty and relationship strength.
- Attack DNA values are heuristic pattern affinities, not calibrated probabilities or attacker attribution.
- Relationship analysis accepts only optional pseudonymous references and marks a shared hub after three linked transactions.
- Intervention projections use the model score and documented review/loss assumptions. They are comparative scenario estimates, not forecasts of Razorpay losses.
- Decision confidence is a boundary- and outlier-sensitive heuristic, not a conformal guarantee or confidence interval.
- Degraded mode uses labelled transparent rules and disables automation eligibility.

## Known limitations

1. Synthetic distributions do not reproduce real customer, merchant or adversary behaviour.
2. The generator covers known archetypes and may overstate generalization to novel fraud.
3. The model has not been evaluated for subgroup fairness because no demographic variables exist in the synthetic data.
4. Probability calibration has not been tested on external data.
5. Merchant spike thresholds are transparent policy rules, not statistically fitted baselines.
6. Audit persistence is a local hash-linked JSONL demonstration. It can reveal edits after the fact but is not an externally anchored, access-controlled production ledger.
7. Merchant baselines are prototype expectations supplied or derived from synthetic features, not learned production merchant profiles.
8. Attack affinities and intervention projections have not been validated on external incidents.
9. The five-window incident challenge is hand-authored and too small to estimate real-world incident-level error rates.

## Monitoring required before production

- precision, recall and PR-AUC by time and merchant cohort;
- calibration and population stability;
- false-positive friction and analyst override rate;
- new fraud-pattern coverage;
- latency, availability and failed-scoring rate;
- fairness evaluation using legally reviewed, appropriate cohorts;
- feature freshness and training-serving skew.
