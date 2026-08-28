# RiskLens AI architecture

## User-facing decision flow

```mermaid
flowchart TD
    A[Analyst selects or submits a transaction] --> B[RiskLens validates every field]
    B --> C[Model estimates fraud risk]
    C --> D[Analyst receives score and top reasons]
    D --> E{Policy gate}
    E -->|Low| F[Allow]
    E -->|Medium| G[Allow and monitor]
    E -->|High| H[Step-up authentication]
    E -->|Critical| I[Hold for human review]
    F --> J[Record audit evidence]
    G --> J
    H --> J
    I --> J
```

## Internal processing flow

```mermaid
flowchart LR
    A[Pydantic input contract] --> B[Derived amount ratio]
    B --> C[Stable 15-feature order]
    C --> D[StandardScaler]
    D --> E[Balanced logistic classifier]
    E --> F[Calibrated probability]
    D --> G[Feature x coefficient contributions]
    G --> H[Top three positive reason codes]
    F --> I[Action thresholds]
    F --> J[Per-merchant aggregation]
    J --> K[Volume + flagged-rate guard]
    H --> L[Decision response]
    I --> L
    K --> M[Merchant spike response]
    L --> N[Minimal append-only audit record]
```

## Component responsibilities

| Component | Purpose | Key design choice |
|---|---|---|
| `schemas.py` | Reject malformed or extreme inputs | Closed schema; unknown fields rejected |
| `features.py` | Keep training and inference identical | One shared ordered feature contract |
| `training.py` | Train, calibrate and freeze evidence | Chronological split; validation-only threshold |
| `risk_engine.py` | Score, explain and apply action policy | Interpretable contributions and bounded actions |
| `audit.py` | Preserve review evidence | Excludes raw feature values and credentials |
| `main.py` | Expose dashboard and APIs | Max 500 transactions per batch |
| dashboard | Demonstrate normal and fraud scenarios | Calls the same public APIs as any client |

## Decision policy

| Risk interval | Recommended action | Human impact |
|---|---|---|
| `< 0.20` | Allow | None |
| `0.20` to calibrated threshold | Allow and monitor | Passive observation |
| Threshold to `< 0.82` | Step-up authentication | Reversible verification friction |
| `>= 0.82` | Hold for review | Temporary hold; human decision required |

The calibrated fraud threshold is currently `0.475`. It was selected on validation data only. The `0.82` critical-action boundary is a transparent prototype policy, not a learned production rule.

## Failure handling

- Invalid values and unknown fields return HTTP 422.
- Null model inputs are rejected rather than silently imputed.
- Batch size is bounded to 500 transactions.
- A merchant spike requires at least 5 transactions, 3 flags and a 30% flagged rate.
- Missing model artifacts are reproducibly regenerated at application startup.
- Model-feature mismatch stops startup instead of allowing silent scoring drift.
- The UI exposes API failure messages and never fabricates a decision.

## Production extension path

The prototype intentionally stops short of production deployment. A production design would add authenticated service-to-service access, encrypted event transport, an online feature store, drift monitoring, analyst feedback labels, controlled retraining, model registry approvals and jurisdiction-specific retention controls.

