# MedVision Operator & Setup Guide

Master reference for how MedVision works, what each component needs, and what you must provide (API keys, models, data, software).

**Last updated:** Phase 1–2 complete (local dev verified)

---

## 1. Executive summary

**MedVision** is an enterprise multimodal Clinical Decision Support System (CDSS). It ingests clinical files, runs an AI pipeline (OCR → NLP → imaging → correlation → RAG summary → alerts), and presents results on a physician dashboard with mandatory review before finalization.

### Current phase status

| Phase | Scope | Status |
|-------|--------|--------|
| Phase 1 | OCR, NLP, chest X-ray AI, summaries, dashboard | Done |
| Phase 2 | Longitudinal timeline, alerting, explainability heatmap, physician review | Done |
| Phase 3 | DICOM, PACS, CT/MRI, public APIs | Not started |
| Phase 4 | Predictive AI, federated learning | Not started |

### Default login (after seed)

| Field | Value |
|-------|--------|
| Email | `admin@medvision.health` |
| Password | `Admin@12345` |

### Local URLs

| Service | URL |
|---------|-----|
| Frontend (dev) | http://localhost:5173 |
| Backend API | http://localhost:5000 |
| OpenAPI docs | http://localhost:5000/docs |
| Frontend (Docker Compose) | http://localhost:8080 — only when running `docker compose up` with the `frontend` service |

---

## 2. Architecture

```mermaid
flowchart TB
  subgraph frontend [Frontend localhost:5173]
    Login[LoginPage]
    Upload[UploadPage]
    Dashboard[DashboardPage]
    Encounters[EncountersPage]
    Review[ReviewPage]
  end

  subgraph backend [Backend localhost:5000]
    Auth["/auth/*"]
    Clinical["/api/clinical/*"]
    Stats["/api/stats/*"]
    Audit["/api/audit/*"]
  end

  subgraph pipeline [AI Pipeline]
    OCR[OcrService]
    NLP[MedicalNlpService]
    Imaging[ImagingAiService]
    RAG[RagIndexingService]
    Summary[ClinicalSummaryService]
    Alerts[AlertEngineService]
  end

  subgraph data [Data Layer]
    PG[(PostgreSQL + pgvector)]
    Redis[(Redis)]
    Files[./data/uploads]
  end

  Upload --> Clinical
  Clinical --> pipeline
  pipeline --> PG
  pipeline --> Files
  RAG --> PG
  Dashboard --> Stats
  Review --> Clinical
```

### Code layout (where things live)

| Layer | Path | Purpose |
|-------|------|---------|
| ORM models | `backend/model/` | Database tables as Python classes |
| DAO | `backend/dao/` | Database queries only |
| Services | `backend/service/` | Business logic + AI orchestration |
| AI clients | `backend/client/` | Model loaders, OpenAI, OCR, X-ray, vectors |
| API | `backend/routes/` → `backend/controller/` | HTTP layer |
| Config | `.env`, `backend/config/settings_manager.py` | Secrets and settings |
| Frontend pages | `frontend/src/pages/` | UI |
| Frontend API | `frontend/src/api/` | Calls backend |

Pipeline orchestrator: [`backend/service/ingestion_service.py`](../backend/service/ingestion_service.py)

---

## 3. End-to-end workflow

When you upload a file via **Upload & AI Workflow**, this sequence runs:

| Step | Service | Input | Stored in DB |
|------|---------|-------|--------------|
| 1 | Upload + storage | PDF / PNG / JPG / TXT / CSV | `patients`, `encounters`, `documents` |
| 2 | OCR | File on disk | `ocr_results` (biomarkers, raw_text) |
| 3 | NLP | OCR `raw_text` | `nlp_extractions` (entities, ICD-10, SNOMED) |
| 4 | Imaging | X-ray images only (`file_type=xray`) | `imaging_studies`, `inference_results` |
| 5 | Correlation | OCR / NLP / imaging confidence | Response JSON only |
| 6 | Explainability | Imaging findings | Evidence traces + heatmap PNG path |
| 7 | RAG + summary | Multimodal context | `document_embeddings`, `clinical_summaries` |
| 8 | Alerts | Imaging findings ≥ 70% probability | `alerts` |
| 9 | Physician review | UI: Approve / Acknowledge | Summary → `FINALIZED`, alerts acknowledged |

