# MedVision — Clinical AI Platform

**intelligence that cares**

AI-powered multimodal clinical decision support for radiology, lab OCR, medical NLP, explainable imaging, and physician-reviewed summaries.

## Architecture

- **Backend**: FastAPI modular monolith (`routes → controller → service → dao → db`)
- **Frontend**: React + Vite clinical workspace UI
- **Data**: PostgreSQL (+ **pgvector** for RAG), Redis
- **AI**: Isolated service layer with singleton model loader

## UI highlights

| Feature | Description |
|---------|-------------|
| **Icon-only sidebar** | Only the MedVision logo shows on the left; click to open the navigation drawer |
| **Adaptive layout** | Main content expands to full width when the menu is closed |
| **Physician triage** | Workspace shows **pending review cards** — one click opens the case review screen |
| **Patient search** | Available on the **Reports** page only (not in the sidebar) |
| **Sage clinical palette** | Soft teal/sage accents for a calm clinical UI |
| **Centered login** | Minimal sign-in with logo and tagline *intelligence that cares* |

### Physician workflow

1. Sign in → land on **Workspace**
2. Review **Reports pending review** cards at the top (status `REVIEW_REQUIRED` or `PROCESSING`)
3. Click a card → enter unified case review
4. Use **Reports** page to search patients by name or MV number
5. Click the **MedVision icon** (left edge) to open navigation: Workspace, New case, Reports

Sidebar open/closed state is remembered in `localStorage`.

## Engineering standards

| Standard | Implementation |
|----------|----------------|
| **OOP** | `BaseDao`, `BaseService`, `BaseController`, `BaseRouteRegistrar`, `SingletonMixin` |
| **PEP8** | 88-char lines, `ruff` + `black` (see `pyproject.toml`) |
| **Agile** | Sprint playbook, backlog, DoD in `docs/agile/`; CI on every PR |

### Quality gate (run before each PR)

```powershell
.\scripts\quality_gate.ps1
```

Or install dev tools: `pip install -r backend/requirements-dev.txt`

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

- **UI**: http://localhost:8080
- **API**: http://localhost:5000 (OpenAPI: http://localhost:5000/docs)

Default admin (after seed):

- Email: `admin@medvision.health`
- Password: `Admin@12345`

### Local development

```powershell
# Backend (from project root)
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
python scripts\seed_database.py
$env:PYTHONPATH = "."
uvicorn backend.app:create_app --factory --reload --port 5000

# Frontend
cd frontend
npm install
npm run dev
```

> **Note:** In PowerShell use `$env:PYTHONPATH = "."` (not `set PYTHONPATH=.`).

The backend Docker image installs `requirements-ml.txt` so TorchXRayVision runs in containers. For local dev without ML deps, the imaging client uses a deterministic fallback scorer.

### Unified clinical cases

Upload lab report + chest X-ray in one intake session:

- **UI**: New case → add documents per slot → unified physician review
- **API**: `POST /api/clinical/cases` with multipart `files[]` and `file_types[]`
- **Review**: unified summary, lab table, X-ray viewer, correlation cards, care plan

### Backfill X-ray anomaly regions (existing encounters)

```powershell
$env:PYTHONPATH = "."
python scripts\backfill_imaging_regions.py
python scripts\backfill_imaging_regions.py --dry-run
```

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /auth/login` | Authenticate |
| `POST /auth/refresh` | Refresh access token |
| `GET /api/stats/dashboard` | Live dashboard metrics |
| `GET /api/stats/charts` | Chart.js datasets |
| `POST /api/clinical/upload` | Single-file AI workflow (backward compatible) |
| `POST /api/clinical/cases` | **Unified case** — multiple documents → one encounter |
| `GET /api/clinical/encounters/{id}` | Full review payload |

## Data layer (PostgreSQL + vectors)

| Store | Purpose | Status |
|-------|---------|--------|
| **PostgreSQL** | Users, encounters, clinical results, audit | Docker `pgvector/pgvector:pg16`, Alembic migrations |
| **pgvector** | RAG embeddings, similarity search | `document_embeddings` table, `VectorStoreClient` |
| **Redis** | Cache, future job queue | Docker Compose |

Start Postgres + pgvector:

```powershell
docker compose up -d postgres redis
Copy-Item .env.example .env
python scripts\seed_database.py
```

## Compliance Notes

Configure Vault, TLS 1.3, and PHI encryption before hospital deployment. This repository provides production structure; operational hardening is environment-specific.
