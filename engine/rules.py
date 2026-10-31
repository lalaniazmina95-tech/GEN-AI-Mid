"""Deterministic tiering rules and the risk-appetite score.

Two layers decide the tier:
  1. Hard rules (this file): enum facts + keyword detectors over the team's own
     words. They set a MINIMUM tier that the conversation cannot lower. This is
     the Phase 1 control against under-tiering ("hard rules set a minimum tier").
  2. The model's screening (Annex III / Art. 5 codes with verified quotes),
     which can raise the tier above the floor, never lower it.

Two tiers are reported:
  eu_tier    - EU AI Act reference tier (Art. 5, Art. 6 + Annex III, Art. 50)
  bank_tier  - eu_tier raised by the administrator's minimum-tier rules
"""
import re

from .config import RANK_TIER, TIER_RANK

INTERNAL_DOMAINS = {"internal_productivity", "it_security", "finance_treasury", "risk_compliance"}
ACTION_DOMAINS = {"credit", "insurance_life_health", "insurance_other", "employment", "fraud_aml", "onboarding_kyc", "collections"}
DECISION_DOMAINS = {"credit", "insurance_life_health", "insurance_other", "employment", "fraud_aml", "onboarding_kyc", "collections", "marketing"}

R = lambda p: re.compile(p, re.I)  # noqa: E731

