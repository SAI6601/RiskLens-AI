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
let currentSystemMode = "normal";
const formatMoney = value => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
const percent = value => `${(value * 100).toFixed(1)}%`;
const escapeHtml = value => String(value).replace(/[&<>'"]/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
const titleCase = value => String(value).replaceAll("_", " ").replace(/\b\w/g, character => character.toUpperCase());

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
  setIrisMood(score >= decision.threshold ? "alert" : "calm");
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
    transactions.push({
      ...scenarios.cardTesting,
      transaction_id: `txn_burst_${String(i).padStart(3, "0")}`,
      amount: 40 + i * 18,
      tx_count_10m: 12 + i,
      merchant_id: "merchant_007",
      customer_ref: `cus_demo_${String(i).padStart(2, "0")}`,
      device_ref: "dev_shared_x17",
      payment_instrument_ref: `card_token_${String(i).padStart(2, "0")}`,
      network_ref: "net_cluster_blr_04",
    });
  }
  for (let i = 0; i < 7; i += 1) {
    transactions.push({
      ...scenarios.normal,
      transaction_id: `txn_normal_${String(i).padStart(3, "0")}`,
      amount: 700 + i * 130,
      merchant_id: "merchant_042",
      customer_ref: `cus_normal_${String(i).padStart(2, "0")}`,
      device_ref: `dev_normal_${String(i).padStart(2, "0")}`,
      payment_instrument_ref: `card_normal_${String(i).padStart(2, "0")}`,
      network_ref: `net_normal_${String(i).padStart(2, "0")}`,
    });
  }
  return transactions;
}

function buildLegitimateSurge() {
  const transactions = [];
  for (let i = 0; i < 16; i += 1) {
    transactions.push({
      ...scenarios.normal,
      transaction_id: `txn_flash_sale_${String(i).padStart(3, "0")}`,
      merchant_id: "merchant_flash_sale",
      amount: 780 + i * 13,
      avg_amount_30d: 850,
      tx_count_10m: 3 + i % 2,
      merchant_risk_score: .04,
      customer_ref: `cus_flash_${String(i).padStart(2, "0")}`,
      device_ref: `dev_flash_${String(i).padStart(2, "0")}`,
      payment_instrument_ref: `card_flash_${String(i).padStart(2, "0")}`,
      network_ref: `net_flash_${String(i).padStart(2, "0")}`,
    });
  }
  return transactions;
}

function renderConstellation(constellation) {
  const svg = document.querySelector("#constellation-svg");
  const nodes = constellation.nodes.slice(0, 24);
  const nodeIds = new Set(nodes.map(node => node.id));
  const merchant = nodes.find(node => node.kind === "merchant");
  const hubs = nodes.filter(node => node.suspicious && !["merchant", "transaction"].includes(node.kind));
  const transactions = nodes.filter(node => node.kind === "transaction");
  const references = nodes.filter(node => !node.suspicious && !["merchant", "transaction"].includes(node.kind)).slice(0, 7);
  const positions = new Map();
  if (merchant) positions.set(merchant.id, { x: 320, y: 170 });
  hubs.forEach((node, index) => {
    const angle = -Math.PI / 2 + index * (Math.PI * 2 / Math.max(hubs.length, 1));
    positions.set(node.id, { x: 320 + Math.cos(angle) * 88, y: 170 + Math.sin(angle) * 72 });
  });
  transactions.forEach((node, index) => {
    const angle = -Math.PI / 2 + index * (Math.PI * 2 / Math.max(transactions.length, 1));
    positions.set(node.id, { x: 320 + Math.cos(angle) * 150, y: 170 + Math.sin(angle) * 132 });
  });
  references.forEach((node, index) => {
    const angle = -Math.PI / 2 + (index + .5) * (Math.PI * 2 / Math.max(references.length, 1));
    positions.set(node.id, { x: 320 + Math.cos(angle) * 204, y: 170 + Math.sin(angle) * 150 });
  });

  const edges = constellation.edges.filter(edge => nodeIds.has(edge.source) && nodeIds.has(edge.target) && positions.has(edge.source) && positions.has(edge.target));
  const edgeMarkup = edges.map((edge, index) => {
    const source = positions.get(edge.source);
    const target = positions.get(edge.target);
    const connectedToHub = hubs.some(node => node.id === edge.target || node.id === edge.source);
    return `<line class="graph-edge ${connectedToHub ? "is-hot" : ""}" style="--edge-delay:${index * 22}ms" x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}"></line>`;
  }).join("");
  const nodeMarkup = nodes.filter(node => positions.has(node.id)).map((node, index) => {
    const point = positions.get(node.id);
    const radius = node.kind === "merchant" ? 23 : node.suspicious && node.kind !== "transaction" ? 15 : node.kind === "transaction" ? 7 : 9;
    const showLabel = node.kind === "merchant" || (node.suspicious && node.kind !== "transaction");
    return `<g class="graph-node kind-${node.kind} ${node.suspicious ? "is-suspicious" : ""}" style="--node-delay:${index * 38}ms" transform="translate(${point.x} ${point.y})"><circle r="${radius}"></circle>${showLabel ? `<text y="${radius + 18}" text-anchor="middle">${escapeHtml(node.label)}</text>` : ""}</g>`;
  }).join("");
  svg.innerHTML = `<g class="graph-edges">${edgeMarkup}</g><g class="graph-nodes">${nodeMarkup}</g>`;
}