### Supported file types (today)

| MIME type | Extensions | Notes |
|-----------|------------|-------|
| `application/pdf` | `.pdf` | Lab reports — pdfplumber OCR |
| `image/png`, `image/jpeg` | `.png`, `.jpg` | X-rays — imaging AI + optional Tesseract OCR |
| `text/plain` | `.txt` | Clinical notes — direct text read |
| `text/csv` | `.csv` | Lab panels — parsed as text |

**Not supported yet:** DICOM (`.dcm`), HL7, PACS direct pull.

### Upload file types (UI dropdown)

| `file_type` value | Use for |
|-------------------|---------|
| `lab_report` | PDF, CSV lab results |
| `xray` | Chest X-ray PNG/JPG |
| `clinical_note` | TXT clinical notes |

---

## 4. UI pages

| URL | Page | What it does |
|-----|------|--------------|
| `/login` | Login | JWT authentication |
| `/dashboard` | Dashboard | Live stats, 4 charts, critical alerts + acknowledge |
| `/upload` | Upload & AI Workflow | Run full pipeline on one file |
| `/encounters` | Encounter triage | Queue of encounters → **Review** link |
| `/review/:encounterId` | Physician review | Summary, heatmap, timeline, finalize, alert ack |
| `/audit` | Audit logs | Admin-only immutable audit trail |

---

## 5. AI components — what YOU need to provide

This is the main checklist for API keys, models, and optional software.

| Component | Engine (current) | Code location | Required from you | Fallback if missing |
|-----------|------------------|---------------|-------------------|---------------------|
| **Chest X-ray AI** | TorchXRayVision DenseNet | [`backend/client/xray_inference_client.py`](../backend/client/xray_inference_client.py) | `pip install -r backend/requirements-ml.txt`; optional GPU (`IMAGING_DEVICE=cuda`); ~100–300 MB download on first run | Deterministic hash-based scores (vary by file path, not real AI) |
| **OCR — PDF** | pdfplumber | [`backend/client/ocr_extractor.py`](../backend/client/ocr_extractor.py) | Included in `requirements-ml.txt` | Empty text, low confidence |
| **OCR — images** | pytesseract + Pillow | same | Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on Windows + `requirements-ml.txt` | No text extracted from images |
| **Medical NLP** | Rule-based keyword extraction | [`backend/client/ocr_extractor.py`](../backend/client/ocr_extractor.py) (`extract_clinical_entities`) | **Nothing** — works offline | Limited vs full scispaCy (Phase 3 upgrade) |
| **RAG embeddings** | sentence-transformers `all-MiniLM-L6-v2` (384-dim) | [`backend/client/embedding_client.py`](../backend/client/embedding_client.py) | `requirements-ml.txt`; ~90 MB model download on first use | Hash-based placeholder vectors |
| **Clinical summaries** | OpenAI GPT | [`backend/client/openai_client.py`](../backend/client/openai_client.py) | **`OPENAI_API_KEY`** in `.env` | Template summary (free, no LLM) |
| **Vector store** | pgvector in PostgreSQL | [`backend/client/vector_store_client.py`](../backend/client/vector_store_client.py) | Docker Postgres: `docker compose up -d postgres` | Disabled if using SQLite URL |
| **Heatmaps** | Intensity overlay PNG | Imaging pipeline | Upload chest X-ray with `file_type=xray` | Review page shows "No heatmap" |
| **Redis** | redis-py | Docker Compose | `docker compose up -d redis` | Configured but lightly used in MVP |

### Imaging findings detected (chest X-ray)

