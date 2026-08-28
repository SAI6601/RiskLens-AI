const base = {
  transaction_id: "txn_live_001",
  merchant_id: "merchant_042",
  amount: 1299,
  avg_amount_30d: 1420,
  customer_tenure_days: 580,
  device_age_days: 240,
  distance_from_home_km: 7,
  failed_attempts_1h: 0,
  tx_count_10m: 1,
  shared_cards_24h: 0,
  shared_devices_24h: 0,
  merchant_risk_score: 0.08,
  hour_of_day: 14,
  is_international: 0,
  is_new_device: 0,
  billing_shipping_mismatch: 0,
};

const scenarios = {
  normal: { ...base },
  cardTesting: { ...base, transaction_id: "txn_burst_001", merchant_id: "merchant_007", amount: 89, device_age_days: 1, failed_attempts_1h: 6, tx_count_10m: 18, is_new_device: 1 },
  takeover: { ...base, transaction_id: "txn_ato_001", amount: 12900, avg_amount_30d: 1450, device_age_days: 2, distance_from_home_km: 2100, failed_attempts_1h: 2, is_international: 1, is_new_device: 1, billing_shipping_mismatch: 1 },
  abuseRing: { ...base, transaction_id: "txn_ring_001", amount: 2499, tx_count_10m: 8, shared_cards_24h: 9, shared_devices_24h: 7, merchant_risk_score: .81, is_new_device: 1 },
};

let activeScenario = "normal";
const formatMoney = value => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
const percent = value => `${(value * 100).toFixed(1)}%`;

function renderPreview() {
  const item = scenarios[activeScenario];
  const rows = [
    ["Transaction", item.transaction_id],
    ["Merchant", item.merchant_id],
    ["Amount", formatMoney(item.amount)],
    ["10-minute velocity", `${item.tx_count_10m} ${item.tx_count_10m === 1 ? "transaction" : "transactions"}`],
    ["Failed attempts", item.failed_attempts_1h],
    ["Device", item.is_new_device ? "Newly observed" : `${item.device_age_days} days old`],
    ["Shared cluster", `${item.shared_cards_24h} cards · ${item.shared_devices_24h} devices`],
  ];
  document.querySelector("#transaction-preview").innerHTML = rows.map(([label, value]) => `<div class="preview-row"><span>${label}</span><strong>${value}</strong></div>`).join("");
}

async function loadMetrics() {
  try {
    const response = await fetch("/api/metrics");
    if (!response.ok) throw new Error("Metrics unavailable");
    const data = await response.json();
    const metrics = data.held_out_test;
    document.querySelector("#metric-precision").textContent = percent(metrics.precision);
    document.querySelector("#metric-recall").textContent = percent(metrics.recall);
    document.querySelector("#metric-f1").textContent = percent(metrics.f1);
    document.querySelector("#metric-fpr").textContent = percent(metrics.false_positive_rate);
  } catch (error) {
    console.error(error);
  }
}

function renderDecision(decision) {
  document.querySelector("#empty-state").classList.add("hidden");
  document.querySelector("#batch-content").classList.add("hidden");
  document.querySelector("#decision-content").classList.remove("hidden");
  const score = decision.risk_score;
  const color = score >= .82 ? "#ff6c72" : score >= decision.threshold ? "#ffb86b" : "#48e4c2";
  const gauge = document.querySelector("#risk-gauge");
  gauge.style.background = `conic-gradient(${color} ${score * 360}deg, #dfe5df 0deg)`;
  document.querySelector("#risk-score").textContent = score.toFixed(2);
  document.querySelector("#risk-band").textContent = `${decision.risk_band} risk`;
  document.querySelector("#decision-action").textContent = decision.recommended_action.replaceAll("_", " ");
  document.querySelector("#decision-threshold").textContent = decision.threshold.toFixed(3);
  document.querySelector("#human-review").textContent = decision.human_review_required ? "required" : "not required";
  document.querySelector("#decision-disclaimer").textContent = decision.disclaimer;
  document.querySelector("#reason-list").innerHTML = decision.reasons.map((reason, index) => `
    <div class="reason">
      <span class="reason-index">0${index + 1}</span>
      <div><strong>${reason.label}</strong><small>${reason.code}</small></div>
      <code>+${reason.contribution.toFixed(2)}</code>
    </div>`).join("");
}

async function analyze() {
  const button = document.querySelector("#analyze-button");
  button.disabled = true;
  button.textContent = "Assessing signal…";
  try {
    const response = await fetch("/api/score", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(scenarios[activeScenario]) });
    if (!response.ok) throw new Error(`Assessment failed (${response.status})`);
    renderDecision(await response.json());
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
    button.innerHTML = "Analyze transaction <span>→</span>";
  }
}

function buildBatch() {
  const transactions = [];
  for (let i = 0; i < 7; i += 1) {
    transactions.push({ ...scenarios.cardTesting, transaction_id: `txn_burst_${String(i).padStart(3, "0")}`, amount: 40 + i * 18, tx_count_10m: 12 + i, merchant_id: "merchant_007" });
  }
  for (let i = 0; i < 7; i += 1) {
    transactions.push({ ...scenarios.normal, transaction_id: `txn_normal_${String(i).padStart(3, "0")}`, amount: 700 + i * 130, merchant_id: "merchant_042" });
  }
  return transactions;
}

async function analyzeBatch() {
  const button = document.querySelector("#batch-button");
  button.disabled = true;
  button.textContent = "Scanning merchant batch…";
  try {
    const response = await fetch("/api/batch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ transactions: buildBatch() }) });
    if (!response.ok) throw new Error(`Batch assessment failed (${response.status})`);
    const data = await response.json();
    document.querySelector("#empty-state").classList.add("hidden");
    document.querySelector("#decision-content").classList.add("hidden");
    document.querySelector("#batch-content").classList.remove("hidden");
    document.querySelector("#batch-headline").textContent = data.summary.merchant_spikes ? "Fraud spike surfaced" : "No merchant spike";
    document.querySelector("#batch-stats").innerHTML = [
      ["Transactions", data.summary.transactions], ["Flagged", data.summary.flagged], ["Average risk", data.summary.average_risk.toFixed(2)]
    ].map(([label, value]) => `<div class="batch-stat"><span>${label}</span><strong>${value}</strong></div>`).join("");
    document.querySelector("#batch-table").innerHTML = data.merchant_spikes.map(row => `<tr><td>${row.merchant_id}</td><td>${row.transaction_count}</td><td>${row.flagged_count}</td><td>${row.average_risk.toFixed(2)}</td><td class="${row.alert ? "alert-yes" : "alert-no"}">${row.alert ? "SPIKE" : "NORMAL"}</td></tr>`).join("");
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Run merchant burst batch instead";
  }
}

document.querySelectorAll(".scenario-tab").forEach(tab => tab.addEventListener("click", () => {
  document.querySelectorAll(".scenario-tab").forEach(item => item.classList.remove("active"));
  tab.classList.add("active");
  activeScenario = tab.dataset.scenario;
  renderPreview();
}));
document.querySelector("#analyze-button").addEventListener("click", analyze);
document.querySelector("#batch-button").addEventListener("click", analyzeBatch);
renderPreview();
loadMetrics();
