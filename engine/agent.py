"""The registration agent loop.

On each team message:
  1. GUARD    personal-data scan; a hit blocks the message before the model.
  2. EXTRACT  model maps the message to registration fields; every value needs
              a verbatim quote, verified in code (unverified facts are dropped).
  3. GAPS     code works out which fields this use case requires (conditional
              on what is known so far, including the hard-rule tier floor) and
              which are missing.
  4. DECIDE   if required gaps remain and the round budget allows -> ASK the
              top-priority gaps (model words them); otherwise -> READY.
On finalise:
  5. SCREEN   model screens the facts + the team's own words against Art. 5,
              Annex III, Art. 6(3) and the Bank's prohibited uses; proposes
              affected parties and a summary.
  6. TIER     hard rules set the floor; verified model signals can raise it.
  7. SCORE    inherent-risk score vs the administrator's appetite.
  8. CARDS    model card + system card from verified facts; gaps -> open items.
  9. WRITE    draft registration, status pending approval (never auto-approved).
"""
import datetime as dt
import re
import uuid

from . import pii
from .cards import build_cards
from .config import RANK_TIER, TIER_RANK, merge_config
from .gaps import missing_fields, not_provided, reason_for, required_fields
from .kb import eu_ai_act as eu
from .kb.schema import FIELD_BY_ID
from .llm import LLMError, Usage, chat_json
from .prompts import AFFECTED_TAXONOMY, ASK_SYSTEM, EXTRACT_SYSTEM, SCREEN_SYSTEM, ask_user, extract_user, screen_user
from .rules import derive_flags, floor_signals, floor_tier, max_tier, risk_score
from .verify import norm, quote_supported

FINISH_WORDS = re.compile(r"^\s*(finish|done|that'?s all|generate( the)? (assessment|cards)?|assess( now)?|submit)\s*[.!]?\s*$", re.I)
DISCLOSURE = ("Hello. I am an AI assistant (an AI system, not a person) that helps teams register AI use cases for the AI governance office. "
              "Paste your use case brief: what the system does, who uses it, who it affects, what data it uses and how it was tested. "
              "Describe data, do not paste customer records. I will ask follow-up questions only about what is missing, then produce a "
              "draft risk tier assessment, affected parties, a model card and a system card for the governance office to approve.")


def new_state() -> dict:
    return {"id": "REG-" + uuid.uuid4().hex[:8].upper(), "created": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "turns": [{"role": "assistant", "text": DISCLOSURE}], "fields": {}, "unknown": [], "asked_count": {}, "rounds": 0,
            "dropped": [], "blocked": 0, "phase": "intake", "last_asked": [], "usage": []}


def team_text(state: dict) -> str:
    return "\n".join(t["text"] for t in state["turns"] if t["role"] == "user")


