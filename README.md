# Komplain.ai

> **Hackathon Domain:** AI Systems & Agentic Workflow Automation
> **Submission:** Single repository containing all deliverables (code + documentation + pitch video).

---

## 🎥 Pitch Video & Live Demo (10 minutes)

> **▶️ Watch the recorded pitch & product demonstration here:**
> **[👉 Click to watch on Google Drive](REPLACE_WITH_YOUR_GOOGLE_DRIVE_LINK)**

> _Replace the link above with your shared Google Drive URL before submitting. Make sure sharing is set to **"Anyone with the link → Viewer"**._

**Mirror / backup link (optional):** _add YouTube unlisted link here_

---

## 📦 Deliverables Index

All required documentation is included in this repository under [`/docs`](./docs) in **PDF format** as required by the submission rubric. Editable source files (`.docx`, `.pptx`) are committed alongside the PDFs for transparency.

| # | Deliverable | PDF | Source |
|---|---|---|---|
| 1 | **PRD** — Product Requirements Document | [docs/PRD.pdf](./docs/PRD.pdf) | — |
| 2 | **SAD** — System Architecture Document | [docs/SAD.pdf](./docs/SAD.pdf) | — |
| 3 | **QATD** — Quality Assurance & Testing Document | [docs/QATD.pdf](./docs/QATD.pdf) | [docs/QATD.docx](./docs/QATD.docx) |
| 4 | **Pitch Deck** | [docs/PitchDeck.pdf](./docs/PitchDeck.pdf) | [docs/PitchDeck.pptx](./docs/PitchDeck.pptx) |
| 5 | **Pitch Video (10 min + demo)** | _see link above_ | — |
| 6 | **Source Code** | _this repository_ | — |
| 7 | **Pitch Script** (speaker notes for the video) | [docs/PitchScript.md](./docs/PitchScript.md) | — |

🌐 **Live deployed app:** https://komplain-ai.netlify.app
🔌 **Backend API:** https://komplain-ai.onrender.com/api

---

## About the Project

<img width="2527" height="1521" alt="image" src="https://github.com/user-attachments/assets/f4c76208-0ec0-4474-8d3a-0b14edcf8c4d" />


Komplain.ai is a hackathon MVP for agentic customer complaint resolution. It combines a browser-based operations dashboard with a FastAPI backend that runs a multi-agent workflow over customer complaints, order context, decision reasoning, bilingual response drafting, and supervisor review.

The project is designed for ecommerce support teams that need to process common complaints quickly while keeping a visible audit trail. A support operator can submit a complaint, optionally include an order ID, watch each agent step run, review the final recommendation, edit the customer reply, and inspect recent cases in the case log.

## What the Project Does

Komplain.ai turns raw customer complaints into structured support outcomes. The system extracts complaint details, looks up order data from local JSON storage, decides whether to refund, reship, escalate, or dismiss the case, drafts replies in English and Bahasa Malaysia, and records each agent step as an event.

The dashboard shows four main work areas:

- New complaint: enter or quick-load a customer complaint.
- Agent trace: watch the intake, context, reasoning, response, and supervisor steps.
- Resolution: review the final decision, confidence score, policy rationale, and bilingual reply.
- Case log: inspect the latest five complaints and open detailed case history.

The backend stores only the latest five complaint records and their matching agent events to keep the demo data focused.

## Tech Stack

- Frontend: static HTML, React UMD, Babel Standalone, plain CSS.
- Backend: FastAPI, Uvicorn, Pydantic.
- LLM integration: ILMU-compatible chat completions API.
- Storage: local JSON files in `data/`.

## Run Locally

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r backend/requirements.txt
```

3. Create `.env` with your ILMU settings.

```env
ILMU_API_KEY=your_api_key_here
ILMU_BASE_URL=https://api.ilmu.ai/v1
ILMU_MODEL=ilmu-glm-5.1
ILMU_TIMEOUT=180
ILMU_REASONING_EFFORT=low
AGENT_LLM_TIMEOUT_SECONDS=180
```

4. Start the backend.

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

5. Start the frontend from the repository root.

```powershell
python -m http.server 3000 --bind 127.0.0.1
```

6. Open the app.

```text
http://127.0.0.1:3000/Komplain.ai%20Dashboard.html
```

API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Deploy Backend on Render

Create a Render Web Service from this repository with these settings:

- Runtime: Python 3
- Root Directory: leave empty
- Build Command: `pip install -r backend/requirements.txt`
- Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

Set this environment variable in the Render dashboard to avoid Python 3.14 dependency builds for packages such as `pydantic-core`:

```env
PYTHON_VERSION=3.13.2
```

Add the same ILMU values from your local `.env` as Render environment variables. Do not upload `.env` to Render or commit it to Git.

## Deploy Frontend on Netlify

Netlify hosts only the static frontend from this repository. The included `netlify.toml` publishes the repository root and runs no build command.

Use these settings if you configure the site manually:

- Base directory: leave empty
- Build command: leave empty
- Publish directory: `.`

The frontend is already configured to call the Render backend at `https://komplain-ai.onrender.com/api`.

