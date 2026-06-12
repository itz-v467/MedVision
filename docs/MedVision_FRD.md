# MedVision — Functional Requirements Document (FRD)

Version: 1.0  
Status: Draft  
Date: May 2026

## Introduction

This FRD defines the functional behavior, workflows, integrations, constraints, and operational requirements for MedVision.

## System Modules

| Module | Purpose |
|---|---|
| Authentication Service | Identity management |
| Data Ingestion Service | Upload workflows |
| OCR Engine | Structured extraction |
| NLP Engine | Medical entity extraction |
| Imaging AI Engine | Radiology inference |
| Correlation Engine | Cross-modal reasoning |
| Summary Generator | AI summaries |
| Explainability Engine | Evidence traceability |
| Dashboard Service | Physician workflows |

## Authentication Requirements

### FR-AUTH-01
Support:
- Email/password login
- OAuth2
- MFA
- SSO

### FR-AUTH-02
Implement RBAC.

### FR-AUTH-03
Use JWT-based sessions.

## Data Ingestion Requirements

### FR-ING-01
Support:
- PDF
- PNG
- JPEG
- DICOM
- CSV
- TXT

### FR-ING-02
Validate:
- file integrity
- MIME type
- file size

### FR-ING-03
Perform antivirus scanning.

## OCR Requirements

### FR-OCR-01
Extract:
- Patient demographics
- Biomarkers
- Lab values
- Dates
- Clinical observations

### FR-OCR-02
Return structured JSON.

### FR-OCR-03
Support confidence scoring.

## NLP Requirements

### FR-NLP-01
Extract:
- Diseases
- Symptoms
- Medications
- Allergies

### FR-NLP-02
Support SNOMED-CT and ICD-10 mapping.

### FR-NLP-03
Support negation detection.

## Imaging AI Requirements

### FR-IMG-01
Support chest X-ray analysis.

### FR-IMG-02
Detect:
- Pneumothorax
- Opacities
- Pleural effusion
- Nodules
- Cardiomegaly

### FR-IMG-03
Generate:
- Probability scores
- Bounding boxes
- Grad-CAM heatmaps

## Correlation Engine Requirements

### FR-COR-01
Correlate:
- Imaging findings
- Lab results
- Symptoms
- Historical encounters

### FR-COR-02
Generate weighted evidence scoring.

## Summary Generation Requirements

### FR-SUM-01
Generate structured AI summaries.

### FR-SUM-02
Use RAG grounding.

### FR-SUM-03
Require physician review before finalization.

## Explainability Requirements

### FR-EXP-01
Provide source traceability.

### FR-EXP-02
Display confidence scores.

### FR-EXP-03
Support heatmap visualization.

## Dashboard Requirements

### FR-DSH-01
Display encounter queues.

### FR-DSH-02
Display AI-generated findings.

### FR-DSH-03
Support physician annotations.

## Audit & Compliance Requirements

### FR-AUD-01
Maintain immutable audit logs.

### FR-AUD-02
Track AI model versions.

## Security Requirements

### FR-SEC-01
AES-256 encryption required.

### FR-SEC-02
TLS 1.3 mandatory.

### FR-SEC-03
Vault-managed secrets required.

## Deployment Requirements

Support:
- Cloud deployment
- Hybrid deployment
- On-prem hospital deployment

## Final Engineering Recommendation

Prioritize:
1. OCR pipeline
2. Chest X-ray AI
3. AI summaries
4. Dashboard workflows
5. Explainability layer

Delay predictive AI and advanced automation until production validation is complete.
