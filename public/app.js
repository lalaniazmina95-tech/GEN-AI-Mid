/* AI Use Case Registry - front end (vanilla JS, no build step). */
(() => {
"use strict";
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage unavailable */ } },
  del(k) { try { localStorage.removeItem(k); } catch { /* ignore */ } },
};
const TIER_LABEL = { prohibited: "Prohibited", high: "High risk", limited: "Limited risk", minimal: "Minimal risk" };
const STATUS_LABEL = { pending_approval: "Pending approval", pending_committee: "Pending committee", approved: "Approved", rejected: "Rejected", returned_to_team: "Returned to team" };
const FW_LABEL = { eu: "EU AI Act", nist: "NIST AI RMF", aigp: "AIGP" };
const tierBadge = (t) => `<span class="tier tier-${esc(t || "none")}">${esc(TIER_LABEL[t] || "–")}</span>`;
const statusBadge = (s) => `<span class="status ${esc(s)}">${esc(STATUS_LABEL[s] || s)}</span>`;

let S = { state: null, health: null, persistent: false, config: null, defaults: null, frameworks: null, inventory: [], usage: null, busy: false, result: null };

function toast(msg) { const t = $("#toast"); t.textContent = msg; t.classList.remove("hidden"); clearTimeout(t._h); t._h = setTimeout(() => t.classList.add("hidden"), 4200); }

async function api(path, opts = {}) {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  let data = null;
  try { data = await r.json(); } catch { /* non-JSON */ }
  if (!r.ok) throw new Error((data && data.detail) || `HTTP ${r.status}`);
  return data;
}