function replayIncidentTimeline() {
  const steps = [...document.querySelectorAll(".replay-step")];
  steps.forEach(step => step.classList.remove("is-active", "is-complete"));
  if (reducedMotion()) {
    steps.forEach((step, index) => step.classList.add(index === steps.length - 1 ? "is-active" : "is-complete"));
    return;
  }
  steps.forEach((step, index) => {
    window.setTimeout(() => {
      steps.forEach((item, itemIndex) => {
        item.classList.toggle("is-active", itemIndex === index);
        item.classList.toggle("is-complete", itemIndex < index);
      });
    }, index * 260);
  });
}

function renderIncident(data) {
  const incident = data.incidents.find(item => item.risk_twin.status === "attack") || data.incidents[0];
  if (!incident) return;
  currentSystemMode = data.system_mode;
  document.querySelector("#incident-awaiting").classList.add("hidden");
  const consolePanel = document.querySelector("#incident-console");
  consolePanel.classList.remove("hidden");
  replayClass(consolePanel, "is-replaying");

  const degraded = data.system_mode === "degraded";
  setIrisMood(degraded ? "degraded" : incident.risk_twin.status === "attack" ? "alert" : "calm");
  const mode = document.querySelector("#system-mode");
  mode.classList.toggle("is-degraded", degraded);
  mode.innerHTML = `<i></i> ${degraded ? "Degraded safety mode" : "Primary model online"}`;
  document.querySelector(".system-status").innerHTML = `<i></i> ${degraded ? "Fallback rules active" : "Model online"}`;
  document.querySelector("#failure-button").textContent = degraded ? "Restore primary model" : "Simulate model failure";
  const noAttackPattern = incident.attack_dna.dominant_pattern === "no_dominant_attack";
  document.querySelector("#incident-headline").textContent = degraded ? "Model unavailable · automation disabled" : noAttackPattern ? "No attack pattern resolved" : titleCase(incident.attack_dna.dominant_pattern);
  document.querySelector("#incident-merchant").textContent = incident.merchant_id;

  const twin = incident.risk_twin;
  document.querySelector("#twin-status").textContent = twin.status.toUpperCase();
  document.querySelector("#twin-deviation").textContent = twin.deviation_score.toFixed(2);
  document.querySelector("#twin-explanation").textContent = twin.explanation;
  document.querySelector("#baseline-risk").textContent = twin.baseline.average_risk.toFixed(2);
  document.querySelector("#observed-risk").textContent = twin.observed.average_risk.toFixed(2);
  document.querySelector("#baseline-velocity").textContent = `${twin.baseline.average_velocity_10m.toFixed(1)} / 10m`;
  document.querySelector("#observed-velocity").textContent = `${twin.observed.average_velocity_10m.toFixed(1)} / 10m`;
  document.querySelector("#baseline-risk-bar").style.width = `${Math.max(twin.baseline.average_risk * 100, 2)}%`;
  document.querySelector("#observed-risk-bar").style.width = `${Math.max(twin.observed.average_risk * 100, 2)}%`;

  const dna = incident.attack_dna;
  document.querySelector("#dna-fingerprint").textContent = dna.fingerprint_id;
  document.querySelector("#dna-pattern").textContent = titleCase(dna.dominant_pattern);
  document.querySelector("#dna-confidence").textContent = noAttackPattern ? "No attack claim" : `${percent(dna.confidence)} heuristic affinity`;
  document.querySelector("#dna-narrative").textContent = dna.narrative;
  document.querySelector("#affinity-bars").innerHTML = Object.entries(dna.pattern_affinities).map(([name, value]) => `
    <div class="affinity-row"><span>${escapeHtml(titleCase(name))}</span><i><b style="width:${value * 100}%"></b></i><strong>${percent(value)}</strong></div>`).join("");
  document.querySelector("#dna-signals").innerHTML = dna.signals.map(signal => `
    <span class="dna-signal severity-${signal.severity}"><i></i>${escapeHtml(signal.code)} <strong>${escapeHtml(signal.value)}</strong></span>`).join("");

  document.querySelector("#constellation-summary").textContent = `${incident.constellation.shared_hubs} shared hubs`;
  renderConstellation(incident.constellation);

  document.querySelector("#intervention-options").innerHTML = incident.interventions.map(option => `
    <article class="intervention-option ${option.recommended ? "is-recommended" : ""}">
      <div><span>${escapeHtml(titleCase(option.action))}</span>${option.recommended ? "<b>Recommended</b>" : ""}</div>
      <strong>${formatMoney(option.projected_loss_prevented_inr)}</strong>
      <small>projected loss prevented</small>
      <dl><div><dt>Residual</dt><dd>${formatMoney(option.projected_residual_loss_inr)}</dd></div><div><dt>Friction exposure</dt><dd>${percent(option.friction_exposure_rate)}</dd></div><div><dt>Review load</dt><dd>${option.review_load}</dd></div></dl>
    </article>`).join("");

  const contract = incident.action_contract;
  document.querySelector("#contract-action").textContent = titleCase(contract.action);
  document.querySelector("#contract-id").textContent = contract.contract_id;
  document.querySelector("#contract-expiry").textContent = `${contract.expires_in_minutes} minutes`;
  document.querySelector("#contract-scope").textContent = `${contract.transaction_limit} transactions max`;
  document.querySelector("#contract-gate").textContent = contract.human_gate_required ? "Required" : "Policy gated";
  document.querySelector("#safety-notice").textContent = data.safety_notice;
  const timelineLabels = noAttackPattern
    ? ["Baseline stable", "Activity changes", "No shared hubs", "No attack pattern", "Bounded response proposed"]
    : ["Baseline stable", "Velocity changes", "Shared hubs form", "Attack DNA resolved", "Bounded action proposed"];
  document.querySelectorAll(".replay-step span").forEach((item, index) => {
    item.textContent = timelineLabels[index];
  });
  replayIncidentTimeline();
  refreshIrisGuide();
}

