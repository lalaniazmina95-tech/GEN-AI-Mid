"""EU AI Act (Regulation (EU) 2024/1689) - structured knowledge base.

Clause texts are faithful paraphrases written for this tool, not verbatim
quotations of the Official Journal text. Each entry carries the article
reference so a reviewer can check it against the source.

Used for: (1) the question bank (which facts must be known), (2) prohibited
practice screening (Art. 5), (3) high-risk classification (Art. 6 + Annex III),
(4) transparency obligations (Art. 50), (5) obligations listed per tier.
"""

SOURCE = "Regulation (EU) 2024/1689 (Artificial Intelligence Act), OJ L, 12.7.2024"

TIMELINE = [
    {"date": "2024-08-01", "event": "Entry into force (Art. 113)"},
    {"date": "2025-02-02", "event": "Chapters I-II apply: AI literacy (Art. 4) and prohibited practices (Art. 5)"},
    {"date": "2025-08-02", "event": "General-purpose AI model obligations (Chapter V), governance and penalties apply"},
    {"date": "2026-08-02", "event": "General application, including Annex III high-risk obligations and Art. 50 transparency"},
    {"date": "2027-08-02", "event": "Art. 6(1) high-risk systems that are safety components of Annex I products"},
]

DEFINITIONS = {
    "Art. 3(1) AI system": "A machine-based system designed to operate with varying levels of autonomy, that may exhibit adaptiveness after deployment, and that, for explicit or implicit objectives, infers from the input it receives how to generate outputs such as predictions, content, recommendations or decisions that can influence physical or virtual environments.",
    "Art. 3(3) provider": "A natural or legal person that develops an AI system or GPAI model, or has one developed, and places it on the market or puts it into service under its own name or trademark.",
    "Art. 3(4) deployer": "A natural or legal person using an AI system under its authority, except for personal non-professional activity.",
    "Art. 3(12) intended purpose": "The use for which an AI system is intended by the provider, including the specific context and conditions of use, as specified in the instructions for use, promotional material and technical documentation.",
    "Art. 3(13) reasonably foreseeable misuse": "Use of an AI system in a way not in accordance with its intended purpose but which may result from reasonably foreseeable human behaviour or interaction with other systems.",
    "Art. 3(60) deep fake": "AI-generated or manipulated image, audio or video content that resembles existing persons, objects, places or events and would falsely appear authentic or truthful.",
    "Art. 3(63) general-purpose AI model": "An AI model, trained with a large amount of data using self-supervision at scale, that displays significant generality and can competently perform a wide range of distinct tasks, and that can be integrated into a variety of downstream systems.",
}

SCOPE = {
    "Art. 2(1)": "Applies to providers placing AI systems on the EU market, deployers established or located in the EU, and providers and deployers in third countries where the output produced by the AI system is used in the Union.",
    "Bank note": "The Bank is in Pakistan. The Act binds it only where AI outputs are used in the EU. In this tool the Act is the reference model for tiers and obligations, as set in the Phase 1 assessment.",
}

