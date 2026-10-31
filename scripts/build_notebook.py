"""Builds notebooks/DATA722_Phase2_UseCaseC.ipynb (then execute it with nbconvert).

  python scripts/build_notebook.py
  jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=7200 notebooks/DATA722_Phase2_UseCaseC.ipynb
"""
import json
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / "notebooks" / "meta.json").read_text()) if (ROOT / "notebooks" / "meta.json").exists() else {}
NOTES = json.loads((ROOT / "notebooks" / "findings.json").read_text()) if (ROOT / "notebooks" / "findings.json").exists() else {}

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))  # noqa: E731
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))  # noqa: E731

APP = META.get("app_url", "(Vercel URL - added at deployment)")
REPO = META.get("repo_url", "(GitHub repository URL)")
SID = META.get("student_id", "(Student ID)")

md(f"""
# DATA722 Phase 2: AI use case registration and risk-tiering chatbot (use case C)

| | |
|---|---|
| Course | DATA722 Generative AI & Strategic Forecasting (Instructor: Danish Haroon) |
| Student | Azmina Lalani, {SID} |
| Use case | C: a chatbot each team uses to register its AI use case. It checks the brief against the EU AI Act, NIST AI RMF and AIGP, asks follow-up questions about what is missing, and produces a risk tier assessment, the affected parties, a model card and a system card that are added to the AI inventory. |
| Hosted application | {APP} |
| Source code | {REPO} |
| Model | OpenAI `gpt-oss-120b` (open-weight) served by Groq |
| Data | **Synthetic only.** All use cases, teams, vendors and inventory records are fictional (Phase 1, question 6: no customer data is needed or accepted). |

This notebook is the working record. It contains:

1. what was built and how it traces to the Phase 1 assessment;
2. the synthetic data and the framework knowledge base;
3. the prompts, context design and agent loop at the centre of the system;
4. a live registration traced turn by turn, with tokens and cost;
5. how I got there: the version 1 baseline, the development iterations and the failures found;
6. the evaluation: the Phase 1 metrics run against the built system, with scores, on a development set and a held-out set;
7. token and cost figures;
8. the honesty section.

**Phase 1 verdict and what I built.** Phase 1 rated use case C *Go, reduced scope*. I built it under that reduced scope and did not reverse any of the reductions: the chatbot only drafts; registrations stay pending until the AI governance office (or the committee for high-risk and above-appetite cases) approves them; hard minimum-tier rules cannot be lowered by the conversation; cards never fill gaps with assumptions; customer data is blocked before the model. The one thing Phase 1 named as the next increment, integration with the vendor and IT asset registers, is **not** built.
""")

md("""
## 1. Traceability: Phase 1 commitments and where they are implemented

| Phase 1 commitment | Implemented in |
|---|---|
| Team self-service chatbot, follow-ups driven by EU AI Act, NIST AI RMF, AIGP | `engine/agent.py` (loop), `engine/kb/schema.py` (40-field question bank with clause mapping), `engine/gaps.py` |
| Asks only about what is missing (redundant-question rate <= 5%) | deterministic gap selection in `engine/gaps.py`; extraction keeps what was already said |
| Administrator sets the risk appetite and minimum-tier rules | `engine/config.py`, Admin tab, `PUT /api/config` |
| Output: risk tier assessment, affected parties, model card, system card | `Agent.finalize`, `engine/cards.py`; Register tab result view; Markdown/JSON download |
| Adds up into the inventory, pending approval | `engine/store.py`, Inventory tab, `POST /api/decision` (role-gated) |
| Hard rules set a minimum tier (credit decisions about individuals, biometric identification, acting on customers without review start at high) | `engine/rules.py` `floor_signals` |
| Cards never fill gaps with assumptions | `engine/cards.py` (`Not provided` + open items); quote verification in `engine/verify.py` |
| Personal-data check before the model; documents, not datasets | `engine/pii.py`; the UI accepts only `.txt` / `.md` |
| The chatbot tells users it is an AI (Art. 50(1)) | opening message and banner |
| Duplicate check against the existing inventory | `engine/agent.py` `duplicates()` |
| Vendor and IT asset register integration | **Not built** (next increment, as stated in Phase 1) |
| Eval metrics fixed in Phase 1 rows 7 and 7a | Section 6 of this notebook; `eval/harness.py` |
""")