async function analyzeBatch(simulateFailure = false, transactions = buildBatch(), triggerSelector = "#batch-button") {
  const button = document.querySelector(triggerSelector);
  const batchButton = document.querySelector("#batch-button");
  const surgeButton = document.querySelector("#surge-button");
  const failureButton = document.querySelector("#failure-button");
  const idleLabel = button.textContent;
  batchButton.disabled = true;
  surgeButton.disabled = true;
  failureButton.disabled = true;
  button.textContent = simulateFailure ? "Disconnecting primary model…" : triggerSelector === "#surge-button" ? "Testing legitimate activity…" : "Building merchant risk twin…";
  try {
    const response = await fetch("/api/batch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ transactions, simulate_model_failure: simulateFailure }) });
    if (!response.ok) throw new Error(`Batch assessment failed (${response.status})`);
    const data = await response.json();
    document.querySelector("#empty-state").classList.add("hidden");
    document.querySelector("#decision-content").classList.add("hidden");
    const content = document.querySelector("#batch-content");
    content.classList.remove("hidden");
    if (!reducedMotion()) replayClass(content, "is-entering");
    document.querySelector("#batch-headline").textContent = data.system_mode === "degraded" ? "Degraded review required" : data.summary.active_incidents ? "Merchant attack surfaced" : "No merchant incident";
    document.querySelector("#batch-stats").innerHTML = [
      ["Transactions", data.summary.transactions], ["Flagged", data.summary.flagged], ["Average risk", data.summary.average_risk.toFixed(2)]
    ].map(([label, value]) => `<div class="batch-stat"><span>${label}</span><strong>${value}</strong></div>`).join("");
    document.querySelector("#batch-table").innerHTML = data.merchant_spikes.map(row => `<tr><td>${row.merchant_id}</td><td>${row.transaction_count}</td><td>${row.flagged_count}</td><td>${row.average_risk.toFixed(2)}</td><td class="${row.alert ? "alert-yes" : "alert-no"}">${row.alert ? "SPIKE" : "NO SPIKE"}</td></tr>`).join("");
    renderIncident(data);
    document.querySelector("#incident").scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "start" });
  } catch (error) {
    alert(error.message);
  } finally {
    batchButton.disabled = false;
    surgeButton.disabled = false;
    failureButton.disabled = false;
    button.textContent = idleLabel;
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
document.querySelector("#batch-button").addEventListener("click", () => analyzeBatch(false));
document.querySelector("#surge-button").addEventListener("click", () => analyzeBatch(false, buildLegitimateSurge(), "#surge-button"));
document.querySelector("#failure-button").addEventListener("click", () => analyzeBatch(currentSystemMode === "normal"));

const irisSteps = [
  {
    kicker: "Orientation",
    title: "Meet IRIS",
    message: "I’m the RiskLens intelligence guide. I’ll take you from a merchant signal to a bounded, explainable decision.",
    target: ".signal-card",
  },
  {
    kicker: "Choose a signal",
    title: "Start with a payment",
    message: "Compare a normal payment with card testing, account takeover or an abuse ring. Then challenge the incident layer with a legitimate sales surge.",
    target: ".scenario-tabs",
  },
  {
    kicker: "Inspect evidence",
    title: "Challenge the score",
    message: "Analyze the transaction. RiskLens exposes its threshold, confidence, ranked reason codes and bounded recommendation.",
    target: "#analyze-button",
  },
  {
    kicker: "Reveal the campaign",
    title: "Watch an attack form",
    message: "Launch the merchant replay. One flag is not enough—RiskLens waits for merchant-level evidence before declaring an incident.",
    target: "#batch-button",
  },
  {
    kicker: "Connect evidence",
    title: "Follow the constellation",
    message: "Shared pseudonymous devices and networks connect payments that may look harmless when viewed separately.",
    target: ".constellation-panel",
    fallback: ".incident-heading",
  },
  {
    kicker: "Compare outcomes",
    title: "Test four futures",
    message: "Compare loss prevented, residual exposure, customer friction and analyst workload before choosing a response.",
    target: ".intervention-panel",
    fallback: ".incident-heading",
  },
  {
    kicker: "Verify resilience",
    title: "Make RiskLens fail safely",
    message: "Simulate a model failure. Automation switches off, fallback rules are labelled and the highest-impact action becomes human-gated.",
    target: "#failure-button",
  },
];

const irisStorageKey = "risklens-iris-guide-seen-v1";
let irisStepIndex = 0;
let irisActiveTarget = null;

function setIrisMood(mood) {
  const guide = document.querySelector("#iris-guide");
  if (guide) guide.dataset.mood = mood;
}

function irisHasBeenSeen() {
  try { return window.localStorage.getItem(irisStorageKey) === "true"; }
  catch (error) { return false; }
}

function rememberIrisVisit() {
  try { window.localStorage.setItem(irisStorageKey, "true"); }
  catch (error) { /* The guide still works when storage is unavailable. */ }
}

function clearIrisTarget() {
  if (irisActiveTarget) irisActiveTarget.classList.remove("iris-target");
  irisActiveTarget = null;
}

function resolveIrisTarget(step) {
  const requested = document.querySelector(step.target);
  if (requested && requested.getClientRects().length) return requested;
  return step.fallback ? document.querySelector(step.fallback) : requested;
}

function renderIrisStep(scrollToTarget = true) {
  const step = irisSteps[irisStepIndex];
  const guide = document.querySelector("#iris-guide");
  document.querySelector("#iris-step-label").textContent = `${step.kicker} · ${String(irisStepIndex + 1).padStart(2, "0")}`;
  document.querySelector("#iris-title").textContent = step.title;
  document.querySelector("#iris-message").textContent = step.message;
  document.querySelector("#iris-back").disabled = irisStepIndex === 0;
  document.querySelector("#iris-next").innerHTML = `${irisStepIndex === 0 ? "Begin tour" : irisStepIndex === irisSteps.length - 1 ? "Finish" : "Next"} <span>→</span>`;
  document.querySelector("#iris-progress").innerHTML = irisSteps.map((_, index) => `<i class="${index < irisStepIndex ? "is-complete" : index === irisStepIndex ? "is-active" : ""}"></i>`).join("");

  clearIrisTarget();
  irisActiveTarget = resolveIrisTarget(step);
  if (!irisActiveTarget) return;
  irisActiveTarget.classList.add("iris-target");
  const targetRect = irisActiveTarget.getBoundingClientRect();
  const targetCenter = targetRect.left + targetRect.width / 2;
  guide.classList.toggle("is-left", window.innerWidth > 720 && targetCenter > window.innerWidth * 0.58);
  if (scrollToTarget) {
    irisActiveTarget.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "center" });
  }
}