# ---- Article 5: prohibited practices --------------------------------------
PROHIBITED = [
    {"code": "art5_1_a", "ref": "Art. 5(1)(a)", "name": "Manipulative or deceptive techniques",
     "text": "Placing on the market, putting into service or using an AI system that deploys subliminal techniques beyond a person's consciousness or purposefully manipulative or deceptive techniques, with the objective or effect of materially distorting behaviour by appreciably impairing informed decision-making, causing a decision the person would not otherwise have taken, in a manner that causes or is reasonably likely to cause significant harm."},
    {"code": "art5_1_b", "ref": "Art. 5(1)(b)", "name": "Exploitation of vulnerabilities",
     "text": "An AI system that exploits vulnerabilities of a natural person or group due to their age, disability or a specific social or economic situation, with the objective or effect of materially distorting their behaviour in a manner that causes or is reasonably likely to cause significant harm."},
    {"code": "art5_1_c", "ref": "Art. 5(1)(c)", "name": "Social scoring",
     "text": "AI systems evaluating or classifying natural persons or groups over a period of time based on their social behaviour or known, inferred or predicted personal or personality characteristics, where the social score leads to detrimental or unfavourable treatment in social contexts unrelated to where the data was generated, or treatment that is unjustified or disproportionate to their social behaviour or its gravity."},
    {"code": "art5_1_d", "ref": "Art. 5(1)(d)", "name": "Criminal-offence prediction from profiling",
     "text": "AI systems making risk assessments of natural persons to assess or predict the risk of a person committing a criminal offence, based solely on profiling or on assessing personality traits and characteristics. Does not apply to systems supporting a human assessment already based on objective and verifiable facts directly linked to a criminal activity."},
    {"code": "art5_1_e", "ref": "Art. 5(1)(e)", "name": "Untargeted facial image scraping",
     "text": "AI systems that create or expand facial recognition databases through the untargeted scraping of facial images from the internet or CCTV footage."},
    {"code": "art5_1_f", "ref": "Art. 5(1)(f)", "name": "Emotion recognition at work or in education",
     "text": "AI systems that infer emotions of a natural person in the areas of workplace and education institutions, except where intended for medical or safety reasons."},
    {"code": "art5_1_g", "ref": "Art. 5(1)(g)", "name": "Biometric categorisation by sensitive attributes",
     "text": "Biometric categorisation systems that categorise natural persons individually based on biometric data to deduce or infer their race, political opinions, trade union membership, religious or philosophical beliefs, sex life or sexual orientation (lawful labelling or filtering of lawfully acquired biometric datasets in law enforcement excepted)."},
    {"code": "art5_1_h", "ref": "Art. 5(1)(h)", "name": "Real-time remote biometric identification for law enforcement",
     "text": "Use of real-time remote biometric identification systems in publicly accessible spaces for the purposes of law enforcement, unless strictly necessary for narrowly defined objectives (targeted search for victims, prevention of specific imminent threats, locating suspects of serious crimes) and subject to authorisation."},
]

# ---- Article 6 + Annex III: high-risk -------------------------------------
ANNEX_III = [
    {"code": "1a", "area": "Biometrics", "ref": "Annex III 1(a)", "text": "Remote biometric identification systems. Excludes biometric verification whose sole purpose is to confirm that a specific natural person is who they claim to be."},
    {"code": "1b", "area": "Biometrics", "ref": "Annex III 1(b)", "text": "Biometric categorisation according to sensitive or protected attributes or characteristics based on inference of those attributes."},
    {"code": "1c", "area": "Biometrics", "ref": "Annex III 1(c)", "text": "Emotion recognition systems."},
    {"code": "2", "area": "Critical infrastructure", "ref": "Annex III 2", "text": "Safety components in the management and operation of critical digital infrastructure, road traffic, or the supply of water, gas, heating or electricity."},
    {"code": "3", "area": "Education and vocational training", "ref": "Annex III 3(a)-(d)", "text": "Determining access or admission, evaluating learning outcomes, assessing the appropriate level of education, monitoring prohibited behaviour during tests."},
    {"code": "4a", "area": "Employment", "ref": "Annex III 4(a)", "text": "Recruitment or selection of natural persons, in particular placing targeted job advertisements, analysing and filtering job applications, and evaluating candidates."},
    {"code": "4b", "area": "Employment", "ref": "Annex III 4(b)", "text": "Decisions affecting terms of work relationships, promotion or termination, allocating tasks based on individual behaviour or personal traits, or monitoring and evaluating the performance and behaviour of persons in such relationships."},
    {"code": "5a", "area": "Essential services", "ref": "Annex III 5(a)", "text": "Evaluating eligibility of natural persons for essential public assistance benefits and services, including healthcare, or granting, reducing, revoking or reclaiming them."},
    {"code": "5b", "area": "Essential services", "ref": "Annex III 5(b)", "text": "Evaluating the creditworthiness of natural persons or establishing their credit score, with the exception of AI systems used for the purpose of detecting financial fraud."},
    {"code": "5c", "area": "Essential services", "ref": "Annex III 5(c)", "text": "Risk assessment and pricing in relation to natural persons in the case of life and health insurance."},
    {"code": "5d", "area": "Essential services", "ref": "Annex III 5(d)", "text": "Evaluating and classifying emergency calls, or dispatching or prioritising emergency first response services, and emergency healthcare patient triage."},
    {"code": "6", "area": "Law enforcement", "ref": "Annex III 6", "text": "Systems used by or on behalf of law enforcement authorities: victim risk assessment, polygraphs, evaluating reliability of evidence, offending or re-offending risk not solely based on profiling, profiling in detection or investigation."},
    {"code": "7", "area": "Migration, asylum and border control", "ref": "Annex III 7", "text": "Systems used by competent public authorities for migration, asylum and border control management."},
    {"code": "8", "area": "Administration of justice and democratic processes", "ref": "Annex III 8", "text": "Assisting judicial authorities in researching and interpreting facts and law; influencing the outcome of elections or referenda or voting behaviour."},
]