class Agent:
    def __init__(self, config: dict | None = None, llm=None, usage: Usage | None = None):
        self.cfg = merge_config(config)
        self.usage = usage or Usage()
        self._llm = llm  # injectable for tests: fn(system, user, step, effort, max_tokens) -> dict

    def llm(self, system, user, step, effort="low", max_tokens=2500):
        if self._llm:
            return self._llm(system, user, step, effort, max_tokens)
        return chat_json(system, user, step=step, usage=self.usage, reasoning_effort=effort, max_tokens=max_tokens)

    # ---- step 2 -----------------------------------------------------------
    def extract(self, state: dict, message: str) -> dict:
        known = {k: v["value"] for k, v in state["fields"].items()}
        out = self.llm(EXTRACT_SYSTEM, extract_user(message, known, state.get("last_asked", [])), "extract", "low", 3000)
        src = message
        just_asked = {q["id"] for q in state.get("last_asked", [])}
        kept, dropped = [], []
        for item in out.get("fields", []) or []:
            fid = item.get("id")
            f = FIELD_BY_ID.get(fid)
            if not f:
                continue
            val = item.get("value")
            quote = (item.get("quote") or "").strip()
            if val in (None, "", "null"):
                continue
            if f["type"] == "enum":
                val = str(val).strip()
                if val not in f["options"]:
                    dropped.append({"id": fid, "value": val, "quote": quote, "reason": "value not in allowed options"})
                    continue
            if f["type"] == "bool":
                if isinstance(val, str):
                    if val.lower() in ("true", "yes"):
                        val = True
                    elif val.lower() in ("false", "no"):
                        val = False
                    else:
                        dropped.append({"id": fid, "value": val, "quote": quote, "reason": "not a boolean"})
                        continue
            short_answer_ok = fid in just_asked and len(norm(quote)) >= 2 and norm(quote) in norm(src)
            if not (quote_supported(quote, src) or short_answer_ok):
                dropped.append({"id": fid, "value": val, "quote": quote, "reason": "quote not found in the team's message"})
                continue
            rec = {"value": val, "quote": quote, "turn": len(state["turns"]) - 1, "source": "team"}
            if f["kind"] == "control":
                st = item.get("status") or "done"
                rec["status"] = st if st in ("done", "planned", "partial", "not_done") else "done"
            state["fields"][fid] = rec
            kept.append(fid)
        for fid in out.get("unknown", []) or []:
            if fid in FIELD_BY_ID and fid not in state["fields"] and fid not in state["unknown"]:
                state["unknown"].append(fid)
        state["dropped"].extend(dropped)
        return {"kept": kept, "dropped": dropped}

    # ---- steps 3-4 ----------------------------------------------------------
    def current_flags(self, state):
        txt = team_text(state)
        flags = derive_flags(state["fields"], txt)
        floor = floor_tier(state["fields"], txt, self.cfg)
        return flags, floor

    def summary_line(self, state):
        f = state["fields"]
        name = f.get("system_name", {}).get("value") or "the system"
        purpose = f.get("intended_purpose", {}).get("value") or "purpose not yet stated"
        return f"{name}: {str(purpose)[:200]}. {len(f)} facts captured."

    def ask(self, state, gaps):
        items = [{"id": g, "question": FIELD_BY_ID[g]["question"], "reason": reason_for(g)} for g in gaps]
        n = len(state["fields"])
        qs, intro = {}, f"Thanks. I have recorded {n} fact{'s' if n != 1 else ''} so far. To complete the registration I need the following."
        if self.cfg.get("llm_question_wording"):
            # optional: model rewords the selected questions (off by default to save tokens on the free tier)
            try:
                out = self.llm(ASK_SYSTEM, ask_user(self.summary_line(state), items), "ask", "low", 1200)
                qs = {q.get("id"): q.get("text") for q in out.get("questions", []) if q.get("id") in gaps and q.get("text")}
                intro = out.get("intro") or intro
            except (LLMError, ValueError, KeyError):
                pass
        asked = [{"id": g, "text": qs.get(g) or f"{FIELD_BY_ID[g]['question']} ({reason_for(g)})"} for g in gaps]
        text = intro + "\n\n" + "\n".join(f"{i + 1}. {q['text']}" for i, q in enumerate(asked))
        text += "\n\nIf you do not know an answer, just say so and I will record it as an open item. Type \"finish\" at any time to generate the assessment with what you have given."
        return text, asked

    def handle(self, state: dict, message: str) -> dict:
        """Process one team message. Returns {'state':..., 'reply':..., 'event':...}."""
        message = (message or "").strip()[:8000]
        if not message:
            return {"state": state, "reply": "Please type a message.", "event": "empty"}
        findings = pii.scan(message)
        if findings:
            state["blocked"] = state.get("blocked", 0) + 1
            kinds = ", ".join(sorted({f["type"] for f in findings}))
            reply = pii.BLOCK_MESSAGE.format(kinds=kinds)
            state["turns"].append({"role": "system", "text": f"[Message blocked by the personal-data guard: {kinds}. Not sent to the model, not stored.]"})
            state["turns"].append({"role": "assistant", "text": reply})
            return {"state": state, "reply": reply, "event": "blocked", "findings": findings}

        if FINISH_WORDS.match(message) and state["fields"]:
            state["turns"].append({"role": "user", "text": message})
            state["phase"] = "ready"
            reply = "Understood. Generating the assessment with what you have provided; anything missing will be listed as an open item."
            state["turns"].append({"role": "assistant", "text": reply})
            return {"state": state, "reply": reply, "event": "ready"}

        state["turns"].append({"role": "user", "text": message})
        ex = self.extract(state, message)
        flags, floor = self.current_flags(state)
        gaps = missing_fields(state, flags, floor)
        if gaps and state["rounds"] < self.cfg["max_followup_rounds"]:
            sel = gaps[: self.cfg["questions_per_round"]]
            reply, asked = self.ask(state, sel)
            for g in sel:
                state["asked_count"][g] = state["asked_count"].get(g, 0) + 1
            state["rounds"] += 1
            state["last_asked"] = asked
            state["phase"] = "questions"
            state["turns"].append({"role": "assistant", "text": reply, "asked": asked})
            event = "ask"
        else:
            state["phase"] = "ready"
            state["last_asked"] = []
            reply = ("Thank you, I have what I need." if not gaps else
                     "Thank you. I have reached the question limit; the remaining gaps will be listed as open items.") + " Generating the draft assessment now."
            state["turns"].append({"role": "assistant", "text": reply})
            event = "ready"
        state["usage"] = self.usage.calls
        return {"state": state, "reply": reply, "event": event, "extracted": ex["kept"], "dropped": ex["dropped"],
                "floor_tier": floor, "progress": progress(state, flags, floor)}

    # ---- steps 5-9 ----------------------------------------------------------
    def screen(self, state):
        facts = {k: v["value"] for k, v in state["fields"].items()}
        try:
            return self.llm(SCREEN_SYSTEM, screen_user(facts, team_text(state), self.cfg["bank_prohibited_uses"]), "screen", "medium", 4000), None
        except LLMError as e:
            return {}, str(e)

    def finalize(self, state: dict, inventory: list | None = None) -> dict:
        cfg = self.cfg
        txt = team_text(state)
        fields = state["fields"]
        screen, screen_err = self.screen(state)
        source_for_quotes = txt + "\n" + "\n".join(str(v["value"]) for v in fields.values())
        flags = derive_flags(fields, txt, screen)
        hard = floor_signals(fields, txt, flags, cfg)
        eu_sig = [dict(s, source="hard rule") for s in hard["eu"]]
        bank_sig = [dict(s, source="hard rule") for s in hard["bank"]]
        review_flags = []
        if screen_err:
            review_flags.append(f"Model screening unavailable ({screen_err}); tier is from hard rules only.")

        derog = (screen.get("derogation") or {}).get("code")
        derog_ok = cfg.get("allow_art6_3_derogation") and derog and not flags.get("profiling")
        annex_name = {a["code"]: a for a in eu.ANNEX_III}
        for s in screen.get("annex_iii", []) or []:
            code = str(s.get("code", "")).strip()
            if code not in annex_name and code not in ("4", "3", "6", "8", "7"):
                continue
            ok = quote_supported(s.get("quote", ""), source_for_quotes)
            a = annex_name.get(code, {"ref": f"Annex III {code}", "text": ""})
            eu_sig.append({"tier": "high", "code": code, "ref": a["ref"], "label": a.get("area", "") + ": " + a["text"][:90],
                           "evidence": s.get("quote", "")[:300], "source": "model screening" + ("" if ok else " (quote not verified)")})
            if not ok:
                review_flags.append(f"Model flagged Annex III {code} with a quote that could not be verified; kept (conservative) for reviewer check.")
        prohibited_name = {p["code"]: p for p in eu.PROHIBITED}
        for s in screen.get("prohibited", []) or []:
            code = str(s.get("code", "")).strip()
            if code not in prohibited_name:
                continue
            ok = quote_supported(s.get("quote", ""), source_for_quotes)
            p = prohibited_name[code]
            eu_sig.append({"tier": "prohibited" if ok else "high", "code": code, "ref": p["ref"], "label": p["name"],
                           "evidence": s.get("quote", "")[:300], "source": "model screening" + ("" if ok else " (quote not verified: raised to high and sent to committee)")})
            if not ok:
                review_flags.append(f"Possible prohibited practice {p['ref']} (unverified quote): committee must review.")
        for s in screen.get("bank_prohibited", []) or []:
            try:
                idx = int(s.get("index"))
                use = cfg["bank_prohibited_uses"][idx]
            except (TypeError, ValueError, IndexError):
                continue
            ok = quote_supported(s.get("quote", ""), source_for_quotes)
            bank_sig.append({"tier": "prohibited" if ok else "high", "code": f"bank_prohibited_{idx}", "ref": "Bank prohibited use", "label": use,
                             "evidence": s.get("quote", "")[:300], "source": "model screening" + ("" if ok else " (quote not verified)")})

        if derog_ok:
            kept = [s for s in eu_sig if not (s["tier"] == "high" and s["code"] in annex_name)]
            if len(kept) != len(eu_sig):
                review_flags.append(f"Art. 6(3) derogation {derog} applied to EU tier (administrator allows derogations); Bank minimum-tier rules still apply.")
            eu_sig = kept

        eu_tier = max_tier(eu_sig)
        bank_tier = max_tier(eu_sig + bank_sig)
        proposed = str(screen.get("proposed_tier", "")).lower().strip()
        if proposed in TIER_RANK and TIER_RANK[proposed] > TIER_RANK[bank_tier]:
            review_flags.append(f"The model proposed '{proposed}' but no verified rule or code supports more than '{bank_tier}'. Reviewer should check.")
        if proposed in TIER_RANK and TIER_RANK[proposed] < TIER_RANK[bank_tier]:
            review_flags.append(f"The model proposed '{proposed}'; hard rules hold the tier at '{bank_tier}' (the conversation cannot lower a rule floor).")

        # required fields given the final tier, controls and score
        floor = bank_tier
        req = required_fields(flags, floor)
        mandatory = list(dict.fromkeys(cfg["mandatory_controls"].get(bank_tier, [])))
        present = {k for k, v in fields.items() if (v.get("status") in (None, "done", "partial"))}
        risk = risk_score(fields, flags, bank_tier, cfg, mandatory, present)
        committee = bank_tier in cfg["committee_tiers"] or not risk["within_appetite"]

        affected = merge_affected(screen.get("affected_parties", []) or [], flags, fields)
        fria = any(s["code"] in ("5b", "5c") for s in eu_sig)
        provider = flags.get("sourcing") in ("in_house", "open_source", "gpai_api")
        obligations = eu.obligations_for(eu_tier, provider=provider, fria=fria,
                                         interacts=bool(flags.get("customer_facing") or flags.get("interacts")),
                                         genai=bool(flags.get("external_genai_content")),
                                         emotion_or_biocat=flags.get("biometric_use") in ("emotion_recognition", "categorisation"))
        open_items = []
        for fid in not_provided(state, flags, floor):
            open_items.append({"field": fid, "label": FIELD_BY_ID[fid]["label"], "why": "required information not provided (" + reason_for(fid) + ")"})
        for fid in mandatory:
            rec = fields.get(fid)
            if rec and rec.get("status") in ("planned", "not_done"):
                open_items.append({"field": fid, "label": FIELD_BY_ID[fid]["label"], "why": f"mandatory control for {eu.TIERS[bank_tier]['label']} is {rec['status'].replace('_', ' ')}"})

        dup = duplicates(state, inventory or [])
        if dup:
            review_flags.append("Possible duplicate of existing inventory entries: " + ", ".join(f"{d['id']} ({d['system_name']})" for d in dup))

        assessment = {
            "eu_tier": eu_tier, "eu_tier_label": eu.TIERS[eu_tier]["label"],
            "bank_tier": bank_tier, "bank_tier_label": eu.TIERS[bank_tier]["label"],
            "model_proposed_tier": proposed or None, "model_rationale": screen.get("rationale"),
            "signals": eu_sig + bank_sig, "flags": flags, "risk": risk,
            "within_appetite": risk["within_appetite"], "committee_required": committee,
            "approval_route": ("AI governance committee" if committee else "AI governance office"),
            "affected_parties": affected, "obligations": [{"ref": o["ref"], "title": o["title"], "text": o["text"]} for o in obligations],
            "mandatory_controls": [{"field": c, "label": FIELD_BY_ID[c]["label"], "status": (fields.get(c) or {}).get("status", "not provided")} for c in mandatory],
            "open_items": open_items, "review_flags": review_flags, "system_summary": screen.get("system_summary", ""),
            "coverage": coverage(fields, req), "required_fields": req, "duplicates": dup,
        }
        assessment["tier_rationale"] = tier_rationale(assessment)
        cards = build_cards(fields, req, assessment)
        reg = {
            "id": state["id"], "created": state["created"], "submitted": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "system_name": (fields.get("system_name") or {}).get("value") or "Unnamed AI use case",
            "team": (fields.get("business_owner") or {}).get("value") or "", "domain": flags.get("domain"),
            "status": "pending_committee" if committee else "pending_approval",
            "assessment": assessment, "cards": cards, "fields": fields,
            "conversation": [t for t in state["turns"] if t["role"] != "system"], "dropped_facts": state.get("dropped", []),
            "usage": self.usage.summary(), "config_version": cfg.get("version"),
        }
        state["phase"] = "assessed"
        state["usage"] = self.usage.calls
        return reg


