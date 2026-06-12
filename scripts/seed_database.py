"""Run database seed from project root (no PYTHONPATH required)."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(_PROJECT_ROOT / ".env")

from backend.config.settings_manager import SettingsManager
from backend.db.database_manager import DatabaseManager

SettingsManager.reset_instance()
DatabaseManager.reset_instance()

import backend.model  # noqa: F401, E402
from backend.db import Base, get_database_manager
from backend.db.seed_data import SeedDataRunner


def main() -> None:
    """Create tables and seed development data."""
    from backend.config import get_settings

    engine = get_database_manager().engine
    tables = list(Base.metadata.sorted_tables)
    if not get_settings().use_pgvector:
        tables = [t for t in tables if t.name != "document_embeddings"]
    Base.metadata.create_all(engine, tables=tables)
    SeedDataRunner().run()
    print("Seed completed: admin@medvision.health / Admin@12345")


if __name__ == "__main__":
    main()