code("""
import os, sys, json, inspect, textwrap, statistics
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
import pandas as pd
import matplotlib.pyplot as plt
pd.set_option("display.max_colwidth", 120); pd.set_option("display.width", 200)

from engine.config import MODEL, PRICES, DEFAULT_CONFIG
from engine.kb import eu_ai_act as EU, nist_ai_rmf as NIST, aigp as AIGP
from engine.kb.schema import FIELDS
from engine import prompts, pii
print("Model:", MODEL, "| prices USD per 1M tokens:", PRICES[MODEL])
print("GROQ_API_KEY set:", bool(os.environ.get("GROQ_API_KEY")))
""")

md("""
## 2. Synthetic data

Real use case registrations would contain vendor contracts, model test results and system owner names, which are confidential; the Phase 1 rule is that real confidential data stays where it is. Everything here is synthetic and generated by code in the repository (`scripts/archetypes.py`, `scripts/archetypes_holdout.py`, `scripts/make_synthetic.py`, `scripts/make_seed_and_samples.py`).

**How the gold set was built.** I wrote 33 archetypes of AI systems a Pakistani digital bank might register (credit scoring, nano-loans, CV screening, chatbots, fraud blocking, emotion recognition, coding assistants, and so on). Each archetype has a full hidden fact sheet: the answer the team would give to every one of the 40 registration questions, including controls the team has *not* put in place. From each archetype the generator makes one to three test cases:

* **complete**: the brief states every required fact (tests redundant questions);
* **seeded**: 4 to 6 required facts are deliberately removed from the brief (tests gap detection recall);
* **adversarial**: a hand-written brief that understates the system, e.g. a credit score described as a "helper tool" (tests under-tiering, Phase 1 row 7a).

Gold labels per case: the Bank tier under the default admin configuration, the EU AI Act reference tier, the legal basis, and the affected-party categories. A **held-out set** of 14 further cases was written *after* the tiering rules were frozen (git commit `2fc5493`) and was never used for tuning.

Also generated: 24 personal-data guard test messages, 10 seeded inventory records, and 8 sample briefs for the hosted app.
""")

code("""
dev = json.loads(Path("data/synthetic/gold_cases.json").read_text())
hold = json.loads(Path("data/synthetic/holdout_cases.json").read_text())
pii_cases = json.loads(Path("data/synthetic/pii_cases.json").read_text())
seed = json.loads(Path("data/synthetic/seed_inventory.json").read_text())
df = pd.DataFrame([{"set": s, "id": c["id"], "title": c["title"], "variant": c["variant"], "gold_tier": c["gold"]["tier"],
                    "gold_eu_tier": c["gold"]["eu_tier"], "basis": ", ".join(c["gold"]["codes"]), "seeded_gaps": len(c["seeded_gaps"])}
                   for s, cs in (("dev", dev), ("held-out", hold)) for c in cs])
print(f"{len(dev)} development cases, {len(hold)} held-out cases, {len(pii_cases)} guard tests, {len(seed)} seeded inventory records")
display(pd.crosstab([df.set, df.variant], df.gold_tier, margins=True))
""")

code("""
c = next(x for x in dev if x["id"] == "H1-A")
print("ADVERSARIAL BRIEF (what the team pastes):\\n", textwrap.fill(c["brief"], 110))
print("\\nHIDDEN FACTS the simulated team gives only when asked (first 8 of", sum(1 for v in c["facts"].values() if v), "):")
for k, v in list((k, v) for k, v in c["facts"].items() if v)[:8]:
    print(f"  {k:<22} {v}")
print("\\nGOLD:", c["gold"]["tier"], "|", c["gold"]["rationale"])
""")

