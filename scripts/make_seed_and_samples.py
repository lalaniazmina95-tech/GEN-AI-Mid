"""Build the seeded (fictional) AI inventory and the UI sample briefs.

Seed records are assembled from archetype fact sheets with the hard rules only
(no model call) and gold affected parties, then given plausible review
statuses. They are labelled "seeded synthetic record" in the UI.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from engine.agent import Agent, new_state  # noqa: E402
from engine.cards import card_markdown  # noqa: E402
from engine.kb.schema import FIELD_BY_ID  # noqa: E402
from engine.prompts import AFFECTED_TAXONOMY  # noqa: E402
from eval.oracle import ENUM_FROM_GOLD  # noqa: E402

CASES = {c["id"]: c for c in json.loads((ROOT / "data/synthetic/gold_cases.json").read_text())}
SEED = [("M3-C", "approved", "2026-05-12"), ("M5-C", "approved", "2026-05-20"), ("L1-C", "approved", "2026-06-03"),
        ("H10-C", "approved", "2026-06-18"), ("H5-C", "approved", "2026-07-02"), ("M10-C", "approved", "2026-07-15"),
        ("L3-C", "pending_approval", "2026-09-28"), ("H13-C", "pending_committee", "2026-10-06"), ("P5-C", "rejected", "2026-08-21"),
        ("M9-C", "approved", "2026-08-30")]
SAMPLES = [("H1-A", "Credit unit 'helper tool' (understated framing)"), ("L1-C", "WhatsApp FAQ assistant (complete brief)"),
           ("M1-S", "Developer coding assistant (brief with gaps)"), ("P1-A", "Contact-centre 'wellbeing' tool (understated framing)"),
           ("H10-S", "Card fraud auto-block (brief with gaps)"), ("M9-C", "SME company credit score (edge case)"),
           ("L3-S", "Marketing content generator (brief with gaps)"), ("H5-A", "CV 'sorting assistant' (understated framing)")]


def build_seed(cid, status, date):
    c = CASES[cid]
    g = c["gold"]
    st = new_state()
    st["id"] = "REG-SEED-" + cid.replace("-", "")
    text = []
    for fid, fact in c["facts"].items():
        if not fact:
            continue
        f = FIELD_BY_ID[fid]
        val = g["flags"][ENUM_FROM_GOLD[fid]] if fid in ENUM_FROM_GOLD else fact
        if fid == "system_name":
            m = re.search(r"(?:called|call it|name is)\s+(\S.*?)\.?$", fact) or re.search(r"It is\s+(\S.*?)\.?$", fact)
            val = m.group(1) if m else fact
        rec = {"value": val, "quote": fact, "turn": 1, "source": "team"}
        if f["kind"] == "control":
            rec["status"] = "done"
        st["fields"][fid] = rec
        text.append(fact)
    st["turns"].append({"role": "user", "text": " ".join(text)})

    def llm(system, user, step, effort, max_tokens):
        return {"affected_parties": [{"category": a, "description": AFFECTED_TAXONOMY[a], "how_affected": "Recorded at registration.", "harm_if_wrong": "", "severity": "medium"} for a in g["affected"]],
                "system_summary": c["facts"]["intended_purpose"], "proposed_tier": g["tier"], "rationale": g["rationale"]}

    reg = Agent(llm=llm).finalize(st, [])
    reg["status"] = status
    reg["submitted"] = reg["created"] = date + "T09:00:00Z"
    reg["seeded"] = True
    reg["history"] = [] if status.startswith("pending") else [{"decision": status, "reviewer": "AI governance committee" if reg["assessment"]["committee_required"] else "AI governance office", "note": "Seeded synthetic record"}]
    reg["markdown"] = card_markdown(reg)
    return reg


def main():
    seed = [build_seed(*s) for s in SEED]
    (ROOT / "data/synthetic/seed_inventory.json").write_text(json.dumps(seed, indent=1, ensure_ascii=False))
    samples = [{"id": cid, "label": label, "brief": CASES[cid]["brief"]} for cid, label in SAMPLES]
    (ROOT / "public/samples.json").write_text(json.dumps(samples, indent=1, ensure_ascii=False))
    print(len(seed), "seed records;", len(samples), "samples")
    for r in seed:
        print(r["id"], r["system_name"], r["assessment"]["bank_tier"], r["assessment"]["risk"]["score"], r["status"])


if __name__ == "__main__":
    main()
