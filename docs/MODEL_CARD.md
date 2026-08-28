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

## Explainability

For each prediction, standardized feature values are multiplied by their logistic coefficients. The three strongest positive contributions become human-readable reason codes. This explains the model's local evidence but does not prove causality.

## Known limitations

1. Synthetic distributions do not reproduce real customer, merchant or adversary behaviour.
2. The generator covers known archetypes and may overstate generalization to novel fraud.
3. The model has not been evaluated for subgroup fairness because no demographic variables exist in the synthetic data.
4. Probability calibration has not been tested on external data.
5. Merchant spike thresholds are transparent policy rules, not statistically fitted baselines.
6. Audit persistence is a local JSONL demonstration, not a tamper-evident production ledger.

## Monitoring required before production

- precision, recall and PR-AUC by time and merchant cohort;
- calibration and population stability;
- false-positive friction and analyst override rate;
- new fraud-pattern coverage;
- latency, availability and failed-scoring rate;
- fairness evaluation using legally reviewed, appropriate cohorts;
- feature freshness and training-serving skew.
