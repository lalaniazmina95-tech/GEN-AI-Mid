"""Registration schema = the question bank.

Each field is one thing the AI governance office must know before it can tier
and document a use case. Every field is traced to the clauses that require it
in the EU AI Act, NIST AI RMF 1.0 and the AIGP body of knowledge. The chatbot
asks only about fields that are (a) required for this use case, given what is
already known, and (b) not yet answered.

required_when values (evaluated in engine/gaps.py):
  always                 every registration
  affects_individuals    outputs concern identifiable natural persons
  decisions_about_people outputs make or shape a decision about a person
  vendor                 bought, licensed or API-based (third party involved)
  personal_data          personal data is processed
  genai                  system generates content (text, image, audio, code)
  interacts              people interact with it directly (chat, voice)
  high_candidate         rule floor is high risk or prohibited
  biometric              biometric data is processed
"""

DOMAINS = {
    "credit": "Credit and financing decisions (lending, limits, credit scoring)",
    "insurance_life_health": "Life or health insurance (risk assessment or pricing)",
    "insurance_other": "Other insurance (property, motor, takaful general)",
    "employment": "Employment and HR (recruitment, performance, promotion, termination, monitoring)",
    "fraud_aml": "Fraud detection, AML or sanctions screening",
    "onboarding_kyc": "Customer onboarding, KYC and identity verification",
    "customer_service": "Customer service and communications",
    "marketing": "Marketing, sales and personalisation",
    "collections": "Collections and recovery",
    "internal_productivity": "Internal productivity (search, drafting, coding, summarising)",
    "it_security": "IT operations and cybersecurity",
    "finance_treasury": "Finance, treasury, ALM and forecasting",
    "risk_compliance": "Risk management, compliance and audit",
    "other": "Other",
}

SOURCING = {"in_house": "Built in-house", "vendor": "Vendor product or SaaS with embedded AI",
            "open_source": "Built on an open-source / open-weight model", "gpai_api": "Built on a third-party general-purpose model API"}
AUTONOMY = {"recommends": "Recommends; a human decides", "acts_with_approval": "Acts after human approval",
            "acts_alone": "Acts without human review"}
BIOMETRIC = {"none": "No biometric data", "verification": "1:1 biometric verification (confirming a claimed identity)",
             "identification": "1:N biometric identification", "categorisation": "Biometric categorisation",
             "emotion_recognition": "Emotion recognition"}
PERSONAL_DATA = {"none": "No personal data", "staff_internal": "Staff or internal data only",
                 "personal": "Customer or other personal data", "financial": "Personal financial data",
                 "special_or_biometric": "Special-category or biometric data"}

S = "Ownership and sourcing"
P = "Purpose and context"
H = "Autonomy and human oversight"
D = "Data"
M = "Model and technology"
T = "Testing and performance"
O = "Operations and governance"

