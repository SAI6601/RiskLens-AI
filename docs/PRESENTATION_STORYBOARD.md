# RiskLens AI presentation storyboard

The presentation should feel like a short product film with one clear argument:

> RiskLens turns a confusing fraud signal into explainable evidence and a bounded human-controlled action.

Do not present the repository as a list of technologies. Present one decision journey in three acts.

## Visual language

| Colour | Meaning in the presentation |
|---|---|
| Obsidian/navy | Uncertainty, risk and the operating environment |
| Luminous mint | Verified intelligence and healthy system state |
| Electric blue | Model evidence and technical depth |
| Amber | Reversible friction such as step-up authentication |
| Coral | Critical risk requiring human review |
| Warm paper | Clarity, measurement and honest evidence |

This colour discipline is important. Never use coral merely as decoration; it should retain its critical-risk meaning.

## Five-minute shot plan

### 0:00–0:12 — Cold open

**Screen:** Reload the dashboard. Let the `RISK / LENS` opening and Signal → Evidence → Action sequence play without moving the cursor.

**Voice:** Begin after the wordmark appears: “A fraud score is easy. A decision you can explain, measure and safely act on is much harder.”

**Purpose:** Establish confidence before showing any interface controls.

### 0:12–0:42 — Act I: Detect

**Screen:** Hold on the dark hero and animated merchant pulse.

**Voice:** “RiskLens AI is an explainable fraud-spike sentinel. It detects suspicious payment events and merchant-level bursts, then recommends a bounded response without permanently auto-blocking an account.”

Pause briefly on the three product promises: Human-gated, Auditable, Measured.

### 0:42–1:10 — Evidence before demo

**Screen:** Click **Evidence**. Let the four metrics count up.

**Voice:** “Before the demo, these are the frozen held-out results—not cherry-picked examples. Precision is 75.6%, recall 87.9%, F1 81.3%, and the false-positive rate is 2.4% on deterministic synthetic data.”

Say “synthetic” clearly. That honesty creates trust.

### 1:10–2:15 — Single-decision contrast

**Screen:** Click **Live assessment**.

1. Analyze **Normal payment**.
2. Switch to **Card-testing burst** and analyze again.

**Voice:** “The normal event stays below the calibrated threshold. The card-testing burst changes three signals: velocity, repeated failures and device novelty. RiskLens does not hide these behind a score—it exposes them as ranked reason codes.”

Pause long enough for the gauge and reason cards to finish animating.

### 2:15–2:55 — Merchant-level spike

**Screen:** Click **Run merchant burst batch instead**.

**Voice:** “One risky transaction is not automatically a merchant spike. The sentinel requires minimum volume, a minimum flagged count and a flagged-rate threshold. Merchant 007 surfaces at seven of seven; merchant 042 remains normal at zero of seven.”

### 2:55–3:35 — Act III: bounded response

**Screen:** Scroll to the architecture flow.

**Voice:** “A shared feature contract prevents training-serving mismatch. The interpretable model creates risk evidence. A separate policy gate chooses allow, monitor, step-up or temporary hold. The strongest decision remains human-reviewed and every result enters a minimized audit trail.”

### 3:35–4:25 — Why the model earns trust

**Screen:** Briefly show the README comparison or `metrics.json`.

**Voice:** “The model is compared with a transparent rule baseline. It improves F1 from 52.2% to 81.3% and reduces the prototype cost estimate from approximately ₹23.2 thousand to ₹8.3 thousand under documented assumptions. The operating threshold was selected only on validation data and then frozen.”

### 4:25–5:00 — Honest close

**Screen:** Return to the hero or end on the architecture’s Audit Trail card.

**Voice:** “These are synthetic-data results, not production claims. The next step is evaluation on approved payment data, drift monitoring and analyst feedback. RiskLens demonstrates the principle I would bring to Razorpay: detect quickly, explain clearly, act within limits, and keep a human accountable for the highest-impact decision.”

End cleanly. Do not add an unrelated thank-you slide.

## Recording setup

- Record at 1440×900 or 1920×1080, 100% browser zoom and at least 30 fps.
- Use a clean browser window with bookmarks, notifications and unrelated tabs hidden.
- Keep the cursor still unless selecting a control. Never circle UI elements repeatedly.
- Use one continuous product walkthrough with at most three purposeful cuts.
- Record voice separately if the room is noisy, then align it with the visual pauses.
- Speak at approximately 125–135 words per minute.
- Leave 0.5–1 second after every important metric or decision so reviewers can read it.
- Export at 1080p; verify that small reason-code and metric text remains legible.

## Delivery style

- Sound calm and technically certain, not excited or rushed.
- Lead with the problem and decision safety—not the technology stack.
- Use “the prototype achieved” rather than “our system guarantees.”
- Say “synthetic held-out test” every time you state performance.
- Explain one trade-off: higher recall catches more fraud but can increase customer friction.
- End with limitations and the production extension path. Honest boundaries make the earlier claims stronger.

## Avoid

- No background music louder than the voice.
- No hacker imagery, payment-card graphics or red warning effects used only for drama.
- No unsupported claim that RiskLens prevents all fraud.
- No long code walkthrough.
- No reading the README line by line.
- No unexplained acronym sequence.

