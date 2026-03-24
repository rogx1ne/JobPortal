# JobPortal

Production-ready AI-powered job aggregator with:
- Django REST backend (JWT auth, ingestion workers, assistant APIs)
- Next.js App Router frontend (jobs listing/detail/dashboard/auth)

## Architecture

```text
Frontend (Next.js + TypeScript + Tailwind + Framer Motion)
        |
        v
Backend API (Django REST + JWT)
        |
        v
Service Layer (ingestion, ranking, assistant)
        |
        +--> MySQL (core data)
        +--> Redis (Celery broker/result + optional cache)
        +--> Meilisearch (optional search index)
```

Ingestion flow:

```text
Celery Beat -> Redis Queue -> Celery Workers -> Normalize/Dedupe -> MySQL -> Meilisearch
```

## Implemented Features

### Backend
- JWT auth with refresh tokens
- User profile support (`GET/PATCH /api/auth/me`)
- Job listing, detail, and search APIs
- Save job and application tracking APIs
- Hybrid ranking: Meilisearch + lexical + recency fallback
- AI assistant endpoints (job discovery, resume help, eligibility guidance)
- Compliant ingestion pipeline:
  - API sources
  - company/scraper sources (with `robots.txt` checks)
  - configurable request delays
  - source attribution + dedupe (`title+company+location`)

### Frontend
- Landing page
- Job listing page with filters, pagination, loading skeletons
- Job detail page with save/apply actions
- Dashboard with:
  - saved jobs
  - AI recommendations
  - profile editor (headline/skills/bio/full name/resume URL)
- Auth pages (login/register)
- Protected dashboard redirect (`/dashboard` -> login when unauthenticated)

## API Endpoints

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `PATCH /api/auth/me`

### Jobs
- `GET /api/jobs`
- `GET /api/jobs/{id}`
- `GET /api/jobs/search`

### User Actions
- `POST /api/jobs/save`
- `POST /api/jobs/apply`
- `GET /api/user/saved`

### Assistant
- `POST /api/assistant/chat`
- `GET /api/assistant/recommendations`

## Project Structure

```text
career_aggregator/   Django settings + celery
api/                 REST API serializers/views/urls
jobs/                Models, tasks, migrations, admin, seed command
services/            ingestion/search/assistant services
frontend/            Next.js App Router app
```

## Backend Setup

From project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_sources
```

Run backend:

```bash
python manage.py runserver
```

Run workers (separate terminals):

```bash
celery -A career_aggregator worker -l info
celery -A career_aggregator beat -l info
```

## Frontend Setup

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run clean
npm run dev
```

Open:
- Frontend: `http://127.0.0.1:3000`
- Backend API: `http://127.0.0.1:8000/api`

## Important Environment Variables

### Backend (`.env`)
- DB: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- Redis/Celery: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- JWT: `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`
- CORS/CSRF:
  - `CORS_ALLOWED_ORIGINS`
  - `CSRF_TRUSTED_ORIGINS`
- Optional integrations:
  - `MEILISEARCH_URL`, `MEILISEARCH_API_KEY`
  - `OPENAI_API_KEY`, `OPENAI_MODEL`

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api`

## Ingestion Quick Test

After `seed_sources`, run one-shot API ingestion:

```bash
python manage.py shell -c "from jobs.models import Source, SourceType; from services.ingestion_service import ingest_api_source; [print(ingest_api_source(s)) for s in Source.objects.filter(type=SourceType.API, is_active=True)]"
```

Then verify:
- `http://127.0.0.1:8000/api/jobs`
- `http://127.0.0.1:8000/api/jobs/search?q=dev`

## Troubleshooting

### Frontend shows `Failed to fetch`
1. Ensure backend is running on `127.0.0.1:8000`.
2. Check API directly in browser: `http://127.0.0.1:8000/api/jobs/search?q=dev`.
3. Verify CORS vars in `.env`:
   - `CORS_ALLOWED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000`
   - `CSRF_TRUSTED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000`
4. Restart backend + frontend.

### Next.js dev errors with Node 25 (`middleware-manifest.json` / unstable HMR)
- Recommended Node runtime: **20.x**.
- `frontend/package.json` includes engine constraints (`>=20 <23`).
- If `nvm` is unavailable, install/use Node 20 via your preferred version manager/package tool.
- Clean and reinstall frontend deps:

```bash
cd frontend
rm -rf node_modules package-lock.json .next
npm install
npm run dev
```

## Legal/Compliance Guardrails

- No login-protected scraping
- `robots.txt` checks for company/scraper sources
- Rate limiting between ingestion requests
- Source attribution always stored (`source`, `source_url`)
- Description stored as snippet (not full copied pages)

## Notes

- Legacy Django template pages still exist from earlier iteration.
- Current product frontend is the `frontend/` Next.js app.
- Assistant uses OpenAI only when configured; otherwise uses deterministic fallback responses.
