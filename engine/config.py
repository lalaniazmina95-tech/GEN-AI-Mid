"""Administrator configuration: the risk appetite and the tiering rules.

The Head of AI Risk Governance (administrator) sets these in the admin console,
in line with the Board-approved risk appetite statement. The chatbot can never
change them, and the conversation can never lower a minimum-tier rule.
"""
import copy
import os

MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

# USD per 1M tokens, Groq on-demand list prices used for cost reporting.
# Check https://groq.com/pricing before quoting; override with env vars.
PRICES = {
    "openai/gpt-oss-120b": {"input": float(os.environ.get("PRICE_IN_120B", 0.15)), "output": float(os.environ.get("PRICE_OUT_120B", 0.60))},
    "openai/gpt-oss-20b": {"input": float(os.environ.get("PRICE_IN_20B", 0.075)), "output": float(os.environ.get("PRICE_OUT_20B", 0.30))},
}

TIER_RANK = {"minimal": 1, "limited": 2, "high": 3, "prohibited": 4}
RANK_TIER = {v: k for k, v in TIER_RANK.items()}

DEFAULT_CONFIG = {
    "version": 1,
    "risk_appetite": {
        "threshold": 60,
        "description": "Composite inherent-risk score (0-100) above which a use case is outside appetite and goes to the AI governance committee, whatever its tier.",
    },
    "weights": {"impact": 0.30, "autonomy": 0.20, "data": 0.15, "scale": 0.10, "vulnerability": 0.10, "control_gaps": 0.15},
    "min_tier_rules": {
        "credit_individuals": {"enabled": True, "tier": "high", "label": "Makes or shapes a credit or financing decision about an individual (EU AI Act Annex III 5(b))"},
        "life_health_insurance": {"enabled": True, "tier": "high", "label": "Risk assessment or pricing of individuals for life or health insurance or takaful (Annex III 5(c))"},
        "employment_decisions": {"enabled": True, "tier": "high", "label": "Recruitment, selection, promotion, termination, task allocation or monitoring of staff (Annex III 4)"},
        "biometric_identification": {"enabled": True, "tier": "high", "label": "Biometric identification (1:N), categorisation or emotion recognition (Annex III 1)"},
        "acts_on_customers_without_review": {"enabled": True, "tier": "high", "label": "Acts on customers (blocks, declines, restricts, closes) without human review - Bank rule"},
        "customer_facing_ai": {"enabled": True, "tier": "limited", "label": "Customers or the public interact with it, or receive content it generates (Art. 50)"},
    },
    "allow_art6_3_derogation": False,
    "bank_prohibited_uses": [
        "Fully automated closure or freezing of customer accounts with no human review or appeal",
        "Inferring customers' religion, sect, ethnicity or political views",
        "Scoring customers on their social media activity or personal relationships",
    ],
    "mandatory_controls": {
        "prohibited": [],
        "high": ["human_oversight", "contestability", "bias_fairness_testing", "data_quality_bias_checks", "explainability",
                 "performance_metrics", "robustness_security", "monitoring_plan", "incident_process", "logging",
                 "transparency_notice", "impact_assessment"],
        "limited": ["transparency_notice", "performance_metrics", "monitoring_plan", "incident_process"],
        "minimal": ["performance_metrics", "monitoring_plan"],
    },
    "committee_tiers": ["high", "prohibited"],
    "max_followup_rounds": 6,
    "questions_per_round": 5,
}


def default_config() -> dict:
    return copy.deepcopy(DEFAULT_CONFIG)


def merge_config(stored: dict | None) -> dict:
    """Overlay a stored (possibly partial or older) config on the defaults."""
    cfg = default_config()
    if not stored:
        return cfg
    for k, v in stored.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            for k2, v2 in v.items():
                if isinstance(v2, dict) and isinstance(cfg[k].get(k2), dict):
                    cfg[k][k2].update(v2)
                else:
                    cfg[k][k2] = v2
        else:
            cfg[k] = v
    return cfg