def merge_affected(model_parties: list, flags: dict, fields: dict) -> list:
    out = {}
    for p in model_parties:
        c = p.get("category")
        if c in AFFECTED_TAXONOMY and c not in out:
            out[c] = {"category": c, "label": AFFECTED_TAXONOMY[c], "description": p.get("description", ""),
                      "how_affected": p.get("how_affected", ""), "harm_if_wrong": p.get("harm_if_wrong", ""),
                      "severity": p.get("severity", "medium"), "source": "model screening"}
    defaults = {"credit": ["credit_applicants", "retail_customers"], "insurance_life_health": ["retail_customers"],
                "employment": ["employees"], "onboarding_kyc": ["prospective_customers"], "collections": ["retail_customers"],
                "customer_service": ["retail_customers"], "marketing": ["retail_customers"], "fraud_aml": ["retail_customers", "transaction_counterparties"]}
    for c in defaults.get(flags.get("domain"), []):
        if c not in out:
            out[c] = {"category": c, "label": AFFECTED_TAXONOMY[c], "description": "Added by domain rule", "how_affected": "Subject of the system's outputs in this domain.",
                      "harm_if_wrong": "", "severity": "medium", "source": "domain rule"}
    if "staff_users" not in out:
        out["staff_users"] = {"category": "staff_users", "label": AFFECTED_TAXONOMY["staff_users"], "description": "Operators of the system",
                              "how_affected": "Rely on its outputs in their work; exposed to automation bias.", "harm_if_wrong": "", "severity": "low", "source": "default"}
    return list(out.values())


