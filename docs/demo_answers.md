# Demo answers for the video

Sample brief: **"Credit unit 'helper tool' (understated framing)"** (load it from the dropdown on the Register tab).

The chatbot asks up to five numbered questions per round. For each question, copy the matching answer below, number it the same way, and send all of them in one message, for example:

```
1. Credit officers use the score to approve or decline financing applications from individuals ...
2. It recommends; a credit officer makes the decision.
```

Answer what it asks rather than pasting every fact at once: in testing, one long message containing 28 facts lost about 11 of them in extraction, and they became open items. For a short video, answer two rounds on camera, then type `finish`. Anything not yet answered is listed as an open item, which is itself worth showing.

| Topic the chatbot asks about | Answer to paste |
|---|---|
| Lifecycle stage | It is in production since March 2026. |
| Intended purpose | It estimates the probability of default of each applicant for personal and auto financing and turns it into a credit score from 300 to 900. |
| Decision or output it influences | Credit officers use the score to approve or decline financing applications from individuals and to set the financing limit; in practice officers follow the score in about 95% of cases. |
| Business domain | It is used in retail credit and financing decisions. |
| Out-of-scope and foreseeable misuse | It must not be used for SME or corporate financing, collections or marketing. |
| People affected by the output | Individual applicants for personal and auto financing are affected by the decisions. |
| Outputs concern individual people | Yes, each score is about one individual applicant. |
| Scale | About 12,000 applications a month. |
| Vulnerable groups | Applicants can include elderly customers and people with irregular income; officers can refer them for manual underwriting. |
| EU nexus | No, all applicants are in Pakistan. |
| Autonomy level | It recommends; a credit officer makes the decision. |
| Human oversight and override | A credit officer reviews every application and can override the score with a documented reason; overrides are about 5% of cases. |
| Explanation and appeal for affected people | Declined applicants are given the main reasons and can appeal to the credit review desk, where a senior officer re-assesses the file. |
| Data used (inputs) | Application data, salary credits, repayment history, the credit bureau report and existing financing exposures. |
| Personal data sensitivity | It processes personal financial data of applicants. |
| Biometric processing | No biometric data is used. |
| Training data source and provenance | It was trained on five years of the Bank's own financing applications and repayment outcomes. |
| Data representativeness and bias examination | We checked the training data for gaps by region, gender and age; women and rural applicants were under-represented and we re-weighted them. |
| Where data is processed and stored | All data stays in the Bank's onshore data centre in Karachi; only the credit risk team can access it. |
| Model type and method | It is a gradient boosting model. |
| Systems it reads from and writes to | It reads from the loan origination system and the credit bureau, and writes the score back to the loan origination system. |
| Performance metrics and results | On a hold-out set it has a Gini of 0.62 and a KS of 0.45, validated by the model validation team. |
| Fairness and bias testing | We compared approval and error rates by gender, age band and province; the largest gap was 3 percentage points, within our 5-point tolerance. |
| Explainability | Each score comes with the top five reason codes, which officers share with declined applicants. |
| Robustness and security testing | It was tested on missing and extreme values and penetration-tested by IT security before go-live. |
| Post-deployment monitoring | Model risk reviews the population stability index and default rates monthly, with a full revalidation every year. |
| Incident handling and fallback | If performance drops, the Head of Consumer Finance is alerted, the score can be switched off and officers fall back to the manual scorecard. |
| Logging and record-keeping | All inputs, scores, overrides and decisions are logged and kept for ten years. |
| Notice to affected people | The application form tells applicants that an automated credit score is used in the decision. |
| Impact assessment (FRIA / DPIA / AI impact) | We completed an AI impact assessment covering fundamental rights and data protection; the CRO's office signed it off in February 2026. |
| Other regulatory requirements and approvals | SBP prudential regulations for consumer financing and consumer protection rules apply, plus Shariah review of the products. |
