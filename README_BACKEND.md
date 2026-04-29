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
2. Start Ollama and ensure model exists:
   ```bash
   ollama pull qwen2.5:7b
   ollama serve
   ```
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
- No DB, no auth, no external API.

## Example complaint payload

```json
{
  "complaint_text": "Hi, my order KM-1001 arrived with a broken screen."
}
```