/* ---------------- tabs & role ---------------- */
function showTab(name) {
  $$(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  $$(".tab").forEach((t) => t.classList.toggle("active", t.id === "tab-" + name));
  store.set("tab", name);
  if (name === "inventory") loadInventory();
  if (name === "admin") renderAdmin();
  if (name === "frameworks") renderFrameworks();
  if (name === "about") renderAbout();
}
$$(".tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
const role = () => $("#role").value;
$("#role").addEventListener("change", () => { store.set("role", role()); renderAdmin(); if (S.detail) renderDetail(S.detail); });

/* ---------------- config ---------------- */
function localConfig() { return S.persistent ? null : store.get("registry_config", null); }

/* ---------------- chat ---------------- */
function renderMessages() {
  const box = $("#messages");
  const turns = (S.state && S.state.turns) || [];
  box.innerHTML = turns.map((t) => {
    const who = t.role === "user" ? "You" : t.role === "assistant" ? "Registry assistant (AI)" : "Guard";
    return `<div class="msg ${esc(t.role)}"><div class="who">${who}</div>${esc(t.text)}</div>`;
  }).join("") + (S.busy ? `<div class="msg assistant thinking">${esc(S.busy)}</div>` : "");
  box.scrollTop = box.scrollHeight;
  $("#reg-id").textContent = S.state ? S.state.id : "New registration";
  $("#reg-phase").textContent = S.state ? "· " + ({ intake: "awaiting brief", questions: `follow-up round ${S.state.rounds}`, ready: "ready to assess", assessed: "assessed" }[S.state.phase] || "") : "";
  const u = S.usage;
  $("#usage-line").textContent = u && u.calls ? `${u.calls} model calls · ${u.total_tokens.toLocaleString()} tokens · $${u.cost_usd.toFixed(4)}` : "";
  $("#send").disabled = !!S.busy; $("#finish-btn").disabled = !!S.busy || !S.state || !Object.keys(S.state.fields || {}).length;
}

function renderSide(progress) {
  const st = S.state; if (!st) return;
  const fields = st.fields || {};
  $("#facts").innerHTML = Object.entries(fields).map(([k, v]) => {
    const label = (S.frameworks && S.frameworks.qb[k] && S.frameworks.qb[k].label) || k;
    const badge = v.status ? ` <span class="badge ${esc(v.status)}">${esc(v.status.replace("_", " "))}</span>` : "";
    return `<li><b>${esc(label)}${badge}</b>${esc(typeof v.value === "boolean" ? (v.value ? "Yes" : "No") : v.value)}</li>`;
  }).join("") || `<li class="muted">Nothing captured yet.</li>`;
  if (progress) {
    S.progress = progress;
    $("#floor").outerHTML = `<span id="floor" class="tier tier-${esc(progress.floor_tier)}">${esc(progress.floor_tier_label)}</span>`;
    $("#req-count").textContent = `${progress.answered} / ${progress.required}`;
    $("#fw-bars").innerHTML = Object.entries(progress.frameworks).map(([fw, d]) => {
      const p = d.total ? Math.round((100 * d.have) / d.total) : 0;
      return `<div class="bar"><div class="lbl"><span>${FW_LABEL[fw]} clauses evidenced</span><span>${d.have}/${d.total}</span></div><div class="track"><div class="fill" style="width:${p}%"></div></div></div>`;
    }).join("");
    $("#missing").innerHTML = progress.missing.map((m) => `<li>${esc((S.frameworks && S.frameworks.qb[m] && S.frameworks.qb[m].label) || m)}</li>`).join("") || "<li>Nothing required is missing.</li>";
  }
}

function saveSession() { store.set("session", { state: S.state, usage: S.usage, progress: S.progress, result: S.result }); }

async function newSession() {
  const { state } = await api("/api/session", { method: "POST" });
  S.state = state; S.usage = null; S.progress = null; S.result = null;
  $("#result").classList.add("hidden");
  $("#floor").outerHTML = `<span id="floor" class="tier tier-none">–</span>`;
  $("#req-count").textContent = "0 / 0"; $("#fw-bars").innerHTML = ""; $("#missing").innerHTML = "";
  renderMessages(); renderSide(); saveSession();
}

async function send(message) {
  if (!message.trim() || S.busy) return;
  if (S.state && S.state.phase === "assessed") { toast("This registration is complete. Click New to start another."); return; }
  S.busy = "Reading your message and checking it against the frameworks…";
  S.state.turns.push({ role: "user", text: message }); renderMessages();
  const optimistic = S.state.turns.pop();
  try {
    const out = await api("/api/turn", { method: "POST", body: JSON.stringify({ state: S.state, message, config: localConfig() }) });
    S.state = out.state; S.usage = sumUsage(S.usage, out.usage);
    S.busy = false; renderMessages(); renderSide(out.progress); saveSession();
    if (out.event === "ready") await finalize();
  } catch (e) {
    S.busy = false; S.state.turns.push(optimistic); S.state.turns.push({ role: "system", text: "Error: " + e.message });
    renderMessages();
  }
}

function sumUsage(a, b) {
  if (!b) return a; if (!a) return { ...b };
  const o = { ...a }; for (const k of ["calls", "prompt_tokens", "completion_tokens", "reasoning_tokens", "total_tokens", "cost_usd", "latency_s"]) o[k] = (a[k] || 0) + (b[k] || 0);
  return o;
}

async function finalize() {
  S.busy = "Screening against Art. 5, Annex III and the Bank's rules, scoring against the risk appetite, and drafting the cards…"; renderMessages();
  try {
    const inv = S.persistent ? null : localInventory();
    const out = await api("/api/finalize", { method: "POST", body: JSON.stringify({ state: S.state, config: localConfig(), inventory: inv }) });
    const reg = out.registration;
    S.usage = sumUsage(S.usage, reg.usage);
    reg.usage_session = S.usage;
    if (!out.saved) { const l = store.get("registry_local", []); l.unshift(reg); store.set("registry_local", l.slice(0, 50)); }
    S.state.phase = "assessed"; S.result = reg;
    S.state.turns.push({ role: "assistant", text: `Draft assessment ready: ${reg.assessment.bank_tier_label}. It has been added to the AI inventory as "${STATUS_LABEL[reg.status]}". It is not official until the ${reg.assessment.approval_route} approves it. See the results below.` });
    S.busy = false; renderMessages(); renderResult($("#result"), reg, false); saveSession();
    $("#result").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    S.busy = false; S.state.turns.push({ role: "system", text: "Error while assessing: " + e.message }); renderMessages();
  }
}

/* ---------------- result rendering (shared by register + inventory) ---------------- */
function entryHtml(e) {
  const badge = e.status ? `<span class="badge ${esc(e.status)}">${esc(e.status_label || e.status)}</span>` : "";
  const src = e.quote ? `<span class="src">Team said: "${esc(e.quote)}"</span>` : e.source && e.source !== "team" && e.source !== "none" ? `<span class="src">Source: ${esc(e.source)}</span>` : "";
  return `<div class="entry ${e.open_item ? "open" : ""}"><div class="lab">${esc(e.label)}${badge}</div><div class="val">${esc(e.value)}${src}</div></div>`;
}
function cardHtml(sections) { return sections.map((s) => `<div class="sec"><h4>${esc(s.title)}</h4>${s.entries.length ? s.entries.map(entryHtml).join("") : '<div class="muted small">No entries.</div>'}</div>`).join(""); }

function renderResult(el, reg, withDecision) {
  const a = reg.assessment;
  const r = a.risk;
  const tabs = [["tier", "Risk tier assessment"], ["affected", "Who is affected"], ["model", "Model card"], ["system", "System card"], ["gaps", "Framework gap map"], ["open", `Open items (${a.open_items.length})`], ["trace", "Conversation"]];
  el.innerHTML = `
    <div class="row between wrap"><div><h2>${esc(reg.system_name)}</h2><div class="muted small">${esc(reg.id)} · submitted ${esc((reg.submitted || "").replace("T", " ").replace("Z", " UTC"))}${reg.seeded ? " · seeded synthetic record" : ""}</div></div>
    <div class="row gap wrap"><button class="ghost" data-dl="md">Download Markdown</button><button class="ghost" data-dl="json">Download JSON</button></div></div>
    <div class="headline">Bank tier ${tierBadge(a.bank_tier)} EU AI Act reference ${tierBadge(a.eu_tier)}
      <span class="status ${r.within_appetite ? "approved" : "pending_committee"}">Risk score ${r.score}/100 vs appetite ${r.threshold}: ${r.within_appetite ? "within" : "ABOVE"} appetite</span> ${statusBadge(reg.status)}</div>
    ${a.review_flags.length ? `<div class="notice">${a.review_flags.map((f) => "• " + esc(f)).join("<br>")}</div>` : ""}
    ${withDecision ? decisionHtml(reg) : `<div class="notice ok">Draft added to the inventory with status <b>${esc(STATUS_LABEL[reg.status])}</b>. Approval route: <b>${esc(a.approval_route)}</b>.</div>`}
    <div class="subtabs">${tabs.map(([k, l], i) => `<button data-rt="${k}" class="${i ? "" : "active"}">${esc(l)}</button>`).join("")}</div>
    <div class="rt-body"></div>`;
  const body = $(".rt-body", el);
  const show = (k) => {
    $$("[data-rt]", el).forEach((b) => b.classList.toggle("active", b.dataset.rt === k));
    if (k === "tier") body.innerHTML = tierHtml(a);
    if (k === "affected") body.innerHTML = `<div class="table-wrap"><table><thead><tr><th>Group</th><th>How affected</th><th>Harm if the system is wrong</th><th>Severity</th><th>Source</th></tr></thead><tbody>${a.affected_parties.map((p) => `<tr><td><b>${esc(p.label)}</b><div class="muted small">${esc(p.description)}</div></td><td>${esc(p.how_affected)}</td><td>${esc(p.harm_if_wrong)}</td><td>${esc(p.severity)}</td><td class="small muted">${esc(p.source)}</td></tr>`).join("")}</tbody></table></div>`;
    if (k === "model") body.innerHTML = `<p class="muted small">Sections follow Mitchell et al. (2019), Model Cards for Model Reporting. Every value is the team's own statement (quoted) or marked Not provided; nothing is assumed.</p>` + cardHtml(reg.cards.model_card);
    if (k === "system") body.innerHTML = `<p class="muted small">Covers the whole deployed system: components, people, oversight, data flows, transparency, safeguards, operations and regulatory position.</p>` + cardHtml(reg.cards.system_card);
    if (k === "gaps") body.innerHTML = gapsHtml(a.coverage);
    if (k === "open") body.innerHTML = a.open_items.length ? `<ul>${a.open_items.map((o) => `<li><b>${esc(o.label)}</b> <span class="muted small">${esc(o.why)}</span></li>`).join("")}</ul>` : `<p>No open items.</p>`;
    if (k === "trace") body.innerHTML = (reg.conversation || []).map((t) => `<div class="msg ${esc(t.role)}" style="max-width:100%;margin-bottom:8px"><div class="who">${t.role === "user" ? "Team" : "Assistant"}</div>${esc(t.text)}</div>`).join("") +
      (reg.dropped_facts && reg.dropped_facts.length ? `<div class="notice">Facts proposed by the model but dropped because the quote could not be found in the team's words: ${reg.dropped_facts.map((d) => esc(d.id)).join(", ")}</div>` : "") +
      (reg.usage ? `<p class="muted small">Assessment step: ${reg.usage.calls} model calls, ${reg.usage.total_tokens} tokens, $${Number(reg.usage.cost_usd).toFixed(5)}.</p>` : "");
  };
  $$("[data-rt]", el).forEach((b) => b.addEventListener("click", () => show(b.dataset.rt)));
  $$("[data-dl]", el).forEach((b) => b.addEventListener("click", () => download(reg, b.dataset.dl)));
  $$("[data-dec]", el).forEach((b) => b.addEventListener("click", () => decide(reg, b.dataset.dec)));
  show("tier");
  el.classList.remove("hidden");
}

function tierHtml(a) {
  const sig = a.signals.length ? `<div class="table-wrap"><table><thead><tr><th>Basis</th><th>What it means</th><th>Tier</th><th>Evidence (team's words)</th><th>Source</th></tr></thead><tbody>${a.signals.map((s) => `<tr><td><b>${esc(s.ref)}</b></td><td>${esc(s.label)}</td><td>${tierBadge(s.tier)}</td><td class="small">${esc(s.evidence)}</td><td class="small muted">${esc(s.source)}</td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">No tier trigger applies.</p>`;
  const dims = Object.entries(a.risk.dimensions).map(([k, v]) => `<div class="bar"><div class="lbl"><span>${esc(k.replace("_", " "))}</span><span>${v}/5</span></div><div class="track"><div class="fill" style="width:${v * 20}%"></div></div></div>`).join("");
  const mc = a.mandatory_controls.length ? `<table><thead><tr><th>Mandatory control for this tier</th><th>Status</th></tr></thead><tbody>${a.mandatory_controls.map((c) => `<tr><td>${esc(c.label)}</td><td><span class="badge ${esc(c.status.replace(" ", "_"))}">${esc(c.status.replace("_", " "))}</span></td></tr>`).join("")}</tbody></table>` : "";
  const obl = a.obligations.length ? `<details open><summary>EU AI Act obligations attached to the reference tier (${a.obligations.length})</summary><ul class="small">${a.obligations.map((o) => `<li><b>${esc(o.ref)} ${esc(o.title)}</b>: ${esc(o.text)}</li>`).join("")}</ul></details>` : "";
  return `<p>${esc(a.tier_rationale)}</p>${sig}
    <div class="grid2" style="margin-top:12px"><div><h4>Inherent-risk score: ${a.risk.score}/100 (appetite ${a.risk.threshold})</h4>${dims}<p class="muted small">Weights and threshold are set by the administrator.</p></div><div>${mc}</div></div>
    ${a.model_rationale ? `<details><summary>Model's own view (advisory, cannot lower a rule floor): ${esc(a.model_proposed_tier || "")}</summary><p class="small">${esc(a.model_rationale)}</p></details>` : ""}${obl}`;
}

function gapsHtml(cov) {
  const fwBlock = (fw) => {
    const c = cov[fw]; if (!c) return "";
    const rows = Object.entries(c.clauses).sort().map(([ref, d]) => `<tr><td><b>${esc(ref)}</b></td><td><span class="badge ${d.state === "evidenced" ? "done" : d.state === "declared_absent" ? "planned" : "not_done"}">${esc(d.state.replace("_", " "))}</span></td><td class="small muted">${esc(d.fields.map((f) => (S.frameworks && S.frameworks.qb[f] && S.frameworks.qb[f].label) || f).join(", "))}</td></tr>`).join("");
    return `<div class="sec"><h4>${FW_LABEL[fw]}: ${c.evidenced}/${c.total} clauses evidenced (${c.pct}%)</h4><div class="table-wrap"><table><thead><tr><th>Clause</th><th>State</th><th>Evidence from</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
  };
  const nf = cov.nist_functions ? `<p class="small">NIST functions: ${Object.entries(cov.nist_functions).map(([k, v]) => `<b>${esc(k)}</b> ${v.evidenced}/${v.total}`).join(" · ")}</p>` : "";
  return `<p class="muted small">"Evidenced" means the team described something in place; "declared absent" means they said it is planned or not done; "missing" means it was required but not provided.</p>${nf}` + ["eu", "nist", "aigp"].map(fwBlock).join("");
}

function download(reg, kind) {
  const blob = kind === "json" ? new Blob([JSON.stringify(reg, null, 2)], { type: "application/json" }) : new Blob([reg.markdown || "(markdown not available)"], { type: "text/markdown" });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `${reg.id}.${kind === "json" ? "json" : "md"}`; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

/* ---------------- inventory ---------------- */
function localInventory() { return store.get("registry_local", []); }
async function loadInventory() {
  try {
    const out = await api("/api/inventory");
    S.persistent = out.persistent_store;
    const local = S.persistent ? [] : localInventory();
    const ids = new Set(local.map((r) => r.id));
    S.inventory = [...local, ...out.items.filter((r) => !ids.has(r.id))];
    $("#inv-note").textContent = S.persistent ? "Shared inventory (persistent store connected)." :
      "No shared store connected: seeded synthetic records come from the server and your own registrations are kept in this browser only.";
    renderInventory();
  } catch (e) { toast("Could not load inventory: " + e.message); }
}
function renderInventory() {
  const ft = $("#f-tier").value, fs = $("#f-status").value, q = $("#f-q").value.toLowerCase();
  const items = S.inventory.filter((r) => (!ft || r.assessment.bank_tier === ft) && (!fs || r.status === fs) && (!q || JSON.stringify([r.system_name, r.id, r.domain]).toLowerCase().includes(q)));
  const all = S.inventory;
  const count = (f) => all.filter(f).length;
  $("#kpis").innerHTML = [
    ["Registered use cases", all.length], ["High risk", count((r) => r.assessment.bank_tier === "high")], ["Prohibited", count((r) => r.assessment.bank_tier === "prohibited")],
    ["Above risk appetite", count((r) => !r.assessment.risk.within_appetite)], ["Awaiting decision", count((r) => r.status.startsWith("pending"))], ["Approved", count((r) => r.status === "approved")],
  ].map(([l, n]) => `<div class="kpi"><div class="n">${n}</div><div class="l">${esc(l)}</div></div>`).join("");
  $("#inv-body").innerHTML = items.map((r) => `<tr class="click" data-id="${esc(r.id)}"><td class="small">${esc(r.id)}</td><td><b>${esc(r.system_name)}</b></td><td class="small">${esc(r.domain || "")}</td><td>${tierBadge(r.assessment.bank_tier)}</td><td>${tierBadge(r.assessment.eu_tier)}</td><td>${r.assessment.risk.score}${r.assessment.risk.within_appetite ? "" : " ▲"}</td><td>${statusBadge(r.status)}</td><td class="small">${esc((r.submitted || "").slice(0, 10))}</td></tr>`).join("") || `<tr><td colspan="8" class="muted">No registrations match.</td></tr>`;
  $$("#inv-body tr.click").forEach((tr) => tr.addEventListener("click", () => { const reg = S.inventory.find((x) => x.id === tr.dataset.id); S.detail = reg; renderDetail(reg); }));
}
["#f-tier", "#f-status", "#f-q"].forEach((s) => $(s).addEventListener("input", renderInventory));
function renderDetail(reg) { const el = $("#inv-detail"); renderResult(el, reg, true); el.scrollIntoView({ behavior: "smooth", block: "start" }); }

function decisionHtml(reg) {
  const r = role(); const a = reg.assessment;
  if (!reg.status.startsWith("pending")) return `<div class="notice ok">Decision recorded: <b>${esc(STATUS_LABEL[reg.status])}</b>${(reg.history || []).length ? " by " + esc(reg.history.slice(-1)[0].reviewer) : ""}.</div>`;
  const canOffice = r === "office" && !a.committee_required;
  const canCommittee = r === "committee";
  if (!canOffice && !canCommittee) {
    return `<div class="notice">Awaiting ${esc(a.approval_route)}. ${r === "office" && a.committee_required ? "This one is high risk or above appetite, so the office can only refer it to the committee." : "Switch \"Viewing as\" to the approver role to decide."} ${r === "office" ? '<button class="ghost" data-dec="committee">Refer to committee</button>' : ""}</div>`;
  }
  const approve = a.bank_tier === "prohibited" ? "" : `<button class="ok" data-dec="approve">Approve</button>`;
  return `<div class="notice">Decision as <b>${r === "committee" ? "AI governance committee" : "AI governance office"}</b>: ${approve} <button class="ghost" data-dec="return">Return to team</button> <button class="bad" data-dec="reject">Reject</button>${a.open_items.length ? ` <span class="small">(${a.open_items.length} open items)</span>` : ""}</div>`;
}
async function decide(reg, decision) {
  const reviewer = role() === "committee" ? "AI governance committee" : "AI governance office";
  try {
    const out = await api("/api/decision", { method: "POST", body: JSON.stringify({ id: reg.id, decision, reviewer, registration: S.persistent ? null : reg }) });
    const upd = out.registration;
    if (!out.persistent_store) { const l = localInventory().filter((x) => x.id !== upd.id); l.unshift(upd); store.set("registry_local", l); }
    toast(`Recorded: ${STATUS_LABEL[upd.status]}`);
    await loadInventory(); S.detail = S.inventory.find((x) => x.id === upd.id) || upd; renderDetail(S.detail);
  } catch (e) { toast(e.message); }
}

/* ---------------- admin ---------------- */
async function loadConfig() {
  const out = await api("/api/config");
  S.persistent = out.persistent_store; S.defaults = out.defaults;
  S.config = S.persistent ? out.config : (store.get("registry_config", null) || out.config);
}
function renderAdmin() {
  if (!S.config || !S.frameworks) return;
  const c = S.config; const editable = role() === "admin";
  $("#admin-note").textContent = (editable ? "" : "Read-only: switch \"Viewing as\" to Administrator to edit. ") + (S.persistent ? "Saved to the shared store." : "No shared store: saved in this browser and sent with each request.");
  const ctrlFields = Object.values(S.frameworks.qb).filter((f) => f.kind === "control");
  const dis = editable ? "" : "disabled";
  $("#admin-form").innerHTML = `
    <div class="form-row"><label for="thr"><b>Risk appetite threshold</b><div class="muted small">${esc(c.risk_appetite.description)}</div></label><div class="row gap"><input type="range" id="thr" min="0" max="100" value="${c.risk_appetite.threshold}" ${dis}><b id="thr-v">${c.risk_appetite.threshold}</b></div></div>
    <div class="form-row"><div><b>Score weights</b><div class="muted small">Relative weight of each inherent-risk dimension (1-5 each).</div></div><div class="grid2">${Object.entries(c.weights).map(([k, v]) => `<label class="small">${esc(k.replace("_", " "))} <input type="number" step="0.05" min="0" max="1" data-w="${esc(k)}" value="${v}" ${dis} style="width:80px"></label>`).join("")}</div></div>
    <div class="form-row"><div><b>Minimum-tier rules</b><div class="muted small">Hard floors the conversation cannot lower.</div></div><div>${Object.entries(c.min_tier_rules).map(([k, r]) => `<label class="row gap small" style="margin:4px 0"><input type="checkbox" data-rule="${esc(k)}" ${r.enabled ? "checked" : ""} ${dis}> ${tierBadge(r.tier)} ${esc(r.label)}</label>`).join("")}</div></div>
    <div class="form-row"><label><b>Allow Art. 6(3) derogation</b><div class="muted small">If on, an Annex III use case can drop out of high risk when the model finds a derogation and no profiling. Bank rules still apply.</div></label><div><input type="checkbox" id="derog" ${c.allow_art6_3_derogation ? "checked" : ""} ${dis}></div></div>
    <div class="form-row"><label for="bp"><b>Bank prohibited uses</b><div class="muted small">One per line. A match makes the use case prohibited at the Bank.</div></label><textarea id="bp" rows="4" ${dis}>${esc(c.bank_prohibited_uses.join("\n"))}</textarea></div>
    <div class="form-row"><div><b>Conversation limits</b></div><div class="row gap wrap small"><label>Max follow-up rounds <input type="number" id="rounds" min="1" max="8" value="${c.max_followup_rounds}" ${dis} style="width:70px"></label><label>Questions per round <input type="number" id="qpr" min="1" max="8" value="${c.questions_per_round}" ${dis} style="width:70px"></label></div></div>
    <div class="sec"><h4>Mandatory controls per tier</h4><div class="ctrl-grid"><table><thead><tr><th>Control</th>${["minimal", "limited", "high"].map((t) => `<th>${tierBadge(t)}</th>`).join("")}</tr></thead><tbody>${ctrlFields.map((f) => `<tr><td>${esc(f.label)}</td>${["minimal", "limited", "high"].map((t) => `<td><input type="checkbox" data-mc="${t}:${esc(f.id)}" ${c.mandatory_controls[t].includes(f.id) ? "checked" : ""} ${dis}></td>`).join("")}</tr>`).join("")}</tbody></table></div></div>`;
  $("#thr").addEventListener("input", (e) => { $("#thr-v").textContent = e.target.value; });
  $("#save-cfg").disabled = !editable; $("#reset-cfg").disabled = !editable;
}
function readAdmin() {
  const c = JSON.parse(JSON.stringify(S.config));
  c.risk_appetite.threshold = Number($("#thr").value);
  $$("[data-w]").forEach((i) => { c.weights[i.dataset.w] = Number(i.value); });
  $$("[data-rule]").forEach((i) => { c.min_tier_rules[i.dataset.rule].enabled = i.checked; });
  c.allow_art6_3_derogation = $("#derog").checked;
  c.bank_prohibited_uses = $("#bp").value.split("\n").map((s) => s.trim()).filter(Boolean);
  c.max_followup_rounds = Number($("#rounds").value); c.questions_per_round = Number($("#qpr").value);
  for (const t of ["minimal", "limited", "high"]) c.mandatory_controls[t] = $$(`[data-mc^="${t}:"]`).filter((i) => i.checked).map((i) => i.dataset.mc.split(":")[1]);
  return c;
}
$("#save-cfg").addEventListener("click", async () => {
  try {
    const out = await api("/api/config", { method: "PUT", body: JSON.stringify(readAdmin()) });
    S.config = out.config; if (!out.saved) store.set("registry_config", out.config);
    toast(`Configuration v${out.config.version} saved${out.saved ? " for everyone" : " in this browser"}. New registrations use it.`); renderAdmin();
  } catch (e) { toast(e.message); }
});
$("#reset-cfg").addEventListener("click", async () => {
  S.config = JSON.parse(JSON.stringify(S.defaults)); store.del("registry_config");
  if (S.persistent) await api("/api/config", { method: "PUT", body: JSON.stringify(S.config) });
  toast("Defaults restored."); renderAdmin();
});

/* ---------------- frameworks ---------------- */
async function loadFrameworks() {
  const fw = await api("/api/frameworks");
  fw.qb = Object.fromEntries(fw.question_bank.map((f) => [f.id, f]));
  S.frameworks = fw;
}
function renderFrameworks(which) {
  const fw = S.frameworks; if (!fw) return;
  which = which || ($(".subtabs#fw-subtabs .active") || {}).dataset?.fw || "bank";
  $$("#fw-subtabs button").forEach((b) => b.classList.toggle("active", b.dataset.fw === which));
  const b = $("#fw-body");
  if (which === "bank") {
    b.innerHTML = `<p class="small muted">${fw.question_bank.length} fields. "Required when" decides whether the chatbot asks.</p><div class="table-wrap"><table><thead><tr><th>Field</th><th>Question</th><th>Required when</th><th>EU AI Act</th><th>NIST AI RMF</th><th>AIGP</th></tr></thead><tbody>${fw.question_bank.map((f) => `<tr><td><b>${esc(f.label)}</b><div class="small muted">${esc(f.section)} · ${esc(f.kind)}</div></td><td class="small">${esc(f.question)}</td><td class="small">${esc(f.required_when.replace("_", " "))}</td><td class="small">${esc((f.refs.eu || []).join(", "))}</td><td class="small">${esc((f.refs.nist || []).join(", "))}</td><td class="small">${esc((f.refs.aigp || []).join(", "))}</td></tr>`).join("")}</tbody></table></div>`;
  } else if (which === "eu") {
    const e = fw.eu_ai_act;
    b.innerHTML = `<p class="small muted">${esc(e.source)}</p><h4>Timeline</h4><ul class="small">${e.timeline.map((t) => `<li><b>${esc(t.date)}</b> ${esc(t.event)}</li>`).join("")}</ul>
      <h4>Tiers</h4><ul class="small">${Object.entries(e.tiers).map(([k, t]) => `<li>${tierBadge(k)} <b>${esc(t.basis)}</b>: ${esc(t.summary)}</li>`).join("")}</ul>
      <h4>Article 5: prohibited practices</h4><ul class="small">${e.prohibited.map((p) => `<li><b>${esc(p.ref)} ${esc(p.name)}.</b> ${esc(p.text)}</li>`).join("")}</ul>
      <h4>Article 6</h4><ul class="small">${Object.entries(e.art6).map(([k, v]) => `<li><b>${esc(k)}</b> ${esc(v)}</li>`).join("")}</ul>
      <h4>Annex III high-risk areas</h4><ul class="small">${e.annex_iii.map((p) => `<li><b>${esc(p.ref)} ${esc(p.area)}.</b> ${esc(p.text)}</li>`).join("")}</ul>
      <h4>Requirements and obligations</h4><ul class="small">${e.requirements.map((p) => `<li><b>${esc(p.ref)} ${esc(p.title)}</b> <span class="muted">(applies: ${esc(p.applies)})</span>. ${esc(p.text)}</li>`).join("")}</ul>`;
  } else if (which === "nist") {
    const n = fw.nist_ai_rmf;
    const cover = {}; fw.question_bank.forEach((f) => (f.refs.nist || []).forEach((r) => { (cover[r] = cover[r] || []).push(f.label); }));
    let count = 0;
    b.innerHTML = `<p class="small muted">${esc(n.source)}</p><h4>Trustworthiness characteristics</h4><ul class="small">${n.trustworthy.map((t) => `<li><b>${esc(t.name)}</b>: ${esc(t.text)}</li>`).join("")}</ul>` +
      Object.entries(n.core).map(([fn, d]) => `<h4>${esc(fn)}</h4><p class="small muted">${esc(d.purpose)}</p>` + Object.entries(d.categories).map(([c, cat]) => `<div class="sec"><b class="small">${esc(c)}: ${esc(cat.text)}</b><div class="table-wrap"><table><tbody>${Object.entries(cat.subcategories).map(([s, t]) => { count++; return `<tr><td class="small" style="width:110px"><b>${esc(s)}</b></td><td class="small">${esc(t)}</td><td class="small muted" style="width:30%">${cover[s] ? "Asked via: " + esc(cover[s].join(", ")) : "Organisation-level (not asked per use case)"}</td></tr>`; }).join("")}</tbody></table></div></div>`).join("")).join("") +
      `<h4>Generative AI Profile (NIST AI 600-1): 12 risks</h4><ul class="small">${n.genai_risks.map((r) => `<li>${esc(r.name)}</li>`).join("")}</ul>`;
    b.insertAdjacentHTML("afterbegin", `<p class="small"><b>${count} subcategories</b>; ${Object.keys(cover).filter((k) => /^(GOVERN|MAP|MEASURE|MANAGE)/.test(k)).length} are evidenced per use case by the question bank. The rest are organisation-level (policies, culture, workforce) and belong to the governance programme, not to a single registration.</p>`);
  } else {
    const a = fw.aigp;
    b.innerHTML = `<p class="small muted">${esc(a.source)}</p>` + Object.entries(a.domains).map(([k, d]) => `<h4>Domain ${esc(k)}: ${esc(d.name)}</h4>` + Object.entries(d.competencies).map(([c, x]) => `<div class="sec"><b class="small">${esc(c)} ${esc(x.name)}</b><ul class="small">${x.indicators.map((i) => `<li>${esc(i)}</li>`).join("")}</ul></div>`).join("")).join("");
  }
}
$$("#fw-subtabs button").forEach((b) => b.addEventListener("click", () => renderFrameworks(b.dataset.fw)));

/* ---------------- about ---------------- */
async function renderAbout() {
  let ev = null;
  try { const r = await fetch("/eval_summary.json"); if (r.ok) ev = await r.json(); } catch { /* none yet */ }
  const steps = [["1 Guard", "Personal-data scan (CNIC, IBAN, card, phone, account, e-mail, pasted tables). A hit blocks the message before the model."],
    ["2 Extract", "The model maps the message to registration fields. Every fact needs a verbatim quote, checked in code; unverified facts are dropped."],
    ["3 Gaps", "Code works out which fields this use case requires (by domain, people affected, vendor, GenAI, tier floor) and which are missing."],
    ["4 Ask", "Up to 5 missing fields per round, highest priority first, each with its framework reason. The model only words them."],
    ["5 Screen", "The model screens the facts and the team's own words against Art. 5, Annex III, Art. 6(3), the Bank's prohibited uses, and lists affected parties."],
    ["6 Tier", "Hard rules set a floor the conversation cannot lower; verified model signals can raise it. EU reference tier and Bank tier reported."],
    ["7 Score", "Inherent-risk score (impact, autonomy, data, scale, vulnerability, control gaps) against the administrator's appetite."],
    ["8 Cards + write", "Model card and system card from verified facts only; gaps become open items. Draft written to the inventory, pending approval."]];
  const evHtml = ev ? `<h3>Evaluation (from the notebook)</h3><div class="table-wrap"><table><thead><tr><th>Metric (Phase 1 target)</th>${ev.columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${ev.rows.map((r) => `<tr><td>${esc(r[0])}</td>${r.slice(1).map((x) => `<td>${esc(x)}</td>`).join("")}</tr>`).join("")}</tbody></table></div><p class="small muted">${esc(ev.note || "")}</p>` : `<p class="muted small">Evaluation results appear here once the notebook has been run.</p>`;
  $("#about").innerHTML = `<h2>How the registry works</h2>
    <p>Each team registers its AI use case by chatting with this assistant. It checks the brief against what the EU AI Act, the NIST AI RMF and the IAPP AIGP body of knowledge require to be known, asks follow-up questions only about what is missing, and produces a draft <b>risk tier assessment</b>, <b>who will be affected</b>, a <b>model card</b> and a <b>system card</b>. The draft goes into the AI inventory as pending: it is never official until the AI governance office (or the committee, for high-risk and above-appetite cases) approves it.</p>
    <div class="pipeline">${steps.map(([t, d]) => `<div class="step"><b>${esc(t)}</b>${esc(d)}</div>`).join("")}</div>
    <h3>Design choices from the Phase 1 assessment (reduced scope)</h3>
    <ul><li>The chatbot proposes; people approve. It talks to the team that wants approval, so it is never the approver.</li>
    <li>Hard minimum-tier rules, so a team cannot talk a credit model down to minimal risk by calling it a helper.</li>
    <li>Cards never fill gaps with assumptions: anything not provided is shown as Not provided and becomes an open item.</li>
    <li>No customer data is accepted: the guard runs before the model.</li>
    <li>The administrator, not the chatbot, sets the risk appetite.</li></ul>
    ${evHtml}
    <h3>Known limits</h3><ul><li>Synthetic data only; gold labels set by the author, not two independent expert reviewers.</li><li>Keyword rules over-fire on some wording (for example "manipulated video" in deepfake detection) and miss others; see the notebook's held-out results.</li><li>No user authentication: the role switcher is for demonstration. Production would use the Bank's SSO.</li><li>Hosted on Vercel and Groq (offshore) for the demo; production would run onshore as set out in Phase 1.</li></ul>`;
}

/* ---------------- samples, file attach, wiring ---------------- */
async function loadSamples() {
  try {
    const r = await fetch("/samples.json"); if (!r.ok) return;
    S.samples = await r.json();
    $("#sample").innerHTML = `<option value="">Load a synthetic sample brief…</option>` + S.samples.map((s, i) => `<option value="${i}">${esc(s.label)}</option>`).join("");
  } catch { /* optional */ }
}
$("#sample").addEventListener("change", (e) => { const s = S.samples && S.samples[e.target.value]; if (s) { $("#input").value = s.brief; $("#input").focus(); } e.target.value = ""; });
$("#file").addEventListener("change", async (e) => {
  const f = e.target.files[0]; e.target.value = ""; if (!f) return;
  if (!/\.(txt|md)$/i.test(f.name) || f.size > 60000) { toast("Attach a .txt or .md document under 60 KB. Datasets (CSV, Excel, JSON) are not accepted: describe data, do not upload it."); return; }
  const text = await f.text(); $("#input").value = ($("#input").value ? $("#input").value + "\n\n" : "") + `[Attached document: ${f.name}]\n` + text;
});
$("#composer").addEventListener("submit", (e) => { e.preventDefault(); const v = $("#input").value; $("#input").value = ""; send(v); });
$("#input").addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); $("#composer").requestSubmit(); } });
$("#finish-btn").addEventListener("click", () => send("finish"));
$("#new-session").addEventListener("click", () => { if (!S.state || S.state.turns.length < 2 || confirm("Start a new registration? The current conversation will be cleared.")) newSession(); });

(async function init() {
  const r0 = store.get("role", "team"); $("#role").value = r0;
  try {
    S.health = await api("/api/health");
    S.persistent = S.health.persistent_store;
    $("#status-pill").textContent = S.health.llm_configured ? `Model online · ${S.health.model.replace("openai/", "")} · ${S.persistent ? "shared inventory" : "browser inventory"}` : "Model key not configured on the server";
  } catch { $("#status-pill").textContent = "API unreachable"; }
  await Promise.allSettled([loadFrameworks(), loadConfig(), loadSamples()]);
  const saved = store.get("session", null);
  if (saved && saved.state) { S.state = saved.state; S.usage = saved.usage; S.result = saved.result; renderMessages(); renderSide(saved.progress); if (S.result) renderResult($("#result"), S.result, false); }
  else await newSession();
  showTab(store.get("tab", "register"));
})();
})();