Mapped from TorchXRayVision to FRD keys: `pneumothorax`, `opacity`, `pleural_effusion`, `nodule`, `cardiomegaly`.

Default model: `densenet121-res224-all` (env: `IMAGING_MODEL_NAME`).

### NLP entities extracted (keyword-based)

- **Diseases:** pneumonia, diabetes, anemia, tuberculosis, hypertension, COPD, asthma  
- **Symptoms:** cough, fever, dyspnea, chest pain, fatigue, nausea  
- **Medications:** amoxicillin, metformin, aspirin, ibuprofen, insulin, azithromycin  
- **ICD-10 / SNOMED:** mapped for common diseases when keywords match  

### OCR biomarkers parsed (regex)

Hemoglobin, glucose, WBC, creatinine (from extracted text).

---

## 6. Environment variables

Copy [`.env.example`](../.env.example) to `.env` in the project root. **Never commit `.env`.**

### Required for local development (defaults work)

| Variable | Example | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql://medvision:medvision@localhost:5432/medvision` | Primary DB + pgvector |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache / future jobs |
| `JWT_SECRET_KEY` | strong random string | JWT signing |
| `SECRET_KEY` | strong random string | App secret |
| `STORAGE_PATH` | `./data/uploads` | Uploaded files + heatmaps |
| `CORS_ORIGINS` | `http://localhost:5173` | Frontend origin |

### Required for real LLM summaries

| Variable | Example | Where to get it |
|----------|---------|-----------------|
| `OPENAI_API_KEY` | `sk-...` | https://platform.openai.com/api-keys |
| `OPENAI_LLM_MODEL` | `gpt-4o-mini` or `gpt-4o` | OpenAI dashboard |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Optional — embeddings use local MiniLM by default |

### Imaging (optional tuning)

| Variable | Default | Purpose |
|----------|---------|---------|
| `IMAGING_MODEL_NAME` | `densenet121-res224-all` | TorchXRayVision weights |
| `IMAGING_WEIGHTS_DIR` | `./models/imaging` | Local cache directory |
| `IMAGING_DEVICE` | `cpu` | Set `cuda` if NVIDIA GPU available |
| `IMAGING_DETECTION_THRESHOLD` | `0.5` | Probability cutoff for "detected" |

### RAG / embeddings (optional — defaults work)

| Variable | Default | Purpose |
|----------|---------|---------|
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Local embedding model |
| `EMBEDDING_DIMENSIONS` | `384` | Must match pgvector column |
| `VECTOR_SEARCH_LIMIT` | `5` | Max RAG chunks retrieved |

### Test-only flags (do not use in production dev)

| Variable | Value | Purpose |
|----------|-------|---------|
| `IMAGING_ENABLED` | `false` | Skip TorchXRayVision probe in tests |
| `EMBEDDINGS_ENABLED` | `false` | Skip sentence-transformers in tests |

### Unused in current MVP (reserved)

| Variable | Default | Notes |
|----------|---------|-------|
| `ML_INFERENCE_BASE_URL` | `http://localhost:8001` | For future external ML microservice |

---

## 7. Software and hardware requirements

| Requirement | Version | Required? | Notes |
|-------------|---------|-----------|-------|
| Python | 3.11+ (3.13 OK) | Yes | Use venv: `python -m venv .venv` |
| Node.js | 18+ | Yes | Frontend only |
| Docker Desktop | Latest | Yes | Postgres + Redis |
| pip packages | see below | Yes | Two requirement files |
| Tesseract OCR | Latest | Optional | Image OCR on Windows |
| NVIDIA GPU + CUDA | — | Optional | Set `IMAGING_DEVICE=cuda` |
| Disk space | ~2 GB | Yes | PyTorch + Hugging Face models |

### Install commands (PowerShell, project root)

```powershell
# 1. Infrastructure
docker compose up -d postgres redis
Copy-Item .env.example .env
# Edit .env — add OPENAI_API_KEY if you want real summaries

# 2. Python backend
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
pip install -r backend\requirements-ml.txt

# 3. Database seed
$env:PYTHONPATH = "."
python scripts\seed_database.py

# 4. Run API
uvicorn backend.app:create_app --factory --reload --port 5000
```