KW = {
    "credit": R(r"credit ?scor|creditworth|credit[- ]?worth|loan (?:approv|decision|eligib|applica)|financing (?:approv|decision|eligib|limit|applica|request)|"
                r"credit (?:limit|line|decision|approv|eligib)|underwrit|probability of default|\bPD model|buy now,? pay later|\bBNPL\b|nano[- ]?loan|"
                r"(?:personal|consumer|auto|car|home|house|salary|payroll)[- ](?:loans?|financing)\b|murabaha|ijarah|diminishing musharakah|repayment capacity|"
                r"eligible for (?:a )?(?:loan|financing|credit)|(?:approve|decline|reject)s? (?:the )?(?:loan|financing|credit|application)"),
    "individuals": R(r"\bindividual|\bcustomers?\b|\bapplicants?\b|\bborrowers?\b|\bperson\b|\bpeople\b|salaried|consumers?\b|retail|natural persons?"),
    "companies_only": R(r"\b(?:sme|corporate|compan(?:y|ies)|businesses|firms|enterprises)\b"),
    "life_health_ins": R(r"(?:life|health|medical|family)[- ](?:insurance|takaful|cover|policy|policies)"),
    "pricing_or_risk": R(r"pric|premium|contribution rate|underwrit|risk (?:assess|scor|rating)|eligib"),
    "employment": R(r"recruit|\bcv\b|\bcvs\b|r[ée]sum[ée]|candidates?\b|shortlist|hiring|job applica|interview scor|promotion|terminat|dismiss|"
                    r"performance (?:rating|score|evaluation|appraisal|review)s? (?:of|for) (?:staff|employees|agents|officers)|"
                    r"(?:employee|staff|agent|workforce) (?:monitoring|productivity|performance|attrition)|attrition risk|task allocation|"
                    r"rate[sd]? (?:staff|employees|agents)|evaluate[sd]? (?:staff|employees|agents)"),
    "biometric_ident": R(r"(?:face|facial|voice|fingerprint|biometric|iris)[- ]?(?:recognition|identif|match(?:es|ing)? against|search)|watch ?list.*(?:face|facial)|"
                         r"(?:face|facial).*watch ?list|1:n\b|one[- ]to[- ]many"),
    "biometric_verif": R(r"liveness|selfie (?:match|compar)|1:1\b|one[- ]to[- ]one|confirm (?:that )?(?:the )?(?:person|customer|applicant) is who|verify (?:the )?(?:customer'?s? )?identity"),
    "emotion": R(r"emotion|facial expression|(?:voice|vocal|tone)[- ](?:stress|mood|sentiment|emotion)|stress (?:level|detection)|mood (?:detect|analys|scor)|"
                 r"frustrat\w* (?:in|from) (?:their|the) (?:voice|face)|wellbeing (?:score|scoring) from (?:voice|face|camera|video)"),
    "biometric_data": R(r"\bface|\bfacial|\bvoice|\bvocal|camera|video|webcam|\btone\b|biometric|selfie|fingerprint"),
    "emotion_of_staff": R(r"(?:agents?|employees?|staff|workers?|tellers?|officers?)'?s?\W+(?:\w+\W+){0,3}(?:voice|tone|emotion|stress|mood|facial|frustration|fatigue)|"
                          r"(?:voice|tone|emotion|stress|mood|frustration|fatigue|wellbeing)\W+(?:\w+\W+){0,4}(?:of|from|in) (?:our |the |each )?(?:call[- ]cent(?:re|er) )?(?:agents|employees|staff|workers|tellers)"),
    "sensitive_attr": R(r"religio|sect\b|ethnic|race\b|racial|caste|political|trade union|sexual orientation|sex life"),
    "categorise": R(r"infer|deduce|predict|classif|categori|estimate|detect"),
    "social_scoring": R(r"social (?:media|behaviou?r|score|network|graph|connections)|online behaviou?r|lifestyle|personal relationships|friends'?|"
                        r"(?:trustworthiness|citizen|engagement) score"),
    "detrimental": R(r"deny|denied|restrict|unfavou?rable|refus|declin|limit (?:access|services)|higher (?:price|rate|fee)|exclude|downgrad|block"),
    "manipulation": R(r"subliminal|dark pattern|manipulat|deceptive|fake (?:urgency|scarcity|countdown)|exploit (?:cognitive|behaviou?ral) bias|"
                      r"without (?:them|customers) (?:noticing|realis|knowing)"),
    "vulnerable_target": R(r"(?:financially )?distress|desperate|elderly|older customers|low[- ]literacy|vulnerab|gambl|in debt|over[- ]indebted|widow|pensioners?"),
    "push_sales": R(r"upsell|cross[- ]sell|push\w*|maximi[sz]e (?:uptake|conversion|sales|take[- ]up)|nudg\w*|target\w* (?:them|these|offers)|aggressive"),
    "scrape_faces": R(r"scrap\w*.*(?:face|facial|image|photo|picture)|(?:face|facial|image|photo|picture).*scrap|(?:collect|harvest)\w* (?:facial )?(?:images|photos|pictures) from (?:the )?(?:internet|social media|cctv)"),
    "crime_prediction": R(r"predict\w* (?:who|whether|which).*(?:commit|crime|criminal|offen[cs]e)|likel\w* to commit|criminal (?:propensity|risk) (?:score|profil)"),
    "acts_alone": R(r"automatically (?:block|declin|reject|freez|clos|restrict|suspend|approv|disburs|decreas|reduc|lower)|"
                    r"(?:block|declin|reject|freez|clos|restrict|suspend|approv|disburs|decreas|reduc)\w* (?:\w+ ){0,2}automatically|"
                    r"auto[- ](?:block|declin|reject|approv|disburs)|straight[- ]through (?:approv|process)|"
                    r"(?:block|declin|reject|restrict|approv|decreas)\w* (?:\w+ ){0,4}without (?:any )?(?:human|manual) review"),
    "fraud": R(r"fraud|scam|mule|anti[- ]money|\baml\b|sanction|suspicious transaction|chargeback"),
    "customer_facing": R(r"customers? (?:can )?(?:chat|talk|speak|interact|ask|message|use (?:it|the)|type)|chatbot for customers|(?:whatsapp|web ?chat|in[- ]app chat|voice ?bot|ivr|virtual assistant)|"
                         r"members of the public|public[- ]facing|customer[- ]facing|website visitors"),
    "external_content": R(r"(?:sent|send|emailed|published|posted|shown|delivered) to (?:customers|the public|clients|prospects)|post\w* (?:public )?(?:replies|content|comments)|publicly|marketing (?:copy|content|emails?|videos?|images?|campaign)|"
                          r"social media posts|deep ?fake|synthetic (?:voice|video|avatar)|ai[- ]generated (?:video|images?|voice|avatar)|digital avatar|campaign (?:images|videos)"),
}


def _has(key: str, text: str) -> bool:
    return bool(KW[key].search(text or ""))


def _quote(key: str, text: str, width: int = 70) -> str:
    m = KW[key].search(text or "")
    if not m:
        return ""
    s, e = max(0, m.start() - width), min(len(text), m.end() + width)
    return ("..." if s else "") + text[s:e].strip() + ("..." if e < len(text) else "")