md("""
## 3. The framework knowledge base and question bank

I could not use the official PDFs inside the app, so the frameworks are encoded as structured data written for this tool (condensed paraphrases with article and subcategory references, `engine/kb/`):

* **EU AI Act** (Regulation (EU) 2024/1689): definitions (Art. 3), scope (Art. 2), all eight Art. 5 prohibited practices, Art. 6(1)-(4) including the 6(3) derogations and the profiling override, all Annex III areas, the requirements and obligations (Art. 4, 9-17, 25-27, 43, 49, 50(1)-(4), 53, 55, 72, 73, 86, 99), tiers and timeline.
* **NIST AI RMF 1.0**: all 4 functions, 19 categories and **72 subcategories**, the 7 trustworthiness characteristics, and the 12 risks of the Generative AI Profile (AI 600-1).
* **IAPP AIGP body of knowledge**: the four domains and their competencies.

The **question bank** is 40 registration fields. Each field carries the clauses that require it and a condition saying when it is required (for example `decisions_about_people`, `vendor`, `genai`, `high_candidate`). That mapping is what lets the chatbot ask a credit team about adverse-action explanations and bias testing, and not ask an internal search tool the same.
""")

code("""
nist_subs = NIST.all_subcategories()
asked = {r for f in FIELDS for r in f["refs"].get("nist", []) if r in nist_subs}
print(f"EU AI Act: {len(EU.PROHIBITED)} prohibited practices, {len(EU.ANNEX_III)} Annex III entries, {len(EU.REQUIREMENTS)} requirement/obligation entries")
print(f"NIST AI RMF: {len(nist_subs)} subcategories; {len(asked)} are evidenced per use case by the question bank; the rest are organisation-level")
print(f"AIGP: {sum(len(d['competencies']) for d in AIGP.DOMAINS.values())} competencies in {len(AIGP.DOMAINS)} domains")
print(f"Question bank: {len(FIELDS)} fields ({sum(f['kind']=='control' for f in FIELDS)} controls)")
qb = pd.DataFrame([{"field": f["id"], "required_when": f["required_when"], "EU AI Act": ", ".join(f["refs"].get("eu", [])),
                    "NIST": ", ".join(f["refs"].get("nist", [])), "AIGP": ", ".join(f["refs"].get("aigp", []))} for f in FIELDS])
display(qb)
org_level = sorted(set(nist_subs) - asked, key=lambda s: (s.split()[0], [int(x) for x in s.split()[1].split(".")]))
print("NIST subcategories NOT asked per use case (organisation-level programme items):\\n", ", ".join(org_level))
""")

md("""
The NIST subcategories that are not asked per use case (for example GOVERN 3.1 workforce diversity, GOVERN 2.2 training programme, MEASURE 2.12 environmental impact) are properties of the Bank's AI governance programme, not of one registration. Asking every team about them would add questions without changing any tier. This is a deliberate scope choice and is listed in the honesty section.
""")

md("""
## 4. The centre of the system: context design, prompts and the agent loop

### 4.1 What the system does on each request

```
team message
   |
   v
[1 GUARD] personal-data regexes (CNIC, IBAN, Luhn card, mobile, labelled account, e-mail, passport, pasted tables)
   |        hit -> message blocked, never sent to the model, never stored
   v
[2 EXTRACT] model call (gpt-oss-120b, reasoning low): new message -> registration fields
   |        every value must carry a verbatim quote; code verifies the quote is in the team's words, else the fact is dropped
   v
[3 GAPS] code: which of the 40 fields does THIS use case require (domain, people affected, vendor, GenAI, rule floor)? which are missing?
   v
[4 DECIDE] code: missing required fields and rounds left? -> [ASK] up to 5 fields, priority order; model only words them
                                                       else -> READY
[on READY]
[5 SCREEN] model call (reasoning medium): facts + team's own words vs Art. 5, Annex III, Art. 6(3), Bank prohibited uses;
   |        affected parties; summary; proposed tier. Every legal code needs a quote, verified in code.
[6 TIER] code: hard-rule floor (cannot be lowered) + verified model signals (can raise) -> EU reference tier, Bank tier
[7 SCORE] code: inherent-risk score (impact, autonomy, data, scale, vulnerability, control gaps) vs admin appetite
[8 CARDS] code: model card (Mitchell et al. 2019) + system card from verified facts only; gaps -> "Not provided" + open items
[9 WRITE] draft registration to the inventory, status pending approval / pending committee
```

**Why it is an agent.** As argued in Phase 1 (row 4a), the path differs for every use case: the next question depends on what the brief and the earlier answers revealed (a credit model triggers explanation, appeal and bias-testing questions; an internal code assistant does not), and the system takes an action (it writes the registration to the inventory). The *choice* of what to ask is made by code from the framework mapping, not by the model. That is a deliberate design decision: it makes the questioning testable and stops the model skipping awkward questions. The model is used where language is needed: reading free text into fields, wording questions, screening the whole description for legal categories, and summarising.

### 4.2 Context design

| Call | What the model sees | What it never sees | Why |
|---|---|---|---|
| Extract | field catalogue, what is known (short), the questions just asked, **only the new message** | earlier messages | keeps prompts small; quotes can only come from the message being read |
| Ask | a one-line summary and the selected gaps with their clause reasons | the rest of the bank | the model cannot add, drop or reorder questions |
| Screen | the Art. 5 / Annex III / Art. 6(3) catalogue, the Bank's prohibited uses, the affected-party taxonomy, verified facts, the team's full words | nothing withheld | needs all evidence to catch understatement |

The prompts below are the exact strings sent to the model.
""")

