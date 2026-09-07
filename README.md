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

## Project structure

```text
ultra-opencart-pro/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   └── service.py
│   └── models/
│       ├── __init__.py
│       └── user.py
├── tests/
│   ├── __init__.py
│   └── test_auth.py
├── .github/
│   └── workflows/
│       └── ci.yml
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
