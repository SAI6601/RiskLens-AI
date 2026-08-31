# Five-minute pitch script

Target duration: 4:40–5:00. Speak naturally and let important transitions breathe.

Use this narration with [`PRESENTATION_STORYBOARD.md`](PRESENTATION_STORYBOARD.md). Let the opening animation play before the first sentence.

## 0:00–0:32 — Cold open

“A fraud score is easy. Recognising that a merchant is entering a coordinated attack—and choosing the safest response—is much harder.”

“Payment fraud often forms gradually. Several transactions may look harmless alone, but together they reveal shared devices, unusual velocity and a merchant behaviour shift. I built RiskLens AI: a Merchant Risk Twin that detects the shift, fingerprints the attack and tests bounded interventions before any money action is proposed.”

## 0:32–0:58 — Evidence boundary

Show the hero promises and evidence ribbon.

“RiskLens is human-gated, attack-aware and measured. The model cannot permanently block an account. Every result exposes evidence and enters a minimized audit trail. All numbers I show are from a reproducible chronological synthetic held-out test—not production Razorpay performance.”

## 0:58–1:30 — Transaction contrast

Analyze **Normal payment**, then **Card-testing burst**.

“An ordinary payment remains below the calibrated threshold. When velocity, failed attempts and device novelty change, the score rises and RiskLens exposes the strongest reason codes instead of hiding behind a black box.”

“But one suspicious payment is not enough to declare a merchant attack. For that we need the incident view.”

## 1:30–2:10 — Merchant Risk Twin

Click **Launch the live merchant attack replay** and allow the interface to enter the incident room.

“RiskLens now compares a controlled merchant window with its expected baseline. Merchant 007 moves from an expected risk of approximately 0.08 to a live average near 0.98, while payment velocity rises from about one to fifteen transactions per ten minutes. Minimum-volume guards prevent a single anomaly from becoming an attack claim.”

## 2:10–2:48 — Fraud Constellation and Attack DNA

Pause on the constellation, then scroll to Attack DNA.

“Seven small payments use different pseudonymous instruments, but the relationship graph reveals one shared device and one shared network cluster. These are privacy-safe references—no raw card or IP data.”

“Attack DNA compares transparent signals against three known archetypes. Card testing has the strongest affinity because velocity and failed attempts dominate. This is an explainable heuristic affinity, not attacker attribution.”

## 2:48–3:35 — Intervention Simulator

Show all four intervention cards and the action contract.

“Detection is only half the decision. RiskLens compares four futures: allow, monitor, step-up authentication and temporary hold for review. Each option exposes projected residual loss, loss prevented, customer-friction exposure and analyst workload under documented prototype assumptions.”

“For this window, step-up authentication has the lowest estimated total cost among containment options. The system proposes a fifteen-minute action contract limited to seven transactions, with rollback conditions. It remains a proposal—not an unlimited autonomous block.”

## 3:35–4:02 — Graceful model failure

Click **Simulate model failure**.

“A risk system must also fail safely. When I disconnect the primary model, RiskLens does not fabricate a prediction. It enters degraded safety mode, labels the fallback rules, disables automation and requires human review.”

Click **Restore primary model**.

## 4:02–4:35 — Honest evaluation

Show the metrics or README comparison.

“The transaction model was trained on twelve thousand deterministic synthetic events with a chronological 70/15/15 split. Threshold selection used validation only. On 1,800 held-out events it achieved 75.6 percent precision, 87.9 percent recall, 81.3 percent F1 and a 2.4 percent false-positive rate. The model outperformed a transparent rule baseline, but these results do not establish production performance.”

## 4:35–5:00 — Close

“Production deployment would require approved payment data, learned merchant baselines, calibrated incident affinities, authenticated ingestion, continuous drift monitoring and analyst-feedback governance.”

“RiskLens demonstrates the product principle I would bring to Razorpay: understand how an attack is forming, explain the evidence, compare the consequences and act only within visible limits.”
