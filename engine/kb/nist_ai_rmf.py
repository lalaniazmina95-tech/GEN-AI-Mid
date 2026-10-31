"""NIST AI Risk Management Framework 1.0 (NIST AI 100-1, January 2023) - core.

All 4 functions, 19 categories and 72 subcategories, plus the seven
trustworthiness characteristics and the 12 risks of the Generative AI Profile
(NIST AI 600-1, July 2024). Subcategory texts are condensed paraphrases of the
published wording, written for this tool.
"""

SOURCE = "NIST AI 100-1, Artificial Intelligence Risk Management Framework (AI RMF 1.0), Jan 2023; NIST AI 600-1, Generative AI Profile, Jul 2024"

TRUSTWORTHY = [
    {"id": "valid_reliable", "name": "Valid and reliable", "text": "Accuracy and robustness confirmed through objective evidence that requirements for the intended use are fulfilled; the necessary condition for the others."},
    {"id": "safe", "name": "Safe", "text": "Does not, under defined conditions, lead to a state in which human life, health, property or the environment is endangered."},
    {"id": "secure_resilient", "name": "Secure and resilient", "text": "Withstands unexpected adverse events or changes, and maintains confidentiality, integrity and availability against attacks."},
    {"id": "accountable_transparent", "name": "Accountable and transparent", "text": "Information about the system and its outputs is available to those interacting with it; accountability presupposes transparency."},
    {"id": "explainable_interpretable", "name": "Explainable and interpretable", "text": "The mechanisms underlying operation (explainability) and the meaning of outputs in context (interpretability) can be understood."},
    {"id": "privacy_enhanced", "name": "Privacy-enhanced", "text": "Norms and practices that safeguard human autonomy, identity and dignity, including limiting intrusion and data minimisation."},
    {"id": "fair", "name": "Fair, with harmful bias managed", "text": "Concerns for equality and equity addressed by managing systemic, computational/statistical and human-cognitive bias."},
]

