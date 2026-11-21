# Access Request & Review Management System

A full-stack internal access governance platform. Employees submit access requests, managers and application owners approve them through a two-stage chain, IT Admins grant/revoke access manually, and periodic access review campaigns keep entitlements auditable.

## Architecture

```
frontend/   React (Vite) — role-aware SPA
backend/    Python Flask — REST API, SQLite, bcrypt auth, RBAC
```

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Employee | `alice` | `password123` |
| Employee | `bob` | `password123` |
| Manager | `charlie` | `password123` |
| Manager | `diana` | `password123` |
| Application Owner | `eve` | `password123` |
| Application Owner | `frank` | `password123` |
| IT Admin | `grace` | `password123` |
| IT Admin | `heidi` | `password123` |
| Auditor | `ivan` | `password123` |
| Auditor | `judy` | `password123` |

---

## Local Setup (Windows 11 PowerShell)

### Prerequisites
- Python 3.11+  (`python --version`)
- Node.js 20+   (`node --version`)
- Git

### 1 — Clone & open the workspace

```powershell
cd "C:\Users\kaart\OneDrive\Desktop\access-review-system"
```

### 2 — Backend

```powershell
# Create virtual environment and install dependencies
Set-Location backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt

# Seed the database with demo data
venv\Scripts\python -m app.seed

# Start the Flask API server (http://localhost:5000)
venv\Scripts\python run.py
```

### 3 — Frontend (new PowerShell tab)

```powershell
Set-Location "C:\Users\kaart\OneDrive\Desktop\access-review-system\frontend"
npm install
npm run dev
# Open http://localhost:3000
```

---

## Running Tests

```powershell
Set-Location "C:\Users\kaart\OneDrive\Desktop\access-review-system\backend"
venv\Scripts\pytest tests\ -v
```

Expected: **all tests pass** across auth, RBAC, requests, fulfilment, campaigns, audit log, and reports.

---

## Running with Docker

### Prerequisites
- Docker Desktop for Windows (with Linux containers)

```powershell
Set-Location "C:\Users\kaart\OneDrive\Desktop\access-review-system"

# Build and start both services
docker compose up --build -d

# Seed the database (run once after first startup)
docker compose exec backend python -m app.seed

# Open http://localhost:80 in your browser

# Stop everything
docker compose down
```

The SQLite database is persisted in a Docker volume named `access-review-system_db_data`.

---

## Core Workflows

### 1. Access Request
1. Log in as **alice** (Employee)
2. Click **New Request**
3. Select Application → Access Level → enter Justification → Submit
4. Status becomes `Pending Manager Approval`

### 2. Approval Chain
1. Log in as **charlie** (Manager) — click **Pending Approvals** → Approve / Reject
2. If approved → status becomes `Pending Owner Approval`
3. Log in as **eve** (App Owner) — click **Pending Approvals** → Approve / Reject
4. If approved → status becomes `Approved`

### 3. Grant / Revoke
1. Log in as **grace** (IT Admin) → **Fulfilment**
2. Under *Grant Access* tab: click **Grant** on approved requests
3. Under *Active Grants* tab: click **Revoke** with a reason

### 4. Access Review Campaign
1. Log in as **grace** → **Campaigns** → **New Campaign**
2. Set name, scope (all / application), due date → Create
3. System auto-generates review items for all active grants
4. Log in as **charlie** or **eve** → **Review Items** → Keep / Revoke per item
5. When all items decided → campaign auto-completes

### 5. Audit Log
- Log in as **ivan** (Auditor) → **Audit Log**
- Filter by action, entity type, or user ID

### 6. Reports & CSV
- Log in as **ivan** → **Reports**
- Choose report type → Run → Download CSV

---

## API Reference

| Method | Endpoint | Roles | Description |
|--------|----------|-------|-------------|
| POST | `/api/auth/login` | — | Login, returns token |
| GET | `/api/auth/me` | any | Current user |
| POST | `/api/auth/logout` | any | Invalidate token |
| GET | `/api/users` | it_admin, auditor | List users |
| POST | `/api/users` | it_admin | Create user |
| PUT | `/api/users/<id>` | it_admin | Update user |
| DELETE | `/api/users/<id>` | it_admin | Deactivate user |
| GET | `/api/applications` | any | List apps |
| POST | `/api/applications` | it_admin | Create app |
| PUT | `/api/applications/<id>` | it_admin | Update app |
| DELETE | `/api/applications/<id>` | it_admin | Deactivate app |
| POST | `/api/requests` | employee, manager, app_owner | Submit request |
| GET | `/api/requests/mine` | any | Own requests |
| GET | `/api/requests/pending` | manager, app_owner, it_admin | Pending approvals |
| GET | `/api/requests` | it_admin, auditor | All requests |
| POST | `/api/requests/<id>/approve` | manager, app_owner | Approve |
| POST | `/api/requests/<id>/reject` | manager, app_owner | Reject |
| GET | `/api/fulfilment/approved` | it_admin | Approved, not yet granted |
| POST | `/api/fulfilment` | it_admin | Grant access |
| GET | `/api/fulfilment` | it_admin, auditor | List grants |
| PATCH | `/api/fulfilment/<id>/revoke` | it_admin | Revoke grant |
| POST | `/api/campaigns` | it_admin | Create campaign |
| GET | `/api/campaigns` | it_admin, auditor, manager, app_owner | List campaigns |
| GET | `/api/campaigns/<id>` | it_admin, auditor, manager, app_owner | Campaign detail |
| POST | `/api/campaigns/<cid>/items/<iid>/decide` | manager, app_owner, it_admin | Keep/Revoke item |
| POST | `/api/campaigns/<id>/cancel` | it_admin | Cancel campaign |
| GET | `/api/audit` | it_admin, auditor | Audit log |
| GET | `/api/reports/access-by-user` | it_admin, auditor | Report |
| GET | `/api/reports/access-by-application` | it_admin, auditor | Report |
| GET | `/api/reports/pending-approvals` | it_admin, auditor | Report |
| GET | `/api/reports/overdue-reviews` | it_admin, auditor | Report |
| GET | `/api/reports/revoked-access` | it_admin, auditor | Report |
| GET | `/api/reports/campaign-results?campaign_id=X` | it_admin, auditor | Report |

Append `?format=csv` to any report endpoint to download a CSV file.

---

## Project Structure

```
access-review-system/
├── backend/
│   ├── app/
│   │   ├── __init__.py        Flask app factory
│   │   ├── config.py          Config (Dev / Test)
│   │   ├── models.py          SQLAlchemy models
│   │   ├── auth.py            bcrypt hashing, token lookup
│   │   ├── rbac.py            @login_required, @require_role decorators
│   │   ├── seed.py            Demo data seeder
│   │   └── routes/
│   │       ├── auth_routes.py
│   │       ├── user_routes.py
│   │       ├── app_routes.py
│   │       ├── request_routes.py
│   │       ├── fulfil_routes.py
│   │       ├── campaign_routes.py
│   │       ├── audit_routes.py
│   │       └── report_routes.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_rbac.py
│   │   ├── test_requests.py
│   │   ├── test_fulfil.py
│   │   ├── test_campaigns.py
│   │   ├── test_audit.py
│   │   └── test_reports.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── context/AuthContext.jsx
│   │   ├── components/
│   │   └── pages/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md
```

## CI/CD

GitHub Actions runs on every push and pull request:
1. **backend-tests** — `pytest tests/ -v`
2. **frontend-build** — `npm install && npm run build`

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
