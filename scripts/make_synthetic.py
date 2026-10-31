"""Generate all synthetic data from the archetypes.

Outputs (data/synthetic/):
  gold_cases.json       63 registration test cases with briefs, hidden fact
                        sheets, seeded gaps and gold labels
  pii_cases.json        personal-data guard test messages (block / allow)
  seed_inventory.json   existing (fictional) registrations for the inventory page
  gold_cases.csv        flat view for human review of gold labels

Run:  python scripts/make_synthetic.py
"""
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from archetypes import A  # noqa: E402
from archetypes_holdout import H  # noqa: E402
from engine.gaps import required_fields  # noqa: E402
from engine.kb.schema import FIELD_BY_ID, FIELDS  # noqa: E402

OUT = ROOT / "data" / "synthetic"
GENERIC = {
    "eu_nexus": "No, all users and affected people are in Pakistan and no output is used in the EU.",
    "logging": "Inputs and outputs are logged and kept for two years.",
}
NEVER_SEED = {"system_name", "intended_purpose", "business_owner"}
# bare yes/no answers make no sense inside a brief; use self-contained sentences
EXPAND = {
    ("eu_nexus", "No."): "No output is used in the EU and no affected people are in the EU.",
    ("eu_nexus", "No EU customers."): "We have no EU customers and no output is used in the EU.",
    ("genai_use", "No."): "It does not generate any text, image or other content.",
    ("interacts_with_people", "No."): "Nobody interacts with it directly; it runs in the background.",
    ("affects_individuals", "No."): "Its outputs are not about individual people.",
    ("biometric_use", "None."): "It uses no biometric data.",
}


def gold_flags(g):
    f = g["flags"]
    return {"domain": f["domain"], "sourcing": f["sourcing"], "autonomy": f["autonomy"], "biometric_use": f["biometric"],
            "affects_individuals": f["affects"], "genai": f["genai"], "interacts": f["interacts"], "personal_data": f["personal_data"],
            "vendor": f["sourcing"] in ("vendor", "gpai_api", "open_source"), "third_party_contract": f["sourcing"] in ("vendor", "gpai_api")}


def full_facts(a):
    facts = {}
    for f in FIELDS:
        fid = f["id"]
        v = a["facts"].get(fid)
        if v is None and fid in GENERIC and fid not in a.get("absent", []):
            v = GENERIC[fid]
        if fid in a.get("absent", []):
            v = None
        if v is not None:
            v = EXPAND.get((fid, v), v)
        facts[fid] = v
    return facts


def build_brief(intro, facts, fields):
    order = [f["id"] for f in FIELDS]
    sents = [facts[fid] for fid in order if fid in fields and facts.get(fid)]
    return intro + " " + " ".join(sents)


def build(archs):
    cases = []
    for a in archs:
        facts = full_facts(a)
        g = a["gold"]
        flags = gold_flags(g)
        req = required_fields(flags, g["tier"])
        present_req = [fid for fid in req if facts.get(fid)]
        absent_controls = [fid for fid in req if FIELD_BY_ID[fid]["kind"] == "control" and not facts.get(fid)]
        for variant in a["variants"]:
            cid = f"{a['id']}-{variant[0].upper()}"
            rnd = random.Random(cid)
            seeded = []
            if variant == "complete":
                brief_fields = present_req
                brief = build_brief("We would like to register an AI use case.", facts, brief_fields)
            elif variant == "seeded":
                cand = [fid for fid in present_req if fid not in NEVER_SEED]
                k = min(len(cand), rnd.choice([4, 5, 6]))
                seeded = sorted(rnd.sample(cand, k), key=lambda x: [f["id"] for f in FIELDS].index(x))
                brief_fields = [fid for fid in present_req if fid not in seeded]
                brief = build_brief("Registration request for a new AI use case.", facts, brief_fields)
            else:
                brief_fields = a["adversarial_fields"]
                brief = a["adversarial_brief"]
            cases.append({
                "id": cid, "archetype": a["id"], "title": a["title"], "variant": variant, "brief": brief,
                "brief_fields": brief_fields, "seeded_gaps": seeded, "facts": facts,
                "gold": {"tier": g["tier"], "eu_tier": g["eu_tier"], "codes": g["codes"], "affected": g["affected"],
                         "required_fields": req, "absent_controls": absent_controls, "rationale": a["rationale"], "flags": g["flags"]},
            })
    return cases


