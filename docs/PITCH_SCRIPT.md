# Five-minute pitch script

Target duration: 4:57. Speak naturally and let the interface breathe between decisions.

Use this narration with [`PRESENTATION_STORYBOARD.md`](PRESENTATION_STORYBOARD.md). Dismiss IRIS once before recording, reload, and let the opening animation begin before the first sentence.

## 0:00–0:12 — Cold open

“A fraud score is easy. Recognising that a merchant is entering a coordinated attack—and choosing the safest response—is much harder.”

## 0:12–0:42 — Product promise

“Payment fraud rarely arrives as one obvious event. It forms across small transactions, shared devices and a merchant’s changing behaviour. I built RiskLens AI: a Merchant Risk Twin that detects that shift, reveals the attack pattern and compares bounded responses before any money action is proposed. Permanent automatic blocking is outside the design.”

## 0:42–1:04 — Honest evidence

Show the evidence ribbon.

“In a held-out chronological synthetic test, the model reached 75.6 percent precision, 87.9 percent recall, 81.3 percent F1 and a 2.4 percent false-positive rate. These are prototype metrics, not Razorpay production results.”

## 1:04–1:34 — Transaction contrast

Analyze **Normal payment**, then **Card-testing burst**.

“An ordinary payment scores 0.03, below the 0.475 threshold, and is allowed. In a controlled card-testing burst, velocity, failures and device novelty push risk to 0.99. RiskLens shows ranked reasons, not a black box. Yet one suspicious payment cannot prove a merchant attack.”

## 1:34–2:09 — Merchant Risk Twin

Click **Launch the live merchant attack replay** and allow the interface to enter the incident room.

“That is why the incident view evaluates a window, not an isolated event. RiskLens compares Merchant 007 against a transparent prototype baseline: average risk moves from 0.08 to 0.98 and velocity from about one to fifteen transactions per ten minutes. Minimum-volume and flagged-count guards stop a single anomaly from being mislabeled as a fraud spike.”

## 2:09–2:46 — Fraud Constellation and Attack DNA

Pause on the constellation, then move to Attack DNA.

“Seven small payments use different pseudonymous instruments, yet the relationship graph reveals one shared device and one shared network cluster: two suspicious hubs without raw card or IP data. Attack DNA compares transparent signals against three known archetypes. Card testing reaches the strongest heuristic affinity because velocity and failed attempts dominate. This explains a pattern; it does not attribute an attacker.”

## 2:46–3:30 — Intervention Simulator

Show all four intervention cards and the action contract.

“Detection is only half the decision. RiskLens compares four futures: allow, monitor, step-up authentication and temporary hold for review. Each option exposes projected residual loss, loss prevented, customer-friction exposure and analyst workload under documented prototype assumptions. For this window, step-up authentication has the lowest estimated total cost among containment options. It becomes a fifteen-minute, seven-transaction proposed contract with rollback conditions—not an unlimited autonomous block.”

## 3:30–3:57 — Graceful model failure

Click **Simulate model failure**, then restore the model after the pause.

“A responsible risk system must fail safely, not confidently. When the primary model is unavailable, RiskLens enters degraded safety mode, labels fallback rules, disables automation and marks the human gate as required. It never fabricates model confidence. When the model returns, normal operation is restored.”

## 3:57–4:32 — Architecture and auditability

Show the architecture flow.

“Under the interface, one feature contract feeds an interpretable logistic model, ranked reason codes and the Merchant Risk Twin. The incident layer adds relationship evidence and attack affinity. The policy layer compares bounded actions, then writes privacy-minimized records into a SHA-256 hash chain. Training uses twelve thousand deterministic synthetic events, a chronological 70/15/15 split and a validation-only operating threshold.”

## 4:32–4:57 — Honest close

“Production would require approved payment data, learned merchant baselines, calibrated incident affinities, authenticated ingestion, drift monitoring and analyst-feedback governance. RiskLens shows the principle I would bring to Razorpay: understand the attack, explain the evidence, compare consequences and act only within visible limits.”