code("""
for name in ("EXTRACT_SYSTEM", "ASK_SYSTEM", "SCREEN_SYSTEM", "BASELINE_SYSTEM"):
    s = getattr(prompts, name)
    print("=" * 100); print(f"{name}  ({len(s)} characters, about {len(s)//4} tokens)"); print("=" * 100)
    print(s if name != "SCREEN_SYSTEM" else s[:2500] + "\\n... [catalogue continues] ...\\n" + s[-1600:])
""")

code("""
from engine.agent import Agent
print(inspect.getsource(Agent.handle))
""")

code("""
from engine.rules import floor_signals
print(inspect.getsource(floor_signals)[:4500], "\\n...")
from engine.verify import quote_supported
print(inspect.getsource(quote_supported))
""")

md("""
### 4.3 A live registration, traced turn by turn (real model)

The adversarial credit brief from section 2, played by the deterministic team simulator (`eval/simulator.py`): it answers only the questions asked, from the hidden fact sheet, and says "not done" for controls the team does not have. Every model call is logged with tokens, cost and latency. This is the **representative run** used for the token and cost figures in section 7.
""")

code("""
from engine.agent import new_state
from engine.llm import Usage
from eval.simulator import TeamSimulator
TRACE_FILE = Path("results/trace_H1-A.json")
if TRACE_FILE.exists() and not os.environ.get("RERUN_TRACE"):
    trace = json.loads(TRACE_FILE.read_text())
else:
    usage = Usage(); agent = Agent(usage=usage); sim = TeamSimulator(c); st = new_state(); trace = {"turns": []}
    msg = sim.opening()
    for _ in range(10):
        out = agent.handle(st, msg); st = out["state"]
        trace["turns"].append({"team": msg, "event": out["event"], "extracted": out.get("extracted"), "dropped": out.get("dropped"),
                               "floor": out.get("floor_tier"), "reply": out["reply"], "asked": [q["id"] for q in st.get("last_asked", [])] if out["event"] == "ask" else []})
        if out["event"] != "ask": break
        msg = sim.answer(st["last_asked"])
    reg = agent.finalize(st, inventory=seed)
    trace.update({"registration": reg, "calls": usage.calls, "summary": usage.summary()})
    TRACE_FILE.write_text(json.dumps(trace, indent=1, default=str))
for i, t in enumerate(trace["turns"], 1):
    print(f"\\n--- TEAM MESSAGE {i} ---\\n" + textwrap.shorten(t["team"], 400))
    print(f"extracted: {t['extracted']}\\ndropped by quote check: {[d['id'] for d in t['dropped'] or []]}\\nrule floor now: {t['floor']}")
    print(f"--- ASSISTANT ({t['event']}) ---\\n" + t["reply"][:1500])
a = trace["registration"]["assessment"]
print("\\n=== RESULT ===\\nBank tier:", a["bank_tier"], "| EU tier:", a["eu_tier"], "| model proposed:", a["model_proposed_tier"])
print("risk score", a["risk"]["score"], "vs appetite", a["risk"]["threshold"], "| route:", a["approval_route"])
for s in a["signals"]: print(f"  {s['ref']:<18} {s['tier']:<10} {s['source']:<32} \\"{s['evidence'][:90]}\\"")
print("review flags:", *a["review_flags"], sep="\\n  ")
print("affected:", [p["category"] for p in a["affected_parties"]])
print("open items:", len(a["open_items"]))
""")

