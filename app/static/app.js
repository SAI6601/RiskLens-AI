document.documentElement.classList.add("motion-enabled");
const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
const reducedMotion = () => motionPreference.matches;

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

function replayClass(element, className) {
  element.classList.remove(className);
  void element.offsetWidth;
  element.classList.add(className);
}

function animateMetric(element) {
  if (!element.dataset.metricValue || element.dataset.animated) return;
  element.dataset.animated = "true";
  const target = Number(element.dataset.metricValue) * 100;
  if (reducedMotion()) {
    element.textContent = `${target.toFixed(1)}%`;
    return;
  }
  const start = performance.now();
  const duration = 900;
  const tick = now => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 4);
    element.textContent = `${(target * eased).toFixed(1)}%`;
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function setMetric(selector, value) {
  const element = document.querySelector(selector);
  element.dataset.metricValue = value;
  element.textContent = reducedMotion() ? percent(value) : "0.0%";
  if (element.closest("article")?.classList.contains("is-visible")) animateMetric(element);
}

function animateGauge(score, color) {
  const gauge = document.querySelector("#risk-gauge");
  const number = document.querySelector("#risk-score");
  const from = Number(gauge.dataset.score || 0);
  gauge.dataset.score = score;
  if (reducedMotion()) {
    gauge.style.background = `conic-gradient(${color} ${score * 360}deg, #dfe5df 0deg)`;
    number.textContent = score.toFixed(2);
    return;
  }
  const start = performance.now();
  const duration = 720;
  const tick = now => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = from + (score - from) * eased;
    gauge.style.background = `conic-gradient(${color} ${current * 360}deg, #dfe5df 0deg)`;
    number.textContent = current.toFixed(2);
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

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
  const preview = document.querySelector("#transaction-preview");
  preview.innerHTML = rows.map(([label, value]) => `<div class="preview-row"><span>${label}</span><strong>${value}</strong></div>`).join("");
  if (!reducedMotion()) replayClass(preview, "is-switching");
}

async function loadMetrics() {
  try {
    const response = await fetch("/api/metrics");
    if (!response.ok) throw new Error("Metrics unavailable");
    const data = await response.json();
    const metrics = data.held_out_test;
    setMetric("#metric-precision", metrics.precision);
    setMetric("#metric-recall", metrics.recall);
    setMetric("#metric-f1", metrics.f1);
    setMetric("#metric-fpr", metrics.false_positive_rate);
  } catch (error) {
    console.error(error);
  }
}

function renderDecision(decision) {
  document.querySelector("#empty-state").classList.add("hidden");
  document.querySelector("#batch-content").classList.add("hidden");
  const content = document.querySelector("#decision-content");
  content.classList.remove("hidden");
  if (!reducedMotion()) replayClass(content, "is-entering");
  const score = decision.risk_score;
  const color = score >= .82 ? "#ff6c72" : score >= decision.threshold ? "#ffb86b" : "#48e4c2";
  animateGauge(score, color);
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
    const content = document.querySelector("#batch-content");
    content.classList.remove("hidden");
    if (!reducedMotion()) replayClass(content, "is-entering");
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

document.querySelectorAll(".scenario-tab").forEach((tab, index) => {
  tab.setAttribute("aria-selected", index === 0 ? "true" : "false");
  tab.addEventListener("click", () => {
  document.querySelectorAll(".scenario-tab").forEach(item => {
    item.classList.remove("active");
    item.setAttribute("aria-selected", "false");
  });
  tab.classList.add("active");
  tab.setAttribute("aria-selected", "true");
  activeScenario = tab.dataset.scenario;
  renderPreview();
  });
});
document.querySelector("#analyze-button").addEventListener("click", analyze);
document.querySelector("#batch-button").addEventListener("click", analyzeBatch);

function initializeExperience() {
  const boot = document.querySelector(".boot-sequence");
  const revealTargets = [
    ...document.querySelectorAll(".metrics-grid article"),
    ...document.querySelectorAll(".section-heading > *"),
    ...document.querySelectorAll(".assessment-grid"),
    ...document.querySelectorAll(".flow article"),
  ];
  revealTargets.forEach((element, index) => {
    element.classList.add("will-reveal");
    element.style.setProperty("--reveal-delay", `${(index % 5) * 70}ms`);
  });

  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      entry.target.querySelectorAll("[data-metric-value]").forEach(animateMetric);
      if (entry.target.matches("[data-metric-value]")) animateMetric(entry.target);
      revealObserver.unobserve(entry.target);
    });
  }, { threshold: .16, rootMargin: "0px 0px -40px" });
  revealTargets.forEach(element => revealObserver.observe(element));

  const header = document.querySelector(".site-header");
  const setHeaderState = () => header.classList.toggle("is-scrolled", window.scrollY > 24);
  setHeaderState();
  window.addEventListener("scroll", setHeaderState, { passive: true });

  const signalCard = document.querySelector(".signal-card");
  if (!reducedMotion() && window.matchMedia("(pointer: fine)").matches) {
    signalCard.addEventListener("pointermove", event => {
      const rect = signalCard.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - .5;
      const y = (event.clientY - rect.top) / rect.height - .5;
      signalCard.style.transition = "transform .16s ease-out, box-shadow .25s ease";
      signalCard.style.transform = `perspective(950px) rotateX(${-y * 3.4}deg) rotateY(${x * 4.2}deg) translateZ(0)`;
    });
    signalCard.addEventListener("pointerleave", () => {
      signalCard.style.transform = "perspective(950px) rotateX(0) rotateY(0) translateZ(0)";
    });
  }

  const revealExperience = () => {
    document.documentElement.classList.add("experience-ready");
    boot.classList.add("is-complete");
    window.setTimeout(() => boot.remove(), 850);
  };
  if (reducedMotion()) revealExperience();
  else window.setTimeout(revealExperience, 1250);
}

renderPreview();
loadMetrics();
initializeExperience();
