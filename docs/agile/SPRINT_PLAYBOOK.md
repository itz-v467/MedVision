# MedVision Agile Sprint Playbook

## Cadence

| Ceremony | Frequency | Output |
|----------|-----------|--------|
| Sprint Planning | Every 2 weeks | Sprint backlog in `PRODUCT_BACKLOG.md` |
| Daily Standup | Daily | Blockers logged in sprint notes |
| Backlog Refinement | Mid-sprint | Sized user stories |
| Sprint Review | End of sprint | Demo + metrics |
| Retrospective | End of sprint | Process improvements |

## Sprint workflow

1. Pick stories from `PRODUCT_BACKLOG.md` (Ready column).
2. Create branch: `feature/MV-<id>-<short-name>`.
3. Implement using layer rules: FastAPI `routes → controller → service → dao`.
4. Run quality gate: `scripts/quality_gate.ps1`.
5. Open PR with test evidence and Definition of Done checklist.
6. Merge after CI green + peer review.

## Story sizing

- **S**: 1–2 days (single module, e.g. enum or DAO)
- **M**: 3–5 days (service + API + tests)
- **L**: 1 sprint (full vertical slice, e.g. imaging workflow)

## Architecture guardrails (every story)

- OOP: classes with `__init__`, inherit from `BaseDao` / `BaseService` / `BaseController`
- PEP8: 88-char lines, `ruff` + `black` clean
- No business logic in routes or controllers
- No DB access outside DAO layer
