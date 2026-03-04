# Career Job Aggregator (Django + MySQL)

A lightweight job discovery engine that aggregates jobs from multiple public APIs in one place.

## Features

- Search jobs by keyword (+ optional location)
- Aggregates multiple job sources into one list (Remotive + Arbeitnow; optional Adzuna)
- Smart relevance ranking (best matches first)
- Trending jobs on the homepage
- Popular searches (based on logged searches)
- Shareable search URLs (copy link)
- Pagination + sorting + source selection
- Basic API health logs in Django Admin
- Filter results by company and category
- Stores search logs (and optional cached jobs) in MySQL
- No user accounts required
- Django Admin for managing logs and cache

## Tech

- Python (Django)
- MySQL
- Django templates (HTML)
- Bootstrap (CDN)

## Project Structure

```
JobPortal/
  career_aggregator/          # Django project settings + root URLs
    settings.py
    urls.py
  core/                       # Static pages + homepage
    views.py                  # Home + About
    middleware.py             # Request ID middleware
    request_id.py             # Request ID log filter support
    templatetags/
      highlight.py            # Highlight query tokens in templates
  jobs/                       # Search UI + DB models + admin
    forms.py                  # Search form + validation
    views.py                  # Search view (aggregation + filters + pagination)
    models.py                 # SearchLog, JobCache, ApiFetchLog
    admin.py                  # Admin configs
    migrations/               # DB migrations
    management/commands/      # `cleanup_job_cache` command
    tests/                    # Unit tests
  services/                   # Service layer (API integration)
    job_aggregator.py         # Multi-source fetch, normalize, dedupe, rank, cache
    job_service.py            # Remotive-only wrapper (compat)
  templates/                  # Django templates
    base.html
    core/                     # home/about
    jobs/                     # results
    404.html, 500.html
  static/                     # Static assets (CSS)
    css/styles.css
  manage.py
  requirements.txt            # Cross-platform deps (PyMySQL)
  requirements-linux.txt      # Optional linux deps (mysqlclient)
  .env.example
  README.md
```

## Setup (local)

Recommended Python: 3.11+.

### 1) Create and activate a virtualenv

```bash
python -m venv .venv
```

Activate:

- Linux/macOS: `source .venv/bin/activate`
- Windows (PowerShell): `.venv\\Scripts\\Activate.ps1`
- Windows (cmd): `.venv\\Scripts\\activate.bat`

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` uses **PyMySQL** (pure Python) for best cross-platform installs.

Optional (Linux): use `mysqlclient` instead (faster, C-based):

```bash
pip install -r requirements-linux.txt
```

### 3) Configure environment variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

On Windows, if you don’t have `cp`, create `.env` manually by copying `.env.example`.

### 4) Create MySQL database

Example (recommended: create a dedicated DB user instead of using `root`):

```sql
CREATE DATABASE career_aggregator CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'career_user'@'localhost' IDENTIFIED BY 'change-me';
CREATE USER 'career_user'@'127.0.0.1' IDENTIFIED BY 'change-me';
GRANT ALL PRIVILEGES ON career_aggregator.* TO 'career_user'@'localhost';
GRANT ALL PRIVILEGES ON career_aggregator.* TO 'career_user'@'127.0.0.1';
FLUSH PRIVILEGES;
```

If your MySQL server uses an auth plugin PyMySQL can’t use in your environment, either:
- install `mysqlclient` (`requirements-linux.txt`), or
- change the MySQL user to a compatible auth plugin for your setup.

### 5) Run migrations + create admin user

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6) Start the server

```bash
python manage.py runserver
```

Open:

- Home: `http://127.0.0.1:8000/`
- Search: `http://127.0.0.1:8000/search/`
- Admin: `http://127.0.0.1:8000/admin/`

## Optional: Enable Adzuna source

1) Create a free Adzuna developer account and get credentials.
2) Add to `.env`:
   - `ADZUNA_APP_ID=...`
   - `ADZUNA_APP_KEY=...`
   - `ADZUNA_COUNTRY=us` (or another supported country code)

Then enable the source on the search page via the “Sources” checkboxes.

## Common Issues

- `Access denied for user 'root'@'localhost'`:
  - Don’t use `root` for the app; create a dedicated user (step 4), then update `.env`.
- Static files not loading in production:
  - Run `python manage.py collectstatic` and serve `STATIC_ROOT`.

## Maintenance

- Cleanup old cached rows:
  - `python manage.py cleanup_job_cache --job-days 30 --api-days 7`

## Tests

```bash
python manage.py test
```

## Production notes

- Set `DEBUG=False`, set a real `SECRET_KEY`, and configure `ALLOWED_HOSTS`.
- Run `python manage.py collectstatic` (uses `STATIC_ROOT`).

## Notes

- This app links users to the original job posting URL (no in-app applications).
- Job descriptions from the API are treated as untrusted HTML and are displayed only as plain text excerpts.
