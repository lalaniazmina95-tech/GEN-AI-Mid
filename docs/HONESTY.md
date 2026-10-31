# Honesty section: what the registry gets wrong, what I would not yet ship, and what it cost

All figures come from the runs recorded in the notebook (section 6). The full-system sample is small: 12 registrations on the real model, 6 on `gpt-oss-120b` (the deployed model) and 6 on `gpt-oss-20b`. That is the most the Groq free tier allowed in one day while leaving some allowance for the live demo. One case moves a percentage by 8 to 17 points, so these numbers are indicative, not conclusive.

## What the system gets wrong

**It over-tiers.** In 3 of 12 real-model registrations the tier was too high: 1 under-tier would have been the dangerous direction, and there were none.
- A bank branch face-recognition camera was tiered *prohibited* because the model read "may call the police" as Art. 5(1)(h), which applies only to law enforcement. I fixed this in code and re-scored the recorded output to *high*, but did not re-run it.
- An internal coding assistant was tiered *limited* because `gpt-oss-20b` called it customer-facing.
- A document-completeness checker on personal financing files was tiered *high* because the keyword rule saw "personal financing applications".

**The keyword rules overfit.** They scored 100% on the 63 cases I tuned them on and 71% on 14 held-out cases written afterwards. They cannot tell "detects manipulated video" from "uses manipulative techniques", or "people recruited as mules" from recruitment. I left this unfixed so the held-out result stays honest.

**It misses gaps and repeats questions.** Two Phase 1 targets were missed:
- Gap-detection recall was 60%, against a target of at least 95%.
- The redundant-question rate was 12.6%, against a target of at most 5%.

There are two reasons. First, the model fills a missing field by inferring it from a neighbouring sentence instead of asking. Second, it does not read facts stated indirectly in understated briefs ("nobody outside the unit sees it"), so it asks again.

**It loses facts from long messages.** In a live test on the hosted app, one pasted message containing 28 facts yielded only about 17 extracted fields. The chatbot then asks again for the rest, which feeds the redundant-question rate, or lists them as open items if the team types "finish". Teams get better results answering the numbered questions than pasting everything at once.

**It can soften a weak control.** In one case the model recorded "human oversight: in place" from a sentence about *weekly monitoring of freezes*, although the team had said nobody reviews an account before it is frozen. My fabrication metric did not catch this: it only flags controls the team never mentioned. A reviewer reading the quoted source would catch it, but only if they read it.

**Its one-paragraph summaries embellish.** A judge model flagged unsupported claims in 4 of 12 AI-drafted system summaries. Some flags are the judge's own errors, but at least one is a real addition: an internal coding tool was said to "not retain code", which the team never said. The summary is labelled as AI-drafted, and all other card entries are quoted facts, but a reviewer must not rely on the summary.

**It fabricated one control, now fixed.** `gpt-oss-20b` recorded "No, we have not done that yet" as a control *in place*. That is the card-fabrication failure Phase 1 row 7a exists for. A deterministic check now forces negative answers to "not in place", and re-scoring the recorded output gives 0 fabrications. Every other card statement (422 in total) traced to a verbatim quote from the team.

**Its gold labels are mine.** Phase 1 planned two independent expert reviewers. Every gold tier was set by me, the person who also wrote the rules, which risks circularity. The CSV in `data/synthetic/gold_cases.csv` has an empty "reviewer 2" column for exactly this reason.

**Its framework text is a paraphrase.** The EU AI Act, NIST AI RMF and AIGP content is my own condensed paraphrase with references, not the official text. The question bank evidences 39 of the 72 NIST subcategories per use case; the other 33 are organisation-level and are not asked.

## What I would not yet put in front of a team, or the committee

- **Any tier without a human review.** The design already requires approval. With 3 of 12 over-tiers and a held-out rules accuracy of 71%, the tier is a draft for a reviewer, not a decision.
- **The "controls in place" column without reading the quotes.** Oversight can be softened, as shown above.
- **The demo hosting.** Data goes to Vercel and Groq in the United States. Phase 1 requires onshore hosting for this tool, and that is the production requirement.
- **The open access.** There is no authentication: anyone with the link can change the risk appetite or approve a registration. The role switcher is for demonstration only. Production needs the Bank's SSO and audit logging of every approval.
- **The free tier.** Groq's free tier allows 8,000 tokens a minute, so two people registering at the same moment will see delays or a "model unavailable" message, and the daily allowance runs out after roughly a dozen registrations.
- **The customer-data guard.** It was tested on 24 hand-written messages, with 100% recall and 0 false blocks. Real leakage will be more varied, for example names with addresses or a pasted screenshot's text.

## What it cost

| Item | Tokens | Cost (US$) |
|---|---|---|
| One registration, `gpt-oss-120b` (mean of 6) | 15,227 | 0.0042 |
| One registration, `gpt-oss-20b` (mean of 6) | 13,658 | 0.0019 |
| All 12 full-system evaluation registrations | 173,306 | 0.036 |
| v1 baseline, 75 cases on `gpt-oss-20b` | about 69,000 | 0.014 |
| Projected model cost: 40 registrations a year on `gpt-oss-120b` | | about 0.17 a year |

Prices are Groq list prices per million tokens: `gpt-oss-120b` $0.15 input and $0.60 output; `gpt-oss-20b` $0.075 and $0.30. On the free tier the actual charge was $0. Model cost is negligible. The real costs are:
- the reviewer's time to check each draft;
- the latency from free-tier rate limits, about 1 to 2 minutes per registration in the evaluation;
- running the full 77-case evaluation, about 1.5 million tokens, which needs a paid tier (about US$0.50) or several days of free allowance.
