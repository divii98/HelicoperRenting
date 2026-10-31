# HeliBook

A full-stack helicopter tour booking app. A Python (FastAPI) server exposes the
`/api/*` JSON API and, in production, serves the built Angular frontend.
MySQL is the datastore. Self-rolled email/password auth (server-side
sessions in a database table, an httponly cookie) gates booking and
"my bookings".

## Two runtimes, one repo

- `server/` - the Python/FastAPI backend. Runs with `uvicorn`.
- `src/` + `angular.json` - the Angular frontend. Runs with the Angular CLI.

Unlike a single-process Node setup, Angular's dev server and FastAPI are
two separate processes in development (Angular's tooling has no equivalent
to Vite's middleware mode). `proxy.conf.json` makes Angular's dev server
forward `/api/*` to FastAPI so the browser only ever talks to one origin -
no CORS configuration anywhere in this app. In production, FastAPI serves
the Angular build directly from the same process, so it's back to a single
origin. See `references/architecture.md` in the
`build-fullstack-python-angular-app` skill for the full rationale.

## Commands

Backend (from the repo root, with a virtualenv activated):

```bash
pip install -r requirements.txt
uvicorn server.main:app --reload --port 8000
```

Frontend (in a second terminal):

```bash
npm install
npm start        # ng serve, with the API proxy from proxy.conf.json
```

Production build + run:

```bash
npm run build             # builds Angular to dist/booking-app/browser
ENV=production uvicorn server.main:app --host 0.0.0.0 --port 8000
```

## Environment

Copy `.env.example` to `.env` and fill in:

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` - MySQL
  connection details
- `ENV` - `development` or `production`
- `PORT` - port FastAPI listens on

Schema migration is not a separate step - `ensure_schema()` runs
automatically on every server start (`server/db/migrate.py`).

## Customizing for a new domain

1. Edit `server/data/resources.py` with real resources.
2. Edit `src/app/core/config.ts` with the domain's vocabulary (app name,
   resource/booking labels).
3. Adjust `capacity` / `slotMinutes` / `openTime` / `closeTime` per resource
   to match real-world booking rules.

See the `build-fullstack-python-angular-app` skill's `references/` docs
for the architecture rationale and domain-modeling guidance behind this
app - including the MySQL-specific adaptations of the double-booking guard
(no partial unique indexes, no transaction-scoped advisory locks) that are
easy to get subtly wrong if you rewrite `server/store/bookings.py` from
scratch.
