"""Evaluation harness: runs gold cases through the built system and scores them.

Metrics fixed in Phase 1 (rows 7 and 7a, use case C):
  tier_agreement        system Bank tier == gold tier          target >= 90%  (+ Cohen's kappa)
  under_tiering_rate    system tier below gold tier             target 0 for gold high/prohibited
  gap_detection_recall  seeded missing fields that were asked   target >= 95%
  redundant_question    asked about info already in the brief   target <= 5%
  affected_party_recall gold affected categories found          target >= 90%
  card_faithfulness     card statements traceable to the team   target 100%
  card_fabrication      card asserts a control the team never   target 0
                        described (or said was not done)
  turns_to_completion   team messages until assessment          median <= 10
Also reported: EU reference tier agreement, over-tiering, PII guard precision /
recall, tokens, cost and latency per registration.
"""
import json
import statistics
import time
from collections import Counter
from pathlib import Path

from engine.agent import Agent, new_state, team_text
from engine.config import TIER_RANK
from engine.kb.schema import FIELD_BY_ID
from engine.llm import Usage
from engine.verify import quote_supported

from .simulator import TeamSimulator

TIERS = ["minimal", "limited", "high", "prohibited"]


def run_case(case: dict, config: dict | None = None, llm=None, max_turns: int = 12) -> dict:
    usage = Usage()
    agent = Agent(config, llm=llm, usage=usage)
    sim = TeamSimulator(case)
    state = new_state()
    asked_log, events, t0 = [], [], time.time()
    msg = sim.opening()
    team_msgs = 0
    error = None
    try:
        while team_msgs < max_turns:
            team_msgs += 1
            out = agent.handle(state, msg)
            state = out["state"]
            events.append(out["event"])
            if out["event"] == "ask":
                asked = state["last_asked"]
                asked_log.append([q["id"] for q in asked])
                msg = sim.answer(asked)
            else:
                break
        reg = agent.finalize(state, inventory=[])
    except Exception as e:  # noqa: BLE001 - record and continue the batch
        error = f"{type(e).__name__}: {e}"
        reg = None
    return {"case_id": case["id"], "variant": case["variant"], "gold": case["gold"], "brief_fields": case["brief_fields"],
            "seeded_gaps": case["seeded_gaps"], "asked": asked_log, "team_messages": team_msgs, "events": events,
            "registration": reg, "dropped": state.get("dropped", []), "team_text": team_text(state),
            "usage": usage.summary(), "usage_calls": usage.calls, "wall_s": round(time.time() - t0, 1), "error": error}


# ------------------------------- scoring -------------------------------------
def cohen_kappa(a: list, b: list, labels=TIERS) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] * cb[l] for l in labels) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def card_checks(r: dict) -> dict:
    """Faithfulness: every team-sourced card value has a quote found in the team's text.
    Fabrication: a control shown as in place (done/partial) that the gold fact sheet says
    the team never had."""
    reg = r["registration"]
    statements, faithful, fabricated, fab_detail = 0, 0, 0, []
    absent = set(r["gold"]["absent_controls"])
    seen = set()
    for card in ("model_card", "system_card"):
        for sec in reg["cards"][card]:
            for e in sec["entries"]:
                if e.get("source") != "team" or e["field"] in seen:
                    continue
                seen.add(e["field"])
                statements += 1
                if quote_supported(e.get("quote", ""), r["team_text"]):
                    faithful += 1
                if e["field"] in absent and e.get("status") in ("done", "partial"):
                    fabricated += 1
                    fab_detail.append({"field": e["field"], "value": e["value"], "quote": e.get("quote")})
    controls_shown = sum(1 for f in seen if FIELD_BY_ID[f]["kind"] == "control")
    return {"statements": statements, "faithful": faithful, "fabricated": fabricated, "controls_shown": controls_shown, "fabrication_detail": fab_detail}