def duplicates(state: dict, inventory: list) -> list:
    def toks(s):
        return {w for w in re.findall(r"[a-z]{4,}", (s or "").lower())}
    f = state["fields"]
    mine = toks(str((f.get("system_name") or {}).get("value", "")) + " " + str((f.get("intended_purpose") or {}).get("value", "")))
    out = []
    if not mine:
        return out
    for r in inventory:
        if r.get("id") == state["id"]:
            continue
        theirs = toks(r.get("system_name", "") + " " + str(((r.get("fields") or {}).get("intended_purpose") or {}).get("value", "")))
        if theirs and len(mine & theirs) / len(mine | theirs) >= 0.35:
            out.append({"id": r["id"], "system_name": r.get("system_name")})
    return out[:3]


def coverage(fields: dict, req: list) -> dict:
    """Framework gap map: for each clause referenced by a required field, is there evidence?"""
    res = {}
    for fw in ("eu", "nist", "aigp"):
        clauses = {}
        for fid in req:
            f = FIELD_BY_ID[fid]
            rec = fields.get(fid)
            state = "missing" if not rec else ("declared_absent" if rec.get("status") in ("not_done", "planned") else "evidenced")
            for ref in f["refs"].get(fw, []):
                prev = clauses.get(ref)
                order = {"evidenced": 2, "declared_absent": 1, "missing": 0}
                if prev is None or order[state] < order[prev["state"]]:
                    clauses[ref] = {"state": state, "fields": sorted(set((prev or {}).get("fields", []) + [fid]))}
                else:
                    prev["fields"] = sorted(set(prev["fields"] + [fid]))
        n = len(clauses)
        ev = sum(1 for c in clauses.values() if c["state"] == "evidenced")
        res[fw] = {"clauses": clauses, "evidenced": ev, "total": n, "pct": round(100 * ev / n) if n else 100}
    nist_fn = {}
    for ref, c in res["nist"]["clauses"].items():
        fn = ref.split()[0] if ref.split()[0] in ("GOVERN", "MAP", "MEASURE", "MANAGE") else "GenAI profile"
        d = nist_fn.setdefault(fn, {"evidenced": 0, "total": 0})
        d["total"] += 1
        d["evidenced"] += c["state"] == "evidenced"
    res["nist_functions"] = nist_fn
    return res


