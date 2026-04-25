# Komplain.ai — 10-Minute Pitch Video Script

**Format:** Spoken narration aligned to the 9-slide pitch deck, with the **live product demo placed at the end** (after all slides) so GLM-5.1 latency cannot disrupt the main pitch flow.
**Total target runtime:** **10:00** (≈ 1,300 spoken words at ~130 wpm).
**Tone mix:** Investor hook → academic / technical depth → results → customer-empathy demo → confident close.

---

## ⏱️ Time Budget at a Glance

| Block | Slide(s) | Time | Cumulative |
|---|---|---|---|
| **A. Cold Open & Problem** | 1 → 2 | 1:30 | 1:30 |
| **B. The Solution & How It Works** | 3 → 4 | 1:45 | 3:15 |
| **C. Why It Wins (differentiators + metrics)** | 6 | 1:15 | 4:30 |
| **D. Architecture & Tech Depth** | 7 | 1:00 | 5:30 |
| **E. Results, Impact & Roadmap** | 8 | 1:00 | 6:30 |
| **F. 🎬 Live Demo (end-loaded)** | 5 (on screen) + product UI | 3:00 | 9:30 |
| **G. Close & Ask** | 9 | 0:30 | 10:00 |

> 🎙️ **Speaking tips for the recording:**
> • Record at a steady **130 words per minute** — slow enough to be understood, fast enough to feel energetic.
> • Stay on slides for blocks A → E, switch to the live product UI for block F, then back to Slide 9 for the close.
> • Pause **1 full second** at every dash ( — ) and at every slide transition.
> • Do **not** read filler bullet text on slides verbatim; let visuals support what you are saying.

> ⚠️ **Why the demo is last (latency strategy):**
> GLM-5.1 occasionally takes 20-40 seconds for a single agent step under load. Ending with the demo means:
> 1. Your scored content (problem → solution → results) is **never blocked** by an unresponsive API.
> 2. If the demo runs long, you trim the final wrap rather than skipping a key slide.
> 3. You have a clear narration script to **fill dead air** (see Block F sub-cues) while agents are thinking.
> 4. If GLM hangs entirely, the close still lands cleanly — you just say "the rest of the trace continues in the same pattern" and pivot to Slide 9.

---

## 🎬 BLOCK A — Cold Open & Problem  (0:00 → 1:30)

### Slide 1 — Title  *(0:00 → 0:30)*

> *(Look at camera. Confident, warm. Title slide visible.)*

> "Hi — I'm **[Your Name]**, and this is **Komplain.ai**.
>
> In the next ten minutes I'll show you how a five-agent pipeline powered by **ILMU GLM-5.1** turns a raw, code-switched customer complaint — the kind of message a Malaysian e-commerce shopper actually writes — into a **structured, auditable, bilingual resolution** in under forty-five seconds.
>
> This is our submission to the **AI Systems and Agentic Workflow Automation** track. I'll walk through the problem, our solution, the architecture and results — and I'll close with a **live demo** of the running product.
>
> Let's start with the problem."

> *(Click to Slide 2.)*

---

### Slide 2 — The Problem  *(0:30 → 1:30)*

> "If you've ever worked an e-commerce support inbox, this image is familiar. Tickets stack up faster than humans can read them.
>
> We spoke to support operators and looked at the workflow honestly, and we found **four problems repeating everywhere**:
>
> First — **fragmented triage.** Every operator categorises differently. There's no standard, so the same complaint gets two different outcomes depending on who picks it up.
>
> Second — **time.** A single complaint takes an agent **eight to fifteen minutes** to read, look up the order, deliberate, and write a reply. During flash sales, that math breaks. SLAs are missed and refunds get delayed.
>
> Third — **no audit trail.** When a refund goes out, there's nothing explaining *why*. Supervisors are flying blind.
>
> And fourth — and this one is uniquely Malaysian — **the inputs are messy.** Customers write in **Manglish** — code-switched English and Bahasa Malaysia in the same sentence. Rigid keyword systems either misclassify these or reject them outright.
>
> Today's average: eight to fifteen minutes per complaint. Our target — **under forty-five seconds**, and fully auditable."

> *(Click to Slide 3.)*

---

## 🧠 BLOCK B — The Solution & How It Works  (1:30 → 3:15)

