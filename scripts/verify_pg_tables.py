import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)

from dotenv import load_dotenv

load_dotenv(root / ".env")

import backend.model  # noqa: F401
from backend.config import get_settings
from backend.db import Base, get_database_manager
from sqlalchemy import text

settings = get_settings()
print("database_url:", settings.database_url)
print("table_count:", len(Base.metadata.tables))
engine = get_database_manager().engine
Base.metadata.create_all(engine)
with engine.connect() as conn:
    rows = conn.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    ).fetchall()
print("postgres tables:", [row[0] for row in rows])
