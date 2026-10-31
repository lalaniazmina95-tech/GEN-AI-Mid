"""Run the evaluation against the real model (Groq, gpt-oss) and save results.

  python -m eval.run_eval --set dev        # 63 development cases, full system
  python -m eval.run_eval --set holdout    # 14 held-out cases, full system
  python -m eval.run_eval --baseline       # v1: one prompt, model-only tiering
  python -m eval.run_eval --oracle         # ablation: perfect extraction, rules only (no model)
  python -m eval.run_eval --all

Each case is cached in results/raw/<run>/<case>.json so an interrupted run
(rate limits) resumes where it stopped. Needs GROQ_API_KEY.
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import os  # noqa: E402

os.environ.setdefault("GROQ_MAX_WAIT", "65")  # batch runs can wait out per-minute rate limits
os.environ.setdefault("GROQ_ATTEMPTS", "10")
from engine import pii  # noqa: E402
from engine.config import MODEL, TIER_RANK  # noqa: E402
from engine.llm import Usage, chat_json  # noqa: E402
from engine.prompts import BASELINE_SYSTEM  # noqa: E402
from eval.harness import cohen_kappa, run_case, save, score  # noqa: E402
from eval.oracle import make_oracle_llm  # noqa: E402

DATA = ROOT / "data" / "synthetic"
RES = ROOT / "results"


def load(name):
    return json.loads((DATA / f"{name}_cases.json").read_text())


def run_set(name, cases, tag, llm_factory=None, limit=None):
    raw = RES / "raw" / tag
    raw.mkdir(parents=True, exist_ok=True)
    results = []
    for i, c in enumerate(cases[:limit] if limit else cases):
        f = raw / f"{c['id']}.json"
        if f.exists():
            r = json.loads(f.read_text())
            if not r.get("error"):
                results.append(r)
                continue
        t0 = time.time()
        r = run_case(c, llm=llm_factory(c) if llm_factory else None)
        f.write_text(json.dumps(r, default=str))
        results.append(r)
        a = r["registration"]["assessment"] if r["registration"] else {}
        print(f"[{tag}] {i + 1}/{len(cases)} {c['id']:<6} gold={c['gold']['tier']:<10} got={a.get('bank_tier', 'ERR'):<10} "
              f"turns={r['team_messages']} tok={r['usage']['total_tokens']} {time.time() - t0:.1f}s {r['error'] or ''}", flush=True)
    s = score(results)
    save(results, RES / f"{tag}_results.json")
    (RES / f"{tag}_summary.json").write_text(json.dumps(s, indent=1))
    return s


def run_baseline(cases, tag):
    """Version 1 of the system: a single prompt classifies the brief. No questions, no rules."""
    raw = RES / "raw" / tag
    raw.mkdir(parents=True, exist_ok=True)
    out = []
    for c in cases:
        f = raw / f"{c['id']}.json"
        if f.exists():
            out.append(json.loads(f.read_text()))
            continue
        u = Usage()
        try:
            r = chat_json(BASELINE_SYSTEM, c["brief"], step="baseline", usage=u, reasoning_effort="medium", max_tokens=1500)
            tier = str(r.get("tier", "")).lower().strip()
            tier = tier if tier in TIER_RANK else "minimal"
            rec = {"case_id": c["id"], "variant": c["variant"], "gold": c["gold"]["tier"], "gold_eu": c["gold"]["eu_tier"], "pred": tier,
                   "rationale": r.get("rationale", ""), "usage": u.summary()}
        except Exception as e:  # noqa: BLE001
            rec = {"case_id": c["id"], "variant": c["variant"], "gold": c["gold"]["tier"], "gold_eu": c["gold"]["eu_tier"], "pred": None, "error": str(e), "usage": u.summary()}
        f.write_text(json.dumps(rec))
        out.append(rec)
        print(f"[{tag}] {c['id']:<6} gold={rec['gold']:<10} got={rec['pred']}", flush=True)
    ok = [r for r in out if r["pred"]]
    g, p = [r["gold"] for r in ok], [r["pred"] for r in ok]
    ge = [r["gold_eu"] for r in ok]
    under = [r for r in ok if TIER_RANK[r["pred"]] < TIER_RANK[r["gold"]]]
    hp = [r for r in ok if r["gold"] in ("high", "prohibited")]
    adv = [r for r in ok if r["variant"] == "adversarial"]
    s = {"n": len(ok), "tier_agreement_pct": round(100 * sum(a == b for a, b in zip(g, p)) / len(ok), 1), "tier_kappa": round(cohen_kappa(g, p), 3),
         "eu_tier_agreement_pct": round(100 * sum(a == b for a, b in zip(ge, p)) / len(ok), 1),
         "under_tiering_rate_pct": round(100 * len(under) / len(ok), 1),
         "under_tiering_high_prohibited": f"{sum(1 for r in under if r['gold'] in ('high', 'prohibited'))}/{len(hp)}",
         "adversarial_under_tiered": f"{sum(1 for r in adv if TIER_RANK[r['pred']] < TIER_RANK[r['gold']])}/{len(adv)}",
         "under_tiered_cases": [f"{r['case_id']} gold={r['gold']} got={r['pred']}" for r in under],
         "tokens_mean": round(statistics.mean(r["usage"]["total_tokens"] for r in ok)), "cost_total_usd": round(sum(r["usage"]["cost_usd"] for r in ok), 5)}
    (RES / f"{tag}_results.json").write_text(json.dumps(out, indent=1))
    (RES / f"{tag}_summary.json").write_text(json.dumps(s, indent=1))
    return s


def pii_eval():
    cases = json.loads((DATA / "pii_cases.json").read_text())
    tp = sum(1 for c in cases if c["block"] and pii.scan(c["text"]))
    fn = sum(1 for c in cases if c["block"] and not pii.scan(c["text"]))
    fp = sum(1 for c in cases if not c["block"] and pii.scan(c["text"]))
    tn = sum(1 for c in cases if not c["block"] and not pii.scan(c["text"]))
    s = {"n": len(cases), "recall_pct": round(100 * tp / (tp + fn), 1), "precision_pct": round(100 * tp / (tp + fp), 1) if tp + fp else None,
         "false_blocks": fp, "missed": fn, "tp": tp, "tn": tn}
    RES.mkdir(exist_ok=True)
    (RES / "pii_summary.json").write_text(json.dumps(s, indent=1))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["dev", "holdout"])
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--cases", help="comma-separated case ids (subset run)")
    ap.add_argument("--tag", help="results tag for a subset run")
    a = ap.parse_args()
    print("model:", MODEL)
    print("pii:", pii_eval())
    if a.oracle or a.all:
        for name in ("gold", "holdout"):
            print(f"oracle {name}:", json.dumps({k: v for k, v in run_set(name, load(name), f"oracle_{name}", make_oracle_llm).items() if k in ("tier_agreement_pct", "under_tiered_cases", "over_tiered_cases")}))
    if (a.baseline or a.all) and not a.cases:
        print("baseline dev:", run_baseline(load("gold"), "baseline_dev"))
        print("baseline holdout:", run_baseline(load("holdout"), "baseline_holdout"))
    if a.cases:
        ids = a.cases.split(",")
        pool = {c["id"]: c for c in load("gold") + load("holdout")}
        subset = [pool[i] for i in ids]
        if a.baseline:
            print("baseline subset:", run_baseline(subset, a.tag))
        else:
            print("subset:", json.dumps(run_set("subset", subset, a.tag), indent=1))
        return
    if a.set == "dev" or a.all:
        print("system dev:", json.dumps(run_set("gold", load("gold"), "system_dev", limit=a.limit), indent=1))
    if a.set == "holdout" or a.all:
        print("system holdout:", json.dumps(run_set("holdout", load("holdout"), "system_holdout", limit=a.limit), indent=1))


if __name__ == "__main__":
    main()
