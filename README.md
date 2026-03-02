# Job Portal (Django + MySQL + Bootstrap)

Fully working Job Portal web application built with:

- Python + Django (templates)
- MySQL (no SQLite)
- Bootstrap (CDN) for basic styling

## Features

- Role-based authentication: **Admin**, **Employer**, **Job Seeker**
- Employers: post/edit/delete jobs, view applicants, update application status
- Job Seekers: browse/search/filter jobs, apply with cover letter + resume, view applied jobs
- Admin: manage users/jobs/applications via Django admin

## Setup (Local)

### 1) Create MySQL database and user

```sql
CREATE DATABASE job_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'job_portal'@'%' IDENTIFIED BY 'job_portal_password';
GRANT ALL PRIVILEGES ON job_portal.* TO 'job_portal'@'%';
FLUSH PRIVILEGES;
```

### 2) Configure environment

```bash
cp .env.example .env
```

Update `DB_NAME`, `DB_USER`, `DB_PASSWORD` (and `DB_HOST` if needed).

### 3) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4) Run migrations

```bash
python manage.py migrate
```

### 5) Seed sample data (optional)

```bash
python manage.py seed_data
```

Seeded credentials:

- Admin: `admin` / `Admin123!Admin123!` (also available at `/admin/`)
- Employer: `employer1` / `Employer123!Employer123!`
- Job seeker: `seeker1` / `Seeker123!Seeker123!`

### 6) Run server

```bash
python manage.py runserver
```

Open:

- Home: `http://127.0.0.1:8000/`
- Jobs: `http://127.0.0.1:8000/jobs/`
- Admin: `http://127.0.0.1:8000/admin/`

## MySQL settings

Database config lives in `config/settings/base.py` and is loaded from `.env` using `django-environ`.

## File uploads

- Uploaded resumes are stored under `media/` (served automatically in debug mode).

Revenue forecasting:
- `forecast_amount = expected_revenue * probability / 100`

### Tasks

- `GET /tasks/`
- `POST /tasks/` (requires `related_type` + `related_id`)
- `PATCH /tasks/{id}/`

Overdue logic:
- `Task.is_overdue == due_at < now and status not in (done, canceled)`

### Analytics (optimized annotations)

- `GET /analytics/leads-by-status/`
- `GET /analytics/revenue-by-month/` (closed won)
- `GET /analytics/sales-rep-performance/`
- `GET /analytics/conversion-rate/`
- `GET /analytics/deal-pipeline/`

## Filtering, Search, Pagination

- Pagination: page-number (`?page=1&page_size=50`)
- Search: `?search=acme`
- Ordering: `?ordering=-created_at`
- Filters (examples):
  - Leads: `?status=qualified&owner=3`
  - Deals: `?stage=negotiation&close_date_gte=2026-01-01`
  - Tasks: `?status=todo&priority=high`

## Error Responses

Validation:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input",
    "details": { "...": ["..."] }
  }
}
```

## Seed Data

`python manage.py seed_data` creates:
- `admin` (role `admin`)
- `manager` (role `manager`)
- `sales1`, `sales2` (role `sales_rep`)
- Sample leads/customers/deals/tasks

Default dev passwords:
- `admin`: `Admin123!Admin123!`
- `manager`: `Manager123!Manager123!`
- `sales1`: `Sales123!Sales123!`
- `sales2`: `Sales123!Sales123!`

Change these in non-development environments.

## Deployment Notes

- Use `DJANGO_ENV=production`
- Set `DJANGO_DEBUG=false`
- Provide `DJANGO_ALLOWED_HOSTS`
- Run with Gunicorn (example in `Dockerfile`)

## Postman Collection

See `postman/CRM.postman_collection.json`.