CORE = {
    "GOVERN": {
        "purpose": "Cultivates a culture of risk management; cross-cutting, informs and is infused through the other three functions.",
        "categories": {
            "GOVERN 1": ("Policies, processes, procedures and practices for mapping, measuring and managing AI risks are in place, transparent and implemented effectively.", {
                "GOVERN 1.1": "Legal and regulatory requirements involving AI are understood, managed and documented.",
                "GOVERN 1.2": "The characteristics of trustworthy AI are integrated into organisational policies, processes, procedures and practices.",
                "GOVERN 1.3": "Processes are in place to determine the needed level of risk management activities based on the organisation's risk tolerance.",
                "GOVERN 1.4": "The risk management process and its outcomes are established through transparent policies, procedures and other controls based on organisational risk priorities.",
                "GOVERN 1.5": "Ongoing monitoring and periodic review of the risk management process and its outcomes are planned, with roles, responsibilities and review frequency defined.",
                "GOVERN 1.6": "Mechanisms are in place to inventory AI systems and are resourced according to organisational risk priorities.",
                "GOVERN 1.7": "Processes are in place for decommissioning and phasing out AI systems safely, without increasing risk or decreasing trustworthiness.",
            }),
            "GOVERN 2": ("Accountability structures ensure appropriate teams and individuals are empowered, responsible and trained.", {
                "GOVERN 2.1": "Roles, responsibilities and lines of communication for mapping, measuring and managing AI risks are documented and clear.",
                "GOVERN 2.2": "Personnel and partners receive AI risk management training consistent with policies and agreements.",
                "GOVERN 2.3": "Executive leadership takes responsibility for decisions about risks associated with AI development and deployment.",
            }),
            "GOVERN 3": ("Workforce diversity, equity, inclusion and accessibility processes are prioritised in AI risk management.", {
                "GOVERN 3.1": "Decision-making on AI risks is informed by a diverse team (demographics, disciplines, experience, expertise, backgrounds).",
                "GOVERN 3.2": "Policies and procedures define and differentiate roles and responsibilities for human-AI configurations and oversight of AI systems.",
            }),
            "GOVERN 4": ("Organisational teams are committed to a culture that considers and communicates AI risk.", {
                "GOVERN 4.1": "Policies foster a critical-thinking and safety-first mindset in design, development, deployment and use.",
                "GOVERN 4.2": "Teams document the risks and potential impacts of the AI technology they design, develop, deploy, evaluate and use, and communicate about impacts.",
                "GOVERN 4.3": "Practices enable AI testing, identification of incidents and information sharing.",
            }),
            "GOVERN 5": ("Processes are in place for robust engagement with relevant AI actors.", {
                "GOVERN 5.1": "Policies collect, consider, prioritise and integrate feedback from those external to the team about individual and societal impacts.",
                "GOVERN 5.2": "Mechanisms let the team regularly incorporate adjudicated feedback from relevant AI actors into design and implementation.",
            }),
            "GOVERN 6": ("Policies and procedures address risks and benefits from third-party software, data and other supply chain issues.", {
                "GOVERN 6.1": "Policies address AI risks associated with third-party entities, including risks of infringement of intellectual property or other rights.",
                "GOVERN 6.2": "Contingency processes handle failures or incidents in third-party data or AI systems deemed high-risk.",
            }),
        },
    },
    "MAP": {
        "purpose": "Establishes the context to frame risks related to an AI system.",
        "categories": {
            "MAP 1": ("Context is established and understood.", {
                "MAP 1.1": "Intended purposes, beneficial uses, context-specific laws, norms and expectations, and prospective deployment settings are understood and documented, including users, positive and negative impacts, assumptions and limitations.",
                "MAP 1.2": "Interdisciplinary AI actors, competencies and capacities for establishing context reflect demographic diversity and domain and user expertise; participation is documented.",
                "MAP 1.3": "The organisation's mission and relevant goals for AI technology are understood and documented.",
                "MAP 1.4": "The business value or context of business use is clearly defined or, for existing systems, re-evaluated.",
                "MAP 1.5": "Organisational risk tolerances are determined and documented.",
                "MAP 1.6": "System requirements are elicited from and understood by relevant AI actors; design decisions take socio-technical implications into account.",
            }),
            "MAP 2": ("Categorisation of the AI system is performed.", {
                "MAP 2.1": "The specific tasks and methods used to implement them are defined (e.g. classifiers, generative models, recommenders).",
                "MAP 2.2": "Information about the system's knowledge limits and how output may be used and overseen by humans is documented.",
                "MAP 2.3": "Scientific integrity and TEVV considerations are identified and documented, including data collection and selection (availability, representativeness, suitability) and construct validation.",
            }),
            "MAP 3": ("Capabilities, targeted usage, goals and expected benefits and costs are understood against benchmarks.", {
                "MAP 3.1": "Potential benefits of intended functionality and performance are examined and documented.",
                "MAP 3.2": "Potential costs, including non-monetary costs from AI errors or trustworthiness failures, are examined and documented against risk tolerance.",
                "MAP 3.3": "Targeted application scope is specified and documented based on capability, context and categorisation.",
                "MAP 3.4": "Processes for operator and practitioner proficiency with system performance and trustworthiness are defined, assessed and documented.",
                "MAP 3.5": "Processes for human oversight are defined, assessed and documented in accordance with GOVERN policies.",
            }),
            "MAP 4": ("Risks and benefits are mapped for all components, including third-party software and data.", {
                "MAP 4.1": "Approaches for mapping technology and legal risks of components, including third-party data or software and IP infringement, are in place and documented.",
                "MAP 4.2": "Internal risk controls for components, including third-party AI technologies, are identified and documented.",
            }),
            "MAP 5": ("Impacts to individuals, groups, communities, organisations and society are characterised.", {
                "MAP 5.1": "Likelihood and magnitude of each identified impact (beneficial and harmful) are identified and documented.",
                "MAP 5.2": "Practices and personnel for regular engagement with relevant AI actors and integrating feedback about impacts are in place and documented.",
            }),
        },
    },
    "MEASURE": {
        "purpose": "Employs quantitative, qualitative or mixed methods to analyse, assess, benchmark and monitor AI risk and impacts.",
        "categories": {
            "MEASURE 1": ("Appropriate methods and metrics are identified and applied.", {
                "MEASURE 1.1": "Approaches and metrics for the most significant mapped risks are selected; risks that will not or cannot be measured are documented.",
                "MEASURE 1.2": "Appropriateness of metrics and effectiveness of existing controls are regularly assessed and updated, including reports of errors and impacts on affected communities.",
                "MEASURE 1.3": "Internal experts who were not front-line developers and/or independent assessors are involved in regular assessments; domain experts, users and affected communities consulted as needed.",
            }),
            "MEASURE 2": ("AI systems are evaluated for trustworthy characteristics.", {
                "MEASURE 2.1": "Test sets, metrics and details about TEVV tools are documented.",
                "MEASURE 2.2": "Evaluations involving human subjects meet applicable requirements and are representative of the relevant population.",
                "MEASURE 2.3": "Performance or assurance criteria are measured and demonstrated for conditions similar to deployment; measures documented.",
                "MEASURE 2.4": "Functionality and behaviour of the system and components are monitored in production.",
                "MEASURE 2.5": "The system is demonstrated to be valid and reliable; limits of generalisability are documented.",
                "MEASURE 2.6": "The system is evaluated regularly for safety risks; residual negative risk does not exceed risk tolerance; it can fail safely.",
                "MEASURE 2.7": "Security and resilience are evaluated and documented.",
                "MEASURE 2.8": "Risks associated with transparency and accountability are examined and documented.",
                "MEASURE 2.9": "The model is explained, validated and documented, and output is interpreted within context to inform responsible use and governance.",
                "MEASURE 2.10": "Privacy risk is examined and documented.",
                "MEASURE 2.11": "Fairness and bias are evaluated and results documented.",
                "MEASURE 2.12": "Environmental impact and sustainability of training and management are assessed and documented.",
                "MEASURE 2.13": "Effectiveness of the employed TEVV metrics and processes is evaluated and documented.",
            }),
            "MEASURE 3": ("Mechanisms for tracking identified AI risks over time are in place.", {
                "MEASURE 3.1": "Approaches, personnel and documentation are in place to regularly identify and track existing, unanticipated and emergent risks.",
                "MEASURE 3.2": "Risk tracking approaches are considered where risks are difficult to assess with available techniques or metrics are not yet available.",
                "MEASURE 3.3": "Feedback processes for end users and impacted communities to report problems and appeal outcomes are established and integrated into evaluation metrics.",
            }),
            "MEASURE 4": ("Feedback about efficacy of measurement is gathered and assessed.", {
                "MEASURE 4.1": "Measurement approaches are connected to deployment contexts and informed by domain experts and end users; approaches documented.",
                "MEASURE 4.2": "Measurement results on trustworthiness in deployment are informed by domain experts and relevant AI actors to validate consistent performance; results documented.",
                "MEASURE 4.3": "Measurable performance improvements or declines, based on consultation and field data, are identified and documented.",
            }),
        },
    },
    "MANAGE": {
        "purpose": "Allocates risk resources to mapped and measured risks on a regular basis.",
        "categories": {
            "MANAGE 1": ("Risks from MAP and MEASURE are prioritised, responded to and managed.", {
                "MANAGE 1.1": "A determination is made whether the system achieves its intended purposes and whether development or deployment should proceed.",
                "MANAGE 1.2": "Treatment of documented risks is prioritised by impact, likelihood and available resources or methods.",
                "MANAGE 1.3": "Responses to high-priority risks are developed, planned and documented (mitigate, transfer, avoid or accept).",
                "MANAGE 1.4": "Negative residual risks to downstream acquirers and end users are documented.",
            }),
            "MANAGE 2": ("Strategies to maximise benefits and minimise negative impacts are planned, prepared, implemented and documented.", {
                "MANAGE 2.1": "Resources required to manage risks are considered, along with viable non-AI alternatives.",
                "MANAGE 2.2": "Mechanisms are in place and applied to sustain the value of deployed systems.",
                "MANAGE 2.3": "Procedures are followed to respond to and recover from a previously unknown risk when identified.",
                "MANAGE 2.4": "Mechanisms and assigned responsibilities exist to supersede, disengage or deactivate systems with performance or outcomes inconsistent with intended use.",
            }),
            "MANAGE 3": ("Risks and benefits from third-party entities are managed.", {
                "MANAGE 3.1": "Risks and benefits from third-party resources are regularly monitored and risk controls applied and documented.",
                "MANAGE 3.2": "Pre-trained models used for development are monitored as part of regular monitoring and maintenance.",
            }),
            "MANAGE 4": ("Risk treatments, including response, recovery and communication plans, are documented and monitored regularly.", {
                "MANAGE 4.1": "Post-deployment monitoring plans are implemented, including capturing user input, appeal and override, decommissioning, incident response, recovery and change management.",
                "MANAGE 4.2": "Measurable activities for continual improvement are integrated into system updates, with regular engagement with interested parties.",
                "MANAGE 4.3": "Incidents and errors are communicated to relevant AI actors including affected communities; tracking, response and recovery processes are followed and documented.",
            }),
        },
    },
}