```powershell
# 5. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Tesseract on Windows (optional, for image OCR)

1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki  
2. Add Tesseract to PATH  
3. Verify: `tesseract --version`

---

## 8. Sample data you should provide

Place anonymized files in `data/samples/` (gitignored except README and bundled samples).

| Folder | Format | Min count | Purpose |
|--------|--------|-----------|---------|
| `data/samples/xray/` | `.png`, `.jpg` | 5–10 | Real chest X-ray AI + heatmap |
| `data/samples/labs/` | `.pdf` | 3–5 | PDF OCR + biomarker parsing |
| `data/samples/notes/` | `.txt` | 2–3 | NLP entity extraction |

### Included in repo

| File | Purpose |
|------|---------|
| `data/samples/notes/sample_clinical_note.txt` | NLP + upload test |
| `data/samples/labs/sample_lab_panel.csv` | Lab biomarker parsing |
| `data/samples/README.md` | Folder guide |

### Rules

- Remove patient names, IDs, and dates (or use synthetic data)  
- Public datasets (e.g. NIH ChestX-ray14) OK if you lack real images  
- Do not commit PHI or API keys  

---

## 9. API reference

All authenticated endpoints require header: `Authorization: Bearer <access_token>`

Interactive documentation: http://localhost:5000/docs

### Authentication (`/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Create user account |
| POST | `/auth/login` | No | Get access + refresh tokens |
| POST | `/auth/refresh` | No | Refresh access token |
| POST | `/auth/logout` | Yes | Revoke refresh tokens |
| POST | `/auth/forgot-password` | No | Password reset request |
| POST | `/auth/reset-password` | No | Complete password reset |
| PUT | `/auth/update-password` | Yes | Change password |

### Clinical AI (`/api/clinical`)

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| POST | `/api/clinical/upload` | Admin, Radiologist, Physician, Technician | Upload + full AI pipeline |
| GET | `/api/clinical/encounters` | Any authenticated | Triage queue |
| GET | `/api/clinical/encounters/{id}` | Any authenticated | Full encounter detail |
| GET | `/api/clinical/encounters/{id}/heatmap` | Any authenticated | Explainability PNG |
| POST | `/api/clinical/summaries/{id}/finalize` | Admin, Radiologist, Physician | Approve summary |
| POST | `/api/clinical/alerts/{id}/acknowledge` | Any authenticated | Acknowledge alert |
| GET | `/api/clinical/patients/{id}/timeline` | Any authenticated | Longitudinal timeline |

### Dashboard stats (`/api/stats`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stats/dashboard` | Overview metrics |
| GET | `/api/stats/charts` | Chart.js datasets |
| GET | `/api/stats/alerts` | Critical alert feed |
| GET | `/api/stats/patients` | Patient statistics |
| GET | `/api/stats/ai-performance` | AI latency / confidence KPIs |