ART6 = {
    "Art. 6(1)": "An AI system is high-risk where it is a safety component of, or is itself, a product covered by Union harmonisation legislation in Annex I and that product requires third-party conformity assessment.",
    "Art. 6(2)": "AI systems referred to in Annex III are high-risk.",
    "Art. 6(3)": "By derogation, an Annex III system is not high-risk where it does not pose a significant risk of harm to health, safety or fundamental rights, including by not materially influencing the outcome of decision-making, because it is intended to: (a) perform a narrow procedural task; (b) improve the result of a previously completed human activity; (c) detect decision-making patterns or deviations from prior patterns and is not meant to replace or influence the previously completed human assessment without proper human review; or (d) perform a preparatory task to an assessment relevant to an Annex III use case. An Annex III system is ALWAYS high-risk where it performs profiling of natural persons.",
    "Art. 6(4)": "A provider who considers an Annex III system not high-risk must document that assessment before placing it on the market and register it (Art. 49(2)).",
}

DEROGATIONS = [
    {"code": "6_3_a", "text": "Narrow procedural task"},
    {"code": "6_3_b", "text": "Improves the result of a previously completed human activity"},
    {"code": "6_3_c", "text": "Detects decision patterns without replacing or influencing the human assessment without proper review"},
    {"code": "6_3_d", "text": "Preparatory task to an Annex III assessment"},
]