code("""
calls = pd.DataFrame(trace["calls"])
display(calls)
s = trace["summary"]
print(f"Representative registration: {s['calls']} model calls, {s['prompt_tokens']:,} input + {s['completion_tokens']:,} output tokens "
      f"({s['reasoning_tokens']:,} of them reasoning) = {s['total_tokens']:,} tokens, cost ${s['cost_usd']:.5f}, model time {s['latency_s']}s")
""")

code("""
from engine.cards import card_markdown
md_text = card_markdown(trace["registration"])
print(md_text[:6000])
""")

md("""
## 5. How I got here: version 1, development iterations and failures

### 5.1 Version 1: one prompt, model only

The first version was the obvious one: give the model the brief and ask for the EU AI Act tier (`BASELINE_SYSTEM` above). No questions, no rules, no quote checks. I ran it on the same cases as the final system.
""")

code("""
def load_summary(tag):
    p = Path(f"results/{tag}_summary.json")
    return json.loads(p.read_text()) if p.exists() else None
b_dev, b_hold = load_summary("baseline_dev"), load_summary("baseline_holdout")
if b_dev:
    display(pd.DataFrame({"v1 baseline, dev": b_dev, "v1 baseline, held-out": b_hold}).loc[
        ["n", "tier_agreement_pct", "tier_kappa", "under_tiering_rate_pct", "under_tiering_high_prohibited", "adversarial_under_tiered", "tokens_mean", "cost_total_usd"]])
    print("Under-tiered by v1 (dev):", *b_dev["under_tiered_cases"], sep="\\n  ")
else:
    print("Run: python -m eval.run_eval --baseline")
""")

md(NOTES.get("baseline", """
*Findings from the baseline are written here after the run.*
"""))

md("""
### 5.2 Development iterations on the rules and the gap logic

Before spending model tokens I tested the deterministic parts (rules, gap selection, quote checks, the simulator and the metrics) with an **oracle** in place of the model: it extracts facts perfectly from the hidden fact sheet and does no screening (`eval/oracle.py`). This isolates the rules from the model. The log below is what I recorded at each iteration; the code for each step is in the git history.
""")

code("""
log = json.loads(Path("results/dev_log.json").read_text())
display(pd.DataFrame([{"iter": e["iteration"], "set": e["set"], "change": e["change"], "tier agreement %": e["metrics"].get("tier_agreement_pct"),
                       "redundant q %": e["metrics"].get("redundant_question_rate_pct"), "under-tiered": ", ".join(e["metrics"].get("under_tiered", [])),
                       "over-tiered": ", ".join(e["metrics"].get("over_tiered", []))} for e in log]))
for e in log: print(f"\\n{e['iteration']}: {e['finding']}")
import subprocess
print("\\n" + subprocess.run(["git", "log", "--oneline", "--reverse"], capture_output=True, text=True).stdout)
""")

md("""
**Failure 1 (found, fixed): short answers were thrown away.** The anti-fabrication quote check rejected answers like "No." because a two-letter quote cannot be verified. Those fields were then asked again, which is the redundant-question failure the Phase 1 metric exists to catch. Fix: a short quote is accepted only when it answers the question just asked about that same field, and it must still appear in the message.

**Failure 2 (found, fixed): the Bank's "acts on customers without review" rule fired on chatbots.** A FAQ chatbot that answers "on its own" was tiered high. Acting *on* a customer (block, decline, restrict) is different from talking to one, which is an Art. 50 transparency matter. Fix: the rule needs a decision domain or explicit action wording.

**Failure 3 (found, fixed): "personal financial data" looked like "personal financing".** A savings chatbot and a voice bot were tiered as credit scoring. Fix: tightened the pattern.

**Failure 4 (found, NOT fixed, reported): the rules overfit.** After those fixes the rules scored 100% on the development cases, which proves nothing because I tuned them on those cases. On the 14 held-out cases written after the freeze, the same rules scored 71%. Keyword rules cannot tell "detects *manipulated* video" from "uses *manipulative* techniques", or "people *recruited* as mules" from recruitment. I left this unfixed on purpose: fixing it now would contaminate the held-out set. The model's screening step is the intended second line for cases the rules miss (it can raise a tier), but it cannot undo a rule that over-fires, because the conversation must never lower a floor. That trade-off is set in Phase 1 (over-tiering only delays a project; under-tiering harms customers).
""")