def score(results: list[dict]) -> dict:
    ok = [r for r in results if r["registration"]]
    gold = [r["gold"]["tier"] for r in ok]
    pred = [r["registration"]["assessment"]["bank_tier"] for r in ok]
    gold_eu = [r["gold"]["eu_tier"] for r in ok]
    pred_eu = [r["registration"]["assessment"]["eu_tier"] for r in ok]
    under = [r for r, g, p in zip(ok, gold, pred) if TIER_RANK[p] < TIER_RANK[g]]
    under_hp = [r for r in under if r["gold"]["tier"] in ("high", "prohibited")]
    hp = [r for r in ok if r["gold"]["tier"] in ("high", "prohibited")]
    over = [r for r, g, p in zip(ok, gold, pred) if TIER_RANK[p] > TIER_RANK[g]]
    adv = [r for r in ok if r["variant"] == "adversarial"]
    adv_under = [r for r in adv if TIER_RANK[r["registration"]["assessment"]["bank_tier"]] < TIER_RANK[r["gold"]["tier"]]]

    seeded_total = seeded_hit = 0
    for r in ok:
        flat = {f for rnd in r["asked"] for f in rnd}
        for g in r["seeded_gaps"]:
            seeded_total += 1
            seeded_hit += g in flat
    q_total = q_redundant = 0
    for r in ok:
        bf = set(r["brief_fields"])
        for rnd in r["asked"]:
            for f in rnd:
                q_total += 1
                q_redundant += f in bf
    aff_total = aff_hit = aff_pred = aff_correct = 0
    for r in ok:
        g = set(r["gold"]["affected"])
        p = {x["category"] for x in r["registration"]["assessment"]["affected_parties"]}
        aff_total += len(g)
        aff_hit += len(g & p)
        aff_pred += len(p)
        aff_correct += len(g & p)
    cc = [card_checks(r) for r in ok]
    st = sum(c["statements"] for c in cc)
    fa = sum(c["faithful"] for c in cc)
    fab = sum(c["fabricated"] for c in cc)
    ctrl = sum(c["controls_shown"] for c in cc)
    turns = [r["team_messages"] for r in ok]
    usage = [r["usage"] for r in ok]
    confusion = {g: {p: 0 for p in TIERS} for g in TIERS}
    for g, p in zip(gold, pred):
        confusion[g][p] += 1
    dropped = sum(len(r["dropped"]) for r in ok)

    def pct(a, b):
        return round(100 * a / b, 1) if b else None

    return {
        "n_cases": len(results), "n_completed": len(ok), "errors": [r["case_id"] + ": " + r["error"] for r in results if r["error"]],
        "tier_agreement_pct": pct(sum(g == p for g, p in zip(gold, pred)), len(ok)),
        "tier_kappa": round(cohen_kappa(gold, pred), 3),
        "eu_tier_agreement_pct": pct(sum(g == p for g, p in zip(gold_eu, pred_eu)), len(ok)),
        "eu_tier_kappa": round(cohen_kappa(gold_eu, pred_eu), 3),
        "under_tiering_rate_pct": pct(len(under), len(ok)),
        "under_tiering_high_prohibited": f"{len(under_hp)}/{len(hp)}",
        "under_tiered_cases": [f"{r['case_id']} gold={r['gold']['tier']} got={r['registration']['assessment']['bank_tier']}" for r in under],
        "adversarial_under_tiered": f"{len(adv_under)}/{len(adv)}",
        "over_tiering_rate_pct": pct(len(over), len(ok)),
        "over_tiered_cases": [f"{r['case_id']} gold={r['gold']['tier']} got={r['registration']['assessment']['bank_tier']}" for r in over],
        "gap_detection_recall_pct": pct(seeded_hit, seeded_total), "seeded_gaps": f"{seeded_hit}/{seeded_total}",
        "redundant_question_rate_pct": pct(q_redundant, q_total), "questions": f"{q_redundant}/{q_total}",
        "affected_party_recall_pct": pct(aff_hit, aff_total), "affected_party_precision_pct": pct(aff_correct, aff_pred),
        "card_faithfulness_pct": pct(fa, st), "card_statements": st,
        "card_fabrication_rate_pct": pct(fab, ctrl), "card_fabrications": fab,
        "fabrication_detail": [dict(case=r["case_id"], **d) for r, c in zip(ok, cc) for d in c["fabrication_detail"]],
        "facts_dropped_by_quote_check": dropped,
        "turns_median": statistics.median(turns) if turns else None, "turns_max": max(turns) if turns else None,
        "confusion": confusion,
        "tokens_per_registration_mean": round(statistics.mean(u["total_tokens"] for u in usage)) if usage else None,
        "cost_per_registration_usd_mean": round(statistics.mean(u["cost_usd"] for u in usage), 5) if usage else None,
        "llm_calls_per_registration_mean": round(statistics.mean(u["calls"] for u in usage), 1) if usage else None,
        "total_tokens": sum(u["total_tokens"] for u in usage), "total_cost_usd": round(sum(u["cost_usd"] for u in usage), 4),
        "latency_s_per_registration_mean": round(statistics.mean(u["latency_s"] for u in usage), 1) if usage else None,
    }


def save(results, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    slim = []
    for r in results:
        s = dict(r)
        if s["registration"]:
            s["registration"] = {k: s["registration"][k] for k in ("id", "assessment", "cards", "fields", "status", "system_name")}
        slim.append(s)
    path.write_text(json.dumps(slim, indent=1, ensure_ascii=False, default=str))