FIELDS = [
    # ---- Ownership and sourcing -----------------------------------------
    dict(id="system_name", label="System name", section=S, kind="context", type="text", priority=1, required_when="always",
         question="What is the system called (or a working name)?",
         refs={"eu": ["Art. 49 / Annex VIII"], "nist": ["GOVERN 1.6"], "aigp": ["I.C"]},
         cards=["model:details", "system:overview"]),
    dict(id="business_owner", label="Accountable business owner", section=S, kind="context", type="text", priority=1, required_when="always",
         question="Which role owns the business outcome of this system and is asked when it goes wrong?",
         refs={"eu": ["Art. 26(2)"], "nist": ["GOVERN 2.1", "GOVERN 2.3"], "aigp": ["I.B"]},
         cards=["system:overview"]),
    dict(id="sourcing", label="Sourcing (build / buy / model API)", section=S, kind="context", type="enum", options=SOURCING, priority=1, required_when="always",
         question="Is it built in-house, bought from a vendor, built on an open-weight model, or built on a third-party model API?",
         refs={"eu": ["Art. 3(3)", "Art. 3(4)", "Art. 25"], "nist": ["GOVERN 6.1", "MAP 4.1"], "aigp": ["IV.A"]},
         cards=["model:details", "system:components"]),
    dict(id="vendor_name", label="Vendor / model provider", section=S, kind="context", type="text", priority=2, required_when="vendor",
         question="Who is the vendor or model provider, and which product or model is it?",
         refs={"eu": ["Art. 13(3)(a)", "Art. 25"], "nist": ["GOVERN 6.1", "MANAGE 3.1"], "aigp": ["IV.B"]},
         cards=["model:details", "system:components"]),
    dict(id="lifecycle_stage", label="Lifecycle stage", section=S, kind="context", type="text", priority=3, required_when="always",
         question="What stage is it at: idea, development, pilot, or in production?",
         refs={"eu": ["Art. 9(2)"], "nist": ["MAP 1.4", "GOVERN 1.6"], "aigp": ["I.A", "III.C"]},
         cards=["model:details", "system:overview"]),
    # ---- Purpose and context --------------------------------------------
    dict(id="intended_purpose", label="Intended purpose", section=P, kind="context", type="text", priority=1, required_when="always",
         question="In one or two sentences, what does the system do and what business problem does it solve?",
         refs={"eu": ["Art. 3(12)", "Art. 13(3)(b)(i)"], "nist": ["MAP 1.1", "MAP 1.4"], "aigp": ["III.A"]},
         cards=["model:intended_use", "system:overview"]),
    dict(id="decision_influenced", label="Decision or output it influences", section=P, kind="context", type="text", priority=1, required_when="always",
         question="What decision or action does the output feed into, who takes it, and about whom (for example, a financing approval about an applicant)?",
         refs={"eu": ["Art. 6(3)", "Art. 86"], "nist": ["MAP 1.1", "MAP 2.2", "MAP 3.3"], "aigp": ["IV.A"]},
         cards=["model:intended_use", "system:oversight"]),
    dict(id="domain", label="Business domain", section=P, kind="context", type="enum", options=DOMAINS, priority=1, required_when="always",
         question="Which business area is it used in (credit, HR, fraud/AML, onboarding, customer service, marketing, internal productivity, and so on)?",
         refs={"eu": ["Art. 6(2)", "Annex III"], "nist": ["MAP 1.1", "MAP 2.1"], "aigp": ["II.C"]},
         cards=["model:intended_use", "system:overview"]),
    dict(id="out_of_scope_uses", label="Out-of-scope and foreseeable misuse", section=P, kind="context", type="text", priority=3, required_when="affects_individuals",
         question="What should the system NOT be used for, and how could it foreseeably be misused?",
         refs={"eu": ["Art. 3(13)", "Art. 9(2)(b)", "Art. 13(3)(b)(iii)"], "nist": ["MAP 1.1", "MAP 3.3"], "aigp": ["III.A"]},
         cards=["model:intended_use"]),
    dict(id="users", label="Operators / users", section=P, kind="context", type="text", priority=2, required_when="always",
         question="Who operates or uses the system day to day, and what training do they get?",
         refs={"eu": ["Art. 4", "Art. 26(2)"], "nist": ["MAP 3.4", "GOVERN 2.2"], "aigp": ["I.B", "IV.C"]},
         cards=["model:intended_use", "system:users"]),
    dict(id="affected_persons", label="People affected by the output", section=P, kind="context", type="text", priority=1, required_when="always",
         question="Who is affected by the system's outputs (customers, applicants, employees, counterparties, the public), even if they never use it?",
         refs={"eu": ["Art. 27(1)(c)", "Art. 9(9)"], "nist": ["MAP 1.1", "MAP 5.1"], "aigp": ["III.A", "IV.A"]},
         cards=["model:factors", "system:users"]),
    dict(id="affects_individuals", label="Outputs concern individual people", section=P, kind="context", type="bool", priority=1, required_when="always",
         question="Do the outputs concern specific, identifiable individuals (for example a score or flag on a person)?",
         refs={"eu": ["Art. 6(3) (profiling)", "Art. 86"], "nist": ["MAP 5.1"], "aigp": ["II.A"]},
         cards=["model:factors"]),
    dict(id="scale", label="Scale", section=P, kind="context", type="text", priority=2, required_when="affects_individuals",
         question="Roughly how many people or decisions does it touch per month?",
         refs={"eu": ["Art. 27(1)(b)"], "nist": ["MAP 5.1"], "aigp": ["IV.A"]},
         cards=["system:users"]),
    dict(id="vulnerable_groups", label="Vulnerable groups", section=P, kind="context", type="text", priority=2, required_when="affects_individuals",
         question="Could the affected people include vulnerable groups (elderly, minors, people with low literacy or in financial distress, people with disabilities)? How is that handled?",
         refs={"eu": ["Art. 5(1)(b)", "Art. 9(9)", "Art. 27(1)(d)"], "nist": ["MAP 5.1", "MEASURE 2.11"], "aigp": ["III.A"]},
         cards=["model:factors", "model:ethics"]),
    dict(id="eu_nexus", label="EU nexus", section=P, kind="context", type="text", priority=3, required_when="affects_individuals",
         question="Will any output be used in the EU or concern people in the EU?",
         refs={"eu": ["Art. 2(1)(c)"], "nist": ["GOVERN 1.1"], "aigp": ["II.C"]},
         cards=["system:regulatory"]),
    # ---- Autonomy and human oversight -----------------------------------
    dict(id="autonomy_level", label="Autonomy level", section=H, kind="context", type="enum", options=AUTONOMY, priority=1, required_when="always",
         question="Does the system only recommend, act after a human approves, or act on its own without review?",
         refs={"eu": ["Art. 14", "Art. 6(3)"], "nist": ["MAP 3.5", "GOVERN 3.2"], "aigp": ["IV.A"]},
         cards=["system:oversight"]),
    dict(id="human_oversight", label="Human oversight and override", section=H, kind="control", type="text", priority=1, required_when="decisions_about_people",
         question="Who reviews the output before it takes effect, can they override or stop it, and how often do they actually change it?",
         refs={"eu": ["Art. 14(4)", "Art. 26(2)"], "nist": ["MAP 3.5", "GOVERN 3.2", "MANAGE 2.4"], "aigp": ["IV.C"]},
         cards=["system:oversight", "model:ethics"]),
    dict(id="contestability", label="Explanation and appeal for affected people", section=H, kind="control", type="text", priority=2, required_when="decisions_about_people",
         question="Can an affected person get an explanation of a decision and appeal or contest it? How?",
         refs={"eu": ["Art. 86", "Art. 26(11)"], "nist": ["MEASURE 3.3", "MANAGE 4.1", "GOVERN 5.1"], "aigp": ["II.A", "IV.C"]},
         cards=["system:oversight", "model:ethics"]),
    # ---- Data -----------------------------------------------------------
    dict(id="data_categories", label="Data used (inputs)", section=D, kind="context", type="text", priority=1, required_when="always",
         question="What data does the system use as input (describe categories, do not paste data)?",
         refs={"eu": ["Art. 10", "Art. 13(3)(b)(vi)"], "nist": ["MAP 2.3", "MEASURE 2.10"], "aigp": ["III.B"]},
         cards=["model:training_data", "system:data"]),
    dict(id="personal_data", label="Personal data sensitivity", section=D, kind="context", type="enum", options=PERSONAL_DATA, priority=1, required_when="always",
         question="Does it process personal data? If so, which kind: staff data, customer personal data, personal financial data, or special-category or biometric data?",
         refs={"eu": ["Art. 10(5)", "Art. 26(9)"], "nist": ["MEASURE 2.10"], "aigp": ["II.A"]},
         cards=["system:data"]),
    dict(id="biometric_use", label="Biometric processing", section=D, kind="context", type="enum", options=BIOMETRIC, priority=1, required_when="always",
         question="Does it use biometric data (face, voice, fingerprint)? If yes, is it 1:1 verification, 1:N identification, categorisation, or emotion recognition?",
         refs={"eu": ["Art. 5(1)(e)-(h)", "Annex III 1", "Art. 50(3)"], "nist": ["MEASURE 2.10", "MEASURE 2.11"], "aigp": ["II.C"]},
         cards=["system:data"]),
    dict(id="training_data_source", label="Training data source and provenance", section=D, kind="control", type="text", priority=2, required_when="always",
         question="Where does the training data come from (internal history, vendor, public data, none because it is a pre-trained model), and do you have the right to use it?",
         refs={"eu": ["Art. 10(2)(a)-(b)", "Art. 53(1)(d)"], "nist": ["MAP 4.1", "MAP 2.3"], "aigp": ["III.B"]},
         cards=["model:training_data"]),
    dict(id="data_quality_bias_checks", label="Data representativeness and bias examination", section=D, kind="control", type="text", priority=2, required_when="decisions_about_people",
         question="Has the training or input data been checked for representativeness, gaps and bias? What was found?",
         refs={"eu": ["Art. 10(2)(f)-(h)", "Art. 10(3)"], "nist": ["MAP 2.3", "MEASURE 2.11"], "aigp": ["III.B"]},
         cards=["model:training_data", "model:quantitative"]),
    dict(id="data_location", label="Where data is processed and stored", section=D, kind="control", type="text", priority=2, required_when="always",
         question="Where is the data processed and stored (Bank data centre, onshore cloud, offshore cloud or vendor), and who can see it?",
         refs={"eu": ["Art. 10", "Art. 26(6)"], "nist": ["GOVERN 6.1", "MEASURE 2.10"], "aigp": ["II.A", "IV.B"]},
         cards=["system:data"]),
    # ---- Model and technology -------------------------------------------
    dict(id="model_type", label="Model type and method", section=M, kind="context", type="text", priority=2, required_when="always",
         question="What kind of model or method is it (rules, gradient boosting, neural network, large language model, vendor black box)?",
         refs={"eu": ["Art. 3(1)", "Annex IV 2(b)"], "nist": ["MAP 2.1"], "aigp": ["I.A", "III.A"]},
         cards=["model:details", "system:components"]),
    dict(id="genai_use", label="Generates content", section=M, kind="context", type="bool", priority=1, required_when="always",
         question="Does it generate content such as text, images, audio, video or code?",
         refs={"eu": ["Art. 50(2)", "Art. 50(4)"], "nist": ["NIST AI 600-1"], "aigp": ["I.A"]},
         cards=["model:details", "system:components"]),
    dict(id="interacts_with_people", label="Interacts directly with people", section=M, kind="context", type="bool", priority=1, required_when="always",
         question="Do people interact with it directly (for example chat or voice), and are they customers or staff?",
         refs={"eu": ["Art. 50(1)"], "nist": ["MAP 3.4"], "aigp": ["IV.C"]},
         cards=["system:transparency"]),
    dict(id="system_integrations", label="Systems it reads from and writes to", section=M, kind="context", type="text", priority=2, required_when="always",
         question="Which systems does it read from and write to, and can it change anything in a production system?",
         refs={"eu": ["Annex IV 1(b)"], "nist": ["MAP 4.2", "MAP 2.1"], "aigp": ["IV.C"]},
         cards=["system:components"]),
    # ---- Testing and performance ----------------------------------------
    dict(id="performance_metrics", label="Performance metrics and results", section=T, kind="control", type="text", priority=1, required_when="always",
         question="How was it tested, on which metric, and what were the results (for example accuracy, recall, false-positive rate)?",
         refs={"eu": ["Art. 15(1)-(3)", "Art. 13(3)(b)(ii)"], "nist": ["MEASURE 2.1", "MEASURE 2.3", "MEASURE 2.5"], "aigp": ["III.B", "IV.B"]},
         cards=["model:metrics", "model:evaluation_data"]),
    dict(id="bias_fairness_testing", label="Fairness and bias testing", section=T, kind="control", type="text", priority=1, required_when="decisions_about_people",
         question="Has it been tested for different outcomes across groups (gender, age, region, disability)? What were the results?",
         refs={"eu": ["Art. 10(2)(f)", "Art. 9(9)"], "nist": ["MEASURE 2.11"], "aigp": ["III.B"]},
         cards=["model:quantitative", "model:ethics"]),
    dict(id="explainability", label="Explainability", section=T, kind="control", type="text", priority=2, required_when="decisions_about_people",
         question="Can the reasons for an individual output be explained to the user and to the affected person (for example reason codes)?",
         refs={"eu": ["Art. 13(1)", "Art. 86"], "nist": ["MEASURE 2.9"], "aigp": ["III.B", "IV.C"]},
         cards=["model:quantitative", "system:transparency"]),
    dict(id="robustness_security", label="Robustness and security testing", section=T, kind="control", type="text", priority=2, required_when="always",
         question="Has it been tested for robustness and security (unusual inputs, adversarial attacks, data poisoning, prompt injection)?",
         refs={"eu": ["Art. 15(4)-(5)"], "nist": ["MEASURE 2.6", "MEASURE 2.7"], "aigp": ["III.B"]},
         cards=["model:caveats", "system:safeguards"]),
    dict(id="genai_safeguards", label="Generative AI safeguards", section=T, kind="control", type="text", priority=1, required_when="genai",
         question="What stops it producing false, harmful or confidential content (grounding, output filters, human review of outputs, red-teaming)?",
         refs={"eu": ["Art. 50(2)", "Art. 15(4)"], "nist": ["NIST AI 600-1", "MEASURE 2.6"], "aigp": ["III.B"]},
         cards=["model:caveats", "system:safeguards"]),
    # ---- Operations and governance --------------------------------------
    dict(id="monitoring_plan", label="Post-deployment monitoring", section=O, kind="control", type="text", priority=1, required_when="always",
         question="How will performance be monitored after go-live (which KPIs, how often, drift checks, who reviews)?",
         refs={"eu": ["Art. 72", "Art. 26(5)"], "nist": ["MEASURE 2.4", "MEASURE 3.1", "MANAGE 4.1"], "aigp": ["III.C", "IV.C"]},
         cards=["model:caveats", "system:operations"]),
    dict(id="incident_process", label="Incident handling and fallback", section=O, kind="control", type="text", priority=2, required_when="always",
         question="What happens if it fails or behaves wrongly: who is told, how is it switched off, and what is the manual fallback?",
         refs={"eu": ["Art. 73", "Art. 26(5)", "Art. 20"], "nist": ["MANAGE 2.3", "MANAGE 2.4", "MANAGE 4.3"], "aigp": ["III.C", "IV.C"]},
         cards=["system:operations"]),
    dict(id="logging", label="Logging and record-keeping", section=O, kind="control", type="text", priority=2, required_when="high_candidate",
         question="Are inputs, outputs and decisions logged, and for how long are logs kept?",
         refs={"eu": ["Art. 12", "Art. 19", "Art. 26(6)"], "nist": ["MEASURE 2.8"], "aigp": ["IV.C"]},
         cards=["system:operations"]),
    dict(id="transparency_notice", label="Notice to affected people", section=O, kind="control", type="text", priority=2, required_when="affects_individuals",
         question="Are affected people told that AI is used in a decision about them or that they are interacting with AI? How?",
         refs={"eu": ["Art. 50(1)", "Art. 26(11)"], "nist": ["MEASURE 2.8", "GOVERN 4.2"], "aigp": ["IV.C"]},
         cards=["system:transparency"]),
    dict(id="third_party_due_diligence", label="Vendor due diligence and contract terms", section=O, kind="control", type="text", priority=2, required_when="vendor",
         question="What due diligence was done on the vendor or model provider, and does the contract cover data use, audit rights, incident notification and exit?",
         refs={"eu": ["Art. 25(4)", "Art. 26(1)"], "nist": ["GOVERN 6.1", "GOVERN 6.2", "MANAGE 3.1", "MANAGE 3.2"], "aigp": ["IV.B"]},
         cards=["system:components"]),
    dict(id="impact_assessment", label="Impact assessment (FRIA / DPIA / AI impact)", section=O, kind="control", type="text", priority=2, required_when="high_candidate",
         question="Has an impact assessment been done (fundamental rights, data protection or AI impact assessment)? What did it conclude?",
         refs={"eu": ["Art. 27", "Art. 26(9)"], "nist": ["MAP 5.1", "GOVERN 4.2"], "aigp": ["III.A", "IV.B"]},
         cards=["model:ethics", "system:regulatory"]),
    dict(id="regulatory_context", label="Other regulatory requirements and approvals", section=O, kind="context", type="text", priority=3, required_when="always",
         question="Which other regulations or approvals apply (for example SBP cloud outsourcing, consumer protection, Shariah review)?",
         refs={"eu": ["Art. 2"], "nist": ["GOVERN 1.1"], "aigp": ["II.B"]},
         cards=["system:regulatory"]),
]

FIELD_BY_ID = {f["id"]: f for f in FIELDS}
CONTROL_FIELDS = [f["id"] for f in FIELDS if f["kind"] == "control"]


def coverage_map() -> dict:
    """Which framework clauses each field gives evidence for (used for the gap map)."""
    out = {"eu": {}, "nist": {}, "aigp": {}}
    for f in FIELDS:
        for fw in out:
            for ref in f["refs"].get(fw, []):
                out[fw].setdefault(ref, []).append(f["id"])
    return out