### Audit (`/api/audit`)

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/audit/logs` | Admin only | Immutable audit log |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |

---

## 10. Database tables

After `python scripts\seed_database.py` with PostgreSQL, these **14 tables** exist:

| Table | Purpose |
|-------|---------|
| `users` | Accounts + RBAC roles |
| `refresh_tokens` | JWT refresh tokens |
| `patients` | Patient records |
| `encounters` | Clinical encounters / triage |
| `documents` | Uploaded file metadata |
| `ocr_results` | Structured OCR output |
| `nlp_extractions` | Entity + code extraction |
| `imaging_studies` | Radiology study metadata |
| `inference_results` | X-ray findings + heatmap path |
| `clinical_summaries` | AI summaries + review status |
| `document_embeddings` | pgvector RAG chunks (384-dim) |
| `alerts` | Clinical alerts |
| `audit_logs` | Immutable audit trail |
| `ai_metrics` | Dashboard seed metrics |

ORM definitions: [`backend/model/`](../backend/model/)

Verify tables:

```powershell
docker exec medvision-main-postgres-1 psql -U medvision -d medvision -c "\dt"
```

---

## 11. User roles (RBAC)

| Role | Upload | Review / finalize | Audit logs |
|------|--------|-------------------|------------|
| ADMIN | Yes | Yes | Yes |
| RADIOLOGIST | Yes | Yes | No |
| PHYSICIAN | Yes | Yes | No |
| TECHNICIAN | Yes | No | No |
| ANALYST | No | No | No |
| VIEWER | No | No | No |

---

## 12. What is NOT built yet (Phase 3+)

| Feature | Backlog / PRD | Status |
|---------|---------------|--------|
| DICOM upload | Phase 3 | Not started |
| PACS / DICOMweb integration | Phase 3 | Not started |
| CT / MRI models | Phase 3 | Not started |
| Public partner API (`/api/v1/external`) | Phase 3 | Not started |
| scispaCy / PaddleOCR / cloud OCR | Enhancement | Not started |
| Vault + TLS production hardening | MV-402 | Ready in backlog |
| MFA / SSO | FRD | Not started |

---

## 13. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Blank frontend page | JS error (e.g. Chart.js) or bad route | Hard refresh (`Ctrl+Shift+R`); check browser console; restart `npm run dev` |
| `pip install` fails on numpy | Python 3.13 + old numpy pin | Use [`backend/requirements.txt`](../backend/requirements.txt) with `numpy>=2.1.0,<3` |
| `ModuleNotFoundError: psycopg2` | Postgres driver missing | `pip install psycopg2-binary pgvector` |
| Login fails | DB not seeded | `docker compose up -d postgres` then `python scripts\seed_database.py` |
| Summaries are generic templates | No OpenAI key | Set `OPENAI_API_KEY` in `.env` and restart backend |
| No heatmap on review | Not an X-ray upload | Upload PNG/JPG with **Chest X-ray** file type |
| Imaging scores look fake / repetitive | ML deps not installed | `pip install -r backend\requirements-ml.txt` |
| `document_embeddings` table missing | SQLite URL used | Set `DATABASE_URL` to PostgreSQL and re-seed |
| CORS errors from frontend | Wrong origin | Set `CORS_ORIGINS=http://localhost:5173` in `.env` |
| Seed connects to wrong DB | Stale `DATABASE_URL` in shell | Remove env override: `Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue` |

### Quality gate (before PRs)

```powershell
.\scripts\quality_gate.ps1
```

---

## 14. Phase 3 handoff checklist

Copy and fill this when asking the agent to start Phase 3:

```
MedVision Phase 3 readiness
---------------------------
OpenAI API key set in .env:        [ ] yes  [ ] no
backend/requirements-ml.txt installed: [ ] yes  [ ] no
Tesseract installed (Windows):     [ ] yes  [ ] no  [ ] not needed
GPU available (IMAGING_DEVICE=cuda): [ ] yes  [ ] no
Sample X-rays in data/samples/xray/: [ ] yes  [ ] no
Docker Postgres + Redis running:   [ ] yes  [ ] no

Phase 3 priority (pick one to start):
[ ] DICOM upload + parsing
[ ] PACS / DICOMweb integration
[ ] Public partner API + API keys
[ ] CT/MRI modality support
```

---

## 15. Related documentation

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Quick start |
| [.env.example](../.env.example) | Environment template |
| [MedVision_PRD.md](../MedVision_PRD.md) | Product requirements |
| [MedVision_FRD.md](../MedVision_FRD.md) | Functional requirements |
| [docs/agile/PRODUCT_BACKLOG.md](agile/PRODUCT_BACKLOG.md) | Sprint backlog |
| [docs/agile/SPRINT_PLAYBOOK.md](agile/SPRINT_PLAYBOOK.md) | Dev workflow |

---

*This guide reflects the codebase as of Phase 2 completion. Update it when Phase 3 features land.*
