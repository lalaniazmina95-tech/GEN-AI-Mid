"""IAPP Artificial Intelligence Governance Professional (AIGP) Body of Knowledge.

Structure follows the AIGP Body of Knowledge v2 (four domains). Competencies
and performance indicators are paraphrased summaries written for this tool;
the IAPP's own document should be consulted for the authoritative wording.
"""

SOURCE = "IAPP AIGP Body of Knowledge, version 2 (four domains)"

DOMAINS = {
    "I": {
        "name": "Understanding the foundations of AI governance",
        "competencies": {
            "I.A": ("Understand what AI is and why it needs governance", [
                "Define AI and machine learning; distinguish AI types (narrow vs general, predictive vs generative, rules-based vs learned).",
                "Understand AI harms to individuals, groups, organisations and society, and the characteristics of trustworthy AI.",
                "Understand the AI lifecycle and the socio-technical nature of AI risk.",
            ]),
            "I.B": ("Establish and communicate organisational expectations for AI governance", [
                "Define roles and responsibilities, accountability and a cross-functional governance body.",
                "Establish and deliver AI literacy and training for staff.",
                "Tailor governance to the organisation's size, risk tolerance, sector and use of AI (developer, deployer, user).",
            ]),
            "I.C": ("Establish policies and procedures to apply throughout the AI lifecycle", [
                "Maintain an inventory of AI systems and classify them by risk.",
                "Set policies on acceptable use, oversight, third-party AI, incident management and decommissioning.",
                "Integrate AI governance with privacy, security, risk and procurement processes.",
            ]),
        },
    },
    "II": {
        "name": "Understanding how laws, standards and frameworks apply to AI",
        "competencies": {
            "II.A": ("Understand how existing data privacy laws apply to AI", [
                "Notice, choice, lawful basis and purpose limitation for personal data in training and use.",
                "Data minimisation, data subject rights and automated decision-making rights.",
                "Privacy impact assessments for AI processing.",
            ]),
            "II.B": ("Understand how other types of existing laws apply to AI", [
                "Anti-discrimination and consumer protection (including fair lending) laws.",
                "Intellectual property, product liability and sector regulation (e.g. financial services supervision).",
            ]),
            "II.C": ("Understand the main elements of the EU AI Act", [
                "Risk classification: prohibited, high-risk, transparency, minimal; GPAI obligations.",
                "Provider and deployer obligations, conformity assessment, FRIA, enforcement and penalties.",
            ]),
            "II.D": ("Understand the main industry standards and tools that apply to AI", [
                "NIST AI RMF and its profiles; ISO/IEC 42001 (AI management system), ISO/IEC 23894 (AI risk), ISO/IEC 42005 (impact assessment).",
                "OECD AI Principles and other voluntary frameworks.",
            ]),
        },
    },
    "III": {
        "name": "Understanding how to govern AI development",
        "competencies": {
            "III.A": ("Govern the designing and building of the AI model", [
                "Define the business case, intended purpose and success criteria; consider non-AI alternatives.",
                "Perform an AI impact assessment early; identify affected stakeholders and potential harms.",
                "Select model architecture and document design decisions; apply privacy and security by design.",
            ]),
            "III.B": ("Govern the collection and use of data in training and testing the AI model", [
                "Establish data provenance, lineage, rights to use and quality.",
                "Assess representativeness and bias in training and test data.",
                "Test and validate: accuracy, robustness, fairness, explainability; document in model cards.",
            ]),
            "III.C": ("Govern the release, monitoring and maintenance of the AI model", [
                "Release readiness review and documentation (model and system cards).",
                "Monitoring for drift and performance, incident response, retraining and change management.",
                "Decommissioning procedures.",
            ]),
        },
    },
    "IV": {
        "name": "Understanding how to govern AI deployment and use",
        "competencies": {
            "IV.A": ("Evaluate key factors and risks relevant to the decision to deploy the AI model", [
                "Context of use, autonomy level, affected people and scale.",
                "Build vs buy vs open-source; vendor and proprietary versus open model trade-offs.",
            ]),
            "IV.B": ("Perform key activities to assess the AI model", [
                "Third-party and vendor due diligence, contract terms (data use, audit rights, liability, incident notification).",
                "Pre-deployment testing in the deployment context; impact assessment for the deployer.",
            ]),
            "IV.C": ("Govern the deployment and use of the AI model", [
                "Human oversight, transparency to users and affected people, and channels for appeal or redress.",
                "Ongoing monitoring, logging, incident management, and deactivation where outcomes are inconsistent with intended use.",
            ]),
        },
    },
}


def all_competencies() -> dict[str, str]:
    return {cid: name for d in DOMAINS.values() for cid, (name, _) in d["competencies"].items()}
