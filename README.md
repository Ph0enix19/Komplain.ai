<div align="center">

# Komplain.ai

[![CI](https://github.com/Ph0enix19/Komplain.AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Ph0enix19/Komplain.AI/actions/workflows/ci.yml)
![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)
![React 18](https://img.shields.io/badge/React-18_UMD-61DAFB?logo=react&logoColor=black)

### Agentic Customer Complaint Resolution

Komplain.ai is a hackathon MVP that turns raw customer complaints into structured, auditable, bilingual support resolutions through a five-agent workflow.

**Hackathon Track:** AI Systems & Agentic Workflow Automation

[Live Frontend](https://komplain-test-xi2r.vercel.app) | [Backend Health](https://komplaintest.onrender.com/api/health) | [GitHub Repository](https://github.com/Ph0enix19/Komplain.AI)

</div>

---

## Current Project Summary

Use this section as handoff context when starting a new AI chat:

Komplain.ai is a Python/FastAPI + static React 18 UMD dashboard for AI-assisted e-commerce complaint handling. The backend exposes `/api` endpoints, stores orders, complaints, and agent events in JSON files under `data/`, and runs a five-step complaint pipeline: intake, context, reasoning, response, and supervisor. The LLM client in `backend/llm.py` is OpenAI-compatible and environment-driven: `LLM_PROVIDER=zai` uses Z.ai / GLM first, with automatic Groq fallback; `LLM_PROVIDER=groq` and legacy `LLM_PROVIDER=ilmu` are also supported. Agents request structured JSON, normalize/validate outputs with Pydantic, record token/latency/provider telemetry, and fall back to deterministic logic when the LLM fails or returns invalid data. The frontend in `frontend/` is a no-build static React app served by `Komplain.ai Dashboard.html`; `frontend/index.html` redirects to it. The dashboard submits complaints, polls the backend until processing completes, renders live agent trace telemetry, shows resolution details and bilingual replies, supports editing/copying replies, and displays the latest five cases. Tests are in `tests/`, are mocked by default, and cover API routes, agent behavior, LLM parsing/fallbacks, storage, and telemetry.

Important files:

- `backend/main.py`: FastAPI app, routes, background pipeline orchestration, SSE event stream.
- `backend/agents.py`: five agent prompts, LLM/fallback agent logic, validation, event creation.
- `backend/llm.py`: OpenAI-compatible provider client, Z.ai/Groq/ILMU config, JSON parsing, fallback, token usage.
- `backend/storage.py`: JSON-backed `DataManager`, latest-five complaint cap, event pruning.
- `backend/models.py`: Pydantic request/response and agent result models.
- `frontend/app.jsx`: dashboard state, backend API integration, polling, case mapping, edit/copy/approve flows.
- `frontend/data.js`: demo scenarios, seed cases, mock order context, simulated traces.
- `frontend/components/`: dashboard UI components.
- `data/orders.json`: sample order lookup data.
- `tests/`: pytest suite with mocked LLM clients.

---

## Live Links

- **Live frontend:** <https://komplain-test-xi2r.vercel.app>
- **Backend API health:** <https://komplaintest.onrender.com/api/health>
- **GitHub repository:** <https://github.com/Ph0enix19/Komplain.AI>
- **Pitch/demo video:** <https://drive.google.com/file/d/1IJ3Xe-SRWEcsv7_5ecS_KsFvllmv88rM/view?usp=sharing>

Render may cold-start after idle periods, so the first backend request can take longer than normal.

---

## What Komplain.ai Does

Komplain.ai is an AI copilot for e-commerce support teams. It accepts unstructured complaints in English, Bahasa Malaysia, or Manglish and produces a structured resolution for human review.

A support operator can:

- Submit a complaint with an optional order ID.
- Run the five-agent workflow from the dashboard.
- View agent trace telemetry with real backend timings.
- Review decision, rationale, confidence, bilingual replies, latency, tokens, and estimated RM cost.
- Edit and copy the generated English and Bahasa Malaysia replies.
- Approve a case and reset the active workspace.
- Search, filter, export, and inspect recent case history.

The MVP does not send customer messages automatically. Approval is represented inside the dashboard workflow.

---

## Architecture

```text
Static React dashboard
        |
        v
FastAPI backend (/api)
        |
        v
Five-agent complaint pipeline
        |
        +--> JSON storage in data/
        |
        +--> OpenAI-compatible LLM provider
             Z.ai / GLM primary, Groq fallback
```

- **Backend:** FastAPI, Uvicorn, Pydantic v2, HTTPX, Python 3.13.
- **Frontend:** Static React 18 UMD, ReactDOM UMD, Babel Standalone, plain CSS.
- **Storage:** JSON files for hackathon MVP persistence.
- **LLM:** OpenAI-compatible chat completions client.
- **Testing:** pytest and pytest-asyncio.
- **Quality/security:** ruff, pip-audit, detect-secrets.

---

## Multi-Agent Pipeline

| Step | Agent | Responsibility |
|---|---|---|
| 1 | Intake | Extracts customer name, order ID, issue type, sentiment, and language. |
| 2 | Context | Looks up matching order data from JSON storage and summarizes context. |
| 3 | Reasoning | Chooses `REFUND`, `RESHIP`, `ESCALATE`, or `DISMISS` with confidence and rationale. |
| 4 | Response | Drafts concise English and Bahasa Malaysia replies. |
| 5 | Supervisor | Validates the outcome and flags review priority. |

The backend records each agent step as an event. Intake, context, and reasoning run sequentially. Response and supervisor run in parallel after reasoning. The completed complaint record is saved with agent metrics and pipeline totals.

---

## LLM Behavior

The provider is selected with `LLM_PROVIDER`:

- `zai`: primary Z.ai / GLM provider using `ZAI_*` environment variables.
- `groq`: Groq provider using `GROQ_*` environment variables.
- `ilmu`: legacy ILMU-compatible provider using `ILMU_*` environment variables.

When Z.ai is selected, provider failures can fall back to Groq. Fallback reasons include timeout, rate limit, provider error, missing key, or invalid response.

The client:

- Calls OpenAI-compatible `/chat/completions` endpoints.
- Requests JSON mode where supported.
- Retries without JSON mode when needed.
- Falls back to key-value parsing if structured JSON fails.
- Estimates tokens when provider usage data is unavailable.
- Adds provider and fallback metadata to agent metrics.

Agents also have deterministic fallback logic, so local tests and demo flows can complete without real provider calls when mocked or when `USE_LLM_AGENTS=false`.

---

## Telemetry

Each completed complaint stores:

- Per-agent duration.
- Per-agent input and output tokens.
- Execution mode: `llm`, `fallback`, or `unknown`.
- Provider metadata when available.
- Total latency.
- Total tokens.
- Estimated cost in RM.

Cost calculation lives in `backend/llm.py`:

```text
COST_PER_1K_TOKENS_RM = 0.002
estimated_cost_rm = (total_tokens / 1000) * COST_PER_1K_TOKENS_RM
```

Telemetry appears through the API and in the frontend agent trace, command center, resolution card, and case detail modal.

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Returns backend status, UTC time, stored complaint count, active provider/model, and fallback provider. |
| `POST` | `/api/test-llm` | Sends a prompt to the configured LLM client. |
| `POST` | `/api/complaints` | Creates a `PROCESSING` placeholder and starts the pipeline in the background. |
| `GET` | `/api/complaints` | Lists stored complaints, capped to the latest five records. |
| `GET` | `/api/complaints/{id}` | Returns one complaint record. |
| `GET` | `/api/complaints/{id}/events` | Returns agent events for one complaint. |
| `GET` | `/api/complaints/{id}/stream` | Streams agent events with server-sent events. |

Example completed complaint telemetry:

```json
{
  "status": "COMPLETED",
  "agent_metrics": {
    "intake": {
      "agent": "intake",
      "duration": 0.73,
      "input_tokens": 184,
      "output_tokens": 37,
      "execution_mode": "llm"
    }
  },
  "total_latency": 4.42,
  "total_tokens": 891,
  "estimated_cost_rm": 0.001782
}
```

---

## Frontend

The frontend is a static React app with no package install or build step.

Current capabilities:

- Complaint intake form with optional order ID.
- Quick-load demo scenarios for delivery delay, damaged item, wrong item, and missing order ID.
- Backend API fallback: local frontend tries `http://127.0.0.1:8000/api` first, then the hosted Render API.
- Agent trace display modes: stepper, cards, and timeline.
- Resolution card with decision, confidence, rationale, bilingual replies, latency, tokens, and RM cost.
- Reply editing before approval.
- Copy buttons for generated replies.
- Approval flow that clears the active workspace.
- Recent case log with search, status filters, CSV export, and case detail modal.
- Optional tweak panel support for embedded edit-mode hosts.

Main entry points:

- `frontend/index.html`: redirects to the dashboard HTML file.
- `frontend/Komplain.ai Dashboard.html`: loads React UMD, styles, data, components, and `app.jsx`.
- `frontend/app.jsx`: application state and backend integration.

---

## Storage

Data is stored in JSON files under `data/`:

- `orders.json`: sample order records used by the context agent.
- `complaints.json`: latest complaint records.
- `agent_events.json`: agent events linked to retained complaints.

`DataManager.MAX_COMPLAINTS` is currently `5`. When a new complaint is added, old complaints beyond the cap are removed and events for removed complaints are pruned.

Sample order IDs currently include:

- `KM-1001`
- `KM-1002`
- `KM-1003`
- `ORD-2041`
- `ORD-1887`

---

## Run Locally

### Prerequisites

- Python 3.13+
- A modern browser
- Optional real-provider API keys for Z.ai and Groq

### 1. Clone the repository

```bash
git clone https://github.com/Ph0enix19/Komplain.AI.git
cd Komplain.AI
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
```

`backend/requirements.txt` is also present for Render and currently mirrors the runtime dependencies.

### 4. Configure environment variables

Create `.env` in the repository root. Use `.env.example` as the template:

```env
LLM_PROVIDER=zai

ZAI_API_KEY=your_zai_api_key_here
ZAI_BASE_URL=https://api.z.ai/api/coding/paas/v4
ZAI_MODEL=glm-5.1
ZAI_TIMEOUT=60
ZAI_THINKING_TYPE=disabled
ZAI_TEMPERATURE=0.1

GROQ_API_KEY=your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT=180

AGENT_LLM_TIMEOUT_SECONDS=180
```

Useful local option:

```env
USE_LLM_AGENTS=false
```

That forces deterministic fallback agent logic instead of calling an LLM.

Never commit `.env` or provider API keys.

### 5. Start the backend

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open API docs at <http://127.0.0.1:8000/docs>.

### 6. Start the frontend

From the repository root:

```bash
python -m http.server 3000 --directory frontend --bind 127.0.0.1
```

Open <http://127.0.0.1:3000/>.

---

## Testing and CI

Run the mocked test suite:

```bash
python -m pytest -q
```

The default suite does not call real LLM providers. It covers:

- API health, LLM smoke route, complaint creation, retrieval, and events.
- Agent extraction, language detection, context lookup, reasoning validation, bilingual response output, supervisor behavior, and fallback paths.
- LLM JSON parsing, markdown JSON extraction, key-value fallback, provider switching, and token estimation.
- JSON storage, order lookup, complaint FIFO cap, and event pruning.

Optional real-provider smoke testing:

```powershell
$env:LLM_PROVIDER = "zai"
$env:ZAI_API_KEY = "your_real_zai_key"
$env:GROQ_API_KEY = "your_real_groq_fallback_key"
python -m pytest tests/ --llm -v
```

GitHub Actions runs on pushes to `main`, pull requests to `main`, and manual `workflow_dispatch`.

| Job | Purpose |
|---|---|
| `lint` | Runs `ruff check backend/ tests/` and `ruff format --check backend/ tests/`. |
| `test` | Installs runtime/dev dependencies and runs `pytest tests/ -v --tb=short` on Python 3.13. |
| `security` | Runs `pip-audit -r requirements.txt --strict` and `detect-secrets scan --baseline .secrets.baseline`. |

The security job is `continue-on-error: true`, so advisories are visible without blocking demo iteration.

---

## Deployment

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

- `PYTHON_VERSION=3.13.2`
- `LLM_PROVIDER=zai`
- `ZAI_API_KEY`
- `ZAI_BASE_URL`
- `ZAI_MODEL`
- `ZAI_TIMEOUT`
- `ZAI_THINKING_TYPE`
- `ZAI_TEMPERATURE`
- `GROQ_API_KEY`
- `GROQ_BASE_URL`
- `GROQ_MODEL`
- `GROQ_TIMEOUT`
- `AGENT_LLM_TIMEOUT_SECONDS`

`app.py` exists as a root ASGI shim for platforms that scan the repository root.

---

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
|-- netlify.toml
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
|-- docs/
|   |-- PRD.pdf
|   |-- SAD.pdf
|   |-- QATD.pdf
|   |-- QATD.docx
|   |-- PitchDeck.pdf
|   |-- PitchDeck.pptx
|   `-- screenshots/dashboard.png
`-- tests/
    |-- conftest.py
    |-- test_api.py
    |-- test_agents.py
    |-- test_llm.py
    |-- test_storage.py
    `-- smoke_test_glm.py
```

---

## Submission Deliverables

| Deliverable | File |
|---|---|
| Product Requirements Document | [docs/PRD.pdf](./docs/PRD.pdf) |
| System Architecture Document | [docs/SAD.pdf](./docs/SAD.pdf) |
| Quality Assurance and Testing Document | [docs/QATD.pdf](./docs/QATD.pdf) |
| QATD editable source | [docs/QATD.docx](./docs/QATD.docx) |
| Pitch deck | [docs/PitchDeck.pdf](./docs/PitchDeck.pdf) |
| Pitch deck editable source | [docs/PitchDeck.pptx](./docs/PitchDeck.pptx) |
| Dashboard screenshot | [docs/screenshots/dashboard.png](./docs/screenshots/dashboard.png) |
| Postman collection | [postman_collection.json](./postman_collection.json) |

---

## Known Limitations and Roadmap

Current MVP tradeoffs:

- JSON storage is not scalable or concurrent-write safe; migrate to PostgreSQL or another managed database.
- There is no authentication, authorization, tenant isolation, or audit identity.
- There is no API rate limiting.
- The frontend has no automated component or end-to-end tests yet.
- The dashboard approval flow does not persist an explicit `APPROVED` status to the backend.
- Customer replies are drafted only; no messaging/email integration sends them.
- LLM output quality depends on provider availability and structured-output reliability.

Likely next steps:

- Add operator login and role-based access.
- Persist approval/review actions through API endpoints.
- Move storage to PostgreSQL.
- Add retry queues and stronger provider failover controls.
- Add frontend tests and Playwright coverage for the main workflow.
- Add deployment health checks that exercise a short mocked or deterministic pipeline.

---

## License

This project is a hackathon submission. All rights reserved by the authors.

---

<div align="center">

**Komplain.ai** - Hackathon Submission - AI Systems & Agentic Workflow Automation

[Live Frontend](https://komplain-test-xi2r.vercel.app) | [Backend Health](https://komplaintest.onrender.com/api/health) | [GitHub Repository](https://github.com/Ph0enix19/Komplain.AI)

</div>