## API Overview

- `GET /api/health`: checks backend status and complaint count.
- `POST /api/complaints`: runs the complaint pipeline and stores the result.
- `GET /api/complaints`: returns stored complaint records.
- `GET /api/complaints/{complaint_id}`: returns one complaint record.
- `GET /api/complaints/{complaint_id}/events`: returns the agent trace for one complaint.
- `GET /api/complaints/{complaint_id}/stream`: streams agent events as server-sent events.
- `POST /api/test-llm`: sends a test prompt to the configured ILMU model.

## Project Structure and File Summary

### Root Files

- `.env`: local environment variables for ILMU credentials and runtime configuration; never commit real secrets.
- `.gitattributes`: Git attribute configuration for repository file handling.
- `.gitignore`: keeps local secrets, virtual environments, and runtime logs out of Git.
- `.venv/`: local Python virtual environment, if created.
- `.tmp/`: local temporary workspace data.
- `Komplain.ai Dashboard.html`: main browser entry point; loads React, Babel, CSS, data, components, and `app.jsx`.
- `index.html`: redirect page that forwards to the dashboard HTML file.
- `app.jsx`: main React application; wires state, API calls, complaint creation, timeline animation, resolution editing, and case modal behavior.
- `data.js`: frontend demo constants, quick-load scenarios, mock orders, seed cases, agent definitions, and offline pipeline examples.
- `styles.css`: global layout, theme variables, app shell, panels, typography, and responsive styling.
- `components.css`: shared component styling for controls, cards, traces, modals, badges, and case log UI.
- `backend/requirements.txt`: Python dependencies for the FastAPI backend.
- `README_BACKEND.md`: earlier backend-focused setup notes.
- `README.md`: this professional project overview and operating guide.
- `backend.log`: runtime stdout log for the backend server.
- `backend.err`: runtime stderr log for the backend server.
- `frontend.log`: runtime stdout log for the local frontend server.
- `frontend.err`: runtime stderr log for the local frontend server.

### Backend

- `backend/__init__.py`: marks `backend` as a Python package.
- `backend/main.py`: FastAPI application; configures CORS, loads `.env`, defines API routes, and orchestrates the complaint pipeline.
- `backend/agents.py`: agent prompts and execution functions for intake, context, reasoning, response drafting, supervisor review, and event creation.
- `backend/llm.py`: ILMU API client; sends chat completion requests, handles JSON responses, and validates response format.
- `backend/models.py`: Pydantic models and enums for complaint input, agent outputs, stored records, events, and test requests.
- `backend/storage.py`: JSON-backed data manager for orders, complaints, and agent events; keeps only the latest five complaints.
- `backend/__pycache__/`: generated Python bytecode cache; not part of the application source.

### Frontend Components

- `components/Topbar.jsx`: dashboard top navigation and controls for theme, density, tone, and trace style.
- `components/ComplaintForm.jsx`: complaint input panel with quick-load scenarios, optional order ID field, and resolve action.
- `components/AgentTracePanel.jsx`: visual agent trace area with stepper, card, and compact timeline variants.
- `components/ResolutionCard.jsx`: final decision panel with confidence meter, policy rationale, bilingual replies, edit, copy, approve, and detail actions.
- `components/CaseLog.jsx`: recent case table, filters, CSV export, and detailed case modal.
- `components/TweaksPanel.jsx`: edit-mode controls for changing theme, density, tone, and trace style.

### Data

- `data/orders.json`: local mock order database used by the context agent.
- `data/complaints.json`: persisted complaint records; currently capped to five records.
- `data/agent_events.json`: persisted agent execution events for the retained complaints.

### Uploads

- `uploads/Komplain_AI_Execution_Blueprint.docx`: project blueprint document used as supporting material.

## Security Notes

Keep `.env` private. If an API key was ever committed to a public repository, rotate or revoke it immediately and push a commit that removes it from Git tracking.

## Current Demo Behavior

- The frontend expects the backend at `https://komplain-ai.onrender.com/api`.
- The backend allows browser requests from static frontend hosts such as Netlify.
- The case log is intentionally limited to the latest five complaints.
- Complaint and event data are stored locally as JSON for simple hackathon deployment.
