# Shop Management SaaS API

FastAPI backend for a multi-shop management product.

## Layout

```
app/
  main.py                 # application entrypoint
  core/                   # settings, logging, errors, middleware
  infrastructure/
    database/             # SQLAlchemy base, session, health check
  modules/                # business modules (identity, shop, sales, ...)
tests/
alembic/                  # database migrations
```

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

Health check: `http://127.0.0.1:8000/health`  
Docs: `http://127.0.0.1:8000/docs`

Copy `.env.example` to `.env` and set `DATABASE_URL` before running migrations.
