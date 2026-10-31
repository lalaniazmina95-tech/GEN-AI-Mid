"""HTTP API (FastAPI) - Vercel Python serverless function.

The browser holds the conversation state and sends it with each message, so the
function is stateless. The Groq key lives only in the server environment.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from engine import store  # noqa: E402
from engine.agent import Agent, new_state  # noqa: E402
from engine.cards import card_markdown  # noqa: E402
from engine.config import MODEL, default_config, merge_config  # noqa: E402
from engine.kb import aigp, eu_ai_act, nist_ai_rmf  # noqa: E402
from engine.kb.schema import FIELDS  # noqa: E402
from engine.llm import LLMError  # noqa: E402

app = FastAPI(title="AI Use Case Registry API")

DECISIONS = {"approve": "approved", "reject": "rejected", "return": "returned_to_team", "committee": "pending_committee"}


class TurnIn(BaseModel):
    state: dict | None = None
    message: str
    config: dict | None = None


class FinalizeIn(BaseModel):
    state: dict
    config: dict | None = None
    inventory: list | None = None


class DecisionIn(BaseModel):
    registration: dict | None = None
    id: str
    decision: str
    reviewer: str = "AI governance office"
    note: str = ""


def _dev_llm(state):
    """DEV ONLY (DEV_MOCK_LLM=1): offline stand-in that recognises a synthetic sample
    brief and answers like the oracle. Never enabled on Vercel."""
    if os.environ.get("DEV_MOCK_LLM") != "1":
        return None
    import json as _json

    from eval.oracle import make_oracle_llm
    txt = " ".join(t["text"] for t in (state or {}).get("turns", []) if t["role"] == "user")
    cases = _json.loads((Path(__file__).resolve().parent.parent / "data/synthetic/gold_cases.json").read_text())
    best = max(cases, key=lambda c: sum(1 for v in c["facts"].values() if v and v in txt) + (5 if c["brief"][:80] in txt else 0))
    return make_oracle_llm(best)


def _config(client_cfg):
    stored = store.get_config()
    return merge_config(stored if stored else client_cfg)


@app.get("/api/health")
def health():
    return {"ok": True, "model": MODEL, "llm_configured": bool(os.environ.get("GROQ_API_KEY")), "persistent_store": store.persistent()}


@app.post("/api/session")
def session():
    return {"state": new_state()}


@app.post("/api/turn")
def turn(body: TurnIn):
    state = body.state or new_state()
    probe = {"turns": state.get("turns", []) + [{"role": "user", "text": body.message}]}
    agent = Agent(_config(body.config), llm=_dev_llm(probe))
    try:
        out = agent.handle(state, body.message)
    except LLMError as e:
        raise HTTPException(503, f"The language model is unavailable right now ({e}). Please retry in a minute.")
    out["usage"] = agent.usage.summary()
    return out


@app.post("/api/finalize")
def finalize(body: FinalizeIn):
    agent = Agent(_config(body.config), llm=_dev_llm(body.state))
    inv = store.list_inventory() if store.persistent() else (body.inventory or store.seed_inventory())
    reg = agent.finalize(body.state, inv)
    reg["markdown"] = card_markdown(reg)
    saved = store.put(reg)
    return {"registration": reg, "saved": saved, "persistent_store": store.persistent()}


@app.get("/api/inventory")
def inventory():
    return {"items": store.list_inventory(), "persistent_store": store.persistent()}


@app.post("/api/decision")
def decision(body: DecisionIn):
    if body.decision not in DECISIONS:
        raise HTTPException(400, "unknown decision")
    reg = store.get(body.id) if store.persistent() else body.registration
    if not reg:
        raise HTTPException(404, "registration not found")
    tier = reg["assessment"]["bank_tier"]
    if body.decision == "approve" and tier == "prohibited":
        raise HTTPException(400, "A prohibited use case cannot be approved. Reject it or return it to the team to redesign.")
    if body.decision == "approve" and reg["assessment"].get("committee_required") and body.reviewer != "AI governance committee":
        raise HTTPException(400, "This registration is high risk or above appetite: only the AI governance committee can approve it.")
    reg["status"] = DECISIONS[body.decision]
    reg.setdefault("history", []).append({"decision": body.decision, "reviewer": body.reviewer, "note": body.note[:500]})
    store.put(reg)
    return {"registration": reg, "persistent_store": store.persistent()}


@app.get("/api/config")
def get_config():
    stored = store.get_config()
    return {"config": merge_config(stored), "defaults": default_config(), "persistent_store": store.persistent()}


@app.put("/api/config")
def put_config(cfg: dict):
    merged = merge_config(cfg)
    thr = merged["risk_appetite"]["threshold"]
    if not (0 <= thr <= 100):
        raise HTTPException(400, "threshold must be 0-100")
    merged["version"] = int(merged.get("version", 1)) + 1
    saved = store.put_config(merged)
    return {"config": merged, "saved": saved, "persistent_store": store.persistent()}


@app.get("/api/frameworks")
def frameworks():
    return {
        "eu_ai_act": {"source": eu_ai_act.SOURCE, "timeline": eu_ai_act.TIMELINE, "prohibited": eu_ai_act.PROHIBITED, "annex_iii": eu_ai_act.ANNEX_III,
                      "art6": eu_ai_act.ART6, "requirements": eu_ai_act.REQUIREMENTS, "tiers": eu_ai_act.TIERS, "definitions": eu_ai_act.DEFINITIONS},
        "nist_ai_rmf": {"source": nist_ai_rmf.SOURCE, "core": {fn: {"purpose": d["purpose"], "categories": {c: {"text": t, "subcategories": s} for c, (t, s) in d["categories"].items()}}
                                                                for fn, d in nist_ai_rmf.CORE.items()},
                        "trustworthy": nist_ai_rmf.TRUSTWORTHY, "genai_risks": nist_ai_rmf.GENAI_RISKS},
        "aigp": {"source": aigp.SOURCE, "domains": {k: {"name": d["name"], "competencies": {c: {"name": n, "indicators": i} for c, (n, i) in d["competencies"].items()}} for k, d in aigp.DOMAINS.items()}},
        "question_bank": FIELDS,
    }


@app.exception_handler(Exception)
def unhandled(_req, exc):
    return JSONResponse(status_code=500, content={"detail": f"Server error: {type(exc).__name__}: {str(exc)[:200]}"})


if os.environ.get("SERVE_STATIC") == "1":  # local development only; Vercel serves public/ itself
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "public"), html=True), name="static")
