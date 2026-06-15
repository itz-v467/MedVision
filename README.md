# MedVision — Enterprise Clinical AI Platform

AI-powered multimodal clinical decision support for radiology, lab OCR, medical NLP, explainable imaging, and physician-reviewed summaries.

## Architecture

- **Backend**: FastAPI modular monolith (`routes → controller → service → dao → db`)
- **Frontend**: React + Vite enterprise dashboard
- **Data**: PostgreSQL (+ **pgvector** for RAG), Redis
- **AI**: Isolated service layer with singleton model loader

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

### Local development

```powershell
# Backend (PowerShell — from project root MedVision)
cd C:\Users\vroy4\Desktop\MedVision
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
python scripts\seed_database.py
$env:PYTHONPATH = "."
uvicorn backend.app:create_app --factory --reload --port 5000
```

> **Note:** `set PYTHONPATH=.` is CMD only. In PowerShell use `$env:PYTHONPATH = "."`
> Or run seed without PYTHONPATH: `python scripts\seed_database.py`

# Frontend
cd frontend
npm install
npm run dev
```

Default admin (after seed):

- Email: `admin@medvision.health`
- Password: `Admin@12345`

### Docker

```bash
docker compose up --build
```

The backend Docker image installs `requirements-ml.txt` so TorchXRayVision runs in containers. For local dev without ML deps, the imaging client uses a deterministic fallback scorer.

### Unified clinical cases

Upload lab report + chest X-ray in one intake session:

- **UI**: Patient intake → add documents per slot → one physician review page
- **API**: `POST /api/clinical/cases` with multipart `files[]` and `file_types[]`
- **Review**: unified summary, lab table, X-ray viewer with anomaly box, correlation cards

### Backfill X-ray anomaly regions (existing encounters)

```powershell
$env:PYTHONPATH = "."
python scripts\backfill_imaging_regions.py
python scripts\backfill_imaging_regions.py --dry-run
```

- API: http://localhost:5000 (OpenAPI docs: http://localhost:5000/docs)
- UI: http://localhost:8080

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /auth/login` | Authenticate |
| `POST /auth/refresh` | Refresh access token |
| `GET /api/stats/dashboard` | Live dashboard metrics |
| `GET /api/stats/charts` | Chart.js datasets |
| `POST /api/clinical/upload` | Single-file AI workflow (backward compatible) |
| `POST /api/clinical/cases` | **Unified case** — multiple documents (lab + X-ray + note) → one encounter |
| `GET /api/clinical/encounters/{id}` | Full review payload (`case_type`, `correlation`, `imaging.regions`) |

## Data layer (PostgreSQL + vectors)

| Store | Purpose | Status |
|-------|---------|--------|
| **PostgreSQL** | Users, encounters, clinical results, audit | Docker `pgvector/pgvector:pg16`, Alembic migrations |
| **pgvector** | RAG embeddings, similarity search | `document_embeddings` table, `VectorStoreClient` |
| **Redis** | Cache, future job queue | Docker Compose |
| **SQLite** | Optional local dev only | No vector search |

Start Postgres + pgvector:

```powershell
docker compose up -d postgres redis
Copy-Item .env.example .env
python scripts\seed_database.py
```

## Compliance Notes

Configure Vault, TLS 1.3, and PHI encryption before hospital deployment. This repository provides production structure; operational hardening is environment-specific.