def _val(fields: dict, fid: str):
    f = fields.get(fid)
    return f.get("value") if isinstance(f, dict) else None


def _truthy(v) -> bool | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("true", "yes", "y", "1"):
        return True
    if s in ("false", "no", "n", "0", "none"):
        return False
    return None


def derive_flags(fields: dict, team_text: str, screen: dict | None = None) -> dict:
    """Facts the tier rules and the gap logic need, from fields + text + screening."""
    sf = (screen or {}).get("flags", {}) or {}
    domain = _val(fields, "domain")
    sourcing = _val(fields, "sourcing")
    autonomy = _val(fields, "autonomy_level")
    bio = _val(fields, "biometric_use")
    affects = _truthy(_val(fields, "affects_individuals"))
    if affects is None and sf.get("natural_persons") is not None:
        affects = bool(sf.get("natural_persons"))
    text = team_text or ""
    return {
        "domain": domain,
        "sourcing": sourcing,
        "autonomy": autonomy,
        "biometric_use": bio,
        "affects_individuals": affects,
        "genai": _truthy(_val(fields, "genai_use")),
        "interacts": _truthy(_val(fields, "interacts_with_people")),
        "vendor": sourcing in ("vendor", "gpai_api", "open_source") if sourcing else None,
        "third_party_contract": sourcing in ("vendor", "gpai_api") if sourcing else None,
        "personal_data": _val(fields, "personal_data"),
        "customer_facing": bool(sf.get("customer_facing")) or _has("customer_facing", text)
        or (bool(_truthy(_val(fields, "interacts_with_people"))) and bool(re.search(
            r"customer|applicant|visitor|public|caller|shopper|commenter|client",
            " ".join(str(_val(fields, k) or "") + " " + str((fields.get(k) or {}).get("quote", "")) for k in ("users", "interacts_with_people")), re.I))
            and not re.search(r"only (?:our )?(?:staff|developers|employees)|^staff", str(_val(fields, "users") or ""), re.I)),
        "external_genai_content": bool(sf.get("external_genai_content")) or (bool(_truthy(_val(fields, "genai_use"))) and _has("external_content", text)),
        "profiling": bool(sf.get("profiling")),
        # "acts on customers": a decision domain acting alone, or explicit block/decline/restrict wording.
        # A chatbot answering on its own is not acting ON a customer (that is Art. 50, not this rule).
        "acts_without_review": bool(sf.get("acts_without_review_on_customers"))
        or (autonomy == "acts_alone" and domain in ACTION_DOMAINS and affects is not False)
        or (_has("acts_alone", text) and domain not in INTERNAL_DOMAINS and affects is not False),
        "workplace_context": bool(sf.get("workplace_context")),
    }


