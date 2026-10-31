# Video script: AI Use Case Registry (DATA722 Phase 2, use case C)

**Length: about 4 min 40 s (ceiling is 5:00).** Tools: record the screen in Clipchamp or Canva; generate the voiceover from the narration below in ElevenLabs (paste each block as one generation, about 150 words a minute), or read it yourself. Footage: `docs/video_footage/` (screen recordings of the live app) plus screenshots of the notebook.

Before recording: open the live app in a fresh browser window, Register tab, "Viewing as: Team member". Open the notebook at section 6 in a second tab.

---

## 1. The problem (0:00 to 0:40, under 45 seconds)

**On screen:** title card "AI Use Case Registry: register, tier, document", then the Phase 1 worksheet row 2 for use case C.

**Narration:**
> Banks are adopting AI faster than they can govern it. At our bank, teams start or buy AI systems such as credit scoring, fraud blocking and customer chatbots, and register them with a brief that rarely says what decision the system shapes, who it affects, or how it was tested. The governance team chases the gaps by email, tiers each case by judgement, and seldom produces model or system documentation. My working estimate is 250 to 400 hours a year, and the real risk is a high-risk credit model running without the oversight its tier needs. So I built a chatbot that every team uses to register its AI use case.

## 2. Live demo (0:40 to 2:30)

**On screen, step by step:**

1. (0:40) Point at the banner: "You are interacting with an AI system". Choose the sample **"Credit unit 'helper tool' (understated framing)"** and click Send.
   > This team describes its credit model as a small helper tool for officers. That is exactly the understatement Phase 1 warned about.
2. (0:55) The assistant replies with five numbered questions, each with its legal reason (EU AI Act, NIST, AIGP). Point at the right panel: the provisional tier floor, the framework bars filling up, the missing list.
   > It asks only about what is missing, and each question cites the clause that needs it. On the right, the framework coverage fills up as we answer.
3. (1:10) Paste the prepared answers (from `docs/demo_answers.md`), Send, and repeat for two or three rounds; then type **finish**.
4. (1:35) The result appears. Show the **Risk tier assessment**: Bank tier High, EU AI Act Annex III 5(b), the team's own words as evidence, the risk score against appetite, mandatory controls.
   > Despite the framing, it is high risk: the system evaluates the creditworthiness of individuals. A hard rule sets that floor and the conversation cannot lower it.
5. (1:50) Click **Who is affected**, then **Model card** (point at a quoted source line and a red "Not provided"), then **System card**, then **Framework gap map**.
   > Every statement in the cards quotes what the team actually said. Anything they did not provide is shown as not provided and becomes an open item. Nothing is invented.
6. (2:10) Go to **Inventory**, switch "Viewing as" to **AI governance committee**, open the new registration, click **Approve**. Switch to **Administrator**, open **Admin**, move the risk appetite slider.
   > The chatbot only drafts. The registration waits for the governance office, or the committee for high-risk cases. The administrator, not the chatbot, sets the risk appetite.
7. (2:25) Back on Register, type a message containing a fake CNIC. Show it blocked.
   > Customer data is blocked before anything reaches the model.

## 3. The implementation: what happens on each request (2:30 to 3:35)

**On screen:** the "How it works" tab pipeline, then the notebook section 4.1 diagram.

**Narration:**
> On every message, five things happen. First, a guard scans for customer identifiers and blocks them. Second, the model, OpenAI's open-weight gpt-oss-120b on Groq, reads the message into forty registration fields. Each fact must carry an exact quote, and code checks the quote really is in the team's words; if not, the fact is dropped. Third, code, not the model, works out which fields this particular use case requires, from the EU AI Act, NIST AI RMF and AIGP mapping, and which are still missing. Fourth, it asks the five most important missing ones. When nothing required is missing, the model screens the whole description against the Article 5 prohibitions, Annex III and the bank's own prohibited uses. Hard rules set a minimum tier; the model can raise it but never lower it. Then code scores the risk against the appetite, builds the model card and system card from verified facts only, and writes a draft to the inventory. One registration is about fourteen model calls and twenty thousand tokens, roughly two thirds of a US cent.

## 4. Evaluation numbers, and one thing that does not work (3:35 to 4:40)

**On screen:** notebook section 6 metrics table; then the held-out results; then the dev log.

**Narration (numbers from the notebook):**
> I measured the metrics fixed in Phase 1. {EVAL_SENTENCE}
> One thing that does not work: my keyword rules overfit. They scored one hundred percent on the cases I developed them on, but seventy-one percent on fourteen held-out cases written afterwards. For example, a deepfake detector that looks for "digitally manipulated" video was flagged as a prohibited manipulative practice, and a mule-account system was treated as recruitment because the text said people were "recruited" as mules. The rules err towards over-tiering, which delays projects rather than harming customers, but a reviewer still has to catch it. And because I ran on Groq's free tier, the full-system evaluation covers twelve registrations, not all seventy-seven: those numbers are indicative, not conclusive.

**Closing card (4:40):** "Synthetic data only. Drafts are never official until approved."
