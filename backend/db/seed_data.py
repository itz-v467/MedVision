"""Database seed script for development dashboards."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Allow: python backend/db/seed_data.py (without setting PYTHONPATH)
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.auth import PasswordHasher
from backend.db import Base, get_database_manager
from backend.enums.user_roles import UserRole
from backend.model.document_model import AiMetricModel
from backend.model.user_model import UserModel


class SeedDataRunner:
    """Seeds default admin and dashboard metrics."""

    def run(self) -> None:
        """Execute seed operations."""
        with get_database_manager().session_scope() as session:
            admin = (
                session.query(UserModel)
                .filter(UserModel.email == "admin@medvision.health")
                .first()
            )
            if admin is None:
                hasher = PasswordHasher()
                admin = UserModel(
                    email="admin@medvision.health",
                    password_hash=hasher.hash_password("Admin@12345"),
                    full_name="MedVision Admin",
                    role=UserRole.ADMIN.value,
                    is_verified=True,
                )
                session.add(admin)

            for day_offset in range(14):
                metric_date = (
                    datetime.now(UTC) - timedelta(days=13 - day_offset)
                ).strftime("%Y-%m-%d")
                existing = (
                    session.query(AiMetricModel)
                    .filter(AiMetricModel.metric_date == metric_date)
                    .first()
                )
                if existing is not None:
                    continue
                session.add(
                    AiMetricModel(
                        metric_date=metric_date,
                        predictions_count=20 + day_offset * 3,
                        avg_confidence=0.82 + (day_offset * 0.005),
                        avg_latency_ms=1200 + (day_offset * 10),
                        abnormality_counts={
                            "opacity": 12 + day_offset,
                            "cardiomegaly": 8,
                            "pneumothorax": 2,
                            "effusion": 5,
                        },
                    )
                )


if __name__ == "__main__":
    from backend.config import get_settings

    engine = get_database_manager().engine
    tables = list(Base.metadata.sorted_tables)
    if not get_settings().use_pgvector:
        tables = [t for t in tables if t.name != "document_embeddings"]
    Base.metadata.create_all(engine, tables=tables)
    SeedDataRunner().run()
    print("Seed completed: admin@medvision.health / Admin@12345")