def floor_signals(fields: dict, team_text: str, flags: dict, cfg: dict) -> dict:
    """Hard-rule signals. Returns {'eu': [...], 'bank': [...]} each item has tier, code, ref, label, evidence."""
    text = team_text or ""
    eu, bank = [], []
    rules = cfg["min_tier_rules"]
    domain = flags.get("domain")
    bio = flags.get("biometric_use")
    affects = flags.get("affects_individuals")

    def add(lst, tier, code, ref, label, evidence):
        lst.append({"tier": tier, "code": code, "ref": ref, "label": label, "evidence": evidence[:300]})

    # --- Art. 5 (strong deterministic patterns only) ---
    emotion = bio == "emotion_recognition" or (_has("emotion", text) and _has("biometric_data", text))
    if emotion and (domain == "employment" or flags.get("workplace_context") or _has("emotion_of_staff", text)):
        add(eu, "prohibited", "art5_1_f", "Art. 5(1)(f)", "Emotion recognition in the workplace", _quote("emotion", text) or "biometric_use = emotion_recognition")
    if (bio == "categorisation" or _has("biometric_data", text)) and _has("sensitive_attr", text) and _has("categorise", text) and _has("biometric_data", text):
        add(eu, "prohibited", "art5_1_g", "Art. 5(1)(g)", "Biometric categorisation by sensitive attributes", _quote("sensitive_attr", text))
    if _has("scrape_faces", text):
        add(eu, "prohibited", "art5_1_e", "Art. 5(1)(e)", "Untargeted scraping of facial images", _quote("scrape_faces", text))
    if _has("social_scoring", text) and re.search(r"scor|rating|rank|trust", text, re.I) and _has("detrimental", text) and (affects is not False):
        add(eu, "prohibited", "art5_1_c", "Art. 5(1)(c)", "Social scoring leading to detrimental treatment", _quote("social_scoring", text))
    if _has("manipulation", text):
        add(eu, "prohibited", "art5_1_a", "Art. 5(1)(a)", "Manipulative or deceptive techniques", _quote("manipulation", text))
    if _has("vulnerable_target", text) and _has("push_sales", text) and (domain in ("marketing", "credit", "collections", None) or _has("credit", text)):
        add(eu, "prohibited", "art5_1_b", "Art. 5(1)(b)", "Exploitation of vulnerabilities to push products", _quote("vulnerable_target", text))
    if _has("crime_prediction", text):
        add(eu, "prohibited", "art5_1_d", "Art. 5(1)(d)", "Predicting criminal offences from profiling", _quote("crime_prediction", text))

    # --- Annex III (high) ---
    credit_text = _has("credit", text)
    companies_only = _has("companies_only", text) and not re.search(r"individual|retail|consumer|salaried|sole proprietor|natural person", text, re.I)
    fraud_only = domain == "fraud_aml" or (_has("fraud", text) and not credit_text)
    if (domain == "credit" or credit_text) and not fraud_only and not companies_only and (affects is not False):
        ev = _quote("credit", text) or f"domain = {domain}"
        add(eu, "high", "5b", "Annex III 5(b)", "Creditworthiness or credit scoring of natural persons", ev)
        if rules["credit_individuals"]["enabled"]:
            add(bank, rules["credit_individuals"]["tier"], "credit_individuals", "Bank rule", rules["credit_individuals"]["label"], ev)
    if domain == "insurance_life_health" or (_has("life_health_ins", text) and _has("pricing_or_risk", text)):
        ev = _quote("life_health_ins", text) or f"domain = {domain}"
        add(eu, "high", "5c", "Annex III 5(c)", "Life or health insurance risk assessment or pricing", ev)
        if rules["life_health_insurance"]["enabled"]:
            add(bank, rules["life_health_insurance"]["tier"], "life_health_insurance", "Bank rule", rules["life_health_insurance"]["label"], ev)
    if domain == "employment" or _has("employment", text):
        ev = _quote("employment", text) or f"domain = {domain}"
        # HR systems that only answer questions are not Annex III 4; require decision/evaluation words
        if _has("employment", text):
            add(eu, "high", "4", "Annex III 4", "Employment: recruitment, evaluation, promotion, termination or monitoring", ev)
            if rules["employment_decisions"]["enabled"]:
                add(bank, rules["employment_decisions"]["tier"], "employment_decisions", "Bank rule", rules["employment_decisions"]["label"], ev)
    bio_ident = bio == "identification" or (_has("biometric_ident", text) and not _has("biometric_verif", text))
    if bio_ident:
        ev = _quote("biometric_ident", text) or "biometric_use = identification"
        add(eu, "high", "1a", "Annex III 1(a)", "Remote biometric identification", ev)
    if bio == "emotion_recognition" or (_has("emotion", text) and _has("biometric_data", text)):
        add(eu, "high", "1c", "Annex III 1(c)", "Emotion recognition", _quote("emotion", text) or "biometric_use = emotion_recognition")
    if bio == "categorisation":
        add(eu, "high", "1b", "Annex III 1(b)", "Biometric categorisation", "biometric_use = categorisation")
    if (bio_ident or bio in ("emotion_recognition", "categorisation")) and rules["biometric_identification"]["enabled"]:
        add(bank, rules["biometric_identification"]["tier"], "biometric_identification", "Bank rule", rules["biometric_identification"]["label"], f"biometric_use = {bio or 'detected in text'}")

    # --- Bank rule: acts on customers without review ---
    if flags.get("acts_without_review") and rules["acts_on_customers_without_review"]["enabled"]:
        add(bank, rules["acts_on_customers_without_review"]["tier"], "acts_on_customers_without_review", "Bank rule",
            rules["acts_on_customers_without_review"]["label"], _quote("acts_alone", text) or f"autonomy = {flags.get('autonomy')}")

    # --- Art. 50 (limited) ---
    if flags.get("customer_facing"):
        add(eu, "limited", "art50_1", "Art. 50(1)", "Interacts directly with customers or the public", _quote("customer_facing", text) or "interacts_with_people = true")
    if flags.get("external_genai_content"):
        add(eu, "limited", "art50_2_4", "Art. 50(2)/(4)", "Generated content reaches customers or the public", _quote("external_content", text) or "genai output is external")
    if rules["customer_facing_ai"]["enabled"] and any(s["code"] in ("art50_1", "art50_2_4") for s in eu):
        add(bank, rules["customer_facing_ai"]["tier"], "customer_facing_ai", "Bank rule", rules["customer_facing_ai"]["label"], "customer-facing or external content")
    return {"eu": eu, "bank": bank}


