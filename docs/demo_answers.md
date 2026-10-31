# Demo answers for the video (sample: "Credit unit 'helper tool' (understated framing)")

The chatbot asks different questions depending on what it has captured. For a short demo, after the first questions appear, paste this whole block as one answer: the assistant extracts every fact it contains, then asks only for anything still missing. Type `finish` to generate the assessment at any time.

```
- Credit officers use the score to approve or decline financing applications from individuals and to set the financing limit; in practice officers follow the score in about 95% of cases.
- It recommends; a credit officer makes the decision.
- A credit officer reviews every application and can override the score with a documented reason; overrides are about 5% of cases.
- Application data, salary credits, repayment history, the credit bureau report and existing financing exposures.
- It processes personal financial data of applicants.
- No biometric data is used.
- Individual applicants for personal and auto financing are affected by the decisions.
- About 12,000 applications a month.
- Applicants can include elderly customers and people with irregular income; officers can refer them for manual underwriting.
- On a hold-out set it has a Gini of 0.62 and a KS of 0.45, validated by the model validation team.
- We compared approval and error rates by gender, age band and province; the largest gap was 3 percentage points, within our 5-point tolerance.
- Each score comes with the top five reason codes, which officers share with declined applicants.
- Declined applicants are given the main reasons and can appeal to the credit review desk, where a senior officer re-assesses the file.
- It was trained on five years of the Bank's own financing applications and repayment outcomes.
- We checked the training data for gaps by region, gender and age; women and rural applicants were under-represented and we re-weighted them.
- All data stays in the Bank's onshore data centre in Karachi; only the credit risk team can access it.
- It is a gradient boosting model.
- It reads from the loan origination system and the credit bureau, and writes the score back to the loan origination system.
- It was tested on missing and extreme values and penetration-tested by IT security before go-live.
- Model risk reviews the population stability index and default rates monthly, with a full revalidation every year.
- If performance drops, the Head of Consumer Finance is alerted, the score can be switched off and officers fall back to the manual scorecard.
- All inputs, scores, overrides and decisions are logged and kept for ten years.
- The application form tells applicants that an automated credit score is used in the decision.
- We completed an AI impact assessment covering fundamental rights and data protection; the CRO's office signed it off in February 2026.
- It is in production since March 2026.
- It must not be used for SME or corporate financing, collections or marketing.
- No, all applicants are in Pakistan.
- SBP prudential regulations for consumer financing and consumer protection rules apply, plus Shariah review of the products.
```