# ---- Requirements and obligations -----------------------------------------
REQUIREMENTS = [
    {"ref": "Art. 4", "title": "AI literacy", "applies": "all", "text": "Providers and deployers take measures to ensure a sufficient level of AI literacy of staff and others operating AI systems on their behalf."},
    {"ref": "Art. 9", "title": "Risk management system", "applies": "high", "text": "A continuous, iterative risk management process across the lifecycle: identify and analyse known and reasonably foreseeable risks to health, safety and fundamental rights; estimate risks under intended use and reasonably foreseeable misuse; evaluate post-market data; adopt targeted risk management measures; test the system; give specific consideration to persons under 18 and other vulnerable groups (Art. 9(9))."},
    {"ref": "Art. 10", "title": "Data and data governance", "applies": "high", "text": "Training, validation and testing data subject to governance practices covering design choices, data collection processes and origin, preparation operations, assumptions, availability and suitability, examination for possible biases likely to affect health, safety or fundamental rights or lead to prohibited discrimination, measures to detect, prevent and mitigate such biases, and identification of data gaps. Data must be relevant, sufficiently representative and as free of errors and complete as possible. Art. 10(5) allows processing special categories of personal data strictly for bias detection and correction, with safeguards."},
    {"ref": "Art. 11 + Annex IV", "title": "Technical documentation", "applies": "high", "text": "Technical documentation drawn up before placing on the market and kept up to date: general description, intended purpose, development process, design specifications, data requirements, human oversight measures, validation and testing procedures and metrics, risk management system, changes over the lifecycle, standards applied, post-market monitoring plan."},
    {"ref": "Art. 12", "title": "Record-keeping", "applies": "high", "text": "Technical capability for automatic recording of events (logs) over the lifetime of the system, enabling identification of risk situations, post-market monitoring and monitoring of operation."},
    {"ref": "Art. 13", "title": "Transparency and information to deployers", "applies": "high", "text": "Designed so deployers can interpret output and use it appropriately; accompanied by instructions for use with the provider's identity, characteristics, capabilities and limitations, intended purpose, level of accuracy, robustness and cybersecurity, known or foreseeable circumstances leading to risks, performance regarding specific persons or groups, input data specifications, human oversight measures, expected lifetime and maintenance, and log collection mechanisms."},
    {"ref": "Art. 14", "title": "Human oversight", "applies": "high", "text": "Designed to be effectively overseen by natural persons during use. Oversight measures enable the assigned persons to: understand capacities and limitations and monitor operation; remain aware of automation bias; correctly interpret output; decide not to use, disregard, override or reverse the output; intervene or interrupt through a stop button or similar procedure."},
    {"ref": "Art. 15", "title": "Accuracy, robustness and cybersecurity", "applies": "high", "text": "Appropriate level of accuracy, robustness and cybersecurity, performing consistently throughout the lifecycle. Accuracy levels and metrics declared in instructions for use. Resilient to errors, faults and inconsistencies; feedback loops addressed; resilient against attempts to alter use or performance by exploiting vulnerabilities (data poisoning, model poisoning, adversarial examples, confidentiality attacks)."},
    {"ref": "Art. 16-17", "title": "Provider obligations and quality management system", "applies": "high_provider", "text": "Providers ensure compliance with Section 2, have a quality management system, keep documentation and logs, undergo conformity assessment (Art. 43), draw up an EU declaration of conformity (Art. 47), affix CE marking (Art. 48), register (Art. 49), take corrective actions (Art. 20) and demonstrate conformity on request."},
    {"ref": "Art. 25", "title": "Responsibilities along the value chain", "applies": "high", "text": "A deployer or other third party becomes a provider of a high-risk system if it puts its name or trademark on it, makes a substantial modification, or modifies the intended purpose of a non-high-risk system so that it becomes high-risk."},
    {"ref": "Art. 26", "title": "Deployer obligations", "applies": "high", "text": "Deployers: use the system according to instructions (26(1)); assign human oversight to persons with the necessary competence, training and authority (26(2)); ensure input data under their control is relevant and sufficiently representative (26(4)); monitor operation and inform the provider, and suspend use if it presents a risk; report serious incidents (26(5)); keep automatically generated logs for at least six months (26(6)); inform workers' representatives before use in the workplace (26(7)); inform natural persons that they are subject to a high-risk system that makes or assists decisions about them (26(11))."},
    {"ref": "Art. 27", "title": "Fundamental rights impact assessment", "applies": "high_fria", "text": "Before deployment, bodies governed by public law, private entities providing public services, and deployers of Annex III 5(b) (creditworthiness) and 5(c) (life and health insurance) systems perform an assessment of: the deployer's processes using the system; period and frequency of use; categories of natural persons and groups likely to be affected; specific risks of harm to them; human oversight measures; measures to be taken if risks materialise, including internal governance and complaint mechanisms."},
    {"ref": "Art. 43", "title": "Conformity assessment", "applies": "high_provider", "text": "High-risk systems undergo conformity assessment before being placed on the market; for most Annex III systems this is internal control (Annex VI)."},
    {"ref": "Art. 49", "title": "Registration", "applies": "high_provider", "text": "Providers (and public-authority deployers) register Annex III high-risk systems in the EU database before placing them on the market or putting them into service."},
    {"ref": "Art. 50(1)", "title": "Transparency: interaction with natural persons", "applies": "limited", "text": "Providers ensure AI systems intended to interact directly with natural persons are designed so those persons are informed they are interacting with an AI system, unless obvious from the context."},
    {"ref": "Art. 50(2)", "title": "Transparency: synthetic content marking", "applies": "limited", "text": "Providers of AI systems generating synthetic audio, image, video or text ensure outputs are marked in a machine-readable format and detectable as artificially generated or manipulated."},
    {"ref": "Art. 50(3)", "title": "Transparency: emotion recognition and biometric categorisation", "applies": "limited", "text": "Deployers of emotion recognition or biometric categorisation systems inform the natural persons exposed to them of the operation of the system and process personal data in accordance with data protection law."},
    {"ref": "Art. 50(4)", "title": "Transparency: deep fakes and public-interest text", "applies": "limited", "text": "Deployers of systems generating or manipulating deep fake content disclose that it has been artificially generated or manipulated; deployers publishing AI-generated text to inform the public on matters of public interest disclose that it is AI-generated unless it has undergone human review and editorial responsibility."},
    {"ref": "Art. 53", "title": "Obligations of GPAI model providers", "applies": "gpai", "text": "Providers of GPAI models draw up technical documentation, provide information to downstream providers integrating the model, put in place a copyright compliance policy, and publish a sufficiently detailed summary of training content."},
    {"ref": "Art. 55", "title": "GPAI models with systemic risk", "applies": "gpai", "text": "Providers of GPAI models with systemic risk (presumed above 10^25 FLOPs of training compute) also perform model evaluations including adversarial testing, assess and mitigate systemic risks, report serious incidents and ensure adequate cybersecurity."},
    {"ref": "Art. 72", "title": "Post-market monitoring", "applies": "high_provider", "text": "Providers establish and document a post-market monitoring system proportionate to the risk, actively collecting and analysing data on performance throughout the lifetime."},
    {"ref": "Art. 73", "title": "Reporting of serious incidents", "applies": "high", "text": "Serious incidents are reported to the market surveillance authority immediately after a causal link is established and no later than 15 days after awareness (shorter deadlines for widespread infringements or death)."},
    {"ref": "Art. 86", "title": "Right to explanation of individual decision-making", "applies": "high", "text": "A person subject to a decision taken by the deployer on the basis of output from an Annex III high-risk system, which produces legal effects or similarly significantly affects them, has the right to obtain clear and meaningful explanations of the role of the AI system in the decision and the main elements of the decision."},
    {"ref": "Art. 99", "title": "Penalties", "applies": "all", "text": "Up to EUR 35 million or 7% of worldwide annual turnover for prohibited practices; up to EUR 15 million or 3% for other obligations; up to EUR 7.5 million or 1% for supplying incorrect, incomplete or misleading information to authorities."},
]