function openIrisGuide(restart = true, scrollToTarget = false) {
  if (restart) irisStepIndex = 0;
  const guide = document.querySelector("#iris-guide");
  guide.classList.add("is-open");
  document.querySelector("#iris-panel").setAttribute("aria-hidden", "false");
  document.querySelector("#iris-trigger").setAttribute("aria-expanded", "true");
  renderIrisStep(scrollToTarget);
}

function closeIrisGuide(markSeen = true) {
  const guide = document.querySelector("#iris-guide");
  guide.classList.remove("is-open", "is-left");
  document.querySelector("#iris-panel").setAttribute("aria-hidden", "true");
  document.querySelector("#iris-trigger").setAttribute("aria-expanded", "false");
  clearIrisTarget();
  if (markSeen) rememberIrisVisit();
}

function refreshIrisGuide() {
  if (document.querySelector("#iris-guide")?.classList.contains("is-open")) renderIrisStep(false);
}

function initializeIrisGuide() {
  document.querySelector("#iris-trigger").addEventListener("click", () => {
    const open = document.querySelector("#iris-guide").classList.contains("is-open");
    if (open) closeIrisGuide();
    else openIrisGuide(true, false);
  });
  document.querySelector("#iris-close").addEventListener("click", () => closeIrisGuide());
  document.querySelector("#iris-dismiss").addEventListener("click", () => closeIrisGuide());
  document.querySelector("#iris-back").addEventListener("click", () => {
    if (irisStepIndex === 0) return;
    irisStepIndex -= 1;
    renderIrisStep();
  });
  document.querySelector("#iris-next").addEventListener("click", () => {
    if (irisStepIndex === irisSteps.length - 1) {
      closeIrisGuide();
      return;
    }
    irisStepIndex += 1;
    renderIrisStep();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && document.querySelector("#iris-guide").classList.contains("is-open")) closeIrisGuide();
  });
  if (!irisHasBeenSeen()) {
    window.setTimeout(() => openIrisGuide(true, false), reducedMotion() ? 1350 : 1900);
  }
}

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
initializeIrisGuide();