md("""
## 6. Evaluation: the Phase 1 metrics against the built system

Each case is run end to end through the real system (guard, extraction, gap logic, questions, simulated team answers, screening, tiering, scoring, cards). Nothing in the loop knows the gold labels. The metrics and targets are the ones fixed in Phase 1 rows 7 and 7a.

**What was run, and why not everything.** The project runs on Groq's free tier, which caps each model at 8,000 tokens a minute and a daily token allowance. One full registration costs about 19,500 tokens, so the free allowance covers only a handful of full registrations per model per day, and some of it must stay free for the hosted demo. I therefore ran:

| Run | Cases | What it measures |
|---|---|---|
| Rules only (oracle extraction, no model) | all 63 dev + 14 held-out | the deterministic tiering, gap logic and question budget at full scale |
| v1 baseline, gpt-oss-20b | all 77 | one-prompt, model-only tiering (section 5.1) |
| Full system, **gpt-oss-120b** (the deployed model) | 6, chosen in advance: 4 understated (adversarial) briefs incl. 1 held-out, 1 held-out seeded, 1 complete | under-tiering on the hardest cases, end-to-end metrics |
| Full system, gpt-oss-20b | 6 other cases, chosen in advance: 3 adversarial, 1 dev seeded, 2 held-out seeded | the same, on a second model with its own free allowance |

The subsets were chosen before running, weighted towards the cases Phase 1 says matter most (understated briefs for under-tiering). Twelve full registrations is a small sample: a single case moves a percentage by 8 to 17 points, so the full-system numbers are indicative, not conclusive. The complete run is one command (`python -m eval.run_eval --all`) and costs about US$0.50 on Groq's paid tier.
""")

code("""
from eval.harness import score
RUN = bool(os.environ.get("RUN_EVAL"))  # set RUN_EVAL=1 to re-run instead of loading cached results
if RUN:
    import subprocess; subprocess.run([sys.executable, "-m", "eval.run_eval", "--all"], check=True)
S = {t: load_summary(t) for t in ("system_120b", "system_20b", "oracle_gold", "oracle_holdout")}
targets = [
    ("Tier agreement (Bank tier) %", "tier_agreement_pct", ">= 90"),
    ("Cohen's kappa (Bank tier)", "tier_kappa", "report"),
    ("EU reference tier agreement %", "eu_tier_agreement_pct", "report"),
    ("Under-tiering, gold high/prohibited", "under_tiering_high_prohibited", "0"),
    ("Under-tiering, adversarial briefs", "adversarial_under_tiered", "0"),
    ("Over-tiering rate %", "over_tiering_rate_pct", "report"),
    ("Gap detection recall %", "gap_detection_recall_pct", ">= 95"),
    ("Redundant-question rate %", "redundant_question_rate_pct", "<= 5"),
    ("Affected-party recall %", "affected_party_recall_pct", ">= 90"),
    ("Affected-party precision %", "affected_party_precision_pct", "report"),
    ("Card faithfulness %", "card_faithfulness_pct", "100"),
    ("Card fabrication (count)", "card_fabrications", "0"),
    ("Turns to completion (median)", "turns_median", "<= 10"),
    ("Facts dropped by quote check", "facts_dropped_by_quote_check", "report"),
    ("Model calls per registration", "llm_calls_per_registration_mean", "report"),
    ("Tokens per registration", "tokens_per_registration_mean", "report"),
    ("Cost per registration (USD)", "cost_per_registration_usd_mean", "report"),
]
def cell(s, k): return None if not s else s.get(k)
tbl = pd.DataFrame([{"metric": n, "Phase 1 target": t, "full system, gpt-oss-120b (6 cases)": cell(S["system_120b"], k), "full system, gpt-oss-20b (6 cases)": cell(S["system_20b"], k),
                     "rules only (oracle), dev (63)": cell(S["oracle_gold"], k), "rules only (oracle), held-out (14)": cell(S["oracle_holdout"], k)} for n, k, t in targets])
display(tbl)
""")

