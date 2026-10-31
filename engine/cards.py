"""Model card and system card assembly.

Cards are assembled in code from verified fields only. Each entry carries the
team's own quote as provenance. Anything not provided is written as
"Not provided" and becomes an open item: cards never fill a gap with an
assumption (Phase 1, decision 4.3).

Model card sections follow Mitchell et al. (2019), "Model Cards for Model
Reporting". The system card covers the whole deployed system: components,
people, oversight, data flows, transparency, safeguards, operations and the
regulatory position.
"""
from .kb.schema import BIOMETRIC, DOMAINS, FIELDS, PERSONAL_DATA, SOURCING, AUTONOMY

MODEL_SECTIONS = [
    ("details", "Model details"), ("intended_use", "Intended use"), ("factors", "Factors (who and what affects performance)"),
    ("metrics", "Metrics"), ("evaluation_data", "Evaluation data"), ("training_data", "Training data"),
    ("quantitative", "Quantitative analyses (fairness, explainability)"), ("ethics", "Ethical considerations"),
    ("caveats", "Caveats and recommendations"),
]
SYSTEM_SECTIONS = [
    ("overview", "System overview"), ("components", "Components and third parties"), ("users", "Users and affected people"),
    ("oversight", "Autonomy and human oversight"), ("data", "Data and data flows"), ("transparency", "Transparency"),
    ("safeguards", "Safeguards"), ("operations", "Operations: monitoring, incidents, logging"), ("regulatory", "Regulatory position"),
]
NOT_PROVIDED = "Not provided"
STATUS_LABEL = {"done": "In place", "partial": "Partly in place", "planned": "Planned, not yet in place", "not_done": "Team states this is not in place"}


def display_value(fid: str, v):
    maps = {"domain": DOMAINS, "sourcing": SOURCING, "autonomy_level": AUTONOMY, "biometric_use": BIOMETRIC, "personal_data": PERSONAL_DATA}
    if fid in maps and isinstance(v, str):
        return maps[fid].get(v, v)
    if isinstance(v, bool):
        return "Yes" if v else "No"
    return v


def _entry(f: dict, fields: dict, required: set):
    rec = fields.get(f["id"])
    if rec:
        e = {"field": f["id"], "label": f["label"], "value": display_value(f["id"], rec["value"]), "quote": rec.get("quote", ""),
             "source": rec.get("source", "team")}
        if f["kind"] == "control":
            e["status"] = rec.get("status") or "done"
            e["status_label"] = STATUS_LABEL.get(e["status"], e["status"])
        return e
    if f["id"] in required:
        return {"field": f["id"], "label": f["label"], "value": NOT_PROVIDED, "quote": "", "source": "none", "open_item": True}
    return None


def _card(card: str, sections, fields: dict, required: set) -> list[dict]:
    out = []
    for key, title in sections:
        entries = []
        for f in FIELDS:
            if f"{card}:{key}" in f.get("cards", []):
                e = _entry(f, fields, required)
                if e:
                    entries.append(e)
        out.append({"key": key, "title": title, "entries": entries})
    return out


def build_cards(fields: dict, required: list[str], assessment: dict) -> dict:
    req = set(required)
    model = _card("model", MODEL_SECTIONS, fields, req)
    system = _card("system", SYSTEM_SECTIONS, fields, req)
    # generated (not team-sourced) entries are labelled as such
    for s in system:
        if s["key"] == "overview" and assessment.get("system_summary"):
            s["entries"].insert(0, {"field": "_summary", "label": "Summary (AI-drafted from the facts below; check before approval)",
                                    "value": assessment["system_summary"], "quote": "", "source": "model_summary"})
        if s["key"] == "users":
            for p in assessment.get("affected_parties", []):
                s["entries"].append({"field": "_affected", "label": f"Affected: {p['label']}", "value": f"{p.get('how_affected', '')} Harm if wrong: {p.get('harm_if_wrong', '')} (severity {p.get('severity', 'n/a')})".strip(),
                                     "quote": "", "source": p.get("source", "assessment")})
        if s["key"] == "regulatory":
            s["entries"].append({"field": "_tier", "label": "Proposed risk tier (Bank)", "value": assessment["bank_tier_label"], "quote": "", "source": "rules"})
            s["entries"].append({"field": "_eu_tier", "label": "EU AI Act reference tier", "value": assessment["eu_tier_label"], "quote": "", "source": "rules"})
            for ob in assessment.get("obligations", []):
                s["entries"].append({"field": "_obligation", "label": f"Obligation: {ob['ref']} {ob['title']}", "value": ob["text"][:240], "quote": "", "source": "framework"})
    for s in model:
        if s["key"] == "caveats" and assessment.get("open_items"):
            s["entries"].append({"field": "_open", "label": "Open items before approval", "value": "; ".join(o["label"] for o in assessment["open_items"]), "quote": "", "source": "rules"})
    return {"model_card": model, "system_card": system}


def card_markdown(reg: dict) -> str:
    a = reg["assessment"]
    lines = [f"# {reg.get('system_name') or 'AI use case'} - registration {reg['id']}", "",
             f"Status: **{reg['status']}**  |  Bank tier: **{a['bank_tier_label']}**  |  EU AI Act reference tier: **{a['eu_tier_label']}**  |  "
             f"Risk score {a['risk']['score']} vs appetite {a['risk']['threshold']} ({'within' if a['risk']['within_appetite'] else 'ABOVE'} appetite)", ""]
    lines += ["## Risk tier assessment", "", a["tier_rationale"], ""]
    for s in a["signals"]:
        lines.append(f"- **{s['ref']}** {s['label']} -> {s['tier']} (evidence: \"{s['evidence']}\")")
    lines += ["", "## Who will be affected", ""]
    for p in a["affected_parties"]:
        lines.append(f"- **{p['label']}**: {p.get('how_affected', '')} Harm if wrong: {p.get('harm_if_wrong', '')} (severity {p.get('severity', '')})")
    for title, key in (("Model card", "model_card"), ("System card", "system_card")):
        lines += ["", f"## {title}", ""]
        for s in reg["cards"][key]:
            lines.append(f"### {s['title']}")
            for e in s["entries"]:
                st = f" [{e['status_label']}]" if e.get("status_label") else ""
                q = f' - source: "{e["quote"]}"' if e.get("quote") else ""
                lines.append(f"- **{e['label']}**{st}: {e['value']}{q}")
            lines.append("")
    lines += ["## Open items", ""] + [f"- {o['label']} ({o['why']})" for o in a["open_items"]]
    return "\n".join(lines)