GENAI_RISKS = [
    {"id": "cbrn", "name": "CBRN information or capabilities"},
    {"id": "confabulation", "name": "Confabulation (confidently stated false content)"},
    {"id": "dangerous_content", "name": "Dangerous, violent or hateful content"},
    {"id": "data_privacy", "name": "Data privacy (leakage, inference of personal data)"},
    {"id": "environmental", "name": "Environmental impacts"},
    {"id": "harmful_bias", "name": "Harmful bias and homogenisation"},
    {"id": "human_ai_config", "name": "Human-AI configuration (automation bias, over-reliance, anthropomorphising)"},
    {"id": "information_integrity", "name": "Information integrity (mis- and disinformation)"},
    {"id": "information_security", "name": "Information security (prompt injection, data poisoning, lowered barriers for attacks)"},
    {"id": "intellectual_property", "name": "Intellectual property"},
    {"id": "obscene_content", "name": "Obscene, degrading and/or abusive content"},
    {"id": "value_chain", "name": "Value chain and component integration (third-party models and data)"},
]


def all_subcategories() -> dict[str, str]:
    out = {}
    for fn in CORE.values():
        for _cat, (_t, subs) in fn["categories"].items():
            out.update(subs)
    return out


assert len(all_subcategories()) == 72, len(all_subcategories())
