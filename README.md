# AI Use Case Registry (DATA722 Phase 2, use case C)

A chatbot each team uses to register its AI use case. It checks the brief against the **EU AI Act**, the **NIST AI RMF 1.0** and the **IAPP AIGP** body of knowledge, asks follow-up questions only about what is missing, and produces a **risk tier assessment**, **who will be affected**, a **model card** and a **system card**. Each registration is added to the **AI inventory** as a draft pending approval. An administrator sets the **risk appetite** and the minimum-tier rules.

**Synthetic data only.** Every use case, team, vendor and inventory record is fictional.

| Deliverable | Where |
|---|---|
| Hosted application | Vercel (link in the notebook header) |
| Notebook (implementation, prompts, agent loop, evaluation, failures, tokens and cost, honesty) | `notebooks/DATA722_Phase2_UseCaseC.ipynb` |
| Honesty section (one page) | `docs/HONESTY.md` (also section 8 of the notebook) |
| Video script and shot list (5 minutes) | `docs/VIDEO_SCRIPT.md` |

## How it works

```
message -> [guard: personal data blocked] -> [extract: fields + verbatim quotes, verified in code]
        -> [gaps: required-for-this-use-case minus answered] -> ask up to 5 / or ready
ready   -> [screen: Art. 5, Annex III, Art. 6(3), Bank prohibited uses, affected parties]
        -> [tier: hard-rule floor + verified model signals] -> [score vs appetite]
        -> [model card + system card from verified facts] -> inventory (pending approval)
```

## Repository layout

```
api/index.py            FastAPI app (Vercel Python function)
engine/                 the system: agent loop, prompts, rules, gaps, cards, guard, store, LLM client
engine/kb/              EU AI Act, NIST AI RMF (72 subcategories), AIGP, 40-field question bank
public/                 web front end (no build step)
data/synthetic/         63 dev cases, 14 held-out cases, guard tests, seed inventory
scripts/                generators for synthetic data, seed inventory, notebook
eval/                   harness (Phase 1 metrics), team simulator, oracle ablation, runner
results/                evaluation outputs used by the notebook
notebooks/              the notebook
docs/                   honesty section, video script
```

## Run locally

```bash
pip install -r requirements.txt uvicorn
```

```bash
export GROQ_API_KEY=your_key
```

```bash
SERVE_STATIC=1 uvicorn api.index:app --port 8000
```

Then open http://localhost:8000.

## Deploy on Vercel

1. Import this GitHub repository in Vercel (Add New > Project). Framework preset: **Other**. No build command needed.
2. Settings > Environment Variables: add `GROQ_API_KEY` (Production and Preview). Optional: `GROQ_MODEL` (default `openai/gpt-oss-120b`).
3. Optional but recommended: Storage > Connect Database > **Upstash for Redis** (free). This sets `KV_REST_API_URL` and `KV_REST_API_TOKEN`, making the inventory and admin settings shared across users. Without it, each browser keeps its own registrations and the seeded records come from the server.
4. Redeploy. Check `https://<your-app>.vercel.app/api/health` shows `"llm_configured": true`.

## Reproduce the evaluation

```bash
python scripts/make_synthetic.py && python scripts/make_seed_and_samples.py
```

```bash
GROQ_API_KEY=your_key python -m eval.run_eval --all
```

```bash
python scripts/build_notebook.py && jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=7200 notebooks/DATA722_Phase2_UseCaseC.ipynb
```

## Security notes

* The Groq key is only read from the server environment; it is never sent to the browser or committed.
* Messages containing CNIC, IBAN, card, mobile, labelled account numbers, personal e-mails, passport numbers or pasted tables are blocked before the model and not stored.
* There is no user authentication in the demo: the "Viewing as" role switcher is for demonstration. Production would sit behind the Bank's SSO.