code("""
TIERS = ["minimal", "limited", "high", "prohibited"]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, tag, title in ((axes[0], "oracle_gold", "Rules only, development (63)"), (axes[1], "oracle_holdout", "Rules only, held-out (14)")):
    s = S[tag]
    if not s: ax.set_axis_off(); continue
    m = [[s["confusion"][g][p] for p in TIERS] for g in TIERS]
    ax.imshow(m, cmap="Blues")
    for i in range(4):
        for j in range(4):
            ax.text(j, i, m[i][j], ha="center", va="center", color="white" if m[i][j] > max(map(max, m)) / 2 else "black")
    ax.set_xticks(range(4), TIERS); ax.set_yticks(range(4), TIERS); ax.set_xlabel("system Bank tier"); ax.set_ylabel("gold tier"); ax.set_title(title)
plt.suptitle("Tier confusion matrices (below the diagonal = under-tiering, the dangerous direction)"); plt.tight_layout(); plt.show()
""")

code("""
def per_variant(tag):
    p = Path(f"results/{tag}_results.json")
    if not p.exists(): return None
    rs = [r for r in json.loads(p.read_text()) if r["registration"]]
    rows = []
    for v in ("complete", "seeded", "adversarial"):
        sub = [r for r in rs if r["variant"] == v]
        if not sub: continue
        agree = sum(r["registration"]["assessment"]["bank_tier"] == r["gold"]["tier"] for r in sub)
        rows.append({"variant": v, "cases": len(sub), "tier agreement %": round(100 * agree / len(sub), 1),
                     "median turns": statistics.median(r["team_messages"] for r in sub)})
    return pd.DataFrame(rows)
sub = []
for tag, model in (("system_120b", "gpt-oss-120b"), ("system_20b", "gpt-oss-20b")):
    p = Path(f"results/{tag}_results.json")
    if not p.exists(): continue
    for r in json.loads(p.read_text()):
        a = r["registration"]["assessment"] if r["registration"] else {}
        b = base.get(r["case_id"], {}) if b_all else {}
        sub.append({"model": model, "case": r["case_id"], "variant": r["variant"], "gold": r["gold"]["tier"], "system tier": a.get("bank_tier"),
                    "v1 baseline tier (20b)": b.get("pred"), "turns": r["team_messages"], "questions": sum(len(x) for x in r["asked"]),
                    "open items": len(a.get("open_items", [])), "tokens": r["usage"]["total_tokens"], "cost $": round(r["usage"]["cost_usd"], 5), "error": r["error"]})
display(pd.DataFrame(sub))
for tag in ("system_120b", "system_20b"):
    s = S[tag]
    if s:
        print(f"\\n{tag}: under-tiered: {s['under_tiered_cases']}\\n{tag}: over-tiered: {s['over_tiered_cases']}")
        print(f"{tag}: fabrication detail: {s['fabrication_detail']}")
        print(f"{tag}: errors: {s['errors']}")
""")

md("""
### 6.1 Faithfulness of the AI-drafted summary (model-as-judge)

The cards themselves are assembled in code from quoted facts, so card faithfulness is checked deterministically above (every team-sourced statement must have a quote found in the team's words). The one free-text part the model writes is the 2-3 sentence system summary at the top of the system card. Here a separate model call judges, for every summary, whether each claim is supported by the verified facts. A judge model can itself be wrong, so this is a screen, not proof.
""")

code("""
JUDGE = '''You check an AI-drafted summary against the facts it was written from. List every claim in the summary that is NOT supported by the facts (added capabilities, tests, controls, numbers, people). Return JSON only: {"unsupported":["..."],"supported_claims":n}'''
from engine.llm import chat_json, Usage
judge_file = Path("results/judge_summaries.json")
judged = json.loads(judge_file.read_text()) if judge_file.exists() else {}
sys_results = [r for t in ("system_120b", "system_20b") if Path(f"results/{t}_results.json").exists() for r in json.loads(Path(f"results/{t}_results.json").read_text())]
if sys_results and os.environ.get("GROQ_API_KEY"):
    ju = Usage()
    for r in sys_results:
        if not r["registration"] or r["case_id"] in judged: continue
        summ = r["registration"]["assessment"].get("system_summary") or ""
        facts = {k: v["value"] for k, v in r["registration"]["fields"].items()}
        if not summ: judged[r["case_id"]] = {"unsupported": [], "supported_claims": 0, "empty": True}; continue
        try:
            judged[r["case_id"]] = chat_json(JUDGE, f"FACTS:\\n{json.dumps(facts)}\\n\\nSUMMARY:\\n{summ}", step="judge", usage=ju, reasoning_effort="medium", max_tokens=1500)
        except Exception as e:
            judged[r["case_id"]] = {"error": str(e)}
    judge_file.write_text(json.dumps(judged, indent=1))
ok = {k: v for k, v in judged.items() if "unsupported" in v and not v.get("empty")}
bad = {k: v["unsupported"] for k, v in ok.items() if v["unsupported"]}
print(f"Summaries judged: {len(ok)}; with at least one unsupported claim: {len(bad)} ({round(100*len(bad)/max(1,len(ok)),1)}%)")
for k, v in list(bad.items())[:10]: print(" ", k, v)
""")

