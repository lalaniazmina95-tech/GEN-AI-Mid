"""Gap analysis: which required fields are still missing, and what to ask next.

Selection is deterministic (code, not the model) so it is testable: a field is
asked only if it is required for this use case and not yet answered. This is
what keeps the redundant-question rate low.
"""
from .config import TIER_RANK
from .kb.schema import FIELD_BY_ID, FIELDS
from .rules import DECISION_DOMAINS, INTERNAL_DOMAINS


def condition_flags(flags: dict, floor: str) -> dict:
    affects = flags.get("affects_individuals")
    domain = flags.get("domain")
    high = TIER_RANK[floor] >= 3
    return {
        "always": True,
        "affects_individuals": bool(affects),
        "decisions_about_people": bool(affects) and (domain in DECISION_DOMAINS or high) and domain not in INTERNAL_DOMAINS,
        "vendor": bool(flags.get("vendor")),
        "third_party_contract": bool(flags.get("third_party_contract")),
        "personal_data": flags.get("personal_data") not in (None, "none"),
        "genai": bool(flags.get("genai")),
        "interacts": bool(flags.get("interacts")),
        "high_candidate": high,
        "biometric": flags.get("biometric_use") not in (None, "none"),
    }


def _cond(f: dict, cf: dict) -> bool:
    rw = f["required_when"]
    if f["id"] == "third_party_due_diligence":
        return cf["third_party_contract"]
    return cf.get(rw, False)


def required_fields(flags: dict, floor: str) -> list[str]:
    cf = condition_flags(flags, floor)
    return [f["id"] for f in FIELDS if _cond(f, cf)]


FRAMEWORK_NAMES = {"eu": "EU AI Act", "nist": "NIST AI RMF", "aigp": "AIGP"}


def reason_for(fid: str) -> str:
    f = FIELD_BY_ID[fid]
    parts = []
    if f["refs"].get("eu"):
        parts.append("EU AI Act " + ", ".join(f["refs"]["eu"][:2]))
    if f["refs"].get("nist"):
        parts.append("NIST " + ", ".join(f["refs"]["nist"][:2]))
    if f["refs"].get("aigp"):
        parts.append("AIGP " + ", ".join(f["refs"]["aigp"][:1]))
    return "; ".join(parts)


def missing_fields(state: dict, flags: dict, floor: str, max_asks: int = 2) -> list[str]:
    req = required_fields(flags, floor)
    have = state["fields"]
    unknown = set(state.get("unknown", []))
    asked = state.get("asked_count", {})
    out = [fid for fid in req if fid not in have and fid not in unknown and asked.get(fid, 0) < max_asks]
    order = {f["id"]: i for i, f in enumerate(FIELDS)}
    # never-asked first, then priority, then schema order
    out.sort(key=lambda fid: (asked.get(fid, 0), FIELD_BY_ID[fid]["priority"], order[fid]))
    return out


def not_provided(state: dict, flags: dict, floor: str) -> list[str]:
    req = required_fields(flags, floor)
    return [fid for fid in req if fid not in state["fields"]]
