<div align="center">

# Komplain.ai

[![CI](https://github.com/Ph0enix19/Komplain.AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Ph0enix19/Komplain.AI/actions/workflows/ci.yml)
![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)
![React 18](https://img.shields.io/badge/React-18_UMD-61DAFB?logo=react&logoColor=black)

### Agentic Customer Complaint Resolution

Komplain.ai turns raw customer complaints into structured, auditable, bilingual support resolutions through a five-agent workflow.

**Hackathon Track:** AI Systems & Agentic Workflow Automation

[Live Frontend](https://komplain-test-xi2r.vercel.app) | [Backend Health](https://komplaintest.onrender.com/api/health) | [GitHub Repository](https://github.com/Ph0enix19/Komplain.AI)

</div>

---

## Live Links

These links were verified against the current deployment:

- **Live frontend:** <https://komplain-test-xi2r.vercel.app>
- **Backend API health:** <https://komplaintest.onrender.com/api/health>
- **GitHub repository:** <https://github.com/Ph0enix19/Komplain.AI>

> Render may cold-start after idle periods, so the first backend request can take longer than normal.

---

## Pitch Video

> **[Watch the recorded pitch and product demo](https://drive.google.com/file/d/1IJ3Xe-SRWEcsv7_5ecS_KsFvllmv88rM/view?usp=sharing)**

---

## What Komplain.ai Does

Komplain.ai is an AI copilot for e-commerce support teams. It accepts unstructured customer complaints, including English, Bahasa Malaysia, and Manglish, then produces a structured decision and bilingual customer response for human review.

A support operator can:

- Submit a complaint with an optional order ID.
- Run the five-agent pipeline from the dashboard.
- View live agent trace telemetry with real timings.
- Review the decision, rationale, confidence, bilingual output, tokens, and estimated RM cost.
- Copy or edit the customer replies before approval.
- Approve the case and reset the workspace for the next complaint.
- Review recent stored cases and their agent events.

The MVP stores only the latest five complaints and related agent events in JSON files.

---

## Architecture

- **Backend:** FastAPI on Render.
- **Frontend:** Static React 18 UMD app on Vercel.
- **Storage:** JSON flat files for the MVP.
- **Pipeline:** Intake -> Context -> Reasoning -> Response -> Supervisor.
- **LLM:** Provider-agnostic OpenAI-compatible client. Z.ai / GLM is the primary provider, with Groq retained as fallback.

---

## Multi-Agent Pipeline

| Step | Agent | Responsibility |
|---|---|---|
| 1 | **Intake** | Extracts customer name, order ID, issue type, sentiment, and language from the raw complaint. |
| 2 | **Context** | Looks up matching order data from JSON storage and summarizes available context. |
| 3 | **Reasoning** | Chooses `REFUND`, `RESHIP`, `ESCALATE`, or `DISMISS`, with confidence and rationale. |
| 4 | **Response** | Drafts concise English and Bahasa Malaysia replies aligned with the decision. |
| 5 | **Supervisor** | Validates the outcome and flags whether human review or high priority handling is required. |

The backend records each agent step as an event. Response and supervisor processing are dispatched after reasoning, and the final complaint record is saved with agent metrics and pipeline totals.

---

## Observability / Telemetry

Each complaint run captures operational telemetry:

- Per-agent latency, rounded to two decimal places.
- Per-agent input and output token counts.
- Token usage from provider responses when available.
- Token estimation fallback when providers omit usage data.
- Total token count across all agents.
- Estimated cost per complaint in RM.

Cost is calculated in `backend/llm.py` with:

```text
COST_PER_1K_TOKENS_RM = 0.002
estimated_cost_rm = (total_tokens / 1000) * COST_PER_1K_TOKENS_RM
```

Telemetry appears in:

- `/api/complaints`
- `/api/complaints/{id}`
- `/api/complaints/{id}/events`
- `/api/complaints/{id}/stream`
- the frontend agent trace, case detail modal, command center, and resolution card

---

## Frontend Capabilities

The frontend is a static React 18 UMD dashboard with no build step. Current capabilities include:

- Complaint intake with optional order ID and quick-load scenarios.
- Agent trace visualization with real backend timings.
- Trace display modes: stepper, cards, and timeline.
- Resolution card showing decision, confidence, rationale, bilingual replies, latency, tokens, and RM cost.
- Copy buttons for English and Bahasa Malaysia replies with visible copied feedback.
- Editable reply drafts before approval.
- Approval flow that closes the active case and clears stale trace/resolution state.
- Recent case log with search, status filters, CSV export, and detail modal.

The MVP does not send messages to customers automatically; approval is represented inside the dashboard workflow.

---

## LLM Architecture

The LLM client in `backend/llm.py` is provider-agnostic and OpenAI-compatible.

- `LLM_PROVIDER=zai` uses Z.ai / GLM with `ZAI_*` environment variables and reports the configured `ZAI_MODEL` to the frontend through `/api/health`.
- `LLM_PROVIDER=groq` uses Groq with `GROQ_*` environment variables.
- `LLM_PROVIDER=ilmu` remains available for the legacy GLM-oriented ILMU configuration with `ILMU_*` environment variables.
- When Z.ai is selected, timeout, rate limit, provider, missing-key, or invalid-response failures fall back to Groq.
- Structured output is requested with JSON mode where supported.
- If JSON mode fails or returns unusable content, the client retries safer request shapes and can parse key-value fallback output.
- Agents also include deterministic fallback logic for timeouts, invalid structured output, or provider failures.

This gives the MVP practical failover behavior at both the LLM request layer and the agent layer, while keeping provider selection environment-driven.

---

## Tech Stack

- **Backend:** FastAPI, Uvicorn, Pydantic v2, HTTPX, Python 3.13.
- **Frontend:** React 18 UMD, ReactDOM UMD, Babel Standalone, plain CSS.
- **LLM:** OpenAI-compatible chat completions client; Z.ai / GLM primary, Groq fallback.
- **Storage:** JSON files in `data/`.
- **Testing:** pytest, pytest-asyncio.
- **Quality / security:** ruff, pip-audit, detect-secrets.

---

## Run Locally

### Prerequisites

- Python 3.13+
- A Z.ai API key for the primary GLM provider
- A Groq API key for fallback
- A modern browser

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
pip install -r backend/requirements.txt
pip install -r requirements-dev.txt
```

### 4. Configure environment variables

Create a local `.env` file in the repository root:

```env
LLM_PROVIDER=zai
ZAI_API_KEY=your_zai_key_here
ZAI_BASE_URL=https://api.z.ai/api/paas/v4
ZAI_MODEL=glm-5.1
ZAI_TIMEOUT=60
ZAI_THINKING_TYPE=disabled
ZAI_TEMPERATURE=0.1

GROQ_API_KEY=your_groq_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT=180
AGENT_LLM_TIMEOUT_SECONDS=180
```

No provider API keys should be committed. Use `.env` locally and hosting environment variables in deployment.

### 5. Start the backend

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open the API docs at <http://127.0.0.1:8000/docs>.

### 6. Start the frontend

From the `frontend/` directory:

```bash
python -m http.server 3000 --bind 127.0.0.1
```

Open <http://127.0.0.1:3000/>.

When served locally, the frontend tries `http://127.0.0.1:8000/api` first and then falls back to the hosted Render API.

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Returns backend status, UTC time, and stored complaint count. |
| `POST` | `/api/test-llm` | Smoke-tests the configured LLM provider. |
| `POST` | `/api/complaints` | Creates a `PROCESSING` complaint and starts the pipeline in the background. |
| `GET` | `/api/complaints` | Lists stored complaints, capped to the latest five records. |
| `GET` | `/api/complaints/{id}` | Returns one complaint record. |
| `GET` | `/api/complaints/{id}/events` | Returns agent events for one complaint. |
| `GET` | `/api/complaints/{id}/stream` | Streams agent events using server-sent events. |

Completed complaint records include telemetry:

```json
{
  "agent_metrics": {
    "intake": {
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

## Testing and CI/CD

The current pytest suite is fully mocked by default and does not call external LLM APIs.

```bash
python -m pytest -q
```

Current local result:

```text
30 passed
```

Coverage areas:

- **API:** health, LLM smoke endpoint, complaint creation, retrieval, and event traces.
- **Agents:** intake extraction, language detection, context lookup, reasoning validation, bilingual response output, and supervisor flags.
- **LLM parsing:** JSON mode, markdown JSON extraction, key-value fallback, provider switching, and token usage estimation.
- **Storage:** JSON save/load, order lookup, FIFO complaint cap, and event pruning.

GitHub Actions runs on pushes to `main`, pull requests to `main`, and manual `workflow_dispatch`.

| Job | Purpose |
|---|---|
| `lint` | Runs `ruff check backend/ tests/` and `ruff format --check backend/ tests/`. |
| `test` | Installs runtime/dev dependencies and runs `pytest tests/ -v --tb=short` on Python 3.13. |
| `security` | Runs `pip-audit -r requirements.txt --strict` and `detect-secrets scan --baseline .secrets.baseline`. |

The security job is marked `continue-on-error: true`, so advisories are visible without blocking demo iteration.

Optional real-provider smoke testing:

```powershell
$env:LLM_PROVIDER = "zai"
$env:ZAI_API_KEY = "your_real_zai_key"
$env:GROQ_API_KEY = "your_real_groq_fallback_key"
python -m pytest tests/ --llm -v
```

---

## Deployment

### Frontend - Vercel

- Public URL: <https://komplain-test-xi2r.vercel.app>
- Serves the static React app from `frontend/`.
- No frontend build step is required.
- The deployed frontend points to the hosted Render API in `frontend/app.jsx`.

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

Render environment variables:

- `PYTHON_VERSION=3.13.2`
- `LLM_PROVIDER=zai`
- `ZAI_API_KEY`
- `ZAI_BASE_URL`
- `ZAI_MODEL`
- `ZAI_TIMEOUT`
- `GROQ_API_KEY`
- `GROQ_BASE_URL`
- `GROQ_MODEL`
- `GROQ_TIMEOUT`
- `AGENT_LLM_TIMEOUT_SECONDS`

Never commit `.env` or provider API keys. Use the hosting platform's environment-variable settings.

---

## Project Structure

```text
Komplain.ai/
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── postman_collection.json
├── .github/workflows/ci.yml
├── backend/
│   ├── main.py
│   ├── agents.py
│   ├── llm.py
│   ├── models.py
│   ├── storage.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── Komplain.ai Dashboard.html
│   ├── app.jsx
│   ├── data.js
│   ├── styles.css
│   ├── components.css
│   └── components/
├── data/
│   ├── orders.json
│   ├── complaints.json
│   └── agent_events.json
├── docs/
│   ├── PRD.pdf
│   ├── SAD.pdf
│   ├── QATD.pdf
│   ├── QATD.docx
│   ├── PitchDeck.pdf
│   ├── PitchDeck.pptx
│   └── screenshots/dashboard.png
└── tests/
    ├── conftest.py
    ├── test_api.py
    ├── test_agents.py
    ├── test_llm.py
    ├── test_storage.py
    └── smoke_test_glm.py
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
| Source code | [GitHub repository](https://github.com/Ph0enix19/Komplain.AI) |

---

## Known Limitations and Roadmap

These are intentional MVP tradeoffs and clear next steps:

- **JSON storage is not scalable:** migrate complaints, orders, and events to PostgreSQL.
- **No authentication:** add operator login, roles, and tenant isolation.
- **No rate limiting:** add API-level request throttling and abuse protection.
- **External LLM dependency:** add stronger provider failover, retries, and offline queue behavior.
- **No frontend automated tests:** add component and end-to-end tests for the dashboard workflow.

---

## License

This project is a hackathon submission. All rights reserved by the authors.

---

<div align="center">

**Komplain.ai** - Hackathon Submission - AI Systems & Agentic Workflow Automation

[Live Frontend](https://komplain-test-xi2r.vercel.app) | [Backend Health](https://komplaintest.onrender.com/api/health) | [GitHub Repository](https://github.com/Ph0enix19/Komplain.AI)

</div>
