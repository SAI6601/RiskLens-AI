# Five-minute pitch script

Target duration: 4:40–5:00. Speak naturally; do not read the headings.

## 0:00–0:35 — Problem

“Payment fraud rarely arrives as one obvious event. It can look like a burst of low-value card tests, an account suddenly paying from a new device and location, or a cluster sharing cards and devices. A useful Risk Manager must detect these signals without creating unlimited customer friction or hiding behind a black-box score.”

“I built RiskLens AI, an explainable fraud-spike sentinel that turns transaction signals into a bounded, auditable recommendation.”

## 0:35–1:10 — Product promise

Show the landing page and the three promises.

“Every decision has three properties. It is human-gated, so the model cannot permanently block an account. It is auditable, so every response contains a model version, score, reason codes and action. And it is measured on a chronological held-out test rather than a cherry-picked demo.”

## 1:10–2:15 — Single-transaction demonstration

Open **Normal payment** and analyze it.

“This ordinary transaction remains below the calibrated threshold and is allowed.”

Switch to **Card-testing burst** and analyze it.

“Now the same system sees high ten-minute velocity, repeated failed attempts and a new device. Risk rises above the threshold. The interface exposes those exact reason codes and recommends a temporary hold for analyst review—not a permanent automatic block.”

Briefly show **Account takeover** or **Abuse ring** without spending too long.

## 2:15–2:55 — Merchant spike demonstration

Click **Run merchant burst batch instead**.

“A single flag does not prove a merchant spike. RiskLens groups the decisions and requires minimum volume, at least three flags and a thirty-percent flagged rate. In this controlled batch, merchant 007 has seven of seven transactions flagged and surfaces as a spike, while merchant 042 remains normal at zero of seven.”

## 2:55–3:45 — Architecture

Show the architecture section or README diagram.

“The flow is intentionally simple. Pydantic validates a closed input schema. A shared feature contract prevents training-serving mismatch. A class-balanced logistic model produces the risk probability. Local coefficient contributions become analyst-readable reason codes. Then a separate policy layer selects allow, monitor, step-up authentication or hold for review. Finally, a minimized audit log records the evidence without raw card credentials.”

## 3:45–4:30 — Honest evaluation

Show the evidence cards and `artifacts/metrics.json`.

“I generated twelve thousand reproducible synthetic events and split them chronologically: seventy percent train, fifteen percent validation and fifteen percent final test. Threshold selection happened only on validation data.”

“On eighteen hundred held-out transactions the model achieved 75.6 percent precision, 87.9 percent recall, 81.3 percent F1 and a 2.4 percent false-positive rate. I also report false-positive review cost and missed fraud amount, because accuracy without customer-friction cost is incomplete.”

## 4:30–5:00 — Limitations and close

“These are synthetic-data results, not production claims. The next step would be evaluation on approved real data, authenticated event ingestion, drift monitoring, analyst feedback labels and model-registry governance.”

“RiskLens demonstrates the product principle I believe an AI Risk Manager needs: detect quickly, explain clearly, act within limits and keep a human accountable for the highest-impact decision.”