def max_tier(signals: list[dict], default: str = "minimal") -> str:
    r = max([TIER_RANK[s["tier"]] for s in signals] + [TIER_RANK[default]])
    return RANK_TIER[r]


def floor_tier(fields: dict, team_text: str, cfg: dict) -> str:
    """Current hard-rule floor (used during the conversation to decide which questions apply)."""
    flags = derive_flags(fields, team_text)
    sig = floor_signals(fields, team_text, flags, cfg)
    return max_tier(sig["eu"] + sig["bank"])


# ---- Risk appetite score ----------------------------------------------------
def _scale_score(text) -> int:
    if not text:
        return 3
    nums = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", str(text))]
    mult = 1
    s = str(text).lower()
    if re.search(r"\b(?:million|mn|m)\b", s):
        mult = 1_000_000
    elif re.search(r"\b(?:thousand|k)\b", s):
        mult = 1000
    if not nums:
        return 3
    n = max(nums) * mult
    if "year" in s or "annual" in s:
        n /= 12
    if "day" in s or "daily" in s:
        n *= 30
    for lim, sc in ((100, 1), (1000, 2), (10000, 3), (100000, 4)):
        if n < lim:
            return sc
    return 5


def risk_score(fields: dict, flags: dict, tier: str, cfg: dict, required_controls: list[str], answered: set) -> dict:
    domain = flags.get("domain")
    impact_by_domain = {"credit": 5, "insurance_life_health": 5, "employment": 5, "onboarding_kyc": 4, "fraud_aml": 4, "collections": 4,
                        "insurance_other": 3, "customer_service": 3, "marketing": 3, "risk_compliance": 2, "finance_treasury": 3,
                        "internal_productivity": 2, "it_security": 2, "other": 3}
    impact = max(impact_by_domain.get(domain, 3), {"prohibited": 5, "high": 4, "limited": 2, "minimal": 1}[tier])
    autonomy = {"recommends": 2, "acts_with_approval": 3, "acts_alone": 5}.get(flags.get("autonomy"), 4)
    data = {"none": 1, "staff_internal": 2, "personal": 3, "financial": 4, "special_or_biometric": 5}.get(flags.get("personal_data"), 4)
    affects = flags.get("affects_individuals")
    scale = _scale_score(_val(fields, "scale")) if affects else (1 if affects is False else 3)
    vg = _val(fields, "vulnerable_groups")
    if affects is False:
        vuln = 1
    elif vg is None:
        vuln = 3
    else:
        neg = re.match(r"\s*(no|none|not|n/a)\b", str(vg), re.I)
        vuln = 2 if neg else 4
    missing = [c for c in required_controls if c not in answered]
    gaps = 1 + round(4 * (len(missing) / len(required_controls))) if required_controls else 1
    dims = {"impact": impact, "autonomy": autonomy, "data": data, "scale": scale, "vulnerability": vuln, "control_gaps": gaps}
    w = cfg["weights"]
    tot_w = sum(w.values()) or 1
    score = round(sum(w[k] * (dims[k] - 1) / 4 for k in dims) / tot_w * 100)
    thr = cfg["risk_appetite"]["threshold"]
    return {"dimensions": dims, "score": score, "threshold": thr, "within_appetite": score <= thr, "missing_controls": missing}
