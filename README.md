# 🏛️ LexIntellectus

**ERP SaaS para el sector legal nicaragüense**

Gestión procesal, notarial, financiera y asistente legal con IA.

---

## 🚀 Quick Start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Python 3.11+](https://python.org)
- [Node.js 18+](https://nodejs.org)

### 1. Start Infrastructure
```bash
docker compose up -d
```
This starts PostgreSQL (with pgvector), Redis, and MinIO.

### 2. Start Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:3000

---

## 📁 Project Structure

```
LexIntellectus/
├── docker-compose.yml          # PostgreSQL, Redis, MinIO
├── .env                        # Environment variables
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── core/               # Config, DB, Security, Dependencies
│   │   ├── models/             # SQLAlchemy ORM (tenant, user, audit)
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── api/v1/             # API routes (auth, users, tenants, health)
│   │   └── middleware/         # Tenant isolation, audit logging
│   └── alembic/                # Database migrations
└── frontend/
    └── src/app/
        ├── login/page.tsx      # Login & registration
        └── dashboard/page.tsx  # Main dashboard
```

## 🎨 Design System — "Minimalismo Judicial"

| Token | Color | Usage |
|-------|-------|-------|
| Primary | `#1E3A5F` (Azul Justicia) | Headers, buttons, sidebar |
| Accent | `#D4AF37` (Dorado Notarial) | Highlights, badges, CTAs |
| Font | Inter + JetBrains Mono | UI + legal codes |

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | Login |
| `POST` | `/api/v1/auth/register` | Register tenant + admin |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT token |
| `GET` | `/api/v1/auth/me` | Current user profile |
| `GET` | `/api/v1/users/` | List users (admin) |
| `POST` | `/api/v1/users/` | Create user (admin) |
| `GET` | `/api/v1/tenants/current` | Current tenant info |
| `GET` | `/api/v1/health` | Health check |

---

© 2026 LexIntellectus. All rights reserved.