md(NOTES.get("evaluation", """
*Findings from the evaluation are written here after the run.*
"""))

md("""
### 6.2 Personal-data guard
""")

code("""
rows = []
for t in pii_cases:
    hit = pii.scan(t["text"])
    rows.append({"expected": "block" if t["block"] else "allow", "got": "block" if hit else "allow", "note": t["note"], "found": ", ".join(h["type"] for h in hit)})
g = pd.DataFrame(rows); display(g)
tp = ((g.expected == "block") & (g.got == "block")).sum(); fn = ((g.expected == "block") & (g.got == "allow")).sum(); fp = ((g.expected == "allow") & (g.got == "block")).sum()
print(f"Guard recall {tp}/{tp+fn}, false blocks {fp}/{(g.expected=='allow').sum()}  (on 24 hand-written test messages; real leakage patterns will be more varied)")
""")

md("""
## 7. Tokens and cost
""")

code("""
rows = []
for tag in ("system_120b", "system_20b"):
    p = Path(f"results/{tag}_results.json")
    if not p.exists(): continue
    for r in json.loads(p.read_text()):
        for cl in r.get("usage_calls", []): rows.append({"set": tag, **cl})
calls_df = pd.DataFrame(rows)
if len(calls_df):
    by = calls_df.groupby(["model", "step"]).agg(calls=("step", "size"), mean_in=("prompt_tokens", "mean"), mean_out=("completion_tokens", "mean"),
                                      mean_reasoning=("reasoning_tokens", "mean"), mean_latency_s=("latency_s", "mean"), total_cost_usd=("cost_usd", "sum")).round(1)
    display(by)
    s = S["system_120b"]
    per = s["cost_per_registration_usd_mean"]
    print(f"Mean per registration: {s['llm_calls_per_registration_mean']} calls, {s['tokens_per_registration_mean']:,} tokens, ${per:.5f}")
    print(f"All system runs in this notebook: ${calls_df.cost_usd.sum():.4f} for {len(calls_df)} calls, {int(calls_df.prompt_tokens.sum() + calls_df.completion_tokens.sum()):,} tokens")
    print(f"Projection: 40 registrations a year (upper end of the Phase 1 estimate) = ${40*per:.2f} of model cost a year; "
          f"even at 20x the tokens it is under ${40*per*20:.2f}. Model cost is not the constraint; reviewer time is.")
""")

md(NOTES.get("honesty", """
## 8. Honesty section
*Written after the evaluation run.*
"""))

md("""
## 9. The hosted application

Built against the same `engine` package used in this notebook. Without installing anything or holding a key the marker can: paste or load a synthetic brief, answer follow-ups, see the tier, affected parties, model card, system card and framework gap map, download them, switch role to approve or reject in the inventory, and change the risk appetite in the admin console.
""")

code("""
import httpx
APP_URL = os.environ.get("APP_URL") or json.loads(Path("notebooks/meta.json").read_text()).get("app_url") if Path("notebooks/meta.json").exists() else None
if APP_URL:
    try:
        h = httpx.get(APP_URL.rstrip("/") + "/api/health", timeout=20).json(); print("health:", h)
        inv = httpx.get(APP_URL.rstrip("/") + "/api/inventory", timeout=20).json(); print("inventory records:", len(inv["items"]))
    except Exception as e:
        print("Could not reach the hosted app from this environment:", e)
else:
    print("APP_URL not set")
""")

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}
out = ROOT / "notebooks" / "DATA722_Phase2_UseCaseC.ipynb"
nbf.write(nb, out)
print("wrote", out, len(cells), "cells")
