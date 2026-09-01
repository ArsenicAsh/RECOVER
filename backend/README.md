# RECOVER Backend

Day 2 foundation for RECOVER V0.1.1.

## Local setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -e ".[test]"
```

Start PostgreSQL from repository root:

```bash
docker compose up -d postgres
```

Set environment:

```bash
copy .env.example .env
```

Run migration:

```bash
cd backend
alembic upgrade head
```

Start API:

```bash
uvicorn app.main:app --reload
```

Health:

```text
GET http://127.0.0.1:8000/health
```

Tests:

```bash
pytest
```