### Slide 3 — The Solution  *(1:30 → 2:15)*

> "Komplain.ai is an **AI copilot for support teams**. Not a chatbot — a copilot. The human supervisor still owns the final decision; we just do the heavy lifting that comes before it.
>
> The core insight is this: instead of one giant prompt trying to do everything, we use **five small, specialised agents** chained sequentially — each with one job, each producing typed output, each leaving a trace.
>
> Three things make it work:
>
> One — we **process Manglish natively**. No translation step, no preprocessing — GLM-5.1 understands code-switched language out of the box.
>
> Two — decisions are **adaptive, not hardcoded**. The system arrives at *refund*, *reship*, *clarify*, or *review* by reasoning over the order context against policy — not by matching keywords.
>
> Three — **bilingual replies are generated simultaneously** in English and Bahasa Malaysia, in a single API call, from semantic intent — not translated after the fact. They sound culturally right because they're written that way from the start."

> *(Click to Slide 4.)*

---

### Slide 4 — How It Works (5-Agent Pipeline)  *(2:15 → 3:15)*

> "Here's the pipeline. Five agents, one orchestrator, GLM-5.1 as the reasoning engine.
>
> **Agent 1 — Intake.** Takes the raw complaint text. GLM extracts the structured fields: order ID, complaint type, language, sentiment.
>
> **Agent 2 — Context.** Looks up the order in our store; GLM then *synthesises a contextual note* — what's actually happening with this order in plain language.
>
> **Agent 3 — Reasoning.** This is the brain. GLM evaluates the complaint plus the order context plus our refund policy, and produces a decision with a confidence score and a written rationale.
>
> **Agent 4 — Response.** Drafts the bilingual customer reply, English and Bahasa Malaysia, aligned to whatever decision Agent 3 made.
>
> **Agent 5 — Supervisor.** An *independent* GLM check — re-reads everything, sets a confidence flag, and assigns escalation priority.
>
> And then — and this is the part that matters most — the **human supervisor must explicitly approve** before any reply leaves the system. AI recommends. Human decides. Always."

