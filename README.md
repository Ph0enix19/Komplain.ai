<div align="center">

# Komplain.ai

### Agentic Customer Complaint Resolution — powered by ILMU GLM-5.1

*From a raw, code-switched complaint to an approved bilingual resolution in under 45 seconds.*

[![Live Demo](https://img.shields.io/badge/Live_Demo-Netlify-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)](https://komplain-ai.netlify.app)
[![Backend](https://img.shields.io/badge/API-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://komplain-ai.onrender.com/api/health)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![GLM-5.1](https://img.shields.io/badge/LLM-ILMU_GLM--5.1-7C3AED?style=for-the-badge)](https://api.ilmu.ai)

**Hackathon Track:** AI Systems & Agentic Workflow Automation

</div>

---

## Pitch Video & Live Demonstration (10 minutes)

> ### **[Watch the recorded pitch + product demo](REPLACE_WITH_YOUR_GOOGLE_DRIVE_LINK)**
>



---

## Try It Right Now

You have **two ways** to experience Komplain.ai. Pick whichever you prefer.

### Option 1 — Live Web App (easiest, zero setup)

The frontend is already deployed on Netlify and the backend on Render. Just open the link:

> ### **[komplain-ai.netlify.app](https://komplain-ai.netlify.app)**

Drop in a complaint (or use a quick-load scenario) and watch the full 5-agent pipeline run in your browser.

> Note: the first request after a long idle period may take ~30 seconds. Render's free tier cold-starts the backend.

### Option 2 — Run Locally

For full control and fast iteration. See the [Run Locally](#run-locally) section below.

```bash
git clone https://github.com/Ph0enix19/Komplain.ai.git
cd Komplain.ai
# then follow the local setup steps in the section below
```

You will need: Python 3.13, an ILMU API key, and a browser.

---

## Live Demo Preview

![Komplain.ai dashboard](./docs/screenshots/dashboard.png)

*The Komplain.ai dashboard: complaint intake, live agent trace, bilingual resolution card, and the recent case log.*

> _If the image above is not displaying, drop your screenshot at `docs/screenshots/dashboard.png` and commit it._

---

## Submission Deliverables

All deliverables required by the hackathon rubric are in this repository, in **PDF format**, with editable sources committed alongside.

| # | Deliverable | PDF | Source |
|---|---|---|---|
| 1 | **PRD** — Product Requirements Document | [docs/PRD.pdf](./docs/PRD.pdf) | — |
| 2 | **SAD** — System Architecture Document | [docs/SAD.pdf](./docs/SAD.pdf) | — |
| 3 | **QATD** — Quality Assurance & Testing Document | [docs/QATD.pdf](./docs/QATD.pdf) | [docs/QATD.docx](./docs/QATD.docx) |
| 4 | **Pitch Deck** | [docs/PitchDeck.pdf](./docs/PitchDeck.pdf) | [docs/PitchDeck.pptx](./docs/PitchDeck.pptx) |
| 5 | **Pitch Script** (speaker notes for the video) | [docs/PitchScript.md](./docs/PitchScript.md) | — |
| 6 | **Pitch Video (10 min + demo)** | _link at top of this README_ | — |
| 7 | **Source Code** | _this repository_ | — |

---

## What Komplain.ai Does

Komplain.ai is an **AI copilot for e-commerce support teams**. It turns raw, unstructured customer complaints — often written in **Manglish** (mixed English + Bahasa Malaysia) — into structured, auditable, bilingual support outcomes, while keeping a human supervisor in the loop for the final approval.

A support operator can:

1. Submit a complaint (with or without an order ID)
2. Watch each agent step run in a live trace
3. Review the final recommendation, confidence score, and policy rationale
4. Edit the bilingual customer reply and click Approve
5. Audit any past case from the case log

The backend persists only the latest five complaints and their event logs — focused MVP scope, designed to scale into PostgreSQL and multi-tenant SaaS post-hackathon.

---

## How It Works — 5-Agent Pipeline

| # | Agent | Role | Engine |
|---|---|---|---|
| 1 | **Intake** | Extracts order ID, complaint type, language, sentiment from raw text | GLM-5.1 |
| 2 | **Context** | Looks up the order; GLM synthesises a contextual note | Rule + GLM |
| 3 | **Reasoning** | Evaluates complaint + policy → REFUND / RESHIP / CLARIFY / REVIEW | GLM-5.1 |
| 4 | **Response** | Drafts bilingual EN + BM customer reply aligned to the decision | GLM-5.1 |
| 5 | **Supervisor** | Independent validation, confidence flag, escalation priority | GLM-5.1 |

> **Human-in-the-Loop:** Every GLM resolution requires explicit supervisor approval before any reply is dispatched.

For the full architectural rationale, agent prompts, validation strategy, and roadmap, see **[docs/SAD.pdf](./docs/SAD.pdf)**.

---

## Tech Stack

- **Frontend:** React 18 (UMD + Babel Standalone, no build step), plain CSS, static site on Netlify
- **Backend:** FastAPI, Uvicorn, Pydantic v2, Python 3.13, hosted on Render
- **LLM Engine:** ILMU GLM-5.1 (OpenAI-compatible API, JSON mode, 3-layer output validation)
- **Storage:** JSON flat-file (MVP); PostgreSQL migration path documented in the SAD

---

## Run Locally

### Prerequisites

- Python 3.13+
- An [ILMU](https://api.ilmu.ai) API key
- A modern browser

### 1. Clone and set up the virtual environment

```bash
git clone https://github.com/Ph0enix19/Komplain.ai.git
cd Komplain.ai
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

### 2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Create your .env file in the repo root

```env
ILMU_API_KEY=your_api_key_here
ILMU_BASE_URL=https://api.ilmu.ai/v1
ILMU_MODEL=ilmu-glm-5.1
ILMU_TIMEOUT=180
ILMU_REASONING_EFFORT=low
AGENT_LLM_TIMEOUT_SECONDS=180
```

### 4. Start the backend (port 8000)

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

API docs auto-generate at <http://127.0.0.1:8000/docs>.

### 5. Start the frontend (port 3000) from the /frontend directory

```bash
cd frontend
python -m http.server 3000 --bind 127.0.0.1
```

### 6. Open the dashboard

```
http://127.0.0.1:3000/
```

> Note: when running locally, the frontend defaults to the deployed Render backend. To point it at your local backend, edit `API_BASE` in `frontend/data.js`.

---

## Deployment

### Frontend on Netlify

[`netlify.toml`](./netlify.toml) publishes the `/frontend` directory with no build command — pure static hosting.

| Setting | Value |
|---|---|
| Base directory | _empty_ |
| Build command | _empty_ |
| Publish directory | `frontend` |

### Backend on Render

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Root directory | _empty_ |
| Build command | `pip install -r backend/requirements.txt` |
| Start command | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |

Set these environment variables in the Render dashboard:

- `PYTHON_VERSION=3.13.2` (prevents Python 3.14 dependency build issues)
- `ILMU_API_KEY`, `ILMU_BASE_URL`, `ILMU_MODEL`, `ILMU_TIMEOUT`, `ILMU_REASONING_EFFORT`, `AGENT_LLM_TIMEOUT_SECONDS`

> **Never commit `.env` to Git or upload it to your hosting provider.** Use the dashboard's environment-variable UI instead.

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/api/health` | Backend status and complaint count |
| `POST` | `/api/complaints` | Run the full pipeline and persist the result |
| `GET`  | `/api/complaints` | List stored complaints |
| `GET`  | `/api/complaints/{id}` | Get one complaint record |
| `GET`  | `/api/complaints/{id}/events` | Agent trace for one complaint |
| `GET`  | `/api/complaints/{id}/stream` | SSE stream of agent events |
| `POST` | `/api/test-llm` | Smoke-test the configured ILMU model |

Full OpenAPI documentation is auto-generated at `/docs` on the running backend.

---

## Project Structure

```text
Komplain.ai/
├── README.md                  ← you are here
├── netlify.toml               ← Netlify config (publishes /frontend)
├── .env                       ← LOCAL ONLY · never commit
├── .gitignore
│
├── docs/                      ← submission deliverables (PDFs)
│   ├── PRD.pdf
│   ├── SAD.pdf
│   ├── QATD.pdf      (+ .docx source)
│   ├── PitchDeck.pdf (+ .pptx source)
│   ├── PitchScript.md
│   └── screenshots/
│
├── frontend/                  ← static React 18 app, served by Netlify
│   ├── index.html
│   ├── Komplain.ai Dashboard.html
│   ├── app.jsx
│   ├── data.js
│   ├── styles.css
│   ├── components.css
│   └── components/
│       ├── Topbar.jsx
│       ├── ComplaintForm.jsx
│       ├── AgentTracePanel.jsx
│       ├── ResolutionCard.jsx
│       ├── CaseLog.jsx
│       └── TweaksPanel.jsx
│
├── backend/                   ← FastAPI + 5-agent pipeline
│   ├── main.py                ← FastAPI app, routes, orchestrator
│   ├── agents.py              ← agent prompts and execution functions
│   ├── llm.py                 ← ILMU client (JSON-mode, 3-layer validation)
│   ├── models.py              ← Pydantic v2 models for typed I/O
│   ├── storage.py             ← JSON-backed DataManager (FIFO, cap 5)
│   └── requirements.txt
│
├── data/                      ← JSON flat-file storage (MVP)
│   ├── orders.json
│   ├── complaints.json
│   └── agent_events.json
│
└── tests/
    └── smoke_test_glm.py      ← end-to-end ILMU connectivity test
```

---

## Security Notes

- `.env` is **gitignored** and must never be committed.
- If a key was ever pushed accidentally, **rotate it immediately** and force-push the cleaning commit.
- The backend has no authentication in MVP scope; production deployments require JWT auth (roadmapped in the SAD).
- No customer PII is sent to the LLM in the MVP — the demo uses synthetic data only.

---

## Results Snapshot (from QATD)

- **All 66** QA test cases pass
- End-to-end pipeline avg: **23 seconds** (target < 30s)
- Decision confidence avg: **0.87** (target ≥ 0.75)
- Manglish input processed natively — zero preprocessing
- Both EN + BM replies generated in a single GLM call
- Zero API keys present in the public repo

Full test methodology and case-by-case results: **[docs/QATD.pdf](./docs/QATD.pdf)**.

---

## Roadmap

- PostgreSQL migration (path documented in SAD §6)
- JWT-based supervisor authentication
- Redis rate-limiting and short-circuit caching for repeat queries
- Multi-tenant SaaS deployment model
- E-commerce platform connectors (Shopify, Lazada, WooCommerce)

---

## License

This project is a hackathon submission. All rights reserved by the authors.

---

<div align="center">

**Komplain.ai** · Hackathon Submission · AI Systems & Agentic Workflow Automation

[github.com/Ph0enix19/Komplain.ai](https://github.com/Ph0enix19/Komplain.ai) · [komplain-ai.netlify.app](https://komplain-ai.netlify.app)

</div>
