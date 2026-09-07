# Ultra OpenCart PRO

MVP foundation for an extensible OpenCart automation platform.

## Stack

- Python 3.12+
- FastAPI
- Pydantic Settings
- SQLAlchemy
- SQLite for development
- JWT authentication
- Argon2 password hashing
- Pytest

## Sync Core — Stage 2

The Sync Core is the central synchronization layer between OpenCart and the platform. Stage 2 provides:

- authenticated `/sync/push` batch ingestion;
- sync jobs with progress counters and status;
- per-item success/failure tracking;
- entity mapping between external OpenCart IDs and Core IDs;
- SHA-256 canonical payload checksums;
- idempotent skipping of unchanged `upsert` payloads;
- `upsert` and `delete` operations;
- job execution and status endpoints.

### Sync API

`POST /sync/push` creates a synchronization job from a batch of entities.

`POST /sync/jobs/{job_id}/run` processes the queued job.

`GET /sync/jobs/{job_id}` returns job status and counters.

All Sync Core endpoints require the existing JWT authentication flow.

## Project structure

```text
ultra-opencart-pro/
├── app/
│   ├── auth/
│   ├── models/
│   ├── opencart/
│   └── sync/
│       ├── __init__.py
│       ├── models.py
│       ├── router.py
│       ├── schemas.py
│       └── service.py
├── tests/
│   ├── test_auth.py
│   └── test_sync.py
├── .github/workflows/ci.yml
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Authentication flow

1. Client sends credentials to `/auth/login`.
2. Server verifies the password hash.
3. Server issues a JWT access token.
4. Client sends `Authorization: Bearer <token>` to protected endpoints.
5. Authentication dependency validates the token and loads the user.

Passwords are never stored in plain text. Secrets are supplied through environment variables and `.env` is ignored by Git.

## Local start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API documentation: `http://127.0.0.1:8000/docs`