def tier_rationale(a: dict) -> str:
    sig = a["signals"]
    top = [s for s in sig if s["tier"] == a["bank_tier"]]
    if not top:
        base = "No prohibited practice, Annex III category, transparency trigger or Bank minimum-tier rule applies, so the use case is minimal risk. AI literacy (Art. 4) and good practice still apply."
    else:
        why = "; ".join(f"{s['ref']} ({s['label']}, {s['source']})" for s in top[:4])
        base = f"Proposed tier {a['bank_tier_label']} because: {why}."
    if a["eu_tier"] != a["bank_tier"]:
        base += f" The EU AI Act reference tier alone would be {a['eu_tier_label']}; the Bank's minimum-tier rules raise it."
    r = a["risk"]
    base += (f" Inherent-risk score {r['score']}/100 against an appetite threshold of {r['threshold']}: "
             + ("within appetite." if r["within_appetite"] else "ABOVE appetite."))
    base += f" Approval route: {a['approval_route']}. This is a draft; it is not official until approved."
    return base


def progress(state: dict, flags: dict, floor: str) -> dict:
    req = required_fields(flags, floor)
    have = [f for f in req if f in state["fields"]]
    by_fw = {}
    for fw in ("eu", "nist", "aigp"):
        refs_total, refs_have = set(), set()
        for fid in req:
            for r in FIELD_BY_ID[fid]["refs"].get(fw, []):
                refs_total.add(r)
                if fid in state["fields"]:
                    refs_have.add(r)
        by_fw[fw] = {"have": len(refs_have), "total": len(refs_total)}
    return {"required": len(req), "answered": len(have), "floor_tier": floor, "floor_tier_label": eu.TIERS[floor]["label"],
            "frameworks": by_fw, "missing": [f for f in req if f not in state["fields"]]}
