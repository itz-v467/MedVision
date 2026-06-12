# Definition of Done

A story is **Done** only when all items pass:

## Code

- [ ] Follows FastAPI `routes → controller → service → dao → model`
- [ ] OOP: classes with typed `__init__` and methods
- [ ] PEP8: `ruff check` and `black --check` pass (88 columns)
- [ ] No magic strings (use `backend/enums/`)
- [ ] Early-return error handling (no deep nesting)
- [ ] Logging via `get_logger()` (no `print()`)

## Tests

- [ ] Unit tests for new service/DAO logic
- [ ] API or integration test for new endpoints
- [ ] All tests pass in CI

## Documentation

- [ ] Backlog item moved to Done
- [ ] README or API note updated if behavior changed

## Deployment

- [ ] Docker build succeeds
- [ ] Migration script included if schema changed
