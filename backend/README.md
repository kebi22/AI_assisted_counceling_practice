# AI-Assisted Counseling Simulator — Backend (Version 1)

A FastAPI backend that powers the counseling-practice simulator: scenario
retrieval, simulated client conversations (Gemini), rubric-based evaluation, and
a faculty review workflow.

Version 1 is **text-only** and **practice-only**.

## Architecture

```
API routes  ->  Services  ->  CRUD  ->  Database
                   |
                   +------>  AI agents  ->  Gemini API
```

- `app/api/` — request/response handling and dependencies (no SQL, no Gemini).
- `app/services/` — workflow coordination and business rules.
- `app/crud/` — SQLAlchemy database access.
- `app/ai/` — Gemini client, scenario agent, evaluation agent, and prompts.
- `app/db/` — models, session factory, declarative base, and seed data.
- `app/schemas/` — Pydantic request/response and structured-output models.

## Tech stack

Python 3.11+, FastAPI, SQLAlchemy 2 (async), PostgreSQL, Alembic, Pydantic 2,
Google Gen AI SDK, Pytest.

## Run with Docker (recommended)

```bash
cd backend
cp .env.example .env            # then set GEMINI_API_KEY
export GEMINI_API_KEY=your_key  # used by docker-compose
docker compose up --build
```

On startup the API container runs Alembic migrations, seeds the demo data, and
serves the app. Then visit:

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## Run locally (without Docker)

Requires Python 3.11+ and a running PostgreSQL instance.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # edit DATABASE_URL and GEMINI_API_KEY

alembic upgrade head
python -m scripts.seed_database
uvicorn app.main:app --reload
```

## Mock authentication

Version 1 uses mock auth. Requests are treated as the demo student by default.
To call faculty endpoints, send the header `X-Demo-Role: faculty`. The interface
is shaped so real authentication can replace `get_current_user` later without
changing services or endpoints.

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/scenarios` | List active scenarios |
| GET | `/api/v1/scenarios/{id}` | Scenario detail (no system prompt) |
| POST | `/api/v1/sessions` | Start a session |
| GET | `/api/v1/sessions/{id}` | Get session + transcript |
| POST | `/api/v1/sessions/{id}/messages` | Send a student message, get client reply |
| POST | `/api/v1/sessions/{id}/complete` | Complete a session |
| POST | `/api/v1/sessions/{id}/evaluation` | Evaluate (idempotent) |
| GET | `/api/v1/sessions/{id}/evaluation` | Get evaluation |
| GET | `/api/v1/faculty/sessions` | List completed sessions (faculty) |
| GET | `/api/v1/faculty/sessions/{id}` | Faculty session detail |
| POST | `/api/v1/faculty/sessions/{id}/review` | Save faculty review |

## Tests

Tests use an in-memory SQLite database and never call the live Gemini API.

```bash
cd backend
pip install -e ".[dev]"
pytest
```

## Security notes

- The Gemini API key and database credentials stay server-side.
- CORS allows only the configured frontend origins.
- Student input is length-limited; HTML is not trusted.
- Raw model output and system prompts are never exposed to students.
- Never commit a real `.env` file or API key.