TIERS = {
    "prohibited": {"label": "Prohibited", "rank": 4, "basis": "Art. 5", "summary": "The practice is banned. The use case cannot proceed in its current form."},
    "high": {"label": "High risk", "rank": 3, "basis": "Art. 6 and Annex III", "summary": "Allowed subject to the requirements of Art. 8-15, deployer obligations (Art. 26), and where applicable a fundamental rights impact assessment (Art. 27)."},
    "limited": {"label": "Limited risk (transparency)", "rank": 2, "basis": "Art. 50", "summary": "Allowed with transparency obligations towards the people who interact with the system or see its output."},
    "minimal": {"label": "Minimal risk", "rank": 1, "basis": "No specific obligations (voluntary codes, Art. 95); AI literacy (Art. 4) still applies", "summary": "Allowed. Good practice and AI literacy apply."},
}


def obligations_for(tier: str, *, provider: bool, fria: bool, interacts: bool, genai: bool,
                    emotion_or_biocat: bool, gpai_provider: bool = False) -> list[dict]:
    """Return the EU AI Act obligations that attach to a registration."""
    out = []
    for r in REQUIREMENTS:
        a = r["applies"]
        if a == "all":
            out.append(r)
        elif a == "high" and tier == "high":
            out.append(r)
        elif a == "high_provider" and tier == "high" and provider:
            out.append(r)
        elif a == "high_fria" and tier == "high" and fria:
            out.append(r)
        elif a == "gpai" and gpai_provider:
            out.append(r)
        elif a == "limited":
            if r["ref"] == "Art. 50(1)" and interacts:
                out.append(r)
            elif r["ref"] == "Art. 50(2)" and genai:
                out.append(r)
            elif r["ref"] == "Art. 50(3)" and emotion_or_biocat:
                out.append(r)
            elif r["ref"] == "Art. 50(4)" and genai:
                out.append(r)
    return out
