# Body Timeline

A health/fitness web app to track patients' physical progress with meals, weigh-ins, goals, workouts, appointments, and professional notes.

**Tech Stack:** Flask + PostgreSQL + SvelteKit + Tailwind CSS | Installable PWA | Offline-first

## Monorepo Structure

```
body-timeline/
├── api/                    # Flask backend
│   ├── app/
│   │   ├── models/         # SQLAlchemy models (UUID PKs)
│   │   ├── routes/         # API blueprints (/api/v1/*)
│   │   ├── services/       # RBAC, storage adapter
│   │   └── utils/          # Error handlers, validators
│   ├── migrations/         # Alembic migrations
│   ├── tests/              # Auth + RBAC tests
│   ├── seed.py             # DB seed script
│   └── wsgi.py             # App entry point
├── web/                    # SvelteKit frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api/        # API client with auto-refresh
│   │   │   ├── components/ # Sidebar, BottomNav, etc.
│   │   │   ├── config/     # Branding constants
│   │   │   ├── i18n/       # EN/ES translations
│   │   │   ├── offline/    # IndexedDB + sync queue
│   │   │   └── stores/     # Auth, theme, online status
│   │   ├── routes/         # SvelteKit pages
│   │   └── service-worker.ts
│   └── static/             # PWA manifest + icons
├── vercel.json             # Deployment config
└── README.md
```

## Features

- **3 Roles (RBAC):** devadmin, professional, patient — enforced server-side
- **Dashboard:** Summary cards, weight chart, activity chart, next appointment, professional notes, news panel
- **Meals:** CRUD + photo upload, date filters (day/week/month/year/all)
- **Weigh-ins:** Weight tracking with trend indicators
- **Goals:** Weekly/monthly/yearly goals, toggle complete/pending
- **Workouts:** Session logging with exercise items (sets/reps/duration)
- **Notifications:** Professionals send notes to patients; patients mark as read
- **Appointments:** Scheduling with status management
- **PWA:** Installable, offline drafts with sync queue, service worker caching
- **i18n:** English + Spanish
- **Theme:** Dark/light mode

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### 1. Clone and configure

```bash
# Copy environment files
cp api/.env.example api/.env
cp web/.env.example web/.env

# Edit api/.env with your database URL:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/body_timeline
```

### 2. Backend setup

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create database
createdb body_timeline  # or via psql: CREATE DATABASE body_timeline;

# Run migrations (migrations/ dir is pre-configured, skip db init)
flask --app wsgi:app db migrate -m "Initial schema"
flask --app wsgi:app db upgrade

# Seed database
python seed.py

# Start backend
python wsgi.py
# → Running on http://localhost:5000
```

### 3. Frontend setup

```bash
cd web

# Install dependencies
npm install

# Start dev server
npm run dev
# → Running on http://localhost:5173
```

### 4. Login with seed accounts

| Role         | Email                          | Password          |
|--------------|--------------------------------|-------------------|
| Devadmin     | admin@bodytimeline.app         | Admin123!         |
| Professional | professional@bodytimeline.app  | Professional123!  |
| Patient      | patient@bodytimeline.app       | Patient123!       |

## API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Auth
- `POST /auth/register` — Register (creates patient)
- `POST /auth/login` — Login → access_token + refresh_token
- `POST /auth/refresh` — Refresh access token
- `GET /auth/me` — Get current user
- `PATCH /auth/me` — Update profile

### Resources (CRUD)
- `/meals` — Meals + `POST /:id/photos` for photo upload
- `/weigh-ins` — Weight check-ins
- `/goals` — Goals + `POST /:id/toggle` to mark done/undone
- `/workouts` — Workouts with items + `POST /:id/photos`
- `/exercises` — Exercise catalog (devadmin only for CUD)
- `/exercises/requests` — Exercise requests + review
- `/notifications` — Notes + `POST /:id/read` to mark read
- `/appointments` — Appointment scheduling

### Dashboard
- `GET /dashboard/summary?patient_id=` — Summary counts
- `GET /dashboard/weight-series?patient_id=&days=90` — Weight over time
- `GET /dashboard/activity-series?patient_id=&weeks=12` — Workouts per week
- `GET /dashboard/goals-series?patient_id=` — Goals completed over time

### Admin
- `GET /admin/users` — List all users (devadmin only)
- `PATCH /admin/users/:id/role` — Change user role
- `POST /admin/users/:id/toggle-active` — Activate/deactivate
- `GET /admin/assignments` — Professional-patient assignments
- `POST /admin/assignments` — Create assignment
- `DELETE /admin/assignments/:id` — Remove assignment

## Running Tests

```bash
cd api
python -m pytest tests/ -v
```

## Testing Offline Mode

1. Open the app in Chrome and install it as a PWA (click the install icon in the address bar)
2. Open DevTools → Application → Service Workers → check "Offline"
3. Create a meal, weigh-in, or workout — it will be saved as a "Draft (offline)"
4. Uncheck "Offline" — the connection banner will appear and items will sync automatically
5. Check Application → IndexedDB → body-timeline → syncQueue to see the outbox

## Deploying to Vercel

### 1. Set up Vercel Postgres

```bash
# Install Vercel CLI
npm i -g vercel

# Link project
vercel link

# Add Vercel Postgres
vercel env add DATABASE_URL  # paste your Vercel Postgres connection string
```

### 2. Set environment variables

In Vercel dashboard → Settings → Environment Variables:

```
DATABASE_URL=postgres://...         # Vercel Postgres connection string
JWT_SECRET_KEY=your-random-secret   # Generate with: openssl rand -hex 32
SECRET_KEY=another-random-secret
FRONTEND_URL=https://your-app.vercel.app
STORAGE_BACKEND=s3                  # For production
S3_BUCKET=your-bucket
S3_REGION=us-east-1
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_ENDPOINT_URL=...                 # For Cloudflare R2
PUBLIC_API_URL=https://your-app.vercel.app/api/v1
```

### 3. Deploy

```bash
vercel --prod
```

The `vercel.json` is configured to build the SvelteKit frontend and route API requests to the Flask backend.

## Photo Storage

The app uses a storage adapter pattern:

- **Local (dev):** Files saved to `api/uploads/`, served at `/uploads/path`
- **S3/R2 (prod):** Set `STORAGE_BACKEND=s3` and configure S3 credentials

The adapter interface (`api/app/services/storage.py`) supports:
- `upload(file, folder)` → `{storage_key, url}`
- `get_url(storage_key)` → signed URL
- `delete(storage_key)`

## Future Improvements

- [ ] Push notifications (Web Push API)
- [ ] Advanced metrics and body composition tracking
- [ ] Shareable progress reports (PDF export)
- [ ] Real-time chat between professional and patient
- [ ] Calendar view for appointments with drag-and-drop
- [ ] Barcode scanner for food logging
- [ ] Integration with fitness devices (Fitbit, Apple Health)
- [ ] Exercise video demonstrations
- [ ] Meal plan templates
- [ ] Progress photo comparison (side-by-side)
- [ ] Password reset via email
- [ ] Two-factor authentication (2FA)
- [ ] Rate limiting and API throttling
- [ ] Automated backup and data export
- [ ] Admin dashboard analytics
- [ ] Multi-language exercise catalog
- [ ] Social features (group challenges, leaderboards)
