"""Oracle stand-in for the language model (NOT the real system).

Used for two things:
  1. Plumbing tests without network access (CI, offline development).
  2. An ablation: "rules with perfect extraction and no model screening" shows
     how much of the tiering the deterministic rules carry on their own.

Extraction is perfect by construction: any fact sentence from the hidden fact
sheet that appears in the team's message is extracted with the gold enum value
and the sentence itself as the quote. Screening returns nothing, so tiers come
from the hard rules only and affected parties from the domain defaults only.
"""
from engine.kb.schema import FIELD_BY_ID

ENUM_FROM_GOLD = {"domain": "domain", "sourcing": "sourcing", "autonomy_level": "autonomy", "biometric_use": "biometric",
                  "personal_data": "personal_data", "affects_individuals": "affects", "genai_use": "genai", "interacts_with_people": "interacts"}


def make_oracle_llm(case: dict):
    facts = case["facts"]
    gflags = case["gold"]["flags"]

    def llm(system, user, step, effort, max_tokens):
        if step == "extract":
            msg = user.split('NEW MESSAGE from the team:\n"""\n', 1)[-1].rsplit('\n"""', 1)[0]
            out = []
            for fid, fact in facts.items():
                if fact and fact in msg:
                    f = FIELD_BY_ID[fid]
                    val = gflags[ENUM_FROM_GOLD[fid]] if fid in ENUM_FROM_GOLD else fact
                    item = {"id": fid, "value": val, "quote": fact}
                    if f["kind"] == "control":
                        item["status"] = "done"
                    out.append(item)
            return {"fields": out, "unknown": []}
        if step == "ask":
            return {}
        if step == "screen":
            return {"prohibited": [], "annex_iii": [], "bank_prohibited": [], "flags": {}, "affected_parties": [],
                    "system_summary": "", "proposed_tier": ""}
        return {}

    return llm