> *(Click to Slide 6 — skipping Slide 5 for now, we'll bring it back during the demo.)*

---

## 🏆 BLOCK C — Why Komplain.ai Wins  (3:15 → 4:30)

### Slide 6 — Differentiators + Metrics  *(3:15 → 4:30)*

> "So why does this approach win?
>
> Five things make Komplain.ai genuinely different from a 'wrap-GPT-in-a-form' project:
>
> One — **Manglish-native.** Code-switched language in, structured output out. Zero preprocessing.
>
> Two — **Evidence-based decisions.** REFUND and RESHIP outcomes *emerge* from GLM reasoning over context. They aren't the result of an `if-else` tree we wrote.
>
> Three — **Bilingual by design.** Generated, not translated.
>
> Four — **Human-in-the-loop.** GLM recommends. The supervisor approves. Always.
>
> Five — **Fully auditable.** Every decision has a rationale string and an event log entry.
>
> And the numbers, measured during evaluation testing:
> • Resolution time **under forty-five seconds**, against an eight-to-fifteen-minute baseline.
> • **Eighty percent or more** of cases auto-resolved without human REVIEW.
> • Average confidence **0.87**, against our target of 0.75.
> • **Five-step pipeline**, fully traced."

> *(Click to Slide 7.)*

---

## 🛠️ BLOCK D — Architecture & Tech Depth  (4:30 → 5:30)

### Slide 7 — Architecture & Stack  *(4:30 → 5:30)*

> "Briefly on the architecture — three clean layers.
>
> The **frontend** is React 18, deliberately built without a bundler — UMD plus Babel Standalone — so it deploys as a static site on Netlify with zero build pipeline.
>
> The **backend** is FastAPI on Python 3.13, hosted on Render. The five agents are orchestrated sequentially. Every agent's output is validated against a **Pydantic v2 schema** with three layers of validation, so a malformed GLM response cannot poison the next stage.
>
> The **LLM engine** is **ILMU GLM-5.1**, called in JSON mode, with a configurable timeout.
>
> One detail I want to call out — the box at the bottom — the **'GLM removal test.'** We deliberately built no fallbacks and no heuristics. If you unset the `ILMU_API_KEY`, the very first agent throws a `RuntimeError` and the API returns HTTP 500. We tested this. **GLM is load-bearing.** This isn't an LLM bolted onto a rule engine — the LLM *is* the engine."

> *(Click to Slide 8.)*

---

## ✅ BLOCK E — Results, Impact & Roadmap  (5:30 → 6:30)

### Slide 8 — Results & Impact  *(5:30 → 6:30)*

> "Results, measured against our QA plan:
>
> All **sixty-six** test cases in the QATD passed. End-to-end pipeline averages **twenty-three seconds** under normal API latency — well inside our thirty-second target. SSE first event under two seconds. Decision confidence averaging 0.87. Manglish processed natively. Both languages generated in a single GLM call. Zero API keys committed to the repo. FIFO five-record cap on storage, verified.
>
> And the path forward is real — not vapourware: a **PostgreSQL** migration path is sketched in the SAD, **JWT** authentication, **Redis** rate-limiting, and a multi-tenant model for SaaS deployment.
>
> Now — let me **show you all of this running live**."

> *(Switch screen-share / browser tab to the dashboard. Bring Slide 5 up beside the live UI if your recording setup allows split-screen — or simply hold Slide 5 in mind as your demo storyboard.)*

---

## 🎬 BLOCK F — LIVE DEMO  (6:30 → 9:30)

> 🎙️ **DEMO CHEAT SHEET — keep this visible while recording:**
> • Pre-load: dashboard at `komplain-ai.netlify.app`, second tab on `/api/health`.
> • **Pre-warm the API ~60 seconds before hitting record:** call `POST /api/test-llm` once so Render isn't cold-starting.
> • Pre-stage the Manglish complaint text in clipboard:
>   *"Hi, my order dah tiga hari tak sampai lagi. I track tapi cakap still processing. Order KM-1042. Boleh refund ke? Very disappointed lah."*
> • Have order **KM-1042** seeded in `data/orders.json` with status PROCESSING.
> • Make sure dark mode + compact density looks clean for screen recording.

> ⚠️ **GLM Latency Safety Net — read this before recording:**
> If any agent step takes longer than ~5 seconds visible to the viewer, **keep talking** using the "Filler narration" lines provided at each beat below. Long silence is the only thing that kills a demo video — talking through latency feels intentional.
>
> If a step stalls past ~30 seconds: say *"While the supervisor agent finishes its independent review — let me show you the case log from earlier runs"* and click into the Case Log to show a previously completed case. **Never sit in silence.**
>
> 🛟 **Backup plan:** Record a clean offline demo run *before* the main recording session and keep the video file ready. If the live demo fails entirely during recording, splice the backup take into this section in post.

### Demo Beat 1 — Setup  *(6:30 → 6:50)*

> "Let me show you this running. I'm on **komplain-ai.netlify.app** — this is the live deployment, frontend on Netlify, backend on Render. The whole stack is in our public repo.
>
> Imagine I'm **Aishah**, a support operator at a Malaysian e-commerce store. A complaint just landed in my queue."

### Demo Beat 2 — Submit Complaint  *(6:50 → 7:15)*

> *(Paste the Manglish complaint into the form. Show the order ID field is optional — but you'll include it: KM-1042.)*

> "Watch the input. This is **real Manglish** — *'order dah tiga hari tak sampai lagi'* — three days, hasn't arrived. *'I track tapi cakap still processing'*. Mixed English and BM in the same sentence. No preprocessing, no translation. I just hit **Resolve**."

### Demo Beat 3 — Watch the Pipeline  *(7:15 → 8:25)*

> *(The Agent Trace Panel animates step by step. Be ready — this is the longest GLM section.)*

> "Now look at the agent trace panel on the right.
>
> **Intake fires** — language detected as Manglish, order ID extracted as KM-1042, complaint type DELAYED_DELIVERY, sentiment negative.
>
> **Context loads** — the order is real, status PROCESSING, ordered three days ago, estimated delivery was *yesterday*. So this complaint is legitimate.
>
> **Reasoning agent runs** — GLM weighs the policy: an order one day overdue, in PROCESSING status, after three days with no shipment. The decision: **REFUND**, confidence **0.82**, with a written rationale explaining exactly *why* this passed the policy threshold.
>
> **Response agent** drafts the bilingual reply. Notice — both English and Bahasa Malaysia versions appear at the same time. Same intent, two languages, both written natively.
>
> **Supervisor agent** does an independent re-read and confirms — confidence high, escalation priority normal."

> 💬 **Filler narration if a step is slow** *(use any of these instead of going silent)*:
> • *"You can see the agent's working — each call is going through GLM-5.1 with a JSON-mode-enforced schema, so even a slow response is a structurally valid one."*
> • *"While that processes — note that every event you see here is also being persisted to `agent_events.json`, which is what gives us the audit trail I mentioned earlier."*
> • *"Each agent's input and output is validated against a Pydantic v2 schema before passing to the next — so the pipeline is structurally safe even if one step is slow."*
> • *"This call is going to ILMU's hosted GLM endpoint — production deployments would put this behind a Redis-cached short-circuit for repeat queries, which is on our roadmap."*

### Demo Beat 4 — Human-in-the-Loop  *(8:25 → 9:00)*

> *(Click into the Resolution Card. Edit the BM reply slightly — change the timeline phrase. Then click Approve.)*

> "Here's the part the AI doesn't get to skip. As the supervisor, *I* am the final approver. I can edit the reply — let me change the refund timeline wording to '3 to 5 working days' — copy it, or send it.
>
> I click **Approve**. Case status updates to *resolved*. Total time on the clock: **about four minutes**, including me reading and editing.
>
> Compare that to the manual baseline of eight to fifteen minutes — and notice we now have a permanent audit trail: every agent's input, output, and rationale, captured in `agent_events.json`."

### Demo Beat 5 — Case Log Recap  *(9:00 → 9:30)*

> *(Scroll to Case Log. Open the case modal.)*

> "Here in the case log — the latest five cases, each with the full event trace clickable. Auditors and supervisors can replay any decision after the fact. **Opaque AI is structurally impossible here** — every output is logged."

> *(Switch back to slides — Slide 9 for the close.)*

---

## 🎯 BLOCK G — Close & Ask  (9:30 → 10:00)

### Slide 9 — Close & Ask  *(9:30 → 10:00)*

> "To recap. Komplain.ai is a five-agent, GLM-powered pipeline that resolves complaints in under forty-five seconds, with bilingual outputs, full audit trails, and a human supervisor in the loop.
>
> Everything you've seen — code, PRD, SAD, QATD, this deck, and this video — is in our GitHub repo at **github.com/Ph0enix19/Komplain.ai**. The live demo is at **komplain-ai.netlify.app**.
>
> Thank you."

> *(Hold final slide for 2 seconds. End recording.)*

---

## 📋 Recording Checklist

Before you hit record, confirm:

- [ ] Backend health check returns 200: `curl https://komplain-ai.onrender.com/api/health`
- [ ] **API pre-warmed** — call `POST /api/test-llm` ~60 seconds before recording so Render isn't cold-starting
- [ ] Order **KM-1042** seeded in `data/orders.json` with status `PROCESSING`
- [ ] Frontend dashboard loads cleanly at `komplain-ai.netlify.app` on the device you're recording
- [ ] Manglish complaint text is in your clipboard
- [ ] Browser zoom set so the agent trace panel is fully visible during demo
- [ ] **Backup demo video pre-recorded** (offline run, ready to splice in if live fails)
- [ ] Mic levels tested; record a 10-second sample first
- [ ] Camera framing (if showing your face) — eye-level, well-lit
- [ ] Slide deck open in **Presenter View** on a second monitor with this script visible
- [ ] Stop all notifications (Slack, mail, system) before recording

## 📤 Post-Recording

1. Export video as MP4 at 1080p.
2. Upload to **Google Drive**; set sharing → *Anyone with the link → Viewer*.
3. Replace `REPLACE_WITH_YOUR_GOOGLE_DRIVE_LINK` placeholder in the repo's `README.md`.
4. (Optional) Mirror to YouTube as **Unlisted** and add the link below the Drive link.
5. Commit & push the README change so the link goes live before the deadline.

---

*Word count of spoken narration (excluding directions and headers): approximately **1,310 words** — comfortably inside a 10-minute video at 130 wpm with natural pauses and the embedded 3-minute end-loaded demo.*
