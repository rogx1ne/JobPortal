# Frontend Scaffold

Next.js App Router frontend wired to the backend API.

## Quick Start

```bash
nvm use || nvm install
cp .env.local.example .env.local
npm install
npm run clean
npm run dev
```

Default backend target:
- `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api`

Recommended runtime:
- Node `20.x` (see `.nvmrc`)

## Routes

- `/` landing page
- `/jobs` listing + filters + save action
- `/jobs/[id]` detail + save/apply + assistant panel
- `/dashboard` auth-gated saved jobs + AI recommendations
- `/auth/login`
- `/auth/register`
