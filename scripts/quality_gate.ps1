# MedVision local quality gate (agile DoD automation)
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "."

Write-Host "Running Ruff (PEP8)..."
ruff check backend

Write-Host "Running Black..."
black --check backend

Write-Host "Running Pytest..."
$env:DATABASE_URL = "sqlite+pysqlite:///:memory:"
$env:JWT_SECRET_KEY = "test-secret"
$env:SECRET_KEY = "test-secret"
pytest

Write-Host "Quality gate passed."
