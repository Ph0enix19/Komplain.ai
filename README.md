<div align="center">

# Komplain.ai

<p>
  <img src="./docs/logos/UMH.jpg" alt="UMHackathon 2026 logo" height="52">
  &nbsp;&nbsp;
  <img src="./docs/logos/Z%20AI%20Logo%20(Restricted%20Usage).png" alt="Z AI logo" height="52">
  &nbsp;&nbsp;
  <img src="./docs/logos/YATL%20LOGO.png" alt="YTL AI Labs logo" height="52">
</p>

[![CI](https://github.com/Ph0enix19/Komplain.AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Ph0enix19/Komplain.AI/actions/workflows/ci.yml)
![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI 0.136](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)
![React 18.3](https://img.shields.io/badge/React-18.3_UMD-61DAFB?logo=react&logoColor=black)
![Storage JSON MVP](https://img.shields.io/badge/Storage-JSON_MVP-f59e0b)

### AI-powered complaint resolution for e-commerce support teams

Komplain.ai turns messy customer complaints into structured decisions, bilingual replies, visual evidence checks, and auditable agent traces.


**UMHackathon 2026 Track:** AI Systems & Agentic Workflow Automation

</div>

---

<a id="final-submission-documents"></a>

## Important: Final Submission Documents in `docs/` 🎯

**Very important:** These are the main judging deliverables. Start here first; the files below are the final documentation assets stored in the repository `docs/` folder.

| Document | File |
|---|---|
| Business Proposal | [docs/Group_AS_ID_178_Komplain_ai_Business_Proposal_Final_Submission-1.pdf](./docs/Group_AS_ID_178_Komplain_ai_Business_Proposal_Final_Submission-1.pdf) |
| Deployment Plan | [docs/Group_AS_Id_178_Komplain_AI_Deployment_Plan_Final_Ss.pdf](./docs/Group_AS_Id_178_Komplain_AI_Deployment_Plan_Final_Ss.pdf) |
| Refined QATD | [docs/Team178_Team(as)_Refined_QATD_Final.pdf](./docs/Team178_Team(as)_Refined_QATD_Final.pdf) |
| Pitch Deck PDF | [docs/Komplain_AI_Pitch_Deck.pdf](./docs/Komplain_AI_Pitch_Deck.pdf) |
| Pitch Deck PPTX | [docs/Komplain_AI_Pitch_Deck.pptx](./docs/Komplain_AI_Pitch_Deck.pptx) |
| Logo Assets | [docs/logos](./docs/logos) |
| Canva Pitch Link | [https://canva.link/kwqw7albmm8g9ap](https://canva.link/kwqw7albmm8g9ap) |

**Try the full working app here:** [https://komplain-test-xi2r.vercel.app/](https://komplain-test-xi2r.vercel.app/)

---

<a id="quick-links"></a>

## Quick Links 🚀

This table includes the full project links after the required document deliverables above.

| Link | Purpose |
|---|---|
| [Final Submission Documents](#final-submission-documents) | Main PDFs, pitch deck, QATD, logos, and Canva pitch link from `docs/` |
| [Live Frontend](https://komplain-test-xi2r.vercel.app) | Vercel-hosted dashboard for the judging demo |
| [Backend Health](https://komplaintest.onrender.com/api/health) | Render-hosted FastAPI health check |
| [GitHub Repository](https://github.com/Ph0enix19/Komplain.AI) | Source code and CI history |
| [Canva Pitch Link](https://canva.link/kwqw7albmm8g9ap) | Online Canva version of the pitch deck |
| [Finalist Deliverables](#finalist-deliverables) | Docs, Postman collections, and logo assets |
| [Testing & CI](#testing-and-ci) | Local and GitHub Actions verification |
| [Image Upload Test](#test-image-upload-and-damage-analysis) | Procedure for visual damage analysis |
| [Judging Criteria Map](#judging-criteria-map) | How this project addresses UMHackathon scoring areas |

Render may cold-start after idle periods, so the first backend request can take longer than normal.

---

<a id="finalist-deliverables"></a>

## Finalist Deliverables 🎯

The UMHackathon finalist handbook asks teams to keep the repository and deliverables easy to reach from the first README section. Current links:

| Deliverable | Status |
|---|---|
| Code Repository | [GitHub repo](https://github.com/Ph0enix19/Komplain.AI) |
| Live Demo | [Frontend](https://komplain-test-xi2r.vercel.app) and [backend health](https://komplaintest.onrender.com/api/health) |
| Canva Pitch Link | [https://canva.link/kwqw7albmm8g9ap](https://canva.link/kwqw7albmm8g9ap) |
| Core Postman API Collection | [postman_collection.json](./postman_collection.json) |
| QATD Postman Evidence Collection | [postman_qatd_collection.json](./postman_qatd_collection.json) |
| Business Proposal PDF | [docs/Group_AS_ID_178_Komplain_ai_Business_Proposal_Final_Submission-1.pdf](./docs/Group_AS_ID_178_Komplain_ai_Business_Proposal_Final_Submission-1.pdf) |
| Deployment Plan PDF | [docs/Group_AS_Id_178_Komplain_AI_Deployment_Plan_Final_Ss.pdf](./docs/Group_AS_Id_178_Komplain_AI_Deployment_Plan_Final_Ss.pdf) |
| QATD PDF | [docs/Team178_Team(as)_Refined_QATD_Final.pdf](./docs/Team178_Team(as)_Refined_QATD_Final.pdf) |
| Pitch Deck PDF | [docs/Komplain_AI_Pitch_Deck.pdf](./docs/Komplain_AI_Pitch_Deck.pdf) |
| Pitch Deck PPTX | [docs/Komplain_AI_Pitch_Deck.pptx](./docs/Komplain_AI_Pitch_Deck.pptx) |
| Logo Assets | [UMH.jpg](./docs/logos/UMH.jpg), [Z AI Logo](./docs/logos/Z%20AI%20Logo%20(Restricted%20Usage).png), [YTL AI Labs Logo](./docs/logos/YATL%20LOGO.png) |
| Quality Assurance Notes | See [Testing and CI](#testing-and-ci) |
| Deployment Plan Summary | See [Deployment](#deployment) |
| Architecture Summary | See [Architecture](#architecture) |

---

<a id="introduction"></a>

## Introduction 👋

Support teams often receive complaints that are short, emotional, mixed-language, or missing order context:

> "Hi team, saya punya order sampai tapi box koyak and item cracked. Can help refund?"

Komplain.ai is an MVP copilot that helps an operator resolve that case without losing accountability. It accepts English, Bahasa Malaysia, and Manglish complaint text, optionally accepts an uploaded product/package image, checks order context, reasons through the next action, drafts English and Bahasa Malaysia replies, and shows each agent step for human review.

The product does **not** auto-send messages to customers. It keeps the human operator in control, which is important for risky refunds, unclear evidence, and escalation cases.

---

<a id="demo-flow"></a>

## Demo Flow 🎬

1. Open the [live frontend](https://komplain-test-xi2r.vercel.app).
2. Enter a complaint in English, Bahasa Malaysia, or Manglish.
3. Optionally attach a JPG, PNG, or WebP image as visual evidence.
4. Click **Resolve Complaint**.
5. Watch the agent trace progress through intake, context, optional vision, reasoning, response, and supervisor review.
6. Review the decision, confidence, rationale, bilingual replies, token usage, latency, and estimated RM cost.
7. Edit or copy the drafted replies before approval.

Useful demo order IDs from [data/orders.json](./data/orders.json):

| Order ID | Demo angle |
|---|---|
| `ORD-15` | Wrong-size apparel case; good for `RESHIP` with clear delivered order context. |
| `ORD-26` | Damaged denim jacket scenario; good for Manglish text plus image evidence. |
| `ORD-37` | Delivered kids boots case; useful for missing-item or clarification demos. |
| `ORD-48` | In-transit Bluetooth speaker; good for delivery delay / follow-up reasoning. |
| `ORD-59` | Ceramic plate set delivered recently; good for damaged fragile-item refund demos. |
| `ORD-70` | Older delivered running shoes with reship disabled; useful for policy-bound review. |
| `ORD-104` | White sport shoes delivered order; useful as a lightweight lookup scenario. |

---

<a id="key-features"></a>

## Key Features ✨

| Feature | What it does | Why judges should care |
|---|---|---|
| Text complaint intake | Extracts customer name, order ID, issue type, sentiment, and language from raw complaints. | Shows practical NLP on real support text, including Manglish. |
| Image upload and damage analysis | Accepts JPG, PNG, and WebP evidence up to 5MB, then uses GLM vision when enabled. | Adds multimodal AI rather than text-only automation. |
| Order-aware reasoning | Looks up JSON order records before deciding refund, reship, clarification, escalation, or dismissal. | Grounds AI output in business context. |
| Bilingual response drafting | Generates English and Bahasa Malaysia replies for operator review. | Fits Malaysian e-commerce support realities. |
| Human review and escalation | Supervisor agent flags review priority and keeps the operator in the approval loop. | Reduces risk from fully automated refunds or mistaken denials. |
| Agent telemetry | Stores per-agent latency, token usage, provider, fallback status, and estimated RM cost. | Demonstrates observability, cost awareness, and auditability. |
| Provider fallback | Z.ai / GLM is primary; Groq can be used as fallback for missing keys, rate limits, provider errors, invalid output, or timeouts. | Improves demo resilience and production realism. |

---

<a id="architecture"></a>

## Architecture 🏗️

```text
Static React 18 UMD dashboard
        |
        v
FastAPI backend (/api)
        |
        v
Multi-agent complaint pipeline
        |
        +--> JSON storage in data/
        |
        +--> OpenAI-compatible LLM client
             Z.ai / GLM 5.1 primary
             GLM vision for image evidence
             Groq fallback when configured
```

### Tech Stack

| Layer | Implementation |
|---|---|
| Backend | FastAPI, Uvicorn, Pydantic v2, HTTPX, Python 3.13 |
| Frontend | Static React 18.3 UMD, ReactDOM UMD, Babel Standalone, plain CSS |
| AI integration | OpenAI-compatible `/chat/completions` client in [backend/llm.py](./backend/llm.py) |
| Primary LLM | Z.ai / GLM 5.1 via `LLM_PROVIDER=zai` |
| Vision model | Z.ai / GLM vision via `ZAI_VISION_MODEL` |
| Fallback LLM | Groq via `GROQ_*` variables |
| Storage | JSON files under [data/](./data/) |
| Quality | pytest, ruff, pip-audit, detect-secrets, GitHub Actions |

### Multi-Agent Pipeline

| Step | Agent | Responsibility |
|---|---|---|
| 1 | Intake | Parses customer name, order ID, issue type, sentiment, and language. |
| 2 | Context | Looks up matching order data from JSON storage and summarizes relevant facts. |
| 3 | Vision, optional | Inspects uploaded image evidence for visible damage or contradiction. |
| 4 | Reasoning | Produces `REFUND`, `RESHIP`, `CLARIFY`, `ESCALATE`, or `DISMISS`. |
| 5 | Response | Drafts English and Bahasa Malaysia replies. |
| 6 | Supervisor | Validates the result, sets review priority, and flags risky cases. |

Intake, context, vision, and reasoning run in order. Response and supervisor run after reasoning, with the backend saving events as each step completes. The frontend polls and renders those events as a live trace.

---

<a id="important-files"></a>

## Important Files

| File | Why it matters |
|---|---|
| [backend/main.py](./backend/main.py) | FastAPI app, API routes, upload validation, background pipeline orchestration, SSE event stream, telemetry totals. |
| [frontend/app.jsx](./frontend/app.jsx) | Dashboard state, API integration, hosted/local API fallback, polling, agent trace mapping, image submission flow. |
| [backend/llm.py](./backend/llm.py) | Z.ai / GLM and Groq provider integration, JSON parsing, image input handling, fallback metadata, token estimation. |
| [backend/storage.py](./backend/storage.py) | JSON-backed `DataManager`, complaint persistence, latest-five complaint cap, event pruning. |
| [backend/agents.py](./backend/agents.py) | Agent prompts, deterministic fallback logic, validation, image-aware reasoning, bilingual response generation. |
| [backend/models.py](./backend/models.py) | Pydantic schemas for complaints, image analysis, decisions, responses, and agent events. |
| [tests/](./tests/) | Mocked API, agent, LLM, storage, fallback, telemetry, and image upload tests. |

---

<a id="api-overview"></a>

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Returns backend status, UTC time, complaint count, active provider/model, and fallback provider. |
| `POST` | `/api/test-llm` | Sends a direct test prompt to the configured LLM client. |
| `POST` | `/api/complaints` | Creates a complaint and starts the pipeline. Accepts JSON or multipart form data with optional `image`. |
| `GET` | `/api/complaints` | Lists stored complaints, capped to the latest five records. |
| `GET` | `/api/complaints/{id}` | Returns one complaint record. |
| `GET` | `/api/complaints/{id}/events` | Returns stored agent events for one complaint. |
| `GET` | `/api/complaints/{id}/stream` | Streams agent events with server-sent events. |
| `GET` | `/api/uploads/{filename}` | Serves safely named uploaded MVP evidence images. |

---

<a id="installation"></a>

## Installation 🛠️

### Prerequisites

- Python 3.13+
- A modern browser
- Optional Z.ai and Groq API keys for real-provider demos

### 1. Clone the repository

```bash
git clone https://github.com/Ph0enix19/Komplain.AI.git
cd Komplain.AI
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
```

`backend/requirements.txt` is present for Render and currently mirrors runtime dependencies.

### 4. Configure environment variables

Create `.env` in the repository root using [.env.example](./.env.example) as the template:

```env
LLM_PROVIDER=zai

ZAI_API_KEY=your_zai_api_key_here
ZAI_BASE_URL=https://api.z.ai/api/coding/paas/v4
ZAI_MODEL=glm-5.1
ZAI_TIMEOUT=60
ZAI_THINKING_TYPE=disabled
ZAI_TEMPERATURE=0.1
ZAI_VISION_BASE_URL=https://api.z.ai/api/coding/paas/v4
ZAI_VISION_MODEL=glm-4.5v
ZAI_VISION_THINKING_TYPE=disabled
VISION_ENABLED=true

GROQ_API_KEY=your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TIMEOUT=180
```

Useful local option:

```env
USE_LLM_AGENTS=false
```

That forces deterministic fallback agent logic instead of real LLM calls. Vision remains optional; set `VISION_ENABLED=false` to accept uploads but skip GLM visual inspection.

Never commit `.env` or provider API keys.

### 5. Start the backend

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open API docs at <http://127.0.0.1:8000/docs>.

### 6. Start the frontend

```bash
python -m http.server 3000 --directory frontend --bind 127.0.0.1
```

Open <http://127.0.0.1:3000/>.

---

<a id="usage"></a>

## Usage 🧭

### Submit a Text Complaint

Use the dashboard form or call the API:

```bash
curl -X POST http://127.0.0.1:8000/api/complaints \
  -H "Content-Type: application/json" \
  -d "{\"complaint_text\":\"Hi, saya punya order ORD-26 arrived damaged. Can refund?\"}"
```

The API returns a `PROCESSING` placeholder immediately, then the background pipeline updates the stored complaint and event trace.

### Review the Agent Trace

The dashboard shows each agent step with:

- Status and timing.
- Input/output token counts.
- Execution mode: `llm`, `fallback`, or `unknown`.
- Provider metadata and fallback reason where available.
- The final decision, rationale, bilingual replies, confidence, and supervisor note.

---

<a id="test-image-upload-and-damage-analysis"></a>

## Test Image Upload and Damage Analysis 🖼️

### Dashboard Procedure

1. Start the backend and frontend locally, or use the live demo.
2. Enter a complaint that mentions visible damage.
3. Attach a JPG, PNG, or WebP image in the visual evidence field.
4. Submit the complaint.
5. Confirm the trace includes the **Visual Evidence** step.
6. Open the resolution card and check `image_analysis`, `visual_evidence_used`, decision, rationale, and supervisor review status.

### API Procedure

```bash
curl -X POST http://127.0.0.1:8000/api/complaints \
  -F "complaint_text=Order ORD-26 arrived with a torn sleeve and damaged packaging. Please help review." \
  -F "order_id=ORD-26" \
  -F "image=@data/images/damaged-box.jpg;type=image/jpeg"
```

The backend validates file type and size, stores the file under `data/uploads/`, and records image analysis in the complaint payload. Supported upload types are `jpg`, `jpeg`, `png`, and `webp`; the MVP size limit is 5MB.

### Real GLM Vision Smoke Test

```powershell
$env:LLM_PROVIDER = "zai"
$env:ZAI_API_KEY = "your_real_zai_key"
$env:ZAI_VISION_MODEL = "glm-4.5v"
$env:ZAI_VISION_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
python tests/smoke_test_glm_vision.py "path\to\normal-box.jpg" "path\to\damaged-box.jpg"
```

The regular test suite mocks vision by default, so CI does not require real provider keys.

---

<a id="telemetry-and-cost-tracking"></a>

## Telemetry and Cost Tracking 📊

Each completed complaint stores:

- Per-agent duration.
- Per-agent input and output tokens.
- Execution mode.
- Provider and fallback metadata.
- Total latency.
- Total tokens.
- Estimated cost in RM.

Cost calculation lives in [backend/llm.py](./backend/llm.py):

```text
COST_PER_1K_TOKENS_RM = 0.002
estimated_cost_rm = (total_tokens / 1000) * COST_PER_1K_TOKENS_RM
```

Current metrics from this workspace's JSON snapshot:

| Metric | Observed value |
|---|---|
| Completed complaints in snapshot | 5 |
| Total pipeline latency | 15.77 s - 33.88 s across 5 recorded complaints |
| Total tokens per resolution | 2,133 - 2,896 tokens, combined input and output |
| Estimated cost per resolution | RM 0.004266 - RM 0.005792 |
| Languages observed in stored complaints | English (`EN`) |
| Decisions observed in stored complaints | `CLARIFY`, `REFUND`, `RESHIP` |
| Decision types supported by backend | `REFUND`, `RESHIP`, `CLARIFY`, `ESCALATE`, `DISMISS` |
| Provider fallback observed in stored events | No fallback events in the current local snapshot |

---

<a id="testing-and-ci"></a>

## Testing and CI ✅

Run the mocked test suite:

```bash
python -m pytest -q
```

Current pytest collection count: **55 tests**.

Run lint and format checks:

```bash
ruff check backend/ tests/
ruff format --check backend/ tests/
```

### Postman Collections

| Collection | Purpose | Requests | `pm.test(...)` assertions |
|---|---|---:|---:|
| [postman_collection.json](./postman_collection.json) | Core API smoke test for the happy path: health, LLM smoke, create complaint, fetch complaint. | 4 | 9 |
| [postman_qatd_collection.json](./postman_qatd_collection.json) | QATD evidence suite covering smoke paths, validation failures, missing records, agent events, latest-five list cap, and SSE stream smoke. | 10 | 22 |

Both collections use the current `ORD-26` demo order from [data/orders.json](./data/orders.json).

The tests cover:

- API health, LLM smoke route, complaint creation, retrieval, and events.
- Text complaint pipeline decisions, confidence, rationale, and bilingual responses.
- Image upload validation, mocked visual evidence analysis, and safe fallback when vision fails.
- Agent extraction, language detection, Manglish handling, order lookup, reasoning validation, supervisor behavior, and fallback paths.
- LLM JSON parsing, markdown JSON extraction, key-value fallback, provider switching, Z.ai to Groq fallback, and token estimation.
- JSON storage persistence, latest-five complaint cap, and agent event pruning.

GitHub Actions runs on pushes to `main`, pull requests to `main`, and manual `workflow_dispatch`.

| Job | Purpose |
|---|---|
| `lint` | Runs `ruff check backend/ tests/` and `ruff format --check backend/ tests/`. |
| `test` | Installs runtime/dev dependencies and runs `pytest tests/ -v --tb=short` on Python 3.13. |
| `security` | Runs `pip-audit -r requirements.txt --strict` and `detect-secrets scan --baseline .secrets.baseline`. |

The security job is currently `continue-on-error: true`, so advisories are visible without blocking hackathon demo iteration.

---

<a id="judging-criteria-map"></a>

## Judging Criteria Map 🏆

The UMHackathon 2026 judging criteria emphasize product viability, architecture, CI/CD, security, QA, code maturity, token cost control, real-world validation, live demo quality, and communication. Komplain.ai maps to those areas as follows:

| Judging area | How Komplain.ai addresses it |
|---|---|
| Product and business viability | Targets a clear e-commerce support pain point: slow, inconsistent complaint handling across languages and evidence types. |
| Technical stack and scalability | Uses FastAPI, Pydantic, React, modular agents, and a documented path from JSON MVP storage to a managed database. |
| CI/CD and automation | GitHub Actions runs lint, tests, and security checks on push and pull request. |
| Integration security and credential management | Uses environment variables, `.env.example`, secret scanning, and avoids committing provider keys. |
| QA and reliability | Mocked tests exercise API routes, agent behavior, provider fallback, storage, telemetry, and image upload handling. |
| Architectural tradeoffs | README explicitly documents JSON storage, no auth, external LLM dependency, and production next steps. |
| Production code maturity | Typed Pydantic models, upload validation, safe filenames, deterministic fallbacks, provider metadata, and structured events. |
| Token efficiency and cost management | Tracks total tokens and estimates RM cost per resolution. |
| Real-world impact | Supports English, Bahasa Malaysia, Manglish, order context, bilingual replies, and human review workflows. |
| Live technical demonstration | Public frontend and backend health endpoints are available for judges. |
| Presentation quality | README keeps demo links, setup, architecture, usage, testing, and judging map easy to scan. |

---

<a id="deployment"></a>

## Deployment 🌐

### Frontend - Vercel

- Public URL: <https://komplain-test-xi2r.vercel.app>
- Serves the static app from `frontend/`.
- No frontend build step is required.
- The deployed frontend uses the hosted Render API by default.

### Backend - Render

- Health endpoint: <https://komplaintest.onrender.com/api/health>
- Build command:

```bash
pip install -r backend/requirements.txt
```

- Start command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Typical Render environment variables:

```env
PYTHON_VERSION=3.13.2
LLM_PROVIDER=zai
ZAI_API_KEY=...
ZAI_BASE_URL=https://api.z.ai/api/coding/paas/v4
ZAI_MODEL=glm-5.1
ZAI_TIMEOUT=60
ZAI_THINKING_TYPE=disabled
ZAI_TEMPERATURE=0.1
ZAI_VISION_BASE_URL=https://api.z.ai/api/coding/paas/v4
ZAI_VISION_MODEL=glm-4.5v
ZAI_VISION_THINKING_TYPE=disabled
VISION_ENABLED=true
GROQ_API_KEY=...
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TIMEOUT=180
AGENT_LLM_TIMEOUT_SECONDS=180
```

`app.py` exists as a root ASGI shim for platforms that scan the repository root.

---

<a id="storage-model"></a>

## Storage Model

Data is stored in JSON files under [data/](./data/):

| File | Purpose |
|---|---|
| [data/orders.json](./data/orders.json) | Sample order records used by the context agent. |
| [data/complaints.json](./data/complaints.json) | Latest complaint records and final resolutions. |
| [data/agent_events.json](./data/agent_events.json) | Agent events linked to retained complaints. |

[backend/storage.py](./backend/storage.py) currently keeps the latest five complaints. When a new complaint is added beyond that cap, old complaints are removed and their events are pruned.

---

<a id="known-limitations"></a>

## Known Limitations ⚠️

Current MVP tradeoffs:

- JSON storage is simple and demo-friendly but not scalable or concurrent-write safe.
- There is no authentication, authorization, tenant isolation, or audit identity yet.
- There is no API rate limiting.
- The frontend does not yet have automated component or end-to-end tests.
- Customer replies are drafted only; no messaging or email integration sends them.
- Real LLM quality and latency depend on external provider availability.
- Vision analysis depends on Z.ai / GLM vision configuration; safe fallback is used when unavailable.
- The dashboard approval flow does not yet persist an explicit `APPROVED` status to the backend.

Likely production next steps:

- Move JSON storage to PostgreSQL or another managed database.
- Add operator login, role-based access, and tenant-aware audit logs.
- Add API rate limiting and request-level observability.
- Persist approval and review actions through backend endpoints.
- Add Playwright or component tests for frontend workflows.
- Add deployment health checks that exercise a short mocked or deterministic pipeline.

---

<a id="project-structure"></a>

## Project Structure

```text
Komplain.ai/
|-- README.md
|-- README_BACKEND.md
|-- app.py
|-- requirements.txt
|-- requirements-dev.txt
|-- pytest.ini
|-- postman_collection.json
|-- postman_qatd_collection.json
|-- .env.example
|-- .github/
|   `-- workflows/ci.yml
|-- backend/
|   |-- main.py
|   |-- agents.py
|   |-- llm.py
|   |-- models.py
|   |-- storage.py
|   |-- requirements.txt
|   `-- __init__.py
|-- frontend/
|   |-- index.html
|   |-- Komplain.ai Dashboard.html
|   |-- app.jsx
|   |-- data.js
|   |-- styles.css
|   |-- components.css
|   `-- components/
|       |-- AgentTracePanel.jsx
|       |-- CaseLog.jsx
|       |-- CommandCenter.jsx
|       |-- ComplaintForm.jsx
|       |-- ResolutionCard.jsx
|       |-- Topbar.jsx
|       `-- TweaksPanel.jsx
|-- data/
|   |-- orders.json
|   |-- complaints.json
|   `-- agent_events.json
`-- tests/
    |-- conftest.py
    |-- test_api.py
    |-- test_agents.py
    |-- test_llm.py
    |-- test_storage.py
    `-- smoke_test_glm_vision.py
```

---

<a id="contributing"></a>

## Contributing 🤝

This is a hackathon project, so changes should stay focused and demo-safe:

1. Create a feature branch.
2. Keep provider secrets in local environment variables only.
3. Run `ruff check backend/ tests/`, `ruff format --check backend/ tests/`, and `python -m pytest -q`.
4. Include tests for backend behavior, agent logic, or storage changes.
5. Document any new setup steps or environment variables in this README and [.env.example](./.env.example).

---

<a id="license"></a>

## License

This repository is a UMHackathon 2026 submission. All intellectual property remains with the project authors unless a separate license is added later.

---

<div align="center">

**Komplain.ai** - built for practical, reviewable, multilingual complaint resolution.

[Live Frontend](https://komplain-test-xi2r.vercel.app) | [Backend Health](https://komplaintest.onrender.com/api/health) | [GitHub Repository](https://github.com/Ph0enix19/Komplain.AI)

</div>
