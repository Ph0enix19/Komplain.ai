# Komplain.ai Backend (Hackathon MVP)

## File Structure

```text
backend/
  __init__.py
  main.py
  models.py
  storage.py
  agents.py
  llm.py
data/
  orders.json
  complaints.json
  agent_events.json
backend/requirements.txt
```

## Run locally

1. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```
2. Configure LLM environment variables:
   ```env
   LLM_PROVIDER=zai
   ZAI_API_KEY=your_zai_api_key_here
   ZAI_BASE_URL=https://api.z.ai/api/coding/paas/v4
   ZAI_MODEL=your_current_glm_model_here
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.1-8b-instant
   ```
   Z.ai / GLM is the primary provider. Groq remains the fallback when Z.ai times out, rate-limits, returns invalid output, or is missing configuration.
3. Run API:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
4. Open docs:
   - http://localhost:8000/docs

## API Endpoints

- `POST /api/complaints`
- `GET /api/complaints`
- `GET /api/complaints/{id}`
- `GET /api/complaints/{id}/stream` (SSE)
- `GET /api/health`
- `POST /api/test-llm`

## Storage model

- App loads all JSON files at startup into memory.
- App writes back on every update.
- No DB and no auth in the MVP.
- Do not commit `.env` or provider API keys; configure secrets through local environment variables or Render.

## Example complaint payload

```json
{
  "complaint_text": "Hi, my order KM-1001 arrived with a broken screen."
}
```
