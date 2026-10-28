# Setup Guide

## Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Git

## Option A: Docker (Recommended)

```bash
# 1. Clone the repo
git clone <repo-url> && cd muqayyim

# 2. Configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY (needed for LLM fallback extraction)

# 3. Start all services
docker-compose up -d

# 4. Run migrations
docker-compose exec api alembic -c api/alembic.ini upgrade head

# 5. Seed demo data
docker-compose exec api python infra/scripts/seed-demo.py

# 6. Access the app
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

## Option B: Local Development

```bash
# 1. Start database + Redis via Docker
docker-compose up -d db redis

# 2. Backend setup
cd api
pip install -e ".[dev]"
cd ..
alembic -c api/alembic.ini upgrade head
python infra/scripts/seed-demo.py
uvicorn api.app.main:app --reload

# 3. Worker (separate terminal)
celery -A workers.celery_app worker --loglevel=info

# 4. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Verify Everything Works

1. Open http://localhost:3000 — you should see the dashboard
2. Open http://localhost:8000/docs — you should see the Swagger UI
3. The demo case should appear with one seeded comparable

## Environment Variables

See `.env.example` for all variables. Key ones:

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection string |
| REDIS_URL | Yes | Redis connection string |
| ANTHROPIC_API_KEY | For extraction | Claude API key for LLM fallback |
| JWT_SECRET | For prod | Change from default in production |

## Running Tests

```bash
cd api && pytest
```

## Common Issues

- **Port 5432 in use**: Stop local PostgreSQL or change the port in docker-compose.yml
- **Migrations fail**: Ensure the database is running and DATABASE_URL_SYNC is correct
- **Frontend can't reach API**: Check NEXT_PUBLIC_API_URL in frontend environment
- **Celery not processing jobs**: Ensure Redis is running and REDIS_URL is correct