def main():
    cases = build(A)
    holdout = build(H)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gold_cases.json").write_text(json.dumps(cases, indent=1, ensure_ascii=False))
    (OUT / "holdout_cases.json").write_text(json.dumps(holdout, indent=1, ensure_ascii=False))
    cases_all = cases + holdout
    with open(OUT / "gold_cases.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "title", "variant", "gold_tier", "gold_eu_tier", "codes", "gold_affected", "seeded_gaps", "rationale", "reviewer_2_tier", "reviewer_2_note"])
        for c in cases_all:
            g = c["gold"]
            w.writerow([c["id"], c["title"], c["variant"], g["tier"], g["eu_tier"], ";".join(g["codes"]), ";".join(g["affected"]), ";".join(c["seeded_gaps"]), g["rationale"], "", ""])
    (OUT / "pii_cases.json").write_text(json.dumps(PII_CASES, indent=1))
    from collections import Counter
    print(len(holdout), "holdout cases", Counter(c["gold"]["tier"] for c in holdout))
    print(len(cases), "cases", Counter(c["gold"]["tier"] for c in cases), Counter(c["variant"] for c in cases))
    print(len(PII_CASES), "pii cases")


PII_CASES = [
    # should block
    {"text": "Here is an example applicant: Ali Raza, CNIC 42101-1234567-1, salary 180,000.", "block": True, "note": "CNIC with dashes"},
    {"text": "Test customer 4210112345671 failed the check last week.", "block": True, "note": "CNIC without dashes"},
    {"text": "Disbursement goes to PK36SCBL0000001123456702 for this customer.", "block": True, "note": "IBAN"},
    {"text": "The disputed card was 4111 1111 1111 1111 used at a merchant in Lahore.", "block": True, "note": "Luhn-valid card number"},
    {"text": "Call the customer on 0300-1234567 if the model flags them.", "block": True, "note": "mobile number"},
    {"text": "For example account no. 0123456789012 was blocked by the model.", "block": True, "note": "labelled account number"},
    {"text": "The complainant emailed from sana.k@gmail.com about the decision.", "block": True, "note": "personal e-mail"},
    {"text": "Applicant passport number AB1234567 was rejected by the liveness check.", "block": True, "note": "passport number"},
    {"text": "+92 321 7654321 is the customer's number in the sample.", "block": True, "note": "mobile +92"},
    {"text": "name,cnic,salary,score\nAli,42101-1234567-1,120000,712\nSara,35202-7654321-2,90000,650\nUsman,61101-1111111-1,150000,780\nHina,37405-2222222-2,70000,590\nBilal,42201-3333333-3,200000,810", "block": True, "note": "pasted table"},
    {"text": "id|name|balance|limit|status\n1|A|20000|5000|ok\n2|B|15000|3000|ok\n3|C|99000|10000|late\n4|D|12000|2000|ok\n5|E|56000|7000|ok", "block": True, "note": "pipe table"},
    {"text": "Customer acct # 1234-5678-9012 complained about the chatbot.", "block": True, "note": "acct # label"},
    # should allow
    {"text": "The model uses CNIC, monthly salary and repayment history as inputs.", "block": False, "note": "describes data categories"},
    {"text": "It scores about 12,000 applications a month with a Gini of 0.62.", "block": False, "note": "numbers"},
    {"text": "We tested it on 25 to 40 use cases in 2026 with 95% recall.", "block": False, "note": "percentages and years"},
    {"text": "Version 3.2.1 of the model went live on 2026-03-15.", "block": False, "note": "version and date"},
    {"text": "Financing limits range from PKR 50,000 to PKR 1,500,000.", "block": False, "note": "amounts"},
    {"text": "The vendor support address is support@vendor.example and the SLA is 24 hours.", "block": False, "note": "example domain"},
    {"text": "Logs are kept for 3650 days and reviewed every 30 days.", "block": False, "note": "small numbers"},
    {"text": "It processes around 4,000,000 transactions a month.", "block": False, "note": "large number with commas"},
    {"text": "The model has 1,200,000,000 parameters.", "block": False, "note": "parameter count"},
    {"text": "Our helpline number is printed on the card; customers can call it.", "block": False, "note": "mentions phone without number"},
    {"text": "Account numbers are masked before anything is sent to the model.", "block": False, "note": "mentions account numbers"},
    {"text": "We track the population stability index (PSI 0.08) every month.", "block": False, "note": "metrics"},
]

if __name__ == "__main__":
    main()
